from faker import Faker
import json
import random
from datetime import datetime, timedelta

fake = Faker("en_US")
Faker.seed(42)

# Templates for support messages with embedded PII
message_templates = [
    "Hi, my name is {name} and I'm having trouble accessing my account. My email is {email} and my phone number is {phone}. Can you help?",
    "I need to update my address from {address} to a new location. My SSN on file is {ssn}. Please call me at {phone}.",
    "Hello, this is {name}. I was born on {dob} and I need to verify my identity. My social security number is {ssn}.",
    "My payment didn't go through. Can you verify the details? Email: {email}, Phone: {phone}, Address: {address}, {city}, {state} {zip}",
    "I'm {name}, DOB {dob}. I need to reset my password for {email}. You can reach me at {phone}.",
    "There's an error in my profile. My SSN should be {ssn}, not what's currently shown. Contact me at {phone} or {email}.",
    "Hi, I live at {address}, {city}, {state} {zip}. I'm {name} and my account shows the wrong income of ${income}. My DOB is {dob}.",
    "Can someone call me at {phone}? I'm {name} and need help with my account. My email {email} isn't working.",
    "I need to verify my information: Name: {name}, SSN: {ssn}, DOB: {dob}, Address: {address}, Phone: {phone}",
    "My name is {name}, I was born {dob}. I live at {address} in {city}, {state}. Email: {email}. I'm locked out of my account.",
    "Hello, {name} here. Can you update my phone from {phone} to a new number? My SSN is {ssn} for verification.",
    "I recently moved to {address}, {city}, {state} {zip}. Please update my records. My email is {email} and my SSN is {ssn}.",
    "This is {name}, DOB: {dob}. I need help with a billing issue. You can reach me at {email} or {phone}.",
    "My social security number {ssn} appears to be incorrect in your system. I'm {name}, born on {dob}. Call me at {phone}.",
    "I can't log in with {email}. My name is {name}, address {address}, {city}, {state}. Phone: {phone}.",
]

tickets = []

# Generate 500 tickets
for i in range(500):
    # Random customer_id between 1 and 1000 (assuming 1000 customers)
    customer_id = random.randint(1, 1000)

    # Generate PII data
    pii_data = {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "ssn": fake.ssn(),
        "address": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip": fake.zipcode(),
        "dob": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d"),
        "income": fake.random_int(min=20000, max=250000),
    }

    # Create message with embedded PII
    template = random.choice(message_templates)
    message = template.format(**pii_data)

    # Generate timestamp within last 365 days
    days_ago = random.randint(0, 365)
    timestamp = (
        datetime.now()
        - timedelta(
            days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59)
        )
    ).isoformat()

    tickets.append(
        {"customer_id": customer_id, "message": message, "timestamp": timestamp}
    )

# Write to JSON file
with open("fixtures/support_tickets.json", "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2)

print(f"Generated {len(tickets)} support ticket records")
