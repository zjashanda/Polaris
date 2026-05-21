# Polaris

## Cucumber Agent Testing 快速入口

Polaris 当前新增了一套可开源上手的 BDD + Agent Testing 入口，位置在：

```text
satellite/cucumber-agent-testing/
```

首次 clone 后，新用户只需要复制并编辑根目录这一个本机配置文件：

```powershell
Copy-Item polaris.local.example.json polaris.local.json
notepad polaris.local.json
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json
```

真机执行时再显式允许副作用：

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode execute --allow-side-effects --manage-session
```

默认配置查找顺序：命令行 `--env-file` > 任务文件 `environment.env_file` > 根目录 `polaris.local.json` > 旧版 `config/polaris_env.json`。

详细说明见：

- `polaris.local.example.json`
- `satellite/cucumber-agent-testing/README.md`
- `satellite/cucumber-agent-testing/docs/configuration.md`
- `satellite/cucumber-agent-testing/tasks/examples/`

## 新项目必须先配什么

以后按项目在 `polaris.local.json` 里分类维护，不再让新人到 `config/` 里找配置。只改这些基础字段：

- `active_project`：选择当前项目，例如 `cskwb01` 或 `venusws63`。
- `projects.<项目>.serial`：串口、波特率、拓扑；WS63 的 `cp` 必须留空。
- `common.audio.default_playback_device_key`：声卡 key；项目/设备没有单独配置或留空时，脚本会走电脑默认播放声卡。
- `common.device.wake_word/wakeup_id`：唤醒词和唤醒 ID。
- `projects.<项目>.network`：Wi-Fi/热点配置；不需要联网编排时可留空或关闭。
- `projects.<项目>.cloud`：API 环境；执行云控前设备端环境必须和这里一致。
- `projects.<项目>.serial.control_preconditions`：声卡播放成功但设备无唤醒时的控制口前置，例如 `uut-pa.on`、`pa-enable.set 0 17 0 1`。

WB01 与 WS63 当前模板已经放在同一个根配置里：

- WB01/CSK：`projects.cskwb01`，需要 `ap/cp/asr/control` 4 个串口；本次已沉淀 PA/声卡链路恢复前置。
- WS63/AP+WiFi：`projects.venusws63`，需要 `ap/upper/control` 3 个串口，`cp` 留空，PA 前置命令走控制口。

`device.iot_id` / `cloud.device_id` 默认可以留空；只有执行 API/云控且脚本无法通过 `deviceinfo` 自动读取时，才需要手动填写。

声卡建议优先填写稳定 key，便于多声卡机器复现；如果某个项目或设备没有单独声卡配置，就把 `audio.default_playback_device_key` 留空或删除，`listenai-play` 会使用电脑当前默认输出设备。此时若播放命令成功但设备无唤醒，要额外确认 Windows 默认声卡是否确实接到 DUT。

## config/ 目录现在怎么定位

`config/` 里不是每个文件都要手改，之前历史沉淀把本机配置、运行状态、报告和参考资料混在了一起，所以看起来乱。现在约定如下：

- 用户入口：只改根目录 `polaris.local.json`。
- 旧版兼容：`config/polaris_env.json`、`config/polaris_local_ports.json` 只给老脚本兜底，不作为新人入口。
- 运行状态/报告：`polaris_doc_case_status.json`、`polaris_auto_executable_case_detail.md`、`polaris_fail_case_detail.md`、`polaris_failure_diagnosis.json` 等是生成或同步结果。
- 参考资料：`polaris_command_catalog.*`、`polaris_validation_reference.md`、`polaris_model_applicability.md` 等是知识库/报告，不是串口配置。

后续我不会直接删除这些文件，先把入口收敛清楚；等确认没有老脚本依赖后，再把历史/生成类文件迁到更明确的目录。

## API 环境注意事项

调用云端/API 前，设备端 CSK/AP 必须先切到和 API 一致的调试环境，否则容易出现接口成功但设备不生效、connector/channel 异常或控制错环境。

- UAT：在 CSK/AP 串口执行 `flash.set.int env@1`，再执行 `reboot`。
- SIT：在 CSK/AP 串口执行 `flash.set.int env@2`，再执行 `reboot`。
- PRO：在 CSK/AP 串口执行 `flash.set.int env@0`，再执行 `reboot`。
- `polaris.local.json` 中 `cloud.api_environment` 必须和设备端 `cloud.device_env` 一致，例如都为 `uat` 或都为 `sit`。
- 重启后先确认设备在线，再执行 `set-volume`、`set-full-duplex`、`set-night-mode` 等 API 类用例。

## 原有 skill 说明

用于在本仓库中验证 Polaris 系列美的空调语音设备，覆盖串口日志、COM15 电源控制、热点编排、短语探测、已验证正常的云端控制、文档用例执行与报告同步。

## 目录结构

根目录只保留启动必须看的入口文件和稳定模块；历史运行证据已归档到 `_runtime/archive/<时间戳>/`。

```text
README.md                         # 新人入口
SKILL.md                          # Codex skill 规则与能力说明
polaris.local.example.json         # 本机配置模板，可提交
polaris.local.json                 # 本机真实配置，已忽略提交
config/                            # 旧版兼容配置 + 状态/报告，不作为新人入口
doc/                               # 产品需求、词表、测试表格等原始资料
docs/skill/                        # 使用说明、环境迁移说明
references/                        # 验证规则、功能池、项目 profile
tools/                             # 底层串口/音频/云控/报告脚本
satellite/cucumber-agent-testing/  # Cucumber/BDD 测试框架
spec/                              # 旧版离线 smoke spec
result/cache/outputs/              # 运行输出根目录，默认只保留 .gitkeep
_runtime/archive/                  # 整理迁出的历史运行文件，不提交
```

原则：新用户先看 `README.md`、`polaris.local.example.json`、`satellite/cucumber-agent-testing/README.md`；不要直接改 `config/` 里的状态报告。

## Install the skill

Copy this folder into:

```text
~/.codex/skills/polaris-device-validation
```

Then restart Codex.

## Usage and workflow

本文档统一使用 UTF-8 编码，作为当前仓库根目录下的本地 skill 使用。后续迁移到新机器时，保留 `README.md`、`SKILL.md`、`polaris.local.example.json` 和 `docs/skill/` 下说明文档即可。

## 这个 skill 当前保留什么能力

只保留已经验证为“能正常控制”或“能稳定执行”的能力：

- 基础设施与观测
  - `COM12 / COM13 / COM14` 持续日志采集
  - 串口命令下发与回显确认
  - `COM15` 控制的 `asr` / `csk` 断电重启
  - 设备状态快照、差异比对、短语探测
  - Windows 热点状态查询、热点重启、`vir_ssid/vir_pwd` 下发后重启验证
- 已验证正常的云端控制
  - `probe-device`
  - `set-full-duplex`
  - `set-volume`
  - `set-multi-wakeup`
  - `set-accent`
  - `set-wakeup-threshold`
  - `set-mic`
  - `set-night-mode`
  - `set-wakeup-audio-upload`
  - `proactive-interaction`
- 已验证可正常执行的自动化入口
  - 单条文档用例执行
  - suite 批量执行
  - audit / status sync / case table / fail detail / auto case detail 导出

## 当前不放入主 skill 的功能

以下能力现在不作为“正常可控”能力写入主技能：

- `set-character-value`
  - 当前 DUT 返回业务 `code=501`，提示“未找到对应的音色”。
- `set-log`
  - 接口可调用，但请求 `level=2` 后本地读回仍是 `4/4`，目前不作为稳定可控能力。
- 自定义唤醒词切换
  - 云端下发成功，但 `客厅空调` 在当前 CA3X 设备上仍无法形成稳定本地唤醒；仅默认唤醒词恢复路径已验证正常。

## 建议使用顺序

1. 先读 `docs/skill/environment-and-migration.md`
   - 确认主机、串口、播放设备、热点、云环境是否满足要求。
2. 再读 `docs/skill/capabilities-and-usage.md`
   - 按“基础设施 → 云控 → 用例 → 报告”的顺序选择入口。
3. 真正执行前，至少确认以下 4 件事：
   - `.current_result_dir` 指向当前 session
   - `result/<session>/logs/live/heartbeat.json` 心跳正常
   - `deviceinfo/state_probe` 能拿到 `iot_id/mac/wakeup_id`
   - 默认播放设备能让 DUT 真正听到音频

## 本地串口配置

现在以根目录 `polaris.local.json` 为主配置入口。工具命令未显式指定串口时，优先读取 `polaris.local.json` 当前 `active_project` 的串口；旧版 `config/polaris_local_ports.json` 只作为兼容缓存。

当前内置项目：

- `cskwb01`：`ap/cp/asr/control` 4 个串口，默认 `COM14/COM12/COM13/COM15`。
- `venusws63`：`ap/upper/control` 3 个串口，默认 `COM14/COM13/COM15`，`cp` 留空。

常用示例：

```powershell
notepad polaris.local.json
python tools/core/polaris_config.py show
python tools/core/polaris_config.py set --role control --port COM15
python tools/device/polaris_serial_harness.py send --role ap --command version
python tools/device/polaris_serial_harness.py send --role asr --command "listen version"
python tools/device/polaris_power_control.py cycle --target asr
```

兼容说明：旧工具中仍写死的 `COM12/COM13/COM14` 会在运行时按角色映射到本地配置里的 `cp/asr/ap` 端口。WS63 这类无 CP 项目会跳过空的 `cp` 端口。

注意：串口 logger 启动时读取一次配置；如果运行中修改了 COM 映射，需要重启 logger 才能让采集线程切到新端口。

## 典型工作流

### 1. 设备接入 / 冒烟

优先使用这些工具：

- `tools/device/polaris_serial_harness.py`
- `tools/probe/polaris_state_probe.py`
- `tools/probe/polaris_phrase_probe.py`
- `tools/device/polaris_power_control.py`
- `tools/device/polaris_network_orchestrator.py`

适用于：新设备接入、怀疑音频链路异常、怀疑网络链路异常、串口拓扑变化后的首次校验。

### 2. 云端功能控制验证

优先使用：`tools/cloud/polaris_app_control.py`

当前建议保留的云控验证项：

- 自然对话开关
- 音量控制
- 多设备唤醒开关
- 方言开关
- 唤醒阈值
- Mic 开关
- 夜间模式
- 唤醒音频上传开关
- 主动交互

### 3. 文档用例与结果同步

优先使用这些工具：

- `tools/execution/polaris_doc_case_runner.py`
- `tools/execution/polaris_batch_runner.py`
- `tools/reporting/polaris_doc_case_audit.py`
- `tools/reporting/polaris_status_sync.py`
- `tools/reporting/polaris_export_case_table.py`
- `tools/reporting/export_fail_case_detail_md.py`
- `tools/reporting/export_auto_case_detail_md.py`

## 按需查看的参考文档

- `docs/skill/capabilities-and-usage.md`
  - 当前保留能力
  - 常用命令
  - 本轮已验证结果
  - 当前边界与排除项
- `docs/skill/environment-and-migration.md`
  - 环境要求
  - 新设备 bootstrap
  - 换机迁移前要改什么

## 当前已验证基线

本 skill 以 `2026-04-23` 这一轮巡检结果为当前基线：

- live session：`result/20260423111046`
- 当前最终回读基线：
  - `inter_mode=1`
  - `threshold=75`
  - `wakeupid=1`
  - `volume=20`
  - `log_lev=4`
  - `vir_ssid=pcwifi24`
- 最新状态汇总：`90 executed / 81 PASS / 3 FAIL / 6 BLOCKED / 625 SKIP`

## 使用边界

- 本 skill 默认面向当前 Polaris 串口拓扑与日志语义；如果新设备拓扑变了，先改环境再跑功能。
- “接口可调用”不等于“设备功能完全支持”；当前文档已只保留确认正常的能力，其余项目统一放到边界说明。
- 如果后续再次验证通过 `set-log`、自定义唤醒词或音色切换，再把它们补回主技能即可。

## 模块化验证池落地规则

后续处理新功能、需求变更、断言收敛或正式全集前，优先读取：

1. `references/modular-validation-workflow.md`
2. `references/validation-pool/INDEX.md`
3. `references/validation-pool/schema.md`
4. `references/evidence-rules.md`
5. 当前命中的 `references/validation-pool/*.md`

新增功能时，先把需求拆成“功能意图 + 触发 + 前置状态 + 期望输出 + 状态变化 + 证据来源”，再匹配验证池模块。不得直接把历史 PASS/FAIL 或某一轮日志当成新功能默认断言。

统一 suite 骨架入口：

```powershell
python tools/suite/run_polaris_formal_suite.py --tag plan_only
```

该命令默认只做 plan-only：分类、门禁文件检查和报告生成，不占用串口、不调用云端、不播放音频。确认执行范围后，才使用 `--execute` 运行 profile 中的现有工具阶段。
