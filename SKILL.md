---
name: polaris-device-validation
description: 用于在本仓库中验证 Polaris 系列美的空调语音设备，覆盖串口日志、COM15 电源控制、热点编排、短语探测、已验证正常的云端控制、文档用例执行与报告同步。
---

# Polaris 设备验证技能

本文档统一使用 UTF-8 编码，作为当前仓库根目录下的本地 skill 使用。后续迁移到新机器时，直接复制根目录这 3 份文档即可，不需要安装到 `.codex/skills`。

## 这个 skill 当前保留什么能力

只保留已经验证为“能正常控制”或“能稳定执行”的能力：

- 基础设施与观测
  - `COM12 / COM13 / COM14` 持续日志采集
  - 串口命令下发与回显确认
  - `COM15` 控制的 `wb01` / `csk` 断电重启
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
