"""
╔══════════════════════════════════════════════════╗
║   🚀  MAIN — TG Music Bot Entry Point            ║
║        ET'AI x EVILTALKS Production              ║
╚══════════════════════════════════════════════════╝

Start order:
  1. Validate env vars
  2. Start Pyrogram bot client
  3. Start Pyrogram userbot (assistant)
  4. Start PyTgCalls on the userbot
  5. Register all handlers
  6. Run until disconnected
"""

import asyncio
import logging
import sys
import os

# ── Fix import paths so relative modules resolve ──
sys.path.insert(0, os.path.dirname(__file__))

from pyrogram import Client

from bot.config import validate, API_ID, API_HASH, BOT_TOKEN
from bot.assistant import assistant
from bot.handlers import register_callbacks, register_messages

# ── Logging ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


async def main():
    # Step 1 — validate env
    validate()
    logger.info("✅ Config validated")

    # Step 2 — create bot client
    bot = Client(
        name="music_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )

    # Step 3 & 4 — start assistant (userbot + pytgcalls)
    await assistant.start()

    # Step 5 — register handlers
    awaiting_search, search_cache = register_callbacks(bot)
    register_messages(bot, awaiting_search, search_cache)

    # Step 6 — start bot and idle
    logger.info("Starting bot…")
    await bot.start()

    me = await bot.get_me()
    logger.info(f"🤖 Bot running as @{me.username}")
    logger.info("Press Ctrl+C to stop.")

    # Keep running
    await asyncio.Event().wait()

    # Cleanup
    await bot.stop()
    await assistant.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down…")
