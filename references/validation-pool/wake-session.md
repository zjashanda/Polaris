---
module_id: wake-session
title: 唤醒、会话和超时
tags: [唤醒, 唤醒词, 小美小美, 会话, 超时, timeout, wake, WAKE, MODE, 重唤醒]
source_projects: [polaris, trisolaris-method]
---

# 唤醒、会话和超时

## 适用需求特征

- 有默认唤醒词、候选唤醒词、唤醒后会话窗口、超时退出或重唤醒要求。
- 需要验证未唤醒命令是否阻断、唤醒后命令是否闭环、超时后是否恢复空闲。

## 变体维度

- 纯唤醒 / 唤醒后命令 / oneshot。
- 超时起点：唤醒成功、响应播报结束、ASR 结束、业务执行结束。
- 超时后策略：必须重唤醒、允许连续对话、按模式变化。
- 在线/离线链路日志标记不同。

## 需求解析字段

- 默认唤醒词、wakeupid、超时时间、超时日志标记、唤醒成功日志、TTS/tone、是否允许连续命令。

## 验证方案模板

1. 默认唤醒 smoke。
2. 唤醒后基础命令闭环。
3. 未唤醒直接命令反例。
4. 超时时间测量。
5. 超时后不重唤醒阻断。
6. 超时后重唤醒恢复。

## 用例模板

- `WAKE-DEFAULT-001`
- `WAKE-CMD-001`
- `SESSION-BLOCK-NO-WAKE-001`
- `SESSION-TIMEOUT-001`
- `SESSION-REWAKE-001`

## 断言与证据

- 主证据：CP/AP/ASR 中 wake、ASR、offline/online callback、MODE 或对话状态标记。
- 辅证据：TTS/tone、状态快照、命令执行结果。
- 负例必须证明采集有效，不能用空日志判 PASS。
- 播放成功但无 wake 时，先排查播放链路和 DUT 听音，再判模型/固件。

## 执行器映射

- `tools/probe/polaris_phrase_probe.py`
- `tools/execution/polaris_doc_case_runner.py`
- `tools/reporting/polaris_status_sync.py`

## 回灌规则

- 新增超时起点、特殊会话窗口或新日志标记时，补充到本模块。
