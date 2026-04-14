"""
╔══════════════════════════════════════════════╗
║         🎹 BUTTONS — Inline Keyboards        ║
╚══════════════════════════════════════════════╝
All InlineKeyboardMarkup layouts live here.
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ─────────────────────────────────────────────
#  🏠  MAIN MENU
# ─────────────────────────────────────────────
def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵  Play Music", callback_data="play_music")],
        [InlineKeyboardButton("📜  Queue",       callback_data="show_queue")],
        [
            InlineKeyboardButton("⏸  Pause",  callback_data="pause"),
            InlineKeyboardButton("▶  Resume", callback_data="resume"),
        ],
        [
            InlineKeyboardButton("⏭  Skip",  callback_data="skip"),
            InlineKeyboardButton("⏹  Stop",  callback_data="stop"),
        ],
        [InlineKeyboardButton("🔊  Volume",   callback_data="volume_menu")],
        [InlineKeyboardButton("⚙  Settings",  callback_data="settings")],
    ])


# ─────────────────────────────────────────────
#  🔊  VOLUME CONTROL
# ─────────────────────────────────────────────
def volume_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔈  Low  (40)",    callback_data="vol_40"),
            InlineKeyboardButton("🔉  Medium (100)", callback_data="vol_100"),
            InlineKeyboardButton("🔊  High  (160)",  callback_data="vol_160"),
        ],
        [InlineKeyboardButton("🔙  Back", callback_data="main_menu")],
    ])


# ─────────────────────────────────────────────
#  🎧  NOW PLAYING CONTROLS
# ─────────────────────────────────────────────
def now_playing_controls() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸",  callback_data="pause"),
            InlineKeyboardButton("▶",  callback_data="resume"),
            InlineKeyboardButton("⏭",  callback_data="skip"),
            InlineKeyboardButton("⏹",  callback_data="stop"),
        ],
        [
            InlineKeyboardButton("📜 Queue",    callback_data="show_queue"),
            InlineKeyboardButton("🔊 Volume",   callback_data="volume_menu"),
        ],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
    ])


# ─────────────────────────────────────────────
#  🔍  SEARCH RESULTS  (dynamic)
# ─────────────────────────────────────────────
def search_results(results: list) -> InlineKeyboardMarkup:
    """
    results = [{"title": "...", "id": "youtube_id", "duration": "3:45"}, ...]
    """
    rows = []
    for i, r in enumerate(results[:5]):
        label = f"{i+1}. {r['title'][:40]}  [{r['duration']}]"
        rows.append([InlineKeyboardButton(label, callback_data=f"play_{r['id']}")])
    rows.append([InlineKeyboardButton("❌  Cancel", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  📜  QUEUE  (dynamic)
# ─────────────────────────────────────────────
def queue_buttons(queue: list) -> InlineKeyboardMarkup:
    """
    queue = [{"title": "...", "index": 0}, ...]
    """
    rows = []
    for item in queue[:8]:
        label = f"❌  {item['index']+1}. {item['title'][:35]}"
        rows.append([InlineKeyboardButton(label, callback_data=f"remove_{item['index']}")])
    rows.append([
        InlineKeyboardButton("🔙 Back", callback_data="main_menu"),
        InlineKeyboardButton("🗑 Clear All", callback_data="clear_queue"),
    ])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  ❌  ERROR  (retry / back)
# ─────────────────────────────────────────────
def error_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Retry",   callback_data="play_music"),
            InlineKeyboardButton("🏠 Menu",    callback_data="main_menu"),
        ]
    ])


# ─────────────────────────────────────────────
#  ⚙  SETTINGS
# ─────────────────────────────────────────────
def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️  Bot Info",    callback_data="bot_info")],
        [InlineKeyboardButton("🔙  Back",        callback_data="main_menu")],
    ])
