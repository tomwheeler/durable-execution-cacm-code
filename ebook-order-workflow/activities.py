import asyncio
import random
from pathlib import Path

from temporalio import activity
from temporalio.exceptions import ApplicationError

from shared import PaymentInput, OrderConfirmation

# Used by charge_customer and refund_customer to store idempotency keys
past_charges = {}
past_refunds = {}


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
async def charge_customer(input_data: PaymentInput) -> str:
    activity.logger.info(
        f"Charging {input_data.amount} on card {input_data.payment_card_number}"
    )

    # Use an idempotency key to handle the edge case of the Worker crashing after
    # the charge was completed but before it was reported to the Temporal Service.
    # NOTE: This is a toy implementation for demonstration purposes only. This is
    # only effective for a single Worker and the list of keys is lost upon a
    # restart.
    if input_data.order_number in past_charges:
        activity.logger.info("Returning confirmation from earlier charge")
        return past_charges[input_data.order_number]

    # Creating a file named 'charge.fail' in your home directory
    # cause this Activity to fail, allowing you to test what happens
    # during a network or service outage. Removing that file enables
    # the Activity to complete during the next retry attempt.
    if Path.home().joinpath("charge.fail").is_file():
        raise Exception("Failed to charge customer (simulated failure)")

    # generate a confirmation number that looks somewhat realistic
    confirmation = f"CHARGE{input_data.amount}{input_data.order_number}"
    past_charges[input_data.order_number] = confirmation

    activity.logger.info(
        f"Successfully charged customer. Confirmation # {confirmation}."
    )
    return confirmation


@activity.defn
async def refund_customer(input_data: PaymentInput) -> str:
    activity.logger.info(
        f"Refunding {input_data.amount} to card {input_data.payment_card_number}"
    )

    if input_data.order_number in past_refunds:
        activity.logger.info("Returning confirmation from earlier refund")
        return past_refunds[input_data.order_number]

    confirmation = f"REFUND{input_data.amount}{input_data.order_number}"
    past_refunds[input_data.order_number] = confirmation

    activity.logger.info(
        f"Successfully refunded customer. Confirmation # {confirmation}."
    )
    return confirmation


@activity.defn
async def send_email(input_data: OrderConfirmation) -> None:
    activity.logger.info(f"Sending email to {input_data.email_addr}")

    # Simulate a failure in half of cases (adjust as needed)
    # Marking it non-retryable triggers the compensation in the workflow.
    # An alternative is to limit the number of retries via a custom
    # retry policy for this activity, in which case the compensation
    # will be triggered once all retry attempts have been exhausted.
    if random.randrange(100) >= 50:
        raise ApplicationError(
            "Failed to send email to customer (simulated failure)",
            non_retryable=True,
        )

    # simulate time spent connecting to SMTP server and sending mail
    await asyncio.sleep(2)

    activity.logger.info(f"Successfully sent email to {input_data.email_addr}")
