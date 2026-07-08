"""The money-transfer workflow.

Workflow code is durable and deterministic: Temporal records each step in an
event history and replays it to reconstruct state after a crash. The workflow
orchestrates the withdraw and deposit activities; if the worker dies between
them, execution resumes from where it left off rather than starting over.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import deposit, withdraw
    from shared import PaymentDetails, TransferDetails


@workflow.defn
class MoneyTransferWorkflow:
    @workflow.run
    async def run(self, details: TransferDetails) -> str:
        withdrawal = PaymentDetails(
            hostname=details.source_hostname,
            account_id=details.source_account,
            amount=details.amount,
        )
        confirmation1 = await workflow.execute_activity(
            withdraw,
            withdrawal,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("Completed withdrawal")

        payment = PaymentDetails(
            hostname=details.dest_hostname,
            account_id=details.dest_account,
            amount=details.amount,
        )
        confirmation2 = await workflow.execute_activity(
            deposit,
            payment,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("Completed deposit")

        return f"SUCCESS: Withdrawal ({confirmation1}), Deposit ({confirmation2})"
