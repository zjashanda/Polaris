#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tools.core.polaris_runtime import current_session_dir, new_artifact_dir, queue_command, read_lines_between


ROOT = Path(__file__).resolve().parents[2]

from doc.api.common_request import MideaCloudRequest  # noqa: E402


FIELD_MAP = {
    "SN": "sn",
    "IoT ID": "iot_id",
    "Mac": "mac",
    "IP": "ip",
    "WakeupID": "wakeup_id",
    "ClientID": "client_id",
    "ClientSec": "client_sec",
}


def now_iso_ms() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def load_env_label() -> str:
    env_path = ROOT / "config" / "polaris_env.json"
    if not env_path.exists():
        return "sit"
    payload = json.loads(env_path.read_text(encoding="utf-8"))
    label = str(payload.get("current_env_label", "sit")).strip().lower()
    if label in {"sit", "uat", "pro"}:
        return label
    return "sit"


def load_env_payload() -> Dict[str, Any]:
    env_path = ROOT / "config" / "polaris_env.json"
    if not env_path.exists():
        return {}
    return json.loads(env_path.read_text(encoding="utf-8"))


def normalize_log_line(line: str) -> str:
    if len(line) > 24 and "] " in line:
        parts = line.split("] ", 1)
        if len(parts) == 2:
            return parts[1]
    return line


def parse_deviceinfo(lines: List[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for raw in lines:
        clean = normalize_log_line(raw).strip()
        for prefix, key in FIELD_MAP.items():
            token = f"{prefix}:"
            if clean.startswith(token):
                result[key] = clean.split(token, 1)[1].strip()
    return result


def merge_deviceinfo_with_env(deviceinfo: Dict[str, str]) -> Dict[str, str]:
    merged = dict(deviceinfo)
    env_payload = load_env_payload()
    current_deviceinfo = env_payload.get("current_deviceinfo", {}) or {}
    fallback_keys = ("sn", "iot_id", "mac", "wakeup_id")
    for key in fallback_keys:
        if merged.get(key):
            continue
        value = str(current_deviceinfo.get(key, "")).strip()
        if value:
            merged[key] = value
    if not merged.get("wakeup_id"):
        for key in ("wakeupid_from_deviceinfo", "current_wakeup_word"):
            value = str(env_payload.get(key, "")).strip()
            if value:
                merged["wakeup_id"] = value
                break
    return merged


def capture_deviceinfo(session_dir: Path, timeout_s: float = 4.0) -> Dict[str, Any]:
    start_dt = datetime.now()
    queue_command("COM14", "deviceinfo", session_dir=session_dir)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        lines = read_lines_between("COM14", start_dt, session_dir=session_dir)
        merged = "\n".join(lines)
        if "Device Info:" in merged and "WakeupID:" in merged:
            time.sleep(0.3)
            break
        time.sleep(0.2)
    end_dt = datetime.now()
    lines = read_lines_between("COM14", start_dt, end_dt, session_dir=session_dir)
    info = merge_deviceinfo_with_env(parse_deviceinfo(lines))
    return {
        "started_at": start_dt.isoformat(timespec="milliseconds"),
        "ended_at": end_dt.isoformat(timespec="milliseconds"),
        "lines": lines,
        "parsed": info,
    }


def response_to_dict(response: Any) -> Dict[str, Any]:
    if response is None:
        return {
            "ok": False,
            "status_code": None,
            "elapsed_s": None,
            "text": "",
            "url": None,
        }
    elapsed_s = None
    try:
        elapsed_s = response.elapsed.total_seconds()
    except Exception:
        elapsed_s = None
    return {
        "ok": bool(getattr(response, "ok", False)),
        "status_code": getattr(response, "status_code", None),
        "elapsed_s": elapsed_s,
        "text": getattr(response, "text", ""),
        "url": getattr(response, "url", None),
    }


def collect_log_excerpt(
    session_dir: Path,
    start_dt: datetime,
    end_dt: datetime,
    port: str,
    keywords: List[str],
) -> List[str]:
    lines = read_lines_between(port, start_dt, end_dt, session_dir=session_dir)
    if not keywords:
        return lines
    lowered = [item.lower() for item in keywords]
    result: List[str] = []
    for line in lines:
        text = line.lower()
        if any(keyword in text for keyword in lowered):
            result.append(line)
    return result


def build_request(deviceinfo: Dict[str, str]) -> MideaCloudRequest:
    device_id = deviceinfo.get("iot_id")
    if not device_id:
        raise RuntimeError("deviceinfo did not return IoT ID")
    return MideaCloudRequest(int(device_id), environment=load_env_label())


def action_probe(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return None


def action_set_full_duplex(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.fullDuplex_switch_new(onoroff=int(args.enable), timeOut=int(args.timeout))


def action_set_volume(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.set_volume(value=int(args.value))


def action_set_multi_wakeup(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.multi_wakeup_switch(enable=int(args.enable))


def action_set_accent(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.accent_switch(
        accentId=str(args.accent_id),
        enableAccent=int(args.enable_accent),
        mixedResEnable=int(args.mixed_res_enable),
    )


def action_set_wakeup_word(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.wakeup_switch(str(args.word))


def action_set_wakeup_threshold(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.wakeup_Threshold_switch(int(args.threshold))


def action_set_log(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.log_set(status=int(args.status), logLevel=int(args.level))


def action_set_wakeup_audio_upload(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.wakeupAudio_upload_new(onoroff=int(args.enable))


def action_set_mic(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.mic_switch(enable=int(args.enable))


def action_set_night_mode(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.night_mode(
        enable=int(args.enable),
        timeFrom=str(args.time_from),
        timeTo=str(args.time_to),
        volume=int(args.volume),
        awakeThreshold=int(args.awake_threshold),
    )


def action_set_character_value(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.characterValue_switch(voice_type=str(args.voice_type))


def action_proactive_interaction(request: MideaCloudRequest, args: argparse.Namespace) -> Any:
    return request.Proactive_interaction(
        interrupt="True" if args.interrupt else "False",
        # doc/common_request.py expects the legacy typo "Ture" for truthy flags.
        endssion="Ture" if args.end_session else "False",
        tts_long="Ture" if args.tts_long else "False",
    )


ACTION_TABLE: Dict[str, Dict[str, Any]] = {
    "probe-device": {
        "handler": action_probe,
        "keywords": ["deviceinfo", "iot id", "clientid", "clientsec"],
    },
    "set-full-duplex": {
        "handler": action_set_full_duplex,
        "keywords": ["fullduplex", "voiceconfig", "fullduplex", "cloud.instructions", "recv ai"],
    },
    "set-volume": {
        "handler": action_set_volume,
        "keywords": ["volume", "cloud.instructions", "recv ai"],
    },
    "set-multi-wakeup": {
        "handler": action_set_multi_wakeup,
        "keywords": ["multi", "wakeup", "cloud.instructions", "recv ai"],
    },
    "set-accent": {
        "handler": action_set_accent,
        "keywords": ["accent", "cloud.instructions", "recv ai"],
    },
    "set-wakeup-word": {
        "handler": action_set_wakeup_word,
        "keywords": ["wakeup", "wake", "cloud.instructions", "recv ai"],
    },
    "set-wakeup-threshold": {
        "handler": action_set_wakeup_threshold,
        "keywords": ["threshold", "awake", "cloud.instructions", "recv ai"],
    },
    "set-log": {
        "handler": action_set_log,
        "keywords": ["log", "cloud.instructions", "recv ai"],
    },
    "set-wakeup-audio-upload": {
        "handler": action_set_wakeup_audio_upload,
        "keywords": ["wakeup", "audio", "upload", "cloud.instructions", "recv ai"],
    },
    "set-mic": {
        "handler": action_set_mic,
        "keywords": ["mic", "cloud.instructions", "recv ai"],
    },
    "set-night-mode": {
        "handler": action_set_night_mode,
        "keywords": ["night", "mode", "cloud.instructions", "recv ai"],
    },
    "set-character-value": {
        "handler": action_set_character_value,
        "keywords": ["voice", "character", "cloud.instructions", "recv ai"],
    },
    "proactive-interaction": {
        "handler": action_proactive_interaction,
        "keywords": ["proactive", "cloud.instructions", "recv ai"],
    },
}


def write_text(path: Path, lines: List[str]) -> None:
    text = "\n".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def save_summary(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polaris app-side cloud control helper")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("probe-device", help="Read deviceinfo and print the latest device identity")

    full = sub.add_parser("set-full-duplex", help="Set full-duplex switch and timeout via cloud")
    full.add_argument("--enable", type=int, choices=[0, 1], required=True)
    full.add_argument("--timeout", type=int, required=True)

    volume = sub.add_parser("set-volume", help="Set volume via cloud")
    volume.add_argument("--value", type=int, required=True)

    multi = sub.add_parser("set-multi-wakeup", help="Set multi-wakeup via cloud")
    multi.add_argument("--enable", type=int, choices=[0, 1], required=True)

    accent = sub.add_parser("set-accent", help="Set accent via cloud")
    accent.add_argument("--accent-id", required=True)
    accent.add_argument("--enable-accent", type=int, choices=[0, 1], required=True)
    accent.add_argument("--mixed-res-enable", type=int, choices=[0, 1], required=True)

    wake_word = sub.add_parser("set-wakeup-word", help="Set wakeup word via cloud")
    wake_word.add_argument("--word", required=True)

    wake_th = sub.add_parser("set-wakeup-threshold", help="Set wakeup threshold via cloud")
    wake_th.add_argument("--threshold", type=int, required=True)

    log_set = sub.add_parser("set-log", help="Set cloud log upload status and level")
    log_set.add_argument("--status", type=int, choices=[0, 1], required=True)
    log_set.add_argument("--level", type=int, required=True)

    wake_audio = sub.add_parser("set-wakeup-audio-upload", help="Set wakeup audio upload via cloud")
    wake_audio.add_argument("--enable", type=int, choices=[0, 1], required=True)

    mic = sub.add_parser("set-mic", help="Set mic on/off via cloud")
    mic.add_argument("--enable", type=int, choices=[0, 1], required=True)

    night = sub.add_parser("set-night-mode", help="Set night mode via cloud")
    night.add_argument("--enable", type=int, choices=[0, 1], required=True)
    night.add_argument("--time-from", default="09:00")
    night.add_argument("--time-to", default="18:00")
    night.add_argument("--volume", type=int, default=0)
    night.add_argument("--awake-threshold", type=int, default=0)

    voice = sub.add_parser("set-character-value", help="Set TTS/character voice type via cloud")
    voice.add_argument("--voice-type", required=True)

    proactive = sub.add_parser("proactive-interaction", help="Trigger proactive interaction via cloud")
    proactive.add_argument("--interrupt", action="store_true")
    proactive.add_argument("--end-session", action="store_true")
    proactive.add_argument("--tts-long", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    session_dir = current_session_dir(ROOT)
    artifact_dir = new_artifact_dir(f"app_control_{args.action.replace('-', '_')}", session_dir=session_dir)

    deviceinfo_capture = capture_deviceinfo(session_dir)
    deviceinfo = deviceinfo_capture["parsed"]
    write_text(artifact_dir / "deviceinfo.log", deviceinfo_capture["lines"])
    save_summary(artifact_dir / "deviceinfo.json", deviceinfo)

    start_dt = datetime.now()
    response = None
    action_meta = ACTION_TABLE[args.action]
    if args.action != "probe-device":
        request = build_request(deviceinfo)
        response = action_meta["handler"](request, args)
        time.sleep(2.0)
    end_dt = datetime.now()

    keywords = action_meta["keywords"]
    ap_window = read_lines_between("COM14", start_dt, end_dt, session_dir=session_dir)
    wb_window = read_lines_between("COM13", start_dt, end_dt, session_dir=session_dir)
    ap_excerpt = collect_log_excerpt(session_dir, start_dt, end_dt, "COM14", keywords)
    wb_excerpt = collect_log_excerpt(session_dir, start_dt, end_dt, "COM13", keywords)
    write_text(artifact_dir / "COM14_window.log", ap_window)
    write_text(artifact_dir / "COM13_window.log", wb_window)
    write_text(artifact_dir / "COM14_excerpt.log", ap_excerpt)
    write_text(artifact_dir / "COM13_excerpt.log", wb_excerpt)

    response_dict = response_to_dict(response)
    save_summary(artifact_dir / "response.json", response_dict)

    payload = {
        "artifact_dir": str(artifact_dir),
        "action": args.action,
        "args": vars(args),
        "env": load_env_label(),
        "deviceinfo": deviceinfo,
        "response": response_dict,
        "ap_window_count": len(ap_window),
        "wb_window_count": len(wb_window),
        "ap_excerpt_count": len(ap_excerpt),
        "wb_excerpt_count": len(wb_excerpt),
        "started_at": start_dt.isoformat(timespec="milliseconds"),
        "ended_at": end_dt.isoformat(timespec="milliseconds"),
    }
    save_summary(artifact_dir / "summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
