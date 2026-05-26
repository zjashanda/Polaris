#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation IR MVP.

The IR is the deterministic object that a future Kernel/Scheduler can consume.
It is intentionally a wrapper around existing task/env/registry inputs rather
than a new execution engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from .capability_runtime import build_capability_matrix
from .constraint_engine import evaluate_constraints
from .device_adapter import build_adapter_registry
from .resource_runtime import build_resource_snapshot


def _text(value: Any) -> str:
    return str(value or "").strip()


def _nested(payload: Dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


@dataclass
class ValidationIR:
    ir_id: str
    task_id: str
    project_id: str
    mode: str
    scenario_tag: str
    feature: str
    mapping: str
    constraints: Dict[str, Any]
    resources: Dict[str, Any]
    capabilities: Dict[str, Any]
    adapters: Dict[str, Any]
    execution: Dict[str, Any] = field(default_factory=dict)
    source: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = "polaris.validation_ir.v1"
        return payload


def build_validation_ir(
    *,
    task: Dict[str, Any],
    env_payload: Dict[str, Any],
    task_path: str = "",
    env_file: str = "",
    mode: str = "",
    allow_side_effects: bool = False,
    tag: str = "",
) -> ValidationIR:
    runner = task.get("runner", {}) if isinstance(task.get("runner"), dict) else {}
    scenario = task.get("scenario", {}) if isinstance(task.get("scenario"), dict) else {}
    execution = task.get("execution", {}) if isinstance(task.get("execution"), dict) else {}
    resolved_mode = _text(mode or runner.get("mode") or task.get("mode") or "dry-run")
    scenario_tag = _text(tag or scenario.get("tag"))
    task_id = _text(task.get("task_id") or task.get("id") or "task")
    project_id = _text(env_payload.get("project_id") or _nested(env_payload, "_config_source", "active_project"))
    constraints = evaluate_constraints(task=task, env_payload=env_payload, mode=resolved_mode, allow_side_effects=allow_side_effects, tag=scenario_tag)
    resources = build_resource_snapshot(env_payload, task).to_dict()
    capabilities = build_capability_matrix(env_payload).to_dict()
    adapters = build_adapter_registry(env_payload).to_dict()
    return ValidationIR(
        ir_id=f"{project_id}:{task_id}:{scenario_tag or 'all'}:{resolved_mode}",
        task_id=task_id,
        project_id=project_id,
        mode=resolved_mode,
        scenario_tag=scenario_tag,
        feature=_text(runner.get("feature")),
        mapping=_text(runner.get("mapping")),
        constraints=constraints,
        resources=resources,
        capabilities=capabilities,
        adapters=adapters,
        execution=dict(execution),
        source={"task_path": task_path, "env_file": env_file},
    )
