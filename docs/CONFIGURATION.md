# Configuration

Rules are **configurable per business or use case** by choosing a preset or a custom YAML file. No code changes are required.

## How it works

- **Business A** (e.g. track certain metrics for ML): use the **ML training** preset → preserves utility for model training.
- **Business B** (e.g. maximum privacy / “track everything” in a compliant way): use the **GDPR compliant** preset or a custom config with stricter rules.

| Choice | CLI | Use case |
|--------|-----|----------|
| ML training | `--preset ml_training` | Maximize utility for ML; preserve correlations and metrics |
| GDPR compliant | `--preset gdpr_compliant` | Maximum privacy; regulatory compliance |
| Vendor sharing | `--preset vendor_sharing` | Balanced; third-party sharing |
| Custom | `--config path/to/your_rules.yaml` | Your own rule set |

## Implementation

1. **Presets** live in `config/presets/`. Each preset is a full YAML with its own `rules` (or `anonymization_rules`).
2. **Default rules** are in `config/anonymization_rules.yaml`. Use this as a template or when you don’t use presets.
3. **Custom config**: copy a preset or the default file, edit rules, then pass `--config your_file.yaml`.

To “track everything” with maximum utility, use `ml_training` or a custom YAML that uses lighter strategies (e.g. more `generalize` with smaller bins, or `preserve` where acceptable). To minimize what’s trackable and maximize privacy, use `gdpr_compliant` or a stricter custom config.

For full schema and strategy options, see `docs/development/configuration_system.md`.
