import argparse
import csv
import logging
import os
import time

from .sender import PositionServiceClient
from .validator import (
    REQUIRED_COLUMNS,
    validate_row,
)


logger = logging.getLogger("order_service")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )


def process_csv(
    file_path: str,
    position_service_url: str,
    max_events_per_second: float = 50.0,
    timeout: float = 5.0,
    max_retries: int = 3,
):
    if max_events_per_second <= 0:
        raise ValueError(
            "max_events_per_second must be greater than zero"
        )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    client = PositionServiceClient(
        base_url=position_service_url,
        timeout=timeout,
        max_retries=max_retries,
    )

    seen_event_ids = set()

    min_interval = 1.0 / max_events_per_second

    last_send_time = 0.0

    logger.info(
        "Starting CSV processing: %s",
        file_path,
    )

    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            logger.error(
                "CSV does not contain a header"
            )
            return

        missing_columns = (
            REQUIRED_COLUMNS
            - set(reader.fieldnames)
        )

        if missing_columns:
            logger.error(
                "Missing CSV columns: %s",
                ", ".join(sorted(missing_columns)),
            )
            return

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                event, error = validate_row(row)

                if error:
                    logger.warning(
                        "Rejected row=%d reason=%s",
                        row_number,
                        error,
                    )
                    continue

                if event.event_id in seen_event_ids:
                    logger.info(
                        "Ignoring duplicate event_id=%s",
                        event.event_id,
                    )
                    continue

                seen_event_ids.add(event.event_id)

                logger.info(
                    "Accepted event_id=%s",
                    event.event_id,
                )

                # Throttle before sending.
                now = time.monotonic()

                elapsed = (
                    now - last_send_time
                )

                if elapsed < min_interval:
                    time.sleep(
                        min_interval - elapsed
                    )

                sent = client.send(event)

                last_send_time = time.monotonic()

                if not sent:
                    logger.error(
                        "Delivery failed for event_id=%s",
                        event.event_id,
                    )

            except Exception:
                logger.exception(
                    "Unexpected error on row=%d. "
                    "Continuing.",
                    row_number,
                )

    logger.info(
        "Input processing complete"
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--file",
        default=os.getenv(
            "ORDER_FILE",
            "data/order_updates.csv",
        ),
    )

    parser.add_argument(
        "--position-url",
        default=os.getenv(
            "POSITION_SERVICE_URL",
            "http://127.0.0.1:8000",
        ),
    )

    parser.add_argument(
        "--rate",
        type=float,
        default=float(
            os.getenv(
                "MAX_EVENTS_PER_SECOND",
                "50",
            )
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=float(
            os.getenv(
                "HTTP_TIMEOUT",
                "5",
            )
        ),
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=int(
            os.getenv(
                "HTTP_RETRIES",
                "3",
            )
        ),
    )

    return parser.parse_args()


def main():
    configure_logging()

    args = parse_args()

    process_csv(
        file_path=args.file,
        position_service_url=args.position_url,
        max_events_per_second=args.rate,
        timeout=args.timeout,
        max_retries=args.retries,
    )


if __name__ == "__main__":
    main()