# config.py - Configuration for the scalping signals bot

# Telegram Bot token (from BotFather)
TELEGRAM_BOT_TOKEN = "8197508817:AAHWAFPEJljOUiC79-Ihv2rxBVu7OYVenvU"

# URL for the Telegram Web App (Mini App) interface
# Use an HTTPS URL of your server where the web interface is hosted.
WEBAPP_URL = "ngrok http http://localhost:8080"

# Toggle between using real PocketOption data or dummy simulated data
USE_REAL_DATA = False

# PocketOption API configuration (if USE_REAL_DATA is True)
POCKETOPTION_SSID = "AAbfUmAoUegBslLQr"    # Your PocketOption session ID 102042762 for API login (if required)
USE_DEMO_BALANCE = True   # If using PocketOption, whether to use demo (practice) or real balance

# Trading parameters
ASSET = "EURUSD"          # Asset (currency pair) to generate signals for
BASE_AMOUNT = 1.0         # Base trade amount in dollars
USE_MARTINGALE = True     # Whether to use Martingale strategy for trade amounts

# Dummy data settings (used if USE_REAL_DATA is False)
DUMMY_INITIAL_PRICE = 1.10000   # Starting price for simulation data
DUMMY_VOLATILITY = 0.0005       # Maximum random price change per tick (simulation)
DATA_UPDATE_INTERVAL = 5        # Seconds between data updates (tick interval for dummy data or polling interval for real data)
TRADE_DURATION_STEPS = 12       # Duration of a trade in ticks (for simulation) – e.g., 12 ticks * 5s = 60s trade

# Note:
# - Set TELEGRAM_BOT_TOKEN and WEBAPP_URL before running the bot.
# - For real data, ensure POCKETOPTION_SSID is provided (obtained from an authenticated PocketOption session).
# - Use HTTPS for WEBAPP_URL (Telegram requires secure URL for Web Apps).
