"""
Unit tests for regex_detector.py

Tests email, phone, SSN, and credit card detection.
"""

import pytest
from src.detectors.regex_detector import RegexDetector, PIIMatch


class TestEmailDetection:
    """Test email detection functionality."""

    @pytest.fixture
    def detector(self):
        return RegexDetector()

    def test_detect_simple_email(self, detector):
        """Test detection of simple email address."""
        text = "Contact me at john.doe@example.com"
        matches = detector.detect_emails(text)

        assert len(matches) == 1
        assert matches[0].pii_type == "email"
        assert matches[0].value == "john.doe@example.com"
        assert matches[0].confidence > 0.9

    def test_detect_multiple_emails(self, detector):
        """Test detection of multiple email addresses."""
        text = "Email alice@test.com or bob@company.org for help"
        matches = detector.detect_emails(text)

        assert len(matches) == 2
        assert matches[0].value == "alice@test.com"
        assert matches[1].value == "bob@company.org"

    def test_detect_email_with_special_chars(self, detector):
        """Test detection of emails with special characters."""
        text = "Contact: user+tag@sub-domain.example.co.uk"
        matches = detector.detect_emails(text)

        assert len(matches) == 1
        assert "user+tag@sub-domain.example.co.uk" in matches[0].value

    def test_no_email_in_text(self, detector):
        """Test that no false positives occur."""
        text = "This text has no email addresses"
        matches = detector.detect_emails(text)

        assert len(matches) == 0


class TestPhoneDetection:
    """Test phone number detection functionality."""

    @pytest.fixture
    def detector(self):
        return RegexDetector()

    def test_detect_us_phone_with_dashes(self, detector):
        """Test detection of US phone with dashes."""
        text = "Call me at 555-123-4567"
        matches = detector.detect_phones(text)

        assert len(matches) == 1
        assert matches[0].pii_type == "phone"
        assert "555-123-4567" in matches[0].value

    def test_detect_us_phone_with_parentheses(self, detector):
        """Test detection of US phone with parentheses."""
        text = "Phone: (555) 123-4567"
        matches = detector.detect_phones(text)

        assert len(matches) == 1
        assert "(555) 123-4567" in matches[0].value

    def test_detect_us_phone_with_dots(self, detector):
        """Test detection of US phone with dots."""
        text = "Contact: 555.123.4567"
        matches = detector.detect_phones(text)

        assert len(matches) == 1
        assert "555.123.4567" in matches[0].value

    def test_detect_international_phone(self, detector):
        """Test detection of international phone numbers."""
        text = "International: +1-555-123-4567"
        matches = detector.detect_phones(text)

        assert len(matches) >= 1
        # Should detect the international format
        assert any("+1" in match.value for match in matches)

    def test_detect_multiple_phones(self, detector):
        """Test detection of multiple phone numbers."""
        text = "Call 555-123-4567 or 555-987-6543"
        matches = detector.detect_phones(text)

        assert len(matches) >= 2

    def test_no_phone_in_text(self, detector):
        """Test that no false positives occur."""
        text = "This text has no phone numbers"
        matches = detector.detect_phones(text)

        assert len(matches) == 0


class TestSSNDetection:
    """Test SSN detection functionality."""

    @pytest.fixture
    def detector(self):
        return RegexDetector()

    def test_detect_valid_ssn(self, detector):
        """Test detection of valid SSN."""
        text = "SSN: 123-45-6789"
        matches = detector.detect_ssns(text)

        assert len(matches) == 1
        assert matches[0].pii_type == "ssn"
        assert matches[0].value == "123-45-6789"

    def test_reject_invalid_ssn_all_zeros(self, detector):
        """Test rejection of SSN with all zeros in area."""
        text = "Invalid: 000-45-6789"
        matches = detector.detect_ssns(text)

        assert len(matches) == 0

    def test_reject_invalid_ssn_666(self, detector):
        """Test rejection of SSN with 666 area."""
        text = "Invalid: 666-45-6789"
        matches = detector.detect_ssns(text)

        assert len(matches) == 0

    def test_reject_invalid_ssn_900_range(self, detector):
        """Test rejection of SSN in 900-999 range."""
        text = "Invalid: 900-45-6789"
        matches = detector.detect_ssns(text)

        assert len(matches) == 0

    def test_reject_invalid_ssn_zero_group(self, detector):
        """Test rejection of SSN with zero group."""
        text = "Invalid: 123-00-6789"
        matches = detector.detect_ssns(text)

        assert len(matches) == 0

    def test_reject_invalid_ssn_zero_serial(self, detector):
        """Test rejection of SSN with zero serial."""
        text = "Invalid: 123-45-0000"
        matches = detector.detect_ssns(text)

        assert len(matches) == 0

    def test_detect_multiple_valid_ssns(self, detector):
        """Test detection of multiple valid SSNs."""
        text = "SSNs: 123-45-6789 and 234-56-7890"
        matches = detector.detect_ssns(text)

        assert len(matches) == 2


class TestCreditCardDetection:
    """Test credit card detection functionality."""

    @pytest.fixture
    def detector(self):
        return RegexDetector()

    def test_detect_valid_credit_card(self, detector):
        """Test detection of valid credit card (with Luhn check)."""
        # Valid test card number (passes Luhn) - Visa test card
        text = "Card: 4532-0151-1283-0366"
        matches = detector.detect_credit_cards(text)

        assert len(matches) == 1
        assert matches[0].pii_type == "credit_card"
        assert "4532" in matches[0].value

    def test_detect_credit_card_no_separators(self, detector):
        """Test detection of credit card without separators."""
        text = "Card: 4532015112830366"
        matches = detector.detect_credit_cards(text)

        assert len(matches) == 1

    def test_detect_credit_card_space_separators(self, detector):
        """Test detection of credit card with space separators."""
        text = "Card: 4532 0151 1283 0366"
        matches = detector.detect_credit_cards(text)

        assert len(matches) == 1

    def test_reject_invalid_luhn_checksum(self, detector):
        """Test rejection of card with invalid Luhn checksum."""
        text = "Invalid card: 1234-5678-9012-3456"
        matches = detector.detect_credit_cards(text)

        # Should not detect because Luhn check fails
        assert len(matches) == 0

    def test_luhn_algorithm_validation(self, detector):
        """Test Luhn algorithm directly."""
        # Valid card numbers (these pass Luhn)
        assert detector._validate_luhn("4532015112830366") == True  # Visa test card
        assert detector._validate_luhn("4111111111111111") == True  # Visa test card
        assert (
            detector._validate_luhn("5425233430109903") == True
        )  # Mastercard test card

        # Invalid card numbers (these fail Luhn)
        assert detector._validate_luhn("1234567890123456") == False
        assert detector._validate_luhn("0000000000000000") == False


class TestDetectAll:
    """Test combined detection of all PII types."""

    @pytest.fixture
    def detector(self):
        return RegexDetector()

    def test_detect_mixed_pii_types(self, detector):
        """Test detection of multiple PII types in one text."""
        text = """
        Contact Information:
        Email: john.doe@example.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        """
        matches = detector.detect_all(text)

        # Should detect email, phone, and SSN
        assert len(matches) >= 3

        pii_types = [m.pii_type for m in matches]
        assert "email" in pii_types
        assert "phone" in pii_types
        assert "ssn" in pii_types

    def test_detect_all_returns_sorted_by_position(self, detector):
        """Test that results are sorted by position in text."""
        text = "Phone: 555-123-4567 Email: test@example.com"
        matches = detector.detect_all(text)

        # Phone should come before email based on position
        assert matches[0].pii_type == "phone"
        assert matches[1].pii_type == "email"

    def test_detect_in_value_simple(self, detector):
        """Test simplified detect_in_value interface."""
        value = "john.doe@example.com"
        pii_types = detector.detect_in_value(value)

        assert "email" in pii_types

    def test_detect_in_value_multiple_types(self, detector):
        """Test detect_in_value with multiple PII types."""
        value = "Contact john.doe@example.com or 555-123-4567"
        pii_types = detector.detect_in_value(value)

        assert "email" in pii_types
        assert "phone" in pii_types

    def test_detect_in_value_no_pii(self, detector):
        """Test detect_in_value with no PII."""
        value = "Just regular text"
        pii_types = detector.detect_in_value(value)

        assert len(pii_types) == 0

    def test_detect_in_value_handles_non_string(self, detector):
        """Test that detect_in_value handles non-string input."""
        value = 12345
        pii_types = detector.detect_in_value(value)

        # Should convert to string and detect (no PII in this case)
        assert isinstance(pii_types, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
