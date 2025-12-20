from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import base64
import logging

API_URL = "https://doodplay.net/api/telegram/broadcast/add_user.php"
API_JAVBOT = "https://doodplay.net/api/telegram/javbot/javbot-api.php"

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
            decoded_text = decoded_bytes.decode("utf-8").strip()

            # === Ambil data dari API JAVBOT ===
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{API_JAVBOT}?shortcode={decoded_text}&limit=1") as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            data_list = result.get("data", [])

                            if data_list:
                            movie = data_list[0]
                        
                            raw_title = movie.get("title", "").strip()
                            raw_code  = movie.get("movie_code", "").strip()
                            actor     = movie.get("actor", "Unknown")
                            poster    = movie.get("poster", "")
                            url       = movie.get("url", "#")
                            shortcode = movie.get("shortcode", "")
                        
                            # ===============================
                            # BERSIHKAN MOVIE CODE
                            # ===============================
                            clean_code = raw_code
                            match = re.match(r'^([A-Z]+-\d+)', raw_code)
                            if match:
                                clean_code = match.group(1)
                        
                            # ===============================
                            # TITLE FINAL (SAMA SEPERTI PHP)
                            # ===============================
                            if raw_title:
                                title_final = raw_title
                            else:
                                title_final = f"[{clean_code}]"
                        
                            # ===============================
                            # INLINE BUTTON
                            # ===============================
                            buttons = InlineKeyboardMarkup([
                                [InlineKeyboardButton("ᴛᴏɴᴛᴏɴ ᴠɪᴅᴇᴏ ꜱᴇᴋᴀʀᴀɴɢ", url=url)]
                            ])
                        
                            # ===============================
                            # KIRIM KE TELEGRAM
                            # ===============================
                            await message.reply_photo(
                                photo=poster,
                                caption=(
                                    f"<b>{title_final}</b>\n"
                                    f"💠 Code: <code>{clean_code}</code>\n"
                                    f"🔖 Shortcode: <code>{shortcode}</code>"
                                ),
                                parse_mode=ParseMode.HTML,
                                reply_markup=buttons,
                                quote=True
                            )
                            else:
                                await message.reply_text(
                                    f"❌ Data tidak ditemukan untuk shortcode <code>{decoded_text}</code>.",
                                    parse_mode=ParseMode.HTML,
                                    quote=True
                                )

                        else:
                            await message.reply_text(
                                f"⚠️ Gagal mengambil data dari server (status {resp.status}).",
                                quote=True
                            )
                except Exception as e:
                    logging.error(f"[API_JAVBOT ERROR] {e}")
                    await message.reply_text(
                        f"⚠️ Gagal menghubungi server JAVBOT.\n<code>{e}</code>",
                        parse_mode=ParseMode.HTML,
                        quote=True
                    )

        except Exception as e:
            # ⚠️ Base64 tidak valid
            logging.warning(f"[DECODE ERROR] Parameter tidak valid: {encoded_param} ({e})")
            await message.reply_text(
                "⚠️ Parameter tidak valid atau bukan base64.",
                quote=True
            )

    else:
        # 🚀 Tanpa parameter (pesan singkat saja)
        await message.reply_text(
            "Gunakan /help untuk melihat fitur lain atau kirim tautan yang valid.",
            quote=True
        )
