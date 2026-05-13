---
module_id: ac-control-command
title: 空调控制命令词验证
tags: [空调, 开机, 关机, 温度, 风速, 模式, 摆风, ECO, 除湿, 除菌, 新风, 净化, command]
source_projects: [polaris]
---

# 空调控制命令词验证

## 适用需求特征

- 需要验证空调业务语义，包括开关机、模式、温度、风速、摆风、ECO、除菌、新风、净化等。

## 变体维度

- 在线支持 / 离线支持 / 仅单侧支持 / 当前机型不支持。
- ASR 命中但云端业务不支持。
- 离线 keyword 命中但无真实空调状态变化，仅 TTS/tone 闭环。
- 需要空调开机前置或特定模式前置。

## 需求解析字段

- 语义、话术、在线 ASR 期望、离线 keyword、期望 TTS/tone、状态变化、机型支持矩阵、前置状态。

## 验证方案模板

1. 建立前置状态，例如开机。
2. 在线短语探测并记录 ASR/NLU/TTS/控制结果。
3. 离线短语探测并记录 keyword/tone/控制结果。
4. 对不支持项验证返回“不支持”是否符合能力矩阵。
5. 对状态依赖项验证前置不足时的提示。

## 用例模板

- `AC-ONLINE-CONTROL-001`
- `AC-OFFLINE-CONTROL-001`
- `AC-UNSUPPORTED-001`
- `AC-STATE-DEPENDENT-001`

## 断言与证据

- ASR 命中不等于控制成功；必须看 NLU/TTS/状态或设备日志闭环。
- 云端回复“不支持”时，先查当前机型能力矩阵。
- 离线用例以 keyword、tone/TTS 和本地控制闭环为主。
- 同义话术要用同一需求行官方别名收敛，避免 TTS/话术选择问题变成固件 FAIL。

## 执行器映射

- `tools/validation/polaris_ac_control_command_probe.py`
- `tools/probe/polaris_phrase_probe.py`
- `tools/execution/polaris_doc_case_runner.py`

## 回灌规则

- 新增空调 family、支持矩阵或在线/离线差异时补充变体。
