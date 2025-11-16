from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import requests
import logging

AVDB_SEARCH_URL = "https://avdbapi.com/search/?wd="


@Client.on_message(filters.command("avdb"))
async def avdb_search(client, message):
    """Melakukan pencarian AVDB berdasarkan query dari user."""

    # Ambil query setelah command
    parts = message.text.split(maxsplit=1)

    # Jika /avdb saja (tanpa query)
    if len(parts) == 1:
        await message.reply(
            "🔎 Tolong masukkan query.\n\n"
            "Contoh:\n`/avdb MIDV-855`",
            quote=True
        )
        return

    query = parts[1].strip()

    status_msg = await message.reply("⏳ Sedang mencari di AVDB...", quote=True)

    try:
        # Request ke API
        response = requests.get(AVDB_SEARCH_URL + query)
        data = response.json()

        # Validasi hasil
        if not data or "data" not in data or not data["data"]:
            await status_msg.edit("❌ Tidak ada hasil ditemukan dari pencarian tersebut.")
            return

        results = data["data"]

        # Buat daftar link text
        reply_text = "📄 *Hasil Pencarian:*\n\n"
        buttons = []

        for i, item in enumerate(results, start=1):
            link = item.get("url")
            if not link:
                continue

            reply_text += f"{i}. {link}\n"

            # Tambah tombol
            buttons.append([InlineKeyboardButton(str(i), callback_data=f"avdb_select|{link}")])

        # Kirim hasil + tombol
        await status_msg.edit(
            reply_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logging.error(f"AVDB search error: {e}")
        await status_msg.edit("❌ Terjadi kesalahan saat mengambil data dari AVDB.")


@Client.on_callback_query(filters.regex(r"^avdb_select\|"))
async def avdb_selected(client, callback: CallbackQuery):
    """User memilih salah satu link dari hasil pencarian."""

    try:
        # Pecah callback data
        _, link = callback.data.split("|", 1)

        await callback.message.reply(
            f"🔗 *Link yang kamu pilih:*\n{link}",
            quote=True
        )

        await callback.answer("Dipilih!")
    except Exception as e:
        logging.error(f"Callback error: {e}")
        await callback.answer("Terjadi kesalahan.", show_alert=True)
