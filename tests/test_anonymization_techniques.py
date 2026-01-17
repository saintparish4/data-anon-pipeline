"""
Unit tests for anonymization techniques.

Tests hashing, redaction, generalization, and pseudonymization.
"""

import pytest
from datetime import datetime
from src.anonymizers.techniques import (
    HashingTechnique,
    RedactionTechnique,
    GeneralizationTechnique,
    PseudonymizationTechnique,
    AnonymizationTechniques,
)


class TestHashingTechnique:
    """Test hashing-based anonymization."""

    @pytest.fixture
    def hasher(self):
        """Create hashing technique instance."""
        return HashingTechnique()

    @pytest.fixture
    def hasher_with_salt(self):
        """Create hashing technique with salt."""
        return HashingTechnique(salt="test_salt")

    def test_hash_value_consistent(self, hasher):
        """Test that same value produces same hash."""
        value = "john.doe@example.com"
        hash1 = hasher.hash_value(value)
        hash2 = hasher.hash_value(value)

        assert hash1 == hash2

    def test_hash_value_different_inputs(self, hasher):
        """Test that different values produce different hashes."""
        hash1 = hasher.hash_value("alice@example.com")
        hash2 = hasher.hash_value("bob@example.com")

        assert hash1 != hash2

    def test_hash_value_with_salt(self, hasher_with_salt):
        """Test hashing with salt."""
        value = "test@example.com"
        hash_with_salt = hasher_with_salt.hash_value(value)

        # Should be different from hash without salt
        hasher_no_salt = HashingTechnique()
        hash_no_salt = hasher_no_salt.hash_value(value)

        assert hash_with_salt != hash_no_salt

    def test_hash_value_override_salt(self, hasher_with_salt):
        """Test that per-call salt overrides instance salt."""
        value = "test@example.com"
        hash1 = hasher_with_salt.hash_value(value, salt="custom_salt")
        hash2 = hasher_with_salt.hash_value(value)  # Uses instance salt

        assert hash1 != hash2

    def test_hash_value_is_sha256(self, hasher):
        """Test that hash is SHA256 (64 hex characters)."""
        hash_value = hasher.hash_value("test")

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_hash_with_prefix(self, hasher):
        """Test hashing with prefix."""
        value = "test@example.com"
        prefixed = hasher.hash_with_prefix(value, prefix="EMAIL_")

        assert prefixed.startswith("EMAIL_")
        assert len(prefixed) == 22  # "EMAIL_" + 16 chars

    def test_hash_numeric_values(self, hasher):
        """Test hashing numeric values."""
        hash1 = hasher.hash_value(12345)
        hash2 = hasher.hash_value(12345)

        assert hash1 == hash2
        assert isinstance(hash1, str)


class TestRedactionTechnique:
    """Test redaction-based anonymization."""

    @pytest.fixture
    def redactor(self):
        """Create redaction technique instance."""
        return RedactionTechnique()

    def test_redact_full(self, redactor):
        """Test full redaction."""
        result = redactor.redact_full("John Smith")
        assert result == "[REDACTED]"

    def test_redact_full_custom_replacement(self, redactor):
        """Test full redaction with custom replacement."""
        result = redactor.redact_full("sensitive data", replacement="[REMOVED]")
        assert result == "[REMOVED]"

    def test_redact_partial_email(self, redactor):
        """Test partial email redaction."""
        result = redactor.redact_partial_email("john.doe@example.com")
        assert result == "j***@example.com"

    def test_redact_partial_email_short(self, redactor):
        """Test partial email redaction with short local part."""
        result = redactor.redact_partial_email("a@example.com")
        assert result == "a@example.com"

    def test_redact_partial_email_keep_multiple(self, redactor):
        """Test partial email redaction keeping multiple characters."""
        result = redactor.redact_partial_email("john.doe@example.com", keep_chars=4)
        assert result == "john***@example.com"

    def test_redact_partial_phone(self, redactor):
        """Test partial phone redaction."""
        result = redactor.redact_partial_phone("(555) 123-4567")
        assert result == "***-***-4567"

    def test_redact_partial_phone_different_format(self, redactor):
        """Test partial phone redaction with different format."""
        result = redactor.redact_partial_phone("555-123-4567")
        assert result == "***-***-4567"

    def test_redact_partial_ssn(self, redactor):
        """Test partial SSN redaction."""
        result = redactor.redact_partial_ssn("123-45-6789")
        assert result == "***-**-6789"

    def test_redact_partial_ssn_no_dashes(self, redactor):
        """Test SSN redaction with no dashes."""
        result = redactor.redact_partial_ssn("123456789")
        assert result == "***-**-6789"

    def test_redact_partial_credit_card(self, redactor):
        """Test partial credit card redaction."""
        result = redactor.redact_partial_credit_card("4532-1488-0343-6467")
        assert result == "****-****-****-6467"

    def test_redact_partial_credit_card_no_dashes(self, redactor):
        """Test credit card redaction without dashes."""
        result = redactor.redact_partial_credit_card("4532148803436467")
        assert result == "****-****-****-6467"

    def test_redact_partial_generic(self, redactor):
        """Test generic partial redaction."""
        result = redactor.redact_partial("HelloWorld", keep_start=2, keep_end=2)
        assert result == "He******ld"

    def test_redact_partial_generic_no_end(self, redactor):
        """Test generic partial redaction without keeping end."""
        result = redactor.redact_partial("HelloWorld", keep_start=3, keep_end=0)
        assert result == "Hel*******"

    def test_redact_partial_custom_mask(self, redactor):
        """Test generic partial redaction with custom mask character."""
        result = redactor.redact_partial(
            "test", keep_start=1, keep_end=1, mask_char="#"
        )
        assert result == "t##t"


class TestGeneralizationTechnique:
    """Test generalization-based anonymization."""

    @pytest.fixture
    def generalizer(self):
        """Create generalization technique instance."""
        return GeneralizationTechnique()

    def test_generalize_age_default(self, generalizer):
        """Test age generalization with default range."""
        result = generalizer.generalize_age(34)
        assert result == "30-39"

    def test_generalize_age_custom_range(self, generalizer):
        """Test age generalization with custom range."""
        result = generalizer.generalize_age(34, range_size=5)
        assert result == "30-34"

    def test_generalize_age_boundaries(self, generalizer):
        """Test age generalization at range boundaries."""
        assert generalizer.generalize_age(30) == "30-39"
        assert generalizer.generalize_age(39) == "30-39"
        assert generalizer.generalize_age(40) == "40-49"

    def test_generalize_age_young(self, generalizer):
        """Test age generalization for young ages."""
        assert generalizer.generalize_age(5) == "0-9"
        assert generalizer.generalize_age(0) == "0-9"

    def test_generalize_zipcode_default(self, generalizer):
        """Test zipcode generalization with default precision."""
        result = generalizer.generalize_zipcode("10001")
        assert result == "100**"

    def test_generalize_zipcode_custom_precision(self, generalizer):
        """Test zipcode generalization with custom precision."""
        result = generalizer.generalize_zipcode("10001", precision=2)
        assert result == "10***"

    def test_generalize_zipcode_with_dash(self, generalizer):
        """Test zipcode generalization with extended format."""
        result = generalizer.generalize_zipcode("10001-1234", precision=3)
        assert "100" in result

    def test_generalize_date_to_quarter(self, generalizer):
        """Test date generalization to quarter."""
        assert generalizer.generalize_date_to_quarter("2024-03-15") == "2024-Q1"
        assert generalizer.generalize_date_to_quarter("2024-06-20") == "2024-Q2"
        assert generalizer.generalize_date_to_quarter("2024-09-10") == "2024-Q3"
        assert generalizer.generalize_date_to_quarter("2024-12-25") == "2024-Q4"

    def test_generalize_date_to_quarter_datetime(self, generalizer):
        """Test date generalization with datetime object."""
        date_obj = datetime(2024, 3, 15)
        result = generalizer.generalize_date_to_quarter(date_obj)
        assert result == "2024-Q1"

    def test_generalize_date_to_quarter_different_formats(self, generalizer):
        """Test date generalization with different date formats."""
        assert generalizer.generalize_date_to_quarter("03/15/2024") == "2024-Q1"
        assert generalizer.generalize_date_to_quarter("15/03/2024") == "2024-Q1"

    def test_generalize_date_to_month(self, generalizer):
        """Test date generalization to month."""
        result = generalizer.generalize_date_to_month("2024-03-15")
        assert result == "2024-03"

    def test_generalize_date_to_year(self, generalizer):
        """Test date generalization to year."""
        result = generalizer.generalize_date_to_year("2024-03-15")
        assert result == "2024"

    def test_generalize_income(self, generalizer):
        """Test income generalization."""
        result = generalizer.generalize_income(75000)
        assert result == "$70,000-$79,999"

    def test_generalize_income_custom_bracket(self, generalizer):
        """Test income generalization with custom bracket size."""
        result = generalizer.generalize_income(75000, bracket_size=25000)
        assert result == "$75,000-$99,999"

    def test_generalize_income_high(self, generalizer):
        """Test income generalization for high income."""
        result = generalizer.generalize_income(125000)
        assert result == "$120,000-$129,999"

    def test_generalize_numeric_range(self, generalizer):
        """Test generic numeric range generalization."""
        result = generalizer.generalize_numeric_range(45.5, range_size=10)
        assert result == "40.0-50.0"


class TestPseudonymizationTechnique:
    """Test pseudonymization-based anonymization."""

    @pytest.fixture
    def pseudonymizer(self):
        """Create pseudonymization technique instance."""
        return PseudonymizationTechnique()

    def test_pseudonymize_name_consistency(self, pseudonymizer):
        """Test that same name produces same fake name."""
        name1 = pseudonymizer.pseudonymize_name("John Smith")
        name2 = pseudonymizer.pseudonymize_name("John Smith")

        assert name1 == name2

    def test_pseudonymize_name_different(self, pseudonymizer):
        """Test that different names produce different fake names."""
        name1 = pseudonymizer.pseudonymize_name("John Smith")
        name2 = pseudonymizer.pseudonymize_name("Jane Doe")

        assert name1 != name2

    def test_pseudonymize_name_is_realistic(self, pseudonymizer):
        """Test that fake name looks realistic."""
        fake_name = pseudonymizer.pseudonymize_name("Original Name")

        # Should have at least first and last name
        assert len(fake_name.split()) >= 2

    def test_pseudonymize_email_consistency(self, pseudonymizer):
        """Test email pseudonymization consistency."""
        email1 = pseudonymizer.pseudonymize_email("john@example.com")
        email2 = pseudonymizer.pseudonymize_email("john@example.com")

        assert email1 == email2

    def test_pseudonymize_email_format(self, pseudonymizer):
        """Test that fake email has valid format."""
        fake_email = pseudonymizer.pseudonymize_email("original@example.com")

        assert "@" in fake_email
        assert "." in fake_email

    def test_pseudonymize_phone_consistency(self, pseudonymizer):
        """Test phone pseudonymization consistency."""
        phone1 = pseudonymizer.pseudonymize_phone("555-123-4567")
        phone2 = pseudonymizer.pseudonymize_phone("555-123-4567")

        assert phone1 == phone2

    def test_pseudonymize_address_consistency(self, pseudonymizer):
        """Test address pseudonymization consistency."""
        address1 = pseudonymizer.pseudonymize_address("123 Main St")
        address2 = pseudonymizer.pseudonymize_address("123 Main St")

        assert address1 == address2

    def test_pseudonymize_company_consistency(self, pseudonymizer):
        """Test company pseudonymization consistency."""
        company1 = pseudonymizer.pseudonymize_company("Acme Corp")
        company2 = pseudonymizer.pseudonymize_company("Acme Corp")

        assert company1 == company2

    def test_pseudonymize_city_consistency(self, pseudonymizer):
        """Test city pseudonymization consistency."""
        city1 = pseudonymizer.pseudonymize_city("New York")
        city2 = pseudonymizer.pseudonymize_city("New York")

        assert city1 == city2

    def test_pseudonymize_generic_name(self, pseudonymizer):
        """Test generic pseudonymization with name type."""
        result = pseudonymizer.pseudonymize_generic("Test", fake_type="name")
        assert len(result) > 0

    def test_pseudonymize_generic_email(self, pseudonymizer):
        """Test generic pseudonymization with email type."""
        result = pseudonymizer.pseudonymize_generic("Test", fake_type="email")
        assert "@" in result

    def test_get_seed_consistency(self, pseudonymizer):
        """Test that seed generation is consistent."""
        seed1 = pseudonymizer._get_seed("test value")
        seed2 = pseudonymizer._get_seed("test value")

        assert seed1 == seed2


class TestAnonymizationTechniques:
    """Test unified anonymization interface."""

    @pytest.fixture
    def anonymizer(self):
        """Create anonymization techniques instance."""
        return AnonymizationTechniques()

    def test_unified_interface_has_all_techniques(self, anonymizer):
        """Test that unified interface provides all techniques."""
        assert hasattr(anonymizer, "hashing")
        assert hasattr(anonymizer, "redaction")
        assert hasattr(anonymizer, "generalization")
        assert hasattr(anonymizer, "pseudonymization")

    def test_convenience_method_hash(self, anonymizer):
        """Test convenience method for hashing."""
        result = anonymizer.hash_value("test@example.com")
        assert len(result) == 64

    def test_convenience_method_redact(self, anonymizer):
        """Test convenience method for redaction."""
        result = anonymizer.redact_full("sensitive")
        assert result == "[REDACTED]"

    def test_convenience_method_generalize_age(self, anonymizer):
        """Test convenience method for age generalization."""
        result = anonymizer.generalize_age(25)
        assert result == "20-29"

    def test_convenience_method_pseudonymize(self, anonymizer):
        """Test convenience method for pseudonymization."""
        result = anonymizer.pseudonymize_name("John Smith")
        assert len(result) > 0
        assert result != "John Smith"

    def test_with_custom_salt(self):
        """Test unified interface with custom salt."""
        anonymizer = AnonymizationTechniques(salt="custom_salt")
        hash1 = anonymizer.hash_value("test")

        anonymizer2 = AnonymizationTechniques(salt="different_salt")
        hash2 = anonymizer2.hash_value("test")

        assert hash1 != hash2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_hashing(self):
        """Test hashing empty string."""
        hasher = HashingTechnique()
        result = hasher.hash_value("")
        assert len(result) == 64

    def test_none_value_handling(self):
        """Test handling None values."""
        hasher = HashingTechnique()
        result = hasher.hash_value(None)
        assert len(result) == 64

    def test_very_long_string(self):
        """Test hashing very long string."""
        hasher = HashingTechnique()
        long_string = "x" * 10000
        result = hasher.hash_value(long_string)
        assert len(result) == 64

    def test_unicode_characters(self):
        """Test handling unicode characters."""
        hasher = HashingTechnique()
        unicode_text = "Hello 世界 🌍"
        result = hasher.hash_value(unicode_text)
        assert len(result) == 64

    def test_invalid_date_format(self):
        """Test generalization with invalid date format."""
        generalizer = GeneralizationTechnique()
        result = generalizer.generalize_date_to_quarter("invalid-date")
        assert result == "invalid-date"  # Should return original

    def test_short_zipcode(self):
        """Test zipcode generalization with too-short zipcode."""
        generalizer = GeneralizationTechnique()
        result = generalizer.generalize_zipcode("12", precision=3)
        assert result == "12"  # Should return original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
