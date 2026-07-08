"""Activities that move money by calling the banking service.

Activities hold the non-deterministic, fallible parts of the application:
network calls that can time out, fail, and be retried. Temporal retries a
failed activity automatically, so each call carries an idempotency key that
lets the bank recognize and ignore a duplicate.
"""

import os

from temporalio import activity

from bankingapi import BankingService
from shared import PaymentDetails


@activity.defn
def withdraw(payment: PaymentDetails) -> str:
    """Debit the source account and return the confirmation number."""

    # This idempotency key is constant across all Activity retries and
    # unique among all Workflow Executions.
    info = activity.info()
    idempotency_key = f"{info.workflow_run_id}-{info.activity_id}"

    bank = BankingService(payment.hostname)
    confirmation = bank.withdraw(payment.account_id, payment.amount, idempotency_key)

    return confirmation


@activity.defn
def deposit(payment: PaymentDetails) -> str:
    """Credit the destination account and return the confirmation number."""
    info = activity.info()
    idempotency_key = f"{info.workflow_run_id}-{info.activity_id}"

    bank = BankingService(payment.hostname)
    confirmation = bank.deposit(payment.account_id, payment.amount, idempotency_key)

    # Demonstration hook (see README). When CRASH_DURING_DEPOSIT is set, kill
    # the worker process *after* the bank has already credited the account but
    # *before* Temporal can record the activity's result. The activity will be
    # retried, but because it sends the same idempotency key, the bank ignores
    # the duplicate and the account is credit only once. Because of Durable
    # Execution, the previous withdraw step, which was recorded into the
    # history, is not repeated.
    if os.getenv("CRASH_DURING_DEPOSIT") and info.attempt == 1:
        activity.logger.warning("Simulating a crash during deposit")
        os._exit(1)

    return confirmation
