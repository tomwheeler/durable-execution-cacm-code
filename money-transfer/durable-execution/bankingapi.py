"""Client for the multi-bank account service HTTP API.

This module provides a convenient API for accessing the
banking service used to simulate calls that modify bank
account balances. This code is unrelated to Temporal.

Example use:

    from bankingapi import BankingService

    bank = BankingService("api.seattle-bank.example.com")
    bank.create_account("B789", 1000)
    confirmation = bank.deposit("B789", 100, "BE83-8EBBEED5165D")
    balance = bank.get_balance("B789")
"""

import json
import urllib.error
import urllib.parse
import urllib.request

# Where to reach the service when no endpoint is supplied.
DEFAULT_ENDPOINT = "localhost:9109"


class BankingAPIError(Exception):
    """Raised when the service returns an error or cannot be reached.

    `status` is the HTTP status code (0 if the service was unreachable) and
    `message` is the human-readable explanation from the service.
    """

    def __init__(self, status, message):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message


class BankingService:
    """A client bound to a single bank, talking to the service over HTTP.

    The first argument simulates a hostname (e.g., api.miami-bank.example.com).
    The bank (city) name is the part after "api." and before "-bank").
    The optional second argument is the host:port combination used to
    access the service, which defaults to localhost:9109.
    """

    def __init__(self, hostname, endpoint=DEFAULT_ENDPOINT):
        self.bank = self._parse_bank(hostname)
        self.base_url = f"http://{endpoint}"

    @staticmethod
    def _parse_bank(hostname):
        name = hostname
        if "api." in name:
            name = name.split("api.", 1)[1]
        bank = name.split("-bank", 1)[0]
        if not bank:
            raise ValueError(f"Could not determine bank name from '{hostname}'")
        return bank

    def create_account(self, account_id, initial_balance):
        """Create an account at this bank with the given starting balance."""
        self._request(
            "POST",
            f"/api/banks/{self.bank}/accounts",
            {"account_id": account_id, "initial_balance": initial_balance},
        )

    def get_balance(self, account_id):
        """Return the current balance (an integer number of dollars)."""
        result = self._request(
            "GET", f"/api/banks/{self.bank}/accounts/{self._enc(account_id)}/balance"
        )
        return result["balance"]

    def withdraw(self, account_id, amount, idempotency_key=None):
        """Debit `amount` dollars; returns the confirmation number."""
        return self._transact("withdraw", account_id, amount, idempotency_key)

    def deposit(self, account_id, amount, idempotency_key=None):
        """Credit `amount` dollars; returns the confirmation number."""
        return self._transact("deposit", account_id, amount, idempotency_key)

    def reset(self):
        """Reset the whole service: remove all banks, accounts, and history."""
        self._request("POST", "/api/reset")

    # there are only utility methods below this point
    def _transact(self, kind, account_id, amount, idempotency_key):
        body = {"amount": amount}
        if idempotency_key is not None:
            body["idempotency_key"] = idempotency_key
        result = self._request(
            "POST",
            f"/api/banks/{self.bank}/accounts/{self._enc(account_id)}/{kind}",
            body,
        )
        return result["confirmation"]

    @staticmethod
    def _enc(value):
        return urllib.parse.quote(str(value), safe="")

    def _request(self, method, path, body=None):
        url = self.base_url + path
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            raw = error.read()
            message = self._error_message(raw) or error.reason
            raise BankingAPIError(error.code, message) from None
        except urllib.error.URLError as error:
            raise BankingAPIError(
                0, f"Could not reach service at {self.base_url}: {error.reason}"
            ) from None

        return json.loads(raw) if raw else {}

    @staticmethod
    def _error_message(raw):
        try:
            return json.loads(raw).get("error")
        except (ValueError, AttributeError):
            return None
