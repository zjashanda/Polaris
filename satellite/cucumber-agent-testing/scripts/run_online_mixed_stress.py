#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Randomized online-interaction stress for Polaris projects.

The runner keeps AP/CP/ASR serial readers open from the beginning and stores full
logs. It mixes wake + online command/music/crosstalk/news/cooking/encyclopedia
phrases with random gaps to look for reboot, crash, serial silence, playback
failures, and missing wake/ASR/TTS evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import serial


SCRIPT_DIR = Path(__file__).resolve().parent
BDD_ROOT = SCRIPT_DIR.parents[0]
ROOT = SCRIPT_DIR.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from polaris_env import load_env_payload, resolve_env_path  # noqa: E402
from tools.audio.polaris_audio_builder import build_sequence  # noqa: E402


DEFAULT_STRATEGY = BDD_ROOT / "references" / "scene_strategy_pool.json"
AP_WAKE_RE = re.compile(r"(Pre Wakeup|wakeup_callback|multi_allow_wakeup_callback|mark has wakeup)", re.I)
CP_WAKE_RE = re.compile(r"\bWAKE\(1\)", re.I)
ASR_WAKE_RE = re.compile(r"\bonline_wakeup\b|offline_wakeup|wakeup", re.I)
ANY_WAKE_RE = re.compile(r"(Pre Wakeup|wakeup_callback|online_wakeup|multi_allow_wakeup_callback|mark has wakeup)", re.I)
ASR_RE = re.compile(r"((?:online|offline)_asr_callbak|MSpeech Cloud 3 evt|cloud asr with|Recv .* ASR|recognizer start)", re.I)
ASR_TEXT_RE = re.compile(r"(?:online|offline)_asr_callbak,\s*(?:text|keyword):\s*(.+)$", re.I)
CLOUD_ASR_TEXT_RE = re.compile(r'"asr"\s*:\s*"([^"]*)"', re.I)
CP_COMMAND_KEYWORD_RE = re.compile(r"WAKE\(0\).*?KEY=\d+\(([^)]*)\)", re.I)
ALGO_COMMAND_KEYWORD_RE = re.compile(r'"keyword"\s*:\s*"([^"]*)"', re.I)
LOCAL_ASR_KEYWORD_RE = re.compile(r"ignore local asr\s+(.+?)\s+when cloud connected", re.I)
PUNCT_OR_SPACE_RE = re.compile(r"[\s，。！？、,.!?:：;；\"'“”‘’（）()\[\]{}<>《》]+")
TTS_RE = re.compile(r"(TTS playing|TTS recv|ttsplayer play|wakeup_tts_callback|shortplayer status|cloud\.instructions\.audioBroadcast|tone player)", re.I)
CLOUD_REPLY_RE = re.compile(r"(cloud\.speech\.reply|cloud\.instructions|MSpeech Cloud 4 evt|MSpeech Cloud 32 evt)", re.I)
MEDIA_PLAY_RE = re.compile(r"(ttsplayer play|play audio https?://|player\".*\"status\":\"play\"|ttsplayer report state: play|TTS playing)", re.I)
MEDIA_STOP_RE = re.compile(r"(player\".*\"status\":\"stop\"|ttsplayer report state: stop|PLAYBACK_COMPLETE|ttsplayer status:\s*6)", re.I)
MEDIA_ERROR_RE = re.compile(
    r"(\[E\]\s*\[http\].*(recv timeout|retry|fail|error)|"
    r"\[HTTPC\]\[ERR\]|"
    r"\[W\]\s*\[http_retry\].*(read_failed|retry)|"
    r"\b(http|https).*(download|demux|play).*(fail|error|timeout)|"
    r"\b(demux|download|decoder|player).*(fail|error|timeout))",
    re.I,
)
BOOT_RE = re.compile(
    r"(Boot Reason|boot reason|ListenAI .*BOOT|RESET=|ASSERT|panic|fatal|watchdog|hard fault|exception|will reboot device|reboot_reason)",
    re.I,
)
BOOT_IGNORE_RE = re.compile(r"ignore exception", re.I)
SERIAL_ERR_RE = re.compile(r"LOGGER_ERROR", re.I)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def smart_decode(data: bytes) -> str:
    for enc in ("utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_datetime(value: str) -> datetime:
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(raw)


def tomorrow_0830() -> datetime:
    now = datetime.now()
    target = now.replace(hour=8, minute=30, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


@dataclass
class CapturedLine:
    wall: str
    mono: float
    port: str
    name: str
    text: str


@dataclass
class SerialState:
    name: str
    port: str
    baudrate: int
    is_open: bool = False
    line_count: int = 0
    bytes_read: int = 0
    last_error: Optional[str] = None


class SerialReader:
    def __init__(self, name: str, port: str, baudrate: int, log_path: Path) -> None:
        self.name = name
        self.port = port
        self.baudrate = baudrate
        self.log_path = log_path
        self.state = SerialState(name=name, port=port, baudrate=baudrate)
        self.entries: List[CapturedLine] = []
        self._fsync_counter = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._serial: Optional[serial.Serial] = None
        self._handle = None
        self._lock = threading.Lock()
        self._partial = ""

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.log_path.open("w", encoding="utf-8", newline="", buffering=1)
        self._thread = threading.Thread(target=self._run, name=f"online-stress-serial-{self.name}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        try:
            if self._serial is not None and self._serial.is_open:
                self._serial.close()
        finally:
            if self._handle is not None:
                self._handle.close()

    def snapshot_len(self) -> int:
        with self._lock:
            return len(self.entries)

    def since(self, index: int) -> List[CapturedLine]:
        with self._lock:
            return list(self.entries[index:])

    def _write_line(self, line: str) -> None:
        clean = line.replace("\r", "").replace("\x00", "").rstrip("\n")
        if not clean:
            return
        entry = CapturedLine(wall=now_iso(), mono=time.perf_counter(), port=self.port, name=self.name, text=clean)
        with self._lock:
            self.entries.append(entry)
        self.state.line_count += 1
        if self._handle is not None:
            self._handle.write(f"{entry.wall} [{entry.port}/{entry.name}] {entry.text}\n")
            self._handle.flush()
            self._fsync_counter += 1
            if self._fsync_counter % 100 == 0:
                os.fsync(self._handle.fileno())

    def _run(self) -> None:
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.state.is_open = True
            self._write_line(f"[LOGGER] opened {self.port} @ {self.baudrate}")
            while not self._stop.is_set():
                data = self._serial.read(self._serial.in_waiting or 1)
                if not data:
                    continue
                self.state.bytes_read += len(data)
                self._partial += smart_decode(data)
                while "\n" in self._partial:
                    line, self._partial = self._partial.split("\n", 1)
                    self._write_line(line)
            if self._partial:
                self._write_line(self._partial)
                self._partial = ""
        except Exception as exc:
            self.state.last_error = str(exc)
            self._write_line(f"[LOGGER_ERROR] {exc}")


def send_control(port: str, baudrate: int, command: str, log_path: Path, read_s: float = 0.8) -> Dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = now_iso()
    echoed: List[str] = []
    error = None
    try:
        with serial.Serial(port, baudrate, timeout=0.1, write_timeout=1.0) as ser:
            ser.reset_input_buffer()
            ser.write((command.rstrip("\r\n") + "\r\n").encode("utf-8", errors="ignore"))
            ser.flush()
            deadline = time.time() + read_s
            chunks: List[str] = []
            while time.time() < deadline:
                data = ser.read(ser.in_waiting or 1)
                if data:
                    chunks.append(smart_decode(data))
            echoed = [line for line in "".join(chunks).replace("\r", "").split("\n") if line.strip()]
    except Exception as exc:
        error = str(exc)
    with log_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(f"{started} [COMMAND] {command}\n")
        if error:
            handle.write(f"{now_iso()} [ERROR] {error}\n")
        for line in echoed:
            handle.write(f"{now_iso()} [ECHO] {line}\n")
    return {
        "command": command,
        "port": port,
        "baudrate": baudrate,
        "started_at": started,
        "result": "BLOCKED" if error else "PASS",
        "error": error,
        "echo_lines": echoed,
    }


def run_cmd(cmd: List[str], cwd: Path, timeout: Optional[int] = None) -> Dict[str, Any]:
    started = now_iso()
    start_mono = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return {
        "cmd": cmd,
        "started_at": started,
        "duration_s": round(time.perf_counter() - start_mono, 3),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def play_audio(audio_file: Path, device_key: str, skip_probe: bool = True) -> Dict[str, Any]:
    script = Path.home() / ".codex" / "skills" / "listenai-play" / "scripts" / "listenai_play.py"
    cmd = [
        sys.executable,
        str(script),
        "play",
        "--audio-file",
        str(audio_file),
    ]
    if device_key:
        cmd.extend(["--device-key", device_key])
    if skip_probe:
        cmd.append("--skip-probe")
    return run_cmd(cmd, ROOT, timeout=120)


def count_re(entries: Iterable[CapturedLine], regex: re.Pattern[str]) -> int:
    return sum(1 for item in entries if regex.search(item.text))


def sample_re(entries: Iterable[CapturedLine], regex: re.Pattern[str], limit: int = 10) -> List[str]:
    samples: List[str] = []
    for item in entries:
        if regex.search(item.text):
            samples.append(f"{item.wall} [{item.port}/{item.name}] {item.text}")
            if len(samples) >= limit:
                break
    return samples


def is_boot_or_crash_line(text: str) -> bool:
    return bool(BOOT_RE.search(text)) and not BOOT_IGNORE_RE.search(text)


def count_boot_or_crash(entries: Iterable[CapturedLine]) -> int:
    return sum(1 for item in entries if is_boot_or_crash_line(item.text))


def sample_boot_or_crash(entries: Iterable[CapturedLine], limit: int = 10) -> List[str]:
    samples: List[str] = []
    for item in entries:
        if is_boot_or_crash_line(item.text):
            samples.append(f"{item.wall} [{item.port}/{item.name}] {item.text}")
            if len(samples) >= limit:
                break
    return samples


def extract_texts(entries: Iterable[CapturedLine]) -> List[str]:
    values: List[str] = []
    for item in entries:
        match = ASR_TEXT_RE.search(item.text) or CLOUD_ASR_TEXT_RE.search(item.text)
        if match:
            text = match.group(1).strip()
            if text not in values:
                values.append(text)
    return values


def extract_command_keywords(entries: Iterable[CapturedLine]) -> List[str]:
    values: List[str] = []
    for item in entries:
        for regex in (CP_COMMAND_KEYWORD_RE, LOCAL_ASR_KEYWORD_RE, ALGO_COMMAND_KEYWORD_RE):
            match = regex.search(item.text)
            if not match:
                continue
            text = match.group(1).strip()
            if text and text not in values and "xiao mei xiao mei" not in text.lower():
                values.append(text)
    return values


def normalize_recognition_text(text: str) -> str:
    return PUNCT_OR_SPACE_RE.sub("", str(text or "").lower())


def recognition_matches_expected(observed: str, expected_values: Iterable[str]) -> bool:
    observed_norm = normalize_recognition_text(observed)
    if not observed_norm:
        return True
    for expected in expected_values:
        expected_norm = normalize_recognition_text(expected)
        if not expected_norm:
            continue
        if observed_norm == expected_norm or observed_norm in expected_norm or expected_norm in observed_norm:
            return True
    return False


def find_unexpected_texts(observed_values: Iterable[str], expected_values: Iterable[str]) -> List[str]:
    expected_list = list(expected_values)
    unexpected: List[str] = []
    for observed in observed_values:
        text = str(observed or "").strip()
        if not text:
            continue
        if not recognition_matches_expected(text, expected_list) and text not in unexpected:
            unexpected.append(text)
    return unexpected


def entries_to_lines(entries: Iterable[CapturedLine]) -> List[str]:
    return [f"{item.wall} [{item.port}/{item.name}] {item.text}" for item in entries]


class StressRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.run_dir = Path(args.run_dir).resolve() if args.run_dir else (
            BDD_ROOT / "debug" / "online_mixed_stress" / stamp()
        )
        self.logs_dir = self.run_dir / "logs"
        self.audio_dir = self.run_dir / "audio"
        self.rounds_dir = self.run_dir / "rounds"
        self.readers = [
            SerialReader("ap", args.ap_port, args.data_baud, self.logs_dir / f"{args.ap_port}_ap.full.log"),
            SerialReader("asr", args.asr_port, args.data_baud, self.logs_dir / f"{args.asr_port}_asr.full.log"),
        ]
        if args.cp_port:
            self.readers.insert(1, SerialReader("cp", args.cp_port, args.data_baud, self.logs_dir / f"{args.cp_port}_cp.full.log"))
        self.rng = random.Random(args.seed)
        self.results: List[Dict[str, Any]] = []
        self.counts: Dict[str, int] = {}
        self.category_counts: Dict[str, int] = {}
        self.anomaly_counts: Dict[str, int] = {}
        self.control_actions: List[Dict[str, Any]] = []
        self.round_csv_path = self.run_dir / "rounds.csv"
        self.stop_requested = False
        self.dump_indices: Dict[str, int] = {}
        self.strategy = getattr(args, "strategy_payload", {}) or {}
        self.phrases = self._build_phrase_bank()
        self.category_bag_template = self._build_category_bag()
        self.category_bag_cache: Dict[int, List[str]] = {}

    def _build_phrase_bank(self) -> Dict[str, List[str]]:
        strategy_phrases = self.strategy.get("phrases") if isinstance(self.strategy.get("phrases"), dict) else {}
        if strategy_phrases:
            return {str(key): [str(item) for item in value] for key, value in strategy_phrases.items() if isinstance(value, list)}
        return {
            "basic_command": [
                "打开空调",
                "关闭空调",
                "调高温度",
                "调低温度",
                "设置温度到二十六度",
                "打开制冷",
                "打开除湿",
                "打开自动模式",
            ],
            "music": [
                "播放音乐",
                "播放一首歌",
                "播放周杰伦的歌",
                "下一首",
                "暂停播放",
                "继续播放",
                "停止播放",
            ],
            "crosstalk": [
                "播放相声",
                "我想听相声",
                "播放郭德纲的相声",
                "来一段相声",
            ],
            "news": [
                "播放新闻",
                "今天有什么新闻",
                "播报今日新闻",
                "来一段新闻",
                "播放财经新闻",
                "播放体育新闻",
            ],
            "qa_cooking": [
                "红烧肉怎么做",
                "番茄炒蛋怎么做",
                "宫保鸡丁怎么做",
                "土豆丝怎么炒",
                "炒青菜怎么做好吃",
                "水煮鱼怎么做",
            ],
            "qa_encyclopedia": [
                "太阳为什么会发光",
                "长城有多长",
                "地球为什么是圆的",
                "恐龙为什么灭绝了",
                "人工智能是什么",
                "珠穆朗玛峰有多高",
            ],
        }

    def _build_category_bag(self) -> List[str]:
        bag_items = self.strategy.get("bag") if isinstance(self.strategy.get("bag"), list) else []
        result: List[str] = []
        for item in bag_items:
            if not isinstance(item, dict):
                continue
            category = str(item.get("category", "")).strip()
            weight = int(item.get("weight", 0) or 0)
            if category and weight > 0:
                result.extend([category] * weight)
        if result:
            return result
        return (
            ["basic_command"] * 4
            + ["music"] * 3
            + ["crosstalk"] * 3
            + ["news"] * 3
            + ["qa_cooking", "qa_encyclopedia", "combo"]
        )

    def run(self) -> int:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        end_at = parse_datetime(self.args.end_at) if self.args.end_at else tomorrow_0830()
        started_at = datetime.now()
        self._write_metadata(started_at, end_at)
        self._init_csv()
        try:
            self._start_readers()
            preflight = self._preflight()
            if not preflight.get("audio_ready") or not preflight.get("serial_ready"):
                self._write_heartbeat("BLOCKED", end_at, preflight)
                return 2
            self._stress_loop(end_at, preflight)
        finally:
            for reader in self.readers:
                reader.stop()
            self._write_final_summary(started_at, end_at)
        return 0

    def _write_metadata(self, started_at: datetime, end_at: datetime) -> None:
        payload = {
            "project_id": self.args.project_id,
            "pid": os.getpid(),
            "started_at": started_at.isoformat(timespec="seconds"),
            "planned_end_at": end_at.isoformat(timespec="seconds"),
            "run_dir": str(self.run_dir),
            "serial": {
                "ap": f"{self.args.ap_port}@{self.args.data_baud}",
                "cp": f"{self.args.cp_port}@{self.args.data_baud}" if self.args.cp_port else "",
                "asr": f"{self.args.asr_port}@{self.args.data_baud}",
                "control": f"{self.args.control_port}@{self.args.control_baud}",
            },
            "env_file": getattr(self.args, "env_file_resolved", ""),
            "device_key": self.args.device_key,
            "wake_text": self.args.wake_text,
            "random_gap_s": [self.args.min_gap_s, self.args.max_gap_s],
            "observe_s": [self.args.min_observe_s, self.args.max_observe_s],
            "categories": self.phrases,
            "category_strategy": {
                "type": self.strategy.get("mode", "random_balanced_bag"),
                "strategy_name": getattr(self.args, "strategy_name", "online_mixed_stress"),
                "strategy_file": getattr(self.args, "strategy_file", ""),
                "bag_size": len(self.category_bag_template),
                "bag_template": self.category_bag_template,
                "note": "每 16 轮先按配比装袋再随机打散，既随机又保底覆盖命令词、音乐、相声、新闻、问答和组合交互。",
            },
        }
        write_json(self.run_dir / "metadata.json", payload)
        (self.run_dir / "runner.pid").write_text(str(os.getpid()), encoding="utf-8")

    def _init_csv(self) -> None:
        self.round_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.round_csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "round",
                "started_at",
                "finished_at",
                "category",
                "phrase",
                "result",
                "playback_returncode",
                "line_count",
                "ap_wake_count",
                "upper_wake_count",
                "cp_wake_count",
                "asr_wake_count",
                "asr_count",
                "tts_count",
                "cloud_reply_count",
                "media_play_count",
                "media_stop_count",
                "media_error_count",
                "boot_count",
                "serial_error_count",
                "asr_texts",
                "command_keywords",
                "expected_utterances",
                "unexpected_asr_texts",
                "unexpected_recognition_count",
                "observe_s",
                "next_gap_s",
                "reason",
            ])
            writer.writeheader()

    def _start_readers(self) -> None:
        for reader in self.readers:
            reader.start()
        time.sleep(1.2)

    def _preflight(self) -> Dict[str, Any]:
        script = Path.home() / ".codex" / "skills" / "listenai-play" / "scripts" / "listenai_play.py"
        ensure = run_cmd([sys.executable, str(script), "ensure-laid"], ROOT, timeout=60)
        probe_cmd = [sys.executable, str(script), "probe"]
        if self.args.device_key:
            probe_cmd.extend(["--device-key", self.args.device_key])
        probe = run_cmd(probe_cmd, ROOT, timeout=60)
        control_log = self.logs_dir / f"{self.args.control_port}_control.log"
        self.control_actions.append(send_control(self.args.control_port, self.args.control_baud, "uut-pa.on", control_log))
        time.sleep(0.4)
        self.control_actions.append(send_control(self.args.control_port, self.args.control_baud, "pa-enable.set 0 17 0 1", control_log))
        time.sleep(0.4)
        payload = {
            "ensure_laid": ensure,
            "probe": probe,
            "audio_ready": ensure.get("returncode") == 0 and probe.get("returncode") == 0,
            "serial_ready": all(reader.state.is_open for reader in self.readers),
            "control_ready": all(item.get("result") == "PASS" for item in self.control_actions),
            "control_actions": self.control_actions,
        }
        write_json(self.run_dir / "preflight.json", payload)
        return payload

    def _choose_interaction(self, round_index: int) -> Tuple[str, str, List[Dict[str, Any]]]:
        # Randomize each block, while the weighted bag prevents long runs from drifting into mostly Q&A.
        categories = ["basic_command", "music", "crosstalk", "news", "qa_cooking", "qa_encyclopedia"]
        block_index = (round_index - 1) // len(self.category_bag_template)
        offset = (round_index - 1) % len(self.category_bag_template)
        bag = self.category_bag_cache.get(block_index)
        if bag is None:
            bag = list(self.category_bag_template)
            self.rng.shuffle(bag)
            self.category_bag_cache[block_index] = bag
        category = bag[offset]
        if category == "combo":
            first_cat = self.rng.choice(categories)
            second_cat = self.rng.choice([item for item in categories if item != first_cat])
            first = self.rng.choice(self.phrases[first_cat])
            second = self.rng.choice(self.phrases[second_cat])
            mid_gap = self.rng.randint(4500, 11000)
            phrase = f"{first} -> {second}"
            sequence = [
                {"type": "tts", "text": self.args.wake_text},
                {"type": "silence", "duration_ms": self.rng.randint(900, 2200)},
                {"type": "tts", "text": first},
                {"type": "silence", "duration_ms": mid_gap},
                {"type": "tts", "text": self.args.wake_text},
                {"type": "silence", "duration_ms": self.rng.randint(900, 2200)},
                {"type": "tts", "text": second},
            ]
            return category, phrase, sequence
        phrase = self.rng.choice(self.phrases[category])
        sequence = [
            {"type": "tts", "text": self.args.wake_text},
            {"type": "silence", "duration_ms": self.rng.randint(900, 2400)},
            {"type": "tts", "text": phrase},
        ]
        return category, phrase, sequence

    def _snapshot(self) -> Dict[str, int]:
        return {reader.name: reader.snapshot_len() for reader in self.readers}

    def _entries_since(self, snap: Dict[str, int]) -> List[CapturedLine]:
        entries: List[CapturedLine] = []
        for reader in self.readers:
            entries.extend(reader.since(snap.get(reader.name, 0)))
        entries.sort(key=lambda item: item.mono)
        return entries

    def _metrics(self, entries: List[CapturedLine]) -> Dict[str, Any]:
        ap_entries = [item for item in entries if item.name == "ap"]
        cp_entries = [item for item in entries if item.name == "cp"]
        asr_entries = [item for item in entries if item.name == "asr"]
        return {
            "line_count": len(entries),
            "ap_line_count": len(ap_entries),
            "cp_line_count": len(cp_entries),
            "asr_line_count": len(asr_entries),
            "ap_wake_count": count_re(ap_entries, AP_WAKE_RE),
            "cp_wake_count": count_re(cp_entries, CP_WAKE_RE),
            "asr_wake_count": count_re(asr_entries, ASR_WAKE_RE),
            "any_wake_count": count_re(entries, ANY_WAKE_RE),
            "asr_count": count_re(entries, ASR_RE),
            "tts_count": count_re(entries, TTS_RE),
            "cloud_reply_count": count_re(entries, CLOUD_REPLY_RE),
            "media_play_count": count_re(entries, MEDIA_PLAY_RE),
            "media_stop_count": count_re(entries, MEDIA_STOP_RE),
            "media_error_count": count_re(entries, MEDIA_ERROR_RE),
            "boot_count": count_boot_or_crash(entries),
            "serial_error_count": count_re(entries, SERIAL_ERR_RE),
            "asr_texts": extract_texts(entries),
            "command_keywords": extract_command_keywords(entries),
            "samples": {
                "wake": sample_re(entries, ANY_WAKE_RE),
                "asr": sample_re(entries, ASR_RE),
                "tts": sample_re(entries, TTS_RE),
                "cloud_reply": sample_re(entries, CLOUD_REPLY_RE),
                "media_play": sample_re(entries, MEDIA_PLAY_RE),
                "media_stop": sample_re(entries, MEDIA_STOP_RE),
                "media_error": sample_re(entries, MEDIA_ERROR_RE),
                "boot": sample_boot_or_crash(entries),
                "serial_error": sample_re(entries, SERIAL_ERR_RE),
            },
        }

    def _classify_round(self, playback: Dict[str, Any], metrics: Dict[str, Any]) -> Tuple[str, str]:
        if playback.get("returncode") != 0:
            return "BLOCKED_PLAYBACK", f"播放失败 returncode={playback.get('returncode')}"
        if metrics["serial_error_count"] > 0:
            return "FAIL_SERIAL_ERROR", "串口 reader 出现错误。"
        if metrics["boot_count"] > 0:
            return "FAIL_REBOOT_OR_CRASH", "窗口内观察到 reboot/crash/reset 类标记。"
        if metrics["line_count"] <= 0:
            return "BLOCKED_SERIAL_SILENT", "窗口内没有串口日志。"
        if metrics["ap_wake_count"] <= 0 and metrics["cp_wake_count"] <= 0 and metrics["asr_wake_count"] <= 0:
            return "FAIL_NO_WAKE", "播放成功但没有唤醒 marker。"
        if metrics["asr_count"] <= 0 and not metrics["asr_texts"]:
            return "WARN_NO_ASR", "有唤醒但没有 ASR 文本/云端识别证据。"
        if metrics.get("unexpected_asr_texts"):
            return "WARN_UNEXPECTED_RECOGNITION", "观察到与本轮播放语料不匹配的 ASR 文本，需按误识别复核。"
        if metrics["media_error_count"] > 0:
            return "WARN_MEDIA_ERROR", "有在线响应链路，但窗口内出现媒体/HTTP 播放错误标记。"
        if metrics["cloud_reply_count"] <= 0 and metrics["tts_count"] <= 0 and metrics["media_play_count"] <= 0:
            return "WARN_NO_ONLINE_RESPONSE", "有唤醒/ASR，但缺少 cloud reply/TTS/media 播放证据。"
        return "PASS", "唤醒/ASR/云端响应或媒体播放链路有证据。"

    def _stress_loop(self, end_at: datetime, preflight: Dict[str, Any]) -> None:
        round_index = 0
        while datetime.now() < end_at:
            if self.args.max_rounds and round_index >= self.args.max_rounds:
                break
            round_index += 1
            category, phrase, sequence = self._choose_interaction(round_index)
            observe_s = self.rng.uniform(self.args.min_observe_s, self.args.max_observe_s)
            next_gap_s = self.rng.uniform(self.args.min_gap_s, self.args.max_gap_s)
            round_dir = self.rounds_dir / f"{round_index:05d}_{category}"
            round_dir.mkdir(parents=True, exist_ok=True)
            audio_file = self.audio_dir / f"{round_index:05d}_{category}.wav"
            manifest = build_sequence(sequence, audio_file)
            snap = self._snapshot()
            started_at = now_iso()
            playback = play_audio(audio_file, self.args.device_key, skip_probe=True)
            time.sleep(observe_s)
            entries = self._entries_since(snap)
            metrics = self._metrics(entries)
            expected_utterances = [
                str(item.get("text", "")).strip()
                for item in sequence
                if isinstance(item, dict)
                and item.get("type") == "tts"
                and str(item.get("text", "")).strip()
                and str(item.get("text", "")).strip() != self.args.wake_text
            ]
            metrics["expected_utterances"] = expected_utterances
            metrics["unexpected_asr_texts"] = find_unexpected_texts(metrics.get("asr_texts", []), expected_utterances)
            metrics["unexpected_recognition_count"] = len(metrics["unexpected_asr_texts"])
            result, reason = self._classify_round(playback, metrics)
            payload = {
                "round": round_index,
                "started_at": started_at,
                "finished_at": now_iso(),
                "category": category,
                "phrase": phrase,
                "sequence": sequence,
                "audio_file": str(audio_file),
                "audio_manifest": manifest,
                "observe_s": round(observe_s, 3),
                "next_gap_s": round(next_gap_s, 3),
                "playback": playback,
                "result": result,
                "reason": reason,
                "metrics": metrics,
            }
            self._store_round(round_dir, entries, payload)
            self._record_round(payload)
            if result.startswith("FAIL") or result.startswith("BLOCKED") or result.startswith("WARN"):
                self.anomaly_counts[result] = self.anomaly_counts.get(result, 0) + 1
            if round_index % self.args.summary_every == 0 or result != "PASS":
                self._write_heartbeat("RUNNING", end_at, preflight)
            time.sleep(next_gap_s)
        self._write_heartbeat("FINISHING", end_at, preflight)

    def _store_round(self, round_dir: Path, entries: List[CapturedLine], payload: Dict[str, Any]) -> None:
        self._append_full_log_mirror()
        write_json(round_dir / "result.json", payload)
        if payload["result"] != "PASS" or payload["round"] % self.args.sample_window_every == 0:
            (round_dir / "window.log").write_text("\n".join(entries_to_lines(entries)) + ("\n" if entries else ""), encoding="utf-8")

    def _append_full_log_mirror(self) -> None:
        """Persist new in-memory serial entries again at round boundaries.

        The primary full logs are written directly by each serial thread. This
        mirror gives us a second complete-on-round-boundary copy so a mid-run
        crash does not hide prior serial evidence.
        """
        for reader in self.readers:
            start = self.dump_indices.get(reader.name, 0)
            new_entries = reader.since(start)
            if not new_entries:
                continue
            mirror = self.logs_dir / f"{reader.port}_{reader.name}.full.mirror.log"
            with mirror.open("a", encoding="utf-8", newline="") as handle:
                for line in entries_to_lines(new_entries):
                    handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.dump_indices[reader.name] = start + len(new_entries)

    def _record_round(self, payload: Dict[str, Any]) -> None:
        self.results.append(payload)
        result = payload["result"]
        category = payload["category"]
        self.counts[result] = self.counts.get(result, 0) + 1
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        metrics = payload["metrics"]
        with self.round_csv_path.open("a", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "round",
                "started_at",
                "finished_at",
                "category",
                "phrase",
                "result",
                "playback_returncode",
                "line_count",
                "ap_wake_count",
                "upper_wake_count",
                "cp_wake_count",
                "asr_wake_count",
                "asr_count",
                "tts_count",
                "cloud_reply_count",
                "media_play_count",
                "media_stop_count",
                "media_error_count",
                "boot_count",
                "serial_error_count",
                "asr_texts",
                "command_keywords",
                "expected_utterances",
                "unexpected_asr_texts",
                "unexpected_recognition_count",
                "observe_s",
                "next_gap_s",
                "reason",
            ])
            writer.writerow({
                "round": payload["round"],
                "started_at": payload["started_at"],
                "finished_at": payload["finished_at"],
                "category": category,
                "phrase": payload["phrase"],
                "result": result,
                "playback_returncode": payload["playback"].get("returncode"),
                "line_count": metrics.get("line_count"),
                "ap_wake_count": metrics.get("ap_wake_count"),
                "upper_wake_count": metrics.get("asr_wake_count"),
                "cp_wake_count": metrics.get("cp_wake_count"),
                "asr_wake_count": metrics.get("asr_wake_count"),
                "asr_count": metrics.get("asr_count"),
                "tts_count": metrics.get("tts_count"),
                "cloud_reply_count": metrics.get("cloud_reply_count"),
                "media_play_count": metrics.get("media_play_count"),
                "media_stop_count": metrics.get("media_stop_count"),
                "media_error_count": metrics.get("media_error_count"),
                "boot_count": metrics.get("boot_count"),
                "serial_error_count": metrics.get("serial_error_count"),
                "asr_texts": "|".join(metrics.get("asr_texts") or []),
                "command_keywords": "|".join(metrics.get("command_keywords") or []),
                "expected_utterances": "|".join(metrics.get("expected_utterances") or []),
                "unexpected_asr_texts": "|".join(metrics.get("unexpected_asr_texts") or []),
                "unexpected_recognition_count": metrics.get("unexpected_recognition_count", 0),
                "observe_s": payload["observe_s"],
                "next_gap_s": payload["next_gap_s"],
                "reason": payload["reason"],
            })

    def _summary_payload(self, status: str, end_at: datetime, preflight: Dict[str, Any]) -> Dict[str, Any]:
        elapsed_s = None
        if self.results:
            try:
                first = parse_datetime(self.results[0]["started_at"])
                elapsed_s = round((datetime.now() - first).total_seconds(), 1)
            except Exception:
                pass
        total_boot = sum(int((item.get("metrics") or {}).get("boot_count", 0) or 0) for item in self.results)
        total_serial_err = sum(int((item.get("metrics") or {}).get("serial_error_count", 0) or 0) for item in self.results)
        total_unexpected = sum(int((item.get("metrics") or {}).get("unexpected_recognition_count", 0) or 0) for item in self.results)
        recent = [
            {
                "round": item["round"],
                "category": item["category"],
                "phrase": item["phrase"],
                "result": item["result"],
                "reason": item["reason"],
                "unexpected_asr_texts": (item.get("metrics") or {}).get("unexpected_asr_texts", []),
            }
            for item in self.results[-10:]
        ]
        return {
            "project_id": self.args.project_id,
            "status": status,
            "pid": os.getpid(),
            "run_dir": str(self.run_dir),
            "updated_at": now_iso(),
            "planned_end_at": end_at.isoformat(timespec="seconds"),
            "round_count": len(self.results),
            "elapsed_s": elapsed_s,
            "result_counts": self.counts,
            "category_counts": self.category_counts,
            "anomaly_counts": self.anomaly_counts,
            "total_boot_or_crash_markers": total_boot,
            "total_serial_error_markers": total_serial_err,
            "total_unexpected_recognition_count": total_unexpected,
            "serial_states": [asdict(reader.state) for reader in self.readers],
            "preflight": {
                "audio_ready": preflight.get("audio_ready"),
                "serial_ready": preflight.get("serial_ready"),
                "control_ready": preflight.get("control_ready"),
            },
            "recent_rounds": recent,
        }

    def _write_heartbeat(self, status: str, end_at: datetime, preflight: Dict[str, Any]) -> None:
        payload = self._summary_payload(status, end_at, preflight)
        write_json(self.run_dir / "heartbeat.json", payload)
        write_json(self.run_dir / "summary_live.json", payload)

    def _write_final_summary(self, started_at: datetime, end_at: datetime) -> None:
        self._append_full_log_mirror()
        total_unexpected = sum(int((item.get("metrics") or {}).get("unexpected_recognition_count", 0) or 0) for item in self.results)
        unexpected_rounds = [
            {
                "round": item.get("round"),
                "category": item.get("category"),
                "phrase": item.get("phrase"),
                "unexpected_asr_texts": (item.get("metrics") or {}).get("unexpected_asr_texts", []),
            }
            for item in self.results
            if int((item.get("metrics") or {}).get("unexpected_recognition_count", 0) or 0) > 0
        ]
        payload = {
            "project_id": self.args.project_id,
            "status": "FINISHED",
            "pid": os.getpid(),
            "run_dir": str(self.run_dir),
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "planned_end_at": end_at.isoformat(timespec="seconds"),
            "round_count": len(self.results),
            "result_counts": self.counts,
            "category_counts": self.category_counts,
            "anomaly_counts": self.anomaly_counts,
            "total_unexpected_recognition_count": total_unexpected,
            "unexpected_recognition_rounds": unexpected_rounds[:200],
            "serial_states": [asdict(reader.state) for reader in self.readers],
            "log_files": [str(reader.log_path) for reader in self.readers],
            "mirror_log_files": [str(self.logs_dir / f"{reader.port}_{reader.name}.full.mirror.log") for reader in self.readers],
            "round_csv": str(self.round_csv_path),
        }
        write_json(self.run_dir / "summary_final.json", payload)
        lines = [
            f"# {self.args.project_id} 在线随机交互压测报告",
            "",
            f"- Run dir: `{self.run_dir}`",
            f"- Started: `{payload['started_at']}`",
            f"- Finished: `{payload['finished_at']}`",
            f"- Planned end: `{payload['planned_end_at']}`",
            f"- Rounds: `{payload['round_count']}`",
            f"- Result counts: `{json.dumps(self.counts, ensure_ascii=False)}`",
            f"- Category counts: `{json.dumps(self.category_counts, ensure_ascii=False)}`",
            f"- Anomaly counts: `{json.dumps(self.anomaly_counts, ensure_ascii=False)}`",
            f"- Unexpected recognition count: `{total_unexpected}`",
            "",
            "## Full Logs",
            "",
        ]
        for reader in self.readers:
            lines.append(f"- `{reader.log_path}`")
        lines.extend(["", "## Round CSV", "", f"- `{self.round_csv_path}`"])
        (self.run_dir / "report_final.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def nested(payload: Dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def read_strategy(path: Path, name: str) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    strategies = payload.get("strategies") if isinstance(payload.get("strategies"), dict) else {}
    strategy = strategies.get(name, {})
    return strategy if isinstance(strategy, dict) else {}


def apply_env_and_strategy_defaults(args: argparse.Namespace) -> argparse.Namespace:
    env_path = resolve_env_path(args.env_file, ROOT)
    env_payload = load_env_payload(env_path)
    ports = nested(env_payload, "serial", "ports")
    if not isinstance(ports, dict):
        ports = {}
    audio = env_payload.get("audio") if isinstance(env_payload.get("audio"), dict) else {}
    device = env_payload.get("device") if isinstance(env_payload.get("device"), dict) else {}
    serial_cfg = env_payload.get("serial") if isinstance(env_payload.get("serial"), dict) else {}

    args.project_id = first_non_empty(args.project, env_payload.get("project_id"), nested(env_payload, "_config_source", "active_project"), "cskwb01")
    args.ap_port = first_non_empty(args.ap_port, ports.get("ap"), "COM14")
    args.cp_port = first_non_empty(args.cp_port, ports.get("cp"), "COM13")
    args.asr_port = first_non_empty(args.asr_port, ports.get("asr"), ports.get("upper"), "COM12")
    args.control_port = first_non_empty(args.control_port, ports.get("control"), "COM15")
    args.data_baud = int(args.data_baud or serial_cfg.get("baudrate") or 115200)
    args.control_baud = int(args.control_baud or serial_cfg.get("control_baudrate") or serial_cfg.get("baudrate") or 115200)
    args.device_key = first_non_empty(args.device_key, audio.get("default_playback_device_key"), env_payload.get("default_playback_device_key"), "")
    args.wake_text = first_non_empty(args.wake_text, device.get("wake_word"), env_payload.get("current_wakeup_word"), "小美小美")
    args.env_file_resolved = str(env_path)

    strategy_path = Path(args.strategy_file) if args.strategy_file else DEFAULT_STRATEGY
    if not strategy_path.is_absolute():
        strategy_path = (ROOT / strategy_path).resolve()
    strategy = read_strategy(strategy_path, args.strategy_name)
    args.strategy_payload = strategy
    args.strategy_file = str(strategy_path)
    gap = strategy.get("random_gap_s", []) if isinstance(strategy.get("random_gap_s"), list) else []
    observe = strategy.get("observe_s", []) if isinstance(strategy.get("observe_s"), list) else []
    args.min_gap_s = float(args.min_gap_s if args.min_gap_s is not None else (gap[0] if len(gap) >= 1 else 6.0))
    args.max_gap_s = float(args.max_gap_s if args.max_gap_s is not None else (gap[1] if len(gap) >= 2 else 28.0))
    args.min_observe_s = float(args.min_observe_s if args.min_observe_s is not None else (observe[0] if len(observe) >= 1 else 18.0))
    args.max_observe_s = float(args.max_observe_s if args.max_observe_s is not None else (observe[1] if len(observe) >= 2 else 42.0))
    return args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Polaris randomized online mixed interaction stress")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--end-at", default="", help="default: next 08:30 local time")
    parser.add_argument("--max-rounds", type=int, default=0)
    parser.add_argument("--env-file", default="", help="默认读取根目录 polaris.local.json")
    parser.add_argument("--project", default="", help="覆盖 project_id；默认使用 env active_project")
    parser.add_argument("--strategy-file", default=str(DEFAULT_STRATEGY))
    parser.add_argument("--strategy-name", default="online_mixed_stress")
    parser.add_argument("--ap-port", default="")
    parser.add_argument("--cp-port", default="")
    parser.add_argument("--asr-port", default="")
    parser.add_argument("--data-baud", type=int, default=0)
    parser.add_argument("--control-port", default="")
    parser.add_argument("--control-baud", type=int, default=0)
    parser.add_argument("--device-key", default="")
    parser.add_argument("--wake-text", default="")
    parser.add_argument("--min-gap-s", type=float, default=None)
    parser.add_argument("--max-gap-s", type=float, default=None)
    parser.add_argument("--min-observe-s", type=float, default=None)
    parser.add_argument("--max-observe-s", type=float, default=None)
    parser.add_argument("--summary-every", type=int, default=5)
    parser.add_argument("--sample-window-every", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260519)
    return parser


def main() -> int:
    args = apply_env_and_strategy_defaults(build_parser().parse_args())
    return StressRunner(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
