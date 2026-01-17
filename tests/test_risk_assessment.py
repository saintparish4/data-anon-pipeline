"""
Unit tests for risk_assessment.py

Tests uniqueness calculation, risk scoring, and report generation.
"""

import pytest
import pandas as pd
from src.risk_assessment import (
    RiskAssessmentEngine,
    UniquenessResult,
    RiskScore,
    RiskReport,
    infer_quasi_identifiers,
)


class TestUniquenessCalculation:
    """Test uniqueness calculation functionality."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "age": [25, 25, 30, 30, 35, 35, 35, 40, 40, 40, 40, 40],
                "zip": [
                    "10001",
                    "10001",
                    "10002",
                    "10002",
                    "10003",
                    "10003",
                    "10003",
                    "10004",
                    "10004",
                    "10004",
                    "10004",
                    "10004",
                ],
                "gender": ["M", "M", "F", "F", "M", "M", "M", "F", "F", "F", "F", "F"],
                "name": [
                    "Alice",
                    "Bob",
                    "Carol",
                    "Dave",
                    "Eve",
                    "Frank",
                    "Grace",
                    "Henry",
                    "Iris",
                    "Jack",
                    "Kate",
                    "Liam",
                ],
            }
        )

    @pytest.fixture
    def engine(self):
        """Create risk assessment engine."""
        return RiskAssessmentEngine()

    def test_calculate_uniqueness_basic(self, engine, sample_df):
        """Test basic uniqueness calculation."""
        results = engine.calculate_uniqueness(sample_df, ["age", "zip"])

        assert len(results) == 12
        assert all(isinstance(r, UniquenessResult) for r in results)

    def test_calculate_uniqueness_identifies_groups(self, engine, sample_df):
        """Test that uniqueness correctly identifies group sizes."""
        results = engine.calculate_uniqueness(sample_df, ["age", "zip"])

        # Check k-anonymity values
        k_values = [r.k_anonymity for r in results]

        # First two records have age=25, zip=10001 (k=2)
        assert k_values[0] == 2
        assert k_values[1] == 2

        # Records with age=40, zip=10004 (k=5)
        assert k_values[7] == 5
        assert k_values[8] == 5

    def test_calculate_uniqueness_identifies_unique_records(self, engine):
        """Test identification of unique records (k=1)."""
        df = pd.DataFrame({"age": [25, 30, 35], "zip": ["10001", "10002", "10003"]})

        results = engine.calculate_uniqueness(df, ["age", "zip"])

        # All records are unique
        assert all(r.is_unique for r in results)
        assert all(r.k_anonymity == 1 for r in results)

    def test_calculate_uniqueness_identifies_rare_records(self, engine):
        """Test identification of rare records (k=2-5)."""
        df = pd.DataFrame(
            {
                "age": [25, 25, 30, 30, 30],
                "zip": ["10001", "10001", "10002", "10002", "10002"],
            }
        )

        results = engine.calculate_uniqueness(df, ["age", "zip"])

        # First two are rare (k=2)
        assert results[0].is_rare
        assert results[1].is_rare

        # Last three are rare (k=3)
        assert results[2].is_rare
        assert results[3].is_rare
        assert results[4].is_rare

    def test_calculate_uniqueness_identifies_safe_records(self, engine):
        """Test identification of safe records (k>10)."""
        # Create dataset with large group
        df = pd.DataFrame({"age": [25] * 15, "zip": ["10001"] * 15})

        results = engine.calculate_uniqueness(df, ["age", "zip"])

        # All records are safe
        assert all(r.is_safe for r in results)
        assert all(r.k_anonymity == 15 for r in results)

    def test_calculate_uniqueness_stores_qi_values(self, engine, sample_df):
        """Test that QI values are stored correctly."""
        results = engine.calculate_uniqueness(sample_df, ["age", "zip"])

        first_result = results[0]
        assert "age" in first_result.quasi_identifier_values
        assert "zip" in first_result.quasi_identifier_values
        assert first_result.quasi_identifier_values["age"] == 25
        assert first_result.quasi_identifier_values["zip"] == "10001"

    def test_calculate_uniqueness_invalid_qi(self, engine, sample_df):
        """Test error handling for invalid quasi-identifiers."""
        with pytest.raises(ValueError) as exc_info:
            engine.calculate_uniqueness(sample_df, ["nonexistent_column"])

        assert "not found" in str(exc_info.value)


class TestRiskScoring:
    """Test risk scoring functionality."""

    @pytest.fixture
    def engine(self):
        """Create risk assessment engine."""
        return RiskAssessmentEngine()

    def test_determine_risk_level_high(self, engine):
        """Test high risk determination (unique on 2+ QI sets)."""
        level, score, reasoning = engine._determine_risk_level(
            unique_count=2, total_qi_sets=3, min_k=1
        )

        assert level == "high"
        assert score >= 0.9
        assert "Unique on 2" in reasoning

    def test_determine_risk_level_medium_unique(self, engine):
        """Test medium risk determination (unique on 1 QI set)."""
        level, score, reasoning = engine._determine_risk_level(
            unique_count=1, total_qi_sets=3, min_k=2
        )

        assert level == "medium"
        assert 0.5 <= score < 0.9
        assert "Unique on 1" in reasoning

    def test_determine_risk_level_low(self, engine):
        """Test low risk determination (k>10)."""
        level, score, reasoning = engine._determine_risk_level(
            unique_count=0, total_qi_sets=3, min_k=15
        )

        assert level == "low"
        assert score <= 0.4
        assert "safe anonymity" in reasoning.lower()

    def test_determine_risk_level_medium_moderate_k(self, engine):
        """Test medium risk with moderate k-anonymity."""
        level, score, reasoning = engine._determine_risk_level(
            unique_count=0, total_qi_sets=3, min_k=5
        )

        assert level == "medium"
        assert 0.3 <= score <= 0.6

    def test_calculate_risk_scores(self, engine):
        """Test risk score calculation for dataset."""
        df = pd.DataFrame({"age": [25, 25, 30], "zip": ["10001", "10001", "10002"]})

        qi_sets = [["age"], ["zip"], ["age", "zip"]]
        risk_scores = engine.calculate_risk_scores(df, qi_sets)

        assert len(risk_scores) == 3
        assert all(isinstance(rs, RiskScore) for rs in risk_scores)

    def test_risk_scores_have_required_fields(self, engine):
        """Test that risk scores have all required fields."""
        df = pd.DataFrame({"age": [25, 30], "zip": ["10001", "10002"]})

        qi_sets = [["age", "zip"]]
        risk_scores = engine.calculate_risk_scores(df, qi_sets)

        for rs in risk_scores:
            assert hasattr(rs, "record_index")
            assert hasattr(rs, "risk_level")
            assert hasattr(rs, "risk_score")
            assert hasattr(rs, "unique_on_qi_count")
            assert hasattr(rs, "k_anonymity")
            assert hasattr(rs, "reasoning")


class TestRiskReport:
    """Test risk report generation."""

    @pytest.fixture
    def engine(self):
        """Create risk assessment engine."""
        return RiskAssessmentEngine()

    @pytest.fixture
    def sample_risk_scores(self):
        """Create sample risk scores."""
        return [
            RiskScore(0, "high", 0.95, 2, 1, "High risk"),
            RiskScore(1, "high", 0.92, 2, 1, "High risk"),
            RiskScore(2, "medium", 0.6, 1, 3, "Medium risk"),
            RiskScore(3, "medium", 0.55, 1, 4, "Medium risk"),
            RiskScore(4, "low", 0.2, 0, 15, "Low risk"),
            RiskScore(5, "low", 0.15, 0, 20, "Low risk"),
            RiskScore(6, "low", 0.18, 0, 18, "Low risk"),
        ]

    def test_generate_risk_report_counts(self, engine, sample_risk_scores):
        """Test risk report counts are correct."""
        df = pd.DataFrame({"dummy": range(7)})
        report = engine.generate_risk_report(df, sample_risk_scores)

        assert report.total_records == 7
        assert report.high_risk_count == 2
        assert report.medium_risk_count == 2
        assert report.low_risk_count == 3

    def test_generate_risk_report_percentages(self, engine, sample_risk_scores):
        """Test risk report percentages are calculated correctly."""
        df = pd.DataFrame({"dummy": range(7)})
        report = engine.generate_risk_report(df, sample_risk_scores)

        # Check percentages add up to ~100%
        total_pct = (
            report.high_risk_percentage
            + report.medium_risk_percentage
            + report.low_risk_percentage
        )

        assert abs(total_pct - 100.0) < 0.1  # Allow for rounding

    def test_generate_risk_report_k_anonymity_stats(self, engine, sample_risk_scores):
        """Test k-anonymity statistics in report."""
        df = pd.DataFrame({"dummy": range(7)})
        report = engine.generate_risk_report(df, sample_risk_scores)

        assert report.min_k_anonymity == 1  # Minimum from sample
        assert report.average_k_anonymity > 0

    def test_generate_risk_report_categorization(self, engine, sample_risk_scores):
        """Test record categorization in report."""
        df = pd.DataFrame({"dummy": range(7)})
        report = engine.generate_risk_report(df, sample_risk_scores)

        # Records with k=1
        assert len(report.unique_records) == 2
        assert 0 in report.unique_records
        assert 1 in report.unique_records

        # Records with k>10
        assert len(report.safe_records) == 3

    def test_assess_dataset_integration(self, engine):
        """Test complete dataset assessment."""
        df = pd.DataFrame(
            {
                "age": [25, 25, 30, 30, 35],
                "zip": ["10001", "10001", "10002", "10002", "10003"],
            }
        )

        qi_sets = [["age"], ["zip"], ["age", "zip"]]
        risk_scores, risk_report = engine.assess_dataset(df, qi_sets)

        assert len(risk_scores) == 5
        assert isinstance(risk_report, RiskReport)
        assert risk_report.total_records == 5


class TestHighRiskRecords:
    """Test high-risk record retrieval."""

    @pytest.fixture
    def engine(self):
        """Create risk assessment engine."""
        return RiskAssessmentEngine()

    def test_get_high_risk_records(self, engine):
        """Test retrieval of high-risk records."""
        df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"], "age": [25, 30, 35]})

        risk_scores = [
            RiskScore(0, "high", 0.95, 2, 1, "Very high risk"),
            RiskScore(1, "medium", 0.6, 1, 3, "Medium risk"),
            RiskScore(2, "high", 0.92, 2, 1, "High risk"),
        ]

        high_risk_df = engine.get_high_risk_records(df, risk_scores, limit=5)

        # Should return 2 high-risk records
        assert len(high_risk_df) == 2
        assert "risk_score" in high_risk_df.columns
        assert "risk_reasoning" in high_risk_df.columns

    def test_get_high_risk_records_sorted(self, engine):
        """Test that high-risk records are sorted by risk score."""
        df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"], "age": [25, 30, 35]})

        risk_scores = [
            RiskScore(0, "high", 0.90, 2, 1, "High risk"),
            RiskScore(1, "high", 0.95, 2, 1, "Very high risk"),
            RiskScore(2, "high", 0.85, 2, 1, "High risk"),
        ]

        high_risk_df = engine.get_high_risk_records(df, risk_scores, limit=5)

        # First record should have highest risk score
        assert high_risk_df.iloc[0]["risk_score"] == 0.95

    def test_get_high_risk_records_limit(self, engine):
        """Test limit parameter works correctly."""
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Carol", "Dave", "Eve"],
                "age": [25, 30, 35, 40, 45],
            }
        )

        risk_scores = [
            RiskScore(i, "high", 0.9 - i * 0.01, 2, 1, "High risk") for i in range(5)
        ]

        high_risk_df = engine.get_high_risk_records(df, risk_scores, limit=3)

        # Should return only 3 records
        assert len(high_risk_df) == 3


class TestQuasiIdentifierInference:
    """Test quasi-identifier inference."""

    def test_infer_qi_from_column_names(self):
        """Test QI inference from column names."""
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob"],
                "age": [25, 30],
                "zipcode": ["10001", "10002"],
                "email": ["a@ex.com", "b@ex.com"],
            }
        )

        pii_results = {}
        qi = infer_quasi_identifiers(df, pii_results)

        assert "age" in qi
        assert "zipcode" in qi

    def test_infer_qi_excludes_non_qi_columns(self):
        """Test that non-QI columns are excluded."""
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob"],
                "email": ["a@ex.com", "b@ex.com"],
                "description": ["text", "more text"],
            }
        )

        pii_results = {}
        qi = infer_quasi_identifiers(df, pii_results)

        # Should not include name, email, or description
        assert "name" not in qi or "email" not in qi

    def test_infer_qi_with_pii_results(self):
        """Test QI inference using PII detection results."""
        from src.scanner import PIIDetectionResult

        df = pd.DataFrame(
            {"city": ["New York", "Boston"], "company": ["Acme", "TechCorp"]}
        )

        pii_results = {
            "city": PIIDetectionResult("city", ["location"], 0.9, [], 10),
            "company": PIIDetectionResult("company", ["organization"], 0.8, [], 8),
        }

        qi = infer_quasi_identifiers(df, pii_results)

        assert "city" in qi
        assert "company" in qi


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
