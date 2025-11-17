from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup
import requests, logging, time

BASE = "https://avdbapi.com"
SEARCH_URL = "https://avdbapi.com/search/?wd="

# Simpan hasil sementara berdasarkan chat_id
temp_results = {}


# ==============================
# 🔄 REQUEST DENGAN RETRY
# ==============================
def fetch_with_retry(url, retries=3, timeout=25):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for i in range(retries):
        try:
            return requests.get(url, headers=headers, timeout=timeout)
        except:
            if i == retries - 1:
                raise
            time.sleep(1.5)


# ==============================
# 🔍 /avdb SEARCH
# ==============================
@Client.on_message(filters.command("avdbb"))
async def avdb_search(client, message):

    parts = message.text.split(maxsplit=1)
    if len(parts) == 1:
        return await message.reply(
            "🔎 Contoh: `/avdb MIDV-855`",
            quote=True,
            disable_web_page_preview=True
        )

    query = parts[1].strip()
    status = await message.reply(
        "⏳ Mencari di AVDB...",
        quote=True,
        disable_web_page_preview=True
    )

    try:
        r = fetch_with_retry(SEARCH_URL + query)
        soup = BeautifulSoup(r.text, "lxml")

        rows = soup.select("table tbody tr")
        if not rows:
            return await status.edit("❌ Tidak ada data ditemukan.", disable_web_page_preview=True)

        results = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            a = cells[1].find("a")
            if not a:
                continue

            href = a.get("href")
            if href.startswith("/detail/"):
                results.append(BASE + href)

        if not results:
            return await status.edit("❌ Tidak ada hasil detail.", disable_web_page_preview=True)

        # Simpan hasil untuk callback nanti
        temp_results[message.chat.id] = results

        text = "📄 *Hasil ditemukan:*\n\n"

        for i, link in enumerate(results[:10], start=1):
            text += f"{i}. {link}\n"

        text += "\n📌 Pilih nomor dengan tap tombol di bawah."

        # ========== INLINE BUTTON 4 KOLOM ==========
        buttons = []
        row = []

        for i in range(1, min(10, len(results)) + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"avdb_pick|{i}"))
            if len(row) == 4:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        # ===========================================

        await status.edit(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

    except Exception as e:
        logging.error(e)
        await status.edit("❌ Error mengambil data AVDB.", disable_web_page_preview=True)



# ==============================
# 🔘 CALLBACK: USER PILIH NOMOR
# ==============================
@Client.on_callback_query(filters.regex(r"^avdb_pick\|"))
async def avdb_choice(client, callback):

    try:
        _, num = callback.data.split("|")
        num = int(num)

        chat_id = callback.message.chat.id

        # Pastikan ada data
        if chat_id not in temp_results:
            return await callback.answer("Data tidak ditemukan.", show_alert=True)

        results = temp_results[chat_id]

        if num < 1 or num > len(results):
            return await callback.answer("Nomor tidak valid.", show_alert=True)

        # Edit pesan menjadi: "Anda telah memilih nomor X"
        await callback.message.edit(
            f"✅ Anda telah memilih *nomor {num}*",
            disable_web_page_preview=True
        )

        await callback.answer("Diproses!")

        # Hapus data (opsional)
        del temp_results[chat_id]

    except Exception as e:
        logging.error(e)
        await callback.answer("Terjadi error.", show_alert=True)
