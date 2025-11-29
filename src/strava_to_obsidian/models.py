"""Data models for Strava activities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from slugify import slugify


# Sport type to emoji mapping
SPORT_ICONS: dict[str, str] = {
    "Run": "🏃",
    "TrailRun": "🏃",
    "VirtualRun": "🏃",
    "Ride": "🚴",
    "GravelRide": "🚴",
    "MountainBikeRide": "🚵",
    "EBikeRide": "🚲",
    "EMountainBikeRide": "🚵",
    "VirtualRide": "🚴",
    "Swim": "🏊",
    "Walk": "🚶",
    "Hike": "🥾",
    "Workout": "💪",
    "WeightTraining": "🏋️",
    "Yoga": "🧘",
    "Crossfit": "🏋️",
    "Elliptical": "🏃",
    "StairStepper": "🪜",
    "Rowing": "🚣",
    "VirtualRow": "🚣",
    "Kayaking": "🛶",
    "Canoeing": "🛶",
    "AlpineSki": "⛷️",
    "BackcountrySki": "⛷️",
    "NordicSki": "🎿",
    "Snowboard": "🏂",
    "IceSkate": "⛸️",
    "Golf": "⛳",
    "Soccer": "⚽",
    "Tennis": "🎾",
    "Pickleball": "🏓",
    "RockClimbing": "🧗",
    "Surfing": "🏄",
    "Windsurf": "🏄",
    "Kitesurf": "🏄",
    "StandUpPaddling": "🏄",
    "Skateboard": "🛹",
    "InlineSkate": "🛼",
    "Sail": "⛵",
}


def get_sport_icon(sport_type: str) -> str:
    """Get emoji icon for a sport type."""
    return SPORT_ICONS.get(sport_type, "🏅")


def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_pace(seconds_per_km: float) -> str:
    """Format pace as M:SS per km."""
    if seconds_per_km <= 0:
        return "—"
    minutes = int(seconds_per_km // 60)
    secs = int(seconds_per_km % 60)
    return f"{minutes}:{secs:02d}"


def format_pace_per_mi(speed_ms: float) -> str:
    """Format pace as M:SS per mile from m/s speed."""
    if speed_ms <= 0:
        return "—"
    # Convert m/s to seconds per mile
    seconds_per_mile = 1609.344 / speed_ms
    minutes = int(seconds_per_mile // 60)
    secs = int(seconds_per_mile % 60)
    return f"{minutes}:{secs:02d}"


def meters_to_miles(meters: float) -> float:
    """Convert meters to miles."""
    return meters / 1609.344


def meters_to_feet(meters: float) -> float:
    """Convert meters to feet."""
    return meters * 3.28084


@dataclass
class Lap:
    """Represents a single lap from a Strava activity."""

    lap_index: int
    distance: float  # meters
    elapsed_time: int  # seconds
    average_speed: float  # m/s
    average_heartrate: Optional[float] = None
    total_elevation_gain: float = 0.0  # meters

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Lap":
        """Create Lap from Strava API lap object."""
        return cls(
            lap_index=data.get("lap_index", 1),
            distance=data.get("distance", 0.0),
            elapsed_time=data.get("elapsed_time", 0),
            average_speed=data.get("average_speed", 0.0),
            average_heartrate=data.get("average_heartrate"),
            total_elevation_gain=data.get("total_elevation_gain", 0.0),
        )

    @property
    def distance_mi(self) -> float:
        """Distance in miles."""
        return meters_to_miles(self.distance)

    @property
    def elapsed_time_fmt(self) -> str:
        """Formatted elapsed time."""
        return format_duration(self.elapsed_time)

    @property
    def pace_per_mi(self) -> str:
        """Pace as M:SS per mile."""
        return format_pace_per_mi(self.average_speed)

    @property
    def elevation_gain_ft(self) -> float:
        """Elevation gain in feet."""
        return meters_to_feet(self.total_elevation_gain)


@dataclass
class Activity:
    """Represents a Strava activity with all relevant data."""

    # Core fields
    id: int
    name: str
    sport_type: str
    start_date_local: datetime
    description: Optional[str] = None

    # Time metrics
    elapsed_time: int = 0  # seconds
    moving_time: int = 0  # seconds

    # Distance and speed
    distance: float = 0.0  # meters
    average_speed: float = 0.0  # m/s
    max_speed: Optional[float] = None  # m/s

    # Elevation
    total_elevation_gain: float = 0.0  # meters

    # Heart rate
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[int] = None

    # Other metrics
    calories: Optional[float] = None

    # Location
    start_latlng: Optional[list[float]] = None

    # Photo (primary only - API limitation)
    photo_url: Optional[str] = None

    # Laps
    laps: list["Lap"] = field(default_factory=list)

    # Raw data for reference
    raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Activity":
        """Create Activity from Strava API response."""
        from dateutil.parser import parse as parse_date

        # Parse start date
        start_date_str = data.get("start_date_local", data.get("start_date", ""))
        start_date = parse_date(start_date_str) if start_date_str else datetime.now()

        # Get primary photo URL if available
        photo_url = None
        photos = data.get("photos", {})
        if photos.get("count", 0) > 0:
            primary = photos.get("primary", {})
            urls = primary.get("urls", {})
            # Prefer larger sizes
            photo_url = urls.get("600") or urls.get("100")

        # Parse laps if available
        laps_data = data.get("laps", [])
        laps = [Lap.from_api_response(lap) for lap in laps_data]

        return cls(
            id=data["id"],
            name=data.get("name", "Untitled Activity"),
            sport_type=data.get("sport_type", data.get("type", "Workout")),
            start_date_local=start_date,
            description=data.get("description"),
            elapsed_time=data.get("elapsed_time", 0),
            moving_time=data.get("moving_time", 0),
            distance=data.get("distance", 0.0),
            average_speed=data.get("average_speed", 0.0),
            max_speed=data.get("max_speed"),
            total_elevation_gain=data.get("total_elevation_gain", 0.0),
            average_heartrate=data.get("average_heartrate"),
            max_heartrate=data.get("max_heartrate"),
            calories=data.get("calories"),
            start_latlng=data.get("start_latlng"),
            photo_url=photo_url,
            laps=laps,
            raw_data=data,
        )

    @property
    def icon(self) -> str:
        """Get emoji icon for this activity's sport type."""
        return get_sport_icon(self.sport_type)

    @property
    def distance_km(self) -> float:
        """Distance in kilometers."""
        return self.distance / 1000

    @property
    def distance_mi(self) -> float:
        """Distance in miles."""
        return self.distance / 1609.344

    @property
    def elapsed_time_fmt(self) -> str:
        """Formatted elapsed time."""
        return format_duration(self.elapsed_time)

    @property
    def moving_time_fmt(self) -> str:
        """Formatted moving time."""
        return format_duration(self.moving_time)

    @property
    def pace_per_km(self) -> Optional[float]:
        """Pace in seconds per km (for running activities)."""
        if self.distance_km > 0:
            return self.moving_time / self.distance_km
        return None

    @property
    def pace_per_mi(self) -> Optional[float]:
        """Pace in seconds per mile (for running activities)."""
        if self.distance_mi > 0:
            return self.moving_time / self.distance_mi
        return None

    @property
    def speed_kph(self) -> float:
        """Average speed in km/h."""
        return self.average_speed * 3.6

    @property
    def speed_mph(self) -> float:
        """Average speed in mph."""
        return self.average_speed * 2.237

    @property
    def elevation_gain_ft(self) -> float:
        """Elevation gain in feet."""
        return self.total_elevation_gain * 3.281

    @property
    def strava_url(self) -> str:
        """URL to view activity on Strava."""
        return f"https://www.strava.com/activities/{self.id}"

    def generate_filename(self) -> str:
        """Generate a filename for this activity."""
        date_str = self.start_date_local.strftime("%Y-%m-%d")
        name_slug = slugify(self.name, max_length=50)
        return f"{date_str}-{name_slug}-{self.id}.md"

    def is_run_or_walk(self) -> bool:
        """Check if this is a running or walking activity (for pace display)."""
        return self.sport_type in {
            "Run",
            "TrailRun",
            "VirtualRun",
            "Walk",
            "Hike",
        }
