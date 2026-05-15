# Polaris Cucumber Agent Testing

该目录用于把语音测试方案中的测试项落地为 BDD/Gherkin 场景，并由本地 Agent runner 生成执行计划或调试报告。

## 当前边界

- 默认只做 `plan-only`，不占用串口、不播放音频、不调用云端。
- 调试输出只写入 `satellite/cucumber-agent-testing/debug/runs/`。
- 需要真机执行时再显式使用 `--mode execute`，并确认可能调用现有 Polaris 工具。

## 首批落地能力

- 首次唤醒
- 识别模式下唤醒
- 半双工识别
- 全双工识别
- 基础命令词识别

## 常用命令

```powershell
python satellite/cucumber-agent-testing/scripts/run_cucumber.py --mode plan-only
python satellite/cucumber-agent-testing/scripts/run_cucumber.py --mode dry-run --tag @first_wake
```

输出目录会打印在命令最后一行。
