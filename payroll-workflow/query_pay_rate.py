import asyncio

from shared import WORKFLOW_ID
from temporalio.client import Client
from workflow import PayrollWorkflow


async def main():
    client = await Client.connect("localhost:7233", namespace="default")
    handle = client.get_workflow_handle(WORKFLOW_ID)

    pay_rate = await handle.query(PayrollWorkflow.get_pay_rate)
    print(f"Current pay is ${pay_rate} per pay period")


if __name__ == "__main__":
    asyncio.run(main())
