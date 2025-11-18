from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup
import requests, logging, time, re

BASE = "https://avdbapi.com"
SEARCH_URL = "https://avdbapi.com/search/?wd="

# Temp hasil berdasarkan chat
temp_results = {}

# Temp flow judul
pending_title_flow = {}     # user_id -> {code, actor, video_url, slug, detail, title(optional)}


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
            return await status.edit("❌ Tidak ada data ditemukan.")

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
            return await status.edit("❌ Tidak ada hasil detail.")

        # Simpan untuk callback
        temp_results[message.chat.id] = results

        text = "📄 *Hasil ditemukan:*\n\n"
        for i, link in enumerate(results[:10], start=1):
            text += f"{i}. {link}\n"

        text += "\n📌 Tap tombol nomor di bawah."

        # Tombol inline
        buttons = []
        row = []

        for i in range(1, min(10, len(results)) + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"avdb_pick|{i}"))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await status.edit(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

    except Exception as e:
        logging.error(e)
        await status.edit("❌ Error mengambil data AVDB.")



# ==============================
# 🔘 CALLBACK: SCRAPE DETAIL
# ==============================
@Client.on_callback_query(filters.regex(r"^avdb_pick\|"))
async def avdb_choice(client, callback):

    try:
        _, num = callback.data.split("|")
        num = int(num)
        chat_id = callback.message.chat.id

        if chat_id not in temp_results:
            return await callback.answer("Data kadaluarsa.", show_alert=True)

        results = temp_results[chat_id]

        if num < 1 or num > len(results):
            return await callback.answer("Nomor tidak valid.", show_alert=True)

        detail_url = results[num - 1]

        await callback.answer("Mengambil detail...")

        # ==============================
        # 🔍 SCRAPE DETAIL
        # ==============================
        r = fetch_with_retry(detail_url)
        html = r.text

        # Slug dari URL
        slug = detail_url.rstrip("/").split("/")[-1]

        m = re.search(r"([A-Za-z0-9]+-\d+)", slug)
        movie_code = m.group(1).upper() if m else "Tidak ditemukan"

        # ===================
        # Ambil Actor:
        # ===================
        block = re.search(
            r"<span[^>]*>\s*Actor:\s*</span>(.*?)</div>",
            html,
            re.IGNORECASE | re.DOTALL
        )

        if block:
            names = re.findall(
                r'<a[^>]*class="tag"[^>]*>(.*?)</a>',
                block.group(1),
                re.IGNORECASE | re.DOTALL
            )
            actor = ", ".join([n.strip() for n in names]) if names else "Tidak ditemukan"
        else:
            actor = "Tidak ditemukan"

        # ===================
        # Video URL
        # ===================
        video_url = f"https://upload18.com/play/index/{slug}"

        # Hapus cache search
        del temp_results[chat_id]

        # ===================
        # Simpan untuk next step → input judul
        # ===================
        pending_title_flow[callback.from_user.id] = {
            "code": movie_code,
            "actor": actor,
            "video_url": video_url,
            "slug": slug,
            "detail": detail_url
        }

        # ===================
        # Kirim detail + button
        # ===================
        await callback.message.edit(
            f"✅ *Detail Film*\n\n"
            f"🎬 *Kode:* `{movie_code}`\n"
            f"👤 *Artis:* {actor}\n"
            f"🔗 *Video URL:* {video_url}\n\n"
            f"📄 Detail: {detail_url}\n\n"
            f"✏️ *Tambahkan judul?*",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Tambah Judul", callback_data="add_title"),
                    InlineKeyboardButton("❌ No Title", callback_data="no_title"),
                ]
            ]),
            disable_web_page_preview=True
        )

    except Exception as e:
        logging.error(e)
        await callback.answer("Terjadi error.", show_alert=True)



# ==============================
# ➕ CALLBACK TAMBAH JUDUL
# ==============================
@Client.on_callback_query(filters.regex("add_title"))
async def cb_add_title(client, callback):

    uid = callback.from_user.id

    if uid not in pending_title_flow:
        return await callback.answer("Data sudah kadaluarsa.", show_alert=True)

    await callback.message.reply("✏️ Silakan *ketik judul* yang ingin ditambahkan.")
    await callback.answer()



# ==============================
# ❌ CALLBACK TANPA JUDUL
# ==============================
@Client.on_callback_query(filters.regex("no_title"))
async def cb_no_title(client, callback):

    uid = callback.from_user.id

    if uid not in pending_title_flow:
        return await callback.answer("Data sudah kadaluarsa.", show_alert=True)

    pending_title_flow[uid]["title"] = None

    await callback.message.reply(
        "📸 Kamu memilih *tanpa judul*.\n"
        "Silakan *upload posternya sekarang.*"
    )

    await callback.answer()



# ==============================
# ✏️ USER MENGIRIM JUDUL
# ==============================
@Client.on_message(filters.text & ~filters.command(["avdb"]))
async def receive_title(client, message):

    uid = message.from_user.id

    if uid not in pending_title_flow:
        return  # bukan flow judul

    title = message.text.strip()
    pending_title_flow[uid]["title"] = title

    await message.reply(
        f"📝 *Judul disimpan:* {title}\n\n"
        "📸 Silakan *upload posternya sekarang.*"
    )
