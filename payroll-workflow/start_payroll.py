import asyncio

from shared import TASK_QUEUE_NAME, WORKFLOW_ID
from temporalio.client import Client
from workflow import PayrollWorkflow


async def main():
    client = await Client.connect("localhost:7233", namespace="default")

    # The employee's bank account number and their pay for each
    # two-week period. Here the pay is $2,000.
    account = "123456789"
    pay = 2000

    handle = await client.start_workflow(
        PayrollWorkflow.run,
        args=[account, pay],
        id=WORKFLOW_ID,
        task_queue=TASK_QUEUE_NAME,
    )
    print(f"Started payroll. Workflow ID: {handle.id}")


if __name__ == "__main__":
    asyncio.run(main())
