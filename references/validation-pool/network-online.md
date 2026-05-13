---
module_id: network-online
title: 联网、热点和云端在线链路
tags: [联网, Wi-Fi, wifi, 热点, SSID, cloud, online, deviceinfo, IP, 断网, 重连]
source_projects: [polaris]
---

# 联网、热点和云端在线链路

## 适用需求特征

- 需要验证设备连接热点/Wi-Fi、注册云端、在线 ASR/NLU/TTS 或云控接口可用。

## 变体维度

- 首次配网 / 已配网重启 / 修改 SSID 后重启 / 断网重连。
- SIT/UAT/PRO 云环境。
- 在线业务成功但离线正常，或离线正常但在线失败。

## 需求解析字段

- SSID、密码、env、cloud status、IP、iot_id、mac、wakeup_id、在线 ASR/TTS 标记。

## 验证方案模板

1. 查询热点状态。
2. 下发或确认 `vir_ssid/vir_pwd`。
3. 重启设备并等待联网。
4. 采集 `deviceinfo` 和 cloud status。
5. 运行在线 probe 和云控 probe。

## 用例模板

- `NET-HOTSPOT-STATUS-001`
- `NET-VIR-REBOOT-001`
- `NET-CLOUD-ONLINE-001`
- `NET-DEVICEINFO-001`
- `NET-ONLINE-ASR-001`

## 断言与证据

- 热点有 client 只证明链路之一；必须结合设备 IP、cloud status 和在线业务。
- 云控失败前先区分 token/接口/设备离线。
- 同环境其他设备正常而当前 DUT 异常，才倾向设备/固件网络问题。
- 设备离线时在线用例 BLOCKED，不得判在线 ASR 固件 FAIL。

## 执行器映射

- `tools/device/polaris_network_orchestrator.py`
- `tools/probe/polaris_state_probe.py`
- `tools/cloud/polaris_app_control.py`

## 回灌规则

- 新增网络状态标记、云端错误码或重连规则时补充。
