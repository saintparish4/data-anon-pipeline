#!/usr/bin/env python3
"""
Automated Demo Script for Asciinema Recording

This script simulates typing commands in the terminal with realistic delays,
creating a polished demo recording. It can be piped into a shell for recording.

Usage:
    # Run directly with asciinema
    asciinema rec --command "python scripts/demo/demo_script.py | bash" demo.cast

    # Or use the automated recording script
    ./scripts/demo/record_automated.sh
"""

import sys
import time
import random


def type_text(text: str, min_delay: float = 0.03, max_delay: float = 0.08):
    """Simulate typing text character by character."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Vary typing speed for realism
        delay = random.uniform(min_delay, max_delay)
        # Slow down slightly for special characters
        if char in "|>&;":
            delay *= 1.5
        time.sleep(delay)


def type_command(cmd: str, execute: bool = True, pause_after: float = 0.5):
    """Type a command and optionally execute it."""
    type_text(cmd)
    time.sleep(0.1)
    print()  # Press enter
    if execute:
        time.sleep(pause_after)


def pause(seconds: float = 1.0):
    """Pause for dramatic effect."""
    time.sleep(seconds)


def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")
    sys.stdout.flush()


def print_comment(text: str):
    """Print a comment (not executed)."""
    print(f"\033[90m# {text}\033[0m")
    time.sleep(0.5)


def run_demo():
    """Run the complete demo sequence."""

    # Introduction
    clear_screen()
    pause(0.5)

    print("\033[1;36m" + "=" * 60 + "\033[0m")
    print("\033[1;36m   Data Anonymization Pipeline - Terminal Demo\033[0m")
    print("\033[1;36m" + "=" * 60 + "\033[0m")
    print()
    pause(1.5)

    # Step 1: Show project structure
    print_comment("Let's explore the project structure")
    type_command("ls -la")
    pause(2)

    # Step 2: Show sample data
    print()
    print_comment("Check our sample customer data")
    type_command("head -5 fixtures/customers.csv")
    pause(3)

    # Step 3: Run PII scan
    print()
    print_comment("Scan the data for PII (Personally Identifiable Information)")
    type_command("python -m src scan --file fixtures/customers.csv")
    pause(4)

    # Step 4: Run the visual demo
    print()
    print_comment("Run the full anonymization demo with GDPR compliance")
    type_command("python examples/demo.py --preset gdpr_compliant")
    pause(5)

    # Step 5: Show anonymized output sample
    print()
    print_comment("Check the anonymized data")
    type_command(
        'head -5 output/demos/anonymized_customers.csv 2>/dev/null || echo "Output saved in demo"'
    )
    pause(2)

    # Step 6: Try ML training preset
    print()
    print_comment("Try a different preset optimized for ML training")
    type_command("python examples/demo.py --preset ml_training")
    pause(5)

    # Step 7: Show available presets
    print()
    print_comment("List all available anonymization presets")
    type_command("python -m src list-presets --verbose")
    pause(3)

    # Conclusion
    print()
    print("\033[1;32m" + "=" * 60 + "\033[0m")
    print("\033[1;32m   Demo Complete! \033[0m")
    print("\033[1;32m" + "=" * 60 + "\033[0m")
    print()
    print(
        "\033[90mLearn more: https://github.com/yourusername/data-anon-pipeline\033[0m"
    )
    print()
    pause(2)


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\033[90mDemo interrupted.\033[0m")
        sys.exit(0)
