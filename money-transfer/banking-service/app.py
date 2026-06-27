import argparse
import logging

from flask import Flask, jsonify, render_template, request

from banking_service import BadRequest, BankingService, ServiceError

app = Flask(__name__)
service = BankingService()


# ---- error handling ----------------------------------------------------


@app.errorhandler(ServiceError)
def handle_service_error(error):
    return jsonify({"error": error.message}), error.status


def _body():
    return request.get_json(force=True, silent=True) or {}


def _api_gate(city):
    """Return a 503 response if the bank's API access is disabled, else None.

    Raises NotFound (404) if the bank does not exist.
    """
    if not service.is_api_enabled(city):
        return (
            jsonify(
                {"error": f"API access for bank '{city}' is currently unavailable"}
            ),
            503,
        )
    return None


# ---- UI ----------------------------------------------------------------


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/state")
def state():
    """Full state snapshot, polled by the browser for realtime updates."""
    return jsonify(service.snapshot())


# ---- operator / admin endpoints (never gated) --------------------------


@app.post("/admin/banks")
def admin_create_bank():
    service.create_bank((_body().get("city") or "").strip())
    return jsonify({"ok": True}), 201


@app.post("/admin/banks/<city>/api")
def admin_set_api(city):
    service.set_api_enabled(city, bool(_body().get("enabled")))
    return jsonify({"ok": True})


@app.post("/admin/banks/<city>/accounts")
def admin_create_account(city):
    body = _body()
    service.create_account(
        city, str(body.get("account_id", "")).strip(), body.get("initial_balance", 0)
    )
    return jsonify({"ok": True}), 201


@app.delete("/admin/banks/<city>/accounts/<account_id>")
def admin_delete_account(city, account_id):
    service.delete_account(city, account_id)
    return jsonify({"ok": True})


@app.post("/admin/banks/<city>/accounts/<account_id>/adjust")
def admin_adjust(city, account_id):
    """Manual operator credit/debit. Reuses deposit/withdraw, no idempotency key."""
    body = _body()
    direction = body.get("direction")
    amount = body.get("amount")
    if direction == "deposit":
        confirmation = service.deposit(city, account_id, amount)
    elif direction == "withdraw":
        confirmation = service.withdraw(city, account_id, amount)
    else:
        raise BadRequest("direction must be 'deposit' or 'withdraw'")
    return jsonify({"confirmation": confirmation})


# ---- public API endpoints (gated per bank) -----------------------------


@app.post("/api/banks/<city>/accounts")
def api_create_account(city):
    gate = _api_gate(city)
    if gate:
        return gate
    body = _body()
    service.create_account(
        city, str(body.get("account_id", "")).strip(), body.get("initial_balance", 0)
    )
    return jsonify({"ok": True}), 201


@app.get("/api/banks/<city>/accounts/<account_id>/balance")
def api_get_balance(city, account_id):
    gate = _api_gate(city)
    if gate:
        return gate
    return jsonify({"balance": service.get_balance(city, account_id)})


@app.post("/api/banks/<city>/accounts/<account_id>/withdraw")
def api_withdraw(city, account_id):
    gate = _api_gate(city)
    if gate:
        return gate
    body = _body()
    confirmation = service.withdraw(
        city, account_id, body.get("amount"), body.get("idempotency_key")
    )
    return jsonify({"confirmation": confirmation})


@app.post("/api/banks/<city>/accounts/<account_id>/deposit")
def api_deposit(city, account_id):
    gate = _api_gate(city)
    if gate:
        return gate
    body = _body()
    confirmation = service.deposit(
        city, account_id, body.get("amount"), body.get("idempotency_key")
    )
    return jsonify({"confirmation": confirmation})


@app.post("/api/reset")
def api_reset():
    """Global reset: wipe every bank and account back to the first-launch state."""
    service.reset()
    return jsonify({"ok": True})


DEFAULT_PORT = 9109

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-bank account service (web UI + API)"
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="host/interface to bind (default: 127.0.0.1)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
    # Quiet the per-request access log; 250ms polling would otherwise flood it.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    app.run(host=args.host, port=args.port, threaded=True)
