import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from order_service.models import OrderEvent

from .store import PositionStore


logger = logging.getLogger("position_service")


class PositionRequestHandler(BaseHTTPRequestHandler):
    store: PositionStore = None

    def _send_json(
        self,
        status_code: int,
        payload: dict,
    ) -> None:

        body = json.dumps(payload).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()

        self.wfile.write(body)

    def _read_json(self):
        content_length = self.headers.get("Content-Length")

        if content_length is None:
            raise ValueError("Missing Content-Length")

        length = int(content_length)

        if length <= 0:
            raise ValueError("Empty request body")

        body = self.rfile.read(length)

        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON")

    def do_GET(self):
        if self.path != "/position":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "not found"},
            )
            return

        positions = self.store.get_positions()

        self._send_json(
            HTTPStatus.OK,
            positions,
        )

    def do_POST(self):
        if self.path != "/events":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "not found"},
            )
            return

        try:
            payload = self._read_json()

            event = self._parse_event(payload)

            accepted, reason = self.store.apply_event(event)

            if accepted:
                logger.info(
                    "Accepted event_id=%s",
                    event.event_id,
                )

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "accepted"
                    },
                )

            else:
                logger.info(
                    "Duplicate event_id=%s",
                    event.event_id,
                )

                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "duplicate"
                    },
                )

        except (ValueError, KeyError) as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": str(exc)
                },
            )

    @staticmethod
    def _parse_event(payload: dict) -> OrderEvent:
        required = {
            "event_id",
            "symbol",
            "transaction_type",
            "quantity",
        }

        missing = required - payload.keys()

        if missing:
            raise ValueError(
                f"Missing fields: "
                f"{', '.join(sorted(missing))}"
            )

        event_id = payload["event_id"]
        symbol = payload["symbol"]
        transaction_type = payload["transaction_type"]
        quantity = payload["quantity"]

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError(
                "event_id must be a non-empty string"
            )

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError(
                "symbol must be a non-empty string"
            )

        if transaction_type not in {"BUY", "SELL"}:
            raise ValueError(
                "transaction_type must be exactly BUY or SELL"
            )

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError(
                "quantity must be a positive integer"
            )

        if quantity <= 0:
            raise ValueError(
                "quantity must be a positive integer"
            )

        return OrderEvent(
            event_id=event_id,
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
        )