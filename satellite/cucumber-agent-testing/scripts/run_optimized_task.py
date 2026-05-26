#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a Polaris task with execution records, preflight and retry.

This is the first operational layer above run_task.py. It does not replace the
existing Cucumber runner; it wraps it and writes deterministic evidence around
each attempt.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from polaris_env import default_env_path, load_env_payload, resolve_env_path


SCRIPT_DIR = Path(__file__).resolve().parent
BDD_ROOT = SCRIPT_DIR.parents[0]
WORKSPACE_ROOT = SCRIPT_DIR.parents[2]
RUN_TASK = SCRIPT_DIR / "run_task.py"
if str(BDD_ROOT) not in sys.path:
    sys.path.insert(0, str(BDD_ROOT))

from runtime.constraint_engine import evaluate_constraints  # noqa: E402
from runtime.resource_runtime import ResourceLockManager, build_resource_snapshot  # noqa: E402


PASS_RESULTS = {"PASS", "PASS_WITH_SKIPPED_TIMING", "DRY_RUN_OK", "PLAN_OK"}
BLOCKED_RESULTS = {"BLOCKED", "PRECHECK_BLOCKED"}
TIMING_RESULTS = {"TIMING_AMBIGUOUS"}


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


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


def resolve_workspace_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (WORKSPACE_ROOT / path).resolve()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT))
    except Exception:
        return str(path)


def quote_cmd(args: List[str]) -> str:
    result: List[str] = []
    for arg in args:
        if not arg:
            result.append('""')
        elif any(ch.isspace() for ch in arg) or any(ch in arg for ch in ['"', "'", "&"]):
            result.append('"' + arg.replace('"', '\\"') + '"')
        else:
            result.append(arg)
    return " ".join(result)


def resolve_bool(cli_value: Optional[bool], *values: Any) -> bool:
    if cli_value is not None:
        return bool(cli_value)
    for value in values:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "1", "yes", "y"}:
            return True
        if isinstance(value, str) and value.strip().lower() in {"false", "0", "no", "n"}:
            return False
    return False


def resolve_mode(args: argparse.Namespace, task: Dict[str, Any]) -> str:
    return first_non_empty(args.mode, nested(task, "runner", "mode"), task.get("mode"), "dry-run")


def resolve_env_file(args: argparse.Namespace, task: Dict[str, Any]) -> Path:
    value = first_non_empty(args.env_file, nested(task, "environment", "env_file"), nested(task, "runner", "env_file"), str(default_env_path(WORKSPACE_ROOT)))
    return resolve_env_path(value, WORKSPACE_ROOT)


def default_out_root(env_payload: Dict[str, Any]) -> Path:
    debug_root = first_non_empty(nested(env_payload, "paths", "debug_root"), "satellite/cucumber-agent-testing/debug")
    return resolve_workspace_path(debug_root) / "optimized_runs"


def snapshot_state(env_path: Path, env_payload: Dict[str, Any], task: Dict[str, Any], label: str) -> Dict[str, Any]:
    resources = build_resource_snapshot(env_payload, task)
    return {
        "label": label,
        "created_at": now_iso(),
        "workspace": str(WORKSPACE_ROOT),
        "env_file": rel(env_path),
        "project_id": env_payload.get("project_id") or nested(env_payload, "_config_source", "active_project"),
        "project_type": env_payload.get("project_type", ""),
        "serial_ports": nested(env_payload, "serial", "ports") if isinstance(nested(env_payload, "serial", "ports"), dict) else {},
        "audio": {
            "default_playback_device_key": nested(env_payload, "audio", "default_playback_device_key") or "DEFAULT_RENDER_DEVICE",
            "playback_volume": nested(env_payload, "audio", "playback_volume"),
        },
        "network": {
            "wifi_ssid": nested(env_payload, "network", "wifi_ssid"),
            "enable_hotspot_control": bool(nested(env_payload, "network", "enable_hotspot_control")),
        },
        "cloud": {
            "api_environment": nested(env_payload, "cloud", "api_environment"),
            "device_env": nested(env_payload, "cloud", "device_env"),
        },
        "resource_snapshot": resources.to_dict(),
    }


def diff_states(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["project_id", "project_type", "serial_ports", "audio", "network", "cloud"]
    changes: Dict[str, Any] = {}
    for key in keys:
        if before.get(key) != after.get(key):
            changes[key] = {"before": before.get(key), "after": after.get(key)}
    return {"changed": bool(changes), "changes": changes}


def build_run_task_command(args: argparse.Namespace, task_path: Path, env_path: Path, mode: str, allow_side_effects: bool, manage_session: bool, runtime_strict: bool, passthrough: List[str]) -> List[str]:
    cmd = [sys.executable, str(RUN_TASK), "--task", str(task_path), "--mode", mode, "--env-file", str(env_path)]
    if args.tag:
        cmd.extend(["--tag", args.tag])
    if args.device_key:
        cmd.extend(["--device-key", args.device_key])
    if args.wake_word:
        cmd.extend(["--wake-word", args.wake_word])
    if args.command_text:
        cmd.extend(["--command-text", args.command_text])
    if args.command_file:
        cmd.extend(["--command-file", args.command_file])
    if args.command_limit:
        cmd.extend(["--command-limit", args.command_limit])
    if args.observe_ms:
        cmd.extend(["--observe-ms", args.observe_ms])
    if args.compile_first:
        cmd.append("--compile-first")
    if args.strict:
        cmd.append("--strict")
    if allow_side_effects:
        cmd.append("--allow-side-effects")
    if manage_session:
        cmd.append("--manage-session")
    if runtime_strict:
        cmd.append("--runtime-strict")
    cmd.extend(passthrough)
    return cmd


def parse_run_dir(output: str) -> str:
    candidates: List[str] = []
    for raw in output.splitlines():
        line = raw.strip().strip('"')
        if not line or line.startswith("$ "):
            continue
        if "cucumber-agent-testing" in line and ("debug" in line or "runs" in line):
            candidates.append(line)
    for candidate in reversed(candidates):
        if candidate.endswith(".md"):
            candidate = str(Path(candidate).parent)
        path = Path(candidate)
        if not path.is_absolute():
            path = WORKSPACE_ROOT / path
        if path.exists():
            return str(path.resolve())
    pattern = re.compile(r"([A-Za-z]:\\[^\r\n]+?cucumber-agent-testing\\debug\\[^\r\n ]+)")
    matches = pattern.findall(output)
    for candidate in reversed(matches):
        path = Path(candidate.strip())
        if path.exists():
            return str(path.resolve())
    return ""


def extract_bdd_result(run_dir: str) -> Dict[str, Any]:
    if not run_dir:
        return {}
    root = Path(run_dir)
    summary = load_json(root / "bdd_run_summary.json")
    run_summary = load_json(root / "run_summary.json")
    runtime_summary = load_json(root / "runtime_replay_summary.json")
    scenario_results = summary.get("scenario_results", [])
    scenario_statuses = [
        str(item.get("result", "") or "").upper()
        for item in scenario_results
        if isinstance(item, dict) and str(item.get("result", "") or "").strip()
    ]
    if scenario_statuses:
        if any(item in {"FAIL", "ERROR"} for item in scenario_statuses):
            result = "FAIL"
        elif any(item in BLOCKED_RESULTS for item in scenario_statuses):
            result = "BLOCKED"
        elif any(item in TIMING_RESULTS for item in scenario_statuses):
            result = "TIMING_AMBIGUOUS"
        elif all(item in PASS_RESULTS for item in scenario_statuses):
            result = "PASS"
        else:
            result = scenario_statuses[0]
    else:
        result = first_non_empty(summary.get("result"), run_summary.get("result"), summary.get("status"), run_summary.get("status"))
    runtime_results: List[str] = []
    if isinstance(runtime_summary, dict):
        for item in runtime_summary.values():
            if isinstance(item, dict):
                runtime_results.append(first_non_empty(item.get("result"), nested(item, "assertion_summary", "result")))
    return {
        "result": result,
        "scenario_results": scenario_results,
        "runtime_results": [item for item in runtime_results if item],
        "bdd_run_summary": rel(root / "bdd_run_summary.json") if (root / "bdd_run_summary.json").exists() else "",
        "runtime_replay_summary": rel(root / "runtime_replay_summary.json") if (root / "runtime_replay_summary.json").exists() else "",
    }


def classify_attempt(mode: str, returncode: int, bdd: Dict[str, Any]) -> str:
    if returncode != 0:
        return "FAIL"
    if mode == "dry-run":
        return "DRY_RUN_OK"
    if mode == "plan-only":
        return "PLAN_OK"
    result = first_non_empty(bdd.get("result"))
    runtime_results = [str(item).upper() for item in bdd.get("runtime_results", [])]
    if result.upper() in PASS_RESULTS:
        return result.upper()
    if result.upper() in BLOCKED_RESULTS:
        return "BLOCKED"
    if result.upper() in TIMING_RESULTS:
        return "TIMING_AMBIGUOUS"
    if runtime_results:
        if all(item in PASS_RESULTS for item in runtime_results):
            return "PASS"
        if any(item == "BLOCKED" for item in runtime_results):
            return "BLOCKED"
        if any(item == "FAIL" for item in runtime_results):
            return "FAIL"
        if any(item in TIMING_RESULTS for item in runtime_results):
            return "TIMING_AMBIGUOUS"
    return "PASS"


def aggregate_attempts(attempts: List[Dict[str, Any]], max_attempts: int) -> Dict[str, Any]:
    results = [str(item.get("result", "")).upper() for item in attempts]
    if any(item in PASS_RESULTS for item in results):
        first_pass = next(index for index, item in enumerate(results, start=1) if item in PASS_RESULTS)
        stability = "PASS" if first_pass == 1 else "FLAKY_PASS"
        return {"result": "PASS", "stability": stability, "passed_attempt": first_pass, "attempts": len(attempts)}
    if any(item in BLOCKED_RESULTS for item in results):
        return {"result": "BLOCKED", "stability": "ENV_RELATED", "attempts": len(attempts)}
    if any(item in TIMING_RESULTS for item in results):
        return {"result": "TIMING_AMBIGUOUS", "stability": "TIMING_AMBIGUOUS", "attempts": len(attempts)}
    if len(set(results)) <= 1 and len(attempts) >= max_attempts:
        return {"result": "FAIL", "stability": "STABLE_FAIL", "attempts": len(attempts)}
    return {"result": "FAIL", "stability": "FLAKY_FAIL", "attempts": len(attempts)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Polaris task with execution record, retry and resource/constraint preflight.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["plan-only", "dry-run", "execute"], default="")
    parser.add_argument("--env-file", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--device-key", default="")
    parser.add_argument("--wake-word", default="")
    parser.add_argument("--command-text", default="")
    parser.add_argument("--command-file", default="")
    parser.add_argument("--command-limit", default="")
    parser.add_argument("--observe-ms", default="")
    parser.add_argument("--compile-first", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-side-effects", dest="allow_side_effects", action="store_true", default=None)
    parser.add_argument("--no-allow-side-effects", dest="allow_side_effects", action="store_false")
    parser.add_argument("--manage-session", dest="manage_session", action="store_true", default=None)
    parser.add_argument("--no-manage-session", dest="manage_session", action="store_false")
    parser.add_argument("--runtime-strict", dest="runtime_strict", action="store_true", default=None)
    parser.add_argument("--no-runtime-strict", dest="runtime_strict", action="store_false")
    parser.add_argument("--max-retries", type=int, default=-1, help="失败后重试次数；-1 使用 task/policy 默认。")
    parser.add_argument("--retry-blocked", action="store_true", help="默认不重试 BLOCKED；开启后 BLOCKED 也重试。")
    parser.add_argument("--out-root", default="")
    parser.add_argument("--precheck-only", action="store_true")
    parser.add_argument("--allow-precheck-blocked", action="store_true")
    parser.add_argument("--no-resource-lock", action="store_true", help="跳过本地资源锁；仅建议调试时使用。")
    parser.add_argument("--lock-root", default="", help="资源锁目录，默认 debug/resource_locks")
    parser.add_argument("--print-command", action="store_true")
    args, passthrough = parser.parse_known_args()

    task_path = resolve_workspace_path(args.task).resolve()
    task = load_json(task_path)
    env_path = resolve_env_file(args, task).resolve()
    env_payload = load_env_payload(env_path)
    mode = resolve_mode(args, task)
    execution = task.get("execution", {}) if isinstance(task.get("execution"), dict) else {}
    policy = task.get("policy", {}) if isinstance(task.get("policy"), dict) else {}
    allow_side_effects = resolve_bool(args.allow_side_effects, execution.get("allow_side_effects"), policy.get("allow_side_effects"))
    manage_session = resolve_bool(args.manage_session, execution.get("manage_session"), policy.get("manage_session"))
    runtime_strict = resolve_bool(args.runtime_strict, execution.get("runtime_strict"), policy.get("runtime_strict"))
    max_retries = args.max_retries if args.max_retries >= 0 else int(first_non_empty(execution.get("max_retries"), policy.get("max_retries"), 0) or 0)
    max_attempts = max(1, max_retries + 1)
    out_root = resolve_workspace_path(args.out_root).resolve() if args.out_root else default_out_root(env_payload).resolve()
    task_id = first_non_empty(task.get("task_id"), task_path.stem)
    run_root = out_root / f"{stamp()}_{task_id}"
    run_root.mkdir(parents=True, exist_ok=True)

    preflight = evaluate_constraints(task=task, env_payload=env_payload, mode=mode, allow_side_effects=allow_side_effects, tag=args.tag)
    before = snapshot_state(env_path, env_payload, task, "before")
    write_json(run_root / "preflight.json", preflight)
    write_json(run_root / "state" / "before.json", before)

    cmd = build_run_task_command(args, task_path, env_path, mode, allow_side_effects, manage_session, runtime_strict, passthrough)
    write_json(run_root / "command.json", {"cmd": cmd, "cmdline": quote_cmd(cmd), "created_at": now_iso()})
    if args.print_command:
        print(run_root)
        print("$ " + quote_cmd(cmd))
        return 0
    if args.precheck_only:
        print(run_root)
        print(f"preflight={preflight['result']}")
        return 0 if preflight["result"] != "FAIL" else 1
    if preflight["result"] in {"FAIL", "BLOCKED"} and not args.allow_precheck_blocked:
        record = {
            "schema": "polaris.execution_record.v1",
            "task": rel(task_path),
            "env_file": rel(env_path),
            "created_at": now_iso(),
            "result": preflight["result"],
            "stability": "PRECHECK_BLOCKED",
            "preflight": preflight,
            "attempts": [],
        }
        write_json(run_root / "execution_record.json", record)
        print(run_root)
        print(f"result={record['result']} stability={record['stability']}")
        return 1

    attempts: List[Dict[str, Any]] = []
    locks = []
    lock_root = resolve_workspace_path(args.lock_root).resolve() if args.lock_root else default_out_root(env_payload).parent / "resource_locks"
    lock_manager = ResourceLockManager(lock_root)
    try:
        if mode == "execute" and not args.no_resource_lock:
            locks = lock_manager.acquire(build_resource_snapshot(env_payload, task).claims, run_id=run_root.name, owner=task_id)
            write_json(run_root / "resource_locks.json", {"lock_root": str(lock_root), "locks": [item.to_dict() for item in locks]})

        for attempt_index in range(1, max_attempts + 1):
            attempt_dir = run_root / f"attempt_{attempt_index:02d}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            started = now_iso()
            completed = subprocess.run(
                cmd,
                cwd=str(WORKSPACE_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            finished = now_iso()
            output = completed.stdout or ""
            (attempt_dir / "stdout.log").write_text(output, encoding="utf-8")
            run_dir = parse_run_dir(output)
            bdd = extract_bdd_result(run_dir)
            result = classify_attempt(mode, completed.returncode, bdd)
            attempt = {
                "attempt": attempt_index,
                "started_at": started,
                "finished_at": finished,
                "returncode": completed.returncode,
                "result": result,
                "run_dir": rel(Path(run_dir)) if run_dir else "",
                "stdout_log": rel(attempt_dir / "stdout.log"),
                "bdd": bdd,
            }
            attempts.append(attempt)
            write_json(attempt_dir / "attempt.json", attempt)
            append_jsonl(run_root / "attempts.jsonl", attempt)
            print(f"attempt={attempt_index} result={result} returncode={completed.returncode} run_dir={attempt['run_dir']}")
            if result in PASS_RESULTS:
                break
            if result in BLOCKED_RESULTS and not args.retry_blocked:
                break
    except RuntimeError as exc:
        attempt = {
            "attempt": len(attempts) + 1,
            "started_at": now_iso(),
            "finished_at": now_iso(),
            "returncode": 2,
            "result": "BLOCKED",
            "run_dir": "",
            "stdout_log": "",
            "reason": str(exc),
        }
        attempts.append(attempt)
        append_jsonl(run_root / "attempts.jsonl", attempt)
        write_json(run_root / "resource_lock_error.json", {"error": str(exc), "lock_root": str(lock_root)})
    finally:
        if locks:
            lock_manager.release(locks)

    after_payload = load_env_payload(env_path)
    after = snapshot_state(env_path, after_payload, task, "after")
    state_diff = diff_states(before, after)
    write_json(run_root / "state" / "after.json", after)
    write_json(run_root / "state_diff.json", state_diff)
    aggregate = aggregate_attempts(attempts, max_attempts)
    record = {
        "schema": "polaris.execution_record.v1",
        "task": rel(task_path),
        "task_id": task_id,
        "env_file": rel(env_path),
        "mode": mode,
        "created_at": now_iso(),
        "result": aggregate["result"],
        "stability": aggregate["stability"],
        "max_retries": max_retries,
        "preflight": preflight,
        "state": {
            "before": rel(run_root / "state" / "before.json"),
            "after": rel(run_root / "state" / "after.json"),
            "diff": rel(run_root / "state_diff.json"),
        },
        "attempts": attempts,
    }
    write_json(run_root / "execution_record.json", record)
    print(run_root)
    print(f"result={record['result']} stability={record['stability']} attempts={len(attempts)}")
    return 0 if record["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
