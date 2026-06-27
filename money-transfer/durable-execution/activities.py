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
    idempotency_key=f"{info.workflow_run_id}-{info.activity_id}"

    bank = BankingService(payment.hostname)
    confirmation = bank.withdraw(
        payment.account_id, payment.amount, idempotency_key
    )

    # Demonstration hook (see README). When CRASH_AFTER_WITHDRAW is set, kill
    # the worker process *after* the bank has already debited the account but
    # *before* Temporal can record the activity's result. Temporal will retry
    # the activity on the next attempt; because it sends the same idempotency
    # key, the bank ignores the duplicate and the account is debited only once.
    if os.getenv("CRASH_AFTER_WITHDRAW") and activity.info().attempt == 1:
        activity.logger.warning("Simulating a crash after the withdrawal")
        os._exit(1)

    return confirmation


@activity.defn
def deposit(payment: PaymentDetails) -> str:
    """Credit the destination account and return the confirmation number."""
    info = activity.info()
    idempotency_key=f"{info.workflow_run_id}-{info.activity_id}"

    bank = BankingService(payment.hostname)
    return bank.deposit(
        payment.account_id, payment.amount, idempotency_key
    )
