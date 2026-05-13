#!/usr/bin/env python3
"""Local configuration helpers for Polaris tools.

`config/polaris_local_ports.json` is the local override file. Tools should read
ports from it when a CLI option is omitted, and sync explicit CLI choices back
to it so later commands inherit the latest mapping.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LOCAL_PORT_CONFIG = ROOT / "config" / "polaris_local_ports.json"
ENV_CONFIG = ROOT / "config" / "polaris_env.json"

DEFAULT_PORTS = {
    "ap": "COM14",
    "cskap": "COM14",
    "cp": "COM12",
    "cskcp": "COM12",
    "asr": "COM13",
    "control": "COM15",
}
DEFAULT_BAUDRATE = 115200
ROLE_ALIASES = {
    "cskap": "ap",
    "ap_uart": "ap",
    "cskcp": "cp",
    "cp_uart": "cp",
    "wb01": "asr",
    "wb": "asr",
    "power": "control",
    "power_control": "control",
}

CANONICAL_LOG_PORTS = {
    "cp": "COM12",
    "asr": "COM13",
    "ap": "COM14",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_port(value: str) -> str:
    return str(value).strip().upper()


def normalize_role(role: str) -> str:
    key = str(role).strip().lower().replace("-", "_")
    return ROLE_ALIASES.get(key, key)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_from_env() -> dict[str, Any]:
    env = read_json(ENV_CONFIG)
    ports = dict(DEFAULT_PORTS)
    env_ports = env.get("ports", {}) if isinstance(env.get("ports"), dict) else {}
    for role in ("ap", "cp", "asr", "control"):
        value = env_ports.get(role) or env_ports.get("wb01" if role == "asr" else role)
        if value:
            ports[role] = normalize_port(value)
    ports["cskap"] = ports["ap"]
    ports["cskcp"] = ports["cp"]

    payload = {
        "updated_at": now_iso(),
        "source": "seeded-from-polaris-env",
        "baudrate": int(env.get("baudrate", DEFAULT_BAUDRATE) or DEFAULT_BAUDRATE),
        "ports": ports,
        "aliases": dict(ROLE_ALIASES),
    }
    refresh_role_index(payload)
    return payload


def refresh_role_index(payload: dict[str, Any]) -> dict[str, Any]:
    ports = payload.setdefault("ports", {})
    roles: dict[str, str] = {}
    role_labels = {
        "ap": "cskap",
        "cp": "cskcp",
        "asr": "asr",
        "control": "power-control",
    }
    for role, label in role_labels.items():
        value = ports.get(role) or DEFAULT_PORTS.get(role)
        if value:
            roles[normalize_port(value)] = label
    payload["roles"] = roles
    return payload


def load_port_config(create: bool = True) -> dict[str, Any]:
    payload = read_json(LOCAL_PORT_CONFIG)
    if not payload:
        payload = seed_from_env()
        if create:
            write_json(LOCAL_PORT_CONFIG, payload)
    payload.setdefault("ports", {})
    for key, value in DEFAULT_PORTS.items():
        payload["ports"].setdefault(key, value)
    for key, value in list(payload["ports"].items()):
        if value:
            payload["ports"][key] = normalize_port(value)
    payload["ports"]["cskap"] = payload["ports"].get("ap", DEFAULT_PORTS["ap"])
    payload["ports"]["cskcp"] = payload["ports"].get("cp", DEFAULT_PORTS["cp"])
    payload["ports"]["wb01"] = payload["ports"].get("asr", DEFAULT_PORTS["asr"])
    payload.setdefault("baudrate", DEFAULT_BAUDRATE)
    aliases = payload.setdefault("aliases", {})
    for key, value in ROLE_ALIASES.items():
        aliases.setdefault(key, value)
    refresh_role_index(payload)
    return payload


def save_port_config(payload: dict[str, Any]) -> None:
    payload["updated_at"] = now_iso()
    write_json(LOCAL_PORT_CONFIG, payload)


def get_baudrate(default: int = DEFAULT_BAUDRATE) -> int:
    payload = load_port_config()
    try:
        return int(payload.get("baudrate", default) or default)
    except Exception:
        return default


def set_baudrate(baudrate: int, source: str = "cli") -> None:
    payload = load_port_config()
    payload["baudrate"] = int(baudrate)
    payload.setdefault("history", []).append(
        {"ts": now_iso(), "role": "baudrate", "value": int(baudrate), "source": source}
    )
    save_port_config(payload)


def get_port(role: str, default: str | None = None) -> str:
    key = normalize_role(role)
    payload = load_port_config()
    value = payload.get("ports", {}).get(key)
    if value:
        return normalize_port(value)
    fallback = default or DEFAULT_PORTS.get(key)
    if not fallback:
        raise KeyError(f"unknown Polaris port role: {role}")
    return normalize_port(fallback)


def sync_port(role: str, port: str, source: str = "cli") -> dict[str, Any]:
    key = normalize_role(role)
    payload = load_port_config()
    port_value = normalize_port(port)
    payload.setdefault("ports", {})[key] = port_value
    if key == "ap":
        payload["ports"]["cskap"] = port_value
    if key == "cp":
        payload["ports"]["cskcp"] = port_value
    if key == "asr":
        # Keep old callers alive while the current official name is ASR.
        payload["ports"]["wb01"] = port_value
    refresh_role_index(payload)
    payload.setdefault("history", []).append(
        {"ts": now_iso(), "role": key, "port": port_value, "source": source}
    )
    save_port_config(payload)
    return payload


def resolve_port(role: str, explicit_port: str | None = None, sync_explicit: bool = True, source: str = "cli") -> str:
    if explicit_port:
        port = normalize_port(explicit_port)
        if sync_explicit:
            sync_port(role, port, source=source)
        return port
    return get_port(role)


def serial_logger_ports() -> dict[str, dict[str, Any]]:
    """Return the current log-port map for the continuous serial harness."""
    ap = get_port("ap")
    cp = get_port("cp")
    asr = get_port("asr")
    return {
        cp: {"role": "cskcp", "writable": False},
        asr: {"role": "asr", "writable": True},
        ap: {"role": "cskap", "writable": True},
    }


def configured_log_ports() -> list[str]:
    """Return CP/ASR/AP log ports from local config, preserving order and uniqueness."""
    ports: list[str] = []
    for role in ("cp", "asr", "ap"):
        port = get_port(role)
        if port not in ports:
            ports.append(port)
    return ports


def add_canonical_log_aliases(logs: dict[str, list[str]]) -> dict[str, list[str]]:
    """Expose configured log lines through legacy COM12/COM13/COM14 keys.

    Many older Polaris assertions still key metrics by the original COM names.
    When a local machine remaps ports, this keeps those assertions working while
    still preserving the actual configured-port keys in the evidence payload.
    """
    for role, canonical_port in CANONICAL_LOG_PORTS.items():
        configured_port = get_port(role)
        if canonical_port not in logs and configured_port in logs:
            logs[canonical_port] = logs[configured_port]
    return logs


def cmd_show(_args: argparse.Namespace) -> int:
    print(json.dumps(load_port_config(), ensure_ascii=False, indent=2))
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    payload = None
    if args.port:
        payload = sync_port(args.role, args.port, source="polaris_config.set")
    if args.baudrate is not None:
        set_baudrate(args.baudrate, source="polaris_config.set")
        payload = load_port_config()
    print(json.dumps(payload or load_port_config(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show or update local Polaris serial-port config")
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="print config/polaris_local_ports.json")
    show.set_defaults(func=cmd_show)
    set_cmd = sub.add_parser("set", help="sync an explicit role/port or baudrate into local config")
    set_cmd.add_argument("--role", default="ap", help="ap/cskap, cp/cskcp, asr/wb01, or control")
    set_cmd.add_argument("--port", default=None)
    set_cmd.add_argument("--baudrate", type=int, default=None)
    set_cmd.set_defaults(func=cmd_set)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
