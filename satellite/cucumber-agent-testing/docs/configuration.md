# 配置说明

本文说明 clone 仓库后需要配置哪些文件、每个参数是什么意思、什么时候必须填写。

## 文件分层

| 文件 | 是否提交 Git | 用途 |
| --- | --- | --- |
| `satellite/cucumber-agent-testing/configs/polaris_env.example.json` | 是 | 本地环境配置模板，给所有人复制。 |
| `config/polaris_env.json` | 否 | 每台电脑自己的串口、声卡、网络、设备信息。 |
| `satellite/cucumber-agent-testing/tasks/examples/*.json` | 是 | 某个功能的触发任务示例。 |
| `satellite/cucumber-agent-testing/tasks/templates/new_feature.template.json` | 是 | 新功能接入前的沉淀模板。 |
| `satellite/cucumber-agent-testing/references/voice_core_mapping.json` | 是 | 已沉淀功能的执行脚本、断言和归因规则。 |
| `satellite/cucumber-agent-testing/features/polaris_voice_core.feature` | 是 | Cucumber 自然语言用例。 |

## 本地环境配置 `config/polaris_env.json`

首次使用：

```powershell
Copy-Item satellite\cucumber-agent-testing\configs\polaris_env.example.json config\polaris_env.json
notepad config\polaris_env.json
```

### `serial`

```json
"serial": {
  "baudrate": 115200,
  "ports": {
    "ap": "COM14",
    "cp": "COM12",
    "asr": "COM13",
    "control": "COM15"
  }
}
```

- `baudrate`：串口波特率。当前 Polaris 常用 `115200`。
- `ports.ap`：AP/cskap 日志串口，通常用于看联网、TTS、云端、设备状态日志。
- `ports.cp`：CP/cskcp 日志串口，通常用于看离线唤醒、离线命令、关键词识别日志。
- `ports.asr`：ASR/WB01 串口，通常用于看 ASR、联网状态、WB01 侧日志。
- `ports.control`：上下电/复位控制串口；只在需要电源循环、复位、断电上电恢复时使用。

如果你机器上的串口号不同，只改这里，不要改 feature 和 mapping。

### `audio`

```json
"audio": {
  "default_playback_device_key": "VID_8765&PID_5678:9_2A847557_7_0000",
  "playback_volume": 80
}
```

- `default_playback_device_key`：播放设备稳定 key。真机执行唤醒词、命令词、噪声、打断音频时必须配置。
- `playback_volume`：建议记录目标音量，便于复现实验。脚本是否主动设置音量取决于具体 action。

如果 key 配错，常见表现是脚本 PASS 了播放命令启动，但设备听不到声音，最终唤醒/识别失败。这类应归因到播放链路或设备听音链路，不应直接判固件失败。

### `device`

```json
"device": {
  "wake_word": "小美小美",
  "wakeup_id": "xiao mei xiao mei",
  "model": "",
  "iot_id": "",
  "mac": ""
}
```

- `wake_word`：要播放/合成的唤醒词中文文本。更换唤醒词时改这里。
- `wakeup_id`：设备日志中的唤醒 ID，用于辅助断言和排查。
- `model`：设备型号。某些测试项只适用于特定机型时用于 skip/block 归因。
- `iot_id`、`mac`：联网、云端、设备状态查询时用于确认是不是当前 DUT。

### `network`

```json
"network": {
  "wifi_ssid": "pcwifi24",
  "wifi_password": "12345678",
  "enable_hotspot_control": false
}
```

- `wifi_ssid` / `wifi_password`：联网恢复、在线识别、在线 VAD、查天气/播歌等场景需要。
- `enable_hotspot_control`：是否允许脚本接管本机热点开关。没有确认前保持 `false` 更安全。

断网/联网类场景要同时区分：热点是否真的关闭/恢复、设备是否重新在线、在线语音链路是否恢复。

### `timeouts`

```json
"timeouts": {
  "observe_ms": 15000,
  "recognition_timeout_s": 15,
  "half_duplex_timeout_s": 15,
  "full_duplex_timeout_s": 60,
  "timing_guard_ms": 1200
}
```

- `observe_ms`：每次播放或动作后抓取串口证据的窗口。
- `recognition_timeout_s`：识别模式超时口径。识别模式下再次唤醒、one-shot、超时后行为都依赖这个参数。
- `half_duplex_timeout_s`：半双工识别窗口或超时口径。
- `full_duplex_timeout_s`：全双工识别窗口或超时口径。
- `timing_guard_ms`：临界时序保护时间。靠近唤醒播报、自播结束、识别超时边界时，建议预留保护窗口；落在保护窗口内的结果应标记 `TIMING_AMBIGUOUS` 或 `BLOCKED`，不要直接判固件 FAIL。

### `limits`

```json
"limits": {
  "command_limit": 20,
  "stress_rounds": 100
}
```

- `command_limit`：命令词 smoke 默认跑多少条。
- `stress_rounds`：压测默认轮次。长时间压测建议在 task 文件中单独覆盖，避免误触发。

### `paths`

```json
"paths": {
  "command_file": "doc/fa2命令词.txt",
  "debug_root": "satellite/cucumber-agent-testing/debug",
  "result_root": "result"
}
```

- `command_file`：默认命令词文件。命令词识别、打断候选、离线长播报测量可能复用。
- `debug_root`：Cucumber 调试输出根目录。不要提交 Git。
- `result_root`：底层 Polaris 工具的结果目录。不要提交 Git。

## 任务配置 `tasks/*.json`

任务配置负责回答“这次我要测什么”：

```json
{
  "schema": "polaris.cucumber.task.v1",
  "task_id": "basic_command_smoke",
  "scenario": { "tag": "basic_command_recognition" },
  "runner": { "mode": "dry-run" },
  "environment": { "env_file": "config/polaris_env.json" },
  "inputs": {
    "command_file": "doc/fa2命令词.txt",
    "command_limit": 20
  },
  "execution": {
    "observe_ms": 15000,
    "manage_session": true,
    "allow_side_effects": false
  }
}
```

字段说明：

| 字段 | 含义 |
| --- | --- |
| `task_id` | 任务唯一名称，用于报告和沟通。 |
| `scenario.tag` | 触发哪个 Cucumber 场景，必须已在 feature/mapping/registry 中沉淀。 |
| `runner.mode` | `plan-only`、`dry-run` 或 `execute`。建议示例文件默认 `dry-run`。 |
| `runner.compile_first` | 是否先用 step/action/assertion registry 离线编译 feature。新 DSL/新步骤建议设为 `true`。 |
| `environment.env_file` | 使用哪份本机环境配置。默认 `config/polaris_env.json`。 |
| `inputs.command_file` | 命令词/语料文件。命令词、自由说、打断候选相关场景常用。 |
| `inputs.command_limit` | 本次最多跑多少条语料。 |
| `execution.observe_ms` | 每轮观察窗口。 |
| `execution.manage_session` | execute 时是否自动启动/停止串口 logger。新人建议 `true`。 |
| `execution.allow_side_effects` | 是否允许真机副作用。示例建议保持 `false`，执行时通过命令行显式加 `--allow-side-effects`。 |

命令行参数优先级高于任务文件，任务文件优先级高于 `config/polaris_env.json`。

## 判断结果对不对

执行后优先看 `bdd_run_report.md`：

- `PASS`：前置、动作、证据和断言闭环满足当前 oracle。
- `FAIL`：证据充分且归因到固件/设备行为不符合预期。
- `BLOCKED`：前置未满足，例如串口不可用、设备未联网、声卡不存在、打断前置自播不可用。
- `TIMING_AMBIGUOUS`：动作落在超时、自播结束、唤醒播报等临界窗口，当前证据不能稳定归因。
- `REQUIREMENT_REVIEW`：需求或 oracle 不清楚，例如自由说文本容差、播报中是否允许识别没有明确口径。

原则：没有证据不要硬判固件失败；先区分环境、设备、脚本、需求，再判断固件。
