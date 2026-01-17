"""
Utility Metrics Module

Measures how well anonymization preserves data utility through:
- Distribution preservation (histograms, KS test)
- Correlation preservation
- Information loss (unique values, entropy)

Provides quantifiable metrics for the privacy/utility tradeoff.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
import warnings

# Import scipy for statistical analysis
try:
    from scipy import stats  # type: ignore
    from scipy.spatial.distance import correlation as correlation_distance  # type: ignore
except ImportError:
    stats = None
    correlation_distance = None


class UtilityMetricsError(Exception):
    """Custom exception for utility metrics errors."""

    pass


@dataclass
class DistributionMetrics:
    """Metrics for distribution preservation."""

    ks_statistic: float
    ks_pvalue: float
    mean_absolute_diff: float
    median_absolute_diff: float
    std_ratio: float
    interpretation: str

    def __post_init__(self):
        """Add interpretation based on metrics."""
        if self.ks_statistic < 0.1:
            self.interpretation = "Excellent preservation (>90%)"
        elif self.ks_statistic < 0.2:
            self.interpretation = "Good preservation (80-90%)"
        elif self.ks_statistic < 0.3:
            self.interpretation = "Moderate preservation (70-80%)"
        else:
            self.interpretation = "Poor preservation (<70%)"


@dataclass
class CorrelationMetrics:
    """Metrics for correlation preservation."""

    correlation_distance: float
    correlation_similarity: float  # 1 - distance
    mean_absolute_difference: float
    max_absolute_difference: float
    interpretation: str

    def __post_init__(self):
        """Add interpretation based on metrics."""
        if self.correlation_similarity > 0.9:
            self.interpretation = "Excellent preservation (>90%)"
        elif self.correlation_similarity > 0.8:
            self.interpretation = "Good preservation (80-90%)"
        elif self.correlation_similarity > 0.7:
            self.interpretation = "Moderate preservation (70-80%)"
        else:
            self.interpretation = "Poor preservation (<70%)"


@dataclass
class InformationLossMetrics:
    """Metrics for information loss."""

    unique_values_original: int
    unique_values_anonymized: int
    unique_values_retained_pct: float
    entropy_original: float
    entropy_anonymized: float
    entropy_retained_pct: float
    interpretation: str

    def __post_init__(self):
        """Add interpretation based on metrics."""
        avg_retention = (
            self.unique_values_retained_pct + self.entropy_retained_pct
        ) / 2

        if avg_retention > 90:
            self.interpretation = "Minimal information loss (<10%)"
        elif avg_retention > 75:
            self.interpretation = "Low information loss (10-25%)"
        elif avg_retention > 50:
            self.interpretation = "Moderate information loss (25-50%)"
        else:
            self.interpretation = "High information loss (>50%)"


@dataclass
class UtilityReport:
    """Comprehensive utility metrics report."""

    overall_utility_score: float
    distribution_metrics: Dict[str, DistributionMetrics] = field(default_factory=dict)
    correlation_metrics: Optional[CorrelationMetrics] = None
    information_loss_metrics: Dict[str, InformationLossMetrics] = field(
        default_factory=dict
    )
    column_level_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            "=" * 60,
            "UTILITY METRICS REPORT",
            "=" * 60,
            f"\nOverall Utility Score: {self.overall_utility_score:.1f}%",
            f"\nInterpretation: {self._get_overall_interpretation()}",
        ]

        if self.distribution_metrics:
            lines.append("\n--- Distribution Preservation ---")
            for col, metrics in self.distribution_metrics.items():
                lines.append(f"  {col}: {metrics.interpretation}")

        if self.correlation_metrics:
            lines.append("\n--- Correlation Preservation ---")
            lines.append(f"  {self.correlation_metrics.interpretation}")

        if self.information_loss_metrics:
            lines.append("\n--- Information Loss ---")
            for col, metrics in self.information_loss_metrics.items():
                lines.append(f"  {col}: {metrics.interpretation}")

        if self.recommendations:
            lines.append("\n--- Recommendations ---")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"  {i}. {rec}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def _get_overall_interpretation(self) -> str:
        """Get interpretation of overall score."""
        score = self.overall_utility_score

        if score >= 90:
            return "Excellent - Data highly useful for analysis"
        elif score >= 80:
            return "Good - Data suitable for most analyses"
        elif score >= 70:
            return "Moderate - Data has some limitations"
        elif score >= 60:
            return "Fair - Data utility significantly reduced"
        else:
            return "Poor - Consider less aggressive anonymization"


class UtilityMetrics:
    """
    Calculate utility preservation metrics for anonymized data.

    Follows Single Responsibility Principle: only measures utility,
    doesn't perform anonymization.
    """

    def __init__(self, original_df: pd.DataFrame, anonymized_df: pd.DataFrame):
        """
        Initialize utility metrics calculator.

        Args:
            original_df: Original DataFrame before anonymization
            anonymized_df: DataFrame after anonymization

        Raises:
            UtilityMetricsError: If DataFrames incompatible
        """
        # Validate inputs
        self._validate_dataframes(original_df, anonymized_df)

        self.original = original_df
        self.anonymized = anonymized_df

        # Identify numeric columns (for distribution/correlation analysis)
        self.numeric_cols = self._get_numeric_columns()

    def _validate_dataframes(
        self, original: pd.DataFrame, anonymized: pd.DataFrame
    ) -> None:
        """Validate that DataFrames are compatible."""
        if original.shape != anonymized.shape:
            raise UtilityMetricsError(
                f"DataFrames have different shapes: "
                f"{original.shape} vs {anonymized.shape}"
            )

        if list(original.columns) != list(anonymized.columns):
            raise UtilityMetricsError("DataFrames have different columns")

    def _get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns from original data."""
        numeric_cols = []

        for col in self.original.columns:
            if pd.api.types.is_numeric_dtype(self.original[col]):
                numeric_cols.append(col)

        return numeric_cols

    @staticmethod
    def _parse_generalized_range(value: Any) -> Optional[float]:
        """
        Parse a generalized range string to extract numeric value.

        Handles formats like:
        - "45-49" -> 47.0 (midpoint)
        - "90000-94999" -> 92499.5 (midpoint)
        - "45" -> 45.0 (single value)
        - Already numeric -> return as-is

        Args:
            value: Value to parse (string range or numeric)

        Returns:
            Numeric value (float) or None if cannot parse
        """
        # If already numeric, return as-is
        if pd.api.types.is_number(value) and not pd.isna(value):
            return float(value)

        # If NaN, return None
        if pd.isna(value):
            return None

        # Convert to string for parsing
        str_value = str(value).strip()

        # Try to parse as range (e.g., "45-49", "90000-94999")
        if "-" in str_value:
            try:
                parts = str_value.split("-")
                if len(parts) == 2:
                    start = float(parts[0].strip())
                    end = float(parts[1].strip())
                    # Return midpoint
                    return (start + end) / 2.0
            except (ValueError, AttributeError):
                pass

        # Try to parse as single number
        try:
            return float(str_value)
        except (ValueError, AttributeError):
            return None

    def _convert_to_numeric_with_ranges(
        self, series: pd.Series, column_name: str
    ) -> pd.Series:
        """
        Convert series to numeric, handling generalized ranges.

        Args:
            series: Series to convert
            column_name: Column name (for error messages)

        Returns:
            Series with numeric values (NaN for unparseable values)
        """
        # First try standard numeric conversion
        numeric_series = pd.to_numeric(series, errors="coerce")

        # For any values that failed conversion, try parsing as ranges
        # This handles cases where anonymization generalized numeric values to ranges
        nan_mask = numeric_series.isna()
        if nan_mask.any():
            # Apply range parsing to values that failed numeric conversion
            parsed_values = series[nan_mask].apply(self._parse_generalized_range)
            # Use parsed values where original conversion failed
            numeric_series = numeric_series.fillna(parsed_values)

        return numeric_series

    def calculate_distribution_preservation(self, column: str) -> DistributionMetrics:
        """
        Calculate distribution preservation metrics for a column.

        Args:
            column: Column name to analyze

        Returns:
            DistributionMetrics object

        Raises:
            UtilityMetricsError: If column not numeric
        """
        if stats is None:
            raise UtilityMetricsError(
                "scipy library required for distribution analysis. "
                "Install with: pip install scipy"
            )

        if column not in self.original.columns:
            raise UtilityMetricsError(f"Column '{column}' not found")

        # Get data, removing NaNs
        original_data = self.original[column].dropna()
        anonymized_data = self.anonymized[column].dropna()

        # Check if numeric, handling generalized ranges
        try:
            original_numeric = pd.to_numeric(original_data, errors="coerce").dropna()
            # Use range parsing for anonymized data (may contain generalized ranges)
            anonymized_numeric = self._convert_to_numeric_with_ranges(
                anonymized_data, column
            ).dropna()
        except Exception as e:
            raise UtilityMetricsError(
                f"Column '{column}' cannot be converted to numeric: {e}"
            )

        if len(original_numeric) == 0 or len(anonymized_numeric) == 0:
            raise UtilityMetricsError(f"Column '{column}' has no valid numeric values")

        # Kolmogorov-Smirnov test
        ks_stat, ks_pval = stats.ks_2samp(original_numeric, anonymized_numeric)

        # Mean and median differences
        mean_diff = abs(original_numeric.mean() - anonymized_numeric.mean())
        median_diff = abs(original_numeric.median() - anonymized_numeric.median())

        # Standard deviation ratio
        original_std = original_numeric.std()
        anonymized_std = anonymized_numeric.std()
        std_ratio = anonymized_std / original_std if original_std > 0 else 1.0

        return DistributionMetrics(
            ks_statistic=ks_stat,
            ks_pvalue=ks_pval,
            mean_absolute_diff=mean_diff,
            median_absolute_diff=median_diff,
            std_ratio=std_ratio,
            interpretation="",  # Set in __post_init__
        )

    def calculate_correlation_preservation(self) -> CorrelationMetrics:
        """
        Calculate correlation matrix preservation.

        Returns:
            CorrelationMetrics object

        Raises:
            UtilityMetricsError: If not enough numeric columns
        """
        if correlation_distance is None:
            raise UtilityMetricsError(
                "scipy library required for correlation analysis. "
                "Install with: pip install scipy"
            )

        if len(self.numeric_cols) < 2:
            raise UtilityMetricsError(
                "Need at least 2 numeric columns for correlation analysis"
            )

        # Calculate correlation matrices
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            original_corr = self.original[self.numeric_cols].corr()

            # Handle anonymized data that might be strings or generalized ranges
            anonymized_numeric = self.anonymized[self.numeric_cols].copy()
            for col in self.numeric_cols:
                anonymized_numeric[col] = self._convert_to_numeric_with_ranges(
                    anonymized_numeric[col], col
                )

            anonymized_corr = anonymized_numeric.corr()

        # Flatten correlation matrices (excluding diagonal)
        mask = np.triu(np.ones_like(original_corr, dtype=bool), k=1)
        original_flat = original_corr.values[mask]
        anonymized_flat = anonymized_corr.values[mask]

        # Remove NaN values
        valid_mask = ~(np.isnan(original_flat) | np.isnan(anonymized_flat))
        original_flat = original_flat[valid_mask]
        anonymized_flat = anonymized_flat[valid_mask]

        if len(original_flat) == 0:
            raise UtilityMetricsError("No valid correlations to compare")

        # Calculate correlation distance with warning suppression
        # Handle edge case: identical vectors return NaN, should be 0 distance
        # Suppress RuntimeWarnings from scipy when encountering edge cases (zero variance, etc.)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                corr_dist = correlation_distance(original_flat, anonymized_flat)
                if np.isnan(corr_dist):
                    # Vectors are identical (perfect correlation preservation)
                    corr_dist = 0.0
            except (ValueError, ZeroDivisionError):
                # Handle edge case where std dev is zero or other numerical issues
                # Check if vectors are identical
                if np.allclose(original_flat, anonymized_flat):
                    corr_dist = 0.0
                else:
                    # Can't compute correlation distance, assume maximum distance
                    corr_dist = 1.0

        corr_similarity = 1 - corr_dist

        # Mean and max absolute differences
        abs_diffs = np.abs(original_flat - anonymized_flat)
        mean_abs_diff = np.mean(abs_diffs)
        max_abs_diff = np.max(abs_diffs)

        return CorrelationMetrics(
            correlation_distance=corr_dist,
            correlation_similarity=corr_similarity,
            mean_absolute_difference=mean_abs_diff,
            max_absolute_difference=max_abs_diff,
            interpretation="",  # Set in __post_init__
        )

    def calculate_information_loss(self, column: str) -> InformationLossMetrics:
        """
        Calculate information loss metrics for a column.

        Args:
            column: Column name to analyze

        Returns:
            InformationLossMetrics object
        """
        if column not in self.original.columns:
            raise UtilityMetricsError(f"Column '{column}' not found")

        original_data = self.original[column].dropna()
        anonymized_data = self.anonymized[column].dropna()

        # Count unique values
        unique_original = original_data.nunique()
        unique_anonymized = anonymized_data.nunique()

        unique_retained_pct = (
            (unique_anonymized / unique_original * 100)
            if unique_original > 0
            else 100.0
        )

        # Calculate entropy
        entropy_original = self._calculate_entropy(original_data)
        entropy_anonymized = self._calculate_entropy(anonymized_data)

        entropy_retained_pct = (
            (entropy_anonymized / entropy_original * 100)
            if entropy_original > 0
            else 100.0
        )

        return InformationLossMetrics(
            unique_values_original=unique_original,
            unique_values_anonymized=unique_anonymized,
            unique_values_retained_pct=unique_retained_pct,
            entropy_original=entropy_original,
            entropy_anonymized=entropy_anonymized,
            entropy_retained_pct=entropy_retained_pct,
            interpretation="",  # Set in __post_init__
        )

    @staticmethod
    def _calculate_entropy(series: pd.Series) -> float:
        """
        Calculate Shannon entropy of a series.

        Args:
            series: Data series

        Returns:
            Entropy value
        """
        value_counts = series.value_counts()
        probabilities = value_counts / len(series)

        # Shannon entropy: -sum(p * log2(p))
        # Use where() to avoid log of zero without offset that causes precision issues
        entropy = -np.sum(
            np.where(probabilities > 0, probabilities * np.log2(probabilities), 0)
        )

        # Handle floating point precision: return exactly 0 for near-zero values
        if abs(entropy) < 1e-9:
            return 0.0

        return entropy

    def generate_report(
        self, columns_to_analyze: Optional[List[str]] = None
    ) -> UtilityReport:
        """
        Generate comprehensive utility report.

        Args:
            columns_to_analyze: List of columns to analyze.
                               If None, analyzes all columns.

        Returns:
            UtilityReport object
        """
        if columns_to_analyze is None:
            columns_to_analyze = list(self.original.columns)

        report = UtilityReport(overall_utility_score=0.0)

        # Calculate distribution preservation for numeric columns
        for col in columns_to_analyze:
            if col in self.numeric_cols:
                try:
                    metrics = self.calculate_distribution_preservation(col)
                    report.distribution_metrics[col] = metrics
                except Exception:
                    pass  # Skip columns that can't be analyzed

        # Calculate correlation preservation
        if len(self.numeric_cols) >= 2:
            try:
                corr_metrics = self.calculate_correlation_preservation()
                report.correlation_metrics = corr_metrics
            except Exception:
                pass  # Skip if correlation can't be calculated

        # Calculate information loss for all columns
        for col in columns_to_analyze:
            try:
                info_metrics = self.calculate_information_loss(col)
                report.information_loss_metrics[col] = info_metrics
            except Exception:
                pass  # Skip columns that can't be analyzed

        # Calculate overall utility score
        scores = []

        # Distribution scores (based on KS statistic)
        for metrics in report.distribution_metrics.values():
            score = max(0, 100 * (1 - metrics.ks_statistic))
            scores.append(score)

        # Correlation score
        if report.correlation_metrics:
            score = report.correlation_metrics.correlation_similarity * 100
            scores.append(score)

        # Information retention scores
        for metrics in report.information_loss_metrics.values():
            avg_retention = (
                metrics.unique_values_retained_pct + metrics.entropy_retained_pct
            ) / 2
            scores.append(avg_retention)

        # Overall score
        report.overall_utility_score = np.mean(scores) if scores else 0.0

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: UtilityReport) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []

        if report.overall_utility_score < 70:
            recommendations.append(
                "Consider using less aggressive anonymization strategies"
            )

        # Check distribution preservation
        poor_dist_cols = [
            col
            for col, metrics in report.distribution_metrics.items()
            if metrics.ks_statistic > 0.3
        ]
        if poor_dist_cols:
            recommendations.append(
                f"Improve distribution preservation for: {', '.join(poor_dist_cols)}"
            )

        # Check correlation preservation
        if report.correlation_metrics:
            if report.correlation_metrics.correlation_similarity < 0.7:
                recommendations.append(
                    "Consider preserving more precise numeric values to maintain correlations"
                )

        # Check information loss
        high_loss_cols = [
            col
            for col, metrics in report.information_loss_metrics.items()
            if metrics.unique_values_retained_pct < 50
        ]
        if high_loss_cols:
            recommendations.append(
                f"High information loss in: {', '.join(high_loss_cols)}"
            )

        if not recommendations:
            recommendations.append(
                "Anonymization provides good balance of privacy and utility"
            )

        return recommendations


# Convenience function
def compare_utility(
    original_df: pd.DataFrame,
    anonymized_df: pd.DataFrame,
    columns: Optional[List[str]] = None,
) -> UtilityReport:
    """
    Convenience function to compare utility of anonymized data.

    Args:
        original_df: Original DataFrame
        anonymized_df: Anonymized DataFrame
        columns: Optional list of columns to analyze

    Returns:
        UtilityReport object

    Example:
        >>> report = compare_utility(original, anonymized)
        >>> print(report.get_summary())
    """
    metrics = UtilityMetrics(original_df, anonymized_df)
    return metrics.generate_report(columns)


# Example usage
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    n = 1000

    original = pd.DataFrame(
        {
            "age": np.random.normal(40, 15, n),
            "income": np.random.normal(50000, 20000, n),
            "score": np.random.normal(75, 10, n),
        }
    )

    # Simulate anonymization (generalization)
    anonymized = original.copy()
    anonymized["age"] = (
        (anonymized["age"] // 10 * 10).astype(str)
        + "-"
        + ((anonymized["age"] // 10 * 10) + 9).astype(str)
    )
    anonymized["income"] = (anonymized["income"] // 10000 * 10000).astype(int)

    print("Calculating utility metrics...")
    print()

    # Generate report
    try:
        report = compare_utility(original, anonymized)
        print(report.get_summary())

    except Exception as e:
        print(f"Error: {e}")
