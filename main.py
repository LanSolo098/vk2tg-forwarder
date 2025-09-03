import time
import logging
import vk_api
from telegram import Bot, ParseMode
from config import VK_TOKEN, VK_CHAT_ID, TG_BOT_TOKEN, TG_CHANNEL_ID

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === ИНИЦИАЛИЗАЦИЯ VK и Telegram ===
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
tg_bot = Bot(token=TG_BOT_TOKEN)

last_id = 0  # последний обработанный ID

def vk_user_link(from_id: int) -> str:
    """Возвращает HTML-ссылку на автора сообщения (пользователь или сообщество)."""
    try:
        if from_id is None:
            return "Неизвестный"
        if from_id > 0:
            user = vk.users.get(user_ids=from_id, fields="domain")[0]
            domain = user.get("domain") or f"id{from_id}"
            name = f"{user['first_name']} {user['last_name']}"
            return f'<a href="https://vk.com/{domain}">{name}</a>'
        else:
            gid = abs(from_id)
            group = vk.groups.getById(group_id=gid, fields="screen_name")[0]
            screen = group.get("screen_name") or f"club{gid}"
            name = group.get("name", f"club{gid}")
            return f'<a href="https://vk.com/{screen}">{name}</a>'
    except Exception:
        # На всякий случай — просто id
        if from_id and from_id > 0:
            return f'<a href="https://vk.com/id{from_id}">id{from_id}</a>'
        if from_id:
            return f"club{abs(from_id)}"
        return "Неизвестный"

print("Бот запущен. Ожидание сообщений...")

while True:
    try:
        # Берём последние 20 сообщений и фильтруем по last_id
        history = vk.messages.getHistory(peer_id=VK_CHAT_ID, count=20)
        items = history.get("items", [])
        items.reverse()  # чтобы шли по порядку

        for msg in items:
            mid = msg.get("id", 0)
            if mid <= last_id:
                continue

            text = msg.get("text", "")
            from_id = msg.get("from_id")
            author = vk_user_link(from_id)

            # Формируем финальный текст
            if text:
                final_text = f"👤 {author}:\n{text}"
            else:
                final_text = f"👤 {author}"

            # Отправляем текст
            tg_bot.send_message(
                chat_id=TG_CHANNEL_ID,
                text=final_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logging.info(f"Переслано сообщение от {author}: {text}")

            # Вложения
            for att in msg.get("attachments", []):
                typ = att.get("type")

                if typ == "photo":
                    try:
                        sizes = att["photo"]["sizes"]
                        photo_url = sizes[-1]["url"]
                        tg_bot.send_photo(
                            chat_id=TG_CHANNEL_ID,
                            photo=photo_url,
                            caption=final_text,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        logging.error(f"Фото: {e}")

                elif typ == "doc":
                    try:
                        doc_url = att["doc"]["url"]
                        tg_bot.send_document(
                            chat_id=TG_CHANNEL_ID,
                            document=doc_url,
                            caption=final_text,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        logging.error(f"Документ: {e}")

                elif typ == "video":
                    try:
                        v = att["video"]
                        url = v.get("player")
                        if not url:
                            # резервная ссылка по owner_id/id (+ access_key если есть)
                            owner_id = v.get("owner_id")
                            vid = v.get("id")
                            access_key = v.get("access_key")
                            url = f"https://vk.com/video{owner_id}_{vid}"
                            if access_key:
                                url += f"?access_key={access_key}"
                        tg_bot.send_message(
                            chat_id=TG_CHANNEL_ID,
                            text=f"{final_text}\n🎥 Видео: {url}",
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False
                        )
                    except Exception as e:
                        logging.error(f"Видео: {e}")

                elif typ == "audio":
                    try:
                        a = att["audio"]
                        artist = a.get("artist", "Аудио")
                        title = a.get("title", "")
                        url = a.get("url")  # часто отсутствует у защищённых треков
                        line = f"{final_text}\n🎵 {artist} — {title}"
                        if url:
                            line += f"\n{url}"
                        tg_bot.send_message(
                            chat_id=TG_CHANNEL_ID,
                            text=line,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                    except Exception as e:
                        logging.error(f"Аудио: {e}")

                elif typ == "sticker":
                    try:
                        st = att["sticker"]
                        images = st.get("images") or st.get("images_with_background") or []
                        if images:
                            sticker_url = images[-1]["url"]
                            tg_bot.send_photo(chat_id=TG_CHANNEL_ID, photo=sticker_url)
                    except Exception as e:
                        logging.error(f"Стикер: {e}")

            # Обновляем last_id
            last_id = mid

        time.sleep(2)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        print("Ошибка:", e)
        time.sleep(5)
