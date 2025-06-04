import telebot
from telebot import types
import logging
from threading import Lock
import config

# Инициализация бота с токеном
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

# Множество подписчиков и соответствующая блокировка
subscribers = set()
subs_lock = Lock()

# Загрузка ранее сохранённых подписчиков из файла при запуске бота
try:
    with open("subscribers.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                subscribers.add(int(line))
    logging.info(f"Loaded {len(subscribers)} subscribers from file.")
except FileNotFoundError:
    logging.info("No subscribers.txt found – starting with an empty subscribers list.")


# Функция сохранения текущего списка подписчиков в файл
def save_subscribers():
    try:
        with open("subscribers.txt", "w") as f:
            for user_id in subscribers:
                f.write(f"{user_id}\n")
    except Exception as e:
        logging.error("Failed to save subscribers to file: %s", e)


def notify_signal(signal):
    """
    Отправляет сообщение всем подписчикам о новом сигнале.
    """
    message_text = (
        f"⚡ New Signal ⚡\n"
        f"Asset: {signal.asset}\n"
        f"Direction: {signal.direction}\n"
        f"Time: {signal.time}\n"
        f"Amount: ${signal.amount:.2f}"
    )
    # Рассылка сообщения всем подписчикам
    with subs_lock:
        user_ids = list(subscribers)
    for user_id in user_ids:
        try:
            bot.send_message(user_id, message_text)
        except Exception as e:
            logging.error("Error sending signal to user %d: %s", user_id, e)
            # Если бот заблокирован или не может отправить сообщение – удалить пользователя
            if "bot was blocked" in str(e) or "Forbidden" in str(e):
                with subs_lock:
                    if user_id in subscribers:
                        subscribers.discard(user_id)
                        save_subscribers()  # сохранить обновление (удаление подписчика)


@bot.message_handler(commands=['start'])
def handle_start(message):
    """
    Обработчик команды /start: подписывает пользователя и отправляет ссылку на интерфейс.
    """
    chat_id = message.chat.id
    # Добавление пользователя в список подписчиков
    with subs_lock:
        subscribers.add(chat_id)
    save_subscribers()  # сохранение нового подписчика в файл

    welcome_text = (
        "Welcome to the Scalping Signals Bot!\n"
        "You will now receive live trading signals.\n"
        "Use the button below to open the detailed interface."
    )
    if config.WEBAPP_URL:
        # Кнопка открытия веб-интерфейса
        keyboard = types.InlineKeyboardMarkup()
        web_app_btn = types.InlineKeyboardButton(
            text="Open Signals Interface",
            web_app=types.WebAppInfo(url=config.WEBAPP_URL)
        )
        keyboard.add(web_app_btn)
        bot.send_message(chat_id, welcome_text, reply_markup=keyboard)
    else:
        bot.send_message(chat_id, welcome_text)
    logging.info("User %d subscribed (started bot).", chat_id)


@bot.message_handler(commands=['stop'])
def handle_stop(message):
    """
    Обработчик команды /stop: отписывает пользователя от рассылки сигналов.
    """
    chat_id = message.chat.id
    with subs_lock:
        subscribers.discard(chat_id)
    save_subscribers()  # сохранение изменения (удаление подписчика)
    bot.reply_to(message, "You have been unsubscribed from signals. Send /start to subscribe again.")
    logging.info("User %d unsubscribed (stopped bot).", chat_id)


@bot.message_handler(commands=['help'])
def handle_help(message):
    """
    Обработчик команды /help: выводит справку по командам.
    """
    help_text = (
        "This bot predicts scalping signals for PocketOption trades.\n\n"
        "Commands:\n"
        "/start – Subscribe and get the interface link\n"
        "/stop – Stop receiving signals\n"
        "/help – Show this help message\n\n"
        "Use the provided interface to view signals in real time."
    )
    bot.reply_to(message, help_text)


@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """
    Обработчик данных, присланных из веб-приложения (Telegram Web App).
    """
    chat_id = message.chat.id
    data = message.web_app_data.data if message.web_app_data else None
    logging.info("Received WebApp data from user %d: %s", chat_id, data)
    if data:
        bot.send_message(chat_id, f"✅ Received data from web app: {data}")
