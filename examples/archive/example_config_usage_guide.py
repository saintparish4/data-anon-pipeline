"""
Configuration System Usage Guide

This guide demonstrates how to use the configuration system in various scenarios.
Includes examples for custom configs, presets, and integration patterns.
"""

from pathlib import Path
from src.config_loader import ConfigLoader, load_config, ConfigurationError


# =============================================================================
# Example 1: Loading Default Configuration
# =============================================================================


def example_basic_usage():
    """Basic configuration loading example."""
    print("=" * 60)
    print("Example 1: Basic Configuration Loading")
    print("=" * 60)

    # Load default configuration
    config = load_config()

    print(f"Configuration loaded: {config}")
    print(f"Number of rules: {len(config.get_all_rules())}")
    print(f"PII types configured: {', '.join(sorted(config.get_pii_types()))}")

    # Access specific rules
    email_rule = config.get_rule("email")
    if email_rule:
        print(f"\nEmail anonymization:")
        print(f"   Strategy: {email_rule.strategy.value}")
        print(f"   Parameters: {email_rule.parameters}")

    print()


# =============================================================================
# Example 2: Using Preset Configurations
# =============================================================================


def example_presets():
    """Demonstrate loading different preset configurations."""
    print("=" * 60)
    print("Example 2: Using Preset Configurations")
    print("=" * 60)

    presets = {
        "GDPR Compliant": "config/presets/gdpr_compliant.yaml",
        "ML Training": "config/presets/ml_training.yaml",
        "Vendor Sharing": "config/presets/vendor_sharing.yaml",
    }

    for name, path in presets.items():
        try:
            config = load_config(Path(path))
            print(f"\n{name} Preset:")
            print(f"   Rules: {len(config.get_all_rules())}")

            # Show age anonymization as example
            age_rule = config.get_rule("age")
            if age_rule:
                bin_size = age_rule.parameters.get("bin_size", "N/A")
                print(f"   Age binning: {bin_size}-year ranges")

        except ConfigurationError as e:
            print(f"   Error: {e}")

    print()


# =============================================================================
# Example 3: Comparing Preset Strategies
# =============================================================================


def example_compare_presets():
    """Compare how different presets handle the same PII type."""
    print("=" * 60)
    print("Example 3: Comparing Preset Strategies")
    print("=" * 60)

    pii_types_to_compare = ["email", "zipcode", "age", "income"]

    presets = {
        "GDPR": Path("config/presets/gdpr_compliant.yaml"),
        "ML": Path("config/presets/ml_training.yaml"),
        "Vendor": Path("config/presets/vendor_sharing.yaml"),
    }

    # Load all presets
    configs = {}
    for name, path in presets.items():
        try:
            configs[name] = load_config(path)
        except ConfigurationError:
            continue

    # Compare each PII type
    for pii_type in pii_types_to_compare:
        print(f"\n{pii_type.upper()}:")
        for preset_name, config in configs.items():
            rule = config.get_rule(pii_type)
            if rule:
                strategy = rule.strategy.value

                # Extract key parameter
                key_param = ""
                if strategy == "generalize":
                    if "bin_size" in rule.parameters:
                        key_param = f"bin={rule.parameters['bin_size']}"
                    elif "precision" in rule.parameters:
                        key_param = f"precision={rule.parameters['precision']}"
                elif strategy == "redact_partial":
                    key_param = f"visible={rule.parameters.get('visible_chars', 0)}"

                print(f"   {preset_name:10} → {strategy:15} {key_param}")
            else:
                print(f"   {preset_name:10} → Not configured")

    print()


# =============================================================================
# Example 4: Validating Configuration Before Use
# =============================================================================


def example_validation():
    """Demonstrate configuration validation."""
    print("=" * 60)
    print("Example 4: Configuration Validation")
    print("=" * 60)

    # Try to load a valid config
    try:
        config = load_config()
        print("Default configuration is valid")

        # Check for required PII types
        required_types = ["email", "phone", "ssn", "name"]
        missing = [t for t in required_types if not config.has_rule(t)]

        if missing:
            print(f"Warning: Missing rules for: {', '.join(missing)}")
        else:
            print(f"All required PII types configured")

    except ConfigurationError as e:
        print(f"Configuration error: {e}")

    print()


# =============================================================================
# Example 5: Runtime Configuration Selection
# =============================================================================


def select_config_for_use_case(use_case: str) -> ConfigLoader:
    """
    Select appropriate configuration based on use case.

    This pattern is useful for applications that need to choose
    configurations dynamically based on the data destination.
    """
    config_map = {
        "public_release": "config/presets/gdpr_compliant.yaml",
        "internal_analytics": "config/presets/ml_training.yaml",
        "vendor_integration": "config/presets/vendor_sharing.yaml",
        "default": "config/anonymization_rules.yaml",
    }

    config_path = config_map.get(use_case, config_map["default"])
    return load_config(Path(config_path))


def example_runtime_selection():
    """Demonstrate runtime configuration selection."""
    print("=" * 60)
    print("Example 5: Runtime Configuration Selection")
    print("=" * 60)

    use_cases = ["public_release", "internal_analytics", "vendor_integration"]

    for use_case in use_cases:
        try:
            config = select_config_for_use_case(use_case)
            print(f"\nUse case: {use_case}")
            print(f"   Configuration: {config.config_path.name}")
            print(f"   Rules loaded: {len(config.get_all_rules())}")
        except ConfigurationError as e:
            print(f"   Error: {e}")

    print()


# =============================================================================
# Example 6: Error Handling Patterns
# =============================================================================


def example_error_handling():
    """Demonstrate proper error handling."""
    print("=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    # Test 1: Missing file
    print("\nTest 1: Missing configuration file")
    try:
        config = load_config(Path("/nonexistent/config.yaml"))
        print("   Should have raised error")
    except ConfigurationError as e:
        print(f"   Caught error: {str(e)[:50]}...")

    # Test 2: Accessing rule before loading (would require creating ConfigLoader)
    print("\nTest 2: Accessing unloaded configuration")
    try:
        loader = ConfigLoader()
        # Don't call load()
        loader.get_rule("email")
        print("   Should have raised error")
    except ConfigurationError as e:
        print(f"   Caught error: {str(e)[:50]}...")

    print()


# =============================================================================
# Example 7: Inspecting Configuration Details
# =============================================================================


def example_inspection():
    """Demonstrate how to inspect configuration details."""
    print("=" * 60)
    print("Example 7: Inspecting Configuration Details")
    print("=" * 60)

    config = load_config()

    # Group rules by strategy
    from collections import defaultdict

    strategy_groups = defaultdict(list)

    for pii_type, rule in config.get_all_rules().items():
        strategy_groups[rule.strategy.value].append(pii_type)

    print("\nRules grouped by strategy:")
    for strategy, pii_types in sorted(strategy_groups.items()):
        print(f"\n   {strategy.upper()}:")
        for pii_type in sorted(pii_types):
            print(f"      - {pii_type}")

    # Global configuration
    global_config = config.get_global_config()
    print(f"\nGlobal settings:")
    print(f"   - Handle nulls: {global_config.handle_nulls}")
    print(f"   - Preserve data types: {global_config.preserve_data_types}")
    print(f"   - Case sensitive: {global_config.case_sensitive}")

    print()


# =============================================================================
# Example 8: Integration Pattern - Anonymization Pipeline
# =============================================================================


def example_integration_pattern():
    """
    Demonstrate how to integrate config loader with an anonymization pipeline.
    This is a simplified example showing the pattern.
    """
    print("=" * 60)
    print("Example 8: Integration Pattern")
    print("=" * 60)

    # Simulated data
    sample_data = {"email": "john@example.com", "age": 34, "zipcode": "10001"}

    print(f"\nOriginal data:")
    for key, value in sample_data.items():
        print(f"   {key}: {value}")

    # Load configuration
    config = load_config()

    print(f"\nApplying anonymization rules...")

    # For each field, show what would be done
    for field, value in sample_data.items():
        rule = config.get_rule(field)
        if rule:
            print(f"\n   {field}:")
            print(f"      Strategy: {rule.strategy.value}")
            print(f"      Parameters: {rule.parameters}")

            # This is where you would call the actual anonymization function
            # anonymized_value = anonymizer.apply(value, rule)
            print(f"      → Would apply {rule.strategy.value} transformation")
        else:
            print(f"\n   {field}:")
            print(f"      No rule configured (would keep as-is)")

    print()


# =============================================================================
# Example 9: Configuration Recommendations
# =============================================================================


def example_recommendations():
    """Provide recommendations for different scenarios."""
    print("=" * 60)
    print("Example 9: Configuration Recommendations")
    print("=" * 60)

    scenarios = {
        "Public Dataset Release": {
            "preset": "GDPR Compliant",
            "rationale": "Maximum privacy protection, irreversible anonymization",
            "k_anonymity": "≥ 10",
            "risk": "< 3%",
        },
        "Internal ML Training": {
            "preset": "ML Training",
            "rationale": "Preserves statistical properties and correlations",
            "utility": "85-95%",
            "risk": "< 10%",
        },
        "Analytics Vendor": {
            "preset": "Vendor Sharing",
            "rationale": "Balanced protection with business utility",
            "utility": "70-80%",
            "risk": "< 5%",
        },
    }

    print("\nScenario-Based Recommendations:\n")

    for scenario, details in scenarios.items():
        print(f"   {scenario}:")
        for key, value in details.items():
            print(f"      - {key.title()}: {value}")
        print()


# =============================================================================
# Main execution
# =============================================================================

if __name__ == "__main__":
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Preset Configurations", example_presets),
        ("Comparing Presets", example_compare_presets),
        ("Configuration Validation", example_validation),
        ("Runtime Selection", example_runtime_selection),
        ("Error Handling", example_error_handling),
        ("Configuration Inspection", example_inspection),
        ("Integration Pattern", example_integration_pattern),
        ("Recommendations", example_recommendations),
    ]

    print("\n" + "=" * 60)
    print("CONFIGURATION SYSTEM USAGE EXAMPLES")
    print("=" * 60 + "\n")

    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\nExample {i} failed: {e}\n")

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")
