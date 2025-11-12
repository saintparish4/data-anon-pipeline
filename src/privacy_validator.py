"""
Privacy Validator
Validates anonymized data against privacy requirements including k-anonymity,
l-diversity, and re-identification risk thresholds.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter


class PrivacyValidator:
    """
    Validates privacy guarantees for anonymized datasets.
    
    Checks:
    - k-anonymity: Minimum group size for quasi-identifiers
    - l-diversity: Diversity of sensitive attributes within groups
    - Re-identification risk: Percentage of high-risk records
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator with configuration.
        
        Args:
            config: Configuration dictionary with privacy_thresholds section
        """
        self.config = config
        self.thresholds = config.get('privacy_thresholds', {})
    
    def validate(self, df_anonymized: pd.DataFrame, 
                df_original: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Validate anonymized data against privacy requirements.
        
        Args:
            df_anonymized: Anonymized dataset to validate
            df_original: Original dataset (optional, for comparison)
        
        Returns:
            Dictionary with validation results:
            {
                'passed': bool,
                'checks': {
                    'check_name': {
                        'passed': bool,
                        'message': str,
                        'details': dict
                    }
                },
                'summary': str
            }
        """
        results = {
            'passed': True,
            'checks': {},
            'summary': ''
        }
        
        # Run all enabled checks
        if self.thresholds.get('k_anonymity', {}).get('enabled', False):
            k_result = self._check_k_anonymity(df_anonymized)
            results['checks']['k_anonymity'] = k_result
            if not k_result['passed']:
                results['passed'] = False
        
        if self.thresholds.get('l_diversity', {}).get('enabled', False):
            l_result = self._check_l_diversity(df_anonymized)
            results['checks']['l_diversity'] = l_result
            if not l_result['passed']:
                results['passed'] = False
        
        if self.thresholds.get('reidentification_risk', {}).get('enabled', False):
            risk_result = self._check_reidentification_risk(df_anonymized)
            results['checks']['reidentification_risk'] = risk_result
            if not risk_result['passed']:
                results['passed'] = False
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _check_k_anonymity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check k-anonymity requirement.
        
        k-anonymity means every record is indistinguishable from at least k-1 
        other records with respect to quasi-identifiers.
        
        Args:
            df: Anonymized dataset
        
        Returns:
            Check result with pass/fail status
        """
        k_config = self.thresholds.get('k_anonymity', {})
        required_k = k_config.get('minimum_k', 5)
        quasi_identifiers = k_config.get('quasi_identifiers', [])
        allow_outliers = k_config.get('allow_outliers', False)
        max_outlier_percent = k_config.get('max_outlier_percent', 0)
        
        # Filter quasi-identifiers to only those present in dataframe
        available_qi = [qi for qi in quasi_identifiers if qi in df.columns]
        
        if not available_qi:
            return {
                'passed': False,
                'message': 'No quasi-identifiers found in dataset',
                'min_k': 0,
                'avg_k': 0,
                'quasi_identifiers': quasi_identifiers
            }
        
        # Calculate k-anonymity
        min_k, avg_k, group_sizes = self._calculate_k_anonymity(df, available_qi)
        
        # Check if meets threshold
        passed = min_k >= required_k
        
        # Handle outliers if allowed
        if not passed and allow_outliers:
            # Count records with k < required_k
            outlier_count = sum(1 for size in group_sizes if size < required_k)
            outlier_percent = (outlier_count / len(df)) * 100
            
            if outlier_percent <= max_outlier_percent:
                passed = True
                message = (f"k-anonymity {min_k} below threshold {required_k}, "
                          f"but {outlier_percent:.1f}% outliers acceptable "
                          f"(max: {max_outlier_percent}%)")
            else:
                message = (f"k-anonymity {min_k} below threshold {required_k}, "
                          f"{outlier_percent:.1f}% outliers exceeds limit "
                          f"(max: {max_outlier_percent}%)")
        else:
            if passed:
                message = f"k-anonymity {min_k} meets threshold {required_k}"
            else:
                message = f"k-anonymity {min_k} below threshold {required_k}"
        
        return {
            'passed': passed,
            'message': message,
            'min_k': min_k,
            'avg_k': avg_k,
            'required_k': required_k,
            'quasi_identifiers': available_qi,
            'total_equivalence_classes': len(set(group_sizes))
        }
    
    def _calculate_k_anonymity(self, df: pd.DataFrame, 
                               quasi_identifiers: List[str]) -> Tuple[int, float, List[int]]:
        """
        Calculate k-anonymity value for dataset.
        
        Args:
            df: Dataset to analyze
            quasi_identifiers: List of quasi-identifier column names
        
        Returns:
            Tuple of (min_k, avg_k, list_of_group_sizes)
        """
        # Group by quasi-identifiers and count group sizes
        grouped = df.groupby(quasi_identifiers, dropna=False).size()
        group_sizes = grouped.values.tolist()
        
        if not group_sizes:
            return 0, 0, []
        
        min_k = min(group_sizes)
        avg_k = sum(group_sizes) / len(group_sizes)
        
        return min_k, avg_k, group_sizes
    
    def _check_l_diversity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check l-diversity requirement.
        
        l-diversity ensures that within each equivalence class (group with same
        quasi-identifiers), there are at least l distinct values for sensitive
        attributes.
        
        Args:
            df: Anonymized dataset
        
        Returns:
            Check result with pass/fail status
        """
        l_config = self.thresholds.get('l_diversity', {})
        required_l = l_config.get('minimum_l', 2)
        quasi_identifiers = self.thresholds.get('k_anonymity', {}).get('quasi_identifiers', [])
        sensitive_attributes = l_config.get('sensitive_attributes', [])
        
        # Filter to available columns
        available_qi = [qi for qi in quasi_identifiers if qi in df.columns]
        available_sa = [sa for sa in sensitive_attributes if sa in df.columns]
        
        if not available_sa:
            return {
                'passed': True,
                'message': 'No sensitive attributes specified or found',
                'min_l': None,
                'avg_l': None
            }
        
        if not available_qi:
            return {
                'passed': False,
                'message': 'No quasi-identifiers found for l-diversity check',
                'min_l': 0,
                'avg_l': 0
            }
        
        # Calculate l-diversity for each sensitive attribute
        min_l_overall = float('inf')
        avg_l_overall = 0
        l_values = []
        
        for sensitive_attr in available_sa:
            # Group by quasi-identifiers
            groups = df.groupby(available_qi, dropna=False)[sensitive_attr]
            
            # Count distinct values in each group
            diversity_counts = groups.nunique()
            
            if len(diversity_counts) > 0:
                min_l = diversity_counts.min()
                avg_l = diversity_counts.mean()
                
                min_l_overall = min(min_l_overall, min_l)
                l_values.append(avg_l)
        
        if l_values:
            avg_l_overall = sum(l_values) / len(l_values)
        else:
            min_l_overall = 0
            avg_l_overall = 0
        
        passed = min_l_overall >= required_l
        
        if passed:
            message = f"l-diversity {min_l_overall} meets threshold {required_l}"
        else:
            message = f"l-diversity {min_l_overall} below threshold {required_l}"
        
        return {
            'passed': passed,
            'message': message,
            'min_l': int(min_l_overall) if min_l_overall != float('inf') else 0,
            'avg_l': avg_l_overall,
            'required_l': required_l,
            'sensitive_attributes': available_sa
        }
    
    def _check_reidentification_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check re-identification risk.
        
        Estimates what percentage of records are at high risk of re-identification
        based on quasi-identifier uniqueness.
        
        Args:
            df: Anonymized dataset
        
        Returns:
            Check result with pass/fail status
        """
        risk_config = self.thresholds.get('reidentification_risk', {})
        max_risk_percent = risk_config.get('max_risk_percent', 5.0)
        quasi_identifiers = self.thresholds.get('k_anonymity', {}).get('quasi_identifiers', [])
        
        # Filter to available columns
        available_qi = [qi for qi in quasi_identifiers if qi in df.columns]
        
        if not available_qi:
            return {
                'passed': False,
                'message': 'No quasi-identifiers found for risk assessment',
                'high_risk_percent': 0,
                'high_risk_count': 0
            }
        
        # Calculate risk based on k-anonymity values
        # Records with k=1 are high risk
        # Records with k=2-4 are medium risk
        # Records with k>=5 are low risk
        
        min_k, avg_k, group_sizes = self._calculate_k_anonymity(df, available_qi)
        
        # Map each record to its group size
        grouped = df.groupby(available_qi, dropna=False).size()
        df_temp = df.copy()
        df_temp['_group_size'] = df_temp.groupby(available_qi, dropna=False)[available_qi[0]].transform('count')
        
        # Count high-risk records (k <= 2)
        high_risk_count = len(df_temp[df_temp['_group_size'] <= 2])
        high_risk_percent = (high_risk_count / len(df)) * 100
        
        # Medium risk (k = 3-4)
        medium_risk_count = len(df_temp[(df_temp['_group_size'] >= 3) & (df_temp['_group_size'] <= 4)])
        medium_risk_percent = (medium_risk_count / len(df)) * 100
        
        # Low risk (k >= 5)
        low_risk_count = len(df_temp[df_temp['_group_size'] >= 5])
        low_risk_percent = (low_risk_count / len(df)) * 100
        
        passed = high_risk_percent <= max_risk_percent
        
        if passed:
            message = f"Re-identification risk {high_risk_percent:.1f}% below threshold {max_risk_percent}%"
        else:
            message = f"Re-identification risk {high_risk_percent:.1f}% exceeds threshold {max_risk_percent}%"
        
        return {
            'passed': passed,
            'message': message,
            'high_risk_percent': round(high_risk_percent, 2),
            'high_risk_count': high_risk_count,
            'medium_risk_percent': round(medium_risk_percent, 2),
            'medium_risk_count': medium_risk_count,
            'low_risk_percent': round(low_risk_percent, 2),
            'low_risk_count': low_risk_count,
            'max_risk_percent': max_risk_percent
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of validation results.
        
        Args:
            results: Validation results dictionary
        
        Returns:
            Summary string
        """
        if results['passed']:
            summary = "✓ All privacy checks passed"
        else:
            failed_checks = [name for name, check in results['checks'].items() 
                           if not check['passed']]
            summary = f"✗ Privacy validation failed: {', '.join(failed_checks)}"
        
        return summary
    
    def get_detailed_report(self, df_anonymized: pd.DataFrame,
                          df_original: Optional[pd.DataFrame] = None) -> str:
        """
        Generate detailed privacy validation report.
        
        Args:
            df_anonymized: Anonymized dataset
            df_original: Original dataset (optional)
        
        Returns:
            Formatted report string
        """
        results = self.validate(df_anonymized, df_original)
        
        report_lines = [
            "=" * 70,
            "PRIVACY VALIDATION REPORT",
            "=" * 70,
            "",
            f"Overall Status: {results['summary']}",
            "",
            "=" * 70,
            "DETAILED CHECK RESULTS",
            "=" * 70,
            ""
        ]
        
        for check_name, check_result in results['checks'].items():
            status = "✓ PASSED" if check_result['passed'] else "✗ FAILED"
            report_lines.append(f"{check_name.upper()}: {status}")
            report_lines.append(f"  {check_result['message']}")
            
            # Add check-specific details
            if check_name == 'k_anonymity':
                report_lines.append(f"  Minimum k: {check_result.get('min_k', 'N/A')}")
                report_lines.append(f"  Average k: {check_result.get('avg_k', 'N/A'):.2f}")
                report_lines.append(f"  Required k: {check_result.get('required_k', 'N/A')}")
                
            elif check_name == 'l_diversity':
                if check_result.get('min_l') is not None:
                    report_lines.append(f"  Minimum l: {check_result.get('min_l', 'N/A')}")
                    report_lines.append(f"  Average l: {check_result.get('avg_l', 'N/A'):.2f}")
                    report_lines.append(f"  Required l: {check_result.get('required_l', 'N/A')}")
            
            elif check_name == 'reidentification_risk':
                report_lines.append(f"  High risk: {check_result.get('high_risk_percent', 0):.1f}% "
                                  f"({check_result.get('high_risk_count', 0)} records)")
                report_lines.append(f"  Medium risk: {check_result.get('medium_risk_percent', 0):.1f}% "
                                  f"({check_result.get('medium_risk_count', 0)} records)")
                report_lines.append(f"  Low risk: {check_result.get('low_risk_percent', 0):.1f}% "
                                  f"({check_result.get('low_risk_count', 0)} records)")
            
            report_lines.append("")
        
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)


if __name__ == "__main__":
    # Example usage
    import yaml
    
    # Sample config
    config = {
        'privacy_thresholds': {
            'k_anonymity': {
                'enabled': True,
                'minimum_k': 5,
                'quasi_identifiers': ['age', 'zipcode', 'gender']
            },
            'l_diversity': {
                'enabled': True,
                'minimum_l': 2,
                'sensitive_attributes': ['income', 'diagnosis']
            },
            'reidentification_risk': {
                'enabled': True,
                'max_risk_percent': 5.0
            }
        }
    }
    
    # Sample data
    df = pd.DataFrame({
        'age': [25, 25, 30, 30, 35, 35, 35, 35, 35, 35],
        'zipcode': ['10001', '10001', '10002', '10002', '10003', '10003', '10003', '10003', '10003', '10003'],
        'gender': ['M', 'M', 'F', 'F', 'M', 'M', 'M', 'F', 'F', 'F'],
        'income': [50000, 55000, 60000, 65000, 70000, 75000, 80000, 70000, 75000, 80000]
    })
    
    # Validate
    validator = PrivacyValidator(config)
    results = validator.validate(df)
    
    print(validator.get_detailed_report(df))