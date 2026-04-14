# 🎵 TG Music Bot
### **ET'AI x EVILTALKS Production**
> A fully button-driven Telegram Voice Chat music bot — no commands needed.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎛 **100% Button UI** | Every action via inline keyboards — zero slash commands |
| 🔍 **YouTube Search** | Top 5 results shown as clickable buttons |
| 🎧 **VC Streaming** | pytgcalls userbot streams high-quality audio |
| 📜 **Queue System** | Add, view & remove songs with buttons |
| 🖼 **Now Playing Card** | Thumbnail + title + duration overlay |
| 🔊 **Volume Control** | Low / Medium / High presets |
| 🛡 **Anti-Spam** | Per-user search cooldown |
| 🌐 **Multi-Group** | Independent state per chat |
| 🚀 **Railway Ready** | nixpacks.toml + Procfile included |

---

## 🚀 Quick Deploy on Railway

### 1. Clone the repo
```bash
git clone https://github.com/yourname/tg-music-bot
cd tg-music-bot
```

### 2. Generate a String Session (run locally once)
```bash
pip install pyrogram TgCrypto
python generate_session.py
```
Copy the printed session string.

### 3. Set Railway Environment Variables

| Variable | Value |
|---|---|
| `API_ID` | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | From my.telegram.org |
| `BOT_TOKEN` | From [@BotFather](https://t.me/botfather) |
| `STRING_SESSION` | Output of `generate_session.py` |

### 4. Deploy
Push to GitHub and connect to Railway — it auto-detects `nixpacks.toml` and installs ffmpeg.

---

## 🛠 Local Development

```bash
# Install system dependency
sudo apt install ffmpeg   # Ubuntu/Debian
brew install ffmpeg       # macOS

# Python setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Fill in .env values

# Run
python main.py
```

---

## 📁 Project Structure

```
tg-music-bot/
├── main.py                  ← Entry point
├── generate_session.py      ← One-time session helper
├── requirements.txt
├── Procfile                 ← Railway worker
├── runtime.txt
├── nixpacks.toml            ← ffmpeg + Python build
├── railway.json
├── .env.example
│
├── bot/
│   ├── config.py            ← Env vars + validation
│   ├── buttons.py           ← All InlineKeyboardMarkup layouts
│   │
│   ├── handlers/
│   │   ├── callbacks.py     ← All callback_query handlers
│   │   └── messages.py      ← /start + song search input
│   │
│   ├── player/
│   │   └── player.py        ← YouTube search, download, queue, stream control
│   │
│   └── assistant/
│       └── assistant.py     ← Pyrogram userbot + PyTgCalls init
│
├── utils/
│   ├── thumbnail.py         ← Auto thumbnail download + text overlay
│   └── antispam.py          ← Per-user cooldown guard
│
├── assets/
│   └── thumbnails/          ← Cached thumbnails (git-ignored)
│
└── downloads/               ← Cached audio files (git-ignored)
```

---

## 🎹 How to Use

1. **Add the bot** to a Telegram group
2. **Add the userbot** (assistant account) to the same group and make it admin
3. **Start a Voice Chat** in the group (Group Info → Start Voice Chat)
4. Send `/start` to the bot in the group
5. **Hit 🎵 Play Music** → type a song name → pick from results
6. Control playback with the buttons!

---

## ⚠️ Notes

- The **assistant account** (STRING_SESSION) must be in the group and have **manage voice chats** permission.
- Voice Chat must be **manually started** by a group admin before the bot can stream.
- Downloaded audio files are cached in `downloads/` to avoid re-downloading.

---

## 🧰 Tech Stack

- **Python 3.11**
- **Pyrogram** — Telegram MTProto client (bot + userbot)
- **py-tgcalls** — Voice Chat streaming
- **yt-dlp** — YouTube search + audio extraction
- **ffmpeg** — Audio conversion
- **Pillow** — Thumbnail overlay (optional)

---

*Made with 🎵 by ET'AI x EVILTALKS*
