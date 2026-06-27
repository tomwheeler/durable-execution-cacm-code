"""Data passed between the starter, workflow, and activities.

These are plain dataclasses. Temporal's default data converter serializes
them to JSON automatically because the workflow and activity signatures are
type-annotated.
"""

from dataclasses import dataclass


@dataclass
class TransferDetails:
    """Input to the money transfer: move `amount` dollars from the source
    account at one bank to the destination account at another bank."""

    source_hostname: str
    source_account: str
    dest_hostname: str
    dest_account: str
    amount: int


@dataclass
class PaymentDetails:
    """Input to a single withdraw or deposit activity.
    """

    hostname: str
    account_id: str
    amount: int
