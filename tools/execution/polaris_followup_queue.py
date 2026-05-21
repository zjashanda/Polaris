#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


from tools.core.polaris_runtime import current_session_dir, find_artifact_files, new_artifact_dir

ROOT = Path(__file__).resolve().parents[2]
SESSION_DIR = current_session_dir()
LOCK_PATH = SESSION_DIR / ".case_runner.lock"
DEFAULT_DEVICE_KEY = ""
QUEUE_CASES = [
    "美的空调_45",
    "美的空调_709",
    "美的空调_710",
    "美的空调_711",
    "美的空调_712",
    "美的空调_713",
    "美的空调_714",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_log(log_path: Path, message: str) -> None:
    line = f"{now_text()} {message}\n"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="", flush=True)


def read_result(result_path: Path) -> Dict[str, object]:
    return json.loads(result_path.read_text(encoding="utf-8"))


def latest_case_result(case_id: str) -> Optional[Path]:
    matches = sorted(find_artifact_files(f"doc_case_run_{case_id}", "doc_case_result.json", SESSION_DIR), key=lambda item: item.stat().st_mtime)
    return matches[-1] if matches else None


def wait_for_runner_slot(log_path: Path) -> None:
    while LOCK_PATH.exists():
        try:
            holder = LOCK_PATH.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            holder = ""
        append_log(log_path, f"case runner busy, waiting for lock {LOCK_PATH.name}, holder={holder or 'unknown'}")
        time.sleep(30)


def run_case(case_id: str, device_key: str, queue_log: Path, queue_dir: Path) -> Dict[str, object]:
    wait_for_runner_slot(queue_log)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stdout_path = queue_dir / f"{stamp}_followup_{case_id}.stdout.log"
    stderr_path = queue_dir / f"{stamp}_followup_{case_id}.stderr.log"
    command = [
        sys.executable,
        str(ROOT / "tools" / "execution" / "polaris_doc_case_runner.py"),
        "--case-id",
        case_id,
    ]
    if str(device_key or "").strip():
        command.extend(["--device-key", str(device_key).strip()])
    append_log(queue_log, f"start case {case_id}")
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open("w", encoding="utf-8") as stderr_handle:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    result_path = latest_case_result(case_id)
    diagnosis = {}
    if result_path and result_path.exists():
        try:
            diagnosis = read_result(result_path).get("diagnosis", {})
        except Exception as exc:
            diagnosis = {"result": "BLOCKED", "reason": f"read result failed: {exc}"}
    else:
        diagnosis = {"result": "BLOCKED", "reason": "result json not found"}
    append_log(
        queue_log,
        f"finish case {case_id} rc={completed.returncode} result={diagnosis.get('result')} reason={diagnosis.get('reason', '')}",
    )
    return {
        "case_id": case_id,
        "returncode": completed.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "result_path": str(result_path) if result_path else "",
        "diagnosis": diagnosis,
    }


def main() -> None:
    queue_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    queue_dir = new_artifact_dir("followup_queue", SESSION_DIR)
    queue_log = queue_dir / f"{queue_stamp}_followup_queue.log"
    queue_summary = queue_dir / f"{queue_stamp}_followup_queue.json"
    queue_records: List[Dict[str, object]] = []

    append_log(queue_log, "queue start")
    case44_result = latest_case_result("美的空调_44")
    if case44_result:
        try:
            diag = read_result(case44_result).get("diagnosis", {})
            append_log(queue_log, f"latest case 44 before queue: result={diag.get('result')} path={case44_result}")
        except Exception as exc:
            append_log(queue_log, f"failed to read latest case 44 result: {exc}")

    for case_id in QUEUE_CASES:
        record = run_case(case_id, DEFAULT_DEVICE_KEY, queue_log, queue_dir)
        queue_records.append(record)
        queue_summary.write_text(json.dumps(queue_records, ensure_ascii=False, indent=2), encoding="utf-8")

    append_log(queue_log, "queue done")


if __name__ == "__main__":
    main()
