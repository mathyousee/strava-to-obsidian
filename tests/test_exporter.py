"""Tests for the Strava to Obsidian exporter."""

from datetime import datetime

import pytest

from strava_to_obsidian.models import Activity, format_duration, format_pace, get_sport_icon
from strava_to_obsidian.exporter import generate_frontmatter, generate_markdown


class TestModels:
    """Tests for data models."""

    def test_format_duration_short(self):
        """Test duration formatting under 1 hour."""
        assert format_duration(90) == "1:30"
        assert format_duration(3599) == "59:59"

    def test_format_duration_long(self):
        """Test duration formatting over 1 hour."""
        assert format_duration(3600) == "1:00:00"
        assert format_duration(3661) == "1:01:01"
        assert format_duration(7325) == "2:02:05"

    def test_format_pace(self):
        """Test pace formatting."""
        assert format_pace(300) == "5:00"
        assert format_pace(330) == "5:30"
        assert format_pace(0) == "—"

    def test_get_sport_icon(self):
        """Test sport type icon mapping."""
        assert get_sport_icon("Run") == "🏃"
        assert get_sport_icon("Ride") == "🚴"
        assert get_sport_icon("Swim") == "🏊"
        assert get_sport_icon("UnknownSport") == "🏅"

    def test_activity_from_api_response(self):
        """Test creating Activity from API response."""
        data = {
            "id": 12345678901,
            "name": "Morning Run",
            "sport_type": "Run",
            "start_date_local": "2025-11-29T07:30:00Z",
            "elapsed_time": 1845,
            "moving_time": 1800,
            "distance": 5000.0,
            "average_speed": 2.78,
            "max_speed": 3.5,
            "total_elevation_gain": 45.0,
            "average_heartrate": 145.0,
            "max_heartrate": 165,
            "calories": 320.0,
            "start_latlng": [47.6062, -122.3321],
        }

        activity = Activity.from_api_response(data)

        assert activity.id == 12345678901
        assert activity.name == "Morning Run"
        assert activity.sport_type == "Run"
        assert activity.distance == 5000.0
        assert activity.distance_km == 5.0
        assert abs(activity.distance_mi - 3.107) < 0.01
        assert activity.icon == "🏃"
        assert activity.is_run_or_walk() is True

    def test_activity_filename_generation(self):
        """Test filename generation."""
        activity = Activity(
            id=12345678901,
            name="Morning Run",
            sport_type="Run",
            start_date_local=datetime(2025, 11, 29, 7, 30, 0),
        )

        filename = activity.generate_filename()
        assert filename == "2025-11-29-morning-run-12345678901.md"

    def test_activity_filename_special_chars(self):
        """Test filename generation with special characters."""
        activity = Activity(
            id=12345678901,
            name="🏃 5K Race!!!",
            sport_type="Run",
            start_date_local=datetime(2025, 11, 29, 7, 30, 0),
        )

        filename = activity.generate_filename()
        assert filename == "2025-11-29-5k-race-12345678901.md"


class TestExporter:
    """Tests for the exporter."""

    @pytest.fixture
    def sample_activity(self):
        """Create a sample activity for testing."""
        return Activity(
            id=12345678901,
            name="Morning Run",
            sport_type="Run",
            start_date_local=datetime(2025, 11, 29, 7, 30, 0),
            description="Easy recovery run",
            elapsed_time=1845,
            moving_time=1800,
            distance=5000.0,
            average_speed=2.78,
            max_speed=3.5,
            total_elevation_gain=45.0,
            average_heartrate=145.0,
            max_heartrate=165,
            calories=320.0,
            start_latlng=[47.6062, -122.3321],
        )

    def test_generate_frontmatter(self, sample_activity):
        """Test frontmatter generation."""
        frontmatter = generate_frontmatter(sample_activity)

        assert "---" in frontmatter
        assert "strava_id: 12345678901" in frontmatter
        assert "sport_type: Run" in frontmatter
        assert "icon: 🏃" in frontmatter
        assert "distance_km: 5.00" in frontmatter
        assert "average_heartrate: 145" in frontmatter
        assert "tags:" in frontmatter
        assert "- activity" in frontmatter
        assert "- run" in frontmatter

    def test_generate_markdown(self, sample_activity):
        """Test full markdown generation."""
        markdown = generate_markdown(sample_activity)

        # Check structure
        assert markdown.startswith("---")
        assert "# 🏃 Morning Run" in markdown
        assert "## Summary" in markdown
        assert "| Distance |" in markdown
        assert "## Description" in markdown
        assert "Easy recovery run" in markdown
        assert "strava.com/activities/12345678901" in markdown

    def test_generate_markdown_without_optional_fields(self):
        """Test markdown generation without optional fields."""
        activity = Activity(
            id=12345678901,
            name="Quick Walk",
            sport_type="Walk",
            start_date_local=datetime(2025, 11, 29, 12, 0, 0),
            elapsed_time=600,
            moving_time=600,
            distance=1000.0,
            average_speed=1.67,
        )

        markdown = generate_markdown(activity)

        assert "# 🚶 Quick Walk" in markdown
        assert "Heart Rate" not in markdown  # No HR data
        assert "Calories" not in markdown  # No calories
        assert "Description" not in markdown  # No description
