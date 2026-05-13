---
module_id: volume-level
title: 音量调节、边界和回读
tags: [音量, volume, set-volume, 调大, 调小, 最大音量, 最小音量, 边界, 回读]
source_projects: [polaris, trisolaris-method]
---

# 音量调节、边界和回读

## 适用需求特征

- 需求包含音量设置、音量增减、最大/最小边界、默认音量、重启保持或 TTS 音量效果。

## 变体维度

- 通过云控设置固定值。
- 通过语音命令调大/调小。
- 回读值等于用户档位 / raw 编码需要转换。
- 设置立即生效 / 需保存 / 不持久化。

## 需求解析字段

- 音量范围、默认值、调节步长、边界提示、回读字段、保存日志、重启策略。

## 验证方案模板

1. 记录当前音量基线。
2. 设置固定音量并回读。
3. 调大/调小并验证变化方向。
4. 探测最大/最小边界。
5. 边界后再次操作验证提示或无变化。
6. 需要持久化时等待保存并重启。

## 用例模板

- `VOLUME-SET-001`
- `VOLUME-UP-001`
- `VOLUME-DOWN-001`
- `VOLUME-MAX-001`
- `VOLUME-MIN-001`
- `VOLUME-PERSIST-001`

## 断言与证据

- 云控返回成功后必须看设备回读或日志变化。
- 人耳音量变化只能作辅助；正式断言用配置/日志/播放状态。
- 回读变化但听感不明显，不直接判 FAIL，除非需求定义声压指标。
- ASR 误识别的语音调音量用例归 ASR/词表，不归音量功能。

## 执行器映射

- `tools/cloud/polaris_app_control.py set-volume`
- `tools/probe/polaris_phrase_probe.py`
- `tools/execution/polaris_doc_case_runner.py`

## 回灌规则

- 新增音量映射、边界提示或保存标记时补充。
