# Order Update & Position Services

A two-service Python application that reads order updates from a CSV file and maintains the current position for each symbol.

## Architecture

```text
order_updates.csv
       |
       v
+---------------------+
| Order Update        |
| Service             |
|                     |
| Read -> Validate    |
| -> Rate Limit       |
| -> Send             |
+----------+----------+
           |
           | HTTP POST /events
           v
+---------------------+
| Position            |
| Service             |
|                     |
| Update positions    |
| Handle duplicates   |
+----------+----------+
           |
           | GET /position
           v
      Current Positions
```



### Communication

The two services communicate over HTTP.

HTTP was chosen because it provides a simple interface between the services, does not require additional infrastructure, and makes the services independently runnable and easy to test.

### State

The Position Service keeps positions and processed event IDs in memory. A lock is used to protect updates and reads when multiple requests are handled concurrently.

---



## Setup



### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```



### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---



## Run



### 1. Start the Position Service

```bash
python -m position_service.main
```

By default it runs on:

```text
http://127.0.0.1:8000
```



### 2. Start the Order Update Service

Open another terminal and run:

```bash
python -m order_service.main \
    --file data/order_updates.csv \
    --position-url http://127.0.0.1:8000
```

The CSV is processed incrementally, so the complete file is not loaded into memory.

---



## Tests

Run all tests with:

```bash
pytest -q
```

The tests cover:

- Event validation
- BUY and SELL position calculations
- Zero and negative positions
- Duplicate event IDs
- Position Service API
- Invalid requests

---



## Configuration



### Order Update Service


| Option           | Default                  | Description               |
| ---------------- | ------------------------ | ------------------------- |
| `--file`         | `data/order_updates.csv` | Input CSV file            |
| `--position-url` | `http://127.0.0.1:8000`  | Position Service URL      |
| `--rate`         | `50`                     | Maximum events per second |
| `--timeout`      | `5`                      | HTTP request timeout      |
| `--retries`      | `3`                      | Number of HTTP retries    |


Example:

```bash
python -m order_service.main \
    --file data/order_updates.csv \
    --position-url http://127.0.0.1:8000 \
    --rate 25 \
    --timeout 5 \
    --retries 3
```



### Position Service


| Option   | Default     | Description |
| -------- | ----------- | ----------- |
| `--host` | `127.0.0.1` | Server host |
| `--port` | `8000`      | Server port |


Example:

```bash
python -m position_service.main \
    --host 127.0.0.1 \
    --port 8000
```

---



## API



### POST `/events`

Adds an order event.

```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-001",
    "symbol": "RELIANCE",
    "transaction_type": "BUY",
    "quantity": 90
  }'
```

Response:

```json
{
  "status": "accepted"
}
```

If the same `event_id` is received again:

```json
{
  "status": "duplicate"
}
```



### GET `/position`

Returns the current position for each symbol.

```bash
curl http://127.0.0.1:8000/position
```

Example response:

```json
{
  "RELIANCE": 90,
  "TCS": -75,
  "INFY": 0
}
```

---



## Validation and Idempotency

- `event_id` and `symbol` must be non-empty.
- `transaction_type` must be `BUY` or `SELL`.
- `quantity` must be a positive integer.
- Invalid CSV rows are logged and skipped.
- Duplicate `event_id`s are ignored; the first valid event wins.
- Positions can be zero or negative.

---



## Limitations and Trade-offs

- Position state and processed event IDs are stored only in memory and are lost when the Position Service restarts.
- HTTP retries are used for temporary failures, but there is no durable message queue.
- If all retries fail, the event is logged as failed and is not automatically recovered.
- No database or external infrastructure is required, keeping the implementation simple for the scope of this assessment.



## AI Assistance

AI tools were used during development for code drafting.