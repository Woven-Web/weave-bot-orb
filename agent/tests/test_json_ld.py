"""Tests for JSON-LD date override logic."""
from datetime import datetime
from agent.core.schemas import Event, EventLocation, EventOrganizer
from agent.scraper.orchestrator import ScrapingOrchestrator


class TestApplyJsonLdDates:
    def setup_method(self):
        # Access the method directly — it's a pure function on self
        self.orchestrator = ScrapingOrchestrator.__new__(ScrapingOrchestrator)

    def test_overrides_start_date(self, sample_event):
        json_ld = {"startDate": "2026-06-01T20:00:00-07:00"}
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert str(result.start_datetime) == "2026-06-01 20:00:00-07:00"

    def test_overrides_end_date(self, sample_event):
        json_ld = {"endDate": "2026-06-01T23:00:00-07:00"}
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert str(result.end_datetime) == "2026-06-01 23:00:00-07:00"

    def test_overrides_both_dates(self, sample_event):
        json_ld = {
            "startDate": "2026-06-01T20:00:00-07:00",
            "endDate": "2026-06-01T23:00:00-07:00",
        }
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert str(result.start_datetime) == "2026-06-01 20:00:00-07:00"
        assert str(result.end_datetime) == "2026-06-01 23:00:00-07:00"

    def test_cleans_milliseconds(self, sample_event):
        json_ld = {"startDate": "2026-06-01T20:00:00.000-07:00"}
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert str(result.start_datetime) == "2026-06-01 20:00:00-07:00"

    def test_adds_extraction_note(self, sample_event):
        json_ld = {"startDate": "2026-06-01T20:00:00-07:00"}
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert "JSON-LD" in result.extraction_notes

    def test_preserves_existing_notes(self):
        event = Event(
            title="Test",
            extraction_notes="Existing note.",
        )
        json_ld = {"startDate": "2026-06-01T20:00:00-07:00"}
        result = self.orchestrator._apply_json_ld_dates(event, json_ld)
        assert "Existing note." in result.extraction_notes
        assert "JSON-LD" in result.extraction_notes

    def test_no_override_without_json_ld_dates(self, sample_event):
        json_ld = {"name": "Some Event"}  # No dates
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert result.start_datetime == sample_event.start_datetime
        assert result.end_datetime == sample_event.end_datetime

    def test_preserves_non_date_fields(self, sample_event):
        json_ld = {"startDate": "2026-06-01T20:00:00-07:00"}
        result = self.orchestrator._apply_json_ld_dates(sample_event, json_ld)
        assert result.title == sample_event.title
        assert result.location.venue == sample_event.location.venue
        assert result.confidence_score == sample_event.confidence_score
