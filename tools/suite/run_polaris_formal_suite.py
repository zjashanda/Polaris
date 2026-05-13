#!/usr/bin/env python3
"""Polaris unified validation-suite dispatcher.

Default mode is plan-only: it creates a suite directory, runs validation-pool
classification, checks non-invasive file gates, and writes a summary/report. Use
--execute to run profile stages that may touch hardware, serial ports, cloud, or
playback devices.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "references" / "project-profiles" / "polaris_midea_ac.json"
SUITE_ROOT = ROOT / "outputs" / "formal_suite_runs"


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(p)


def sanitize(value: str) -> str:
    keep = [ch if ch.isalnum() or ch in "._-" else "_" for ch in value]
    return "".join(keep).strip("_") or "suite"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class CommandRecord:
    name: str
    cmd: list[str]
    returncode: int
    log_path: Path
    started_at: str
    finished_at: str


class CommandRunner:
    def __init__(self, suite_dir: Path) -> None:
        self.logs_dir = suite_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def run(self, name: str, cmd: list[str], *, allow_nonzero: bool = False) -> CommandRecord:
        log_path = self.logs_dir / f"{len(list(self.logs_dir.glob('*.log'))) + 1:02d}_{sanitize(name)}.log"
        started_at = iso_now()
        with log_path.open("w", encoding="utf-8") as log:
            log.write(f"$ {' '.join(cmd)}\n")
            log.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(line)
                log.flush()
                print(line, end="")
            rc = proc.wait()
        finished_at = iso_now()
        record = CommandRecord(name, cmd, rc, log_path, started_at, finished_at)
        if rc != 0 and not allow_nonzero:
            raise RuntimeError(f"stage {name} failed, rc={rc}, log={log_path}")
        return record


def check_file_gates(profile: dict[str, Any]) -> dict[str, Any]:
    marker = ROOT / profile.get("session_marker", ".current_result_dir")
    gates: dict[str, Any] = {"session_marker": {"path": rel(marker), "exists": marker.exists()}}
    if marker.exists():
        raw = marker.read_text(encoding="utf-8", errors="replace").strip().lstrip("\ufeff")
        session_dir = Path(raw)
        if not session_dir.is_absolute():
            session_dir = (ROOT / session_dir).resolve()
        gates["session_dir"] = {"path": rel(session_dir), "exists": session_dir.exists()}
        heartbeat = session_dir / "logs" / "live" / "heartbeat.json"
        gates["heartbeat"] = {"path": rel(heartbeat), "exists": heartbeat.exists()}
        if heartbeat.exists():
            try:
                gates["heartbeat"]["payload"] = load_json(heartbeat)
            except Exception as exc:
                gates["heartbeat"]["error"] = str(exc)
    for cfg in profile.get("config_files", []):
        p = ROOT / cfg
        gates.setdefault("config_files", []).append({"path": cfg, "exists": p.exists()})
    return gates


def run_classification(runner: CommandRunner, suite_dir: Path) -> tuple[Path, CommandRecord]:
    out = suite_dir / "classification.md"
    inputs = ["SKILL.md", "capabilities-and-usage.md", "environment-and-migration.md", "references"]
    cmd = [
        sys.executable,
        "tools/pool/polaris_validation_pool.py",
        "classify",
        "--project-key",
        "polaris_midea_ac",
        "--out",
        str(out),
        *inputs,
    ]
    return out, runner.run("validation_pool_classify", cmd)


def command_record(record: CommandRecord) -> dict[str, Any]:
    return {
        "name": record.name,
        "cmd": record.cmd,
        "returncode": record.returncode,
        "log_path": rel(record.log_path),
        "started_at": record.started_at,
        "finished_at": record.finished_at,
    }


def write_report(suite_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Polaris 统一验证套件报告",
        "",
        f"- 状态：`{summary.get('status')}`",
        f"- 模式：`{'execute' if summary.get('executed') else 'plan-only'}`",
        f"- 项目：`{summary.get('project_id')}`",
        f"- 结果目录：`{rel(suite_dir)}`",
        f"- 分类结果：`{summary.get('classification')}`",
        "",
        "## 文件门禁",
        "",
    ]
    for key, value in (summary.get("gates") or {}).items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`：exists=`{value.get('exists')}` path=`{value.get('path')}`")
        elif isinstance(value, list):
            for item in value:
                lines.append(f"- `{key}`：exists=`{item.get('exists')}` path=`{item.get('path')}`")
    lines.extend(["", "## 阶段", ""])
    for phase in summary.get("phases", []):
        if phase.get("planned_only"):
            lines.append(f"- `{phase['name']}`：planned cmd=`{' '.join(phase.get('cmd', []))}`")
        else:
            lines.append(f"- `{phase['name']}`：rc=`{phase.get('returncode')}` log=`{phase.get('log_path')}`")
    if not summary.get("executed"):
        lines.extend([
            "",
            "## 下一步",
            "",
            "- 默认 plan-only 不占用串口、不调用云端、不播放音频。",
            "- 确认门禁和执行范围后，加 `--execute` 才会运行 profile 中的现有工具阶段。",
        ])
    (suite_dir / "suite_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Polaris unified formal-suite skeleton")
    parser.add_argument("--tag", default="polaris_formal_suite")
    parser.add_argument("--execute", action="store_true", help="run hardware/cloud-touching profile stages")
    parser.add_argument("--skip-stage", action="append", default=[], help="stage name to skip; repeatable")
    args = parser.parse_args()

    profile = load_json(PROFILE_PATH)
    suite_dir = SUITE_ROOT / f"{stamp()}_{sanitize(args.tag)}"
    suite_dir.mkdir(parents=True, exist_ok=True)
    runner = CommandRunner(suite_dir)
    phases: list[dict[str, Any]] = []

    try:
        classification, classify_record = run_classification(runner, suite_dir)
        phases.append(command_record(classify_record))
        gates = check_file_gates(profile)
        if args.execute:
            for stage in profile.get("stages", []):
                name = stage.get("name")
                if name in {"validation_pool_classify", *args.skip_stage}:
                    continue
                if stage.get("kind") != "existing_tool":
                    phases.append({"name": name, "planned_only": True, "kind": stage.get("kind"), "cmd": stage.get("cmd", [])})
                    continue
                record = runner.run(name, [str(part) for part in stage.get("cmd", [])], allow_nonzero=bool(stage.get("allow_nonzero")))
                phases.append(command_record(record))
        else:
            for stage in profile.get("stages", []):
                if stage.get("name") == "validation_pool_classify":
                    continue
                phases.append({"name": stage.get("name"), "planned_only": True, "kind": stage.get("kind"), "cmd": stage.get("cmd", [])})

        summary = {
            "status": "DONE",
            "executed": bool(args.execute),
            "project_id": profile.get("project_id"),
            "profile": rel(PROFILE_PATH),
            "suite_dir": rel(suite_dir),
            "classification": rel(classification),
            "gates": gates,
            "phases": phases,
        }
        write_json(suite_dir / "suite_summary.json", summary)
        write_report(suite_dir, summary)
        print(suite_dir)
        return 0
    except Exception as exc:
        summary = {
            "status": "ERROR",
            "executed": bool(args.execute),
            "project_id": profile.get("project_id"),
            "suite_dir": rel(suite_dir),
            "error": str(exc),
            "phases": phases,
        }
        write_json(suite_dir / "suite_summary.json", summary)
        write_report(suite_dir, summary)
        print(f"ERROR: {exc}", file=sys.stderr)
        print(suite_dir)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
