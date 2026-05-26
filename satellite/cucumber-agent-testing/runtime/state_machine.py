#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small explicit state machine for runtime replay.

This is intentionally conservative. It is used to make the current device state
visible in replay packages; formal assertions still live in assertion_engine.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .events import ValidationEvent


TRANSITIONS = {
    "AudioInjected": "WAKE_PENDING",
    "WakeDetected": "LISTENING",
    "ASRDetected": "ASR_PROCESSING",
    "CommandDetected": "ASR_PROCESSING",
    "TTSStarted": "TTS_PLAYING",
    "MediaStarted": "MEDIA_PLAYING",
    "InterruptInjected": "MEDIA_PLAYING",
    "InterruptCompleted": "MEDIA_PLAYING",
    "MediaCompleted": "LISTENING",
    "NetworkLost": "NETWORK_LOST",
    "NetworkRecovered": "IDLE",
    "RebootDetected": "REBOOTING",
    "CrashDetected": "CRASHED",
}


@dataclass
class StateSnapshot:
    state: str
    event_id: str
    event_type: str
    timestamp: str
    timestamp_ms: int | None
    timestamp_wall: str = ""
    timestamp_wall_ms: int | None = None
    timestamp_monotonic_ms: int | None = None
    plugin: str = ""


@dataclass
class RuntimeStateMachine:
    state: str = "IDLE"
    audio_state: str = "IDLE"
    recognition_state: str = "IDLE"
    media_state: str = "IDLE"
    network_state: str = "UNKNOWN"
    power_state: str = "ON"
    cloud_state: str = "UNKNOWN"
    history: List[StateSnapshot] = field(default_factory=list)

    def apply(self, event: ValidationEvent) -> None:
        next_state = TRANSITIONS.get(event.event_type)
        if not next_state:
            return
        self.state = next_state
        self.history.append(
            StateSnapshot(
                state=self.state,
                event_id=event.event_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                timestamp_ms=event.timestamp_ms,
                timestamp_wall=event.timestamp_wall,
                timestamp_wall_ms=event.timestamp_wall_ms,
                timestamp_monotonic_ms=event.timestamp_monotonic_ms,
                plugin=event.plugin,
            )
        )
        self._apply_parallel_states(event)

    def _apply_parallel_states(self, event: ValidationEvent) -> None:
        if event.event_type == "AudioInjected":
            self.audio_state = "INJECTING"
            self.recognition_state = "WAKE_PENDING"
        elif event.event_type == "AudioCompleted":
            self.audio_state = "IDLE"
        elif event.event_type == "WakeDetected":
            self.recognition_state = "LISTENING"
        elif event.event_type in {"ASRDetected", "CommandDetected"}:
            self.recognition_state = "RECOGNIZING"
        elif event.event_type == "TTSStarted":
            self.media_state = "TTS_PLAYING"
            self.cloud_state = "RESPONDING" if event.source in {"ap", "asr", "upper", "ws63"} else self.cloud_state
        elif event.event_type == "MediaStarted":
            self.media_state = "MEDIA_PLAYING"
        elif event.event_type in {"MediaCompleted", "InterruptCompleted"}:
            self.media_state = "IDLE"
        elif event.event_type == "NetworkLost":
            self.network_state = "OFFLINE"
            self.cloud_state = "UNAVAILABLE"
        elif event.event_type == "NetworkRecovered":
            self.network_state = "ONLINE"
            self.cloud_state = "AVAILABLE"
        elif event.event_type == "RebootDetected":
            self.power_state = "REBOOTING"
            self.recognition_state = "RESETTING"
            self.media_state = "IDLE"
        elif event.event_type == "CrashDetected":
            self.power_state = "CRASHED"
            self.recognition_state = "UNKNOWN"

    def run(self, events: List[ValidationEvent]) -> "RuntimeStateMachine":
        for event in events:
            self.apply(event)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_state": self.state,
            "parallel_states": {
                "audio": self.audio_state,
                "recognition": self.recognition_state,
                "media": self.media_state,
                "network": self.network_state,
                "power": self.power_state,
                "cloud": self.cloud_state,
            },
            "history": [item.__dict__ for item in self.history],
        }
