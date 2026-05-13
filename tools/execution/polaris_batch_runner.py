#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path
from typing import List

import yaml

from tools.execution.polaris_case_runner import run_case
from tools.core.polaris_runtime import current_session_dir, new_artifact_dir


def load_suite(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_suite(suite_path: Path, device_key: str = "") -> Path:
    session_dir = current_session_dir()
    suite = load_suite(suite_path)
    execution_dir = new_artifact_dir(f"suite_run_{suite['suite_id']}", session_dir)
    results: List[dict] = []
    for case_entry in suite["cases"]:
        case_path = Path(case_entry)
        if not case_path.is_absolute():
            case_path = (Path.cwd() / case_path).resolve()
        result_path = run_case(case_path, device_key=device_key)
        result = json.loads(Path(result_path).read_text(encoding="utf-8"))
        results.append(result)

    counts = {
        "PASS": sum(1 for item in results if item["diagnosis"]["result"] == "PASS"),
        "FAIL": sum(1 for item in results if item["diagnosis"]["result"] == "FAIL"),
        "BLOCKED": sum(1 for item in results if item["diagnosis"]["result"] == "BLOCKED"),
        "total": len(results),
    }
    summary = {
        "suite_id": suite["suite_id"],
        "name": suite["name"],
        "description": suite.get("description", ""),
        "session_dir": str(session_dir),
        "execution_dir": str(execution_dir),
        "counts": counts,
        "cases": [
            {
                "case_id": item["case_id"],
                "name": item["name"],
                "result": item["diagnosis"]["result"],
                "failure_type": item["diagnosis"]["failure_type"],
                "root_cause": item["diagnosis"]["suspected_root_cause"],
                "reason": item["diagnosis"]["reason"],
                "execution_dir": item["execution_dir"],
            }
            for item in results
        ],
    }
    out_path = execution_dir / "suite_result.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# {suite['suite_id']}",
        "",
        f"- 名称: `{suite['name']}`",
        f"- 总数: `{counts['total']}`",
        f"- PASS: `{counts['PASS']}`",
        f"- FAIL: `{counts['FAIL']}`",
        f"- BLOCKED: `{counts['BLOCKED']}`",
        "",
        "| case_id | result | failure_type | root_cause | execution_dir |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in summary["cases"]:
        lines.append(
            f"| `{item['case_id']}` | `{item['result']}` | `{item['failure_type'] or 'PASS'}` | `{item['root_cause'] or 'none'}` | `{item['execution_dir']}` |"
        )
    (execution_dir / "suite_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polaris batch runner")
    parser.add_argument("--suite-file", required=True)
    parser.add_argument("--device-key", default="")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    out_path = run_suite(Path(args.suite_file), device_key=args.device_key)
    print(out_path)


if __name__ == "__main__":
    main()
