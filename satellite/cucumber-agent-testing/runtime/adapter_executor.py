#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Execute or plan actions from the Device Adapter Registry."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .device_adapter import AdapterAction, AdapterRegistry


PLACEHOLDER_RE = re.compile(r"\{(?P<name>[A-Za-z0-9_.-]+)\}")


@dataclass
class AdapterActionResult:
    adapter_id: str
    action: str
    result: str
    reason: str
    cmd: List[str] = field(default_factory=list)
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    side_effect: bool = False
    dry_run: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def find_action(registry: AdapterRegistry, adapter_id: str, action_name: str) -> tuple[Optional[AdapterAction], str]:
    for adapter in registry.adapters:
        if adapter.adapter_id != adapter_id:
            continue
        for action in adapter.actions:
            if action.name == action_name:
                return action, ""
        return None, f"adapter {adapter_id} exists but action {action_name} was not found"
    return None, f"adapter {adapter_id} was not found"


def render_command(template: List[str], params: Dict[str, Any]) -> tuple[List[str], List[str]]:
    missing: List[str] = []
    rendered: List[str] = []
    for raw in template:
        text = str(raw)
        for match in PLACEHOLDER_RE.finditer(text):
            key = match.group("name")
            if key not in params or str(params.get(key, "")).strip() == "":
                missing.append(key)
        for key, value in params.items():
            text = text.replace("{" + key + "}", str(value))
        rendered.append(sys.executable if text.lower() == "python" else text)
    return rendered, sorted(set(missing))


def execute_adapter_action(
    registry: AdapterRegistry,
    *,
    adapter_id: str,
    action_name: str,
    params: Dict[str, Any],
    allow_side_effects: bool = False,
    dry_run: bool = True,
    cwd: Optional[Path] = None,
    timeout_s: int = 120,
) -> AdapterActionResult:
    action, error = find_action(registry, adapter_id, action_name)
    if action is None:
        return AdapterActionResult(adapter_id, action_name, "BLOCKED", error, dry_run=dry_run)
    cmd, missing = render_command(action.command_template, params)
    if missing:
        return AdapterActionResult(
            adapter_id,
            action_name,
            "BLOCKED",
            f"missing action parameters: {', '.join(missing)}",
            cmd=cmd,
            side_effect=action.side_effect,
            dry_run=dry_run,
        )
    if not cmd:
        return AdapterActionResult(
            adapter_id,
            action_name,
            "BLOCKED",
            "adapter action has no command_template",
            side_effect=action.side_effect,
            dry_run=dry_run,
        )
    if action.side_effect and not allow_side_effects and not dry_run:
        return AdapterActionResult(
            adapter_id,
            action_name,
            "BLOCKED",
            "side-effect action requires --allow-side-effects",
            cmd=cmd,
            side_effect=True,
            dry_run=dry_run,
        )
    if dry_run:
        return AdapterActionResult(
            adapter_id,
            action_name,
            "PLAN_OK",
            "adapter command rendered; dry-run did not execute it",
            cmd=cmd,
            side_effect=action.side_effect,
            dry_run=True,
        )

    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
    )
    return AdapterActionResult(
        adapter_id,
        action_name,
        "PASS" if completed.returncode == 0 else "FAIL",
        f"adapter command exited with returncode={completed.returncode}",
        cmd=cmd,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        side_effect=action.side_effect,
        dry_run=False,
    )
