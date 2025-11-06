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

class GeneralizationTechnique:
    """Implements generalization-based anonymization."""
    
    @staticmethod
    def generalize_age(age: int, range_size: int = 10) -> str:
        """
        Generalize age into ranges.
        
        Example: 34 → "30-39"
        
        Args:
            age: Age to generalize
            range_size: Size of age range (default: 10 years)
            
        Returns:
            Age range as string
        """
        lower_bound = (age // range_size) * range_size
        upper_bound = lower_bound + range_size - 1
        return f"{lower_bound}-{upper_bound}"
    
    @staticmethod
    def generalize_zipcode(zipcode: str, precision: int = 3) -> str:
        """
        Generalize zipcode by masking last digits.
        
        Example: "10001" → "100**"
        
        Args:
            zipcode: Zipcode to generalize
            precision: Number of digits to keep (default: 3)
            
        Returns:
            Generalized zipcode
        """
        str_zip = str(zipcode)
        
        # Remove any non-digits
        digits_only = re.sub(r'\D', '', str_zip)
        
        if len(digits_only) < precision:
            return str_zip
        
        return digits_only[:precision] + '*' * (len(digits_only) - precision)
    
    @staticmethod
    def generalize_date_to_quarter(date: Union[str, datetime]) -> str:
        """
        Generalize date to quarter.
        
        Example: "2024-03-15" → "2024-Q1"
        
        Args:
            date: Date to generalize (string or datetime)
            
        Returns:
            Quarter string (YYYY-QN)
        """
        if isinstance(date, str):
            # Try to parse date string
            try:
                date_obj = datetime.fromisoformat(date.split()[0])  # Handle datetime strings
            except ValueError:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date  # Return original if can't parse
        else:
            date_obj = date
        
        # Determine quarter
        quarter = (date_obj.month - 1) // 3 + 1
        return f"{date_obj.year}-Q{quarter}"
    
    @staticmethod
    def generalize_date_to_month(date: Union[str, datetime]) -> str:
        """
        Generalize date to year-month.
        
        Example: "2024-03-15" → "2024-03"
        
        Args:
            date: Date to generalize
            
        Returns:
            Year-month string (YYYY-MM)
        """
        if isinstance(date, str):
            try:
                date_obj = datetime.fromisoformat(date.split()[0])
            except ValueError:
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date
        else:
            date_obj = date
        
        return f"{date_obj.year}-{date_obj.month:02d}"
    
    @staticmethod
    def generalize_date_to_year(date: Union[str, datetime]) -> str:
        """
        Generalize date to year only.
        
        Example: "2024-03-15" → "2024"
        
        Args:
            date: Date to generalize
            
        Returns:
            Year string
        """
        if isinstance(date, str):
            try:
                date_obj = datetime.fromisoformat(date.split()[0])
            except ValueError:
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date
        else:
            date_obj = date
        
        return str(date_obj.year)
    
    @staticmethod
    def generalize_income(income: float, bracket_size: int = 10000) -> str:
        """
        Generalize income into brackets.
        
        Example: 75000 → "$70,000-$79,999"
        
        Args:
            income: Income to generalize
            bracket_size: Size of income bracket
            
        Returns:
            Income bracket as string
        """
        lower_bound = (int(income) // bracket_size) * bracket_size
        upper_bound = lower_bound + bracket_size - 1
        return f"${lower_bound:,}-${upper_bound:,}"
    
    @staticmethod
    def generalize_numeric_range(value: float, range_size: float) -> str:
        """
        Generic numeric range generalization.
        
        Args:
            value: Numeric value to generalize
            range_size: Size of range
            
        Returns:
            Range as string
        """
        lower_bound = (value // range_size) * range_size
        upper_bound = lower_bound + range_size
        return f"{lower_bound}-{upper_bound}"


class PseudonymizationTechnique:
    """Implements pseudonymization with consistent fake data."""
    
    def __init__(self):
        """Initialize pseudonymization technique."""
        self._faker_cache = {}  # Cache Faker instances by seed
    
    def _get_faker(self, seed: int) -> Faker:
        """
        Get or create a Faker instance with specific seed.
        
        Args:
            seed: Seed for Faker
            
        Returns:
            Faker instance
        """
        if seed not in self._faker_cache:
            faker = Faker()
            Faker.seed(seed)
            self._faker_cache[seed] = faker
        return self._faker_cache[seed]
    
    def _get_seed(self, value: Any) -> int:
        """
        Generate consistent seed from value.
        
        Args:
            value: Value to generate seed from
            
        Returns:
            Integer seed
        """
        # Use hash of value as seed for consistency
        hash_value = hashlib.md5(str(value).encode('utf-8')).hexdigest()
        return int(hash_value[:8], 16)  # Use first 8 hex chars as seed
    
    def pseudonymize_name(self, name: str) -> str:
        """
        Generate consistent fake name.
        
        Same input always produces same output.
        
        Args:
            name: Original name
            
        Returns:
            Fake name
        """
        seed = self._get_seed(name)
        faker = Faker()
        Faker.seed(seed)
        return faker.name()
    
    def pseudonymize_email(self, email: str) -> str:
        """
        Generate consistent fake email.
        
        Args:
            email: Original email
            
        Returns:
            Fake email
        """
        seed = self._get_seed(email)
        faker = Faker()
        Faker.seed(seed)
        return faker.email()
    
    def pseudonymize_phone(self, phone: str) -> str:
        """
        Generate consistent fake phone number.
        
        Args:
            phone: Original phone
            
        Returns:
            Fake phone number
        """
        seed = self._get_seed(phone)
        faker = Faker()
        Faker.seed(seed)
        return faker.phone_number()
    
    def pseudonymize_address(self, address: str) -> str:
        """
        Generate consistent fake address.
        
        Args:
            address: Original address
            
        Returns:
            Fake address
        """
        seed = self._get_seed(address)
        faker = Faker()
        Faker.seed(seed)
        return faker.address().replace('\n', ', ')
    
    def pseudonymize_company(self, company: str) -> str:
        """
        Generate consistent fake company name.
        
        Args:
            company: Original company name
            
        Returns:
            Fake company name
        """
        seed = self._get_seed(company)
        faker = Faker()
        Faker.seed(seed)
        return faker.company()
    
    def pseudonymize_city(self, city: str) -> str:
        """
        Generate consistent fake city name.
        
        Args:
            city: Original city
            
        Returns:
            Fake city name
        """
        seed = self._get_seed(city)
        faker = Faker()
        Faker.seed(seed)
        return faker.city()
    
    def pseudonymize_generic(self, value: Any, fake_type: str = 'name') -> str:
        """
        Generic pseudonymization with specified type.
        
        Args:
            value: Original value
            fake_type: Type of fake data to generate
                      ('name', 'email', 'phone', 'address', 'company', 'city')
            
        Returns:
            Fake data
        """
        method_map = {
            'name': self.pseudonymize_name,
            'email': self.pseudonymize_email,
            'phone': self.pseudonymize_phone,
            'address': self.pseudonymize_address,
            'company': self.pseudonymize_company,
            'city': self.pseudonymize_city
        }
        
        method = method_map.get(fake_type, self.pseudonymize_name)
        return method(str(value))


class AnonymizationTechniques:
    """
    Unified interface for all anonymization techniques.
    
    Provides easy access to all anonymization methods.
    """
    
    def __init__(self, salt: Optional[str] = None):
        """
        Initialize anonymization techniques.
        
        Args:
            salt: Optional salt for hashing
        """
        self.hashing = HashingTechnique(salt)
        self.redaction = RedactionTechnique()
        self.generalization = GeneralizationTechnique()
        self.pseudonymization = PseudonymizationTechnique()
    
    # Convenience methods that delegate to specific techniques
    
    def hash_value(self, value: Any, salt: Optional[str] = None) -> str:
        """Hash a value using SHA256."""
        return self.hashing.hash_value(value, salt)
    
    def redact_full(self, value: Any) -> str:
        """Fully redact a value."""
        return self.redaction.redact_full(value)
    
    def redact_partial_email(self, email: str) -> str:
        """Partially redact an email."""
        return self.redaction.redact_partial_email(email)
    
    def generalize_age(self, age: int, range_size: int = 10) -> str:
        """Generalize age into ranges."""
        return self.generalization.generalize_age(age, range_size)
    
    def generalize_zipcode(self, zipcode: str, precision: int = 3) -> str:
        """Generalize zipcode."""
        return self.generalization.generalize_zipcode(zipcode, precision)
    
    def generalize_date_to_quarter(self, date: Union[str, datetime]) -> str:
        """Generalize date to quarter."""
        return self.generalization.generalize_date_to_quarter(date)
    
    def pseudonymize_name(self, name: str) -> str:
        """Generate consistent fake name."""
        return self.pseudonymization.pseudonymize_name(name)
    
    def pseudonymize_email(self, email: str) -> str:
        """Generate consistent fake email."""
        return self.pseudonymization.pseudonymize_email(email)     
  