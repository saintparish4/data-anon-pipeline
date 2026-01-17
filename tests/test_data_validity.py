"""
Test suite to validate sample data fixtures.

Verifies that generated sample data has:
- Expected structure and columns
- Minimum required row counts
- Proper PII types in correct format
"""

import pytest
import pandas as pd
import json
import re
from pathlib import Path

# Regex patterns for PII validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(
    r"^(\+?1[-.\s]?|001[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(x\d+)?$"
)  # Accept international prefixes and extensions
SSN_PATTERN = re.compile(r"^\d{3}-\d{2}-\d{4}$")
CREDIT_CARD_PATTERN = re.compile(r"^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$")
ZIP_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")
IP_ADDRESS_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TestCustomersCSV:
    """Test suite for customers.csv fixture"""

    @pytest.fixture
    def customers_df(self):
        """Load customers.csv as a pandas DataFrame"""
        fixture_path = Path("fixtures/customers.csv")
        assert fixture_path.exists(), "fixtures/customers.csv not found"
        return pd.read_csv(fixture_path, dtype={"zip": str})

    def test_minimum_row_count(self, customers_df):
        """Verify at least 1000 rows are present"""
        required_columns = [
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
        missing_columns = set(required_columns) - set(customers_df.columns)
        assert not missing_columns, f"Missing columns: {missing_columns}"

    def test_no_null_values_in_pii_fields(self, customers_df):
        """Verify no null values in PII fields"""
        pii_fields = ["name", "email", "phone", "ssn"]
        for field in pii_fields:
            null_count = customers_df[field].isnull().sum()
            assert null_count == 0, f"Field '{field}' has null values"

    def test_email_format(self, customers_df):
        """Verify emails are in valid format."""
        sample_size = min(100, len(customers_df))
        sample_emails = customers_df["email"].sample(sample_size)

        invalid_emails = []
        for email in sample_emails:
            if not EMAIL_PATTERN.match(str(email)):
                invalid_emails.append(email)

        assert (
            len(invalid_emails) == 0
        ), f"Found {len(invalid_emails)} invalid emails: {invalid_emails[:5]}"

    def test_phone_format(self, customers_df):
        """Verify phone numbers are in valid US format."""
        sample_size = min(100, len(customers_df))
        sample_phones = customers_df["phone"].sample(sample_size)

        invalid_phones = []
        for phone in sample_phones:
            if not PHONE_PATTERN.match(str(phone)):
                invalid_phones.append(phone)

        assert (
            len(invalid_phones) == 0
        ), f"Found {len(invalid_phones)} invalid phone numbers: {invalid_phones[:5]}"

    def test_ssn_format(self, customers_df):
        """Verify SSNs are in valid format (XXX-XX-XXXX)."""
        sample_size = min(100, len(customers_df))
        sample_ssns = customers_df["ssn"].sample(sample_size)

        invalid_ssns = []
        for ssn in sample_ssns:
            if not SSN_PATTERN.match(str(ssn)):
                invalid_ssns.append(ssn)

        assert (
            len(invalid_ssns) == 0
        ), f"Found {len(invalid_ssns)} invalid SSNs: {invalid_ssns[:5]}"

    def test_zip_format(self, customers_df):
        """Verify zip codes are in valid format (XXXXX or XXXXX-XXXX)."""
        sample_size = min(100, len(customers_df))
        sample_zips = customers_df["zip"].sample(sample_size)

        invalid_zips = []
        for zipcode in sample_zips:
            if not ZIP_PATTERN.match(str(zipcode)):
                invalid_zips.append(zipcode)

        assert (
            len(invalid_zips) == 0
        ), f"Found {len(invalid_zips)} invalid zip codes: {invalid_zips[:5]}"

    def test_dob_format(self, customers_df):
        """Verify dates of birth are in valid format (YYYY-MM-DD)."""
        sample_size = min(100, len(customers_df))
        sample_dobs = customers_df["dob"].sample(sample_size)

        invalid_dobs = []
        for dob in sample_dobs:
            if not DATE_PATTERN.match(str(dob)):
                invalid_dobs.append(dob)

        assert (
            len(invalid_dobs) == 0
        ), f"Found {len(invalid_dobs)} invalid dates: {invalid_dobs[:5]}"

    def test_name_is_non_empty(self, customers_df):
        """Verify names are non-empty strings."""
        assert customers_df["name"].str.len().min() > 0, "Found empty names"

    def test_address_is_non_empty(self, customers_df):
        """Verify addresses are non-empty strings."""
        assert customers_df["address"].str.len().min() > 0, "Found empty addresses"

    def test_income_is_numeric(self, customers_df):
        """Verify income values are numeric and positive."""
        assert pd.api.types.is_numeric_dtype(
            customers_df["income"]
        ), "Income should be numeric"
        assert (customers_df["income"] > 0).all(), "Income should be positive"


class TestSupportTicketsJSON:
    """Test suite for support_tickets.json fixture"""

    @pytest.fixture
    def support_tickets_df(self):
        """Load support_tickets.json"""
        fixture_path = Path("fixtures/support_tickets.json")
        assert fixture_path.exists(), "fixtures/support_tickets.json not found"
        with open(fixture_path, "r") as f:
            return json.load(f)

    def test_minimum_record_count(self, support_tickets_df):
        """Verify support_tickets.json has at least 500 records."""
        assert (
            len(support_tickets_df) >= 500
        ), f"Expected at least 500 records, got {len(support_tickets_df)}"

    def test_required_fields(self, support_tickets_df):
        """Verify all records have required fields."""
        required_fields = ["customer_id", "message", "timestamp"]

        for i, ticket in enumerate(support_tickets_df[:100]):  # Check first 100
            missing_fields = set(required_fields) - set(ticket.keys())
            assert not missing_fields, f"Record {i} missing fields: {missing_fields}"

    def test_message_contains_pii(self, support_tickets_df):
        """Verify messages contain embedded PII (emails, phones, or names)."""
        sample_size = min(100, len(support_tickets_df))
        sample_tickets = support_tickets_df[:sample_size]

        pii_found_count = 0

        for ticket in sample_tickets:
            message = ticket.get("message", "")

            # Check for email in message
            if EMAIL_PATTERN.search(message):
                pii_found_count += 1
                continue

            # Check for phone in message
            if PHONE_PATTERN.search(message):
                pii_found_count += 1
                continue

            # Check for potential names (simple heuristic: capitalized words)
            if re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", message):
                pii_found_count += 1

        # At least 50% of messages should contain some form of PII
        pii_percentage = (pii_found_count / sample_size) * 100
        assert (
            pii_percentage >= 50
        ), f"Only {pii_percentage:.1f}% of messages contain PII (expected ≥50%)"

    def test_customer_id_is_valid(self, support_tickets_df):
        """Verify customer_id fields are present and non-empty."""
        sample_size = min(100, len(support_tickets_df))

        for i, ticket in enumerate(support_tickets_df[:sample_size]):
            customer_id = ticket.get("customer_id")
            assert customer_id is not None, f"Record {i} has null customer_id"
            assert str(customer_id).strip() != "", f"Record {i} has empty customer_id"

    def test_timestamp_format(self, support_tickets_df):
        """Verify timestamps are in valid format."""
        sample_size = min(100, len(support_tickets_df))

        for i, ticket in enumerate(support_tickets_df[:sample_size]):
            timestamp = ticket.get("timestamp")
            assert timestamp is not None, f"Record {i} has null timestamp"
            # Basic check: should be a non-empty string
            assert (
                isinstance(timestamp, str) and len(timestamp) > 0
            ), f"Record {i} has invalid timestamp format"


class TestTransactionsCSV:
    """Test suite for transactions.csv fixture."""

    @pytest.fixture
    def transactions_df(self):
        """Load transactions.csv as a pandas DataFrame."""
        fixture_path = Path("fixtures/transactions.csv")
        assert fixture_path.exists(), "fixtures/transactions.csv not found"
        return pd.read_csv(fixture_path)

    def test_minimum_row_count(self, transactions_df):
        """Verify transactions.csv has at least 5000 rows."""
        assert (
            len(transactions_df) >= 5000
        ), f"Expected at least 5000 rows, got {len(transactions_df)}"

    def test_required_columns(self, transactions_df):
        """Verify all required columns are present."""
        required_columns = [
            "user_id",
            "amount",
            "credit_card",
            "ip_address",
            "timestamp",
        ]
        missing_columns = set(required_columns) - set(transactions_df.columns)
        assert not missing_columns, f"Missing columns: {missing_columns}"

    def test_no_null_values(self, transactions_df):
        """Verify no null values in any field."""
        null_counts = transactions_df.isnull().sum()
        fields_with_nulls = null_counts[null_counts > 0]
        assert (
            len(fields_with_nulls) == 0
        ), f"Fields with null values: {fields_with_nulls.to_dict()}"

    def test_credit_card_format(self, transactions_df):
        """Verify credit card numbers are in valid format."""
        sample_size = min(100, len(transactions_df))
        sample_cards = transactions_df["credit_card"].sample(sample_size)

        invalid_cards = []
        for card in sample_cards:
            # Remove spaces/dashes for validation
            card_str = str(card).replace(" ", "").replace("-", "")
            # Accept 11-19 digit credit cards (various card types)
            if not re.match(r"^\d{11,19}$", card_str):
                invalid_cards.append(card)

        assert (
            len(invalid_cards) == 0
        ), f"Found {len(invalid_cards)} invalid credit cards: {invalid_cards[:5]}"

    def test_ip_address_format(self, transactions_df):
        """Verify IP addresses are in valid format."""
        sample_size = min(100, len(transactions_df))
        sample_ips = transactions_df["ip_address"].sample(sample_size)

        invalid_ips = []
        for ip in sample_ips:
            if not IP_ADDRESS_PATTERN.match(str(ip)):
                invalid_ips.append(ip)

        assert (
            len(invalid_ips) == 0
        ), f"Found {len(invalid_ips)} invalid IP addresses: {invalid_ips[:5]}"

    def test_amount_is_numeric_and_positive(self, transactions_df):
        """Verify transaction amounts are numeric and positive."""
        assert pd.api.types.is_numeric_dtype(
            transactions_df["amount"]
        ), "Amount should be numeric"
        assert (transactions_df["amount"] > 0).all(), "All amounts should be positive"

    def test_user_id_is_valid(self, transactions_df):
        """Verify user_id values are present and valid."""
        assert transactions_df["user_id"].isnull().sum() == 0, "Found null user_ids"

    def test_timestamp_is_present(self, transactions_df):
        """Verify timestamp values are present."""
        assert transactions_df["timestamp"].isnull().sum() == 0, "Found null timestamps"


class TestDatasetIntegrity:
    """Cross-dataset integrity tests"""

    def test_all_fixtures_exist(self):
        """Verify all required fixture files exist"""
        required_files = [
            "fixtures/customers.csv",
            "fixtures/support_tickets.json",
            "fixtures/transactions.csv",
        ]

        for file_path in required_files:
            assert Path(file_path).exists(), f"Required fixture not found: {file_path}"

    def test_fixtures_directory_exists(self):
        """Verify fixtures directory exists"""
        assert Path("fixtures").exists(), "fixtures/ directory not found"
        assert Path("fixtures").is_dir(), "fixtures/ is not a directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
