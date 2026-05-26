# Polaris Voice Validation Skill

Polaris 是一个面向嵌入式语音设备的本地真机验证 skill。当前仓库已经切换到新的 **Cucumber/BDD + Event Runtime** 方案：用 Cucumber 描述测试意图，用固定 runner 执行动作，用 Event Runtime 把串口、声卡、云控和执行产物统一转换成事件，再由确定性的断言逻辑判断 PASS/FAIL/BLOCKED。

本仓库不要求每次执行时联网或依赖大模型生成脚本。新用例只要进入已有的 step/action/assertion registry，后续就可以脱离大模型稳定执行。

## 1. 适合解决什么问题

- 语音唤醒：首次唤醒、识别模式下唤醒、连续唤醒、唤醒率压测。
- 语音识别：基础命令词、需求命令词、自由说小样本、one-shot 间隔矩阵。
- 交互模式：半双工识别、全双工识别、识别超时、临界超时保护。
- 打断验证：设备自播/TTS/媒体播放过程中进行唤醒打断或命令打断。
- 在线交互压测：基础命令、音乐、相声、新闻、问答、组合场景随机压测。
- 异常归因：重启、crash、看门狗、误唤醒、误识别、额外识别结果记录。
- 项目化复用：同一套框架支持 `cskwb01`、`venusws63` 等不同串口拓扑。

## 2. 当前目录结构

```text
Polaris/
  README.md                         # 当前文档，新人入口
  SKILL.md                          # Codex skill 说明，描述必须遵守的工作流
  AGENTS.md                         # 本仓库 agent 启动规则：每次先读/写 plan.md
  polaris.local.example.json         # 本机配置模板，提交到 git
  polaris.local.json                 # 本机真实配置，不提交 git
  plan.md                            # 本地执行计划和进度，不提交 git
  .gitignore                         # 忽略本地配置、运行产物、旧归档
  docs/                              # 文档、需求、命令词、表格、学习入口
    fa2命令词.txt                    # 默认命令词文件
    requirements/                    # 需求文档、词表、自由说资料
    cases/                           # 用例表格资料
    api/                             # 云控/API 相关辅助代码
    intake/                          # 新项目/新功能资料导入入口
    knowledge/                       # 学习后的结构化知识沉淀
    skill/                           # 当前 skill 设计、能力、落地说明
  satellite/cucumber-agent-testing/  # Cucumber/BDD + Event Runtime 主体
    features/                        # Cucumber feature 用例
    references/                      # step/action/assertion mapping、策略池、能力沉淀
    tasks/                           # 可直接运行的任务 JSON
    configs/                         # 旧兼容示例配置；根目录配置优先
    scripts/                         # run_task/run_cucumber/replay/压测入口脚本
    runtime/                         # Event Runtime 内核、插件、解析器、断言、replay
    debug/                           # 运行产物目录，不提交 git
  tools/                             # 最小工具层：串口、声卡、云控、case runner 支撑
  oldTime/                           # 旧方案完整归档，不作为当前执行入口
```

> 当前只保留一个 `docs/` 目录；旧 `doc/`、`config/`、`result/`、`cache/`、`outputs/`、`_runtime/`、`spec/`、`references/` 等混杂入口不再作为新方案入口。

## 3. 框架是怎么工作的

```text
Cucumber Feature / Task JSON
        ↓
run_task.py 读取任务和 polaris.local.json
        ↓
compile_feature.py 可选离线编译 step/action/assertion plan
        ↓
run_cucumber.py 调用固定动作：串口、声卡、云控、日志采集
        ↓
运行产物写入 satellite/cucumber-agent-testing/debug/
        ↓
runtime_replay.py / Event Runtime 解析产物为 ValidationEvent
        ↓
Timeline + StateMachine + Assertion Engine
        ↓
输出 replay_package.json、assertions.json、runtime_replay_report.md
```

关键原则：

- Cucumber 只表达“要验证什么”，不把复杂判断写进自然语言。
- runner 只执行已注册的动作，不临时让大模型生成脚本。
- Runtime 只根据事件和固定断言判断结果，不让大模型决定 PASS/FAIL。
- 所有 wake/asr/media/network/reboot 等能力逐步走 plugin 化，避免 runtime 变成巨型脚本。
- 断言用 monotonic timeline 做时序判断，wall clock 只用于报告展示。

## 4. 首次使用步骤

### 4.1 克隆后准备本机配置

```powershell
Copy-Item polaris.local.example.json polaris.local.json
notepad polaris.local.json
```

只需要优先改这些字段：

| 配置 | 说明 |
|---|---|
| `active_project` | 当前连接的项目，例如 `cskwb01` 或 `venusws63`。 |
| `common.audio.default_playback_device_key` | 指定声卡 key；留空则使用电脑默认声卡。 |
| `common.device.wake_word` | 当前唤醒词，例如 `小美小美`。 |
| `common.network.wifi_ssid/password` | 当前测试 Wi-Fi 或热点信息。 |
| `projects.<项目>.serial.ports` | AP/CP/ASR/上位/控制口 COM 口。 |
| `projects.<项目>.cloud.api_environment` | 云控环境，常见为 `uat` 或 `sit`。 |
| `projects.<项目>.cloud.device_env_command` | 设备切换环境命令，必须发到设备支持的串口。 |

### 4.2 WB01 项目最小配置

`cskwb01` 通常是 AP + CP + ASR/WB01 + 控制口四串口：

```json
{
  "active_project": "cskwb01",
  "projects": {
    "cskwb01": {
      "serial": {
        "ports": {
          "ap": "COM14",
          "cp": "COM12",
          "asr": "COM13",
          "control": "COM15"
        }
      },
      "cloud": {
        "api_environment": "sit",
        "device_env": "sit"
      }
    }
  }
}
```

注意：如果声卡播放成功但设备无唤醒证据，优先在 `control` 串口执行 PA 前置：

```text
uut-pa.on
pa-enable.set 0 17 0 1
```

这两个命令必须发到控制口，不要发到 AP/CP/ASR 口。

### 4.3 WS63 项目最小配置

`venusws63` 通常是 AP + 上位/WiFi + 控制口三串口，没有独立 CP：

```json
{
  "active_project": "venusws63",
  "projects": {
    "venusws63": {
      "serial": {
        "ports": {
          "ap": "COM16",
          "upper": "COM20",
          "asr": "COM20",
          "cp": "",
          "control": "COM17"
        }
      },
      "cloud": {
        "api_environment": "uat",
        "device_env": "uat"
      }
    }
  }
}
```

WS63 没有 CP 时，`cp` 必须留空；断言会根据 capability 自动降级，不会强行要求 CP 日志。

## 5. 常用执行方式

### 5.1 只打印将要执行的命令

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --print-command
```

### 5.2 dry-run 检查流程，不碰真机

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode dry-run
```

### 5.3 真机执行

真机执行会占用串口、声卡、热点或云控，所以必须显式允许副作用：

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode execute --allow-side-effects --manage-session
```

### 5.4 先编译 Cucumber 再执行

用于验证 feature 是否能通过 registry 固化执行，不依赖临时脚本生成：

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --compile-first --mode execute --allow-side-effects --manage-session
```

### 5.5 在线混合压测

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\online_mixed_stress.example.json --mode execute --allow-side-effects
```

WS63 示例：

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\online_mixed_stress.ws63.example.json --mode execute --allow-side-effects
```

### 5.6 对已有日志做 replay 和断言

```powershell
python satellite\cucumber-agent-testing\scripts\runtime_replay.py --input-dir satellite\cucumber-agent-testing\debug\runs\<某次运行目录> --profile first_wake --env-file polaris.local.json
```

replay 输出默认在：

```text
satellite/cucumber-agent-testing/debug/runtime_replay/<时间戳>_<profile>/
```

重点看：

```text
assertions.json              # 机器可读断言结果
runtime_replay_report.md     # 人可读报告
events.json                  # 标准化事件
timeline.json                # monotonic 时间线
runtime_state.json           # 状态机结果
replay_package.json          # 完整 replay 包
```

### 5.7 优化执行封装：执行记录、重试和资源预检

`run_optimized_task.py` 是当前按两份 Runtime 优化方案新增的第一层工程化入口。它不会替换 `run_task.py`，而是在外层增加：

- 资源/约束 preflight：串口、声卡、网络、云环境、副作用策略、项目拓扑。
- 执行前后状态快照：`state/before.json`、`state/after.json`。
- 状态差异：`state_diff.json`。
- 尝试记录：`attempts.jsonl` 和每次 attempt 的 `stdout.log`。
- 汇总记录：`execution_record.json`，包含 `PASS`、`STABLE_FAIL`、`FLAKY_PASS`、`ENV_RELATED` 等分类。

只做预检，不碰真机：

```powershell
python satellite\cucumber-agent-testing\scripts\run_optimized_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode dry-run --precheck-only
```

打印将要执行的底层命令：

```powershell
python satellite\cucumber-agent-testing\scripts\run_optimized_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode dry-run --print-command
```

真机执行并允许一次失败重试：

```powershell
python satellite\cucumber-agent-testing\scripts\run_optimized_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode execute --allow-side-effects --manage-session --runtime-strict --max-retries 1
```

默认输出目录：

```text
satellite/cucumber-agent-testing/debug/optimized_runs/<时间戳>_<task_id>/
```

重点看：

```text
preflight.json
command.json
execution_record.json
attempts.jsonl
state/before.json
state/after.json
state_diff.json
attempt_01/stdout.log
```

## 6. Task JSON 怎么写

推荐先复制 `satellite/cucumber-agent-testing/tasks/examples/` 下的模板。

最小结构如下：

```json
{
  "schema": "polaris.task.v1",
  "runner": {
    "mode": "dry-run",
    "compile_first": true,
    "feature": "satellite/cucumber-agent-testing/features/polaris_voice_core.feature",
    "mapping": "satellite/cucumber-agent-testing/references/voice_core_mapping.json"
  },
  "scenario": {
    "tag": "first_wake"
  },
  "environment": {
    "env_file": "polaris.local.json"
  },
  "inputs": {
    "command_file": "docs/fa2命令词.txt"
  },
  "execution": {
    "observe_ms": 15000,
    "manage_session": true,
    "allow_side_effects": false
  }
}
```

字段含义：

| 字段 | 用途 |
|---|---|
| `runner.mode` | `plan-only`、`dry-run`、`execute`。 |
| `runner.compile_first` | 是否先通过 registry 编译成确定性执行计划。 |
| `scenario.tag` | 要执行的 Cucumber 场景 tag，例如 `first_wake`。 |
| `environment.env_file` | 默认使用根目录 `polaris.local.json`。 |
| `inputs.command_file` | 命令词文件，默认 `docs/fa2命令词.txt`。 |
| `execution.allow_side_effects` | 真机执行必须为 `true` 或命令行传 `--allow-side-effects`。 |
| `execution.manage_session` | 是否自动建立/关闭串口日志会话。 |

## 7. 当前已注册测试项

这些 tag 可以通过 task 或 `run_cucumber.py --tag <tag>` 触发：

```text
first_wake
recognition_mode_wake
half_duplex_recognition
full_duplex_recognition
basic_command_recognition
requirement_command_smoke
requirement_free_speech_smoke
interrupt_prerequisite_measurement
wake_interrupt
command_interrupt
network_recovery_basic
offline_oneshot_matrix
online_oneshot_matrix
false_wake_quiet_basic
wake_latency_smoke
continuous_wake_smoke
random_interval_wake_smoke
online_vad_special_smoke
attribution_validator_smoke
false_wake_human_speech_smoke
false_wake_white_noise_smoke
```

## 8. 断言和归因口径

Runtime 会先把证据转换为标准事件，例如：

```text
AudioInjected
WakeDetected
ASRDetected
CommandDetected
TTSStarted
MediaStarted
MediaCompleted
NetworkLost
NetworkRecovered
RebootDetected
CrashDetected
```

然后按 profile 做断言：

| 结果 | 含义 |
|---|---|
| `PASS` | 证据满足功能意图，时序和禁止行为也满足。 |
| `FAIL` | 有足够证据证明设备行为不符合预期。 |
| `BLOCKED` | 环境、串口、声卡、云控、日志缺失等导致无法判断。 |
| `PASS_WITH_SKIPPED_TIMING` | 主功能通过，但部分时序证据不足，只能跳过时序断言。 |
| `TIMING_AMBIGUOUS` | 临界超时或播报占用导致时序不可稳定归因，需要复核。 |

首唤醒时序的锚点策略已经固化到 `runtime/assertion_engine.py`：

- 优先使用真实 `AudioInjected` 到首个物理唤醒簇的时差。
- 如果主机播放进程明显长于 wav 时长，说明 `AudioInjected` 更像“播放进程启动”而不是“声波到达设备”；此时优先用 `AudioCompleted - audio_duration_ms` 估算有效波形起点。
- 如果仍无法稳定估算，但唤醒落在播放窗口内，结果标记为 `TIMING_AMBIGUOUS`，不直接归因为固件超时。
- WB01 要求 CP/AP/ASR 唤醒闭环；WS63 没有 CP 时按 AP/ASR 闭环断言。

归因原则：

- 没有发音频却出现 wake/ASR/command，要记录为疑似误唤醒或误识别。
- 有声卡播放但无任何设备侧证据，优先判为环境/设备链路阻塞，而不是直接判固件失败。
- 有 AP/ASR 识别但无预期响应，需要结合媒体/TTS/云控事件判断是识别问题、执行问题还是云端问题。
- 出现 `RebootDetected`、`CrashDetected`、watchdog、panic、hardfault 等标记，要单独进入健康度和稳定性统计。

## 9. Runtime Phase 2 最小落地：执行记录、资源和约束

当前已经新增 Phase 2 的最小闭环，不做复杂平台化，只先保证本地真机任务更可控：

```text
runtime/
  resource_runtime.py       # ResourceClaim/ResourceSnapshot，检查串口/声卡/网络/云控/电源资源冲突
  constraint_engine.py      # task/env preflight，检查副作用、串口拓扑、在线网络、云环境、打断 guard
scripts/
  run_optimized_task.py     # 包装 run_task.py，产出 execution_record、attempts、state snapshot
references/optimization/
  execution_record.schema.json
  retry_policy.json
```

这一步的目标不是替代现有 Cucumber runner，而是给每次执行补上“可审计上下文”。后续做场景引擎、失败聚类、设备健康度时，都以 `execution_record.json` 为输入。

继续对齐两份优化方案后，当前还提供这些轻量入口：

```text
scripts/generate_scene.py           # strategy -> scene graph
scripts/run_scene.py                # scene graph -> run_optimized_task
scripts/analyze_execution_store.py  # execution_record -> failure fingerprint / health report
scripts/replay_vm.py                # replay package -> VM-lite snapshot/time travel
scripts/simulate_runtime.py         # Fake log -> replay smoke
scripts/run_assertion_dsl.py        # EXPECT/FORBID DSL-lite
scripts/inspect_device_adapters.py  # env -> adapter registry
scripts/build_capability_matrix.py  # env -> project capability matrix
scripts/build_event_graph.py        # timeline/run_dir -> causal event graph
scripts/run_state_assertion_dsl.py  # runtime_state -> state assertions
scripts/compile_validation_ir.py    # task + env -> Validation IR
scripts/build_analytics_trend.py    # execution_record history -> local trend report
docs/skill/runtime-implementation-matrix.md
```

本轮真机 smoke 已验证：

- WB01：`first_wake` 通过，managed session 使用 COM13/COM12/COM14，BDD 观察到 CP/AP/ASR 闭环，Runtime PASS。
- WS63：`first_wake` 通过，managed session 使用 COM20/COM16，BDD 观察到 AP/ASR 闭环，Runtime PASS。
- `run_optimized_task.py` 已修正聚合逻辑，会按 scenario/runtime 结果输出 `FAIL`、`BLOCKED`、`TIMING_AMBIGUOUS` 或 `PASS`，不会把 `status=DONE` 误当 PASS。
- Adapter/Capability/EventGraph/StateDSL/ValidationIR/AnalyticsTrend 已完成本地 MVP，WB01 与 WS63 都做了 smoke 验证；详细数字见 `docs/skill/runtime-implementation-matrix.md`。

## 10. Event Runtime Phase 1 结构

当前已开始按高级优化方案做 Phase 1：

```text
runtime/
  events.py                # ValidationEvent v1 schema，含 plugin、severity、tags、wall/monotonic 时间
  timeline.py              # monotonic timeline，断言使用相对单调时间
  state_machine.py         # 运行状态机
  assertion_engine.py      # 固化断言逻辑
  replay.py                # replay package 构建
  kernel/
    plugin.py              # RuntimePlugin、PluginManager、PluginContext
  plugins/
    wake.py                # 唤醒域插件
    asr.py                 # ASR/命令识别域插件
    media.py               # TTS/媒体/打断域插件
    network.py             # 网络域插件
    reboot.py              # 重启/crash 域插件
  parsers/
    serial_log_parser.py   # 串口/播放日志解析
    json_artifact_parser.py# 结构化产物解析
```

后续新功能不要直接塞进一个巨大的 runtime 文件里，优先按领域进入 plugin：wake、asr、media、network、reboot，必要时再新增 plugin。

## 11. 新项目/新功能怎么导入学习

如果后续有新项目说明、新功能需求、外部测试方案、类似 `voice-test-plan-designer` 的资料，统一放到：

```text
docs/intake/<project_id>/<YYYYMMDD_topic>/
  learning_manifest.json
  raw/
```

操作步骤：

1. 从 `docs/intake/templates/learning_manifest.template.json` 复制 `learning_manifest.json`。
2. 把原始资料放入 `raw/`，例如 PDF、Excel、Markdown、日志、旧 skill。
3. 在 manifest 里写清楚本次目标：项目 profile、功能测试策略、Cucumber 用例、断言逻辑、压测策略或缺口分析。
4. 我学习后会把结构化理解沉淀到 `docs/knowledge/<project_id>/`。
5. 资料足够时，再把可执行能力写入 `features/`、`references/`、`tasks/`、`runtime/plugins/` 或 `tools/`。

资料不足时，只输出缺口清单，不伪造可执行能力。

## 12. 哪些文件不要提交

这些只属于本机或运行产物：

```text
polaris.local.json
plan.md
oldTime/
satellite/cucumber-agent-testing/debug/
result/
cache/
outputs/
_runtime/
__pycache__/
*.log
*.tmp
```

## 13. 常见问题

### 声卡播放不生效怎么办

- 如果项目/设备配置里没有填写声卡 key，默认使用电脑默认声卡。
- 多声卡环境建议用 `laid` 或 `listenai-play` 扫描稳定 key 后填入 `common.audio.default_playback_device_key`。
- 如果声卡播放成功但设备无唤醒证据，WB01/WS63 可尝试在控制口执行：`uut-pa.on`、`pa-enable.set 0 17 0 1`。

### 云控/API 设置不生效怎么办

- 先确认 `polaris.local.json` 的 `cloud.api_environment` 是 `uat` 还是 `sit`。
- 再确认设备端 CSK/AP 已切到同一环境。
- 环境切换命令通常在 `projects.<项目>.cloud.device_env_command` 中配置，切换后可能需要重启。

### 新写 Cucumber 用例为什么还要 registry

Cucumber 是自然语言入口，但真正执行要靠固定的 step/action/assertion registry。这样做的目的是：

- 用例文本可以变，但执行动作和断言逻辑稳定。
- 执行时不依赖大模型、不依赖网络动态改脚本。
- 同一功能更换唤醒词、超时时间、声卡、串口后仍能复用。

### 老方案还能用吗

旧方案已归档到 `oldTime/`，只作为历史参考，不作为当前执行入口。当前维护和新增能力都应进入新方案目录。
