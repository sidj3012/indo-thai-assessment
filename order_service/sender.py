import json
import logging
import time
import urllib.error
import urllib.request

from .models import OrderEvent


logger = logging.getLogger("order_service")


class PositionServiceClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def send(self, event: OrderEvent) -> bool:
        url = f"{self.base_url}/events"

        payload = json.dumps(
            event.to_dict()
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        for attempt in range(
            1,
            self.max_retries + 1,
        ):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout,
                ) as response:

                    if 200 <= response.status < 300:
                        logger.info(
                            "Successfully sent event_id=%s",
                            event.event_id,
                        )
                        return True

                    logger.error(
                        "Unexpected status %s for event_id=%s",
                        response.status,
                        event.event_id,
                    )

            except urllib.error.HTTPError as exc:
                logger.error(
                    "HTTP error for event_id=%s: %s",
                    event.event_id,
                    exc.code,
                )

            except urllib.error.URLError as exc:
                logger.error(
                    "Connection error for event_id=%s: %s",
                    event.event_id,
                    exc.reason,
                )

            except TimeoutError:
                logger.error(
                    "Timeout for event_id=%s",
                    event.event_id,
                )

            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        logger.error(
            "Failed to deliver event_id=%s",
            event.event_id,
        )

        return False