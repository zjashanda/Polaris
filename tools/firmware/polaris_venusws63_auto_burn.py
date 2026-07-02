#!/usr/bin/env python3
"""Polaris wrapper for VenusA+WS63 automatic firmware burning."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
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
PROJECT_VERSION_RE = re.compile(r"Project Version:\s*(?P<version>\S+)")
BUILDINFO_LINE_RE = re.compile(r"^(?P<key>Package Name|Firmware Version|Generated At|VenusA BuildInfo|WS63 BuildInfo):\s*(?P<value>.+)$")
VENUSA_BUILD_RE = re.compile(r"project_mai build info:\s*(?P<build>\S+)")
WS63_BUILD_RE = re.compile(r"ListenAI Build Info:\s*(?P<build>\S+)")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text_safe(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


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


def parse_firmware_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(read_text_safe(path))
    except Exception as exc:
        return {"path": str(path), "error": repr(exc)}
    files = []
    for item in payload.get("files", []) or []:
        files.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "ver": item.get("ver"),
                "size": item.get("size"),
                "md5": item.get("md5"),
            }
        )
    return {"path": str(path), "pkg_ver": payload.get("pkg_ver"), "files": files}


def first_match(path: Path, pattern: re.Pattern[str]) -> str:
    if not path.is_file():
        return ""
    for line in read_text_safe(path).splitlines():
        match = pattern.search(line)
        if match:
            return match.group("build")
    return ""


def all_matches(path: Path, pattern: re.Pattern[str]) -> List[str]:
    if not path.is_file():
        return []
    values: List[str] = []
    for line in read_text_safe(path).splitlines():
        match = pattern.search(line)
        if match:
            values.append(match.group("build"))
    return values


def collect_package_metadata(firmware_root: Path) -> Dict[str, Any]:
    """Read package-internal metadata; never infer version from the zip name alone."""
    metadata: Dict[str, Any] = {
        "firmware_root": str(firmware_root),
        "buildinfo": {},
        "configs": {},
        "venus_build_log_info": "",
        "ws63_build_log_infos": [],
        "firmware_files": {},
    }
    buildinfo_path = firmware_root / "BuildInfo.txt"
    if buildinfo_path.is_file():
        metadata["buildinfo_path"] = str(buildinfo_path)
        for line in read_text_safe(buildinfo_path).splitlines():
            match = BUILDINFO_LINE_RE.match(line.strip())
            if match:
                key = match.group("key").lower().replace(" ", "_")
                metadata["buildinfo"][key] = match.group("value").strip()

    for name in ("config.json", "config_hex.json"):
        metadata["configs"][name] = parse_firmware_config(firmware_root / name)

    other_dir = firmware_root / "Other"
    venus_logs = sorted(other_dir.glob("VenusA_build_*.log")) if other_dir.is_dir() else []
    ws63_logs = sorted(other_dir.glob("WS63_build_*.log")) if other_dir.is_dir() else []
    if venus_logs:
        metadata["venus_build_log"] = str(venus_logs[-1])
        metadata["venus_build_log_info"] = first_match(venus_logs[-1], VENUSA_BUILD_RE)
    if ws63_logs:
        metadata["ws63_build_log"] = str(ws63_logs[-1])
        metadata["ws63_build_log_infos"] = all_matches(ws63_logs[-1], WS63_BUILD_RE)

    for name in ("fw.hex", "fw.img", "ws63-liteos-app_all.fwpkg"):
        path = firmware_root / name
        metadata["firmware_files"][name] = {"exists": path.is_file(), "path": str(path) if path.exists() else ""}

    target_version = str(metadata["buildinfo"].get("firmware_version", "")).strip()
    if not target_version:
        for config in metadata["configs"].values():
            for item in config.get("files", []) if isinstance(config, dict) else []:
                if str(item.get("name", "")).lower() in {"fw.hex", "fw.img"} and item.get("ver"):
                    target_version = str(item["ver"]).strip()
                    break
            if target_version:
                break
    metadata["target_project_version"] = target_version
    return metadata


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


def command_with_codepage(command: List[str], batch_path: Path) -> List[str]:
    if os.name != "nt":
        return command
    cmdline = subprocess.list2cmdline(command)
    batch_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "chcp 936 >nul",
                'set "PYTHONIOENCODING=utf-8"',
                'set "PYTHONUTF8=1"',
                cmdline,
                "exit /b %ERRORLEVEL%",
                "",
            ]
        ),
        encoding="gb18030",
    )
    return ["cmd", "/d", "/c", str(batch_path)]


def run_streaming(command: List[str], cwd: Path, output_log: Path) -> int:
    output_log.parent.mkdir(parents=True, exist_ok=True)
    batch_path = output_log.with_suffix(".run.bat")
    with output_log.open("w", encoding="utf-8", errors="replace") as log_fp:
        proc = subprocess.Popen(
            command_with_codepage(command, batch_path),
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


def smart_decode(data: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def capture_serial_command(port: str, baudrate: int, command: str, timeout_s: float, log_path: Path) -> Dict[str, Any]:
    import serial

    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    started_at = datetime.now().isoformat(timespec="milliseconds")
    with serial.Serial(port, baudrate, timeout=0.2, write_timeout=1.0) as ser:
        try:
            ser.reset_input_buffer()
        except Exception:
            pass
        ser.write((command.rstrip("\r\n") + "\r\n").encode("utf-8"))
        deadline = time.time() + timeout_s
        partial = ""
        while time.time() < deadline:
            chunk = ser.read(ser.in_waiting or 1)
            if not chunk:
                continue
            partial += smart_decode(chunk).replace("\r", "")
            while "\n" in partial:
                line, partial = partial.split("\n", 1)
                if line.strip():
                    lines.append(line.strip())
        if partial.strip():
            lines.append(partial.strip())
    ended_at = datetime.now().isoformat(timespec="milliseconds")
    log_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return {
        "port": port,
        "baudrate": baudrate,
        "command": command,
        "started_at": started_at,
        "ended_at": ended_at,
        "lines": lines,
        "log_path": str(log_path),
    }


def parse_project_version(lines: List[str]) -> str:
    for line in lines:
        match = PROJECT_VERSION_RE.search(line)
        if match:
            return match.group("version").strip()
    return ""


def parse_deviceinfo(lines: List[str]) -> Dict[str, str]:
    patterns = {
        "sn": re.compile(r"\bSN:\s*(?P<value>\S+)", re.I),
        "iot_id": re.compile(r"\bIoT ID:\s*(?P<value>\S+)", re.I),
        "mac": re.compile(r"\bMac:\s*(?P<value>\S+)", re.I),
        "ip": re.compile(r"\bIP:\s*(?P<value>\S+)", re.I),
        "wakeup_id": re.compile(r"\bWakeupID:\s*(?P<value>.+)$", re.I),
    }
    parsed: Dict[str, str] = {}
    for line in lines:
        for key, pattern in patterns.items():
            match = pattern.search(line)
            if match and key not in parsed:
                parsed[key] = match.group("value").strip()
    return parsed


def verify_after_burn(
    args: argparse.Namespace,
    project: Dict[str, Any],
    ports: Dict[str, str],
    package_metadata: Dict[str, Any],
    run_dir: Path,
) -> Dict[str, Any]:
    serial_cfg = project.get("serial") or {}
    baudrate = int(args.verify_baud or serial_cfg.get("baudrate") or 921600)
    verify_dir = run_dir / "post_burn_verify"
    if args.post_burn_wait_s > 0:
        time.sleep(args.post_burn_wait_s)
    version_capture = capture_serial_command(
        ports["venusa"],
        baudrate,
        "version",
        args.verify_timeout_s,
        verify_dir / f"{ports['venusa']}_version.log",
    )
    deviceinfo_capture = capture_serial_command(
        ports["venusa"],
        baudrate,
        "deviceinfo",
        args.verify_timeout_s,
        verify_dir / f"{ports['venusa']}_deviceinfo.log",
    )
    expected = str(package_metadata.get("target_project_version", "")).strip()
    observed = parse_project_version(version_capture["lines"])
    deviceinfo = parse_deviceinfo(deviceinfo_capture["lines"])
    checks = [
        {
            "name": "project_version_matches_package",
            "status": "PASS" if expected and observed == expected else "FAIL",
            "expected": expected,
            "observed": observed,
            "reason": "设备 Project Version 与包内 BuildInfo/config 版本一致。"
            if expected and observed == expected
            else "设备 Project Version 未匹配包内 BuildInfo/config 版本。",
        },
        {
            "name": "deviceinfo_readable",
            "status": "PASS" if deviceinfo.get("sn") or deviceinfo.get("iot_id") else "WARN",
            "observed": deviceinfo,
            "reason": "已读取 deviceinfo。" if deviceinfo else "未从 deviceinfo 中解析到设备身份信息。",
        },
    ]
    payload = {
        "schema": "polaris.venusws63_post_burn_verify.v1",
        "artifact_dir": str(verify_dir),
        "expected_project_version": expected,
        "observed_project_version": observed,
        "version_capture": version_capture,
        "deviceinfo_capture": deviceinfo_capture,
        "deviceinfo": deviceinfo,
        "checks": checks,
        "verdict": "PASS" if all(item["status"] in {"PASS", "WARN"} for item in checks) and checks[0]["status"] == "PASS" else "FAIL",
    }
    write_json(verify_dir / "post_burn_verify.json", payload)
    (verify_dir / "post_burn_verify.md").write_text(
        "\n".join(
            [
                "# VenusA+WS63 烧录后版本核对",
                "",
                f"- 结论：`{payload['verdict']}`",
                f"- 期望版本：`{expected}`",
                f"- 设备版本：`{observed}`",
                f"- SN：`{deviceinfo.get('sn', '')}`",
                f"- IoT ID：`{deviceinfo.get('iot_id', '')}`",
                f"- version 日志：`{version_capture['log_path']}`",
                f"- deviceinfo 日志：`{deviceinfo_capture['log_path']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload


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
        f"- 包内目标版本：`{summary.get('package_metadata', {}).get('target_project_version', '')}`",
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
    verify = summary.get("post_burn_verify") or {}
    if verify:
        lines.extend(
            [
                "",
                "## 烧录后版本核对",
                f"- 结论：`{verify.get('verdict', '')}`",
                f"- 期望版本：`{verify.get('expected_project_version', '')}`",
                f"- 设备版本：`{verify.get('observed_project_version', '')}`",
                f"- 证据目录：`{verify.get('artifact_dir', '')}`",
            ]
        )
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
    parser.add_argument("--verify-after-burn", action="store_true", help="After a successful real burn, read version/deviceinfo and compare with package metadata.")
    parser.add_argument("--verify-timeout-s", type=float, default=10.0)
    parser.add_argument("--verify-baud", type=int, default=0)
    parser.add_argument("--post-burn-wait-s", type=float, default=8.0)
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
    package_metadata = collect_package_metadata(firmware_root)
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
        "package_metadata": package_metadata,
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
    if args.verify_after_burn and not args.dry_run and returncode == 0 and not args.skip_venusa:
        summary["post_burn_verify"] = verify_after_burn(args, project, ports, package_metadata, run_dir)
        if summary["post_burn_verify"].get("verdict") != "PASS":
            summary["verdict"] = "FAIL"
    write_json(run_dir / "summary.json", summary)
    write_markdown_summary(run_dir / "summary.md", summary)
    print(f"Summary: {run_dir / 'summary.md'}")
    return 0 if returncode == 0 else returncode


if __name__ == "__main__":
    raise SystemExit(main())
