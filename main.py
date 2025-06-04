# main.py - Entry point to start the bot, data provider, and web server

import threading
import logging

import config
from strategy import Strategy
from money import MoneyManager
from data_provider import DummyDataProvider, PocketOptionDataProvider
import bot
import app_server

if __name__ == "__main__":
    # Configure logging for the entire application
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    # Initialize strategy and money management
    strategy = Strategy(window_size=5)
    money_manager = MoneyManager(base_amount=config.BASE_AMOUNT, use_martingale=config.USE_MARTINGALE)
    # Choose data provider based on configuration
    if config.USE_REAL_DATA:
        provider = PocketOptionDataProvider(config.ASSET, strategy, money_manager,
                                            config.POCKETOPTION_SSID, use_demo=config.USE_DEMO_BALANCE)
    else:
        provider = DummyDataProvider(config.ASSET, strategy, money_manager)
    # Start the Telegram bot polling in a separate thread
    bot_thread = threading.Thread(target=bot.bot.infinity_polling, name="TelegramBotThread", daemon=True)
    bot_thread.start()
    logging.info("Telegram bot polling started.")
    # Start the data provider loop in a separate thread
    data_thread = threading.Thread(target=provider.run, name="DataProviderThread", daemon=True)
    data_thread.start()
    logging.info("Data provider started.")
    # Start the Flask web server (this will block the main thread)
    logging.info("Starting Flask web server for Telegram Web App...")
    app_server.app.run(host="0.0.0.0", port=5000)
