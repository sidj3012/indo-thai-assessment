import threading
from typing import Dict, Tuple

from order_service.models import OrderEvent


class PositionStore:
    def __init__(self):
        self._positions: Dict[str, int] = {}
        self._processed_event_ids = set()
        self._lock = threading.RLock()

    def apply_event(
        self,
        event: OrderEvent,
    ) -> Tuple[bool, str]:

        with self._lock:
            if event.event_id in self._processed_event_ids:
                return False, "duplicate"

            self._processed_event_ids.add(event.event_id)

            if event.symbol not in self._positions:
                self._positions[event.symbol] = 0

            if event.transaction_type == "BUY":
                self._positions[event.symbol] += event.quantity

            elif event.transaction_type == "SELL":
                self._positions[event.symbol] -= event.quantity

            else:
                raise ValueError(
                    f"Invalid transaction type: "
                    f"{event.transaction_type}"
                )

            return True, "accepted"

    def get_positions(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._positions)