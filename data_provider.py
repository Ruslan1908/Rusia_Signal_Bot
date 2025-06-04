# data_provider.py - Data source providers for price data (dummy simulation or PocketOption API)

import time
import logging
import random
from datetime import datetime

from models import Signal, signals, signals_lock
from bot import notify_signal  # function to notify Telegram users of new signals
import config


class DataProvider:
    """Base class for data providers that feed price data and generate signals."""

    def __init__(self, asset: str, strategy, money_manager, update_interval: float):
        self.asset = asset
        self.strategy = strategy
        self.mm = money_manager
        self.update_interval = update_interval

    def run(self):
        """Run the data provider loop. (To be implemented in subclasses.)"""
        raise NotImplementedError


class DummyDataProvider(DataProvider):
    """
    Simulated data provider that generates random walk price data for testing.
    It produces signals based on the Strategy without needing real market data.
    """

    def __init__(self, asset: str, strategy, money_manager,
                 initial_price: float = None, volatility: float = None):
        initial_price = initial_price if initial_price is not None else config.DUMMY_INITIAL_PRICE
        volatility = volatility if volatility is not None else config.DUMMY_VOLATILITY
        super().__init__(asset, strategy, money_manager, update_interval=config.DATA_UPDATE_INTERVAL)
        self.price = initial_price
        self.volatility = volatility
        self.current_tick = 0
        self.pending_signals = []  # list of tuples (Signal, expiry_tick) for open trades awaiting result

    def generate_price(self):
        """Generate the next price by simulating a random price change."""
        change = random.uniform(-self.volatility, self.volatility)
        self.price += change
        # Prevent the price from becoming non-positive
        if self.price <= 0:
            self.price = abs(self.price)
        # Round to 5 decimal places (typical for currency prices)
        self.price = round(self.price, 5)
        return self.price

    def run(self):
        logging.info("Starting DummyDataProvider for %s (initial price=%.5f)...", self.asset, self.price)
        while True:
            try:
                price = self.generate_price()
                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.current_tick += 1
                # Check pending signals for expiration
                if self.pending_signals:
                    new_pending = []
                    for (sig, expiry_tick) in self.pending_signals:
                        if self.current_tick >= expiry_tick:
                            # Determine outcome of the trade at expiry
                            if sig.direction == "CALL":
                                sig.result = "WIN" if price > sig.entry_price else "LOSS"
                            else:
                                sig.result = "WIN" if price < sig.entry_price else "LOSS"
                            logging.info("Signal resolved: %s %s -> %s", sig.asset, sig.direction, sig.result)
                            # Update money manager with result
                            self.mm.record_result(sig.result)
                        else:
                            new_pending.append((sig, expiry_tick))
                    self.pending_signals = new_pending  # keep only still-pending signals
                # Determine if a new signal should be generated (if no trade is currently open)
                signal_direction = self.strategy.check_signal(price)
                if signal_direction and not self.pending_signals:
                    # Create a new Signal object
                    amount = self.mm.get_amount()
                    new_signal = Signal(time=now_time, asset=self.asset,
                                        direction=signal_direction, amount=amount,
                                        entry_price=price, result=None)
                    # Set expiry for this simulated trade after TRADE_DURATION_STEPS ticks
                    expiry_tick = self.current_tick + config.TRADE_DURATION_STEPS
                    # Record the signal in the global list (with thread safety)
                    with signals_lock:
                        signals.append(new_signal)
                    # Mark this signal as pending resolution
                    self.pending_signals.append((new_signal, expiry_tick))
                    logging.info("New signal generated: %s %s at %s (amount=%.2f)",
                                 new_signal.asset, new_signal.direction, new_signal.time, new_signal.amount)
                    # Notify all subscribers via Telegram
                    notify_signal(new_signal)
                # Wait for the next update cycle
                time.sleep(self.update_interval)
            except Exception as e:
                logging.error("Error in DummyDataProvider loop: %s", str(e), exc_info=True)
                time.sleep(1)  # brief pause before retrying the loop


class PocketOptionDataProvider(DataProvider):
    """
    Real data provider that connects to PocketOption via their API to fetch live prices and generate signals.
    Requires a valid session ID (SSID) for authentication.
    """

    def __init__(self, asset: str, strategy, money_manager, session_id: str, use_demo: bool = True):
        super().__init__(asset, strategy, money_manager, update_interval=config.DATA_UPDATE_INTERVAL)
        self.session_id = session_id
        self.use_demo = use_demo
        self.account = None  # will be the PocketOption API client

    def connect(self):
        """Establish connection to PocketOption API using the provided session_id."""
        try:
            from pocketoptionapi.stable_api import PocketOption
        except ImportError:
            logging.error("PocketOption API library not installed. Cannot use real data provider.")
            return False
        self.account = PocketOption(self.session_id)
        connected, message = self.account.connect()
        if not connected:
            logging.error("Failed to connect to PocketOption API: %s", message)
            return False
        # Select demo or real balance
        try:
            balance_type = "PRACTICE" if self.use_demo else "REAL"
            self.account.change_balance(balance_type)
        except Exception as e:
            logging.warning("Could not change balance type: %s", e)
        return True

    def run(self):
        logging.info("Starting PocketOptionDataProvider for %s...", self.asset)
        if not self.connect():
            logging.error("PocketOptionDataProvider: Connection failed. Stopping data provider.")
            return
        try:
            # Start streaming real-time candle data for the asset
            self.account.start_candles_stream(self.asset, 2)  # keep a small buffer of recent candles
        except Exception as e:
            logging.error("Could not start candle stream for %s: %s", self.asset, e)
            return
        while True:
            try:
                candles = self.account.get_realtime_candles(self.asset)
                if candles:
                    latest_candle = candles[-1]
                    # Get the latest close price (key name may differ by API version)
                    price = float(latest_candle.get("close") or latest_candle.get("close_price") or 0)
                else:
                    time.sleep(self.update_interval)
                    continue
                if price == 0:
                    # No valid price retrieved, skip this iteration
                    time.sleep(self.update_interval)
                    continue
                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Check strategy for a signal
                signal_direction = self.strategy.check_signal(price)
                if signal_direction:
                    amount = self.mm.get_amount()
                    new_signal = Signal(time=now_time, asset=self.asset,
                                        direction=signal_direction, amount=amount,
                                        entry_price=price, result=None)
                    with signals_lock:
                        signals.append(new_signal)
                    logging.info("New signal generated (real data): %s %s at %s (amount=%.2f)",
                                 new_signal.asset, new_signal.direction, new_signal.time, new_signal.amount)
                    notify_signal(new_signal)
                    # Note: In real-data mode, trade outcomes are not automatically determined here,
                    # as actual trade execution and result tracking would be needed.
                    # The MoneyManager will continue using the base amount unless updated with real results.
                time.sleep(self.update_interval)
            except Exception as e:
                logging.error("Error in PocketOptionDataProvider loop: %s", str(e), exc_info=True)
                # Attempt to reconnect on error (e.g., connection lost)
                try:
                    if self.account:
                        self.account.close()
                except Exception:
                    pass
                time.sleep(5)
                if not self.connect():
                    logging.error("Reconnection to PocketOption failed. Retrying in 5s...")
                    continue  # retry connecting in the loop
