#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Device adapter registry for the local Polaris runtime.

This module does not replace the existing tools.  It gives the runtime a stable
description of the adapters that those tools already provide, so schedulers,
constraints and reports can reason about device access without hard-coded
project branches.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


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
class AdapterAction:
    name: str
    kind: str
    command_template: List[str] = field(default_factory=list)
    side_effect: bool = False
    resources: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceAdapter:
    adapter_id: str
    kind: str
    status: str
    resources: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    actions: List[AdapterAction] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        item = asdict(self)
        item["actions"] = [action.to_dict() for action in self.actions]
        return item


@dataclass
class AdapterRegistry:
    project_id: str
    project_type: str
    adapters: List[DeviceAdapter]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "polaris.adapter_registry.v1",
            "project_id": self.project_id,
            "project_type": self.project_type,
            "adapter_count": len(self.adapters),
            "warnings": self.warnings,
            "adapters": [adapter.to_dict() for adapter in self.adapters],
        }


def _serial_adapter(role: str, port: str, baudrate: str, *, writable: bool) -> DeviceAdapter:
    role_label = role.lower()
    status = "available" if port else "disabled"
    actions = [
        AdapterAction(
            name="log",
            kind="serial_log",
            command_template=[
                "python",
                "tools/device/polaris_serial_harness.py",
                "start",
                f"--{role_label}-port",
                port,
                "--baudrate",
                baudrate,
            ],
            side_effect=False,
            resources=[f"serial:{port}"] if port else [],
        )
    ]
    if writable:
        actions.append(
            AdapterAction(
                name="send",
                kind="serial_write",
                command_template=[
                    "python",
                    "tools/device/polaris_serial_harness.py",
                    "send",
                    "--role",
                    role_label,
                    "--command",
                    "{command}",
                ],
                side_effect=True,
                resources=[f"serial:{port}"] if port else [],
            )
        )
    return DeviceAdapter(
        adapter_id=f"serial.{role_label}",
        kind="serial",
        status=status,
        resources=[f"serial:{port}"] if port else [],
        capabilities=[f"{role_label}_log"] + ([f"{role_label}_write"] if writable else []),
        actions=actions if port else [],
        config={"role": role_label, "port": port, "baudrate": baudrate, "writable": writable},
        warnings=[] if port else [f"{role_label} port is empty"],
    )


def build_adapter_registry(env_payload: Dict[str, Any]) -> AdapterRegistry:
    project_id = _text(env_payload.get("project_id") or _nested(env_payload, "_config_source", "active_project"))
    project_type = _text(env_payload.get("project_type"))
    ports = _nested(env_payload, "serial", "ports")
    ports = ports if isinstance(ports, dict) else {}
    baudrate = _text(_nested(env_payload, "serial", "baudrate") or env_payload.get("baudrate") or "115200")
    control_baudrate = _text(_nested(env_payload, "serial", "control_baudrate") or baudrate)

    adapters: List[DeviceAdapter] = [
        _serial_adapter("ap", _text(ports.get("ap")), baudrate, writable=True),
        _serial_adapter("cp", _text(ports.get("cp")), baudrate, writable=False),
        _serial_adapter("asr", _text(ports.get("asr") or ports.get("upper")), baudrate, writable=True),
    ]

    control_port = _text(ports.get("control"))
    control_actions = [
        AdapterAction(
            name="send_control",
            kind="serial_control",
            command_template=[
                "python",
                "tools/device/polaris_power_control.py",
                "send",
                "--port",
                control_port,
                "--baudrate",
                control_baudrate,
                "--command",
                "{command}",
            ],
            side_effect=True,
            resources=[f"serial:{control_port}"] if control_port else [],
            notes=["PA and power-control commands must be sent through the control port."],
        )
    ]
    adapters.append(
        DeviceAdapter(
            adapter_id="control.serial",
            kind="power_control",
            status="available" if control_port else "disabled",
            resources=[f"serial:{control_port}"] if control_port else [],
            capabilities=["power_control", "pa_control"] if control_port else [],
            actions=control_actions if control_port else [],
            config={
                "port": control_port,
                "baudrate": control_baudrate,
                "preconditions": _nested(env_payload, "serial", "control_preconditions") or [],
            },
            warnings=[] if control_port else ["control port is empty"],
        )
    )

    audio_key = _text(_nested(env_payload, "audio", "default_playback_device_key"))
    adapters.append(
        DeviceAdapter(
            adapter_id="audio.playback",
            kind="audio",
            status="available",
            resources=[f"audio:{audio_key or 'DEFAULT_RENDER_DEVICE'}"],
            capabilities=["audio_playback", "wake_audio_injection"],
            actions=[
                AdapterAction(
                    name="play",
                    kind="audio_playback",
                    command_template=[
                        "python",
                        "listenai_play.py",
                        "play",
                        "--audio-file",
                        "{audio_file}",
                    ]
                    + (["--device-key", audio_key] if audio_key else []),
                    side_effect=True,
                    resources=[f"audio:{audio_key or 'DEFAULT_RENDER_DEVICE'}"],
                )
            ],
            config={"device_key": audio_key or "DEFAULT_RENDER_DEVICE", "volume": _nested(env_payload, "audio", "playback_volume")},
        )
    )

    wifi_ssid = _text(_nested(env_payload, "network", "wifi_ssid"))
    hotspot_enabled = bool(_nested(env_payload, "network", "enable_hotspot_control"))
    adapters.append(
        DeviceAdapter(
            adapter_id="network.local",
            kind="network",
            status="available" if wifi_ssid or hotspot_enabled else "config_required",
            resources=["network:wifi"],
            capabilities=(["wifi_config"] if wifi_ssid else []) + (["hotspot_control"] if hotspot_enabled else []),
            actions=[
                AdapterAction(name="hotspot_cycle", kind="network_control", side_effect=True, resources=["network:wifi"])
            ]
            if hotspot_enabled
            else [],
            config={"wifi_ssid": wifi_ssid, "enable_hotspot_control": hotspot_enabled},
            warnings=[] if wifi_ssid or hotspot_enabled else ["wifi_ssid and hotspot control are not configured"],
        )
    )

    api_env = _text(_nested(env_payload, "cloud", "api_environment"))
    device_env = _text(_nested(env_payload, "cloud", "device_env"))
    adapters.append(
        DeviceAdapter(
            adapter_id="cloud.api",
            kind="cloud",
            status="available" if api_env else "config_required",
            resources=[f"cloud:{api_env or 'UNKNOWN'}"],
            capabilities=["cloud_api", "device_env_switch"] if api_env else [],
            actions=[
                AdapterAction(name="set_device_env", kind="cloud_or_serial_config", side_effect=True, resources=[f"cloud:{api_env}"]),
                AdapterAction(name="call_api", kind="cloud_api", side_effect=True, resources=[f"cloud:{api_env}"]),
            ]
            if api_env
            else [],
            config={
                "api_environment": api_env,
                "device_env": device_env,
                "device_env_command": _nested(env_payload, "cloud", "device_env_command"),
                "device_env_reboot_required": bool(_nested(env_payload, "cloud", "device_env_reboot_required")),
            },
            warnings=[] if api_env else ["cloud api_environment is empty"],
        )
    )

    warnings = [warning for adapter in adapters for warning in adapter.warnings]
    return AdapterRegistry(project_id=project_id, project_type=project_type, adapters=adapters, warnings=warnings)
