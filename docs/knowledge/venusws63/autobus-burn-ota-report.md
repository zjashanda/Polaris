# VenusA+WS63 自动烧录、OTA 与报告集成说明

## 来源能力

本说明沉淀自 `X:\skillhub\autobus` 的 Autobus skill。当前 Polaris 已将关键能力迁移到本仓库：

- 自动烧录工具目录：`tools\VenusA+WS63`
- Polaris 烧录包装入口：`tools\firmware\polaris_venusws63_auto_burn.py`
- OTA 轮次统计工具：`tools\ota\venus_ota_stats.py`
- OTA 邮件 HTML 报告工具：`tools\ota\build_venus_ota_html_report.py`

## 当前设备串口映射

当前 `polaris.local.json` 的 `venusws63` 项目映射为：

- VenusA/AP：`COM11@921600`
- WS63/upper/asr：`COM12@921600`
- 控制口：`COM13@115200`

Autobus 原台架默认是 `COM22/COM21/COM23`。在 Polaris 中执行时必须优先读取 `polaris.local.json`，不要沿用 Autobus 原默认端口。

## 自动烧录逻辑

烧录包装入口会完成以下动作：

1. 读取 `polaris.local.json`，提取当前项目串口。
2. 接收固件 zip 或已解压目录；zip 会解压到 `tools\fw\extracted\<固件名>`。
3. 定位 VenusA 固件：优先 `fw.hex`，必要时使用 `fw.img`。
4. 定位 WS63 固件：优先 `ws63-liteos-app_all.fwpkg` 或匹配 `ws63/ws53 + all` 的 fwpkg。
5. 调用 `tools\VenusA+WS63\auto_burn.py`。
6. Windows 下通过 `cmd /c chcp 936` 启动，避免 WS63 `optLog` 里 `烧写结果：成功` 变成乱码。
7. 保存 `preflight.json`、`auto_burn_stdout.log`、`summary.json`、`summary.md` 到 debug 目录。

真实烧录必须显式携带 `--allow-side-effects`；只验证命令构造时使用 `--dry-run`。

示例：

```powershell
python tools\firmware\polaris_venusws63_auto_burn.py `
  --firmware tools\fw\Midea_VenusA_WS63_35.03.01.01.18.26.06.04.00.04_20260616_171724.zip `
  --dry-run

python tools\firmware\polaris_venusws63_auto_burn.py `
  --firmware tools\fw\Midea_VenusA_WS63_35.03.01.01.18.26.06.04.00.04_20260616_171724.zip `
  --allow-side-effects
```

## 烧录成功标准

- VenusA 烧录 stdout 出现 `MD5 CHECK SUCCESS` 和 `FLASH DOWNLOAD SUCCESS`。
- WS63 最新 `tools\VenusA+WS63\BurnTool_Gold\optLog\optLog_*.txt` 出现 `烧写结果：成功`。
- `auto_burn.py` 返回码为 0。
- 烧录后执行 `version`，`Project Version` 必须为目标固件版本。

如果 VenusA 已成功但 WS63 失败，优先用 `--skip-venusa` 只重烧 WS63；不要无证据地反复重烧 VenusA。

## OTA 自动化逻辑

Autobus OTA 主脚本 `otaPartitaForMidea-test_burn.py` 的核心逻辑如下，当前先沉淀为 Polaris 知识和统计/报告能力：

- `-b 1`：下载阶段设备断电。
- `-b 2`：升级阶段设备断电。
- `-b 3`：下载阶段路由器/网络断电。
- `-b 4`：下载阶段设备断电 + 网络断电。
- `-b 5`：每轮随机选择下载阶段或升级阶段设备断电。
- `-b 6`：每轮随机选择下载阶段设备断电、升级阶段设备断电或下载阶段网络断电。
- `-e uat`：每轮前后通过 `flash.set.int env@1` 保持 UAT 环境。
- 工作日 12:30-13:30 只暂停启动新轮次，不强行中断正在执行的 OTA。

## OTA 统计与报告

统计：

```powershell
python tools\ota\venus_ota_stats.py <TASK_DIR>\stdout.log --csv <TASK_DIR>\ota_break_stats.csv
```

邮件 HTML 报告：

```powershell
python tools\ota\build_venus_ota_html_report.py --task-dir <TASK_DIR>
```

HTML 报告遵守以下口径：

1. 标题/header。
2. `重点结论`。
3. `一、测试项`。
4. `二、测试步骤`。
5. `三、测试结果`。
6. `四、测试分析`。
7. `五、日志附件路径`。

邮件版使用 inline CSS 和 table 布局，不依赖 `<style>`、CSS 变量、flex/grid、外部字体或脚本。

## 已知异常归因

- `hasNewVer:false` 且没有 `otaStart/fw_url`：优先归因云端未推送，不判脚本失败。
- `OTA update success`、版本正确、环境正确但脚本判失败：归因自动化判定问题。
- `not support flash` -> `Exception on CORE1` / `CORE1 HALTED` -> `RESET=0x1/AON`：归因 flash 型号/安装流程支持问题。
- WS63 `csk_flash_drv.c:294` ASSERT 后长期停在 `ota_step=2`：归因设备/固件 OTA 状态恢复问题。
- WS63 `optLog` 结果为 `????`：优先归因 code page，不直接判烧录失败；需用 `chcp 936` 重新执行。

## 后续扩展

如果要把完整 OTA 执行也迁移为 Polaris 原生入口，应先解决 `otaPartitaForMidea-test_burn.py` 对 `pyaudio` 等历史依赖的导入问题，再将 OTA 真机执行包装成 side-effect gated 工具，避免与语音验证串口 session 冲突。
