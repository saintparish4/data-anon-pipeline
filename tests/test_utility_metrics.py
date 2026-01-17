"""
Unit tests for the utility_metrics module.

Tests cover:
- Distribution preservation metrics
- Correlation preservation metrics
- Information loss metrics
- Report generation
- Error handling
"""

import pytest
import pandas as pd
import numpy as np
from scipy import stats  # type: ignore

from src.utility_metrics import (
    UtilityMetrics,
    UtilityMetricsError,
    DistributionMetrics,
    CorrelationMetrics,
    InformationLossMetrics,
    UtilityReport,
    compare_utility,
)


class TestDistributionMetrics:
    """Test distribution metrics dataclass."""

    def test_distribution_metrics_excellent(self):
        """Test interpretation for excellent preservation."""
        metrics = DistributionMetrics(
            ks_statistic=0.05,
            ks_pvalue=0.9,
            mean_absolute_diff=1.0,
            median_absolute_diff=0.5,
            std_ratio=0.98,
            interpretation="",
        )

        assert "Excellent" in metrics.interpretation
        assert ">90%" in metrics.interpretation

    def test_distribution_metrics_poor(self):
        """Test interpretation for poor preservation."""
        metrics = DistributionMetrics(
            ks_statistic=0.4,
            ks_pvalue=0.01,
            mean_absolute_diff=10.0,
            median_absolute_diff=8.0,
            std_ratio=0.5,
            interpretation="",
        )

        assert "Poor" in metrics.interpretation


class TestCorrelationMetrics:
    """Test correlation metrics dataclass."""

    def test_correlation_metrics_excellent(self):
        """Test interpretation for excellent correlation preservation."""
        metrics = CorrelationMetrics(
            correlation_distance=0.05,
            correlation_similarity=0.95,
            mean_absolute_difference=0.02,
            max_absolute_difference=0.05,
            interpretation="",
        )

        assert "Excellent" in metrics.interpretation

    def test_correlation_metrics_poor(self):
        """Test interpretation for poor correlation preservation."""
        metrics = CorrelationMetrics(
            correlation_distance=0.5,
            correlation_similarity=0.5,
            mean_absolute_difference=0.2,
            max_absolute_difference=0.4,
            interpretation="",
        )

        assert "Poor" in metrics.interpretation


class TestInformationLossMetrics:
    """Test information loss metrics dataclass."""

    def test_information_loss_minimal(self):
        """Test interpretation for minimal information loss."""
        metrics = InformationLossMetrics(
            unique_values_original=100,
            unique_values_anonymized=95,
            unique_values_retained_pct=95.0,
            entropy_original=6.0,
            entropy_anonymized=5.8,
            entropy_retained_pct=96.7,
            interpretation="",
        )

        assert "Minimal" in metrics.interpretation

    def test_information_loss_high(self):
        """Test interpretation for high information loss."""
        metrics = InformationLossMetrics(
            unique_values_original=100,
            unique_values_anonymized=20,
            unique_values_retained_pct=20.0,
            entropy_original=6.0,
            entropy_anonymized=2.0,
            entropy_retained_pct=33.3,
            interpretation="",
        )

        assert "High" in metrics.interpretation


class TestUtilityMetricsInitialization:
    """Test UtilityMetrics initialization."""

    def test_initialization_with_valid_dataframes(self):
        """Test initialization with compatible DataFrames."""
        df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df2 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        metrics = UtilityMetrics(df1, df2)

        assert metrics.original.equals(df1)
        assert metrics.anonymized.equals(df2)

    def test_initialization_different_shapes_raises_error(self):
        """Test error when DataFrames have different shapes."""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2]})  # Different length

        with pytest.raises(UtilityMetricsError, match="different shapes"):
            UtilityMetrics(df1, df2)

    def test_initialization_different_columns_raises_error(self):
        """Test error when DataFrames have different columns."""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"b": [1, 2, 3]})  # Different column name

        with pytest.raises(UtilityMetricsError, match="different columns"):
            UtilityMetrics(df1, df2)

    def test_numeric_columns_identified(self):
        """Test that numeric columns are correctly identified."""
        df = pd.DataFrame(
            {
                "numeric1": [1, 2, 3],
                "numeric2": [4.0, 5.0, 6.0],
                "string": ["a", "b", "c"],
            }
        )

        metrics = UtilityMetrics(df, df)

        assert "numeric1" in metrics.numeric_cols
        assert "numeric2" in metrics.numeric_cols
        assert "string" not in metrics.numeric_cols


class TestDistributionPreservation:
    """Test distribution preservation metrics."""

    def test_identical_distributions(self):
        """Test metrics for identical distributions."""
        df1 = pd.DataFrame({"age": [20, 30, 40, 50, 60]})
        df2 = df1.copy()

        metrics = UtilityMetrics(df1, df2)
        dist_metrics = metrics.calculate_distribution_preservation("age")

        assert dist_metrics.ks_statistic == 0.0  # Perfect match
        assert dist_metrics.mean_absolute_diff == 0.0
        assert dist_metrics.median_absolute_diff == 0.0

    def test_similar_distributions(self):
        """Test metrics for similar distributions."""
        np.random.seed(42)
        df1 = pd.DataFrame({"age": np.random.normal(40, 10, 100)})
        df2 = pd.DataFrame({"age": np.random.normal(40, 10, 100)})

        metrics = UtilityMetrics(df1, df2)
        dist_metrics = metrics.calculate_distribution_preservation("age")

        # Should be similar (low KS statistic)
        assert dist_metrics.ks_statistic < 0.3
        assert (
            "Excellent" in dist_metrics.interpretation
            or "Good" in dist_metrics.interpretation
        )

    def test_different_distributions(self):
        """Test metrics for very different distributions."""
        df1 = pd.DataFrame({"age": [20, 30, 40, 50, 60]})
        df2 = pd.DataFrame({"age": [100, 110, 120, 130, 140]})

        metrics = UtilityMetrics(df1, df2)
        dist_metrics = metrics.calculate_distribution_preservation("age")

        # Should be very different (high KS statistic)
        assert dist_metrics.ks_statistic > 0.5
        assert dist_metrics.mean_absolute_diff > 50

    def test_distribution_with_missing_values(self):
        """Test handling of missing values in distribution analysis."""
        df1 = pd.DataFrame({"age": [20, 30, np.nan, 50, 60]})
        df2 = pd.DataFrame({"age": [21, 31, np.nan, 51, 61]})

        metrics = UtilityMetrics(df1, df2)
        dist_metrics = metrics.calculate_distribution_preservation("age")

        # Should handle NaN gracefully
        assert not np.isnan(dist_metrics.ks_statistic)

    def test_distribution_nonexistent_column(self):
        """Test error for nonexistent column."""
        df = pd.DataFrame({"age": [20, 30, 40]})

        metrics = UtilityMetrics(df, df)

        with pytest.raises(UtilityMetricsError, match="not found"):
            metrics.calculate_distribution_preservation("nonexistent")

    def test_distribution_non_numeric_column(self):
        """Test error for non-numeric column."""
        df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})

        metrics = UtilityMetrics(df, df)

        with pytest.raises(UtilityMetricsError):
            metrics.calculate_distribution_preservation("name")


class TestCorrelationPreservation:
    """Test correlation preservation metrics."""

    def test_identical_correlations(self):
        """Test metrics for identical correlations."""
        np.random.seed(42)
        df = pd.DataFrame(
            {"a": np.random.normal(0, 1, 100), "b": np.random.normal(0, 1, 100)}
        )

        metrics = UtilityMetrics(df, df)
        corr_metrics = metrics.calculate_correlation_preservation()

        assert corr_metrics.correlation_distance < 0.01  # Nearly 0
        assert corr_metrics.correlation_similarity > 0.99

    def test_preserved_correlations(self):
        """Test correlation preservation with slight changes."""
        np.random.seed(42)
        n = 100

        # Create correlated data
        x = np.random.normal(0, 1, n)
        y = x + np.random.normal(0, 0.1, n)  # Highly correlated

        df1 = pd.DataFrame({"a": x, "b": y})

        # Add small noise
        df2 = pd.DataFrame(
            {
                "a": x + np.random.normal(0, 0.05, n),
                "b": y + np.random.normal(0, 0.05, n),
            }
        )

        metrics = UtilityMetrics(df1, df2)
        corr_metrics = metrics.calculate_correlation_preservation()

        # Should be well preserved
        assert corr_metrics.correlation_similarity > 0.8

    def test_correlation_with_single_column(self):
        """Test error with only one numeric column."""
        df = pd.DataFrame({"a": [1, 2, 3]})

        metrics = UtilityMetrics(df, df)

        with pytest.raises(UtilityMetricsError, match="at least 2 numeric"):
            metrics.calculate_correlation_preservation()

    def test_correlation_with_string_columns(self):
        """Test correlation with mixed types."""
        df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": ["x", "y", "z"]})
        df2 = df1.copy()

        metrics = UtilityMetrics(df1, df2)

        # Should only use numeric columns
        corr_metrics = metrics.calculate_correlation_preservation()

        assert corr_metrics is not None


class TestInformationLoss:
    """Test information loss metrics."""

    def test_no_information_loss(self):
        """Test when no information is lost."""
        df = pd.DataFrame({"color": ["red", "blue", "green", "red", "blue"]})

        metrics = UtilityMetrics(df, df)
        info_metrics = metrics.calculate_information_loss("color")

        assert info_metrics.unique_values_original == 3
        assert info_metrics.unique_values_anonymized == 3
        assert info_metrics.unique_values_retained_pct == 100.0
        assert info_metrics.entropy_retained_pct == 100.0

    def test_partial_information_loss(self):
        """Test partial information loss."""
        df1 = pd.DataFrame({"color": ["red", "blue", "green", "yellow", "orange"]})
        df2 = pd.DataFrame(
            {"color": ["red", "red", "blue", "blue", "blue"]}
        )  # Less variety

        metrics = UtilityMetrics(df1, df2)
        info_metrics = metrics.calculate_information_loss("color")

        assert info_metrics.unique_values_original == 5
        assert info_metrics.unique_values_anonymized == 2
        assert info_metrics.unique_values_retained_pct == 40.0
        assert info_metrics.entropy_anonymized < info_metrics.entropy_original

    def test_complete_information_loss(self):
        """Test complete information loss."""
        df1 = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
        df2 = pd.DataFrame({"value": [0, 0, 0, 0, 0]})  # All same

        metrics = UtilityMetrics(df1, df2)
        info_metrics = metrics.calculate_information_loss("value")

        assert info_metrics.unique_values_anonymized == 1
        assert info_metrics.entropy_anonymized == 0.0  # No entropy

    def test_information_loss_with_missing_values(self):
        """Test information loss with NaN values."""
        df1 = pd.DataFrame({"value": [1, 2, np.nan, 4, 5]})
        df2 = pd.DataFrame({"value": [1, 1, np.nan, 1, 1]})

        metrics = UtilityMetrics(df1, df2)
        info_metrics = metrics.calculate_information_loss("value")

        # Should handle NaN gracefully
        assert info_metrics.unique_values_original > 0

    def test_entropy_calculation(self):
        """Test entropy calculation directly."""
        # Uniform distribution (max entropy)
        series1 = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
        entropy1 = UtilityMetrics._calculate_entropy(series1)

        # Skewed distribution (lower entropy)
        series2 = pd.Series([1, 1, 1, 1, 1, 1, 1, 2])
        entropy2 = UtilityMetrics._calculate_entropy(series2)

        assert entropy1 > entropy2


class TestReportGeneration:
    """Test comprehensive report generation."""

    def test_generate_report_basic(self):
        """Test basic report generation."""
        np.random.seed(42)
        df1 = pd.DataFrame(
            {
                "age": np.random.normal(40, 10, 100),
                "income": np.random.normal(50000, 15000, 100),
            }
        )
        df2 = df1.copy()  # Identical

        metrics = UtilityMetrics(df1, df2)
        report = metrics.generate_report()

        assert report.overall_utility_score > 90  # Should be excellent
        assert len(report.distribution_metrics) > 0
        assert report.correlation_metrics is not None
        assert len(report.information_loss_metrics) > 0

    def test_generate_report_with_column_selection(self):
        """Test report with specific columns."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": ["x", "y", "z"]})

        metrics = UtilityMetrics(df, df)
        report = metrics.generate_report(columns_to_analyze=["a", "b"])

        # Should only analyze selected columns
        assert "a" in report.information_loss_metrics
        assert "b" in report.information_loss_metrics

    def test_report_get_summary(self):
        """Test report summary generation."""
        df = pd.DataFrame({"age": [20, 30, 40]})

        metrics = UtilityMetrics(df, df)
        report = metrics.generate_report()

        summary = report.get_summary()

        assert "UTILITY METRICS REPORT" in summary
        assert "Overall Utility Score" in summary
        assert "%" in summary

    def test_report_with_poor_utility(self):
        """Test report generation with poor utility."""
        df1 = pd.DataFrame(
            {
                "age": [20, 30, 40, 50, 60],
                "income": [30000, 50000, 70000, 90000, 110000],
            }
        )
        df2 = pd.DataFrame(
            {
                "age": [100, 100, 100, 100, 100],  # All same
                "income": [0, 0, 0, 0, 0],  # All same
            }
        )

        metrics = UtilityMetrics(df1, df2)
        report = metrics.generate_report()

        assert report.overall_utility_score < 50  # Poor score
        assert len(report.recommendations) > 0

    def test_recommendations_generated(self):
        """Test that recommendations are generated."""
        df1 = pd.DataFrame({"age": [20, 30, 40, 50, 60]})
        df2 = pd.DataFrame({"age": [100, 100, 100, 100, 100]})

        metrics = UtilityMetrics(df1, df2)
        report = metrics.generate_report()

        assert len(report.recommendations) > 0
        # Should recommend less aggressive anonymization
        assert any("aggressive" in rec.lower() for rec in report.recommendations)


class TestConvenienceFunction:
    """Test convenience function."""

    def test_compare_utility_function(self):
        """Test compare_utility convenience function."""
        df1 = pd.DataFrame({"age": [20, 30, 40]})
        df2 = pd.DataFrame({"age": [21, 31, 41]})

        report = compare_utility(df1, df2)

        assert isinstance(report, UtilityReport)
        assert report.overall_utility_score > 0

    def test_compare_utility_with_columns(self):
        """Test compare_utility with specific columns."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        report = compare_utility(df, df, columns=["a"])

        assert "a" in report.information_loss_metrics


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_dataframes(self):
        """Test with empty DataFrames."""
        df = pd.DataFrame({"age": []})

        # Should initialize but might have issues with metrics
        metrics = UtilityMetrics(df, df)
        assert metrics is not None

    def test_single_value_column(self):
        """Test with column having single unique value."""
        df = pd.DataFrame({"value": [1, 1, 1, 1, 1]})

        metrics = UtilityMetrics(df, df)
        info_metrics = metrics.calculate_information_loss("value")

        assert info_metrics.unique_values_original == 1
        assert info_metrics.entropy_original == 0.0

    def test_all_nan_column(self):
        """Test with column that's all NaN."""
        df = pd.DataFrame({"value": [np.nan, np.nan, np.nan]})

        metrics = UtilityMetrics(df, df)

        # Should handle gracefully
        with pytest.raises(UtilityMetricsError):
            metrics.calculate_distribution_preservation("value")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
