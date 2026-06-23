# -*- coding: utf-8 -*-
import argparse
import csv
import json
import re
from pathlib import Path


MODE_DOWNLOAD = "download"
MODE_UPGRADE = "upgrade"
MODE_DOWNLOAD_NET = "download_net"
MODE_DOWNLOAD_POWER_NET = "download_power_net"


def read_text_best_effort(path):
    data = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gbk", "gb18030", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def parse_rounds(text):
    rounds = []
    current = None
    start_re = re.compile(r"CURRENT TESTTIMES\s+(\d+)\s+START")
    end_re = re.compile(
        r".*当前测试第(\d+)次结束,csk 重启(\d+)次,当前版本信息:\s*([^,]+),OTA(升级成功|升级失败),ota 执行最后阶段\s+(\d+).*"
    )
    env_re = re.compile(r".*当前测试第(\d+)次结束,检测到起始环境为：([^，,]*).*结束环境为：([^，,]*).*")

    for line_no, line in enumerate(text.splitlines(), 1):
        start_match = start_re.search(line)
        if start_match:
            index = int(start_match.group(1))
            current = {
                "round_index": index,
                "round_no": index + 1,
                "break_mode": "",
                "download_done": False,
                "power_cut": False,
                "network_cut": False,
                "ota_done": False,
                "completed": False,
                "result": "",
                "ota_step": "",
                "csk_reboots": "",
                "version": "",
                "env_start": "",
                "env_end": "",
                "start_line": line_no,
                "end_line": "",
            }
            rounds.append(current)
            continue

        if current is None:
            continue

        if "本轮 OTA 使用随机断电模式" in line or "本轮 OTA 使用融合随机模式" in line:
            if "断网" in line:
                current["break_mode"] = MODE_DOWNLOAD_NET
            elif "下载" in line:
                current["break_mode"] = MODE_DOWNLOAD
            elif "升级" in line:
                current["break_mode"] = MODE_UPGRADE

        if "当前开始下载" in line and "同时重启设备并断开网络" in line:
            current["break_mode"] = MODE_DOWNLOAD_POWER_NET
        elif "当前开始下载" in line and "断开网络" in line:
            current["break_mode"] = MODE_DOWNLOAD_NET
        elif "当前开始下载" in line and "重启设备" in line and not current.get("break_mode"):
            current["break_mode"] = MODE_DOWNLOAD
        elif "当前下载已完成" in line and "重启设备" in line and not current.get("break_mode"):
            current["break_mode"] = MODE_UPGRADE

        if "ota download succ" in line:
            current["download_done"] = True
        elif "uut-switch1.off" in line:
            current["power_cut"] = True
        elif "开始关闭路由器/网络电源" in line:
            current["network_cut"] = True
        elif "OTA update success" in line:
            current["ota_done"] = True

        env_match = env_re.search(line)
        if env_match:
            current["env_start"] = env_match.group(2).strip()
            current["env_end"] = env_match.group(3).strip()

        end_match = end_re.search(line)
        if end_match:
            current["completed"] = True
            current["csk_reboots"] = end_match.group(2)
            current["version"] = end_match.group(3).strip()
            current["result"] = end_match.group(4)
            current["ota_step"] = end_match.group(5)
            current["end_line"] = line_no

    return rounds


def write_csv(rounds, csv_path):
    fieldnames = [
        "round_no",
        "round_index",
        "break_mode",
        "download_done",
        "power_cut",
        "network_cut",
        "ota_done",
        "completed",
        "result",
        "ota_step",
        "csk_reboots",
        "version",
        "env_start",
        "env_end",
        "start_line",
        "end_line",
    ]
    with Path(csv_path).open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for item in rounds:
            writer.writerow({key: item.get(key, "") for key in fieldnames})


def summarize(rounds):
    completed = [item for item in rounds if item.get("completed")]
    return {
        "started_rounds": len(rounds),
        "completed_rounds": len(completed),
        "download_break_count": sum(1 for item in rounds if item.get("break_mode") == MODE_DOWNLOAD),
        "upgrade_break_count": sum(1 for item in rounds if item.get("break_mode") == MODE_UPGRADE),
        "download_net_break_count": sum(1 for item in rounds if item.get("break_mode") == MODE_DOWNLOAD_NET),
        "download_power_net_break_count": sum(1 for item in rounds if item.get("break_mode") == MODE_DOWNLOAD_POWER_NET),
        "download_break_rounds": [item["round_no"] for item in rounds if item.get("break_mode") == MODE_DOWNLOAD],
        "upgrade_break_rounds": [item["round_no"] for item in rounds if item.get("break_mode") == MODE_UPGRADE],
        "download_net_break_rounds": [item["round_no"] for item in rounds if item.get("break_mode") == MODE_DOWNLOAD_NET],
        "download_power_net_break_rounds": [
            item["round_no"] for item in rounds if item.get("break_mode") == MODE_DOWNLOAD_POWER_NET
        ],
        "network_cut_count": sum(1 for item in rounds if item.get("network_cut")),
        "ota_done_count": sum(1 for item in rounds if item.get("ota_done")),
        "download_done_count": sum(1 for item in rounds if item.get("download_done")),
        "script_success_count": sum(1 for item in completed if item.get("result") == "升级成功"),
        "script_fail_count": sum(1 for item in completed if item.get("result") == "升级失败"),
        "current_round": rounds[-1]["round_no"] if rounds else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse VenusA OTA random power/network-cut stats from stdout log.")
    parser.add_argument("log", help="stdout log path, for example result/.../stdout.log")
    parser.add_argument("--csv", dest="csv_path", help="optional CSV output path")
    args = parser.parse_args()

    rounds = parse_rounds(read_text_best_effort(args.log))
    if args.csv_path:
        write_csv(rounds, args.csv_path)
    print(json.dumps({"summary": summarize(rounds), "rounds": rounds}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
