from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ActivityError

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from activities import validate_coupon, charge_customer, refund_customer, send_email
    from shared import PaymentInput, OrderConfirmation, BookOrder


@workflow.defn
class BookOrderWorkflow:
    @workflow.run
    async def order_books(self, order: BookOrder) -> OrderConfirmation:
        total_price = 0
        for book in order.items:
            total_price += book.price
        workflow.logger.info(
            f"Before discount, total price for order is: {total_price} cents"
        )

        # validate the coupon code, if there is one
        discount_percent = 0
        if order.coupon_code:
            discount_percent = await workflow.execute_activity_method(
                validate_coupon,
                order.coupon_code,
                start_to_close_timeout=timedelta(seconds=10),
            )

        if discount_percent > 0:
            workflow.logger.info(f"applying {discount_percent}% discount to order")
            total_price -= round(total_price * discount_percent / 100)
            workflow.logger.info(
                f"After discount, total price for order is: {total_price} cents"
            )

        payment_input = PaymentInput(
            order_number=order.order_number,
            payment_card_number=order.payment_card_number,
            description="Order #" + order.order_number,
            amount=total_price,
        )

        payment_confirmation = await workflow.execute_activity_method(
            charge_customer,
            payment_input,
            start_to_close_timeout=timedelta(seconds=30),
        )

        order_confirmation = OrderConfirmation(
            order_number=order.order_number,
            amount_charged=total_price,
            payment_confirmation=payment_confirmation,
            email_addr=order.email_addr,
        )

        try:
            await workflow.execute_activity_method(
                send_email,
                order_confirmation,
                start_to_close_timeout=timedelta(seconds=15),
            )
        except ActivityError:
            payment_confirmation = await workflow.execute_activity_method(
                refund_customer,
                payment_input,
                start_to_close_timeout=timedelta(seconds=30),
            )
            order_confirmation.payment_confirmation = payment_confirmation
            order_confirmation.amount_charged = 0

        return order_confirmation
