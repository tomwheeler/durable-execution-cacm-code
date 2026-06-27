from temporalio import activity


@activity.defn
async def deposit(account: str, amount: int) -> None:
    # A real application would call a bank or payment provider here. This
    # example just logs the deposit so you can watch it happen in the
    # Worker's output.
    activity.logger.info(f"Depositing ${amount} into account {account}")
