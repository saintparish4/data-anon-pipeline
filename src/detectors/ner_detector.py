"""
Named Entity Recognition (NER) based PII detector.

Uses spaCy to detect:
- Person names (PERSON entity)
- Locations (GPE, LOC entities)
- Organizations (ORG entity)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NERMatch:
    """Represents a detected named entity."""

    entity_type: str
    value: str
    start: int
    end: int
    confidence: float


class NERDetector:
    """Detects PII using Named Entity Recognition."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NER detector with spaCy model.

        Args:
            model_name: Name of spaCy model to use
        """
        self.model_name = model_name
        self._nlp = None

    @property
    def nlp(self):
        """Lazy load spaCy model."""
        if self._nlp is None:
            try:
                import spacy

                self._nlp = spacy.load(self.model_name)
            except OSError:
                raise RuntimeError(
                    f"spaCy model '{self.model_name}' not found. "
                    f"Install it with: python -m spacy download {self.model_name}"
                )
        return self._nlp

    def detect_persons(self, text: str) -> List[NERMatch]:
        """
        Detect person names in text.

        Args:
            text: Input text to scan

        Returns:
            List of NERMatch objects for detected person names
        """
        doc = self.nlp(text)
        matches = []

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                matches.append(
                    NERMatch(
                        entity_type="person",
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=self._calculate_confidence(ent),
                    )
                )

        return matches

    def detect_locations(self, text: str) -> List[NERMatch]:
        """
        Detect location entities in text.

        Detects both GPE (geopolitical entities) and LOC (locations).

        Args:
            text: Input text to scan

        Returns:
            List of NERMatch objects for detected locations
        """
        doc = self.nlp(text)
        matches = []

        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC"):
                matches.append(
                    NERMatch(
                        entity_type="location",
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=self._calculate_confidence(ent),
                    )
                )

        return matches

    def detect_organizations(self, text: str) -> List[NERMatch]:
        """
        Detect organization entities in text.

        Args:
            text: Input text to scan

        Returns:
            List of NERMatch objects for detected organizations
        """
        doc = self.nlp(text)
        matches = []

        for ent in doc.ents:
            if ent.label_ == "ORG":
                matches.append(
                    NERMatch(
                        entity_type="organization",
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=self._calculate_confidence(ent),
                    )
                )

        return matches

    def detect_all(self, text: str) -> List[NERMatch]:
        """
        Detect all named entities (persons, locations, organizations).

        Args:
            text: Input text to scan

        Returns:
            List of all NERMatch objects found
        """
        doc = self.nlp(text)
        matches = []

        entity_type_map = {
            "PERSON": "person",
            "GPE": "location",
            "LOC": "location",
            "ORG": "organization",
        }

        for ent in doc.ents:
            if ent.label_ in entity_type_map:
                matches.append(
                    NERMatch(
                        entity_type=entity_type_map[ent.label_],
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=self._calculate_confidence(ent),
                    )
                )

        # Sort by start position
        matches.sort(key=lambda m: m.start)

        return matches

    def detect_in_value(self, value: str) -> List[str]:
        """
        Detect entity types in a single value (simplified interface).

        Args:
            value: String value to check

        Returns:
            List of entity type names detected
        """
        if not isinstance(value, str):
            value = str(value)

        matches = self.detect_all(value)
        return list(set(match.entity_type for match in matches))

    def _calculate_confidence(self, entity) -> float:
        """
        Calculate confidence score for a named entity.

        Uses heuristics based on:
        - Entity length (longer names are more reliable)
        - Capitalization patterns
        - Context from spaCy

        Args:
            entity: spaCy entity object

        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.75

        # Longer entities are generally more reliable
        if len(entity.text.split()) >= 2:
            base_confidence += 0.10

        # Proper capitalization increases confidence
        if entity.text[0].isupper():
            base_confidence += 0.05

        # Cap at 0.95
        return min(base_confidence, 0.95)

    def get_available_entity_types(self) -> List[str]:
        """
        Get list of entity types this detector can identify.

        Returns:
            List of entity type names
        """
        return ["person", "location", "organization"]
