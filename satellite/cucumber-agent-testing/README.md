# Polaris Cucumber Agent Testing

这个目录把 Polaris 语音功能测试沉淀成 **Cucumber/BDD + 本地 Agent runner**：

- Feature 用自然语言描述“前置、动作、证据、断言”。
- `references/voice_core_mapping.json` 和 registry 固化每个功能怎么执行、怎么断言、怎么归因。
- 执行时不依赖大模型、不依赖网络生成脚本；clone 仓库后按配置文件即可运行。
- 默认 `plan-only` / `dry-run` 不占用串口、不播放音频；真机执行必须显式允许 side effects。

## 30 秒上手

在仓库根目录执行：

```powershell
# 1. 准备本机配置。首次 clone 后复制模板，再按自己的设备改参数。
Copy-Item satellite\cucumber-agent-testing\configs\polaris_env.example.json config\polaris_env.json
notepad config\polaris_env.json

# 2. 先 dry-run，确认会触发哪个场景、哪些脚本、哪些断言。
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json

# 3. 真机执行。会占用串口、播放声卡、可能调用网络/云端/上下电能力。
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode execute --allow-side-effects --manage-session
```

输出统一写到：

```text
satellite/cucumber-agent-testing/debug/runs/<时间戳>_<模式>/
```

关键文件：

- `execution_plan.md`：本次要执行什么。
- `run_summary.json`：runner 原始结果。
- `bdd_run_report.md`：BDD 汇总报告，execute 模式生成。
- `logs/`、`session/`：串口、播放、模块脚本证据。

## 两种触发方式

### 方式 A：按 tag 直接触发

适合熟悉框架的人：

```powershell
python satellite\cucumber-agent-testing\scripts\run_cucumber.py --mode dry-run --tag first_wake
python satellite\cucumber-agent-testing\scripts\run_cucumber.py --mode execute --tag first_wake --allow-side-effects --manage-session
```

### 方式 B：按任务配置触发（推荐给新人）

适合开源仓库 clone 后快速上手：

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\basic_command.example.json
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\basic_command.example.json --mode execute --allow-side-effects --manage-session
```

任务文件只描述“我要测哪个功能、用哪些输入、执行窗口多长、是否管理串口 session”。本机串口、声卡、Wi-Fi 等硬件差异放到 `config/polaris_env.json`。

## 必配参数

首次 clone 后至少检查这些参数：

| 配置路径 | 必填 | 含义 | 示例 |
| --- | --- | --- | --- |
| `serial.ports.ap` | 是 | AP/cskap 日志串口 | `COM14` |
| `serial.ports.cp` | 是 | CP/cskcp 日志串口 | `COM12` |
| `serial.ports.asr` | 是 | ASR/WB01 日志串口 | `COM13` |
| `serial.ports.control` | 按需 | 上下电/复位控制串口 | `COM15` |
| `serial.baudrate` | 是 | 串口波特率 | `115200` |
| `audio.default_playback_device_key` | 真机必填 | 播放唤醒词/命令词的声卡稳定 key | `VID_8765&PID_5678:9_2A847557_7_0000` |
| `device.wake_word` | 是 | 当前唤醒词中文文本 | `小美小美` |
| `device.wakeup_id` | 建议 | 设备日志里的唤醒 ID | `xiao mei xiao mei` |
| `network.wifi_ssid` | 联网场景必填 | 测试热点/路由 SSID | `pcwifi24` |
| `network.wifi_password` | 联网场景必填 | Wi-Fi 密码 | `12345678` |
| `paths.command_file` | 命令词场景必填 | 命令词文件路径 | `doc/fa2命令词.txt` |
| `timeouts.observe_ms` | 是 | 每轮触发后观察串口窗口 | `15000` |
| `timeouts.recognition_timeout_s` | 识别模式相关 | 识别模式超时时间 | `15` |
| `timeouts.half_duplex_timeout_s` | 半双工相关 | 半双工窗口/超时口径 | `15` |
| `timeouts.full_duplex_timeout_s` | 全双工相关 | 全双工窗口/超时口径 | `60` |
| `timeouts.timing_guard_ms` | 边界时序建议 | 避开唤醒播报和超时临界点的保护时间 | `1200` |

更详细说明见 `docs/configuration.md`。

## 任务配置长什么样

最小任务配置：

```json
{
  "schema": "polaris.cucumber.task.v1",
  "task_id": "first_wake_smoke",
  "scenario": { "tag": "first_wake" },
  "runner": { "mode": "dry-run" },
  "environment": { "env_file": "config/polaris_env.json" },
  "execution": {
    "observe_ms": 15000,
    "manage_session": true,
    "allow_side_effects": false
  }
}
```

如果是命令词识别，再加输入：

```json
{
  "inputs": {
    "command_file": "doc/fa2命令词.txt",
    "command_limit": 20
  }
}
```

新功能第一次接入，请从 `tasks/templates/new_feature.template.json` 复制，先补齐功能意图、前置、动作、期望证据和失败归因，再沉淀到正式 feature/mapping/registry。

## 已支持 tag

| tag | 功能 |
| --- | --- |
| `first_wake` | 首次唤醒 |
| `recognition_mode_wake` | 识别模式下唤醒 |
| `half_duplex_recognition` | 半双工识别 |
| `full_duplex_recognition` | 全双工识别 |
| `basic_command_recognition` | 基础命令词识别 |
| `requirement_command_smoke` | 需求命令词小样本 |
| `requirement_free_speech_smoke` | 需求自由说小样本 |
| `interrupt_prerequisite_measurement` | 打断前置自播测量 |
| `wake_interrupt` | 自播中唤醒打断 |
| `command_interrupt` | 自播中识别打断 |
| `network_recovery_basic` | 联网恢复基础验证 |
| `offline_oneshot_matrix` | 离线 one-shot 间隔矩阵 |
| `online_oneshot_matrix` | 在线 one-shot 间隔矩阵 |
| `false_wake_quiet_basic` | 静默误唤醒监听 |
| `wake_latency_smoke` | 唤醒响应时间小样本 |
| `continuous_wake_smoke` | 连续唤醒稳定性小样本 |
| `random_interval_wake_smoke` | 随机间隔唤醒小样本 |
| `online_vad_special_smoke` | 在线 VAD 专项小样本 |
| `attribution_validator_smoke` | 归因一致性复核 |
| `false_wake_human_speech_smoke` | 合成人声干扰误唤醒 |
| `false_wake_white_noise_smoke` | 白噪声误唤醒 |

## 新功能怎么接入

1. 在 `features/polaris_voice_core.feature` 写场景和 tag。
2. 在 `references/voice_core_mapping.json` 或 `step/action/assertion registry` 中注册执行逻辑。
3. 明确断言：哪些证据算 PASS，哪些算 FAIL/BLOCKED/TIMING_AMBIGUOUS/REQUIREMENT_REVIEW。
4. 在 `tasks/examples/` 增加一个可复制任务文件。
5. 先跑 `dry-run`，再真机小样本，最后再做压测或全量。

原则：自然语言用例可以变，但只要落在已注册的功能意图和 step/action/assertion 上，脚本就不需要大模型实时改代码。
