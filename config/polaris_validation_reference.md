# Polaris Validation Reference

- updated_at: `2026-04-23T11:58:12`
- workspace: `D:\revolution4s\Polaris`
- active_session: `D:\revolution4s\Polaris\result\20260423111046`
- logger_pid: `47956`
- heartbeat: `D:\revolution4s\Polaris\result\20260423111046\logs\live\heartbeat.json`
- ports: `COM14=cskap/AP/writable`, `COM13=asr/writable`, `COM12=cskcp/CP/read_only`, `COM15=power-control`
- baudrate: `115200`
- audio_device_key: `VID_8765&PID_5678:9_2A847557_7_0000`
- playback_skill: `listenai-play`
- wake_word: `小美小美` / `xiao mei xiao mei`
- wifi_state: `online`
- current_connected_ssid: `pcwifi24`
- current_env: `SIT (env=2)`
- execution_stage: `debug`
- current_deviceinfo: `iot_id=177021372191476`, `mac=8C:3F:44:2B:7A:D9`
- current_device_model: `CA3X系列空调` (source=`env.current_device_model`)

## Latest auto-executable sweep

- audit_summary: `D:\revolution4s\Polaris\result\20260423111046\artifacts\doc_cases\audit\20260423115116048_doc_case_audit\audit_summary.json`
- auto_executable_now: `90`
- latest_executed: `90`
- latest_pass: `81`
- latest_fail: `3`
- latest_blocked: `6`
- latest_skip: `625`
- continuous logger remained connected for the whole sweep.
- Stability/stress cases are deferred in the current debug stage and are not included in this active baseline.

## Newly confirmed in this round

- Current effective baseline is `90 executed / 81 PASS / 3 FAIL / 6 BLOCKED / 625 SKIP`.
- `美的空调_709` ~ `美的空调_714` remain `BLOCKED`: the local trigger path and local evidence are complete, but cloud-side log/audio retrieval is still required for final closure.

## Key verified capabilities

- Online/offline continuous serial logging under the active result session.
- Windows hotspot off/on orchestration and ASR `vir_ssid` / `vir_pwd` plus reboot recovery.
- ASR / CSK hard power control via `COM15`.
- Cloud-side automation for natural-dialog, mic, wake word, threshold, accent, wakeup-audio-upload, log level, proactive interaction, and several other app settings.

## Remaining boundaries to keep in mind

- Remote/panel/manual extra-resource cases remain outside current auto scope unless a real automation entry point appears.
- Delete/unbind, first provisioning, specified external router, and OTA-risk families remain intentionally excluded.
- Cases that require cloud-side artifact retrieval or downloaded uploaded-audio inspection still need external evidence even if the local trigger path is automated.
