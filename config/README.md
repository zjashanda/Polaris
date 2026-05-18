# 本地配置目录

本目录用于放每台机器自己的 Polaris 配置。首次 clone 后执行：

```powershell
Copy-Item satellite\cucumber-agent-testing\configs\polaris_env.example.json config\polaris_env.json
notepad config\polaris_env.json
```

`config/polaris_env.json` 包含串口号、声卡 key、Wi-Fi、设备信息等本机差异，默认不提交 Git。

详细字段说明见 `satellite/cucumber-agent-testing/docs/configuration.md`。
