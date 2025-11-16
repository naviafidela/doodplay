from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup
import requests
import logging
import time

BASE = "https://avdbapi.com"
SEARCH_URL = "https://avdbapi.com/search/?wd="


# ==============================
# 🔄 REQUEST DENGAN RETRY
# ==============================
def fetch_with_retry(url, retries=3, timeout=25):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    for i in range(retries):
        try:
            return requests.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            if i == retries - 1:
                raise e
            time.sleep(1.5)  # tunggu sebelum retry


# ==============================
# 🔍 /avdb SEARCH
# ==============================
@Client.on_message(filters.command("avdb"))
async def avdb_search(client, message):
    """Cari hasil AVDB dan ambil list /detail/…"""

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
        # Ambil HTML dengan retry
        r = fetch_with_retry(SEARCH_URL + query)
        html = r.text

        soup = BeautifulSoup(html, "lxml")

        # Ambil baris hasil tabel
        rows = soup.select("table tbody tr")
        if not rows:
            await status_msg.edit("❌ Tidak ada data ditemukan.")
            return

        results = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            detail_a = cells[1].find("a")
            if not detail_a:
                continue

            href = detail_a.get("href")  # contoh: /detail/midv-855-uncensored-leak/
            if not href.startswith("/detail/"):
                continue

            full_url = BASE + href
            results.append(full_url)

        if not results:
            await status_msg.edit("❌ Tidak ada result detail ditemukan.")
            return

        # Susun balasan
        reply_text = "📄 *Hasil Pencarian:*\n\n"
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
        await status_msg.edit("❌ Error saat memproses data dari AVDB.")


# ==============================
# 🔘 Callback tombol
# ==============================
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
