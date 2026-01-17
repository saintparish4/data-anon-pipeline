"""
Example usage of PII Scanner.

Demonstrates how to use the regex detector, NER detector, and scanner orchestrator.
"""

from src.detectors.regex_detector import RegexDetector
from src.detectors.ner_detector import NERDetector
from src.scanner import PIIScanner


def example_regex_detection():
    """Example: Using the regex detector directly."""
    print("=" * 70)
    print("EXAMPLE 1: Regex-Based Detection")
    print("=" * 70)

    detector = RegexDetector()

    # Sample text with various PII types
    text = """
    Contact Information:
    Email: john.doe@example.com
    Phone: (555) 123-4567
    SSN: 123-45-6789
    Credit Card: 4532-1488-0343-6467
    """

    print(f"\nScanning text: {text}\n")

    # Detect all PII types
    matches = detector.detect_all(text)

    print(f"Found {len(matches)} PII matches:\n")
    for match in matches:
        print(
            f"  {match.pii_type.upper():12} | {match.value:25} | Confidence: {match.confidence:.2f}"
        )

    print("\n")


def example_ner_detection():
    """Example: Using the NER detector directly."""
    print("=" * 70)
    print("EXAMPLE 2: NER-Based Detection")
    print("=" * 70)

    try:
        detector = NERDetector()

        # Sample text with named entities
        text = """
        John Smith works at Microsoft Corporation in Seattle, Washington.
        He recently met with Mary Johnson from Google in San Francisco.
        """

        print(f"\nScanning text: {text}\n")

        # Detect all named entities
        matches = detector.detect_all(text)

        print(f"Found {len(matches)} named entities:\n")
        for match in matches:
            print(
                f"  {match.entity_type.upper():15} | {match.value:30} | Confidence: {match.confidence:.2f}"
            )

        print("\n")

    except RuntimeError as e:
        print(f"\nNER detection skipped: {e}")
        print("Install spaCy model with: python -m spacy download en_core_web_sm\n")


def example_scan_csv():
    """Example: Scanning a CSV file."""
    print("=" * 70)
    print("EXAMPLE 3: Scanning CSV File")
    print("=" * 70)

    scanner = PIIScanner(use_ner=False)  # NER optional

    # Scan the customers fixture
    try:
        results = scanner.scan_csv("fixtures/customers.csv", sample_size=50)

        print(f"\nScanned customers.csv")
        print(f"Found PII in {len(results)} fields:\n")

        for field_name, result in results.items():
            print(f"  Field: {field_name}")
            print(f"    PII Types: {', '.join(result.pii_types)}")
            print(f"    Confidence: {result.confidence:.2f}")
            print(f"    Detections: {result.detection_count}/50 samples")
            print()

        # Generate text report
        print("\nText Report:")
        print(scanner.generate_report(results, format="text"))

    except FileNotFoundError:
        print(
            "\nNote: Run the data generation script first to create fixtures/customers.csv"
        )
        print("Expected fixture file not found.\n")


def example_scan_json():
    """Example: Scanning a JSON file."""
    print("=" * 70)
    print("EXAMPLE 4: Scanning JSON File")
    print("=" * 70)

    scanner = PIIScanner(use_ner=True)  # Enable NER for messages

    try:
        results = scanner.scan_json("fixtures/support_tickets.json", sample_size=50)

        print(f"\nScanned support_tickets.json")
        print(f"Found PII in {len(results)} fields:\n")

        for field_name, result in results.items():
            print(f"  Field: {field_name}")
            print(f"    PII Types: {', '.join(result.pii_types)}")
            print(f"    Confidence: {result.confidence:.2f}")
            print()

        # Get high-risk fields
        high_risk = scanner.get_high_risk_fields(results, threshold=0.8)
        print(f"High-risk fields (confidence ≥ 0.8): {', '.join(high_risk)}\n")

    except FileNotFoundError:
        print(
            "\nNote: Run the data generation script first to create fixtures/support_tickets.json"
        )
        print("Expected fixture file not found.\n")


def example_structured_output():
    """Example: Getting structured output."""
    print("=" * 70)
    print("EXAMPLE 5: Structured JSON Output")
    print("=" * 70)

    scanner = PIIScanner(use_ner=False)

    try:
        results = scanner.scan_csv("fixtures/customers.csv", sample_size=50)

        # Generate JSON report
        json_report = scanner.generate_report(results, format="json")

        print("\nJSON Report (first 500 characters):")
        print(json_report[:500])
        print("...\n")

    except FileNotFoundError:
        print(
            "\nNote: Run the data generation script first to create fixtures/customers.csv\n"
        )


def main():
    """Run all examples."""
    print("\n")
    print("#" * 70)
    print("# PII SCANNER - USAGE EXAMPLES")
    print("#" * 70)
    print("\n")

    # Run examples
    example_regex_detection()
    example_ner_detection()
    example_scan_csv()
    example_scan_json()
    example_structured_output()

    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run tests: pytest tests/ -v")
    print("2. Scan your own data: scanner.scan_file('your_data.csv')")
    print("3. Integrate into your pipeline")
    print()


if __name__ == "__main__":
    main()
