#!/usr/bin/env python3
"""
Demo Script: Data Anonymization Pipeline Showcase

This script demonstrates the complete workflow in under 60 seconds:
1. Load Realistic customer data
2. Setect PII and assess risj
3. Apply GDPR-compliant anonymization
4. Validate ML utility retention
5. Generate compliance report

Usage:
    python examples/demo.py
    python examples/demo.py --dataset fixtures/transactions.csv
    python examples/demo.py --preset ml_training --output demo_output.csv
"""

import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.scanner import PIIScanner
from src.anonymizer import Anonymizer
from src.risk_assessment import RiskAssessmentEngine
from src.config_loader import ConfigLoader, load_config
from src.utility_metrics import UtilityMetrics
from src.report.compliance_report import ComplianceReportGenerator

console = Console()


class DemoRunner:
    """Orchestrates the demo workflow with visual feedback"""

    def __init__(self, dataset_path: str, preset: str = "gdpr_compliant"):
        self.dataset_path = Path(dataset_path)
        self.preset = preset
        self.start_time = time.time()
        self.pii_results = {}  # Store PII detection results

    def print_header(self):
        """Display demo header"""
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]Data Anonymization Pipeline Demo[/bold cyan]\n"
                "[dim]Built for Privacy Engineering for ML Teams[/dim]",
                border_style="cyan",
            )
        )
        console.print()

    def load_data(self) -> pd.DataFrame:
        """Load and display dataset info"""
        console.print("[bold]Step 1: Loading Data[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Reading data...", total=None)
            df = pd.read_csv(self.dataset_path)
            progress.update(task, completed=True)

        console.print(f"   ✓ Loaded {len(df):,} rows × {len(df.columns)} columns")
        console.print(
            f"   ✓ Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}"
        )
        console.print()

        return df

    def detect_pii(self, df: pd.DataFrame) -> dict:
        """Scan for PII and display results"""
        console.print("[bold]Step 2: Detecting PII[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Scanning with NER and regex patterns...", total=None
            )
            scanner = PIIScanner()
            results = scanner.scan_dataframe(df)
            progress.update(task, completed=True)

        # Display PII findings in a table
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Column", style="cyan")
        table.add_column("PII Types", style="yellow")
        table.add_column("Detections", justify="right", style="red")
        table.add_column("Confidence", justify="right")

        for column, info in results.items():
            # info is a PIIDetectionResult object, not a dict
            confidence_indicator = (
                "●●●"
                if info.confidence > 0.9
                else "●●○" if info.confidence > 0.7 else "●○○"
            )
            pii_types_str = ", ".join(info.pii_types) if info.pii_types else "None"
            table.add_row(
                column, pii_types_str, str(info.detection_count), confidence_indicator
            )

        console.print(table)
        console.print()

        # Store results for later use
        self.pii_results = results
        return results

    def assess_risk(self, df: pd.DataFrame) -> dict:
        """Calculate risk metrics"""
        console.print("[bold]Step 3: Assessing Re-identification Risk[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Calculating k-anonymity and l-diversity...", total=None
            )

            # Identify quasi-identifiers (columns that could be used for re-identification)
            quasi_identifiers = ["age", "zip_code", "gender", "city", "state"]
            quasi_identifiers = [col for col in quasi_identifiers if col in df.columns]

            if not quasi_identifiers:
                # Fallback to common columns if none found
                quasi_identifiers = [
                    col for col in df.columns if col in ["age", "zipcode", "zip_code"]
                ]
                if not quasi_identifiers and len(df.columns) > 0:
                    # Use first numeric or string column as fallback
                    quasi_identifiers = [df.columns[0]]

            # Use RiskAssessmentEngine
            assessor = RiskAssessmentEngine()
            uniqueness_results = assessor.calculate_uniqueness(df, quasi_identifiers)

            # Calculate metrics from uniqueness results
            k_values = [r.k_anonymity for r in uniqueness_results]
            min_k = min(k_values) if k_values else 0
            unique_count = sum(1 for r in uniqueness_results if r.is_unique)

            # Calculate re-identification risk (percentage of unique records)
            reidentification_risk = unique_count / len(df) if len(df) > 0 else 0.0

            risk_metrics = {
                "k_anonymity": min_k,
                "reidentification_risk": reidentification_risk,
                "unique_records": unique_count,
            }
            progress.update(task, completed=True)

        # Display risk metrics
        risk_table = Table(
            show_header=True, header_style="bold yellow", box=box.ROUNDED
        )
        risk_table.add_column("Metric", style="cyan", width=30)
        risk_table.add_column("Value", justify="right")
        risk_table.add_column("Status")

        k_anon = risk_metrics.get("k_anonymity", 0)
        k_status = "✓ Good" if k_anon >= 10 else "✗ Needs work"
        k_color = "green" if k_anon >= 10 else "red"

        re_id = risk_metrics.get("reidentification_risk", 0) * 100
        re_id_status = "✓ Good" if re_id < 5 else "✗ High"
        re_id_color = "green" if re_id < 5 else "red"

        risk_table.add_row(
            "k-anonymity (min)", f"{k_anon}", f"[{k_color}]{k_status}[/{k_color}]"
        )
        risk_table.add_row(
            "Re-identification Risk",
            f"{re_id:.1f}%",
            f"[{re_id_color}]{re_id_status}[/{re_id_color}]",
        )
        risk_table.add_row(
            "Unique Records", f"{risk_metrics.get('unique_records', 0):,}", ""
        )

        console.print(risk_table)
        console.print()

        return risk_metrics

    def anonymize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply anonymization with the selected preset."""
        console.print(f"[bold]Step 4: Applying Anonymization ({self.preset})[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Loading configuration and applying rules...", total=None
            )

            # Load preset configuration (presets need transformation)
            from src.cli import AnonymizationCLI

            cli = AnonymizationCLI()
            config, _ = cli.load_config(preset=self.preset)

            # Apply anonymization
            anonymizer = Anonymizer(config)
            df_anon = anonymizer.anonymize(df)

            progress.update(task, completed=True)

        # Show before/after sample
        console.print("   [bold]Before/After Sample:[/bold]")

        # Select a few interesting columns
        sample_cols = []
        for col in ["name", "email", "phone", "address", "age"]:
            if col in df.columns:
                sample_cols.append(col)
                if len(sample_cols) == 3:
                    break

        if sample_cols:
            sample_table = Table(
                show_header=True, header_style="bold", box=box.SIMPLE_HEAVY
            )
            sample_table.add_column("Column", style="cyan")
            sample_table.add_column("Original", style="red", overflow="fold")
            sample_table.add_column("Anonymized", style="green", overflow="fold")

            for col in sample_cols:
                orig_val = str(df[col].iloc[0])
                anon_val = str(df_anon[col].iloc[0])
                sample_table.add_row(col, orig_val[:40], anon_val[:40])

            console.print(sample_table)

            # Add note about pseudonymization for names
            if "name" in sample_cols:
                console.print(
                    "   [dim]Note: Names are pseudonymized (replaced with consistent fake names)[/dim]"
                )

        console.print()
        return df_anon

    def validate_utility(self, df_original: pd.DataFrame, df_anonymized: pd.DataFrame):
        """Compare ML utility between original and anonymized data."""
        console.print("[bold]Step 5: Validating ML Utility[/bold]")

        # Check if we have a suitable target column for ML
        # First try common ML target column names
        target_candidates = [
            "purchase_amount",
            "total",
            "churn",
            "fraud",
            "outcome",
            "income",
            "salary",
            "price",
            "amount",
        ]
        target_col = None
        for candidate in target_candidates:
            if candidate in df_original.columns:
                # Verify it's numeric and has reasonable variance
                if pd.api.types.is_numeric_dtype(df_original[candidate]):
                    target_col = candidate
                    break

        # If no exact match, look for any numeric column that could be a target
        if not target_col:
            numeric_cols = [
                col
                for col in df_original.columns
                if pd.api.types.is_numeric_dtype(df_original[col])
                and col not in ["age", "zip", "zipcode"]  # Exclude common QIs
            ]
            if numeric_cols:
                # Prefer columns that aren't likely to be anonymized (like income)
                for col in numeric_cols:
                    if col in [
                        "income",
                        "salary",
                        "price",
                        "amount",
                        "value",
                        "score",
                        "rating",
                    ]:
                        target_col = col
                        break
                # If still no match, use first numeric column
                if not target_col and numeric_cols:
                    target_col = numeric_cols[0]

        if not target_col:
            console.print(
                "   [dim]⊘ No suitable target column found for ML validation[/dim]"
            )
            console.print(
                "   [dim]  (Need a numeric column like: income, purchase_amount, total, etc.)[/dim]"
            )
            available_numeric = [
                col
                for col in df_original.columns
                if pd.api.types.is_numeric_dtype(df_original[col])
            ]
            if available_numeric:
                console.print(
                    f"   [dim]  Available numeric columns: {', '.join(available_numeric)}[/dim]"
                )
            console.print()
            return

        # Generate utility report instead of ML performance (since compare_ml_performance doesn't exist)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Calculating utility metrics...", total=None)

            utility = UtilityMetrics(df_original, df_anonymized)
            report = utility.generate_report()

            progress.update(task, completed=True)

        # Display utility metrics summary
        utility_table = Table(
            show_header=True, header_style="bold green", box=box.ROUNDED
        )
        utility_table.add_column("Metric", style="cyan")
        utility_table.add_column("Value", justify="right")
        utility_table.add_column("Status")

        overall_score = report.overall_utility_score
        score_color = (
            "green"
            if overall_score >= 80
            else "yellow" if overall_score >= 70 else "red"
        )
        score_status = (
            "✓ Good"
            if overall_score >= 80
            else "⚠ Fair" if overall_score >= 70 else "✗ Poor"
        )

        utility_table.add_row(
            "Overall Utility Score",
            f"{overall_score:.1f}%",
            f"[{score_color}]{score_status}[/{score_color}]",
        )

        # Add correlation preservation if available
        if report.correlation_metrics:
            corr_preservation = report.correlation_metrics.correlation_similarity * 100
            corr_color = (
                "green"
                if corr_preservation >= 80
                else "yellow" if corr_preservation >= 70 else "red"
            )
            utility_table.add_row(
                "Correlation Preservation",
                f"{corr_preservation:.1f}%",
                f"[{corr_color}]{'✓' if corr_preservation >= 80 else '⚠'}[/{corr_color}]",
            )

        console.print(utility_table)
        console.print()

    def generate_report(
        self, df_original: pd.DataFrame, df_anonymized: pd.DataFrame
    ) -> str:
        """Generate compliance report."""
        console.print("[bold]Step 6: Generating Compliance Report[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating HTML report...", total=None)

            # Load preset configuration for report metadata
            preset_path = Path(f"config/presets/{self.preset}.yaml")
            raw_config = None
            if preset_path.exists():
                with open(preset_path, "r", encoding="utf-8") as f:
                    raw_config = yaml.safe_load(f)

            # Generate report using ComplianceReportGenerator
            generator = ComplianceReportGenerator()
            report_content = generator.generate(
                original_data=df_original,
                anonymized_data=df_anonymized,
                config=raw_config,
                output_format="html",
            )

            # Save report
            report_path = Path("output/demos/compliance_report.html")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            progress.update(task, completed=True)

        console.print(f"   ✓ Report saved to: [cyan]{report_path}[/cyan]")
        console.print()

        return str(report_path)

    def print_summary(self, df_original: pd.DataFrame, df_anonymized: pd.DataFrame):
        """Display final summary."""
        elapsed = time.time() - self.start_time

        # Count actual PII fields detected
        pii_fields_count = len(self.pii_results) if self.pii_results else 0

        summary_panel = Panel.fit(
            f"[bold green]✓ Demo Complete[/bold green]\n\n"
            f"[cyan]Processing Time:[/cyan] {elapsed:.2f}s\n"
            f"[cyan]Records Processed:[/cyan] {len(df_original):,}\n"
            f"[cyan]PII Fields Protected:[/cyan] {pii_fields_count}\n"
            f"[cyan]Anonymization Preset:[/cyan] {self.preset}\n\n"
            f"[dim]Next Steps:[/dim]\n"
            f"  • Review compliance report in output/demos/\n"
            f"  • Try different presets: --preset ml_training\n"
            f"  • Use your own data: --dataset your_file.csv",
            title="[bold]Summary[/bold]",
            border_style="green",
        )

        console.print(summary_panel)
        console.print()


def main():
    """Run the demo."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Data Anonymization Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        default="fixtures/customers.csv",
        help="Path to dataset (default: fixtures/customers.csv)",
    )
    parser.add_argument(
        "--preset",
        default="gdpr_compliant",
        choices=["gdpr_compliant", "ml_training", "vendor_sharing"],
        help="Anonymization preset to use (default: gdpr_compliant)",
    )
    parser.add_argument("--output", help="Path to save anonymized data (optional)")

    args = parser.parse_args()

    # Validate dataset exists
    if not Path(args.dataset).exists():
        console.print(
            f"[red]Error:[/red] Dataset not found: {args.dataset}", style="bold"
        )
        console.print(f"\nAvailable datasets:")
        fixtures_dir = Path("fixtures")
        if fixtures_dir.exists():
            for fixture in fixtures_dir.glob("*.csv"):
                console.print(f"  • {fixture}")
        sys.exit(1)

    try:
        # Run the demo
        demo = DemoRunner(args.dataset, args.preset)
        demo.print_header()

        # Execute workflow
        df_original = demo.load_data()
        pii_results = demo.detect_pii(df_original)
        risk_metrics = demo.assess_risk(df_original)
        df_anonymized = demo.anonymize_data(df_original)
        demo.validate_utility(df_original, df_anonymized)
        report_path = demo.generate_report(df_original, df_anonymized)

        # Save output if requested
        if args.output:
            df_anonymized.to_csv(args.output, index=False)
            console.print(f"Anonymized data saved to: [cyan]{args.output}[/cyan]\n")

        # Show summary
        demo.print_summary(df_original, df_anonymized)

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}", style="bold")
        console.print(f"\n[dim]Stack trace:[/dim]")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
