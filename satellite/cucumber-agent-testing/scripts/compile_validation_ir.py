#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile a task + env file into Polaris Validation IR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from polaris_env import load_env_payload, resolve_env_path


SCRIPT_DIR = Path(__file__).resolve().parent
BDD_ROOT = SCRIPT_DIR.parents[0]
WORKSPACE_ROOT = SCRIPT_DIR.parents[2]
if str(BDD_ROOT) not in sys.path:
    sys.path.insert(0, str(BDD_ROOT))

from runtime.validation_ir import build_validation_ir  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile Polaris Validation IR")
    parser.add_argument("--task", required=True)
    parser.add_argument("--env-file", default="polaris.local.json")
    parser.add_argument("--mode", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--allow-side-effects", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = (WORKSPACE_ROOT / task_path).resolve()
    env_path = resolve_env_path(args.env_file, WORKSPACE_ROOT)
    ir = build_validation_ir(
        task=load_json(task_path),
        env_payload=load_env_payload(env_path),
        task_path=str(task_path),
        env_file=str(env_path),
        mode=args.mode,
        allow_side_effects=args.allow_side_effects,
        tag=args.tag,
    )
    out = Path(args.out) if args.out else BDD_ROOT / "debug" / "validation_ir" / f"{ir.project_id}_{ir.task_id}.json"
    if not out.is_absolute():
        out = (WORKSPACE_ROOT / out).resolve()
    write_json(out, ir.to_dict())
    print(out)
    print(f"ir_id={ir.ir_id} constraints={ir.constraints.get('result')}")
    return 0 if ir.constraints.get("result") != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
