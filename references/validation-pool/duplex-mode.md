---
module_id: duplex-mode
title: 全双工、半双工和打断验证
tags: [全双工, 半双工, duplex, full-duplex, half-duplex, 打断, 播报中, 连续对话]
source_projects: [polaris]
---

# 全双工、半双工和打断验证

## 适用需求特征

- 需求包含全双工/半双工模式切换、播报中是否可收音、是否允许打断或连续对话。

## 变体维度

- 全双工开启后播报中可识别新命令。
- 全双工开启后只允许打断，不允许并行执行。
- 半双工播报中完全不响应，播报结束后恢复。
- 模式切换来自云控、串口配置或固件默认。

## 需求解析字段

- 模式设置入口、状态回读字段、播报窗口、打断规则、恢复规则、禁止行为。

## 验证方案模板

1. 设置模式并回读确认。
2. 触发一条会产生 TTS 的命令。
3. 在 TTS 播放中播放第二条命令。
4. 比对全双工/半双工预期。
5. 播报结束后验证收音恢复。

## 用例模板

- `DUPLEX-FULL-INTERRUPT-001`
- `DUPLEX-FULL-CONTINUE-001`
- `DUPLEX-HALF-BLOCK-DURING-TTS-001`
- `DUPLEX-HALF-RECOVER-AFTER-TTS-001`

## 断言与证据

- 全双工 PASS：播报窗口内出现第二条 ASR/命令闭环，且符合需求定义。
- 半双工 PASS：播报窗口内目标命令不执行，播报结束后同命令可执行。
- 模式设置未回读成功时，功能用例 BLOCKED。
- 播报窗口要用日志中的 TTS/play start/complete 限定，不能用人工听感。

## 执行器映射

- `tools/cloud/polaris_app_control.py` 的 `set-full-duplex`
- `tools/probe/polaris_phrase_probe.py`
- `tools/execution/polaris_doc_case_runner.py`

## 回灌规则

- 新增打断策略、连续对话策略或模式字段时，补充变体和证据标记。
