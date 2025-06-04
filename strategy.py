# strategy.py - Strategy for generating trading signals from price data

from collections import deque


class Strategy:
    """Trading strategy that generates signals based on recent price extremes."""

    def __init__(self, window_size: int = 5):
        # Use a sliding window of the last `window_size` prices
        self.window_size = window_size
        self.recent_prices = deque(maxlen=window_size)

    def check_signal(self, price: float):
        """
        Update the strategy with the latest price.
        Returns "CALL", "PUT", or None if no signal is generated.
        A signal is generated when the latest price is a local min or max in the window.
        """
        self.recent_prices.append(price)
        if len(self.recent_prices) < self.window_size:
            # Not enough data collected yet to decide
            return None
        # Check if the latest price is a local minimum or maximum
        if price == min(self.recent_prices):
            # Price dropped to a local low -> signal an upward trade (CALL)
            return "CALL"
        elif price == max(self.recent_prices):
            # Price rose to a local high -> signal a downward trade (PUT)
            return "PUT"
        else:
            return None
