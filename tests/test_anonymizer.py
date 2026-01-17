"""
Unit tests for the anonymizer module.

Tests cover:
- All 5 anonymization strategies
- DataFrame anonymization
- Error handling
- Data type preservation
- Missing value handling
- Statistics tracking
"""

import pytest
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path
import tempfile
import yaml  # type: ignore

from src.anonymizer import (
    Anonymizer,
    AnonymizationStrategies,
    AnonymizationError,
    anonymize,
)
from src.config_loader import load_config, ConfigLoader


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    config_dict = {
        "rules": {
            "email": {
                "strategy": "hash",
                "parameters": {"algorithm": "sha256", "salt": False},
            },
            "age": {
                "strategy": "generalize",
                "parameters": {"bin_size": 10, "min_value": 0, "max_value": 100},
            },
            "phone": {
                "strategy": "redact_partial",
                "parameters": {"visible_chars": 4, "mask_char": "*"},
            },
        },
        "global": {"handle_nulls": True, "preserve_data_types": True},
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_dict, f)
        config_path = Path(f.name)

    config = load_config(config_path)
    config_path.unlink()  # Clean up

    return config


class TestAnonymizationStrategies:
    """Test individual anonymization strategies."""

    def test_hash_strategy_sha256(self):
        """Test SHA256 hashing."""
        value = "test@example.com"
        params = {"algorithm": "sha256", "salt": False}

        result = AnonymizationStrategies.hash_strategy(value, params)

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length
        # Verify it's actually a hash of the value
        expected = hashlib.sha256(value.encode()).hexdigest()
        assert result == expected

    def test_hash_strategy_with_salt(self):
        """Test hashing with salt."""
        value = "test@example.com"
        params = {"algorithm": "sha256", "salt": True}

        result = AnonymizationStrategies.hash_strategy(value, params)

        # With salt, result should be different from simple hash
        simple_hash = hashlib.sha256(value.encode()).hexdigest()
        assert result != simple_hash

        # But should be consistent
        result2 = AnonymizationStrategies.hash_strategy(value, params)
        assert result == result2

    def test_hash_strategy_consistency(self):
        """Test that same value produces same hash."""
        value = "test@example.com"
        params = {"algorithm": "sha256", "salt": False}

        result1 = AnonymizationStrategies.hash_strategy(value, params)
        result2 = AnonymizationStrategies.hash_strategy(value, params)

        assert result1 == result2

    def test_hash_strategy_with_nan(self):
        """Test hash strategy preserves NaN."""
        params = {"algorithm": "sha256", "salt": False}

        result = AnonymizationStrategies.hash_strategy(np.nan, params)

        assert pd.isna(result)

    def test_redact_full_strategy(self):
        """Test full redaction."""
        value = "sensitive_data"
        params = {"replacement": "[REDACTED]"}

        result = AnonymizationStrategies.redact_full_strategy(value, params)

        assert result == "[REDACTED]"
        assert "sensitive" not in result

    def test_redact_full_with_nan(self):
        """Test full redaction preserves NaN."""
        params = {"replacement": "[REDACTED]"}

        result = AnonymizationStrategies.redact_full_strategy(np.nan, params)

        assert pd.isna(result)

    def test_redact_partial_strategy(self):
        """Test partial redaction."""
        value = "555-1234"
        params = {"visible_chars": 4, "mask_char": "*"}

        result = AnonymizationStrategies.redact_partial_strategy(value, params)

        assert result == "****1234"
        assert result.endswith("1234")
        assert result.count("*") == 4

    def test_redact_partial_zero_visible(self):
        """Test partial redaction with no visible chars."""
        value = "test"
        params = {"visible_chars": 0, "mask_char": "*"}

        result = AnonymizationStrategies.redact_partial_strategy(value, params)

        assert result == "****"

    def test_redact_partial_more_visible_than_length(self):
        """Test partial redaction when visible > length."""
        value = "hi"
        params = {"visible_chars": 10, "mask_char": "*"}

        result = AnonymizationStrategies.redact_partial_strategy(value, params)

        assert result == "hi"

    def test_pseudonymize_strategy_consistency(self):
        """Test pseudonymization is consistent."""
        value = "John Doe"
        params = {"seed_based": True, "locale": "en_US"}

        # Clear cache to ensure fresh start
        AnonymizationStrategies._pseudo_cache.clear()

        result1 = AnonymizationStrategies.pseudonymize_strategy(value, params)
        result2 = AnonymizationStrategies.pseudonymize_strategy(value, params)

        assert result1 == result2
        assert result1 != value

    def test_pseudonymize_different_values_different_results(self):
        """Test different values get different pseudonyms."""
        params = {"seed_based": True, "locale": "en_US"}

        # Clear cache
        AnonymizationStrategies._pseudo_cache.clear()

        result1 = AnonymizationStrategies.pseudonymize_strategy("John", params)
        result2 = AnonymizationStrategies.pseudonymize_strategy("Jane", params)

        assert result1 != result2

    def test_generalize_strategy(self):
        """Test generalization to ranges."""
        value = 34
        params = {"bin_size": 10, "min_value": 0, "max_value": 100}

        result = AnonymizationStrategies.generalize_strategy(value, params)

        assert result == "30-39"

    def test_generalize_strategy_edge_cases(self):
        """Test generalization edge cases."""
        params = {"bin_size": 10, "min_value": 0, "max_value": 100}

        # Minimum value
        result = AnonymizationStrategies.generalize_strategy(0, params)
        assert result == "0-9"

        # Maximum value
        result = AnonymizationStrategies.generalize_strategy(100, params)
        assert result == "91-100"

        # Value outside range (should clamp)
        result = AnonymizationStrategies.generalize_strategy(150, params)
        assert result == "91-100"

        result = AnonymizationStrategies.generalize_strategy(-10, params)
        assert result == "0-9"

    def test_generalize_with_nan(self):
        """Test generalization preserves NaN."""
        params = {"bin_size": 10, "min_value": 0, "max_value": 100}

        result = AnonymizationStrategies.generalize_strategy(np.nan, params)

        assert pd.isna(result)

    def test_generalize_non_numeric_raises_error(self):
        """Test generalization with non-numeric value."""
        params = {"bin_size": 10, "min_value": 0, "max_value": 100}

        with pytest.raises(AnonymizationError):
            AnonymizationStrategies.generalize_strategy("not a number", params)


class TestAnonymizer:
    """Test Anonymizer class."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "email": ["john@example.com", "jane@example.com", "bob@test.com"],
                "age": [34, 28, 45],
                "phone": ["555-1234", "555-5678", "555-9012"],
                "name": ["John Doe", "Jane Smith", "Bob Johnson"],  # No rule
            }
        )

    def test_anonymizer_initialization(self, sample_config):
        """Test Anonymizer initialization."""
        anonymizer = Anonymizer(sample_config)

        assert anonymizer.config == sample_config
        assert anonymizer.global_config is not None

    def test_anonymize_dataframe(self, sample_config, sample_df):
        """Test anonymizing a DataFrame."""
        anonymizer = Anonymizer(sample_config)

        result = anonymizer.anonymize(sample_df)

        # Check shape preserved
        assert result.shape == sample_df.shape

        # Check columns preserved
        assert list(result.columns) == list(sample_df.columns)

        # Check email was hashed
        assert result["email"].iloc[0] != sample_df["email"].iloc[0]
        assert len(result["email"].iloc[0]) == 64  # SHA256 length

        # Check age was generalized
        assert "-" in result["age"].iloc[0]  # Should be a range

        # Check phone was partially redacted
        assert result["phone"].iloc[0].endswith("1234")
        assert "*" in result["phone"].iloc[0]

        # Check name unchanged (no rule)
        assert result["name"].iloc[0] == sample_df["name"].iloc[0]

    def test_anonymize_with_column_mapping(self, sample_config, sample_df):
        """Test anonymization with explicit column mapping."""
        anonymizer = Anonymizer(sample_config)

        # Rename columns to not match PII types
        df = sample_df.rename(columns={"email": "customer_email"})

        # Provide mapping
        column_mapping = {"customer_email": "email"}

        result = anonymizer.anonymize(df, column_mapping)

        # Check email column was anonymized
        assert result["customer_email"].iloc[0] != df["customer_email"].iloc[0]

    def test_anonymize_preserves_original(self, sample_config, sample_df):
        """Test that anonymization doesn't modify original DataFrame."""
        anonymizer = Anonymizer(sample_config)

        original_copy = sample_df.copy()

        result = anonymizer.anonymize(sample_df)

        # Original should be unchanged
        pd.testing.assert_frame_equal(sample_df, original_copy)

        # Result should be different
        assert not sample_df["email"].equals(result["email"])

    def test_anonymize_handles_missing_values(self, sample_config):
        """Test handling of missing values."""
        df = pd.DataFrame(
            {
                "email": ["john@example.com", np.nan, "bob@test.com"],
                "age": [34, np.nan, 45],
            }
        )

        anonymizer = Anonymizer(sample_config)
        result = anonymizer.anonymize(df)

        # Check NaN preserved in correct positions
        assert pd.isna(result["email"].iloc[1])
        assert pd.isna(result["age"].iloc[1])

        # Check non-NaN values were anonymized
        assert result["email"].iloc[0] != df["email"].iloc[0]

    def test_get_statistics(self, sample_config, sample_df):
        """Test statistics tracking."""
        anonymizer = Anonymizer(sample_config)

        anonymizer.anonymize(sample_df)
        stats = anonymizer.get_statistics()

        assert stats["columns_processed"] == 4  # All columns checked
        assert stats["columns_anonymized"] == 3  # 3 have rules
        assert stats["rows_processed"] == 3
        assert len(stats["errors"]) == 0

    def test_anonymizer_repr(self, sample_config):
        """Test string representation."""
        anonymizer = Anonymizer(sample_config)

        repr_str = repr(anonymizer)
        assert "Anonymizer" in repr_str
        assert "rules=" in repr_str


class TestConvenienceFunction:
    """Test convenience function."""

    def test_anonymize_function_with_config_object(self):
        """Test anonymize function with ConfigLoader object."""
        config_dict = {
            "rules": {
                "email": {
                    "strategy": "hash",
                    "parameters": {"algorithm": "sha256", "salt": False},
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            config_path = Path(f.name)

        config = load_config(config_path)
        config_path.unlink()

        df = pd.DataFrame({"email": ["test@example.com"]})

        result = anonymize(df, config)

        assert result["email"].iloc[0] != df["email"].iloc[0]

    def test_anonymize_function_with_path(self):
        """Test anonymize function with config path."""
        config_dict = {
            "rules": {
                "email": {
                    "strategy": "hash",
                    "parameters": {"algorithm": "sha256", "salt": False},
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            config_path = Path(f.name)

        df = pd.DataFrame({"email": ["test@example.com"]})

        result = anonymize(df, config_path)
        config_path.unlink()

        assert result["email"].iloc[0] != df["email"].iloc[0]


class TestDataTypePreservation:
    """Test data type preservation."""

    def test_numeric_types_preserved_where_possible(self):
        """Test that numeric types are preserved when possible."""
        config_dict = {
            "rules": {
                "age": {
                    "strategy": "generalize",
                    "parameters": {"bin_size": 10, "min_value": 0, "max_value": 100},
                }
            },
            "global": {"preserve_data_types": True},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            config_path = Path(f.name)

        config = load_config(config_path)
        config_path.unlink()

        df = pd.DataFrame({"age": [34, 28, 45]})

        anonymizer = Anonymizer(config)
        result = anonymizer.anonymize(df)

        # Generalization returns string ranges, so type changes
        assert result["age"].dtype == object


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self, sample_config):
        """Test anonymizing empty DataFrame."""
        df = pd.DataFrame({"email": [], "age": []})

        anonymizer = Anonymizer(sample_config)
        result = anonymizer.anonymize(df)

        assert len(result) == 0
        assert list(result.columns) == ["email", "age"]

    def test_single_row_dataframe(self, sample_config):
        """Test anonymizing single-row DataFrame."""
        df = pd.DataFrame({"email": ["test@example.com"], "age": [34]})

        anonymizer = Anonymizer(sample_config)
        result = anonymizer.anonymize(df)

        assert len(result) == 1
        assert result["email"].iloc[0] != df["email"].iloc[0]

    def test_no_matching_rules(self):
        """Test DataFrame with no matching rules."""
        config_dict = {
            "rules": {
                "email": {
                    "strategy": "hash",
                    "parameters": {"algorithm": "sha256", "salt": False},
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            config_path = Path(f.name)

        config = load_config(config_path)
        config_path.unlink()

        # DataFrame with different columns
        df = pd.DataFrame({"name": ["John"], "phone": ["555-1234"]})

        anonymizer = Anonymizer(config)
        result = anonymizer.anonymize(df)

        # Should be unchanged
        pd.testing.assert_frame_equal(result, df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
