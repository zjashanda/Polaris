# -*- coding: utf-8 -*-
from pathlib import Path
import sys

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = ROOT / 'config' / 'polaris_doc_case_status.json'
SOURCE_MD = ROOT / 'config' / 'polaris_auto_executable_case_detail.md'
OUTPUT_MD = ROOT / 'config' / 'polaris_fail_case_detail.md'


def sort_case_id(case_id: str):
    try:
        return int(case_id.split('_')[-1])
    except Exception:
        return case_id


def load_fail_items():
    status = json.loads(STATUS_PATH.read_text(encoding='utf-8'))
    items = [
        item for item in status['cases']
        if item.get('classification') == 'auto_executable_now' and item.get('result') == 'FAIL'
    ]
    items.sort(key=lambda item: (item.get('runner_kind', ''), sort_case_id(item['case_id'])))
    effective = status.get('effective_counts_after_recheck', {})
    return status, items, effective


def build_section_index(text: str):
    matches = list(re.finditer(r'(?m)^###\s+(.+?)$', text))
    sections = {}
    for idx, match in enumerate(matches):
        heading = match.group(1)
        case_id = heading.split(' ', 1)[0].strip()
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[case_id] = text[start:end].strip()
    return sections


def main():
    status, fail_items, effective = load_fail_items()
    source_text = SOURCE_MD.read_text(encoding='utf-8')
    sections = build_section_index(source_text)

    by_kind = defaultdict(list)
    for item in fail_items:
        by_kind[item.get('runner_kind', '')].append(item)

    lines = [
        '# Polaris FAIL 用例专项明细',
        '',
        '> 该文件从 `config/polaris_auto_executable_case_detail.md` 中抽取当前所有 FAIL 用例，便于只看失败项。',
        '',
        '## 当前统计',
        '',
        f"- 自动可执行总数：`{effective.get('auto_executable_now', 0)}`",
        f"- 当前 FAIL 总数：`{len(fail_items)}`",
        f"- 当前 session：`{status.get('session_dir', '')}`",
        f"- 来源大文件：`{SOURCE_MD}`",
        '',
        '## FAIL 家族分布',
        '',
        '| runner_kind | FAIL 数量 | case_id 列表 |',
        '| --- | --- | --- |',
    ]

    for kind in sorted(by_kind):
        case_ids = '、'.join(item['case_id'] for item in by_kind[kind])
        lines.append(f"| {kind} | {len(by_kind[kind])} | {case_ids} |")

    lines.append('')
    lines.append('## FAIL 详细内容')
    lines.append('')

    for kind in sorted(by_kind):
        items = by_kind[kind]
        lines.append(f'## {kind}')
        lines.append('')
        lines.append(f"- 当前 family FAIL 数：`{len(items)}`")
        lines.append('')
        for item in items:
            section = sections.get(item['case_id'])
            if section:
                lines.append(section)
                lines.append('')
            else:
                lines.append(f"### {item['case_id']} {item.get('name', '')}")
                lines.append('')
                lines.append('- 未能从大文件中抽取到该 case section，请回看原始大文件。')
                lines.append(f"- 原执行目录：`{item.get('execution_dir', '')}`")
                lines.append('')

    OUTPUT_MD.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    print(OUTPUT_MD)


if __name__ == '__main__':
    main()
