from pyrogram import Client, filters
from pyrogram.utils import escape_html
import aiohttp
import base64
import logging

API_URL = "https://doodplay.net/provide/telegram/broadcast/add_user.php"
API_JAVBOT = "https://doodplay.net/provide/telegram/javbot/database-api.php"

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    text = message.text.strip()

    # === Kirim data user ke API ===
    data = {
        "user_id": user.id,
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or ""
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, data=data, timeout=5) as resp:
                result = await resp.text()
                logging.info(f"[API] {user.id} -> {result}")
        except Exception as e:
            logging.error(f"[API ERROR] Gagal kirim data user {user.id}: {e}")

    # === Cek apakah ada parameter base64 ===
    parts = text.split(" ", 1)

    if len(parts) > 1:
        encoded_param = parts[1]

        try:
            # Decode base64
            decoded_bytes = base64.b64decode(encoded_param)
            decoded_text = decoded_bytes.decode("utf-8")

            # Ambil data dari API JAVBOT
            async with aiohttp.ClientSession() as session:
                url = f"{API_JAVBOT}?shortcode={decoded_text}&limit=1"
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        json_data = await resp.json()
                        if json_data["data"]:
                            item = json_data["data"][0]

                            title = escape_html(item["title"])
                            code = escape_html(item["movie_code"])
                            link = escape_html(item["url"])
                            poster = item["poster"]

                            caption = (
                                f"<b>{title}</b>\n"
                                f"🎬 Code: <code>{code}</code>\n"
                                f"🌐 <a href='{link}'>Tonton Sekarang</a>"
                            )

                            # kirim poster dan caption
                            await message.reply_photo(
                                photo=poster,
                                caption=caption,
                                parse_mode="HTML"
                            )
                            return
                        else:
                            await message.reply_text("❌ Data tidak ditemukan di database JAVBOT.")
                    else:
                        await message.reply_text(f"⚠️ Gagal menghubungi server JAVBOT.\nStatus: {resp.status}")

        except Exception as e:
            logging.warning(f"[DECODE ERROR] Parameter tidak valid: {encoded_param} ({e})")
            await message.reply_text(
                "⚠️ Parameter tidak valid atau bukan base64.",
                quote=True
            )
    else:
        await message.reply_text(
            f"Halo {user.first_name or 'Teman'}! 👋\n"
            "Gunakan perintah /help untuk melihat fitur lain.",
            quote=True
        )
