---
module_id: cloud-control-settings
title: 云控设置类能力验证
tags: [云控, App, set-volume, set-mic, set-night-mode, set-full-duplex, 多唤醒, 方言, 主动交互, 配置]
source_projects: [polaris]
---

# 云控设置类能力验证

## 适用需求特征

- 需求或用例要求通过云端/App 设置设备配置，并验证设备行为或状态回读。

## 变体维度

- 接口成功且设备生效。
- 接口成功但设备未生效。
- 云端返回业务不支持。
- 设置需要重启后生效或立即生效。
- 设置有持久化要求或只在当前会话有效。

## 需求解析字段

- 控制项、入参、期望返回、设备日志标记、回读字段、行为验证、是否支持、是否持久化。

## 验证方案模板

1. 执行 cloud probe 确认设备在线。
2. 下发目标设置。
3. 读取 HTTP 返回与错误码。
4. 在 AP/ASR 日志确认设备收到配置。
5. 状态回读或行为验证。
6. 如涉及保存，重启后复测。

## 用例模板

- `CLOUD-PROBE-001`
- `CLOUD-SETTING-APPLY-001`
- `CLOUD-SETTING-READBACK-001`
- `CLOUD-SETTING-UNSUPPORTED-001`

## 断言与证据

- HTTP 200/业务成功不是最终 PASS；必须有设备侧日志、回读或行为变化。
- 业务 `code=501` 或明确不支持时，按需求/能力矩阵归因，不判固件 FAIL。
- 云 token、云端 5xx、设备离线归 BLOCKED 或云端问题。

## 执行器映射

- `tools/cloud/polaris_app_control.py`
- `tools/probe/polaris_state_probe.py`
- `tools/reporting/polaris_status_sync.py`

## 回灌规则

- 每新增一个云控项，补充入参、日志标记、回读字段和支持矩阵。
