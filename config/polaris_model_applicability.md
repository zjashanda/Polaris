# Polaris Model Applicability

## Current DUT identification

- current_device_model: `CA3X绯诲垪绌鸿皟`
- model_source: `after_controlled_reboot_rebaseline_state.json:wb.listen_flash_show.ota_url`
- state_probe: `20260420103049281` ???? rebaseline probe ?????????? session ????????????????? `wb.listen_flash_show.ota_url` ?????????
- wb01.listen_flash_show.ota_url: `https://listenai-test-internal.oss-cn-beijing.aliyuncs.com/Midea_OTA/CA3X/03271705_CA3X_CSK6012_V26.3.4.0.1.bin`
- conclusion: current DUT is treated as `CA3X????`, not a colmo model, and not a single-mic hanging model.

## learnCase evidence used

- test definition source: `D:\revolution4s\SKILLHUB\learnCase\???????\data\TTS_CSK5+Aisound5.0_20251114101501_test.json`
- historical CA3X result source: `D:\revolution4s\SKILLHUB\learnCase\????case????\CA3X????\20260325145906_16.03.01.01.05.26.03.04.00.01??-???????????.json`
- learned rule: use doc `??` as the first-class applicability boundary when the current DUT model can be identified objectively.

## Reclassified by model boundary

- model_skip_case_total: `50`
- 鐢ㄤ緥澶囨敞鏍囨敞浠?colmo 鏈哄瀷锛堝帹鎴跨┖璋?/ EVO鏌滄満 / EVO鎸傛満锛夐€傜敤锛涘綋鍓嶈澶囨満鍨嬭瘑鍒负 CA3X绯诲垪绌鸿皟锛堟潵婧?env.current_device_model锛夛紝涓嶉€傜敤銆?-> `25` cases: `缇庣殑绌鸿皟_140?缇庣殑绌鸿皟_141?缇庣殑绌鸿皟_142?缇庣殑绌鸿皟_143?缇庣殑绌鸿皟_144?缇庣殑绌鸿皟_145?缇庣殑绌鸿皟_146?缇庣殑绌鸿皟_147?缇庣殑绌鸿皟_148?缇庣殑绌鸿皟_149?缇庣殑绌鸿皟_150?缇庣殑绌鸿皟_151?缇庣殑绌鸿皟_152?缇庣殑绌鸿皟_153?缇庣殑绌鸿皟_154?缇庣殑绌鸿皟_155?缇庣殑绌鸿皟_156?缇庣殑绌鸿皟_157?缇庣殑绌鸿皟_158?缇庣殑绌鸿皟_159?缇庣殑绌鸿皟_160?缇庣殑绌鸿皟_161?缇庣殑绌鸿皟_162?缇庣殑绌鸿皟_163?缇庣殑绌鸿皟_164`
- 鐢ㄤ緥澶囨敞鏍囨敞鈥滃崟楹︽寕鏈虹殑鍔熻兘锛屽叾浠栨満鍨嬫病鏈夋鍔熻兘鈥濓紱褰撳墠璁惧鏈哄瀷璇嗗埆涓?CA3X绯诲垪绌鸿皟锛堟潵婧?env.current_device_model锛夛紝涓嶉€傜敤銆?-> `15` cases: `缇庣殑绌鸿皟_97?缇庣殑绌鸿皟_98?缇庣殑绌鸿皟_99?缇庣殑绌鸿皟_100?缇庣殑绌鸿皟_101?缇庣殑绌鸿皟_102?缇庣殑绌鸿皟_103?缇庣殑绌鸿皟_104?缇庣殑绌鸿皟_105?缇庣殑绌鸿皟_106?缇庣殑绌鸿皟_107?缇庣殑绌鸿皟_108?缇庣殑绌鸿皟_109?缇庣殑绌鸿皟_110?缇庣殑绌鸿皟_111`
- 鐢ㄤ緥澶囨敞鏍囨敞鈥滈潪colmo鏈哄瀷璺宠繃姝ょ敤渚嬧€濓紱褰撳墠璁惧鏈哄瀷璇嗗埆涓?CA3X绯诲垪绌鸿皟锛堟潵婧?env.current_device_model锛夛紝涓嶉€傜敤銆?-> `10` cases: `缇庣殑绌鸿皟_87?缇庣殑绌鸿皟_88?缇庣殑绌鸿皟_89?缇庣殑绌鸿皟_90?缇庣殑绌鸿皟_91?缇庣殑绌鸿皟_92?缇庣殑绌鸿皟_93?缇庣殑绌鸿皟_94?缇庣殑绌鸿皟_95?缇庣殑绌鸿皟_96`

## Effect on current baseline

- previous effective baseline: `157 executed / 92 PASS / 55 FAIL / 10 BLOCKED / 558 SKIP`
- current effective baseline: `109 executed / 92 PASS / 9 FAIL / 8 BLOCKED / 606 SKIP`
- closed by applicability rather than rerun regression: custom colmo-only threshold families, single-mic-only threshold families, and colmo-only hicolmo natural-dialog families.

## Remaining real FAIL/BLOCKED after applicability cleanup

- FAIL: `缇庣殑绌鸿皟_1?缇庣殑绌鸿皟_44?缇庣殑绌鸿皟_45?缇庣殑绌鸿皟_51?缇庣殑绌鸿皟_61?缇庣殑绌鸿皟_65?缇庣殑绌鸿皟_69?缇庣殑绌鸿皟_137?缇庣殑绌鸿皟_685`
- BLOCKED: `缇庣殑绌鸿皟_113?缇庣殑绌鸿皟_687?缇庣殑绌鸿皟_709?缇庣殑绌鸿皟_710?缇庣殑绌鸿皟_711?缇庣殑绌鸿皟_712?缇庣殑绌鸿皟_713?缇庣殑绌鸿皟_714`

## Implementation touchpoints

- classification logic: `tools/library/polaris_doc_case_lib.py`
- status/env/reference refresh: `tools/reporting/polaris_status_sync.py`
- failure bucket refresh: `tools/reporting/polaris_refresh_failure_diagnosis.py`

