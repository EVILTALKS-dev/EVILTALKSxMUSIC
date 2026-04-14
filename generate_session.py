"""
╔══════════════════════════════════════════════╗
║   🔑  GENERATE STRING SESSION                ║
║   Run this ONCE locally, copy the output     ║
║   into STRING_SESSION env var on Railway.    ║
╚══════════════════════════════════════════════╝

Usage:
    python generate_session.py

You'll be prompted for:
  • API_ID
  • API_HASH
  • Phone number
  • OTP from Telegram

The script prints the session string — keep it SECRET.
"""

import asyncio
from pyrogram import Client


async def main():
    print("=" * 50)
    print("   🎵 TG Music Bot — Session Generator")
    print("=" * 50)

    api_id   = int(input("Enter API_ID   : ").strip())
    api_hash = input("Enter API_HASH : ").strip()

    async with Client(
        name=":memory:",
        api_id=api_id,
        api_hash=api_hash,
    ) as client:
        session = await client.export_session_string()

    print("\n" + "=" * 50)
    print("✅  Your STRING_SESSION:")
    print()
    print(session)
    print()
    print("=" * 50)
    print("⚠️  Keep this PRIVATE — it grants full account access!")
    print("Copy it into your Railway / .env as STRING_SESSION=")


if __name__ == "__main__":
    asyncio.run(main())
