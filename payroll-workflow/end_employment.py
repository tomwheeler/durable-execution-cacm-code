import asyncio

from shared import WORKFLOW_ID
from temporalio.client import Client
from workflow import PayrollWorkflow


async def main():
    client = await Client.connect("localhost:7233", namespace="default")
    handle = client.get_workflow_handle(WORKFLOW_ID)

    await handle.signal(PayrollWorkflow.end_employment)
    print("Ended employment. Payroll will stop at the start of the next pay period.")


if __name__ == "__main__":
    asyncio.run(main())
