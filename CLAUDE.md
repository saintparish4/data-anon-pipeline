# Data Anonymization Pipeline – Development Guide

## Project Structure

```
/src/                  - Python package (scanner, anonymizer, reporting)
  /detectors/          - PII detection (regex, NER)
  /anonymizers/        - Anonymization techniques
  /report/             - Compliance report generation
/tests/                - Pytest test suite
/scripts/              - Validation, demo recording, data generation
  /demo/               - Asciinema demo scripts (record_automated.sh, etc.)
/config/               - YAML configuration
  /presets/            - Preset configs (gdpr_compliant, ml_training, vendor_sharing)
/examples/             - Example pipelines and demo scripts
/fixtures/             - Test data (e.g. customers.csv)
/notebook/             - Jupyter notebooks (e.g. utility validation)
/docs/                 - Documentation and guides
output/demos/          - Demo recordings (GIF/cast); created by demo scripts
```

## Technology Stack

- **Python:** Core pipeline (3.8+); setuptools, `src` package
- **Data:** pandas, scipy; input/output CSV/JSON
- **PII detection:** Regex patterns, spaCy NER (e.g. `en_core_web_sm`)
- **Anonymization:** Configurable strategies (hash, generalize, substitute, etc.); Faker for synthetic data
- **Config:** YAML (PyYAML); presets and custom rule files
- **CLI:** Rich for output; entry point `data-anon-scan`
- **Testing:** pytest, pytest-xdist; optional markers: `slow`, `integration`
- **Code style:** Black (including Jupyter)
- **Demos:** asciinema (+ agg for GIF conversion)

## Local Development

**Quick start:**

```bash
# From repo root: install package and deps (incl. spaCy model)
pip install -e .
python -m spacy download en_core_web_sm

# Run CLI
data-anon-scan scan --file fixtures/customers.csv
data-anon-scan anonymize --file fixtures/customers.csv --preset gdpr_compliant --output out.csv
data-anon-scan list-presets
```

**Optional:** Use a virtual environment before `pip install -e .`.

## Testing

Run from repo root (pytest uses `pythonpath = .` and `testpaths = tests`):

```bash
# All tests
pytest

# Parallel (if pytest-xdist installed)
pytest -n auto

# Exclude slow / integration
pytest -m "not slow"
pytest -m "not integration"

# Specific module or test
pytest tests/test_anonymizer.py
pytest tests/test_anonymizer.py -k "test_hash"
```

**Full validation (presets + fixtures + reports):**

```bash
python scripts/validate_all.py
```

Run this before committing to ensure presets and pipeline work end-to-end.

## Code Quality

No Docker required. Run on host:

```bash
# Format
black src tests scripts examples

# Tests
pytest

# Full validation
python scripts/validate_all.py
```

## Build / Run Commands

| Action              | Command |
|---------------------|--------|
| Install (editable)  | `pip install -e .` |
| Scan file           | `data-anon-scan scan --file <path> [--output results.json]` |
| Anonymize (preset)  | `data-anon-scan anonymize --file <path> --preset <name> --output <path>` |
| Anonymize (custom)  | `data-anon-scan anonymize --file <path> --config <rules.yaml> --output <path>` |
| With report         | Add `--report` to anonymize |
| List presets        | `data-anon-scan list-presets` |
| Run demos           | `./scripts/demo/record_automated.sh` (see README for `--scenario`, `--fast`, `--all`) |
| Validate all        | `python scripts/validate_all.py` |

## Coding Standards

- **Python:** PEP 8; `snake_case` (functions, variables), `PascalCase` (classes). Format with Black. Document public APIs and non-obvious logic with docstrings.
- **Config:** YAML in `config/`; presets in `config/presets/`. Document new presets or rule schema in `docs/` (e.g. `docs/development/configuration_system.md`).
- **Line endings:** LF (Unix).
- **New detectors / anonymizers:** Add tests under `tests/`; use fixtures in `fixtures/` or inline data as appropriate. Document behavior and edge cases in code or `/docs`.

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

**Types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert  

**Scopes (examples):** detector, anonymizer, scanner, config, cli, report, docs, deps  

**Examples:**

- `feat(detector): add NER fallback for person names`
- `fix(anonymizer): handle nulls in generalize strategy`
- `docs(config): document preset k-anonymity defaults`
- `chore(deps): bump pandas to 3.x`

**Breaking changes:** Add `!` after type/scope or use `BREAKING CHANGE:` in footer.

## Detector / Anonymizer Guidelines

- **Detectors** live in `src/detectors/` (e.g. `regex_detector`, `ner_detector`). Add or extend tests in `tests/` (e.g. `test_regex_detector.py`, `test_ner_detector.py`).
- **Anonymization rules** are YAML-driven; add or adjust rules in `config/anonymization_rules.yaml` or preset files. Cover both vulnerable and safe patterns in tests; document confidence and edge cases where relevant.
- **Presets:** `gdpr_compliant`, `ml_training`, `vendor_sharing` in `config/presets/`. For new use cases, add a preset or document how to use a custom `--config` file (see `docs/CONFIGURATION.md`).

## Common Gotchas

- **spaCy model:** NER detector needs `en_core_web_sm` (or equivalent). Install with `python -m spacy download en_core_web_sm` after installing deps.
- **CLI entry point:** Installed as `data-anon-scan` via `setup.py`; ensure package is installed with `pip install -e .` when developing.
- **Paths:** Scripts under `scripts/demo/` assume run from repo root; `record_automated.sh` uses bash (WSL/Linux/macOS). On Windows, use WSL or run the underlying Python demo scripts as needed.
- **Demo GIFs:** Converting `.cast` to GIF requires `agg` (e.g. `cargo install --git https://github.com/asciinema/agg`); see README.

## Key Documentation

- `README.md` – Overview, problem statement, quick start, demo commands
- `docs/CONFIGURATION.md` – Presets and custom config usage
- `docs/development/configuration_system.md` – Config schema and strategies
- `docs/development/` – Additional dev notes (e.g. realistic data generation, test results)
- `docs/validation/` – Utility validation and related results
