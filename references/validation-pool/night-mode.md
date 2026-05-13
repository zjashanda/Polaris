---
module_id: night-mode
title: 夜间模式验证
tags: [夜间模式, 夜间, night, set-night-mode, 静音, 灯光, 主动播报]
source_projects: [polaris]
---

# 夜间模式验证

## 适用需求特征

- 需要验证夜间模式开关、状态回读、夜间模式下的播报/灯光/主动交互限制。

## 变体维度

- 仅配置项，无可观察行为。
- 降低音量 / 禁止主动播报 / 控制灯光 / 多行为组合。
- 立即生效 / 重启后生效。
- 在线云控支持，离线语音不支持。

## 需求解析字段

- 开关入口、期望状态字段、关联行为、时间段、是否持久化、恢复动作。

## 验证方案模板

1. 确认设备在线和云控可用。
2. 下发夜间模式打开。
3. 验证设备收到并回读打开。
4. 验证需求定义的夜间行为。
5. 下发关闭并验证恢复。

## 用例模板

- `NIGHT-ON-001`
- `NIGHT-BEHAVIOR-001`
- `NIGHT-OFF-001`
- `NIGHT-PERSIST-001`

## 断言与证据

- 若需求只写“可设置夜间模式”，主断言是下发、收到、回读一致。
- 若需求定义具体行为，必须单独验证行为，不以“设置成功”替代。
- 需求未定义夜间行为时，不凭主观听感判 FAIL。

## 执行器映射

- `tools/cloud/polaris_app_control.py set-night-mode`
- `tools/probe/polaris_state_probe.py`
- `tools/probe/polaris_phrase_probe.py`

## 回灌规则

- 新发现夜间模式关联行为时，补充行为断言和恢复规则。
