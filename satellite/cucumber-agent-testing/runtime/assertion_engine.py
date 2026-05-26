#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temporal assertions over Timeline events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .timeline import Timeline
from .timeline import normalize_source


RECOGNITION_EVENT_TYPES = {
    "WakeDetected",
    "ASRDetected",
    "CommandDetected",
    "CommandUtterancePassed",
    "CommandUtteranceFailed",
    "CommandUtteranceBlocked",
    "CommandUtteranceUnknown",
    "OneshotIntervalPassed",
    "OneshotIntervalFailed",
    "OneshotIntervalBlocked",
    "OneshotIntervalUnknown",
    "OnlineVADCasePassed",
    "OnlineVADCaseFailed",
    "OnlineVADCaseBlocked",
    "OnlineVADCaseUnknown",
    "DocCaseJudgeSummary",
    "DocCaseJudgePassed",
    "DocCaseJudgeFailed",
}


@dataclass
class AssertionResult:
    name: str
    result: str
    reason: str
    actual: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _pass(name: str, reason: str, **actual: Any) -> AssertionResult:
    return AssertionResult(name=name, result="PASS", reason=reason, actual=actual)


def _fail(name: str, reason: str, **actual: Any) -> AssertionResult:
    return AssertionResult(name=name, result="FAIL", reason=reason, actual=actual)


def _skip(name: str, reason: str, **actual: Any) -> AssertionResult:
    return AssertionResult(name=name, result="SKIP", reason=reason, actual=actual)


def _blocked(name: str, reason: str, **actual: Any) -> AssertionResult:
    return AssertionResult(name=name, result="BLOCKED", reason=reason, actual=actual)


def _ambiguous(name: str, reason: str, **actual: Any) -> AssertionResult:
    return AssertionResult(name=name, result="TIMING_AMBIGUOUS", reason=reason, actual=actual)


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if "|" in text:
        return [item.strip() for item in text.split("|") if item.strip()]
    return [text]


def _unique_texts(values: List[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def collect_recognition_observations(timeline: Timeline, *, limit: int = 80) -> Dict[str, Any]:
    """Collect every wake/ASR/command-like observation for later attribution.

    PASS/FAIL assertions decide whether the observation is allowed. This summary
    simply preserves unexpected recognitions so a run never hides "the device
    recognized something we did not say".
    """
    observations: List[Dict[str, Any]] = []
    recognized_texts: List[str] = []
    recognized_commands: List[str] = []
    wake_keywords: List[str] = []
    for event in timeline.events:
        payload = event.payload or {}
        text_carrier = event.event_type == "ASRDetected" or event.event_type.startswith(("CommandUtterance", "OneshotInterval", "OnlineVADCase", "DocCaseJudge"))
        texts = []
        if text_carrier:
            texts = _as_list(payload.get("recognized_text")) + _as_list(payload.get("ap_online_asr_texts")) + _as_list(payload.get("actual_online_asr_texts"))
        commands = _as_list(payload.get("recognized_command")) + _as_list(payload.get("recognized_command_keywords"))
        wake_items = _as_list(payload.get("wake_keyword"))
        if event.event_type not in RECOGNITION_EVENT_TYPES and not texts and not commands and not wake_items:
            continue
        recognized_texts.extend(texts)
        recognized_commands.extend(commands)
        wake_keywords.extend(wake_items)
        if len(observations) < limit:
            observations.append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "source": normalize_source(event.source),
                    "event_type": event.event_type,
                    "marker": payload.get("marker", ""),
                    "recognized_texts": texts,
                    "recognized_commands": commands,
                    "wake_keywords": wake_items,
                    "expected_command": payload.get("command", ""),
                    "result": payload.get("result", ""),
                    "file": event.file,
                    "line_no": event.line_no,
                    "raw": event.raw[:240],
                }
            )
    return {
        "wake_event_count": len(timeline.find("WakeDetected")),
        "asr_event_count": len(timeline.find("ASRDetected")),
        "command_event_count": len(timeline.find("CommandDetected")),
        "recognized_texts": _unique_texts(recognized_texts),
        "recognized_commands": _unique_texts(recognized_commands),
        "wake_keywords": _unique_texts(wake_keywords),
        "observations": observations,
        "truncated": len(observations) >= limit,
    }


@dataclass
class WakeCluster:
    index: int
    start_ms: Optional[int]
    end_ms: Optional[int]
    events: List[Any]

    @property
    def sources(self) -> List[str]:
        return sorted({normalize_source(event.source) for event in self.events})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "sources": self.sources,
            "event_count": len(self.events),
            "event_ids": [event.event_id for event in self.events],
            "markers": [event.payload.get("marker", "") for event in self.events],
        }


@dataclass
class MediaWindow:
    index: int
    start_ms: int
    end_ms: int
    start_event_id: str
    end_event_id: str
    source: str

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "duration_ms": self.duration_ms,
            "start_event_id": self.start_event_id,
            "end_event_id": self.end_event_id,
            "source": self.source,
        }


def cluster_wake_events(timeline: Timeline, *, gap_ms: int = 2500) -> List[WakeCluster]:
    """Group duplicate wake markers from AP/CP/ASR into one physical wake."""
    wake_events = timeline.find("WakeDetected")
    timed = [event for event in wake_events if event.timestamp_ms is not None]
    if not timed:
        if not wake_events:
            return []
        return [WakeCluster(index=0, start_ms=None, end_ms=None, events=wake_events)]

    clusters: List[WakeCluster] = []
    current: List[Any] = []
    current_end: Optional[int] = None
    for event in sorted(timed, key=lambda item: (item.timestamp_ms or 0, item.file, item.line_no, item.event_id)):
        event_ms = event.timestamp_ms or 0
        if current and current_end is not None and event_ms - current_end > gap_ms:
            start = current[0].timestamp_ms
            end = current[-1].timestamp_ms
            clusters.append(WakeCluster(index=len(clusters), start_ms=start, end_ms=end, events=current))
            current = []
        current.append(event)
        current_end = event_ms
    if current:
        clusters.append(WakeCluster(index=len(clusters), start_ms=current[0].timestamp_ms, end_ms=current[-1].timestamp_ms, events=current))
    return clusters


def build_media_windows(timeline: Timeline, *, max_duration_ms: int = 60000) -> List[MediaWindow]:
    starts = [event for event in timeline.find("MediaStarted") if event.timestamp_ms is not None]
    stops = [event for event in timeline.find("MediaCompleted") if event.timestamp_ms is not None]
    starts.sort(key=lambda item: int(item.timestamp_ms or 0))
    stops.sort(key=lambda item: int(item.timestamp_ms or 0))
    used_stops: set[str] = set()
    windows: List[MediaWindow] = []
    for start in starts:
        start_ms = int(start.timestamp_ms or 0)
        candidates = [
            stop
            for stop in stops
            if stop.event_id not in used_stops
            and stop.timestamp_ms is not None
            and int(stop.timestamp_ms) > start_ms
            and int(stop.timestamp_ms) - start_ms <= max_duration_ms
        ]
        if not candidates:
            continue
        stop = candidates[0]
        used_stops.add(stop.event_id)
        windows.append(
            MediaWindow(
                index=len(windows),
                start_ms=start_ms,
                end_ms=int(stop.timestamp_ms or 0),
                start_event_id=start.event_id,
                end_event_id=stop.event_id,
                source=normalize_source(start.source),
            )
        )
    return windows


def _first_wake_cluster_after_audio(
    clusters: List[WakeCluster],
    audio_ms: int,
    *,
    within_ms: int,
) -> Optional[WakeCluster]:
    for cluster in clusters:
        if cluster.start_ms is None:
            continue
        if cluster.start_ms < audio_ms:
            continue
        if cluster.start_ms - audio_ms <= within_ms:
            return cluster
    return None


def _assert_cluster_sources(cluster: WakeCluster, *, cp_log: bool = True, asr_log: bool = True, prefix: str = "wake_cluster") -> AssertionResult:
    expected = ["ap"]
    if cp_log:
        expected.append("cp")
    if asr_log:
        expected.append("asr")
    missing = [source for source in expected if source not in cluster.sources]
    name = f"{prefix}_source_evidence"
    if not missing:
        return _pass(name, f"唤醒簇包含期望来源：{', '.join(expected)}。", sources=cluster.sources, expected=expected)
    return _fail(name, f"唤醒簇缺少来源：{', '.join(missing)}。", sources=cluster.sources, expected=expected, missing=missing)


def assert_event_exists(timeline: Timeline, event_type: str, *, min_count: int = 1, source: str = "") -> AssertionResult:
    events = timeline.find(event_type, source=source or None)
    name = f"{event_type}_exists" if not source else f"{source}_{event_type}_exists"
    if len(events) >= min_count:
        return _pass(name, f"观察到 {len(events)} 个 {event_type} 事件。", count=len(events))
    return _fail(name, f"期望至少 {min_count} 个 {event_type} 事件，实际 {len(events)}。", count=len(events))


def assert_event_within_ms(
    timeline: Timeline,
    event_type: str,
    *,
    within_ms: int,
    anchor_event_type: str = "AudioInjected",
) -> AssertionResult:
    anchors = timeline.find(anchor_event_type)
    targets = timeline.find(event_type)
    name = f"{event_type}_within_{within_ms}ms"
    if not targets:
        return _fail(name, f"未观察到 {event_type}，无法判断时间窗口。")
    if not anchors:
        return _skip(name, f"未观察到 {anchor_event_type}，离线日志只能判断事件存在，不能判断注入后耗时。")
    anchor = anchors[0]
    if anchor.timestamp_ms is None:
        return _skip(name, f"{anchor_event_type} 缺少可计算时间戳。")
    measurable = [event for event in targets if event.timestamp_ms is not None and event.timestamp_ms >= anchor.timestamp_ms]
    if not measurable:
        return _fail(name, f"{anchor_event_type} 后未观察到带时间戳的 {event_type}。")
    first = measurable[0]
    delta = int(first.timestamp_ms - anchor.timestamp_ms)
    if delta <= within_ms:
        return _pass(name, f"{event_type} 在 {delta}ms 内发生。", delta_ms=delta, event_id=first.event_id)
    return _fail(name, f"{event_type} 发生耗时 {delta}ms，超过阈值 {within_ms}ms。", delta_ms=delta, threshold_ms=within_ms)


def assert_event_order(timeline: Timeline, before_type: str, after_type: str) -> AssertionResult:
    before = timeline.first(before_type)
    after = timeline.first(after_type)
    name = f"{before_type}_before_{after_type}"
    if before is None or after is None:
        return _fail(name, f"缺少顺序断言事件：{before_type}={bool(before)}, {after_type}={bool(after)}。")
    if before.timestamp_ms is not None and after.timestamp_ms is not None:
        if before.timestamp_ms <= after.timestamp_ms:
            return _pass(name, f"{before_type} 先于 {after_type}。", delta_ms=after.timestamp_ms - before.timestamp_ms)
        return _fail(name, f"{after_type} 早于 {before_type}，顺序不符合预期。")
    before_index = timeline.events.index(before)
    after_index = timeline.events.index(after)
    if before_index <= after_index:
        return _pass(name, f"{before_type} 在日志顺序上先于 {after_type}。", delta_index=after_index - before_index)
    return _fail(name, f"{after_type} 在日志顺序上早于 {before_type}。")


def assert_no_event_during(
    timeline: Timeline,
    event_type: str,
    *,
    duration_ms: int,
    anchor_event_type: Optional[str] = None,
) -> AssertionResult:
    name = f"no_{event_type}_during_{duration_ms}ms"
    anchor = timeline.first(anchor_event_type) if anchor_event_type else None
    start_ms = anchor.timestamp_ms if anchor is not None else timeline.start_ms
    if start_ms is None:
        events = timeline.find(event_type)
        if events:
            return _fail(name, f"观察到禁止事件 {event_type}，但缺少时间戳窗口。", count=len(events))
        return _pass(name, f"未观察到 {event_type}。", count=0)
    end_ms = start_ms + duration_ms
    events = timeline.find(event_type, after_ms=start_ms, before_ms=end_ms)
    if not events:
        return _pass(name, f"{duration_ms}ms 窗口内未观察到 {event_type}。", count=0)
    return _fail(name, f"{duration_ms}ms 窗口内观察到 {len(events)} 个 {event_type}。", count=len(events), event_ids=[event.event_id for event in events[:5]])


def assert_no_event_exists(timeline: Timeline, event_type: str, *, name: str = "") -> AssertionResult:
    events = timeline.find(event_type)
    assertion_name = name or f"no_{event_type}"
    if not events:
        return _pass(assertion_name, f"未观察到 {event_type}。", count=0)
    return _fail(assertion_name, f"观察到 {len(events)} 个不应出现的 {event_type}。", count=len(events), event_ids=[event.event_id for event in events[:5]])


def _first_payload(timeline: Timeline, event_type: str) -> Optional[Dict[str, Any]]:
    event = timeline.first(event_type)
    if event is None:
        return None
    return event.payload or {}


def _payloads(timeline: Timeline, event_type: str) -> List[Dict[str, Any]]:
    return [event.payload or {} for event in timeline.find(event_type)]


def _int_value(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _result_is_pass(payload: Dict[str, Any]) -> bool:
    return str(payload.get("result", "") or "").upper() == "PASS"


def aggregate_result(assertions: List[AssertionResult]) -> str:
    if any(item.result == "FAIL" for item in assertions):
        return "FAIL"
    if any(item.result == "BLOCKED" for item in assertions):
        return "BLOCKED"
    if any(item.result == "TIMING_AMBIGUOUS" for item in assertions):
        return "TIMING_AMBIGUOUS"
    if any(item.result == "SKIP" for item in assertions):
        return "PASS_WITH_SKIPPED_TIMING"
    return "PASS"


def evaluate_first_wake(timeline: Timeline, *, cp_log: bool = True, asr_log: bool = True, wake_within_ms: int = 3000) -> Dict[str, Any]:
    wake_by_source = timeline.counts_by_source("WakeDetected")
    assertions: List[AssertionResult] = [
        assert_event_exists(timeline, "WakeDetected"),
        assert_event_exists(timeline, "WakeDetected", source="ap"),
    ]
    if cp_log:
        assertions.append(assert_event_exists(timeline, "WakeDetected", source="cp"))
    if asr_log:
        assertions.append(assert_event_exists(timeline, "WakeDetected", source="asr"))
    assertions.extend(
        [
            assert_event_within_ms(timeline, "WakeDetected", within_ms=wake_within_ms),
            assert_no_event_during(timeline, "RebootDetected", duration_ms=10000, anchor_event_type="WakeDetected"),
            assert_no_event_during(timeline, "CrashDetected", duration_ms=10000, anchor_event_type="WakeDetected"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "first_wake",
        "result": result,
        "wake_by_source": wake_by_source,
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_basic_command(timeline: Timeline, *, cp_log: bool = True, asr_log: bool = True) -> Dict[str, Any]:
    assertions: List[AssertionResult] = [
        assert_event_exists(timeline, "WakeDetected"),
        assert_event_exists(timeline, "ASRDetected"),
        assert_event_exists(timeline, "CommandDetected"),
        assert_event_order(timeline, "WakeDetected", "CommandDetected"),
        assert_no_event_during(timeline, "RebootDetected", duration_ms=10000, anchor_event_type="WakeDetected"),
        assert_no_event_during(timeline, "CrashDetected", duration_ms=10000, anchor_event_type="WakeDetected"),
    ]
    if cp_log:
        assertions.append(assert_event_exists(timeline, "WakeDetected", source="cp"))
    if asr_log:
        assertions.append(assert_event_exists(timeline, "ASRDetected", source="asr"))
    result = aggregate_result(assertions)
    return {
        "profile": "basic_command",
        "result": result,
        "event_counts": timeline.counts(),
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_command_batch(
    timeline: Timeline,
    *,
    cp_log: bool = True,
    asr_log: bool = True,
    exploratory: bool = False,
) -> Dict[str, Any]:
    """Validate a fa2 command/free-speech batch from structured runner output."""
    summary = _first_payload(timeline, "CommandBatchSummary")
    passed_rows = _payloads(timeline, "CommandUtterancePassed")
    failed_rows = _payloads(timeline, "CommandUtteranceFailed")
    blocked_rows = _payloads(timeline, "CommandUtteranceBlocked")
    unknown_rows = _payloads(timeline, "CommandUtteranceUnknown")
    all_rows = [*passed_rows, *failed_rows, *blocked_rows, *unknown_rows]
    assertions: List[AssertionResult] = []

    if summary is None:
        assertions.append(_blocked("command_batch_summary_exists", "未找到 fa2_command_batch_summary.json，无法做批量命令结构化断言。"))
    else:
        total = _int_value(summary.get("total"), len(all_rows))
        assertions.append(_pass("command_batch_summary_exists", "观察到批量命令 summary。", total=total, counts=summary.get("counts", {})))
        if _int_value(summary.get("playback_returncode"), 0) == 0:
            assertions.append(_pass("batch_playback_returncode", "批量播放 returncode=0。", returncode=summary.get("playback_returncode")))
        else:
            assertions.append(_fail("batch_playback_returncode", "批量播放 returncode 非 0。", returncode=summary.get("playback_returncode")))
        if total > 0:
            assertions.append(_pass("command_batch_total", f"批量包含 {total} 条语料。", total=total))
        else:
            assertions.append(_fail("command_batch_total", "批量语料数量为 0。", total=total))
        if len(passed_rows) == total and not failed_rows and not blocked_rows and not unknown_rows:
            assertions.append(_pass("command_batch_all_passed", f"{total} 条语料全部 PASS。", passed=len(passed_rows), total=total))
        else:
            assertions.append(
                _fail(
                    "command_batch_all_passed",
                    "批量语料存在 FAIL/BLOCKED/UNKNOWN 或 PASS 数不匹配。",
                    passed=len(passed_rows),
                    failed=len(failed_rows),
                    blocked=len(blocked_rows),
                    unknown=len(unknown_rows),
                    total=total,
                )
            )

    if all_rows:
        wake_missing = [
            row.get("index")
            for row in all_rows
            if _int_value(row.get("ap_wake_count")) <= 0 or (cp_log and _int_value(row.get("cp_wake_count")) <= 0)
        ]
        if not wake_missing:
            assertions.append(_pass("wake_evidence_per_utterance", "每条语料都有 AP/CP 唤醒证据。", row_count=len(all_rows)))
        else:
            assertions.append(_fail("wake_evidence_per_utterance", "部分语料缺少唤醒证据。", missing_indices=wake_missing[:20]))

        command_missing = []
        for row in all_rows:
            has_intent = (
                _int_value(row.get("cp_command_count")) > 0
                or _int_value(row.get("unique_command_keyword_count")) > 0
                or _int_value(row.get("asr_total")) > 0
                or bool(str(row.get("ap_online_asr_texts", "") or "").strip())
                or bool(str(row.get("recognized_command_keywords", "") or "").strip())
            )
            if not has_intent:
                command_missing.append(row.get("index"))
        assertion_name = "asr_or_intent_evidence_per_utterance" if exploratory else "command_evidence_per_utterance"
        if not command_missing:
            assertions.append(_pass(assertion_name, "每条语料都有 ASR/命令/意图证据。", row_count=len(all_rows)))
        elif exploratory:
            assertions.append(
                _blocked(
                    assertion_name,
                    "探索性自由说缺少正式 oracle，部分语料没有 ASR/意图证据，不能直接归固件 FAIL。",
                    missing_indices=command_missing[:20],
                )
            )
        else:
            assertions.append(_fail(assertion_name, "部分命令缺少 ASR/命令证据。", missing_indices=command_missing[:20]))
    else:
        assertions.append(_blocked("command_batch_rows_exist", "未解析到逐条语料结果。"))

    assertions.extend(
        [
            assert_no_event_exists(timeline, "RebootDetected", name="no_reboot_in_batch"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_crash_in_batch"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "command_batch_exploratory" if exploratory else "command_batch",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "row_count": len(all_rows),
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_duplex_recognition(timeline: Timeline, *, mode: str, cp_log: bool = True, asr_log: bool = True) -> Dict[str, Any]:
    mode = "full" if mode == "full" else "half"
    mode_name = "全双工" if mode == "full" else "半双工"
    mode_events = [event for event in timeline.find("DuplexModeApplied") if (event.payload or {}).get("mode") == mode]
    judge_events = [event for event in timeline.find("DocCaseJudgeSummary") if (event.payload or {}).get("mode") == mode]
    mode_payload = (mode_events[0].payload if mode_events else (judge_events[0].payload if judge_events else {})) or {}
    assertions: List[AssertionResult] = []

    if mode_payload:
        assertions.append(_pass("duplex_judge_summary_exists", f"观察到{mode_name} doc case 判定 summary。", case_id=mode_payload.get("case_id", ""), detail_reason=mode_payload.get("reason", "")))
        if str(mode_payload.get("result", "")).upper() == "PASS":
            assertions.append(_pass("duplex_judge_result", f"{mode_name} doc case 结果为 PASS。", result=mode_payload.get("result")))
        else:
            assertions.append(_fail("duplex_judge_result", f"{mode_name} doc case 结果不是 PASS。", result=mode_payload.get("result"), detail_reason=mode_payload.get("reason", "")))
        if bool(mode_payload.get("cloud_apply_success")):
            assertions.append(_pass("duplex_cloud_apply_success", f"{mode_name}云端/配置应用成功。", cloud_apply_success=True))
        else:
            assertions.append(_fail("duplex_cloud_apply_success", f"未观察到{mode_name}云端/配置应用成功证据。", cloud_apply_success=mode_payload.get("cloud_apply_success")))
        timeout_values = mode_payload.get("full_timeout_values" if mode == "full" else "half_timeout_values", [])
        if timeout_values:
            assertions.append(_pass("duplex_mode_timeout_evidence", f"观察到{mode_name}超时/模式刷新证据。", timeout_values=timeout_values))
        else:
            assertions.append(_blocked("duplex_mode_timeout_evidence", f"未观察到{mode_name}超时/模式刷新证据。", mode=mode))
        if _int_value(mode_payload.get("successful_response_count")) > 0:
            assertions.append(_pass("duplex_successful_response", f"{mode_name}识别后有云端响应/播报证据。", successful_response_count=mode_payload.get("successful_response_count")))
        else:
            assertions.append(_fail("duplex_successful_response", f"{mode_name}识别后缺少云端响应/播报证据。", successful_response_count=mode_payload.get("successful_response_count")))
    else:
        assertions.append(_blocked("duplex_judge_summary_exists", f"未解析到{mode_name}模式应用 summary，不能证明模式切换已生效。", mode=mode))

    assertions.extend(
        [
            assert_event_exists(timeline, "WakeDetected"),
            assert_event_exists(timeline, "ASRDetected"),
            assert_event_exists(timeline, "CommandDetected"),
            assert_event_order(timeline, "WakeDetected", "CommandDetected"),
            assert_no_event_exists(timeline, "RebootDetected", name="no_reboot_in_duplex_recognition"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_crash_in_duplex_recognition"),
        ]
    )
    if cp_log:
        assertions.append(assert_event_exists(timeline, "WakeDetected", source="cp"))
    if asr_log:
        assertions.append(assert_event_exists(timeline, "ASRDetected", source="asr"))

    result = aggregate_result(assertions)
    return {
        "profile": f"{mode}_duplex_recognition",
        "result": result,
        "event_counts": timeline.counts(),
        "mode": mode,
        "duplex_summary": mode_payload,
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_oneshot_matrix(timeline: Timeline, *, online: bool = False, cp_log: bool = True, asr_log: bool = True) -> Dict[str, Any]:
    summary = _first_payload(timeline, "OneshotMatrixSummary")
    passed_rows = _payloads(timeline, "OneshotIntervalPassed")
    failed_rows = _payloads(timeline, "OneshotIntervalFailed")
    blocked_rows = _payloads(timeline, "OneshotIntervalBlocked")
    unknown_rows = _payloads(timeline, "OneshotIntervalUnknown")
    all_rows = [*passed_rows, *failed_rows, *blocked_rows, *unknown_rows]
    assertions: List[AssertionResult] = []

    if summary is None:
        assertions.append(_blocked("oneshot_matrix_summary_exists", "未找到 oneshot_matrix_summary.json。"))
    else:
        assertions.append(_pass("oneshot_matrix_summary_exists", "观察到 one-shot 矩阵 summary。", intervals=summary.get("intervals", [])))
        if _result_is_pass(summary):
            assertions.append(_pass("oneshot_matrix_result", "one-shot 矩阵总结果为 PASS。", result=summary.get("result")))
        else:
            assertions.append(_fail("oneshot_matrix_result", "one-shot 矩阵总结果不是 PASS。", result=summary.get("result"), detail_reason=summary.get("reason", "")))

    if all_rows:
        if not failed_rows and not blocked_rows and not unknown_rows:
            assertions.append(_pass("oneshot_intervals_all_passed", f"{len(all_rows)} 个间隔全部 PASS。", row_count=len(all_rows)))
        else:
            assertions.append(
                _fail(
                    "oneshot_intervals_all_passed",
                    "one-shot 间隔存在 FAIL/BLOCKED/UNKNOWN。",
                    failed=len(failed_rows),
                    blocked=len(blocked_rows),
                    unknown=len(unknown_rows),
                )
            )
        wake_missing = [
            row.get("interval_ms")
            for row in all_rows
            if _int_value(row.get("ap_wake_count")) <= 0 or (cp_log and _int_value(row.get("cp_wake_count")) <= 0)
        ]
        if not wake_missing:
            assertions.append(_pass("oneshot_wake_evidence_per_interval", "每个间隔都有唤醒证据。", row_count=len(all_rows)))
        else:
            assertions.append(_fail("oneshot_wake_evidence_per_interval", "部分间隔缺少唤醒证据。", missing_intervals=wake_missing))

        evidence_missing = []
        for row in all_rows:
            if online:
                has_evidence = bool(str(row.get("ap_online_asr_texts", "") or "").strip()) or timeline.find("TTSStarted") or timeline.find("MediaStarted")
            else:
                has_evidence = (
                    _int_value(row.get("cp_command_count")) > 0
                    or _int_value(row.get("unique_command_keyword_count")) > 0
                    or _int_value(row.get("asr_total")) > 0
                    or bool(str(row.get("recognized_command_keywords", "") or "").strip())
                    or bool(str(row.get("ap_online_asr_texts", "") or "").strip())
                )
            if not has_evidence:
                evidence_missing.append(row.get("interval_ms"))
        name = "online_asr_or_cloud_tts_per_interval" if online else "command_evidence_per_interval"
        if not evidence_missing:
            assertions.append(_pass(name, "每个间隔都有识别/命令闭环证据。", row_count=len(all_rows)))
        else:
            assertions.append(_fail(name, "部分间隔缺少识别/命令闭环证据。", missing_intervals=evidence_missing))
    else:
        assertions.append(_blocked("oneshot_interval_rows_exist", "未解析到 one-shot 逐间隔结果。"))

    assertions.extend(
        [
            assert_no_event_exists(timeline, "RebootDetected", name="no_reboot_in_oneshot_matrix"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_crash_in_oneshot_matrix"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "online_oneshot_matrix" if online else "offline_oneshot_matrix",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "row_count": len(all_rows),
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_wake_matrix(timeline: Timeline, *, cp_log: bool = True, asr_log: bool = True) -> Dict[str, Any]:
    summary = _first_payload(timeline, "WakeMatrixSummary")
    passed_rows = _payloads(timeline, "WakeRoundPassed")
    failed_rows = _payloads(timeline, "WakeRoundFailed")
    blocked_rows = _payloads(timeline, "WakeRoundBlocked")
    unknown_rows = _payloads(timeline, "WakeRoundUnknown")
    all_rows = [*passed_rows, *failed_rows, *blocked_rows, *unknown_rows]
    assertions: List[AssertionResult] = []
    scenario = str((summary or {}).get("scenario", "") or "")

    if summary is None:
        assertions.append(_blocked("wake_matrix_summary_exists", "未找到 wake_matrix_summary.json。"))
    else:
        assertions.append(_pass("wake_matrix_summary_exists", "观察到唤醒矩阵 summary。", scenario=scenario))
        if _result_is_pass(summary):
            assertions.append(_pass("wake_matrix_result", "唤醒矩阵总结果为 PASS。", result=summary.get("result")))
        else:
            assertions.append(_fail("wake_matrix_result", "唤醒矩阵总结果不是 PASS。", result=summary.get("result"), detail_reason=summary.get("reason", "")))
        counted = _int_value(summary.get("counted_rounds"))
        if counted > 0:
            assertions.append(_pass("wake_matrix_counted_rounds", f"有效计数轮次 {counted}。", counted_rounds=counted))
        else:
            assertions.append(_fail("wake_matrix_counted_rounds", "有效计数轮次为 0。", counted_rounds=counted))
        latency = summary.get("latency", {}) if isinstance(summary.get("latency"), dict) else {}
        if latency and _int_value(latency.get("sample_count")) > 0:
            assertions.append(
                _pass(
                    "wake_latency_stats_reported",
                    "已输出唤醒耗时统计；当前为 host 命令起点到首个串口唤醒 marker 的 proxy。",
                    sample_count=latency.get("sample_count"),
                    avg_ms=latency.get("avg_ms"),
                    min_ms=latency.get("min_ms"),
                    max_ms=latency.get("max_ms"),
                    limitation=latency.get("limitation", ""),
                )
            )
        else:
            assertions.append(_skip("wake_latency_stats_reported", "该场景未产生可统计的唤醒耗时样本。"))

    if all_rows:
        if not failed_rows and not blocked_rows and not unknown_rows:
            assertions.append(_pass("wake_rounds_all_passed", f"{len(all_rows)} 个唤醒轮次全部 PASS。", row_count=len(all_rows)))
        else:
            assertions.append(
                _fail(
                    "wake_rounds_all_passed",
                    "唤醒轮次存在 FAIL/BLOCKED/UNKNOWN。",
                    failed=len(failed_rows),
                    blocked=len(blocked_rows),
                    unknown=len(unknown_rows),
                )
            )
        wake_missing = []
        stability_fail = []
        for row in all_rows:
            expected_wake_ok = _int_value(row.get("ap_wake_count")) > 0 and (not cp_log or _int_value(row.get("cp_wake_count")) > 0)
            if asr_log:
                expected_wake_ok = expected_wake_ok and _int_value(row.get("asr_wake_count")) > 0
            if not expected_wake_ok:
                wake_missing.append(row.get("round"))
            if _int_value(row.get("boot_marker_count")) > 0 or _int_value(row.get("crash_marker_count")) > 0:
                stability_fail.append(row.get("round"))
        if not wake_missing:
            assertions.append(_pass("wake_evidence_per_round", "每个有效轮次都有期望端唤醒证据。", row_count=len(all_rows)))
        else:
            assertions.append(_fail("wake_evidence_per_round", "部分轮次缺少期望端唤醒证据。", missing_rounds=wake_missing[:20]))
        if not stability_fail:
            assertions.append(_pass("no_reboot_or_crash_per_wake_round", "逐轮未观察到 reboot/crash marker。", row_count=len(all_rows)))
        else:
            assertions.append(_fail("no_reboot_or_crash_per_wake_round", "部分轮次出现 reboot/crash marker。", rounds=stability_fail[:20]))
    else:
        assertions.append(_blocked("wake_round_rows_exist", "未解析到唤醒逐轮结果。"))

    assertions.extend(
        [
            assert_no_event_exists(timeline, "RebootDetected", name="no_reboot_in_wake_matrix_logs"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_crash_in_wake_matrix_logs"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": f"wake_matrix_{scenario}" if scenario else "wake_matrix",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "row_count": len(all_rows),
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_online_vad_special(timeline: Timeline, *, cp_log: bool = True, asr_log: bool = True) -> Dict[str, Any]:
    summary = _first_payload(timeline, "OnlineVADSummary")
    passed_rows = _payloads(timeline, "OnlineVADCasePassed")
    failed_rows = _payloads(timeline, "OnlineVADCaseFailed")
    blocked_rows = _payloads(timeline, "OnlineVADCaseBlocked")
    unknown_rows = _payloads(timeline, "OnlineVADCaseUnknown")
    all_rows = [*passed_rows, *failed_rows, *blocked_rows, *unknown_rows]
    assertions: List[AssertionResult] = []

    if summary is None:
        assertions.append(_blocked("online_vad_summary_exists", "未找到 online_vad_special_summary.json。"))
    else:
        assertions.append(_pass("online_vad_summary_exists", "观察到在线 VAD summary。", candidate_count=summary.get("candidate_count")))
        if _result_is_pass(summary):
            assertions.append(_pass("online_vad_result", "在线 VAD 小样本总结果为 PASS。", result=summary.get("result")))
        else:
            assertions.append(_fail("online_vad_result", "在线 VAD 小样本总结果不是 PASS。", result=summary.get("result"), detail_reason=summary.get("reason", "")))
        review_count = _int_value(summary.get("needs_review_count"))
        assertions.append(
            _pass(
                "vad_truncation_review_policy",
                "已记录文本覆盖差异；无正式容差前仅作为探索性复核，不直接判固件失败。",
                needs_review_count=review_count,
                attribution=summary.get("attribution", ""),
            )
        )

    if all_rows:
        if not failed_rows and not blocked_rows and not unknown_rows:
            assertions.append(_pass("vad_candidates_all_passed", f"{len(all_rows)} 个 VAD 候选全部 PASS。", row_count=len(all_rows)))
        else:
            assertions.append(
                _fail(
                    "vad_candidates_all_passed",
                    "VAD 候选存在 FAIL/BLOCKED/UNKNOWN。",
                    failed=len(failed_rows),
                    blocked=len(blocked_rows),
                    unknown=len(unknown_rows),
                )
            )
        wake_missing = []
        evidence_missing = []
        for row in all_rows:
            wake_ok = _int_value(row.get("ap_wake_count")) > 0 and (not cp_log or _int_value(row.get("cp_wake_count")) > 0)
            if asr_log:
                wake_ok = wake_ok and _int_value(row.get("asr_wake_count")) > 0
            if not wake_ok:
                wake_missing.append(row.get("candidate_id"))
            has_online_evidence = (
                bool(row.get("online_asr_texts"))
                or _int_value(row.get("vad_end_count")) > 0
                or _int_value(row.get("cloud_tts_or_instruction_count")) > 0
            )
            if not has_online_evidence:
                evidence_missing.append(row.get("candidate_id"))
        if not wake_missing:
            assertions.append(_pass("vad_wake_evidence_per_candidate", "每个 VAD 候选都有唤醒证据。", row_count=len(all_rows)))
        else:
            assertions.append(_fail("vad_wake_evidence_per_candidate", "部分 VAD 候选缺少唤醒证据。", candidates=wake_missing))
        if not evidence_missing:
            assertions.append(_pass("online_asr_or_vad_or_tts_per_candidate", "每个 VAD 候选都有在线 ASR/VAD end/云端播报证据。", row_count=len(all_rows)))
        else:
            assertions.append(_fail("online_asr_or_vad_or_tts_per_candidate", "部分 VAD 候选缺少在线闭环证据。", candidates=evidence_missing))
    else:
        assertions.append(_blocked("online_vad_rows_exist", "未解析到在线 VAD 逐候选结果。"))

    assertions.extend(
        [
            assert_no_event_exists(timeline, "RebootDetected", name="no_reboot_in_online_vad"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_crash_in_online_vad"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "online_vad_special",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "row_count": len(all_rows),
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_false_wake(timeline: Timeline, *, playback_required: bool = False) -> Dict[str, Any]:
    summary = _first_payload(timeline, "FalseWakeSummary")
    assertions: List[AssertionResult] = []
    if summary is None:
        assertions.append(_blocked("false_wake_summary_exists", "未找到误唤醒 summary。"))
    else:
        assertions.append(_pass("false_wake_summary_exists", "观察到误唤醒 summary。", kind=summary.get("kind", "")))
        if _result_is_pass(summary):
            assertions.append(_pass("false_wake_result", "误唤醒场景总结果为 PASS。", result=summary.get("result")))
        else:
            assertions.append(_fail("false_wake_result", "误唤醒场景总结果不是 PASS。", result=summary.get("result"), detail_reason=summary.get("reason", "")))
        total_lines = _int_value(summary.get("total_lines"), _int_value(summary.get("line_count")))
        if total_lines > 0:
            assertions.append(_pass("serial_logger_available", "监听窗口内串口有日志输出。", total_lines=total_lines))
        else:
            assertions.append(_blocked("serial_logger_available", "监听窗口内串口无日志，无法证明误唤醒监听有效。", total_lines=total_lines))
        wake_total = _int_value(summary.get("wake_marker_total"), _int_value(summary.get("wake_line_count")))
        if wake_total == 0:
            assertions.append(_pass("no_wake_marker_in_false_wake_window", "误唤醒窗口内未观察到 wake marker。", wake_marker_total=wake_total))
        else:
            assertions.append(_fail("no_wake_marker_in_false_wake_window", "误唤醒窗口内观察到 wake marker。", wake_marker_total=wake_total))
        boot_crash = _int_value(summary.get("boot_or_crash_count")) + _int_value(summary.get("boot_marker_count")) + _int_value(summary.get("crash_marker_count"))
        if boot_crash == 0:
            assertions.append(_pass("no_reboot_or_crash_in_false_wake_window", "误唤醒窗口内无 reboot/crash。", boot_or_crash_count=boot_crash))
        else:
            assertions.append(_fail("no_reboot_or_crash_in_false_wake_window", "误唤醒窗口内出现 reboot/crash。", boot_or_crash_count=boot_crash))

    if playback_required:
        audio_events = timeline.find("AudioInjected")
        if audio_events:
            assertions.append(_pass("interference_audio_injected", "观察到干扰音频播放事件。", count=len(audio_events)))
        elif summary and summary.get("audio_manifest"):
            assertions.append(_pass("interference_audio_injected", "summary 中存在干扰音频 manifest。", audio_manifest=summary.get("audio_manifest")))
        else:
            assertions.append(_blocked("interference_audio_injected", "未观察到干扰音频播放事件或 manifest。"))

    assertions.extend(
        [
            assert_no_event_exists(timeline, "WakeDetected", name="no_runtime_wake_detected_in_false_wake"),
            assert_no_event_exists(timeline, "ASRDetected", name="no_runtime_asr_detected_in_false_wake"),
            assert_no_event_exists(timeline, "CommandDetected", name="no_runtime_command_detected_in_false_wake"),
            assert_no_event_exists(timeline, "RebootDetected", name="no_runtime_reboot_in_false_wake"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_runtime_crash_in_false_wake"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "false_wake_playback" if playback_required else "false_wake_quiet",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_attribution_validator(timeline: Timeline) -> Dict[str, Any]:
    summary = _first_payload(timeline, "AttributionValidatorSummary")
    assertions: List[AssertionResult] = []
    if summary is None:
        assertions.append(_blocked("attribution_validator_summary_exists", "未找到 attribution_validator_summary.json。"))
    else:
        assertions.append(_pass("attribution_validator_summary_exists", "观察到归因一致性复核 summary。", run_count=summary.get("run_count")))
        if _result_is_pass(summary):
            assertions.append(_pass("attribution_validator_result", "归因一致性复核总结果为 PASS。", result=summary.get("result")))
        else:
            assertions.append(_fail("attribution_validator_result", "归因一致性复核总结果不是 PASS。", result=summary.get("result"), detail_reason=summary.get("reason", "")))
        if _int_value(summary.get("run_count")) > 0:
            assertions.append(_pass("attribution_validator_scanned_runs", "归因复核扫描到历史 run。", run_count=summary.get("run_count")))
        else:
            assertions.append(_blocked("attribution_validator_scanned_runs", "归因复核未扫描到历史 run。", run_count=summary.get("run_count")))
        if _int_value(summary.get("error_count")) == 0:
            assertions.append(_pass("no_error_level_attribution_mismatch", "未发现 ERROR 级归因不一致。", error_count=summary.get("error_count")))
        else:
            assertions.append(_fail("no_error_level_attribution_mismatch", "发现 ERROR 级归因不一致。", error_count=summary.get("error_count")))
    assertions.append(assert_no_event_exists(timeline, "AttributionFindingError", name="no_attribution_error_events"))
    result = aggregate_result(assertions)
    return {
        "profile": "attribution_validator",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_interrupt_prerequisite(timeline: Timeline) -> Dict[str, Any]:
    summary = _first_payload(timeline, "InterruptPrerequisiteSummary")
    selected = _first_payload(timeline, "InterruptPrerequisiteSelected")
    usable = _payloads(timeline, "InterruptPrerequisiteUsable")
    assertions: List[AssertionResult] = []

    if summary is None:
        assertions.append(_blocked("interrupt_prerequisite_summary_exists", "未找到 interrupt_prerequisite_measurement.json。"))
    else:
        assertions.append(_pass("interrupt_prerequisite_summary_exists", "观察到打断前置测量 summary。", total=summary.get("total"), counts=summary.get("counts", {})))
        if _int_value(summary.get("playback_returncode"), 0) == 0:
            assertions.append(_pass("prerequisite_playback_returncode", "前置候选播放 returncode=0。", returncode=summary.get("playback_returncode")))
        else:
            assertions.append(_fail("prerequisite_playback_returncode", "前置候选播放 returncode 非 0。", returncode=summary.get("playback_returncode")))

    if usable:
        assertions.append(_pass("usable_prerequisite_candidates", f"解析到 {len(usable)} 个可用自播前置候选。", count=len(usable)))
    else:
        assertions.append(_blocked("usable_prerequisite_candidates", "未解析到可用自播前置候选。"))

    if selected:
        duration = _int_value(selected.get("self_play_duration_ms"))
        offset = _int_value(selected.get("injection_offset_ms"))
        minimum = _int_value((summary or {}).get("minimum_duration_ms"), 2500)
        assertions.append(
            _pass(
                "selected_prerequisite_exists",
                "已选出后续打断可复用的自播前置。",
                candidate_id=selected.get("candidate_id", ""),
                phrase=selected.get("phrase", ""),
                duration_ms=duration,
                injection_offset_ms=offset,
            )
        )
        if duration >= minimum and offset > 0:
            assertions.append(_pass("selected_window_duration_enough", "选中自播窗口满足最小时长和注入偏移要求。", duration_ms=duration, minimum_duration_ms=minimum, injection_offset_ms=offset))
        else:
            assertions.append(_fail("selected_window_duration_enough", "选中自播窗口不满足最小时长或注入偏移要求。", duration_ms=duration, minimum_duration_ms=minimum, injection_offset_ms=offset))
        if _int_value(selected.get("ap_wake_count")) > 0 and _int_value(selected.get("cp_wake_count")) > 0:
            assertions.append(_pass("selected_candidate_recognition_evidence", "选中前置具备唤醒和识别链路证据。", ap_wake_count=selected.get("ap_wake_count"), cp_wake_count=selected.get("cp_wake_count")))
        else:
            assertions.append(_fail("selected_candidate_recognition_evidence", "选中前置缺少唤醒或识别链路证据。", ap_wake_count=selected.get("ap_wake_count"), cp_wake_count=selected.get("cp_wake_count")))
    else:
        assertions.append(_blocked("selected_prerequisite_exists", "未选出可复用自播前置，后续打断用例应 BLOCKED。"))

    media_windows = build_media_windows(timeline)
    if media_windows:
        assertions.append(_pass("selected_self_play_window_detected", "已解析到可配对自播 start/end 窗口。", windows=[window.to_dict() for window in media_windows[:3]]))
    else:
        assertions.append(_blocked("selected_self_play_window_detected", "未解析到可配对自播 start/end 窗口。"))

    assertions.extend(
        [
            assert_no_event_exists(timeline, "RebootDetected", name="no_reboot_in_prerequisite_measurement"),
            assert_no_event_exists(timeline, "CrashDetected", name="no_crash_in_prerequisite_measurement"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "interrupt_prerequisite_measurement",
        "result": result,
        "event_counts": timeline.counts(),
        "summary": summary or {},
        "selected": selected or {},
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_interrupt(
    timeline: Timeline,
    *,
    kind: str,
    cp_log: bool = True,
    asr_log: bool = True,
    guard_ms: int = 600,
    post_injection_ms: int = 5000,
) -> Dict[str, Any]:
    injection_events = [event for event in timeline.find("InterruptInjected") if event.timestamp_ms is not None]
    media_windows = build_media_windows(timeline)
    assertions: List[AssertionResult] = []
    selected_window: Optional[MediaWindow] = None
    injection = injection_events[0] if injection_events else None

    if injection is None:
        assertions.append(_blocked("interrupt_injection_exists", "未观察到 InterruptInjected，无法判断打断注入时序。"))
    else:
        assertions.append(_pass("interrupt_injection_exists", "观察到打断注入事件。", event_id=injection.event_id))

    if not media_windows:
        assertions.append(_blocked("self_play_window_exists", "未观察到可配对的 MediaStarted/MediaCompleted 自播窗口。"))
    else:
        assertions.append(_pass("self_play_window_exists", f"观察到 {len(media_windows)} 个自播窗口。", count=len(media_windows)))

    if injection is not None and media_windows:
        injection_ms = int(injection.timestamp_ms or 0)
        containing = [
            window
            for window in media_windows
            if window.start_ms + guard_ms <= injection_ms <= window.end_ms - guard_ms
        ]
        nearby = [
            window
            for window in media_windows
            if window.start_ms - 1000 <= injection_ms <= window.end_ms + 1000
        ]
        if containing:
            selected_window = containing[0]
            assertions.append(
                _pass(
                    "injection_inside_self_play_window",
                    "注入点落在自播窗口保护区内。",
                    injection_ms=injection_ms,
                    guard_ms=guard_ms,
                    window=selected_window.to_dict(),
                )
            )
        elif nearby:
            assertions.append(
                _ambiguous(
                    "injection_inside_self_play_window",
                    "注入点只落在自播窗口边界附近，不能直接判固件失败。",
                    injection_ms=injection_ms,
                    guard_ms=guard_ms,
                    nearby_windows=[window.to_dict() for window in nearby[:3]],
                )
            )
        else:
            assertions.append(
                _ambiguous(
                    "injection_inside_self_play_window",
                    "注入点未落入自播窗口，当前结果属于时序不明确。",
                    injection_ms=injection_ms,
                    guard_ms=guard_ms,
                    windows=[window.to_dict() for window in media_windows[:5]],
                )
            )

    if injection is not None and selected_window is not None:
        start_ms = int(injection.timestamp_ms or 0)
        end_ms = start_ms + post_injection_ms
        if kind == "wake":
            wake_events = timeline.find("WakeDetected", after_ms=start_ms, before_ms=end_ms)
            if wake_events:
                assertions.append(
                    _pass(
                        "wake_evidence_after_injection",
                        f"注入后 {post_injection_ms}ms 内观察到 {len(wake_events)} 个唤醒事件。",
                        count=len(wake_events),
                        event_ids=[event.event_id for event in wake_events[:5]],
                    )
                )
            else:
                assertions.append(_fail("wake_evidence_after_injection", "注入命中自播窗口，但未观察到唤醒证据。", count=0))
        else:
            asr_events = timeline.find("ASRDetected", after_ms=start_ms, before_ms=end_ms)
            command_events = timeline.find("CommandDetected", after_ms=start_ms, before_ms=end_ms)
            if asr_events or command_events:
                assertions.append(
                    _pass(
                        "asr_or_command_after_injection",
                        f"注入后 {post_injection_ms}ms 内观察到 ASR/命令证据。",
                        asr_count=len(asr_events),
                        command_count=len(command_events),
                        event_ids=[event.event_id for event in [*asr_events, *command_events][:5]],
                    )
                )
            else:
                assertions.append(_fail("asr_or_command_after_injection", "注入命中自播窗口，但未观察到 ASR/命令证据。", asr_count=0, command_count=0))
        assertions.extend(
            [
                assert_no_event_during(timeline, "RebootDetected", duration_ms=post_injection_ms, anchor_event_type="InterruptInjected"),
                assert_no_event_during(timeline, "CrashDetected", duration_ms=post_injection_ms, anchor_event_type="InterruptInjected"),
            ]
        )
    else:
        if kind == "wake":
            assertions.append(_skip("wake_evidence_after_injection", "注入未命中可信自播窗口，跳过固件唤醒证据断言。"))
        else:
            assertions.append(_skip("asr_or_command_after_injection", "注入未命中可信自播窗口，跳过固件识别证据断言。"))

    result = aggregate_result(assertions)
    return {
        "profile": f"{kind}_interrupt",
        "result": result,
        "guard_ms": guard_ms,
        "post_injection_ms": post_injection_ms,
        "media_windows": [window.to_dict() for window in media_windows],
        "selected_window": selected_window.to_dict() if selected_window else None,
        "interrupt_injection_count": len(injection_events),
        "event_counts": timeline.counts(),
        "assertions": [item.to_dict() for item in assertions],
    }


def evaluate_wake_interrupt(
    timeline: Timeline,
    *,
    cp_log: bool = True,
    asr_log: bool = True,
    guard_ms: int = 600,
    post_injection_ms: int = 5000,
) -> Dict[str, Any]:
    return evaluate_interrupt(
        timeline,
        kind="wake",
        cp_log=cp_log,
        asr_log=asr_log,
        guard_ms=guard_ms,
        post_injection_ms=post_injection_ms,
    )


def evaluate_command_interrupt(
    timeline: Timeline,
    *,
    cp_log: bool = True,
    asr_log: bool = True,
    guard_ms: int = 600,
    post_injection_ms: int = 5000,
) -> Dict[str, Any]:
    return evaluate_interrupt(
        timeline,
        kind="command",
        cp_log=cp_log,
        asr_log=asr_log,
        guard_ms=guard_ms,
        post_injection_ms=post_injection_ms,
    )


def evaluate_network_recovery(timeline: Timeline, *, post_recovery_ms: int = 60000) -> Dict[str, Any]:
    assertions: List[AssertionResult] = [
        assert_event_exists(timeline, "NetworkLost"),
        assert_event_exists(timeline, "NetworkRecovered"),
        assert_event_order(timeline, "NetworkLost", "NetworkRecovered"),
    ]
    recovered = timeline.first("NetworkRecovered")
    if recovered is None or recovered.timestamp_ms is None:
        assertions.append(_skip("online_voice_after_recovery", "缺少恢复在线精确时间，无法判断恢复后的在线语音闭环。"))
    else:
        start_ms = int(recovered.timestamp_ms)
        end_ms = start_ms + post_recovery_ms
        asr_events = timeline.find("ASRDetected", after_ms=start_ms, before_ms=end_ms)
        command_events = timeline.find("CommandDetected", after_ms=start_ms, before_ms=end_ms)
        tts_events = timeline.find("TTSStarted", after_ms=start_ms, before_ms=end_ms)
        media_events = timeline.find("MediaStarted", after_ms=start_ms, before_ms=end_ms)
        if asr_events and (tts_events or media_events or command_events):
            assertions.append(
                _pass(
                    "online_voice_after_recovery",
                    f"恢复在线后 {post_recovery_ms}ms 内观察到在线语音闭环证据。",
                    asr_count=len(asr_events),
                    command_count=len(command_events),
                    tts_count=len(tts_events),
                    media_count=len(media_events),
                )
            )
        else:
            assertions.append(
                _fail(
                    "online_voice_after_recovery",
                    f"恢复在线后 {post_recovery_ms}ms 内未观察到完整在线语音闭环。",
                    asr_count=len(asr_events),
                    command_count=len(command_events),
                    tts_count=len(tts_events),
                    media_count=len(media_events),
                )
            )
        assertions.extend(
            [
                assert_no_event_during(timeline, "RebootDetected", duration_ms=post_recovery_ms, anchor_event_type="NetworkRecovered"),
                assert_no_event_during(timeline, "CrashDetected", duration_ms=post_recovery_ms, anchor_event_type="NetworkRecovered"),
            ]
        )
    result = aggregate_result(assertions)
    return {
        "profile": "network_recovery_basic",
        "result": result,
        "post_recovery_ms": post_recovery_ms,
        "event_counts": timeline.counts(),
        "assertions": [item.to_dict() for item in assertions],
    }




def _cluster_has_sources(cluster: WakeCluster, *, cp_log: bool = True, asr_log: bool = True) -> bool:
    expected = ["ap"]
    if cp_log:
        expected.append("cp")
    if asr_log:
        expected.append("asr")
    return all(source in cluster.sources for source in expected)


def _pair_audio_scoped(first: WakeCluster, audio_events: List[Any], *, pre_roll_ms: int = 3000) -> bool:
    if first.start_ms is None:
        return False
    for audio in audio_events:
        if audio.timestamp_ms is None:
            continue
        # Host playback timestamps and DUT serial timestamps can differ by a
        # small amount, so allow a short pre-roll around AudioInjected.
        if first.start_ms >= int(audio.timestamp_ms) - pre_roll_ms:
            return True
    return False


def _recognition_pair_candidates(
    clusters: List[WakeCluster],
    *,
    audio_events: List[Any],
    recognition_timeout_ms: int,
    timing_guard_ms: int,
    cp_log: bool,
    asr_log: bool,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for first, second in zip(clusters, clusters[1:]):
        if first.start_ms is None or second.start_ms is None:
            continue
        delta = int(second.start_ms - first.start_ms)
        if delta <= 0:
            continue
        safe_limit_ms = max(0, recognition_timeout_ms - timing_guard_ms)
        if delta <= safe_limit_ms:
            status = "safe"
        elif delta <= recognition_timeout_ms + timing_guard_ms:
            status = "ambiguous"
        else:
            status = "out_of_window"
        candidates.append(
            {
                "first": first,
                "second": second,
                "delta_ms": delta,
                "status": status,
                "audio_scoped": _pair_audio_scoped(first, audio_events),
                "source_complete": _cluster_has_sources(first, cp_log=cp_log, asr_log=asr_log)
                and _cluster_has_sources(second, cp_log=cp_log, asr_log=asr_log),
            }
        )
    return candidates


def _select_recognition_pair(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None
    for status in ("safe", "ambiguous", "out_of_window"):
        scoped_complete = [item for item in candidates if item["status"] == status and item["audio_scoped"] and item["source_complete"]]
        if scoped_complete:
            return scoped_complete[0]
        scoped = [item for item in candidates if item["status"] == status and item["audio_scoped"]]
        if scoped:
            return scoped[0]
        complete = [item for item in candidates if item["status"] == status and item["source_complete"]]
        if complete:
            return complete[0]
    return candidates[0]


def evaluate_recognition_mode_wake(
    timeline: Timeline,
    *,
    cp_log: bool = True,
    asr_log: bool = True,
    recognition_timeout_s: int = 15,
    timing_guard_ms: int = 1200,
    wake_within_ms: int = 3000,
    wake_cluster_gap_ms: int = 2500,
) -> Dict[str, Any]:
    """Validate wake while the device is still in recognition mode.

    One physical wake normally emits several markers across AP/CP/ASR, so this
    profile first clusters wake events and then reasons on adjacent physical
    wakes. AudioInjected is treated as execution evidence, not as a strict
    one-to-one marker, because some runners play a composite audio containing
    multiple wake words.
    """
    wake_clusters = cluster_wake_events(timeline, gap_ms=wake_cluster_gap_ms)
    audio_events = [event for event in timeline.find("AudioInjected") if event.timestamp_ms is not None]
    assertions: List[AssertionResult] = []
    recognition_timeout_ms = int(recognition_timeout_s * 1000)
    safe_limit_ms = max(0, recognition_timeout_ms - int(timing_guard_ms))

    if not wake_clusters:
        assertions.append(_fail("first_wake_cluster_exists", "未观察到任何物理唤醒簇。"))
        result = aggregate_result(assertions)
        return {
            "profile": "recognition_mode_wake",
            "result": result,
            "recognition_timeout_s": recognition_timeout_s,
            "timing_guard_ms": timing_guard_ms,
            "wake_cluster_gap_ms": wake_cluster_gap_ms,
            "wake_clusters": [],
            "audio_injection_count": len(audio_events),
            "assertions": [item.to_dict() for item in assertions],
        }

    assertions.append(_pass("first_wake_cluster_exists", f"观察到 {len(wake_clusters)} 个物理唤醒簇。", cluster_count=len(wake_clusters)))
    if audio_events:
        assertions.append(_pass("audio_injected_exists", f"观察到 {len(audio_events)} 个音频注入事件。", count=len(audio_events)))
    else:
        assertions.append(_skip("audio_injected_exists", "未观察到 AudioInjected，不能判断唤醒簇是否由本轮音频触发。"))

    candidates = _recognition_pair_candidates(
        wake_clusters,
        audio_events=audio_events,
        recognition_timeout_ms=recognition_timeout_ms,
        timing_guard_ms=int(timing_guard_ms),
        cp_log=cp_log,
        asr_log=asr_log,
    )
    selected = _select_recognition_pair(candidates)
    selected_pair: Optional[Dict[str, Any]] = None

    if selected is None:
        assertions.append(
            _fail(
                "second_wake_cluster_exists",
                "未找到可用于识别模式二次唤醒判断的相邻唤醒簇。",
                cluster_count=len(wake_clusters),
            )
        )
    else:
        first_cluster = selected["first"]
        second_cluster = selected["second"]
        selected_pair = {
            "first_cluster": first_cluster.to_dict(),
            "second_cluster": second_cluster.to_dict(),
            "delta_ms": selected["delta_ms"],
            "status": selected["status"],
            "audio_scoped": selected["audio_scoped"],
            "source_complete": selected["source_complete"],
        }
        assertions.append(
            _pass(
                "second_wake_cluster_exists",
                "找到可用于识别模式二次唤醒判断的相邻唤醒簇。",
                pair=selected_pair,
            )
        )
        assertions.append(_assert_cluster_sources(first_cluster, cp_log=cp_log, asr_log=asr_log, prefix="first_wake_cluster"))
        assertions.append(_assert_cluster_sources(second_cluster, cp_log=cp_log, asr_log=asr_log, prefix="second_wake_cluster"))
        if audio_events and selected["audio_scoped"]:
            assertions.append(_pass("wake_pair_audio_scoped", "选中的唤醒簇与音频注入时间线匹配。", pair=selected_pair))
        elif audio_events:
            assertions.append(_blocked("wake_pair_audio_scoped", "存在音频注入事件，但选中的唤醒簇未落在可信音频范围内。", pair=selected_pair))
        else:
            assertions.append(_skip("wake_pair_audio_scoped", "无 AudioInjected，跳过音频范围匹配断言。"))

        delta = int(selected["delta_ms"])
        if selected["status"] == "safe":
            assertions.append(
                _pass(
                    "second_wake_inside_recognition_window",
                    f"第二次唤醒落在识别超时安全窗口内，间隔 {delta}ms。",
                    delta_ms=delta,
                    safe_limit_ms=safe_limit_ms,
                    timeout_ms=recognition_timeout_ms,
                    guard_ms=timing_guard_ms,
                )
            )
        elif selected["status"] == "ambiguous":
            assertions.append(
                _ambiguous(
                    "second_wake_inside_recognition_window",
                    "第二次唤醒处在识别超时临界灰区，不能直接判固件失败。",
                    delta_ms=delta,
                    safe_limit_ms=safe_limit_ms,
                    timeout_ms=recognition_timeout_ms,
                    guard_ms=timing_guard_ms,
                )
            )
        else:
            assertions.append(
                _blocked(
                    "second_wake_inside_recognition_window",
                    f"第二次唤醒已超出识别超时窗口，间隔 {delta}ms。",
                    delta_ms=delta,
                    timeout_ms=recognition_timeout_ms,
                    guard_ms=timing_guard_ms,
                )
            )

    assertions.extend(
        [
            assert_no_event_during(timeline, "RebootDetected", duration_ms=recognition_timeout_ms + 5000, anchor_event_type="WakeDetected"),
            assert_no_event_during(timeline, "CrashDetected", duration_ms=recognition_timeout_ms + 5000, anchor_event_type="WakeDetected"),
        ]
    )
    result = aggregate_result(assertions)
    return {
        "profile": "recognition_mode_wake",
        "result": result,
        "recognition_timeout_s": recognition_timeout_s,
        "timing_guard_ms": timing_guard_ms,
        "wake_cluster_gap_ms": wake_cluster_gap_ms,
        "wake_clusters": [cluster.to_dict() for cluster in wake_clusters],
        "recognition_pair_candidates": [
            {
                "first_index": item["first"].index,
                "second_index": item["second"].index,
                "delta_ms": item["delta_ms"],
                "status": item["status"],
                "audio_scoped": item["audio_scoped"],
                "source_complete": item["source_complete"],
            }
            for item in candidates
        ],
        "selected_pair": selected_pair,
        "audio_injection_count": len(audio_events),
        "assertions": [item.to_dict() for item in assertions],
    }
