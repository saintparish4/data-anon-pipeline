"""
End-to-End Anonymization Pipeline Example

Demonstrates the complete workflow:
1. Load configuration
2. Create sample data
3. Apply anonymization
4. Measure utility preservation
5. Generate comprehensive report

This example shows how all components work together.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_config
from src.anonymizer import Anonymizer
from src.utility_metrics import UtilityMetrics


def create_sample_dataset(n_rows=1000):
    """
    Create a realistic sample dataset with various PII types.
    
    Args:
        n_rows: Number of rows to generate
        
    Returns:
        DataFrame with sample data
    """
    np.random.seed(42)
    
    # Generate realistic data
    data = {
        # Contact information
        'email': [f"user{i}@example.com" for i in range(n_rows)],
        'phone': [f"555-{str(i).zfill(4)}" for i in range(n_rows)],
        
        # Demographics
        'age': np.random.normal(40, 15, n_rows).clip(18, 90).astype(int),
        'income': np.random.normal(60000, 25000, n_rows).clip(20000, 200000).astype(int),
        
        # Location (zipcode - first 5 digits only)
        'zipcode': [f"{10000 + (i % 80000)}" for i in range(n_rows)],
        
        # Transaction data
        'transaction_amount': np.random.exponential(50, n_rows).clip(5, 500),
        'purchase_count': np.random.poisson(5, n_rows),
        
        # Sensitive identifiers
        'ssn': [f"{123 + i % 900}-45-{6789 + i % 9000}" for i in range(n_rows)],
        
        # User ID (for tracking)
        'user_id': [f"USER_{i:06d}" for i in range(n_rows)]
    }
    
    return pd.DataFrame(data)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_dataframe_sample(df, title, n=5):
    """Print a sample of DataFrame with title."""
    print(f"{title}:")
    print(df.head(n).to_string())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {', '.join(df.columns)}\n")


def compare_before_after(original, anonymized, columns):
    """Compare specific columns before and after anonymization."""
    print("\nBefore → After Comparison:")
    print("-" * 70)
    
    for col in columns:
        if col in original.columns:
            orig_val = original[col].iloc[0]
            anon_val = anonymized[col].iloc[0]
            print(f"{col:20} | {str(orig_val):30} → {str(anon_val):30}")


def main():
    """Run the complete end-to-end pipeline."""
    
    print("\n" + "=" * 70)
    print("     DATA ANONYMIZATION PIPELINE - END-TO-END EXAMPLE")
    print("=" * 70)
    
    # =================================================================
    # STEP 1: Create Sample Dataset
    # =================================================================
    print_section("STEP 1: Creating Sample Dataset")
    
    original_df = create_sample_dataset(n_rows=1000)
    print_dataframe_sample(original_df, "Original Dataset Sample")
    
    # Show statistics
    print("Dataset Statistics:")
    print(f"  Total rows: {len(original_df):,}")
    print(f"  PII fields: {len(original_df.columns)}")
    print(f"  Age range: {original_df['age'].min()}-{original_df['age'].max()}")
    print(f"  Income range: ${original_df['income'].min():,.0f}-${original_df['income'].max():,.0f}")
    print(f"  Unique users: {original_df['user_id'].nunique():,}")
    
    # =================================================================
    # STEP 2: Load Configuration
    # =================================================================
    print_section("STEP 2: Loading Configuration")
    
    # Try different presets
    preset_choice = "ml_training"  # Change to: gdpr_compliant, ml_training, vendor_sharing
    
    try:
        if preset_choice in ["gdpr_compliant", "ml_training", "vendor_sharing"]:
            config_path = Path(f"config/presets/{preset_choice}.yaml")
            config = load_config(config_path)
            print(f"Loaded preset: {preset_choice}")
        else:
            config = load_config()
            print("Loaded default configuration")
        
        print(f"Configuration contains {len(config.get_all_rules())} rules")
        
        # Show some rules
        print("\nSample Rules:")
        for pii_type in ['email', 'age', 'income', 'ssn']:
            rule = config.get_rule(pii_type)
            if rule:
                print(f"  {pii_type:15} → {rule.strategy.value}")
        
    except Exception as e:
        print(f"ERROR: Error loading configuration: {e}")
        return 1
    
    # =================================================================
    # STEP 3: Apply Anonymization
    # =================================================================
    print_section("STEP 3: Applying Anonymization")
    
    try:
        anonymizer = Anonymizer(config)
        print("Anonymizer initialized")
        
        print("Anonymizing dataset...")
        anonymized_df = anonymizer.anonymize(original_df)
        print("Anonymization complete")
        
        # Show statistics
        stats = anonymizer.get_statistics()
        print(f"\nAnonymization Statistics:")
        print(f"  Columns processed: {stats['columns_processed']}")
        print(f"  Columns anonymized: {stats['columns_anonymized']}")
        print(f"  Rows processed: {stats['rows_processed']:,}")
        print(f"  Errors: {len(stats['errors'])}")
        
        # Show sample of anonymized data
        print_dataframe_sample(anonymized_df, "\nAnonymized Dataset Sample")
        
        # Compare before/after
        compare_before_after(
            original_df,
            anonymized_df,
            ['email', 'age', 'income', 'phone', 'ssn']
        )
        
    except Exception as e:
        print(f"ERROR: Error during anonymization: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # =================================================================
    # STEP 4: Measure Utility Preservation
    # =================================================================
    print_section("STEP 4: Measuring Utility Preservation")
    
    try:
        print("Calculating utility metrics...")
        metrics = UtilityMetrics(original_df, anonymized_df)
        
        # Analyze numeric columns for distribution preservation
        numeric_cols = ['age', 'income', 'transaction_amount', 'purchase_count']
        
        print("\nDistribution Preservation:")
        print("-" * 70)
        
        for col in numeric_cols:
            try:
                dist_metrics = metrics.calculate_distribution_preservation(col)
                print(f"\n{col}:")
                print(f"  KS Statistic: {dist_metrics.ks_statistic:.4f} (lower is better)")
                print(f"  Mean difference: {dist_metrics.mean_absolute_diff:.2f}")
                print(f"  Interpretation: {dist_metrics.interpretation}")
            except Exception as e:
                print(f"\n{col}: Could not analyze ({e})")
        
        # Correlation preservation
        print("\n\nCorrelation Preservation:")
        print("-" * 70)
        
        try:
            corr_metrics = metrics.calculate_correlation_preservation()
            print(f"Correlation Similarity: {corr_metrics.correlation_similarity:.2%}")
            print(f"Mean Absolute Difference: {corr_metrics.mean_absolute_difference:.4f}")
            print(f"Interpretation: {corr_metrics.interpretation}")
        except Exception as e:
            print(f"Could not calculate correlation: {e}")
        
        # Information loss
        print("\n\nInformation Loss:")
        print("-" * 70)
        
        for col in original_df.columns[:6]:  # Sample first 6 columns
            try:
                info_metrics = metrics.calculate_information_loss(col)
                print(f"\n{col}:")
                print(f"  Unique values: {info_metrics.unique_values_original} → "
                      f"{info_metrics.unique_values_anonymized} "
                      f"({info_metrics.unique_values_retained_pct:.1f}% retained)")
                print(f"  Entropy: {info_metrics.entropy_original:.2f} → "
                      f"{info_metrics.entropy_anonymized:.2f} "
                      f"({info_metrics.entropy_retained_pct:.1f}% retained)")
            except Exception as e:
                print(f"\n{col}: Could not analyze")
        
    except Exception as e:
        print(f"ERROR: Error measuring utility: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # =================================================================
    # STEP 5: Generate Comprehensive Report
    # =================================================================
    print_section("STEP 5: Comprehensive Utility Report")
    
    try:
        print("Generating comprehensive report...")
        report = metrics.generate_report()
        
        print(report.get_summary())
        
        # Export recommendation
        print("\n\n" + "=" * 70)
        print("  NEXT STEPS")
        print("=" * 70)
        print("\n1. Review the utility score and recommendations above")
        print("2. If score < 70%, consider using different preset:")
        print("   - GDPR Compliant: Maximum privacy (score ~65-75%)")
        print("   - ML Training: Maximum utility (score ~85-95%)")
        print("   - Vendor Sharing: Balanced (score ~75-85%)")
        print("\n3. Export anonymized data:")
        print("   anonymized_df.to_csv('anonymized_data.csv', index=False)")
        print("\n4. Measure privacy metrics (k-anonymity) in next example")
        
    except Exception as e:
        print(f"ERROR: Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 70)
    print("     PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())