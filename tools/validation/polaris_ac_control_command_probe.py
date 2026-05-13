#!/usr/bin/env python3
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import argparse
import json
import time
from collections import Counter
from datetime import datetime
from typing import List, Tuple
import re

from tools.core.polaris_runtime import current_session_dir, workspace_root
from tools.device.polaris_network_orchestrator import hotspot_set, hotspot_status
from tools.probe.polaris_phrase_probe import run_probe
from tools.validation.polaris_workbook_voice_recognition_batch import write_json


COMMANDS = [
    {
        "semantic": "open_ac",
        "group": "\u5f00\u5173\u673a",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u7a7a\u8c03",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u7a7a\u8c03\u5f00\u673a",
        "expected_online_asr": "\u6253\u5f00\u7a7a\u8c03",
        "expected_keyword": "kong tiao kai ji",
        "strict_keyword": True,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_6",
            "\u547d\u4ee4\u8bcd\u8868:\u6253\u5f00\u7a7a\u8c03",
        ],
    },
    {
        "semantic": "close_ac",
        "group": "\u5f00\u5173\u673a",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7a7a\u8c03",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u7a7a\u8c03\u5173\u673a",
        "expected_online_asr": "\u5173\u95ed\u7a7a\u8c03",
        "expected_keyword": "kong tiao guan ji",
        "strict_keyword": True,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_11",
            "\u547d\u4ee4\u8bcd\u8868:\u5173\u95ed\u7a7a\u8c03",
        ],
    },
    {
        "semantic": "cool_mode",
        "group": "\u6a21\u5f0f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5236\u51b7\u6a21\u5f0f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5236\u51b7\u6a21\u5f0f",
        "expected_online_asr": "\u5236\u51b7\u6a21\u5f0f",
        "expected_keyword": "zhi leng mo shi",
        "strict_keyword": True,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_20"],
    },
    {
        "semantic": "heat_mode",
        "group": "\u6a21\u5f0f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5236\u70ed\u6a21\u5f0f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5236\u70ed\u6a21\u5f0f",
        "expected_online_asr": "\u5236\u70ed\u6a21\u5f0f",
        "expected_keyword": "zhi re mo shi",
        "strict_keyword": True,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_24"],
    },
    {
        "semantic": "fan_mode",
        "group": "\u6a21\u5f0f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u9001\u98ce\u6a21\u5f0f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u9001\u98ce\u6a21\u5f0f",
        "expected_online_asr": "\u9001\u98ce\u6a21\u5f0f",
        "expected_keyword": "song feng mo shi",
        "strict_keyword": True,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_28"],
    },
    {
        "semantic": "temperature_26",
        "group": "\u6e29\u5ea6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8c03\u523026\u5ea6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8c03\u523026\u5ea6",
        "expected_online_asr": "\u8c03\u523026\u5ea6",
        "online_asr_candidates": ["\u8c03\u523026\u5ea6", "26\u5ea6", "\u4e8c\u5341\u516d\u5ea6"],
        "expected_keyword": "er shi liu du",
        "keyword_candidates": ["er shi liu du", "tiao dao er shi liu du"],
        "strict_keyword": False,
        "source_refs": [
            "config/polaris_command_word_report.md:\u8c03\u523026\u5ea6",
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_139",
        ],
    },
    {
        "semantic": "auto_wind",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u81ea\u52a8\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u81ea\u52a8\u98ce",
        "expected_online_asr": "\u81ea\u52a8\u98ce",
        "expected_keyword": "zi dong feng",
        "keyword_candidates": ["zi dong feng", "feng su zi dong"],
        "strict_keyword": False,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_46",
            "config/polaris_command_word_report.md:\u81ea\u52a8\u98ce",
        ],
    },
    {
        "semantic": "swing_up_down_open",
        "group": "\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u4e0a\u4e0b\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u4e0a\u4e0b\u6446\u98ce",
        "expected_online_asr": "\u6253\u5f00\u4e0a\u4e0b\u6446\u98ce",
        "online_asr_candidates": ["\u6253\u5f00\u4e0a\u4e0b\u6446\u98ce", "\u4e0a\u4e0b\u6446\u98ce", "\u4e0a\u4e0b\u98ce"],
        "expected_keyword": "da kai shang xia bai feng",
        "keyword_candidates": ["da kai shang xia bai feng", "shang xia bai feng", "shang xia feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_174"],
    },
    {
        "semantic": "swing_up_down_close",
        "group": "\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u4e0a\u4e0b\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u4e0a\u4e0b\u6446\u98ce",
        "expected_online_asr": "\u5173\u95ed\u4e0a\u4e0b\u6446\u98ce",
        "online_asr_candidates": ["\u5173\u95ed\u4e0a\u4e0b\u6446\u98ce", "\u505c\u6b62\u4e0a\u4e0b\u6446\u98ce", "\u5173\u95ed\u4e0a\u4e0b\u98ce"],
        "expected_keyword": "guan bi shang xia bai feng",
        "keyword_candidates": ["guan bi shang xia bai feng", "ting zhi shang xia bai feng", "guan bi shang xia feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_177"],
    },
    {
        "semantic": "swing_left_right_open",
        "group": "\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5de6\u53f3\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5de6\u53f3\u6446\u98ce",
        "expected_online_asr": "\u6253\u5f00\u5de6\u53f3\u6446\u98ce",
        "online_asr_candidates": ["\u6253\u5f00\u5de6\u53f3\u6446\u98ce", "\u5de6\u53f3\u6446\u98ce", "\u5de6\u53f3\u98ce"],
        "expected_keyword": "da kai zuo you bai feng",
        "keyword_candidates": ["da kai zuo you bai feng", "zuo you bai feng", "zuo you feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_181"],
    },
    {
        "semantic": "swing_left_right_close",
        "group": "\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5de6\u53f3\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5de6\u53f3\u6446\u98ce",
        "expected_online_asr": "\u5173\u95ed\u5de6\u53f3\u6446\u98ce",
        "online_asr_candidates": ["\u5173\u95ed\u5de6\u53f3\u6446\u98ce", "\u505c\u6b62\u5de6\u53f3\u6446\u98ce", "\u5173\u95ed\u5de6\u53f3\u98ce"],
        "expected_keyword": "guan bi zuo you bai feng",
        "keyword_candidates": ["guan bi zuo you bai feng", "ting zhi zuo you bai feng", "guan bi zuo you feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_184"],
    },
    {
        "semantic": "volume_max",
        "group": "\u97f3\u91cf",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5927\u97f3\u91cf",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5927\u97f3\u91cf",
        "expected_online_asr": "\u6700\u5927\u97f3\u91cf",
        "expected_keyword": "zui da yin liang",
        "keyword_candidates": ["zui da yin liang", "yin liang bai fen zhi yi bai"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_206"],
    },
    {
        "semantic": "volume_min",
        "group": "\u97f3\u91cf",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5c0f\u97f3\u91cf",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5c0f\u97f3\u91cf",
        "expected_online_asr": "\u6700\u5c0f\u97f3\u91cf",
        "expected_keyword": "zui xiao yin liang",
        "keyword_candidates": ["zui xiao yin liang", "yin liang bai fen zhi yi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_209"],
    },
    {
        "semantic": "sleep_mode",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u7761\u7720",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u7761\u7720",
        "expected_online_asr": "\u7761\u7720",
        "expected_keyword": "da kai shui mian",
        "keyword_candidates": ["da kai shui mian", "shui mian"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_279"],
    },
    {
        "semantic": "auto_mode",
        "group": "\u6a21\u5f0f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u81ea\u52a8\u6a21\u5f0f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u81ea\u52a8\u6a21\u5f0f",
        "expected_online_asr": "\u81ea\u52a8\u6a21\u5f0f",
        "expected_keyword": "zi dong mo shi",
        "keyword_candidates": ["zi dong mo shi", "da kai zi dong mo shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_16"],
    },
    {
        "semantic": "dehumidify_mode",
        "group": "\u6a21\u5f0f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u9664\u6e7f\u6a21\u5f0f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u9664\u6e7f\u6a21\u5f0f",
        "expected_online_asr": "\u9664\u6e7f\u6a21\u5f0f",
        "online_asr_candidates": ["\u9664\u6e7f\u6a21\u5f0f", "\u62bd\u6e7f\u6a21\u5f0f"],
        "expected_keyword": "chu shi mo shi",
        "keyword_candidates": ["chu shi mo shi", "chou shi mo shi", "da kai chu shi mo shi", "chu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_35"],
    },
    {
        "semantic": "smart_clean_open",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u667a\u6e05\u6d01",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u667a\u6e05\u6d01",
        "expected_online_asr": "\u6253\u5f00\u667a\u6e05\u6d01",
        "expected_keyword": "da kai zhi qing jie",
        "keyword_candidates": ["da kai zhi qing jie", "zhi qing jie"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_255"],
    },
    {
        "semantic": "electric_heat_open",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u7535\u8f85\u70ed",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u7535\u8f85\u70ed",
        "expected_online_asr": "\u6253\u5f00\u7535\u8f85\u70ed",
        "expected_keyword": "da kai dian fu re",
        "keyword_candidates": ["da kai dian fu re", "dian fu re"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_258"],
    },
    {
        "semantic": "display_open",
        "group": "\u5c4f\u663e",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5c4f\u663e",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5c4f\u663e",
        "expected_online_asr": "\u6253\u5f00\u5c4f\u663e",
        "online_asr_candidates": ["\u6253\u5f00\u5c4f\u663e", "\u6253\u5f00\u663e\u793a", "\u5c4f\u663e", "\u663e\u793a"],
        "expected_keyword": "da kai ping xian",
        "keyword_candidates": ["da kai ping xian", "da kai xian shi", "ping xian", "xian shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_262"],
    },
    {
        "semantic": "display_close",
        "group": "\u5c4f\u663e",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5c4f\u663e",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5c4f\u663e",
        "expected_online_asr": "\u5173\u95ed\u5c4f\u663e",
        "online_asr_candidates": ["\u5173\u95ed\u5c4f\u663e", "\u5173\u6389\u5c4f\u663e", "\u53d6\u6d88\u5c4f\u663e", "\u5173\u95ed\u663e\u793a"],
        "expected_keyword": "guan bi ping xian",
        "keyword_candidates": ["guan bi ping xian", "guan diao ping xian", "qu xiao ping xian", "guan bi xian shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_266"],
    },
    {
        "semantic": "eco_open",
        "group": "ECO",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8282\u80fd",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8282\u80fd",
        "expected_online_asr": "\u8282\u80fd",
        "online_asr_candidates": ["\u8282\u80fd", "ECO", "\u7701\u7535"],
        "expected_keyword": "jie neng",
        "keyword_candidates": ["jie neng", "da kai eco", "eco", "sheng dian", "jie neng mo shi", "sheng dian mo shi"],
        "strict_keyword": False,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_275",
            "\u9ad8\u9891\u8bcd:\u6253\u5f00\u8282\u80fd\u7701\u7535",
        ],
    },
    {
        "semantic": "eco_close",
        "group": "ECO",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95edECO",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95edECO",
        "expected_online_asr": "\u5173\u95edECO",
        "online_asr_candidates": ["\u5173\u95edECO", "\u53d6\u6d88ECO", "\u5173\u95ed\u7701\u7535\u6a21\u5f0f"],
        "expected_keyword": "guan bi eco",
        "keyword_candidates": ["guan bi eco", "qu xiao eco", "guan bi sheng dian mo shi", "guan bi jie neng"],
        "strict_keyword": False,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_277",
            "\u9ad8\u9891\u8bcd:\u5173\u95ed\u8282\u80fd\u7701\u7535",
        ],
    },
    {
        "semantic": "query_mode",
        "group": "\u67e5\u8be2\u72b6\u6001",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u67e5\u8be2\u7a7a\u8c03\u6a21\u5f0f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u67e5\u8be2\u7a7a\u8c03\u6a21\u5f0f",
        "expected_online_asr": "\u67e5\u8be2\u7a7a\u8c03\u6a21\u5f0f",
        "online_asr_candidates": ["\u67e5\u8be2\u7a7a\u8c03\u6a21\u5f0f", "\u7a7a\u8c03\u6a21\u5f0f"],
        "expected_keyword": "cha xun kong tiao mo shi",
        "keyword_candidates": ["cha xun kong tiao mo shi", "kong tiao mo shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_427"],
    },
    {
        "semantic": "query_wind_speed",
        "group": "\u67e5\u8be2\u72b6\u6001",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u67e5\u8be2\u7a7a\u8c03\u98ce\u901f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u67e5\u8be2\u7a7a\u8c03\u98ce\u901f",
        "expected_online_asr": "\u67e5\u8be2\u7a7a\u8c03\u98ce\u901f",
        "online_asr_candidates": ["\u67e5\u8be2\u7a7a\u8c03\u98ce\u901f", "\u7a7a\u8c03\u98ce\u901f"],
        "expected_keyword": "cha xun kong tiao feng su",
        "keyword_candidates": ["cha xun kong tiao feng su", "kong tiao feng su"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_429"],
    },
    {
        "semantic": "timer_power_on_half_hour",
        "group": "\u5b9a\u65f6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5b9a\u65f6\u534a\u5c0f\u65f6\u5f00\u673a",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5b9a\u65f6\u534a\u5c0f\u65f6\u5f00\u673a",
        "expected_online_asr": "\u5b9a\u65f6\u534a\u5c0f\u65f6\u5f00\u673a",
        "online_asr_candidates": ["\u5b9a\u65f6\u534a\u5c0f\u65f6\u5f00\u673a", "\u4e09\u5341\u5206\u949f\u540e\u5f00\u673a"],
        "expected_keyword": "ding shi ban xiao shi kai ji",
        "keyword_candidates": [
            "ding shi ban xiao shi kai ji",
            "ding shi san shi fen zhong kai ji",
            "san shi fen zhong hou kai ji",
        ],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_287"],
    },
    {
        "semantic": "timer_cancel",
        "group": "\u5b9a\u65f6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u53d6\u6d88\u5b9a\u65f6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u53d6\u6d88\u5b9a\u65f6",
        "expected_online_asr": "\u53d6\u6d88\u5b9a\u65f6",
        "online_asr_candidates": ["\u53d6\u6d88\u5b9a\u65f6", "\u5173\u95ed\u5b9a\u65f6"],
        "expected_keyword": "qu xiao ding shi",
        "keyword_candidates": ["qu xiao ding shi", "guan bi ding shi", "ding shi guan bi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_327"],
    },
    {
        "semantic": "strong_dehumidify_open",
        "group": "\u5f3a\u52b2\u9664\u6e7f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5f3a\u52b2\u9664\u6e7f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5f3a\u52b2\u9664\u6e7f",
        "expected_online_asr": "\u6253\u5f00\u5f3a\u52b2\u9664\u6e7f",
        "online_asr_candidates": ["\u6253\u5f00\u5f3a\u52b2\u9664\u6e7f", "\u5f3a\u52b2\u9664\u6e7f"],
        "expected_keyword": "da kai qiang jin chu shi",
        "keyword_candidates": ["da kai qiang jin chu shi", "qiang jin chu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_410"],
    },
    {
        "semantic": "drying_open",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\u6253\u5f00\u5e72\u71e5\u9632\u9709",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5e72\u71e5",
        "expected_online_asr": "\u6253\u5f00\u5e72\u71e5\u9632\u9709",
        "online_asr_candidates": ["\u6253\u5f00\u5e72\u71e5\u9632\u9709", "\u6253\u5f00\u5e72\u71e5"],
        "expected_keyword": "da kai gan zao fang mei",
        "keyword_candidates": ["da kai gan zao fang mei", "da kai gan zao", "gan zao", "da kai nei ji fang mei"],
        "strict_keyword": False,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_422",
            "\u547d\u4ee4\u8bcd\u8868:\u6253\u5f00\u5e72\u71e5\u9632\u9709",
        ],
    },
    {
        "semantic": "sleep_mode_off",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7761\u7720",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7761\u7720",
        "expected_online_asr": "\u5173\u95ed\u7761\u7720",
        "expected_keyword": "guan bi shui mian",
        "keyword_candidates": ["guan bi shui mian", "shui mian"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_280"],
    },
    {
        "semantic": "smart_clean_close",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u667a\u6e05\u6d01",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u667a\u6e05\u6d01",
        "expected_online_asr": "\u5173\u95ed\u667a\u6e05\u6d01",
        "expected_keyword": "guan bi zhi qing jie",
        "keyword_candidates": ["guan bi zhi qing jie", "zhi qing jie"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_257"],
    },
    {
        "semantic": "electric_heat_close",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7535\u8f85\u70ed",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7535\u8f85\u70ed",
        "expected_online_asr": "\u5173\u95ed\u7535\u8f85\u70ed",
        "expected_keyword": "guan bi dian fu re",
        "keyword_candidates": ["guan bi dian fu re", "dian fu re"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_260"],
    },
    {
        "semantic": "drying_close",
        "group": "\u5176\u4ed6\u63a7\u5236",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\u5173\u95ed\u5e72\u71e5\u9632\u9709",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5e72\u71e5",
        "expected_online_asr": "\u5173\u95ed\u5e72\u71e5\u9632\u9709",
        "online_asr_candidates": ["\u5173\u95ed\u5e72\u71e5\u9632\u9709", "\u5173\u95ed\u5e72\u71e5"],
        "expected_keyword": "guan bi gan zao fang mei",
        "keyword_candidates": ["guan bi gan zao fang mei", "guan bi gan zao", "guan bi nei ji fang mei"],
        "strict_keyword": False,
        "source_refs": [
            "\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_424",
            "\u547d\u4ee4\u8bcd\u8868:\u5173\u95ed\u5e72\u71e5\u9632\u9709",
        ],
    },
    {
        "semantic": "strong_dehumidify_close",
        "group": "\u5f3a\u52b2\u9664\u6e7f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5f3a\u52b2\u9664\u6e7f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5f3a\u52b2\u9664\u6e7f",
        "expected_online_asr": "\u5173\u95ed\u5f3a\u52b2\u9664\u6e7f",
        "online_asr_candidates": ["\u5173\u95ed\u5f3a\u52b2\u9664\u6e7f", "\u53d6\u6d88\u5f3a\u52b2\u9664\u6e7f"],
        "expected_keyword": "guan bi qiang jin chu shi",
        "keyword_candidates": ["guan bi qiang jin chu shi", "qu xiao qiang jin chu shi", "qiang jin chu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_412"],
    },
    {
        "semantic": "body_sterilize_open",
        "group": "\u673a\u8eab\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u673a\u8eab\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u673a\u8eab\u9664\u83cc",
        "expected_online_asr": "\u6253\u5f00\u673a\u8eab\u9664\u83cc",
        "online_asr_candidates": ["\u6253\u5f00\u673a\u8eab\u9664\u83cc", "\u673a\u8eab\u9664\u83cc"],
        "expected_keyword": "da kai ji shen chu jun",
        "keyword_candidates": ["da kai ji shen chu jun", "ji shen chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_360"],
    },
    {
        "semantic": "body_sterilize_close",
        "group": "\u673a\u8eab\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u673a\u8eab\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u673a\u8eab\u9664\u83cc",
        "expected_online_asr": "\u5173\u95ed\u673a\u8eab\u9664\u83cc",
        "online_asr_candidates": ["\u5173\u95ed\u673a\u8eab\u9664\u83cc", "\u673a\u8eab\u9664\u83cc"],
        "expected_keyword": "guan bi ji shen chu jun",
        "keyword_candidates": ["guan bi ji shen chu jun", "ji shen chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_362"],
    },
    {
        "semantic": "wind_direction_left",
        "group": "\u98ce\u5411",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u5de6\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u5de6\u5439",
        "expected_online_asr": "\u5411\u5de6\u5439",
        "online_asr_candidates": ["\u5411\u5de6\u5439", "\u5f80\u5de6\u5439"],
        "expected_keyword": "xiang zuo chui",
        "keyword_candidates": ["xiang zuo chui", "wang zuo chui", "zuo chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_196"],
    },
    {
        "semantic": "wind_direction_right",
        "group": "\u98ce\u5411",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u53f3\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u53f3\u5439",
        "expected_online_asr": "\u5411\u53f3\u5439",
        "online_asr_candidates": ["\u5411\u53f3\u5439", "\u5f80\u53f3\u5439"],
        "expected_keyword": "xiang you chui",
        "keyword_candidates": ["xiang you chui", "wang you chui", "you chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_198"],
    },
    {
        "semantic": "wind_direction_up",
        "group": "\u98ce\u5411",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u4e0a\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u4e0a\u5439",
        "expected_online_asr": "\u5411\u4e0a\u5439",
        "online_asr_candidates": ["\u5411\u4e0a\u5439", "\u5f80\u4e0a\u5439"],
        "expected_keyword": "xiang shang chui",
        "keyword_candidates": ["xiang shang chui", "wang shang chui", "shang chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_200"],
    },
    {
        "semantic": "wind_direction_down",
        "group": "\u98ce\u5411",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u4e0b\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u4e0b\u5439",
        "expected_online_asr": "\u5411\u4e0b\u5439",
        "online_asr_candidates": ["\u5411\u4e0b\u5439", "\u5f80\u4e0b\u5439"],
        "expected_keyword": "xiang xia chui",
        "keyword_candidates": ["xiang xia chui", "wang xia chui", "xia chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_202"],
    },
    {
        "semantic": "wind_direction_center",
        "group": "\u98ce\u5411",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u4e2d\u95f4\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5411\u4e2d\u95f4\u5439",
        "expected_online_asr": "\u5411\u4e2d\u95f4\u5439",
        "online_asr_candidates": ["\u5411\u4e2d\u95f4\u5439", "\u5f80\u4e2d\u95f4\u5439", "\u5411\u4e2d\u95f4\u98ce"],
        "expected_keyword": "xiang zhong jian chui",
        "keyword_candidates": ["xiang zhong jian chui", "wang zhong jian chui", "zhong jian chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_204"],
    },
    {
        "semantic": "sterilize_open",
        "group": "\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u9664\u83cc",
        "expected_online_asr": "\u6253\u5f00\u9664\u83cc",
        "online_asr_candidates": ["\u6253\u5f00\u9664\u83cc", "\u6253\u5f00\u7a7a\u6c14\u9664\u83cc"],
        "expected_keyword": "da kai chu jun",
        "keyword_candidates": ["da kai chu jun", "da kai kong qi chu jun", "chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_331"],
    },
    {
        "semantic": "sterilize_close",
        "group": "\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u9664\u83cc",
        "expected_online_asr": "\u5173\u95ed\u9664\u83cc",
        "online_asr_candidates": ["\u5173\u95ed\u9664\u83cc", "\u5173\u95ed\u7a7a\u6c14\u9664\u83cc"],
        "expected_keyword": "guan bi chu jun",
        "keyword_candidates": ["guan bi chu jun", "guan bi kong qi chu jun", "chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_333"],
    },
    {
        "semantic": "sterilize_strong",
        "group": "\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5f3a\u52b2\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5f3a\u52b2\u9664\u83cc",
        "expected_online_asr": "\u5f3a\u52b2\u9664\u83cc",
        "online_asr_candidates": ["\u5f3a\u52b2\u9664\u83cc", "\u5f3a\u52b2\u7a7a\u6c14\u9664\u83cc"],
        "expected_keyword": "qiang jin chu jun",
        "keyword_candidates": ["qiang jin chu jun", "qiang jing chu jun", "qiang jin kong qi chu jun", "qiang jing kong qi chu jun", "kong qi chu jun qiang jin"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_348"],
    },
    {
        "semantic": "air_sterilize_open",
        "group": "\u7a7a\u6c14\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u7a7a\u6c14\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u7a7a\u6c14\u9664\u83cc",
        "expected_online_asr": "\u6253\u5f00\u7a7a\u6c14\u9664\u83cc",
        "online_asr_candidates": ["\u6253\u5f00\u7a7a\u6c14\u9664\u83cc", "\u6253\u5f00\u9664\u83cc"],
        "expected_keyword": "da kai kong qi chu jun",
        "keyword_candidates": ["da kai kong qi chu jun", "da kai chu jun", "kong qi chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_354"],
    },
    {
        "semantic": "air_sterilize_close",
        "group": "\u7a7a\u6c14\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7a7a\u6c14\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7a7a\u6c14\u9664\u83cc",
        "expected_online_asr": "\u5173\u95ed\u7a7a\u6c14\u9664\u83cc",
        "online_asr_candidates": ["\u5173\u95ed\u7a7a\u6c14\u9664\u83cc", "\u5173\u95ed\u9664\u83cc"],
        "expected_keyword": "guan bi kong qi chu jun",
        "keyword_candidates": ["guan bi kong qi chu jun", "guan bi chu jun", "kong qi chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_356"],
    },
    {
        "semantic": "ac_sterilize_open",
        "group": "\u7a7a\u8c03\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u7a7a\u8c03\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u7a7a\u8c03\u9664\u83cc",
        "expected_online_asr": "\u7a7a\u8c03\u9664\u83cc",
        "online_asr_candidates": ["\u7a7a\u8c03\u9664\u83cc", "\u6253\u5f00\u7a7a\u8c03\u9664\u83cc"],
        "expected_keyword": "kong tiao chu jun",
        "keyword_candidates": ["kong tiao chu jun", "da kai kong tiao chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_358"],
    },
    {
        "semantic": "ac_sterilize_close",
        "group": "\u7a7a\u8c03\u9664\u83cc",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7a7a\u8c03\u9664\u83cc",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u7a7a\u8c03\u9664\u83cc",
        "expected_online_asr": "\u5173\u95ed\u7a7a\u8c03\u9664\u83cc",
        "online_asr_candidates": ["\u5173\u95ed\u7a7a\u8c03\u9664\u83cc", "\u7a7a\u8c03\u9664\u83cc"],
        "expected_keyword": "guan bi kong tiao chu jun",
        "keyword_candidates": ["guan bi kong tiao chu jun", "kong tiao chu jun"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_359"],
    },
    {
        "semantic": "fresh_air_open",
        "group": "\u65b0\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u65b0\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u65b0\u98ce",
        "expected_online_asr": "\u6253\u5f00\u65b0\u98ce",
        "online_asr_candidates": ["\u6253\u5f00\u65b0\u98ce", "\u5f00\u542f\u65b0\u98ce"],
        "expected_keyword": "da kai xin feng",
        "keyword_candidates": ["da kai xin feng", "kai qi xin feng", "xin feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_99"],
    },
    {
        "semantic": "fresh_air_close",
        "group": "\u65b0\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u65b0\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u65b0\u98ce",
        "expected_online_asr": "\u5173\u95ed\u65b0\u98ce",
        "online_asr_candidates": ["\u5173\u95ed\u65b0\u98ce", "\u5173\u6389\u65b0\u98ce"],
        "expected_keyword": "guan bi xin feng",
        "keyword_candidates": ["guan bi xin feng", "guan diao xin feng", "xin feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_101"],
    },
    {
        "semantic": "fresh_air_auto_open",
        "group": "\u65b0\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u81ea\u52a8\u65b0\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u81ea\u52a8\u65b0\u98ce",
        "expected_online_asr": "\u6253\u5f00\u81ea\u52a8\u65b0\u98ce",
        "online_asr_candidates": ["\u6253\u5f00\u81ea\u52a8\u65b0\u98ce", "\u6253\u5f00\u4e3b\u52a8\u65b0\u98ce"],
        "expected_keyword": "da kai zi dong xin feng",
        "keyword_candidates": ["da kai zi dong xin feng", "da kai zhu dong xin feng", "zi dong xin feng", "zhu dong xin feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_102"],
    },
    {
        "semantic": "fresh_air_auto_close",
        "group": "\u65b0\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u81ea\u52a8\u65b0\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u81ea\u52a8\u65b0\u98ce",
        "expected_online_asr": "\u5173\u95ed\u81ea\u52a8\u65b0\u98ce",
        "online_asr_candidates": ["\u5173\u95ed\u81ea\u52a8\u65b0\u98ce", "\u5173\u95ed\u4e3b\u52a8\u65b0\u98ce"],
        "expected_keyword": "guan bi zi dong xin feng",
        "keyword_candidates": ["guan bi zi dong xin feng", "guan bi zhu dong xin feng", "zi dong xin feng", "zhu dong xin feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_104"],
    },
    {
        "semantic": "purify_open",
        "group": "\u51c0\u5316",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u51c0\u5316",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u51c0\u5316",
        "expected_online_asr": "\u6253\u5f00\u51c0\u5316",
        "online_asr_candidates": ["\u6253\u5f00\u51c0\u5316", "\u5f00\u542f\u51c0\u5316"],
        "expected_keyword": "da kai jing hua",
        "keyword_candidates": ["da kai jing hua", "kai qi jing hua", "jing hua"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_363"],
    },
    {
        "semantic": "purify_close",
        "group": "\u51c0\u5316",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u51c0\u5316",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u51c0\u5316",
        "expected_online_asr": "\u5173\u95ed\u51c0\u5316",
        "online_asr_candidates": ["\u5173\u95ed\u51c0\u5316", "\u5173\u6389\u51c0\u5316"],
        "expected_keyword": "guan bi jing hua",
        "keyword_candidates": ["guan bi jing hua", "guan diao jing hua", "jing hua"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_365"],
    },
    {
        "semantic": "powerful_mode_open",
        "group": "\u5f3a\u52b2",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5f3a\u52b2",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5f3a\u52b2",
        "expected_online_asr": "\u6253\u5f00\u5f3a\u52b2",
        "online_asr_candidates": ["\u6253\u5f00\u5f3a\u52b2", "\u6253\u5f00\u5f3a\u52b2\u98ce", "\u5f3a\u52b2\u6a21\u5f0f"],
        "expected_keyword": "da kai qiang jin",
        "keyword_candidates": ["da kai qiang jin", "da kai qiang jing", "da kai qiang jin feng", "da kai qiang jing feng", "qiang jin", "qiang jing", "qiang jin feng", "qiang jing feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_431"],
    },
    {
        "semantic": "powerful_mode_close",
        "group": "\u5f3a\u52b2",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5f3a\u52b2",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5f3a\u52b2",
        "expected_online_asr": "\u5173\u95ed\u5f3a\u52b2",
        "online_asr_candidates": ["\u5173\u95ed\u5f3a\u52b2", "\u5173\u95ed\u5f3a\u52b2\u98ce", "\u53d6\u6d88\u5f3a\u52b2"],
        "expected_keyword": "guan bi qiang jin",
        "keyword_candidates": ["guan bi qiang jin", "guan bi qiang jing", "guan bi qiang jin feng", "guan bi qiang jing feng", "qu xiao qiang jin", "qu xiao qiang jing", "qiang jin", "qiang jing"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_433"],
    },
]

COMMANDS.extend([
    {
        "semantic": "wind_min",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5c0f\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5c0f\u98ce",
        "expected_online_asr": "\u6700\u5c0f\u98ce",
        "online_asr_candidates": ["\u6700\u5c0f\u98ce", "\u98ce\u901f\u8c03\u5230\u6700\u5c0f", "\u6700\u4f4e\u98ce"],
        "expected_keyword": "zui xiao feng",
        "keyword_candidates": ["zui xiao feng", "feng su zui xiao", "feng su tiao dao zui xiao", "zui di feng", "feng su bai fen zhi yi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_40"],
    },
    {
        "semantic": "wind_mid",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u4e2d\u7b49\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u4e2d\u7b49\u98ce",
        "expected_online_asr": "\u4e2d\u7b49\u98ce",
        "online_asr_candidates": ["\u4e2d\u7b49\u98ce", "\u4e2d\u98ce"],
        "expected_keyword": "zhong deng feng",
        "keyword_candidates": ["zhong deng feng", "zhong feng", "feng su zhong deng", "feng su bai fen zhi liu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_43"],
    },
    {
        "semantic": "wind_max",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5927\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6700\u5927\u98ce",
        "expected_online_asr": "\u6700\u5927\u98ce",
        "online_asr_candidates": ["\u6700\u5927\u98ce", "\u98ce\u901f\u8c03\u5230\u6700\u5927"],
        "expected_keyword": "zui da feng",
        "keyword_candidates": ["zui da feng", "feng su zui da", "feng su tiao dao zui da", "feng su bai fen zhi yi bai"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_44"],
    },
    {
        "semantic": "wind_silent",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u9759\u97f3\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u9759\u97f3\u98ce",
        "expected_online_asr": "\u9759\u97f3\u98ce",
        "online_asr_candidates": ["\u9759\u97f3\u98ce", "\u9759\u97f3\u98ce\u901f"],
        "expected_keyword": "jing yin feng",
        "keyword_candidates": ["jing yin feng", "jing yin feng su", "feng su bai fen zhi er shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_47"],
    },
    {
        "semantic": "wind_increase",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u589e\u5927\u98ce\u901f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u589e\u5927\u98ce\u901f",
        "expected_online_asr": "\u589e\u5927\u98ce\u901f",
        "online_asr_candidates": ["\u589e\u5927\u98ce\u901f", "\u8c03\u5927\u98ce\u901f", "\u98ce\u901f\u5927\u70b9"],
        "expected_keyword": "zeng da feng su",
        "keyword_candidates": ["zeng da feng su", "tiao da feng su", "jia da feng su", "feng su da dian"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_56"],
    },
    {
        "semantic": "wind_decrease",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u51cf\u5c0f\u98ce\u901f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u51cf\u5c0f\u98ce\u901f",
        "expected_online_asr": "\u51cf\u5c0f\u98ce\u901f",
        "online_asr_candidates": ["\u51cf\u5c0f\u98ce\u901f", "\u8c03\u5c0f\u98ce\u901f", "\u98ce\u901f\u5c0f\u70b9"],
        "expected_keyword": "jian xiao feng su",
        "keyword_candidates": ["jian xiao feng su", "tiao xiao feng su", "jiang di feng su", "feng su xiao dian"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_51"],
    },
    {
        "semantic": "wind_level_3",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u98ce\u901f\u4e09\u6863",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u98ce\u901f\u4e09\u6863",
        "expected_online_asr": "\u98ce\u901f\u4e09\u6863",
        "online_asr_candidates": ["\u98ce\u901f\u4e09\u6863", "\u4e09\u6863\u98ce"],
        "expected_keyword": "feng su san dang",
        "keyword_candidates": ["feng su san dang", "san dang feng", "feng su san", "feng su bai fen zhi liu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_63"],
    },
    {
        "semantic": "wind_percent_50",
        "group": "\u98ce\u901f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u98ce\u901f\u767e\u5206\u4e4b\u4e94\u5341",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u98ce\u901f\u767e\u5206\u4e4b\u4e94\u5341",
        "expected_online_asr": "\u98ce\u901f\u767e\u5206\u4e4b\u4e94\u5341",
        "online_asr_candidates": ["\u98ce\u901f\u767e\u5206\u4e4b\u4e94\u5341", "\u98ce\u901f\u4e94\u5341"],
        "expected_keyword": "feng su bai fen zhi wu shi",
        "keyword_candidates": ["feng su bai fen zhi wu shi", "feng su wu shi", "feng su tiao dao wu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_80"],
    },
    {
        "semantic": "temperature_16",
        "group": "\u6e29\u5ea6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5341\u516d\u5ea6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5341\u516d\u5ea6",
        "expected_online_asr": "\u5341\u516d\u5ea6",
        "online_asr_candidates": ["\u5341\u516d\u5ea6", "16\u5ea6"],
        "expected_keyword": "shi liu du",
        "keyword_candidates": ["shi liu du", "tiao dao shi liu du"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_125"],
    },
    {
        "semantic": "temperature_30",
        "group": "\u6e29\u5ea6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u4e09\u5341\u5ea6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u4e09\u5341\u5ea6",
        "expected_online_asr": "\u4e09\u5341\u5ea6",
        "online_asr_candidates": ["\u4e09\u5341\u5ea6", "30\u5ea6"],
        "expected_keyword": "san shi du",
        "keyword_candidates": ["san shi du", "tiao dao san shi du"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_153"],
    },
    {
        "semantic": "temperature_up_one",
        "group": "\u6e29\u5ea6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8c03\u9ad8\u4e00\u5ea6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8c03\u9ad8\u4e00\u5ea6",
        "expected_online_asr": "\u8c03\u9ad8\u4e00\u5ea6",
        "online_asr_candidates": ["\u8c03\u9ad8\u4e00\u5ea6", "\u589e\u5927\u4e00\u5ea6"],
        "expected_keyword": "tiao gao yi du",
        "keyword_candidates": ["tiao gao yi du", "zeng da yi du", "wen du tiao gao yi du"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_160"],
    },
    {
        "semantic": "temperature_down_one",
        "group": "\u6e29\u5ea6",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8c03\u4f4e\u4e00\u5ea6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u8c03\u4f4e\u4e00\u5ea6",
        "expected_online_asr": "\u8c03\u4f4e\u4e00\u5ea6",
        "online_asr_candidates": ["\u8c03\u4f4e\u4e00\u5ea6", "\u51cf\u5c0f\u4e00\u5ea6"],
        "expected_keyword": "tiao di yi du",
        "keyword_candidates": ["tiao di yi du", "jian xiao yi du", "wen du tiao di yi du"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_162"],
    },
    {
        "semantic": "volume_increase",
        "group": "\u97f3\u91cf",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u589e\u5927\u97f3\u91cf",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u589e\u5927\u97f3\u91cf",
        "expected_online_asr": "\u589e\u5927\u97f3\u91cf",
        "online_asr_candidates": ["\u589e\u5927\u97f3\u91cf", "\u8c03\u5927\u97f3\u91cf", "\u58f0\u97f3\u5927\u4e00\u70b9"],
        "expected_keyword": "zeng da yin liang",
        "keyword_candidates": ["zeng da yin liang", "tiao da yin liang", "sheng yin da yi dian", "yin liang da dian"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_212"],
    },
    {
        "semantic": "volume_decrease",
        "group": "\u97f3\u91cf",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u51cf\u5c0f\u97f3\u91cf",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u51cf\u5c0f\u97f3\u91cf",
        "expected_online_asr": "\u51cf\u5c0f\u97f3\u91cf",
        "online_asr_candidates": ["\u51cf\u5c0f\u97f3\u91cf", "\u8c03\u5c0f\u97f3\u91cf", "\u58f0\u97f3\u5c0f\u4e00\u70b9"],
        "expected_keyword": "jian xiao yin liang",
        "keyword_candidates": ["jian xiao yin liang", "tiao xiao yin liang", "sheng yin xiao yi dian", "yin liang xiao dian"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_216"],
    },
    {
        "semantic": "volume_percent_50",
        "group": "\u97f3\u91cf",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u97f3\u91cf\u767e\u5206\u4e4b\u4e94\u5341",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u97f3\u91cf\u767e\u5206\u4e4b\u4e94\u5341",
        "expected_online_asr": "\u97f3\u91cf\u767e\u5206\u4e4b\u4e94\u5341",
        "online_asr_candidates": ["\u97f3\u91cf\u767e\u5206\u4e4b\u4e94\u5341", "\u97f3\u91cf\u4e94\u5341"],
        "expected_keyword": "yin liang bai fen zhi wu shi",
        "keyword_candidates": ["yin liang bai fen zhi wu shi", "yin liang wu shi", "yin liang tiao dao wu shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_236"],
    },
    {
        "semantic": "swing_all_open",
        "group": "\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u6446\u98ce",
        "expected_online_asr": "\u6253\u5f00\u6446\u98ce",
        "online_asr_candidates": ["\u6253\u5f00\u6446\u98ce", "\u5f00\u542f\u6446\u98ce", "\u6446\u98ce"],
        "expected_keyword": "da kai bai feng",
        "keyword_candidates": ["da kai bai feng", "kai qi bai feng", "bai feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_188"],
    },
    {
        "semantic": "swing_all_close",
        "group": "\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u6446\u98ce",
        "expected_online_asr": "\u5173\u95ed\u6446\u98ce",
        "online_asr_candidates": ["\u5173\u95ed\u6446\u98ce", "\u5173\u6389\u6446\u98ce", "\u505c\u6b62\u6446\u98ce"],
        "expected_keyword": "guan bi bai feng",
        "keyword_candidates": ["guan bi bai feng", "guan diao bai feng", "ting zhi bai feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_191"],
    },
    {
        "semantic": "direction_swing_left",
        "group": "\u65b9\u5411\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5de6\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5de6\u6446\u98ce",
        "expected_online_asr": "\u5de6\u6446\u98ce",
        "online_asr_candidates": ["\u5de6\u6446\u98ce"],
        "expected_keyword": "zuo bai feng",
        "keyword_candidates": ["zuo bai feng", "da kai zuo feng dao bai feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_194"],
    },
    {
        "semantic": "direction_swing_right",
        "group": "\u65b9\u5411\u6446\u98ce",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u53f3\u6446\u98ce",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u53f3\u6446\u98ce",
        "expected_online_asr": "\u53f3\u6446\u98ce",
        "online_asr_candidates": ["\u53f3\u6446\u98ce"],
        "expected_keyword": "you bai feng",
        "keyword_candidates": ["you bai feng", "da kai you feng dao bai feng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_195"],
    },
    {
        "semantic": "query_temperature",
        "group": "\u67e5\u8be2\u72b6\u6001",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u67e5\u8be2\u7a7a\u8c03\u6e29\u5ea6",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u67e5\u8be2\u7a7a\u8c03\u6e29\u5ea6",
        "expected_online_asr": "\u67e5\u8be2\u7a7a\u8c03\u6e29\u5ea6",
        "online_asr_candidates": ["\u67e5\u8be2\u7a7a\u8c03\u6e29\u5ea6", "\u7a7a\u8c03\u6e29\u5ea6"],
        "expected_keyword": "cha xun kong tiao wen du",
        "keyword_candidates": ["cha xun kong tiao wen du", "kong tiao wen du"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_425"],
    },
    {
        "semantic": "no_wind_sense_open",
        "group": "\u65e0\u98ce\u611f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u65e0\u98ce\u611f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u65e0\u98ce\u611f",
        "expected_online_asr": "\u6253\u5f00\u65e0\u98ce\u611f",
        "online_asr_candidates": ["\u6253\u5f00\u65e0\u98ce\u611f", "\u65e0\u98ce\u611f"],
        "expected_keyword": "da kai wu feng gan",
        "keyword_candidates": ["da kai wu feng gan", "wu feng gan"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_270"],
    },
    {
        "semantic": "no_wind_sense_close",
        "group": "\u65e0\u98ce\u611f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u65e0\u98ce\u611f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u65e0\u98ce\u611f",
        "expected_online_asr": "\u5173\u95ed\u65e0\u98ce\u611f",
        "online_asr_candidates": ["\u5173\u95ed\u65e0\u98ce\u611f", "\u53d6\u6d88\u65e0\u98ce\u611f"],
        "expected_keyword": "guan bi wu feng gan",
        "keyword_candidates": ["guan bi wu feng gan", "qu xiao wu feng gan", "wu feng gan"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_272"],
    },
    {
        "semantic": "anti_direct_blow_open",
        "group": "\u9632\u76f4\u5439",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u9632\u76f4\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u9632\u76f4\u5439",
        "expected_online_asr": "\u6253\u5f00\u9632\u76f4\u5439",
        "online_asr_candidates": ["\u6253\u5f00\u9632\u76f4\u5439", "\u9632\u76f4\u5439"],
        "expected_keyword": "da kai fang zhi chui",
        "keyword_candidates": ["da kai fang zhi chui", "fang zhi chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_281"],
    },
    {
        "semantic": "anti_direct_blow_close",
        "group": "\u9632\u76f4\u5439",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u9632\u76f4\u5439",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u9632\u76f4\u5439",
        "expected_online_asr": "\u5173\u95ed\u9632\u76f4\u5439",
        "online_asr_candidates": ["\u5173\u95ed\u9632\u76f4\u5439", "\u53d6\u6d88\u9632\u76f4\u5439"],
        "expected_keyword": "guan bi fang zhi chui",
        "keyword_candidates": ["guan bi fang zhi chui", "qu xiao fang zhi chui", "fang zhi chui"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_283"],
    },
    {
        "semantic": "soft_wind_open",
        "group": "\u67d4\u98ce\u611f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u67d4\u98ce\u611f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u67d4\u98ce\u611f",
        "expected_online_asr": "\u6253\u5f00\u67d4\u98ce\u611f",
        "online_asr_candidates": ["\u6253\u5f00\u67d4\u98ce\u611f", "\u67d4\u98ce\u611f"],
        "expected_keyword": "da kai rou feng gan",
        "keyword_candidates": ["da kai rou feng gan", "rou feng gan"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_284"],
    },
    {
        "semantic": "soft_wind_close",
        "group": "\u67d4\u98ce\u611f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u67d4\u98ce\u611f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u67d4\u98ce\u611f",
        "expected_online_asr": "\u5173\u95ed\u67d4\u98ce\u611f",
        "online_asr_candidates": ["\u5173\u95ed\u67d4\u98ce\u611f", "\u53d6\u6d88\u67d4\u98ce\u611f"],
        "expected_keyword": "guan bi rou feng gan",
        "keyword_candidates": ["guan bi rou feng gan", "qu xiao rou feng gan", "rou feng gan"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_286"],
    },
    {
        "semantic": "one_key_good_air_open",
        "group": "\u4e00\u952e\u597d\u7a7a\u6c14",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u4e00\u952e\u597d\u7a7a\u6c14",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u4e00\u952e\u597d\u7a7a\u6c14",
        "expected_online_asr": "\u6253\u5f00\u4e00\u952e\u597d\u7a7a\u6c14",
        "online_asr_candidates": ["\u6253\u5f00\u4e00\u952e\u597d\u7a7a\u6c14", "\u4e00\u952e\u597d\u7a7a\u6c14"],
        "expected_keyword": "da kai yi jian hao kong qi",
        "keyword_candidates": ["da kai yi jian hao kong qi", "yi jian hao kong qi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_383"],
    },
    {
        "semantic": "one_key_good_air_close",
        "group": "\u4e00\u952e\u597d\u7a7a\u6c14",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u4e00\u952e\u597d\u7a7a\u6c14",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u4e00\u952e\u597d\u7a7a\u6c14",
        "expected_online_asr": "\u5173\u95ed\u4e00\u952e\u597d\u7a7a\u6c14",
        "online_asr_candidates": ["\u5173\u95ed\u4e00\u952e\u597d\u7a7a\u6c14", "\u53d6\u6d88\u4e00\u952e\u597d\u7a7a\u6c14"],
        "expected_keyword": "guan bi yi jian hao kong qi",
        "keyword_candidates": ["guan bi yi jian hao kong qi", "qu xiao yi jian hao kong qi", "yi jian hao kong qi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_385"],
    },
    {
        "semantic": "health_open",
        "group": "\u5065\u5eb7",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5065\u5eb7",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u5065\u5eb7",
        "expected_online_asr": "\u6253\u5f00\u5065\u5eb7",
        "online_asr_candidates": ["\u6253\u5f00\u5065\u5eb7", "\u5065\u5eb7"],
        "expected_keyword": "da kai jian kang",
        "keyword_candidates": ["da kai jian kang", "jian kang"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_386"],
    },
    {
        "semantic": "health_close",
        "group": "\u5065\u5eb7",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5065\u5eb7",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u5065\u5eb7",
        "expected_online_asr": "\u5173\u95ed\u5065\u5eb7",
        "online_asr_candidates": ["\u5173\u95ed\u5065\u5eb7", "\u53d6\u6d88\u5065\u5eb7"],
        "expected_keyword": "guan bi jian kang",
        "keyword_candidates": ["guan bi jian kang", "qu xiao jian kang", "jian kang"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_388"],
    },
    {
        "semantic": "humidify_open",
        "group": "\u4fdd\u6e7f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u4fdd\u6e7f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u4fdd\u6e7f",
        "expected_online_asr": "\u6253\u5f00\u4fdd\u6e7f",
        "online_asr_candidates": ["\u6253\u5f00\u4fdd\u6e7f", "\u4fdd\u6e7f"],
        "expected_keyword": "da kai bao shi",
        "keyword_candidates": ["da kai bao shi", "bao shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_389"],
    },
    {
        "semantic": "humidify_close",
        "group": "\u4fdd\u6e7f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u4fdd\u6e7f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u4fdd\u6e7f",
        "expected_online_asr": "\u5173\u95ed\u4fdd\u6e7f",
        "online_asr_candidates": ["\u5173\u95ed\u4fdd\u6e7f", "\u53d6\u6d88\u4fdd\u6e7f"],
        "expected_keyword": "guan bi bao shi",
        "keyword_candidates": ["guan bi bao shi", "qu xiao bao shi", "bao shi"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_391"],
    },
    {
        "semantic": "humidify_strong",
        "group": "\u4fdd\u6e7f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5f3a\u52b2\u4fdd\u6e7f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5f3a\u52b2\u4fdd\u6e7f",
        "expected_online_asr": "\u5f3a\u52b2\u4fdd\u6e7f",
        "online_asr_candidates": ["\u5f3a\u52b2\u4fdd\u6e7f"],
        "expected_keyword": "qiang jin bao shi",
        "keyword_candidates": ["qiang jin bao shi", "qiang jing bao shi", "bao shi qiang jin"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_404"],
    },
    {
        "semantic": "ambient_light_open",
        "group": "\u6c1b\u56f4\u706f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u6c1b\u56f4\u706f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u6c1b\u56f4\u706f",
        "expected_online_asr": "\u6253\u5f00\u6c1b\u56f4\u706f",
        "online_asr_candidates": ["\u6253\u5f00\u6c1b\u56f4\u706f", "\u6c1b\u56f4\u706f"],
        "expected_keyword": "da kai fen wei deng",
        "keyword_candidates": ["da kai fen wei deng", "fen wei deng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_413"],
    },
    {
        "semantic": "ambient_light_close",
        "group": "\u6c1b\u56f4\u706f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u6c1b\u56f4\u706f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u6c1b\u56f4\u706f",
        "expected_online_asr": "\u5173\u95ed\u6c1b\u56f4\u706f",
        "online_asr_candidates": ["\u5173\u95ed\u6c1b\u56f4\u706f", "\u53d6\u6d88\u6c1b\u56f4\u706f"],
        "expected_keyword": "guan bi fen wei deng",
        "keyword_candidates": ["guan bi fen wei deng", "qu xiao fen wei deng", "fen wei deng"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_415"],
    },
    {
        "semantic": "light_open",
        "group": "\u706f\u5149",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u706f\u5149",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u706f\u5149",
        "expected_online_asr": "\u6253\u5f00\u706f\u5149",
        "online_asr_candidates": ["\u6253\u5f00\u706f\u5149", "\u706f\u5149"],
        "expected_keyword": "da kai deng guang",
        "keyword_candidates": ["da kai deng guang", "deng guang"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_416"],
    },
    {
        "semantic": "light_close",
        "group": "\u706f\u5149",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u706f\u5149",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u706f\u5149",
        "expected_online_asr": "\u5173\u95ed\u706f\u5149",
        "online_asr_candidates": ["\u5173\u95ed\u706f\u5149", "\u53d6\u6d88\u706f\u5149"],
        "expected_keyword": "guan bi deng guang",
        "keyword_candidates": ["guan bi deng guang", "qu xiao deng guang", "deng guang"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_418"],
    },
    {
        "semantic": "smart_light_sensor_open",
        "group": "\u667a\u80fd\u5149\u611f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u667a\u80fd\u5149\u611f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u6253\u5f00\u667a\u80fd\u5149\u611f",
        "expected_online_asr": "\u6253\u5f00\u667a\u80fd\u5149\u611f",
        "online_asr_candidates": ["\u6253\u5f00\u667a\u80fd\u5149\u611f", "\u667a\u80fd\u5149\u611f"],
        "expected_keyword": "da kai zhi neng guang gan",
        "keyword_candidates": ["da kai zhi neng guang gan", "zhi neng guang gan"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_419"],
    },
    {
        "semantic": "smart_light_sensor_close",
        "group": "\u667a\u80fd\u5149\u611f",
        "online_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u667a\u80fd\u5149\u611f",
        "offline_text": "\u5c0f\u7f8e\u5c0f\u7f8e\uff0c\u5173\u95ed\u667a\u80fd\u5149\u611f",
        "expected_online_asr": "\u5173\u95ed\u667a\u80fd\u5149\u611f",
        "online_asr_candidates": ["\u5173\u95ed\u667a\u80fd\u5149\u611f", "\u53d6\u6d88\u667a\u80fd\u5149\u611f"],
        "expected_keyword": "guan bi zhi neng guang gan",
        "keyword_candidates": ["guan bi zhi neng guang gan", "qu xiao zhi neng guang gan", "zhi neng guang gan"],
        "strict_keyword": False,
        "source_refs": ["\u7f8e\u7684\u7a7a\u8c03_T6\u6302\u673a_421"],
    },
])


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def wait_for_hotspot_state(
    *,
    expect_operational_state: str,
    expect_client_mac: str = "",
    timeout_s: float = 120.0,
    interval_s: float = 2.0,
) -> Tuple[dict, bool]:
    deadline = time.time() + timeout_s
    last = hotspot_status()
    while time.time() <= deadline:
        last = hotspot_status()
        ok = str(last.get("operational_state")) == expect_operational_state
        if ok and expect_client_mac:
            macs = [str(item.get("mac_address", "")).lower() for item in last.get("clients", [])]
            ok = expect_client_mac.lower() in macs
        if ok:
            return last, True
        time.sleep(interval_s)
    return last, False


def response_evidence_online(metrics: dict) -> bool:
    return (
        metrics["ap_instruction_broadcast_count"] >= 1
        or metrics["ap_cloud_tts_recv_count"] >= 1
        or metrics["ap_cloud_tts_play_count"] >= 1
    )


def response_evidence_offline(metrics: dict) -> bool:
    return bool(
        metrics["wb_tts_callback_ids"]
        or metrics["tone_ids"]
        or metrics["wb_playback_end_count"] > 0
        or metrics["ap_cloud_tts_play_count"] > 0
    )


def extract_reply_texts(step_payload: dict) -> List[str]:
    texts: List[str] = []
    for line in step_payload.get("key_lines", []):
        for match in re.finditer(r'"text":"([^"]+)"', str(line)):
            texts.append(match.group(1))
    return texts


def has_unsupported_reply(reply_texts: List[str]) -> bool:
    markers = [
        "\u6682\u65f6\u4e0d\u652f\u6301\u8be5\u529f\u80fd",
        "\u4e0d\u652f\u6301\u8be5\u529f\u80fd",
        "\u6682\u4e0d\u652f\u6301",
        "\u4e0d\u652f\u6301",
        "\u8d85\u51fa\u63a7\u5236\u8303\u56f4",
        "\u672a\u80fd\u7406\u89e3",
        "\u672a\u80fd\u8bc6\u522b",
        "\u6362\u4e00\u79cd\u8bf4\u6cd5",
        "APP\u786e\u8ba4",
        "\u00e6\u009c\u00aa\u00e8\u0083\u00bd",
        "\u00e7\u0090\u0086\u00e8\u00a7\u00a3",
        "\u00e8\u00af\u0086\u00e5\u0088\u00ab",
        "\u00e6\u008d\u00a2",
        "\u00e6\u008a\u00b1\u00e6\u00ad\u0089",
        "\u00e4\u00b8\u008d\u00e5\u00a5\u00bd\u00e6\u0084\u008f\u00e6\u0080\u009d",
        "APP",
    ]
    return any(marker in text for text in reply_texts for marker in markers)


def semantic_ok(metrics: dict, cmd: dict, mode: str) -> bool:
    expected_keyword = cmd.get("expected_keyword", "")
    keyword_candidates = list(cmd.get("keyword_candidates") or ([expected_keyword] if expected_keyword else []))
    expected_online_asr = cmd.get("expected_online_asr", "")
    online_asr_candidates = list(cmd.get("online_asr_candidates") or ([expected_online_asr] if expected_online_asr else []))
    recognized = set(metrics["recognized_command_keywords"])
    online_asr = set(metrics["ap_online_asr_texts"])

    if mode == "online":
        if any(candidate in online_asr for candidate in online_asr_candidates):
            return True
        if any(candidate in recognized for candidate in keyword_candidates):
            return True
        return False

    if any(candidate in recognized for candidate in keyword_candidates):
        return True
    return False


def evaluate_step(cmd: dict, mode: str, step_payload: dict, probe_summary_path: Path) -> dict:
    metrics = step_payload["metrics"]
    reply_texts = extract_reply_texts(step_payload)
    checks = [
        {"name": "playback_returncode", "actual": step_payload["playback"]["returncode"], "expected": 0, "passed": step_payload["playback"]["returncode"] == 0},
        {"name": "cp_wake_count", "actual": metrics["cp_wake_count"], "expected": ">=1", "passed": metrics["cp_wake_count"] >= 1},
        {"name": "ap_wake_count", "actual": metrics["ap_wake_count"], "expected": ">=1", "passed": metrics["ap_wake_count"] >= 1},
        {"name": "cp_command_count", "actual": metrics["cp_command_count"], "expected": ">=1", "passed": metrics["cp_command_count"] >= 1},
    ]

    if mode == "online":
        checks.extend(
            [
                {"name": "wb_online_wake_count", "actual": metrics["wb_online_wake_count"], "expected": ">=1", "passed": metrics["wb_online_wake_count"] >= 1},
                {
                    "name": "response_evidence_online",
                    "actual": {
                        "ap_instruction_broadcast_count": metrics["ap_instruction_broadcast_count"],
                        "ap_cloud_tts_recv_count": metrics["ap_cloud_tts_recv_count"],
                        "ap_cloud_tts_play_count": metrics["ap_cloud_tts_play_count"],
                    },
                    "expected": "broadcast or cloud TTS",
                    "passed": response_evidence_online(metrics),
                },
                {
                    "name": "semantic_match_online",
                    "actual": {
                        "ap_online_asr_texts": metrics["ap_online_asr_texts"],
                        "recognized_command_keywords": metrics["recognized_command_keywords"],
                    },
                    "expected": {
                        "expected_online_asr": cmd.get("expected_online_asr", ""),
                        "online_asr_candidates": cmd.get("online_asr_candidates", []),
                        "expected_keyword": cmd.get("expected_keyword", ""),
                        "keyword_candidates": cmd.get("keyword_candidates", []),
                        "strict_keyword": cmd["strict_keyword"],
                    },
                    "passed": semantic_ok(metrics, cmd, mode),
                },
                {
                    "name": "unsupported_reply_online",
                    "actual": reply_texts,
                    "expected": "no unsupported business reply",
                    "passed": not has_unsupported_reply(reply_texts),
                },
            ]
        )
    else:
        checks.extend(
            [
                {"name": "ap_asr_count", "actual": metrics["ap_asr_count"], "expected": ">=1", "passed": metrics["ap_asr_count"] >= 1},
                {"name": "wb_asr_count", "actual": metrics["wb_asr_count"], "expected": ">=1", "passed": metrics["wb_asr_count"] >= 1},
                {
                    "name": "response_evidence_offline",
                    "actual": {
                        "wb_tts_callback_ids": metrics["wb_tts_callback_ids"],
                        "tone_ids": metrics["tone_ids"],
                        "wb_playback_end_count": metrics["wb_playback_end_count"],
                    },
                    "expected": "wb tts callback or tone/playback evidence",
                    "passed": response_evidence_offline(metrics),
                },
                {
                    "name": "semantic_match_offline",
                    "actual": {"recognized_command_keywords": metrics["recognized_command_keywords"]},
                    "expected": {
                        "expected_keyword": cmd.get("expected_keyword", ""),
                        "keyword_candidates": cmd.get("keyword_candidates", []),
                        "strict_keyword": cmd["strict_keyword"],
                    },
                    "passed": semantic_ok(metrics, cmd, mode),
                },
            ]
        )

    checks.extend(
        [
            {"name": "boot_marker_count", "actual": metrics["boot_marker_count"], "expected": 0, "passed": metrics["boot_marker_count"] == 0},
            {"name": "crash_marker_count", "actual": metrics["crash_marker_count"], "expected": 0, "passed": metrics["crash_marker_count"] == 0},
        ]
    )

    failed_checks = [item for item in checks if not item["passed"]]
    verdict = "PASS" if not failed_checks else "FAIL"
    return {
        "semantic": cmd["semantic"],
        "group": cmd["group"],
        "mode": mode,
        "spoken": step_payload["text"],
        "source_refs": cmd["source_refs"],
        "verdict": verdict,
        "failed_checks": failed_checks,
        "checks": checks,
        "probe_summary_path": str(probe_summary_path),
        "probe_step_id": step_payload["step_id"],
        "probe_step_dir": str(probe_summary_path.parent / step_payload["step_id"]),
        "metrics": {
            "cp_wake_count": metrics["cp_wake_count"],
            "ap_wake_count": metrics["ap_wake_count"],
            "cp_command_count": metrics["cp_command_count"],
            "ap_asr_count": metrics["ap_asr_count"],
            "wb_asr_count": metrics["wb_asr_count"],
            "wb_online_wake_count": metrics["wb_online_wake_count"],
            "ap_online_asr_texts": metrics["ap_online_asr_texts"],
            "recognized_command_keywords": metrics["recognized_command_keywords"],
            "wb_tts_callback_ids": metrics["wb_tts_callback_ids"],
            "tone_ids": metrics["tone_ids"],
            "ap_instruction_broadcast_count": metrics["ap_instruction_broadcast_count"],
            "ap_cloud_tts_recv_count": metrics["ap_cloud_tts_recv_count"],
            "ap_cloud_tts_play_count": metrics["ap_cloud_tts_play_count"],
            "boot_marker_count": metrics["boot_marker_count"],
            "crash_marker_count": metrics["crash_marker_count"],
            "reply_texts": reply_texts,
        },
    }


def run_mode_batch(commands: List[dict], mode: str, observe_ms: int) -> Tuple[Path, List[dict]]:
    label = f"ac_control_{mode}_{now_stamp()}"
    texts = [item[f"{mode}_text"] for item in commands]
    probe_summary_path = run_probe(texts=texts, device_key="", observe_ms=observe_ms, label=label)
    probe_summary = json.loads(probe_summary_path.read_text(encoding="utf-8"))
    results = [
        evaluate_step(cmd, mode, step_payload, probe_summary_path)
        for cmd, step_payload in zip(commands, probe_summary["steps"])
    ]
    return probe_summary_path, results


def run_probe_suite(observe_ms: int, commands: List[dict]) -> Path:
    session_dir = current_session_dir()
    workspace = workspace_root()
    env_path = workspace / "config" / "polaris_env.json"
    env_payload = json.loads(env_path.read_text(encoding="utf-8"))
    dut_mac = str(env_payload.get("current_deviceinfo", {}).get("mac", "")).lower()

    validation_dir = (
        session_dir
        / "artifacts"
        / "validation"
        / "ac_control_command_probe"
        / f"{now_stamp()}_ac_control_command_probe"
    )
    validation_dir.mkdir(parents=True, exist_ok=False)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "session_dir": str(session_dir),
        "validation_dir": str(validation_dir),
        "commands": commands,
        "observe_ms": observe_ms,
        "hotspot_before": None,
        "online_probe_summary": None,
        "online_results": [],
        "hotspot_off_result": None,
        "hotspot_offline_state": None,
        "hotspot_offline_ready": None,
        "offline_probe_summary": None,
        "offline_results": [],
        "hotspot_restore_result": None,
        "hotspot_after_restore": None,
        "hotspot_restore_ready": None,
        "counts": {},
    }

    summary["hotspot_before"] = hotspot_status()
    if str(summary["hotspot_before"].get("operational_state")) != "On":
        hotspot_set(True)
        _, _ = wait_for_hotspot_state(
            expect_operational_state="On",
            expect_client_mac=dut_mac,
            timeout_s=120.0,
        )
        summary["hotspot_before"] = hotspot_status()

    try:
        online_probe_summary, online_results = run_mode_batch(commands, "online", observe_ms=observe_ms)
        summary["online_probe_summary"] = str(online_probe_summary)
        summary["online_results"] = online_results

        summary["hotspot_off_result"] = hotspot_set(False)
        offline_state, offline_ready = wait_for_hotspot_state(expect_operational_state="Off", timeout_s=60.0)
        summary["hotspot_offline_state"] = offline_state
        summary["hotspot_offline_ready"] = offline_ready

        offline_probe_summary, offline_results = run_mode_batch(commands, "offline", observe_ms=observe_ms)
        summary["offline_probe_summary"] = str(offline_probe_summary)
        summary["offline_results"] = offline_results
    finally:
        summary["hotspot_restore_result"] = hotspot_set(True)
        after_restore, restore_ready = wait_for_hotspot_state(
            expect_operational_state="On",
            expect_client_mac=dut_mac,
            timeout_s=120.0,
        )
        summary["hotspot_after_restore"] = after_restore
        summary["hotspot_restore_ready"] = restore_ready

    merged = summary["online_results"] + summary["offline_results"]
    summary["counts"] = {
        "total": len(merged),
        "by_mode": dict(Counter(item["mode"] for item in merged)),
        "by_verdict": dict(Counter(item["verdict"] for item in merged)),
        "by_group": dict(Counter(item["group"] for item in merged)),
        "by_mode_verdict": dict(Counter(f"{item['mode']}:{item['verdict']}" for item in merged)),
    }
    write_json(validation_dir / "ac_control_command_probe_summary.json", summary)
    return validation_dir / "ac_control_command_probe_summary.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate representative AC control command words in online/offline modes")
    parser.add_argument("--observe-ms", type=int, default=15000)
    parser.add_argument("--semantics", nargs="*", default=[], help="Optional semantic ids to run, e.g. open_ac auto_mode")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    selected = set(args.semantics or [])
    commands = [item for item in COMMANDS if not selected or item["semantic"] in selected]
    if not commands:
        raise SystemExit("no commands selected")
    summary_path = run_probe_suite(observe_ms=args.observe_ms, commands=commands)
    print(summary_path)


if __name__ == "__main__":
    main()
