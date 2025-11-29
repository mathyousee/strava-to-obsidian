# strava-to-obsidian

Export your Strava activities via the official API and store them as Obsidian-flavored Markdown files.

## Overview

A Python CLI tool that:

- **Exports all Strava activities** using the official Strava API (not HTML scraping)
- **Creates Obsidian-compatible Markdown files** with rich YAML frontmatter
- **Downloads media** (photos, videos, map images) into an organized `/media/` folder
- **Supports incremental sync** to keep your local archive up-to-date

## Documentation

📋 **[Software Requirements Document](REQUIREMENTS.md)** - Detailed specifications for the exporter including:
- Strava API integration requirements
- Data model and activity fields
- File structure and naming conventions
- Obsidian Markdown format specification
- Media handling (photos, videos, maps)
- Configuration options
- Error handling and security considerations

## Quick Start

*(Coming soon - implementation in progress)*

```bash
# Install
pip install strava-to-obsidian

# Authenticate with Strava
strava-to-obsidian auth

# Export all activities
strava-to-obsidian export --output ~/ObsidianVault/Fitness

# Sync new activities (incremental)
strava-to-obsidian sync

# Check status
strava-to-obsidian status
```

### CLI Options

```
strava-to-obsidian export [OPTIONS]

Options:
  -o, --output PATH    Output directory (default: ./activities)
  -d, --days INTEGER   Export last N days (default: 30)
  --after YYYY-MM-DD   Export activities after this date
  --before YYYY-MM-DD  Export activities before this date
  -f, --force          Overwrite existing files
  --no-media           Skip downloading photos
  --dry-run            Preview without writing files
  -v, --verbose        Show detailed output
```

## Output Structure

```
activities/
├── 2025-11-29-morning-run.md
├── 2025-11-28-evening-ride.md
└── media/
    ├── 12345678901_photo.jpg
    └── ...
```

## Features

- ✅ OAuth 2.0 authentication with automatic token refresh
- ✅ Full activity data export with all metrics
- ✅ Map image generation from GPS data
- ✅ Photo and video downloads
- ✅ Obsidian-friendly YAML frontmatter
- ✅ Incremental sync support
- ✅ Rate limit handling
- ✅ Configurable export options

## Requirements

- Python 3.9+
- Strava account with API application credentials
- Internet connection for export

## License

*(License to be determined)*
