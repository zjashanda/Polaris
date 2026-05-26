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


@dataclass
class RuntimeStateMachine:
    state: str = "IDLE"
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
            )
        )

    def run(self, events: List[ValidationEvent]) -> "RuntimeStateMachine":
        for event in events:
            self.apply(event)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_state": self.state,
            "history": [item.__dict__ for item in self.history],
        }
