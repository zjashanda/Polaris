# Polaris FAIL 用例专项明细

> 该文件从 `config/polaris_auto_executable_case_detail.md` 中抽取当前所有 FAIL 用例，便于只看失败项。

## 当前统计

- 自动可执行总数：`90`
- 当前 FAIL 总数：`2`
- 当前 session：`D:\revolution4s\Polaris\result\20260420091943`
- 来源大文件：`D:\revolution4s\Polaris\config\polaris_auto_executable_case_detail.md`

## FAIL 家族分布

| runner_kind | FAIL 数量 | case_id 列表 |
| --- | --- | --- |
| app_dialog_config_case | 1 | 美的空调_137 |
| serial_only | 1 | 美的空调_51 |

## FAIL 详细内容

## app_dialog_config_case

- 当前 family FAIL 数：`1`

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

## serial_only

- 当前 family FAIL 数：`1`

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
