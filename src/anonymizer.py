"""
Anonymization Pipeline Module

Applies anonymization strategies to DataFrames based on configuration rules.
Preserves data types, handles missing values, and maintains data utility where possible.
"""

from typing import Any, Dict, Optional, Union, Callable
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path

# Import Faker for pseudonymization
try:
    from faker import Faker
except ImportError:
    Faker = None

from src.config_loader import ConfigLoader, RuleConfig, AnonymizationStrategy


class AnonymizationError(Exception):
    """Custom exception for anonymization errors."""
    pass


class AnonymizationStrategies:
    """
    Implementation of all anonymization strategies.

    Each strategy is a static method that takes a value and parameters,
    returning the anonymized value. This follows the Strategy Pattern.
    """

    # Cache for Faker instances (keyed by locale)
    _faker_cache: Dict[str, Any] = {}

    # Cache for pseudonymization mappings (for consistency)
    _pseudo_cache: Dict[tuple, Any] = {}

    @staticmethod
    def hash_strategy(value: Any, parameters: Dict[str, Any]) -> str:
        """
        Hash values using SHA256 or other algorithms.

        Args:
            value: Value to hash
            parameters: Must contain 'algorithm', optional 'salt'

        Returns:
            Hexadecimal hash string
        """
        if pd.isna(value):
            return value 

        # Convert to string for hashing
        str_value = str(value)

        # Add salt if specified 
        if parameters.get('salt', False):
            # Use a determinstic salt based on value for consistency
            salt = hashlib.md5(str_value.encode()).hexdigest()[:8]
            str_value = f"{salt}{str_value}"

        # Select algorithm
        algorithm = parameters.get('algorithm', 'sha256')

        if algorithm == 'sha256':
            return hashlib.sha256(str_value.encode()).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(str_value.encode()).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(str_value.encode()).hexdigest()
        else:
            raise AnonymizationError(f"Unsupported hash algorithm: {algorithm}")

    @staticmethod
    def redact_full_strategy(value: Any, parameters: Dict[str, Any]) -> str:
        """
        Completely redact/remove values.
        
        Args:
            value: Value to redact
            parameters: Must contain 'replacement'
            
        Returns:
            Replacement string
        """
        if pd.isna(value):
            return value
        
        return parameters.get('replacement', '[REDACTED]')
    
    @staticmethod
    def redact_partial_strategy(value: Any, parameters: Dict[str, Any]) -> str:
        """
        Partially redact values, keeping some characters visible.
        
        Args:
            value: Value to partially redact
            parameters: Must contain 'visible_chars' and 'mask_char'
            
        Returns:
            Partially masked string
        """
        if pd.isna(value):
            return value
        
        str_value = str(value)
        visible_chars = parameters.get('visible_chars', 0)
        mask_char = parameters.get('mask_char', '*')
        
        if visible_chars <= 0:
            return mask_char * len(str_value)
        
        if visible_chars >= len(str_value):
            return str_value
        
        # Keep last N characters visible
        masked_length = len(str_value) - visible_chars
        return (mask_char * masked_length) + str_value[-visible_chars:]
    
    @staticmethod
    def pseudonymize_strategy(value: Any, parameters: Dict[str, Any]) -> Any:
        """
        Replace with fake but realistic data, maintaining consistency.
        
        Args:
            value: Value to pseudonymize
            parameters: Must contain 'seed_based', optional 'locale'
            
        Returns:
            Fake value (same type if possible)
        """
        if pd.isna(value):
            return value
        
        if Faker is None:
            raise AnonymizationError(
                "Faker library required for pseudonymization. "
                "Install with: pip install faker"
            )
        
        seed_based = parameters.get('seed_based', True)
        locale = parameters.get('locale', 'en_US')
        
        # Get or create Faker instance
        if locale not in AnonymizationStrategies._faker_cache:
            AnonymizationStrategies._faker_cache[locale] = Faker(locale)
        
        faker = AnonymizationStrategies._faker_cache[locale]
        
        if seed_based:
            # Use value as seed for consistency (same input -> same output)
            cache_key = (locale, str(value))
            
            if cache_key in AnonymizationStrategies._pseudo_cache:
                return AnonymizationStrategies._pseudo_cache[cache_key]
            
            # Create deterministic seed from value
            seed = int(hashlib.md5(str(value).encode()).hexdigest(), 16) % (2**32)
            faker.seed_instance(seed)
            
            # Generate fake value (use name as default)
            fake_value = faker.name()
            
            # Cache for consistency
            AnonymizationStrategies._pseudo_cache[cache_key] = fake_value
            
            return fake_value
        else:
            # Non-deterministic pseudonymization
            return faker.name()
    
    @staticmethod
    def generalize_strategy(value: Any, parameters: Dict[str, Any]) -> str:
        """
        Generalize values to ranges or categories.
        
        Args:
            value: Numeric value to generalize
            parameters: Must contain 'bin_size', 'min_value', 'max_value'
            
        Returns:
            Range string (e.g., "30-39")
        """
        if pd.isna(value):
            return value
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise AnonymizationError(
                f"Generalization requires numeric value, got: {type(value)}"
            )
        
        bin_size = parameters.get('bin_size')
        min_value = parameters.get('min_value')
        max_value = parameters.get('max_value')
        
        # Clamp to range
        clamped = max(min_value, min(max_value, numeric_value))
        
        # Calculate bin
        bin_index = int((clamped - min_value) / bin_size)
        bin_start = min_value + (bin_index * bin_size)
        bin_end = bin_start + bin_size - 1
        
        # Handle edge case for maximum value
        if clamped == max_value:
            bin_start = max_value - bin_size + 1
            bin_end = max_value
        
        return f"{int(bin_start)}-{int(bin_end)}"


class Anonymizer:
    """
    Main anonymization pipeline that applies strategies to DataFrames.
    
    Follows Single Responsibility Principle: only handles anonymization,
    delegates strategy implementation to AnonymizationStrategies.
    """
    
    # Strategy mapping
    _strategy_map: Dict[AnonymizationStrategy, Callable] = {
        AnonymizationStrategy.HASH: AnonymizationStrategies.hash_strategy,
        AnonymizationStrategy.REDACT_FULL: AnonymizationStrategies.redact_full_strategy,
        AnonymizationStrategy.REDACT_PARTIAL: AnonymizationStrategies.redact_partial_strategy,
        AnonymizationStrategy.PSEUDONYMIZE: AnonymizationStrategies.pseudonymize_strategy,
        AnonymizationStrategy.GENERALIZE: AnonymizationStrategies.generalize_strategy,
    }
    
    def __init__(self, config: ConfigLoader):
        """
        Initialize anonymizer with configuration.
        
        Args:
            config: Loaded ConfigLoader instance
        """
        self.config = config
        self.global_config = config.get_global_config()
        
        # Statistics tracking
        self._stats = {
            'columns_processed': 0,
            'columns_anonymized': 0,
            'rows_processed': 0,
            'errors': []
        }
    
    def anonymize(
        self,
        df: pd.DataFrame,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Anonymize a DataFrame based on configuration rules.
        
        Args:
            df: DataFrame to anonymize
            column_mapping: Optional mapping of column names to PII types.
                           If None, assumes column names match PII types.
                           Example: {'customer_email': 'email', 'age_years': 'age'}
        
        Returns:
            Anonymized DataFrame (copy, original unchanged)
            
        Raises:
            AnonymizationError: If anonymization fails
        """
        # Create a copy to avoid modifying original
        result = df.copy()
        
        # Reset statistics
        self._stats = {
            'columns_processed': 0,
            'columns_anonymized': 0,
            'rows_processed': len(df),
            'errors': []
        }
        
        # Handle edge case: empty DataFrame
        if len(df) == 0:
            return result
        
        # Process each column
        for column in df.columns:
            self._stats['columns_processed'] += 1
            
            # Determine PII type for this column
            pii_type = self._get_pii_type(column, column_mapping)
            
            if pii_type is None:
                # No mapping, skip this column
                continue
            
            # Get rule for this PII type
            rule = self.config.get_rule(pii_type)
            
            if rule is None:
                # No rule configured, skip
                continue
            
            try:
                # Anonymize the column
                result[column] = self._anonymize_column(
                    df[column],
                    rule,
                    column_name=column
                )
                self._stats['columns_anonymized'] += 1
                
            except Exception as e:
                error_msg = f"Error anonymizing column '{column}': {str(e)}"
                self._stats['errors'].append(error_msg)
                
                # Re-raise if we want to fail fast
                if not self.global_config.handle_nulls:
                    raise AnonymizationError(error_msg) from e
        
        return result
    
    def _get_pii_type(
        self,
        column: str,
        column_mapping: Optional[Dict[str, str]]
    ) -> Optional[str]:
        """
        Determine PII type for a column.
        
        Args:
            column: Column name
            column_mapping: Optional explicit mapping
            
        Returns:
            PII type string or None if no mapping
        """
        if column_mapping:
            return column_mapping.get(column)
        else:
            # Assume column name matches PII type
            return column if self.config.has_rule(column) else None
    
    def _anonymize_column(
        self,
        series: pd.Series,
        rule: RuleConfig,
        column_name: str
    ) -> pd.Series:
        """
        Anonymize a single column based on rule.
        
        Args:
            series: Column to anonymize
            rule: Anonymization rule to apply
            column_name: Name of column (for error messages)
            
        Returns:
            Anonymized series
        """
        strategy = rule.strategy
        parameters = rule.parameters
        
        # Get strategy function
        strategy_func = self._strategy_map.get(strategy)
        if strategy_func is None:
            raise AnonymizationError(f"Unknown strategy: {strategy}")
        
        # Apply strategy to each value
        try:
            result = series.apply(
                lambda x: strategy_func(x, parameters)
            )
            
            # Try to preserve data types where possible
            if self.global_config.preserve_data_types:
                result = self._preserve_dtype(result, series.dtype, strategy)
            
            return result
            
        except Exception as e:
            raise AnonymizationError(
                f"Failed to apply {strategy.value} to column '{column_name}': {e}"
            ) from e
    
    def _preserve_dtype(
        self,
        result: pd.Series,
        original_dtype: np.dtype,
        strategy: AnonymizationStrategy
    ) -> pd.Series:
        """
        Attempt to preserve original data type where possible.
        
        Args:
            result: Anonymized series
            original_dtype: Original data type
            strategy: Strategy used
            
        Returns:
            Series with preserved dtype if possible
        """
        # Handle empty series
        if len(result) == 0:
            return result
        
        # Only certain strategies can preserve types
        type_preserving = {
            AnonymizationStrategy.HASH,  # Always returns string
            AnonymizationStrategy.GENERALIZE,  # Returns string range
        }
        
        # If strategy always returns strings, don't try to convert
        if strategy in type_preserving:
            return result
        
        # For redaction, keep as string
        if 'redact' in strategy.value:
            return result
        
        # For other strategies, try to maintain original type
        try:
            if pd.api.types.is_numeric_dtype(original_dtype):
                # Only convert if result is actually numeric
                # Use more robust check that handles edge cases
                def is_numeric_or_null(x):
                    if pd.isna(x):
                        return True
                    try:
                        str_val = str(x).replace('.', '').replace('-', '')
                        return str_val.isdigit() if str_val else False
                    except:
                        return False
                
                if result.apply(is_numeric_or_null).all():
                    return pd.to_numeric(result, errors='ignore')
        except Exception:
            pass
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get anonymization statistics from last run.
        
        Returns:
            Dictionary with statistics
        """
        return self._stats.copy()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Anonymizer(config={self.config}, rules={len(self.config.get_all_rules())})"


def anonymize(
    df: pd.DataFrame,
    config: Union[ConfigLoader, Path, str],
    column_mapping: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Convenience function to anonymize a DataFrame.
    
    Args:
        df: DataFrame to anonymize
        config: ConfigLoader instance, or path to config file
        column_mapping: Optional mapping of column names to PII types
        
    Returns:
        Anonymized DataFrame
        
    Example:
        >>> df = pd.DataFrame({'email': ['john@example.com'], 'age': [34]})
        >>> anonymized = anonymize(df, 'config/anonymization_rules.yaml')
    """
    from src.config_loader import load_config
    
    # Load config if needed
    if not isinstance(config, ConfigLoader):
        config = load_config(Path(config))
    
    # Create anonymizer and apply
    anonymizer = Anonymizer(config)
    return anonymizer.anonymize(df, column_mapping)


# Example usage
if __name__ == "__main__":
    import sys
    
    # Check dependencies
    missing_deps = []
    if Faker is None:
        missing_deps.append("faker")
    
    if missing_deps:
        print(f"WARNING: Missing dependencies: {', '.join(missing_deps)}")
        print(f"Install with: pip install {' '.join(missing_deps)}")
        sys.exit(1)
    
    # Create sample data
    df = pd.DataFrame({
        'email': ['john@example.com', 'jane@example.com', 'bob@test.com'],
        'age': [34, 28, 45],
        'phone': ['555-1234', '555-5678', '555-9012'],
        'income': [50000, 75000, 120000]
    })
    
    print("Original DataFrame:")
    print(df)
    print()
    
    # Load configuration and anonymize
    from src.config_loader import load_config
    
    try:
        config = load_config()
        anonymizer = Anonymizer(config)
        
        result = anonymizer.anonymize(df)
        
        print("Anonymized DataFrame:")
        print(result)
        print()
        
        # Show statistics
        stats = anonymizer.get_statistics()
        print("Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
