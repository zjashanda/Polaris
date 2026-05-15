#!/usr/bin/env python3
"""Execute a measured interruption injection case on real hardware.

The script consumes `selected_interrupt_prerequisite.json` produced by
measure_interrupt_prerequisites.py, builds one deterministic audio sequence:

  wake -> prerequisite command -> wait until measured self-play injection point
  -> wake/command injection

It then parses serial evidence to decide whether the injection really landed
inside a self-play window and whether the expected new wake/ASR evidence was
observed. Timing misses are reported as TIMING_AMBIGUOUS/BLOCKED instead of
firmware failures.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


BASE = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEVICE_KEY = "VID_8765&PID_5678:9_2A847557_7_0000"
DEFAULT_WAKE_WORD = "小美小美"

if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from tools.audio.polaris_audio_builder import CHANNELS, SAMPLE_RATE, SAMPLE_WIDTH, ensure_tts_pcm, read_pcm, silence_pcm
from tools.core.polaris_config import add_canonical_log_aliases, configured_log_ports
from tools.core.polaris_runtime import parse_prefixed_timestamp, read_lines_between
from tools.execution.polaris_case_runner import sanitize_logs, summarize_window
from tools.execution.polaris_doc_case_runner import collect_metrics
from tools.validation.polaris_fa2_command_batch import pcm_duration_ms, run_playback

from measure_interrupt_prerequisites import build_events, build_wb_events, pair_windows, window_to_payload


CP_WAKE_RE = re.compile(r"WAKE\(1\)", re.I)
AP_WAKE_RE = re.compile(r"wakeup_callback|multi_allow_wakeup_callback", re.I)
ASR_WAKE_RE = re.compile(r"\b(?:online|offline)_wakeup\b", re.I)
ASR_TEXT_RE = re.compile(r"(?:online|offline)_asr_callbak,\s*text:\s*(.+)$", re.I)
CP_CMD_KEYWORD_RE = re.compile(r"WAKE\(0\):.*?\(([^)]+)\)", re.I)


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT))
    except Exception:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def default_output_dir() -> Path:
    bdd_run_dir = os.environ.get("POLARIS_BDD_RUN_DIR", "").strip()
    if bdd_run_dir:
        return Path(bdd_run_dir).resolve() / "interrupt_execution"
    return BASE / "debug" / "interrupt_execution" / stamp()


def latest_selected_file() -> Optional[Path]:
    patterns = [
        BASE / "debug" / "runs",
        BASE / "debug" / "interrupt_measurements",
    ]
    files: List[Path] = []
    for root in patterns:
        if root.exists():
            files.extend(root.glob("**/selected_interrupt_prerequisite.json"))
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def append_tts(combined: bytearray, text: str) -> Dict[str, Any]:
    pcm_path = ensure_tts_pcm(text)
    pcm = read_pcm(pcm_path)
    start_ms = pcm_duration_ms(combined)
    combined.extend(pcm)
    end_ms = pcm_duration_ms(combined)
    return {
        "type": "tts",
        "text": text,
        "pcm_path": str(pcm_path),
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
    }


def append_silence(combined: bytearray, duration_ms: int) -> Dict[str, Any]:
    start_ms = pcm_duration_ms(combined)
    pcm = silence_pcm(max(0, duration_ms))
    combined.extend(pcm)
    end_ms = pcm_duration_ms(combined)
    return {"type": "silence", "start_ms": start_ms, "end_ms": end_ms, "duration_ms": duration_ms}


def build_interrupt_audio(
    output_wav: Path,
    *,
    wake_word: str,
    prerequisite_phrase: str,
    injection_text: str,
    wake_gap_ms: int,
    delay_after_command_ms: int,
    tail_observe_ms: int,
) -> Dict[str, Any]:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    combined = bytearray()
    steps: List[Dict[str, Any]] = []
    steps.append(append_tts(combined, wake_word))
    steps.append(append_silence(combined, wake_gap_ms))
    command_step = append_tts(combined, prerequisite_phrase)
    steps.append(command_step)
    steps.append(append_silence(combined, delay_after_command_ms))
    injection_step = append_tts(combined, injection_text)
    steps.append(injection_step)
    steps.append(append_silence(combined, tail_observe_ms))

    with wave.open(str(output_wav), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(combined))

    manifest = {
        "output_wav": str(output_wav),
        "wake_word": wake_word,
        "prerequisite_phrase": prerequisite_phrase,
        "injection_text": injection_text,
        "wake_gap_ms": wake_gap_ms,
        "delay_after_command_ms": delay_after_command_ms,
        "tail_observe_ms": tail_observe_ms,
        "duration_ms": pcm_duration_ms(combined),
        "command_start_ms": command_step["start_ms"],
        "command_end_ms": command_step["end_ms"],
        "injection_start_ms": injection_step["start_ms"],
        "injection_end_ms": injection_step["end_ms"],
        "steps": steps,
    }
    output_wav.with_suffix(".json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def collect_logs(session_dir: Path, start: datetime, end: datetime, output_dir: Path) -> Dict[str, List[str]]:
    logs: Dict[str, List[str]] = {}
    logs_dir = output_dir / "window_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    for port in configured_log_ports():
        lines = read_lines_between(port, start, end, session_dir=session_dir)
        logs[port] = lines
        (logs_dir / f"{port}.log").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    add_canonical_log_aliases(logs)
    return logs


def parse_ts(line: str) -> Optional[datetime]:
    try:
        return parse_prefixed_timestamp(line)
    except Exception:
        return None


def lines_between(lines: Iterable[str], start: datetime, end: datetime) -> List[str]:
    found: List[str] = []
    for line in lines:
        ts = parse_ts(line)
        if ts is not None and start <= ts <= end:
            found.append(line)
    return found


def count_matching(lines: Iterable[str], regex: re.Pattern[str], start: datetime, end: datetime) -> int:
    return sum(1 for line in lines_between(lines, start, end) if regex.search(line))


def extract_asr_texts(lines: Iterable[str], start: datetime, end: datetime) -> List[str]:
    texts: List[str] = []
    for line in lines_between(lines, start, end):
        match = ASR_TEXT_RE.search(line)
        if match:
            texts.append(match.group(1).strip())
    return texts


def extract_cp_command_keywords(lines: Iterable[str], start: datetime, end: datetime) -> List[str]:
    keywords: List[str] = []
    for line in lines_between(lines, start, end):
        match = CP_CMD_KEYWORD_RE.search(line)
        if match:
            keyword = match.group(1).strip()
            if keyword and keyword not in keywords:
                keywords.append(keyword)
    return keywords


def analyze_interrupt(
    output_dir: Path,
    manifest: Dict[str, Any],
    selected: Dict[str, Any],
    playback: Dict[str, Any],
    raw_logs: Dict[str, List[str]],
    *,
    kind: str,
    guard_ms: int,
) -> Dict[str, Any]:
    clean_logs = sanitize_logs(raw_logs)
    window_summary = summarize_window(clean_logs)
    metrics = collect_metrics(clean_logs, window_summary)
    playback_started_at = datetime.fromisoformat(str(playback["playback_started_at"]))
    injection_start = playback_started_at + timedelta(milliseconds=int(manifest["injection_start_ms"]))
    injection_end = playback_started_at + timedelta(milliseconds=int(manifest["injection_end_ms"]))
    eval_start = injection_start - timedelta(milliseconds=800)
    eval_end = injection_end + timedelta(milliseconds=5000)

    ap_starts, ap_stops = build_events(clean_logs.get("COM14", []), "COM14")
    wb_starts, wb_stops = build_wb_events(clean_logs.get("COM13", []), "COM13")
    windows = pair_windows(ap_starts, ap_stops, max_duration_ms=30000) + pair_windows(wb_starts, wb_stops, max_duration_ms=30000)
    containing = [
        item
        for item in windows
        if item.start + timedelta(milliseconds=guard_ms) <= injection_start <= item.end - timedelta(milliseconds=guard_ms)
    ]
    nearby = [
        item
        for item in windows
        if item.start - timedelta(milliseconds=1000) <= injection_start <= item.end + timedelta(milliseconds=1000)
    ]
    evidence = {
        "cp_wake_after_injection": count_matching(clean_logs.get("COM12", []), CP_WAKE_RE, eval_start, eval_end),
        "ap_wake_after_injection": count_matching(clean_logs.get("COM14", []), AP_WAKE_RE, eval_start, eval_end),
        "asr_wake_after_injection": count_matching(clean_logs.get("COM13", []), ASR_WAKE_RE, eval_start, eval_end),
        "asr_texts_after_injection": extract_asr_texts(clean_logs.get("COM14", []), eval_start, eval_end)
        + extract_asr_texts(clean_logs.get("COM13", []), eval_start, eval_end),
        "cp_command_keywords_after_injection": extract_cp_command_keywords(clean_logs.get("COM12", []), eval_start, eval_end),
        "interrupt_reset_count": metrics.get("interrupt_reset_count", 0),
    }
    playback_returncode = int(playback.get("returncode", -1))
    if playback_returncode != 0:
        result = "BLOCKED"
        attribution = "audio_playback_or_device_key"
        reason = f"注入音频播放失败，returncode={playback_returncode}。"
    elif not containing:
        result = "TIMING_AMBIGUOUS"
        attribution = "injection_not_inside_self_play_window"
        reason = "计划注入点未稳定落在自播 start/end 保护窗口内，不能判固件打断失败。"
    elif kind == "wake" and evidence["cp_wake_after_injection"] + evidence["ap_wake_after_injection"] + evidence["asr_wake_after_injection"] > 0:
        result = "PASS"
        attribution = "pass"
        reason = "注入点位于自播窗口内，注入后观察到唤醒证据。"
    elif kind == "command" and (evidence["asr_texts_after_injection"] or evidence["cp_command_keywords_after_injection"]):
        result = "PASS"
        attribution = "pass"
        reason = (
            "注入点位于自播窗口内，注入后观察到识别/命令证据："
            f"ASR={evidence['asr_texts_after_injection']}，CP={evidence['cp_command_keywords_after_injection']}。"
        )
    else:
        result = "FAIL"
        attribution = "firmware_or_device_interrupt"
        reason = "注入点位于自播窗口内，但注入后未观察到期望唤醒/识别证据。"

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "result": result,
        "attribution": attribution,
        "reason": reason,
        "selected_prerequisite": selected,
        "manifest": {**manifest, "output_wav": rel(Path(manifest["output_wav"]))},
        "playback": playback,
        "timing": {
            "playback_started_at": playback_started_at.isoformat(timespec="milliseconds"),
            "planned_injection_start": injection_start.isoformat(timespec="milliseconds"),
            "planned_injection_end": injection_end.isoformat(timespec="milliseconds"),
            "guard_ms": guard_ms,
            "containing_self_play_windows": [window_to_payload(item) for item in containing],
            "nearby_self_play_windows": [window_to_payload(item) for item in nearby[:5]],
        },
        "evidence": evidence,
        "metrics": metrics,
    }
    write_json(output_dir / "interrupt_injection_result.json", payload)
    write_injection_report(output_dir / "interrupt_injection_report.md", payload)
    return payload


def write_injection_report(path: Path, payload: Dict[str, Any]) -> None:
    timing = payload["timing"]
    evidence = payload["evidence"]
    lines = [
        "# 打断注入执行报告",
        "",
        f"- 生成时间：`{payload.get('generated_at')}`",
        f"- 类型：`{payload.get('kind')}`",
        f"- 结论：`{payload.get('result')}`",
        f"- 归因：`{payload.get('attribution')}`",
        f"- 原因：{payload.get('reason')}",
        f"- 前置候选：`{payload.get('selected_prerequisite', {}).get('phrase', '')}`",
        f"- 注入时间：`{timing.get('planned_injection_start')}`",
        f"- 命中自播窗口数：`{len(timing.get('containing_self_play_windows', []))}`",
        "",
        "## 注入后证据",
        "",
        f"- CP wake：`{evidence.get('cp_wake_after_injection')}`",
        f"- AP wake：`{evidence.get('ap_wake_after_injection')}`",
        f"- ASR wake：`{evidence.get('asr_wake_after_injection')}`",
        f"- ASR texts：`{json.dumps(evidence.get('asr_texts_after_injection', []), ensure_ascii=False)}`",
        f"- CP command keywords：`{json.dumps(evidence.get('cp_command_keywords_after_injection', []), ensure_ascii=False)}`",
        f"- player reset：`{evidence.get('interrupt_reset_count')}`",
        "",
        "## 断言口径",
        "",
        "- `TIMING_AMBIGUOUS` 表示注入未可靠落在自播窗口内，只能说明时序需要重跑或调整，不能算固件 FAIL。",
        "- 只有自播窗口命中且注入后缺少目标证据时，才归因到固件/设备打断能力。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_windows_csv(path: Path, windows: List[Dict[str, Any]]) -> None:
    if not windows:
        return
    fields = ["source", "start", "end", "duration_ms", "start_kind", "stop_kind", "url"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in windows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a wake/command interruption injection using measured prerequisite timing.")
    parser.add_argument("--kind", choices=["wake", "command"], default="wake")
    parser.add_argument("--selected-file", type=Path, default=None)
    parser.add_argument("--device-key", default=DEFAULT_DEVICE_KEY)
    parser.add_argument("--wake-word", default=DEFAULT_WAKE_WORD)
    parser.add_argument("--injection-text", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--wake-gap-ms", type=int, default=900)
    parser.add_argument("--tail-observe-ms", type=int, default=7000)
    parser.add_argument("--fallback-response-start-ms", type=int, default=7500)
    parser.add_argument("--fallback-injection-offset-ms", type=int, default=1800)
    parser.add_argument("--timing-advance-ms", type=int, default=1200, help="提前注入以抵消自播起点抖动，避免压到播报尾部")
    parser.add_argument("--guard-ms", type=int, default=600)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    selected_file = args.selected_file or latest_selected_file()
    if selected_file is None or not selected_file.exists():
        raise SystemExit("未找到 selected_interrupt_prerequisite.json，请先执行 interrupt_prerequisite_measurement。")
    selected = load_json(selected_file)
    prerequisite_phrase = str(selected.get("phrase", "")).strip()
    if not prerequisite_phrase:
        raise SystemExit("selected_interrupt_prerequisite.json 中缺少 phrase。")
    response_start_delta_ms = int(selected.get("response_start_delta_ms") or args.fallback_response_start_ms)
    injection_offset_ms = int(selected.get("injection_offset_ms") or args.fallback_injection_offset_ms)
    delay_after_command_ms = max(0, response_start_delta_ms + injection_offset_ms - int(args.timing_advance_ms))
    injection_text = args.injection_text.strip() or (args.wake_word if args.kind == "wake" else "打开空调")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_file = output_dir / "audio" / f"interrupt_{args.kind}.wav"
    manifest = build_interrupt_audio(
        audio_file,
        wake_word=args.wake_word,
        prerequisite_phrase=prerequisite_phrase,
        injection_text=injection_text,
        wake_gap_ms=args.wake_gap_ms,
        delay_after_command_ms=delay_after_command_ms,
        tail_observe_ms=args.tail_observe_ms,
    )
    manifest["timing_advance_ms"] = int(args.timing_advance_ms)
    playback = run_playback(audio_file, args.device_key, output_dir, timeout_s=max(120, int(manifest["duration_ms"] / 1000) + 120))
    playback_started_at = datetime.fromisoformat(str(playback["playback_started_at"]))
    finished_at = datetime.fromisoformat(str(playback["finished_at"]))
    session_dir = Path(selected_file).resolve().parents[1] / "session"
    bdd_run_dir = os.environ.get("POLARIS_BDD_RUN_DIR", "").strip()
    if bdd_run_dir:
        session_dir = Path(bdd_run_dir).resolve() / "session"
    elif not session_dir.exists():
        marker = WORKSPACE_ROOT / ".current_result_dir"
        session_dir = Path(marker.read_text(encoding="utf-8").strip()) if marker.exists() else WORKSPACE_ROOT / "result"
    raw_logs = collect_logs(session_dir, playback_started_at - timedelta(seconds=2), finished_at + timedelta(seconds=5), output_dir)
    payload = analyze_interrupt(
        output_dir,
        manifest,
        selected,
        playback,
        raw_logs,
        kind=args.kind,
        guard_ms=args.guard_ms,
    )
    print(output_dir)
    print(json.dumps({"result": payload["result"], "attribution": payload["attribution"]}, ensure_ascii=False))
    return 0 if payload["result"] == "PASS" else (3 if payload["result"] == "TIMING_AMBIGUOUS" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
