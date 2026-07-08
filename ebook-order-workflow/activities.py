import asyncio
import random
from pathlib import Path

from temporalio import activity
from temporalio.exceptions import ApplicationError

from shared import PaymentInput, Receipt


@activity.defn
async def validate_coupon(coupon_code: str) -> int:
    activity.logger.info(f"Validating coupon code: {coupon_code}")

    discount_percent = 0
    if coupon_code == "SAVENOW10":
        discount_percent = 10
    elif coupon_code == "READANDSAVE25":
        discount_percent = 25
    elif coupon_code == "EMPLOYEE":
        discount_percent = 75

    activity.logger.info(f"Coupon code discount is {discount_percent}%")
    return discount_percent


@activity.defn
async def charge_customer(input: PaymentInput) -> str:
    activity.logger.info(f"Charging {input.amount} to customer")

    # Creating a file named 'charge.fail' in your home directory
    # causes this Activity to fail, allowing you to test what happens
    # during a network or service outage. Removing that file enables
    # the Activity to complete during the next retry attempt.
    if Path.home().joinpath("charge.fail").is_file():
        raise Exception("Failed to charge customer (intentional failure)")

    # generate a confirmation number that looks realistic
    confirmation = f"CHARGE{input.amount}{input.order_number}"

    activity.logger.info(f"Successful charge: Confirmation #{confirmation}")
    return confirmation


@activity.defn
async def refund_customer(input: PaymentInput) -> str:
    activity.logger.info(f"Refunding {input.amount} to customer")

    # generate a confirmation number that looks realistic
    confirmation = f"REFUND{input.amount}{input.order_number}"

    activity.logger.info(f"Successful refund: Confirmation # {confirmation}.")
    return confirmation


@activity.defn
async def send_email(input: Receipt) -> None:
    activity.logger.info(f"Sending email to {input.email_addr}")

    # Simulate a failure in one-fifth of cases (adjust as needed).
    # Marking it non-retryable triggers compensation (refund) in the
    # workflow. An alternative approach is to change the workflow code
    # to use a custom retry policy for this activity that limits the
    # maximum number of retry attempts, which will trigger compensation
    # once that limit is reached.
    if random.randrange(100) >= 80:
        raise ApplicationError(
            "Failed to send email to customer (simulated failure)",
            non_retryable=True,
        )

    # simulate time spent connecting to SMTP server and sending mail
    await asyncio.sleep(random.randrange(3))

    activity.logger.info(f"Successfully sent email to {input.email_addr}")
