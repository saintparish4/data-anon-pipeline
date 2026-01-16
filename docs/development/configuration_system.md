# Configuration System Documentation

## Overview

The configuration system provides flexible, YAML-based anonymization rule management. It supports multiple strategies, validation, and preset configurations for common use cases.

## Quick Start

```python
from src.config_loader import load_config

# Load default configuration
config = load_config()

# Get a specific rule
email_rule = config.get_rule("email")
print(f"Strategy: {email_rule.strategy.value}")
print(f"Parameters: {email_rule.parameters}")

# Load a preset
from pathlib import Path
gdpr_config = load_config(Path("config/presets/gdpr_compliant.yaml"))
```

## Configuration Structure

```yaml
version: "1.0"
description: "Your configuration description"

rules:
  email:
    strategy: hash
    parameters:
      algorithm: sha256
  
  age:
    strategy: generalize
    parameters:
      bin_size: 10
      min_value: 0
      max_value: 100

global:
  handle_nulls: true
  preserve_data_types: true
  case_sensitive: false
```

## Anonymization Strategies

| Strategy | Description | Required Parameters |
|----------|-------------|---------------------|
| `hash` | One-way cryptographic hashing | `algorithm` (sha256, sha512, md5) |
| `redact_full` | Complete removal/replacement | None |
| `redact_partial` | Partial masking | `visible_chars`, `mask_char` |
| `pseudonymize` | Consistent fake data generation | `seed_based` |
| `generalize` | Data aggregation/binning | Varies by type (see below) |

### Generalize Parameters

**Numeric data:**
```yaml
parameters:
  bin_size: 10
  min_value: 0
  max_value: 100
```

**Location data (zipcode, coordinates):**
```yaml
parameters:
  precision: 3  # Keep first N digits
```

**Date/time data:**
```yaml
parameters:
  granularity: month  # day, week, month, quarter, year
```

**Address data:**
```yaml
parameters:
  level: city  # full, street, city, state, country
```

**IP addresses:**
```yaml
parameters:
  octets: 2  # Keep first N octets (1-4)
```

## Preset Configurations

### GDPR Compliant (`config/presets/gdpr_compliant.yaml`)
- **Purpose:** Maximum privacy protection for public data release
- **Characteristics:** Irreversible anonymization, k-anonymity ≥ 10
- **Use Case:** Public datasets, regulatory compliance

### ML Training (`config/presets/ml_training.yaml`)
- **Purpose:** Preserve statistical properties and correlations
- **Characteristics:** Maintains data utility (85-95%), enables ML workflows
- **Use Case:** Internal analytics, model training

### Vendor Sharing (`config/presets/vendor_sharing.yaml`)
- **Purpose:** Balanced protection with business utility
- **Characteristics:** Moderate anonymization (70-80% utility)
- **Use Case:** Third-party integrations, analytics vendors

## Usage Patterns

### Runtime Configuration Selection

```python
def select_config(use_case: str):
    config_map = {
        "public": "config/presets/gdpr_compliant.yaml",
        "internal": "config/presets/ml_training.yaml",
        "vendor": "config/presets/vendor_sharing.yaml"
    }
    return load_config(Path(config_map[use_case]))

config = select_config("public")
```

### Validation and Error Handling

```python
from src.config_loader import ConfigurationError

try:
    config = load_config(Path("custom_config.yaml"))
    
    # Check for required PII types
    required = ["email", "phone", "ssn"]
    missing = [t for t in required if not config.has_rule(t)]
    if missing:
        print(f"Warning: Missing rules for {missing}")
        
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### Inspecting Configuration

```python
# Get all configured PII types
pii_types = config.get_pii_types()

# Get all rules
all_rules = config.get_all_rules()

# Get global settings
global_config = config.get_global_config()
print(f"Handle nulls: {global_config.handle_nulls}")
```

## API Reference

### ConfigLoader

**Methods:**
- `load()` - Load and validate configuration
- `get_rule(pii_type: str)` - Get rule for specific PII type
- `get_all_rules()` - Get all configured rules
- `get_pii_types()` - Get set of configured PII types
- `has_rule(pii_type: str)` - Check if rule exists
- `get_global_config()` - Get global settings

### RuleConfig

**Attributes:**
- `pii_type: str` - PII type identifier
- `strategy: AnonymizationStrategy` - Anonymization strategy
- `parameters: Dict[str, Any]` - Strategy parameters

### GlobalConfig

**Attributes:**
- `handle_nulls: bool` - Whether to process null values
- `null_replacement: Optional[str]` - Replacement for nulls
- `preserve_data_types: bool` - Maintain original data types
- `case_sensitive: bool` - Case-sensitive PII detection

## Validation Rules

The configuration loader automatically validates:

1. **Schema:** Required keys, correct types
2. **Strategies:** Only allowed strategies accepted
3. **Parameters:** Required parameters present for each strategy
4. **Values:** Parameter values within acceptable ranges
   - `bin_size` > 0
   - `min_value` < `max_value`
   - `visible_chars` ≥ 0
   - `mask_char` is single character
   - `algorithm` in allowed list
   - `granularity` in [day, week, month, quarter, year]
   - `level` in [full, street, city, state, country]
   - `octets` in range 1-4

## Common Patterns

### Creating Custom Configurations

1. Copy base config: `cp config/anonymization_rules.yaml config/custom.yaml`
2. Modify rules for your use case
3. Load: `config = load_config(Path("config/custom.yaml"))`

### Integration with Anonymization Pipeline

```python
config = load_config()

for field, value in data.items():
    rule = config.get_rule(field)
    if rule:
        anonymized = anonymizer.apply(value, rule)
        data[field] = anonymized
```

## Additional Resources

- **Example Guide:** `example_config_usage_guide.py` - 9 detailed usage examples
- **Tests:** `tests/test_config_loader.py` - Comprehensive test suite
- **Base Config:** `config/anonymization_rules.yaml` - Template with all PII types

