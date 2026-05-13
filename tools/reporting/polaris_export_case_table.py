#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openpyxl import Workbook

from tools.core.polaris_runtime import current_session_dir, new_artifact_dir, resolve_artifact_reference


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_case_index(case_id: str) -> int:
    match = re.search(r"_(\d+)$", case_id)
    return int(match.group(1)) if match else 10**9


def read_result_meta(case: Dict[str, Any]) -> Dict[str, Any]:
    session_dir = current_session_dir(ROOT)
    result_path = resolve_artifact_reference(case.get("result_path", ""), session_dir=session_dir) if case.get("result_path") else None
    execution_dir = resolve_artifact_reference(case.get("execution_dir", ""), session_dir=session_dir) if case.get("execution_dir") else None
    started_at = ""
    ended_at = ""
    judge_reason = ""
    failed_names: List[str] = []

    if result_path and result_path.exists():
        payload = load_json(result_path)
        started_at = str(payload.get("started_at", "") or "")
        ended_at = str(payload.get("ended_at", "") or "")

    judge_path = (execution_dir / "judge.json") if execution_dir else None
    if judge_path and judge_path.exists():
        judge = load_json(judge_path)
        judge_reason = str(judge.get("reason", "") or "")
        failed_names = [
            str(item.get("name", "")).strip()
            for item in judge.get("checks", [])
            if not bool(item.get("passed", True))
        ]

    if not failed_names:
        failed_names = [
            str(item.get("name", "")).strip()
            for item in case.get("failed_checks", [])
            if not bool(item.get("passed", True))
        ]

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "judge_reason": judge_reason,
        "failed_check_names": failed_names,
    }


def build_rows(status: Dict[str, Any], scope: str, executed_only: bool) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in status.get("cases", []):
        if scope and case.get("classification") != scope:
            continue
        if executed_only and not str(case.get("result", "")).strip():
            continue
        meta = read_result_meta(case)
        row = {
            "case_id": case.get("case_id", ""),
            "name": case.get("name", ""),
            "mode": case.get("mode", ""),
            "priority": case.get("priority", ""),
            "classification": case.get("classification", ""),
            "runner_kind": case.get("runner_kind", ""),
            "result": case.get("result", ""),
            "started_at": meta["started_at"],
            "ended_at": meta["ended_at"],
            "judge_reason": meta["judge_reason"],
            "failed_check_names": ", ".join(meta["failed_check_names"]),
            "execution_dir": case.get("execution_dir", ""),
            "result_path": case.get("result_path", ""),
        }
        rows.append(row)
    rows.sort(key=lambda item: (parse_case_index(str(item["case_id"])), str(item["case_id"])))
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    columns = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def auto_fit_columns(ws) -> None:
    for column_cells in ws.columns:
        letter = column_cells[0].column_letter
        max_len = 0
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            if len(value) > max_len:
                max_len = len(value)
        ws.column_dimensions[letter].width = min(max(max_len + 2, 12), 60)


def write_xlsx(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "summary"
    ws_summary.append(["metric", "value"])
    ws_summary.append(["exported_at", summary["exported_at"]])
    ws_summary.append(["scope", summary["scope"]])
    ws_summary.append(["row_count", summary["row_count"]])
    ws_summary.append(["result_counts", json.dumps(summary["result_counts"], ensure_ascii=False)])
    ws_summary.append(["runner_kind_counts", json.dumps(summary["runner_kind_counts"], ensure_ascii=False)])
    auto_fit_columns(ws_summary)

    ws_detail = wb.create_sheet("details")
    columns = list(rows[0].keys()) if rows else []
    if columns:
        ws_detail.append(columns)
        for row in rows:
            ws_detail.append([row.get(column, "") for column in columns])
    auto_fit_columns(ws_detail)
    wb.save(path)


def write_md(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# Polaris 初版用例执行结果表")
    lines.append("")
    lines.append(f"- 导出时间: `{summary['exported_at']}`")
    lines.append(f"- 状态文件更新时间: `{summary['status_updated_at']}`")
    lines.append(f"- 导出范围: `{summary['scope']}`")
    lines.append(f"- 用例数量: `{summary['row_count']}`")
    lines.append(f"- 结果分布: `{json.dumps(summary['result_counts'], ensure_ascii=False)}`")
    effective_counts = summary.get("status_effective_counts") or {}
    if effective_counts:
        lines.append(f"- 状态总表: `{json.dumps(effective_counts, ensure_ascii=False)}`")
    lines.append("")
    lines.append("## 前 20 条详情")
    lines.append("")
    lines.append("| case_id | result | mode | runner_kind | name | failed_checks |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for row in rows[:20]:
        lines.append(
            f"| {row['case_id']} | {row['result']} | {row['mode']} | {row['runner_kind']} | "
            f"{row['name']} | {row['failed_check_names']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_table(status_path: Path, scope: str, executed_only: bool) -> Path:
    status = load_json(status_path)
    session_dir = current_session_dir(ROOT)
    artifact_dir = new_artifact_dir("case_result_table", session_dir=session_dir)

    rows = build_rows(status, scope=scope, executed_only=executed_only)
    result_counts = Counter(str(row.get("result", "") or "EMPTY") for row in rows)
    runner_counts = Counter(str(row.get("runner_kind", "") or "EMPTY") for row in rows)
    summary = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "status_updated_at": status.get("updated_at", ""),
        "scope": scope,
        "row_count": len(rows),
        "result_counts": dict(result_counts),
        "runner_kind_counts": dict(runner_counts),
        "status_effective_counts": status.get("effective_counts_after_recheck", {}),
        "source_status": str(status_path),
    }

    (artifact_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(artifact_dir / "case_result_table.csv", rows)
    write_xlsx(artifact_dir / "case_result_table.xlsx", rows, summary)
    write_md(artifact_dir / "case_result_table.md", rows, summary)
    print(json.dumps({"artifact_dir": str(artifact_dir), "summary": summary}, ensure_ascii=False, indent=2))
    return artifact_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export current Polaris case execution table")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=ROOT / "config" / "polaris_doc_case_status.json",
    )
    parser.add_argument("--scope", default="auto_executable_now")
    parser.add_argument("--executed-only", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    export_table(status_path=args.status_path, scope=args.scope, executed_only=args.executed_only)


if __name__ == "__main__":
    main()
