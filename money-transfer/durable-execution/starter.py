"""Starts a money-transfer workflow execution.

This is the Durable Execution counterpart to running `transfer.py` in the
`normal-execution` example. Instead of running the transfer logic in this
process, it asks the Temporal service to start a workflow; a worker then
carries it out durably.
"""

import asyncio
import uuid

from temporalio.client import Client

from shared import TransferDetails
from workflow import MoneyTransferWorkflow

TASK_QUEUE = "money-transfer"


async def main():
    client = await Client.connect("localhost:7233")

    # Transfer $100 from account A123 at the Miami bank to account B789 at the
    # Seattle bank -- the same transfer performed by the normal-execution
    # example.
    details = TransferDetails(
        source_hostname="api.miami-bank.example.com",
        source_account="A123",
        dest_hostname="api.seattle-bank.example.com",
        dest_account="B789",
        amount=100,
    )

    # A unique workflow ID per run. Each idempotency key the workflow sends to
    # the bank combines the run ID (unique per execution) with the activity ID,
    # so retries within one execution are deduplicated while a brand-new
    # transfer is treated as distinct.
    result = await client.execute_workflow(
        MoneyTransferWorkflow.run,
        details,
        id=f"money-transfer-{uuid.uuid4()}",
        task_queue=TASK_QUEUE,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
