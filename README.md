# strava-to-obsidian

Export your Strava activities via the official API and store them as Obsidian-flavored Markdown files.

## Overview

A Python CLI tool that:

- **Exports Strava activities** using the official Strava API (not HTML scraping)
- **Creates Obsidian-compatible Markdown files** with YAML frontmatter
- **Downloads activity photos** into an organized `media/` folder
- **Supports incremental sync** to keep your local archive up-to-date

## Quick Start

```bash
# Authenticate with Strava
strava-to-obsidian auth

# Export last 30 days of activities
strava-to-obsidian export --days 30

# Sync new activities
strava-to-obsidian sync
```

## Features

- ✅ OAuth 2.0 authentication with automatic token refresh
- ✅ Activity metrics: distance, duration, pace, heart rate, elevation, calories
- ✅ Sport-specific icons (🏃 🚴 🏊 🥾 and more)
- ✅ Primary photo download
- ✅ Obsidian-friendly YAML frontmatter with both metric and imperial units
- ✅ Incremental sync support
- ✅ Rate limit handling with automatic retry
- ✅ Date range filtering for historical exports

## Output Structure

```
activities/
├── 2025-11-29-morning-run.md
├── 2025-11-28-evening-ride.md
└── media/
    ├── 12345678901_photo.jpg
    └── ...
```

## Requirements

- Python 3.9+
- Strava account with [API application credentials](https://www.strava.com/settings/api)

## Documentation

📋 **[Software Requirements Document](REQUIREMENTS.md)** — Full technical specification including API integration, data model, file formats, and configuration options.

## Known Limitations

Due to Strava API restrictions:
- Only the **primary photo** per activity is accessible (not all photos)
- **Videos are not available** via the API
- Rate limits: 100 requests/15 min, 1,000/day (large historical exports may require multiple runs)

## License

MIT
