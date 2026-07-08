import asyncio
import logging

from activities import validate_coupon, charge_customer, refund_customer, send_email
from shared import TASK_QUEUE_NAME
from temporalio.client import Client
from temporalio.worker import Worker
from workflow import BookOrderWorkflow


async def main():
    client = await Client.connect("localhost:7233", namespace="default")

    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[BookOrderWorkflow],
        activities=[validate_coupon, charge_customer, refund_customer, send_email],
    )
    logging.info("Starting the worker...")
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
