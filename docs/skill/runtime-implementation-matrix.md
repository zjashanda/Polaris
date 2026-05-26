# Runtime 优化方案一致性矩阵

本文用于对齐：

- `docs/embedded_validation_runtime_rearchitecture_plan.md`
- `docs/validation_runtime_advanced_optimization_plan.md`
- 当前 skill 已落地代码

## 已完成

| 方案项 | 当前实现 | 主要文件 |
|---|---|---|
| Event Layer | 日志/JSON 产物转 `ValidationEvent` | `runtime/events.py`, `runtime/parsers/*` |
| Timeline | 统一时间线，断言使用 monotonic ms | `runtime/timeline.py` |
| Temporal Assertion | 事件存在、顺序、窗口、禁止事件、profile 断言 | `runtime/assertion_engine.py` |
| Replay Package | 输出 events/timeline/runtime_state/assertions/report | `runtime/replay.py`, `scripts/runtime_replay.py` |
| Runtime Plugin 化 | kernel + wake/asr/media/network/reboot 插件骨架 | `runtime/kernel/*`, `runtime/plugins/*` |
| Event Schema 正式化 | event_version/plugin/tags/severity/wall/monotonic/parent/caused_by | `runtime/events.py` |
| 执行记录闭环 | preflight、attempts、state before/after/diff、execution_record | `scripts/run_optimized_task.py` |
| Resource Runtime MVP | serial/audio/network/cloud/power claim、conflict、local lock/release | `runtime/resource_runtime.py` |
| Constraint Engine MVP | 项目、场景、副作用、串口拓扑、云环境、网络、打断 guard 校验 | `runtime/constraint_engine.py` |
| Parallel State Snapshot | audio/recognition/media/network/power/cloud 并行状态 | `runtime/state_machine.py` |
| Scene Graph MVP | strategy -> DAG scene，constraint check，mutation | `runtime/scene_engine.py`, `scripts/generate_scene.py` |
| Scene Runner MVP | scene node 顺序调用 `run_optimized_task.py` | `scripts/run_scene.py` |
| Failure/Health MVP | failure fingerprint、health metrics、报告 | `runtime/failure_analysis.py`, `scripts/analyze_execution_store.py` |
| Replay VM-lite | cursor、snapshot、rollback、time travel 到事件 | `runtime/replay_vm.py`, `scripts/replay_vm.py` |
| Simulation-lite | 生成 Fake log 并可 replay | `runtime/simulation.py`, `scripts/simulate_runtime.py` |
| Assertion DSL-lite | `EXPECT/FORBID` 三类基础时序 DSL | `runtime/assertion_dsl.py`, `scripts/run_assertion_dsl.py` |
| 真机 session 配置隔离 | `run_cucumber.py` 将 env-file/context 的 AP/CP/ASR/baudrate 传给 managed session，probe/read_lines 优先使用 session_manifest | `scripts/run_cucumber.py`, `tools/device/polaris_serial_harness.py`, `tools/core/polaris_runtime.py`, `tools/core/polaris_config.py` |
| 首唤醒有效音频锚点 | 播放进程明显长于 wav 时长时，使用 `AudioCompleted - audio_duration_ms` 估算有效波形起点；不能估算才输出 `TIMING_AMBIGUOUS` | `runtime/assertion_engine.py`, `runtime/parsers/json_artifact_parser.py` |
| 项目能力降级 | WS63 `cp` 留空时，BDD 与 Runtime 均按 AP/ASR 闭环判断；WB01 仍要求 CP/AP/ASR | `scripts/run_cucumber.py`, `runtime/capabilities.py`, `runtime/replay.py` |
| 优化任务结果聚合 | `run_optimized_task.py` 优先按 scenario/runtime 聚合，不把 `status=DONE` 误判为 PASS | `scripts/run_optimized_task.py` |

## 部分完成

| 方案项 | 当前状态 | 后续差距 |
|---|---|---|
| Validation Kernel | 已有 plugin kernel | 尚未统一管理 IR、resource、constraint、replay vm 生命周期 |
| Event Graph | scene graph 已有 DAG，event 有 parent/caused_by 字段 | runtime timeline 还不是完整 Event DAG，事件因果关系仍需自动推导 |
| Hierarchical StateMachine | 已有并行状态快照 | 尚未实现完整层级状态机和状态断言 DSL |
| Capability Runtime | 已能推导 cp/asr 能力并降级 | 尚未覆盖 codec/latency/media/network/power 细粒度能力 |
| Device Adapter Layer | tools/scripts 已承担串口/声卡/云控 | 尚未形成统一 adapter interface |
| IR Compiler | compile_feature 已有 compiled plan | 尚未形成 feature/task/agent 全入口统一 IR schema |
| Analytics Pipeline | 可离线分析 execution_record | 尚未流式化，也未接长期指标库 |

## 明确暂缓

| 方案项 | 暂缓原因 |
|---|---|
| Distributed Runtime | 当前只做本地真机 skill，不做远程 worker/device pool |
| 大规模 Failure Clustering | 当前先做 fingerprint/health MVP，不做大规模聚类平台 |
| 完整 Replay VM | 当前只有 VM-lite，不做完整 snapshot rollback/fault injection |
| 完整 Device Simulation | 当前只有 Fake log，不模拟云端协议/ASR 模型/媒体栈 |
| 完整 Validation DSL Compiler | 当前只有 assertion DSL-lite，不替代 Python profile 断言 |
| Runtime Plugin Sandbox | 当前插件同进程执行，暂不做进程级隔离和内存限制 |

## 当前优先验证路径

1. `run_optimized_task.py --precheck-only`：验证 env/task/resource/constraint。
2. `run_optimized_task.py --mode dry-run`：验证 Cucumber runner 不被破坏。
3. `generate_scene.py` + `run_scene.py --print-command`：验证 scene graph 和 runner 串联。
4. `simulate_runtime.py --replay`：验证 Simulation-lite + Replay。
5. `run_assertion_dsl.py`：验证 DSL-lite。
6. WB01/WS63 分别执行 precheck/dry-run，小规模 true-device smoke 按需执行。

## 2026-05-26 真机验证记录

| 项目 | 场景 | 端口来源 | BDD 断言 | Runtime 断言 | 结论 |
|---|---|---|---|---|---|
| `cskwb01` | `first_wake` | env-file/context -> managed session，COM13/COM12/COM14 | CP/AP/ASR 唤醒闭环，播放 returncode=0 | `WakeDetected_within_3000ms` PASS，估算有效波形起点后约 1062ms | PASS |
| `venusws63` | `first_wake` | env-file/context -> managed session，COM20/COM16，CP 留空 | AP/ASR 唤醒闭环，播放 returncode=0 | `WakeDetected_within_3000ms` PASS，估算有效波形起点后约 895ms | PASS |

说明：两次真机 smoke 都遇到主机播放进程耗时明显大于 1266ms wav 时长的情况，因此 Runtime 使用 `AudioCompleted - audio_duration_ms` 作为有效波形起点；这与方案中的 Timeline/Temporal Assertion 思路一致，避免把播放工具初始化耗时误归因为固件唤醒超时。
