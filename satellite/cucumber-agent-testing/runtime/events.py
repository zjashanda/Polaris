#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Common event model used by the Polaris validation runtime.

The runtime keeps assertions away from raw grep results. Log parsers convert
serial/playback/cloud lines into these stable event records first.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
HOST_TS_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
)


@dataclass(frozen=True)
class ValidationEvent:
    event_id: str
    timestamp: str
    timestamp_ms: Optional[int]
    source: str
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    file: str = ""
    line_no: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_host_timestamp(line: str) -> tuple[str, Optional[int]]:
    match = HOST_TS_RE.search(line)
    if not match:
        return "", None
    text = match.group("ts")
    try:
        dt = datetime.fromisoformat(text)
        return text, int(dt.timestamp() * 1000)
    except Exception:
        return text, None


def stable_event_id(path: Path, line_no: int, event_type: str, raw: str) -> str:
    material = f"{path.as_posix()}:{line_no}:{event_type}:{raw}".encode("utf-8", errors="replace")
    return "evt_" + hashlib.sha1(material).hexdigest()[:16]


def make_event(
    *,
    path: Path,
    line_no: int,
    raw: str,
    source: str,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
) -> ValidationEvent:
    timestamp, timestamp_ms = parse_host_timestamp(raw)
    clean = strip_ansi(raw.rstrip("\n"))
    return ValidationEvent(
        event_id=stable_event_id(path, line_no, event_type, clean),
        timestamp=timestamp,
        timestamp_ms=timestamp_ms,
        source=source,
        event_type=event_type,
        payload=payload or {},
        raw=clean,
        file=str(path),
        line_no=line_no,
    )
