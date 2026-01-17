from faker import Faker
import csv
import random
from datetime import datetime, timedelta

fake = Faker("en_US")
Faker.seed(42)

with open("fixtures/transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["user_id", "amount", "credit_card", "ip_address", "timestamp"])

    for _ in range(5000):
        # user_id corresponds to customer_id (1-1000)
        user_id = random.randint(1, 1000)

        # Transaction amount between $1 and $10,000
        amount = round(random.uniform(1.00, 10000.00), 2)

        # Generate credit card number
        credit_card = fake.credit_card_number()

        # Generate IP address
        ip_address = fake.ipv4()

        # Generate timestamp within last 365 days
        days_ago = random.randint(0, 365)
        timestamp = (
            datetime.now()
            - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
        ).strftime("%Y-%m-%d %H:%M:%S")

        writer.writerow([user_id, amount, credit_card, ip_address, timestamp])

print("Generated 5000 transaction records")
