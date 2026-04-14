"""
╔══════════════════════════════════════════════╗
║    🤖  ASSISTANT — Pyrogram Userbot          ║
╚══════════════════════════════════════════════╝
The string-session userbot that physically joins
the Voice Chat and streams audio via pytgcalls.
"""

import logging
from pyrogram import Client
from pytgcalls import PyTgCalls

from bot.config import API_ID, API_HASH, STRING_SESSION
from bot.player.player import music_player

logger = logging.getLogger(__name__)


class MusicAssistant:
    """
    Wraps the Pyrogram userbot + PyTgCalls instance.
    Call `.start()` once at startup.
    """

    def __init__(self):
        self.userbot: Client = Client(
            name="music_assistant",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=STRING_SESSION,
            no_updates=True,   # userbot doesn't need to handle updates
        )
        self.call_client: PyTgCalls = PyTgCalls(self.userbot)
        # Inject into the global music_player so it can call play/pause etc.
        music_player.call_client = self.call_client

    async def start(self):
        logger.info("Starting Music Assistant (userbot)…")
        await self.userbot.start()
        await self.call_client.start()
        logger.info("✅ Music Assistant is ready.")

    async def stop(self):
        logger.info("Stopping Music Assistant…")
        try:
            await self.call_client.stop()
        except Exception:
            pass
        try:
            await self.userbot.stop()
        except Exception:
            pass


# ── Singleton export ──────────────────────────
assistant = MusicAssistant()
