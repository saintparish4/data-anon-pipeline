"""
Integration Tests for Complete Anonymization Pipeline
Tests the full workflow: scan → anonymize → validate

These tests verify:
1. End-to-end pipeline execution with each preset
2. Privacy guarantees are maintained
3. Utility targets are achieved
4. Configuration loading and validation
5. CLI commands work correctly
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import yaml
import subprocess
import sys

# Import your pipeline components
# Adjust based on your actual module structure
try:
    from src.scanner import PIIScanner
    from src.anonymizer import Anonymizer
    from src.risk_assessment import RiskAssessmentEngine
    from src.utility_metrics import UtilityMetrics
    from src.privacy_validator import PrivacyValidator
    from src.cli import AnonymizationCLI
    from src.config_loader import ConfigLoader
except ImportError:
    pytest.skip("Pipeline modules not available", allow_module_level=True)


# Helper function to convert scan results to column mapping
def scan_results_to_column_mapping(scan_results):
    """Convert PIIScanner results to column mapping for Anonymizer"""
    column_mapping = {}
    for field_name, detection_result in scan_results.items():
        if detection_result.pii_types:
            # Use the first (highest confidence) PII type detected
            column_mapping[field_name] = detection_result.pii_types[0]
    return column_mapping


# Fixtures for test data
@pytest.fixture
def sample_customer_data():
    """Generate realistic customer data for testing"""
    np.random.seed(42)
    n_records = 1000
    
    data = {
        'customer_id': range(1, n_records + 1),
        'name': [f"Person {i}" for i in range(n_records)],
        'email': [f"person{i}@example.com" for i in range(n_records)],
        'phone': [f"555-{i:04d}" for i in range(n_records)],
        'age': np.random.randint(18, 80, n_records),
        'zipcode': np.random.choice(['10001', '10002', '10003', '90001', '90002'], n_records),
        'income': np.random.randint(30000, 150000, n_records),
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago'], n_records),
        'state': np.random.choice(['NY', 'CA', 'IL'], n_records),
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def config_dir(tmp_path):
    """Create temporary config directory with presets"""
    preset_dir = tmp_path / "config" / "presets"
    preset_dir.mkdir(parents=True)
    return preset_dir


@pytest.fixture
def gdpr_config():
    """Load GDPR preset configuration"""
    config_path = Path(__file__).parent.parent / "config" / "presets" / "gdpr_compliant.yaml"
    return ConfigLoader(config_path).load()


@pytest.fixture
def gdpr_config_dict():
    """Load GDPR preset configuration as raw dict (for validator)"""
    config_path = Path(__file__).parent.parent / "config" / "presets" / "gdpr_compliant.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def ml_config():
    """Load ML training preset configuration"""
    config_path = Path(__file__).parent.parent / "config" / "presets" / "ml_training.yaml"
    return ConfigLoader(config_path).load()


@pytest.fixture
def ml_config_dict():
    """Load ML training preset configuration as raw dict (for validator)"""
    config_path = Path(__file__).parent.parent / "config" / "presets" / "ml_training.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def vendor_config():
    """Load vendor sharing preset configuration"""
    config_path = Path(__file__).parent.parent / "config" / "presets" / "vendor_sharing.yaml"
    return ConfigLoader(config_path).load()


@pytest.fixture
def vendor_config_dict():
    """Load vendor sharing preset configuration as raw dict (for validator)"""
    config_path = Path(__file__).parent.parent / "config" / "presets" / "vendor_sharing.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class TestConfigurationLoading:
    """Test configuration loading and validation"""
    
    def test_gdpr_config_loads(self, gdpr_config_dict):
        """Test GDPR config loads correctly"""
        assert gdpr_config_dict is not None
        assert 'metadata' in gdpr_config_dict
        assert gdpr_config_dict['metadata']['min_k_anonymity'] == 10
        assert 'anonymization_rules' in gdpr_config_dict
    
    def test_ml_config_loads(self, ml_config_dict):
        """Test ML training config loads correctly"""
        assert ml_config_dict is not None
        assert ml_config_dict['metadata']['min_k_anonymity'] == 5
        assert 'utility_targets' in ml_config_dict
    
    def test_vendor_config_loads(self, vendor_config_dict):
        """Test vendor sharing config loads correctly"""
        assert vendor_config_dict is not None
        assert vendor_config_dict['metadata']['min_k_anonymity'] == 7
        assert 'privacy_thresholds' in vendor_config_dict
    
    def test_all_configs_have_required_sections(self, gdpr_config_dict, ml_config_dict, vendor_config_dict):
        """Test all configs have required sections"""
        required_sections = ['metadata', 'anonymization_rules', 'privacy_thresholds', 'output']
        
        for config in [gdpr_config_dict, ml_config_dict, vendor_config_dict]:
            for section in required_sections:
                assert section in config, f"Missing required section: {section}"


class TestFullPipelineWorkflow:
    """Test complete pipeline: scan → anonymize → validate"""
    
    def test_gdpr_preset_workflow(self, sample_customer_data, gdpr_config, gdpr_config_dict):
        """Test full workflow with GDPR preset"""
        df_original = sample_customer_data
        
        # Step 1: Scan for PII
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(df_original)
        
        assert isinstance(scan_results, dict)
        assert len(scan_results) > 0  # Should detect PII
        
        # Step 2: Assess risk
        risk_assessor = RiskAssessmentEngine()
        risk_results = risk_assessor.assess(df_original, scan_results)
        
        assert 'risk_distribution' in risk_results
        assert risk_results['total_records'] == len(df_original)
        
        # Step 3: Anonymize
        column_mapping = scan_results_to_column_mapping(scan_results)
        anonymizer = Anonymizer(gdpr_config)
        df_anonymized = anonymizer.anonymize(df_original, column_mapping)
        
        assert len(df_anonymized) == len(df_original)  # Same number of records
        
        # Verify direct identifiers are removed/anonymized
        assert not df_anonymized['email'].equals(df_original['email'])
        assert not df_anonymized['name'].equals(df_original['name'])
        
        # Step 4: Validate privacy
        validator = PrivacyValidator(gdpr_config_dict)
        validation_results = validator.validate(df_anonymized, df_original)
        
        assert 'passed' in validation_results
        assert validation_results['passed'] is True, \
            f"GDPR validation failed: {validation_results.get('failures', [])}"
        
        # Verify k-anonymity threshold met
        k_anon_check = validation_results['checks'].get('k_anonymity', {})
        assert k_anon_check['passed'] is True
        assert k_anon_check['min_k'] >= 10  # GDPR requires k≥10
    
    def test_ml_preset_workflow(self, sample_customer_data, ml_config, ml_config_dict):
        """Test full workflow with ML training preset"""
        df_original = sample_customer_data
        
        # Full pipeline
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(df_original)
        
        column_mapping = scan_results_to_column_mapping(scan_results)
        anonymizer = Anonymizer(ml_config)
        df_anonymized = anonymizer.anonymize(df_original, column_mapping)
        
        validator = PrivacyValidator(ml_config_dict)
        validation_results = validator.validate(df_anonymized, df_original)
        
        assert validation_results['passed'] is True
        
        # ML preset should have higher utility preservation
        utility_analyzer = UtilityMetrics()
        utility_metrics = utility_analyzer.analyze(df_original, df_anonymized)
        
        assert utility_metrics['correlation_preservation'] >= 0.90  # ML target: 90%
        assert utility_metrics['distribution_similarity'] >= 0.85  # ML target: 85%
    
    def test_vendor_preset_workflow(self, sample_customer_data, vendor_config, vendor_config_dict):
        """Test full workflow with vendor sharing preset"""
        df_original = sample_customer_data
        
        # Full pipeline
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(df_original)
        
        column_mapping = scan_results_to_column_mapping(scan_results)
        anonymizer = Anonymizer(vendor_config)
        df_anonymized = anonymizer.anonymize(df_original, column_mapping)
        
        validator = PrivacyValidator(vendor_config_dict)
        validation_results = validator.validate(df_anonymized, df_original)
        
        assert validation_results['passed'] is True
        
        # Verify balanced approach (k=7)
        k_anon_check = validation_results['checks'].get('k_anonymity', {})
        assert k_anon_check['min_k'] >= 7


class TestUtilityPreservation:
    """Test utility preservation across different presets"""
    
    def test_gdpr_vs_ml_utility_tradeoff(self, sample_customer_data, gdpr_config, ml_config):
        """Verify ML preset preserves more utility than GDPR preset"""
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(sample_customer_data)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        # Anonymize with both presets
        anonymizer_gdpr = Anonymizer(gdpr_config)
        df_gdpr = anonymizer_gdpr.anonymize(sample_customer_data, column_mapping)
        
        anonymizer_ml = Anonymizer(ml_config)
        df_ml = anonymizer_ml.anonymize(sample_customer_data, column_mapping)
        
        # Measure utility
        utility_analyzer = UtilityMetrics()
        utility_gdpr = utility_analyzer.analyze(sample_customer_data, df_gdpr)
        utility_ml = utility_analyzer.analyze(sample_customer_data, df_ml)
        
        # ML should preserve more utility
        assert utility_ml['correlation_preservation'] > utility_gdpr['correlation_preservation']
        assert utility_ml['information_retention'] > utility_gdpr['information_retention']
    
    def test_correlation_preservation(self, sample_customer_data, ml_config):
        """Test that important correlations are preserved"""
        # Add correlated column
        df = sample_customer_data.copy()
        df['purchase_freq'] = (df['income'] / 10000).astype(int) + np.random.randint(-2, 3, len(df))
        
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(df)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        anonymizer = Anonymizer(ml_config)
        df_anon = anonymizer.anonymize(df, column_mapping)
        
        # Check correlation preservation
        original_corr = df[['income', 'purchase_freq']].corr().iloc[0, 1]
        anon_corr = df_anon[['income', 'purchase_freq']].corr().iloc[0, 1]
        
        # Correlation should be preserved within reasonable bounds
        correlation_preservation = abs(anon_corr / original_corr) if original_corr != 0 else 1
        assert correlation_preservation >= 0.80  # At least 80% preserved


class TestPrivacyGuarantees:
    """Test privacy guarantees are maintained"""
    
    def test_k_anonymity_enforcement(self, sample_customer_data, gdpr_config):
        """Test k-anonymity is enforced correctly"""
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(sample_customer_data)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        anonymizer = Anonymizer(gdpr_config)
        df_anon = anonymizer.anonymize(sample_customer_data, column_mapping)
        
        # Calculate k-anonymity manually
        quasi_identifiers = ['age', 'zipcode']
        equivalence_classes = df_anon.groupby(quasi_identifiers).size()
        min_k = equivalence_classes.min()
        
        assert min_k >= 10, f"k-anonymity violated: min_k={min_k}, required=10"
    
    def test_no_unique_combinations(self, sample_customer_data, gdpr_config):
        """Test that no unique quasi-identifier combinations exist"""
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(sample_customer_data)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        anonymizer = Anonymizer(gdpr_config)
        df_anon = anonymizer.anonymize(sample_customer_data, column_mapping)
        
        # Check for unique records
        quasi_identifiers = ['age', 'zipcode', 'city']
        unique_count = df_anon.groupby(quasi_identifiers).size().value_counts().get(1, 0)
        
        assert unique_count == 0, f"Found {unique_count} unique records"
    
    def test_reidentification_risk_below_threshold(self, sample_customer_data, gdpr_config):
        """Test re-identification risk is below acceptable threshold"""
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(sample_customer_data)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        anonymizer = Anonymizer(gdpr_config)
        df_anon = anonymizer.anonymize(sample_customer_data, column_mapping)
        
        # Assess risk
        risk_assessor = RiskAssessmentEngine()
        risk_results = risk_assessor.assess(df_anon, scan_results)
        
        high_risk_pct = risk_results['risk_distribution'].get('high_pct', 100)
        assert high_risk_pct <= 1.0, f"High risk percentage too high: {high_risk_pct}%"


class TestCLIIntegration:
    """Test CLI commands work correctly"""
    
    def test_cli_scan_command(self, sample_customer_data, tmp_path):
        """Test CLI scan command"""
        # Save test data
        input_file = tmp_path / "test_data.csv"
        output_file = tmp_path / "scan_results.json"
        sample_customer_data.to_csv(input_file, index=False)
        
        # Run CLI command
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", 
             "--file", str(input_file),
             "--output", str(output_file)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert output_file.exists()
    
    def test_cli_anonymize_with_preset(self, sample_customer_data, tmp_path):
        """Test CLI anonymize command with preset"""
        # Save test data
        input_file = tmp_path / "test_data.csv"
        output_file = tmp_path / "anonymized.csv"
        sample_customer_data.to_csv(input_file, index=False)
        
        # Run CLI command
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "anonymize",
             "--file", str(input_file),
             "--preset", "gdpr_compliant",
             "--output", str(output_file)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert output_file.exists()
        
        # Verify output is valid
        df_output = pd.read_csv(output_file)
        assert len(df_output) == len(sample_customer_data)
    
    def test_cli_list_presets(self):
        """Test CLI list-presets command"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "list-presets"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "gdpr_compliant" in result.stdout
        assert "ml_training" in result.stdout
        assert "vendor_sharing" in result.stdout


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_preset_name(self, sample_customer_data, tmp_path):
        """Test handling of invalid preset name"""
        input_file = tmp_path / "test_data.csv"
        output_file = tmp_path / "output.csv"
        sample_customer_data.to_csv(input_file, index=False)
        
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "anonymize",
             "--file", str(input_file),
             "--preset", "nonexistent_preset",
             "--output", str(output_file)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
    
    def test_missing_required_config_sections(self):
        """Test validation of config file structure"""
        import tempfile
        from src.config_loader import ConfigurationError
        
        # Create a temporary incomplete config file
        incomplete_config = {
            'metadata': {'name': 'test'},
            # Missing anonymization_rules
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(incomplete_config, f)
            config_path = f.name
        
        try:
            with pytest.raises((KeyError, ValueError, AttributeError, ConfigurationError)):
                config = ConfigLoader(config_path).load()
                anonymizer = Anonymizer(config)
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_empty_dataset(self, gdpr_config):
        """Test handling of empty dataset"""
        df_empty = pd.DataFrame()
        
        scanner = PIIScanner()
        # Empty dataframe should return empty scan results, not raise error
        scan_results = scanner.scan_dataframe(df_empty)
        assert isinstance(scan_results, dict)
        assert len(scan_results) == 0  # No columns to scan


class TestRegressionPrevention:
    """Tests to prevent regression of known issues"""
    
    def test_consistent_anonymization(self, sample_customer_data, gdpr_config):
        """Test that same input produces same output (for pseudonymization)"""
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(sample_customer_data)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        anonymizer = Anonymizer(gdpr_config)
        
        df_anon_1 = anonymizer.anonymize(sample_customer_data.copy(), column_mapping)
        df_anon_2 = anonymizer.anonymize(sample_customer_data.copy(), column_mapping)
        
        # For consistent techniques (hash, pseudonymize), output should be identical
        pd.testing.assert_frame_equal(df_anon_1, df_anon_2)
    
    def test_no_data_leakage(self, sample_customer_data, gdpr_config):
        """Test that original PII doesn't leak into anonymized data"""
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(sample_customer_data)
        column_mapping = scan_results_to_column_mapping(scan_results)
        
        anonymizer = Anonymizer(gdpr_config)
        df_anon = anonymizer.anonymize(sample_customer_data, column_mapping)
        
        # Check that original emails don't appear in anonymized data
        original_emails = set(sample_customer_data['email'].unique())
        anonymized_emails = set(df_anon['email'].unique())
        
        intersection = original_emails.intersection(anonymized_emails)
        assert len(intersection) == 0, f"Data leakage detected: {intersection}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])