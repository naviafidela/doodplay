from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

@Client.on_message(filters.command("avdb", prefixes="/"))
def avdb_handler(client, message):
    # Ambil argumen setelah /avdb
    args = message.text.split(maxsplit=1)

    # Jika tidak ada query
    if len(args) == 1:
        message.reply("❗ Tolong masukkan query. Contoh: `/avdb MIDV-855`", quote=True)
        return

    query = args[1].strip()
    url = f"https://avdbapi.com/search/?wd={query}"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
    except Exception:
        message.reply("⚠️ Gagal mengambil data dari API.")
        return

    # Validasi hasil
    if not data or "data" not in data or len(data["data"]) == 0:
        message.reply("❌ Tidak ada hasil ditemukan.")
        return

    results = data["data"]
    text_lines = []
    buttons = []

    # Loop hasil
    for i, item in enumerate(results, start=1):
        link = item.get("url", "")
        text_lines.append(f"{i}. {link}")
        buttons.append([InlineKeyboardButton(str(i), url=link)])

    reply_text = "\n".join(text_lines)

    message.reply(
        reply_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )
