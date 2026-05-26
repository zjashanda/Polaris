#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation Kernel lifecycle MVP.

The kernel is a thin deterministic coordinator.  It compiles Validation IR,
captures adapter/capability/resource/constraint snapshots and can delegate
execution to the existing run_optimized_task.py without replacing it.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .analytics_trend import build_trend, render_trend_markdown
from .event_graph import build_event_graph, render_event_graph_markdown
from .events import ValidationEvent
from .timeline import Timeline
from .validation_ir import build_validation_ir


EVENT_FIELDS = set(ValidationEvent.__dataclass_fields__.keys())


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _quote_cmd(args: List[str]) -> str:
    rendered: List[str] = []
    for arg in args:
        text = str(arg)
        if not text:
            rendered.append('""')
        elif any(ch.isspace() for ch in text) or any(ch in text for ch in ['"', "'", "&"]):
            rendered.append('"' + text.replace('"', '\\"') + '"')
        else:
            rendered.append(text)
    return " ".join(rendered)


def _timeline_from_json(path: Path) -> Timeline:
    payload = _load_json(path)
    events: List[ValidationEvent] = []
    for item in payload.get("events", []):
        if isinstance(item, dict):
            events.append(ValidationEvent(**{key: value for key, value in item.items() if key in EVENT_FIELDS}))
    return Timeline.from_events(events)


@dataclass
class KernelStage:
    name: str
    result: str
    started_at: str
    finished_at: str
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KernelRecord:
    kernel_id: str
    result: str
    task_id: str
    project_id: str
    mode: str
    created_at: str
    stages: List[KernelStage]
    artifacts: Dict[str, str] = field(default_factory=dict)
    runner: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "polaris.validation_kernel_record.v1",
            "kernel_id": self.kernel_id,
            "result": self.result,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "mode": self.mode,
            "created_at": self.created_at,
            "stages": [stage.to_dict() for stage in self.stages],
            "artifacts": self.artifacts,
            "runner": self.runner,
        }


class ValidationKernel:
    def __init__(self, *, workspace_root: Path, scripts_dir: Path, out_dir: Path) -> None:
        self.workspace_root = workspace_root
        self.scripts_dir = scripts_dir
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.lifecycle_path = self.out_dir / "lifecycle.jsonl"
        self.stages: List[KernelStage] = []

    def stage(self, name: str, result: str, started_at: str, detail: Optional[Dict[str, Any]] = None) -> None:
        stage = KernelStage(name=name, result=result, started_at=started_at, finished_at=now_iso(), detail=detail or {})
        self.stages.append(stage)
        append_jsonl(self.lifecycle_path, stage.to_dict())

    def run(
        self,
        *,
        task_path: Path,
        env_path: Path,
        task: Dict[str, Any],
        env_payload: Dict[str, Any],
        mode: str,
        tag: str = "",
        allow_side_effects: bool = False,
        execute_runner: bool = False,
        manage_session: bool = False,
        runtime_strict: bool = False,
        max_retries: int = 0,
    ) -> KernelRecord:
        started = now_iso()
        ir = build_validation_ir(
            task=task,
            env_payload=env_payload,
            task_path=str(task_path),
            env_file=str(env_path),
            mode=mode,
            allow_side_effects=allow_side_effects,
            tag=tag,
        )
        write_json(self.out_dir / "validation_ir.json", ir.to_dict())
        write_json(self.out_dir / "adapter_registry.json", ir.adapters)
        write_json(self.out_dir / "capability_matrix.json", ir.capabilities)
        write_json(self.out_dir / "resource_snapshot.json", ir.resources)
        write_json(self.out_dir / "constraint_result.json", ir.constraints)
        self.stage("compile_ir", "PASS", started, {"ir_id": ir.ir_id})
        self.stage("preflight", str(ir.constraints.get("result", "UNKNOWN")), now_iso(), {"warning_count": len(ir.constraints.get("warnings", []))})

        runner_summary: Dict[str, Any] = {}
        result = "PLAN_OK" if ir.constraints.get("result") == "PASS" else str(ir.constraints.get("result", "BLOCKED"))
        if execute_runner and result in {"PLAN_OK", "PASS"}:
            runner_summary = self._run_optimized_task(
                task_path=task_path,
                env_path=env_path,
                mode=mode,
                tag=tag,
                allow_side_effects=allow_side_effects,
                manage_session=manage_session,
                runtime_strict=runtime_strict,
                max_retries=max_retries,
            )
            result = str(runner_summary.get("result", "UNKNOWN") or "UNKNOWN")
            self._build_runner_sidecars(runner_summary)
        elif execute_runner:
            self.stage("runner_skipped", "BLOCKED", now_iso(), {"reason": f"preflight result={result}"})

        records = list((self.out_dir / "optimized").rglob("execution_record.json"))
        if records:
            trend = build_trend(records)
            write_json(self.out_dir / "analytics_trend.json", trend)
            (self.out_dir / "analytics_trend.md").write_text(render_trend_markdown(trend), encoding="utf-8")

        artifacts = {
            "lifecycle": str(self.lifecycle_path),
            "validation_ir": str(self.out_dir / "validation_ir.json"),
            "adapter_registry": str(self.out_dir / "adapter_registry.json"),
            "capability_matrix": str(self.out_dir / "capability_matrix.json"),
            "resource_snapshot": str(self.out_dir / "resource_snapshot.json"),
            "constraint_result": str(self.out_dir / "constraint_result.json"),
        }
        optional_artifacts = {
            "event_graph": self.out_dir / "event_graph.json",
            "event_graph_report": self.out_dir / "event_graph_report.md",
            "analytics_trend": self.out_dir / "analytics_trend.json",
            "analytics_trend_report": self.out_dir / "analytics_trend.md",
        }
        for name, path in optional_artifacts.items():
            if path.exists():
                artifacts[name] = str(path)
        record = KernelRecord(
            kernel_id=ir.ir_id,
            result=result,
            task_id=ir.task_id,
            project_id=ir.project_id,
            mode=mode,
            created_at=now_iso(),
            stages=self.stages,
            artifacts=artifacts,
            runner=runner_summary,
        )
        write_json(self.out_dir / "kernel_record.json", record.to_dict())
        return record

    def _run_optimized_task(
        self,
        *,
        task_path: Path,
        env_path: Path,
        mode: str,
        tag: str,
        allow_side_effects: bool,
        manage_session: bool,
        runtime_strict: bool,
        max_retries: int,
    ) -> Dict[str, Any]:
        started = now_iso()
        cmd = [
            sys.executable,
            str(self.scripts_dir / "run_optimized_task.py"),
            "--task",
            str(task_path),
            "--env-file",
            str(env_path),
            "--mode",
            mode,
            "--out-root",
            str(self.out_dir / "optimized"),
            "--max-retries",
            str(max_retries),
        ]
        if tag:
            cmd.extend(["--tag", tag])
        if allow_side_effects:
            cmd.append("--allow-side-effects")
        if manage_session:
            cmd.append("--manage-session")
        if runtime_strict:
            cmd.append("--runtime-strict")
        write_json(self.out_dir / "runner_command.json", {"cmd": cmd, "cmdline": _quote_cmd(cmd)})
        completed = subprocess.run(
            cmd,
            cwd=str(self.workspace_root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout = completed.stdout or ""
        (self.out_dir / "runner_stdout.log").write_text(stdout, encoding="utf-8")
        summary = self._parse_runner_output(stdout)
        summary.update({"returncode": completed.returncode, "stdout": str(self.out_dir / "runner_stdout.log"), "cmd": cmd})
        self.stage("run_optimized_task", summary.get("result", "UNKNOWN"), started, {"returncode": completed.returncode, "run_root": summary.get("run_root", "")})
        return summary

    def _parse_runner_output(self, stdout: str) -> Dict[str, Any]:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        run_root = ""
        for line in lines:
            if "optimized" in line and ("Polaris" in line or "cucumber-agent-testing" in line):
                candidate = Path(line)
                if not candidate.is_absolute():
                    candidate = (self.workspace_root / candidate).resolve()
                if candidate.exists():
                    run_root = str(candidate)
        match = re.search(r"result=(?P<result>[A-Z_]+)\s+stability=(?P<stability>[A-Z_]+)(?:\s+attempts=(?P<attempts>\d+))?", stdout)
        return {
            "result": match.group("result") if match else ("FAIL" if "returncode=1" in stdout else "UNKNOWN"),
            "stability": match.group("stability") if match else "",
            "attempts": int(match.group("attempts") or 0) if match else 0,
            "run_root": run_root,
        }

    def _build_runner_sidecars(self, runner_summary: Dict[str, Any]) -> None:
        run_root = Path(str(runner_summary.get("run_root", "") or ""))
        if not run_root.exists():
            return
        execution_record = next(run_root.rglob("execution_record.json"), None)
        if execution_record:
            write_json(self.out_dir / "runner_execution_record_ref.json", {"execution_record": str(execution_record)})
        timeline_files = list(run_root.rglob("runtime_replay/*/timeline.json"))
        if not timeline_files:
            return
        timeline = _timeline_from_json(timeline_files[0])
        graph = build_event_graph(timeline)
        write_json(self.out_dir / "event_graph.json", graph.to_dict())
        (self.out_dir / "event_graph_report.md").write_text(render_event_graph_markdown(graph), encoding="utf-8")
        self.stage("event_graph", "PASS", now_iso(), {"nodes": len(graph.nodes), "edges": len(graph.edges), "warnings": len(graph.warnings)})
