#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Heuristic event graph builder over a replay Timeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .assertion_engine import build_audio_windows, cluster_wake_events
from .events import ValidationEvent
from .timeline import Timeline, normalize_source


@dataclass
class EventGraphNode:
    event_id: str
    event_type: str
    source: str
    timestamp_ms: Optional[int]
    plugin: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EventGraphEdge:
    src: str
    dst: str
    relation: str
    confidence: str = "medium"
    delta_ms: Optional[int] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EventGraph:
    nodes: List[EventGraphNode]
    edges: List[EventGraphEdge]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "polaris.event_graph.v1",
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "warnings": self.warnings,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }


def _summary(event: ValidationEvent) -> str:
    payload = event.payload or {}
    for key in ("recognized_text", "recognized_command", "wake_keyword", "marker"):
        if payload.get(key):
            return str(payload.get(key))[:120]
    return (event.raw or "")[:120]


def _delta(src: ValidationEvent, dst: ValidationEvent) -> Optional[int]:
    if src.timestamp_ms is None or dst.timestamp_ms is None:
        return None
    return int(dst.timestamp_ms - src.timestamp_ms)


def _latest_before(events: List[ValidationEvent], target: ValidationEvent, within_ms: int) -> Optional[ValidationEvent]:
    if target.timestamp_ms is None:
        return None
    candidates = [
        event
        for event in events
        if event.timestamp_ms is not None
        and event.timestamp_ms <= target.timestamp_ms
        and int(target.timestamp_ms - event.timestamp_ms) <= within_ms
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda event: int(event.timestamp_ms or 0))[-1]


def _append_edge(edges: List[EventGraphEdge], edge: EventGraphEdge, seen: set[tuple[str, str, str]]) -> None:
    key = (edge.src, edge.dst, edge.relation)
    if key in seen:
        return
    seen.add(key)
    edges.append(edge)


def build_event_graph(timeline: Timeline) -> EventGraph:
    nodes = [
        EventGraphNode(
            event_id=event.event_id,
            event_type=event.event_type,
            source=normalize_source(event.source),
            timestamp_ms=event.timestamp_ms,
            plugin=event.plugin,
            summary=_summary(event),
        )
        for event in timeline.events
    ]
    edges: List[EventGraphEdge] = []
    seen: set[tuple[str, str, str]] = set()

    for previous, current in zip(timeline.events, timeline.events[1:]):
        _append_edge(
            edges,
            EventGraphEdge(previous.event_id, current.event_id, "timeline_next", confidence="low", delta_ms=_delta(previous, current)),
            seen,
        )

    wakes = timeline.find("WakeDetected")
    asrs = timeline.find("ASRDetected")
    commands = timeline.find("CommandDetected")
    tts_or_media = timeline.find("TTSStarted") + timeline.find("MediaStarted")
    network_lost = timeline.find("NetworkLost")
    network_recovered = timeline.find("NetworkRecovered")
    reboots = timeline.find("RebootDetected") + timeline.find("CrashDetected")

    audio_windows = build_audio_windows(timeline)
    wake_clusters = cluster_wake_events(timeline)
    for cluster in wake_clusters:
        if not cluster.events or cluster.start_ms is None:
            continue
        first = cluster.events[0]
        matched_window = None
        for window in audio_windows:
            if window.start_ms - 800 <= int(cluster.start_ms) <= window.end_ms + 800:
                matched_window = window
                break
        if matched_window:
            effective_start = matched_window.end_ms - int(matched_window.audio_duration_ms or 0) if matched_window.audio_duration_ms else matched_window.start_ms
            _append_edge(
                edges,
                EventGraphEdge(
                    matched_window.start_event_id,
                    first.event_id,
                    "audio_caused_wake",
                    confidence="high" if matched_window.audio_duration_ms else "medium",
                    delta_ms=int(cluster.start_ms - effective_start),
                    reason="wake cluster falls inside audio playback window",
                ),
                seen,
            )

    for asr in asrs:
        wake = _latest_before(wakes, asr, 5000)
        if wake:
            _append_edge(edges, EventGraphEdge(wake.event_id, asr.event_id, "wake_to_asr", "high", _delta(wake, asr)), seen)
    for command in commands:
        asr = _latest_before(asrs, command, 5000)
        if asr:
            _append_edge(edges, EventGraphEdge(asr.event_id, command.event_id, "asr_to_command", "high", _delta(asr, command)), seen)
    for media in tts_or_media:
        asr = _latest_before(asrs, media, 15000)
        wake = _latest_before(wakes, media, 15000)
        if asr:
            _append_edge(edges, EventGraphEdge(asr.event_id, media.event_id, "asr_to_response", "medium", _delta(asr, media)), seen)
        elif wake:
            _append_edge(edges, EventGraphEdge(wake.event_id, media.event_id, "wake_to_response", "medium", _delta(wake, media)), seen)
    for recovered in network_recovered:
        lost = _latest_before(network_lost, recovered, 120000)
        if lost:
            _append_edge(edges, EventGraphEdge(lost.event_id, recovered.event_id, "network_recovered_after_loss", "high", _delta(lost, recovered)), seen)
    for reboot in reboots:
        anchor = _latest_before(wakes + asrs + commands + tts_or_media, reboot, 60000)
        if anchor:
            _append_edge(edges, EventGraphEdge(anchor.event_id, reboot.event_id, "possible_failure_after_activity", "medium", _delta(anchor, reboot)), seen)

    warnings: List[str] = []
    if wakes and not any(edge.relation == "audio_caused_wake" for edge in edges):
        warnings.append("WakeDetected exists but no audio_caused_wake edge was inferred.")
    return EventGraph(nodes=nodes, edges=edges, warnings=warnings)


def render_event_graph_markdown(graph: EventGraph) -> str:
    lines = [
        "# Polaris Event Graph",
        "",
        f"- nodes: `{len(graph.nodes)}`",
        f"- edges: `{len(graph.edges)}`",
        "",
        "## Causal Edges",
        "",
    ]
    causal = [edge for edge in graph.edges if edge.relation != "timeline_next"]
    if not causal:
        lines.append("- <none>")
    for edge in causal:
        delta = "" if edge.delta_ms is None else f", delta={edge.delta_ms}ms"
        lines.append(f"- `{edge.relation}` `{edge.src}` -> `{edge.dst}` ({edge.confidence}{delta}) {edge.reason}")
    if graph.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in graph.warnings:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
