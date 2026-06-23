#!/usr/bin/env python3
"""Polaris wrapper for VenusA+WS63 automatic firmware burning."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
BURN_TOOL_DIR = ROOT / "tools" / "VenusA+WS63"
DEFAULT_DEBUG_ROOT = ROOT / "satellite" / "cucumber-agent-testing" / "debug"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project_config(env_file: Path, project_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    data = load_json(env_file)
    active_project = project_id or data.get("active_project")
    if not active_project:
        raise SystemExit("active_project is not configured and --project was not provided.")
    projects = data.get("projects") or {}
    project = projects.get(active_project)
    if not project:
        raise SystemExit(f"Project {active_project!r} was not found in {env_file}.")
    return active_project, project


def get_serial_ports(project: Dict[str, Any], args: argparse.Namespace) -> Dict[str, str]:
    serial_cfg = project.get("serial") or {}
    ports = serial_cfg.get("ports") or {}
    venusa_port = args.venusa_port or ports.get("ap") or ""
    ws63_port = args.ws63_port or ports.get("upper") or ports.get("asr") or ""
    control_port = args.control_port or ports.get("control") or ""
    if not control_port:
        raise SystemExit("Control port is missing. Set projects.<id>.serial.ports.control or pass --control-port.")
    if not args.skip_venusa and not venusa_port:
        raise SystemExit("VenusA/AP port is missing. Set projects.<id>.serial.ports.ap or pass --venusa-port.")
    if not args.skip_ws63 and not ws63_port:
        raise SystemExit("WS63/upper port is missing. Set projects.<id>.serial.ports.upper/asr or pass --ws63-port.")
    return {"venusa": venusa_port, "ws63": ws63_port, "control": control_port}


def run_capture(command: List[str], cwd: Optional[Path] = None, timeout_s: int = 30) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
        )
        return {"command": command, "returncode": proc.returncode, "output": proc.stdout}
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return {"command": command, "returncode": None, "output": str(exc), "error": type(exc).__name__}


def collect_preflight() -> Dict[str, Any]:
    preflight: Dict[str, Any] = {
        "burn_tool_dir_exists": BURN_TOOL_DIR.is_dir(),
        "auto_burn_exists": (BURN_TOOL_DIR / "auto_burn.py").is_file(),
        "venusa_tool_exists": (BURN_TOOL_DIR / "VenusA_Burn" / "Uart_Burn_Tool.exe").is_file(),
        "ws63_tool_exists": (BURN_TOOL_DIR / "BurnTool_Gold" / "BurnTool.exe").is_file(),
        "platform": platform.platform(),
        "python": sys.executable,
    }
    preflight["list_ports"] = run_capture([sys.executable, "-m", "serial.tools.list_ports", "-v"], timeout_s=20)
    if os.name == "nt":
        ps = (
            "Get-CimInstance Win32_Process | "
            "? { $_.Name -like 'python*' -and "
            "($_.CommandLine -like '*auto_burn.py*' -or $_.CommandLine -like '*otaPartitaForMidea-test_burn.py*') } | "
            "select ProcessId,CommandLine | ConvertTo-Json -Compress"
        )
        preflight["busy_python_processes"] = run_capture(
            ["powershell", "-NoProfile", "-Command", ps],
            timeout_s=20,
        )
    return preflight


def is_zip(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".zip"


def contains_firmware(root: Path) -> bool:
    venus = any((root / name).is_file() for name in ("fw.hex", "fw.img"))
    venus = venus or any(((root / "VenusA") / name).is_file() for name in ("fw.hex", "fw.img"))
    ws63 = any(root.rglob("*.fwpkg"))
    return bool(venus and ws63)


def locate_firmware_root(root: Path) -> Path:
    if contains_firmware(root):
        return root.resolve()
    candidates = [path for path in root.rglob("*") if path.is_dir() and contains_firmware(path)]
    candidates.sort(key=lambda item: (len(item.relative_to(root).parts), str(item).lower()))
    if candidates:
        return candidates[0].resolve()
    raise SystemExit(f"Unable to locate VenusA/WS63 firmware files under {root}.")


def prepare_firmware(firmware: Path, extract_root: Path, force_extract: bool = False) -> Dict[str, Any]:
    if not firmware.exists():
        raise SystemExit(f"Firmware path does not exist: {firmware}")
    if firmware.is_dir():
        root = locate_firmware_root(firmware)
        return {"input": str(firmware), "firmware_root": str(root), "extracted": False}
    if not is_zip(firmware):
        raise SystemExit(f"Unsupported firmware file type: {firmware}")

    target = extract_root / firmware.stem
    if force_extract and target.exists():
        shutil.rmtree(target)
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(firmware, "r") as zf:
            zf.extractall(target)
    root = locate_firmware_root(target)
    return {"input": str(firmware), "extract_dir": str(target), "firmware_root": str(root), "extracted": True}


def build_auto_burn_command(args: argparse.Namespace, firmware_root: Path, ports: Dict[str, str]) -> List[str]:
    cmd = [
        sys.executable,
        "-u",
        "auto_burn.py",
        "--firmware-root",
        str(firmware_root),
        "--control-port",
        ports["control"],
        "--control-baud",
        str(args.control_baud),
        "--venusa-firmware-type",
        args.venusa_firmware_type,
        "--ws63-burn-timeout-ms",
        str(args.ws63_burn_timeout_ms),
    ]
    if args.skip_venusa:
        cmd.append("--skip-venusa")
    else:
        cmd.extend(["--venusa-port", ports["venusa"], "--venusa-baud", str(args.venusa_baud)])
    if args.skip_ws63:
        cmd.append("--skip-ws63")
    else:
        cmd.extend(
            [
                "--ws63-port",
                ports["ws63"],
                "--ws63-signal-baud",
                str(args.ws63_signal_baud),
                "--ws63-at-baud",
                str(args.ws63_at_baud),
            ]
        )
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def cmd_with_codepage(command: List[str]) -> List[str]:
    if os.name != "nt":
        return command
    quoted = subprocess.list2cmdline(command)
    return [
        "cmd",
        "/c",
        f'chcp 936 >nul && set "PYTHONIOENCODING=utf-8" && set "PYTHONUTF8=1" && {quoted}',
    ]


def run_streaming(command: List[str], cwd: Path, output_log: Path) -> int:
    output_log.parent.mkdir(parents=True, exist_ok=True)
    with output_log.open("w", encoding="utf-8", errors="replace") as log_fp:
        proc = subprocess.Popen(
            cmd_with_codepage(command),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            log_fp.write(line)
            log_fp.flush()
        return proc.wait()


def write_markdown_summary(path: Path, summary: Dict[str, Any]) -> None:
    verdict = summary.get("verdict", "UNKNOWN")
    lines = [
        "# VenusA+WS63 自动烧录结果",
        "",
        f"- 结论：`{verdict}`",
        f"- 项目：`{summary.get('project_id', '')}`",
        f"- 固件根目录：`{summary.get('firmware', {}).get('firmware_root', '')}`",
        f"- VenusA/AP 串口：`{summary.get('ports', {}).get('venusa', '')}`",
        f"- WS63 串口：`{summary.get('ports', {}).get('ws63', '')}`",
        f"- 控制串口：`{summary.get('ports', {}).get('control', '')}`",
        f"- dry-run：`{summary.get('dry_run')}`",
        f"- 返回码：`{summary.get('returncode')}`",
        f"- stdout：`{summary.get('stdout_log', '')}`",
        "",
        "## 后续建议",
    ]
    if summary.get("dry_run"):
        lines.append("- dry-run 仅验证命令构造；真实烧录需追加 `--allow-side-effects` 且去掉 `--dry-run`。")
    elif verdict == "PASS":
        lines.append("- 烧录脚本返回成功；继续执行 version/deviceinfo、联网、唤醒和识别验证。")
    else:
        lines.append("- 烧录未通过；优先查看 stdout 与 WS63 optLog，按 VenusA 成功/WS63 失败分支决定是否 `--skip-venusa` 重试。")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Polaris VenusA+WS63 automatic burn flow.")
    parser.add_argument("--firmware", required=True, help="Firmware zip or extracted firmware root.")
    parser.add_argument("--env-file", default=str(ROOT / "polaris.local.json"))
    parser.add_argument("--project", default=None)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--extract-root", default=str(ROOT / "tools" / "fw" / "extracted"))
    parser.add_argument("--force-extract", action="store_true")
    parser.add_argument("--allow-side-effects", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-venusa", action="store_true")
    parser.add_argument("--skip-ws63", action="store_true")
    parser.add_argument("--control-port")
    parser.add_argument("--venusa-port")
    parser.add_argument("--ws63-port")
    parser.add_argument("--control-baud", type=int, default=115200)
    parser.add_argument("--venusa-baud", type=int, default=3000000)
    parser.add_argument("--venusa-firmware-type", choices=["auto", "hex", "img"], default="auto")
    parser.add_argument("--ws63-signal-baud", type=int, default=1000000)
    parser.add_argument("--ws63-at-baud", type=int, default=921600)
    parser.add_argument("--ws63-burn-timeout-ms", type=int, default=600000)
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    if args.skip_venusa and args.skip_ws63:
        raise SystemExit("--skip-venusa and --skip-ws63 cannot both be set.")
    if not args.dry_run and not args.allow_side_effects:
        raise SystemExit("Real burn changes firmware. Re-run with --allow-side-effects, or use --dry-run.")

    env_file = Path(args.env_file).resolve()
    project_id, project = load_project_config(env_file, args.project)
    ports = get_serial_ports(project, args)
    run_dir = Path(args.output_dir) if args.output_dir else DEFAULT_DEBUG_ROOT / "firmware_burn" / f"{now_stamp()}_venusws63_burn"
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    firmware = prepare_firmware(Path(args.firmware).resolve(), Path(args.extract_root).resolve(), args.force_extract)
    firmware_root = Path(firmware["firmware_root"]).resolve()
    preflight = collect_preflight()
    command = build_auto_burn_command(args, firmware_root, ports)

    summary: Dict[str, Any] = {
        "schema": "polaris.venusws63_auto_burn.v1",
        "project_id": project_id,
        "env_file": str(env_file),
        "firmware": firmware,
        "ports": ports,
        "dry_run": bool(args.dry_run),
        "allow_side_effects": bool(args.allow_side_effects),
        "preflight": preflight,
        "command": command,
        "run_dir": str(run_dir),
    }
    write_json(run_dir / "preflight.json", summary)

    stdout_log = run_dir / "auto_burn_stdout.log"
    if args.dry_run:
        stdout_log.write_text(subprocess.list2cmdline(command) + "\n", encoding="utf-8")
        returncode = 0
    else:
        returncode = run_streaming(command, BURN_TOOL_DIR, stdout_log)

    summary["returncode"] = returncode
    summary["stdout_log"] = str(stdout_log)
    summary["verdict"] = "PASS" if returncode == 0 else "FAIL"
    write_json(run_dir / "summary.json", summary)
    write_markdown_summary(run_dir / "summary.md", summary)
    print(f"Summary: {run_dir / 'summary.md'}")
    return 0 if returncode == 0 else returncode


if __name__ == "__main__":
    raise SystemExit(main())
