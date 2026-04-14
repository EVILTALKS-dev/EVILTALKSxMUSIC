"""
╔══════════════════════════════════════════════╗
║   💬  MESSAGES — /start + search text input  ║
╚══════════════════════════════════════════════╝
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from bot import buttons
from bot.player import search_youtube
from utils import check_spam

logger = logging.getLogger(__name__)


def register_messages(app: Client, awaiting_search: dict, search_cache: dict):

    # ─────────────────────────────────────────
    #  /start  (only trigger — everything else is buttons)
    # ─────────────────────────────────────────
    @app.on_message(filters.command("start") & (filters.group | filters.private))
    async def cmd_start(_, msg: Message):
        await msg.reply_text(
            "🎵 **TG Music Bot**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Your Voice Chat DJ is here! 🎧\n"
            "Use the buttons below to get started.",
            reply_markup=buttons.main_menu(),
        )

    # ─────────────────────────────────────────
    #  Song search input (when user is awaiting)
    # ─────────────────────────────────────────
    @app.on_message(filters.text & ~filters.command([]) & filters.group)
    async def handle_search_input(_, msg: Message):
        user_id = msg.from_user.id
        chat_id = msg.chat.id

        # Only handle if this user is mid-search for THIS chat
        if awaiting_search.get(user_id) != chat_id:
            return

        del awaiting_search[user_id]   # clear awaiting state

        query = msg.text.strip()
        if not query:
            return

        if check_spam(user_id):
            await msg.reply_text("⏳ Too fast! Please wait a moment.", quote=True)
            return

        # Show searching indicator
        loading = await msg.reply_text(
            f"🔍 Searching for: `{query[:50]}`\n⏳ Please wait…",
            quote=True,
        )

        try:
            results = await search_youtube(query)
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            await loading.edit_text(
                "❌ **Search failed.**\nTry again or use a YouTube link.",
                reply_markup=buttons.error_buttons(),
            )
            return

        if not results:
            await loading.edit_text(
                "🔍 **No results found.**\nTry a different query.",
                reply_markup=buttons.error_buttons(),
            )
            return

        # Cache results for callback handler
        search_cache[user_id] = results

        lines = ["🎵 **Search Results** — tap to play:\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"`{i}.` {r['title'][:45]}  `[{r['duration']}]`")

        await loading.edit_text(
            "\n".join(lines),
            reply_markup=buttons.search_results(results),
        )
