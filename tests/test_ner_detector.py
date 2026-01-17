"""
Unit tests for ner_detector.py

Tests person, location, and organization detection using spaCy.
"""

import pytest
from src.detectors.ner_detector import NERDetector, NERMatch


# Skip tests if spaCy model is not installed
def check_spacy_model():
    """Check if spaCy model is available."""
    try:
        import spacy

        spacy.load("en_core_web_sm")
        return True
    except (ImportError, OSError):
        return False


requires_spacy = pytest.mark.skipif(
    not check_spacy_model(), reason="spaCy model 'en_core_web_sm' not installed"
)


@requires_spacy
class TestPersonDetection:
    """Test person name detection functionality."""

    @pytest.fixture
    def detector(self):
        return NERDetector()

    def test_detect_single_person_name(self, detector):
        """Test detection of a single person name."""
        text = "John Smith works at the company."
        matches = detector.detect_persons(text)

        assert len(matches) >= 1
        assert any("John Smith" in match.value for match in matches)

    def test_detect_multiple_person_names(self, detector):
        """Test detection of multiple person names."""
        text = "John Smith and Mary Johnson attended the meeting."
        matches = detector.detect_persons(text)

        assert len(matches) >= 2
        person_names = [match.value for match in matches]
        assert any("John Smith" in name for name in person_names)
        assert any("Mary Johnson" in name or "Johnson" in name for name in person_names)

    def test_person_match_attributes(self, detector):
        """Test that person matches have correct attributes."""
        text = "Alice Cooper is here."
        matches = detector.detect_persons(text)

        assert len(matches) >= 1
        match = matches[0]

        assert match.entity_type == "person"
        assert isinstance(match.value, str)
        assert isinstance(match.start, int)
        assert isinstance(match.end, int)
        assert 0 <= match.confidence <= 1

    def test_no_person_in_text(self, detector):
        """Test that no false positives occur."""
        text = "The quick brown fox jumps over the lazy dog."
        matches = detector.detect_persons(text)

        # Should not detect any persons
        assert len(matches) == 0


@requires_spacy
class TestLocationDetection:
    """Test location detection functionality."""

    @pytest.fixture
    def detector(self):
        return NERDetector()

    def test_detect_city_name(self, detector):
        """Test detection of city names."""
        text = "I live in New York City."
        matches = detector.detect_locations(text)

        assert len(matches) >= 1
        assert any("New York" in match.value for match in matches)

    def test_detect_country_name(self, detector):
        """Test detection of country names."""
        text = "I visited France last summer."
        matches = detector.detect_locations(text)

        assert len(matches) >= 1
        assert any("France" in match.value for match in matches)

    def test_detect_multiple_locations(self, detector):
        """Test detection of multiple locations."""
        text = "The trip from London to Paris was amazing."
        matches = detector.detect_locations(text)

        assert len(matches) >= 2
        locations = [match.value for match in matches]
        assert any("London" in loc for loc in locations)
        assert any("Paris" in loc for loc in locations)

    def test_location_match_attributes(self, detector):
        """Test that location matches have correct attributes."""
        text = "Visit California soon."
        matches = detector.detect_locations(text)

        assert len(matches) >= 1
        match = matches[0]

        assert match.entity_type == "location"
        assert isinstance(match.value, str)
        assert match.confidence > 0

    def test_no_location_in_text(self, detector):
        """Test that no false positives occur."""
        text = "The quick brown fox jumps over the lazy dog."
        matches = detector.detect_locations(text)

        # Should not detect any locations
        assert len(matches) == 0


@requires_spacy
class TestOrganizationDetection:
    """Test organization detection functionality."""

    @pytest.fixture
    def detector(self):
        return NERDetector()

    def test_detect_company_name(self, detector):
        """Test detection of company names."""
        text = "I work at Microsoft Corporation."
        matches = detector.detect_organizations(text)

        assert len(matches) >= 1
        assert any("Microsoft" in match.value for match in matches)

    def test_detect_multiple_organizations(self, detector):
        """Test detection of multiple organizations."""
        text = "Apple and Google are competing companies."
        matches = detector.detect_organizations(text)

        assert len(matches) >= 2
        orgs = [match.value for match in matches]
        assert any("Apple" in org for org in orgs)
        assert any("Google" in org for org in orgs)

    def test_organization_match_attributes(self, detector):
        """Test that organization matches have correct attributes."""
        text = "Amazon is hiring."
        matches = detector.detect_organizations(text)

        assert len(matches) >= 1
        match = matches[0]

        assert match.entity_type == "organization"
        assert isinstance(match.value, str)
        assert match.confidence > 0

    def test_no_organization_in_text(self, detector):
        """Test that no false positives occur."""
        text = "The quick brown fox jumps over the lazy dog."
        matches = detector.detect_organizations(text)

        # Should not detect any organizations
        assert len(matches) == 0


@requires_spacy
class TestDetectAll:
    """Test combined detection of all entity types."""

    @pytest.fixture
    def detector(self):
        return NERDetector()

    def test_detect_mixed_entity_types(self, detector):
        """Test detection of multiple entity types in one text."""
        text = "John Smith from Microsoft visited New York last week."
        matches = detector.detect_all(text)

        # Should detect person, organization, and location
        assert len(matches) >= 3

        entity_types = [m.entity_type for m in matches]
        assert "person" in entity_types
        assert "organization" in entity_types
        assert "location" in entity_types

    def test_detect_all_returns_sorted_by_position(self, detector):
        """Test that results are sorted by position in text."""
        text = "Microsoft hired John Smith."
        matches = detector.detect_all(text)

        # Microsoft should come before John Smith based on position
        if len(matches) >= 2:
            assert matches[0].start < matches[1].start

    def test_detect_in_value_simple(self, detector):
        """Test simplified detect_in_value interface."""
        value = "John Smith"
        entity_types = detector.detect_in_value(value)

        assert "person" in entity_types

    def test_detect_in_value_multiple_types(self, detector):
        """Test detect_in_value with multiple entity types."""
        value = "John Smith works at Microsoft in Seattle"
        entity_types = detector.detect_in_value(value)

        assert "person" in entity_types
        assert "organization" in entity_types or "location" in entity_types

    def test_detect_in_value_no_entities(self, detector):
        """Test detect_in_value with no entities."""
        value = "The quick brown fox"
        entity_types = detector.detect_in_value(value)

        assert len(entity_types) == 0

    def test_detect_in_value_handles_non_string(self, detector):
        """Test that detect_in_value handles non-string input."""
        value = 12345
        entity_types = detector.detect_in_value(value)

        # Should convert to string and detect
        assert isinstance(entity_types, list)


@requires_spacy
class TestNERDetectorUtility:
    """Test utility functions of NER detector."""

    @pytest.fixture
    def detector(self):
        return NERDetector()

    def test_lazy_loading(self, detector):
        """Test that spaCy model is lazy-loaded."""
        # Model should not be loaded initially
        assert detector._nlp is None

        # After first use, model should be loaded
        detector.detect_persons("Test text")
        assert detector._nlp is not None

    def test_get_available_entity_types(self, detector):
        """Test retrieval of available entity types."""
        entity_types = detector.get_available_entity_types()

        assert "person" in entity_types
        assert "location" in entity_types
        assert "organization" in entity_types
        assert len(entity_types) == 3

    def test_confidence_calculation(self, detector):
        """Test that confidence scores are reasonable."""
        text = "John Smith works at Microsoft in New York."
        matches = detector.detect_all(text)

        for match in matches:
            assert 0 < match.confidence <= 1.0
            # Most confidence scores should be relatively high for clear entities
            assert match.confidence >= 0.7


@requires_spacy
class TestErrorHandling:
    """Test error handling in NER detector."""

    def test_missing_spacy_model_raises_error(self):
        """Test that missing spaCy model raises appropriate error."""
        detector = NERDetector(model_name="nonexistent_model")

        with pytest.raises(RuntimeError) as exc_info:
            detector.detect_persons("Test text")

        assert "not found" in str(exc_info.value)
        assert "spacy download" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
