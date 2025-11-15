"""
Risk Assessment Engine.

Calculates uniqueness and risk scores for records based on quasi-identifiers.
Implements k-anonymity concepts to assess re-identification risk.
"""

import pandas as pd
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from collections import Counter


@dataclass
class UniquenessResult:
    """Represents uniqueness analysis for a record."""
    record_index: int
    k_anonymity: int  # Number of records with same quasi-identifiers
    quasi_identifier_values: Dict[str, Any]
    is_unique: bool  # k=1
    is_rare: bool  # k=2-5
    is_safe: bool  # k>10


@dataclass
class RiskScore:
    """Represents risk assessment for a record."""
    record_index: int
    risk_level: str  # 'high', 'medium', 'low'
    risk_score: float  # 0.0 (low) to 1.0 (high)
    unique_on_qi_count: int  # Number of QI combinations where record is unique
    k_anonymity: int
    reasoning: str


@dataclass
class RiskReport:
    """Aggregate risk assessment report."""
    total_records: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    high_risk_percentage: float
    medium_risk_percentage: float
    low_risk_percentage: float
    average_k_anonymity: float
    min_k_anonymity: int
    unique_records: List[int]  # Record indices
    rare_records: List[int]  # Record indices
    safe_records: List[int]  # Record indices


class RiskAssessmentEngine:
    """
    Assess re-identification risk based on uniqueness and k-anonymity.
    
    Uses quasi-identifiers to determine how easily records can be 
    re-identified in a dataset.
    """
    
    def __init__(self):
        """Initialize the risk assessment engine."""
        pass
    
    def calculate_uniqueness(
        self, 
        df: pd.DataFrame, 
        quasi_identifiers: List[str]
    ) -> List[UniquenessResult]:
        """
        Calculate uniqueness for each record based on quasi-identifiers.
        
        Args:
            df: DataFrame to analyze
            quasi_identifiers: List of column names to use as quasi-identifiers
            
        Returns:
            List of UniquenessResult objects, one per record
        """
        # Validate quasi-identifiers exist in DataFrame
        missing_cols = set(quasi_identifiers) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Quasi-identifiers not found in DataFrame: {missing_cols}")
        
        results = []
        
        # Group by quasi-identifiers to count occurrences
        qi_counts = df.groupby(quasi_identifiers).size()
        
        for idx, row in df.iterrows():
            # Get quasi-identifier values for this record
            qi_values = {qi: row[qi] for qi in quasi_identifiers}
            
            # Get k-anonymity (count of records with same QI values)
            # Handle single vs multiple QIs differently for pandas indexing
            if len(quasi_identifiers) == 1:
                # Single QI: access with scalar value
                k = qi_counts[row[quasi_identifiers[0]]]
            else:
                # Multiple QIs: access with tuple
                qi_tuple = tuple(row[qi] for qi in quasi_identifiers)
                k = qi_counts[qi_tuple]
            
            # Classify based on k-anonymity thresholds
            is_unique = (k == 1)
            is_rare = (2 <= k <= 9)  # Rare to insufficient anonymity
            is_safe = (k >= 10)  # Meets k>=10 standard
            
            results.append(UniquenessResult(
                record_index=idx,
                k_anonymity=k,
                quasi_identifier_values=qi_values,
                is_unique=is_unique,
                is_rare=is_rare,
                is_safe=is_safe
            ))
        
        return results
    
    def calculate_risk_scores(
        self,
        df: pd.DataFrame,
        quasi_identifier_sets: List[List[str]]
    ) -> List[RiskScore]:
        """
        Calculate risk scores for each record.
        
        Risk is based on how many quasi-identifier combinations make a 
        record unique.
        
        Args:
            df: DataFrame to analyze
            quasi_identifier_sets: List of QI combinations to test
                                   e.g., [['age', 'zip'], ['age', 'gender']]
            
        Returns:
            List of RiskScore objects, one per record
        """
        risk_scores = []
        
        # For each record, check uniqueness across all QI sets
        for idx in df.index:
            unique_count = 0
            k_values = []
            
            for qi_set in quasi_identifier_sets:
                uniqueness_results = self.calculate_uniqueness(df, qi_set)
                # Find result matching this record index
                result = next((r for r in uniqueness_results if r.record_index == idx), None)
                if result is None:
                    # Fallback: use position if index is integer and sequential
                    if isinstance(idx, int) and 0 <= idx < len(uniqueness_results):
                        result = uniqueness_results[idx]
                    else:
                        raise ValueError(f"Could not find uniqueness result for record index {idx}")
                k_values.append(result.k_anonymity)
                
                if result.is_unique:
                    unique_count += 1
            
            # Calculate risk level and score
            risk_level, risk_score, reasoning = self._determine_risk_level(
                unique_count, 
                len(quasi_identifier_sets),
                min(k_values) if k_values else 1
            )
            
            risk_scores.append(RiskScore(
                record_index=idx,
                risk_level=risk_level,
                risk_score=risk_score,
                unique_on_qi_count=unique_count,
                k_anonymity=min(k_values) if k_values else 1,
                reasoning=reasoning
            ))
        
        return risk_scores
    
    def _determine_risk_level(
        self,
        unique_count: int,
        total_qi_sets: int,
        min_k: int
    ) -> Tuple[str, float, str]:
        """
        Determine risk level based on uniqueness patterns.
        
        Rules (based on k-anonymity best practices):
        - High risk: k=1 (unique) or k=2 (extremely rare) - easily re-identifiable
        - Medium risk: k=3-9 (rare/insufficient) - below standard k=10 threshold
        - Low risk: k≥10 (adequate anonymity) - meets common privacy standards
        
        Args:
            unique_count: Number of QI sets where record is unique
            total_qi_sets: Total number of QI sets tested
            min_k: Minimum k-anonymity across all QI sets
            
        Returns:
            Tuple of (risk_level, risk_score, reasoning)
        """
        # High risk: unique on 2+ QI combinations (check this first - most critical)
        if unique_count >= 2:
            risk_score = 0.9 + (unique_count / max(total_qi_sets, 1)) * 0.1
            reasoning = f"Unique on {unique_count} different quasi-identifier combinations"
            return 'high', min(risk_score, 1.0), reasoning
        
        # High risk: uniquely identifiable (k=1) but only on 1 QI set
        if min_k == 1:
            risk_score = 0.95
            reasoning = f"Uniquely identifiable (k=1) - high re-identification risk"
            return 'high', risk_score, reasoning
        
        # Medium risk: unique on exactly 1 QI combination (when unique_count=1, min_k≥2)
        if unique_count == 1:
            # Score varies based on min_k (k=2 → 0.75, k=3 → 0.65, k≥5 → 0.55)
            risk_score = 0.5 + min(0.25, (5.0 - min_k) / 10.0)
            reasoning = f"Unique on 1 quasi-identifier combination"
            return 'medium', risk_score, reasoning
        
        # High risk: extremely rare records (k=2) - very high re-identification risk
        if min_k == 2:
            risk_score = 0.90
            reasoning = f"Extremely rare (k=2) - very high re-identification risk"
            return 'high', risk_score, reasoning
        
        # Medium risk: rare to insufficient anonymity (k=3-9)
        # Below the common k=10 threshold used in privacy standards
        if 3 <= min_k <= 9:
            # Score decreases as k increases (k=3 → 0.6, k=5 → 0.5, k=9 → 0.3)
            risk_score = 0.3 + (10.0 - min_k) / 33.33
            reasoning = f"Insufficient anonymity (k={min_k}) - below k≥10 standard"
            return 'medium', risk_score, reasoning
        
        # Low risk: adequate anonymity (k≥10)
        # Meets common k-anonymity thresholds for privacy protection
        # min_k >= 10
        # Score decreases as k increases (k=10 → 0.35, k=20 → 0.225, k→∞ → 0.10)
        risk_score = 0.1 + (10.0 / min_k) * 0.25
        if min_k >= 20:
            reasoning = f"safe anonymity (k={min_k}) - well-protected"
        elif min_k >= 15:
            reasoning = f"safe anonymity (k={min_k}) - adequately protected"
        else:
            reasoning = f"Adequate anonymity (k={min_k}) - meets k≥10 standard"
        return 'low', min(risk_score, 0.40), reasoning
    
    def generate_risk_report(
        self,
        df: pd.DataFrame,
        risk_scores: List[RiskScore]
    ) -> RiskReport:
        """
        Generate aggregate risk report from individual risk scores.
        
        Args:
            df: DataFrame that was analyzed
            risk_scores: List of RiskScore objects
            
        Returns:
            RiskReport with aggregate statistics
        """
        total = len(risk_scores)
        
        # Count by risk level
        risk_counter = Counter(rs.risk_level for rs in risk_scores)
        high_count = risk_counter['high']
        medium_count = risk_counter['medium']
        low_count = risk_counter['low']
        
        # Calculate percentages
        high_pct = (high_count / total * 100) if total > 0 else 0
        medium_pct = (medium_count / total * 100) if total > 0 else 0
        low_pct = (low_count / total * 100) if total > 0 else 0
        
        # Calculate k-anonymity statistics
        k_values = [rs.k_anonymity for rs in risk_scores]
        avg_k = sum(k_values) / len(k_values) if k_values else 0
        min_k = min(k_values) if k_values else 0
        
        # Categorize records
        unique_records = [rs.record_index for rs in risk_scores if rs.k_anonymity == 1]
        rare_records = [rs.record_index for rs in risk_scores if 2 <= rs.k_anonymity <= 5]
        safe_records = [rs.record_index for rs in risk_scores if rs.k_anonymity > 10]
        
        return RiskReport(
            total_records=total,
            high_risk_count=high_count,
            medium_risk_count=medium_count,
            low_risk_count=low_count,
            high_risk_percentage=round(high_pct, 2),
            medium_risk_percentage=round(medium_pct, 2),
            low_risk_percentage=round(low_pct, 2),
            average_k_anonymity=round(avg_k, 2),
            min_k_anonymity=min_k,
            unique_records=unique_records,
            rare_records=rare_records,
            safe_records=safe_records
        )
    
    def assess_dataset(
        self,
        df: pd.DataFrame,
        quasi_identifier_sets: List[List[str]]
    ) -> Tuple[List[RiskScore], RiskReport]:
        """
        Perform complete risk assessment on a dataset.
        
        Args:
            df: DataFrame to analyze
            quasi_identifier_sets: List of QI combinations to test
            
        Returns:
            Tuple of (risk_scores, risk_report)
        """
        # Calculate risk scores
        risk_scores = self.calculate_risk_scores(df, quasi_identifier_sets)
        
        # Generate aggregate report
        risk_report = self.generate_risk_report(df, risk_scores)
        
        return risk_scores, risk_report
    
    def assess(
        self,
        df: pd.DataFrame,
        scan_results: Dict
    ) -> Dict:
        """
        Convenience method for assessing risk with PII scan results.
        
        This method integrates with PII scanner results to automatically
        infer quasi-identifiers and perform risk assessment.
        
        Args:
            df: DataFrame to analyze
            scan_results: Results from PIIScanner (dict of column -> PIIResult)
            
        Returns:
            Dictionary with risk assessment results including:
            - total_records: Number of records analyzed
            - risk_distribution: Count/percentage by risk level
            - risk_scores: List of individual risk scores
            - risk_report: Aggregate RiskReport object
        """
        # Infer quasi-identifiers from PII results
        quasi_ids = infer_quasi_identifiers(df, scan_results)
        
        if not quasi_ids:
            # No quasi-identifiers found, return default safe assessment
            return {
                'total_records': len(df),
                'risk_distribution': {
                    'high': {'count': 0, 'percentage': 0.0},
                    'medium': {'count': 0, 'percentage': 0.0},
                    'low': {'count': len(df), 'percentage': 100.0}
                },
                'risk_scores': [],
                'risk_report': None,
                'quasi_identifiers': []
            }
        
        # Create QI sets to test
        qi_sets = [quasi_ids]  # Test all QIs together
        # Also test pairs of QIs for more detailed analysis
        if len(quasi_ids) > 1:
            for i, qi in enumerate(quasi_ids[:3]):  # Limit to first 3 to avoid too many combinations
                qi_sets.append([qi])
        
        # Perform risk assessment
        risk_scores, risk_report = self.assess_dataset(df, qi_sets)
        
        # Format results
        return {
            'total_records': risk_report.total_records,
            'risk_distribution': {
                'high': {
                    'count': risk_report.high_risk_count,
                    'percentage': risk_report.high_risk_percentage
                },
                'medium': {
                    'count': risk_report.medium_risk_count,
                    'percentage': risk_report.medium_risk_percentage
                },
                'low': {
                    'count': risk_report.low_risk_count,
                    'percentage': risk_report.low_risk_percentage
                }
            },
            'average_k_anonymity': risk_report.average_k_anonymity,
            'min_k_anonymity': risk_report.min_k_anonymity,
            'risk_scores': risk_scores,
            'risk_report': risk_report,
            'quasi_identifiers': quasi_ids
        }
    
    def get_high_risk_records(
        self,
        df: pd.DataFrame,
        risk_scores: List[RiskScore],
        limit: int = 10
    ) -> pd.DataFrame:
        """
        Get high-risk records from the dataset.
        
        Args:
            df: Original DataFrame
            risk_scores: List of RiskScore objects
            limit: Maximum number of records to return
            
        Returns:
            DataFrame with high-risk records
        """
        # Filter high-risk scores
        high_risk = [rs for rs in risk_scores if rs.risk_level == 'high']
        
        # Sort by risk score (highest first)
        high_risk.sort(key=lambda rs: rs.risk_score, reverse=True)
        
        # Get record indices
        indices = [rs.record_index for rs in high_risk[:limit]]
        
        # Return DataFrame with those records
        result_df = df.loc[indices].copy()
        result_df['risk_score'] = [rs.risk_score for rs in high_risk[:limit]]
        result_df['risk_reasoning'] = [rs.reasoning for rs in high_risk[:limit]]
        
        return result_df


def infer_quasi_identifiers(df: pd.DataFrame, pii_results: Dict) -> List[str]:
    """
    Infer potential quasi-identifiers from PII detection results.
    
    Quasi-identifiers are typically demographic or geographic attributes
    that can be combined to identify individuals.
    
    IMPORTANT: Excludes direct identifiers (name, email, phone, SSN, etc.)
    
    Args:
        df: DataFrame being analyzed
        pii_results: PII detection results from scanner
        
    Returns:
        List of column names that are likely quasi-identifiers
    """
    # Direct identifiers to EXCLUDE (these are not quasi-identifiers)
    direct_identifiers = [
        'name', 'email', 'phone', 'ssn', 'social_security', 
        'credit_card', 'card', 'address', 'street', 'full_address'
    ]
    
    quasi_identifiers = []
    
    # Common quasi-identifier patterns
    qi_keywords = ['age', 'zip', 'zipcode', 'gender', 'city', 'state', 
                   'birth', 'dob', 'date_of_birth', 'income', 'salary',
                   'company', 'employer', 'organization', 'occupation', 'job']
    
    for column in df.columns:
        col_lower = column.lower()
        
        # Skip direct identifiers
        if any(di in col_lower for di in direct_identifiers):
            continue
        
        # Check if column name matches QI patterns
        if any(keyword in col_lower for keyword in qi_keywords):
            quasi_identifiers.append(column)
            continue
        
        # Check if column has location, demographic, or organization info from PII detection
        # But only if it's not a direct identifier
        if column in pii_results:
            pii_types = pii_results[column].pii_types
            # Include location (if not street address), organization, and other QI-relevant types
            if 'location' in pii_types and 'address' not in col_lower:
                quasi_identifiers.append(column)
            elif 'organization' in pii_types:
                quasi_identifiers.append(column)
    
    return quasi_identifiers