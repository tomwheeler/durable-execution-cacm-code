from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ActivityError

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from activities import validate_coupon, charge_customer, refund_customer, send_email
    from shared import PaymentInput, Receipt, BookOrder


@workflow.defn
class BookOrderWorkflow:
    @workflow.run
    async def process_order(self, order: BookOrder) -> Receipt:
        total_price = sum(item.price for item in order.items)
        workflow.logger.info(
            f"Before discount, total price for order is: {total_price} cents"
        )

        # validate the coupon code, if there is one
        if order.coupon_code:
            discount_percent = await workflow.execute_activity(
                validate_coupon,
                order.coupon_code,
                start_to_close_timeout=timedelta(seconds=10),
            )
            workflow.logger.info(f"applying {discount_percent}% discount")
            total_price -= round(total_price * discount_percent / 100)
            workflow.logger.info(f"Final price is: {total_price}")

        payment_input = PaymentInput(
            order_number=order.order_number,
            payment_card_number=order.payment_card_number,
            description="Order #" + order.order_number,
            amount=total_price,
        )

        payment_confirmation = await workflow.execute_activity(
            charge_customer,
            payment_input,
            start_to_close_timeout=timedelta(seconds=30),
        )

        receipt = Receipt(
            order_number=order.order_number,
            amount_charged=total_price,
            payment_confirmation=payment_confirmation,
            email_addr=order.email_addr,
        )

        try:
            await workflow.execute_activity(
                send_email,
                receipt,
                start_to_close_timeout=timedelta(seconds=15),
            )
        except ActivityError:
            workflow.logger.warning("Email delivery failed; issuing refund")
            try:
                payment_confirmation = await workflow.execute_activity(
                    refund_customer,
                    payment_input,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                receipt.payment_confirmation = payment_confirmation
                receipt.amount_charged = 0
            except ActivityError:
                # If compensation fails, it can be handled outside the
                # system (e.g., by mailing a check to the customer).
                workflow.logger.error("Refund failed: manual intervention required")
                raise

        return receipt
