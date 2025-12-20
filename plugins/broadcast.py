from pyrogram import Client, filters
import requests
import logging

# Ganti URL API kamu
API_GET_URL = "https://doodplay.net/api/telegram/broadcast/add_user.php?view=json"
API_DELETE_URL = "https://doodplay.net/api/telegram/broadcast/delete_user.php"

@Client.on_message(filters.command("broadcast") & filters.reply)
async def broadcast_message(client, message):
    """Kirim pesan ke semua user yang tersimpan di database, hapus jika gagal"""

    # Hanya admin yang boleh broadcast
    ADMIN_ID = [1309757945]  # Ganti dengan user_id kamu
    if message.from_user.id not in ADMIN_ID:
        await message.reply("🚫 Kamu tidak punya izin untuk melakukan broadcast.")
        return

    target_message = message.reply_to_message
    if not target_message:
        await message.reply("❗ Reply ke pesan yang ingin dikirim, lalu ketik /broadcast")
        return

    status_msg = await message.reply("📢 Mengirim broadcast ke semua pengguna...")

    try:
        # Ambil semua user_id dari API
        response = requests.get(API_GET_URL)
        users = response.json()

        if not users or not isinstance(users, list):
            await status_msg.edit("❌ Gagal mengambil data user dari server (format tidak valid).")
            return

        success_count = 0
        failed_count = 0

        # Kirim pesan ke setiap user
        for user in users:
            user_id = user.get("user_id")
            if not user_id:
                continue

            try:
                await target_message.copy(int(user_id))
                success_count += 1
            except Exception as e:
                logging.warning(f"Gagal kirim ke {user_id}: {e}")
                failed_count += 1

                # Hapus user dari database via API
                try:
                    requests.post(API_DELETE_URL, data={"user_id": user_id})
                except Exception as err:
                    logging.error(f"Gagal menghapus user {user_id}: {err}")

        await status_msg.edit(
            f"✅ Broadcast selesai!\n\n"
            f"📬 Berhasil: {success_count}\n"
            f"❌ Gagal & dihapus: {failed_count}"
        )

    except Exception as e:
        logging.error(f"Broadcast error: {e}")
        await status_msg.edit("❌ Terjadi kesalahan saat broadcast.")

@Client.on_message(filters.command("users"))
async def total_users(client, message):
    """Menampilkan jumlah user yang tersimpan di database"""

    ADMIN_ID = [1309757945]  # samakan dengan admin broadcast

    if message.from_user.id not in ADMIN_ID:
        await message.reply("🚫 Kamu tidak punya izin.")
        return

    try:
        response = requests.get(API_GET_URL, timeout=10)
        users = response.json()

        if not users or not isinstance(users, list):
            await message.reply("❌ Gagal mengambil data user (format tidak valid).")
            return

        total = len(users)

        await message.reply(
            f"👥 Total User Terdaftar\n\n"
            f"📊 Jumlah: {total}"
        )

    except Exception as e:
        logging.error(f"Users command error: {e}")
        await message.reply("❌ Terjadi kesalahan saat mengambil data user.")
