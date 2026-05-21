# config 目录说明

这个目录现在不作为新人主配置入口。

新用户只需要在仓库/skill 根目录维护：

```powershell
Copy-Item polaris.local.example.json polaris.local.json
notepad polaris.local.json
```

`polaris.local.json` 只记录基础环境：当前项目、串口、波特率、声卡 key、唤醒词、Wi-Fi、API/设备端环境。

`config/` 下文件分三类：

- `polaris_env.json`、`polaris_local_ports.json`：旧版兼容或串口缓存。
- `polaris_doc_case_status.json`、`polaris_auto_executable_case_detail.md`、`polaris_fail_case_detail.md`、`polaris_failure_diagnosis.json`：运行状态、结果、诊断输出。
- `polaris_command_catalog.*`、`polaris_validation_reference.md`、`polaris_model_applicability.md`：知识库或参考报告。

不要把新的项目基础配置继续堆到这里；后续只在确认没有脚本依赖后，再考虑迁移/归档历史文件。
