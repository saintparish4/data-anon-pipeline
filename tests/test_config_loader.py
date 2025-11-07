"""
Unit tests for the configuration loader.

Tests cover:
- Valid configuration loading
- Schema validation
- Rule validation
- Error handling
- Edge cases
"""

import pytest
from pathlib import Path
import tempfile
import yaml  # pyright: ignore[reportMissingModuleSource]
from typing import Dict, Any

from src.config_loader import (
    ConfigLoader,
    ConfigurationError,
    AnonymizationStrategy,
    RuleConfig,
    load_config
)


@pytest.fixture
def valid_config() -> Dict[str, Any]:
    """Fixture providing a valid configuration dictionary."""
    return {
        "version": "1.0",
        "description": "Test configuration",
        "rules": {
            "email": {
                "strategy": "hash",
                "parameters": {
                    "salt": True,
                    "algorithm": "sha256"
                }
            },
            "age": {
                "strategy": "generalize",
                "parameters": {
                    "bin_size": 10,
                    "min_value": 0,
                    "max_value": 100
                }
            },
            "phone": {
                "strategy": "redact_partial",
                "parameters": {
                    "visible_chars": 3,
                    "mask_char": "*"
                }
            }
        },
        "global": {
            "handle_nulls": True,
            "preserve_data_types": True
        }
    }


@pytest.fixture
def temp_config_file(valid_config):
    """Fixture that creates a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_config, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()


class TestConfigLoaderBasics:
    """Test basic configuration loading functionality."""
    
    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file."""
        loader = ConfigLoader(temp_config_file)
        loader.load()
        
        assert loader.get_pii_types() == {"email", "age", "phone"}
        assert loader.has_rule("email")
        assert not loader.has_rule("nonexistent")
    
    def test_load_nonexistent_file(self):
        """Test error handling for missing file."""
        loader = ConfigLoader(Path("/nonexistent/config.yaml"))
        
        with pytest.raises(ConfigurationError, match="not found"):
            loader.load()
    
    def test_load_invalid_yaml(self):
        """Test error handling for malformed YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("{ invalid: yaml: content:")
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_methods_before_load_raise_error(self, temp_config_file):
        """Test that methods fail before load() is called."""
        loader = ConfigLoader(temp_config_file)
        
        with pytest.raises(ConfigurationError, match="not loaded"):
            loader.get_rule("email")
        
        with pytest.raises(ConfigurationError, match="not loaded"):
            loader.get_all_rules()
    
    def test_repr(self, temp_config_file):
        """Test string representation."""
        loader = ConfigLoader(temp_config_file)
        
        repr_before = repr(loader)
        assert "loaded=False" in repr_before
        
        loader.load()
        repr_after = repr(loader)
        assert "loaded=True" in repr_after
        assert "rules=3" in repr_after


class TestRuleRetrieval:
    """Test rule retrieval and access methods."""
    
    def test_get_specific_rule(self, temp_config_file):
        """Test retrieving a specific rule."""
        loader = ConfigLoader(temp_config_file).load()
        
        email_rule = loader.get_rule("email")
        assert email_rule is not None
        assert email_rule.pii_type == "email"
        assert email_rule.strategy == AnonymizationStrategy.HASH
        assert email_rule.parameters["algorithm"] == "sha256"
    
    def test_get_nonexistent_rule(self, temp_config_file):
        """Test retrieving a rule that doesn't exist."""
        loader = ConfigLoader(temp_config_file).load()
        
        rule = loader.get_rule("nonexistent")
        assert rule is None
    
    def test_get_all_rules(self, temp_config_file):
        """Test retrieving all rules."""
        loader = ConfigLoader(temp_config_file).load()
        
        all_rules = loader.get_all_rules()
        assert len(all_rules) == 3
        assert "email" in all_rules
        assert "age" in all_rules
        assert "phone" in all_rules
    
    def test_get_global_config(self, temp_config_file):
        """Test retrieving global configuration."""
        loader = ConfigLoader(temp_config_file).load()
        
        global_config = loader.get_global_config()
        assert global_config.handle_nulls is True
        assert global_config.preserve_data_types is True


class TestSchemaValidation:
    """Test configuration schema validation."""
    
    def test_missing_rules_key(self):
        """Test error when 'rules' key is missing."""
        config = {"version": "1.0"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="missing required keys"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_rules_not_dict(self):
        """Test error when 'rules' is not a dictionary."""
        config = {"rules": ["not", "a", "dict"]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="must be a dictionary"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_invalid_version_type(self):
        """Test error when version is not a string."""
        config = {
            "version": 1.0,  # Should be string
            "rules": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Version must be a string"):
                loader.load()
        finally:
            temp_path.unlink()


class TestRuleValidation:
    """Test individual rule validation."""
    
    def test_missing_strategy(self):
        """Test error when a rule is missing the 'strategy' field."""
        config = {
            "rules": {
                "email": {
                    "parameters": {"algorithm": "sha256"}
                    # Missing 'strategy'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="missing 'strategy'"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_unknown_strategy(self):
        """Test error when strategy is not recognized."""
        config = {
            "rules": {
                "email": {
                    "strategy": "unknown_strategy",
                    "parameters": {}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Unknown strategy"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_missing_required_parameters(self):
        """Test error when required parameters are missing."""
        config = {
            "rules": {
                "age": {
                    "strategy": "generalize",
                    "parameters": {
                        "bin_size": 10
                        # Missing min_value and max_value
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="missing required parameters"):
                loader.load()
        finally:
            temp_path.unlink()


class TestParameterValidation:
    """Test validation of parameter values."""
    
    def test_invalid_bin_size(self):
        """Test error when bin_size is invalid."""
        config = {
            "rules": {
                "age": {
                    "strategy": "generalize",
                    "parameters": {
                        "bin_size": -10,  # Invalid: negative
                        "min_value": 0,
                        "max_value": 100
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid bin_size"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_invalid_min_max_range(self):
        """Test error when min_value >= max_value."""
        config = {
            "rules": {
                "age": {
                    "strategy": "generalize",
                    "parameters": {
                        "bin_size": 10,
                        "min_value": 100,  # Invalid: greater than max
                        "max_value": 50
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid range"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_invalid_visible_chars(self):
        """Test error when visible_chars is invalid."""
        config = {
            "rules": {
                "phone": {
                    "strategy": "redact_partial",
                    "parameters": {
                        "visible_chars": -1,  # Invalid: negative
                        "mask_char": "*"
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid visible_chars"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_invalid_mask_char(self):
        """Test error when mask_char is not a single character."""
        config = {
            "rules": {
                "phone": {
                    "strategy": "redact_partial",
                    "parameters": {
                        "visible_chars": 3,
                        "mask_char": "**"  # Invalid: multiple characters
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid mask_char"):
                loader.load()
        finally:
            temp_path.unlink()
    
    def test_invalid_hash_algorithm(self):
        """Test error when hash algorithm is not allowed."""
        config = {
            "rules": {
                "email": {
                    "strategy": "hash",
                    "parameters": {
                        "algorithm": "sha1"  # Not in allowed list
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigurationError, match="Invalid hash algorithm"):
                loader.load()
        finally:
            temp_path.unlink()


class TestConvenienceFunctions:
    """Test convenience functions and utilities."""
    
    def test_load_config_function(self, temp_config_file):
        """Test the load_config convenience function."""
        config = load_config(temp_config_file)
        
        assert config.has_rule("email")
        assert len(config.get_all_rules()) == 3
    
    def test_rule_config_dataclass(self):
        """Test RuleConfig dataclass."""
        rule = RuleConfig(
            pii_type="email",
            strategy=AnonymizationStrategy.HASH,
            parameters={"algorithm": "sha256"}
        )
        
        assert rule.pii_type == "email"
        assert rule.strategy == AnonymizationStrategy.HASH
        assert rule.parameters["algorithm"] == "sha256"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_rules(self):
        """Test configuration with no rules."""
        config = {"rules": {}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path).load()
            assert len(loader.get_all_rules()) == 0
            assert loader.get_pii_types() == set()
        finally:
            temp_path.unlink()
    
    def test_optional_global_section(self):
        """Test that global section is optional."""
        config = {
            "rules": {
                "email": {
                    "strategy": "hash",
                    "parameters": {"algorithm": "sha256"}
                }
            }
            # No 'global' section
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path).load()
            global_config = loader.get_global_config()
            # Should use defaults
            assert global_config.handle_nulls is True
        finally:
            temp_path.unlink()
    
    def test_optional_parameters_dict(self):
        """Test that parameters dict is optional for strategies with no requirements."""
        config = {
            "rules": {
                "name": {
                    "strategy": "redact_full"
                    # No parameters needed for redact_full
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            loader = ConfigLoader(temp_path).load()
            rule = loader.get_rule("name")
            assert rule.parameters == {}
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




