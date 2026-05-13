---
module_id: fault-convergence
title: raw FAIL 收敛和最终归因
tags: [FAIL, BLOCKED, 归因, 固件问题, 设备问题, 需求问题, 环境问题, 云端, 脚本, 重跑, 控制变量]
source_projects: [polaris, trisolaris-method]
---

# raw FAIL 收敛和最终归因

## 适用需求特征

- 任意用例执行后出现 FAIL、BLOCKED、无日志、识别失败、云控失败、设备离线、断言争议。

## 变体维度

- 环境/串口/播放/热点问题。
- 云端接口/业务能力问题。
- 设备硬件或个体问题。
- 固件运行态问题。
- 需求错误或矛盾。
- 脚本/断言/用例设计问题。

## 需求解析字段

- 用例 ID、需求期望、实测现象、证据路径、前置状态、复现次数、控制变量结果。

## 验证方案模板

1. 检查前置门禁。
2. 检查输入是否真实发生。
3. 检查日志窗口和采集完整性。
4. 检查状态污染和恢复动作。
5. 检查在线/离线路径是否匹配需求。
6. 检查云端返回和机型支持矩阵。
7. 检查 ASR/keyword/TTS 候选。
8. 控制变量复测：换话术、换模式、重启、重放、对照功能。
9. 修正验证逻辑后重跑。
10. 保留最终 FAIL 或归为 BLOCKED/TODO/INVALID。

## 用例模板

- `FAIL-TRIAGE-001`
- `FAIL-ASSERT-FIX-001`
- `FAIL-CONTROL-VARIABLE-001`
- `FAIL-RETEST-001`

## 断言与证据

- raw FAIL 不等于最终 FAIL。
- 后续 PASS 不能吞掉异常重启或状态污染。
- 环境问题归 BLOCKED；人工项归 TODO；脚本错误归 INVALID。
- 最终 FAIL 必须写明需求、实际、证据、归因和复测情况。

## 执行器映射

- `tools/reporting/polaris_refresh_failure_diagnosis.py`
- `tools/reporting/export_fail_case_detail_md.py`
- `tools/reporting/polaris_status_sync.py`
- 各功能模块的 targeted rerun 脚本。

## 回灌规则

- 每次收敛出新的通用排查步骤，补到本模块或对应功能模块。
