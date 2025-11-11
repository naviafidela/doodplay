from pyrogram import Client, filters
import aiohttp

API_URL = "https://doodplay.net/provide/telegram/broadcast/add_user.php"

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user

    # Data user
    data = {
        "user_id": user.id,
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or ""
    }

    # Kirim ke server kamu (asynchronous HTTP request)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, data=data) as resp:
                result = await resp.text()
                print(f"[INFO] Data terkirim ke API: {result}")
        except Exception as e:
            print(f"[ERROR] Gagal mengirim data ke API: {e}")

    # Kirim balasan ke user
    await message.reply_text(
        f"Halo {user.first_name or 'Teman'}! 👋\n"
        "Kamu sudah terdaftar untuk menerima broadcast bot ini.\n\n"
        "Gunakan perintah /help untuk melihat fitur lain."
    )
