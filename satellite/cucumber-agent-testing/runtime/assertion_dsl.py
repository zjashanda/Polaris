#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tiny assertion DSL compiler for replay timelines.

Supported examples:
- EXPECT WakeDetected
- EXPECT WakeDetected WITHIN 3000ms AFTER AudioInjected
- FORBID RebootDetected FOR 10000ms AFTER WakeDetected
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .assertion_engine import assert_event_exists, assert_event_within_ms, assert_no_event_during
from .timeline import Timeline


EXPECT_WITHIN_RE = re.compile(r"^EXPECT\s+(?P<event>\w+)\s+WITHIN\s+(?P<ms>\d+)ms(?:\s+AFTER\s+(?P<anchor>\w+))?$", re.I)
EXPECT_RE = re.compile(r"^EXPECT\s+(?P<event>\w+)$", re.I)
FORBID_RE = re.compile(r"^FORBID\s+(?P<event>\w+)\s+FOR\s+(?P<ms>\d+)ms(?:\s+AFTER\s+(?P<anchor>\w+))?$", re.I)


def evaluate_dsl(lines: List[str], timeline: Timeline) -> Dict[str, Any]:
    assertions = []
    for raw in lines:
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        match = EXPECT_WITHIN_RE.match(line)
        if match:
            assertions.append(
                assert_event_within_ms(
                    timeline,
                    match.group("event"),
                    within_ms=int(match.group("ms")),
                    anchor_event_type=match.group("anchor") or "AudioInjected",
                ).to_dict()
            )
            continue
        match = EXPECT_RE.match(line)
        if match:
            assertions.append(assert_event_exists(timeline, match.group("event")).to_dict())
            continue
        match = FORBID_RE.match(line)
        if match:
            assertions.append(
                assert_no_event_during(
                    timeline,
                    match.group("event"),
                    duration_ms=int(match.group("ms")),
                    anchor_event_type=match.group("anchor"),
                ).to_dict()
            )
            continue
        assertions.append({"name": "dsl_parse", "result": "FAIL", "reason": f"unsupported DSL: {line}", "actual": {"line": line}})
    result = "FAIL" if any(item.get("result") == "FAIL" for item in assertions) else "PASS"
    return {"schema": "polaris.assertion_dsl_result.v1", "result": result, "assertions": assertions}
