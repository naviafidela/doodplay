from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import base64
import logging

API_URL = "https://doodplay.net/provide/telegram/broadcast/add_user.php"
API_JAVBOT = "https://doodplay.net/provide/telegram/javbot/database-api.php"


@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    text = message.text.strip()

    # === Kirim data user ke API utama ===
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
                logging.info(f"[API_USER] {user.id} -> {result}")
        except Exception as e:
            logging.error(f"[API_USER ERROR] {user.id}: {e}")

    # === Cek apakah ada parameter base64 ===
    parts = text.split(" ", 1)
    if len(parts) > 1:
        encoded_param = parts[1]

        try:
            decoded_bytes = base64.b64decode(encoded_param)
            decoded_text = decoded_bytes.decode("utf-8").strip()

            # === Ambil data film dari API JAVBOT ===
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{API_JAVBOT}?shortcode={decoded_text}&limit=1") as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            data_list = result.get("data", [])

                            if data_list:
                                movie = data_list[0]
                                title = movie.get("title", "Tanpa Judul")
                                poster = movie.get("poster", "")
                                url = movie.get("url", "#")
                                code = movie.get("movie_code", "")
                                shortcode = movie.get("shortcode", "")

                                # === Inline Button ===
                                buttons = [
                                    [InlineKeyboardButton("🎬 Tonton Sekarang", url=url)]
                                ]

                                # === Kirim detail film ===
                                await message.reply_photo(
                                    photo=poster,
                                    caption=(
                                        f"<b>{title}</b>\n"
                                        f"💠 Code: <code>{code}</code>\n"
                                        f"🔖 Shortcode: <code>{shortcode}</code>"
                                    ),
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    quote=True
                                )
                                return

                            else:
                                await message.reply_text(
                                    f"❌ Tidak ditemukan data untuk shortcode `{decoded_text}`.",
                                    quote=True
                                )
                                return

                        else:
                            await message.reply_text(
                                f"⚠️ Gagal mengambil data dari server (status {resp.status}).",
                                quote=True
                            )
                            return

                except Exception as e:
                    logging.error(f"[API_JAVBOT ERROR] {e}")
                    await message.reply_text(
                        f"⚠️ Gagal menghubungi server JAVBOT.\n{e}",
                        quote=True
                    )
                    return

        except Exception as e:
            logging.warning(f"[DECODE ERROR] Parameter tidak valid: {encoded_param} ({e})")
            await message.reply_text(
                "⚠️ Parameter tidak valid atau bukan base64.",
                quote=True
            )
            return

    # === Jika tidak ada parameter (start biasa) ===
    await message.reply_text(
        "👋 Selamat datang di <b>JapanBestBot</b>!\n"
        "Gunakan perintah /help untuk melihat fitur lain.",
        parse_mode=ParseMode.HTML,
        quote=True
    )
