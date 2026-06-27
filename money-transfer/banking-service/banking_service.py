import hashlib
import json
import logging
import os
import re
import secrets
import threading
from datetime import datetime

logger = logging.getLogger("banking_service")

STATE_FILE = "bank-state.json"

# A bank is identified by the city it is in: a single lowercase word of
# letters only (so "seattle" is valid but "san francisco", "st. louis",
# and "o'fallon" are not).
CITY_PATTERN = re.compile(r"^[a-z]+$")

# A confirmation number's suffix follows a primary slice derived from the
# transaction's economic identity (bank, type, account, amount). How the
# suffix is formed depends on whether an idempotency key was supplied:
#
#   * With a key, the suffix is a short deterministic hash of the key. Giving
#     the key fewer characters makes it the least influential field while
#     still letting it affect the confirmation number, and ensures a retried
#     request reproduces its original confirmation number.
#   * Without a key, there is no idempotency contract -- every call is a
#     distinct transaction -- so the suffix is random, guaranteeing each one
#     gets its own confirmation number instead of colliding with identical
#     transactions.
#
# The four primary characters give 16**4 (65,536) values, so two fully
# distinct keyed transactions collide only about one in 65,536 times -- under
# one in ten thousand. The single key character means two transactions that
# differ only by idempotency key collide about one in sixteen times, which is
# the deliberate cost of treating the key as least important. The six random
# characters give 16**6 (~16.8 million) values for the no-key case.
PRIMARY_HASH_LENGTH = 4
KEY_HASH_LENGTH = 1
RANDOM_SUFFIX_LENGTH = 6


class ServiceError(Exception):
    """Base class for errors that map to an HTTP status code."""

    status = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class BadRequest(ServiceError):
    status = 400


class NotFound(ServiceError):
    status = 404


class Conflict(ServiceError):
    status = 409


def _short_hash(value, length):
    """Return the first `length` hex characters (uppercased) of SHA-256(value)."""
    return hashlib.sha256(str(value).encode()).hexdigest()[:length].upper()


def _make_confirmation(bank, transaction_type, account_id, amount, idempotency_key):
    """Derive a short, uppercase confirmation number.

    With an idempotency key, the result is deterministic: the same (bank,
    transaction type, account ID, amount, idempotency key) always produces the
    same confirmation number, and the key is the least influential field.
    Without an idempotency key, each call gets a unique random suffix so that
    repeated identical transactions do not collide on the same number.
    """
    prefix = "WD" if transaction_type == "withdraw" else "DEP"
    primary = _short_hash(
        f"{bank}|{transaction_type}|{account_id}|{amount}", PRIMARY_HASH_LENGTH
    )
    if idempotency_key is None:
        suffix = secrets.token_hex(RANDOM_SUFFIX_LENGTH).upper()[:RANDOM_SUFFIX_LENGTH]
    else:
        suffix = _short_hash(idempotency_key, KEY_HASH_LENGTH)
    return f"{prefix}-{bank.upper()}-{account_id}-{primary}{suffix}"


def _seeded_bank(account_id, balance, timestamp):
    """Build a bank with a single freshly opened account and no seen requests."""
    return {
        "api_enabled": True,
        "accounts": {account_id: {"balance": balance}},
        "transactions": {
            account_id: [
                {
                    "timestamp": timestamp,
                    "type": "open",
                    "amount": balance,
                    "confirmation": None,
                    "balance_after": balance,
                }
            ]
        },
        "seen_requests": {},
    }


def _default_state():
    """The state on first use and immediately after a reset.

    Two banks, each with one account holding $1000, and an empty idempotency
    map.
    """
    timestamp = datetime.now().isoformat(timespec="seconds")
    return {
        "banks": {
            "seattle": _seeded_bank("B789", 1000, timestamp),
            "miami": _seeded_bank("A123", 1000, timestamp),
        }
    }


class BankingService:
    """Maintains balances for multiple banks, each with multiple accounts.

    All state (banks, per-bank API on/off status, account balances, the
    idempotency map, and the processed-transaction log) is held in memory
    and persisted to a human-readable JSON file so nothing is lost across
    restarts. Writes are atomic (temp file + os.replace) and serialized with
    a lock.
    """

    def __init__(self, state_file=STATE_FILE):
        self._state_file = state_file
        self._lock = threading.RLock()
        self._state = self._load()

    # ---- persistence ---------------------------------------------------

    def _load(self):
        if os.path.exists(self._state_file):
            with open(self._state_file, "r") as f:
                return json.load(f)
        return _default_state()

    def _save(self):
        """Atomically write state to disk so a crash mid-write can't corrupt it."""
        tmp = f"{self._state_file}.tmp"
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self._state_file)

    # ---- lookups -------------------------------------------------------

    def _bank(self, city):
        bank = self._state["banks"].get(city)
        if bank is None:
            raise NotFound(f"Bank '{city}' does not exist")
        return bank

    def _account(self, city, account_id):
        bank = self._bank(city)
        if account_id not in bank["accounts"]:
            raise NotFound(f"Account '{account_id}' does not exist at bank '{city}'")
        return bank, bank["accounts"][account_id]

    @staticmethod
    def _validate_amount(amount, allow_zero=False):
        try:
            value = int(amount)
        except (TypeError, ValueError):
            raise BadRequest("Amount must be an integer number of dollars")
        if value < 0 or (value == 0 and not allow_zero):
            raise BadRequest("Amount must be a positive integer number of dollars")
        return value

    def create_bank(self, city):
        with self._lock:
            if not CITY_PATTERN.match(city or ""):
                raise BadRequest(
                    "Bank name must be a single lowercase word containing only letters"
                )
            if city in self._state["banks"]:
                raise Conflict(f"Bank '{city}' already exists")
            self._state["banks"][city] = {
                "api_enabled": True,
                "accounts": {},
                "transactions": {},
                "seen_requests": {},
            }
            self._save()
            logger.info("create_bank: created bank %s", city)

    def set_api_enabled(self, city, enabled):
        with self._lock:
            bank = self._bank(city)
            bank["api_enabled"] = bool(enabled)
            self._save()
            logger.info(
                "api: bank %s API access %s",
                city,
                "enabled" if enabled else "disabled",
            )

    def is_api_enabled(self, city):
        with self._lock:
            return self._bank(city)["api_enabled"]

    def create_account(self, city, account_id, initial_balance):
        with self._lock:
            bank = self._bank(city)
            account_id = str(account_id)
            if not account_id:
                raise BadRequest("Account ID is required")
            if account_id in bank["accounts"]:
                raise Conflict(
                    f"Account '{account_id}' already exists at bank '{city}'"
                )
            initial_balance = self._validate_amount(initial_balance, allow_zero=True)
            bank["accounts"][account_id] = {"balance": initial_balance}
            bank["transactions"][account_id] = []
            self._record(
                bank, account_id, "open", initial_balance, None, initial_balance
            )
            self._save()
            logger.info(
                "create_account: bank %s account %s created with balance $%d",
                city,
                account_id,
                initial_balance,
            )

    def delete_account(self, city, account_id):
        with self._lock:
            bank, _ = self._account(city, account_id)
            del bank["accounts"][account_id]
            bank["transactions"].pop(account_id, None)
            stale = [
                k for k in bank["seen_requests"] if k.split("|", 2)[1] == account_id
            ]
            for k in stale:
                del bank["seen_requests"][k]
            self._save()
            logger.info("delete_account: bank %s account %s deleted", city, account_id)

    def get_balance(self, city, account_id):
        with self._lock:
            _, account = self._account(city, account_id)
            balance = account["balance"]
            logger.info(
                "get_balance: bank %s account %s balance is $%d",
                city,
                account_id,
                balance,
            )
            return balance

    def withdraw(self, city, account_id, amount, idempotency_key=None):
        return self._transact(city, account_id, "withdraw", amount, idempotency_key)

    def deposit(self, city, account_id, amount, idempotency_key=None):
        return self._transact(city, account_id, "deposit", amount, idempotency_key)

    def _transact(self, city, account_id, transaction_type, amount, idempotency_key):
        with self._lock:
            bank, account = self._account(city, account_id)
            amount = self._validate_amount(amount)
            seen_key = f"{transaction_type}|{account_id}|{idempotency_key}"

            # A repeated request with a known idempotency key is a duplicate:
            # return the original confirmation without changing the balance.
            if idempotency_key is not None and seen_key in bank["seen_requests"]:
                confirmation = bank["seen_requests"][seen_key]
                logger.info(
                    "%s: bank %s account %s ignoring duplicate request (confirmation #: %s)",
                    transaction_type,
                    city,
                    account_id,
                    confirmation,
                )
                return confirmation

            if transaction_type == "withdraw":
                if amount > account["balance"]:
                    raise BadRequest("Insufficient funds for withdrawal")
                account["balance"] -= amount
                verb = "debited"
            else:
                account["balance"] += amount
                verb = "credited"

            confirmation = _make_confirmation(
                city, transaction_type, account_id, amount, idempotency_key
            )
            logger.info(
                "%s: bank %s account %s %s $%d (confirmation #: %s)",
                transaction_type,
                city,
                account_id,
                verb,
                amount,
                confirmation,
            )
            self._record(
                bank,
                account_id,
                transaction_type,
                amount,
                confirmation,
                account["balance"],
            )
            if idempotency_key is not None:
                bank["seen_requests"][seen_key] = confirmation
            self._save()
            return confirmation

    def get_transactions(self, city, account_id):
        """Return processed transactions for an account, newest first."""
        with self._lock:
            bank, _ = self._account(city, account_id)
            return list(reversed(bank["transactions"].get(account_id, [])))

    def reset(self):
        """Restore the first-launch state: the two seeded banks, empty idempotency map."""
        with self._lock:
            self._state = _default_state()
            if os.path.exists(self._state_file):
                os.remove(self._state_file)
            logger.info("reset: restored default banks and accounts")

    def snapshot(self):
        """Return a deep copy of the full state for the UI to render."""
        with self._lock:
            return json.loads(json.dumps(self._state))

    # ---- internal ------------------------------------------------------

    def _record(
        self, bank, account_id, transaction_type, amount, confirmation, balance_after
    ):
        """Append a processed transaction. Ignored duplicates never get here."""
        bank["transactions"].setdefault(account_id, []).append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "type": transaction_type,
                "amount": amount,
                "confirmation": confirmation,
                "balance_after": balance_after,
            }
        )
