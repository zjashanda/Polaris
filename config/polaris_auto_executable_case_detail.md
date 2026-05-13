# Polaris 自动可执行用例执行与断言说明（增强版）

> 这一版补齐了：每条用例的摘要、要测试什么、文档预期、自动化如何执行、自动化如何断言、当前 FAIL/BLOCKED 到底卡在哪里。

## 1. 当前自动化基线

- 工作目录：`D:\revolution4s\Polaris`
- 当前证据 session：`D:\revolution4s\Polaris\result\20260423111046`
- 自动可执行总数：`90` / 全量 doc 用例 `715`
- 当前执行结果：`90 executed / 81 PASS / 3 FAIL / 6 BLOCKED / 625 SKIP`
- Wi-Fi：`pcwifi24`；状态：`online`
- 唤醒词：显示值=`小美小美`；设备值=`xiao mei xiao mei`
- 声卡 key：`VID_8765&PID_5678:9_2A847557_7_0000`
- 串口：`COM12=cskcp / CP / read_only` / `COM13=wb01 / writable` / `COM14=cskap / AP / writable` / `COM15=power control / writable`

## 2. 统一执行入口

```powershell
python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_28 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"

python tools/execution/polaris_doc_case_batch_runner.py --case-ids 美的空调_22 美的空调_23 美的空调_24 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"
```

- 三路日志 `COM12/COM13/COM14` 持续采集，不会因为跑某条 case 中断。
- case 执行只做时间窗切片，把窗口日志落到各自证据目录。
- 最终判定优先看 `judge.json`；完整过程、setup/recovery/playback/state 看 `doc_case_result.json`。

## 3. 157 条自动可执行用例详细说明

## algo_version_upload_case

- runner 调度函数：`run_algo_version_upload_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 先经 COM15 硬重启 WB01。
- 再在 COM14 发送 version，并对比本地版本和上传版本。

### 美的空调_707 在线情况下csk算法版本信息上报功能

**摘要**
- 该用例位于 `csk算法版本信息上报 -> csk算法版本信息上报 -> 在线 -> csk算法版本信息上报`。
- 重点验证 `csk算法版本信息上报` 场景下“在线情况下csk算法版本信息上报功能”是否符合文档预期。
- 自动化接管说明：在线硬重启后应在 AP 日志看到上传的 algo_version / esrVersion，并与本地 version 命令输出保持一致。

**要测试什么**
- 文档层级：`csk算法版本信息上报 -> csk算法版本信息上报 -> 在线 -> csk算法版本信息上报`
- case_type：`csk算法版本信息上报`
- 文档标题：`在线情况下csk算法版本信息上报功能`
- 自动化接管依据：在线硬重启后应在 AP 日志看到上传的 algo_version / esrVersion，并与本地 version 命令输出保持一致。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、先将设备联网，之后断电再上电
2、上电之后，找美的捞上传到云端的csk算法版本信息
- 文档预期：上传的算法版本信息与本地csk-ap侧输入version获取的版本信息一致

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_707 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_algo_version_upload_case`，runner_kind=`algo_version_upload_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经 COM15 硬重启 WB01。
- 再在 COM14 发送 version，并对比本地版本和上传版本。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：本地 `version` 查询结果必须与上传 algo/esr version 对齐，deviceId 也要匹配。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_accent_case

- runner 调度函数：`run_app_accent_case`
- 家族结果分布：`PASS 2 / FAIL 0 / BLOCKED 0`
- 按方言配置计划切换方言。
- 每个方言都跑 one-shot 探测。

### 美的空调_704 在线情况下开启方言后，不支持在线oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下开启方言后，不支持在线oneshot对话功能”是否符合文档预期。
- 自动化接管说明：打开方言后回归在线 one-shot：对粤语/河南话/上海话/山东话/闽南话逐一切换，再验证“小美小美打开空调”不再保留完整命令词在线 ASR。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下开启方言后，不支持在线oneshot对话功能`
- 自动化接管依据：打开方言后回归在线 one-shot：对粤语/河南话/上海话/山东话/闽南话逐一切换，再验证“小美小美打开空调”不再保留完整命令词在线 ASR。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app上开启方言（粤语、河南话、上海话、山东话、闽南话都要设置一遍）
2、使用oneshot交互方式，唤醒+识别中间没有间隔的交互方式，比如“小美小美打开空调”唤醒词和识别词连着说
- 文档预期：1、打开方言后，不支持oneshot交互的方式，后面的识别词无法正常完整识别出来；
比如说“小美小美打开空调”，在线识别结果应是“空调”、“调”或无结果

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_704 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_accent_case`，runner_kind=`app_accent_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按方言配置计划切换方言。
- 每个方言都跑 one-shot 探测。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_705 在线情况下关闭方言后，设为普通话，支持在线oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下关闭方言后，设为普通话，支持在线oneshot对话功能”是否符合文档预期。
- 自动化接管说明：先切到方言再关闭方言恢复普通话，验证“小美小美打开空调”重新支持在线 one-shot，在线 ASR 只保留“打开空调”。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下关闭方言后，设为普通话，支持在线oneshot对话功能`
- 自动化接管依据：先切到方言再关闭方言恢复普通话，验证“小美小美打开空调”重新支持在线 one-shot，在线 ASR 只保留“打开空调”。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app上关闭方言，设为普通话
2、使用oneshot交互方式，唤醒+识别中间没有间隔的交互方式，比如“小美小美打开空调”唤醒词和识别词连着说
- 文档预期：1、关闭方言设为普通话胡，支持oneshot交互的方式，前面的唤醒词不会识别到在线识别结果里面，后面的识别词可以正常完整识别出来；
比如说“小美小美打开空调”，在线识别结果应为"打开空调”，如果识别出来“小美小美打开空调”，则错误！

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_705 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_accent_case`，runner_kind=`app_accent_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按方言配置计划切换方言。
- 每个方言都跑 one-shot 探测。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_accent_persist_case

- runner 调度函数：`run_app_accent_persist_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 设置方言后掉电重启。
- 复机后逐个方言做 one-shot 探测。

### 美的空调_687 在线方言切换后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 方言切换`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线方言切换后掉电操作”是否符合文档预期。
- 自动化接管说明：APP 逐一切换方言后执行 WB01 掉电上电；在当前缺少方言音频的口径下，以重启后的 cloud.order.config.query.reply 仍保留目标 accentId/enableAccent，且“小美小美打开空调”继续表现为方言开启后的 one-shot 降级作为 PASS 证据。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 方言切换`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线方言切换后掉电操作`
- 自动化接管依据：APP 逐一切换方言后执行 WB01 掉电上电；在当前缺少方言音频的口径下，以重启后的 cloud.order.config.query.reply 仍保留目标 accentId/enableAccent，且“小美小美打开空调”继续表现为方言开启后的 one-shot 降级作为 PASS 证据。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app上设置打开方言再切换方言，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
3、有几个方言就反复切换几次
- 文档预期：1、上电后手机app上的方言是切换后的方言，唤醒播报语是切换后的方言播报语
2、掉电前切换的方言掉电后还是这个切换的方言

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_687 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_accent_persist_case`，runner_kind=`app_accent_persist_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 设置方言后掉电重启。
- 复机后逐个方言做 one-shot 探测。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_dialog_announce_case

- runner 调度函数：`run_app_dialog_announce_case`
- 家族结果分布：`PASS 2 / FAIL 0 / BLOCKED 0`
- 只下发云端配置，不播放探测音频。
- 直接从 AP/WB 配置回执日志判断自然对话播报与状态是否正确。

### 美的空调_113 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话后，应立即在 AP/WB 日志看到 full-duplex 配置生效与对应播报开始/结束链路。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话后，应立即在 AP/WB 日志看到 full-duplex 配置生效与对应播报开始/结束链路。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将自然对话打开
3、听一下喇叭播放内容
- 文档预期：1、自然对话被打开后，喇叭会播报“自然对话已开启，现在只要唤醒我就可以进行连续对话”

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_113 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_announce_case`，runner_kind=`app_dialog_announce_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 只下发云端配置，不播放探测音频。
- 直接从 AP/WB 配置回执日志判断自然对话播报与状态是否正确。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：该类不靠语音结果，直接看 AP/WB 是否打印 fullduplex 状态回执。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_134 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 关闭自然对话后，应立即在 AP/WB 日志看到 half-duplex 配置生效与对应播报开始链路。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 关闭自然对话后，应立即在 AP/WB 日志看到 half-duplex 配置生效与对应播报开始链路。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将自然对话关闭
3、听一下喇叭播放内容
- 文档预期：1、自然对话被关闭后，喇叭会播报“自然对话已关闭，现在每次对话都要先唤醒我”

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_134 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_announce_case`，runner_kind=`app_dialog_announce_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 只下发云端配置，不播放探测音频。
- 直接从 AP/WB 配置回执日志判断自然对话播报与状态是否正确。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：该类不靠语音结果，直接看 AP/WB 是否打印 fullduplex 状态回执。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_dialog_config_case

- runner 调度函数：`run_app_dialog_config_case`
- 家族结果分布：`PASS 24 / FAIL 2 / BLOCKED 0`
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。

### 美的空调_22 在线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：在线 half-duplex 下，唤醒后 10ms 内说“打开空调”应形成稳定识别与云端播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下的oneshot对话功能`
- 自动化接管依据：在线 half-duplex 下，唤醒后 10ms 内说“打开空调”应形成稳定识别与云端播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网,关闭自然对话
- 文档步骤：1、将设备整机联网,关闭自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔小于200ms,Wakeup#talk#小美小美#,Action#sleep#10#,online_Asr#talk#打开空调#，Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到在线命令词后，3s内，喇叭播报在线tts语音，在线提示语为空调开机相关的播报提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_22 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10ms -> online_Asr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`8000` ms。
- 本次实际 setup 轨迹：
-   - action=cloud_mic_switch；success=True；enable=True；response_status=200；response_text={"result":{"returnData":{"msg":"成功","code":"0","data":{}}},"errorCode":"0"}；artifact=D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\setup\00_ensure_mic_on
-   - action=cloud_full_duplex；success=True；enable=False；timeout_seconds=15；response_status=；artifact=D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\setup\01_set_dialog_config
-   - action=voice_command_phrase；success=True；artifact=D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\setup\01_02_prepare_voice_command
- 本次实际 recovery 轨迹：
-   - action=cloud_full_duplex；success=True；enable=False；timeout_seconds=15；response_status=；artifact=D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\recovery\01_restore_half_duplex
- 播放返回码=`0`
- 音频文件=`D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\audio\美的空调_22.wav`
- 主音频参数：duration_ms=`7516`；sample_rate=`16000`；channels=`1`；segments=`4`
- 主音频序列：tts:小美小美 -> silence:10ms -> tts:打开空调 -> silence:5000ms
- 播放片段：main_audio:0

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

| 检查项 | actual | expected | 是否通过 |
| --- | --- | --- | --- |
| cloud_apply_success | `True` | `True` | `PASS` |
| cp_wake_count | `1` | `>=1` | `PASS` |
| ap_wake_count | `1` | `>=1` | `PASS` |
| required_online_asr_texts | `{"actual_online_asr_texts": ["打开空调"], "recognized_command_keywords": ["kong tiao kai ji"]}` | `{"required_online_asr_texts": ["打开空调"], "required_command_keywords": ["kong tiao kai ji"]}` | `PASS` |
| successful_response_count | `0` | `>=1` | `FAIL` |
| closure_prompt_count_reference | `0` | `reference-only` | `PASS` |

**当前结果 / FAIL 在哪里**
- 当前结果=`FAIL`。
- 判定原因：自然对话行为未满足 successful_response_count，actual=0 expected=>=1。
- 失败直接来自以下检查项：
-   - successful_response_count：actual=0；expected=>=1

**本次关键观测值**
- 关键计数：cp_wake_count=1；cp_command_count=1；ap_wake_count=1；wb_wake_count=0；wb_online_wake_count=1；ap_asr_count=0；wb_asr_count=0；ap_cloud_tts_play_count=1；ap_instruction_broadcast_count=1；wb_playback_start_count=0；wb_playback_end_count=0；unique_command_keyword_count=1；interrupt_reset_count=4；wake_during_playback_count=0；boot_marker_count=0；crash_marker_count=0
- 关键内容：recognized_command_keywords=["kong tiao kai ji"]；ap_online_asr_texts=["打开空调"]；ap_instruction_broadcast_mids=["29c68927-c658-4a24-982f-0925afa08824"]

**关键日志摘录**
- line_counts={"COM12": 11, "COM13": 1104, "COM14": 609}
- wakeup_lines：
  - 2026-04-23T11:57:11.000 [COM12/cskcp] [C/I:1637261]WAKE(1): CHN=3, KEY=3(xiao mei xiao mei), NCM=-26
  - 2026-04-23T11:57:13.030 [COM12/cskcp] [C/I:1639296]WAKE(0): CHN=1, KEY=1(kong tiao kai ji), NCM=0
  - 2026-04-23T11:57:11.134 [COM14/cskap] [2026-04-23 11:57:10.640][O][evs_event # client] wakeup_callback, keyword: xiao mei xiao mei
- player_status_lines：
  - 2026-04-23T11:57:16.570 [COM14/cskap] [2026-04-23 11:57:15.900][O][player_td # AI]{"keyTime_log":{"ev":2006,"timestamp":"2026-04-23 11:57:15.900","mid":"","text":"TTS playing with http://staging-tts.iflyos.cn/live/b6773868017531b06b5179961de8d81bb896fe8b.mp3"}} 

**证据路径**
- 执行目录：`D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22`
- judge：`D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\judge.json`
- result：`D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\runs\20260423115613233_doc_case_run_美的空调_22\doc_case_result.json`

### 美的空调_23 在线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：在线 half-duplex 下，唤醒后 1s 说“打开空调”应形成稳定识别与云端播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下的oneshot对话功能`
- 自动化接管依据：在线 half-duplex 下，唤醒后 1s 说“打开空调”应形成稳定识别与云端播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网,关闭自然对话
- 文档步骤：1、将设备整机联网,关闭自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔大于1s,Wakeup#talk#小美小美#,Action#sleep#1000#,online_Asr#talk#打开空调#，Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到在线命令词后，3s内，喇叭播报在线tts语音，在线提示语为空调开机相关的播报提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_23 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_24 在线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：在线 half-duplex 下仅唤醒并等待超时，再说命令词不应被识别，且应只播报一次超时退出提示。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下的oneshot对话功能`
- 自动化接管依据：在线 half-duplex 下仅唤醒并等待超时，再说命令词不应被识别，且应只播报一次超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网,关闭自然对话
- 文档步骤：1、将设备整机联网,关闭自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔大于15s,Wakeup#talk#小美小美#,Action#sleep#15000#,online_UnAsr#talk#打开空调#，Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、唤醒后超过超时时间再说命令词"打开空调”，命令词不会识别，喇叭会播报超时时间的提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_24 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 15000ms -> online_UnAsr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_25 在线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：在线 full-duplex 下，唤醒后 10ms 内说“打开空调”应形成稳定识别与云端播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下的oneshot对话功能`
- 自动化接管依据：在线 full-duplex 下，唤醒后 10ms 内说“打开空调”应形成稳定识别与云端播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网,打开自然对话
- 文档步骤：1、将设备整机联网,打开自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔小于200ms,Wakeup#talk#小美小美#,Action#sleep#10#,online_Asr#talk#打开空调#，Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到在线命令词后，3s内，喇叭播报在线tts语音，在线提示语为空调开机相关的播报提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_25 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10ms -> online_Asr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_26 在线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：在线 full-duplex 下，唤醒后 1s 说“打开空调”应形成稳定识别与云端播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下的oneshot对话功能`
- 自动化接管依据：在线 full-duplex 下，唤醒后 1s 说“打开空调”应形成稳定识别与云端播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，打开自然对话
- 文档步骤：1、将设备整机联网,打开自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔大于1s,Wakeup#talk#小美小美#,Action#sleep#1000#,online_Asr#talk#打开空调#，Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到在线命令词后，3s内，喇叭播报在线tts语音，在线提示语为空调开机相关的播报提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_26 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_27 在线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“在线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：在线 full-duplex 下，单次唤醒后先说“关闭空调”再说“打开空调”应都被识别并播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 在线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`在线情况下的oneshot对话功能`
- 自动化接管依据：在线 full-duplex 下，单次唤醒后先说“关闭空调”再说“打开空调”应都被识别并播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网,打开自然对话
- 文档步骤：1、将设备整机联网,打开自然对话
2、发送语音“小美小美，关闭空调，打开空调”，这前两句句话中间的时间间隔小于200ms,最后一句话的时间间隔大于3s，小于10s,Wakeup#talk#小美小美#,Action#sleep#10#,online_Asr#talk#关闭空调#，Action#sleep#5000#,online_Asr#talk#打开空调#,Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到关闭空调的在线命令词后，3s内，喇叭播报在线tts空调关机相关的播报提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
3、最后一句话“打开空调”的命令词会识别，会播报在线tts打开空调相关的提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_27 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10ms -> online_Asr[talk]=关闭空调 -> 静默 5000ms -> online_Asr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `2`。
- 识别关键词必须包含：kong tiao guan ji、kong tiao kai ji。
- AP 云端 TTS 播放至少 `2` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_33 在线情况下的识别播报语打断对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音打断（回声消除） -> 在线 -> 在线识别播报语打断`。
- 重点验证 `识别播报语打断` 场景下“在线情况下的识别播报语打断对话功能”是否符合文档预期。
- 自动化接管说明：在线天气播报期间再次唤醒，应打断当前在线播报并切回新的唤醒会话。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音打断（回声消除） -> 在线 -> 在线识别播报语打断`
- case_type：`识别播报语打断`
- 文档标题：`在线情况下的识别播报语打断对话功能`
- 自动化接管依据：在线天气播报期间再次唤醒，应打断当前在线播报并切回新的唤醒会话。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、发送语音“小美小美，合肥今天的天气，小美小美”，第二句话与第三句话的时间间隔小于200ms,,Wakeup#talk#小美小美#,Action#sleep#1000#，online_Asr#talk#合肥今天的天气#，Action#sleep#3000#，Wakeup#talk#小美小美#,Action#sleep#1000#，
3、听一下喇叭播放的内容
- 文档预期：1、唤醒正确识别2次，在线播报天气时进行唤醒，会打断在线天气播报的提示语，切换为唤醒提示语的播报

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_33 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=合肥今天的天气 -> 静默 3000ms -> 唤醒词[talk]=小美小美 -> 静默 1000ms
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 在线 ASR 文本必须包含：合肥今天的天气。
- AP 云端 TTS 播放至少 `1` 次。
- AP `player reset by user` 至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_34 在线情况下的识别播报语打断对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音打断（回声消除） -> 在线 -> 在线识别播报语打断`。
- 重点验证 `识别播报语打断` 场景下“在线情况下的识别播报语打断对话功能”是否符合文档预期。
- 自动化接管说明：在线全双工下，天气播报期间继续说股票查询，应打断前一条在线播报并切换到后一条请求。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音打断（回声消除） -> 在线 -> 在线识别播报语打断`
- case_type：`识别播报语打断`
- 文档标题：`在线情况下的识别播报语打断对话功能`
- 自动化接管依据：在线全双工下，天气播报期间继续说股票查询，应打断前一条在线播报并切换到后一条请求。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网，自然对话已打开
- 文档步骤：1、将设备联网，打开自然对话
2、发送语音“小美小美，合肥今天的天气，今天的股票情况”，第二句话与第三句话的时间间隔小于3000ms,,Wakeup#talk#小美小美#,Action#sleep#1000#，online_Asr#talk#合肥今天的天气#，Action#sleep#3000#，online_Asr#talk#今天的股票情况#,Action#sleep#5000#，
3、听一下喇叭播放的内容
- 文档预期：1、唤醒正常，在线播报天气tts时再交互股票情况，会打断在线天气播报的tts，切换为播报股票情况的tts

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_34 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=合肥今天的天气 -> 静默 3000ms -> online_Asr[talk]=今天的股票情况 -> 静默 5000ms
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 在线 ASR 文本必须包含：合肥今天的天气、今天的股票情况。
- AP 云端 TTS 播放至少 `2` 次。
- AP `player reset by user` 至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_46 在线情况下的唤醒功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒 -> 在线 -> 在线唤醒测试`。
- 重点验证 `唤醒词` 场景下“在线情况下的唤醒功能”是否符合文档预期。
- 自动化接管说明：在线 half-duplex 唤醒后等待超时，应出现一次退出提示播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒 -> 在线 -> 在线唤醒测试`
- case_type：`唤醒词`
- 文档标题：`在线情况下的唤醒功能`
- 自动化接管依据：在线 half-duplex 唤醒后等待超时，应出现一次退出提示播报。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备整机联网
2、发送语音“小美小美”，等待唤醒提示音播放，之后等待30s,Wakeup#talk#小美小美#，Action#sleep#20000#
3、听一下喇叭播放的内容
- 文档预期：1、喇叭播报“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、唤醒提示语播完后，若是打开空调的状态下，在关闭自然对话的情况下，等待15s后，会再播一次退出提示语，若是打开空调的状态下，当前打开自然对话的情况下，则根据之前云端配置的超时时间之后，会再播一次退出提示语；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_46 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 20000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_47 在线情况下的连续说唤醒词的功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒 -> 在线 -> 在线唤醒测试`。
- 重点验证 `唤醒词` 场景下“在线情况下的连续说唤醒词的功能”是否符合文档预期。
- 自动化接管说明：在线 half-duplex 连续三次唤醒后，最后一轮应仍能稳定进入并按时退出会话。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒 -> 在线 -> 在线唤醒测试`
- case_type：`唤醒词`
- 文档标题：`在线情况下的连续说唤醒词的功能`
- 自动化接管依据：在线 half-duplex 连续三次唤醒后，最后一轮应仍能稳定进入并按时退出会话。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备整机联网
2、发送语音“小美小美、小美小美、小美小美”，三句话的时间间隔小于2s，Wakeup#talk#小美小美#，Action#sleep#1000#，Wakeup#talk#小美小美#，Action#sleep#1000#，Wakeup#talk#小美小美#，Action#sleep#20000#，
3、听一下喇叭播放的内容
- 文档预期：1、喇叭顺序播报“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，播报三次，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、最后一次唤醒提示语播完后，若是打开空调的状态下，在关闭自然对话的情况下，等待15s后，会再播一次退出提示语，若是打开空调的状态下，当前打开自然对话的情况下，则根据之前云端配置的超时时间之后，会再播一次退出提示语；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_47 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> 唤醒词[talk]=小美小美 -> 静默 1000ms -> 唤醒词[talk]=小美小美 -> 静默 20000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `3` 次。
- COM14 `wakeup_callback` 至少 `3` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_50 在线情况下的识别测试

**摘要**
- 该用例位于 `语音交互能力 -> 语音识别 -> 在线 -> 在线技能交互应答测试`。
- 重点验证 `在线技能识别和应答音测试` 场景下“在线情况下的识别测试”是否符合文档预期。
- 自动化接管说明：在线闹钟技能应至少完成一次稳定识别，并返回云端播报结果。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音识别 -> 在线 -> 在线技能交互应答测试`
- case_type：`在线技能识别和应答音测试`
- 文档标题：`在线情况下的识别测试`
- 自动化接管依据：在线闹钟技能应至少完成一次稳定识别，并返回云端播报结果。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：举例：
1、将设备联网
2、发送语音“小美小美，帮我定个明天早上7点的闹钟”，Wakeup#talk#小美小美#，Action#sleep#1000#，online_Asr#talk#帮我定个明天早上7点的闹钟#，Action#sleep#5000#
3、听一下喇叭播放内容
其他的支持的在线通用技能都要测一遍,目前可使用工具自动交互测试；
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到在线命令词“帮我定个早上7点的闹钟”后，1s内，喇叭播报在线tts提示语“好的，已经帮你定好了明天早上7点的闹钟”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_50 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=帮我定个明天早上7点的闹钟 -> 静默 5000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 在线 ASR 文本必须包含：帮我定个明天早上七点的闹钟。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_114 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 30s 后，单次唤醒下连续三条在线空调指令都应可用。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 30s 后，单次唤醒下连续三条在线空调指令都应可用。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间30s
- 文档步骤：1、将设备联网
2、在手机app上，将自然对话打开,并设置超时时间30s
3、发送语音“小美小美，关闭空调，打开空调，制冷模式”，每句话的时间间隔小于30s，Wakeup#talk#小美小美#,Action#sleep#1000#,online_Asr#talk#关闭空调#，Action#sleep#5000#,online_Asr#talk#打开空调#,Action#sleep#5000#,online_Asr#talk#制冷模式#,Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、喇叭会顺序播报关闭空调、打开空调、调到制冷模式相关的三个提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_114 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=关闭空调 -> 静默 5000ms -> online_Asr[talk]=打开空调 -> 静默 5000ms -> online_Asr[talk]=制冷模式 -> 静默 5000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `3`。
- 识别关键词必须包含：kong tiao guan ji、kong tiao kai ji、zhi leng mo shi。
- AP 云端 TTS 播放至少 `3` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_115 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 30s 后，仅唤醒并等待 30s 应只播报一次超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 30s 后，仅唤醒并等待 30s 应只播报一次超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间30s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间30s
3、发送语音“小美小美”，等待30s,Wakeup#talk#小美小美#,Action#sleep#30000#
4、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、唤醒后等待30s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_115 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 30000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_116 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 30s 后，先说“打开空调”再等待 30s，应先有命令播报，再有超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 30s 后，先说“打开空调”再等待 30s，应先有命令播报，再有超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间30s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间30s
3、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#，online_Asr#talk#打开空调#，Action#sleep#30000#,
4、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到在线命令词“打开空调”，设备播报打开空调的在线tts提示语，当提示语播报完之后，再等待30s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_116 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> online_Asr[talk]=打开空调 -> 静默 30000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `2` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_117 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 20s 后，仅唤醒并等待 20s 应只播报一次超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 20s 后，仅唤醒并等待 20s 应只播报一次超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间20s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间20s
3、发送语音“小美小美”，等待20s,Wakeup#talk#小美小美#,Action#sleep#20000#
3、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待20s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_117 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 20000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_118 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 20s 后，先说“打开空调”再等待 20s，应先有命令播报，再有超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 20s 后，先说“打开空调”再等待 20s，应先有命令播报，再有超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间20s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间20s
3、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#，online_Asr#talk#打开空调#，Action#sleep#20000#,
4、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到在线命令词“打开空调”，设备播报打开空调的在线tts提示语，当提示语播报完之后，再等待20s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_118 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> online_Asr[talk]=打开空调 -> 静默 20000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `2` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_119 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 15s 后，仅唤醒并等待 15s 应只播报一次超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 15s 后，仅唤醒并等待 15s 应只播报一次超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间15s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间15s
3、发送语音“小美小美”，等待15s,Wakeup#talk#小美小美#,Action#sleep#15000#
3、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待15s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_119 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 15000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_120 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 15s 后，先说“打开空调”再等待 15s，应先有命令播报，再有超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 15s 后，先说“打开空调”再等待 15s，应先有命令播报，再有超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间15s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间15s
3、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#，online_Asr#talk#打开空调#，Action#sleep#15000#,
4、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到在线命令词“打开空调”，设备播报打开空调的在线tts提示语，当提示语播报完之后，再等待15s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_120 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> online_Asr[talk]=打开空调 -> 静默 15000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `2` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_121 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 10s 后，仅唤醒并等待 10s 应只播报一次超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 10s 后，仅唤醒并等待 10s 应只播报一次超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间10s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间10s
3、发送语音“小美小美”，等待10s,Wakeup#talk#小美小美#,Action#sleep#10000#
3、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待10s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_121 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_122 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 10s 后，先说“打开空调”再等待 10s，应先有命令播报，再有超时退出提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 10s 后，先说“打开空调”再等待 10s，应先有命令播报，再有超时退出提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间10s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间10s
3、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#，online_Asr#talk#打开空调#，Action#sleep#10000#,
4、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到在线命令词“打开空调”，设备播报打开空调的在线tts提示语，当提示语播报完之后，再等待10s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_122 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> online_Asr[talk]=打开空调 -> 静默 10000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `2` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_131 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 10s 后，等待超时再说“打开空调”不应继续识别。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 10s 后，等待超时再说“打开空调”不应继续识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间10s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间10s
3、发送语音“小美小美”，等待10s后，发送语音“打开空调”Wakeup#talk#小美小美#,Action#sleep#10000#，online_UnAsr#talk#打开空调#,
4、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、唤醒后等待10s，喇叭播报超时退出相关的提示音，语音“打开空调”，不识别也不进行喇叭播报

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_131 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10000ms -> online_UnAsr[talk]=打开空调
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_132 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话 15s 后，连续三条在线空调指令都应可识别并播报。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 打开自然对话 15s 后，连续三条在线空调指令都应可识别并播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间15s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间15s
3、发送语音“小美小美，关闭空调，打开空调，制冷模式”，每句话的时间间隔小于10s，Wakeup#talk#小美小美#,Action#sleep#1000#,online_Asr#talk#关闭空调#，Action#sleep#8000#,online_Asr#talk#打开空调#,Action#sleep#8000#,online_Asr#talk#制冷模式#,Action#sleep#8000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、命令词“关闭空调”、“打开空调”、“制冷模式”都可以正确识别，并且喇叭按顺序播报相关提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_132 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=关闭空调 -> 静默 8000ms -> online_Asr[talk]=打开空调 -> 静默 8000ms -> online_Asr[talk]=制冷模式 -> 静默 8000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `3`。
- 识别关键词必须包含：kong tiao guan ji、kong tiao kai ji、zhi leng mo shi。
- AP 云端 TTS 播放至少 `3` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_133 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 将自然对话最终配置为 20s 后，超时后再说“打开空调”不应继续识别。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 将自然对话最终配置为 20s 后，超时后再说“打开空调”不应继续识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间15s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间15s
3、发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep#5000#
4、在手机app上，将自然对话设置超时时间20s
5、发送语音“小美小美，打开空调”两句话间隔20s，Wakeup#talk#小美小美#,Action#sleep#20000#，online_UnAsr#talk#打开空调#Action#sleep#5000#
6、听一下喇叭播放的内容
7、步骤2到步骤5再次执行5次
- 文档预期：1、最后设置自然对话超时时间20s，等待20s后，喇叭播报超时退出的提示音，在说命令词“打开空调”不会识别命令词

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_133 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 5000ms -> 唤醒词[talk]=小美小美 -> 静默 20000ms -> online_UnAsr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_135 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：空调处于关机态时，full-duplex 10s 仅唤醒等待不应再播报超时提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：空调处于关机态时，full-duplex 10s 仅唤醒等待不应再播报超时提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，空调关机
2、在手机app上，将自然对话打开，超时时间设为10s
发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep#10000
3、听一下喇叭播放的内容
- 文档预期：1、自然对话被打开后并设置超时时间10s，空调关机情况下，等待10s后,不会播报超时提示语，且10s后再说指令词不会被识别

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_135 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放不超过 `0` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_137 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：空调处于关机态时，half-duplex 15s 仅唤醒等待不应再播报超时提示。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：空调处于关机态时，half-duplex 15s 仅唤醒等待不应再播报超时提示。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，空调关机
2、在手机app上，将自然对话关闭
发送语音“小美小美o”，Wakeup#talk#小美小美#,Action#sleep#15000
3、听一下喇叭播放的内容
- 文档预期：1、自然对话被关闭后，空调关机情况下，等待15s后,不会播报超时提示语，且15s后再说指令词不会被识别

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_137 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美
- 观察窗口=`8000` ms。
- 本次实际 setup 轨迹：
-   - action=cloud_mic_switch；success=True；enable=True；response_status=200；response_text={"result":{"returnData":{"msg":"成功","code":"0","data":{}}},"errorCode":"0"}；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\setup\00_ensure_mic_on
-   - action=cloud_full_duplex；success=True；enable=False；timeout_seconds=15；response_status=；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\setup\01_set_dialog_config
-   - action=voice_command_phrase；success=True；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\setup\01_02_prepare_voice_command
- 本次实际 recovery 轨迹：
-   - action=cloud_full_duplex；success=True；enable=False；timeout_seconds=15；response_status=；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\recovery\01_restore_half_duplex
- 播放返回码=`0`
- 音频文件=`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\audio\美的空调_137.wav`
- 主音频参数：duration_ms=`1266`；sample_rate=`16000`；channels=`1`；segments=`1`
- 主音频序列：tts:小美小美
- 播放片段：main_audio:0

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数不超过 `0`。
- AP 云端 TTS 播放不超过 `0` 次。

**本次实际判定检查表**

| 检查项 | actual | expected | 是否通过 |
| --- | --- | --- | --- |
| cloud_apply_success | `True` | `True` | `PASS` |
| cp_wake_count | `1` | `>=1` | `PASS` |
| ap_wake_count | `1` | `>=1` | `PASS` |
| successful_response_count | `0` | `>=0` | `PASS` |
| closure_prompt_count_reference | `1` | `reference-only` | `PASS` |
| closure_prompt_count_max | `1` | `<=0` | `FAIL` |

**当前结果 / FAIL 在哪里**
- 当前结果=`FAIL`。
- 判定原因：自然对话行为未满足 closure_prompt_count_max，actual=1 expected=<=0。
- 失败直接来自以下检查项：
-   - closure_prompt_count_max：actual=1；expected=<=0

**本次关键观测值**
- 关键计数：cp_wake_count=1；cp_command_count=0；ap_wake_count=1；wb_wake_count=0；wb_online_wake_count=1；ap_asr_count=0；wb_asr_count=0；ap_cloud_tts_play_count=0；ap_instruction_broadcast_count=1；wb_playback_start_count=0；wb_playback_end_count=0；unique_command_keyword_count=0；interrupt_reset_count=2；wake_during_playback_count=0；boot_marker_count=0；crash_marker_count=0
- 关键内容：ap_online_asr_texts=[""]；ap_instruction_broadcast_mids=["54e5cbbd-849c-4bbd-bdf4-cbbd15c8cbbd"]

**关键日志摘录**
- line_counts={"COM12": 8, "COM13": 375, "COM14": 367}
- wakeup_lines：
  - 2026-04-22T19:23:34.112 [COM12/cskcp] [C/I:65846571]WAKE(1): CHN=2, KEY=3(xiao mei xiao mei), NCM=-285
  - 2026-04-22T19:23:34.324 [COM14/cskap] [2026-04-22 19:23:32.410][O][evs_event # client] wakeup_callback, keyword: xiao mei xiao mei
  - 2026-04-22T19:23:34.436 [COM14/cskap] [2026-04-22 19:23:32.510][O][evs_event # client] multi_allow_wakeup_callback, cost 150ms

**证据路径**
- 执行目录：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137`
- judge：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\judge.json`
- result：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422192205581_doc_case_run_美的空调_137\doc_case_result.json`

### 美的空调_139 在线情况下使用手机app进行自然对话配置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置”是否符合文档预期。
- 自动化接管说明：APP 关闭自然对话后，首条“关闭空调”应识别播报，15s 后再说“打开空调”不应继续识别。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置`
- 自动化接管依据：APP 关闭自然对话后，首条“关闭空调”应识别播报，15s 后再说“打开空调”不应继续识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话关闭
发送语音“小美小美，关闭空调，打开空调”，每句命令词的时间间隔大于15s，Wakeup#talk#小美小美#,Action#sleep#1000#,online_Asr#talk#关闭空调#，Action#sleep#15000#,online_UnAsr#talk#打开空调#,Action#sleep5000#
3、听一下喇叭播放的内容
- 文档预期：1、自然对话被关闭后，命令词“关闭空调”可以正确识别，并且喇叭播报关闭空调相关的提示音，间隔15s后，喇叭不会播报超时提示音，命令词“打开空调”不识别，喇叭也不播报打开空调相关的提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_139 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_config_case`，runner_kind=`app_dialog_config_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先经云端/App 接口设置自然对话、超时或唤醒词等配置。
- 再播放文档里的在线探测音频，最后做 recovery。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> online_Asr[talk]=关闭空调 -> 静默 15000ms -> online_UnAsr[talk]=打开空调
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 唯一识别关键词数不超过 `1`。
- 识别关键词必须包含：kong tiao guan ji。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_dialog_persist_case

- runner 调度函数：`run_app_dialog_persist_case`
- 家族结果分布：`PASS 4 / FAIL 0 / BLOCKED 0`
- 先做自然对话配置。
- 再对 WB01 做硬重启，复机后跑持久化探测序列。

### 美的空调_681 在线关闭自然对话后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线关闭自然对话后掉电操作”是否符合文档预期。
- 自动化接管说明：APP 关闭自然对话后掉电重启，重启后应保持一次唤醒一次识别。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线关闭自然对话后掉电操作`
- 自动化接管依据：APP 关闭自然对话后掉电重启，重启后应保持一次唤醒一次识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app打开自然对话再关闭自然对话后，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
- 文档预期：1、上电后手机app上显示自然对话是关闭状态,交互电控控制时是一次唤醒一次识别控制指令，不能一次唤醒多次识别控制指令

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_681 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_persist_case`，runner_kind=`app_dialog_persist_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先做自然对话配置。
- 再对 WB01 做硬重启，复机后跑持久化探测序列。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 唯一识别关键词数不超过 `1`。
- 识别关键词必须包含：kong tiao guan ji。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_682 在线打开自然对话后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线打开自然对话后掉电操作”是否符合文档预期。
- 自动化接管说明：APP 打开自然对话后掉电重启，重启后应保持单次唤醒多轮识别。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线打开自然对话后掉电操作`
- 自动化接管依据：APP 打开自然对话后掉电重启，重启后应保持单次唤醒多轮识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app关闭自然对话再打开自然对话后，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
- 文档预期：1、上电后手机app上显示自然对话是打开状态,交互电控控制时是一次唤醒多次识别控制指令

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_682 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_persist_case`，runner_kind=`app_dialog_persist_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先做自然对话配置。
- 再对 WB01 做硬重启，复机后跑持久化探测序列。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `3`。
- 识别关键词必须包含：kong tiao guan ji、kong tiao kai ji、zhi leng mo shi。
- AP 云端 TTS 播放至少 `3` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_683 在线关闭自然对话后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线关闭自然对话后掉电操作”是否符合文档预期。
- 自动化接管说明：语音关闭自然对话后掉电重启，重启后应保持一次唤醒一次识别。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线关闭自然对话后掉电操作`
- 自动化接管依据：语音关闭自然对话后掉电重启，重启后应保持一次唤醒一次识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、唤醒后说：“打开自然对话”再唤醒说“关闭自然对话”后，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
- 文档预期：1、上电后手机app上显示自然对话是关闭状态,交互电控控制时是一次唤醒一次识别控制指令，不能一次唤醒多次识别控制指令

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_683 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_persist_case`，runner_kind=`app_dialog_persist_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先做自然对话配置。
- 再对 WB01 做硬重启，复机后跑持久化探测序列。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 唯一识别关键词数不超过 `1`。
- 识别关键词必须包含：kong tiao guan ji。
- AP 云端 TTS 播放至少 `1` 次。
- AP 云端 TTS 播放不超过 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_684 在线打开自然对话后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线打开自然对话后掉电操作”是否符合文档预期。
- 自动化接管说明：语音打开自然对话后掉电重启，重启后应保持单次唤醒多轮识别。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 自然对话配置`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线打开自然对话后掉电操作`
- 自动化接管依据：语音打开自然对话后掉电重启，重启后应保持单次唤醒多轮识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、唤醒后说：“关闭自然对话”再唤醒说“打开自然对话”后，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
- 文档预期：1、上电后手机app上显示自然对话是打开状态,交互电控控制时是一次唤醒多次识别控制指令

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_684 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_dialog_persist_case`，runner_kind=`app_dialog_persist_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先做自然对话配置。
- 再对 WB01 做硬重启，复机后跑持久化探测序列。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `3`。
- 识别关键词必须包含：kong tiao guan ji、kong tiao kai ji、zhi leng mo shi。
- AP 云端 TTS 播放至少 `3` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_mic_case

- runner 调度函数：`run_app_mic_case`
- 家族结果分布：`PASS 7 / FAIL 0 / BLOCKED 0`
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。

### 美的空调_52 在线情况下使用手机app进行语音开关设置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 语音开关`。
- 重点验证 `语音开关` 场景下“在线情况下使用手机app进行语音开关设置”是否符合文档预期。
- 自动化接管说明：APP 关闭语音后，单次唤醒不应触发 AP/WB 播报；10s 内连续 3 次唤醒应只播报一次 tone 417，11s 后再唤醒不应重复提醒。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 语音开关`
- case_type：`语音开关`
- 文档标题：`在线情况下使用手机app进行语音开关设置`
- 自动化接管依据：APP 关闭语音后，单次唤醒不应触发 AP/WB 播报；10s 内连续 3 次唤醒应只播报一次 tone 417，11s 后再唤醒不应重复提醒。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将语音开关关闭
3、语音关闭后，发送语音“小美小美”，尝试唤醒10次,
4、在10s内连续唤醒3次及以上"小美小美“，
5、说一次“小美小美”，10s后再说一次“小美小美”
6、听一下喇叭播放内容
- 文档预期：1、语音开关关闭后，电控会“叮”一声；
2、设备的语音交互被关闭，喇叭不播报任何内容,
3、在10s内，连续唤醒3次及以上，会播报“主人，当前语音功能已关闭，您可以使用遥控器或APP打开语音功能”
4、间隔10s后再说“小美小美”则不会有提醒播报

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_52 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`6000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `4` 次。
- COM14 `wakeup_callback` 不超过 `0` 次。
- COM13 `offline_wakeup` 不超过 `0` 次。
- COM14 离线 ASR 不超过 `0` 次。
- COM13 离线 ASR 不超过 `0` 次。
- COM13 `PLAYING` 至少 `1` 次。
- COM13 `PLAYING` 不超过 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 不超过 `1` 次。
- tone id 必须包含：417 (417_主人，当前语音功能已关闭，您可以使用遥控器或APP打开语音功能.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_53 在线情况下使用手机app进行语音开关设置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 语音开关`。
- 重点验证 `语音开关` 场景下“在线情况下使用手机app进行语音开关设置”是否符合文档预期。
- 自动化接管说明：APP 关闭语音后执行 WB01 掉电上电，重启后单次唤醒应仍只留 CP wake，不应恢复用户可感知播报。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 语音开关`
- case_type：`语音开关`
- 文档标题：`在线情况下使用手机app进行语音开关设置`
- 自动化接管依据：APP 关闭语音后执行 WB01 掉电上电，重启后单次唤醒应仍只留 CP wake，不应恢复用户可感知播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将语音开关关闭，之后将空调断电，等待几秒后再上电
3、语音关闭后，发送语音“小美小美”
4、听一下喇叭播放内容
- 文档预期：1、语音开关关闭后，会播报“语音已关闭”；
2、设备的语音交互被关闭，再次上电后，唤醒空调喇叭不播报任何内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_53 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`6000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 不超过 `0` 次。
- COM13 `offline_wakeup` 不超过 `0` 次。
- COM14 离线 ASR 不超过 `0` 次。
- COM13 离线 ASR 不超过 `0` 次。
- COM13 `PLAYING` 不超过 `0` 次。
- COM13 `PLAYBACK_COMPLETE` 不超过 `0` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_54 在线情况下使用手机app进行语音开关设置

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 语音开关`。
- 重点验证 `语音开关` 场景下“在线情况下使用手机app进行语音开关设置”是否符合文档预期。
- 自动化接管说明：APP 打开语音后，在线唤醒+打开空调应恢复正常交互，至少出现一次有效命令识别和云端 TTS 播放。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 语音开关`
- case_type：`语音开关`
- 文档标题：`在线情况下使用手机app进行语音开关设置`
- 自动化接管依据：APP 打开语音后，在线唤醒+打开空调应恢复正常交互，至少出现一次有效命令识别和云端 TTS 播放。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将语音开关打开
3、语音打开后，发送语音“小美小美、打开空调”，“小美小美，今天合肥的天气”等语音指令，尝试交互10次
4、听一下喇叭播放内容
- 文档预期：1、语音开关开启后，会播报“语音已开启”；
1、设备的语音交互打开，喇叭正常播报内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_54 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_55 在线情况下使用手机app进行语音开关设置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 语音开关`。
- 重点验证 `语音开关` 场景下“在线情况下使用手机app进行语音开关设置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 打开语音后断网，离线唤醒+打开空调仍应可用，且连续唤醒不应出现“语音已关闭”提醒 tone 417。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 语音开关`
- case_type：`语音开关`
- 文档标题：`在线情况下使用手机app进行语音开关设置，之后空调离线`
- 自动化接管依据：APP 打开语音后断网，离线唤醒+打开空调仍应可用，且连续唤醒不应出现“语音已关闭”提醒 tone 417。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将语音开关打开
3、设置完成后，将空调断网
4、语音打开后，发送语音“小美小美、打开空调”，“小美小美，今天合肥的天气”等语音指令，尝试交互10次
5、连续唤醒3次及以上，看下是否会触发语音已关闭的提醒
4、听一下喇叭播放内容
- 文档预期：1、语音开关开启后，会播报“语音已开启”；
2、设备的语音交互打开，喇叭正常播报内容，
3、连续唤醒3次及以上，不会出现播报"主人，当前语音功能已关闭，您可以使用遥控器或APP打开语音功能"的提醒

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_55 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`6000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `4` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)。
- tone id 不得包含：417 (417_主人，当前语音功能已关闭，您可以使用遥控器或APP打开语音功能.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_56 在线情况下使用手机app进行语音开关设置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 语音开关`。
- 重点验证 `语音开关` 场景下“在线情况下使用手机app进行语音开关设置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 关闭语音后先断网再执行 WB01 掉电上电，离线重启后单次唤醒仍不应恢复任何 AP/WB 播报。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 语音开关`
- case_type：`语音开关`
- 文档标题：`在线情况下使用手机app进行语音开关设置，之后空调离线`
- 自动化接管依据：APP 关闭语音后先断网再执行 WB01 掉电上电，离线重启后单次唤醒仍不应恢复任何 AP/WB 播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将语音开关关闭
3、设置完成后，将空调断网，之后将空调断电等待几秒后再上电
4、语音关闭后，发送语音“小美小美、打开空调”，“小美小美，今天合肥的天气”等语音指令
5、听一下喇叭播放内容
- 文档预期：1、语音开关关闭后，会播报“语音已关闭”；
2、设备的语音交互被关闭，再次上电后，唤醒空调喇叭不播报任何内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_56 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`6000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 不超过 `0` 次。
- COM13 `offline_wakeup` 不超过 `0` 次。
- COM14 离线 ASR 不超过 `0` 次。
- COM13 离线 ASR 不超过 `0` 次。
- COM13 `PLAYING` 不超过 `0` 次。
- COM13 `PLAYBACK_COMPLETE` 不超过 `0` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_677 在线语音开启后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 语音开关`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线语音开启后掉电操作”是否符合文档预期。
- 自动化接管说明：APP 先关再开语音后掉电重启，重启后在线唤醒+命令应恢复正常交互。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 语音开关`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线语音开启后掉电操作`
- 自动化接管依据：APP 先关再开语音后掉电重启，重启后在线唤醒+命令应恢复正常交互。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app关闭语音再打开语音后，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
- 文档预期：1、上电后语音是开启状态，唤醒识别响应正常

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_677 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- 唯一识别关键词数至少 `1`。
- 识别关键词必须包含：kong tiao kai ji。
- AP 云端 TTS 播放至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_678 在线语音关闭后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 语音开关`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线语音关闭后掉电操作”是否符合文档预期。
- 自动化接管说明：APP 先开再关语音后掉电重启，重启后单次唤醒仍应保持静默。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 语音开关`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线语音关闭后掉电操作`
- 自动化接管依据：APP 先开再关语音后掉电重启，重启后单次唤醒仍应保持静默。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app打开语音再关闭语音后，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
- 文档预期：1、上电后语音是关闭状态，唤醒识别无响应

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_678 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_mic_case`，runner_kind=`app_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先切在线语音开关。
- 必要时叠加断网/掉电，再播放探测序列。
- 观察窗口=`6000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 不超过 `0` 次。
- COM13 `offline_wakeup` 不超过 `0` 次。
- COM14 离线 ASR 不超过 `0` 次。
- COM13 离线 ASR 不超过 `0` 次。
- COM13 `PLAYING` 不超过 `0` 次。
- COM13 `PLAYBACK_COMPLETE` 不超过 `0` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_offline_timeout_case

- runner 调度函数：`run_app_offline_timeout_case`
- 家族结果分布：`PASS 8 / FAIL 0 / BLOCKED 0`
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。

### 美的空调_123 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 30s，再断网；离线仅唤醒后应播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 30s，再断网；离线仅唤醒后应播报超时退出提示音。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间30s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开，并设置超时时间30s
3、设置完成后，将空调断网
4、发送语音“小美小美”，等待30s,Wakeup#talk#小美小美#,Action#sleep#30000#
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待30s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_123 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 30000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- tone id 必须包含：287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_124 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 30s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 30s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间30s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开，并设置超时时间30s
3、设置完成后，将空调断网
4、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#,Asr#talk#打开空调#，Action#sleep#30000#,
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到离线命令词“打开空调”，设备播报打开空调的离线tts提示语，当提示语播报完之后，再等待30s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_124 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> Asr[talk]=打开空调 -> 静默 30000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- 识别关键词必须包含：kong tiao kai ji。
- COM13 `PLAYBACK_COMPLETE` 至少 `3` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)、287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_125 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 20s，再断网；离线仅唤醒后应播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 20s，再断网；离线仅唤醒后应播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间20s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开，并设置超时时间20s
3、设置完成后，将空调断网
4、发送语音“小美小美”，等待20s,Wakeup#talk#小美小美#,Action#sleep#20000#
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待20s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_125 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 20000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- tone id 必须包含：287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_126 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 20s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 20s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间20s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开，并设置超时时间20s
3、设置完成后，将空调断网
4、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#,Asr#talk#打开空调#，Action#sleep#20000#,
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到离线命令词“打开空调”，设备播报打开空调的离线tts提示语，当提示语播报完之后，再等待20s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_126 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> Asr[talk]=打开空调 -> 静默 20000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- 识别关键词必须包含：kong tiao kai ji。
- COM13 `PLAYBACK_COMPLETE` 至少 `3` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)、287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_127 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 15s，再断网；离线仅唤醒后应播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 15s，再断网；离线仅唤醒后应播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间15s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间15s
3、设置完成后，将空调断网
4、发送语音“小美小美”，等待15s,Wakeup#talk#小美小美#,Action#sleep#15000#
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待15s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_127 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 15000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- tone id 必须包含：287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_128 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 15s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 15s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间15s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开，并设置超时时间15s
3、设置完成后，将空调断网
4、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#,Asr#talk#打开空调#，Action#sleep#15000#,
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到离线命令词“打开空调”，设备播报打开空调的离线tts提示语，当提示语播报完之后，再等待15s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_128 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> Asr[talk]=打开空调 -> 静默 15000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- 识别关键词必须包含：kong tiao kai ji。
- COM13 `PLAYBACK_COMPLETE` 至少 `3` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)、287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_129 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 10s，再断网；离线仅唤醒后应播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 10s，再断网；离线仅唤醒后应播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间10s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开,并设置超时时间10s
3、设置完成后，将空调断网
4、发送语音“小美小美”，等待10s,Wakeup#talk#小美小美#,Action#sleep#10000#
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
1、唤醒后等待10s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_129 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- tone id 必须包含：287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_130 在线情况下使用手机app进行自然对话配置，之后空调离线

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 自然对话配置`。
- 重点验证 `自然对话配置` 场景下“在线情况下使用手机app进行自然对话配置，之后空调离线”是否符合文档预期。
- 自动化接管说明：APP 先打开自然对话并设超时 10s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 自然对话配置`
- case_type：`自然对话配置`
- 文档标题：`在线情况下使用手机app进行自然对话配置，之后空调离线`
- 自动化接管依据：APP 先打开自然对话并设超时 10s，再断网；离线唤醒+打开空调后应先播报命令结果，再播报超时退出提示音。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网，在手机app上，将自然对话打开,并设置超时时间10s
- 文档步骤：1、将设备联网，空调开机
2、在手机app上，将自然对话打开，并设置超时时间10s
3、设置完成后，将空调断网
4、发送语音“小美小美，打开空调”，Wakeup#talk#小美小美#,Action#sleep#2000#,Asr#talk#打开空调#，Action#sleep#10000#,
5、听一下喇叭播放的内容
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到离线命令词“打开空调”，设备播报打开空调的离线tts提示语，当提示语播报完之后，再等待10s，喇叭播报超时退出相关的提示音；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_130 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_offline_timeout_case`，runner_kind=`app_offline_timeout_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 在线完成配置后，切本机热点断网。
- 离线状态下播放探测音频验证超时/交互效果。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> Asr[talk]=打开空调 -> 静默 10000ms
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- 识别关键词必须包含：kong tiao kai ji。
- COM13 `PLAYBACK_COMPLETE` 至少 `3` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)、287 (287_先退下啦，有需要请再唤醒我哦.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_proactive_mic_case

- runner 调度函数：`run_app_proactive_mic_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 直接下发主动播报请求。
- 覆盖 mic off/on 与 interrupt/endSession 组合。

### 美的空调_58 在线情况下使用手机app进行语音关闭和开启之后，主动交互播报的情况

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在离线 -> 语音开关`。
- 重点验证 `语音开关` 场景下“在线情况下使用手机app进行语音关闭和开启之后，主动交互播报的情况”是否符合文档预期。
- 自动化接管说明：APP 语音关闭时 4 组主动交互都不应播报；重新打开语音后同 4 组主动交互都应恢复播报。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在离线 -> 语音开关`
- case_type：`语音开关`
- 文档标题：`在线情况下使用手机app进行语音关闭和开启之后，主动交互播报的情况`
- 自动化接管依据：APP 语音关闭时 4 组主动交互都不应播报；重新打开语音后同 4 组主动交互都应恢复播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在手机app上，将语音开关关闭
3、设置完成后，发送云端下发的主动交互（切到uat环境下操作），interrupt=False/Ture, endssion=False/Ture，四种组合都发送一遍
4、之后将手机app上的语音开关打开，再发送发送云端下发的主动交互（切到uat环境下操作），interrupt=False/Ture, endssion=False/Ture，四种组合都发送一遍
- 文档预期：1、语音开关关闭后，会播报“语音已关闭”；
2、在语音关闭情况下，发送主动交互，都不会播报；
3、打开语音之后，发送的主动交互，都正常播报；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_58 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_proactive_mic_case`，runner_kind=`app_proactive_mic_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 直接下发主动播报请求。
- 覆盖 mic off/on 与 interrupt/endSession 组合。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_threshold_case

- runner 调度函数：`run_app_threshold_case`
- 家族结果分布：`PASS 5 / FAIL 0 / BLOCKED 0`
- 先设置唤醒词与唤醒阈值。
- 再做双唤醒探测并检查 AP 的 threshold 日志。

### 美的空调_77 在线情况下使用手机app进行唤醒阈值调节

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`。
- 重点验证 `唤醒阈值调节` 场景下“在线情况下使用手机app进行唤醒阈值调节”是否符合文档预期。
- 自动化接管说明：APP 设置唤醒词为 小美小美、阈值请求为 0 后，语音 小美小美 的首次阈值应为 -73，同一会话内二次唤醒应出现识别态阈值 -308。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`
- case_type：`唤醒阈值调节`
- 文档标题：`在线情况下使用手机app进行唤醒阈值调节`
- 自动化接管依据：APP 设置唤醒词为 小美小美、阈值请求为 0 后，语音 小美小美 的首次阈值应为 -73，同一会话内二次唤醒应出现识别态阈值 -308。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，将唤醒词切换为“小美小美”
2、在手机app上，将唤醒灵敏度设为最低
3、发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep3000#查看日志的唤醒得分
Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".*#,Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".*#,Check#regex#.*threshold.*match.*\[(.*)\]#,Check#regex#.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*#
- 文档预期：1、S12机型，xiao mei xiao mei唤醒的首次唤醒阈值为-73，识别模式下的唤醒阈值为-308，且喇叭播报唤醒提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_77 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_threshold_case`，runner_kind=`app_threshold_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先设置唤醒词与唤醒阈值。
- 再做双唤醒探测并检查 AP 的 threshold 日志。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".* -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".* -> 日志检查[regex]=.*threshold.*match.*\[(.*)\] -> 日志检查[regex]=.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*
- 目标唤醒词=`小美小美`；恢复唤醒词=`小美小美`。
- 阈值设置=`0`；探测词=`小美小美`；双唤醒间隔=`1500` ms。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 阈值日志中的目标关键词必须是 `xiao mei xiao mei`。
- 阈值日志必须出现唤醒阈值 `-73`。
- 阈值日志必须出现识别阈值 `-308`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_78 在线情况下使用手机app进行唤醒阈值调节

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`。
- 重点验证 `唤醒阈值调节` 场景下“在线情况下使用手机app进行唤醒阈值调节”是否符合文档预期。
- 自动化接管说明：APP 设置唤醒词为 小美小美、阈值请求为 25 后，语音 小美小美 的首次阈值应为 -82，同一会话内二次唤醒应出现识别态阈值 -308。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`
- case_type：`唤醒阈值调节`
- 文档标题：`在线情况下使用手机app进行唤醒阈值调节`
- 自动化接管依据：APP 设置唤醒词为 小美小美、阈值请求为 25 后，语音 小美小美 的首次阈值应为 -82，同一会话内二次唤醒应出现识别态阈值 -308。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，将唤醒词切换为“小美小美”
2、在手机app上，将唤醒灵敏度设为低
3、发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep3000#查看日志的唤醒得分
Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".*#,Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".*#,Check#regex#.*threshold.*match.*\[(.*)\]#,Check#regex#.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*#
- 文档预期：1、S12机型，xiao mei xiao mei唤醒的首次唤醒阈值为-82，识别模式下的唤醒阈值为-308，且喇叭播报唤醒提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_78 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_threshold_case`，runner_kind=`app_threshold_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先设置唤醒词与唤醒阈值。
- 再做双唤醒探测并检查 AP 的 threshold 日志。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".* -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".* -> 日志检查[regex]=.*threshold.*match.*\[(.*)\] -> 日志检查[regex]=.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*
- 目标唤醒词=`小美小美`；恢复唤醒词=`小美小美`。
- 阈值设置=`25`；探测词=`小美小美`；双唤醒间隔=`1500` ms。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 阈值日志中的目标关键词必须是 `xiao mei xiao mei`。
- 阈值日志必须出现唤醒阈值 `-82`。
- 阈值日志必须出现识别阈值 `-308`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_79 在线情况下使用手机app进行唤醒阈值调节

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`。
- 重点验证 `唤醒阈值调节` 场景下“在线情况下使用手机app进行唤醒阈值调节”是否符合文档预期。
- 自动化接管说明：APP 设置唤醒词为 小美小美、阈值请求为 50 后，语音 小美小美 的首次阈值应为 -90，同一会话内二次唤醒应出现识别态阈值 -308。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`
- case_type：`唤醒阈值调节`
- 文档标题：`在线情况下使用手机app进行唤醒阈值调节`
- 自动化接管依据：APP 设置唤醒词为 小美小美、阈值请求为 50 后，语音 小美小美 的首次阈值应为 -90，同一会话内二次唤醒应出现识别态阈值 -308。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，，将唤醒词切换为“小美小美”
2、在手机app上，将唤醒灵敏度设为中
3、发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep3000#查看日志的唤醒得分
Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".*#,Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".*#,Check#regex#.*threshold.*match.*\[(.*)\]#,Check#regex#.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*#
- 文档预期：1、S12机型，xiao mei xiao mei唤醒的首次唤醒阈值为-90，识别模式下的唤醒阈值为-308，且喇叭播报唤醒提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_79 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_threshold_case`，runner_kind=`app_threshold_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先设置唤醒词与唤醒阈值。
- 再做双唤醒探测并检查 AP 的 threshold 日志。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".* -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".* -> 日志检查[regex]=.*threshold.*match.*\[(.*)\] -> 日志检查[regex]=.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*
- 目标唤醒词=`小美小美`；恢复唤醒词=`小美小美`。
- 阈值设置=`50`；探测词=`小美小美`；双唤醒间隔=`1500` ms。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 阈值日志中的目标关键词必须是 `xiao mei xiao mei`。
- 阈值日志必须出现唤醒阈值 `-90`。
- 阈值日志必须出现识别阈值 `-308`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_80 在线情况下使用手机app进行唤醒阈值调节

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`。
- 重点验证 `唤醒阈值调节` 场景下“在线情况下使用手机app进行唤醒阈值调节”是否符合文档预期。
- 自动化接管说明：APP 设置唤醒词为 小美小美、阈值请求为 75 后，语音 小美小美 的首次阈值应为 -100，同一会话内二次唤醒应出现识别态阈值 -308。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`
- case_type：`唤醒阈值调节`
- 文档标题：`在线情况下使用手机app进行唤醒阈值调节`
- 自动化接管依据：APP 设置唤醒词为 小美小美、阈值请求为 75 后，语音 小美小美 的首次阈值应为 -100，同一会话内二次唤醒应出现识别态阈值 -308。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，将唤醒词切换为“小美小美”
2、在手机app上，将唤醒灵敏度设为高
3、发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep3000#查看日志的唤醒得分
Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".*#,Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".*#,Check#regex#.*threshold.*match.*\[(.*)\]#,Check#regex#.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*#
- 文档预期：1、S12机型，xiao mei xiao mei唤醒的首次唤醒阈值为-100，识别模式下的唤醒阈值为-308，且喇叭播报唤醒提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_80 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_threshold_case`，runner_kind=`app_threshold_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先设置唤醒词与唤醒阈值。
- 再做双唤醒探测并检查 AP 的 threshold 日志。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".* -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".* -> 日志检查[regex]=.*threshold.*match.*\[(.*)\] -> 日志检查[regex]=.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*
- 目标唤醒词=`小美小美`；恢复唤醒词=`小美小美`。
- 阈值设置=`75`；探测词=`小美小美`；双唤醒间隔=`1500` ms。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 阈值日志中的目标关键词必须是 `xiao mei xiao mei`。
- 阈值日志必须出现唤醒阈值 `-100`。
- 阈值日志必须出现识别阈值 `-308`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_81 在线情况下使用手机app进行唤醒阈值调节

**摘要**
- 该用例位于 `云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`。
- 重点验证 `唤醒阈值调节` 场景下“在线情况下使用手机app进行唤醒阈值调节”是否符合文档预期。
- 自动化接管说明：APP 设置唤醒词为 小美小美、阈值请求为 100 后，语音 小美小美 的首次阈值应为 -109，同一会话内二次唤醒应出现识别态阈值 -308。

**要测试什么**
- 文档层级：`云端能力 -> 手机app -> 在线 -> 唤醒阈值调节`
- case_type：`唤醒阈值调节`
- 文档标题：`在线情况下使用手机app进行唤醒阈值调节`
- 自动化接管依据：APP 设置唤醒词为 小美小美、阈值请求为 100 后，语音 小美小美 的首次阈值应为 -109，同一会话内二次唤醒应出现识别态阈值 -308。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网，将唤醒词切换为“小美小美”
2、在手机app上，将唤醒灵敏度设为最高
3、发送语音“小美小美”，Wakeup#talk#小美小美#,Action#sleep3000#查看日志的唤醒得分
Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".*#,Check#regex#.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".*#,Check#regex#.*threshold.*match.*\[(.*)\]#,Check#regex#.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*#
- 文档预期：1、S12机型，xiao mei xiao mei唤醒的首次唤醒阈值为-109，识别模式下的唤醒阈值为-308，且喇叭播报唤醒提示音

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_81 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_threshold_case`，runner_kind=`app_threshold_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先设置唤醒词与唤醒阈值。
- 再做双唤醒探测并检查 AP 的 threshold 日志。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei3 xiao3 mei3".* -> 日志检查[regex]=.*algo info: .*\"ncm\":(.*),.*\"keyword\":"xiao3 mei4 xiao3 mei4".* -> 日志检查[regex]=.*threshold.*match.*\[(.*)\] -> 日志检查[regex]=.*\"ncmThreshold\":(.*),\"keyword\":\"xiao mei xiao mei\".*
- 目标唤醒词=`小美小美`；恢复唤醒词=`小美小美`。
- 阈值设置=`100`；探测词=`小美小美`；双唤醒间隔=`1500` ms。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 阈值日志中的目标关键词必须是 `xiao mei xiao mei`。
- 阈值日志必须出现唤醒阈值 `-109`。
- 阈值日志必须出现识别阈值 `-308`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## app_threshold_persist_case

- runner 调度函数：`run_app_threshold_persist_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 先做阈值配置再掉电。
- 复机后继续检查 threshold 日志是否保持。

### 美的空调_686 在线唤醒词唤醒阈值调节后掉电操作

**摘要**
- 该用例位于 `掉电测试 -> 掉电测试 -> 在线 -> 唤醒阈值调节`。
- 重点验证 `功能设置后掉电的操作` 场景下“在线唤醒词唤醒阈值调节后掉电操作”是否符合文档预期。
- 自动化接管说明：APP 先把唤醒阈值切到最高再切到最低并掉电重启，重启后最低阈值应保留并继续生效。

**要测试什么**
- 文档层级：`掉电测试 -> 掉电测试 -> 在线 -> 唤醒阈值调节`
- case_type：`功能设置后掉电的操作`
- 文档标题：`在线唤醒词唤醒阈值调节后掉电操作`
- 自动化接管依据：APP 先把唤醒阈值切到最高再切到最低并掉电重启，重启后最低阈值应保留并继续生效。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、手机app上设置唤醒阈值为最高，再设置为最低，立刻断电上电，
2、上电后唤醒+识别交互几下，观察响应情况
3、有几个阈值就反复切换几次
- 文档预期：1、上电后手机app上的唤醒阈值是最低
2、掉电前切换的阈值掉电后还是这个切换的阈值

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_686 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_app_threshold_persist_case`，runner_kind=`app_threshold_persist_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先做阈值配置再掉电。
- 复机后继续检查 threshold 日志是否保持。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM14 `wakeup_callback` 至少 `2` 次。
- 阈值日志中的目标关键词必须是 `xiao mei xiao mei`。
- 阈值日志必须出现唤醒阈值 `-73`。
- 阈值日志必须出现识别阈值 `-308`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## cloud_log_upload_probe_case

- runner 调度函数：`run_cloud_log_upload_probe_case`
- 家族结果分布：`PASS 0 / FAIL 0 / BLOCKED 5`
- 先清本地 loglev/console，再发云端日志上传请求。
- 随后播放“现在几点了”探测日志等级是否真正生效。

### 美的空调_709 在线情况下发送日志上传相关的post请求

**摘要**
- 该用例位于 `云端能力 -> post请求 -> 在线 -> 日志上传`。
- 重点验证 `测试日志上传` 场景下“在线情况下发送日志上传相关的post请求”是否符合文档预期。
- 自动化接管说明：在线将云端日志上传等级切到 debug 后，本地应看到 `set device loglev 4 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**要测试什么**
- 文档层级：`云端能力 -> post请求 -> 在线 -> 日志上传`
- case_type：`测试日志上传`
- 文档标题：`在线情况下发送日志上传相关的post请求`
- 自动化接管依据：在线将云端日志上传等级切到 debug 后，本地应看到 `set device loglev 4 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在csk-ap端输入：flash show 若显示了有设置日志等级，使用flash clear log_lev的命令去掉设置的日志等级，以及使用flash clear console的命令去掉日志等级重启保留，Action#shell#flash clear log_lev#，Action#shell#flash clear console#
2、使用post工具，发送日志上传的请求：
post请求地址：https://uat.aimidea.cn:11003/v1/base2pro/data/transmit
请求参数：
serviceUrl=/v1/device/log/set
data={"deviceId":"208907215507085","logLevel":7,"status":"1"}
参数将日志等级设置为7，代表上传debug等级的日志，包括 debug -> AI SDK (debug)，NET (info)，APP (debug)、SYS (debug)、Player (debug)
deviceId在csk-ap端输入：deviceinfo 的指令，获取到IOT-id就是deviceId
3、日志上传请求发送后，返回success,本地的csk-ap日志会打印“set device loglev 4 by cloud_change”之后与电控进行几轮语音交互，找美的客户技术人员去捞云端日志
- 文档预期：1、将云端的日志与本地的csk-ap的日志进行一致性对比，云端日志没有丢掉内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_709 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_cloud_log_upload_probe_case`，runner_kind=`cloud_log_upload_probe_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先清本地 loglev/console，再发云端日志上传请求。
- 随后播放“现在几点了”探测日志等级是否真正生效。
- 文档 token / 语音输入序列：串口命令 `flash clear log_lev` -> 串口命令 `flash clear console`
- 探测轮数=`2`。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- AP 必须打印目标设备日志等级 `4` 的生效证据。
- 额外检查：云请求必须 business success，且 AP 必须打印目标 log level 生效，再通过探测语音拿到 wake + cloud TTS 证据。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`BLOCKED`。
- 该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_710 在线情况下发送日志上传相关的post请求

**摘要**
- 该用例位于 `云端能力 -> post请求 -> 在线 -> 日志上传`。
- 重点验证 `测试日志上传` 场景下“在线情况下发送日志上传相关的post请求”是否符合文档预期。
- 自动化接管说明：在线将云端日志上传等级切到 info 后，本地应看到 `set device loglev 3 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**要测试什么**
- 文档层级：`云端能力 -> post请求 -> 在线 -> 日志上传`
- case_type：`测试日志上传`
- 文档标题：`在线情况下发送日志上传相关的post请求`
- 自动化接管依据：在线将云端日志上传等级切到 info 后，本地应看到 `set device loglev 3 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在csk-ap端输入：flash show 若显示了有设置日志等级，使用flash clear log_lev的命令去掉设置的日志等级，以及使用flash clear console的命令去掉日志等级重启保留
2、使用post工具，发送日志上传的请求：
post请求地址：https://uat.aimidea.cn:11003/v1/base2pro/data/transmit
请求参数：
serviceUrl=/v1/device/log/set
data={"deviceId":"208907215507085","logLevel":6,"status":"1"}
参数将日志等级设置为6，代表上传info等级的日志，包括info -> AI SDK (info)，NET (info)，APP (info)、SYS (info)、Player (info)
deviceId在csk-ap端输入：deviceinfo 的指令，获取到IOT-id就是deviceId
3、日志上传请求发送后，返回success,本地的csk-ap日志会打印“set device loglev 3 by cloud_change”之后与电控进行几轮语音交互，找美的客户技术人员去捞云端日志
- 文档预期：1、将云端的日志与本地的csk-ap的日志进行一致性对比，云端日志没有丢掉内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_710 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_cloud_log_upload_probe_case`，runner_kind=`cloud_log_upload_probe_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先清本地 loglev/console，再发云端日志上传请求。
- 随后播放“现在几点了”探测日志等级是否真正生效。
- 探测轮数=`2`。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- AP 必须打印目标设备日志等级 `3` 的生效证据。
- 额外检查：云请求必须 business success，且 AP 必须打印目标 log level 生效，再通过探测语音拿到 wake + cloud TTS 证据。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`BLOCKED`。
- 该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_711 在线情况下发送日志上传相关的post请求

**摘要**
- 该用例位于 `云端能力 -> post请求 -> 在线 -> 日志上传`。
- 重点验证 `测试日志上传` 场景下“在线情况下发送日志上传相关的post请求”是否符合文档预期。
- 自动化接管说明：在线将云端日志上传等级切到 warning 后，本地应看到 `set device loglev 2 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**要测试什么**
- 文档层级：`云端能力 -> post请求 -> 在线 -> 日志上传`
- case_type：`测试日志上传`
- 文档标题：`在线情况下发送日志上传相关的post请求`
- 自动化接管依据：在线将云端日志上传等级切到 warning 后，本地应看到 `set device loglev 2 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在csk-ap端输入：flash show 若显示了有设置日志等级，使用flash clear log_lev的命令去掉设置的日志等级，以及使用flash clear console的命令去掉日志等级重启保留
2、使用post工具，发送日志上传的请求：
post请求地址：https://uat.aimidea.cn:11003/v1/base2pro/data/transmit
请求参数：
serviceUrl=/v1/device/log/set
data={"deviceId":"208907215507085","logLevel":4,"status":"1"}
参数将日志等级设置为4，代表上传warning等级的日志，包括warning -> AI SDK (warning)，NET (warning)，APP (warning)、SYS (warning)、Player (warning)
deviceId在csk-ap端输入：deviceinfo 的指令，获取到IOT-id就是deviceId
3、日志上传请求发送后，返回success,本地的csk-ap日志会打印“set device loglev 2 by cloud_change”之后与电控进行几轮语音交互，找美的客户技术人员去捞云端日志
- 文档预期：1、将云端的日志与本地的csk-ap的日志进行一致性对比，云端日志没有丢掉内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_711 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_cloud_log_upload_probe_case`，runner_kind=`cloud_log_upload_probe_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先清本地 loglev/console，再发云端日志上传请求。
- 随后播放“现在几点了”探测日志等级是否真正生效。
- 探测轮数=`2`。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- AP 必须打印目标设备日志等级 `2` 的生效证据。
- 额外检查：云请求必须 business success，且 AP 必须打印目标 log level 生效，再通过探测语音拿到 wake + cloud TTS 证据。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`BLOCKED`。
- 该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_712 在线情况下发送日志上传相关的post请求

**摘要**
- 该用例位于 `云端能力 -> post请求 -> 在线 -> 日志上传`。
- 重点验证 `测试日志上传` 场景下“在线情况下发送日志上传相关的post请求”是否符合文档预期。
- 自动化接管说明：在线将云端日志上传等级切到 error 后，本地应看到 `set device loglev 1 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**要测试什么**
- 文档层级：`云端能力 -> post请求 -> 在线 -> 日志上传`
- case_type：`测试日志上传`
- 文档标题：`在线情况下发送日志上传相关的post请求`
- 自动化接管依据：在线将云端日志上传等级切到 error 后，本地应看到 `set device loglev 1 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、在csk-ap端输入：flash show 若显示了有设置日志等级，使用flash clear log_lev的命令去掉设置的日志等级，以及使用flash clear console的命令去掉日志等级重启保留
2、使用post工具，发送日志上传的请求：
post请求地址：https://uat.aimidea.cn:11003/v1/base2pro/data/transmit
请求参数：
serviceUrl=/v1/device/log/set
data={"deviceId":"208907215507085","logLevel":3,"status":"1"}
参数将日志等级设置为3，代表上传error 等级的日志，包括 error -> AI SDK (error)，NET (error)，APP (error)、SYS (error)、Player (error)
deviceId在csk-ap端输入：deviceinfo 的指令，获取到IOT-id就是deviceId
3、日志上传请求发送后，返回success,本地的csk-ap日志会打印“set device loglev 1 by cloud_change”之后与电控进行几轮语音交互，找美的客户技术人员去捞云端日志
- 文档预期：1、将云端的日志与本地的csk-ap的日志进行一致性对比，云端日志没有丢掉内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_712 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_cloud_log_upload_probe_case`，runner_kind=`cloud_log_upload_probe_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先清本地 loglev/console，再发云端日志上传请求。
- 随后播放“现在几点了”探测日志等级是否真正生效。
- 探测轮数=`2`。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- AP 必须打印目标设备日志等级 `1` 的生效证据。
- 额外检查：云请求必须 business success，且 AP 必须打印目标 log level 生效，再通过探测语音拿到 wake + cloud TTS 证据。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`BLOCKED`。
- 该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_713 在线情况下发送日志上传相关的post请求

**摘要**
- 该用例位于 `云端能力 -> post请求 -> 在线 -> 日志上传`。
- 重点验证 `测试日志上传` 场景下“在线情况下发送日志上传相关的post请求”是否符合文档预期。
- 自动化接管说明：在线恢复默认日志上传配置后，本地应看到 `set device loglev 1 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**要测试什么**
- 文档层级：`云端能力 -> post请求 -> 在线 -> 日志上传`
- case_type：`测试日志上传`
- 文档标题：`在线情况下发送日志上传相关的post请求`
- 自动化接管依据：在线恢复默认日志上传配置后，本地应看到 `set device loglev 1 by cloud_change`，并能继续完成在线语音交互；最终仍需云端日志回捞才能判 PASS。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、使用post工具，发送日志上传的请求：
post请求地址：https://uat.aimidea.cn:11003/v1/base2pro/data/transmit
请求参数：
serviceUrl=/v1/device/log/set
data={"deviceId":"208907215507085","logLevel":7,"status":"0"}
参数status为0，代表 清除之前设置的日志等级记录，恢复默认
deviceId在csk-ap端输入：deviceinfo 的指令，获取到IOT-id就是deviceId
3、日志上传请求发送后，返回success,本地的csk-ap日志会打印“set device loglev 1 by cloud_change”之后与电控进行几轮语音交互，找美的客户技术人员去捞云端日志
- 文档预期：1、将云端的日志与本地的csk-ap的日志进行一致性对比，云端日志没有丢掉内容

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_713 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_cloud_log_upload_probe_case`，runner_kind=`cloud_log_upload_probe_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先清本地 loglev/console，再发云端日志上传请求。
- 随后播放“现在几点了”探测日志等级是否真正生效。
- 探测轮数=`2`。
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- AP 必须打印目标设备日志等级 `1` 的生效证据。
- 额外检查：云请求必须 business success，且 AP 必须打印目标 log level 生效，再通过探测语音拿到 wake + cloud TTS 证据。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`BLOCKED`。
- 该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## dialog_phase_case

- runner 调度函数：`run_dialog_phase_case / run_offline_dialog_phase_case`
- 家族结果分布：`PASS 11 / FAIL 0 / BLOCKED 0`
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

### 美的空调_298 离线情况下半双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`。
- 重点验证 `半双工交互` 场景下“离线情况下半双工交互功能”是否符合文档预期。
- 自动化接管说明：离线半双工：关闭自然对话后，验证空调开机时有超时播报、关机时无超时播报。

**要测试什么**
- 文档层级：`半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`
- case_type：`半双工交互`
- 文档标题：`离线情况下半双工交互功能`
- 自动化接管依据：离线半双工：关闭自然对话后，验证空调开机时有超时播报、关机时无超时播报。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），关闭自然对话”，
3、关闭自然对话后，先将空调开机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，堵住麦克风，中间没有人说话，等待15s
4、关闭自然对话后，先将空调关机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，堵住麦克风，中间没有人说话，等待15s
- 文档预期：1、识别到“关闭自然对话”结果正常，之后设备播报提示语“连续对话已关闭，现在每次对话都需要先唤醒我哦”
2、空调开机的情况下，再次唤醒后，等待15s中间没有人说话，设备播放超时提示语“先退下啦，有需要请再唤醒我哦”
3、空调关机的情况下，再次唤醒后，等待15s中间没有人说话，设备不会播报超时提示语

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_298 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_299 离线情况下半双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`。
- 重点验证 `半双工交互` 场景下“离线情况下半双工交互功能”是否符合文档预期。
- 自动化接管说明：离线半双工：关闭自然对话后，验证 3 次及以上非空调人声时的兜底+超时逻辑。

**要测试什么**
- 文档层级：`半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`
- case_type：`半双工交互`
- 文档标题：`离线情况下半双工交互功能`
- 自动化接管依据：离线半双工：关闭自然对话后，验证 3 次及以上非空调人声时的兜底+超时逻辑。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），关闭自然对话”，
3、关闭自然对话后，先将空调开机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以及3次以上，不是任何空调的指令词
4、关闭自然对话后，先将空调关机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以及3次以上，不是任何空调的指令词
- 文档预期：1、识别到“关闭自然对话”结果正常，之后设备播报提示语“连续对话已关闭，现在每次对话都需要先唤醒我哦”
2、空调开机的情况下，再次唤醒后，等待15s中间有人说话，且VAD检测人声3次以及3次以上，设备会先播报“你说的指令暂不支持”，之后再播放超时提示语“先退下啦，有需要请再唤醒我哦”
3、空调关机的情况下，再次唤醒后，等待15s中间有人说话，且VAD检测人声3次以及3次以上，设备不会播放兜底提示语和超时提示语；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_299 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_300 离线情况下半双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`。
- 重点验证 `半双工交互` 场景下“离线情况下半双工交互功能”是否符合文档预期。
- 自动化接管说明：离线半双工：关闭自然对话后，验证少量非空调人声时直接超时的逻辑。

**要测试什么**
- 文档层级：`半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`
- case_type：`半双工交互`
- 文档标题：`离线情况下半双工交互功能`
- 自动化接管依据：离线半双工：关闭自然对话后，验证少量非空调人声时直接超时的逻辑。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），关闭自然对话”，
3、关闭自然对话后，先将空调开机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以下，不是任何空调的指令词
4、关闭自然对话后，先将空调关机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以下，不是任何空调的指令词
- 文档预期：1、识别到“关闭自然对话”结果正常，之后设备播报提示语“连续对话已关闭，现在每次对话都需要先唤醒我哦”
2、空调开机情况下，再次唤醒后，等待15s中间有人说话，且VAD检测人声3次以下，设备到超时15s后，会直接播放超时提示语“先退下啦，有需要请再唤醒我哦”
3、空调关机情况下，再次唤醒后，等待15s中间有人说话，且VAD检测人声3次以下，设备到超时15s后，不会播报超时提示语

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_300 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_301 离线情况下半双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`。
- 重点验证 `半双工交互` 场景下“离线情况下半双工交互功能”是否符合文档预期。
- 自动化接管说明：离线半双工：同一会话多条指令仅第一条应生效。

**要测试什么**
- 文档层级：`半/全双工交互 -> 半双工交互 -> 离线 -> 半双工交互`
- case_type：`半双工交互`
- 文档标题：`离线情况下半双工交互功能`
- 自动化接管依据：离线半双工：同一会话多条指令仅第一条应生效。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），关闭自然对话”，
3、关闭自然对话后，再对设备说“小美小美（或目前支持的唤醒词），开机，关机，制冷模式”，开机、关机、制冷模式三句话中间需要等2s以上
- 文档预期：1、识别到“关闭自然对话”结果正常，之后设备播报提示语“连续对话已关闭，现在每次对话都需要先唤醒我哦”
2、再次交互，只识别第一个指令词“开机”，并且空调执行开机的动作和反馈已开机的提示语，后面说的关机和制冷模式有识别结果但没有任何响应
3、识别到“开机”之后，等待15s后，不会播报超时提示语

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_301 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_302 离线情况下全双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 全双工交互 -> 离线 -> 全双工交互`。
- 重点验证 `全双工交互` 场景下“离线情况下全双工交互功能”是否符合文档预期。
- 自动化接管说明：离线全双工：打开自然对话后，验证空调开机时有超时播报、关机时无超时播报。

**要测试什么**
- 文档层级：`半/全双工交互 -> 全双工交互 -> 离线 -> 全双工交互`
- case_type：`全双工交互`
- 文档标题：`离线情况下全双工交互功能`
- 自动化接管依据：离线全双工：打开自然对话后，验证空调开机时有超时播报、关机时无超时播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），打开自然对话”，
3、打开自然对话后，先将空调开机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，堵住麦克风，中间没有人说话，等待15s
4、打开自然对话后，先将空调关机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，堵住麦克风，中间没有人说话，等待15s
- 文档预期：1、识别到“打开自然对话”结果正常，之后设备播报提示语“连续对话已打开，现在只要唤醒我一次就可以连续对话啦”
2、空调开机的情况下，再次唤醒后，等待15s中间没有人说话，设备播放超时提示语“先退下啦，有需要请再唤醒我哦”
3、空调关机的情况下，再次唤醒后，等待15s中间没有人说话，设备不会播放超时提示语

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_302 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_303 离线情况下全双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 全双工交互 -> 离线 -> 全双工交互`。
- 重点验证 `全双工交互` 场景下“离线情况下全双工交互功能”是否符合文档预期。
- 自动化接管说明：离线全双工：打开自然对话后，验证 3 次及以上非空调人声时的兜底+超时逻辑。

**要测试什么**
- 文档层级：`半/全双工交互 -> 全双工交互 -> 离线 -> 全双工交互`
- case_type：`全双工交互`
- 文档标题：`离线情况下全双工交互功能`
- 自动化接管依据：离线全双工：打开自然对话后，验证 3 次及以上非空调人声时的兜底+超时逻辑。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），打开自然对话”，
3、打开自然对话后，先将空调开机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以及3次以上，不是任何空调的指令词
4、打开自然对话后，先将空调关机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以及3次以上，不是任何空调的指令词
- 文档预期：1、识别到“打开自然对话”结果正常，之后设备播报提示语“连续对话已打开，现在只要唤醒我一次就可以连续对话啦”
2、空调开机的情况下，再次唤醒后，等待15s中间有人说话，，且VAD检测人声3次以及3次以上，设备会先播报“你说的指令暂不支持”，之后再播放超时提示语“先退下啦，有需要请再唤醒我哦”
3、空调关机的情况下，再次唤醒后，等待15s中间有人说话，，且VAD检测人声3次以及3次以上，设备不会播报兜底回复语和超时提示语

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_303 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_304 离线情况下全双工交互功能

**摘要**
- 该用例位于 `半/全双工交互 -> 全双工交互 -> 离线 -> 全双工交互`。
- 重点验证 `全双工交互` 场景下“离线情况下全双工交互功能”是否符合文档预期。
- 自动化接管说明：离线全双工：打开自然对话后，验证少量非空调人声时直接超时的逻辑。

**要测试什么**
- 文档层级：`半/全双工交互 -> 全双工交互 -> 离线 -> 全双工交互`
- case_type：`全双工交互`
- 文档标题：`离线情况下全双工交互功能`
- 自动化接管依据：离线全双工：打开自然对话后，验证少量非空调人声时直接超时的逻辑。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备断网
2、对设备说“小美小美（或目前支持的唤醒词），打开自然对话”，
3、打开自然对话后，先将空调开机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以下，不是任何空调的指令词
4、打开自然对话后，先将空调关机，之后再唤醒设备说“小美小美（或目前支持的唤醒词）”，等待15s，中间有人说话，且VAD检测人声3次以下，不是任何空调的指令词
- 文档预期：1、识别到“打开自然对话”结果正常，之后设备播报提示语“连续对话已打开，现在只要唤醒我一次就可以连续对话啦”
2、空调开机的情况下，再次唤醒后，等待15s中间有人说话，，且VAD检测人声3次以下，设备到超时15s后，会直接播放超时提示语“先退下啦，有需要请再唤醒我哦”
3、空调关机的情况下，再次唤醒后，等待15s中间有人说话，，且VAD检测人声3次以下，设备到超时15s后，不会播放超时提示语

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_304 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_311 离线情况下全双工切换到半双工交互状态立即生效

**摘要**
- 该用例位于 `半/全双工交互 -> 全双工切换到半双工交互状态立即生效 -> 离线 -> 全双工切换到半双工交互状态立即生效`。
- 重点验证 `全双工切换到半双工交互状态立即生效` 场景下“离线情况下全双工切换到半双工交互状态立即生效”是否符合文档预期。
- 自动化接管说明：离线全双工切半双工：关闭自然对话后，后续同一句里的打开空调不应再识别。

**要测试什么**
- 文档层级：`半/全双工交互 -> 全双工切换到半双工交互状态立即生效 -> 离线 -> 全双工切换到半双工交互状态立即生效`
- case_type：`全双工切换到半双工交互状态立即生效`
- 文档标题：`离线情况下全双工切换到半双工交互状态立即生效`
- 自动化接管依据：离线全双工切半双工：关闭自然对话后，后续同一句里的打开空调不应再识别。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：1、设备断网，对设备说“小美小美（或目前支持的唤醒词），打开自然对话”，设备提示自然对话已打开，进入了全双工模式
2、在全双工模式下，对设备说“小美小美（或目前支持的唤醒词），关闭自然对话，打开空调”
- 文档预期：1、设备在全双工模式下，识别到“关闭自然对话”的命令词后，播报已关闭自然对话的提示语，之后的“打开空调”则不识别

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_311 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_312 离线情况下半双工切换到全双工交互状态不立即生效

**摘要**
- 该用例位于 `半/全双工交互 -> 半双工切换到全双工交互状态不立即生效 -> 离线 -> 半双工切换到全双工交互状态不立即生效`。
- 重点验证 `半双工切换到全双工交互状态不立即生效` 场景下“离线情况下半双工切换到全双工交互状态不立即生效”是否符合文档预期。
- 自动化接管说明：离线半双工切全双工：打开自然对话后，后续同一句里的打开空调不应在当句立即生效。

**要测试什么**
- 文档层级：`半/全双工交互 -> 半双工切换到全双工交互状态不立即生效 -> 离线 -> 半双工切换到全双工交互状态不立即生效`
- case_type：`半双工切换到全双工交互状态不立即生效`
- 文档标题：`离线情况下半双工切换到全双工交互状态不立即生效`
- 自动化接管依据：离线半双工切全双工：打开自然对话后，后续同一句里的打开空调不应在当句立即生效。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：1、设备断网，对设备说“小美小美（或目前支持的唤醒词），关闭自然对话”，设备提示自然对话已关闭，进入了半双工模式
2、在半双工模式下，对设备说“小美小美（或目前支持的唤醒词），打开自然对话，打开空调”
- 文档预期：1、设备在半双工模式下，识别到“打开自然对话”的命令词后，播报已打开自然对话的提示语，但之后的“打开空调”不会识别

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_312 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_613 未联网情况下的语音交互压测

**摘要**
- 该用例位于 `语音交互压测 -> 离线语音交互压测 -> 离线 -> 未联网`。
- 重点验证 `交互压测` 场景下“未联网情况下的语音交互压测”是否符合文档预期。
- 自动化接管说明：未联网+自然对话打开的离线语音交互压测：执行多轮随机间隔的唤醒+空调命令，校验不重启、不死机、链路持续可用。

**要测试什么**
- 文档层级：`语音交互压测 -> 离线语音交互压测 -> 离线 -> 未联网`
- case_type：`交互压测`
- 文档标题：`未联网情况下的语音交互压测`
- 自动化接管依据：未联网+自然对话打开的离线语音交互压测：执行多轮随机间隔的唤醒+空调命令，校验不重启、不死机、链路持续可用。

**文档原始信息**
- 优先级：`P2`
- 前置条件：设备未联网，自然对话打开
- 文档步骤：1、使用空调控制的命令词进行交互压测，每次唤醒和识别的间隔时间随机
- 文档预期：1、设备不会出现异常重启、死机、喇叭不出声、连续不识别、连续无法唤醒等异常功能性问题

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_613 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。
- 压测参数：scenario=`stress_interaction`；cycles=`8`；seed=`613`。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_614 未联网情况下的语音交互压测

**摘要**
- 该用例位于 `语音交互压测 -> 离线语音交互压测 -> 离线 -> 未联网`。
- 重点验证 `交互压测` 场景下“未联网情况下的语音交互压测”是否符合文档预期。
- 自动化接管说明：未联网+自然对话关闭的离线语音交互压测：执行多轮随机间隔的唤醒+空调命令，校验不重启、不死机、链路持续可用。

**要测试什么**
- 文档层级：`语音交互压测 -> 离线语音交互压测 -> 离线 -> 未联网`
- case_type：`交互压测`
- 文档标题：`未联网情况下的语音交互压测`
- 自动化接管依据：未联网+自然对话关闭的离线语音交互压测：执行多轮随机间隔的唤醒+空调命令，校验不重启、不死机、链路持续可用。

**文档原始信息**
- 优先级：`P2`
- 前置条件：设备未联网，自然对话关闭
- 文档步骤：1、使用空调控制的命令词进行交互压测，每次唤醒和识别的间隔时间随机
- 文档预期：1、设备不会出现异常重启、死机、喇叭不出声、连续不识别、连续无法唤醒等异常功能性问题

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_614 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_dialog_phase_case / run_offline_dialog_phase_case`，runner_kind=`dialog_phase_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按照 phase 计划逐段执行，每个 phase 都独立产出 metrics 与 checks。
- 最终再汇总 phase 结果生成整条 case 的结论。
- 压测参数：scenario=`stress_interaction`；cycles=`8`；seed=`614`。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## network_disconnect_case

- runner 调度函数：`run_network_disconnect_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 通过本机热点断网。
- 直接判断断网窗口内 AP/WB 的断连状态码。

### 美的空调_585 AI云未连接状态的返回码测试

**摘要**
- 该用例位于 `状态返回确认测试 -> AI云未连接状态 -> 在线 -> AI云未连接状态信息给上位机`。
- 重点验证 `状态返回确认测试` 场景下“AI云未连接状态的返回码测试”是否符合文档预期。
- 自动化接管说明：热点断网后应先在 AP 日志看到 AI disconnected，再在 WB01 日志看到 class ai state 4，对应文档里的 ai,4 断云返回码。

**要测试什么**
- 文档层级：`状态返回确认测试 -> AI云未连接状态 -> 在线 -> AI云未连接状态信息给上位机`
- case_type：`状态返回确认测试`
- 文档标题：`AI云未连接状态的返回码测试`
- 自动化接管依据：热点断网后应先在 AP 日志看到 AI disconnected，再在 WB01 日志看到 class ai state 4，对应文档里的 ai,4 断云返回码。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、设备已联网，将连接的路由器断网或断电或在路由器设置页面将当前联网的设备加入黑名单无法访问网络；
- 文档预期：1、AI云会断开连接，之后csk会发送ai,4给上位机，代表AI云断开连接，wb01侧自行处理控制灯光动效

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_585 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_network_disconnect_case`，runner_kind=`network_disconnect_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 通过本机热点断网。
- 直接判断断网窗口内 AP/WB 的断连状态码。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：AP 必须出现 `AI disconnected` 或 `wifiLink_update:disconnect close`；WB 必须出现 `class ai state 4`。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## network_reconnect_voice_case

- runner 调度函数：`run_network_reconnect_voice_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 断网后先验证在线技能失效、离线命令仍可用。
- 复网后再验证在线技能与控制都恢复。

### 美的空调_20 网络关闭后再开启网络的语音交互测试

**摘要**
- 该用例位于 `语音交互能力 -> 网络异常 -> 离线 -> 网络异常测试`。
- 重点验证 `网络关闭后再开启网络` 场景下“网络关闭后再开启网络的语音交互测试”是否符合文档预期。
- 自动化接管说明：热点断开后，在线技能“现在几点了”应不再进入在线 ASR/云端 TTS，但离线“打开空调”仍可控制；热点恢复后，在线技能与空调控制都应恢复正常。

**要测试什么**
- 文档层级：`语音交互能力 -> 网络异常 -> 离线 -> 网络异常测试`
- case_type：`网络关闭后再开启网络`
- 文档标题：`网络关闭后再开启网络的语音交互测试`
- 自动化接管依据：热点断开后，在线技能“现在几点了”应不再进入在线 ASR/云端 TTS，但离线“打开空调”仍可控制；热点恢复后，在线技能与空调控制都应恢复正常。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、设备已联网情况下，将设备连接的手机热点/路由器wifi关闭
2、等待3分钟后再将手机热点/路由器wifi开启
- 文档预期：1、在网络断开的3分钟内，设备可以唤醒,在线指令词不能控制（比如说现在几点了？），离线指令词可控制（比如说打开空调），
2、手机热点/路由器wifi开启之后正常再自动连上网，语音控制正常（在线技能和空调控制指令均正常识别并操作）

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_20 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_network_reconnect_voice_case`，runner_kind=`network_reconnect_voice_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 断网后先验证在线技能失效、离线命令仍可用。
- 复网后再验证在线技能与控制都恢复。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：断网阶段“现在几点了”不能进入在线 ASR/TTS；“打开空调”仍要能离线控制；复网后二者都要恢复。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## offline_interrupt_voice

- runner 调度函数：`execute_standard_audio_case(interrupt mode)`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 先播放第一段语音。
- 等待第一条识别或播放开始标记后，再插入第二段唤醒音频做打断验证。

### 美的空调_32 离线情况下的识别播报语打断对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音打断（回声消除） -> 离线 -> 离线识别播报语打断`。
- 重点验证 `识别播报语打断` 场景下“离线情况下的识别播报语打断对话功能”是否符合文档预期。
- 自动化接管说明：文档离线识别播报语打断，重点验证命令播报开始后第二次唤醒是否能打断当前播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音打断（回声消除） -> 离线 -> 离线识别播报语打断`
- case_type：`识别播报语打断`
- 文档标题：`离线情况下的识别播报语打断对话功能`
- 自动化接管依据：文档离线识别播报语打断，重点验证命令播报开始后第二次唤醒是否能打断当前播报。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备整机断开网络
2、发送语音“小美小美，打开空调，小美小美”，第二句话与第三句话的时间间隔小于200ms,,Wakeup#talk#小美小美#,Action#sleep#1000#，UnAsr#talk#打开空调#，#,Action#sleep#150#，Wakeup#talk#小美小美#,Action#sleep#1000#，
3、听一下喇叭播放的内容
- 文档预期：1、唤醒正确识别2次，在命令词提示语“已为您打开空调”/“空调已开机”播报时进行唤醒，会打断命令词提示语，切换为唤醒提示语的播报

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_32 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> execute_standard_audio_case(interrupt mode)`，runner_kind=`offline_interrupt_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先播放第一段语音。
- 等待第一条识别或播放开始标记后，再插入第二段唤醒音频做打断验证。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> UnAsr[talk]=打开空调 -> 静默 150ms -> 唤醒词[talk]=小美小美 -> 静默 1000ms
- 观察窗口=`14000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `2` 次。
- COM13 `offline_wakeup` 至少 `2` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- 必须观测到“播报进行中再次唤醒”。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## offline_voice

- runner 调度函数：`run_offline_audio_case`
- 家族结果分布：`PASS 7 / FAIL 0 / BLOCKED 0`
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。

### 美的空调_28 离线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 离线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“离线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：文档离线 one-shot，唤醒后 10ms 接打开空调。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 离线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`离线情况下的oneshot对话功能`
- 自动化接管依据：文档离线 one-shot，唤醒后 10ms 接打开空调。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网，关闭自然对话
- 文档步骤：1、将设备整机断开网络,关闭自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔小于200ms,Wakeup#talk#小美小美#,Action#sleep#10#,Asr#talk#打开空调#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到打开空调的离线命令词后，1s内，喇叭播报离线tts语音“空调已开机”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_28 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10ms -> Asr[talk]=打开空调
- 观察窗口=`14000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_29 离线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 离线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“离线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：文档离线 one-shot，唤醒后 1s 接打开空调。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 离线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`离线情况下的oneshot对话功能`
- 自动化接管依据：文档离线 one-shot，唤醒后 1s 接打开空调。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网，关闭自然对话
- 文档步骤：1、将设备整机断开网络,关闭自然对话
2、发送语音“小美小美，打开空调”，这两句话中间的时间间隔大于1s,Wakeup#talk#小美小美#,Action#sleep#1000#,Asr#talk#打开空调#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到打开空调的离线命令词后，1s内，喇叭播报离线tts语音“空调已开机”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_29 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> Asr[talk]=打开空调
- 观察窗口=`14000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_30 离线情况下的oneshot对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒+识别 -> 离线 -> oneshot`。
- 重点验证 `oneshot对话` 场景下“离线情况下的oneshot对话功能”是否符合文档预期。
- 自动化接管说明：文档离线 one-shot，关闭空调后再打开空调；判定重点是两条命令是否都被识别并播报。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒+识别 -> 离线 -> oneshot`
- case_type：`oneshot对话`
- 文档标题：`离线情况下的oneshot对话功能`
- 自动化接管依据：文档离线 one-shot，关闭空调后再打开空调；判定重点是两条命令是否都被识别并播报。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网，打开自然对话
- 文档步骤：1、将设备整机断开网络，打开自然对话
2、发送语音“小美小美，关闭空调，打开空调”，这前两句句话中间的时间间隔小于200ms,最后一句话的时间间隔大于3s，小于10s,Wakeup#talk#小美小美#,Action#sleep#10#,Asr#talk#关闭空调#，Action#sleep#4000#,Asr#talk#打开空调#Action#sleep#5000#
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行5次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、在识别到关闭空调的离线命令词后，1s内，喇叭播报离线tts语音“空调已关机”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
3、最后一句话“打开空调”的命令词会识别，会播报打开空调相关的提示语，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_30 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 10ms -> Asr[talk]=关闭空调 -> 静默 4000ms -> Asr[talk]=打开空调 -> 静默 5000ms
- 观察窗口=`18000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- 唯一识别关键词数至少 `2`。
- 识别关键词必须包含：kong tiao guan ji、kong tiao kai ji。
- COM13 `PLAYBACK_COMPLETE` 至少 `3` 次。
- tone id 必须包含：4 (004_空调已关机.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_31 离线情况下的唤醒提示语打断对话功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音打断（回声消除） -> 离线 -> 唤醒打断`。
- 重点验证 `唤醒提示语打断` 场景下“离线情况下的唤醒提示语打断对话功能”是否符合文档预期。
- 自动化接管说明：文档离线唤醒提示语打断，重点看连续唤醒链路是否不断。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音打断（回声消除） -> 离线 -> 唤醒打断`
- case_type：`唤醒提示语打断`
- 文档标题：`离线情况下的唤醒提示语打断对话功能`
- 自动化接管依据：文档离线唤醒提示语打断，重点看连续唤醒链路是否不断。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备整机断开网络
2、发送语音“小美小美，小美小美，小美小美，小美小美”，这每句话中间的时间间隔小于200ms,,Wakeup#talk#小美小美#,Action#sleep#150#，Wakeup#talk#小美小美#,Action#sleep#150#，Wakeup#talk#小美小美#,Action#sleep#150#，Wakeup#talk#小美小美#,Action#sleep#150#，
3、听一下喇叭播放的内容
- 文档预期：1、喇叭播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、唤醒正确识别4次，提示语依次播报4次

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_31 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 150ms -> 唤醒词[talk]=小美小美 -> 静默 150ms -> 唤醒词[talk]=小美小美 -> 静默 150ms -> 唤醒词[talk]=小美小美 -> 静默 150ms
- 观察窗口=`12000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `4` 次。
- COM13 `offline_wakeup` 至少 `4` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_42 离线情况下的唤醒功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒 -> 离线 -> 离线唤醒测试`。
- 重点验证 `唤醒词` 场景下“离线情况下的唤醒功能”是否符合文档预期。
- 自动化接管说明：文档离线连续 6 次唤醒。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒 -> 离线 -> 离线唤醒测试`
- case_type：`唤醒词`
- 文档标题：`离线情况下的唤醒功能`
- 自动化接管依据：文档离线连续 6 次唤醒。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备整机联网
2、发送语音“小美小美”，一共6次，等待唤醒提示音播放，Wakeup#talk#小美小美#，Action#sleep#2000#，Wakeup#talk#小美小美#，Action#sleep#2000#，Wakeup#talk#小美小美#，Action#sleep#2000#，Wakeup#talk#小美小美#，Action#sleep#2000#，Wakeup#talk#小美小美#，Action#sleep#2000#，Wakeup#talk#小美小美#，Action#sleep#2000#，
3、听一下喇叭播放的内容
- 文档预期：1、喇叭播报“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，一共播6次，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_42 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 2000ms -> 唤醒词[talk]=小美小美 -> 静默 2000ms -> 唤醒词[talk]=小美小美 -> 静默 2000ms -> 唤醒词[talk]=小美小美 -> 静默 2000ms -> 唤醒词[talk]=小美小美 -> 静默 2000ms -> 唤醒词[talk]=小美小美 -> 静默 2000ms
- 观察窗口=`16000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `6` 次。
- COM13 `offline_wakeup` 至少 `6` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `6` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_43 离线情况下的连续说唤醒词的功能

**摘要**
- 该用例位于 `语音交互能力 -> 语音唤醒 -> 离线 -> 离线唤醒测试`。
- 重点验证 `唤醒词` 场景下“离线情况下的连续说唤醒词的功能”是否符合文档预期。
- 自动化接管说明：文档离线连续 3 次唤醒。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音唤醒 -> 离线 -> 离线唤醒测试`
- case_type：`唤醒词`
- 文档标题：`离线情况下的连续说唤醒词的功能`
- 自动化接管依据：文档离线连续 3 次唤醒。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网
- 文档步骤：1、将设备整机联网
2、发送语音“小美小美、小美小美、小美小美”，三句话的时间间隔小于2s，Wakeup#talk#小美小美#，Action#sleep#1000#，Wakeup#talk#小美小美#，Action#sleep#1000#，Wakeup#talk#小美小美#，Action#sleep#20000#，
3、听一下喇叭播放的内容
- 文档预期：1、喇叭顺序播报“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，播报三次，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、最后一次唤醒提示语播完后，若是关闭自然对话情况下，等待15s后，播报超时提示语，若是打开自然对话情况下，按手机app上设置的超时时间为准

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_43 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> 唤醒词[talk]=小美小美 -> 静默 1000ms -> 唤醒词[talk]=小美小美 -> 静默 20000ms
- 观察窗口=`24000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `3` 次。
- COM13 `offline_wakeup` 至少 `3` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `3` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_48 离线情况下的识别测试

**摘要**
- 该用例位于 `语音交互能力 -> 语音识别 -> 离线 -> 离线命令词识别和控制播报音测试`。
- 重点验证 `离线命令词识别和控制播报音测试` 场景下“离线情况下的识别测试”是否符合文档预期。
- 自动化接管说明：文档离线识别测试示例，先回归当前已知命令词打开空调。

**要测试什么**
- 文档层级：`语音交互能力 -> 语音识别 -> 离线 -> 离线命令词识别和控制播报音测试`
- case_type：`离线命令词识别和控制播报音测试`
- 文档标题：`离线情况下的识别测试`
- 自动化接管依据：文档离线识别测试示例，先回归当前已知命令词打开空调。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备未联网，用遥控器或者语音把空调打开，处于开机状态，发送语音“小美小美，打开空调”将空调设为开机状态，Wakeup#talk#小美小美#，Action#sleep#1000#，Asr#talk#打开空调#
- 文档步骤：举例：
1、将设备断网
2、发送语音“小美小美，打开空调”，这两句话的时间间隔小于20s,Wakeup#talk#小美小美#，Action#sleep#1000#，Asr#talk#打开空调#
3、听一下喇叭播放内容
其他的支持的离线命令词都要测一遍,目前可使用工具自动交互测试；
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、识别到离线命令词“打开空调”后，1s内，喇叭播报离线tts提示语“空调已开机”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_48 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_offline_audio_case`，runner_kind=`offline_voice`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 按文档 token 生成一段 WAV，并通过固定声卡回放。
- 播放完成后，按观察窗口抓取 COM12/COM13/COM14 日志并做统一断言。
- 文档 token / 语音输入序列：唤醒词[talk]=小美小美 -> 静默 1000ms -> Asr[talk]=打开空调
- 观察窗口=`14000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `1` 次。
- COM14 `wakeup_callback` 至少 `1` 次。
- COM13 `offline_wakeup` 至少 `1` 次。
- COM14 离线 ASR 至少 `1` 次。
- COM13 离线 ASR 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。
- tone id 必须包含：3 (003_空调已开机.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## online_empty_nlu_case

- runner 调度函数：`run_online_empty_nlu_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 构造异常在线语料。
- 观察是否走到“有 ASR 但 NLU 为空”的兜底播报链路。

### 美的空调_21 联网状态下，有asr但nlu为空的主动播音测试

**摘要**
- 该用例位于 `语音交互能力 -> 主动播音 -> 离线 -> 异常情况提示语`。
- 重点验证 `联网状态下，有asr但nlu为空` 场景下“联网状态下，有asr但nlu为空的主动播音测试”是否符合文档预期。
- 自动化接管说明：在线状态下连续 4 轮唤醒后说“度”，应稳定形成在线 ASR 文本 do，并进入云端兜底 TTS，而不是命中本地空调命令。

**要测试什么**
- 文档层级：`语音交互能力 -> 主动播音 -> 离线 -> 异常情况提示语`
- case_type：`联网状态下，有asr但nlu为空`
- 文档标题：`联网状态下，有asr但nlu为空的主动播音测试`
- 自动化接管依据：在线状态下连续 4 轮唤醒后说“度”，应稳定形成在线 ASR 文本 do，并进入云端兜底 TTS，而不是命中本地空调命令。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备联网
- 文档步骤：1、将设备联网
2、发送语音“小美小美”后，说“度”（或者其他云端不能理解的说法）
3、听一下喇叭播放的内容
4、步骤2和步骤3再次执行3次
- 文档预期：1、喇叭先播报唤醒提示语，“在呢”、"请吩咐"、“我在”、“你说”、“你好”、“来啦”当中的任意一条唤醒提示音，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；
2、喇叭播报在线tts提示语“没太理解，能完整再说一遍吗”等兜底提示语且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_21 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_online_empty_nlu_case`，runner_kind=`online_empty_nlu_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 构造异常在线语料。
- 观察是否走到“有 ASR 但 NLU 为空”的兜底播报链路。
- 观察窗口=`8000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM12 `WAKE(1)` 至少 `4` 次。
- COM14 `wakeup_callback` 至少 `4` 次。
- COM13 `online_wakeup` 至少 `4` 次。
- 唯一识别关键词数不超过 `0`。
- 在线 ASR 文本必须包含：do。
- AP 云端 TTS 播放至少 `4` 次。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## power_broadcast_case

- runner 调度函数：`run_power_broadcast_case`
- 家族结果分布：`PASS 2 / FAIL 0 / BLOCKED 0`
- 必要时先切到目标在线/离线网络状态。
- 再通过 COM15 对 WB01 硬重启，只判上电播报链路。

### 美的空调_1 上电播报音测试

**摘要**
- 该用例位于 `上电播报 -> 主动播音 -> 离线 -> 上电播报`。
- 重点验证 `上电播报` 场景下“上电播报音测试”是否符合文档预期。
- 自动化接管说明：热点离线后执行 WB01 硬重启，校验上电欢迎链路是否走“欢迎使用美的语音空调 + 未联网提示”播报。

**要测试什么**
- 文档层级：`上电播报 -> 主动播音 -> 离线 -> 上电播报`
- case_type：`上电播报`
- 文档标题：`上电播报音测试`
- 自动化接管依据：热点离线后执行 WB01 硬重启，校验上电欢迎链路是否走“欢迎使用美的语音空调 + 未联网提示”播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：1、电控拔掉电源再插上电源
2、插上电源后，听一下喇叭播放的内容
Action#shell#console 1#
Action#shell#flash.setloglev 4#
- 文档预期：1、插上电源后，3s内，喇叭播报“欢迎使用美的语音空调，空调还未联网，请使用美的美居app进行配网”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_1 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_power_broadcast_case`，runner_kind=`power_broadcast_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 必要时先切到目标在线/离线网络状态。
- 再通过 COM15 对 WB01 硬重启，只判上电播报链路。
- 文档 token / 语音输入序列：串口命令 `console 1` -> 串口命令 `flash.setloglev 4`

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- tone id 必须包含：102 (102_欢迎使用美的语音空调.mp3)、406 (406_空调还未联网，可下载美的美居APP，将空调联网后体验更多功能.mp3)。
- tone id 不得包含：290 (290_主人请吩咐.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

### 美的空调_5 上电播报音测试

**摘要**
- 该用例位于 `上电播报 -> 主动播音 -> 在线 -> 上电播报`。
- 重点验证 `上电播报` 场景下“上电播报音测试”是否符合文档预期。
- 自动化接管说明：联网状态下执行 WB01 硬重启，校验上电欢迎链路是否走“欢迎使用美的语音空调 + 主人请吩咐”播报。

**要测试什么**
- 文档层级：`上电播报 -> 主动播音 -> 在线 -> 上电播报`
- case_type：`上电播报`
- 文档标题：`上电播报音测试`
- 自动化接管依据：联网状态下执行 WB01 硬重启，校验上电欢迎链路是否走“欢迎使用美的语音空调 + 主人请吩咐”播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备已联网
- 文档步骤：1、电控拔掉电源再插上电源
2、插上电源后，听一下喇叭播放的内容
Action#shell#console 1#
Action#shell#flash.setloglev 4#
- 文档预期：1、插上电源后，3s内，喇叭播报“欢迎使用美的语音空调，我准备好啦，主人请吩咐”，且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_5 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_power_broadcast_case`，runner_kind=`power_broadcast_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 必要时先切到目标在线/离线网络状态。
- 再通过 COM15 对 WB01 硬重启，只判上电播报链路。
- 文档 token / 语音输入序列：串口命令 `console 1` -> 串口命令 `flash.setloglev 4`

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM13 `PLAYBACK_COMPLETE` 至少 `2` 次。
- tone id 必须包含：102 (102_欢迎使用美的语音空调.mp3)、290 (290_主人请吩咐.mp3)。
- tone id 不得包含：406 (406_空调还未联网，可下载美的美居APP，将空调联网后体验更多功能.mp3)。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## serial_only

- runner 调度函数：`execute_standard_audio_case(serial mode)`
- 家族结果分布：`PASS 0 / FAIL 1 / BLOCKED 0`
- 不放语音，只发串口命令。
- 通过 WB/AP 日志里的播报回调与播放开始/结束断言。

### 美的空调_51 离线tts播报语

**摘要**
- 该用例位于 `离线tts播报语 -> 离线tts播报语 -> 离线 -> 离线tts播报语`。
- 重点验证 `离线tts播报语` 场景下“离线tts播报语”是否符合文档预期。
- 自动化接管说明：文档离线 TTS 播报语示例，当前自动验证示例命令 listen player play 310 的链路是否真的可播报。

**要测试什么**
- 文档层级：`离线tts播报语 -> 离线tts播报语 -> 离线 -> 离线tts播报语`
- case_type：`离线tts播报语`
- 文档标题：`离线tts播报语`
- 自动化接管依据：文档离线 TTS 播报语示例，当前自动验证示例命令 listen player play 310 的链路是否真的可播报。

**文档原始信息**
- 优先级：`P1`
- 前置条件：设备未联网
- 文档步骤：举例：
1、给wb01发送串口命令Action#shell#listen player play 310#
其他ID的离线tts都要听一遍，目前可使用工具自动按顺序发送串口命令，找实习生听一遍
- 文档预期：播报提示音“小美小美”,且播报音播放过程中无卡顿、内容不全、杂音等异常情况；

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_51 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> execute_standard_audio_case(serial mode)`，runner_kind=`serial_only`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 不放语音，只发串口命令。
- 通过 WB/AP 日志里的播报回调与播放开始/结束断言。
- 文档 token / 语音输入序列：串口命令 `listen player play 310`
- 观察窗口=`8000` ms。
- 本次实际 setup 轨迹：
-   - action=prepare_local_hotspot；success=True；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422191854164_doc_case_run_美的空调_51\setup\01_prepare_local_hotspot
-   - action=hotspot_off；success=True；requested_enable=False；expected_state=offline；wait_s=15.0；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422191854164_doc_case_run_美的空调_51\setup\02_hotspot_offline
- 本次实际 recovery 轨迹：
-   - action=hotspot_on；success=True；requested_enable=True；expected_state=online；wait_s=60.0；artifact=D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422191854164_doc_case_run_美的空调_51\recovery\01_hotspot_online
- 播放返回码=`0`
- 串口命令：listen player play 310

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- COM13 `PLAYING` 至少 `1` 次。
- COM13 `PLAYBACK_COMPLETE` 至少 `1` 次。
- WB 离线 `offline_tts_callbak` 至少 `1` 次。

**本次实际判定检查表**

| 检查项 | actual | expected | 是否通过 |
| --- | --- | --- | --- |
| wb_playback_start_count | `0` | `>=1` | `FAIL` |
| wb_playback_end_count | `0` | `>=1` | `FAIL` |
| wb_tts_callback_ids | `[310]` | `>=1 callback(s)` | `PASS` |
| command_echo | `True` | `>=1 command line` | `PASS` |

**当前结果 / FAIL 在哪里**
- 当前结果=`FAIL`。
- 判定原因：WB01 已触发离线 TTS 回调，但 AP 侧报 tts 310 can't play，当前固件资源缺失或示例 ID 无效。
- 失败直接来自以下检查项：
-   - wb_playback_start_count：actual=0；expected=>=1
-   - wb_playback_end_count：actual=0；expected=>=1

**本次关键观测值**
- 关键计数：cp_wake_count=0；cp_command_count=0；ap_wake_count=0；wb_wake_count=0；wb_online_wake_count=0；ap_asr_count=0；wb_asr_count=0；ap_cloud_tts_play_count=0；ap_instruction_broadcast_count=0；wb_playback_start_count=0；wb_playback_end_count=0；unique_command_keyword_count=0；interrupt_reset_count=0；wake_during_playback_count=0；boot_marker_count=0；crash_marker_count=0
- 关键内容：wb_tts_callback_ids=[310]；ap_tts_fail_ids=[310]

**关键日志摘录**
- line_counts={"COM12": 0, "COM13": 275, "COM14": 9}

**证据路径**
- 执行目录：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422191854164_doc_case_run_美的空调_51`
- judge：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422191854164_doc_case_run_美的空调_51\judge.json`
- result：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422191854164_doc_case_run_美的空调_51\doc_case_result.json`

## wake_info_upload_case

- runner 调度函数：`run_wake_info_upload_case`
- 家族结果分布：`PASS 1 / FAIL 0 / BLOCKED 0`
- 播放一次唤醒词。
- 把本地 algo info 与上传 wake_info 报文逐字段比对。

### 美的空调_706 

**摘要**
- 该用例位于 `唤醒信息上传 -> 唤醒信息上传 -> 在线 -> 唤醒信息上传`。
- 重点验证 `` 场景下“”是否符合文档预期。
- 自动化接管说明：在线唤醒后应在 AP 日志同时看到本地 algo info 与发送到云端的 device.report.wakeInfo，关键字段保持一致。

**要测试什么**
- 文档层级：`唤醒信息上传 -> 唤醒信息上传 -> 在线 -> 唤醒信息上传`
- case_type：``
- 文档标题：``
- 自动化接管依据：在线唤醒后应在 AP 日志同时看到本地 algo info 与发送到云端的 device.report.wakeInfo，关键字段保持一致。

**文档原始信息**
- 优先级：`P1`
- 前置条件：空调已上电，正常联网
- 文档步骤：1、使用当前的唤醒词唤醒设备，
2、去云端捞一下上传的唤醒信息与本地的是否能对上，上传的唤醒信息需要包含的字段如下：
"wakeupInfo"的内容为算法提供，主要有以下字段，后面的值为示例，不代表测试时实际的内容{
        "rlt": [{
                "istart": 19,
                "iresid": 1,
                "iduration": 21,
                "nfillerscore": 0,
                "nkeywordscore": 0,
                "ncm": -34,
                "ncmThreshold": -126,
                "keyword": "xiao3 mei3 xiao3 mei3",
                "nDelayFrame": 0,
                "nThrowFrame": 40,
                "decId": 0,
                "branch": 3,
                "wakeUpType": 0,
                "VadGap": 0,
                "nE2eIntervalFrame": 8,
                "nE2eNodeFrame": 2,
                "nStartStateThreshold": 500,
                "bMain": 1,
                "bAbsorb": 0,
                "iframe": 4756
        }]
}
"timestamp"为时间戳。
"response"代表是否响应唤醒，1-需要响应，0-不响应\忽略
"multi_wakeup"中"energy"代表唤醒能量值，"enable"代表是否开始唯一唤醒
"sessionId"本轮对话的sessionid，若response为0，"sessionId"也为“0”。
"isUploadingFile"代表是否正在上传唤醒音频
"isPreWakeUp"代表是否为预唤醒
"deviceId"代表设备的iotid
- 文档预期：1、上传到云端的唤醒信息与本地的唤醒信息一致

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_706 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_wake_info_upload_case`，runner_kind=`wake_info_upload_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 播放一次唤醒词。
- 把本地 algo info 与上传 wake_info 报文逐字段比对。
- 观察窗口=`10000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：本地 algo info 与上传 wake_info 需要字段比对一致，且 deviceId / response0 / response1 都要合理。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`PASS`。
- 本次无失败检查。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``

## wakeup_audio_upload_probe_case

- runner 调度函数：`run_wakeup_audio_upload_probe_case`
- 家族结果分布：`PASS 0 / FAIL 0 / BLOCKED 1`
- 先开启唤醒音频上传。
- 再连续播放多次唤醒词，检查上传 session / success 证据。

### 美的空调_714 在线情况下上传预唤醒与唤醒音频的功能

**摘要**
- 该用例位于 `云端能力 -> post请求 -> 在线 -> 音频上传`。
- 重点验证 `唤醒音频上传` 场景下“在线情况下上传预唤醒与唤醒音频的功能”是否符合文档预期。
- 自动化接管说明：在线开启唤醒音频上传后，本地应至少看到一次 `wakeup_upload` 成功响应与 `isUploadingFile=1`；最终仍需云端下载音频并校验格式/内容才能判 PASS。

**要测试什么**
- 文档层级：`云端能力 -> post请求 -> 在线 -> 音频上传`
- case_type：`唤醒音频上传`
- 文档标题：`在线情况下上传预唤醒与唤醒音频的功能`
- 自动化接管依据：在线开启唤醒音频上传后，本地应至少看到一次 `wakeup_upload` 成功响应与 `isUploadingFile=1`；最终仍需云端下载音频并校验格式/内容才能判 PASS。

**文档原始信息**
- 优先级：`P0`
- 前置条件：设备已联网
- 文档步骤：1、将设备联网
2、使用post工具，发送唤醒音频上传开启的请求：
deviceId在csk-ap端输入：deviceinfo 的指令，获取到IOT-id就是deviceId，使用python脚本发送开启请求；
3、唤醒音频和预唤醒音频都是这个接口，开启音频上传后，唤醒一次后捂住麦克风不要说话，(不要进入在线识别，在线识别后则不会上传唤醒音频）等待约5分钟后，开始音频上传，唤醒音频上传完成csk-ap侧会打印[wakeup_upload # wakeup_upload] resp : {"code":"200","msg":"success","data":null}，之后再继续进行唤醒，重复10次后，找美的技术人员去捞上传的音频
- 文档预期：1、上传的音频是2通道，16k，16bit的音频，打开播放声音正常

**自动化如何执行**
- 命令入口：`python tools/execution/polaris_doc_case_runner.py --case-id 美的空调_714 --device-key "VID_8765&PID_5678:9_2A847557_7_0000"`
- 调度函数：`run_doc_case -> run_wakeup_audio_upload_probe_case`，runner_kind=`wakeup_audio_upload_probe_case`。
- 三路日志 `COM12/COM13/COM14` 持续采集，执行时只按时间窗切片，不会断日志。
- 先开启唤醒音频上传。
- 再连续播放多次唤醒词，检查上传 session / success 证据。
- 探测轮数=`1`。
- 观察窗口=`15000` ms。

**自动化如何断言**
- 统一先从日志抽取 metrics，再用 rule 做客观判定，不依赖主观听音。
- 关键 marker 包括：CP `WAKE(1)/WAKE(0)`、AP `wakeup_callback/online_asr_callbak`、WB `offline_wakeup/online_wakeup/PLAYING/PLAYBACK_COMPLETE`、AP `audioBroadcast mid / stream_tts url id`、AP `play next tone <id>`。
- 额外检查：除了 wake 证据外，还要有 `isUploadingFile=1` 和上传 success 响应。

**本次实际判定检查表**

- <none>

**当前结果 / FAIL 在哪里**
- 当前结果=`BLOCKED`。
- 该条更多是“前置/环境/云端闭环未建起来”导致 BLOCKED，而不是业务断言失败。

**本次关键观测值**
- <none>

**关键日志摘录**
- - <none>

**证据路径**
- 执行目录：``
- judge：``
- result：``
