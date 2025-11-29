# strava-to-obsidian

Export your Strava activities via the official API and store them as Obsidian-flavored Markdown files.

## Overview

A Python CLI tool that:

- **Exports Strava activities** using the official Strava API (not scraping)
- **Creates Obsidian-compatible Markdown files** with YAML frontmatter
- **Downloads primary activity photo** into an organized `media/` folder
- **Supports incremental sync** to keep your local archive up-to-date

## Installation

```bash
# Clone the repository
git clone https://github.com/mathyousee/strava-to-obsidian.git
cd strava-to-obsidian

# Install in development mode
pip install -e .
```

## Setup

### 1. Create a Strava API Application

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Note your **Client ID** and **Client Secret**

### 2. Configure Credentials

**Option A: Using a `.env` file (recommended)**

```bash
cp .env.example .env
# Edit .env with your credentials
```

```env
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

**Option B: Using environment variables**

```bash
export STRAVA_CLIENT_ID='your_client_id'
export STRAVA_CLIENT_SECRET='your_client_secret'
```

### 3. Authenticate

```bash
strava-to-obsidian auth
```

This opens your browser to authorize the app. Tokens are saved locally.

## Usage

```bash
# Export last 30 days of activities
strava-to-obsidian export

# Export to a specific directory
strava-to-obsidian export --output ~/ObsidianVault/activities

# Export last 90 days
strava-to-obsidian export --days 90

# Export a specific date range
strava-to-obsidian export --after 2024-01-01 --before 2024-12-31

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
- ✅ Activity metrics: distance, duration, pace, heart rate, elevation, calories
- ✅ Sport-specific icons (🏃 🚴 🏊 🥾 and 30+ more)
- ✅ Primary photo download
- ✅ Obsidian-friendly YAML frontmatter with both metric and imperial units
- ✅ Incremental sync support
- ✅ Rate limit handling with automatic retry
- ✅ Date range filtering for historical exports

## Known Limitations

Due to Strava API restrictions:
- Only the **primary photo** per activity is accessible (not all photos)
- **Videos are not available** via the API
- Rate limits: 100 requests/15 min, 1,000/day (large historical exports may require multiple runs)

## Documentation

📋 **[Requirements Document](REQUIREMENTS.md)** — Full technical specification

## Requirements

- Python 3.9+
- Strava account with [API application](https://www.strava.com/settings/api)

## License

MIT
