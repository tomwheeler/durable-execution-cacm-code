# Banking service

This application provides the server-side implementation used by the
money transfer. It simulates API servers for multiple banks, each of
which can be independently enabled or disabled. In addition to the
API, it provides a web interface that allows a user to view the
accounts at each bank, see the current balances, and manage both
the banks and accounts. A single command starts a process that serves
both the browser UI and the HTTP APIs.

Although the Temporal code in the `durable-execution` project uses this
service, the service itself has nothing to do with Temporal and does not
contain any Temporal code.

## What it does

* **Seeded default state.** On first launch (and immediately after a reset)
  the service starts with two banks — `miami` with account `A123` and
  `seattle` with account `B789`, each holding $1000 — and an empty map
  used to store idempotency keys.
* **Multiple banks.** A bank is identified by the city it is in: a single
  lowercase word of letters only (`seattle`, `miami`, `denver`). Names such
  as `san francisco`, `st. louis`, or `o'fallon` are rejected. Account IDs
  must be unique within each bank.
* **Browser UI.** Create banks, create and delete accounts, and manually
  credit/debit an account's balance. The main page lists every account at
  every bank with **realtime balances** (the page polls every 250 ms).
  Click an account to see its **processed** transactions, newest first.
  Ignored duplicate requests never appear in that list.
* **Per-bank API control.** Each bank has a **Start API / Stop API** button
  and a status indicator. While a bank's API is stopped, API requests for
  that bank return HTTP `503` with an explanatory message. 
* **Idempotency.** `withdraw` and `deposit` accept an optional idempotency
  key. A repeated request with a known key returns the original confirmation
  number without changing the balance (and logs that it ignored a
  duplicate). Confirmation numbers are uppercase. With an idempotency key,
  a retried request reproduces its number (e.g. `WD-MIAMI-A123-595B6`); 
  without a key each call gets a unique number so that repeated identical
  transactions don't collide.
* **Persistence.** All state is written to a human-readable
  `bank-state.json` in the current directory and reloaded on startup, so
  nothing is lost across restarts. 


## Running

### Prerequisites
* These instructions use the `uv` package manager. Ensure that it is
  [installed](https://docs.astral.sh/uv/getting-started/installation/) and on
  your path. Run `uv sync` in this directory to install dependencies (Flask).
* [Python 3.10](https://www.python.org/downloads/) or higher


### Start the application

```command
uv run python app.py
```

Then open <http://127.0.0.1:9109/> in a browser. The app listens on port
9109 by default. You can override it by using the `--port` (or `-p`) 
option to specify a different port number:

```command
uv run python app.py --port 8000
```

If you do so, you will also need to make a corresponding change to any
client code that expects to access the service at the default port.


## HTTP API

Five service operations are available over HTTP. Four are bank-scoped
operations that are conditionally available based on that bank's current
API status. The fifth, `reset`, is global and not affected by the API
status of any bank.

| Operation | Method & path | Body |
| --- | --- | --- |
| Create account | `POST /api/banks/<city>/accounts` | `{"account_id": "A123", "initial_balance": 1000}` |
| Get balance | `GET /api/banks/<city>/accounts/<id>/balance` | — |
| Withdraw | `POST /api/banks/<city>/accounts/<id>/withdraw` | `{"amount": 100, "idempotency_key": "k1"}` |
| Deposit | `POST /api/banks/<city>/accounts/<id>/deposit` | `{"amount": 100, "idempotency_key": "k2"}` |
| Reset (global) | `POST /api/reset` | — |

The `idempotency_key` field is optional. 

The `reset` operation restores the seeded default state (the `seattle` 
and `miami` banks) rather than emptying everything. Additional banks 
can be created through the UI or the admin endpoint `POST /admin/banks` 
with body `{"city": "..."}`.

### Example

The seeded `miami` bank already has account `A123` with a $1000 balance,
so you can perform transactions with it right away:

```command
# Withdraw $100 twice with the same idempotency key: the balance drops once.
curl -X POST http://127.0.0.1:9109/api/banks/miami/accounts/A123/withdraw \
  -H 'Content-Type: application/json' -d '{"amount":100,"idempotency_key":"k1"}'
curl -X POST http://127.0.0.1:9109/api/banks/miami/accounts/A123/withdraw \
  -H 'Content-Type: application/json' -d '{"amount":100,"idempotency_key":"k1"}'

curl http://127.0.0.1:9109/api/banks/miami/accounts/A123/balance
# -> {"balance": 900}
```

When a bank's API is stopped from the UI, the same calls return:

```json
{"error": "API access for bank 'miami' is currently unavailable"}
```

with HTTP status `503`.
