from order_service.validator import validate_row


def make_row(
    event_id="evt-1",
    symbol="RELIANCE",
    transaction_type="BUY",
    quantity="10",
):
    return {
        "event_id": event_id,
        "symbol": symbol,
        "transaction_type": transaction_type,
        "quantity": quantity,
    }


def test_valid_buy():
    event, error = validate_row(make_row())

    assert error is None
    assert event.quantity == 10
    assert event.transaction_type == "BUY"


def test_valid_sell():
    event, error = validate_row(
        make_row(
            transaction_type="SELL",
            quantity="20",
        )
    )

    assert error is None
    assert event.quantity == 20


def test_invalid_transaction_type():
    event, error = validate_row(
        make_row(transaction_type="HOLD")
    )

    assert event is None
    assert error is not None


def test_zero_quantity():
    event, error = validate_row(
        make_row(quantity="0")
    )

    assert event is None
    assert error is not None


def test_negative_quantity():
    event, error = validate_row(
        make_row(quantity="-10")
    )

    assert event is None
    assert error is not None


def test_non_integer_quantity():
    event, error = validate_row(
        make_row(quantity="10.5")
    )

    assert event is None
    assert error is not None


def test_blank_quantity():
    event, error = validate_row(
        make_row(quantity="")
    )

    assert event is None
    assert error is not None


def test_blank_event_id():
    event, error = validate_row(
        make_row(event_id="")
    )

    assert event is None
    assert error is not None


def test_blank_symbol():
    event, error = validate_row(
        make_row(symbol="")
    )

    assert event is None
    assert error is not None