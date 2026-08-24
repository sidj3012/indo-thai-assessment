from dataclasses import dataclass


@dataclass(frozen=True)
class OrderEvent:
    event_id: str
    symbol: str
    transaction_type: str
    quantity: int

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "symbol": self.symbol,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
        }