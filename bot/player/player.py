"""
╔══════════════════════════════════════════════╗
║      🎬  PLAYER — YouTube + Streaming        ║
╚══════════════════════════════════════════════╝
Handles:
  • YouTube search via yt-dlp
  • Audio download to temp file
  • Per-chat queue management
  • pytgcalls stream control
"""

import asyncio
import os
import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional

import yt_dlp
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality
from pytgcalls.exceptions import (
    NotInCallError,
    AlreadyJoinedError,
    NoActiveGroupCall,
)

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ─────────────────────────────────────────────
#  📦  Song dataclass
# ─────────────────────────────────────────────
@dataclass
class Song:
    title: str
    url: str          # YouTube watch URL
    video_id: str
    duration: str     # "mm:ss"
    duration_sec: int
    thumbnail: str    # thumbnail URL
    requested_by: int # user_id
    file_path: Optional[str] = None   # local downloaded file


# ─────────────────────────────────────────────
#  🗂  Per-chat state
# ─────────────────────────────────────────────
@dataclass
class ChatState:
    queue: list[Song] = field(default_factory=list)
    current: Optional[Song] = None
    is_playing: bool = False
    is_paused: bool = False
    volume: int = 100
    now_playing_msg_id: Optional[int] = None   # message id to edit


# ─────────────────────────────────────────────
#  🔍  YouTube Search
# ─────────────────────────────────────────────
YDL_SEARCH_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "default_search": "ytsearch5",
    "skip_download": True,
}

def _fmt_duration(sec: int) -> str:
    if not sec:
        return "Live"
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


async def search_youtube(query: str) -> list[dict]:
    """
    Returns up to 5 results:
      [{"title", "id", "duration", "thumbnail", "url"}, ...]
    Runs yt-dlp in executor to avoid blocking the event loop.
    """
    def _search():
        with yt_dlp.YoutubeDL(YDL_SEARCH_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get("entries", [])
            results = []
            for e in entries[:5]:
                if not e:
                    continue
                vid_id = e.get("id") or e.get("url", "")
                results.append({
                    "title":     e.get("title", "Unknown")[:60],
                    "id":        vid_id,
                    "duration":  _fmt_duration(e.get("duration") or 0),
                    "duration_sec": e.get("duration") or 0,
                    "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
                    "url":       f"https://www.youtube.com/watch?v={vid_id}",
                })
            return results

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _search)


# ─────────────────────────────────────────────
#  ⬇️  Audio Download
# ─────────────────────────────────────────────
YDL_DOWNLOAD_OPTS_TEMPLATE = {
    "quiet": True,
    "no_warnings": True,
    "format": "bestaudio/best",
    "outtmpl": "",          # filled at runtime
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}


async def download_audio(song: Song) -> str:
    """
    Downloads audio for `song`, returns local file path (.mp3).
    Skips download if file already exists.
    """
    safe_name = re.sub(r'[^\w]', '_', song.video_id)
    out_path = os.path.join(DOWNLOAD_DIR, safe_name)
    mp3_path = out_path + ".mp3"

    if os.path.exists(mp3_path):
        return mp3_path

    opts = dict(YDL_DOWNLOAD_OPTS_TEMPLATE)
    opts["outtmpl"] = out_path

    def _dl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([song.url])

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _dl)
    return mp3_path


# ─────────────────────────────────────────────
#  🎛  MusicPlayer — singleton per bot instance
# ─────────────────────────────────────────────
class MusicPlayer:
    """
    Central controller.  One instance shared across the app.
    chat_states: {chat_id: ChatState}
    """

    def __init__(self):
        self.call_client: Optional[PyTgCalls] = None   # set after assistant init
        self._states: dict[int, ChatState] = {}

    def _state(self, chat_id: int) -> ChatState:
        if chat_id not in self._states:
            self._states[chat_id] = ChatState()
        return self._states[chat_id]

    # ── Queue helpers ──────────────────────────
    def add_to_queue(self, chat_id: int, song: Song) -> int:
        """Appends song to queue. Returns new queue length."""
        state = self._state(chat_id)
        state.queue.append(song)
        return len(state.queue)

    def get_queue(self, chat_id: int) -> list[Song]:
        return self._state(chat_id).queue

    def remove_from_queue(self, chat_id: int, index: int) -> bool:
        state = self._state(chat_id)
        if 0 <= index < len(state.queue):
            state.queue.pop(index)
            return True
        return False

    def clear_queue(self, chat_id: int):
        self._state(chat_id).queue.clear()

    def get_current(self, chat_id: int) -> Optional[Song]:
        return self._state(chat_id).current

    def is_playing(self, chat_id: int) -> bool:
        return self._state(chat_id).is_playing

    def is_paused(self, chat_id: int) -> bool:
        return self._state(chat_id).is_paused

    # ── Core stream actions ────────────────────
    async def play(self, chat_id: int, song: Song):
        """Download and stream the song in the group VC."""
        state = self._state(chat_id)

        # Download audio
        logger.info(f"[{chat_id}] Downloading: {song.title}")
        file_path = await download_audio(song)
        song.file_path = file_path

        state.current  = song
        state.is_playing = True
        state.is_paused  = False

        try:
            await self.call_client.play(
                chat_id,
                MediaStream(
                    file_path,
                    audio_parameters=AudioQuality.HIGH,
                )
            )
            logger.info(f"[{chat_id}] Now playing: {song.title}")
        except AlreadyJoinedError:
            # Already in call — just change stream
            await self.call_client.change_stream(
                chat_id,
                MediaStream(file_path, audio_parameters=AudioQuality.HIGH)
            )
        except NoActiveGroupCall:
            state.is_playing = False
            raise RuntimeError("❌ No active Voice Chat in this group.\nPlease start a Voice Chat first.")

    async def pause(self, chat_id: int) -> bool:
        state = self._state(chat_id)
        if state.is_playing and not state.is_paused:
            await self.call_client.pause(chat_id)
            state.is_paused = True
            return True
        return False

    async def resume(self, chat_id: int) -> bool:
        state = self._state(chat_id)
        if state.is_paused:
            await self.call_client.resume(chat_id)
            state.is_paused = False
            return True
        return False

    async def skip(self, chat_id: int) -> Optional[Song]:
        """
        Skip current song. Plays next in queue if available.
        Returns next song or None.
        """
        state = self._state(chat_id)
        if state.queue:
            next_song = state.queue.pop(0)
            await self.play(chat_id, next_song)
            return next_song
        else:
            await self.stop(chat_id)
            return None

    async def stop(self, chat_id: int):
        state = self._state(chat_id)
        state.is_playing = False
        state.is_paused  = False
        state.current    = None
        state.queue.clear()
        try:
            await self.call_client.leave_call(chat_id)
        except (NotInCallError, Exception):
            pass

    async def set_volume(self, chat_id: int, volume: int):
        state = self._state(chat_id)
        state.volume = max(1, min(200, volume))
        try:
            await self.call_client.change_volume_call(chat_id, state.volume)
        except Exception as e:
            logger.warning(f"Volume set failed: {e}")

    def get_volume(self, chat_id: int) -> int:
        return self._state(chat_id).volume

    def set_now_playing_msg(self, chat_id: int, msg_id: int):
        self._state(chat_id).now_playing_msg_id = msg_id

    def get_now_playing_msg(self, chat_id: int) -> Optional[int]:
        return self._state(chat_id).now_playing_msg_id


# ── Singleton export ──────────────────────────
music_player = MusicPlayer()
