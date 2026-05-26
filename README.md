# Polaris Voice Validation Skill

当前目录只保留优化后的 BDD + Event Runtime 真机验证方案。历史旧方案、运行结果、旧配置、旧脚本和旧资料已整体归档到 `oldTime/`。

## 快速开始

```powershell
Copy-Item polaris.local.example.json polaris.local.json
notepad polaris.local.json
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --print-command
```

真机执行必须显式允许副作用：

```powershell
python satellite\cucumber-agent-testing\scripts\run_task.py --task satellite\cucumber-agent-testing\tasks\examples\first_wake.example.json --mode execute --allow-side-effects --manage-session
```

## 当前新方案目录

```text
README.md                         # 新方案入口
SKILL.md                          # Codex skill 说明
polaris.local.example.json         # 本机配置模板
polaris.local.json                 # 本机真实配置，按需保留，不提交
satellite/cucumber-agent-testing/  # Cucumber/BDD + Event Runtime 主体
tools/                             # 新 runner 必需的最小串口/音频/云控工具层
docs/                              # 说明文档 + 命令词、用例表、API、需求输入资料
docs/intake/                       # 新项目/新功能资料导入入口
docs/knowledge/                    # 学习后的结构化沉淀
docs/skill/                        # 新方案说明和验证口径
oldTime/                           # 旧方案完整归档，不作为运行入口
```

## 重要原则

- 新人只改 `polaris.local.json`，不要再到旧 `config/` 里找配置。
- 执行入口统一走 `satellite/cucumber-agent-testing/scripts/run_task.py` 或 `run_cucumber.py`。
- 运行产物只写到 `satellite/cucumber-agent-testing/debug/`，不提交 git。
- Runtime 会记录实际识别文本、命令关键词和额外识别结果；未说却识别到的内容按误唤醒/误识别复核。
- API/云控前必须确认设备端 CSK/AP 环境与 `polaris.local.json` 里的 `cloud.api_environment` 一致。

更多说明见：

- `satellite/cucumber-agent-testing/README.md`
- `satellite/cucumber-agent-testing/docs/configuration.md`
- `docs/intake/README.md`
- `docs/skill/event-runtime-mvp.md`
- `docs/skill/supported-test-items-cucumber-guide.md`

## 新项目/新功能怎么让我学习

后续有新项目说明、新功能需求、外部测试方案、类似 `voice-test-plan-designer` 的 skill，统一放到：

```text
docs/intake/<project_id>/<YYYYMMDD_topic>/
  learning_manifest.json
  raw/
```

从 `docs/intake/templates/learning_manifest.template.json` 复制模板，填写本次资料希望我学习什么、有哪些文件、目标是项目 profile、Cucumber 用例、Runtime 断言还是压测策略。

我学习后会把结构化理解写到 `docs/knowledge/<project_id>/`，并在资料足够时再沉淀到 `satellite/cucumber-agent-testing/` 的 feature、reference、task 和 runtime。资料不够时只输出缺口清单，不直接伪造可执行能力。
