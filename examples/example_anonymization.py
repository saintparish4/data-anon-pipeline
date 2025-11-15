"""
Anonymization Techniques Examples.

Demonstrates all anonymization techniques with real-world scenarios.
"""

from src.anonymizers.techniques import AnonymizationTechniques
from datetime import datetime
import pandas as pd


def example_hashing():
    """Example 1: Hashing technique."""
    print("=" * 70)
    print("EXAMPLE 1: Hashing Technique")
    print("=" * 70)
    
    anonymizer = AnonymizationTechniques()
    
    # Hash emails
    emails = ["john.doe@example.com", "jane.smith@company.org", "alice@email.com"]
    
    print("\nOriginal Emails → Hashed:")
    for email in emails:
        hashed = anonymizer.hash_value(email)
        print(f"  {email:30s} → {hashed[:20]}...")
    
    # Hash with salt for added security
    print("\nWith Salt (more secure):")
    anonymizer_salted = AnonymizationTechniques(salt="my_secret_salt")
    for email in emails:
        hashed = anonymizer_salted.hash_value(email)
        print(f"  {email:30s} → {hashed[:20]}...")
    
    # Show consistency
    print("\nConsistency Check:")
    email = "test@example.com"
    hash1 = anonymizer.hash_value(email)
    hash2 = anonymizer.hash_value(email)
    print(f"  Hash 1: {hash1[:20]}...")
    print(f"  Hash 2: {hash2[:20]}...")
    print(f"  Consistent: {hash1 == hash2}")


def example_redaction():
    """Example 2: Redaction techniques."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Redaction Techniques")
    print("=" * 70)
    
    anonymizer = AnonymizationTechniques()
    
    # Full redaction
    print("\nFull Redaction:")
    sensitive_data = ["John Smith", "123-45-6789", "Secret Project X"]
    for data in sensitive_data:
        redacted = anonymizer.redact_full(data)
        print(f"  {data:30s} → {redacted}")
    
    # Partial redaction for different PII types
    print("\nPartial Redaction:")
    
    # Emails
    print("\n  Emails:")
    emails = ["john.doe@example.com", "alice@company.org", "bob.jones@email.co.uk"]
    for email in emails:
        redacted = anonymizer.redaction.redact_partial_email(email)
        print(f"    {email:30s} → {redacted}")
    
    # Phone numbers
    print("\n  Phone Numbers:")
    phones = ["(555) 123-4567", "555-987-6543", "5551234567"]
    for phone in phones:
        redacted = anonymizer.redaction.redact_partial_phone(phone)
        print(f"    {phone:30s} → {redacted}")
    
    # SSNs
    print("\n  Social Security Numbers:")
    ssns = ["123-45-6789", "987-65-4321"]
    for ssn in ssns:
        redacted = anonymizer.redaction.redact_partial_ssn(ssn)
        print(f"    {ssn:30s} → {redacted}")
    
    # Credit Cards
    print("\n  Credit Card Numbers:")
    cards = ["4532-1488-0343-6467", "5425-2334-3010-9903"]
    for card in cards:
        redacted = anonymizer.redaction.redact_partial_credit_card(card)
        print(f"    {card:30s} → {redacted}")


def example_generalization():
    """Example 3: Generalization techniques."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Generalization Techniques")
    print("=" * 70)
    
    anonymizer = AnonymizationTechniques()
    
    # Age generalization
    print("\nAge Generalization (10-year ranges):")
    ages = [25, 34, 42, 58, 67]
    for age in ages:
        generalized = anonymizer.generalize_age(age)
        print(f"  Age {age:2d} → {generalized}")
    
    print("\nAge Generalization (5-year ranges):")
    for age in ages:
        generalized = anonymizer.generalize_age(age, range_size=5)
        print(f"  Age {age:2d} → {generalized}")
    
    # Zipcode generalization
    print("\nZipcode Generalization:")
    zipcodes = ["10001", "90210", "02138", "94102"]
    for zipcode in zipcodes:
        generalized = anonymizer.generalize_zipcode(zipcode)
        print(f"  {zipcode} → {generalized}")
    
    # Date generalization
    print("\nDate Generalization:")
    dates = ["2024-03-15", "2024-06-22", "2024-09-10", "2024-12-31"]
    
    print("\n  To Quarter:")
    for date in dates:
        generalized = anonymizer.generalization.generalize_date_to_quarter(date)
        print(f"    {date} → {generalized}")
    
    print("\n  To Month:")
    for date in dates:
        generalized = anonymizer.generalization.generalize_date_to_month(date)
        print(f"    {date} → {generalized}")
    
    print("\n  To Year:")
    for date in dates:
        generalized = anonymizer.generalization.generalize_date_to_year(date)
        print(f"    {date} → {generalized}")
    
    # Income generalization
    print("\nIncome Generalization:")
    incomes = [45000, 75000, 125000, 250000]
    for income in incomes:
        generalized = anonymizer.generalization.generalize_income(income)
        print(f"  ${income:,} → {generalized}")


def example_pseudonymization():
    """Example 4: Pseudonymization technique."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Pseudonymization (Consistent Fake Data)")
    print("=" * 70)
    
    anonymizer = AnonymizationTechniques()
    
    # Names
    print("\nName Pseudonymization:")
    names = ["John Smith", "Jane Doe", "Alice Johnson"]
    for name in names:
        fake_name = anonymizer.pseudonymize_name(name)
        print(f"  {name:20s} → {fake_name}")
    
    # Show consistency
    print("\nConsistency Check (same input = same output):")
    original = "John Smith"
    fake1 = anonymizer.pseudonymize_name(original)
    fake2 = anonymizer.pseudonymize_name(original)
    print(f"  Original: {original}")
    print(f"  Fake 1:   {fake1}")
    print(f"  Fake 2:   {fake2}")
    print(f"  Consistent: {fake1 == fake2}")
    
    # Emails
    print("\nEmail Pseudonymization:")
    emails = ["john.doe@example.com", "jane@company.org", "alice@email.com"]
    for email in emails:
        fake_email = anonymizer.pseudonymize_email(email)
        print(f"  {email:30s} → {fake_email}")
    
    # Phone numbers
    print("\nPhone Pseudonymization:")
    phones = ["(555) 123-4567", "555-987-6543"]
    for phone in phones:
        fake_phone = anonymizer.pseudonymization.pseudonymize_phone(phone)
        print(f"  {phone:20s} → {fake_phone}")
    
    # Addresses
    print("\nAddress Pseudonymization:")
    addresses = ["123 Main St, New York, NY", "456 Oak Ave, Boston, MA"]
    for address in addresses:
        fake_address = anonymizer.pseudonymization.pseudonymize_address(address)
        print(f"  {address:35s} → {fake_address[:40]}...")


def example_combined_techniques():
    """Example 5: Combining multiple techniques."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Combined Techniques on Dataset")
    print("=" * 70)
    
    # Create sample dataset
    df = pd.DataFrame({
        'name': ['John Smith', 'Jane Doe', 'Alice Johnson'],
        'email': ['john@example.com', 'jane@example.com', 'alice@example.com'],
        'ssn': ['123-45-6789', '987-65-4321', '456-78-9012'],
        'age': [34, 45, 28],
        'zipcode': ['10001', '90210', '02138'],
        'dob': ['1990-03-15', '1979-06-22', '1996-12-10'],
        'income': [75000, 125000, 55000]
    })
    
    print("\nOriginal Dataset:")
    print(df.to_string(index=False))
    
    # Anonymize dataset
    anonymizer = AnonymizationTechniques()
    
    df_anon = df.copy()
    
    # Apply different techniques to different fields
    df_anon['name'] = df['name'].apply(anonymizer.pseudonymize_name)
    df_anon['email'] = df['email'].apply(lambda x: anonymizer.redaction.redact_partial_email(x))
    df_anon['ssn'] = df['ssn'].apply(lambda x: anonymizer.redaction.redact_partial_ssn(x))
    df_anon['age'] = df['age'].apply(anonymizer.generalize_age)
    df_anon['zipcode'] = df['zipcode'].apply(anonymizer.generalize_zipcode)
    df_anon['dob'] = df['dob'].apply(anonymizer.generalization.generalize_date_to_quarter)
    df_anon['income'] = df['income'].apply(anonymizer.generalization.generalize_income)
    
    print("\nAnonymized Dataset:")
    print(df_anon.to_string(index=False))
    
    print("\nTechniques Applied:")
    print("  name:     Pseudonymization (consistent fake names)")
    print("  email:    Partial redaction")
    print("  ssn:      Partial redaction (last 4 digits)")
    print("  age:      Generalization (10-year ranges)")
    print("  zipcode:  Generalization (3-digit precision)")
    print("  dob:      Generalization (quarterly)")
    print("  income:   Generalization ($10k brackets)")


def example_technique_selection():
    """Example 6: Choosing the right technique."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Choosing the Right Technique")
    print("=" * 70)
    
    print("\nGuidelines for Technique Selection:")
    print("-" * 70)
    
    print("\n1. HASHING:")
    print("   Use when: Need one-way transformation, no reverse needed")
    print("   Examples: Passwords, API keys, unique IDs")
    print("   Pros: Strong privacy, deterministic")
    print("   Cons: Cannot recover original, vulnerable to rainbow tables")
    
    print("\n2. REDACTION:")
    print("   Use when: Must completely hide sensitive data")
    print("   Examples: Full SSNs, credit cards, sensitive text")
    print("   Pros: Simple, complete privacy")
    print("   Cons: Loses all utility of data")
    
    print("\n3. GENERALIZATION:")
    print("   Use when: Need to preserve statistical properties")
    print("   Examples: Age ranges, location regions, date periods")
    print("   Pros: Preserves trends, enables analytics")
    print("   Cons: Reduces precision, still has some re-id risk")
    
    print("\n4. PSEUDONYMIZATION:")
    print("   Use when: Need realistic data for testing/development")
    print("   Examples: Names, emails, addresses in non-prod environments")
    print("   Pros: Maintains format, looks realistic")
    print("   Cons: Could still be linked if patterns exist")
    
    # Show examples
    print("\n" + "-" * 70)
    print("Example Applications:")
    print("-" * 70)
    
    anonymizer = AnonymizationTechniques()
    
    print("\nScenario 1: Sharing data with third-party analytics")
    print("  Original: John Smith, age 34, zip 10001")
    print("  Solution:")
    print(f"    Name → Hashed: {anonymizer.hash_value('John Smith')[:20]}...")
    print(f"    Age → Generalized: {anonymizer.generalize_age(34)}")
    print(f"    Zip → Generalized: {anonymizer.generalize_zipcode('10001')}")
    
    print("\nScenario 2: Creating test database for development")
    print("  Original: john.doe@example.com, (555) 123-4567")
    print("  Solution:")
    print(f"    Email → Fake: {anonymizer.pseudonymize_email('john.doe@example.com')}")
    print(f"    Phone → Fake: {anonymizer.pseudonymization.pseudonymize_phone('(555) 123-4567')}")
    
    print("\nScenario 3: Complying with data retention policy")
    print("  Original: SSN 123-45-6789, Credit Card 4532-1488-0343-6467")
    print("  Solution:")
    print(f"    SSN → Partial: {anonymizer.redaction.redact_partial_ssn('123-45-6789')}")
    print(f"    Card → Partial: {anonymizer.redaction.redact_partial_credit_card('4532-1488-0343-6467')}")


def main():
    """Run all examples."""
    print("\n")
    print("#" * 70)
    print("# ANONYMIZATION TECHNIQUES - COMPREHENSIVE EXAMPLES")
    print("#" * 70)
    
    try:
        example_hashing()
        example_redaction()
        example_generalization()
        example_pseudonymization()
        example_combined_techniques()
        example_technique_selection()
        
        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        
        print("\nNext Steps:")
        print("1. Run tests: pytest tests/test_anonymization_techniques.py -v")
        print("2. Try anonymizing your own data")
        print("3. Combine with PII detection and risk assessment")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()