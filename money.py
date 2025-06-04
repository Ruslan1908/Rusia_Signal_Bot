# money.py – Zarządzanie kapitałem (np. system Martingale)

class MoneyManager:
    """
    Klasa do zarządzania kwotami transakcji.
    Obsługuje opcjonalny system Martingale.
    """

    def __init__(self, base_amount: float, use_martingale: bool = True):
        """
        Inicjalizacja:
        :param base_amount: Bazowa kwota dla pierwszej transakcji (USD).
        :param use_martingale: Czy stosować system Martingale (podwajanie stawki po przegranej).
        """
        self.base_amount = base_amount
        self.use_martingale = use_martingale
        self.current_amount = base_amount  # Kwota bierząca dla następnej transakcji

    def get_amount(self) -> float:
        """
        Zwraca obecną kwotę, którą należy postawić.
        :return: float – bieżąca kwota.
        """
        return self.current_amount

    def record_result(self, result: str) -> None:
        """
        Rejestruje wynik ostatniej transakcji i aktualizuje kwotę następnej transakcji:
        - Jeśli Martingale wyłączony lub wynik to "WIN", resetuje do bazowej kwoty.
        - Jeśli Martingale włączony i wynik to "LOSS", podwaja bieżącą kwotę.
        :param result: "WIN" lub "LOSS".
        """
        if result is None:
            # Brak wyniku (transakcja jeszcze nie zakończona) – nic nie zmieniamy
            return

        if not self.use_martingale or result.upper() == "WIN":
            # Jeśli nie stosujemy Martingale lub wygraliśmy, resetujemy stawkę
            self.current_amount = self.base_amount
        elif result.upper() == "LOSS":
            # Przegrana i Martingale włączony – podwajamy stawkę
            self.current_amount *= 2
