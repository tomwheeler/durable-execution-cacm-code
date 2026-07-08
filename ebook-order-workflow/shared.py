from dataclasses import dataclass
from typing import List

TASK_QUEUE_NAME = "ebook-orders"


@dataclass
class Book:
    sku: str
    description: str
    price: int


@dataclass
class BookOrder:
    order_number: str
    items: List[Book]
    coupon_code: str | None
    email_addr: str
    payment_card_number: str


@dataclass
class Receipt:
    order_number: str
    amount_charged: int
    payment_confirmation: str
    email_addr: str


@dataclass
class PaymentInput:
    order_number: str
    payment_card_number: str
    description: str
    amount: int
