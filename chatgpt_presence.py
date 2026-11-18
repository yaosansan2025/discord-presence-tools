#!/usr/bin/env python3
"""在本机 Discord 客户端发布带图标的 ChatGPT 活动。"""

import argparse
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import time
import uuid


DEFAULT_IMAGE = "chatgpt"
CHATGPT_EXECUTABLE = "/Applications/ChatGPT.app/Contents/MacOS/ChatGPT"
CHECK_INTERVAL = 3
HEADER = struct.Struct("<II")
HANDSHAKE, FRAME, CLOSE, PING, PONG = range(5)


class DiscordError(RuntimeError):
    pass


def connect():
    folders = [os.environ.get(key) for key in ("XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP")]
    if sys.platform == "darwin" and not os.environ.get("TMPDIR"):
        # macOS 后台任务不一定继承桌面客户端使用的临时目录。
        user_temp = subprocess.run(
            ["/usr/bin/getconf", "DARWIN_USER_TEMP_DIR"], capture_output=True, text=True
        ).stdout.strip()
        folders.append(user_temp)
    for folder in dict.fromkeys([*filter(None, folders), "/tmp"]):
        for index in range(10):
            path = Path(folder) / f"discord-ipc-{index}"
            if not path.is_socket():
                continue
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.settimeout(5)
            try:
                connection.connect(str(path))
            except OSError:
                connection.close()
                continue
            return connection
    raise ConnectionError("找不到 Discord 桌面客户端的活动接口。")


def send(connection, opcode, body):
    connection.sendall(HEADER.pack(opcode, len(body)) + body)


def send_json(connection, opcode, payload):
    send(connection, opcode, json.dumps(payload, separators=(",", ":")).encode())


def read_exact(connection, length):
    buffer = bytearray()
    while len(buffer) < length:
        chunk = connection.recv(length - len(buffer))
        if not chunk:
            raise ConnectionError("Discord 客户端已断开。")
        buffer.extend(chunk)
    return bytes(buffer)


def receive(connection):
    opcode, length = HEADER.unpack(read_exact(connection, HEADER.size))
    if length > 65536:
        raise DiscordError("Discord 返回了超出预期的数据。")
    body = read_exact(connection, length)
    if opcode == PING:
        send(connection, PONG, body)
        return {}
    if opcode not in (FRAME, CLOSE):
        return {}
    data = json.loads(body)
    if opcode == CLOSE or data.get("evt") == "ERROR":
        error = data.get("data") or data
        raise DiscordError(f"Discord 拒绝了活动请求（错误代码 {error.get('code', '未知')}）。")
    return data


def wait_for(connection, matches):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        ready, _, _ = select.select([connection], [], [], max(0, deadline - time.monotonic()))
        if ready:
            message = receive(connection)
            if matches(message):
                return message
    raise TimeoutError("Discord 没有确认活动请求。")


def set_activity(connection, app_pid, activity=None):
    nonce = uuid.uuid4().hex
    send_json(connection, FRAME, {
        "cmd": "SET_ACTIVITY",
        "nonce": nonce,
        "args": {"pid": app_pid, "activity": activity},
    })
    wait_for(connection, lambda message: message.get("nonce") == nonce)


def chatgpt_pid():
    processes = subprocess.run(
        ["/bin/ps", "-axo", "pid=,comm="], capture_output=True, text=True, check=True
    ).stdout
    for process in processes.splitlines():
        columns = process.split(maxsplit=1)
        if len(columns) == 2 and columns[1].strip() == CHATGPT_EXECUTABLE:
            return int(columns[0])
    return None


def publish(application_id, image, app_pid):
    with connect() as connection:
        send_json(connection, HANDSHAKE, {"v": 1, "client_id": application_id})
        wait_for(connection, lambda message: message.get("cmd") == "DISPATCH" and message.get("evt") == "READY")
        if chatgpt_pid() != app_pid:
            return
        set_activity(connection, app_pid, {
            "type": 0,
            "details": "Using ChatGPT",
            "timestamps": {"start": int(time.time())},
            "assets": {"large_image": image, "large_text": "ChatGPT"},
        })
        print("Discord 已确认带图标的活动。", flush=True)
        try:
            while chatgpt_pid() == app_pid:
                ready, _, _ = select.select([connection], [], [], CHECK_INTERVAL)
                if ready:
                    receive(connection)
        finally:
            try:
                set_activity(connection, app_pid)
            except (OSError, DiscordError):
                pass


def watch(application_id, image):
    last_error = None
    while True:
        try:
            app_pid = chatgpt_pid()
            if app_pid is not None:
                publish(application_id, image, app_pid)
            last_error = None
        except (OSError, DiscordError, subprocess.CalledProcessError) as error:
            message = str(error)
            if message != last_error:
                print(message, file=sys.stderr, flush=True)
                last_error = message
        time.sleep(CHECK_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application_id", help="Discord 开发者后台的 Application ID")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="活动图标的公开 URL 或已上传的图片名称")
    parser.add_argument("--watch", action="store_true", help="自动随 ChatGPT 打开和关闭发布活动")
    args = parser.parse_args()
    if not (args.application_id.isascii() and args.application_id.isdigit() and 17 <= len(args.application_id) <= 20):
        parser.error("Application ID 应是 17 到 20 位数字。")
    try:
        if args.watch:
            watch(args.application_id, args.image)
        else:
            app_pid = chatgpt_pid()
            if app_pid is None:
                raise DiscordError("请先打开 ChatGPT 桌面客户端。")
            publish(args.application_id, args.image, app_pid)
    except KeyboardInterrupt:
        return 0
    except (OSError, DiscordError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
