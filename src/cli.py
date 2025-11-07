"""
Command-line interface for PII Scanner and Risk Assessment.

Provides easy-to-use commands for scanning datasets and assessing risk.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path if running as script
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback to empty strings if colorama not available
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''
    class Back:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = BLACK = RESET = ''

from src.scanner import PIIScanner
from src.risk_assessment import RiskAssessmentEngine, infer_quasi_identifiers


class ColorPrinter:
    """Helper class for colored console output."""
    
    @staticmethod
    def success(message: str):
        """Print success message in green."""
        print(f"{Fore.GREEN}{Style.BRIGHT}SUCCESS:{Style.RESET_ALL} {message}")
    
    @staticmethod
    def error(message: str):
        """Print error message in red."""
        print(f"{Fore.RED}{Style.BRIGHT}ERROR:{Style.RESET_ALL} {message}")
    
    @staticmethod
    def warning(message: str):
        """Print warning message in yellow."""
        print(f"{Fore.YELLOW}{Style.BRIGHT}WARNING:{Style.RESET_ALL} {message}")
    
    @staticmethod
    def info(message: str):
        """Print info message in blue."""
        print(f"{Fore.BLUE}{Style.BRIGHT}INFO:{Style.RESET_ALL} {message}")
    
    @staticmethod
    def header(message: str):
        """Print header in cyan."""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 70}{Style.RESET_ALL}\n")
    
    @staticmethod
    def subheader(message: str):
        """Print subheader in magenta."""
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{message}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'-' * 70}{Style.RESET_ALL}")
    
    @staticmethod
    def risk_level(level: str) -> str:
        """Get colored risk level string."""
        if level == 'high':
            return f"{Fore.RED}{Style.BRIGHT}HIGH{Style.RESET_ALL}"
        elif level == 'medium':
            return f"{Fore.YELLOW}{Style.BRIGHT}MEDIUM{Style.RESET_ALL}"
        else:
            return f"{Fore.GREEN}{Style.BRIGHT}LOW{Style.RESET_ALL}"


def scan_command(args):
    """
    Execute the scan command.
    
    Scans a file for PII and assesses re-identification risk.
    """
    printer = ColorPrinter()
    
    # Validate file exists
    filepath = Path(args.file)
    if not filepath.exists():
        printer.error(f"File not found: {args.file}")
        sys.exit(1)
    
    printer.header("PII SCANNER & RISK ASSESSMENT")
    printer.info(f"Scanning file: {filepath.name}")
    
    # Initialize scanner
    scanner = PIIScanner(use_ner=not args.no_ner)
    
    try:
        # Scan for PII
        printer.info("Detecting PII types...")
        pii_results = scanner.scan_file(str(filepath), sample_size=args.sample_size)
        
        if not pii_results:
            printer.warning("No PII detected in the file")
            return
        
        printer.success(f"Found PII in {len(pii_results)} fields")
        
        # Display PII results
        if not args.quiet:
            printer.subheader("PII DETECTION RESULTS")
            for field_name, result in pii_results.items():
                confidence_color = Fore.GREEN if result.confidence >= 0.8 else Fore.YELLOW
                print(f"  {Fore.CYAN}{field_name}{Style.RESET_ALL}")
                print(f"    PII Types: {', '.join(result.pii_types)}")
                print(f"    Confidence: {confidence_color}{result.confidence:.2f}{Style.RESET_ALL}")
                print(f"    Detections: {result.detection_count}")
                print()
        
        # Risk assessment
        if args.assess_risk:
            printer.info("Assessing re-identification risk...")
            
            # Load full dataset for risk assessment
            import pandas as pd
            if filepath.suffix.lower() == '.csv':
                df = pd.read_csv(filepath)
            elif filepath.suffix.lower() == '.json':
                df = pd.DataFrame(json.load(open(filepath)))
            else:
                printer.error("Unsupported file format for risk assessment")
                return
            
            # Infer quasi-identifiers
            quasi_identifiers = infer_quasi_identifiers(df, pii_results)
            
            if not quasi_identifiers:
                printer.warning("No quasi-identifiers found for risk assessment")
                return
            
            printer.info(f"Using quasi-identifiers: {', '.join(quasi_identifiers)}")
            
            # Perform risk assessment
            risk_engine = RiskAssessmentEngine()
            
            # Use ONLY pairs of QIs (most realistic)
            # This prevents over-identification
            qi_sets = []
            
            if len(quasi_identifiers) >= 2:
                # Test 2-3 different pairs instead of cumulative sets
                qi_sets.append(quasi_identifiers[:2])  # e.g., [age, zip]
                
                if len(quasi_identifiers) >= 4:
                    qi_sets.append([quasi_identifiers[0], quasi_identifiers[3]])  # e.g., [age, income]
                
                if len(quasi_identifiers) >= 3:
                    qi_sets.append([quasi_identifiers[1], quasi_identifiers[2]])  # e.g., [zip, dob]
            
            # Never use 3-4 QIs together - creates too much uniqueness
            
            printer.info(f"Testing {len(qi_sets)} QI combinations: {qi_sets}")
            
            risk_scores, risk_report = risk_engine.assess_dataset(df, qi_sets)
            
            printer.success("Risk assessment complete")
            
            # Warn if all records are high risk (may indicate over-identification)
            if risk_report.high_risk_count == risk_report.total_records:
                printer.warning(
                    f"All {risk_report.total_records} records are high risk. "
                    f"This may indicate the dataset has very unique combinations even with "
                    f"fewer quasi-identifiers, or too many QIs are being used together."
                )
            
            # Display risk report
            if not args.quiet:
                _display_risk_report(risk_report, printer)
            
            # Get high-risk records
            high_risk_df = risk_engine.get_high_risk_records(df, risk_scores, limit=args.limit)
            
            if len(high_risk_df) > 0:
                printer.subheader(f"HIGH-RISK RECORDS (Top {len(high_risk_df)})")
                for idx, row in high_risk_df.iterrows():
                    print(f"  Record {idx}:")
                    print(f"    Risk Score: {Fore.RED}{row['risk_score']:.2f}{Style.RESET_ALL}")
                    print(f"    Reasoning: {row['risk_reasoning']}")
                    # Show quasi-identifier values
                    for qi in quasi_identifiers:
                        if qi in row:
                            print(f"    {qi}: {row[qi]}")
                    print()
        
        # Generate JSON output
        if args.output:
            output_data = _generate_json_output(pii_results, risk_scores if args.assess_risk else None, 
                                                risk_report if args.assess_risk else None)
            
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            printer.success(f"JSON report saved to: {output_path}")
        
    except Exception as e:
        printer.error(f"Error during scan: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_risk_report(report, printer):
    """Display risk report with colors."""
    printer.subheader("RISK ASSESSMENT SUMMARY")
    
    print(f"  Total Records: {report.total_records}")
    print()
    
    print(f"  {Fore.RED}High Risk:{Style.RESET_ALL}   {report.high_risk_count:4d} ({report.high_risk_percentage:5.1f}%)")
    print(f"  {Fore.YELLOW}Medium Risk:{Style.RESET_ALL} {report.medium_risk_count:4d} ({report.medium_risk_percentage:5.1f}%)")
    print(f"  {Fore.GREEN}Low Risk:{Style.RESET_ALL}    {report.low_risk_count:4d} ({report.low_risk_percentage:5.1f}%)")
    print()
    
    print(f"  K-Anonymity Statistics:")
    print(f"    Average k: {report.average_k_anonymity:.2f}")
    print(f"    Minimum k: {report.min_k_anonymity}")
    print()
    
    print(f"  Record Classification:")
    print(f"    Unique records (k=1):    {len(report.unique_records)}")
    print(f"    Rare records (k=2-5):    {len(report.rare_records)}")
    print(f"    Safe records (k>10):     {len(report.safe_records)}")
    print()


def _generate_json_output(pii_results, risk_scores, risk_report) -> Dict[str, Any]:
    """Generate JSON output structure."""
    output = {
        "pii_detection": {
            "fields": {}
        }
    }
    
    # Add PII results
    for field_name, result in pii_results.items():
        output["pii_detection"]["fields"][field_name] = {
            "pii_types": result.pii_types,
            "confidence": result.confidence,
            "detection_count": result.detection_count
        }
    
    # Add risk assessment if available
    if risk_scores and risk_report:
        output["risk_assessment"] = {
            "summary": {
                "total_records": risk_report.total_records,
                "high_risk_count": risk_report.high_risk_count,
                "medium_risk_count": risk_report.medium_risk_count,
                "low_risk_count": risk_report.low_risk_count,
                "high_risk_percentage": risk_report.high_risk_percentage,
                "medium_risk_percentage": risk_report.medium_risk_percentage,
                "low_risk_percentage": risk_report.low_risk_percentage,
                "average_k_anonymity": risk_report.average_k_anonymity,
                "min_k_anonymity": risk_report.min_k_anonymity
            },
            "high_risk_records": risk_report.unique_records[:10],  # Top 10
            "risk_distribution": {
                "high": risk_report.high_risk_count,
                "medium": risk_report.medium_risk_count,
                "low": risk_report.low_risk_count
            }
        }
    
    return output


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PII Scanner & Risk Assessment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a CSV file for PII
  python cli.py scan --file=fixtures/customers.csv
  
  # Scan with risk assessment
  python cli.py scan --file=fixtures/customers.csv --assess-risk
  
  # Save results to JSON
  python cli.py scan --file=data.csv --output=report.json
  
  # Quiet mode (minimal output)
  python cli.py scan --file=data.csv --quiet
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a file for PII and assess risk')
    scan_parser.add_argument('--file', '-f', required=True, help='File to scan (CSV or JSON)')
    scan_parser.add_argument('--output', '-o', help='Output file for JSON report')
    scan_parser.add_argument('--sample-size', type=int, default=100, 
                           help='Number of rows to sample (default: 100)')
    scan_parser.add_argument('--assess-risk', action='store_true', 
                           help='Perform risk assessment')
    scan_parser.add_argument('--limit', type=int, default=10,
                           help='Number of high-risk records to show (default: 10)')
    scan_parser.add_argument('--no-ner', action='store_true',
                           help='Disable NER detection (faster)')
    scan_parser.add_argument('--quiet', '-q', action='store_true',
                           help='Minimal output (only summary)')
    scan_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output (show errors)')
    
    args = parser.parse_args()
    
    # Check for command
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check for colorama
    if not COLORAMA_AVAILABLE and not args.quiet:
        print("Note: Install 'colorama' for colored output: pip install colorama\n")
    
    # Execute command
    if args.command == 'scan':
        scan_command(args)


if __name__ == '__main__':
    main()