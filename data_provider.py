# data_provider.py – Dostarcza dane (symulowane lub z PocketOption) i generuje sygnały

import time
import logging
import random
from datetime import datetime

from models import Signal, signals, signals_lock
from bot import notify_signal
import config
from strategy import Strategy
from money import MoneyManager

class DataProvider:
    """
    Bazowa klasa dostawcy danych. Implementuje wspólne elementy
    dla różnych typów dostawców (symulacja vs. PocketOption).
    """
    def __init__(self, asset: str, strategy: Strategy, money_manager: MoneyManager, update_interval: float):
        """
        :param asset: Symbol aktywa (np. "EURUSD").
        :param strategy: Instancja strategii do wykrywania sygnałów.
        :param money_manager: Manager kwot (np. Martingale).
        :param update_interval: Interwał (w sekundach) pomiędzy kolejnymi odczytami ceny.
        """
        self.asset = asset
        self.strategy = strategy
        self.money_manager = money_manager
        self.update_interval = update_interval

    def run(self):
        """
        Główna pętla dostawcy danych – do implementacji w podklasach.
        """
        raise NotImplementedError("Metoda run() musi być zaimplementowana w podklasie.")


class DummyDataProvider(DataProvider):
    """
    Symulator danych cenowych metodą losowego spaceru.
    Generuje sygnały na podstawie strategii przy lokalnych ekstremach.
    """
    def __init__(self, asset: str, strategy: Strategy, money_manager: MoneyManager,
                 initial_price: float = None, volatility: float = None):
        # Ustawienie domyślnych wartości, jeśli nie przekazano argumentów
        initial_price = initial_price if initial_price is not None else config.DUMMY_INITIAL_PRICE
        volatility = volatility if volatility is not None else config.DUMMY_VOLATILITY
        super().__init__(asset, strategy, money_manager, update_interval=config.DATA_UPDATE_INTERVAL)
        self.price = initial_price
        self.volatility = volatility
        self.current_tick = 0
        # Lista oczekujących sygnałów w formacie [(Signal, expiry_tick)]
        self.pending_signals: list[tuple[Signal, int]] = []

    def generate_price(self) -> float:
        """
        Generuje następną cenę metodą losowego spaceru wokół bieżącej ceny.
        """
        change = random.uniform(-self.volatility, self.volatility)
        self.price += change
        # Zapobiegamy sytuacji, gdy cena byłaby ujemna lub zerowa
        if self.price <= 0:
            self.price = abs(self.price) + 0.00001
        # Zaokrąglamy do 5 miejsc po przecinku (typowe dla par walutowych)
        self.price = round(self.price, 5)
        return self.price

    def run(self) -> None:
        """
        Główna pętla symulatora:
        - Generuje nowe ceny co update_interval sekund.
        - Sprawdza, czy wygasły oczekujące transakcje (pending_signals) i rozlicza je.
        - Sprawdza strategię pod kątem nowych sygnałów, jeśli nie ma aktywnych oczekujących.
        """
        logging.info("Uruchomienie DummyDataProvider dla aktywa %s (początkowa cena = %.5f)", self.asset, self.price)
        while True:
            try:
                price = self.generate_price()
                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.current_tick += 1

                # Rozliczenie oczekujących sygnałów (jeśli expiry_tick <= current_tick)
                if self.pending_signals:
                    updated_pending: list[tuple[Signal, int]] = []
                    for sig, expiry_tick in self.pending_signals:
                        if self.current_tick >= expiry_tick:
                            # Określenie wyniku na podstawie porównania cen
                            if sig.direction == "CALL":
                                sig.result = "WIN" if price > sig.entry_price else "LOSS"
                            else:  # PUT
                                sig.result = "WIN" if price < sig.entry_price else "LOSS"
                            logging.info("Transakcja rozliczona: %s %s → %s", sig.asset, sig.direction, sig.result)
                            # Aktualizacja managera pieniędzy na podstawie wyniku
                            self.money_manager.record_result(sig.result)
                        else:
                            updated_pending.append((sig, expiry_tick))
                    self.pending_signals = updated_pending

                # Jeśli brak oczekujących sygnałów, sprawdzamy, czy pojawi się nowy sygnał
                if not self.pending_signals:
                    direction = self.strategy.check_signal(price)
                    if direction:  # Zwróci "CALL" lub "PUT", albo None
                        amount = self.money_manager.get_amount()
                        new_signal = Signal(
                            time=now_time,
                            asset=self.asset,
                            direction=direction,
                            amount=amount,
                            entry_price=price,
                            result=None
                        )
                        # Obliczamy tick wygaśnięcia: TRADE_DURATION_STEPS ticków od teraz
                        expiry_tick = self.current_tick + config.TRADE_DURATION_STEPS
                        # Dodajemy sygnał do globalnej listy wątkowo bezpiecznie
                        with signals_lock:
                            signals.append(new_signal)
                        # Dodajemy do listy oczekujących sygnałów
                        self.pending_signals.append((new_signal, expiry_tick))
                        logging.info("Nowy sygnał: %s %s o godzinie %s (kwota = %.2f USD)",
                                     new_signal.asset, new_signal.direction, new_signal.time, new_signal.amount)
                        # Powiadamiamy subskrybentów Telegram o nowym sygnale
                        notify_signal(new_signal)

                # Pauza przed następną iteracją
                time.sleep(self.update_interval)

            except Exception as e:
                logging.error("Błąd w pętli DummyDataProvider: %s", str(e), exc_info=True)
                # Jeśli wystąpi błąd, czekamy sekundę i próbujemy ponownie
                time.sleep(1)


class PocketOptionDataProvider(DataProvider):
    """
    Dostawca danych z rzeczywistego API PocketOption.
    Wymaga poprawnego POCKETOPTION_SSID w config.py.
    """
    def __init__(self, asset: str, strategy: Strategy, money_manager: MoneyManager,
                 session_id: str, use_demo: bool = True):
        super().__init__(asset, strategy, money_manager, update_interval=config.DATA_UPDATE_INTERVAL)
        self.session_id = session_id
        self.use_demo = use_demo
        self.account = None  # Obiekt połączenia z PocketOption API

    def connect(self) -> bool:
        """
        Próbuje połączyć się z API PocketOption za pomocą session_id.
        Zwraca True, jeśli połączenie OK, False w przeciwnym razie.
        """
        try:
            from pocketoptionapi.stable_api import PocketOption
        except ImportError:
            logging.error("Biblioteka pocketoptionapi nie jest zainstalowana.")
            return False

        self.account = PocketOption(self.session_id)
        success, msg = self.account.connect()
        if not success:
            logging.error("Nie udało się połączyć z PocketOption: %s", msg)
            return False

        # Przełączanie na demo lub real balance
        try:
            balance_type = "PRACTICE" if self.use_demo else "REAL"
            self.account.change_balance(balance_type)
        except Exception as e:
            logging.warning("Nie można zmienić typu konta: %s", e)

        return True

    def run(self) -> None:
        """
        Główna pętla dostawcy realnych danych:
        - Łączy się z PocketOption API.
        - Odbiera strumień świec co update_interval sekund.
        - Generuje sygnały na podstawie strategii (rozliczenie transakcji wymaga dodatkowej logiki).
        """
        logging.info("Uruchomienie PocketOptionDataProvider dla %s...", self.asset)
        if not self.connect():
            logging.error("PocketOptionDataProvider nie połączony – zakończono działanie.")
            return

        try:
            # Uruchom strumień świec (interwał 2 minuty – przykład; dostosuj w razie potrzeby)
            self.account.start_candles_stream(self.asset, 2)
        except Exception as e:
            logging.error("Nie można uruchomić strumienia świec dla %s: %s", self.asset, e)
            return

        while True:
            try:
                # Pobieranie najnowszych świec
                candles = self.account.get_realtime_candles(self.asset)
                if not candles:
                    time.sleep(self.update_interval)
                    continue

                latest_candle = candles[-1]
                # W API PocketOption klucz może być "close" lub "close_price"
                price = float(latest_candle.get("close") or latest_candle.get("close_price") or 0)
                if price == 0:
                    # Jeśli cena = 0 (błędne dane), odczekaj i pobierz ponownie
                    time.sleep(self.update_interval)
                    continue

                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Sprawdź, czy generujemy nowy sygnał
                direction = self.strategy.check_signal(price)
                if direction:
                    amount = self.money_manager.get_amount()
                    new_signal = Signal(
                        time=now_time,
                        asset=self.asset,
                        direction=direction,
                        amount=amount,
                        entry_price=price,
                        result=None
                    )
                    # Dodajemy sygnał do listy globalnej
                    with signals_lock:
                        signals.append(new_signal)
                    logging.info("Nowy sygnał (realne dane): %s %s o godzinie %s (kwota = %.2f USD)",
                                 new_signal.asset, new_signal.direction, new_signal.time, new_signal.amount)
                    # Powiadamiamy subskrybentów Telegram
                    notify_signal(new_signal)
                    # UWAGA: rozliczenie transakcji w realnym trybie wymaga dodatkowej logiki

                # Przerwa przed kolejnym odczytem
                time.sleep(self.update_interval)

            except Exception as e:
                logging.error("Błąd w pętli PocketOptionDataProvider: %s", str(e), exc_info=True)
                # Próba ponownego połączenia w razie błędu
                try:
                    if self.account:
                        self.account.close()
                except Exception:
                    pass
                time.sleep(5)
                if not self.connect():
                    logging.error("Ponowne połączenie do PocketOption nie powiodło się, ponawiam w 5s...")
                    continue
