"""
Risk Assessment Examples.

Demonstrates how to use the risk assessment engine with various scenarios.
"""

import pandas as pd
from src.risk_assessment import RiskAssessmentEngine, infer_quasi_identifiers
from src.scanner import PIIScanner


def example_basic_uniqueness():
    """Example 1: Basic uniqueness calculation."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Uniqueness Calculation")
    print("=" * 70)

    # Create sample dataset
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"],
            "age": [25, 25, 30, 30, 30, 35],
            "zip": ["10001", "10001", "10002", "10002", "10002", "10003"],
        }
    )

    print("\nSample Dataset:")
    print(df)

    # Initialize engine
    engine = RiskAssessmentEngine()

    # Calculate uniqueness based on age + zip
    print("\nCalculating uniqueness on [age, zip]...")
    uniqueness = engine.calculate_uniqueness(df, ["age", "zip"])

    print("\nUniqueness Results:")
    for result in uniqueness:
        print(f"  Record {result.record_index}:")
        print(f"    k-anonymity: {result.k_anonymity}")
        print(f"    Is unique (k=1): {result.is_unique}")
        print(f"    Is rare (k=2-5): {result.is_rare}")
        print(f"    Is safe (k>10): {result.is_safe}")
        print()


def example_risk_scoring():
    """Example 2: Risk score calculation."""
    print("=" * 70)
    print("EXAMPLE 2: Risk Score Calculation")
    print("=" * 70)

    # Create dataset with varying risk levels
    df = pd.DataFrame(
        {
            "patient_id": range(1, 11),
            "age": [34, 34, 45, 45, 45, 45, 67, 67, 67, 67],
            "zip": [
                "02138",
                "02138",
                "10001",
                "10001",
                "10001",
                "10001",
                "90210",
                "90210",
                "90210",
                "90210",
            ],
            "gender": ["F", "F", "M", "M", "F", "F", "M", "M", "M", "M"],
            "diagnosis": [
                "Disease A",
                "Disease B",
                "Disease C",
                "Disease D",
                "Disease E",
                "Disease F",
                "Disease G",
                "Disease H",
                "Disease I",
                "Disease J",
            ],
        }
    )

    print("\nSample Dataset:")
    print(df[["patient_id", "age", "zip", "gender"]])

    # Initialize engine
    engine = RiskAssessmentEngine()

    # Define quasi-identifier combinations to test
    qi_sets = [["age", "zip"], ["age", "gender"], ["age", "zip", "gender"]]

    print(f"\nTesting {len(qi_sets)} quasi-identifier combinations...")

    # Calculate risk scores
    risk_scores, risk_report = engine.assess_dataset(df, qi_sets)

    print("\nRisk Scores:")
    for rs in risk_scores[:5]:  # Show first 5
        print(f"  Record {rs.record_index}:")
        print(f"    Risk Level: {rs.risk_level.upper()}")
        print(f"    Risk Score: {rs.risk_score:.2f}")
        print(f"    Unique on {rs.unique_on_qi_count}/{len(qi_sets)} QI combinations")
        print(f"    Min k-anonymity: {rs.k_anonymity}")
        print(f"    Reasoning: {rs.reasoning}")
        print()


def example_risk_report():
    """Example 3: Generating risk assessment report."""
    print("=" * 70)
    print("EXAMPLE 3: Risk Assessment Report")
    print("=" * 70)

    # Create larger dataset
    df = pd.DataFrame(
        {
            "age": [25] * 5 + [30] * 10 + [35] * 8 + [40] * 15 + [45] * 20,
            "zip": ["10001"] * 5
            + ["10002"] * 10
            + ["10003"] * 8
            + ["10004"] * 15
            + ["10005"] * 20,
            "income": [50000] * 5
            + [60000] * 10
            + [70000] * 8
            + [80000] * 15
            + [90000] * 20,
        }
    )

    print(f"\nDataset: {len(df)} records")
    print("\nAge distribution:")
    print(df["age"].value_counts().sort_index())

    # Initialize engine
    engine = RiskAssessmentEngine()

    # Assess risk
    qi_sets = [["age", "zip"]]
    risk_scores, risk_report = engine.assess_dataset(df, qi_sets)

    print("\n" + "=" * 50)
    print("RISK ASSESSMENT SUMMARY")
    print("=" * 50)
    print(f"\nTotal Records: {risk_report.total_records}")
    print(f"\nRisk Distribution:")
    print(
        f"  High Risk:   {risk_report.high_risk_count:4d} ({risk_report.high_risk_percentage:5.1f}%)"
    )
    print(
        f"  Medium Risk: {risk_report.medium_risk_count:4d} ({risk_report.medium_risk_percentage:5.1f}%)"
    )
    print(
        f"  Low Risk:    {risk_report.low_risk_count:4d} ({risk_report.low_risk_percentage:5.1f}%)"
    )

    print(f"\nK-Anonymity Statistics:")
    print(f"  Average k: {risk_report.average_k_anonymity:.2f}")
    print(f"  Minimum k: {risk_report.min_k_anonymity}")

    print(f"\nRecord Classification:")
    print(f"  Unique records (k=1):    {len(risk_report.unique_records)}")
    print(f"  Rare records (k=2-5):    {len(risk_report.rare_records)}")
    print(f"  Safe records (k>10):     {len(risk_report.safe_records)}")


def example_high_risk_records():
    """Example 4: Identifying high-risk records."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Identifying High-Risk Records")
    print("=" * 70)

    # Create dataset with some unique records
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Carol", "Dave", "Eve"],
            "age": [34, 45, 67, 45, 45],
            "zip": ["02138", "10001", "90210", "10001", "10001"],
            "gender": ["F", "M", "M", "M", "M"],
            "salary": [75000, 85000, 95000, 80000, 82000],
        }
    )

    print("\nDataset:")
    print(df)

    # Initialize engine
    engine = RiskAssessmentEngine()

    # Assess risk
    qi_sets = [["age", "zip"], ["age", "gender"]]
    risk_scores, risk_report = engine.assess_dataset(df, qi_sets)

    # Get high-risk records
    high_risk_df = engine.get_high_risk_records(df, risk_scores, limit=10)

    print(f"\nFound {len(high_risk_df)} high-risk records:")
    print("\n" + "-" * 70)

    for idx, row in high_risk_df.iterrows():
        print(f"\nRecord {idx} ({row['name']}):")
        print(f"  Risk Score: {row['risk_score']:.2f}")
        print(f"  Age: {row['age']}, Zip: {row['zip']}, Gender: {row['gender']}")
        print(f"  Reasoning: {row['risk_reasoning']}")


def example_integrated_workflow():
    """Example 5: Integrated PII detection and risk assessment."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Integrated Workflow (PII + Risk)")
    print("=" * 70)

    # Create dataset with PII
    df = pd.DataFrame(
        {
            "name": ["Alice Smith", "Bob Jones", "Carol White"],
            "email": ["alice@example.com", "bob@example.com", "carol@example.com"],
            "age": [25, 30, 25],
            "zip": ["10001", "10002", "10001"],
            "city": ["New York", "Boston", "New York"],
        }
    )

    print("\nDataset:")
    print(df)

    # Step 1: Scan for PII
    print("\n" + "-" * 70)
    print("Step 1: PII Detection")
    print("-" * 70)

    scanner = PIIScanner(use_ner=False)  # Disable NER for this example

    # Save to temp file
    df.to_csv("temp_example.csv", index=False)
    pii_results = scanner.scan_csv("temp_example.csv")

    print("\nDetected PII:")
    for field, result in pii_results.items():
        print(f"  {field}: {result.pii_types} (confidence: {result.confidence:.2f})")

    # Step 2: Assess risk
    print("\n" + "-" * 70)
    print("Step 2: Risk Assessment")
    print("-" * 70)

    # Infer quasi-identifiers from PII results
    quasi_ids = infer_quasi_identifiers(df, pii_results)
    print(f"\nInferred quasi-identifiers: {quasi_ids}")

    if quasi_ids:
        engine = RiskAssessmentEngine()
        qi_sets = [quasi_ids]
        risk_scores, risk_report = engine.assess_dataset(df, qi_sets)

        print(f"\nRisk Summary:")
        print(f"  High risk: {risk_report.high_risk_percentage}%")
        print(f"  Medium risk: {risk_report.medium_risk_percentage}%")
        print(f"  Low risk: {risk_report.low_risk_percentage}%")

    # Cleanup
    import os

    if os.path.exists("temp_example.csv"):
        os.remove("temp_example.csv")


def example_comparative_qi_sets():
    """Example 6: Comparing different quasi-identifier sets."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Comparing QI Sets")
    print("=" * 70)

    df = pd.DataFrame(
        {
            "age": [25, 25, 30, 30, 35, 35],
            "zip": ["10001", "10002", "10001", "10002", "10003", "10003"],
            "gender": ["M", "F", "M", "F", "M", "F"],
            "city": ["NYC", "NYC", "Boston", "Boston", "LA", "LA"],
        }
    )

    print("\nDataset:")
    print(df)

    engine = RiskAssessmentEngine()

    # Test different QI combinations
    qi_combinations = [
        ["age"],
        ["zip"],
        ["age", "zip"],
        ["age", "gender"],
        ["age", "zip", "gender"],
    ]

    print("\nComparing different quasi-identifier combinations:")
    print("-" * 70)

    for qi_set in qi_combinations:
        uniqueness = engine.calculate_uniqueness(df, qi_set)
        unique_count = sum(1 for u in uniqueness if u.is_unique)
        avg_k = sum(u.k_anonymity for u in uniqueness) / len(uniqueness)

        print(f"\nQI Set: {qi_set}")
        print(f"  Unique records: {unique_count}/{len(df)}")
        print(f"  Average k: {avg_k:.2f}")


def main():
    """Run all examples."""
    print("\n")
    print("#" * 70)
    print("# RISK ASSESSMENT ENGINE - EXAMPLES")
    print("#" * 70)

    try:
        example_basic_uniqueness()
        example_risk_scoring()
        example_risk_report()
        example_high_risk_records()
        example_integrated_workflow()
        example_comparative_qi_sets()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
