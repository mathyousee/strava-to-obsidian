"""Export activities to Obsidian Markdown files."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from strava_to_obsidian.models import Activity, format_pace


def generate_frontmatter(activity: Activity) -> str:
    """Generate YAML frontmatter for an activity."""
    lines = [
        "---",
        f"strava_id: {activity.id}",
        f'date: {activity.start_date_local.strftime("%Y-%m-%dT%H:%M:%S")}',
        f'name: "{activity.name}"',
        f"sport_type: {activity.sport_type}",
        f"icon: {activity.icon}",
    ]

    # Description (if present)
    if activity.description:
        # Escape quotes in description
        desc = activity.description.replace('"', '\\"').replace("\n", " ")
        lines.append(f'description: "{desc}"')

    # Time metrics
    lines.extend([
        f"elapsed_time: {activity.elapsed_time}",
        f'elapsed_time_fmt: "{activity.elapsed_time_fmt}"',
        f"moving_time: {activity.moving_time}",
        f'moving_time_fmt: "{activity.moving_time_fmt}"',
    ])

    # Distance
    lines.extend([
        f"distance_m: {activity.distance:.1f}",
        f"distance_km: {activity.distance_km:.2f}",
        f"distance_mi: {activity.distance_mi:.2f}",
    ])

    # Speed
    lines.extend([
        f"average_speed_ms: {activity.average_speed:.2f}",
        f"speed_kph: {activity.speed_kph:.1f}",
        f"speed_mph: {activity.speed_mph:.1f}",
    ])

    # Pace (for run/walk activities)
    if activity.is_run_or_walk() and activity.pace_per_km:
        lines.extend([
            f"pace_per_km: {activity.pace_per_km:.1f}",
            f"pace_per_mi: {activity.pace_per_mi:.1f}",
        ])

    # Max speed (if available)
    if activity.max_speed:
        lines.append(f"max_speed_ms: {activity.max_speed:.2f}")

    # Elevation (if > 0)
    if activity.total_elevation_gain > 0:
        lines.extend([
            f"elevation_gain_m: {activity.total_elevation_gain:.1f}",
            f"elevation_gain_ft: {activity.elevation_gain_ft:.1f}",
        ])

    # Heart rate (if available)
    if activity.average_heartrate:
        lines.append(f"average_heartrate: {activity.average_heartrate:.0f}")
    if activity.max_heartrate:
        lines.append(f"max_heartrate: {activity.max_heartrate}")

    # Calories (if available)
    if activity.calories:
        lines.append(f"calories: {activity.calories:.0f}")

    # Location (if available)
    if activity.start_latlng and len(activity.start_latlng) == 2:
        lines.extend([
            f"start_lat: {activity.start_latlng[0]:.6f}",
            f"start_lng: {activity.start_latlng[1]:.6f}",
        ])

    # Photo (if available)
    if activity.photo_url:
        lines.append(f'photo: "[[media/{activity.id}_photo.jpg]]"')

    # Tags
    sport_tag = activity.sport_type.lower().replace(" ", "-")
    lines.extend([
        "tags:",
        "  - activity",
        f"  - {sport_tag}",
    ])

    lines.append("---")
    return "\n".join(lines)


def generate_body(activity: Activity) -> str:
    """Generate Markdown body for an activity."""
    lines = [
        f"# {activity.icon} {activity.name}",
        "",
        f"**Date:** {activity.start_date_local.strftime('%A, %B %d, %Y at %I:%M %p')}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Distance | {activity.distance_km:.2f} km ({activity.distance_mi:.2f} mi) |",
        f"| Duration | {activity.moving_time_fmt} moving / {activity.elapsed_time_fmt} elapsed |",
    ]

    # Pace or speed based on activity type
    if activity.is_run_or_walk() and activity.pace_per_km:
        pace_km = format_pace(activity.pace_per_km)
        pace_mi = format_pace(activity.pace_per_mi) if activity.pace_per_mi else "—"
        lines.append(f"| Pace | {pace_km} /km ({pace_mi} /mi) |")
    else:
        lines.append(f"| Speed | {activity.speed_kph:.1f} km/h ({activity.speed_mph:.1f} mph) |")

    # Elevation
    if activity.total_elevation_gain > 0:
        lines.append(
            f"| Elevation | ↑ {activity.total_elevation_gain:.0f} m "
            f"({activity.elevation_gain_ft:.0f} ft) |"
        )

    # Calories
    if activity.calories:
        lines.append(f"| Calories | {activity.calories:.0f} kcal |")

    # Heart rate
    if activity.average_heartrate or activity.max_heartrate:
        hr_parts = []
        if activity.average_heartrate:
            hr_parts.append(f"{activity.average_heartrate:.0f} avg")
        if activity.max_heartrate:
            hr_parts.append(f"{activity.max_heartrate} max")
        lines.append(f"| Heart Rate | {' / '.join(hr_parts)} bpm |")

    # Description
    if activity.description:
        lines.extend([
            "",
            "## Description",
            "",
            activity.description,
        ])

    # Photo
    if activity.photo_url:
        lines.extend([
            "",
            "## Photo",
            "",
            f"![[media/{activity.id}_photo.jpg]]",
        ])

    # Footer
    lines.extend([
        "",
        "---",
        f"*Exported from Strava activity [{activity.id}]({activity.strava_url})*",
    ])

    return "\n".join(lines)


def generate_markdown(activity: Activity) -> str:
    """Generate complete Markdown file content for an activity."""
    frontmatter = generate_frontmatter(activity)
    body = generate_body(activity)
    return f"{frontmatter}\n\n{body}\n"


class ActivityExporter:
    """Exports activities to Markdown files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.activities_dir = output_dir
        self.media_dir = output_dir / "media"

    def setup_directories(self) -> None:
        """Create output directories if they don't exist."""
        self.activities_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def get_activity_path(self, activity: Activity) -> Path:
        """Get the file path for an activity."""
        filename = activity.generate_filename()
        return self.activities_dir / filename

    def activity_exists(self, activity: Activity) -> bool:
        """Check if an activity file already exists."""
        return self.get_activity_path(activity).exists()

    def export_activity(
        self,
        activity: Activity,
        force: bool = False,
        download_photo: bool = True,
    ) -> Optional[Path]:
        """
        Export a single activity to Markdown.

        Args:
            activity: The activity to export
            force: Overwrite existing file if True
            download_photo: Download the primary photo if available

        Returns:
            Path to the created file, or None if skipped
        """
        filepath = self.get_activity_path(activity)

        # Skip if exists and not forcing
        if filepath.exists() and not force:
            return None

        # Ensure directories exist
        self.setup_directories()

        # Download photo if available
        if download_photo and activity.photo_url:
            self._download_photo(activity)

        # Generate and write markdown
        content = generate_markdown(activity)
        filepath.write_text(content, encoding="utf-8")

        return filepath

    def _download_photo(self, activity: Activity) -> Optional[Path]:
        """Download the primary photo for an activity."""
        if not activity.photo_url:
            return None

        import requests

        photo_path = self.media_dir / f"{activity.id}_photo.jpg"

        # Skip if already downloaded
        if photo_path.exists():
            return photo_path

        try:
            response = requests.get(activity.photo_url, timeout=30)
            response.raise_for_status()
            photo_path.write_bytes(response.content)
            return photo_path
        except requests.RequestException:
            return None
