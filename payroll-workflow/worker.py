import asyncio
import logging

from activities import deposit
from shared import TASK_QUEUE_NAME
from temporalio.client import Client
from temporalio.worker import Worker
from workflow import PayrollWorkflow


async def main():
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect("localhost:7233", namespace="default")

    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[PayrollWorkflow],
        activities=[deposit],
    )
    logging.info("Starting the worker...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
