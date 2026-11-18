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

When you enter a Roblox session, the script attempts to add a button labeled **加入我的 Roblox** (“Join my Roblox”) to your Discord activity. The activity clears when you leave the session. Use `--check` to see whether the script detects your current session locally.

The publishing flow passed a simulated test. Joining the same server in one click still needs a live test from a separate account. Visitors must have permission to join you on Roblox.

Press `Control+C` in Terminal to stop either tool.
