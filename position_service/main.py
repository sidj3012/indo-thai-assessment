import argparse
import logging
import os
from http.server import ThreadingHTTPServer

from .api import PositionRequestHandler
from .store import PositionStore


logger = logging.getLogger("position_service")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )


def run_server(host: str, port: int):
    store = PositionStore()

    PositionRequestHandler.store = store

    server = ThreadingHTTPServer(
        (host, port),
        PositionRequestHandler,
    )

    logger.info(
        "Position service listening on %s:%d",
        host,
        port,
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Shutdown requested")

    finally:
        server.server_close()
        logger.info("Position service stopped")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--host",
        default=os.getenv(
            "POSITION_HOST",
            "127.0.0.1",
        ),
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(
            os.getenv(
                "POSITION_PORT",
                "8000",
            )
        ),
    )

    return parser.parse_args()


def main():
    configure_logging()

    args = parse_args()

    run_server(
        args.host,
        args.port,
    )


if __name__ == "__main__":
    main()