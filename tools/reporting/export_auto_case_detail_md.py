# -*- coding: utf-8 -*-
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import json
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
from tools.core.polaris_runtime import current_session_dir, resolve_artifact_reference
from tools.library.polaris_doc_case_lib import SUPPORTED_DOC_CASES, load_doc_cases, parse_tone_catalog

STATUS_PATH = ROOT / 'config' / 'polaris_doc_case_status.json'
OUTPUT_PATH = ROOT / 'config' / 'polaris_auto_executable_case_detail.md'

status = json.loads(STATUS_PATH.read_text(encoding='utf-8'))
cases = {c.case_id: c for c in load_doc_cases()}
tone_catalog = parse_tone_catalog()
auto_items = [i for i in status['cases'] if i.get('classification') == 'auto_executable_now']
auto_items.sort(key=lambda i: (i.get('runner_kind', ''), int(i['case_id'].split('_')[-1]) if i['case_id'].split('_')[-1].isdigit() else i['case_id']))
by_kind = defaultdict(list)
for item in auto_items:
    by_kind[item.get('runner_kind', '')].append(item)

env = status.get('environment', {})
effective = status.get('effective_counts_after_recheck', {})
device_key = env.get('audio_device_key', 'VID_8765&PID_5678:9_2A847557_7_0000')

FUNC_MAP = {
    'algo_version_upload_case': 'run_algo_version_upload_case',
    'app_accent_case': 'run_app_accent_case',
    'app_accent_persist_case': 'run_app_accent_persist_case',
    'app_dialog_announce_case': 'run_app_dialog_announce_case',
    'app_dialog_config_case': 'run_app_dialog_config_case',
    'app_dialog_persist_case': 'run_app_dialog_persist_case',
    'app_mic_case': 'run_app_mic_case',
    'app_offline_timeout_case': 'run_app_offline_timeout_case',
    'app_proactive_mic_case': 'run_app_proactive_mic_case',
    'app_threshold_case': 'run_app_threshold_case',
    'app_threshold_persist_case': 'run_app_threshold_persist_case',
    'app_wakeup_word_case': 'run_app_wakeup_word_case',
    'app_wakeup_word_persist_case': 'run_app_wakeup_word_persist_case',
    'cloud_log_upload_probe_case': 'run_cloud_log_upload_probe_case',
    'dialog_phase_case': 'run_dialog_phase_case / run_offline_dialog_phase_case',
    'network_disconnect_case': 'run_network_disconnect_case',
    'network_reconnect_voice_case': 'run_network_reconnect_voice_case',
    'offline_interrupt_voice': 'execute_standard_audio_case(interrupt mode)',
    'offline_voice': 'run_offline_audio_case',
    'online_empty_nlu_case': 'run_online_empty_nlu_case',
    'online_stress_case': 'run_online_stress_case',
    'power_broadcast_case': 'run_power_broadcast_case',
    'serial_only': 'execute_standard_audio_case(serial mode)',
    'wake_info_upload_case': 'run_wake_info_upload_case',
    'wakeup_audio_upload_probe_case': 'run_wakeup_audio_upload_probe_case',
}

RUNNER_FLOW = {
    'offline_voice': ['按文档 token 生成一段 WAV，并通过固定声卡回放。', '播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。'],
    'offline_interrupt_voice': ['先播放第一段语音。', '等待第一条识别或播放开始标记后，再插入第二段唤醒音频做打断验证。'],
    'online_stress_case': ['按 seed 生成长序列压测音频。', '一次播放完成后统计 1000 轮在线唤醒/识别/播报闭环。'],
    'dialog_phase_case': ['按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。', '最终再汇总 phase 结果生成整条 case 的结论。'],
    'app_dialog_config_case': ['先经云端/App 接口设置自然对话、超时或唤醒词等配置。', '再播放文档里的在线探测音频，最后做 recovery。'],
    'app_dialog_announce_case': ['只下发云端配置，不播放探测音频。', '直接从 AP/WB 配置回执日志判断自然对话播报与状态是否正确。'],
    'app_dialog_persist_case': ['先做自然对话配置。', '再对 WB01 做硬重启，复机后跑持久化探测序列。'],
    'app_mic_case': ['先切在线语音开关。', '必要时叠加断网/掉电，再播放探测序列。'],
    'app_proactive_mic_case': ['直接下发主动播报请求。', '覆盖 mic off/on 与 interrupt/endSession 组合。'],
    'app_wakeup_word_case': ['先切换目标唤醒词。', '再播放探测词验证唤醒是否按预期生效。'],
    'app_wakeup_word_persist_case': ['先切换唤醒词再掉电。', '复机后再播放探测词验证是否持久化。'],
    'app_threshold_case': ['先设置唤醒词与唤醒阈值。', '再做双唤醒探测并检查 AP 的 threshold 日志。'],
    'app_threshold_persist_case': ['先做阈值配置再掉电。', '复机后继续检查 threshold 日志是否保持。'],
    'app_offline_timeout_case': ['在线完成配置后，切本机热点断网。', '离线状态下播放探测音频验证超时/交互效果。'],
    'app_accent_case': ['按方言配置计划切换方言。', '每个方言都跑 one-shot 探测。'],
    'app_accent_persist_case': ['设置方言后掉电重启。', '复机后逐个方言做 one-shot 探测。'],
    'network_disconnect_case': ['通过本机热点断网。', '直接判断断网窗口内 AP/WB 的断连状态码。'],
    'network_reconnect_voice_case': ['断网后先验证在线技能失效、离线命令仍可用。', '复网后再验证在线技能与控制都恢复。'],
    'power_broadcast_case': ['必要时先切到目标在线/离线网络状态。', '再通过 COM15 对 WB01 硬重启，只判上电播报链路。'],
    'serial_only': ['不放语音，只发串口命令。', '通过 WB/AP 日志里的播报回调与播放开始/结束断言。'],
    'cloud_log_upload_probe_case': ['先清本地 loglev/console，再发云端日志上传请求。', '随后播放“现在几点了”探测日志等级是否真正生效。'],
    'wake_info_upload_case': ['播放一次唤醒词。', '把本地 algo info 与上传 wake_info 报文逐字段比对。'],
    'algo_version_upload_case': ['先经 COM15 硬重启 WB01。', '再在 COM14 发送 version，并对比本地版本和上传版本。'],
    'wakeup_audio_upload_probe_case': ['先开启唤醒音频上传。', '再连续播放多次唤醒词，检查上传 session / success 证据。'],
    'online_empty_nlu_case': ['构造异常在线语料。', '观察是否走到“有 ASR 但 NLU 为空”的兜底播报链路。'],
}

RULE_ORDER = [
    'min_cp_wake', 'max_cp_wake', 'min_cp_command', 'min_ap_wake', 'max_ap_wake', 'min_wb_wake', 'max_wb_wake',
    'min_wb_online_wake', 'max_wb_online_wake', 'min_ap_asr', 'max_ap_asr', 'min_wb_asr', 'max_wb_asr',
    'min_asr_total', 'max_asr_total', 'min_unique_command_keywords', 'max_unique_command_keywords',
    'required_command_keywords', 'required_online_asr_texts', 'min_wb_playback_start', 'max_wb_playback_start',
    'min_wb_playback_end', 'max_wb_playback_end', 'min_wb_tts_callback', 'min_ap_cloud_tts_play', 'max_ap_cloud_tts_play',
    'min_ap_instruction_broadcast', 'min_ap_ignore_broadcast', 'max_ap_ignore_broadcast', 'require_wake_during_playback',
    'min_interrupt_reset_count', 'max_interrupt_reset_count', 'required_tones', 'forbidden_tones',
    'expected_wakeup_keyword', 'expected_wakeup_threshold', 'expected_recognition_threshold', 'expected_device_loglev',
    'max_boot_markers', 'max_crash_markers'
]

KEY_METRICS = [
    'cp_wake_count', 'cp_command_count', 'ap_wake_count', 'wb_wake_count', 'wb_online_wake_count', 'ap_asr_count',
    'wb_asr_count', 'ap_cloud_tts_play_count', 'ap_instruction_broadcast_count', 'wb_playback_start_count',
    'wb_playback_end_count', 'unique_command_keyword_count', 'interrupt_reset_count', 'wake_during_playback_count',
    'boot_marker_count', 'crash_marker_count'
]

KEY_LIST_METRICS = [
    'recognized_command_keywords', 'ap_online_asr_texts', 'tone_ids', 'wb_tts_callback_ids', 'ap_tts_fail_ids',
    'ap_instruction_broadcast_mids', 'ap_cloud_tts_url_ids'
]

WINDOW_KEYS = [
    'wakeup_lines', 'offline_asr_lines', 'player_status_lines', 'playback_start_markers', 'playback_end_markers'
]


def listify(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return [value]


def sort_case_id(case_id: str):
    try:
        return int(case_id.split('_')[-1])
    except Exception:
        return case_id


def md(text: Any) -> str:
    if text is None:
        return ''
    s = str(text)
    s = s.replace('|', '\\|').replace('\r\n', '<br>').replace('\n', '<br>')
    return s


def compact(value: Any, limit: int = 8) -> str:
    if isinstance(value, list):
        if len(value) <= limit:
            return json.dumps(value, ensure_ascii=False)
        return json.dumps(value[:limit], ensure_ascii=False)[:-1] + f', ...] (total={len(value)})'
    if isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    return text if len(text) <= 220 else text[:220] + '...'


def tone_label(value: Any) -> str:
    try:
        tone_id = int(value)
    except Exception:
        return str(value)
    return f'{tone_id} ({tone_catalog.get(tone_id, "unknown")})'


def token_to_text(token: Any) -> str:
    kind = getattr(token, 'kind', '')
    channel = getattr(token, 'channel', '')
    value = getattr(token, 'value', '')
    if kind == 'Wakeup':
        return f'唤醒词[{channel}]={value}'
    if kind in {'Asr', 'online_Asr', 'online_UnAsr'}:
        return f'{kind}[{channel}]={value}'
    if kind == 'Action' and channel == 'sleep':
        return f'静默 {value}ms'
    if kind == 'Action' and channel == 'shell':
        return f'串口命令 `{value}`'
    if kind == 'Check':
        return f'日志检查[{channel}]={value}'
    return f'{kind}[{channel}]={value}'


def rule_to_text(key: str, value: Any) -> str:
    mapping = {
        'min_cp_wake': f'COM12 `WAKE(1)` 至少 `{value}` 次。',
        'max_cp_wake': f'COM12 `WAKE(1)` 不超过 `{value}` 次。',
        'min_cp_command': f'COM12 `WAKE(0)` 至少 `{value}` 次。',
        'min_ap_wake': f'COM14 `wakeup_callback` 至少 `{value}` 次。',
        'max_ap_wake': f'COM14 `wakeup_callback` 不超过 `{value}` 次。',
        'min_wb_wake': f'COM13 `offline_wakeup` 至少 `{value}` 次。',
        'max_wb_wake': f'COM13 `offline_wakeup` 不超过 `{value}` 次。',
        'min_wb_online_wake': f'COM13 `online_wakeup` 至少 `{value}` 次。',
        'max_wb_online_wake': f'COM13 `online_wakeup` 不超过 `{value}` 次。',
        'min_ap_asr': f'COM14 离线 ASR 至少 `{value}` 次。',
        'max_ap_asr': f'COM14 离线 ASR 不超过 `{value}` 次。',
        'min_wb_asr': f'COM13 离线 ASR 至少 `{value}` 次。',
        'max_wb_asr': f'COM13 离线 ASR 不超过 `{value}` 次。',
        'min_asr_total': f'AP/WB ASR 总数至少 `{value}`。',
        'max_asr_total': f'AP/WB ASR 总数不超过 `{value}`。',
        'min_unique_command_keywords': f'唯一识别关键词数至少 `{value}`。',
        'max_unique_command_keywords': f'唯一识别关键词数不超过 `{value}`。',
        'required_command_keywords': '识别关键词必须包含：' + '、'.join(str(v) for v in listify(value)) + '。',
        'required_online_asr_texts': '在线 ASR 文本必须包含：' + '、'.join(str(v) for v in listify(value)) + '。',
        'min_wb_playback_start': f'COM13 `PLAYING` 至少 `{value}` 次。',
        'max_wb_playback_start': f'COM13 `PLAYING` 不超过 `{value}` 次。',
        'min_wb_playback_end': f'COM13 `PLAYBACK_COMPLETE` 至少 `{value}` 次。',
        'max_wb_playback_end': f'COM13 `PLAYBACK_COMPLETE` 不超过 `{value}` 次。',
        'min_wb_tts_callback': f'WB 离线 `offline_tts_callbak` 至少 `{value}` 次。',
        'min_ap_cloud_tts_play': f'AP 云端 TTS 播放至少 `{value}` 次。',
        'max_ap_cloud_tts_play': f'AP 云端 TTS 播放不超过 `{value}` 次。',
        'min_ap_instruction_broadcast': f'AP `audioBroadcast` mid 至少 `{value}` 个。',
        'min_ap_ignore_broadcast': f'AP `ignore broadcast` 至少 `{value}` 次。',
        'max_ap_ignore_broadcast': f'AP `ignore broadcast` 不超过 `{value}` 次。',
        'require_wake_during_playback': '必须观测到“播报进行中再次唤醒”。',
        'min_interrupt_reset_count': f'AP `player reset by user` 至少 `{value}` 次。',
        'max_interrupt_reset_count': f'AP `player reset by user` 不超过 `{value}` 次。',
        'expected_wakeup_keyword': f'阈值日志中的目标关键词必须是 `{value}`。',
        'expected_wakeup_threshold': f'阈值日志必须出现唤醒阈值 `{value}`。',
        'expected_recognition_threshold': f'阈值日志必须出现识别阈值 `{value}`。',
        'expected_device_loglev': f'AP 必须打印目标设备日志等级 `{value}` 的生效证据。',
        'max_boot_markers': f'boot 标记数量不超过 `{value}`。',
        'max_crash_markers': f'crash/panic/assert 标记数量不超过 `{value}`。',
    }
    if key == 'required_tones':
        return 'tone id 必须包含：' + '、'.join(tone_label(v) for v in listify(value)) + '。'
    if key == 'forbidden_tones':
        return 'tone id 不得包含：' + '、'.join(tone_label(v) for v in listify(value)) + '。'
    return mapping.get(key, '')


def load_runtime(item: Dict[str, Any]) -> Dict[str, Any]:
    runtime: Dict[str, Any] = {}
    session_dir = current_session_dir(ROOT)
    execution_dir_raw = str(item.get('execution_dir') or '').strip()
    result_path_raw = str(item.get('result_path') or '').strip()
    execution_dir = resolve_artifact_reference(execution_dir_raw, session_dir=session_dir) if execution_dir_raw else None
    result_path = resolve_artifact_reference(result_path_raw, session_dir=session_dir) if result_path_raw else None
    judge_path = execution_dir / 'judge.json' if execution_dir else None
    if judge_path and judge_path.is_file():
        runtime['judge'] = json.loads(judge_path.read_text(encoding='utf-8'))
        runtime['judge_path'] = str(judge_path)
    if result_path and result_path.is_file():
        runtime['result'] = json.loads(result_path.read_text(encoding='utf-8'))
        runtime['result_path'] = str(result_path)
    runtime['execution_dir'] = str(execution_dir) if execution_dir else ''
    return runtime


def get_diagnosis(runtime: Dict[str, Any]) -> Dict[str, Any]:
    judge = runtime.get('judge', {})
    if isinstance(judge.get('result'), str):
        return {
            'result': judge.get('result', ''),
            'confidence': judge.get('confidence', ''),
            'reason': judge.get('reason', ''),
            'checks': judge.get('checks', []),
        }
    return runtime.get('result', {}).get('diagnosis', {})


def get_checks(runtime: Dict[str, Any]) -> List[Dict[str, Any]]:
    diagnosis = get_diagnosis(runtime)
    checks = diagnosis.get('checks')
    return checks if isinstance(checks, list) else []


def get_metrics(runtime: Dict[str, Any]) -> Dict[str, Any]:
    judge = runtime.get('judge', {})
    if isinstance(judge.get('metrics'), dict):
        return judge['metrics']
    result_obj = runtime.get('result', {})
    metrics = result_obj.get('metrics')
    return metrics if isinstance(metrics, dict) else {}


def get_phases(runtime: Dict[str, Any]) -> List[Dict[str, Any]]:
    judge = runtime.get('judge', {})
    phases = judge.get('phases')
    if isinstance(phases, list):
        return phases
    result_obj = runtime.get('result', {})
    phases = result_obj.get('phases')
    return phases if isinstance(phases, list) else []


def get_window_summary(runtime: Dict[str, Any]) -> Dict[str, Any]:
    result_obj = runtime.get('result', {})
    summary = result_obj.get('window_summary')
    return summary if isinstance(summary, dict) else {}


def get_records(runtime: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    result_obj = runtime.get('result', {})
    records = result_obj.get(key)
    return records if isinstance(records, list) else []


def summarize_record(record: Dict[str, Any]) -> str:
    parts = [f"action={record.get('action', '')}"]
    if 'success' in record:
        parts.append(f"success={record.get('success')}")
    for key in ['enable', 'dialog_mode', 'wakeup_word', 'threshold', 'status', 'level', 'target', 'requested_enable', 'expected_state', 'timeout_seconds', 'wait_s', 'port', 'command']:
        if key in record:
            parts.append(f"{key}={compact(record.get(key))}")
    if 'commands' in record:
        parts.append(f"commands={compact(record.get('commands'))}")
    if 'response' in record:
        response = record.get('response')
        if isinstance(response, dict):
            parts.append(f"response_status={response.get('status_code', '')}")
            if response.get('text'):
                parts.append(f"response_text={compact(response.get('text'))}")
    if record.get('artifact_dir'):
        parts.append(f"artifact={record.get('artifact_dir')}")
    return '；'.join(str(p) for p in parts)


def playback_lines(runtime: Dict[str, Any]) -> List[str]:
    result_obj = runtime.get('result', {})
    playback = result_obj.get('playback')
    if not isinstance(playback, dict):
        return []
    lines: List[str] = []
    lines.append(f"播放返回码=`{playback.get('returncode', '')}`")
    if playback.get('audio_file'):
        lines.append(f"音频文件=`{playback.get('audio_file')}`")
    manifest = playback.get('manifest') if isinstance(playback.get('manifest'), dict) else {}
    if manifest:
        lines.append(
            f"主音频参数：duration_ms=`{manifest.get('duration_ms', '')}`；sample_rate=`{manifest.get('sample_rate', '')}`；channels=`{manifest.get('channels', '')}`；segments=`{len(manifest.get('sequence', []))}`"
        )
        seq = manifest.get('sequence', [])
        if seq:
            seq_text = []
            for item in seq[:12]:
                kind = item.get('type', '')
                if kind == 'tts':
                    seq_text.append(f"tts:{item.get('text', '')}")
                elif kind == 'silence':
                    seq_text.append(f"silence:{item.get('duration_ms', '')}ms")
                else:
                    seq_text.append(compact(item))
            lines.append('主音频序列：' + ' -> '.join(seq_text))
    commands = playback.get('commands') if isinstance(playback.get('commands'), list) else []
    if commands:
        lines.append('串口命令：' + '；'.join(str(c) for c in commands))
    segments = playback.get('segments') if isinstance(playback.get('segments'), list) else []
    if segments:
        lines.append('播放片段：' + '；'.join(f"{seg.get('name', '')}:{seg.get('returncode', '')}" for seg in segments))
    return lines


def check_table(checks: List[Dict[str, Any]]) -> List[str]:
    if not checks:
        return ['- <none>']
    lines = [
        '| 检查项 | actual | expected | 是否通过 |',
        '| --- | --- | --- | --- |',
    ]
    for item in checks:
        lines.append(
            f"| {md(item.get('name', ''))} | `{md(compact(item.get('actual')) )}` | `{md(compact(item.get('expected')) )}` | `{ 'PASS' if item.get('passed') else 'FAIL' }` |"
        )
    return lines


def failed_check_table(checks: List[Dict[str, Any]]) -> List[str]:
    failed = [item for item in checks if not item.get('passed')]
    return check_table(failed)


def phase_summary_table(phases: List[Dict[str, Any]]) -> List[str]:
    if not phases:
        return ['- <none>']
    lines = [
        '| phase_id | label | result | reason |',
        '| --- | --- | --- | --- |',
    ]
    for phase in phases:
        lines.append(
            f"| {md(phase.get('phase_id', ''))} | {md(phase.get('label', ''))} | `{md(phase.get('result', ''))}` | {md(phase.get('reason', ''))} |"
        )
    return lines


def phase_failed_sections(phases: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for phase in phases:
        failed = [item for item in phase.get('checks', []) if not item.get('passed')]
        if not failed:
            continue
        lines += [f"#### phase {phase.get('phase_id', '')} 的失败点", '']
        lines += failed_check_table(failed)
        lines.append('')
    if not lines:
        return ['- 所有 phase 都没有失败检查，或该 case 不走 phase 断言。']
    return lines


def metrics_lines(metrics: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    parts = [f"{key}={compact(metrics[key])}" for key in KEY_METRICS if key in metrics]
    if parts:
        lines.append('关键计数：' + '；'.join(parts))
    list_parts = []
    for key in KEY_LIST_METRICS:
        if key in metrics and metrics[key]:
            value = metrics[key]
            if key == 'tone_ids':
                value = [tone_label(v) for v in value]
            list_parts.append(f"{key}={compact(value)}")
    if list_parts:
        lines.append('关键内容：' + '；'.join(list_parts))
    return lines


def window_excerpt_lines(summary: Dict[str, Any]) -> List[str]:
    if not summary:
        return ['- <none>']
    lines: List[str] = []
    if summary.get('line_counts'):
        lines.append('line_counts=' + compact(summary.get('line_counts')))
    tones = summary.get('tones') if isinstance(summary.get('tones'), list) else []
    if tones:
        tone_text = []
        for item in tones[:6]:
            tone_text.append(tone_label(item.get('tone_id', '')))
        lines.append('tone 摘要：' + '；'.join(tone_text))
    for key in WINDOW_KEYS:
        rows = summary.get(key) if isinstance(summary.get(key), list) else []
        if rows:
            lines.append(f"{key}：")
            for row in rows[:3]:
                lines.append(f"  - {row}")
    return lines if lines else ['- <none>']


def testing_summary(case: Any, rule: Dict[str, Any]) -> List[str]:
    return [
        f"该用例位于 `{getattr(case, 'level1', '')} -> {getattr(case, 'level2', '')} -> {getattr(case, 'level3', '')} -> {getattr(case, 'level4', '')}`。",
        f"重点验证 `{getattr(case, 'case_type', '')}` 场景下“{case.name}”是否符合文档预期。",
        f"自动化接管说明：{rule.get('notes', '') or '按 runner 规则将文档步骤转成串口动作 / 热点动作 / 云端配置 / 音频播放，并依据日志做客观判定。'}",
    ]


def execution_lines(case: Any, rule: Dict[str, Any], runtime: Dict[str, Any]) -> List[str]:
    lines = [
        f"命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id {case.case_id} --device-key \"{device_key}\"`",
        f"调度函数：`run_doc_case -> {FUNC_MAP.get(rule['runner_kind'], 'run_doc_case dispatch')}`，runner_kind=`{rule['runner_kind']}`。",
        '三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。',
    ]
    for row in RUNNER_FLOW.get(rule['runner_kind'], ['按该 runner 的 setup -> probe -> recovery 逻辑执行。']):
        lines.append(row)
    if getattr(case, 'tokens', None):
        lines.append('文档 token / 语音输入序列：' + ' -> '.join(token_to_text(t) for t in case.tokens))
    if rule.get('target_wakeup_word'):
        lines.append(f"目标唤醒词=`{rule.get('target_wakeup_word')}`；恢复唤醒词=`{rule.get('recovery_wakeup_word', '小美小美')}`。")
    if rule.get('threshold_request') is not None:
        lines.append(f"阈值设置=`{rule.get('threshold_request')}`；探测词=`{rule.get('probe_text', '')}`；双唤醒间隔=`{rule.get('double_wake_gap_ms', '')}` ms。")
    if rule.get('stress_cycles') is not None:
        lines.append(f"压测参数：scenario=`{rule.get('scenario', '')}`；cycles=`{rule.get('stress_cycles')}`；seed=`{rule.get('stress_seed')}`。")
    if rule.get('probe_rounds') is not None:
        lines.append(f"探测轮数=`{rule.get('probe_rounds')}`。")
    if rule.get('observe_after_ms') is not None:
        lines.append(f"观察窗口=`{rule.get('observe_after_ms')}` ms。")

    setup = get_records(runtime, 'setup')
    recovery = get_records(runtime, 'recovery')
    if setup:
        lines.append('本次实际 setup 轨迹：')
        for record in setup[:12]:
            lines.append('  - ' + summarize_record(record))
    if recovery:
        lines.append('本次实际 recovery 轨迹：')
        for record in recovery[:12]:
            lines.append('  - ' + summarize_record(record))

    for row in playback_lines(runtime):
        lines.append(row)
    return lines


def assertion_lines(case: Any, rule: Dict[str, Any]) -> List[str]:
    lines = [
        '统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。',
        '关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。',
    ]
    for key in RULE_ORDER:
        if key in rule:
            text = rule_to_text(key, rule[key])
            if text:
                lines.append(text)
    if rule['runner_kind'] == 'network_disconnect_case':
        lines.append('额外检查：AP 必须出现 `AI disconnected` 或 `wifiLink_update:disconnect close`；WB 必须出现 `class ai state 4`。')
    if rule['runner_kind'] == 'network_reconnect_voice_case':
        lines.append('额外检查：断网阶段“现在几点了”不能进入在线 ASR/TTS；“打开空调”仍要能离线控制；复网后二者都要恢复。')
    if rule['runner_kind'] == 'cloud_log_upload_probe_case':
        lines.append('额外检查：云请求必须 business success，且 AP 必须打印目标 log level 生效，再通过探测语音拿到 wake + cloud TTS 证据。')
    if rule['runner_kind'] == 'wakeup_audio_upload_probe_case':
        lines.append('额外检查：除了 wake 证据外，还要有 `isUploadingFile=1` 和上传 success 响应。')
    if rule['runner_kind'] == 'wake_info_upload_case':
        lines.append('额外检查：本地 algo info 与上传 wake_info 需要字段比对一致，且 deviceId / response0 / response1 都要合理。')
    if rule['runner_kind'] == 'algo_version_upload_case':
        lines.append('额外检查：本地 `version` 查询结果必须与上传 algo/esr version 对齐，deviceId 也要匹配。')
    if rule['runner_kind'] == 'app_dialog_announce_case':
        lines.append('额外检查：该类不靠语音结果，直接看 AP/WB 是否打印 fullduplex 状态回执。')
    return lines


def fail_where_lines(item: Dict[str, Any], runtime: Dict[str, Any]) -> List[str]:
    diagnosis = get_diagnosis(runtime)
    result = diagnosis.get('result', item.get('result', ''))
    lines = [f"当前结果=`{result}`。"]
    if diagnosis.get('reason'):
        lines.append('判定原因：' + str(diagnosis.get('reason')))
    checks = get_checks(runtime)
    failed = [check for check in checks if not check.get('passed')]
    if failed:
        lines.append('失败直接来自以下检查项：')
        for check in failed:
            lines.append(f"  - {check.get('name')}：actual={compact(check.get('actual'))}；expected={compact(check.get('expected'))}")
    elif result == 'FAIL' and item.get('failed_checks'):
        lines.append('状态文件记录的失败检查：')
        for check in item.get('failed_checks', []):
            lines.append(f"  - {check.get('name')}：actual={compact(check.get('actual'))}；expected={compact(check.get('expected'))}")
    elif result == 'BLOCKED':
        lines.append('该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。')
    else:
        lines.append('本次无失败检查。')

    phases = get_phases(runtime)
    failed_phases = [phase for phase in phases if phase.get('result') != 'PASS']
    if failed_phases:
        lines.append('失败还体现在这些 phase：')
        for phase in failed_phases:
            lines.append(f"  - {phase.get('phase_id')}：{phase.get('reason')}")
            phase_failed = [check for check in phase.get('checks', []) if not check.get('passed')]
            for check in phase_failed[:6]:
                lines.append(f"    - {check.get('name')}：actual={compact(check.get('actual'))}；expected={compact(check.get('expected'))}")
    return lines


lines: List[str] = [
    '# Polaris 自动可执行用例执行与断言说明（增强版）',
    '',
    '> 这一版补齐了：每条用例的摘要、要测试什么、文档预期、自动化如何执行、自动化如何断言、当前 FAIL/BLOCKED 到底卡在哪里。',
    '',
    '## 1. 当前自动化基线',
    '',
    f'- 工作目录：`{status.get("workspace", "")}`',
    f'- 当前证据 session：`{status.get("session_dir", "")}`',
    f'- 自动可执行总数：`{effective.get("auto_executable_now", 0)}` / 全量 doc 用例 `715`',
    f'- 当前执行结果：`{effective.get("executed", 0)} executed / {effective.get("pass", 0)} PASS / {effective.get("fail", 0)} FAIL / {effective.get("blocked", 0)} BLOCKED / {effective.get("skip", 0)} SKIP`',
    f'- Wi-Fi：`{env.get("connected_ssid", "")}`；状态：`{env.get("wifi_state", "")}`',
    f'- 唤醒词：显示值=`{env.get("wake_word_display", "")}`；设备值=`{env.get("wake_word_deviceinfo", "")}`',
    f'- 声卡 key：`{device_key}`',
    f'- 串口：`COM12={env.get("ports", {}).get("COM12", "")}` / `COM13={env.get("ports", {}).get("COM13", "")}` / `COM14={env.get("ports", {}).get("COM14", "")}` / `COM15={env.get("ports", {}).get("COM15", "")}`',
    '',
    '## 2. 统一执行入口',
    '',
    '```powershell',
    f'python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_28 --device-key "{device_key}"',
    '',
    f'python tools/execution/polaris_doc_case_batch_runner.py --case-ids 美的空调_22 美的空调_23 美的空调_24 --device-key "{device_key}"',
    '```',
    '',
    '- 三路日志 `COM12/COM13/COM14` 持续采集，不会因为跑某条 case 中断。',
    '- case 执行只做时间窗切片，把窗口日志落到各自证据目录。',
    '- 最终判定优先看 `judge.json`；完整过程、setup/recovery/playback/state 看 `doc_case_result.json`。',
    '',
    '## 3. 157 条自动可执行用例详细说明',
    '',
]

for kind in sorted(by_kind):
    family_items = by_kind[kind]
    counter = Counter(item.get('result', '') for item in family_items)
    lines += [
        f'## {kind}',
        '',
        f'- runner 调度函数：`{FUNC_MAP.get(kind, "run_doc_case dispatch")}`',
        f'- 家族结果分布：`PASS {counter.get("PASS", 0)} / FAIL {counter.get("FAIL", 0)} / BLOCKED {counter.get("BLOCKED", 0)}`',
    ]
    for flow in RUNNER_FLOW.get(kind, ['按该 runner 的 setup -> probe -> recovery 逻辑执行。']):
        lines.append(f'- {flow}')
    lines.append('')

    for item in sorted(family_items, key=lambda row: sort_case_id(row['case_id'])):
        case = cases[item['case_id']]
        rule = SUPPORTED_DOC_CASES[case.case_id]
        runtime = load_runtime(item)
        diagnosis = get_diagnosis(runtime)
        checks = get_checks(runtime)
        phases = get_phases(runtime)
        metrics = get_metrics(runtime)
        summary = get_window_summary(runtime)

        lines += [
            f'### {case.case_id} {case.name}',
            '',
            '**摘要**',
        ]
        for row in testing_summary(case, rule):
            lines.append(f'- {row}')

        lines += [
            '',
            '**要测试什么**',
            f'- 文档层级：`{getattr(case, "level1", "")} -> {getattr(case, "level2", "")} -> {getattr(case, "level3", "")} -> {getattr(case, "level4", "")}`',
            f'- case_type：`{getattr(case, "case_type", "")}`',
            f'- 文档标题：`{case.name}`',
            f'- 自动化接管依据：{item.get("reason", "")}',
            '',
            '**文档原始信息**',
            f'- 优先级：`{case.priority}`',
            f'- 前置条件：{case.precondition}',
            f'- 文档步骤：{case.steps}',
            f'- 文档预期：{case.expected}',
            '',
            '**自动化如何执行**',
        ]
        for row in execution_lines(case, rule, runtime):
            lines.append(f'- {row}')

        lines += [
            '',
            '**自动化如何断言**',
        ]
        for row in assertion_lines(case, rule):
            lines.append(f'- {row}')

        lines += [
            '',
            '**本次实际判定检查表**',
            '',
        ]
        lines += check_table(checks)

        if phases:
            lines += [
                '',
                '**phase 总览**',
                '',
            ]
            lines += phase_summary_table(phases)
            lines += [
                '',
                '**phase 失败点**',
                '',
            ]
            lines += phase_failed_sections(phases)

        lines += [
            '',
            '**当前结果 / FAIL 在哪里**',
        ]
        for row in fail_where_lines(item, runtime):
            lines.append(f'- {row}')

        lines += [
            '',
            '**本次关键观测值**',
        ]
        metric_rows = metrics_lines(metrics)
        if metric_rows:
            for row in metric_rows:
                lines.append(f'- {row}')
        else:
            lines.append('- <none>')

        lines += [
            '',
            '**关键日志摘录**',
        ]
        excerpt_rows = window_excerpt_lines(summary)
        for row in excerpt_rows:
            if row.startswith('  - '):
                lines.append(row)
            else:
                lines.append(f'- {row}')

        lines += [
            '',
            '**证据路径**',
            f'- 执行目录：`{runtime.get("execution_dir", "")}`',
            f'- judge：`{runtime.get("judge_path", "")}`',
            f'- result：`{runtime.get("result_path", "")}`',
            '',
        ]

OUTPUT_PATH.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
print(OUTPUT_PATH)
