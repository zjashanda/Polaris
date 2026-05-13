# Polaris 模块化验证池工作流

## 目标

把 Polaris 从“按现有脚本临时验证”升级为“输入需求、设备环境和证据后，按模块化验证池生成测试方案、用例、断言、执行入口和最终归因”的稳定工作流。

## 核心原则

1. 旧执行结果只能作为案例，不是新功能的默认断言。
2. 新功能必须先拆成“功能意图 + 触发方式 + 前置状态 + 期望输出 + 状态变化 + 证据来源”。
3. 同名能力允许多个变体，例如全双工/半双工、在线/离线、云控/语音控制、支持/不支持。
4. 需求未说明的关键维度，不强行判固件 FAIL；先生成 TODO、BLOCKED 或最小探测用例。
5. raw FAIL 先收敛验证路径，再保留最终 FAIL；最终 FAIL 只能是固件不满足需求，或需求本身错误/矛盾。
6. 通用方法回灌 `references/validation-pool/`；Polaris 当前设备、云端账号、串口和结论留在 `config/`、`result/` 或后续项目 deliverables 中。

## 标准流程

### 1. 输入归档

- 需求文档、Excel 用例、词表、tone 表、协议说明。
- 当前设备信息：`iot_id`、`mac`、`wakeup_id`、机型、环境 SIT/UAT/PRO。
- 串口拓扑：`COM12=CP`、`COM13=ASR`、`COM14=AP`、`COM15=电源控制`。
- 本机串口配置：`config/polaris_local_ports.json`；命令未指定串口时读取该文件，命令指定串口时同步回该文件。
- 播放链路：默认 render device key、音量、播放脚本。
- 热点/联网信息：SSID、密码、IP、cloud status。
- 历史结果：`config/`、`result/<session>/`、报告和失败分析。

### 2. 功能点建模

```text
功能点 = 意图 + 触发 + 模式 + 前置状态 + 输入 + 期望状态变化 + 期望反馈 + 禁止行为 + 证据源
```

常用标签：

- `wake-session`
- `duplex-mode`
- `network-online`
- `cloud-control-settings`
- `night-mode`
- `volume-level`
- `ac-control-command`
- `online-offline-asr`
- `fault-convergence`

### 3. 模块匹配

```powershell
python tools/pool/polaris_validation_pool.py classify --project-key polaris_midea_ac SKILL.md capabilities-and-usage.md environment-and-migration.md
```

命中多个互斥变体时，优先生成最小探测用例，而不是直接套旧结论。

### 4. 方案与用例生成

每个功能点落成：

| 需求点 | 模块 | 变体 | 用例 | 主断言 | 辅断言 | 证据 | 归因规则 |
| --- | --- | --- | --- | --- | --- | --- | --- |

方案必须包含正向、反向、边界、状态恢复、BLOCKED 条件和失败归因规则。

### 5. 执行前门禁

- `plan.md` 已更新本轮计划。
- `.current_result_dir` 指向当前 session。
- `result/<session>/logs/live/heartbeat.json` 新鲜且串口打开。
- 播放链路能让 DUT 真正听到音频。
- DUT 已联网，或当前用例明确是离线用例。
- `deviceinfo` 能拿到或能从 `config/polaris_env.json` 回退得到设备身份。
- COM15 或替代控制方式能执行预期重启/断电动作；否则相关用例 BLOCKED。

### 6. 执行与收敛

- 串口采集避免并发抢占。
- 每个阶段都写入证据目录。
- raw FAIL 先按 `fault-convergence.md` 排查：采集窗口、状态污染、播放路径、云端返回、ASR 误识别、热点/网络、脚本断言。
- 修正验证逻辑后重跑对应最小用例。
- 最终报告不能把环境问题、脚本问题、人工项伪造成固件 FAIL。

### 7. 回灌验证池

出现新功能类型、新变体、新证据标记、新门禁规则、新收敛步骤或新反例覆盖方法时，回灌到对应模块。
