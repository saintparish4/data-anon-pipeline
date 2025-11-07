"""
Configuration Loader for Anonymization Rules

This module handles loading, validating, and parsing YAML configuration files for the anonymization pipeline.
"""

from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import yaml  # pyright: ignore[reportMissingModuleSource]
from dataclasses import dataclass, field
from enum import Enum


class AnonymizationStrategy(Enum):
    """Enumeration of supported anonymization strategies."""
    HASH = "hash"
    REDACT_FULL = "redact_full"
    REDACT_PARTIAL = "redact_partial"
    PSEUDONYMIZE = "pseudonymize"
    GENERALIZE = "generalize"


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


@dataclass
class RuleConfig:
    """
    Data class representing a single anonymization rule.
    
    Attributes:
        pii_type: The type of PII this rule applies to (e.g., 'email', 'ssn')
        strategy: The anonymization strategy to use
        parameters: Dictionary of strategy-specific parameters
    """
    pii_type: str
    strategy: AnonymizationStrategy
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """
        Validate that the rule configuration is complete and correct.
        
        Raises:
            ConfigurationError: If validation fails
        """
        # Special handling for GENERALIZE strategy (supports multiple parameter sets)
        if self.strategy == AnonymizationStrategy.GENERALIZE:
            self._validate_generalize_parameters()
        else:
            # Strategy-specific validation for other strategies
            required_params = self._get_required_parameters()
            missing = set(required_params) - set(self.parameters.keys())
            
            if missing:
                raise ConfigurationError(
                    f"Rule for '{self.pii_type}' missing required parameters for "
                    f"strategy '{self.strategy.value}': {missing}"
                )
        
        # Validate parameter values
        self._validate_parameter_values()
    
    def _validate_generalize_parameters(self) -> None:
        """Validate GENERALIZE strategy parameters (supports multiple parameter sets)."""
        params = set(self.parameters.keys())
        
        # Valid parameter sets for GENERALIZE
        valid_sets = [
            {"bin_size", "min_value", "max_value"},  # Numeric binning
            {"precision"},  # Location data (zipcode, IP)
            {"granularity"},  # Date/time data
            {"level"},  # Address/hierarchical data
            {"octets"},  # IP address specific
        ]
        
        # Check if parameters match any valid set
        for valid_set in valid_sets:
            if valid_set.issubset(params):
                return  # Valid configuration found
        
        raise ConfigurationError(
            f"Rule for '{self.pii_type}' missing required parameters for strategy 'generalize'. "
            f"Expected one of: numeric (bin_size, min_value, max_value), "
            f"location (precision), date (granularity), address (level), or IP (octets). "
            f"Got: {params}"
        )
    
    def _get_required_parameters(self) -> List[str]:
        """Get required parameters for the current strategy."""
        # For GENERALIZE, we accept multiple parameter sets (see validation below)
        requirements = {
            AnonymizationStrategy.REDACT_PARTIAL: ["visible_chars", "mask_char"],
            AnonymizationStrategy.PSEUDONYMIZE: ["seed_based"],
            AnonymizationStrategy.HASH: ["algorithm"],
        }
        return requirements.get(self.strategy, [])
    
    def _validate_parameter_values(self) -> None:
        """Validate that parameter values are appropriate."""
        if self.strategy == AnonymizationStrategy.GENERALIZE:
            # Validate numeric binning parameters (if present)
            if "bin_size" in self.parameters:
                bin_size = self.parameters.get("bin_size")
                min_val = self.parameters.get("min_value")
                max_val = self.parameters.get("max_value")
                
                if not isinstance(bin_size, (int, float)) or bin_size <= 0:
                    raise ConfigurationError(
                        f"Invalid bin_size for '{self.pii_type}': must be positive number"
                    )
                
                if min_val >= max_val:
                    raise ConfigurationError(
                        f"Invalid range for '{self.pii_type}': min_value must be < max_value"
                    )
            
            # Validate precision parameter (if present)
            if "precision" in self.parameters:
                precision = self.parameters.get("precision")
                if not isinstance(precision, int) or precision <= 0:
                    raise ConfigurationError(
                        f"Invalid precision for '{self.pii_type}': must be positive integer"
                    )
            
            # Validate octets parameter (if present)
            if "octets" in self.parameters:
                octets = self.parameters.get("octets")
                if not isinstance(octets, int) or octets < 1 or octets > 4:
                    raise ConfigurationError(
                        f"Invalid octets for '{self.pii_type}': must be integer between 1 and 4"
                    )
            
            # Validate granularity parameter (if present)
            if "granularity" in self.parameters:
                granularity = self.parameters.get("granularity")
                allowed_granularities = ["day", "week", "month", "quarter", "year"]
                if granularity not in allowed_granularities:
                    raise ConfigurationError(
                        f"Invalid granularity for '{self.pii_type}': "
                        f"must be one of {allowed_granularities}"
                    )
            
            # Validate level parameter (if present)
            if "level" in self.parameters:
                level = self.parameters.get("level")
                allowed_levels = ["full", "street", "city", "state", "country"]
                if level not in allowed_levels:
                    raise ConfigurationError(
                        f"Invalid level for '{self.pii_type}': "
                        f"must be one of {allowed_levels}"
                    )
        
        elif self.strategy == AnonymizationStrategy.REDACT_PARTIAL:
            visible = self.parameters.get("visible_chars")
            if not isinstance(visible, int) or visible < 0:
                raise ConfigurationError(
                    f"Invalid visible_chars for '{self.pii_type}': must be non-negative integer"
                )
            
            mask_char = self.parameters.get("mask_char")
            if not isinstance(mask_char, str) or len(mask_char) != 1:
                raise ConfigurationError(
                    f"Invalid mask_char for '{self.pii_type}': must be single character"
                )
        
        elif self.strategy == AnonymizationStrategy.HASH:
            algorithm = self.parameters.get("algorithm")
            allowed_algorithms = ["sha256", "sha512", "md5"]  # md5 not recommended
            if algorithm not in allowed_algorithms:
                raise ConfigurationError(
                    f"Invalid hash algorithm for '{self.pii_type}': "
                    f"must be one of {allowed_algorithms}"
                )


@dataclass
class GlobalConfig:
    """Global configuration settings for anonymization."""
    handle_nulls: bool = True
    null_replacement: Optional[str] = None
    preserve_data_types: bool = True
    case_sensitive: bool = False


class ConfigLoader:
    """
    Loads and validates anonymization configuration from YAML files.
    
    Follows Single Responsibility Principle (SRP): only handles config loading.
    Follows Open-Closed Principle (OCP): extensible through adding new strategies.
    """
    
    ALLOWED_STRATEGIES = {s.value for s in AnonymizationStrategy}
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._raw_config: Optional[Dict[str, Any]] = None
        self._rules: Optional[Dict[str, RuleConfig]] = None
        self._global_config: Optional[GlobalConfig] = None
    
    @staticmethod
    def _get_default_config_path() -> Path:
        """Get the default configuration file path."""
        return Path(__file__).parent.parent / "config" / "anonymization_rules.yaml"
    
    def load(self) -> 'ConfigLoader':
        """
        Load and validate the configuration file.
        
        Returns:
            self for method chaining
            
        Raises:
            ConfigurationError: If loading or validation fails
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}"
            )
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in {self.config_path}: {e}"
            )
        
        self._validate_schema()
        self._parse_rules()
        self._parse_global_config()
        
        return self
    
    def _validate_schema(self) -> None:
        """
        Validate the overall configuration schema.
        
        Raises:
            ConfigurationError: If schema validation fails
        """
        if not isinstance(self._raw_config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        
        required_keys = ["rules"]
        missing_keys = set(required_keys) - set(self._raw_config.keys())
        if missing_keys:
            raise ConfigurationError(
                f"Configuration missing required keys: {missing_keys}"
            )
        
        # Validate version if present
        if "version" in self._raw_config:
            version = self._raw_config["version"]
            if not isinstance(version, str):
                raise ConfigurationError("Version must be a string")
    
    def _parse_rules(self) -> None:
        """Parse individual anonymization rules from config."""
        rules_dict = self._raw_config.get("rules", {})
        
        if not isinstance(rules_dict, dict):
            raise ConfigurationError("'rules' must be a dictionary")
        
        self._rules = {}
        
        for pii_type, rule_data in rules_dict.items():
            if not isinstance(rule_data, dict):
                raise ConfigurationError(
                    f"Rule for '{pii_type}' must be a dictionary"
                )
            
            strategy_str = rule_data.get("strategy")
            if not strategy_str:
                raise ConfigurationError(
                    f"Rule for '{pii_type}' missing 'strategy' field"
                )
            
            if strategy_str not in self.ALLOWED_STRATEGIES:
                raise ConfigurationError(
                    f"Unknown strategy '{strategy_str}' for '{pii_type}'. "
                    f"Allowed: {self.ALLOWED_STRATEGIES}"
                )
            
            strategy = AnonymizationStrategy(strategy_str)
            parameters = rule_data.get("parameters", {})
            
            rule = RuleConfig(
                pii_type=pii_type,
                strategy=strategy,
                parameters=parameters
            )
            
            # Validate the rule
            rule.validate()
            
            self._rules[pii_type] = rule
    
    def _parse_global_config(self) -> None:
        """Parse global configuration settings."""
        global_dict = self._raw_config.get("global", {})
        
        if not isinstance(global_dict, dict):
            raise ConfigurationError("'global' must be a dictionary")
        
        self._global_config = GlobalConfig(
            handle_nulls=global_dict.get("handle_nulls", True),
            null_replacement=global_dict.get("null_replacement"),
            preserve_data_types=global_dict.get("preserve_data_types", True),
            case_sensitive=global_dict.get("case_sensitive", False)
        )
    
    def get_rule(self, pii_type: str) -> Optional[RuleConfig]:
        """
        Get the anonymization rule for a specific PII type.
        
        Args:
            pii_type: The type of PII (e.g., 'email', 'ssn')
            
        Returns:
            RuleConfig if found, None otherwise
        """
        if self._rules is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        
        return self._rules.get(pii_type)
    
    def get_all_rules(self) -> Dict[str, RuleConfig]:
        """
        Get all anonymization rules.
        
        Returns:
            Dictionary mapping PII types to their rules
        """
        if self._rules is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        
        return self._rules.copy()
    
    def get_global_config(self) -> GlobalConfig:
        """Get global configuration settings."""
        if self._global_config is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        
        return self._global_config
    
    def get_pii_types(self) -> Set[str]:
        """Get set of all configured PII types."""
        if self._rules is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        
        return set(self._rules.keys())
    
    def has_rule(self, pii_type: str) -> bool:
        """Check if a rule exists for the given PII type."""
        if self._rules is None:
            raise ConfigurationError("Configuration not loaded. Call load() first.")
        
        return pii_type in self._rules
    
    def __repr__(self) -> str:
        """String representation of the config loader."""
        if self._rules is None:
            return f"ConfigLoader(path={self.config_path}, loaded=False)"
        return (
            f"ConfigLoader(path={self.config_path}, "
            f"rules={len(self._rules)}, loaded=True)"
        )


def load_config(config_path: Optional[Path] = None) -> ConfigLoader:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded ConfigLoader instance
        
    Example:
        >>> config = load_config()
        >>> email_rule = config.get_rule('email')
        >>> print(email_rule.strategy)
    """
    loader = ConfigLoader(config_path)
    return loader.load()


# Example usage
if __name__ == "__main__":
    # Load and validate configuration
    try:
        config = load_config()
        print(f"Configuration loaded successfully: {config}")
        print(f"Found {len(config.get_all_rules())} PII type rules")
        
        # Display some rules
        for pii_type in ["email", "ssn", "age"]:
            rule = config.get_rule(pii_type)
            if rule:
                print(f"  - {pii_type}: {rule.strategy.value}")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")