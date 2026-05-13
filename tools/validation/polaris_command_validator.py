#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import json
from datetime import datetime
from typing import Dict, List

from tools.core.polaris_config import get_port
from tools.core.polaris_runtime import (
    current_session_dir,
    new_artifact_dir,
    now_iso_ms,
    queue_command,
    wait_for_patterns,
)


ROOT = Path(__file__).resolve().parents[2]
DOC_SOURCE = "doc/reference/美的空调相关特殊操作说明文档.docx"
CATALOG_PATH = ROOT / "config" / "polaris_command_catalog.json"
SUMMARY_PATH = ROOT / "config" / "polaris_command_catalog.md"

FALLBACK_COMMANDS: List[Dict[str, object]] = [
    {
        "id": "ap.version",
        "port": "COM14",
        "command": "version",
        "syntax": "version",
        "description": "Read AP/CP/algo versions.",
        "category": "info",
        "risk_level": "safe",
        "source": DOC_SOURCE,
        "verify_mode": "auto",
        "patterns": ["ap version:", "cp version:", "algo version"],
        "pattern_port": "COM14",
        "timeout_s": 4.0,
    },
    {
        "id": "ap.deviceinfo",
        "port": "COM14",
        "command": "deviceinfo",
        "syntax": "deviceinfo",
        "description": "Read SN/MAC/WakeupID/IP/IoT ID.",
        "category": "info",
        "risk_level": "safe",
        "source": DOC_SOURCE,
        "verify_mode": "auto",
        "patterns": ["device info:", "wakeupid:"],
        "pattern_port": "COM14",
        "timeout_s": 4.0,
    },
    {
        "id": "ap.flash_show",
        "port": "COM14",
        "command": "flash.show",
        "syntax": "flash.show",
        "description": "Read AP flash settings.",
        "category": "config_query",
        "risk_level": "safe",
        "source": DOC_SOURCE,
        "verify_mode": "auto",
        "patterns": ["boot.action=", "env="],
        "pattern_port": "COM14",
        "timeout_s": 4.0,
    },
    {
        "id": "wb.version",
        "port": "COM13",
        "command": "listen version",
        "syntax": "listen version",
        "description": "Read ASR version info.",
        "category": "info",
        "risk_level": "safe",
        "source": DOC_SOURCE,
        "verify_mode": "auto",
        "patterns": ["listenai build info:", "ms version:"],
        "pattern_port": "COM13",
        "timeout_s": 4.0,
    },
    {
        "id": "wb.flash_show",
        "port": "COM13",
        "command": "listen flash show",
        "syntax": "listen flash show",
        "description": "Read ASR flash settings.",
        "category": "config_query",
        "risk_level": "safe",
        "source": DOC_SOURCE,
        "verify_mode": "auto",
        "patterns": ["flash kv list:", "log_lev="],
        "pattern_port": "COM13",
        "timeout_s": 4.0,
    },
]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_commands() -> List[Dict[str, object]]:
    if CATALOG_PATH.exists():
        try:
            payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            commands = payload.get("commands", [])
            if isinstance(commands, list) and commands:
                normalized: List[Dict[str, object]] = []
                for item in commands:
                    if isinstance(item, dict):
                        normalized.append(dict(item))
                if normalized:
                    return normalized
        except Exception:
            pass
    return [dict(item) for item in FALLBACK_COMMANDS]


def normalize_command(item: Dict[str, object]) -> Dict[str, object]:
    normalized = dict(item)
    normalized.setdefault("id", "")
    normalized.setdefault("port", "")
    normalized.setdefault("command", "")
    normalized.setdefault("syntax", normalized["command"])
    normalized.setdefault("description", "")
    normalized.setdefault("category", "misc")
    normalized.setdefault("risk_level", "documented_only")
    normalized.setdefault("source", DOC_SOURCE)
    normalized.setdefault("verify_mode", "documented_only")
    normalized.setdefault("patterns", [])
    normalized.setdefault("pattern_port", normalized.get("port", ""))
    normalized.setdefault("timeout_s", 5.0)
    normalized.setdefault("notes", "")
    normalized["source"] = DOC_SOURCE
    command = str(normalized.get("command", "")).strip().lower()
    command_id = str(normalized.get("id", "")).strip().lower()
    role = "asr" if command.startswith("listen ") or command_id.startswith(("wb.", "asr.")) else "ap"
    port = get_port(role)
    normalized["role"] = role
    normalized["port"] = port
    normalized["pattern_port"] = port
    return normalized


def validate_commands(session_dir: Path, commands: List[Dict[str, object]]) -> List[Dict[str, object]]:
    artifact_dir = new_artifact_dir("command_validation", session_dir=session_dir)
    validated: List[Dict[str, object]] = []

    for item in commands:
        result = dict(item)
        verify_mode = str(result.get("verify_mode", "documented_only"))
        result["verified_at"] = None
        result["evidence"] = []

        if verify_mode != "auto":
            risk_level = str(result.get("risk_level", "documented_only"))
            result["verified_status"] = "not_run" if risk_level not in {"safe", "safe_with_caution"} else "documented_only"
            validated.append(result)
            continue

        start_dt = datetime.now()
        queue_meta = queue_command(str(result["port"]), str(result["command"]), session_dir=session_dir)
        matched = wait_for_patterns(
            str(result.get("pattern_port") or result["port"]),
            start_dt,
            [str(pattern) for pattern in result.get("patterns", [])],
            timeout_s=float(result.get("timeout_s", 5.0) or 5.0),
            session_dir=session_dir,
        )
        failures = [pattern for pattern, line in matched.items() if line is None]
        if failures:
            result["verified_status"] = "fail"
            result["notes"] = f"Missing expected log markers: {', '.join(failures)}"
        else:
            result["verified_status"] = "pass"
            result["notes"] = "Matched all expected log markers."
        result["verified_at"] = queue_meta["ts"]
        result["evidence"] = [
            {
                "pattern": pattern,
                "line": line,
                "log": f"{result.get('pattern_port') or result['port']}.log",
            }
            for pattern, line in matched.items()
            if line is not None
        ]
        validated.append(result)

    artifact_payload = {
        "generated_at": now_iso_ms(),
        "session_dir": str(session_dir),
        "commands": validated,
    }
    (artifact_dir / "command_validation_results.json").write_text(
        json.dumps(artifact_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        "# Polaris serial command validation",
        "",
        f"- session: `{session_dir}`",
        f"- generated_at: `{artifact_payload['generated_at']}`",
        "",
        "| id | port | command | status | notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in validated:
        report_lines.append(
            f"| `{item['id']}` | `{item['port']}` | `{item['command']}` | `{item['verified_status']}` | {item.get('notes', '')} |"
        )
    (artifact_dir / "command_validation_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    return validated


def write_catalog(commands: List[Dict[str, object]], session_dir: Path) -> None:
    ensure_parent(CATALOG_PATH)
    catalog = {
        "generated_at": now_iso_ms(),
        "session_dir": str(session_dir),
        "source_files": [DOC_SOURCE],
        "commands": commands,
    }
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Polaris 串口命令目录",
        "",
        f"- 生成时间: `{catalog['generated_at']}`",
        f"- 当前日志会话: `{catalog['session_dir']}`",
        f"- 文档来源: `{DOC_SOURCE}`",
        "",
    ]
    ap_port = get_port("ap")
    asr_port = get_port("asr")
    for port, title in ((ap_port, f"AP / {ap_port}"), (asr_port, f"ASR / {asr_port}")):
        lines.extend(
            [
                f"## {title}",
                "",
                "| 命令 | 类别 | 风险 | 验证状态 | 说明 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for item in commands:
            if str(item.get("port", "")) != port:
                continue
            lines.append(
                f"| `{item['command']}` | `{item['category']}` | `{item['risk_level']}` | `{item.get('verified_status', 'documented_only')}` | {item.get('description', '')} |"
            )
        lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    session_dir = current_session_dir()
    commands = [normalize_command(item) for item in load_commands()]
    validated = validate_commands(session_dir, commands)
    write_catalog(validated, session_dir)
    print(CATALOG_PATH)
    print(SUMMARY_PATH)


if __name__ == "__main__":
    main()
