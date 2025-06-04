# models.py – Definicje struktur danych dla sygnałów

from dataclasses import dataclass
from threading import Lock

@dataclass
class Signal:
    """
    Klasa reprezentująca pojedynczy sygnał handlowy.
    :param time: Czas utworzenia sygnału (format "YYYY-MM-DD HH:MM:SS").
    :param asset: Symbol aktywa, np. "EURUSD".
    :param direction: Kierunek transakcji – "CALL" (kupno) lub "PUT" (sprzedaż).
    :param amount: Kwota transakcji w USD.
    :param entry_price: Cena wejścia w momencie generacji sygnału.
    :param result: Wynik transakcji – "WIN", "LOSS" lub None, jeżeli jeszcze nie rozliczony.
    """
    time: str
    asset: str
    direction: str
    amount: float
    entry_price: float
    result: str = None

# Globalna lista sygnałów oraz blokada dla bezpiecznego dostępu wątków
signals: list[Signal] = []
signals_lock = Lock()
