from pyrogram import Client, filters
import aiohttp
import base64
import logging

API_URL = "https://doodplay.net/provide/telegram/broadcast/add_user.php"

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

            # ✅ Balasan jika base64 valid
            await message.reply_text(
                f"Halo {user.first_name or 'Teman'}! 👋\n"
                "Terima kasih sudah memulai bot ini.\n\n"
                f"🔍 Data yang kamu kirim: `{decoded_text}`",
                quote=True
            )

        except Exception as e:
            # ⚠️ Balasan jika base64 tidak valid
            logging.warning(f"[DECODE ERROR] Parameter tidak valid: {encoded_param} ({e})")
            await message.reply_text(
                f"Halo {user.first_name or 'Teman'}! 👋\n"
                "⚠️ Parameter tidak valid atau bukan base64.",
                quote=True
            )

    else:
        # 🚀 Balasan jika tanpa parameter
        await message.reply_text(
            f"Halo {user.first_name or 'Teman'}! 👋\n"
            "Gunakan perintah /help untuk melihat fitur lain.",
            quote=True
        )
