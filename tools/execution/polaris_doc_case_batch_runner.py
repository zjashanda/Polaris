#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from tools.core.polaris_runtime import current_session_dir, find_artifact_files, new_artifact_dir, workspace_root


ROOT = workspace_root()
DEFAULT_DEVICE_KEY = ""


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def latest_case_result(session_dir: Path, case_id: str) -> Optional[Path]:
    matches = sorted(find_artifact_files(f"doc_case_run_{case_id}", "doc_case_result.json", session_dir), key=lambda item: item.stat().st_mtime)
    return matches[-1] if matches else None


def read_result(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_lock_holder(lock_path: Path) -> str:
    try:
        holder = lock_path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        holder = ""
    return holder or "unknown"


def wait_for_runner_slot(lock_path: Path, queue_log: Path, poll_seconds: int) -> None:
    while lock_path.exists():
        append_log(
            queue_log,
            f"case runner busy, waiting for lock {lock_path.name}, holder={read_lock_holder(lock_path)}",
        )
        time.sleep(poll_seconds)


def append_log(path: Path, message: str) -> None:
    line = f"{now_text()} {message}\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    try:
        sys.stdout.write(line)
        sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(line.encode("gbk", errors="backslashreplace"))
        sys.stdout.flush()


def case_num(case_id: str) -> str:
    return case_id.split("_")[-1]


def run_case(
    *,
    session_dir: Path,
    case_id: str,
    device_key: str,
    batch_stamp: str,
    batch_dir: Path,
    queue_log: Path,
    lock_path: Path,
    poll_seconds: int,
) -> Dict[str, object]:
    wait_for_runner_slot(lock_path, queue_log, poll_seconds)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    num = case_num(case_id)
    stdout_path = batch_dir / f"batch_case_{num}_{batch_stamp}.stdout.log"
    stderr_path = batch_dir / f"batch_case_{num}_{batch_stamp}.stderr.log"
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
    result_path = latest_case_result(session_dir, case_id)
    if result_path and result_path.exists():
        try:
            payload = read_result(result_path)
            diagnosis = payload.get("diagnosis", {})
            judge_path = Path(result_path.parent / "judge.json")
        except Exception as exc:
            diagnosis = {"result": "BLOCKED", "reason": f"read result failed: {exc}"}
            judge_path = Path()
    else:
        diagnosis = {"result": "BLOCKED", "reason": "result json not found"}
        judge_path = Path()
    append_log(
        queue_log,
        f"finish case {case_id} rc={completed.returncode} result={diagnosis.get('result')} reason={diagnosis.get('reason', '')}",
    )
    return {
        "case_num": int(num) if num.isdigit() else num,
        "case_id": case_id,
        "started_at": datetime.strptime(stamp, "%Y%m%d%H%M%S").isoformat(timespec="seconds"),
        "returncode": completed.returncode,
        "judge_path": str(judge_path) if judge_path else "",
        "result": diagnosis.get("result", "BLOCKED"),
        "reason": diagnosis.get("reason", ""),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "result_path": str(result_path) if result_path else "",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run multiple Polaris doc cases sequentially.")
    parser.add_argument("--case-ids", nargs="+", required=True)
    parser.add_argument("--device-key", default=DEFAULT_DEVICE_KEY)
    parser.add_argument("--poll-seconds", type=int, default=10)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    session_dir = current_session_dir(ROOT)
    lock_path = session_dir / ".case_runner.lock"
    batch_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    batch_dir = new_artifact_dir("recovery_batch", session_dir)
    queue_log = batch_dir / f"{batch_stamp}_recovery_batch.log"
    summary_path = batch_dir / f"{batch_stamp}_recovery_batch.json"
    records: List[Dict[str, object]] = []

    append_log(queue_log, f"batch start session={session_dir}")
    append_log(queue_log, f"cases={','.join(args.case_ids)}")
    for case_id in args.case_ids:
        record = run_case(
            session_dir=session_dir,
            case_id=case_id,
            device_key=args.device_key,
            batch_stamp=batch_stamp,
            batch_dir=batch_dir,
            queue_log=queue_log,
            lock_path=lock_path,
            poll_seconds=args.poll_seconds,
        )
        records.append(record)
        summary_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = {
        "PASS": sum(1 for item in records if item["result"] == "PASS"),
        "FAIL": sum(1 for item in records if item["result"] == "FAIL"),
        "BLOCKED": sum(1 for item in records if item["result"] == "BLOCKED"),
        "total": len(records),
    }
    append_log(queue_log, f"batch done counts={counts}")


if __name__ == "__main__":
    main()
