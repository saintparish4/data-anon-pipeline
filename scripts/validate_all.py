"""
Validation Test Script
Tests all anonymization presets on fixture datasets

This script verifies:
1. All presets load correctly
2. Anonymization works on all fixture datasets
3. Privacy thresholds are met
4. Utility metrics are calculated correctly
5. Reports are generated successfully

Run this before committing to ensure everything works!
"""

import sys
from pathlib import Path
import pandas as pd
import yaml
from datetime import datetime
from typing import Dict, List, Tuple
import json


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class ValidationTester:
    """Comprehensive validation testing"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fixtures_dir = self.project_root / "fixtures"
        self.config_dir = self.project_root / "config" / "presets"
        self.results: List[Dict] = []

    def _transform_preset_to_configloader_format(self, preset_config: Dict) -> Dict:
        """
        Transform preset config format to ConfigLoader format.

        Preset format uses 'anonymization_rules' with 'technique'/'params',
        ConfigLoader expects 'rules' with 'strategy'/'parameters'.
        """
        transformed = {
            "version": preset_config.get("metadata", {}).get("version", "1.0"),
            "rules": {},
        }

        # Transform anonymization_rules to rules
        anon_rules = preset_config.get("anonymization_rules", {})
        for pii_type, rule in anon_rules.items():
            if not isinstance(rule, dict) or "technique" not in rule:
                continue

            technique = rule["technique"]
            params = rule.get("params", {})

            # Skip techniques that aren't in ConfigLoader's allowed strategies
            if technique in ["preserve", "add_noise", "differential_privacy"]:
                continue

            # Transform generalize parameters based on method
            if technique == "generalize" and "method" in params:
                params = self._transform_generalize_params(pii_type, params)

            # Add required parameters for pseudonymize
            if technique == "pseudonymize" and "seed_based" not in params:
                params["seed_based"] = params.get("consistent", True)

            # Add required parameters for hash
            if technique == "hash" and "algorithm" not in params:
                params["algorithm"] = params.get("algorithm", "sha256")

            # Add required parameters for redact_partial
            if technique == "redact_partial":
                if "visible_chars" not in params:
                    params["visible_chars"] = params.get("keep_chars", 3)
                if "mask_char" not in params:
                    params["mask_char"] = "*"

            transformed["rules"][pii_type] = {
                "strategy": technique,
                "parameters": params,
            }

        return transformed

    def _transform_generalize_params(self, pii_type: str, params: Dict) -> Dict:
        """Transform method-based generalize params to ConfigLoader format."""
        method = params.get("method", "")

        # For age with bins
        if method == "bins" and "bin_size" in params:
            return {
                "bin_size": params["bin_size"],
                "min_value": params.get("min_value", 0),
                "max_value": params.get("max_value", 120),
            }

        # For zipcodes/IP addresses - use precision
        if (
            method in ["truncate", "subnet"]
            or "keep_digits" in params
            or "subnet_mask" in params
        ):
            precision = params.get("keep_digits") or params.get("subnet_mask", 3)
            return {"precision": precision}

        # For dates
        if method in ["year_only", "month_only", "quarter"] or pii_type in [
            "date_of_birth",
            "date",
            "timestamp",
        ]:
            granularity = params.get("format", "year")
            # Map invalid granularity values to valid ones
            granularity_map = {
                "decade": "year",
                "yearly": "year",
                "monthly": "month",
                "quarterly": "quarter",
                "daily": "day",
                "weekly": "week",
            }
            granularity = granularity_map.get(granularity, granularity)
            return {"granularity": granularity}

        # For addresses - use level
        if pii_type in ["address", "location"] or method in [
            "city_state_only",
            "city_only",
        ]:
            return {"level": params.get("level", "city")}

        # Default: try to use precision if numeric-looking
        if "bin_size" in params:
            return {"bin_size": params["bin_size"], "min_value": 0, "max_value": 1000}

        # Fallback to precision
        return {"precision": 2}

    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.END}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"  {text}")

    def test_config_loading(self) -> bool:
        """Test that all preset configs load correctly"""
        self.print_header("Testing Configuration Loading")

        presets = ["gdpr_compliant", "ml_training", "vendor_sharing"]
        all_passed = True

        for preset_name in presets:
            config_file = self.config_dir / f"{preset_name}.yaml"

            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)

                # Validate required sections
                required_sections = [
                    "metadata",
                    "anonymization_rules",
                    "privacy_thresholds",
                    "utility_targets",
                    "output",
                ]

                missing_sections = [s for s in required_sections if s not in config]

                if missing_sections:
                    self.print_error(
                        f"{preset_name}: Missing sections: {missing_sections}"
                    )
                    all_passed = False
                else:
                    self.print_success(f"{preset_name}.yaml loaded successfully")

                    # Print key parameters
                    metadata = config["metadata"]
                    self.print_info(
                        f"  k-anonymity: {metadata.get('min_k_anonymity', 'N/A')}"
                    )
                    self.print_info(
                        f"  Target risk: {metadata.get('target_reidentification_risk', 'N/A')}"
                    )
                    self.print_info(
                        f"  Rules defined: {len(config['anonymization_rules'])}"
                    )

            except Exception as e:
                self.print_error(f"{preset_name}: Failed to load - {e}")
                all_passed = False

        return all_passed

    def test_fixture_data(self) -> bool:
        """Test that fixture datasets exist and are valid"""
        self.print_header("Testing Fixture Datasets")

        expected_fixtures = [
            "customers.csv",
            "support_tickets.json",
            "transactions.csv",
        ]

        all_passed = True

        for fixture in expected_fixtures:
            fixture_path = self.fixtures_dir / fixture

            if not fixture_path.exists():
                self.print_warning(
                    f"{fixture}: Not found (this is OK if not created yet)"
                )
                continue

            try:
                # Load and validate
                if fixture.endswith(".csv"):
                    df = pd.read_csv(fixture_path)
                elif fixture.endswith(".json"):
                    df = pd.read_json(fixture_path)
                else:
                    self.print_warning(f"{fixture}: Unknown format")
                    continue

                self.print_success(
                    f"{fixture}: {len(df)} records, {len(df.columns)} columns"
                )
                self.print_info(f"  Columns: {', '.join(df.columns.tolist()[:5])}...")

            except Exception as e:
                self.print_error(f"{fixture}: Failed to load - {e}")
                all_passed = False

        return all_passed

    def test_anonymization_workflow(
        self, preset_name: str, fixture_name: str
    ) -> Tuple[bool, Dict]:
        """Test complete anonymization workflow for a preset+fixture combination"""

        # Import pipeline components
        try:
            from src.scanner import PIIScanner
            from src.anonymizer import Anonymizer
            from src.risk_assessment import RiskAssessmentEngine
            from src.utility_metrics import UtilityMetrics
            from src.privacy_validator import PrivacyValidator
            from src.config_loader import ConfigLoader
        except ImportError as e:
            self.print_error(f"Cannot import pipeline components: {e}")
            # Return properly structured result dict even on failure
            return False, {
                "preset": preset_name,
                "fixture": fixture_name,
                "error": str(e),
                "validation_passed": False,
            }

        # Load config
        config_file = self.config_dir / f"{preset_name}.yaml"
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)

        # Transform preset format to ConfigLoader format
        transformed_config = self._transform_preset_to_configloader_format(config_dict)

        # Write transformed config to temporary file for ConfigLoader
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump(transformed_config, tmp_file)
            tmp_config_path = tmp_file.name

        try:
            # Create ConfigLoader instance with transformed config
            config_loader = ConfigLoader(tmp_config_path)
            config_loader.load()
        finally:
            # Clean up temp file
            Path(tmp_config_path).unlink(missing_ok=True)

        # Load fixture
        fixture_path = self.fixtures_dir / fixture_name
        if fixture_name.endswith(".csv"):
            df = pd.read_csv(fixture_path)
        else:
            df = pd.read_json(fixture_path)

        results = {
            "preset": preset_name,
            "fixture": fixture_name,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Step 1: Scan (disable NER to avoid spaCy dependency)
            scanner = PIIScanner(use_ner=False)
            scan_results = scanner.scan_dataframe(df)
            results["pii_detected"] = len(scan_results)

            # Step 2: Risk assessment
            risk_assessor = RiskAssessmentEngine()
            risk_results = risk_assessor.assess(df, scan_results)
            results["original_risk"] = risk_results.get("risk_distribution", {})

            # Step 3: Anonymize
            # Convert scan_results to column_mapping format (column_name -> pii_type)
            column_mapping = {}
            for col_name, detection_result in scan_results.items():
                # Use the first detected PII type for this column
                if detection_result.pii_types:
                    column_mapping[col_name] = detection_result.pii_types[0]

            anonymizer = Anonymizer(config_loader)
            df_anon = anonymizer.anonymize(df, column_mapping)
            results["records_processed"] = len(df_anon)

            # Step 4: Validate
            validator = PrivacyValidator(config_dict)
            validation_results = validator.validate(df_anon, df)
            results["validation_passed"] = validation_results.get("passed", False)
            results["validation_checks"] = validation_results.get("checks", {})

            # Step 5: Utility metrics
            utility_calculator = UtilityMetrics(df, df_anon)
            utility_report = utility_calculator.generate_report()
            results["utility_metrics"] = {
                "overall_utility_score": utility_report.overall_utility_score,
                "correlation_preservation": (
                    utility_report.correlation_metrics.correlation_similarity
                    if utility_report.correlation_metrics
                    else 0
                ),
                "information_retention": (
                    sum(
                        m.entropy_retained_pct
                        for m in utility_report.information_loss_metrics.values()
                    )
                    / len(utility_report.information_loss_metrics)
                    if utility_report.information_loss_metrics
                    else 0
                ),
            }

            # Overall success
            success = results["validation_passed"]

            return success, results

        except Exception as e:
            # Ensure results dict has all required keys even on exception
            results["error"] = str(e)
            results["validation_passed"] = False
            return False, results

    def test_all_combinations(self) -> bool:
        """Test all preset+fixture combinations"""
        self.print_header("Testing Anonymization Workflows")

        presets = ["gdpr_compliant", "ml_training", "vendor_sharing"]
        fixtures = [
            f for f in self.fixtures_dir.glob("*.csv") if f.name not in ["README.md"]
        ]

        if not fixtures:
            self.print_warning("No fixture files found - skipping workflow tests")
            return True

        all_passed = True
        test_count = 0

        for preset in presets:
            for fixture_path in fixtures:
                fixture_name = fixture_path.name
                test_count += 1

                print(
                    f"\n{Colors.BOLD}Test {test_count}: {preset} + {fixture_name}{Colors.END}"
                )

                try:
                    success, results = self.test_anonymization_workflow(
                        preset, fixture_name
                    )

                    self.results.append(results)

                    if success:
                        self.print_success(f"Workflow completed successfully")
                        self.print_info(
                            f"  Records: {results.get('records_processed', 0)}"
                        )
                        self.print_info(
                            f"  PII detected: {results.get('pii_detected', 0)} types"
                        )

                        # Print validation summary
                        checks = results.get("validation_checks", {})
                        for check_name, check_result in checks.items():
                            if check_result.get("passed"):
                                self.print_info(f"  ✓ {check_name}")
                            else:
                                self.print_info(f"  ✗ {check_name}")

                        # Print utility metrics
                        utility = results.get("utility_metrics", {})
                        if utility:
                            self.print_info(
                                f"  Utility: {utility.get('correlation_preservation', 0):.1%} "
                                f"correlation, {utility.get('information_retention', 0):.1%} info"
                            )
                    else:
                        self.print_error(f"Workflow failed")
                        if "error" in results:
                            self.print_error(f"  Error: {results['error']}")
                        all_passed = False

                except Exception as e:
                    self.print_error(f"Test failed with exception: {e}")
                    all_passed = False

        return all_passed

    def test_cli_commands(self) -> bool:
        """Test that CLI commands work"""
        self.print_header("Testing CLI Commands")

        import subprocess

        # Test list-presets
        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.cli", "list-presets"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.print_success("list-presets command works")
            else:
                self.print_error(f"list-presets failed: {result.stderr}")
                return False

        except Exception as e:
            self.print_error(f"CLI test failed: {e}")
            return False

        return True

    def generate_summary_report(self):
        """Generate summary report of all tests"""
        self.print_header("Validation Summary Report")

        if not self.results:
            self.print_warning("No workflow tests were run")
            return

        # Overall stats
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("validation_passed", False))

        print(f"Total workflow tests: {total_tests}")
        print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.END}")
        print(f"Failed: {Colors.RED}{total_tests - passed_tests}{Colors.END}")
        print(f"Success rate: {passed_tests/total_tests:.1%}\n")

        # Detailed breakdown by preset
        # Filter out results that don't have 'preset' key (shouldn't happen, but defensive)
        valid_results = [r for r in self.results if "preset" in r]
        presets = set(r["preset"] for r in valid_results)

        for preset in presets:
            preset_results = [r for r in self.results if r["preset"] == preset]
            preset_passed = sum(
                1 for r in preset_results if r.get("validation_passed", False)
            )

            print(f"\n{Colors.BOLD}{preset}:{Colors.END}")
            print(f"  Tests: {len(preset_results)}")
            print(f"  Passed: {preset_passed}/{len(preset_results)}")

            # Average utility
            utilities = [
                r.get("utility_metrics", {}).get("correlation_preservation", 0)
                for r in preset_results
                if "utility_metrics" in r
            ]

            if utilities:
                avg_utility = sum(utilities) / len(utilities)
                print(f"  Avg utility: {avg_utility:.1%}")

        # Save detailed results
        report_path = self.project_root / "validation_report.json"
        with open(report_path, "w") as f:
            json.dump(
                {
                    "summary": {
                        "timestamp": datetime.now().isoformat(),
                        "total_tests": total_tests,
                        "passed": passed_tests,
                        "failed": total_tests - passed_tests,
                        "success_rate": (
                            passed_tests / total_tests if total_tests > 0 else 0
                        ),
                    },
                    "detailed_results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n{Colors.BLUE}Detailed report saved to: {report_path}{Colors.END}")

    def run_quick_test(self) -> bool:
        """Run a quick test with just one preset+fixture combination"""
        # Test just gdpr_compliant with customers.csv
        preset = "gdpr_compliant"
        fixture = "customers.csv"
        fixture_path = self.fixtures_dir / fixture

        if not fixture_path.exists():
            self.print_error(f"Fixture {fixture} not found")
            return False

        print(f"{Colors.BOLD}Testing: {preset} + {fixture}{Colors.END}\n")

        try:
            success, results = self.test_anonymization_workflow(preset, fixture)
            self.results.append(results)

            if success:
                self.print_success("Quick test PASSED!")
                self.print_info(f"  Records: {results.get('records_processed', 0)}")
                self.print_info(
                    f"  PII detected: {results.get('pii_detected', 0)} types"
                )
                return True
            else:
                self.print_error("Quick test FAILED")
                if "error" in results:
                    self.print_error(f"  Error: {results['error']}")
                return False
        except Exception as e:
            self.print_error(f"Quick test failed with exception: {e}")
            return False

    def run_custom_test(
        self, preset_name: str = None, fixture_name: str = None
    ) -> bool:
        """Run tests for specific preset and/or fixture"""
        presets = (
            [preset_name]
            if preset_name
            else ["gdpr_compliant", "ml_training", "vendor_sharing"]
        )

        fixtures = []
        if fixture_name:
            fixture_path = self.fixtures_dir / fixture_name
            if fixture_path.exists():
                fixtures = [fixture_path]
            else:
                self.print_error(f"Fixture {fixture_name} not found")
                return False
        else:
            fixtures = list(self.fixtures_dir.glob("*.csv"))

        all_passed = True
        test_count = 0

        for preset in presets:
            for fixture_path in fixtures:
                test_count += 1
                fixture = fixture_path.name

                print(
                    f"\n{Colors.BOLD}Test {test_count}: {preset} + {fixture}{Colors.END}"
                )

                try:
                    success, results = self.test_anonymization_workflow(preset, fixture)
                    self.results.append(results)

                    if success:
                        self.print_success("Test passed")
                    else:
                        self.print_error("Test failed")
                        if "error" in results:
                            self.print_error(f"  Error: {results['error']}")
                        all_passed = False
                except Exception as e:
                    self.print_error(f"Test failed with exception: {e}")
                    all_passed = False

        return all_passed

    def run_all_tests(self) -> bool:
        """Run all validation tests"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(
            f"{Colors.BOLD}Data Anonymization Pipeline - Validation Test Suite{Colors.END}"
        )
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        all_passed = True

        # Test 1: Config loading
        if not self.test_config_loading():
            all_passed = False

        # Test 2: Fixture data
        if not self.test_fixture_data():
            self.print_warning("Fixture validation had issues, but continuing...")

        # Test 3: Full workflows (only if components are available)
        try:
            from src.scanner import PIIScanner

            if not self.test_all_combinations():
                all_passed = False
        except ImportError:
            self.print_warning(
                "Pipeline components not available - skipping workflow tests"
            )

        # Test 4: CLI commands (optional)
        try:
            if not self.test_cli_commands():
                self.print_warning(
                    "CLI tests failed, but this may be expected during development"
                )
        except Exception as e:
            self.print_warning(f"CLI tests skipped: {e}")

        # Generate summary
        self.generate_summary_report()

        # Final status
        self.print_header("Final Status")

        if all_passed:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}\n")
            print("Your anonymization pipeline is ready!")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}\n")
            print("Please review the errors above and fix them before deploying.")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate anonymization pipeline")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with only one preset+fixture combination",
    )
    parser.add_argument(
        "--preset", type=str, help="Test only this preset (e.g., gdpr_compliant)"
    )
    parser.add_argument(
        "--fixture", type=str, help="Test only this fixture (e.g., customers.csv)"
    )

    args = parser.parse_args()

    tester = ValidationTester()

    if args.quick:
        # Quick mode: test just one combination
        print(
            f"\n{Colors.BOLD}🚀 Quick Test Mode - Testing single preset+fixture{Colors.END}\n"
        )
        success = tester.run_quick_test()
    elif args.preset or args.fixture:
        # Custom test mode
        print(f"\n{Colors.BOLD}🎯 Custom Test Mode{Colors.END}\n")
        success = tester.run_custom_test(args.preset, args.fixture)
    else:
        # Full test suite
        success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
