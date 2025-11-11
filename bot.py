from pyrogram import Client, idle
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

API_ID = 21404483
API_HASH = "c60cf837b400cd918163820b314ef8d0"
BOT_TOKEN = "8489286033:AAEp8BDY2IiAFb4YmqXCKCIdxGcmV70iHQo"

app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

async def main():
    print("🤖 Bot sedang berjalan...")
    await app.start()
    try:
        await idle()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt detected, stopping bot...")
    finally:
        await app.stop()
        print("❌ Bot dihentikan dengan aman.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
