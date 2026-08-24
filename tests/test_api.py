import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest

from position_service.api import (
    PositionRequestHandler,
)
from position_service.store import PositionStore


@pytest.fixture
def server():
    store = PositionStore()

    PositionRequestHandler.store = store

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        PositionRequestHandler,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    yield server

    server.shutdown()
    server.server_close()
    thread.join()


def request(
    server,
    method,
    path,
    body=None,
):
    host, port = server.server_address

    connection = HTTPConnection(
        host,
        port,
        timeout=5,
    )

    headers = {}

    encoded_body = None

    if body is not None:
        encoded_body = json.dumps(body)

        headers["Content-Type"] = (
            "application/json"
        )

    connection.request(
        method,
        path,
        body=encoded_body,
        headers=headers,
    )

    response = connection.getresponse()

    response_body = response.read()

    connection.close()

    return (
        response.status,
        json.loads(
            response_body.decode("utf-8")
        ),
    )


def test_post_and_get_position(server):
    status, body = request(
        server,
        "POST",
        "/events",
        {
            "event_id": "evt-1",
            "symbol": "RELIANCE",
            "transaction_type": "BUY",
            "quantity": 90,
        },
    )

    assert status == 200
    assert body == {
        "status": "accepted"
    }

    status, body = request(
        server,
        "GET",
        "/position",
    )

    assert status == 200

    assert body == {
        "RELIANCE": 90
    }


def test_negative_and_zero_positions(server):
    request(
        server,
        "POST",
        "/events",
        {
            "event_id": "evt-1",
            "symbol": "TCS",
            "transaction_type": "SELL",
            "quantity": 75,
        },
    )

    request(
        server,
        "POST",
        "/events",
        {
            "event_id": "evt-2",
            "symbol": "INFY",
            "transaction_type": "BUY",
            "quantity": 100,
        },
    )

    request(
        server,
        "POST",
        "/events",
        {
            "event_id": "evt-3",
            "symbol": "INFY",
            "transaction_type": "SELL",
            "quantity": 100,
        },
    )

    status, body = request(
        server,
        "GET",
        "/position",
    )

    assert status == 200

    assert body == {
        "TCS": -75,
        "INFY": 0,
    }


def test_duplicate_event(server):
    event = {
        "event_id": "evt-1",
        "symbol": "RELIANCE",
        "transaction_type": "BUY",
        "quantity": 90,
    }

    status, body = request(
        server,
        "POST",
        "/events",
        event,
    )

    assert status == 200
    assert body["status"] == "accepted"

    duplicate = {
        "event_id": "evt-1",
        "symbol": "RELIANCE",
        "transaction_type": "SELL",
        "quantity": 999,
    }

    status, body = request(
        server,
        "POST",
        "/events",
        duplicate,
    )

    assert status == 200
    assert body["status"] == "duplicate"

    _, positions = request(
        server,
        "GET",
        "/position",
    )

    assert positions == {
        "RELIANCE": 90
    }


def test_invalid_transaction_type(server):
    status, body = request(
        server,
        "POST",
        "/events",
        {
            "event_id": "evt-1",
            "symbol": "TCS",
            "transaction_type": "HOLD",
            "quantity": 10,
        },
    )

    assert status == 400
    assert "transaction_type" in body["error"]


def test_invalid_quantity(server):
    status, body = request(
        server,
        "POST",
        "/events",
        {
            "event_id": "evt-1",
            "symbol": "TCS",
            "transaction_type": "BUY",
            "quantity": -10,
        },
    )

    assert status == 400
    assert "quantity" in body["error"]