"""The worker: a long-running process that executes workflow and activity code.

It polls the task queue for work, runs the workflow logic and the activities,
and reports results back to the Temporal service. Activities here are sync
(they use the blocking `urllib`-based banking client), so they run in a thread
pool executor.
"""

import asyncio
import concurrent.futures
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from activities import deposit, withdraw
from workflow import MoneyTransferWorkflow

TASK_QUEUE = "money-transfer"


async def main():
    # Connect to the Temporal service (the default address used by
    # `temporal server start-dev`).
    client = await Client.connect("localhost:7233")

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[MoneyTransferWorkflow],
            activities=[withdraw, deposit],
            activity_executor=activity_executor,
        )
        print(f"Worker started, polling task queue '{TASK_QUEUE}'")
        await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
