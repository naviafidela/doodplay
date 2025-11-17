from pyrogram import Client, filters
from bs4 import BeautifulSoup
import requests, logging, time

BASE = "https://avdbapi.com"
SEARCH_URL = "https://avdbapi.com/search/?wd="

# Menyimpan hasil search untuk user tertentu
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
@Client.on_message(filters.command("avdb"))
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
            return await status.edit(
                "❌ Tidak ada data ditemukan.",
                disable_web_page_preview=True
            )

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
            return await status.edit(
                "❌ Tidak ada hasil detail.",
                disable_web_page_preview=True
            )

        # Simpan hasil search
        temp_results[message.chat.id] = results

        # Buat list numerik
        txt = "📄 *Hasil ditemukan:*\n\n"
        for i, link in enumerate(results[:10], start=1):
            txt += f"{i}. {link}\n"

        txt += "\n📌 *Ketik angka (1–10) untuk memilih.*"

        await status.edit(
            txt,
            disable_web_page_preview=True
        )

    except Exception as e:
        logging.error(e)
        await status.edit(
            "❌ Terjadi kesalahan mengambil data.",
            disable_web_page_preview=True
        )


# ==============================
# 🔢 TANGGAPAN ANGKA USER
# ==============================
@Client.on_message(filters.text & filters.regex(r"^\d+$"))
async def avdb_number_reply(client, message):

    chat_id = message.chat.id
    number = int(message.text.strip())

    # Pastikan ada hasil untuk chat ini
    if chat_id not in temp_results:
        return

    results = temp_results[chat_id]

    # Cek nomor valid
    if number < 1 or number > len(results):
        return await message.reply(
            "❌ Nomor di luar pilihan.",
            quote=True,
            disable_web_page_preview=True
        )

    selected_link = results[number - 1]

    await message.reply(
        f"🔗 *Link detail pilihanmu:*\n{selected_link}",
        quote=True,
        disable_web_page_preview=True
    )

    # Hapus data
    del temp_results[chat_id]
