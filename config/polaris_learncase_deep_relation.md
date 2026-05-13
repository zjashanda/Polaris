# Polaris × learnCase 深挖关系与闭环记录

## 1. 本次深挖范围

- 目录：`D:\revolution4s\SKILLHUB\learnCase`
- 重点资产：
  - `20260130141231_lyzuo-美的空调-功能测试用例（全）.xlsx`
  - `测试矩阵-测试方案与断言.md`
  - `美的空调用例执行说明.md`
  - `美的空调用例执行与日志断言-实操版.md`
  - `测试执行器代码/main.py`
  - `测试执行器代码/run_testplan.py`
  - `测试执行器代码/serThead.py`
  - `美的空调case执行结果/`
  - `美的空调执行日志/`

## 2. learnCase 内部关系

- 入口层：Excel 只是导入源，不是最终执行体。
- 计划层：`main.py` 负责校验 Excel 表头并生成测试计划 JSON / 执行结果 JSON。
- 调度层：`run_testplan.py` 负责 UI 状态流、Pass/Fail/Block 按钮和日志落盘。
- 执行层：`serThead.py` 负责动作解析与串口执行，核心函数包括：
  - `getTestAction`
  - `writeSerCmd`
  - `oneShot`
  - `UntilCheck`
  - `actionHandle`
  - `runTestCase`
- 结果层：
  - 会话总日志：`output_log_*.log`
  - 单 case 局部快照：`CaseErrorLog/<case>.log`
  - 执行结果：机型目录下的 `*.json`

## 3. learnCase 给 Polaris 的关键边界

- `Check#regex#...#` 主要是取证，不是严格 fail gate。
- `Action#shell#...#` 只代表命令发出，不代表业务一定生效。
- 无自动动作的 case，在旧执行器里仍可能被点成 `Pass`，所以不能把旧结果 JSON 直接当真闭环。
- 日志/上传/云端类 case，在 learnCase 里本来就存在“本地只闭环触发侧，最终仍需云端回捞”的边界。
- 自然对话、阈值、唤醒词切换这些 family，本质是“行为闭环”而不是“单个计数闭环”。

## 4. 历史结果对当前 Polaris 的启发

### 4.1 历史执行结果分布

- `美的空调_1`：历史上同时存在 `Pass` / `Fail`，说明旧体系主要靠人工听音闭环。
- `美的空调_21`：历史上存在 `Pass` / `Fail` / `Block`，旧体系对 empty-NLU 兜底链路并不稳定。
- `美的空调_51`：历史上多数为 `Pass`，但旧执行器本质也是串口示例 + 人工听音。
- `美的空调_61/65/69/73`：历史上多数可 `Pass`，说明这族用例理论上设备应支持，不是天然不可测。
- `美的空调_709~714`：历史上也大量依赖人工/云端侧闭环，不能只靠本地串口直接判最终 `PASS`。

### 4.2 历史日志现场

- `美的空调_1`：
  - 历史失败现场出现 `102` / `290`
  - 用户在旧 UI 上手动点了 `Fail`
  - 说明旧体系也把“欢迎播报后又进请吩咐链路”视为异常
- `美的空调_21`：
  - 历史日志能看到 `online_Asr` 未按预期命中时被点 `Block`
  - 旧体系并没有稳定抓住 empty-NLU 的云端兜底链
- `美的空调_51`：
  - 历史 output_log 主要能看到 `CaseErrorLog` 落盘
  - 这条本来就是“串口下发 + 人工听音”风格
- `美的空调_97`：
  - 历史日志里既出现过 `主人，空调暂时不支持该功能`
  - 也出现过后续正常控制
  - 说明阈值 / 唤醒词类 case 不能只看一次播报或单个计数，必须看 wake 证据和阈值日志

## 5. 本轮结合 learnCase 做的 Polaris 收敛

### 5.1 `美的空调_21` 已闭环为 PASS

- learnCase 启发：
  - 这条应该看 `online_asr_callbak`
  - 更应该看 empty-NLU 返回后的 `cloud.instructions.audioBroadcast`
  - 不该只靠 `ap_cloud_tts_play_count`
- Polaris 落地：
  - 修正 `online_empty_nlu_case`
  - 用以下组合闭环：
    - 4 次 wake
    - 4 次 `online_asr_callbak` 命中 `do`
    - 4 次 `mideaSkillId=asrInvalid`
    - 4 次 `endSession=true`
    - 过滤 `wen du shu zi fan ji` 这类 empty-NLU 特殊 token，不再误记为真实命令词
- 最新结果：
  - `美的空调_21 -> PASS`

### 5.2 `美的空调_73` 已闭环为 PASS

- learnCase 启发：
  - 唤醒词切换正向 case 核心是“能唤醒 + 有提示音”
  - 不应机械绑定 WB 侧 `PLAYBACK_COMPLETE`
- Polaris 落地：
  - 正向 `app_wakeup_word_case` 从只看 `wb_playback_end_count`
    改为也接受 AP 侧播报起止证据：
    - `play audio mem://...`
    - `ttsplayer/tone player` 停止标记
- 最新结果：
  - `美的空调_73 -> PASS`

### 5.3 `美的空调_51` 继续保持 FAIL

- learnCase 原始边界：
  - 旧体系这条偏人工听音
- 但 Polaris 最新证据已超过“仅命令回显”：
  - WB01 有 `offline_tts_callbak 310`
  - AP 明确报 `tts 310 can't play`
- 结论：
  - 这不是单纯的自动化边界问题
  - 更像资源缺失 / 示例 ID 无效 / 固件侧不可播
  - 所以保持 `FAIL` 更准确

### 5.4 `美的空调_1` 继续保持 FAIL

- learnCase 旧体系只能人工听音
- 但 Polaris 现有 tone catalog 已能把 tone id 映射到文件名：
  - `102_欢迎使用美的语音空调.mp3`
  - `290_主人请吩咐.mp3`
  - `406_空调还未联网，可下载美的美居APP，将空调联网后体验更多功能.mp3`
- 当前设备证据是 `102 + 290`，没有 `406`
- 因此这条已具备客观 fail 条件，不再只是“人工边界”

## 6. 当前剩余 fail 的可闭环判断

### 6.1 可继续当真实设备/配置问题保留 FAIL

- `美的空调_1`
- `美的空调_44/45`
- `美的空调_51`
- `美的空调_61/65/69`
- `美的空调_87~111`
- `美的空调_137`
- `美的空调_140~160`
- `美的空调_685`

这些 case 当前已不再主要是“断言写错”，而是：
- 设备不形成 wake
- 设备拒绝目标唤醒词
- 资源/播放链异常
- 行为与文档预期相反

### 6.2 继续保留 BLOCKED 的项

- `美的空调_161`
- `美的空调_163`
- `美的空调_709~714`

原因：
- 前置语音条件无法建立
- 本地已拿到触发侧证据，但最终仍缺云端回捞 / 下载物证

## 7. 本轮对外可引用的最新基线

- 连续日志会话：`result/20260420091943/`
- 当前基线：`92 executed / 82 PASS / 4 FAIL / 6 BLOCKED / 623 SKIP`
- 最新结果表：`result/20260420091943/case_result_table_20260422010857430/summary.json`
- 状态总表：`config/polaris_doc_case_status.json`
- 失败明细：`config/polaris_fail_case_detail.md`
- 失败诊断：`config/polaris_failure_diagnosis.json`

## 8. 后续继续排查时的优先顺序

1. 先看这条 case 在 learnCase 里到底是“严格自动项”还是“探针/人工项”
2. 再看 Polaris 当前是否已经拿到了比 learnCase 更强的证据
3. 如果已经拿到：
   - 保持 `FAIL`
   - 不要为了贴近旧体系而弱化真实问题
4. 如果仍只有命令发出/弱取证：
   - 才考虑 `BLOCKED`
   - 并明确写清缺的外部证据是什么

## 9. 2026-04-22 补充修正

### 9.1 case 编号不能机械复用

- 继续深挖 `D:\revolution4s\SKILLHUB\learnCase` 后确认：
- 低编号的一些 case（如 `美的空调_44/45/51/113`）和当前 Polaris 文档仍大体同义；
  - 但高编号 case 已经出现明显“同编号不同语义”的漂移。
- 典型例子：
  - learnCase 的 `美的空调_687` 是 `OTA 升级压测`
  - 当前 Polaris 的 `美的空调_687` 是 `在线方言切换后掉电操作`
  - learnCase 的 `美的空调_709~714` 是 `闹钟/第三方铃声`
  - 当前 Polaris 的 `美的空调_709~713` 是 `日志上传等级切换`，`美的空调_714` 是 `预唤醒/唤醒音频上传`
- 结论：
  - 对 `600+` 编号，不能只按 case id 做历史映射；
  - 必须同时按“用例名称 + 操作步骤 + 预期结果 + runner family”做语义比对。

### 9.2 learnCase 对当前 `709~714` 的真实启发

- `美的空调用例执行与日志断言-实操版.md` 已明确写出：
  - `美的空调_709` 在旧体系属于 `probe-only`
  - 日志上传类 case 是“本地 + 云端联合断言”
  - 只满足 `POST success` 不能判 `PASS`
  - 必须同时具备：
    - 本地 `deviceinfo / IoT ID`
    - 本地 `set device loglev ... by cloud_change`
    - 云端回捞到对应时间窗的日志/字段
- 这与当前 Polaris 的本地证据边界完全一致：
  - 本地链路已能自动验证“请求下发 + 本地 loglev 生效 + 继续交互”
  - 但最终仍缺云端回捞/下载物证
  - 因此 `美的空调_709~714` 保留 `BLOCKED` 是正确收口，不应伪造 `PASS`

### 9.3 `美的空调_113` 已闭环

- 本轮对 `run_app_dialog_announce_case()` 做了两点修正：
  - `cloud_apply_success` 不再误取 `00_ensure_mic_on`，而是准确取目标 `cloud_full_duplex` 记录；
  - 自然对话配置断言不再强绑 AP 侧文本行，新增接受 WB/AP 协议级证据：
    - `process cmd 0x05 / 0x04`
    - `fullduplex: 2`
    - `PLAYER cmd: 0x4009`
    - AP `cloud.speech.broadcast / ttsplayer play / play audio http`
- 回归结果：
  - `美的空调_113 -> PASS`
  - 证据目录：`result/20260420091943/doc_case_run_美的空调_113_20260422005830437/`

### 9.4 `美的空调_687` 已闭环

- 旧结论里的 `美的空调_687 -> BLOCKED` 已过时，根因是当时 setup 阶段遇到一次 `501 设备未上线`
- 本轮重新回归后确认：
  - 云端切半双工前置已恢复可用
  - 方言切换 + WB01 硬掉电 + 配置查询 + one-shot 降级链路可完整执行
  - 5 个方言阶段全部 `PASS`
- 最新结果：
  - `美的空调_687 -> PASS`
  - 证据目录：`result/20260420091943/doc_case_run_美的空调_687_20260422010002278/`

### 9.5 当前最终未闭环项

- 当前基线已刷新为：
  - `715 total / 92 auto_executable_now / 92 executed / 82 PASS / 4 FAIL / 6 BLOCKED / 623 SKIP`
- 当前剩余真实 `FAIL`：
  - `美的空调_44`
  - `美的空调_45`
  - `美的空调_51`
  - `美的空调_137`
- 当前剩余外部物证阻塞 `BLOCKED`：
  - `美的空调_709`
  - `美的空调_710`
  - `美的空调_711`
  - `美的空调_712`
  - `美的空调_713`
  - `美的空调_714`
- 其中：
  - `44/45` 已复核为 1000 次压测里真实少计数，不是正则错误；
  - `51` 已复核为 `offline_tts_callbak 310` + AP `tts 310 can't play`；
  - `137` 已复核为 half-duplex 15s 后仍出现 `asrInvalid` 结束播报链；
  - `709~714` 的缺口仍是 learnCase 明确要求的云端侧回捞/下载物证。
