#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Timeline utilities for event-based validation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .events import ValidationEvent


SOURCE_GROUPS = {
    "ap": {"ap", "cskap"},
    "cp": {"cp", "cskcp"},
    "asr": {"asr", "upper", "ws63", "wb01"},
    "audio": {"audio", "playback"},
    "control": {"control"},
}


def normalize_source(source: str) -> str:
    text = (source or "").strip().lower()
    for group, aliases in SOURCE_GROUPS.items():
        if text == group or text in aliases:
            return group
    return text


@dataclass
class Timeline:
    events: List[ValidationEvent]

    @classmethod
    def from_events(cls, events: Iterable[ValidationEvent]) -> "Timeline":
        deduped: List[ValidationEvent] = []
        seen: set[tuple[str, str]] = set()
        for event in events:
            key = (event.event_type, event.raw)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(event)
        sorted_events = sorted(
            deduped,
            key=lambda event: (
                event.timestamp_ms if event.timestamp_ms is not None else 10**18,
                event.file,
                event.line_no,
                event.event_id,
            ),
        )
        return cls(sorted_events)

    @property
    def start_ms(self) -> Optional[int]:
        for event in self.events:
            if event.timestamp_ms is not None:
                return event.timestamp_ms
        return None

    def find(
        self,
        event_type: Optional[str] = None,
        *,
        source: Optional[str] = None,
        sources: Optional[Sequence[str]] = None,
        after_ms: Optional[int] = None,
        before_ms: Optional[int] = None,
    ) -> List[ValidationEvent]:
        wanted_sources = {normalize_source(item) for item in sources or []}
        if source:
            wanted_sources.add(normalize_source(source))
        result: List[ValidationEvent] = []
        for event in self.events:
            if event_type and event.event_type != event_type:
                continue
            if wanted_sources and normalize_source(event.source) not in wanted_sources:
                continue
            if after_ms is not None and event.timestamp_ms is not None and event.timestamp_ms < after_ms:
                continue
            if before_ms is not None and event.timestamp_ms is not None and event.timestamp_ms > before_ms:
                continue
            result.append(event)
        return result

    def first(self, event_type: str, *, source: Optional[str] = None) -> Optional[ValidationEvent]:
        events = self.find(event_type, source=source)
        return events[0] if events else None

    def counts(self) -> Dict[str, int]:
        return dict(Counter(event.event_type for event in self.events))

    def counts_by_source(self, event_type: str) -> Dict[str, int]:
        return dict(Counter(normalize_source(event.source) for event in self.find(event_type)))

    def to_dict(self) -> Dict[str, Any]:
        start = self.start_ms
        serialized = []
        for event in self.events:
            item = event.to_dict()
            item["source_group"] = normalize_source(event.source)
            item["relative_ms"] = (
                event.timestamp_ms - start
                if start is not None and event.timestamp_ms is not None
                else None
            )
            serialized.append(item)
        return {
            "event_count": len(self.events),
            "start_timestamp_ms": start,
            "event_counts": self.counts(),
            "events": serialized,
        }
