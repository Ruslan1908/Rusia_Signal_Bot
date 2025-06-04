# money.py - Money management strategy (e.g., Martingale system)

class MoneyManager:
    """Manages trade amounts using a base amount and optional Martingale strategy for loss recovery."""

    def __init__(self, base_amount: float, use_martingale: bool = True):
        self.base_amount = base_amount
        self.use_martingale = use_martingale
        self.current_amount = base_amount  # amount to be used for the next trade

    def get_amount(self):
        """Get the amount for the next trade."""
        return self.current_amount

    def record_result(self, result: str):
        """
        Record the result of the last trade and adjust the next trade amount accordingly.
        - If Martingale is enabled and last trade was a LOSS, double the amount (to recover losses).
        - If the last trade was a WIN, or Martingale is disabled, reset to the base amount.
        """
        if result is None:
            return  # Trade still pending or no result to record
        if not self.use_martingale or result == "WIN":
            # On win (or if not using Martingale), reset to base amount
            self.current_amount = self.base_amount
        elif result == "LOSS":
            # On loss, if Martingale is enabled, double the amount for next trade
            self.current_amount *= 2
