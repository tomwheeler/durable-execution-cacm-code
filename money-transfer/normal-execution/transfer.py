import sys
from bankingapi import BankingService


def transfer_money():
    bank_one = BankingService("api.miami-bank.example.com")
    confirmation1 = bank_one.withdraw("A123", 100)
    print("Completed withdrawal")

    # Uncomment this line to induce a crash
    #sys.exit("Crash!")

    bank_two = BankingService("api.seattle-bank.example.com")
    confirmation2 = bank_two.deposit("B789", 100)
    print("Completed deposit")

    return generate_success_message(confirmation1, confirmation2)


def generate_success_message(c1, c2):
    """Returns a confirmation for a successful transaction."""
    return f"SUCCESS: Withdrawal ({c1}), Deposit ({c2})"


if __name__ == "__main__":
    transfer_money()
