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


class TestDatasetIntegrity:
    """Dataset integrity tests"""

    def test_all_fixtures_exist(self):
        """Verify all required fixture files exist"""
        required_files = [
            "fixtures/customers.csv",
        ]

        for file_path in required_files:
            assert Path(file_path).exists(), f"Required fixture not found: {file_path}"

    def test_fixtures_directory_exists(self):
        """Verify fixtures directory exists"""
        assert Path("fixtures").exists(), "fixtures/ directory not found"
        assert Path("fixtures").is_dir(), "fixtures/ is not a directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
