# Discord Presence Tools

**简体中文** · [English](README.en.md)

两个 macOS 小工具，通过正在运行的 Discord 桌面客户端发布活动。

使用前请准备 Python 3.9 或更新版本，以及各工具对应的 [Discord Application ID](https://discord.com/developers/applications)。ChatGPT 和 Roblox 客户端应安装在 `/Applications`。

## ChatGPT 活动图标

在 Discord 应用的 Rich Presence 素材里添加图标，素材名称设为 `chatgpt`。运行下面的命令时，把引号内的占位文本换成应用 ID。

```sh
python3 chatgpt_presence.py 'CHATGPT_DISCORD_APP_ID' --watch
```

程序运行期间会随 ChatGPT 打开和退出发布或清除活动。可以用 `--image` 指定其他素材名或公开图片 URL。

## Roblox 加入按钮

使用另一个 Discord 应用，并填入你的公开 Roblox 用户 ID。

```sh
python3 roblox_join.py --application-id 'ROBLOX_DISCORD_APP_ID' --roblox-user 'ROBLOX_USER_ID'
```

进入对局后，程序会在 Discord 活动中发布 **Join My Roblox Game** 按钮。默认在离开对局后清除活动。使用 `--check` 可以只检查本机对局识别。按钮已在真实对局中发布，实际一键入服仍待另一账号验证。访客须有权限在 Roblox 中加入你的对局。

## 仅在 Roblox 位于前台时显示

使用 macOS 命令行开发工具编译前台检测程序，再把它的绝对路径传给 Roblox 工具。

```sh
xcrun clang -framework AppKit frontmost_pid.m -o frontmost_pid
python3 roblox_join.py --application-id 'ROBLOX_DISCORD_APP_ID' --roblox-user 'ROBLOX_USER_ID' \
  --foreground-helper "$PWD/frontmost_pid" --show-while-open --image roblox
```

先在 Roblox 对应的 Discord 应用里上传名为 `roblox` 的素材。`--show-while-open` 可在前台显示 Roblox 主页，加入按钮只在对局中出现。如果同时运行两个工具，给两条命令传入同一个 `--priority-lock` 路径，例如 `"$HOME/Library/Caches/roblox-priority.lock"`。Roblox 活动结束后，仍运行的 ChatGPT 会恢复显示。给 Roblox 应用再上传名为 `chatgpt` 的素材，并加上 `--include-chatgpt`，即可在 Roblox 活动中显示 ChatGPT 小图标。

两个工具均可在终端按 `Control+C` 停止。
