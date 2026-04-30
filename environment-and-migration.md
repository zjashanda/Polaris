# Polaris 环境与迁移说明

本文档统一使用 UTF-8 编码，用来说明当前 skill 所依赖的环境、默认值，以及换设备或换主机后需要先做哪些准备。

## 1. 主机环境要求

### 1.1 操作系统

- Windows 主机
- 可用 PowerShell
- 支持 Windows 热点相关接口

原因：`tools/device/polaris_network_orchestrator.py` 依赖 Windows 热点能力。

### 1.2 Python 与依赖包

当前工作流依赖这些 Python 包：

- `requests`
- `pyserial`
- `openpyxl`
- `websockets`
- `pyyaml`

### 1.3 外部工具与资产

- `ffmpeg`
- `listenai-play` 播放脚本
- 可用的本地 TTS 能力
  - 优先走项目内 TTS 构建路径
  - Windows 上可回退到 SAPI

## 2. 设备与连接要求

### 2.1 串口拓扑

当前默认拓扑：

- `COM12` = CP，只读日志
- `COM13` = WB01，可写
- `COM14` = AP，可写
- `COM15` = 电源/复位控制，可写

如果换机器后 COM 号变了，优先修这里：

- `tools/device/polaris_serial_harness.py`
- `tools/device/polaris_power_control.py`

### 2.2 播放链路

- 主机必须有一个能稳定播放到 DUT 麦克风的输出设备。
- 播放设备需要有稳定的 `device_key`，并能被 `listenai-play` 正常识别。

当前默认值来自：

- `config/polaris_env.json -> default_playback_device_key`

### 2.3 设备身份信息

当前流程依赖 AP `deviceinfo` 中的这些字段：

- `iot_id`
- `mac`
- `wakeup_id`

这些字段用于：

- 云端控制请求
- 结果同步
- 设备身份确认

补充说明：

- 如果重启后 `deviceinfo` 临时只回部分字段，当前脚本会回退使用 `config/polaris_env.json -> current_deviceinfo`，不会再因此阻断云控。

## 3. 仓库内必须保留的数据

迁移 skill 时，以下内容建议一起带走：

- `SKILL.md`
- `capabilities-and-usage.md`
- `environment-and-migration.md`
- `config/*.json`
- `config/*.md`
- `doc/api/common_request.py`
- `doc/cases/*.xlsx`
- `doc/reference/tone.h`
- `spec/cases/*.yaml`
- `spec/suites/*.yaml`
- `tools/**/*.py`

## 4. 当前默认配置

以当前仓库为准：

- 热点 SSID：`pcwifi24`
- 热点密码：`12345678`
- 云环境：`SIT`
- 默认唤醒词：`小美小美`
- 默认播放设备 key：`VID_8765&PID_5678:9_2A847557_7_0000`
- 当前设备：
  - `iot_id=177021372191476`
  - `mac=8C:3F:44:2B:7A:D9`

## 5. 新设备 bootstrap 顺序

换 DUT 后，建议严格按下面顺序做：

### 第 1 步：新建 session

```powershell
$ts = Get-Date -Format yyyyMMddHHmmss
New-Item -ItemType Directory -Path ("result\$ts") -Force | Out-Null
Set-Content .current_result_dir (Resolve-Path ("result\$ts")).Path -Encoding ASCII
python tools/device/polaris_serial_harness.py start --session-dir ("result\$ts")
```

### 第 2 步：确认串口映射

至少执行一次：

```powershell
$session = Get-Content .current_result_dir
python tools/device/polaris_serial_harness.py send --session-dir $session --port COM14 --command version
python tools/device/polaris_serial_harness.py send --session-dir $session --port COM13 --command "listen version"
```

### 第 3 步：确认播放链路

- 检查 `default_playback_device_key` 是否还是正确设备。
- 执行一次唤醒探测，确认 DUT 能真正听到播放音频。

### 第 4 步：采集设备身份

```powershell
python tools/cloud/polaris_app_control.py probe-device
python tools/probe/polaris_state_probe.py snapshot --label bootstrap
```

至少确认：

- `iot_id`
- `mac`
- `wakeup_id`
- 当前热点 IP

### 第 5 步：确认网络链路

```powershell
python tools/device/polaris_network_orchestrator.py hotspot-status
```

必要时继续跑：

```powershell
python tools/device/polaris_network_orchestrator.py hotspot-cycle
python tools/device/polaris_network_orchestrator.py vir-reboot --ssid pcwifi24 --pwd 12345678
```

### 第 6 步：先做最小冒烟

```powershell
python tools/probe/polaris_phrase_probe.py --text 小美小美 --observe-ms 15000 --label bootstrap_wake
python tools/probe/polaris_phrase_probe.py --text 小美小美 --text 打开空调 --observe-ms 15000 --label bootstrap_wake_cmd
python tools/cloud/polaris_app_control.py set-volume --value 20
python tools/cloud/polaris_app_control.py set-mic --enable 1
```

### 第 7 步：再扩到用例与报告

```powershell
python tools/reporting/polaris_doc_case_audit.py
python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_22 --device-key "YOUR_DEVICE_KEY"
python tools/reporting/polaris_status_sync.py
```

## 6. 换机器时优先检查的地方

### 必改或必核对

- `config/polaris_env.json`
  - `default_playback_device_key`
  - `current_env_label`
  - `current_deviceinfo`
- `tools/device/polaris_serial_harness.py`
  - 串口映射
- `tools/device/polaris_power_control.py`
  - `COM15` 是否变化
- `tools/execution/polaris_case_runner.py`
  - `listenai-play` 路径
- `tools/audio/polaris_audio_builder.py`
  - TTS 配置是否仍可用

## 7. 当前 skill 的迁移边界

满足下面条件时，通常可以直接复用这套 skill：

- 串口拓扑仍是 Polaris 风格
- 云端接口仍兼容当前 `common_request.py`
- 音频播放仍通过 `listenai-play` 或兼容入口完成
- 网络编排仍基于 Windows 热点

以下情况通常需要改脚本再继续：

- COM 号整体变化
- 播放路径变化
- 热点机制变化
- 云端接口或 payload 变化
- 设备型号能力边界明显不同

## 8. 当前不建议在新设备上默认继承的能力

这些能力即使脚本入口还在，也不要当作“默认可复用能力”：

- `set-character-value`
- `set-log`
- 自定义唤醒词本地生效

建议在新设备上重新验证通过后，再把它们加入主 skill。
