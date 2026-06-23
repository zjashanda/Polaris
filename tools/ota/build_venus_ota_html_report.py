#!/usr/bin/env python3
"""Build an email-safe VenusA+WS63 OTA analysis report."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ota.venus_ota_stats import parse_rounds, read_text_best_effort, summarize


TOKENS = [
    "ASSERT",
    "hardfault",
    "crash",
    "CORE1 HALTED",
    "Exception on CORE1",
    "not support flash",
    "Boot Reason: AON",
    "RESET=0x1",
    "hasNewVer\":false",
    "OTA update success",
]


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def td(value: object, color: str = "#111827") -> str:
    return f'<td style="border:1px solid #d1d5db;padding:6px 8px;color:{color};font-size:13px;">{esc(value)}</td>'


def th(value: object) -> str:
    return f'<th style="border:1px solid #9ca3af;padding:7px 8px;background:#f3f4f6;color:#111827;font-size:13px;text-align:left;">{esc(value)}</th>'


def table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    head = "".join(th(item) for item in headers)
    body = "".join("<tr>" + "".join(td(cell) for cell in row) + "</tr>" for row in rows)
    return f'<table style="border-collapse:collapse;width:100%;margin:8px 0 14px 0;">' f"<tr>{head}</tr>{body}</table>"


def find_stdout(task_dir: Path, stdout_log: str) -> Path:
    if stdout_log:
        path = Path(stdout_log)
        return path if path.is_absolute() else task_dir / path
    candidate = task_dir / "stdout.log"
    if candidate.is_file():
        return candidate
    matches = sorted(task_dir.glob("*stdout*.log"))
    if matches:
        return matches[0]
    raise SystemExit(f"stdout log was not found under {task_dir}; pass --stdout-log.")


def scan_anomalies(task_dir: Path) -> Dict[str, object]:
    logs = sorted(task_dir.glob("*.log"))
    counts = {token: 0 for token in TOKENS}
    samples: List[Tuple[str, int, str]] = []
    for log_path in logs:
        text = read_text_best_effort(log_path)
        for line_no, line in enumerate(text.splitlines(), 1):
            matched = False
            for token in TOKENS:
                if token.lower() in line.lower():
                    counts[token] += 1
                    matched = True
            if matched and len(samples) < 25:
                samples.append((log_path.name, line_no, line.strip()[:240]))
    fatal_tokens = ["ASSERT", "hardfault", "crash", "CORE1 HALTED", "Exception on CORE1", "not support flash"]
    has_fatal = any(counts.get(token, 0) for token in fatal_tokens)
    return {"counts": counts, "samples": samples, "has_fatal": has_fatal, "log_count": len(logs)}


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def build_report(task_dir: Path, stdout_log: Path, output: Path, attachment_root: Path) -> Dict[str, object]:
    stdout_text = read_text_best_effort(stdout_log)
    rounds = parse_rounds(stdout_text)
    summary = summarize(rounds)
    anomalies = scan_anomalies(task_dir)
    completed = summary["completed_rounds"]
    success = summary["script_success_count"]
    fail = summary["script_fail_count"]
    success_rate = f"{(success / completed * 100):.1f}%" if completed else "N/A"
    verdict_fail = bool(fail or anomalies["has_fatal"])
    verdict = "OTA 压测不通过" if verdict_fail else "OTA 压测未发现明确失败"
    conclusion_style = (
        "background:#fef2f2;border:2px solid #b91c1c;color:#7f1d1d;"
        if verdict_fail
        else "background:#ecfdf5;border:2px solid #047857;color:#064e3b;"
    )
    token_rows = [(k, v) for k, v in anomalies["counts"].items() if v]
    if not token_rows:
        token_rows = [("未检出重点异常 token", 0)]
    sample_rows = anomalies["samples"] or [("无", "", "未检出重点异常样例")]
    round_rows = [
        ("启动轮次", summary["started_rounds"]),
        ("完成轮次", completed),
        ("脚本成功", success),
        ("脚本失败", fail),
        ("脚本成功率", success_rate),
        ("下载断电轮次", summary["download_break_count"]),
        ("升级断电轮次", summary["upgrade_break_count"]),
        ("下载断网轮次", summary["download_net_break_count"]),
        ("下载断电+断网轮次", summary["download_power_net_break_count"]),
    ]
    log_paths = [relative_to_root(path, attachment_root) for path in sorted(task_dir.glob("*.log"))]
    if not log_paths:
        log_paths = [relative_to_root(stdout_log, attachment_root)]

    content = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>{esc(verdict)}</title></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Microsoft YaHei,SimSun,Arial,sans-serif;color:#111827;">
<table style="width:100%;border-collapse:collapse;background:#f9fafb;"><tr><td style="padding:20px;">
<table style="width:920px;max-width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #e5e7eb;"><tr><td style="padding:20px;">
<h1 style="margin:0 0 12px 0;font-size:22px;color:#111827;">VenusA+WS63 OTA 分析报告</h1>
<div style="{conclusion_style}padding:12px;margin:0 0 16px 0;">
<div style="font-size:18px;font-weight:bold;margin-bottom:6px;">重点结论：{esc(verdict)}</div>
<div style="font-size:14px;">完成 {completed} 轮，脚本成功 {success} 轮，脚本失败 {fail} 轮，成功率 {esc(success_rate)}。重点异常 token 数：{sum(anomalies["counts"].values())}。</div>
</div>
<h2 style="font-size:18px;color:#111827;margin:14px 0 8px 0;">一、测试项</h2>
<p style="font-size:14px;line-height:1.7;margin:0 0 8px 0;">测试对象为 VenusA+WS63 OTA 自动化任务，统计随机断电/断网轮次、OTA 完成情况、脚本判定和重点异常日志。</p>
{table(["指标", "值"], round_rows)}
<h2 style="font-size:18px;color:#111827;margin:14px 0 8px 0;">二、测试步骤</h2>
<p style="font-size:14px;line-height:1.7;margin:0 0 8px 0;">自动化脚本按轮次触发 OTA，依据配置在下载阶段、升级阶段或网络阶段注入故障，采集 stdout、VenusA、WS63 和控制口日志，并在轮次结束时记录版本、环境、重启和 OTA step。</p>
<h2 style="font-size:18px;color:#111827;margin:14px 0 8px 0;">三、测试结果</h2>
{table(["异常/事件 token", "次数"], token_rows)}
<h2 style="font-size:18px;color:#111827;margin:14px 0 8px 0;">四、测试分析</h2>
<p style="font-size:14px;line-height:1.7;margin:0 0 8px 0;">若存在 ASSERT、hardfault、CORE1 异常、not support flash 或干净 OTA 过程中的 AON，应优先作为失败驱动分析；hasNewVer:false 且未进入 OTA 时应归为未推送/无效样本。</p>
{table(["日志", "行号", "样例"], sample_rows)}
<h2 style="font-size:18px;color:#111827;margin:14px 0 8px 0;">五、日志附件路径</h2>
{table(["路径"], [(item,) for item in log_paths])}
</td></tr></table>
</td></tr></table>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return {
        "verdict": verdict,
        "output": str(output),
        "summary": summary,
        "anomalies": anomalies,
        "stdout_log": str(stdout_log),
        "task_dir": str(task_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build email-safe VenusA+WS63 OTA HTML report.")
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--stdout-log", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--attachment-root", default="")
    args = parser.parse_args()
    task_dir = Path(args.task_dir).resolve()
    stdout_log = find_stdout(task_dir, args.stdout_log).resolve()
    attachment_root = Path(args.attachment_root).resolve() if args.attachment_root else task_dir.parent.resolve()
    output = Path(args.output) if args.output else task_dir / f"{task_dir.name}_analysis_report_email.html"
    if not output.is_absolute():
        output = task_dir / output
    result = build_report(task_dir, stdout_log, output.resolve(), attachment_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
