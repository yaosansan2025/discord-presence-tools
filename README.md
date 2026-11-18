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

进入对局后，程序会尝试向 Discord 活动添加「加入我的 Roblox」按钮。离开对局后会清除活动。使用 `--check` 可以只检查本机对局识别。按钮发布已通过模拟测试，实际一键入服仍待另一账号验证，访客须满足 Roblox 的加入权限。

两个工具均可在终端按 `Control+C` 停止。
