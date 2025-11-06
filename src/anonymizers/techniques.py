"""
Anonymization Technique Module

Implements various anonymization strategies:
- Hashing (SHA256 with optional salt)
- Redaction (full and partial)
- Generalization (age ranges, zip codes, dates)
- Pseudonymization (consistent fake data) 
"""

import hashlib
import re
from datetime import datetime
from typing import Any, Optional, Union
from faker import Faker

class HashingTechnique:
    """Implements hashing-based anonymization using SHA256"""

    def __init__(self, salt: Optional[str] = None):
        """
        Initialize hashing technique

        Args:
            salt: Optional salt for hashing (improves security)
        """
        self.salt = salt

    def hash_value(self, value: Any, salt: Optional[str] = None) -> str:
        """
        Hash a value using SHA256

        Args:
            value: Value to hash
            salt: Optional salt (overrides instance salt)

        Returns:
            Hexadecimal hash string
        """
        # Use provided salt or instance salt
        effective_salt = salt if salt is not None else self.salt

        # Convert value to string
        str_value = str(value)

        # Add salt if provided
        if effective_salt:
                str_value = f"{effective_salt}:{str_value}"
        
        #Compute SHA256 hash
        hash_obj = hashlib.sha256(str_value.encode('utf-8'))
        return hash_obj.hexdigest()

    def hash_with_prefix(self, value: Any, prefix: str = "HASH_", salt: Optional[str] = None) -> str:
        """
        Hash value and add a readable prefix

        Useful for maintaining some context about the original data type

        Args:
            value: Value to hash
            prefix: Prefix to add (default: "HASH_")
            salt: Optional salt 

        Returns:
            Prefixed hash string
        """
        hash_value = self.hash_value(value, salt)
        return f"{prefix}{hash_value[:16]}" # Use first 16 chars for readability

class RedactionTechnique:
    """Implements redaction-based anonymization"""

    @staticmethod
    def redact_full(value: Any, replacement: str = "[REDACTED]") -> str:
        """ 
        Fully refact a value

        Args:
            value: Value to redact
            replacement: Replacement string

        Returns:
            Redacted string
        """
        return replacement 

    @staticmethod
    def redact_partial_email(email: str, keep_chars: int = 1) -> str:
        """
        Partially redact an email address

        Example: john.doe@example.com -> j***@example.com

        Args:
            email: Email address to redact
            keep_chars: Number of characters to keep at start

        Returns:
            Partially redacted email
        """
        if '@' not in email:
            return email
        
        local, domain = email.split('@', 1)

        if len(local) <= keep_chars:
            redacted_local = local
        else:
            redacted_local = local[:keep_chars] + '***' 

        return f"{redacted_local}@{domain}"

    @staticmethod
    def redact_partial_phone(phone: str, keep_last: int = 4) -> str:
        """
        Partially redact a phone number

        Example: 123-456-7890 -> ****-****-7890

        Args:
            phone: Phone number to redact
            keep_last: Number of characters to keep at end

        Returns:
            Partially redacted phone number
        """

        # Extract only digits
        digits = re.sub(r'\D', '', phone)

        if len(digits) <= keep_last:
            return phone 

        # Redacted all but last N digits
        redacted = '*' * (len(digits) - keep_last) + digits[-keep_last:]

        # Format as xxx-xxx-xxxx
        if len(redacted) == 10:
            return f"***-***-{redacted[-4:]}"
        else:
            return redacted 

    @staticmethod
    def redact_partial_ssn(ssn: str) -> str:
        """ 
        Partially redact SSN (keep last 4 digits)

        Example: 123-45-6789 -> ***-**-6789

        Args:
            ssn: SSN to redact

        Returns:
            Partially redacted SSN
        """
        # Extract only digits
        digits = re.sub(r'\D', '', ssn)

        if len(digits) != 9:
            return ssn

        return f"***-**-{digits[-4:]}"

    @staticmethod
    def redact_partial_credit_card(card: str) -> str:
        """
        Partially redact credit card (keep last 4 digits)

        Example: 4532-1488-0343-6467 -> ****-****-****-6467

        Args:
            card: Credit card number to redact

        Returns:
            Partially redacted card numner 
        """
        # Extract only digits
        digits = re.sub(r'\D', '', card)

        if len(digits) != 16:
            return card 

        return f"****-****-****-{digits[-4:]}"

    @staticmethod
    def redact_partial(value: str, keep_start: int = 1, keep_end: int = 0, mask_char: str = '*') -> str:
        """
        Generic partial redaction

        Args:
            value: Value to redact
            keep_start: Characters to keep at start
            keep_end: Characterrs to keep at end
            mask_char: Character to use for masking

        Returns:
            Partially redacted string
        """
        str_value = str(value)
        length = len(str_value)

        if length <= (keep_start + keep_end):
            return str_value

        start = str_value[:keep_start] if keep_start > 0 else ''
        end = str_value[-keep_end:] if keep_end > 0 else ''
        middle = mask_char * (length - keep_start - keep_end)

        return f"{start}{middle}{end}"

        
