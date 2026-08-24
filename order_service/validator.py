from typing import Mapping, Optional, Tuple

from .models import OrderEvent


REQUIRED_COLUMNS = {
    "event_id",
    "symbol",
    "transaction_type",
    "quantity",
}


def validate_row(
    row: Mapping[str, Optional[str]],
) -> Tuple[Optional[OrderEvent], Optional[str]]:

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in row
    ]

    if missing_columns:
        return None, (
            f"missing columns: {', '.join(sorted(missing_columns))}"
        )

    event_id = row.get("event_id")
    symbol = row.get("symbol")
    transaction_type = row.get("transaction_type")
    quantity = row.get("quantity")

    if event_id is None or not isinstance(event_id, str) or not event_id.strip():
        return None, "event_id must be a non-empty string"

    if symbol is None or not isinstance(symbol, str) or not symbol.strip():
        return None, "symbol must be a non-empty string"

    if transaction_type not in {"BUY", "SELL"}:
        return None, "transaction_type must be exactly BUY or SELL"

    if quantity is None or not isinstance(quantity, str) or not quantity.strip():
        return None, "quantity must be a positive integer"

    try:
        parsed_quantity = int(quantity)
    except ValueError:
        return None, "quantity must be a positive integer"

    if parsed_quantity <= 0:
        return None, "quantity must be a positive integer"

    return (
        OrderEvent(
            event_id=event_id,
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=parsed_quantity,
        ),
        None,
    )