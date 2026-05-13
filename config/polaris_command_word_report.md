# Polaris 命令词专项收口报告



- 更新时间：`2026-04-22 15:41:46`

- 当前基线：`715 total / 90 auto_executable_now / 90 executed / 82 PASS / 2 FAIL / 6 BLOCKED / 625 SKIP`

- 当前连续日志会话：`result/20260420091943/`

- 本报告只收口“命令词/控制词”范围，不把“自然对话/配置类”与“阈值/唤醒灵敏度类”混在一起。



## 1. 范围拆分



### 1.1 纯命令词 family（已完成的既有自动化）



**在线命令词/oneshot**

- ``美的空调_22``：``PASS``，在线情况下的oneshot对话功能

- ``美的空调_23``：``PASS``，在线情况下的oneshot对话功能

- ``美的空调_24``：``PASS``，在线情况下的oneshot对话功能

- ``美的空调_25``：``PASS``，在线情况下的oneshot对话功能

- ``美的空调_26``：``PASS``，在线情况下的oneshot对话功能

- ``美的空调_27``：``PASS``，在线情况下的oneshot对话功能

- ``美的空调_33``：``PASS``，在线情况下的识别播报语打断对话功能

- ``美的空调_34``：``PASS``，在线情况下的识别播报语打断对话功能

- ``美的空调_46``：``PASS``，在线情况下的唤醒功能

- ``美的空调_47``：``PASS``，在线情况下的连续说唤醒词的功能

- ``美的空调_50``：``PASS``，在线情况下的识别测试



**离线命令词/oneshot**

- ``美的空调_28``：``PASS``，离线情况下的oneshot对话功能

- ``美的空调_29``：``PASS``，离线情况下的oneshot对话功能

- ``美的空调_30``：``PASS``，离线情况下的oneshot对话功能

- ``美的空调_31``：``PASS``，离线情况下的唤醒提示语打断对话功能

- ``美的空调_42``：``PASS``，离线情况下的唤醒功能

- ``美的空调_43``：``PASS``，离线情况下的连续说唤醒词的功能

- ``美的空调_48``：``PASS``，离线情况下的识别测试

- ``美的空调_51``：``FAIL``，离线tts播报语



### 1.2 边界支撑用例（不算纯命令词，但和命令链路有关）



- ``美的空调_20``：``PASS``，网络关闭后再开启网络的语音交互测试

- ``美的空调_21``：``PASS``，联网状态下，有asr但nlu为空的主动播音测试



### 1.3 明确不混入本报告的自然对话/配置类



- ``美的空调_137``：``FAIL``，在线情况下使用手机app进行自然对话配置



- `美的空调_137` 仍属于 `app_dialog_config_case`，是“在线情况下使用手机 app 进行自然对话配置”，不应和本报告里的控制命令词统计混在一起。



## 2. 在线/离线控制命令矩阵扩展



- 在线矩阵证据：`result/20260420091943/artifacts/probe/phrase/20260422151746488_phrase_probe_command_matrix_online_control_v2/probe_summary.json`

- 离线矩阵证据：`result/20260420091943/artifacts/probe/phrase/20260422152029166_phrase_probe_command_matrix_offline_control_v2/probe_summary.json`

- 本轮按正确顺序执行：`打开空调 -> 制冷模式 -> 调到26度 -> 自动风 -> 关闭空调`。

- 离线首轮尝试因为把 `关闭空调` 放在前面，导致后续模式/温度/风速返回 `005_请先开空调.mp3`；v2 顺序已修正，因此以下结论以 v2 为准。



| 命令 | 在线观察 | 离线观察 | 结论 |

| --- | --- | --- | --- |

| 打开空调 | ``kong tiao kai ji``；在线 ASR=``打开空调``；cloud TTS=``1`` | ``kong tiao kai ji``；WB TTS callback=``3``；tone=``67 (067_请吩咐.mp3)、3 (003_空调已开机.mp3)、134 (134_制冷模式.mp3)、43 (043_26度.mp3)、12 (012_自动风.mp3)`` | PASS |

| 制冷模式 | ``zhi leng mo shi``；在线 ASR=``制冷模式``；cloud TTS=``1`` | ``zhi leng mo shi``；WB TTS callback=``14``；tone=``76 (076_你说.mp3)、14 (014_当前已经是.mp3)、134 (134_制冷模式.mp3)`` | PASS |

| 调到26度 | ``er shi liu du``；在线 ASR=``编码异常串（但关键词命中 26 度）``；cloud TTS=``1`` | ``er shi liu du``；WB TTS callback=``6``；tone=``189 (189_你好.mp3)、6 (006_已设为.mp3)、43 (043_26度.mp3)`` | PASS |

| 自动风 | ``zi dong feng``；在线 ASR=``自动风``；cloud TTS=``1`` | ``zi dong feng``；WB TTS callback=``324``；tone=``194 (194_哎.mp3)、324 (324_风速.mp3)、6 (006_已设为.mp3)、12 (012_自动风.mp3)`` | PASS |

| 关闭空调 | ``kong tiao guan ji``；在线 ASR=``关闭空调``；cloud TTS=``1`` | ``kong tiao guan ji``；WB TTS callback=``4``；tone=``52 (052_来啦.mp3)、4 (004_空调已关机.mp3)`` | PASS |



**补充结论**

- 这轮矩阵已经把用户关心的“命令词相关验证”从原先的自然对话汇报里单独拆了出来，且不只停留在 `打开空调/关闭空调`，已经扩到 `模式/温度/风速` 四类典型控制命令。

- 在线侧闭环特征是：CP 命令词识别成功、AP 在线 ASR 可见、cloud TTS 下发且播放成功。

- 离线侧闭环特征是：CP/WB/AP 三侧都能看到离线唤醒与离线 ASR，WB/AP 均出现离线 TTS callback 与对应 tone 链路。

- 当前热点已经恢复在线：`python tools/polaris_network_orchestrator.py hotspot-status` 于 `2026-04-22T15:34:09` 返回 `operational_state=On`、`client_count=1`、客户端 `midea_ac_1072` 已重连。



## 3. `美的空调_51` 单独处理



### 3.1 可信结论



- `美的空调_51` 结论继续保持 `FAIL`。

- 可信根因不是“没测到”，而是设备侧离线 TTS 资源/示例 ID `310` 本身不可播。

- 当前最可信物证来自连续日志，而不是本轮最新重跑目录。



### 3.2 可信日志证据（保留 FAIL 的依据）



- COM13 已实际接收到串口命令：

  - 2026-04-21T23:34:51.817 [COM13/wb01] [COMMAND] listen player play 310

- WB01 已回调示例 ID `310`：

  - 2026-04-21T23:34:52.107 [COM13/wb01] [A][cli # client] offline_tts_callbak, tts: 310

- AP 侧明确报错 `tts 310 can't play`：

  - 2026-04-21T23:34:52.147 [COM14/cskap] [2026-04-21 23:34:51.630][W][evs_event # soundplayer] tts 310 can't play



### 3.3 本轮最新重跑为何不能直接拿来翻案



- 最新重跑目录：`result/20260420091943/artifacts/doc_cases/runs/20260422152540905_doc_case_run_美的空调_51`

- 对应 judge：`D:\revolution4s\Polaris\result\20260420091943\artifacts\doc_cases\runs\20260422152540905_doc_case_run_美的空调_51\judge.json`

- 该次 judge 的客观结果是：`command_echo=False`, `wb_tts_callback_ids=[]`, `ap_tts_fail_ids=[]`, `wb_playback_start_count=0`, `wb_playback_end_count=0`。

- 但这不是“310 问题消失了”，而是这次 shell 命令没有被日志/串口命令消费链真正执行。

- `control.jsonl` 中可以看到命令已经入队：

  - {"ts": "2026-04-22T15:26:27.617", "port": "COM13", "command": "listen player play 310"}

- 但 `COM13.log` 在 `2026-04-22 15:26:27` 附近没有对应的 `[COMMAND] listen player play 310` 回显；说明命令队列消费者当时已经卡住，导致该次重跑不具备判定 `PASS/FAIL` 的可信度。

- 当前连续日志里最近一次可见的正常命令消费记录仍停留在 `2026-04-22 01:07` 左右，后续 `15:26` 这一批 `version/deviceinfo/flash.show/listen version/listen flash show/listen player play 310` 都只进入了 `control.jsonl`，没有继续落入 `COM13/COM14` 的 `[COMMAND]` 轨迹。



### 3.4 本地证据完整性备注



- `config/polaris_doc_case_status.json` ??????? `execution_dir/result_path`??????? `result/20260420091943/doc_case_run_????_51_20260421233421255` ???????????

- ????????????????`result/20260420091943/artifacts/doc_cases/runs/20260422152540905_doc_case_run_????_51`?

- ???????? `????_51` ?????????? `result/20260420091943/COM13.log` ? `result/20260420091943/COM14.log` ??????????????? invalid ??????? FAIL ???



## 4. 当前收口状态



- 用户要求的 1/2/3 已顺序完成：

  1. 已把命令词 family 与自然对话 family 分开展示。

  2. 已补齐在线/离线控制命令矩阵，覆盖 `开机/模式/温度/风速/关机`。

  3. 已将 `美的空调_51` 单独拆出，并明确：最新重跑无效，但真实结论仍为 `FAIL`。

- 若后续继续推进，下一优先级应是排查 `result/20260420091943/control.jsonl` 对应的命令队列消费者为何在长会话后不再把命令写入 `COM13/COM14` 的 `[COMMAND]` 日志。





