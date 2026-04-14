"""
╔══════════════════════════════════════════════╗
║   🎛  CALLBACKS — All inline-button actions  ║
╚══════════════════════════════════════════════╝
Routes every callback_data to the right action.
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from bot import buttons
from bot.player import music_player, Song, search_youtube
from utils import check_spam, remaining_cooldown, get_thumbnail

logger = logging.getLogger(__name__)

# ── Track which users are mid-search (waiting for song name input) ──
# {user_id: chat_id}
_awaiting_search: dict[int, int] = {}

# ── Track search results per (user_id) ──
# {user_id: [result_dict, ...]}
_search_cache: dict[int, list] = {}


def register_callbacks(app: Client):

    # ─────────────────────────────────────────
    #  🏠  Main Menu
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^main_menu$"))
    async def cb_main_menu(_, cq: CallbackQuery):
        await cq.message.edit_text(
            "🎵 **Music Bot**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Welcome! Use the buttons below to control music in your Voice Chat.",
            reply_markup=buttons.main_menu(),
        )
        await cq.answer()


    # ─────────────────────────────────────────
    #  🎵  Play Music — ask for query
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^play_music$"))
    async def cb_play_music(_, cq: CallbackQuery):
        if check_spam(cq.from_user.id):
            secs = remaining_cooldown(cq.from_user.id)
            await cq.answer(f"⏳ Slow down! Wait {secs}s.", show_alert=True)
            return

        # Mark user as awaiting input
        _awaiting_search[cq.from_user.id] = cq.message.chat.id

        await cq.message.edit_text(
            "🔍 **Search Music**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Send me a **song name** or **YouTube link** in this chat now.",
            reply_markup=buttons.error_buttons(),   # has Cancel = main_menu
        )
        await cq.answer("Send song name 🎵")


    # ─────────────────────────────────────────
    #  ▶  Play a selected YouTube result
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^play_(.+)$"))
    async def cb_play_selected(client: Client, cq: CallbackQuery):
        video_id = cq.data[5:]  # strip "play_"
        user_id  = cq.from_user.id
        chat_id  = cq.message.chat.id

        # Get cached results for this user
        results = _search_cache.get(user_id, [])
        song_data = next((r for r in results if r["id"] == video_id), None)
        if not song_data:
            await cq.answer("❌ Result expired. Search again.", show_alert=True)
            return

        song = Song(
            title=song_data["title"],
            url=song_data["url"],
            video_id=video_id,
            duration=song_data["duration"],
            duration_sec=song_data["duration_sec"],
            thumbnail=song_data["thumbnail"],
            requested_by=user_id,
        )

        # If already playing, add to queue
        if music_player.is_playing(chat_id):
            pos = music_player.add_to_queue(chat_id, song)
            await cq.message.edit_text(
                f"📥 **Added to Queue** — Position #{pos}\n\n"
                f"🎵 `{song.title}`\n"
                f"⏱ Duration: `{song.duration}`",
                reply_markup=buttons.now_playing_controls(),
            )
            await cq.answer(f"Added to queue at #{pos}")
            return

        # Show loading state
        await cq.message.edit_text(
            f"⏳ **Loading…**\n\n"
            f"🎵 `{song.title}`\n"
            f"⬇️ Downloading audio…",
            reply_markup=None,
        )
        await cq.answer("Starting…")

        try:
            await music_player.play(chat_id, song)
        except RuntimeError as e:
            await cq.message.edit_text(
                f"❌ **Error**\n`{e}`",
                reply_markup=buttons.error_buttons(),
            )
            return
        except Exception as e:
            logger.error(f"Play error: {e}", exc_info=True)
            await cq.message.edit_text(
                "❌ **Something went wrong** while streaming.\n"
                "Make sure Voice Chat is active.",
                reply_markup=buttons.error_buttons(),
            )
            return

        # ── Build Now Playing card ──
        thumb = await get_thumbnail(video_id, song.title, song.duration)

        caption = (
            "🎵 **Now Playing**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"**{song.title}**\n\n"
            f"⏱ Duration : `{song.duration}`\n"
            f"👤 Requested by : [{cq.from_user.first_name}](tg://user?id={user_id})"
        )

        if thumb:
            sent = await cq.message.reply_photo(
                photo=thumb,
                caption=caption,
                reply_markup=buttons.now_playing_controls(),
            )
        else:
            sent = await cq.message.edit_text(
                caption,
                reply_markup=buttons.now_playing_controls(),
            )

        music_player.set_now_playing_msg(chat_id, sent.id if thumb else cq.message.id)


    # ─────────────────────────────────────────
    #  ⏸  Pause
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^pause$"))
    async def cb_pause(_, cq: CallbackQuery):
        paused = await music_player.pause(cq.message.chat.id)
        if paused:
            await cq.answer("⏸ Paused")
        else:
            await cq.answer("Nothing is playing right now.", show_alert=True)


    # ─────────────────────────────────────────
    #  ▶  Resume
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^resume$"))
    async def cb_resume(_, cq: CallbackQuery):
        resumed = await music_player.resume(cq.message.chat.id)
        if resumed:
            await cq.answer("▶ Resumed")
        else:
            await cq.answer("Not paused or nothing playing.", show_alert=True)


    # ─────────────────────────────────────────
    #  ⏭  Skip
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^skip$"))
    async def cb_skip(_, cq: CallbackQuery):
        chat_id = cq.message.chat.id
        next_song = await music_player.skip(chat_id)
        if next_song:
            await cq.answer(f"⏭ Skipped → {next_song.title[:30]}")
            await cq.message.edit_text(
                "🎵 **Now Playing**\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"**{next_song.title}**\n\n"
                f"⏱ Duration : `{next_song.duration}`",
                reply_markup=buttons.now_playing_controls(),
            )
        else:
            await cq.answer("⏹ Queue is empty — stopped.")
            await cq.message.edit_text(
                "⏹ **Queue Empty**\nNo more songs in queue.",
                reply_markup=buttons.main_menu(),
            )


    # ─────────────────────────────────────────
    #  ⏹  Stop
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^stop$"))
    async def cb_stop(_, cq: CallbackQuery):
        await music_player.stop(cq.message.chat.id)
        await cq.answer("⏹ Stopped")
        await cq.message.edit_text(
            "⏹ **Stopped**\nVoice Chat music has been stopped.",
            reply_markup=buttons.main_menu(),
        )


    # ─────────────────────────────────────────
    #  🔊  Volume menu
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^volume_menu$"))
    async def cb_volume_menu(_, cq: CallbackQuery):
        vol = music_player.get_volume(cq.message.chat.id)
        await cq.message.edit_text(
            f"🔊 **Volume Control**\nCurrent: `{vol}`",
            reply_markup=buttons.volume_menu(),
        )
        await cq.answer()


    @app.on_callback_query(filters.regex(r"^vol_(\d+)$"))
    async def cb_set_volume(_, cq: CallbackQuery):
        vol = int(cq.data.split("_")[1])
        await music_player.set_volume(cq.message.chat.id, vol)
        await cq.answer(f"🔊 Volume set to {vol}")
        await cq.message.edit_text(
            f"🔊 **Volume set to {vol}**",
            reply_markup=buttons.volume_menu(),
        )


    # ─────────────────────────────────────────
    #  📜  Queue
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^show_queue$"))
    async def cb_show_queue(_, cq: CallbackQuery):
        chat_id = cq.message.chat.id
        queue = music_player.get_queue(chat_id)
        current = music_player.get_current(chat_id)

        if not queue and not current:
            await cq.answer("Queue is empty!", show_alert=True)
            return

        lines = []
        if current:
            lines.append(f"🎵 **Now:** `{current.title[:45]}`")
        if queue:
            lines.append("\n**Up Next:**")
            for i, s in enumerate(queue[:8]):
                lines.append(f"  `{i+1}.` {s.title[:40]}")

        queue_items = [{"title": s.title, "index": i} for i, s in enumerate(queue)]

        await cq.message.edit_text(
            "\n".join(lines) or "Queue is empty.",
            reply_markup=buttons.queue_buttons(queue_items),
        )
        await cq.answer()


    @app.on_callback_query(filters.regex(r"^remove_(\d+)$"))
    async def cb_remove_queue(_, cq: CallbackQuery):
        index = int(cq.data.split("_")[1])
        removed = music_player.remove_from_queue(cq.message.chat.id, index)
        if removed:
            await cq.answer("✅ Removed from queue")
        else:
            await cq.answer("Song not found.", show_alert=True)
        # Refresh queue view
        queue = music_player.get_queue(cq.message.chat.id)
        queue_items = [{"title": s.title, "index": i} for i, s in enumerate(queue)]
        await cq.message.edit_text(
            "📜 **Queue** (tap to remove):",
            reply_markup=buttons.queue_buttons(queue_items),
        )


    @app.on_callback_query(filters.regex("^clear_queue$"))
    async def cb_clear_queue(_, cq: CallbackQuery):
        music_player.clear_queue(cq.message.chat.id)
        await cq.answer("🗑 Queue cleared")
        await cq.message.edit_text(
            "🗑 **Queue cleared.**",
            reply_markup=buttons.main_menu(),
        )


    # ─────────────────────────────────────────
    #  ⚙  Settings
    # ─────────────────────────────────────────
    @app.on_callback_query(filters.regex("^settings$"))
    async def cb_settings(_, cq: CallbackQuery):
        await cq.message.edit_text(
            "⚙ **Settings**",
            reply_markup=buttons.settings_menu(),
        )
        await cq.answer()


    @app.on_callback_query(filters.regex("^bot_info$"))
    async def cb_bot_info(_, cq: CallbackQuery):
        await cq.message.edit_text(
            "ℹ️ **Bot Info**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 **TG Music Bot** by ET'AI x EVILTALKS\n"
            "🎵 Powered by pytgcalls + yt-dlp\n"
            "🚀 Ready to rock your VC!\n",
            reply_markup=buttons.settings_menu(),
        )
        await cq.answer()


    # ─────────────────────────────────────────
    #  Expose _awaiting_search for message handler
    # ─────────────────────────────────────────
    return _awaiting_search, _search_cache
