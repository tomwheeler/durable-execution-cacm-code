import asyncio
import random

from shared import TASK_QUEUE_NAME, Book, BookOrder

from temporalio.client import Client
from workflow import BookOrderWorkflow


async def main():
    # Connect to a Temporal Service running locally
    client = await Client.connect("localhost:7233", namespace="default")

    order = create_book_order()

    handle = await client.start_workflow(
        BookOrderWorkflow.order_books,
        order,
        id=f"ebook-order-{order.order_number}",
        task_queue=TASK_QUEUE_NAME,
    )

    result = await handle.result()
    print(f"Result:\n{result}")


def create_book_order() -> BookOrder:
    book1 = Book(sku="a197", description="London Travel Guide", price=1500)
    book2 = Book(sku="b323", description="Favorite French Recipes", price=2400)
    book3 = Book(sku="c482", description="Woodworking for the Beginner", price=1800)

    books = [book1, book2, book3]

    book_order = BookOrder(
        order_number=f"XD{random.randint(1000, 9999)}",
        items=books,
        coupon_code="SAVENOW10",
        email_addr="customer@example.com",
        payment_card_number="1234 5678 9012 3456",
    )
    return book_order


if __name__ == "__main__":
    asyncio.run(main())
