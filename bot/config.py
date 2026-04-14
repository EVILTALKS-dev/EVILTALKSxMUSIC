"""
╔══════════════════════════════════════════════╗
║         🎵 TG MUSIC BOT — CONFIG             ║
║         ET'AI x EVILTALKS Production         ║
╚══════════════════════════════════════════════╝
All environment variables are loaded here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram API credentials ──────────────────
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")

# ── Bot token (BotFather) ─────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ── Userbot string session (Pyrogram) ─────────
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# ── Optional settings ─────────────────────────
# Maximum songs in queue per group
MAX_QUEUE = int(os.environ.get("MAX_QUEUE", 10))

# Default volume (1–200)
DEFAULT_VOLUME = int(os.environ.get("DEFAULT_VOLUME", 100))

# Anti-spam: seconds between search requests per user
SEARCH_COOLDOWN = int(os.environ.get("SEARCH_COOLDOWN", 5))

# ── Validation ────────────────────────────────
def validate():
    missing = []
    if not API_ID:    missing.append("API_ID")
    if not API_HASH:  missing.append("API_HASH")
    if not BOT_TOKEN: missing.append("BOT_TOKEN")
    if not STRING_SESSION: missing.append("STRING_SESSION")
    if missing:
        raise EnvironmentError(
            f"❌ Missing required env vars: {', '.join(missing)}\n"
            "Please check your .env file or Railway variables."
        )
