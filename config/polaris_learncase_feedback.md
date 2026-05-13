# Polaris LearnCase Feedback

## Source

- Directory inspected: `D:\revolution4s\SKILLHUB\learnCase`
- Key references used:
  - `美的空调用例执行说明.md`
  - `美的空调用例执行与日志断言-实操版.md`
  - `测试矩阵-测试方案与断言.md`
  - historical assets under `测试执行器代码/data/` and `美的空调case执行结果/`

## What can be reused for Polaris

- Evidence hierarchy is consistent with the current Polaris direction: `output_log` / runner result is only the first layer; AP raw logs and final device behavior still decide whether a case is truly closed.
- Historical docs explicitly treat `online_asr_callbak` and `offline_asr_callbak` as the primary recognition evidence, which matches the current Polaris assertion repair.
- Threshold cases should always be judged in three layers together:
  - setup download/readback, such as `threshold ...` / `set wake threshold` / `get threshold is`
  - score evidence from `algo info`
  - final wake behavior via `wakeup_callback`
- Natural-dialog cases are described as behavior cases rather than simple count cases:
  - whether later commands still work without re-wakeup
  - whether timeout happens after the configured interval
  - whether AC-on and AC-off branches behave differently for timeout prompts
  - whether mode-switch commands like `打开自然对话` / `关闭自然对话` terminate the rest of the same utterance as expected
- Upload/log/report families are also documented there as needing cloud-side closure; local serial evidence alone is not enough for final PASS.

## Concrete historical cues worth keeping in Polaris

- Typical online chain in AP log:
  - `wakeup_callback`
  - `online_asr_callbak, text: ...`
  - `online_asr_tts_callbak, tts: ...`
- Typical threshold setup chain:
  - `threshold 50, source 0`
  - `set wake threshold, [NORMAL 50]`
  - `Upload wakeup threshold: {...}`
  - `algo info: {... ncm / ncmThreshold ...}`
  - `wakeup_callback`
- The learnCase notes repeatedly强调 that `Check#regex#...#` is mostly evidence collection, not a strict fail gate; this directly supports the Polaris move away from regex-only PASS/FAIL decisions.

## Historical expectations that explain current Polaris FAILs

- Half-duplex / natural-dialog close cases: the older material clearly expects that some AC-off branches must not play the timeout prompt; this reinforces keeping `美的空调_137` as a real behavior issue.
- Custom wake-word families: historical materials already separate “configuration accepted” from “later wake succeeds”; if the AP side rejects the wake word itself, the case should stay FAIL/BLOCKED instead of being forced through by runner heuristics.
- Cloud upload families: local success markers like `isUploadingFile=1` and upload success logs prove the local path, but the case still needs cloud callback or downloaded artifact to become PASS.

## Actionable follow-up for Polaris

- Keep the current behavior-first assertion style for online ASR, natural dialog, and threshold families.
- For remaining custom wake-word and room-name wake-word failures, prioritize device/config diagnosis instead of further loosening runner assertions.
- For upload families, preserve the current local automation result as `BLOCKED with positive local evidence` until cloud artifacts can be pulled.
- If later需要继续增强文档，可把 learnCase 里的“证据分层”结构继续迁移到 Polaris 的 fail detail / reference exports 中。
