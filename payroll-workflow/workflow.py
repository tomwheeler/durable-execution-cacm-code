from datetime import timedelta

from temporalio import workflow

# Import the activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from activities import deposit

@workflow.defn
class PayrollWorkflow:
    def __init__(self):
        self.is_employed = True
        self.pay_rate = 0
        self.cumulative_pay = 0

    @workflow.run
    async def run(self, account: str, pay_rate: int):
        self.pay_rate = pay_rate

        # Deposit the employee's pay every two weeks for as long as they
        # remain employed. The workflow.sleep call begins a durable timer, 
        # which is maintained by the Temporal service. It can survive 
        # worker restarts and crashes.
        # 
        # For demo purposes, this uses a pay period of 14 seconds 
        # instead of 14 days, but you can change it to any duration
        # you like (just restart the worker afterwards so your change
        # will take effect).
        while self.is_employed:
            await workflow.execute_activity(
                deposit, args=[account, self.pay_rate],
                start_to_close_timeout=timedelta(seconds=30),
            )
            self.cumulative_pay += self.pay_rate
            await workflow.sleep(timedelta(seconds=14))

    @workflow.signal
    def end_employment(self):
        self.is_employed = False

    @workflow.signal
    def set_pay_rate(self, pay_rate: int):
        self.pay_rate = pay_rate

    @workflow.query
    def get_pay_rate(self) -> int:
        return self.pay_rate

    @workflow.query
    def get_cumulative_amount(self) -> int:
        return self.cumulative_pay
