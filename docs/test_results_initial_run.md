# Initial Test Run Results - End-to-End Pipeline

**Date:** Initial run  
**Test File:** `example_end_to_end_pipeline.py`  
**Configuration:** `ml_training` preset

## Summary

The end-to-end pipeline executed successfully, but utility metrics calculation failed for generalized numeric columns, resulting in a poor utility score of **57.4%**.

## Test Execution

### Step 1: Dataset Creation
- Created sample dataset with 1,000 rows
- Generated 9 columns: email, phone, age, income, zipcode, transaction_amount, purchase_count, ssn, user_id
- Age range: 18-90
- Income range: $20,000-$139,827

### Step 2: Configuration Loading
- Successfully loaded `ml_training` preset
- Configuration contains 30 rules
- Sample rules applied:
  - `email` → hash
  - `age` → generalize
  - `income` → generalize
  - `ssn` → redact_full

### Step 3: Anonymization
- Anonymizer initialized successfully
- Processed 9 columns, anonymized 8 columns
- Processed 1,000 rows
- 1 error encountered (details not shown)

**Sample Transformations:**
- `email`: `user0@example.com` → `62048e165e05a183e4fcdd9d548e44489095880b165c1a5d8da017e0139e7103` (hashed)
- `age`: `47` → `45-49` (generalized to range)
- `income`: `94983` → `90000-94999` (generalized to range)
- `phone`: `555-0000` → `d12ddee4b597b984bfdda012894f281cd84565a2f2bb0533389dfd4bb7f2838f` (hashed)
- `ssn`: `123-45-6789` → `[REDACTED]` (fully redacted)

### Step 4: Utility Metrics Calculation

#### Distribution Preservation - FAILED
All numeric columns failed with error: **"Column 'X' has no valid numeric values"**

**Affected Columns:**
- `age`: Could not analyze
- `income`: Could not analyze
- `transaction_amount`: Could not analyze
- `purchase_count`: Could not analyze

**Root Cause:** Generalized columns return string ranges (e.g., "45-49", "90000-94999") which cannot be directly converted to numeric values for statistical analysis.

#### Correlation Preservation - FAILED
Error: **"No valid correlations to compare"**

**Root Cause:** Since distribution metrics failed for all numeric columns, correlation analysis had no valid numeric data to work with.

#### Information Loss Metrics - PARTIAL SUCCESS
Some metrics calculated successfully:

| Column | Unique Values Retained | Entropy Retained | Status |
|--------|----------------------|------------------|--------|
| email | 100.0% | 100.0% | Minimal loss |
| phone | 100.0% | 100.0% | Minimal loss |
| age | 25.4% | 62.0% | High loss |
| income | 2.4% | 42.8% | High loss |
| zipcode | 100.0% | 100.0% | Minimal loss |
| transaction_amount | 3.1% | 40.4% | High loss |
| purchase_count | (not shown) | (not shown) | High loss |
| ssn | (not shown) | (not shown) | High loss |
| user_id | 100.0% | 100.0% | Minimal loss |

### Step 5: Overall Utility Report

**Overall Utility Score: 57.4%**  
**Interpretation: Poor - Consider less aggressive anonymization**

**Issues Identified:**
1. Distribution preservation metrics completely failed
2. Correlation preservation metrics completely failed
3. High information loss in generalized columns (age, income, transaction_amount, purchase_count)
4. Utility score calculation likely incomplete due to missing distribution/correlation data

## Problems Identified

1. **Generalized Range Parsing:** Utility metrics cannot parse generalized ranges (e.g., "45-49") to extract numeric values for statistical analysis
2. **Missing Midpoint Extraction:** Need to convert ranges to midpoint values (e.g., "45-49" → 47) for distribution analysis
3. **Incomplete Metrics:** Without distribution and correlation metrics, the overall utility score is incomplete and misleading

## Recommendations

1. **Fix utility metrics to handle generalized ranges:**
   - Parse range strings (e.g., "45-49") to extract midpoint or use range boundaries
   - Convert generalized columns back to numeric for statistical analysis
   
2. **Improve error handling:**
   - Provide more informative error messages
   - Gracefully handle mixed data types (some rows generalized, some not)
   
3. **Enhance utility score calculation:**
   - Ensure all metric types contribute to overall score
   - Weight metrics appropriately when some are missing

## Next Steps

1. Implement range parsing in utility metrics module
2. Update distribution preservation to handle generalized columns
3. Re-run tests to verify improved metrics
4. Target utility score: >70% for ml_training preset

