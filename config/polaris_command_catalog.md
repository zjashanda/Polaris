# Polaris 涓插彛鍛戒护鐩綍

- 鐢熸垚鏃堕棿: `2026-04-23T09:34:08.943`
- 褰撳墠鏃ュ織浼氳瘽: `D:\revolution4s\Polaris\result\20260420091943`
- 鏂囨。鏉ユ簮: `doc/缇庣殑绌鸿皟鐩稿叧鐗规畩鎿嶄綔璇存槑鏂囨。.docx`

## AP / COM14

| 鍛戒护 | 绫诲埆 | 椋庨櫓 | 楠岃瘉鐘舵€?| 璇存槑 |
| --- | --- | --- | --- | --- |
| `version` | `info` | `safe` | `pass` | 鏌ョ湅 AP/CP/绠楁硶鐗堟湰 |
| `deviceinfo` | `info` | `safe` | `fail` | 鏌ョ湅 SN銆丮AC銆乄akeupID銆両P/IoT ID 绛夎澶囦俊鎭?|
| `flash.show` | `config_query` | `safe` | `pass` | 鏌ョ湅 AP 渚?flash 閰嶇疆椤癸紝濡傛棩蹇楃瓑绾с€佺幆澧冪瓑 |
| `flash.setloglev 4` | `log_level` | `safe` | `pass` | 灏?AP/CSK 鏃ュ織绛夌骇璁句负鏈€楂?|
| `flash.setloglev 0` | `log_level` | `safe_with_caution` | `documented_only` | 灏?AP/CSK 鏃ュ織绛夌骇璁句负鏈€浣?|
| `console 1` | `log_control` | `safe` | `pass` | 淇濇寔鏃ュ織绛夌骇涓?console 杈撳嚭锛屼究浜庤皟璇?|
| `console 0` | `log_control` | `safe_with_caution` | `documented_only` | 鍏抽棴 console 杈撳嚭锛岄€傜敤浜庢墦鐐规祴璇?|
| `player.setloglev 4` | `log_level` | `safe` | `pass` | 寮€鍚挱鏀惧櫒鏃ュ織 |
| `player.setloglev 0` | `log_level` | `safe_with_caution` | `documented_only` | 鍏抽棴鎾斁鍣ㄦ棩蹇?|
| `mai.setloglev 4` | `log_level` | `safe` | `pass` | 寮€鍚?miniSDK / 缇庣殑涓氬姟渚ф棩蹇?|
| `mai.setloglev 0` | `log_level` | `safe_with_caution` | `documented_only` | 鍏抽棴 miniSDK / 缇庣殑涓氬姟渚ф棩蹇?|
| `player.play.tone 76` | `playback` | `safe` | `pass` | AP 渚х洿鎺ユ挱鏀剧绾?tone |
| `player.play.url <url>` | `playback` | `env_dependent` | `not_run` | AP 渚ф挱鏀捐仈缃?URL 闊抽 |
| `flash.set.int env@<0|1|2>` | `environment` | `high_risk` | `not_run` | 鍒囨崲 PRO/UAT/SIT 鐜 |
| `reboot` | `device_control` | `medium_risk` | `documented_only` | 杞噸鍚澶?|
| `ota.set.url <url>@<md5>@<loop>` | `ota` | `high_risk` | `not_run` | 鍛戒护琛岃Е鍙?OTA 鍗囩骇 |
| `flash.clear ota_test_url` | `ota` | `high_risk` | `not_run` | 娓呴櫎 OTA 娴嬭瘯 URL |
| `flash.clear ota_test_md5` | `ota` | `high_risk` | `not_run` | 娓呴櫎 OTA 娴嬭瘯 MD5 |
| `dot.cfg <num>` | `timing` | `manual_only` | `not_run` | 璁剧疆鎵撶偣褰曢煶浣嶅浘锛岀敤浜庡搷搴旀椂寤舵祴璇?|
| `flash.set.string vir_ver@<version>` | `version_override` | `high_risk` | `not_run` | 淇敼鍥轰欢涓婃姤 AI 浜戠殑鐗堟湰鍙?|

## WB01 / COM13

| 鍛戒护 | 绫诲埆 | 椋庨櫓 | 楠岃瘉鐘舵€?| 璇存槑 |
| --- | --- | --- | --- | --- |
| `listen version` | `info` | `safe` | `pass` | 鏌ョ湅 WB01 鐗堟湰淇℃伅 |
| `listen flash show` | `config_query` | `safe` | `pass` | 鏌ョ湅 WB01 flash 閰嶇疆椤?|
| `listen flash setloglev 4` | `log_level` | `safe` | `pass` | 灏?WB01 鏃ュ織绛夌骇璁句负鏈€楂?|
| `listen flash setloglev 0` | `log_level` | `safe_with_caution` | `documented_only` | 灏?WB01 鏃ュ織绛夌骇璁句负鏈€浣?|
| `listen player play 76` | `playback` | `safe` | `pass` | 鐢?WB01 渚цЕ鍙戠绾挎挱鎶ワ紝鏇存帴杩戝鎴蜂晶閾捐矾 |
| `listen flash set int ignore_midea 1` | `application_override` | `high_risk` | `not_run` | 蹇界暐缇庣殑搴旂敤閫昏緫锛屼粎淇濈暀搴曞眰绂荤嚎閾捐矾 |
| `listen flash clear ignore_midea` | `application_override` | `high_risk` | `not_run` | 鎭㈠缇庣殑搴旂敤閫昏緫 |
| `listen flash set string vir_ssid <ssid>` | `network_override` | `high_risk` | `not_run` | 鍐欏叆鍛戒护琛岃仈缃?SSID |
| `listen flash set string vir_pwd <pwd>` | `network_override` | `high_risk` | `not_run` | 鍐欏叆鍛戒护琛岃仈缃戝瘑鐮?|
| `listen flash clear vir_ssid` | `network_override` | `high_risk` | `not_run` | 娓呴櫎鍛戒护琛岃仈缃?SSID |
| `listen flash clear vir_pwd` | `network_override` | `high_risk` | `not_run` | 娓呴櫎鍛戒护琛岃仈缃戝瘑鐮?|

