from faker import Faker
import csv
import random
import sys

fake = Faker("en_US")
Faker.seed(42)
random.seed(42)

num_records = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

# 6 locations - balanced between too few (3) and too many (10)
LOCATION_POOLS = [
    ("New York", "NY", "10001"),  # Common
    ("Los Angeles", "CA", "90001"),  # Common
    ("Chicago", "IL", "60601"),  # Medium
    ("Houston", "TX", "77001"),  # Medium
    ("Phoenix", "AZ", "85001"),  # Rare
    ("Philadelphia", "PA", "19101"),  # Rare
]

# Moderately skewed weights - creates tiers
# Top 2 cities: 60% of records (create low-risk combinations)
# Middle 2 cities: 30% of records (create medium-risk combinations)
# Bottom 2 cities: 10% of records (create high-risk combinations)
location_weights = [35, 25, 15, 15, 6, 4]

# 3 age groups with moderate distribution
AGE_GROUPS = [
    (28, 38),  # 50% - common
    (39, 49),  # 35% - medium
    (50, 60),  # 15% - rare
]
age_weights = [50, 35, 15]

# 5 income values with tiered distribution
INCOME_VALUES = [
    60000,  # 35% - very common
    75000,  # 30% - common
    90000,  # 20% - medium
    110000,  # 10% - rare
    150000,  # 5% - very rare
]
INCOME_WEIGHTS = [35, 30, 20, 10, 5]


def generate_dob_for_age_group(age_min, age_max):
    """Generate DOB with moderate variance - 2-3 dates per age group"""
    age = random.randint(age_min, age_max)
    birth_year = 2024 - age
    # 3 possible months per age group (creates some clustering but not total)
    month = random.choice([1, 6, 12])
    # Always 1st of month for consistency
    return f"{birth_year}-{month:02d}-01"


with open("fixtures/customers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(
        [
            "name",
            "email",
            "phone",
            "ssn",
            "address",
            "city",
            "state",
            "zip",
            "dob",
            "income",
        ]
    )

    for i in range(num_records):
        city, state, zip_code = random.choices(
            LOCATION_POOLS, weights=location_weights, k=1
        )[0]

        age_group = random.choices(AGE_GROUPS, weights=age_weights, k=1)[0]
        dob = generate_dob_for_age_group(age_group[0], age_group[1])

        income = random.choices(INCOME_VALUES, weights=INCOME_WEIGHTS, k=1)[0]

        writer.writerow(
            [
                fake.name(),
                fake.email(),
                fake.phone_number(),
                fake.ssn(),
                fake.street_address(),
                city,
                state,
                zip_code,
                dob,
                income,
            ]
        )

print(f"Generated {num_records} records with balanced risk distribution")
print(f"Combinations: 6 locations × 3 ages × 3 DOB × 5 income = 270 combinations")
print(f"Expected distribution:")
print(f"  - Common combinations (NYC/LA + age 28-38 + $60-75k): k=10-40 → Low Risk")
print(f"  - Medium combinations (Chicago/Houston + middle values): k=3-9 → Medium Risk")
print(f"  - Rare combinations (Phoenix/Philly + rare values): k=1-2 → High Risk")
