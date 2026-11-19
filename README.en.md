# Discord Presence Tools

[简体中文](README.md) · **English**

Two macOS tools that publish activity through the Discord desktop client.

You’ll need Python 3.9 or later and a separate [Discord Application ID](https://discord.com/developers/applications) for each tool. Install the ChatGPT and Roblox desktop apps in `/Applications` and keep the Discord desktop client running.

## ChatGPT activity icon

Upload an icon in your Discord application's Rich Presence assets and name it `chatgpt`. Replace the placeholder in the command with your application ID.

```sh
python3 chatgpt_presence.py 'CHATGPT_DISCORD_APP_ID' --watch
```

While the script is running, it publishes the activity when ChatGPT opens and clears it when ChatGPT quits. Use `--image` to specify another asset name or a public image URL.

## Roblox join button

Use a separate Discord application and provide your public Roblox user ID.

```sh
python3 roblox_join.py --application-id 'ROBLOX_DISCORD_APP_ID' --roblox-user 'ROBLOX_USER_ID'
```

When you enter a Roblox session, the script adds a **Join My Roblox Game** button to your Discord activity. By default, the activity clears when you leave the session. Use `--check` to see whether the script detects your current session locally.

The button was published in a live Roblox session. Joining the same server in one click still needs a test from a separate account. Visitors must have permission to join you on Roblox.

## Show Roblox only in the foreground

Compile the foreground detector with the macOS command-line developer tools, then pass its absolute path to the Roblox tool.

```sh
xcrun clang -framework AppKit frontmost_pid.m -o frontmost_pid
python3 roblox_join.py --application-id 'ROBLOX_DISCORD_APP_ID' --roblox-user 'ROBLOX_USER_ID' \
  --foreground-helper "$PWD/frontmost_pid" --show-while-open --image roblox
```

Upload an asset named `roblox` to the Roblox Discord application. The `--show-while-open` option also shows the Roblox home screen while it has focus. The join button appears during a game session only. If you run both tools, pass the same `--priority-lock` path to both commands, such as `"$HOME/Library/Caches/roblox-priority.lock"`. When the Roblox activity clears, ChatGPT resumes if it is still open. To show a small ChatGPT icon on the Roblox activity, upload an asset named `chatgpt` to the Roblox Discord application and pass `--include-chatgpt`.

Press `Control+C` in Terminal to stop either tool.
