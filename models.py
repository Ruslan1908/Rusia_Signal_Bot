# models.py - Data models and shared data structures

from dataclasses import dataclass
from threading import Lock

@dataclass
class Signal:
    """Data class representing a trading signal."""
    time: str         # Timestamp of the signal (formatted string)
    asset: str        # Asset/currency pair of the trade
    direction: str    # "CALL" for buy/up, "PUT" for sell/down
    amount: float     # Trade amount in USD
    entry_price: float  # Price at the time the signal was generated
    result: str = None  # Trade outcome: "WIN", "LOSS", or None (if not yet determined)

# Shared list of signals and a lock for thread-safe access from multiple threads
signals = []
signals_lock = Lock()
