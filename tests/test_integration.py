"""
Integration tests for PII Scanner and Risk Assessment.

Tests complete workflows on fixture datasets.
"""

import pytest
import pandas as pd
import json
from pathlib import Path

from src.scanner import PIIScanner
from src.risk_assessment import RiskAssessmentEngine, infer_quasi_identifiers


# Skip tests if fixtures don't exist
def check_fixtures_exist():
    """Check if fixture files exist."""
    fixtures = [
        "fixtures/customers.csv",
        "fixtures/support_tickets.json",
        "fixtures/transactions.csv",
    ]
    return all(Path(f).exists() for f in fixtures)


requires_fixtures = pytest.mark.skipif(
    not check_fixtures_exist(),
    reason="Fixture files not found. Run data generation script first.",
)


@requires_fixtures
class TestCustomersCSVIntegration:
    """Integration tests on customers.csv fixture."""

    @pytest.fixture
    def scanner(self):
        """Create PII scanner."""
        return PIIScanner(use_ner=False)  # Disable NER for speed

    @pytest.fixture
    def risk_engine(self):
        """Create risk assessment engine."""
        return RiskAssessmentEngine()

    def test_scan_customers_csv(self, scanner):
        """Test scanning customers.csv for PII."""
        results = scanner.scan_csv("fixtures/customers.csv", sample_size=100)

        # Should detect PII in multiple fields
        assert len(results) > 0

        # Check expected PII types
        field_names = list(results.keys())

        # Email field should be detected
        assert any("email" in name.lower() for name in field_names)

        # Phone field should be detected
        assert any("phone" in name.lower() for name in field_names)

        # SSN field should be detected
        assert any("ssn" in name.lower() for name in field_names)

    def test_scan_customers_pii_types(self, scanner):
        """Test that correct PII types are detected."""
        results = scanner.scan_csv("fixtures/customers.csv", sample_size=100)

        # Email field should contain 'email' PII type
        if "email" in results:
            assert "email" in results["email"].pii_types

        # Phone field should contain 'phone' PII type
        if "phone" in results:
            assert "phone" in results["phone"].pii_types

        # SSN field should contain 'ssn' PII type
        if "ssn" in results:
            assert "ssn" in results["ssn"].pii_types

    def test_risk_assessment_customers(self, scanner, risk_engine):
        """Test risk assessment on customers.csv."""
        # Scan for PII
        pii_results = scanner.scan_csv("fixtures/customers.csv", sample_size=100)

        # Load full dataset
        df = pd.read_csv("fixtures/customers.csv")

        # Infer quasi-identifiers
        qi = infer_quasi_identifiers(df, pii_results)

        # Should find some quasi-identifiers
        assert len(qi) > 0

        # Perform risk assessment
        qi_sets = [qi[:2]] if len(qi) >= 2 else [qi]
        risk_scores, risk_report = risk_engine.assess_dataset(df, qi_sets)

        # Should have risk scores for all records
        assert len(risk_scores) == len(df)

        # Report should have valid statistics
        assert risk_report.total_records == len(df)
        assert (
            risk_report.high_risk_count
            + risk_report.medium_risk_count
            + risk_report.low_risk_count
            == len(df)
        )

    def test_customers_confidence_scores(self, scanner):
        """Test that confidence scores are reasonable."""
        results = scanner.scan_csv("fixtures/customers.csv", sample_size=100)

        for field, result in results.items():
            # Confidence should be between 0 and 1
            assert 0 <= result.confidence <= 1

            # For direct PII fields (email, phone, ssn), confidence should be high
            if any(
                pii_type in ["email", "phone", "ssn"] for pii_type in result.pii_types
            ):
                assert result.confidence >= 0.7


@requires_fixtures
class TestSupportTicketsJSONIntegration:
    """Integration tests on support_tickets.json fixture."""

    @pytest.fixture
    def scanner(self):
        """Create PII scanner with NER enabled."""
        return PIIScanner(use_ner=True)

    def test_scan_support_tickets_json(self, scanner):
        """Test scanning support_tickets.json for PII."""
        try:
            results = scanner.scan_json(
                "fixtures/support_tickets.json", sample_size=100
            )

            # Should detect PII in message field
            assert len(results) > 0

        except RuntimeError:
            # NER not available - skip
            pytest.skip("spaCy model not available")

    def test_support_tickets_message_field(self, scanner):
        """Test that message field contains embedded PII."""
        try:
            results = scanner.scan_json(
                "fixtures/support_tickets.json", sample_size=100
            )

            # Message field should be detected (contains PII)
            field_names = list(results.keys())
            assert any("message" in name.lower() for name in field_names)

        except RuntimeError:
            pytest.skip("spaCy model not available")

    def test_support_tickets_pii_variety(self, scanner):
        """Test that various PII types are detected in messages."""
        try:
            results = scanner.scan_json(
                "fixtures/support_tickets.json", sample_size=100
            )

            # Should detect multiple PII types across fields
            all_pii_types = set()
            for result in results.values():
                all_pii_types.update(result.pii_types)

            # Should have at least 2 different PII types
            assert len(all_pii_types) >= 2

        except RuntimeError:
            pytest.skip("spaCy model not available")


@requires_fixtures
class TestTransactionsCSVIntegration:
    """Integration tests on transactions.csv fixture."""

    @pytest.fixture
    def scanner(self):
        """Create PII scanner."""
        return PIIScanner(use_ner=False)

    @pytest.fixture
    def risk_engine(self):
        """Create risk assessment engine."""
        return RiskAssessmentEngine()

    def test_scan_transactions_csv(self, scanner):
        """Test scanning transactions.csv for PII."""
        results = scanner.scan_csv("fixtures/transactions.csv", sample_size=200)

        # Should detect PII
        assert len(results) > 0

    def test_transactions_credit_card_detection(self, scanner):
        """Test credit card detection in transactions."""
        results = scanner.scan_csv("fixtures/transactions.csv", sample_size=200)

        # Should detect credit card field
        field_names = list(results.keys())
        has_cc = any(
            "credit" in name.lower() or "card" in name.lower() for name in field_names
        )

        if has_cc:
            cc_fields = [
                name
                for name in field_names
                if "credit" in name.lower() or "card" in name.lower()
            ]

            for field in cc_fields:
                assert "credit_card" in results[field].pii_types

    def test_transactions_ip_address_detection(self, scanner):
        """Test IP address detection might occur."""
        results = scanner.scan_csv("fixtures/transactions.csv", sample_size=200)

        # IP addresses might be detected (depending on fixture generation)
        # Just verify scan completes without errors
        assert isinstance(results, dict)

    def test_risk_assessment_transactions(self, scanner, risk_engine):
        """Test risk assessment on transactions."""
        # Scan for PII
        pii_results = scanner.scan_csv("fixtures/transactions.csv", sample_size=200)

        # Load dataset (limit to first 1000 for speed)
        df = pd.read_csv("fixtures/transactions.csv").head(1000)

        # Create quasi-identifier sets manually for transactions
        # (user_id + ip_address could be quasi-identifiers)
        qi_sets = []
        if "user_id" in df.columns:
            qi_sets.append(["user_id"])

        if len(qi_sets) > 0:
            risk_scores, risk_report = risk_engine.assess_dataset(df, qi_sets)

            # Should have valid report
            assert risk_report.total_records == len(df)
            assert risk_report.min_k_anonymity > 0


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    def test_scan_and_assess_workflow(self):
        """Test complete workflow: scan → assess risk → generate report."""
        # Create sample dataset
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Carol", "Dave"],
                "email": [
                    "alice@example.com",
                    "bob@example.com",
                    "carol@example.com",
                    "dave@example.com",
                ],
                "age": [25, 30, 25, 30],
                "zip": ["10001", "10002", "10001", "10002"],
            }
        )

        # Save to CSV
        test_file = Path("test_workflow.csv")
        df.to_csv(test_file, index=False)

        try:
            # Step 1: Scan for PII
            scanner = PIIScanner(use_ner=False)
            pii_results = scanner.scan_csv(str(test_file))

            assert len(pii_results) > 0
            assert "email" in pii_results

            # Step 2: Assess risk
            risk_engine = RiskAssessmentEngine()
            qi = ["age", "zip"]
            qi_sets = [qi]

            risk_scores, risk_report = risk_engine.assess_dataset(df, qi_sets)

            assert len(risk_scores) == 4
            assert risk_report.total_records == 4

            # Step 3: Generate report
            report_dict = scanner.generate_report(pii_results, format="dict")

            assert "summary" in report_dict
            assert "fields" in report_dict

        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()

    def test_high_risk_record_identification(self):
        """Test identification and retrieval of high-risk records."""
        # Create dataset with unique records
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Carol"],
                "age": [25, 30, 35],
                "zip": ["10001", "10002", "10003"],
            }
        )

        # All records are unique on age+zip
        risk_engine = RiskAssessmentEngine()
        qi_sets = [["age", "zip"]]

        risk_scores, risk_report = risk_engine.assess_dataset(df, qi_sets)

        # All should be high risk (unique)
        assert risk_report.high_risk_count + risk_report.medium_risk_count >= 3

        # Get high-risk records
        high_risk_df = risk_engine.get_high_risk_records(df, risk_scores)

        assert len(high_risk_df) > 0
        assert "risk_score" in high_risk_df.columns

    def test_json_output_structure(self):
        """Test that JSON output has correct structure."""
        from src.cli import _generate_json_output
        from src.scanner import PIIDetectionResult

        # Create mock results
        pii_results = {
            "email": PIIDetectionResult("email", ["email"], 0.95, ["test@ex.com"], 10)
        }

        from src.risk_assessment import RiskScore, RiskReport

        risk_scores = [RiskScore(0, "high", 0.9, 2, 1, "High risk")]
        risk_report = RiskReport(
            total_records=1,
            high_risk_count=1,
            medium_risk_count=0,
            low_risk_count=0,
            high_risk_percentage=100.0,
            medium_risk_percentage=0.0,
            low_risk_percentage=0.0,
            average_k_anonymity=1.0,
            min_k_anonymity=1,
            unique_records=[0],
            rare_records=[],
            safe_records=[],
        )

        # Generate JSON output
        output = _generate_json_output(pii_results, risk_scores, risk_report)

        # Check structure
        assert "pii_detection" in output
        assert "risk_assessment" in output
        assert "summary" in output["risk_assessment"]
        assert "risk_distribution" in output["risk_assessment"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
