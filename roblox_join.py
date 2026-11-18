#!/usr/bin/env python3
"""在有对局时向本机 Discord 发布 Roblox 加入按钮。"""

import argparse
from datetime import datetime
from pathlib import Path
import re
import select
import subprocess
import sys
import time
from urllib.parse import urlencode

from chatgpt_presence import (
    DiscordError,
    HANDSHAKE,
    connect,
    receive,
    send_json,
    set_activity,
    wait_for,
)


PLAYER = "/Applications/Roblox.app/Contents/MacOS/RobloxPlayer"
LOG_DIRECTORY = Path.home() / "Library" / "Logs" / "Roblox"
CHECK_INTERVAL = 3
JOIN_EVENT = re.compile(rb"^\[FLog::Output\] ! Joining game '[0-9a-fA-F-]{36}' place [0-9]+\b")
USER_ID = re.compile(rb"\buserid:\s*([0-9]{1,20})\b", re.IGNORECASE)


class GameLog:
    def __init__(self, path):
        self.path = path
        self.offset = 0
        self.started_at = None
        self.connected = False
        self.user_id = None

    def update(self):
        with self.path.open("rb") as source:
            source.seek(self.offset)
            for line in source:
                if not line.endswith(b"\n"):
                    break
                self.offset += len(line)
                prefix, _, event = line.partition(b" ")
                self.handle(event, prefix)

    def handle(self, event, prefix=b""):
        # 只处理客户端写的事件，忽略 Roblox 游戏脚本的输出。
        if JOIN_EVENT.match(event):
            try:
                timestamp = prefix.split(b",", 1)[0].decode("ascii").replace("Z", "+00:00")
                self.started_at = int(datetime.fromisoformat(timestamp).timestamp())
            except (ValueError, OverflowError, OSError):
                self.started_at = int(time.time())
            self.connected = False
            self.user_id = None
        elif event.startswith((
            b"[FLog::Network] Time to disconnect replication data:",
            b"[FLog::SingleSurfaceApp] leaveUGCGameInternal",
        )):
            self.started_at = None
            self.connected = False
            self.user_id = None
        elif self.started_at is not None:
            if event.startswith(b"[FLog::GameJoinLoadTime] Report game_join_loadtime:"):
                match = USER_ID.search(event)
                if match:
                    self.user_id = int(match[1])
            elif event.startswith(b"[FLog::Network] Replicator created:"):
                self.connected = True


def player_pid():
    output = subprocess.check_output(["/bin/ps", "-axo", "pid=,comm="], text=True)
    for line in output.splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) == 2 and fields[1] == PLAYER:
            return int(fields[0])
    return None


def player_log(pid):
    # 只选当前进程打开的日志，避免从前一次会话发布已经离开的对局。
    opened = subprocess.run(
        ["/usr/sbin/lsof", "-a", "-p", str(pid), "-Fn"],
        capture_output=True, text=True, timeout=6,
    ).stdout
    candidates = []
    for line in opened.splitlines():
        if line.startswith("n"):
            path = Path(line[1:])
            if path.parent == LOG_DIRECTORY and path.suffix == ".log" and "player" in path.name.lower():
                candidates.append(path)
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def activity_for(log, user_id):
    if not log.connected or log.user_id != user_id:
        return None
    url = "roblox://experiences/start?" + urlencode({"userId": user_id})
    return {
        "type": 0,
        "details": "Playing Roblox",
        "timestamps": {"start": log.started_at},
        "buttons": [{"label": "加入我的 Roblox", "url": url}],
    }


def publish_session(app_id, user_id, pid, log):
    with connect() as connection:
        send_json(connection, HANDSHAKE, {"v": 1, "client_id": app_id})
        wait_for(connection, lambda reply: reply.get("cmd") == "DISPATCH" and reply.get("evt") == "READY")
        previous = None
        try:
            while player_pid() == pid:
                log.update()
                current = activity_for(log, user_id)
                if current != previous:
                    set_activity(connection, pid, current)
                    print("Discord 已接收加入按钮。" if current else "已清除 Roblox 活动。", flush=True)
                    previous = current
                ready, _, _ = select.select([connection], [], [], CHECK_INTERVAL)
                if ready:
                    receive(connection)
        finally:
            if previous is not None:
                try:
                    set_activity(connection, pid)
                except (OSError, DiscordError):
                    pass


def watch(app_id, user_id):
    last_error = None
    while True:
        try:
            pid = player_pid()
            path = player_log(pid) if pid else None
            if path:
                log = GameLog(path)
                log.update()
                publish_session(app_id, user_id, pid, log)
            last_error = None
        except (DiscordError, OSError, subprocess.SubprocessError) as error:
            message = str(error)
            if message != last_error:
                print(message, file=sys.stderr, flush=True)
                last_error = message
        time.sleep(CHECK_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roblox-user", type=int, required=True, help="你的 Roblox 公开用户 ID")
    parser.add_argument("--application-id", help="此工具的 Discord Application ID")
    parser.add_argument("--check", action="store_true", help="仅检查对局，省略 Discord 发布")
    args = parser.parse_args()
    if args.roblox_user < 1 or args.roblox_user >= 10**20:
        parser.error("Roblox 用户 ID 应是 1 到 20 位的正整数。")
    if args.check:
        pid = player_pid()
        path = player_log(pid) if pid else None
        if not path:
            print("未找到运行中的 Roblox 玩家日志。")
            return 1
        log = GameLog(path)
        log.update()
        if activity_for(log, args.roblox_user):
            print("已识别此账号的当前 Roblox 对局。")
            return 0
        print("Roblox 正在运行，但还未检测到匹配此账号的对局。")
        return 1
    if not args.application_id or not re.fullmatch(r"[0-9]{17,20}", args.application_id):
        parser.error("请提供 Discord Application ID。")
    print("等待 Roblox 对局。按 Control+C 停止。", flush=True)
    try:
        watch(args.application_id, args.roblox_user)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
