from order_service.models import OrderEvent
from position_service.store import PositionStore


def test_buy_increases_position():
    store = PositionStore()

    accepted, reason = store.apply_event(
        OrderEvent(
            "evt-1",
            "RELIANCE",
            "BUY",
            90,
        )
    )

    assert accepted is True
    assert reason == "accepted"
    assert store.get_positions() == {
        "RELIANCE": 90
    }


def test_sell_decreases_position():
    store = PositionStore()

    store.apply_event(
        OrderEvent(
            "evt-1",
            "RELIANCE",
            "BUY",
            100,
        )
    )

    store.apply_event(
        OrderEvent(
            "evt-2",
            "RELIANCE",
            "SELL",
            30,
        )
    )

    assert store.get_positions() == {
        "RELIANCE": 70
    }


def test_negative_position():
    store = PositionStore()

    store.apply_event(
        OrderEvent(
            "evt-1",
            "TCS",
            "SELL",
            75,
        )
    )

    assert store.get_positions() == {
        "TCS": -75
    }


def test_zero_position_is_kept():
    store = PositionStore()

    store.apply_event(
        OrderEvent(
            "evt-1",
            "INFY",
            "BUY",
            100,
        )
    )

    store.apply_event(
        OrderEvent(
            "evt-2",
            "INFY",
            "SELL",
            100,
        )
    )

    assert store.get_positions() == {
        "INFY": 0
    }


def test_duplicate_event_is_ignored():
    store = PositionStore()

    first = OrderEvent(
        "evt-1",
        "RELIANCE",
        "BUY",
        90,
    )

    second = OrderEvent(
        "evt-1",
        "RELIANCE",
        "SELL",
        999,
    )

    assert store.apply_event(first) == (
        True,
        "accepted",
    )

    assert store.apply_event(second) == (
        False,
        "duplicate",
    )

    assert store.get_positions() == {
        "RELIANCE": 90
    }