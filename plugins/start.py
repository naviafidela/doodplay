from pyrogram import Client, filters

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user = message.from_user.first_name or "Teman"
    await message.reply_text(
        f"Halo {user}! 👋\n"
        "Saya adalah bot Pyrogram sederhana.\n\n"
        "Gunakan perintah /help untuk melihat daftar perintah."
    )
