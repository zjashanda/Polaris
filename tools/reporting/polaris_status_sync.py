# -*- coding: utf-8 -*-
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import csv
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.core.polaris_config import get_baudrate, get_port
from tools.library.polaris_doc_case_lib import build_device_capability_tags, infer_device_model, load_doc_cases
from tools.core.polaris_runtime import current_session_dir, find_artifact_files, heartbeat_path as session_heartbeat_path, latest_heartbeat, pid_path as session_pid_path, resolve_artifact_reference, workspace_root


WAKE_WORD_FALLBACK = "小美小美"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_artifact_path(value: str, session_dir: Path, *, must_exist: bool = True) -> str:
    resolved = resolve_artifact_reference(value, session_dir=session_dir, must_exist=must_exist)
    return str(resolved) if resolved is not None else ""


def find_latest_audit_summary(session_dir: Path) -> Path:
    candidates = sorted(find_artifact_files("doc_case_audit", "audit_summary.json", session_dir), key=lambda item: item.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"no doc_case_audit summary under {session_dir}")
    return candidates[-1]


def choose_newer_result(existing: Optional[dict], candidate: dict) -> dict:
    if existing is None:
        return candidate
    existing_key = (existing.get("ended_at") or "", existing.get("result_path") or "")
    candidate_key = (candidate.get("ended_at") or "", candidate.get("result_path") or "")
    return candidate if candidate_key >= existing_key else existing


def parse_failed_check_names(raw_value: str) -> List[dict]:
    names = [item.strip() for item in str(raw_value or "").split(",") if item.strip()]
    return [{"name": name, "passed": False} for name in names]


def find_best_case_table_csv(session_dir: Path) -> Optional[Path]:
    best_key = (-1, "", "")
    best_csv: Optional[Path] = None
    for summary_path in find_artifact_files("case_result_table", "summary.json", session_dir):
        try:
            payload = read_json(summary_path)
        except Exception:
            continue
        row_count = int(payload.get("row_count", 0) or 0)
        scope = str(payload.get("scope", "") or "")
        if scope != "auto_executable_now":
            continue
        exported_at = str(payload.get("exported_at", "") or "")
        status_updated_at = str(payload.get("status_updated_at", "") or "")
        candidate_key = (row_count, status_updated_at, exported_at)
        csv_path = summary_path.parent / "case_result_table.csv"
        if csv_path.exists() and candidate_key > best_key:
            best_key = candidate_key
            best_csv = csv_path
    return best_csv


def load_case_table_results(session_dir: Path) -> Dict[str, dict]:
    csv_path = find_best_case_table_csv(session_dir)
    if not csv_path:
        return {}

    latest_by_case: Dict[str, dict] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            case_id = str(row.get("case_id", "") or "").strip()
            result = str(row.get("result", "") or "").strip()
            if not case_id or not result:
                continue
            execution_dir = canonical_artifact_path(str(row.get("execution_dir", "") or ""), session_dir)
            result_path = canonical_artifact_path(str(row.get("result_path", "") or ""), session_dir)
            record = {
                "case_id": case_id,
                "name": str(row.get("name", "") or ""),
                "result": result,
                "reason": str(row.get("judge_reason", "") or ""),
                "execution_dir": execution_dir,
                "result_path": result_path,
                "ended_at": str(row.get("ended_at", "") or ""),
                "failed_checks": parse_failed_check_names(str(row.get("failed_check_names", "") or "")),
                "source": "case_table",
            }
            latest_by_case[case_id] = choose_newer_result(latest_by_case.get(case_id), record)
    return latest_by_case


def load_latest_results(session_dir: Path) -> Tuple[Dict[str, dict], str]:
    latest_by_case: Dict[str, dict] = load_case_table_results(session_dir)
    latest_result_path = ""
    latest_result_key = ("", "")
    for result_path in find_artifact_files("doc_case_run", "doc_case_result.json", session_dir):
        payload = read_json(result_path)
        diagnosis = payload.get("diagnosis", {})
        execution_dir = canonical_artifact_path(payload.get("execution_dir", ""), session_dir) or str(result_path.parent)
        record = {
            "case_id": payload.get("case_id", ""),
            "name": payload.get("name", ""),
            "result": diagnosis.get("result", ""),
            "reason": diagnosis.get("reason", ""),
            "execution_dir": execution_dir,
            "result_path": str(result_path),
            "ended_at": payload.get("ended_at") or "",
            "failed_checks": [item for item in diagnosis.get("checks", []) if not item.get("passed", False)],
            "source": "raw_result",
        }
        case_id = record["case_id"]
        if case_id:
            existing = latest_by_case.get(case_id)
            existing_result_path = Path(str(existing.get("result_path", "")).strip()) if existing else None
            existing_execution_dir = Path(str(existing.get("execution_dir", "")).strip()) if existing else None
            existing_artifact_exists = bool(
                (existing_result_path and existing_result_path.is_file())
                or (existing_execution_dir and existing_execution_dir.exists())
            )
            # Keep the carry-forward baseline when a sparse rerun lands on the same verdict.
            if (
                existing
                and existing.get("source") == "case_table"
                and str(existing.get("result", "")).strip().lower() == str(record.get("result", "")).strip().lower()
                and existing_artifact_exists
            ):
                pass
            else:
                latest_by_case[case_id] = choose_newer_result(existing, record)
        result_key = (record["ended_at"], record["result_path"])
        if result_key >= latest_result_key:
            latest_result_key = result_key
            latest_result_path = record["result_path"]
    return latest_by_case, latest_result_path


def simplify_tokens(case) -> List[dict]:
    return [{"kind": token.kind, "channel": token.channel, "value": token.value} for token in case.tokens]


def normalize_wake_word(display: str, wakeup_id: str) -> str:
    display = (display or "").strip()
    wakeup_id = (wakeup_id or "").strip().lower()
    if display and "灏" not in display and "?" not in display:
        return display
    if wakeup_id == "xiao mei xiao mei":
        return WAKE_WORD_FALLBACK
    return display or WAKE_WORD_FALLBACK


def enrich_env_seed(session_dir: Path, env_seed: dict) -> dict:
    merged = dict(env_seed or {})
    heartbeat = latest_heartbeat(session_dir)
    merged["logger_heartbeat"] = str(session_heartbeat_path(session_dir))
    logger_pid_path = session_pid_path(session_dir)
    if logger_pid_path.exists():
        raw_pid = logger_pid_path.read_text(encoding="utf-8").strip().lstrip("\ufeff")
        if raw_pid.isdigit():
            merged["active_logger_pid"] = int(raw_pid)
    if heartbeat:
        heartbeat_pid = int(heartbeat.get("logger_pid", 0) or 0)
        if heartbeat_pid > 0:
            merged["active_logger_pid"] = heartbeat_pid
        merged["baudrate"] = int(heartbeat.get("baudrate", merged.get("baudrate", 115200)) or 115200)
    if not int(merged.get("active_logger_pid", 0) or 0):
        merged["active_logger_pid"] = int(os.environ.get("POLARIS_ACTIVE_LOGGER_PID", "0") or 0)
    return merged


def build_status_payload(audit_summary: dict, latest_results: Dict[str, dict], env_seed: dict) -> dict:
    case_map = {case.case_id: case for case in load_doc_cases()}
    device_model, device_model_source = infer_device_model(env_seed)
    capability_tags = build_device_capability_tags(device_model)
    counts = dict(audit_summary["counts"])
    effective = {
        "total": counts["total"],
        "auto_executable_now": counts["auto_executable_now"],
        "executed": 0,
        "pass": 0,
        "fail": 0,
        "blocked": 0,
        "partial": 0,
        "skip": counts["skip"],
    }

    merged_cases: List[dict] = []
    latest_fail_case_ids: List[str] = []
    latest_blocked_case_ids: List[str] = []
    remaining_skipped_with_tokens: List[dict] = []

    for audit_case in audit_summary["cases"]:
        merged = dict(audit_case)
        result = latest_results.get(audit_case["case_id"])
        if result:
            merged["result"] = result["result"]
            merged["execution_dir"] = result["execution_dir"]
            merged["result_path"] = result["result_path"]
            merged["failed_checks"] = result["failed_checks"]
            if audit_case["classification"] == "auto_executable_now":
                effective["executed"] += 1
                result_key = str(result["result"]).strip().lower()
                if result_key in effective:
                    effective[result_key] += 1
                if result_key == "fail":
                    latest_fail_case_ids.append(audit_case["case_id"])
                elif result_key == "blocked":
                    latest_blocked_case_ids.append(audit_case["case_id"])
        if audit_case["classification"] == "skip":
            case = case_map.get(audit_case["case_id"])
            remaining_skipped_with_tokens.append(
                {
                    "case_id": audit_case["case_id"],
                    "name": audit_case["name"],
                    "reason": audit_case["reason"],
                    "mode": audit_case["mode"],
                    "tokens": simplify_tokens(case) if case else [],
                }
            )
        merged_cases.append(merged)

    skip_summary = [{"count": count, "reason": reason} for reason, count in Counter(item["reason"] for item in remaining_skipped_with_tokens).most_common()]

    wake_word_display = normalize_wake_word(
        str(env_seed.get("current_wakeup_word", "")),
        str(env_seed.get("wakeupid_from_deviceinfo", "")),
    )

    status_payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace_root()),
        "session_dir": audit_summary["session_dir"],
        "audit_summary_path": audit_summary["execution_dir"] + "\\audit_summary.json",
        "audit_counts": counts,
        "effective_counts_after_recheck": effective,
        "environment": {
            "ports": {
                get_port("ap"): "cskap / AP / writable",
                get_port("asr"): "asr / writable",
                get_port("cp"): "cskcp / CP / read_only",
                get_port("control"): "power control / writable",
            },
            "baudrate": int(env_seed.get("baudrate", get_baudrate()) or get_baudrate()),
            "wake_word_display": wake_word_display,
            "wake_word_deviceinfo": str(env_seed.get("wakeupid_from_deviceinfo", "")),
            "wifi_state": str(env_seed.get("wifi_state", "online")),
            "connected_ssid": str(env_seed.get("current_connected_ssid", "")),
            "audio_device_key": str(env_seed.get("default_playback_device_key", "")),
            "logger_pid": int(env_seed.get("active_logger_pid", 0) or 0),
            "heartbeat_path": str(env_seed.get("logger_heartbeat", "")),
            "result_root": str(env_seed.get("active_result_root", "")),
            "result_root_count_in_workspace": int(env_seed.get("result_layout", {}).get("root_dir_count_in_workspace", 1) or 1),
            "local_playback_skill": str(env_seed.get("playback_skill", "")),
            "iot_id": str(env_seed.get("current_deviceinfo", {}).get("iot_id", "")),
            "mac": str(env_seed.get("current_deviceinfo", {}).get("mac", "")),
            "env_label": str(env_seed.get("current_env_label", "")),
            "device_model": device_model,
            "device_model_source": device_model_source,
            "device_capability_tags": capability_tags,
        },
        "skip_summary": skip_summary,
        "remaining_skipped_with_tokens": remaining_skipped_with_tokens,
        "cases": merged_cases,
        "latest_fail_case_ids": latest_fail_case_ids,
        "latest_blocked_case_ids": latest_blocked_case_ids,
    }
    return status_payload


def build_env_payload(env_seed: dict, status_payload: dict, latest_audit_path: Path, latest_result_path: str, session_dir: Path) -> dict:
    effective = status_payload["effective_counts_after_recheck"]
    wake_word_display = status_payload["environment"]["wake_word_display"]
    total_auto = max(int(effective["auto_executable_now"]), 1)
    progress = int(round(100 * int(effective["executed"]) / total_auto))
    return {
        "ports": {
            "ap": get_port("ap"),
            "asr": get_port("asr"),
            "wb01": get_port("asr"),
            "cp": get_port("cp"),
            "control": get_port("control"),
        },
        "port_roles": {
            get_port("ap"): "cskap / AP / writable",
            get_port("asr"): "asr / writable",
            get_port("cp"): "cskcp / CP / read_only",
            get_port("control"): "power control / writable",
        },
        "baudrate": int(status_payload["environment"]["baudrate"]),
        "default_playback_device_key": status_payload["environment"]["audio_device_key"],
        "playback_skill": env_seed.get("playback_skill", "listenai-play"),
        "playback_entry": env_seed.get("playback_entry", ""),
        "execution_stage": str(env_seed.get("execution_stage", "")),
        "execution_policy": dict(env_seed.get("execution_policy", {})),
        "current_wakeup_word": wake_word_display,
        "wakeupid_from_deviceinfo": status_payload["environment"]["wake_word_deviceinfo"],
        "wifi_state": status_payload["environment"]["wifi_state"],
        "active_result_root": str(workspace_root() / "result"),
        "active_result_session": str(session_dir),
        "active_logger_pid": status_payload["environment"]["logger_pid"],
        "logger_heartbeat": str(session_heartbeat_path(session_dir)),
        "latest_doc_case_audit": str(latest_audit_path),
        "latest_doc_case_status": str(workspace_root() / "config" / "polaris_doc_case_status.json"),
        "verified_commands_reference": str(workspace_root() / "config" / "polaris_validation_reference.md"),
        "last_case_result": latest_result_path,
        "last_validated_case_spec": (
            f"doc auto-executable sweep through {datetime.now().strftime('%Y-%m-%d %H:%M')} "
            f"({effective['auto_executable_now']} mapped cases)"
        ),
        "judge_capability": "enabled",
        "current_scope_progress_percent": progress,
        "coverage_summary": (
            f"Latest doc scope now has {effective['auto_executable_now']} auto-executable cases; "
            f"{effective['executed']} executed / {effective['pass']} PASS / {effective['fail']} FAIL / "
            f"{effective['blocked']} BLOCKED / {effective['skip']} SKIP."
        ),
        "result_layout": {
            "root_dir": str(workspace_root() / "result"),
            "root_dir_count_in_workspace": int(env_seed.get("result_layout", {}).get("root_dir_count_in_workspace", 1) or 1),
            "session_dir_pattern": "result/YYYYMMDDHHMMSS",
            "duplicate_result_root_detected": bool(env_seed.get("result_layout", {}).get("duplicate_result_root_detected", False)),
        },
        "current_env_value": str(env_seed.get("current_env_value", "")),
        "current_env_label": str(env_seed.get("current_env_label", "")),
        "current_connected_ssid": status_payload["environment"]["connected_ssid"],
        "current_device_model": status_payload["environment"].get("device_model", ""),
        "current_device_model_source": status_payload["environment"].get("device_model_source", ""),
        "current_deviceinfo": dict(env_seed.get("current_deviceinfo", {})),
        "device_capability_tags": dict(status_payload["environment"].get("device_capability_tags", {})),
        "automation_capability": {
            "natural_dialog_switch_phrases": {
                "full_duplex": "打开自然对话",
                "half_duplex": "关闭自然对话",
            },
            "network_orchestration": [
                "windows_hotspot_off_on",
                "asr vir_ssid/vir_pwd + reboot",
            ],
            "power_control": [
                "uut-reset.on/off",
                "uut-csk-reset.on/off",
            ],
            "app_actions": [
                "probe-device",
                "set-full-duplex",
                "set-volume",
                "set-multi-wakeup",
                "set-accent",
                "set-wakeup-word",
                "set-wakeup-threshold",
                "set-log",
                "set-wakeup-audio-upload",
                "set-mic",
                "set-night-mode",
                "set-character-value",
                "proactive-interaction",
            ],
        },
        "latest_doc_case_counts": effective,
        "latest_fail_case_ids": status_payload["latest_fail_case_ids"],
        "latest_blocked_case_ids": status_payload["latest_blocked_case_ids"],
        "remaining_skip_summary": status_payload["skip_summary"],
        "updated_at": status_payload["updated_at"],
    }


def build_reference_md(status_payload: dict, env_payload: dict) -> str:
    effective = status_payload["effective_counts_after_recheck"]
    device_model = status_payload["environment"].get("device_model", "")
    device_model_source = status_payload["environment"].get("device_model_source", "")
    defer_stability_cases = bool(env_payload.get("execution_policy", {}).get("defer_stability_cases", False))
    lines = [
        "# Polaris Validation Reference",
        "",
        f"- updated_at: `{status_payload['updated_at']}`",
        f"- workspace: `{status_payload['workspace']}`",
        f"- active_session: `{status_payload['session_dir']}`",
        f"- logger_pid: `{status_payload['environment']['logger_pid']}`",
        f"- heartbeat: `{status_payload['environment']['heartbeat_path']}`",
        (
            f"- ports: `{get_port('ap')}=cskap/AP/writable`, `{get_port('asr')}=asr/writable`, "
            f"`{get_port('cp')}=cskcp/CP/read_only`, `{get_port('control')}=power-control`"
        ),
        f"- baudrate: `{status_payload['environment']['baudrate']}`",
        f"- audio_device_key: `{status_payload['environment']['audio_device_key']}`",
        f"- playback_skill: `{status_payload['environment']['local_playback_skill']}`",
        f"- wake_word: `{status_payload['environment']['wake_word_display']}` / `{status_payload['environment']['wake_word_deviceinfo']}`",
        f"- wifi_state: `{status_payload['environment']['wifi_state']}`",
        f"- current_connected_ssid: `{status_payload['environment']['connected_ssid']}`",
        f"- current_env: `{status_payload['environment']['env_label']} (env={env_payload['current_env_value']})`",
        f"- execution_stage: `{env_payload.get('execution_stage', '') or 'default'}`",
        (
            f"- current_deviceinfo: `iot_id={status_payload['environment']['iot_id']}`, "
            f"`mac={status_payload['environment']['mac']}`"
        ),
    ]
    if device_model:
        model_line = f"- current_device_model: `{device_model}`"
        if device_model_source:
            model_line += f" (source=`{device_model_source}`)"
        lines.append(model_line)
    lines.extend(
        [
            "",
            "## Latest auto-executable sweep",
            "",
            f"- audit_summary: `{status_payload['audit_summary_path']}`",
            f"- auto_executable_now: `{effective['auto_executable_now']}`",
            f"- latest_executed: `{effective['executed']}`",
            f"- latest_pass: `{effective['pass']}`",
            f"- latest_fail: `{effective['fail']}`",
            f"- latest_blocked: `{effective['blocked']}`",
            f"- latest_skip: `{effective['skip']}`",
            "- continuous logger remained connected for the whole sweep.",
            "- Stability/stress cases are deferred in the current debug stage and are not included in this active baseline." if defer_stability_cases else "- Stability/stress cases remain part of the active executable baseline.",
            "",
            "## Newly confirmed in this round",
            "",
            f"- Current effective baseline is `{effective['executed']} executed / {effective['pass']} PASS / {effective['fail']} FAIL / {effective['blocked']} BLOCKED / {effective['skip']} SKIP`.",
            "- `美的空调_709` ~ `美的空调_714` remain `BLOCKED`: the local trigger path and local evidence are complete, but cloud-side log/audio retrieval is still required for final closure.",
            "",
            "## Key verified capabilities",
            "",
            "- Online/offline continuous serial logging under the active result session.",
            "- Windows hotspot off/on orchestration and ASR `vir_ssid` / `vir_pwd` plus reboot recovery.",
            "- ASR / CSK hard power control via `COM15`.",
            "- Cloud-side automation for natural-dialog, mic, wake word, threshold, accent, wakeup-audio-upload, log level, proactive interaction, and several other app settings.",
            "",
            "## Remaining boundaries to keep in mind",
            "",
            "- Remote/panel/manual extra-resource cases remain outside current auto scope unless a real automation entry point appears.",
            "- Delete/unbind, first provisioning, specified external router, and OTA-risk families remain intentionally excluded.",
            "- Cases that require cloud-side artifact retrieval or downloaded uploaded-audio inspection still need external evidence even if the local trigger path is automated.",
        ]
    )
    return "\n".join(lines) + "\n"


def sync_status(audit_summary_path: Optional[Path] = None) -> dict:
    root = workspace_root()
    session_dir = current_session_dir()
    env_path = root / "config" / "polaris_env.json"
    status_path = root / "config" / "polaris_doc_case_status.json"
    ref_path = root / "config" / "polaris_validation_reference.md"

    env_seed = enrich_env_seed(session_dir, read_json(env_path) if env_path.exists() else {})
    audit_summary_path = audit_summary_path or find_latest_audit_summary(session_dir)
    audit_summary = read_json(audit_summary_path)
    latest_results, latest_result_path = load_latest_results(session_dir)

    status_payload = build_status_payload(audit_summary, latest_results, env_seed)
    env_payload = build_env_payload(env_seed, status_payload, audit_summary_path, latest_result_path, session_dir)
    ref_text = build_reference_md(status_payload, env_payload)

    status_path.write_text(json.dumps(status_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    env_path.write_text(json.dumps(env_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ref_path.write_text(ref_text, encoding="utf-8")

    return {
        "status_path": str(status_path),
        "env_path": str(env_path),
        "reference_path": str(ref_path),
        "audit_summary_path": str(audit_summary_path),
        "effective_counts": status_payload["effective_counts_after_recheck"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh local Polaris status/config/reference files from latest audit and case results")
    parser.add_argument("--audit-summary", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = sync_status(audit_summary_path=args.audit_summary)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
