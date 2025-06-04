# main.py - Точка входа: запускает бота, провайдера данных и веб-сервер

import threading
import logging

import config
from strategy import Strategy
from money import MoneyManager
from data_provider import DummyDataProvider, PocketOptionDataProvider
import bot
import app_server

if __name__ == "__main__":
    # Настройка логирования для всего приложения
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Инициализируем стратегию и менеджер денег
    strategy = Strategy(window_size=5)
    money_manager = MoneyManager(
        base_amount=config.BASE_AMOUNT,
        use_martingale=config.USE_MARTINGALE
    )

    # Выбираем провайдера данных в зависимости от конфигурации
    if config.USE_REAL_DATA:
        provider = PocketOptionDataProvider(
            config.ASSET,
            strategy,
            money_manager,
            config.POCKETOPTION_SSID,
            use_demo=config.USE_DEMO_BALANCE
        )
    else:
        provider = DummyDataProvider(
            config.ASSET,
            strategy,
            money_manager
        )

    # Запускаем Telegram-бота в отдельном треде
    bot_thread = threading.Thread(
        target=bot.bot.infinity_polling,
        name="TelegramBotThread",
        daemon=True
    )
    bot_thread.start()
    logging.info("Telegram bot polling started.")

    # Запускаем провайдера данных в отдельном треде
    data_thread = threading.Thread(
        target=provider.run,
        name="DataProviderThread",
        daemon=True
    )
    data_thread.start()
    logging.info("Data provider started.")

    # Запускаем Flask-сервер (этот вызов блокирует главный тред)
    logging.info("Starting Flask web server for Telegram Web App...")
    app_server.app.run(host="0.0.0.0", port=5000)
