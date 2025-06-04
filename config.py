# config.py – Konfiguracja bota do sygnałów skalpowania

import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env (jeśli istnieje)
load_dotenv()

# Token bota Telegram uzyskany od BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "WSTAW_TUTAJ_SWÓJ_TOKEN")

# URL do interfejsu strony web (Telegram Web App), np. "https://yourdomain.com"
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

# FLAGA: czy używać prawdziwych danych z PocketOption, czy symulacji
USE_REAL_DATA = os.getenv("USE_REAL_DATA", "False").lower() in ("1", "true", "yes")

# Jeśli USE_REAL_DATA == True: dane API PocketOption
POCKETOPTION_SSID = os.getenv("POCKETOPTION_SSID", "")
USE_DEMO_BALANCE = os.getenv("USE_DEMO_BALANCE", "True").lower() in ("1", "true", "yes")

# Parametry handlu
ASSET = os.getenv("ASSET", "EURUSD")         # Para walutowa
BASE_AMOUNT = float(os.getenv("BASE_AMOUNT", 1.0))  # Bazowa kwota w dolarach
USE_MARTINGALE = os.getenv("USE_MARTINGALE", "True").lower() in ("1", "true", "yes")

# Ustawienia symulacji (gdy USE_REAL_DATA=False)
DUMMY_INITIAL_PRICE = float(os.getenv("DUMMY_INITIAL_PRICE", 1.10000))
DUMMY_VOLATILITY = float(os.getenv("DUMMY_VOLATILITY", 0.0005))
DATA_UPDATE_INTERVAL = int(os.getenv("DATA_UPDATE_INTERVAL", 5))      # w sekundach
TRADE_DURATION_STEPS = int(os.getenv("TRADE_DURATION_STEPS", 12))     # liczba „ticków” (np. 12 ticków × 5s = 60s)

# Plik, w którym zapisywani są subskrybenci (identyfikatory użytkowników Telegram)
SUBSCRIBERS_FILE = os.getenv("SUBSCRIBERS_FILE", "subscribers.txt")
