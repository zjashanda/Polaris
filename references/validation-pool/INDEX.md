# Polaris 模块化验证池索引

## 使用顺序

1. 读取 `schema.md`。
2. 读取输入需求和当前环境。
3. 用 `tools/pool/polaris_validation_pool.py classify` 匹配候选模块。
4. 只读取命中的模块。
5. 按当前需求选择变体并生成用例。
6. 执行后把新发现的通用逻辑回灌。

## 模块列表

| 模块 | 适用场景 | 当前来源 |
| --- | --- | --- |
| `wake-session.md` | 唤醒、会话保持、超时、未唤醒阻断、重唤醒恢复 | Polaris + Trisolaris 方法 |
| `duplex-mode.md` | 全双工、半双工、播报中收音、打断、播放后恢复 | Polaris |
| `network-online.md` | 热点、Wi-Fi、IP、cloud status、deviceinfo、断网重连 | Polaris |
| `cloud-control-settings.md` | 云控设置项：Mic、音量、多唤醒、方言、主动交互等 | Polaris |
| `night-mode.md` | 夜间模式开关、状态回读、重启/联网边界 | Polaris |
| `volume-level.md` | 音量固定值、增减、边界、回读、持久化 | Polaris + Trisolaris 方法 |
| `ac-control-command.md` | 空调业务命令词，在线/离线控制语义 | Polaris |
| `online-offline-asr.md` | 在线 ASR/NLU/TTS 与离线 ASR/tone 对照 | Polaris |
| `fault-convergence.md` | raw FAIL 收敛、控制变量、最终归因 | Polaris + Trisolaris 方法 |

## 变体优先级

1. 当前需求明确写出的逻辑。
2. 用户当前轮明确澄清的逻辑。
3. 当前 DUT 实测证据。
4. 验证池通用模板。
5. 历史结果仅作案例，不作为默认断言。
