import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from order_service.models import OrderEvent
from .store import PositionStore


class PositionRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/position":
            self.send_response(404)
            self.end_headers()
            return

        # BUG:
        # A new store is created for every request.
        store = PositionStore()

        positions = store.get_positions()

        body = json.dumps(positions).encode()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()

        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)

        payload = json.loads(body)

        event = OrderEvent(
            event_id=payload["event_id"],
            symbol=payload["symbol"],
            transaction_type=payload["transaction_type"],
            quantity=payload["quantity"],
        )

        # BUG:
        # Another new store is created here.
        store = PositionStore()
        store.apply_event(event)

        response = {
            "status": "accepted"
        }

        response_body = json.dumps(response).encode()

        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(response_body)),
        )
        self.end_headers()

        self.wfile.write(response_body)