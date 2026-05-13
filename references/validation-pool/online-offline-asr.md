---
module_id: online-offline-asr
title: 在线 ASR/NLU/TTS 与离线识别对照
tags: [在线, 离线, ASR, NLU, TTS, keyword, tone, online_asr, offline_asr]
source_projects: [polaris]
---

# 在线 ASR/NLU/TTS 与离线识别对照

## 适用需求特征

- 同一语义需要在线/离线双态验证，或需要区分 ASR、NLU、TTS、离线 keyword 的失败层级。

## 变体维度

- 在线 ASR 正确但 NLU/业务失败。
- 在线不可用时离线可用。
- 离线 keyword 命中但 TTS/tone 不符合。
- 语音识别错误导致业务未触发。

## 需求解析字段

- 话术、在线 ASR 文本、离线 keyword、期望意图、期望 TTS/tone、网络前置、离线触发条件。

## 验证方案模板

1. 确认在线链路可用，执行在线 probe。
2. 记录 ASR、NLU、云端回复、TTS 播放。
3. 切换/构造离线条件或执行离线 probe。
4. 记录离线 keyword、tone、本地控制。
5. 对比两侧支持矩阵和失败层级。

## 用例模板

- `ASR-ONLINE-001`
- `ASR-OFFLINE-001`
- `ASR-ONLINE-OFFLINE-MATRIX-001`
- `ASR-MISRECOGNITION-TRIAGE-001`

## 断言与证据

- ASR 失败、NLU 失败、业务不支持、TTS 失败必须分层标注。
- 在线用例需要网络门禁；离线用例不得依赖云端成功。
- 识别候选词表不全时先修断言，不保留最终 FAIL。

## 执行器映射

- `tools/probe/polaris_phrase_probe.py`
- `tools/validation/polaris_ac_control_command_probe.py`
- `tools/validation/polaris_workbook_voice_recognition_batch.py`

## 回灌规则

- 新增 ASR/TTS 日志标记、误识别归因或话术别名时补充。
