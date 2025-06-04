# strategy.py – Logika strategii generowania sygnałów na podstawie lokalnych ekstremów cenowych

from collections import deque

class Strategy:
    """
    Klasa strategii, która generuje sygnały "CALL" lub "PUT"
    gdy aktualna cena jest lokalnym minimum lub maksimum w zadanym oknie czasowym.
    """

    def __init__(self, window_size: int = 5):
        """
        Inicjalizacja:
        :param window_size: Liczba ostatnich cen, które przechowujemy dla detekcji ekstremów.
        """
        self.window_size = window_size
        self.recent_prices = deque(maxlen=window_size)

    def check_signal(self, price: float) -> str | None:
        """
        Dodaje nową cenę do bufora i sprawdza, czy jest to lokalne minimum lub maksimum.
        :param price: Bieżąca cena aktywa.
        :return: "CALL" (kupno), "PUT" (sprzedaż) lub None (brak sygnału).
        """
        # Dodajemy cenę do kolejki o długości window_size
        self.recent_prices.append(price)

        # Jeśli nie zebraliśmy jeszcze window_size cen, nie generujemy sygnału
        if len(self.recent_prices) < self.window_size:
            return None

        # Sprawdź, czy obecna cena jest minimalną w oknie → sygnał CALL
        if price == min(self.recent_prices):
            return "CALL"
        # Sprawdź, czy obecna cena jest maksymalną w oknie → sygnał PUT
        if price == max(self.recent_prices):
            return "PUT"

        return None
