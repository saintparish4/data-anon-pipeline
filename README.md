# Data Anonymization Pipeline

## The Real Problem

"We need to share customer data with [vendor/partner/researcher] but our lawyer says we can't share PII."

**Who has this problem:**

- ML teams needing realistic test data (can't use production)
- Companies sharing data with vendors (analytics, ML training)
- Researchers needing datasets for studies
- Compliance teams proving GDPR Article 25 (data minimization)

**Current solutions are bad:**

- Manual redaction (slow, error-prone, doesn't scale)
- "Just delete names/emails" (insufficient - still re-identifiable)
- Vendor tools ($$$, black box, still leaks data)
- Legal says "no" → innovation stops

## Core Purpose

"Transform production data into shareable data that's legally safe and actually useful."

**Success criteria:** Data scientist can still train accurate models, but can't identify individuals.

## Demos

**Main pipeline (default):**

![Main pipeline demo](output/demos/demo_full_20260201_194419.gif)

**Business scenario (Rendr vs PrivaShield):**

![Scenario demo](output/demos/demo_scenario_20260201_154337.gif)

## Quick start

```bash
# Main pipeline demo (default)
./scripts/demo/record_automated.sh

# Business scenario demo - Rendr vs PrivaShield
./scripts/demo/record_automated.sh --scenario

# Fast versions
./scripts/demo/record_automated.sh --fast
./scripts/demo/record_automated.sh --scenario-fast

# Record all demos
./scripts/demo/record_automated.sh --all
```

```bash
# Convert a .cast to GIF (optional; requires agg)
#   Install agg: cargo install --git https://github.com/asciinema/agg
#   Or download from https://github.com/asciinema/agg/releases
#   agg --font-size 14 --theme monokai output/demos/demo_*.cast output/demos/demo.gif

    Install as prerequiste 
   cargo install --git https://github.com/asciinema/agg
```