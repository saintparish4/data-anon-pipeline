"""
Regex-based PII detector.

Detects various PII types using regular expressions:
- Email addresses
- Phone numbers (US and international formats)
- Social Security Numbers (with format validation)
- Credit card numbers (with Luhn algorithm validation)
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """Represents a detected PII match."""

    pii_type: str
    value: str
    start: int
    end: int
    confidence: float


class RegexDetector:
    """Detects PII using regular expression patterns."""

    # Regex patterns
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    # Phone patterns
    PHONE_US_PATTERN = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    PHONE_INTL_PATTERN = re.compile(
        r"\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
    )

    # SSN pattern
    SSN_PATTERN = re.compile(r"\d{3}-\d{2}-\d{4}")

    # Credit card patterns (with or without separators)
    CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")

    def __init__(self):
        """Initialize the regex detector."""
        pass

    def detect_emails(self, text: str) -> List[PIIMatch]:
        """
        Detect email addresses in text.

        Args:
            text: Input text to scan

        Returns:
            List of PIIMatch objects for detected emails
        """
        matches = []
        for match in self.EMAIL_PATTERN.finditer(text):
            matches.append(
                PIIMatch(
                    pii_type="email",
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,  # High confidence for email pattern
                )
            )
        return matches

    def detect_phones(self, text: str) -> List[PIIMatch]:
        """
        Detect phone numbers in text (US and international formats).

        Args:
            text: Input text to scan

        Returns:
            List of PIIMatch objects for detected phone numbers
        """
        matches = []

        # Check for international format first (more specific)
        for match in self.PHONE_INTL_PATTERN.finditer(text):
            matches.append(
                PIIMatch(
                    pii_type="phone",
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.90,
                )
            )

        # Check for US format
        # Avoid double-detecting numbers already found as international
        existing_ranges = [(m.start, m.end) for m in matches]

        for match in self.PHONE_US_PATTERN.finditer(text):
            # Check if this overlaps with existing matches
            overlaps = any(
                match.start() < end and match.end() > start
                for start, end in existing_ranges
            )
            if not overlaps:
                matches.append(
                    PIIMatch(
                        pii_type="phone",
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=0.85,
                    )
                )

        return matches

    def detect_ssns(self, text: str) -> List[PIIMatch]:
        """
        Detect Social Security Numbers in text with format validation.

        Args:
            text: Input text to scan

        Returns:
            List of PIIMatch objects for detected SSNs
        """
        matches = []
        for match in self.SSN_PATTERN.finditer(text):
            ssn = match.group()
            if self._validate_ssn_format(ssn):
                matches.append(
                    PIIMatch(
                        pii_type="ssn",
                        value=ssn,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.90,
                    )
                )
        return matches

    def _validate_ssn_format(self, ssn: str) -> bool:
        """
        Validate SSN format (basic validation).

        SSNs should not be:
        - All zeros in any segment
        - 666 in first segment
        - 900-999 in first segment

        Args:
            ssn: SSN string in format XXX-XX-XXXX

        Returns:
            True if valid format, False otherwise
        """
        parts = ssn.split("-")
        if len(parts) != 3:
            return False

        area, group, serial = parts

        # Invalid area numbers
        if area == "000" or area == "666" or area.startswith("9"):
            return False

        # Invalid group/serial
        if group == "00" or serial == "0000":
            return False

        return True

    def detect_credit_cards(self, text: str) -> List[PIIMatch]:
        """
        Detect credit card numbers with Luhn algorithm validation.

        Args:
            text: Input text to scan

        Returns:
            List of PIIMatch objects for detected credit cards
        """
        matches = []
        for match in self.CREDIT_CARD_PATTERN.finditer(text):
            card_number = match.group()
            # Remove separators for validation
            digits_only = re.sub(r"[-\s]", "", card_number)

            if len(digits_only) == 16 and self._validate_luhn(digits_only):
                matches.append(
                    PIIMatch(
                        pii_type="credit_card",
                        value=card_number,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.95,
                    )
                )
        return matches

    def _validate_luhn(self, card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.

        Args:
            card_number: Card number as string (digits only)

        Returns:
            True if valid according to Luhn algorithm, False otherwise
        """
        # Reject all zeros or other obviously invalid patterns
        if not card_number or card_number == "0" * len(card_number):
            return False

        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]

            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]

            checksum = sum(odd_digits)
            for digit in even_digits:
                checksum += sum(digits_of(digit * 2))

            return checksum % 10

        try:
            return luhn_checksum(card_number) == 0
        except (ValueError, TypeError):
            return False

    def detect_all(self, text: str) -> List[PIIMatch]:
        """
        Detect all PII types in text.

        Args:
            text: Input text to scan

        Returns:
            List of all PIIMatch objects found
        """
        all_matches = []
        all_matches.extend(self.detect_emails(text))
        all_matches.extend(self.detect_phones(text))
        all_matches.extend(self.detect_ssns(text))
        all_matches.extend(self.detect_credit_cards(text))

        # Sort by start position
        all_matches.sort(key=lambda m: m.start)

        return all_matches

    def detect_in_value(self, value: str) -> List[str]:
        """
        Detect PII types in a single value (simplified interface).

        Args:
            value: String value to check

        Returns:
            List of PII type names detected
        """
        if not isinstance(value, str):
            value = str(value)

        matches = self.detect_all(value)
        return list(set(match.pii_type for match in matches))
