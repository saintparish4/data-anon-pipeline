"""
PII Scanner Orchestrator.

Combines regex-based and NER-based detection to provide comprehensive
PII scanning with structured output and confidence scores.
"""

import pandas as pd
import json
from typing import Dict, List, Union, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from src.detectors.regex_detector import RegexDetector
from src.detectors.ner_detector import NERDetector


@dataclass
class PIIDetectionResult:
    """Represents the result of PII detection for a field."""

    field_name: str
    pii_types: List[str]
    confidence: float
    sample_values: List[str]
    detection_count: int


class PIIScanner:
    """
    Orchestrates PII detection across multiple detectors.

    Combines regex-based and NER-based detection to identify PII in
    structured data (CSV, JSON) and returns detailed results.
    """

    def __init__(self, use_ner: bool = True):
        """
        Initialize the PII scanner.

        Args:
            use_ner: Whether to use NER detection (requires spaCy)
        """
        self.regex_detector = RegexDetector()
        self.use_ner = use_ner
        self.ner_detector = None

        if use_ner:
            try:
                self.ner_detector = NERDetector()
                # Test that the model can be loaded (triggers lazy loading)
                _ = self.ner_detector.nlp
            except (RuntimeError, OSError) as e:
                print(
                    f"Warning: spaCy model not available ({e}). NER detection disabled."
                )
                self.use_ner = False
                self.ner_detector = None

    def scan_dataframe(
        self, df: pd.DataFrame, sample_size: int = 100
    ) -> Dict[str, PIIDetectionResult]:
        """
        Scan a pandas DataFrame for PII.

        Args:
            df: DataFrame to scan
            sample_size: Number of rows to sample for detection

        Returns:
            Dictionary mapping field names to detection results
        """
        results = {}

        for column in df.columns:
            result = self._scan_column(df[column], column, sample_size)
            if result.pii_types:  # Only include if PII was detected
                results[column] = result

        return results

    def scan_csv(
        self, filepath: str, sample_size: int = 100
    ) -> Dict[str, PIIDetectionResult]:
        """
        Scan a CSV file for PII.

        Args:
            filepath: Path to CSV file
            sample_size: Number of rows to sample for detection

        Returns:
            Dictionary mapping field names to detection results
        """
        df = pd.read_csv(filepath)
        return self.scan_dataframe(df, sample_size)

    def scan_json(
        self, filepath: str, sample_size: int = 100
    ) -> Dict[str, PIIDetectionResult]:
        """
        Scan a JSON file for PII.

        Handles both list of objects and single object formats.

        Args:
            filepath: Path to JSON file
            sample_size: Number of records to sample for detection

        Returns:
            Dictionary mapping field names to detection results
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        # Convert to DataFrame for consistent processing
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported JSON format: {type(data)}")

        return self.scan_dataframe(df, sample_size)

    def scan_file(
        self, filepath: str, sample_size: int = 100
    ) -> Dict[str, PIIDetectionResult]:
        """
        Scan a file for PII (auto-detects format).

        Args:
            filepath: Path to file (CSV or JSON)
            sample_size: Number of records to sample for detection

        Returns:
            Dictionary mapping field names to detection results
        """
        path = Path(filepath)

        if path.suffix.lower() == ".csv":
            return self.scan_csv(filepath, sample_size)
        elif path.suffix.lower() == ".json":
            return self.scan_json(filepath, sample_size)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    def _scan_column(
        self, series: pd.Series, column_name: str, sample_size: int
    ) -> PIIDetectionResult:
        """
        Scan a single column/series for PII.

        Args:
            series: Pandas Series to scan
            column_name: Name of the column
            sample_size: Number of values to sample

        Returns:
            PIIDetectionResult for this column
        """
        # Sample the data
        sample = series.dropna().head(sample_size)

        if len(sample) == 0:
            return PIIDetectionResult(
                field_name=column_name,
                pii_types=[],
                confidence=0.0,
                sample_values=[],
                detection_count=0,
            )

        # Aggregate detection results
        pii_type_counts = {}
        detected_values = []
        total_confidence = 0.0
        detection_count = 0

        for value in sample:
            if not isinstance(value, str):
                value = str(value)

            # Skip empty values
            if not value.strip():
                continue

            # Detect with regex
            regex_types = self.regex_detector.detect_in_value(value)

            # Detect with NER if enabled
            ner_types = []
            if self.use_ner and self.ner_detector:
                ner_types = self.ner_detector.detect_in_value(value)

            # Combine results
            all_types = set(regex_types + ner_types)

            if all_types:
                detection_count += 1
                detected_values.append(value[:50])  # Truncate for display

                for pii_type in all_types:
                    pii_type_counts[pii_type] = pii_type_counts.get(pii_type, 0) + 1

        # Calculate confidence based on consistency of detection
        if detection_count > 0:
            # Higher confidence if more samples contain PII
            consistency_ratio = detection_count / len(sample)
            # Higher confidence if same PII type detected consistently
            max_type_count = max(pii_type_counts.values()) if pii_type_counts else 0
            type_consistency = (
                max_type_count / detection_count if detection_count > 0 else 0
            )

            confidence = consistency_ratio * 0.6 + type_consistency * 0.4
        else:
            confidence = 0.0

        # Get top PII types
        sorted_types = sorted(pii_type_counts.items(), key=lambda x: x[1], reverse=True)
        pii_types = [pii_type for pii_type, _ in sorted_types]

        return PIIDetectionResult(
            field_name=column_name,
            pii_types=pii_types,
            confidence=round(confidence, 2),
            sample_values=detected_values[:3],  # Keep top 3 samples
            detection_count=detection_count,
        )

    def generate_report(
        self, results: Dict[str, PIIDetectionResult], format: str = "dict"
    ) -> Union[Dict, str]:
        """
        Generate a report from scan results.

        Args:
            results: Dictionary of detection results
            format: Output format ('dict', 'json', or 'text')

        Returns:
            Report in specified format
        """
        if format == "dict":
            return {
                "summary": self._generate_summary(results),
                "fields": {k: asdict(v) for k, v in results.items()},
            }
        elif format == "json":
            report = self.generate_report(results, format="dict")
            return json.dumps(report, indent=2)
        elif format == "text":
            return self._generate_text_report(results)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_summary(
        self, results: Dict[str, PIIDetectionResult]
    ) -> Dict[str, Any]:
        """Generate summary statistics from results."""
        if not results:
            return {
                "total_fields": 0,
                "fields_with_pii": 0,
                "pii_types_found": [],
                "high_confidence_fields": 0,
            }

        all_pii_types = set()
        high_confidence_count = 0

        for result in results.values():
            all_pii_types.update(result.pii_types)
            if result.confidence >= 0.8:
                high_confidence_count += 1

        return {
            "total_fields_scanned": len(results),
            "fields_with_pii": len(results),
            "pii_types_found": sorted(list(all_pii_types)),
            "high_confidence_fields": high_confidence_count,
        }

    def _generate_text_report(self, results: Dict[str, PIIDetectionResult]) -> str:
        """Generate human-readable text report."""
        if not results:
            return "No PII detected in the scanned data."

        lines = []
        lines.append("=" * 70)
        lines.append("PII DETECTION REPORT")
        lines.append("=" * 70)
        lines.append("")

        summary = self._generate_summary(results)
        lines.append("SUMMARY:")
        lines.append(f"  Fields scanned: {summary['total_fields_scanned']}")
        lines.append(f"  Fields with PII: {summary['fields_with_pii']}")
        lines.append(
            f"  High confidence detections: {summary['high_confidence_fields']}"
        )
        lines.append(f"  PII types found: {', '.join(summary['pii_types_found'])}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("DETAILED RESULTS:")
        lines.append("-" * 70)
        lines.append("")

        for field_name, result in sorted(results.items()):
            lines.append(f"Field: {field_name}")
            lines.append(f"  PII Types: {', '.join(result.pii_types)}")
            lines.append(f"  Confidence: {result.confidence:.2f}")
            lines.append(f"  Detections: {result.detection_count}")
            if result.sample_values:
                lines.append(f"  Sample values:")
                for sample in result.sample_values:
                    lines.append(f"    - {sample}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)

    def get_high_risk_fields(
        self, results: Dict[str, PIIDetectionResult], threshold: float = 0.8
    ) -> List[str]:
        """
        Get list of high-risk fields (high confidence PII detection).

        Args:
            results: Dictionary of detection results
            threshold: Confidence threshold for high risk

        Returns:
            List of field names with high-risk PII
        """
        return [
            field_name
            for field_name, result in results.items()
            if result.confidence >= threshold
        ]
