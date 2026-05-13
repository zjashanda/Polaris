# polaris-device-validation

用于在本仓库中验证 Polaris 系列美的空调语音设备，覆盖串口日志、COM15 电源控制、热点编排、短语探测、已验证正常的云端控制、文档用例执行与报告同步。

## Skill layout

- `.gitignore`
- `capabilities-and-usage.md`
- `config/polaris_auto_executable_case_detail.md`
- `config/polaris_command_catalog.json`
- `config/polaris_command_catalog.md`
- `config/polaris_command_word_report.md`
- `config/polaris_doc_case_status.json`
- `config/polaris_env.json`
- `config/polaris_fail_case_detail.md`
- `config/polaris_failure_diagnosis.json`
- `config/polaris_learncase_deep_relation.md`
- `config/polaris_learncase_feedback.md`
- `config/polaris_local_ports.json`
- `config/polaris_model_applicability.md`
- `config/polaris_validation_reference.md`
- `doc/__init__.py`
- `doc/api/__init__.py`
- `doc/api/common_request.py`
- `doc/cases/20260130141231_lyzuo-美的空调-功能测试用例（全）.xlsx`
- `doc/cases/FA2新增命令词测试用例.xlsx`
- `doc/fa2命令词.txt`
- `doc/reference/tone.h`
- `doc/reference/美的空调相关特殊操作说明文档.docx`
- `doc/reference/自动化测试优化方案.pdf`
- `doc/requirements/20241128105427_功能测试用例.xlsx`
- `doc/requirements/美的FA2挂机需求文档_20250818.xlsx`
- `doc/requirements/美的FA2柜机需求文档_20250818.xlsx`
- `environment-and-migration.md`
- `references/evidence-rules.md`
- `references/fullflow-validation-method.md`
- `references/modular-validation-workflow.md`
- `references/project-profiles/polaris_midea_ac.json`
- `references/validation-pool/ac-control-command.md`
- `references/validation-pool/cloud-control-settings.md`
- `references/validation-pool/duplex-mode.md`
- `references/validation-pool/fault-convergence.md`
- `references/validation-pool/INDEX.md`
- `references/validation-pool/network-online.md`
- `references/validation-pool/night-mode.md`
- `references/validation-pool/online-offline-asr.md`
- `references/validation-pool/schema.md`
- `references/validation-pool/volume-level.md`
- `references/validation-pool/wake-session.md`
- `SKILL.md`
- `spec/cases/offline_oneshot_open_ac_fast_gap.yaml`
- `spec/cases/offline_wakeup.yaml`
- `spec/cases/offline_wakeup_open_ac.yaml`
- `spec/suites/offline_smoke.yaml`
- `tools/__init__.py`
- `tools/audio/__init__.py`
- `tools/audio/polaris_audio_builder.py`
- `tools/audio/tts_sync_legacy/run.bat`
- `tools/audio/tts_sync_legacy/tts.txt`
- `tools/audio/tts_sync_legacy/tts_synthesis.py`
- `tools/cloud/__init__.py`
- `tools/cloud/polaris_app_control.py`
- `tools/core/__init__.py`
- `tools/core/polaris_config.py`
- `tools/core/polaris_runtime.py`
- `tools/device/__init__.py`
- `tools/device/polaris_network_orchestrator.py`
- `tools/device/polaris_power_control.py`
- `tools/device/polaris_serial_harness.py`
- `tools/execution/__init__.py`
- `tools/execution/polaris_batch_runner.py`
- `tools/execution/polaris_case_runner.py`
- `tools/execution/polaris_doc_case_batch_runner.py`
- `tools/execution/polaris_doc_case_runner.py`
- `tools/execution/polaris_followup_queue.py`
- `tools/library/__init__.py`
- `tools/library/polaris_doc_case_lib.py`
- `tools/pool/polaris_validation_pool.py`
- `tools/probe/__init__.py`
- `tools/probe/polaris_phrase_probe.py`
- `tools/probe/polaris_state_probe.py`
- `tools/reporting/__init__.py`
- `tools/reporting/build_auto_executable_cases_xlsx.mjs`
- `tools/reporting/export_auto_case_detail_md.py`
- `tools/reporting/export_fail_case_detail_md.py`
- `tools/reporting/polaris_doc_case_audit.py`
- `tools/reporting/polaris_export_case_table.py`
- `tools/reporting/polaris_refresh_failure_diagnosis.py`
- `tools/reporting/polaris_status_sync.py`
- `tools/suite/run_polaris_formal_suite.py`
- `tools/validation/__init__.py`
- `tools/validation/polaris_ac_control_command_probe.py`
- `tools/validation/polaris_command_validator.py`
- `tools/validation/polaris_fa2_command_batch.py`
- `tools/validation/polaris_workbook_voice_recognition_batch.py`

## Install the skill

Copy this folder into:

```text
~/.codex/skills/polaris-device-validation
```

Then restart Codex.

## Usage and workflow

本文档统一使用 UTF-8 编码，作为当前仓库根目录下的本地 skill 使用。后续迁移到新机器时，直接复制根目录这 3 份文档即可，不需要安装到 `.codex/skills`。

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

1. 先读 `environment-and-migration.md`
   - 确认主机、串口、播放设备、热点、云环境是否满足要求。
2. 再读 `capabilities-and-usage.md`
   - 按“基础设施 → 云控 → 用例 → 报告”的顺序选择入口。
3. 真正执行前，至少确认以下 4 件事：
   - `.current_result_dir` 指向当前 session
   - `result/<session>/logs/live/heartbeat.json` 心跳正常
   - `deviceinfo/state_probe` 能拿到 `iot_id/mac/wakeup_id`
   - 默认播放设备能让 DUT 真正听到音频

## 本地串口配置

当前本机串口映射写入 `config/polaris_local_ports.json`。工具命令未显式指定串口时，默认读取该配置；显式指定串口时，会同步对应角色到该配置文件。

当前角色：

- `ap / cskap`：`COM14`
- `cp / cskcp`：`COM12`
- `asr`：`COM13`
- `control`：`COM15`

常用示例：

```powershell
python tools/core/polaris_config.py show
python tools/core/polaris_config.py set --role control --port COM15
python tools/device/polaris_serial_harness.py send --role ap --command version
python tools/device/polaris_serial_harness.py send --role asr --command "listen version"
python tools/device/polaris_power_control.py cycle --target asr
```

兼容说明：旧工具中仍写死的 `COM12/COM13/COM14` 会在运行时按角色映射到本地配置里的 `cp/asr/ap` 端口，避免换机器后逐个改脚本。

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

- `capabilities-and-usage.md`
  - 当前保留能力
  - 常用命令
  - 本轮已验证结果
  - 当前边界与排除项
- `environment-and-migration.md`
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
