from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
import logging

BASE = "https://avdbapi.com"
SEARCH_URL = "https://avdbapi.com/search/?wd="


@Client.on_message(filters.command("avdb"))
async def avdb_search(client, message):
    """Cari hasil AVDB dan ambil link /detail/..."""

    parts = message.text.split(maxsplit=1)

    # Jika /avdb tanpa query
    if len(parts) == 1:
        await message.reply(
            "🔎 Tolong masukkan query.\n\nContoh:\n`/avdb MIDV-855`",
            quote=True
        )
        return

    query = parts[1].strip()
    status_msg = await message.reply("⏳ Sedang mencari di AVDB...", quote=True)

    try:
        # Ambil halaman HTML
        r = requests.get(SEARCH_URL + query, timeout=10)
        html = r.text

        soup = BeautifulSoup(html, "lxml")

        # Ambil semua baris hasil pencarian
        rows = soup.select("table tbody tr")
        if not rows:
            await status_msg.edit("❌ Tidak ada data ditemukan.")
            return

        results = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # Kolom kedua adalah <a href="/detail/...">
            detail_a = cells[1].find("a")
            if not detail_a:
                continue

            relative = detail_a.get("href")  # contoh: /detail/midv-855-uncensored-leak/
            if not relative.startswith("/detail/"):
                continue

            full_url = BASE + relative
            results.append(full_url)

        if not results:
            await status_msg.edit("❌ Tidak ada result detail ditemukan.")
            return

        # Buat daftar text
        reply_text = "📄 *Hasil Pencarian:* \n\n"
        buttons = []

        for i, link in enumerate(results, start=1):
            reply_text += f"{i}. {link}\n"
            buttons.append(
                [InlineKeyboardButton(str(i), callback_data=f"avdb_select|{link}")]
            )

        await status_msg.edit(
            reply_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logging.error(f"AVDB scrape error: {e}")
        await status_msg.edit("❌ Error saat memproses HTML AVDB.")


# Klik tombol pilihan
@Client.on_callback_query(filters.regex(r"^avdb_select\|"))
async def avdb_selected(client, callback):
    try:
        _, link = callback.data.split("|", 1)

        await callback.message.reply(
            f"🔗 *Link detail yang kamu pilih:*\n{link}",
            quote=True
        )
        await callback.answer("Diterima!")

    except Exception as e:
        logging.error(f"Callback error: {e}")
        await callback.answer("Terjadi kesalahan.", show_alert=True)
