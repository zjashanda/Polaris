#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from tools.core.polaris_runtime import current_session_dir, new_artifact_dir, queue_command, read_lines_between


ROOT = Path(__file__).resolve().parents[2]
PS_COMMON = """
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Networking.Connectivity.NetworkInformation, Windows, ContentType=WindowsRuntime]
$null=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows, ContentType=WindowsRuntime]
$profile=[Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
$mgr=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
$config=$mgr.GetCurrentAccessPointConfiguration()
""".strip()
WB_KEYWORDS = [
    "connect_route:user_ssid=",
    "vir ssid:",
    "Appliance boot up success.",
    "Cur router rssi get failed.",
    "Cur router rssi=",
    "conn scan fail",
    "route info upload ok",
    "get heartbeat from cloud",
]
AP_KEYWORDS = [
    "cloud.online.reply",
    "device.event.keepAlive.ack",
    "Do not upload log since wifi offline",
    "bootloader application",
]
TETHERING_RESULT_TYPE = "[Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]"


def now_iso_ms() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def run_powershell(script: str) -> Dict[str, Any]:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"powershell failed: {completed.returncode}")
    text = completed.stdout.strip()
    if not text:
        return {}
    return json.loads(text)


def hotspot_status() -> Dict[str, Any]:
    script = f"""
{PS_COMMON}
$obj=[ordered]@{{
  ts=(Get-Date).ToString('s')
  operational_state=[string]$mgr.TetheringOperationalState
  client_count=[int]$mgr.ClientCount
  max_client_count=[int]$mgr.MaxClientCount
  ssid=[string]$config.Ssid
  passphrase=[string]$config.Passphrase
  band=[string]$config.Band
  clients=@($mgr.GetTetheringClients() | ForEach-Object {{
    [ordered]@{{
      mac_address=[string]$_.MacAddress
      host_names=@($_.HostNames | ForEach-Object {{ $_.CanonicalName }})
    }}
  }})
}}
$obj | ConvertTo-Json -Depth 6 -Compress
""".strip()
    return run_powershell(script)


def hotspot_set(enable: bool) -> Dict[str, Any]:
    action_name = "StartTetheringAsync" if enable else "StopTetheringAsync"
    script = f"""
{PS_COMMON}
$asTask=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 }} | Select-Object -First 1)
$task=$asTask.MakeGenericMethod({TETHERING_RESULT_TYPE}).Invoke($null, @($mgr.{action_name}()))
$task.Wait()
$result=$task.Result
$obj=[ordered]@{{
  ts=(Get-Date).ToString('s')
  requested_state={'$true' if enable else '$false'}
  op_status=[string]$result.Status
  additional_error=[string]$result.AdditionalErrorMessage
  operational_state=[string]$mgr.TetheringOperationalState
  client_count=[int]$mgr.ClientCount
}}
$obj | ConvertTo-Json -Depth 4 -Compress
""".strip()
    return run_powershell(script)


def command_window(
    port: str,
    command: str,
    session_dir: Path,
    settle_s: float = 1.5,
) -> Dict[str, Any]:
    start_dt = datetime.now()
    queue_command(port, command, session_dir=session_dir)
    time.sleep(settle_s)
    end_dt = datetime.now()
    lines = read_lines_between(port, start_dt, end_dt, session_dir=session_dir)
    return {
        "port": port,
        "command": command,
        "started_at": start_dt.isoformat(timespec="milliseconds"),
        "ended_at": end_dt.isoformat(timespec="milliseconds"),
        "lines": lines,
    }


def filter_lines(lines: List[str], keywords: List[str]) -> List[str]:
    lowered = [item.lower() for item in keywords]
    return [line for line in lines if any(token in line.lower() for token in lowered)]


def collect_window(session_dir: Path, start_dt: datetime, end_dt: datetime, artifact_dir: Path, label: str) -> Dict[str, Any]:
    wb_lines = read_lines_between("COM13", start_dt, end_dt, session_dir=session_dir)
    ap_lines = read_lines_between("COM14", start_dt, end_dt, session_dir=session_dir)
    cp_lines = read_lines_between("COM12", start_dt, end_dt, session_dir=session_dir)
    wb_excerpt = filter_lines(wb_lines, WB_KEYWORDS)
    ap_excerpt = filter_lines(ap_lines, AP_KEYWORDS)
    (artifact_dir / f"{label}_COM13.log").write_text("\n".join(wb_lines) + "\n", encoding="utf-8")
    (artifact_dir / f"{label}_COM14.log").write_text("\n".join(ap_lines) + "\n", encoding="utf-8")
    (artifact_dir / f"{label}_COM12.log").write_text("\n".join(cp_lines) + "\n", encoding="utf-8")
    (artifact_dir / f"{label}_COM13_excerpt.log").write_text("\n".join(wb_excerpt) + "\n", encoding="utf-8")
    (artifact_dir / f"{label}_COM14_excerpt.log").write_text("\n".join(ap_excerpt) + "\n", encoding="utf-8")
    return {
        "label": label,
        "start": start_dt.isoformat(timespec="milliseconds"),
        "end": end_dt.isoformat(timespec="milliseconds"),
        "wb_excerpt": wb_excerpt,
        "ap_excerpt": ap_excerpt,
        "analysis": analyze_window(wb_excerpt, ap_excerpt),
    }


def analyze_window(wb_lines: List[str], ap_lines: List[str]) -> Dict[str, Any]:
    connect_route = [line for line in wb_lines if "connect_route:user_ssid=" in line]
    vir_ssid = [line for line in wb_lines if "vir ssid:" in line.lower()]
    conn_scan_fail = [line for line in wb_lines if "conn scan fail" in line.lower()]
    rssi_fail = [line for line in wb_lines if "cur router rssi get failed" in line.lower()]
    rssi_ok = [line for line in wb_lines if "cur router rssi=" in line.lower() and "failed" not in line.lower()]
    cloud_login = [line for line in ap_lines if "cloud.online.reply" in line.lower()]
    keepalive = [line for line in ap_lines if "device.event.keepalive.ack" in line.lower()]
    wifi_offline = [line for line in ap_lines if "do not upload log since wifi offline" in line.lower()]
    return {
        "connect_route_count": len(connect_route),
        "vir_ssid_count": len(vir_ssid),
        "conn_scan_fail_count": len(conn_scan_fail),
        "rssi_fail_count": len(rssi_fail),
        "rssi_ok_count": len(rssi_ok),
        "cloud_login_count": len(cloud_login),
        "keepalive_count": len(keepalive),
        "wifi_offline_count": len(wifi_offline),
        "connect_route_lines": connect_route,
        "vir_ssid_lines": vir_ssid,
        "conn_scan_fail_lines": conn_scan_fail,
        "rssi_fail_lines": rssi_fail,
        "rssi_ok_lines": rssi_ok,
        "cloud_login_lines": cloud_login,
        "keepalive_lines": keepalive,
        "wifi_offline_lines": wifi_offline,
    }


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def action_hotspot_status(args: argparse.Namespace) -> None:
    payload = hotspot_status()
    if args.output:
        write_json(Path(args.output), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def action_hotspot_cycle(args: argparse.Namespace) -> None:
    session_dir = current_session_dir()
    artifact_dir = Path(args.output_dir) if args.output_dir else new_artifact_dir("hotspot_cycle", session_dir)
    before_status = hotspot_status()
    stop_start = datetime.now()
    stop_result = hotspot_set(False)
    time.sleep(float(args.off_wait))
    stop_end = datetime.now()
    after_stop_status = hotspot_status()
    off_window = collect_window(session_dir, stop_start, stop_end, artifact_dir, "after_stop")

    start_start = datetime.now()
    start_result = hotspot_set(True)
    time.sleep(float(args.on_wait))
    start_end = datetime.now()
    after_start_status = hotspot_status()
    on_window = collect_window(session_dir, start_start, start_end, artifact_dir, "after_start")

    summary = {
        "action": "hotspot-cycle",
        "artifact_dir": str(artifact_dir),
        "session_dir": str(session_dir),
        "before_status": before_status,
        "stop_result": stop_result,
        "after_stop_status": after_stop_status,
        "off_window": off_window,
        "start_result": start_result,
        "after_start_status": after_start_status,
        "on_window": on_window,
    }
    write_json(artifact_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def action_vir_reboot(args: argparse.Namespace) -> None:
    session_dir = current_session_dir()
    artifact_dir = Path(args.output_dir) if args.output_dir else new_artifact_dir("vir_reboot", session_dir)
    before_status = hotspot_status()
    commands = [
        command_window("COM13", f"listen flash set string vir_ssid {args.ssid}", session_dir=session_dir),
        command_window("COM13", f"listen flash set string vir_pwd {args.pwd}", session_dir=session_dir),
        command_window("COM13", "listen flash show", session_dir=session_dir, settle_s=2.5),
    ]
    for index, entry in enumerate(commands, 1):
        write_json(artifact_dir / f"command_{index:02d}.json", entry)

    reboot_start = datetime.now()
    queue_command("COM13", "reboot", session_dir=session_dir)
    time.sleep(float(args.wait))
    reboot_end = datetime.now()
    after_status = hotspot_status()
    reboot_window = collect_window(session_dir, reboot_start, reboot_end, artifact_dir, "after_reboot")
    summary = {
        "action": "vir-reboot",
        "artifact_dir": str(artifact_dir),
        "session_dir": str(session_dir),
        "target_ssid": args.ssid,
        "target_pwd": args.pwd,
        "before_hotspot_status": before_status,
        "commands": commands,
        "after_hotspot_status": after_status,
        "reboot_window": reboot_window,
    }
    write_json(artifact_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polaris network orchestration helper")
    sub = parser.add_subparsers(dest="action", required=True)

    status = sub.add_parser("hotspot-status", help="print current Windows mobile hotspot status")
    status.add_argument("--output", default=None)
    status.set_defaults(handler=action_hotspot_status)

    hotspot_cycle = sub.add_parser("hotspot-cycle", help="turn hotspot off and on while collecting serial evidence")
    hotspot_cycle.add_argument("--off-wait", type=float, default=35.0)
    hotspot_cycle.add_argument("--on-wait", type=float, default=60.0)
    hotspot_cycle.add_argument("--output-dir", default=None)
    hotspot_cycle.set_defaults(handler=action_hotspot_cycle)

    vir_reboot = sub.add_parser("vir-reboot", help="write vir_ssid/vir_pwd, reboot WB01, and collect evidence")
    vir_reboot.add_argument("--ssid", required=True)
    vir_reboot.add_argument("--pwd", required=True)
    vir_reboot.add_argument("--wait", type=float, default=60.0)
    vir_reboot.add_argument("--output-dir", default=None)
    vir_reboot.set_defaults(handler=action_vir_reboot)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
