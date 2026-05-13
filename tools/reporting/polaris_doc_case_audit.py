# -*- coding: utf-8 -*-
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from tools.library.polaris_doc_case_lib import classify_doc_case, load_doc_cases, load_env
from tools.execution.polaris_doc_case_runner import run_doc_case
from tools.core.polaris_runtime import current_session_dir, new_artifact_dir



def audit_cases(execute_feasible: bool = False) -> Path:
    session_dir = current_session_dir()
    execution_dir = new_artifact_dir("doc_case_audit", session_dir)
    env = load_env()
    cases = load_doc_cases()

    records: List[dict] = []
    counts: Dict[str, int] = {
        "total": 0,
        "auto_executable_now": 0,
        "executed": 0,
        "pass": 0,
        "fail": 0,
        "blocked": 0,
        "partial": 0,
        "skip": 0,
    }

    for case in cases:
        classification = classify_doc_case(case, env=env)
        record = {
            "case_id": case.case_id,
            "name": case.name,
            "mode": case.level3,
            "priority": case.priority,
            "classification": classification["status"],
            "reason": classification["reason"],
            "runner_kind": classification.get("runner_kind", ""),
            "result": "",
            "execution_dir": "",
        }
        counts["total"] += 1
        if classification["status"] == "auto_executable_now":
            counts["auto_executable_now"] += 1
            if execute_feasible:
                result_path = run_doc_case(case.case_id)
                result = json.loads(Path(result_path).read_text(encoding="utf-8"))
                result_value = result["diagnosis"]["result"].lower()
                counts["executed"] += 1
                counts[result_value] = counts.get(result_value, 0) + 1
                record["result"] = result["diagnosis"]["result"]
                record["execution_dir"] = result["execution_dir"]
                record["reason"] = result["diagnosis"]["reason"]
        else:
            counts["skip"] += 1
        records.append(record)

    summary = {
        "session_dir": str(session_dir),
        "execution_dir": str(execution_dir),
        "counts": counts,
        "cases": records,
    }
    (execution_dir / "audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with (execution_dir / "audit_cases.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["case_id", "name", "mode", "priority", "classification", "result", "reason", "runner_kind", "execution_dir"],
        )
        writer.writeheader()
        writer.writerows(records)

    lines = [
        "# Doc Case Audit",
        "",
        f"- Total: `{counts['total']}`",
        f"- Auto executable now: `{counts['auto_executable_now']}`",
        f"- Executed: `{counts['executed']}`",
        f"- PASS: `{counts['pass']}`",
        f"- PARTIAL: `{counts['partial']}`",
        f"- FAIL: `{counts['fail']}`",
        f"- BLOCKED: `{counts['blocked']}`",
        f"- Skip: `{counts['skip']}`",
        "",
        "| case_id | mode | classification | result | reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in records:
        reason = item["reason"].replace("\n", " ").replace("|", "/")
        lines.append(
            f"| `{item['case_id']}` | `{item['mode']}` | `{item['classification']}` | `{item['result'] or '-'} ` | {reason} |"
        )
    (execution_dir / "audit_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return execution_dir / "audit_summary.json"



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit all doc cases and optionally execute feasible ones")
    parser.add_argument("--execute-feasible", action="store_true")
    return parser



def main() -> None:
    args = build_parser().parse_args()
    out_path = audit_cases(execute_feasible=args.execute_feasible)
    print(out_path)


if __name__ == "__main__":
    main()
