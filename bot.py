# bot.py - Telegram bot interface and user interaction logic

import telebot
from telebot import types
import logging
from threading import Lock
import config

# Initialize the Telegram bot with the provided token
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

# Maintain a set of subscriber chat IDs (users who will receive signals)
subscribers = set()
subs_lock = Lock()

def notify_signal(signal):
    """
    Send a message to all subscribed users with details of a new signal.
    """
    # Compose the message text with signal details
    message_text = (f"⚡ New Signal ⚡\n"
                    f"Asset: {signal.asset}\n"
                    f"Direction: {signal.direction}\n"
                    f"Time: {signal.time}\n"
                    f"Amount: ${signal.amount:.2f}")
    # Broadcast to all subscribers
    with subs_lock:
        user_ids = list(subscribers)
    for user_id in user_ids:
        try:
            bot.send_message(user_id, message_text)
        except Exception as e:
            logging.error("Error sending signal to user %d: %s", user_id, e)
            # If bot is blocked by the user or cannot send, remove that user from subscribers
            if "bot was blocked" in str(e) or "Forbidden" in str(e):
                with subs_lock:
                    subscribers.discard(user_id)

@bot.message_handler(commands=['start'])
def handle_start(message):
    """
    /start command handler. Subscribes the user and provides the Web App link.
    """
    chat_id = message.chat.id
    # Add the user to the subscribers list
    with subs_lock:
        subscribers.add(chat_id)
    # Send a welcome message and the interface button
    welcome_text = ("Welcome to the Scalping Signals Bot!\n"
                    "You will now receive live trading signals.\n"
                    "Use the button below to open the detailed interface.")
    if config.WEBAPP_URL:
        # Create an inline keyboard with a Web App button
        keyboard = types.InlineKeyboardMarkup()
        web_app_btn = types.InlineKeyboardButton(
            text="Open Signals Interface",
            web_app=types.WebAppInfo(url=config.WEBAPP_URL)
        )
        keyboard.add(web_app_btn)
        bot.send_message(chat_id, welcome_text, reply_markup=keyboard)
    else:
        # If no WebApp URL is set, just send the welcome text
        bot.send_message(chat_id, welcome_text)
    logging.info("User %d subscribed (started bot).", chat_id)

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    """
    /stop command handler. Unsubscribes the user from signal notifications.
    """
    chat_id = message.chat.id
    with subs_lock:
        subscribers.discard(chat_id)
    bot.reply_to(message, "You have been unsubscribed from signals. Send /start to subscribe again.")
    logging.info("User %d unsubscribed (stopped bot).", chat_id)

@bot.message_handler(commands=['help'])
def handle_help(message):
    """
    /help command handler. Provides information on how to use the bot.
    """
    help_text = ("This bot predicts scalping signals for PocketOption trades.\n\n"
                 "Commands:\n"
                 "/start – Subscribe and get the interface link\n"
                 "/stop – Stop receiving signals\n"
                 "/help – Show this help message\n\n"
                 "Use the provided interface to view signals in real time.")
    bot.reply_to(message, help_text)

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """
    Handler for data sent from the Telegram Web App (if implemented).
    This will trigger if the Web App sends data via Telegram.WebApp.sendData().
    """
    chat_id = message.chat.id
    data = message.web_app_data.data if message.web_app_data else None
    logging.info("Received WebApp data from user %d: %s", chat_id, data)
    if data:
        # Echo or handle the received data (for demonstration, we just acknowledge it)
        bot.send_message(chat_id, f"✅ Received data from web app: {data}")
