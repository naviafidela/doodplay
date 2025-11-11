from pyrogram import Client, idle
import asyncio
import logging

# Aktifkan logging agar bisa melihat pesan status
logging.basicConfig(level=logging.INFO)

# Ganti dengan kredensial bot Anda
API_ID = 21404483                # Dapatkan dari https://my.telegram.org
API_HASH = "c60cf837b400cd918163820b314ef8d0" # Dapatkan dari https://my.telegram.org
BOT_TOKEN = "8489286033:AAEp8BDY2IiAFb4YmqXCKCIdxGcmV70iHQo"  # Dapatkan dari @BotFather

# Inisialisasi Client Pyrogram
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")  # otomatis muat semua handler dari folder plugins/
)

async def main():
    print("🤖 Bot sedang berjalan...")
    await app.start()
    await idle()  # tetap berjalan menunggu pesan
    await app.stop()
    print("❌ Bot dihentikan.")

if __name__ == "__main__":
    asyncio.run(main())
