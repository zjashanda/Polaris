# venusws63 项目 Profile

## 定位

`venusws63` 是当前正在调试的新 AP+WiFi/WS63 设备项目。该项目只有 AP、上位/WiFi 和控制口，没有独立 CP 串口。

## 硬件拓扑

| 角色 | 串口 | 波特率 | 用途 |
| --- | --- | --- | --- |
| AP | `COM14` | `921600` | AP 日志观察口 |
| 上位/WiFi | `COM13` | `921600` | 上位/WiFi 日志观察口 |
| control | `COM15` | `115200` | 上下电、PA 控制口 |
| CP | 无 | - | 当前项目没有独立 CP 串口 |

## 声卡与唤醒词

- 声卡 key：`VID_8765&PID_5678:9_2A847557_7_0000`
- 唤醒词：`小美小美`
- 日志唤醒 ID：`xiao mei xiao mei`

## 必须执行的 PA 前置

如果声卡播放不生效，先在控制/上下电串口 `COM15@115200` 输入：

```text
uut-pa.on
pa-enable.set 0 17 0 1
```

注意：这两个命令不能发到 `COM14` 或 `COM13`。

## 已验证证据

- 控制口 `uut-switch1.on` / `uut-switch1.off` / `uut-switch1.on` 可控制上电掉电。
- 下发 PA 前置后，声卡播放 `小美小美` 可以唤醒设备。
- AP `COM14` 出现：`Pre Wakeup: xiao mei xiao mei`、`wakeup_callback, keyword: xiao mei xiao mei`、`cloud asr with <SID>`。
- 上位 `COM13` 出现：`online_wakeup, SID: <uuid>`。

## 当前可验证能力

### 已具备基础链路，可优先落地

- 首次唤醒。
- 识别模式下唤醒。
- 唤醒响应时间 smoke。
- 连续唤醒、随机间隔唤醒、首次唤醒率和识别模式唤醒率压测。
- 静默误唤醒、人声干扰误唤醒、白噪声误唤醒。

### 需要把旧 CP 断言改成 AP+上位断言后验证

- 基础命令词识别。
- 需求命令词小样本。
- 需求自由说探索性小样本。
- 离线/在线 one-shot 间隔矩阵。
- 打断前置自播测量、自播中唤醒打断、自播中识别打断。
- 在线 VAD 专项：设备自身在线时可测。

### 需要补充配置入口后验证

- 半双工/全双工模式切换：需要确认新设备通过 App/cloud、语音开关词还是本地串口命令切换。
- 音量、夜间模式、多唤醒、唤醒阈值、唤醒词变更等配置类：需要 App/cloud API、IoT ID/token 或本地等价命令。
- 上电/掉电保持：控制口可执行电源循环，但每个配置项需要先能自动设置。

## 当前排除项

- 联网/断网恢复、Windows 热点切换、清配网、重新配网：当前设备没有连接本机 Wi-Fi，不能由本机稳定控制网络状态。
- 依赖独立 CP 串口的旧断言：必须改为 AP+上位证据后再执行。
- OTA、8 通道 AEC/录音、遥控器/面板按键、人工听辨发音人：需要额外外设或人工资料。

## AP+上位断言建议

- 唤醒 PASS：声卡播放成功 + AP 出现 `wakeup_callback` 或 `Pre Wakeup` + 上位出现 `online_wakeup` 或 AP 出现 `cloud asr with <SID>`。
- 命令/语料 PASS：已唤醒 + AP/上位出现 `online_asr_callbak`、ASR 文本、TTS、状态闭环或 intent 证据。
- BLOCKED：声卡播放失败、PA 未开、串口无日志、设备重启、设备离线导致云端 ASR 不可用。
- FAIL：前置和播放均正常，但有效窗口内没有目标 AP/上位识别或响应证据。
