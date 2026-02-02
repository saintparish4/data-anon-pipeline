#!/bin/bash
# =============================================================================
# Automated Asciinema Demo Recording
# Records scripted demos with live progress feedback
# =============================================================================
#
# This creates polished, reproducible demo recordings without manual input.
#
# Available Demos:
#   --main       Main pipeline demo (PII detection → anonymization → validation)
#   --scenario   Business scenario demo (Rendr vs Priva comparison)
#   --fast       Fast mode of main demo (shorter pauses)
#   --quick      Quick demo (just runs demo.py)
#   --all        Record all demos
#
# Usage:
#   ./scripts/demo/record_automated.sh              # Main demo (default)
#   ./scripts/demo/record_automated.sh --scenario   # Business scenarios
#   ./scripts/demo/record_automated.sh --all        # All demos
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/output/demos"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check for asciinema
if ! command -v asciinema &> /dev/null; then
    echo "Error: asciinema is not installed"
    echo ""
    echo "In WSL, install with:"
    echo "  sudo apt install asciinema"
    echo "  # or"
    echo "  pip3 install asciinema  # Use Linux pip, not Windows venv!"
    exit 1
fi

cd "$PROJECT_ROOT"

show_next_steps() {
    echo ""
    echo "Recording saved!"
    echo ""
    echo "Next steps:"
    echo "  # Play locally"
    echo "  asciinema play $1"
    echo ""
    echo "  # Upload to asciinema.org (get shareable link)"
    echo "  asciinema upload $1"
    echo ""
    echo "  # Convert to GIF (requires agg: https://github.com/asciinema/agg)"
    echo "  #   Install: cargo install --git https://github.com/asciinema/agg"
    echo "  #   Or: download binary from https://github.com/asciinema/agg/releases"
    echo "  agg --font-size 14 --theme monokai $1 ${1%.cast}.gif"
}

# Parse arguments
case "$1" in
    --quick)
        CAST_FILE="$OUTPUT_DIR/demo_quick_${TIMESTAMP}.cast"
        echo "Recording quick demo to: $CAST_FILE"
        echo ""
        asciinema rec \
            --title "Data Anonymization Pipeline - Quick Demo" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 35 \
            --command "python3 examples/demo.py" \
            "$CAST_FILE"
        show_next_steps "$CAST_FILE"
        ;;
        
    --fast)
        CAST_FILE="$OUTPUT_DIR/demo_fast_${TIMESTAMP}.cast"
        echo "Recording fast demo to: $CAST_FILE"
        echo ""
        asciinema rec \
            --title "Data Anonymization Pipeline - Demo" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 40 \
            --command "python3 scripts/demo/run_demo_sequence.py --fast" \
            "$CAST_FILE"
        show_next_steps "$CAST_FILE"
        ;;
        
    --scenario)
        CAST_FILE="$OUTPUT_DIR/demo_scenario_${TIMESTAMP}.cast"
        echo "=========================================="
        echo "  SCENARIO DEMO: Rendr vs Priva"
        echo "=========================================="
        echo ""
        echo "This demo shows how two companies with different needs"
        echo "use different anonymization strategies:"
        echo ""
        echo "  RENDR       - ML platform, needs max data utility"
        echo "  PRIVASHIELD - Privacy-first, needs GDPR compliance"
        echo ""
        echo "Recording to: $CAST_FILE"
        echo ""
        asciinema rec \
            --title "Data Anonymization - Business Scenarios (Rendr vs Priva)" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 50 \
            --command "python3 scripts/demo/run_scenario_demo.py" \
            "$CAST_FILE"
        show_next_steps "$CAST_FILE"
        ;;
        
    --scenario-fast)
        CAST_FILE="$OUTPUT_DIR/demo_scenario_fast_${TIMESTAMP}.cast"
        echo "Recording fast scenario demo to: $CAST_FILE"
        echo ""
        asciinema rec \
            --title "Data Anonymization - Business Scenarios" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 50 \
            --command "python3 scripts/demo/run_scenario_demo.py --fast" \
            "$CAST_FILE"
        show_next_steps "$CAST_FILE"
        ;;
        
    --all)
        echo "=========================================="
        echo "  RECORDING ALL DEMOS"
        echo "=========================================="
        echo ""
        
        # Main demo
        CAST_FILE="$OUTPUT_DIR/demo_main_${TIMESTAMP}.cast"
        echo "[1/3] Recording main pipeline demo..."
        asciinema rec \
            --title "Data Anonymization Pipeline - Main Demo" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 40 \
            --command "python3 scripts/demo/run_demo_sequence.py --fast" \
            "$CAST_FILE"
        echo "  ✓ Saved: $CAST_FILE"
        echo ""
        
        # Scenario demo
        CAST_FILE="$OUTPUT_DIR/demo_scenario_${TIMESTAMP}.cast"
        echo "[2/3] Recording scenario demo (Rendr vs Priva)..."
        asciinema rec \
            --title "Data Anonymization - Business Scenarios" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 50 \
            --command "python3 scripts/demo/run_scenario_demo.py --fast" \
            "$CAST_FILE"
        echo "  ✓ Saved: $CAST_FILE"
        echo ""
        
        # Quick demo
        CAST_FILE="$OUTPUT_DIR/demo_quick_${TIMESTAMP}.cast"
        echo "[3/3] Recording quick demo..."
        asciinema rec \
            --title "Data Anonymization Pipeline - Quick Demo" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 35 \
            --command "python3 examples/demo.py" \
            "$CAST_FILE"
        echo "  ✓ Saved: $CAST_FILE"
        echo ""
        
        echo "=========================================="
        echo "  ALL DEMOS RECORDED"
        echo "=========================================="
        echo ""
        echo "Output directory: $OUTPUT_DIR"
        echo ""
        find "$OUTPUT_DIR" -maxdepth 1 -name "*.cast" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -5 | cut -d' ' -f2-
        ;;
        
    --help|-h)
        echo "Asciinema Demo Recording Script"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  (none)          Record main pipeline demo (default)"
        echo "  --scenario      Record business scenario demo (Rendr vs Priva)"
        echo "  --fast          Record main demo in fast mode"
        echo "  --scenario-fast Record scenario demo in fast mode"
        echo "  --quick         Record quick demo (just demo.py)"
        echo "  --all           Record all demos"
        echo "  --help, -h      Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                    # Main demo"
        echo "  $0 --scenario         # Show different company use cases"
        echo "  $0 --all              # Record everything"
        ;;
        
    --main|*)
        # Default: Full main demo
        CAST_FILE="$OUTPUT_DIR/demo_full_${TIMESTAMP}.cast"
        echo "=========================================="
        echo "  MAIN PIPELINE DEMO"
        echo "=========================================="
        echo ""
        echo "This demo shows the complete pipeline:"
        echo "  1. Load customer data (21 columns)"
        echo "  2. Detect PII fields"
        echo "  3. Assess re-identification risk"
        echo "  4. Apply anonymization"
        echo "  5. Validate utility"
        echo ""
        echo "Recording to: $CAST_FILE"
        echo ""
        asciinema rec \
            --title "Data Anonymization Pipeline - Full Demo" \
            --idle-time-limit 1 \
            --cols 100 \
            --rows 45 \
            --command "python3 scripts/demo/run_demo_sequence.py" \
            "$CAST_FILE"
        show_next_steps "$CAST_FILE"
        ;;
esac
