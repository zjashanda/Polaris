---
name: polaris-device-validation
version: 2.0.0
summary: Polaris 语音设备 BDD + Event Runtime 真机验证 skill。
---

# Polaris 语音设备验证 Skill

本 skill 已切换到新方案：Cucumber/BDD 用例入口 + Event Runtime 事件断言 + 项目化本机配置。旧方案已迁移到 `oldTime/`，不再作为执行入口。

## 必须遵守

1. 每次启动先读取根目录 `plan.md`；没有则创建。
2. 执行计划、已执行、待执行、未执行内容必须及时同步到 `plan.md`。
3. 本机配置只使用根目录 `polaris.local.json`；新人从 `polaris.local.example.json` 复制。
4. 真机执行必须显式 `--allow-side-effects`，避免误占串口、声卡、热点或电源控制。
5. 运行结果、debug、cache、result、`polaris.local.json` 不提交 git。

## 主要入口

- 任务入口：`satellite/cucumber-agent-testing/scripts/run_task.py`
- Cucumber 入口：`satellite/cucumber-agent-testing/scripts/run_cucumber.py`
- Runtime replay：`satellite/cucumber-agent-testing/scripts/runtime_replay.py`
- 在线混合压测：`satellite/cucumber-agent-testing/scripts/run_online_mixed_stress.py`
- 压测分析：`satellite/cucumber-agent-testing/scripts/analyze_online_stress.py`
- 新资料学习入口：`docs/intake/<project_id>/<YYYYMMDD_topic>/learning_manifest.json`

## 当前支持方向

- 首次唤醒、识别模式下唤醒。
- 半双工、全双工识别。
- 基础命令词、需求命令词、自由说小样本。
- 自播前置测量、唤醒打断、命令打断。
- 联网恢复、one-shot、唤醒矩阵、误唤醒、在线 VAD。
- 在线基础命令、音乐、相声、新闻、问答混合压测。
- 误唤醒/误识别记录：额外 wake/ASR/command 都要保留并参与归因。

## 常用命令

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --print-command
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\basic_command.example.json --mode execute --allow-side-effects --manage-session
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\online_mixed_stress.example.json --print-command
```

## 配置要点

- WB01：配置 `ap/cp/asr/control` 四个串口。
- WS63：配置 `ap/upper/control` 三个串口，`cp` 留空。
- 真机执行时 managed session 必须使用当前任务/env-file 的串口；不要让根目录 `active_project` 或旧 `config/` 缓存影响另一台设备。
- 没有单独声卡时，`default_playback_device_key` 留空，使用电脑默认声卡。
- 声卡播放返回 0 但设备无唤醒时，先在控制口执行 `uut-pa.on` 和 `pa-enable.set 0 17 0 1`。
- API 场景要先切设备端 UAT/SIT/PRO 环境，再调用接口。

## 持续学习规则

新项目、新功能、新资料不要直接散放到根目录或脚本目录。统一放入：

```text
docs/intake/<project_id>/<YYYYMMDD_topic>/
  learning_manifest.json
  raw/
```

处理顺序：

1. 读取 `learning_manifest.json` 和 `raw/` 原始资料。
2. 输出结构化理解到 `docs/knowledge/<project_id>/`。
3. 列出可自动化项、缺口项、需求不明确项。
4. 资料足够且可验证时，才更新 Cucumber feature、reference registry、task example、Runtime profile 或必要工具。
5. 资料不足时只沉淀 gap list，不伪造 PASS/FAIL 逻辑。

## Runtime 扩展约束

- 新功能不要直接堆到一个大脚本里；优先进入 `satellite/cucumber-agent-testing/runtime/plugins/` 对应领域插件。
- 事件统一使用 `ValidationEvent` v1 schema，保留 wall time，但断言以 monotonic timeline 为准。
- Cucumber 只表达测试意图；执行动作、证据解析、断言逻辑必须落到 registry/runtime/tool 层。
- 外部调度、远程设备池、大规模聚类暂不纳入当前 skill，当前优先保证本地真机闭环稳定。

## 当前优化执行入口

- 新增任务优先走 `satellite/cucumber-agent-testing/scripts/run_optimized_task.py`。
- 它会在现有 `run_task.py` 外层生成 `execution_record.json`、`attempts.jsonl`、`adapter_flows/pre.json`、`adapter_flows/post.json`、`state/before.json`、`state/after.json`、`state_diff.json`。
- 执行记录、重试、资源/约束预检优先走 `run_optimized_task.py`；只有调试底层 Cucumber runner 时才直接用 `run_task.py`。
- 需要稳定前置/收尾动作时，把 `execution.adapter_flows.pre/post` 写进 task；`required=true` 的 pre flow 失败应阻断主流程，避免前置问题误判成固件问题。
- 场景生成走 `generate_scene.py`；新场景执行优先走 `run_kernel_scene.py`，只有需要对比旧直接 runner 时才用 `run_scene.py`。
- Replay VM-lite、Simulation-lite、Assertion DSL-lite 分别走 `replay_vm.py`、`simulate_runtime.py`、`run_assertion_dsl.py`。
- Assertion DSL-lite 已支持 `EXPECT_SEQUENCE`、`EXPECT_RESPONSE`、`EXPECT_DURATION`，可表达 ASR/Command 到 TTS/Media 的响应链路和媒体持续时间；复杂业务仍优先固化到 Python profile 断言。
- Adapter/Capability/IR/EventGraph/StateDSL/Trend 分别走 `inspect_device_adapters.py`、`build_capability_matrix.py`、`compile_validation_ir.py`、`build_event_graph.py`、`run_state_assertion_dsl.py`、`build_analytics_trend.py`。
- Validation IR 不再只支持 task：`compile_validation_ir.py` 可用 `--task`、`--scene` 或 `--feature-plan` 编译；`run_kernel_scene.py --emit-ir-bundle` 可输出 scene 级 IR bundle，用于确认 feature/task/scene 最终走同一套 deterministic runtime 输入。
- 新项目接入时先看 `build_capability_matrix.py`，其中 `audio.loopback_oracle`、`media.acoustic_response_oracle`、云控权限和 `reboot.boot_reason_oracle` 为常见缺口；不要把“设备日志说播了”直接等同于“真实出声质量通过”。
- Kernel 生命周期入口走 `run_validation_kernel.py`；它会在 runner 后自动补齐 runtime replay 侧的 event graph、默认 state assertions 和 Replay VM-lite snapshot。
- 状态稳定性不要只看最终 PASS/FAIL；必须结合 `runtime_state.json` 里的 `state_health`、`state_violations`、`coverage` 区分崩溃/重启、日志缺口、媒体顺序缺失和业务断言失败。
- `run_state_coverage_policy.py` 和 Kernel 后处理会按 profile 检查 coverage 阈值；缺少首唤醒 WakeDetected、基础命令 ASR/Command、联网恢复 NetworkLost/NetworkRecovered 等关键覆盖时，应先归因日志/前置/需求，再决定是否判固件问题。
- 项目差异优先写到 `state_assertion_policy.json` 的 `coverage.projects.<project_id>`，不要在代码里硬编码 WB01/WS63 或新项目阈值。
- Event Graph 需要优先查看 `risk_summary` 和因果边：`command/asr_to_*_response`、`media_started_to_completed`、`media_interrupted`、`interrupt_to_recognition`、`possible_reboot/crash_after_activity`，用于分析在线媒体、打断和重启根因。
- 项目私有云端/媒体/TTS/MP3 marker 先沉淀到 `references/optimization/event_graph_rules.json` 或通过 `build_event_graph.py --rules` 加载，不要优先写死到核心 `runtime/event_graph.py`。
- adapter 单动作规划/执行入口走 `run_adapter_action.py`，默认只 dry-run 渲染命令；常见多步前置走 `plan_adapter_flow.py`，例如 `pa_recover`、`switch_device_env`、`wake_audio_file`、`set_volume`、`set_half_duplex`、`set_full_duplex`。真执行副作用必须显式 `--execute --allow-side-effects`。
- 首次唤醒时序不要直接拿播放进程启动当唯一锚点；如播放进程明显长于 wav 时长，优先按 `AudioCompleted - audio_duration_ms` 估算有效波形起点，无法估算才输出 `TIMING_AMBIGUOUS`。
