#!/usr/bin/env python3
"""
Demo Data Setup Script

Ensures sample data files exist for running demos.
Uses generate_customers.py for realistic, correlated customer data.

Usage:
    python scripts/demo/setup_demo_data.py
    python scripts/demo/setup_demo_data.py --records 500
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Set up demo data if needed."""
    import argparse

    parser = argparse.ArgumentParser(description="Set up demo data")
    parser.add_argument(
        "--records",
        type=int,
        default=100,
        help="Number of records to generate (default: 100)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Regenerate even if data exists"
    )
    args = parser.parse_args()

    fixtures_dir = PROJECT_ROOT / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    customers_file = fixtures_dir / "customers.csv"

    # Check if file already exists
    if customers_file.exists() and customers_file.stat().st_size > 0 and not args.force:
        print("Demo data already exists:")
        print(f"  - {customers_file}")

        # Show record count
        with open(customers_file, "r") as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header
        print(f"  - {line_count:,} records")
        print()
        print("Use --force to regenerate.")
        return

    print(f"Generating {args.records} customer records...")
    print()

    # Use the generate_customers.py script
    generate_script = PROJECT_ROOT / "scripts" / "generate_customers.py"

    if generate_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(generate_script), str(args.records)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(result.stdout)
                print()
                print(f"Demo data saved to: {customers_file}")
            else:
                print(f"Error running generate_customers.py:")
                print(result.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print(f"Error: generate_customers.py not found at {generate_script}")
        sys.exit(1)


if __name__ == "__main__":
    main()
