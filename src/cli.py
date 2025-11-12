
"""
Enhanced CLI for Data Anonymization Pipeline
Supports preset configurations, custom configs, and comprehensive reporting
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from datetime import datetime

# Assuming these imports from your existing codebase
# Adjust import paths based on your actual structure
try:
    from src.scanner import PIIScanner
    from src.anonymizer import Anonymizer
    from src.risk_assessment import RiskAssessmentEngine, infer_quasi_identifiers
    from src.utility_metrics import UtilityMetrics
    from src.privacy_validator import PrivacyValidator
    from src.report.compliance_report import ComplianceReportGenerator
    from src.config_loader import ConfigLoader
    import pandas as pd
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    print("This CLI expects your pipeline components to be installed.")


class AnonymizationCLI:
    """Enhanced CLI for the anonymization pipeline"""
    
    PRESET_DIR = Path(__file__).parent.parent / "config" / "presets"
    
    AVAILABLE_PRESETS = {
        "gdpr_compliant": "Conservative GDPR compliance (k=10, max privacy)",
        "ml_training": "Optimized for ML training (k=5, max utility)",
        "vendor_sharing": "Balanced for vendor sharing (k=7, balanced approach)"
    }
    
    def __init__(self):
        self.parser = self._build_parser()
    
    def _build_parser(self) -> argparse.ArgumentParser:
        """Build the argument parser with all commands"""
        parser = argparse.ArgumentParser(
            description="Data Anonymization Pipeline - Privacy-preserving data transformation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Scan a file for PII and assess risk
  %(prog)s scan --file data/customers.csv
  
  # Anonymize using GDPR preset
  %(prog)s anonymize --file data/customers.csv --preset gdpr_compliant --output data/customers_anon.csv
  
  # Anonymize with custom config
  %(prog)s anonymize --file data/customers.csv --config custom_rules.yaml --output data/output.csv
  
  # Generate full compliance report
  %(prog)s anonymize --file data/customers.csv --preset gdpr_compliant --report --output data/anonymized.csv
  
  # List available presets
  %(prog)s list-presets
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Scan command
        scan_parser = subparsers.add_parser(
            "scan",
            help="Scan file for PII and assess re-identification risk"
        )
        scan_parser.add_argument(
            "--file",
            required=True,
            help="Input file path (CSV or JSON)"
        )
        scan_parser.add_argument(
            "--output",
            help="Output file for scan results (JSON)"
        )
        scan_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed detection information"
        )
        
        # Anonymize command
        anon_parser = subparsers.add_parser(
            "anonymize",
            help="Anonymize data using specified configuration"
        )
        anon_parser.add_argument(
            "--file",
            required=True,
            help="Input file path (CSV or JSON)"
        )
        anon_parser.add_argument(
            "--output",
            required=True,
            help="Output file for anonymized data"
        )
        
        # Config options (mutually exclusive)
        config_group = anon_parser.add_mutually_exclusive_group(required=True)
        config_group.add_argument(
            "--preset",
            choices=list(self.AVAILABLE_PRESETS.keys()),
            help="Use a predefined preset configuration"
        )
        config_group.add_argument(
            "--config",
            help="Path to custom YAML configuration file"
        )
        
        anon_parser.add_argument(
            "--report",
            action="store_true",
            help="Generate compliance and utility report"
        )
        anon_parser.add_argument(
            "--report-output",
            help="Output path for report (default: <output_dir>/report.html)"
        )
        anon_parser.add_argument(
            "--skip-validation",
            action="store_true",
            help="Skip privacy validation checks (not recommended)"
        )
        anon_parser.add_argument(
            "--force",
            action="store_true",
            help="Force anonymization even if validation fails"
        )
        
        # Validate command
        validate_parser = subparsers.add_parser(
            "validate",
            help="Validate anonymized data against privacy requirements"
        )
        validate_parser.add_argument(
            "--file",
            required=True,
            help="Anonymized file to validate"
        )
        validate_parser.add_argument(
            "--original",
            help="Original file (for utility comparison)"
        )
        validate_parser.add_argument(
            "--config",
            help="Configuration file with validation thresholds"
        )
        validate_parser.add_argument(
            "--preset",
            choices=list(self.AVAILABLE_PRESETS.keys()),
            help="Use preset validation thresholds"
        )
        
        # Report command
        report_parser = subparsers.add_parser(
            "report",
            help="Generate compliance report for anonymized data"
        )
        report_parser.add_argument(
            "--file",
            required=True,
            help="Anonymized file"
        )
        report_parser.add_argument(
            "--original",
            help="Original file (for comparison)"
        )
        report_parser.add_argument(
            "--output",
            default="compliance_report.html",
            help="Output path for report"
        )
        report_parser.add_argument(
            "--format",
            choices=["html", "markdown", "json"],
            default="html",
            help="Report format"
        )
        
        # List presets command
        list_parser = subparsers.add_parser(
            "list-presets",
            help="List available configuration presets"
        )
        list_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed preset information"
        )
        
        return parser
    
    def _transform_preset_format(self, preset_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform preset format to ConfigLoader format
        
        Preset format uses:
        - anonymization_rules (instead of rules)
        - technique (instead of strategy)
        - params (instead of parameters)
        
        Args:
            preset_config: Preset configuration dictionary
            
        Returns:
            Transformed config compatible with ConfigLoader
        """
        transformed = preset_config.copy()
        
        # Transform anonymization_rules to rules if present
        if "anonymization_rules" in transformed:
            rules = {}
            for pii_type, rule_data in transformed["anonymization_rules"].items():
                if isinstance(rule_data, dict):
                    technique = rule_data.get("technique")
                    
                    # Skip "preserve" and "add_noise" techniques - not yet implemented
                    if technique in ["preserve", "add_noise"]:
                        continue
                    
                    transformed_rule = {}
                    params = rule_data.get("params", {})
                    
                    # Convert technique -> strategy
                    if technique:
                        transformed_rule["strategy"] = technique
                    
                    # Transform parameters based on strategy
                    transformed_params = self._transform_parameters(pii_type, technique, params)
                    if transformed_params is not None:
                        transformed_rule["parameters"] = transformed_params
                    
                    rules[pii_type] = transformed_rule
            
            transformed["rules"] = rules
            # Remove old key
            del transformed["anonymization_rules"]
        
        return transformed
    
    def _transform_parameters(self, pii_type: str, technique: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform preset parameters to ConfigLoader-expected format
        
        Args:
            pii_type: The PII type (e.g., 'address', 'age')
            technique: The anonymization technique
            params: Original preset parameters
            
        Returns:
            Transformed parameters, or None to omit parameters
        """
        if not params:
            return {}
            
        if technique == "generalize":
            # Handle generalize strategy parameter transformations
            if "method" in params:
                method = params.get("method")
                
                # Address generalization - map to 'level' parameter
                if method in ["city_state_only", "state_only", "country_only"]:
                    # Address: map descriptive method names to valid levels
                    # Valid levels: ['full', 'street', 'city', 'state', 'country']
                    method_to_level = {
                        "city_state_only": "city",
                        "state_only": "state",
                        "country_only": "country"
                    }
                    level = method_to_level.get(method, "city")
                    return {"level": level}
                
                elif method == "truncate":
                    # Zipcode: keep_digits -> precision
                    if "keep_digits" in params:
                        return {"precision": params["keep_digits"]}
                    else:
                        return {"precision": 3}  # default to 3 digits
                
                elif method == "round":
                    # Timestamp/datetime rounding
                    if "precision" in params:
                        return {"granularity": params["precision"]}
                    else:
                        return {"granularity": "day"}
                
                elif method == "subnet":
                    # IP address: subnet_mask -> octets
                    if "subnet_mask" in params:
                        octets = params["subnet_mask"] // 8  # Convert /16 to 2 octets
                        return {"octets": octets}
                    else:
                        return {"octets": 2}  # default to 2 octets
                
                elif method == "year_only":
                    # Date: map to granularity
                    # ConfigLoader allows: ["day", "week", "month", "quarter", "year"]
                    format_val = params.get("format", "year")
                    # Map descriptive formats to valid granularities
                    if format_val == "decade":
                        return {"granularity": "year"}
                    elif format_val in ["day", "week", "month", "quarter", "year"]:
                        return {"granularity": format_val}
                    else:
                        return {"granularity": "year"}  # default
                
                elif method == "bins":
                    # Numeric binning - ensure min_value and max_value are present
                    result = {k: v for k, v in params.items() if k in ["bin_size", "min_value", "max_value", "format"]}
                    # Add defaults if missing based on PII type
                    if "min_value" not in result:
                        result["min_value"] = 0
                    if "max_value" not in result:
                        # Set sensible max based on PII type
                        max_defaults = {
                            "age": 120,
                            "income": 10000000,
                            "salary": 10000000,
                        }
                        result["max_value"] = max_defaults.get(pii_type, 1000000)
                    return result
            
            # For other cases, check if we already have the right parameters
            if "precision" in params or "granularity" in params or "level" in params or "octets" in params:
                # Filter to only keep expected params
                return {k: v for k, v in params.items() 
                       if k in ["precision", "granularity", "level", "octets", "bin_size", "min_value", "max_value", "format"]}
            
            # Numeric binning - keep these params
            if "bin_size" in params:
                result = {k: v for k, v in params.items() if k in ["bin_size", "min_value", "max_value", "format"]}
                # Add default min/max if missing
                if "min_value" not in result:
                    result["min_value"] = 0
                if "max_value" not in result:
                    result["max_value"] = 100
                return result
            
            # If we get here with generalize but no recognized params, return empty
            # (ConfigLoader will validate and report error if needed)
            return {}
        
        elif technique == "pseudonymize":
            # Transform pseudonymize parameters
            result = params.copy()
            
            # Map 'consistent' to 'seed_based' (required by ConfigLoader)
            if "consistent" in result:
                result["seed_based"] = result.pop("consistent")
            
            # Ensure seed_based is present (required)
            if "seed_based" not in result:
                result["seed_based"] = True
            
            return result
        
        elif technique == "preserve":
            # Preserve technique might have validation params we don't need for ConfigLoader
            return {}
        
        # For other techniques (hash, redact_full, redact_partial), return params as-is
        return params
    
    def load_config(self, preset: Optional[str] = None, 
                   config_path: Optional[str] = None) -> tuple[ConfigLoader, Dict[str, Any]]:
        """Load configuration from preset or custom file
        
        Returns:
            Tuple of (ConfigLoader instance, raw config dict)
        """
        if preset:
            preset_file = self.PRESET_DIR / f"{preset}.yaml"
            if not preset_file.exists():
                raise FileNotFoundError(f"Preset '{preset}' not found at {preset_file}")
            config_path = preset_file
        
        if not config_path:
            raise ValueError("Must specify either --preset or --config")
        
        # Load raw config
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Transform preset format to ConfigLoader format if needed
        transformed_config = self._transform_preset_format(raw_config)
        
        # Debug: Print first few transformed rules (if verbose)
        if transformed_config.get("rules"):
            import os
            if os.environ.get("DEBUG_CLI"):
                print("\n[DEBUG] Sample transformed rules:")
                for pii_type, rule in list(transformed_config["rules"].items())[:3]:
                    print(f"  {pii_type}: {rule}")
        
        # Write transformed config to a temporary file for ConfigLoader
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
            yaml.dump(transformed_config, tmp_file)
            tmp_config_path = tmp_file.name
        
        try:
            # Load with ConfigLoader for structured access (needed by Anonymizer)
            config_loader = ConfigLoader(tmp_config_path)
            config_loader.load()
        finally:
            # Clean up temp file
            Path(tmp_config_path).unlink(missing_ok=True)
        
        return config_loader, raw_config
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from CSV or JSON"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix == ".csv":
            return pd.read_csv(file_path)
        elif path.suffix == ".json":
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def save_data(self, df: pd.DataFrame, output_path: str):
        """Save data to CSV or JSON"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix == ".csv":
            df.to_csv(output_path, index=False)
        elif path.suffix == ".json":
            df.to_json(output_path, orient="records", indent=2)
        else:
            raise ValueError(f"Unsupported output format: {path.suffix}")
    
    def cmd_scan(self, args):
        """Execute scan command"""
        print(f"🔍 Scanning {args.file} for PII...")
        
        # Load data
        df = self.load_data(args.file)
        print(f"   Loaded {len(df)} records with {len(df.columns)} columns")
        
        # Initialize scanner
        scanner = PIIScanner()
        
        # Scan for PII
        scan_results = scanner.scan_dataframe(df)
        
        # Assess risk
        print("\n📊 Assessing re-identification risk...")
        risk_assessor = RiskAssessmentEngine()
        
        # Infer quasi-identifiers from scan results
        quasi_ids = infer_quasi_identifiers(df, scan_results)
        
        if quasi_ids:
            print(f"   Identified quasi-identifiers: {', '.join(quasi_ids)}")
            # Create QI sets to test
            qi_sets = [quasi_ids]  # Test all QIs together
            # Also test individual QIs
            for qi in quasi_ids[:3]:  # Limit to first 3 to avoid too many combinations
                qi_sets.append([qi])
            
            risk_scores, risk_report = risk_assessor.assess_dataset(df, qi_sets)
            risk_results = {'scores': risk_scores, 'report': risk_report}
        else:
            print("   No quasi-identifiers detected, skipping risk assessment")
            risk_results = None
        
        # Display results
        self._display_scan_results(scan_results, risk_results)
        
        # Save results if requested
        if args.output:
            output_data = {
                "scan_timestamp": datetime.now().isoformat(),
                "input_file": args.file,
                "record_count": len(df),
                "pii_detections": scan_results,
                "risk_assessment": risk_results
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\n💾 Results saved to {args.output}")
    
    def cmd_anonymize(self, args):
        """Execute anonymize command"""
        print(f"🔒 Anonymizing {args.file}...")
        
        # Load configuration
        config_loader, raw_config = self.load_config(preset=args.preset, config_path=args.config)
        config_name = args.preset or Path(args.config).stem
        print(f"   Using configuration: {config_name}")
        
        # Load data
        df_original = self.load_data(args.file)
        print(f"   Loaded {len(df_original)} records")
        
        # Scan first (needed for anonymization decisions)
        scanner = PIIScanner()
        scan_results = scanner.scan_dataframe(df_original)
        
        # Convert scan results to column mapping (column_name -> pii_type)
        column_mapping = {}
        for field_name, detection_result in scan_results.items():
            if detection_result.pii_types:
                # Use the first (highest confidence) PII type detected
                column_mapping[field_name] = detection_result.pii_types[0]
        
        if column_mapping:
            print(f"\n🔍 Detected PII in {len(column_mapping)} columns:")
            for col, pii_type in column_mapping.items():
                print(f"   {col} → {pii_type}")
        else:
            print("\n⚠️  No PII detected in the dataset")
        
        # Anonymize
        print("\n⚙️  Applying anonymization techniques...")
        anonymizer = Anonymizer(config_loader)
        df_anonymized = anonymizer.anonymize(df_original, column_mapping)
        
        # Validate unless skipped
        validation_passed = True
        validation_results = None
        if not args.skip_validation:
            print("\n✓ Validating privacy guarantees...")
            validator = PrivacyValidator(raw_config)
            validation_results = validator.validate(df_anonymized, df_original)
            validation_passed = validation_results["passed"]
            
            self._display_validation_results(validation_results)
            
            if not validation_passed and not args.force:
                print("\n❌ Validation failed. Use --force to save anyway.")
                return 1
        
        # Save anonymized data
        self.save_data(df_anonymized, args.output)
        print(f"\n💾 Anonymized data saved to {args.output}")
        
        # Generate report if requested
        if args.report:
            report_path = args.report_output or \
                         str(Path(args.output).parent / "compliance_report.html")
            self._generate_report(
                df_original, 
                df_anonymized, 
                raw_config,
                scan_results,
                validation_results,
                report_path
            )
        
        return 0
    
    def cmd_validate(self, args):
        """Execute validate command"""
        print(f"✓ Validating {args.file}...")
        
        # Load config
        config_loader, raw_config = self.load_config(preset=args.preset, config_path=args.config)
        
        # Load data
        df_anonymized = self.load_data(args.file)
        df_original = self.load_data(args.original) if args.original else None
        
        # Validate
        validator = PrivacyValidator(raw_config)
        results = validator.validate(df_anonymized, df_original)
        
        self._display_validation_results(results)
        
        return 0 if results["passed"] else 1
    
    def cmd_report(self, args):
        """Execute report command"""
        print(f"📄 Generating report for {args.file}...")
        
        df_anonymized = self.load_data(args.file)
        df_original = self.load_data(args.original) if args.original else None
        
        # Generate report
        generator = ComplianceReportGenerator()
        report = generator.generate(
            df_original,
            df_anonymized,
            output_format=args.format
        )
        
        # Save report
        with open(args.output, 'w') as f:
            f.write(report)
        
        print(f"💾 Report saved to {args.output}")
    
    def cmd_list_presets(self, args):
        """Execute list-presets command"""
        print("\n📋 Available Anonymization Presets:\n")
        
        for preset_name, description in self.AVAILABLE_PRESETS.items():
            print(f"  • {preset_name}")
            print(f"    {description}")
            
            if args.verbose:
                preset_file = self.PRESET_DIR / f"{preset_name}.yaml"
                if preset_file.exists():
                    with open(preset_file, 'r') as f:
                        config = yaml.safe_load(f)
                    metadata = config.get("metadata", {})
                    thresholds = config.get("privacy_thresholds", {})
                    
                    print(f"    Use case: {metadata.get('use_case', 'N/A')}")
                    print(f"    Min k-anonymity: {metadata.get('min_k_anonymity', 'N/A')}")
                    print(f"    Target risk: {metadata.get('target_reidentification_risk', 'N/A')}")
                print()
    
    def _display_scan_results(self, scan_results: Dict, risk_results: Optional[Dict]):
        """Display scan and risk results in a formatted way"""
        print("\n" + "="*60)
        print("PII DETECTION RESULTS")
        print("="*60)
        
        if scan_results:
            print("\n🔴 PII Detected in the following columns:")
            for field_name, detection_result in scan_results.items():
                pii_types_str = ', '.join(detection_result.pii_types)
                print(f"   {field_name}: {pii_types_str} (confidence: {detection_result.confidence:.2f})")
        else:
            print("\n🟢 No PII detected")
        
        if risk_results:
            print("\n" + "="*60)
            print("RISK ASSESSMENT")
            print("="*60)
            
            risk_report = risk_results['report']
            print(f"\n   High Risk:   {risk_report.high_risk_count:>6} records ({risk_report.high_risk_percentage:.1f}%)")
            print(f"   Medium Risk: {risk_report.medium_risk_count:>6} records ({risk_report.medium_risk_percentage:.1f}%)")
            print(f"   Low Risk:    {risk_report.low_risk_count:>6} records ({risk_report.low_risk_percentage:.1f}%)")
            
            print(f"\n   Minimum k-anonymity: {risk_report.min_k_anonymity}")
            print(f"   Average k-anonymity: {risk_report.average_k_anonymity:.1f}")
    
    def _display_validation_results(self, results: Dict):
        """Display validation results"""
        print("\n" + "="*60)
        print("PRIVACY VALIDATION RESULTS")
        print("="*60)
        
        status = "✓ PASSED" if results["passed"] else "❌ FAILED"
        print(f"\nOverall Status: {status}\n")
        
        for check_name, check_result in results.get("checks", {}).items():
            icon = "✓" if check_result["passed"] else "❌"
            print(f"   {icon} {check_name}: {check_result.get('message', '')}")
    
    def _convert_utility_report_to_dict(self, utility_report) -> Dict[str, Any]:
        """Convert UtilityReport object to dictionary format for report generator"""
        from dataclasses import asdict
        
        # Convert dataclass to dict (handles nested dataclasses)
        utility_dict = asdict(utility_report)
        
        # Add simple summary metrics for backwards compatibility
        utility_dict['overall_utility_score'] = utility_report.overall_utility_score
        utility_dict['correlation_preservation'] = (
            utility_report.correlation_metrics.correlation_similarity 
            if utility_report.correlation_metrics else None
        )
        
        # Calculate average distribution preservation
        if utility_report.distribution_metrics:
            avg_dist = sum(
                (1 - m.ks_statistic) for m in utility_report.distribution_metrics.values()
            ) / len(utility_report.distribution_metrics)
            utility_dict['distribution_similarity'] = avg_dist
        else:
            utility_dict['distribution_similarity'] = None
        
        # Calculate average information retention
        if utility_report.information_loss_metrics:
            avg_retention = sum(
                (m.unique_values_retained_pct + m.entropy_retained_pct) / 200  # normalize to 0-1
                for m in utility_report.information_loss_metrics.values()
            ) / len(utility_report.information_loss_metrics)
            utility_dict['information_retention'] = avg_retention
        else:
            utility_dict['information_retention'] = None
        
        return utility_dict
    
    def _generate_report(self, df_original, df_anonymized, config, 
                        scan_results, validation_results, output_path):
        """Generate comprehensive compliance report"""
        print(f"\n📊 Generating compliance report...")
        
        # Calculate utility metrics
        utility_analyzer = UtilityMetrics(df_original, df_anonymized)
        utility_report = utility_analyzer.generate_report()
        
        # Convert UtilityReport object to dictionary for the report generator
        utility_metrics = self._convert_utility_report_to_dict(utility_report)
        
        # Generate report
        generator = ComplianceReportGenerator()
        report = generator.generate(
            original_data=df_original,
            anonymized_data=df_anonymized,
            config=config,
            scan_results=scan_results,
            validation_results=validation_results,
            utility_metrics=utility_metrics,
            output_format="html"
        )
        
        # Save with UTF-8 encoding to handle Unicode characters
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"   Report saved to {output_path}")
    
    def run(self):
        """Main entry point"""
        # Fix encoding for Windows
        import io
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return 0
        
        try:
            # Dispatch to command handler
            handler = getattr(self, f"cmd_{args.command.replace('-', '_')}")
            return handler(args)
        
        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main():
    """CLI entry point"""
    cli = AnonymizationCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
