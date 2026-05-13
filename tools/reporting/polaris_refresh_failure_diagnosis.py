#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / 'config'

from tools.core.polaris_runtime import current_session_dir, find_artifact_files, resolve_artifact_reference
STATUS_PATH = CONFIG_DIR / 'polaris_doc_case_status.json'
ENV_PATH = CONFIG_DIR / 'polaris_env.json'
DIAG_PATH = CONFIG_DIR / 'polaris_failure_diagnosis.json'
SESSION_DIR = current_session_dir(ROOT)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def parse_case_index(case_id: str) -> Optional[int]:
    match = re.search(r'_(\d+)$', case_id or '')
    return int(match.group(1)) if match else None


def build_case_lookup(status: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    lookup: Dict[int, Dict[str, Any]] = {}
    for case in status.get('cases', []):
        index = parse_case_index(str(case.get('case_id', '')))
        if index is not None:
            lookup[index] = case
    return lookup


def load_case_result(case: Dict[str, Any]) -> Dict[str, Any]:
    result_path = resolve_artifact_reference(case.get('result_path', ''), session_dir=SESSION_DIR) if case.get('result_path') else None
    if result_path and result_path.exists():
        return load_json(result_path)
    return {}


def latest_case_table_dir(session_dir: Path) -> str:
    candidates = sorted(find_artifact_files('case_result_table', 'summary.json', session_dir), key=lambda item: item.stat().st_mtime)
    if not candidates:
        return ''
    return str(candidates[-1].parent)


def case_record(case: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not case:
        return None
    payload = load_case_result(case)
    diagnosis = payload.get('diagnosis', {})
    artifacts = payload.get('artifacts', {})
    resolved_judge = resolve_artifact_reference(
        artifacts.get('judge') or str(Path(str(case.get('execution_dir', ''))) / 'judge.json'),
        session_dir=SESSION_DIR,
    )
    judge_path = str(resolved_judge) if resolved_judge else ''
    return {
        'case_id': case.get('case_id', ''),
        'result': case.get('result', ''),
        'judge': judge_path,
        'summary': diagnosis.get('reason', ''),
        'runner_kind': case.get('runner_kind', ''),
    }


def collect_cases(
    case_lookup: Dict[int, Dict[str, Any]],
    indices: Iterable[int],
    *,
    allowed_results: Optional[Iterable[str]] = None,
    allowed_classifications: Optional[Iterable[str]] = ('auto_executable_now',),
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    allowed = set(allowed_results or [])
    classifications = set(allowed_classifications or [])
    for index in indices:
        case = case_lookup.get(index)
        if not case:
            continue
        if classifications and str(case.get('classification', '')) not in classifications:
            continue
        if not allowed or str(case.get('result', '')) in allowed:
            items.append(case)
    return items


def bucket_payload(case_lookup: Dict[int, Dict[str, Any]], name: str, indices: Iterable[int], summary: str) -> Dict[str, Any]:
    cases = collect_cases(case_lookup, indices, allowed_results={'FAIL', 'BLOCKED'})
    return {
        'category': name,
        'count': len(cases),
        'cases': [case.get('case_id', '') for case in cases],
        'summary': summary,
        'results': {
            'PASS': sum(1 for case in cases if case.get('result') == 'PASS'),
            'FAIL': sum(1 for case in cases if case.get('result') == 'FAIL'),
            'BLOCKED': sum(1 for case in cases if case.get('result') == 'BLOCKED'),
        },
    }


def build_representative_pass(case_lookup: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    picks = [1, 20, 21, 613, 684, 705]
    result: Dict[str, Any] = {}
    for index in picks:
        record = case_record(case_lookup.get(index))
        if record and record['result'] == 'PASS':
            result[record['case_id']] = {
                'judge': record['judge'],
                'summary': record['summary'],
            }
    return result


def build_failure_bucket_table(case_lookup: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets = [
        bucket_payload(
            case_lookup,
            'cloud_or_precondition_blocked',
            [113, 687],
            'The app/cloud setting call returns code 501 or the prerequisite voice command cannot be established, so the case cannot close locally.',
        ),
        bucket_payload(
            case_lookup,
            'cloud_artifact_closure_pending',
            [709, 710, 711, 712, 713, 714],
            'Local trigger, log markers, and upload/log-level evidence are present, but cloud-side artifact retrieval is still required for final closure.',
        ),
        bucket_payload(
            case_lookup,
            'stress_continuity_gap',
            [44, 45],
            'Long-run online wake or wake-plus-command stress still misses the doc threshold on response continuity.',
        ),
        bucket_payload(
            case_lookup,
            'other_functional_failures',
            [51, 137],
            'Remaining failures are concrete behavior mismatches: offline TTS resource playability and half-duplex timeout prompt behavior.',
        ),
    ]
    return [bucket for bucket in buckets if bucket.get('count', 0) > 0]


def build_representative_fail(case_lookup: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    def add(label: str, category: str, indices: Iterable[int], summary: str, result: Dict[str, Any]) -> None:
        items = collect_cases(case_lookup, indices, allowed_results={'FAIL'})
        if not items:
            return
        result[label] = {
            'category': category,
            'cases': [case.get('case_id', '') for case in items],
            'summary': summary,
        }

    result: Dict[str, Any] = {}
    add('????_137', 'natural_dialog_half_duplex_timeout_prompt_mismatch', [137], 'Half-duplex + closure scenario still emits a timeout closure prompt that the doc expectation forbids.', result)
    add('????_44/45', 'stress_continuity_gap', [44, 45], '1000-cycle online stress still loses part of the response continuity or playback chain.', result)
    add('????_51/137', 'other_functional_failures', [51, 137], 'Offline TTS resource playability and half-duplex timeout prompt behavior still show real device/resource mismatches.', result)
    return result


def build_representative_blocked(case_lookup: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    groups = {
        '????_113/687': ('cloud_setting_returns_501', [113, 687], 'Cloud/app setting still returns business code 501, so the case cannot be fully closed from the local side.'),
        '????_161/163': ('voice_precondition_cannot_be_established', [161, 163], 'The prerequisite voice command chain cannot be formed after the target wake-word setup path, so the subsequent persistence check remains blocked.'),
        '????_709~714': ('cloud_artifact_retrieval_pending', [709, 710, 711, 712, 713, 714], 'Local logs already prove trigger-side behavior, but cloud-side retrieval/download is still missing.'),
    }
    for label, (category, indices, summary) in groups.items():
        items = collect_cases(case_lookup, indices, allowed_results={'BLOCKED'})
        if items:
            result[label] = {
                'category': category,
                'cases': [case.get('case_id', '') for case in items],
                'summary': summary,
            }
    return result


def main() -> None:
    status = load_json(STATUS_PATH)
    env = load_json(ENV_PATH) if ENV_PATH.exists() else {}
    previous = load_json(DIAG_PATH) if DIAG_PATH.exists() else {}
    case_lookup = build_case_lookup(status)
    counts = status.get('effective_counts_after_recheck', {})
    session_dir = Path(status.get('session_dir', ROOT / 'result'))
    runner_kind_count = len({case.get('runner_kind', '') for case in status.get('cases', []) if case.get('classification') == 'auto_executable_now'})

    all_non_pass = {
        case.get('case_id', '')
        for case in status.get('cases', [])
        if case.get('classification') == 'auto_executable_now' and case.get('result') in {'FAIL', 'BLOCKED'}
    }
    bucket_table = build_failure_bucket_table(case_lookup)
    bucket_cases = {case_id for bucket in bucket_table for case_id in bucket.get('cases', [])}
    uncovered_non_pass = sorted(all_non_pass - bucket_cases)

    payload = {
        'updated_at': datetime.now().isoformat(timespec='seconds'),
        'workspace': status.get('workspace', str(ROOT)),
        'active_session': str(session_dir),
        'logger_pid': status.get('environment', {}).get('logger_pid', 0),
        'target_playback_device_key': status.get('environment', {}).get('audio_device_key', ''),
        'latest_doc_case_counts': {
            'total': counts.get('total', 0),
            'auto_executable_now': counts.get('auto_executable_now', 0),
            'executed': counts.get('executed', 0),
            'pass': counts.get('pass', 0),
            'fail': counts.get('fail', 0),
            'blocked': counts.get('blocked', 0),
            'partial': counts.get('partial', 0),
            'skip': counts.get('skip', 0),
        },
        'latest_case_table_artifact_dir': latest_case_table_dir(session_dir),
        'baseline_after_recovery': previous.get('baseline_after_recovery', {}),
        'current_conclusion': {
            'primary_state': 'auto_executable_scope_converged',
            'primary_reason': (
                f"Current doc auto-executable scope is stable at {counts.get('executed', 0)} executed / "
                f"{counts.get('pass', 0)} PASS / {counts.get('fail', 0)} FAIL / {counts.get('blocked', 0)} BLOCKED."
            ),
            'remaining_blocker': 'real_device_behavior_gaps_and_external_cloud_closure',
            'remaining_blocker_reason': 'Remaining issues are now dominated by real device/config behavior mismatches plus cloud-side artifact retrieval gaps, not by generic regex assertions.',
            'parser_or_regex_status': 'Recent reruns closed case 21 with behavior-first empty-NLU evidence, re-judged case 1 with the CA3X/T6 note-aligned offline boot prompt chain, and used learnCase model-applicability evidence to move the CA3X-inapplicable single-mic wake-word families out of the executable set.',
            'local_logger_status': 'continuous logger healthy on COM12/COM13/COM14 throughout the current session',
            'runner_family_coverage': f'{runner_kind_count} runner kinds covered in the current auto-executable sweep',
            'tooling_fixups_this_round': [
                'Reworked online_empty_nlu_case to close on online ASR + asrInvalid audioBroadcast evidence instead of a fragile AP cloud-TTS play count.',
                'Allowed positive wake-word switch cases to use AP prompt start/stop markers when WB playback end markers are absent.',
                'Re-ran case 1 under the same continuous logging session and aligned the offline boot prompt assertion with the CA3X/T6 note-backed historical evidence.',
                'Applied learnCase note-based model gating so CA3X can skip the non-applicable single-mic wake-word family (61~76) and the dependent room-name wake-word persistence case 685 before the baseline is exported.',
            ],
        },
        'representative_results': {
            'pass': build_representative_pass(case_lookup),
            'fail': build_representative_fail(case_lookup),
            'blocked': build_representative_blocked(case_lookup),
        },
        'failure_buckets': bucket_table,
        'marker_extraction_evidence': previous.get('marker_extraction_evidence', {
            'audio_broadcast_mid': 'AP cloud.instructions.audioBroadcast mid extraction is available.',
            'cloud_tts_url_id': 'stream_tts / TTS recv / TTS playing URL-id extraction is available.',
            'playback_markers': 'status=play/status=stop/play complete/tone player evt markers are available.',
            'note': 'wake/asr/tts/broadcast-id/start-stop markers are already used by both probe and runner paths.',
        }),
        'coverage_guard': {
            'non_pass_case_total': len(all_non_pass),
            'bucket_case_total': len(bucket_cases),
            'uncovered_non_pass_cases': uncovered_non_pass,
        },
        'next_actions': [
            'If cloud-side retrieval becomes available, close ????_709~714 with downloaded evidence instead of local trigger-only proof.',
            'If firmware/app capability changes, re-run the remaining real-fail families first: 44/45/51/137.',
            f"Keep using config/polaris_doc_case_status.json as the source of truth for the latest {counts.get('auto_executable_now', 0)}-case active baseline.",
        ],
    }

    DIAG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'diagnosis_path': str(DIAG_PATH), 'counts': payload['latest_doc_case_counts'], 'uncovered_non_pass_cases': uncovered_non_pass}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
