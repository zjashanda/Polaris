# WS63 项目 Event Graph 与 Coverage 记录

WS63 通常为 AP+upper/control，无 CP；coverage 规则不应强制要求 CP marker。

## 当前状态

- 已在 `state_assertion_policy.json` 的 `coverage.projects.venusws63` 预留项目覆盖位置。
- 已在 `event_graph_rules.json` 预留项目私有规则示例，默认 disabled，等待真实日志后启用。
- 暂无新增真实日志可支撑更严格项目阈值；后续有压测/异常 run 目录时，按 `docs/wiki/voice-validation/failure-feedback.md` 反哺。
- 2026-05-27 真机 smoke 发现：AP 口 `COM16` 曾被 Xshell 占用，导致 managed logger 无法打开 AP 口；此类问题应判为环境 `BLOCKED`，不能把 AP 证据缺失归因为固件失败。已在 execute preflight 中增加串口打开探测，提前识别 Xshell/串口助手/旧 logger 占用。

## 新日志分析清单

| 项 | 需要记录 |
| --- | --- |
| 证据路径 | debug run 目录、replay package、原始串口日志。 |
| 事件链 | Wake/ASR/Command/TTS/Media/Network/Reboot/Crash 的时间顺序。 |
| 私有 marker | 项目日志中能代表 TTS、MP3、播放器、boot reason、API env 的字段。 |
| 规则建议 | Event Graph relation、within_ms、confidence、是否 enabled。 |
| coverage 建议 | required/forbidden event、min_transition_count、项目 profile 阈值。 |

## 启用门槛

没有真实日志前，不启用强规则；只保留候选和缺口，避免把项目猜测写成固件断言。
