# Software Requirements Document
## Strava to Obsidian Activity Exporter

**Version:** 1.1  
**Last Updated:** November 2025  
**Implementation Status:** MVP Complete

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Strava API Integration](#3-strava-api-integration)
4. [Data Model](#4-data-model)
5. [File Structure and Organization](#5-file-structure-and-organization)
6. [Obsidian Markdown Format](#6-obsidian-markdown-format)
7. [Media Handling](#7-media-handling)
8. [Configuration](#8-configuration)
9. [Error Handling and Logging](#9-error-handling-and-logging)
10. [Security Requirements](#10-security-requirements)
11. [Technical Requirements](#11-technical-requirements)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Appendix](#13-appendix)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for a Python script that exports Strava activities via the official Strava API and saves them as Obsidian-compatible Markdown files with associated media assets.

### 1.2 Scope

The Strava to Obsidian Exporter will:
- Authenticate with the Strava API using OAuth 2.0
- Retrieve user activities from Strava with date range filtering
- Convert activity data to Obsidian-flavored Markdown files
- Download primary activity photos (API limitation: only primary photo accessible)
- Support incremental sync to avoid re-downloading existing activities
- Maintain a local archive that can be used with Obsidian or any Markdown-compatible tool

**Known API Limitations:**
- Only the primary photo per activity is accessible via API
- Videos are not available via the Strava API
- Rate limits: 100 requests/15 min, 1,000 requests/day

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **Strava** | A social fitness tracking platform and application |
| **Obsidian** | A knowledge management and note-taking application using Markdown files |
| **API** | Application Programming Interface |
| **OAuth 2.0** | Industry-standard authorization protocol |
| **YAML** | YAML Ain't Markup Language - a human-readable data serialization format |
| **Frontmatter** | YAML metadata block at the beginning of a Markdown file |
| **Polyline** | An encoded representation of a route or path |

### 1.4 References

- [Strava API Documentation](https://developers.strava.com/docs/reference/)
- [Strava API Authentication](https://developers.strava.com/docs/authentication/)
- [Obsidian Markdown Reference](https://help.obsidian.md/Editing+and+formatting/Obsidian+Flavored+Markdown)

### 1.5 Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| OAuth Authentication | ✅ Complete | Includes manual mode for restricted environments |
| Activity Export | ✅ Complete | Exports to Markdown with YAML frontmatter |
| Incremental Sync | ✅ Complete | Only downloads new activities |
| Primary Photo Download | ✅ Complete | Downloads cover photo per activity |
| Rate Limiting | ✅ Complete | Respects 100/15min, 1000/day limits |
| Static Map Generation | ⏳ Planned | Requires Mapbox or similar API |
| Lap Data | ⏳ Planned | Table with distance, time, pace, HR, elevation |
| Segment Efforts | ⏳ Planned | Available in API, not yet exported |
| Gear Tracking | ⏳ Planned | Available in API, not yet exported |

---

## 2. Overall Description

### 2.1 Product Perspective

This script serves as a bridge between Strava's cloud-based activity storage and a local Obsidian vault. It enables users to:
- Create a permanent local backup of their fitness activities
- Integrate activity data with personal knowledge management workflows
- Link activities with other notes, journals, or documentation in Obsidian
- Own their data in a portable, open format (Markdown)

### 2.2 User Characteristics

The target user is someone who:
- Has an active Strava account with recorded activities
- Uses Obsidian for personal knowledge management
- Has basic technical skills to run Python scripts
- Wants to archive and integrate fitness data with other notes

### 2.3 Constraints

- Must comply with Strava's API Terms of Service and rate limits
- Limited to data accessible through the authenticated user's Strava account
- Dependent on Strava API availability
- Photo/video downloads may be limited based on Strava subscription level

### 2.4 Assumptions

- User has Python 3.9+ installed
- User has registered a Strava API application
- User has write access to the target output directory
- Internet connectivity is available during export

---

## 3. Strava API Integration

### 3.1 Authentication

#### 3.1.1 OAuth 2.0 Flow

The script SHALL implement the Strava OAuth 2.0 authorization flow:

1. **Initial Authorization**
   - Direct user to Strava authorization URL
   - Request required scopes: `read`, `activity:read_all`
   - Handle authorization callback with authorization code
   - Exchange authorization code for access and refresh tokens

2. **Token Management**
   - Store tokens securely in a local configuration file
   - Automatically refresh expired access tokens using the refresh token
   - Handle token refresh failures gracefully

#### 3.1.2 Required API Scopes

| Scope | Purpose |
|-------|---------|
| `read` | Read public profile and public activities |
| `activity:read_all` | Read all activities including private ones |
| `read_all` | (Optional) Read all private data including zones |

#### 3.1.3 Rate Limiting

The script SHALL respect Strava API rate limits:
- **15-minute limit:** 100 requests per 15 minutes
- **Daily limit:** 1,000 requests per day

Implementation requirements:
- Track API request count
- Implement exponential backoff on 429 (Rate Limit Exceeded) responses
- Display rate limit status to user
- Support resumable exports to handle rate limit interruptions

### 3.2 API Endpoints

The script SHALL use the following Strava API v3 endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/athlete` | GET | Retrieve authenticated athlete profile |
| `/athlete/activities` | GET | List all athlete activities (paginated) |
| `/activities/{id}` | GET | Get detailed activity information |
| `/activities/{id}/streams` | GET | Get activity stream data (GPS, heart rate, etc.) |
| `/activities/{id}/photos` | GET | Get photos associated with activity |
| `/activities/{id}/laps` | GET | Get lap data for activity |
| `/routes/{id}` | GET | Get route details if activity follows a route |

### 3.3 Pagination

For list endpoints, the script SHALL:
- Use pagination parameters (`page`, `per_page`)
- Set `per_page` to maximum allowed value (200 for activities)
- Continue fetching until all activities are retrieved
- Support resumable pagination in case of interruption

---

## 4. Data Model

### 4.1 Activity Data Fields

The script SHALL extract and store the following activity data:

#### 4.1.1 Core Activity Information

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `id` | Integer | Unique Strava activity identifier | Yes |
| `name` | String | User-defined activity name | Yes |
| `type` | String | Activity type (Run, Ride, Swim, etc.) | Yes |
| `sport_type` | String | Detailed sport type | Yes |
| `start_date` | DateTime | Activity start time (UTC) | Yes |
| `start_date_local` | DateTime | Activity start time (local timezone) | Yes |
| `timezone` | String | Timezone of activity | Yes |
| `description` | String | User-provided description | No |
| `private` | Boolean | Whether activity is private | Yes |
| `commute` | Boolean | Whether marked as commute | No |
| `trainer` | Boolean | Whether performed on trainer | No |
| `manual` | Boolean | Whether manually entered | No |

#### 4.1.2 Performance Metrics

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `distance` | Float | meters | Total distance |
| `moving_time` | Integer | seconds | Time spent moving |
| `elapsed_time` | Integer | seconds | Total elapsed time |
| `total_elevation_gain` | Float | meters | Total elevation climbed |
| `elev_high` | Float | meters | Highest elevation point |
| `elev_low` | Float | meters | Lowest elevation point |
| `average_speed` | Float | m/s | Average speed |
| `max_speed` | Float | m/s | Maximum speed |
| `average_cadence` | Float | rpm | Average cadence |
| `average_heartrate` | Float | bpm | Average heart rate |
| `max_heartrate` | Float | bpm | Maximum heart rate |
| `average_watts` | Float | watts | Average power |
| `max_watts` | Float | watts | Maximum power |
| `weighted_average_watts` | Float | watts | Normalized power |
| `kilojoules` | Float | kJ | Total energy output |
| `calories` | Float | kcal | Estimated calories burned |
| `suffer_score` | Integer | - | Strava Relative Effort score |

#### 4.1.3 Location Data

| Field | Type | Description |
|-------|------|-------------|
| `start_latlng` | [Float, Float] | Starting coordinates [lat, lng] |
| `end_latlng` | [Float, Float] | Ending coordinates [lat, lng] |
| `map.summary_polyline` | String | Encoded polyline of route |
| `map.polyline` | String | Detailed encoded polyline |

#### 4.1.4 Equipment and Gear

| Field | Type | Description |
|-------|------|-------------|
| `gear_id` | String | Strava gear identifier |
| `gear.name` | String | Name of gear used |
| `gear.primary` | Boolean | Whether this is primary gear |
| `gear.distance` | Float | Total distance on gear |

#### 4.1.5 Segments and Achievements

| Field | Type | Description |
|-------|------|-------------|
| `segment_efforts` | Array | List of segment efforts |
| `best_efforts` | Array | Personal records achieved |
| `achievement_count` | Integer | Number of achievements |
| `kudos_count` | Integer | Number of kudos received |
| `comment_count` | Integer | Number of comments |
| `pr_count` | Integer | Number of PRs achieved |

#### 4.1.6 Lap Data

Lap data is included in the activity detail response. Fields used for export:

| Field | Type | Description | Used In |
|-------|------|-------------|----------|
| `laps` | Array | Array of lap objects | - |
| `lap.lap_index` | Integer | Lap number (1-based) | Lap column |
| `lap.distance` | Float | Lap distance (meters) | Distance column (converted to mi) |
| `lap.elapsed_time` | Integer | Lap elapsed time (seconds) | Time column |
| `lap.average_speed` | Float | Average speed (m/s) | Pace column (converted to min/mi) |
| `lap.average_heartrate` | Float | Lap average heart rate | Avg HR column |
| `lap.total_elevation_gain` | Float | Elevation gain (meters) | Elev column (converted to ft) |

### 4.2 Athlete Data

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Athlete ID |
| `firstname` | String | First name |
| `lastname` | String | Last name |
| `profile` | String | Profile photo URL |
| `measurement_preference` | String | "feet" or "meters" |

---

## 5. File Structure and Organization

### 5.1 Directory Structure

The script creates the following directory structure:

```
<output_directory>/               # e.g., ./activities
├── 2025-11-15-morning-run-16468414097.md
├── 2025-11-16-evening-ride-16478523456.md
├── ...
└── media/
    ├── 16468414097_photo.jpg     # Primary photo per activity
    ├── 16478523456_photo.jpg
    └── ...
```

**Token Storage (separate location):**
```
.strava_tokens.json              # OAuth tokens (chmod 600)
```

### 5.2 File Naming Conventions

#### 5.2.1 Activity Files

Activity Markdown files SHALL be named using the pattern:
```
YYYY-MM-DD-<slugified-activity-name>-<strava_id>.md
```

**Examples:**
- `2025-11-15-taco-trot-25k-16468414097.md`
- `2025-11-28-morning-run-16593713184.md`

Slugification rules:
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters (keep alphanumeric and hyphens)
- Truncate name to 50 characters max
- Always append Strava activity ID for uniqueness

#### 5.2.2 Media Files

**Photos:**
```
<activity_id>_photo.jpg
```

**Note:** Due to Strava API limitations, only the primary (cover) photo is accessible per activity.

**Map Images (Future):**
```
<activity_id>_map.png
```

### 5.3 Index and State Files

#### 5.3.1 Activity Index (`activity_index.json`)

```json
{
  "version": "1.0",
  "last_updated": "2025-01-15T10:30:00Z",
  "activities": [
    {
      "strava_id": 12345678901,
      "file_path": "activities/2024/2024-01/2024-01-15_Morning_Run.md",
      "media_files": [
        "media/maps/12345678901_map.png",
        "media/photos/12345678901/001_photo.jpg"
      ],
      "exported_at": "2025-01-15T10:25:00Z",
      "strava_updated_at": "2024-01-15T08:00:00Z"
    }
  ]
}
```

#### 5.3.2 Export State (`state.json`)

```json
{
  "version": "1.0",
  "last_full_sync": "2025-01-15T10:30:00Z",
  "last_activity_date": "2025-01-14T07:30:00Z",
  "total_activities_exported": 523,
  "total_media_files": 1247,
  "sync_status": "completed"
}
```

---

## 6. Obsidian Markdown Format

### 6.1 Frontmatter Structure

Each activity Markdown file includes YAML frontmatter with activity metadata. The current MVP implementation uses this structure:

```yaml
---
# Core Identification
id: 12345678901
strava_url: "https://www.strava.com/activities/12345678901"
name: "Morning Run"
date: 2024-01-15
start_date_local: "2024-01-15T07:30:00"

# Activity Classification
sport_type: Run
icon: 🏃

# Performance Metrics
elapsed_time: 3150
moving_time: 3015
distance: 10500.0
total_elevation_gain: 125.0
average_speed: 3.48
max_speed: 4.52
calories: 650

# Heart Rate (if available)
average_heartrate: 152
max_heartrate: 175

# Location (as YAML array)
coordinates:
  - 40.7128
  - -74.0060

# Media (primary photo only, if available)
photo: "[[media/12345678901_photo.jpg]]"

# Tags for Obsidian
tags:
  - strava
  - run
---
```

**Notes on Implementation:**
- `coordinates` is stored as a YAML array `[lat, lng]` for Obsidian Leaflet compatibility
- `photo` uses Obsidian wikilink syntax for embedding
- Times are stored in seconds (raw API values) for easy processing
- Only fields with values are included (nulls are omitted)

### 6.2 Markdown Body Structure

The body of each activity file follows this template:

```markdown
# Morning Run

**Run** · Mon, Jan 15, 2024 · 6.52 mi in 52:30

## Description

User's activity description appears here if provided.

## Photo

![[media/12345678901_photo.jpg]]

## Laps

| Lap | Distance | Time | Pace | Avg HR | Elev |
|-----|----------|------|------|--------|------|
| 1 | 1.00 mi | 8:05 | 8:05/mi | 145 | +42 ft |
| 2 | 1.00 mi | 7:58 | 7:58/mi | 150 | +38 ft |
| 3 | 1.00 mi | 7:52 | 7:52/mi | 154 | +25 ft |
| 4 | 1.00 mi | 8:10 | 8:10/mi | 152 | +18 ft |
| 5 | 1.00 mi | 7:45 | 7:45/mi | 158 | +12 ft |
| 6 | 1.00 mi | 7:40 | 7:40/mi | 162 | +15 ft |
| 7 | 0.52 mi | 4:00 | 7:41/mi | 165 | +10 ft |
```

**Notes:**
- Lap table only included for activities with lap data
- Distance displayed in miles
- Pace calculated as time / distance
- Avg HR omitted if heart rate data unavailable
- Elevation shown as gain per lap (+ prefix)

### 6.3 Future Enhancements

The following sections may be added in future versions:

#### Segments (Planned)
```markdown
## Segments

### Segment Name
- **Time:** 2:45
- **Rank:** 15 / 1,234
```

#### Best Efforts (Planned)
```markdown
## Best Efforts

| Effort | Time |
|--------|------|
| 1 mile | 7:25 |
| 5K | 24:15 |
```

### 6.3 Activity Type Icons

The script uses appropriate icons for different activity types:

| Activity Type | Icon |
|---------------|------|
| Run | 🏃 |
| Ride | 🚴 |
| Swim | 🏊 |
| Walk | 🚶 |
| Hike | 🥾 |
| Alpine Ski | ⛷️ |
| Nordic Ski | 🎿 |
| Snowboard | 🏂 |
| Weight Training | 🏋️ |
| Yoga | 🧘 |
| Workout | 💪 |
| Rock Climbing | 🧗 |
| Rowing | 🚣 |
| Kayaking | 🛶 |
| Golf | ⛳ |
| Soccer | ⚽ |
| Tennis | 🎾 |
| Other | 🏅 |

### 6.4 Unit Formatting

The script SHALL support both metric and imperial units:

#### 6.4.1 Distance
- Display both km and miles in summary
- Use user's Strava preference as primary

#### 6.4.2 Pace/Speed
- Running activities: pace (min/km or min/mi)
- Cycling activities: speed (km/h or mph)

#### 6.4.3 Elevation
- Display both meters and feet

#### 6.4.4 Time Formatting
- Duration: `HH:MM:SS` or `MM:SS` for activities under 1 hour
- Pace: `M:SS` format

---

## 7. Media Handling

### 7.1 API Limitations (Important)

**The Strava API has significant limitations for media access:**

| Media Type | API Support | Implementation |
|------------|-------------|----------------|
| Primary Photo | ✅ Available | Downloaded via activity detail endpoint |
| Additional Photos | ❌ No API access | Not implemented |
| Videos | ❌ No API access | Not implemented |
| Route Polyline | ✅ Available | Stored in activity data |
| Static Maps | ⚠️ Requires external API | Future enhancement |

### 7.2 Photo Handling (Current Implementation)

The script downloads the **primary photo only** for each activity:

1. **Source:** `activity.photos.primary.urls` from activity detail endpoint
2. **Size Selection:** Largest available (typically 600px)
3. **Storage:** `media/<activity_id>_photo.jpg`
4. **Embedding:** Obsidian wikilink format `![[media/<id>_photo.jpg]]`

**Code Flow:**
```python
# From activity detail response
if activity.get("photos", {}).get("primary"):
    photo_url = activity["photos"]["primary"]["urls"].get("600")
    # Download and save to media folder
```

### 7.3 Map Generation (Future Enhancement)

Map generation is planned but not yet implemented. Options include:

**Option 1: Mapbox Static Images API**
- Requires Mapbox access token
- Uses encoded polyline from activity

**Option 2: Leaflet in Obsidian**
- Use Obsidian Leaflet plugin with stored coordinates
- No additional API required

#### 7.4.2 Progressive Download

- Support resumable downloads for large files
- Implement retry logic for failed downloads
- Track download progress for large media sets

---

## 8. Configuration

### 8.1 Configuration File

The script SHALL use a JSON configuration file:

#### 8.1.1 Configuration File Location

Default locations (in order of precedence):
1. `--config` command line argument
2. `./strava-export-config.json`
3. `~/.config/strava-to-obsidian/config.json`

#### 8.1.2 Configuration Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "strava": {
      "type": "object",
      "properties": {
        "client_id": {
          "type": "string",
          "description": "Strava API application client ID"
        },
        "client_secret": {
          "type": "string",
          "description": "Strava API application client secret"
        },
        "access_token": {
          "type": "string",
          "description": "Current access token (auto-managed)"
        },
        "refresh_token": {
          "type": "string",
          "description": "Refresh token for token renewal"
        },
        "token_expires_at": {
          "type": "integer",
          "description": "Token expiration timestamp"
        }
      },
      "required": ["client_id", "client_secret"]
    },
    "output": {
      "type": "object",
      "properties": {
        "base_directory": {
          "type": "string",
          "description": "Root directory for exported files",
          "default": "./strava-export"
        },
        "activities_folder": {
          "type": "string",
          "description": "Subdirectory for activity files",
          "default": "activities"
        },
        "media_folder": {
          "type": "string",
          "description": "Subdirectory for media files",
          "default": "media"
        },
        "organize_by_year": {
          "type": "boolean",
          "description": "Create year/month subdirectories",
          "default": true
        },
        "organize_by_month": {
          "type": "boolean",
          "description": "Create month subdirectories within years",
          "default": true
        }
      }
    },
    "export": {
      "type": "object",
      "properties": {
        "include_private": {
          "type": "boolean",
          "description": "Export private activities",
          "default": true
        },
        "include_manual": {
          "type": "boolean",
          "description": "Export manually entered activities",
          "default": true
        },
        "activity_types": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Activity types to export (empty = all)",
          "default": []
        },
        "date_range": {
          "type": "object",
          "properties": {
            "after": {
              "type": "string",
              "format": "date",
              "description": "Only export activities after this date"
            },
            "before": {
              "type": "string",
              "format": "date",
              "description": "Only export activities before this date"
            }
          }
        },
        "include_raw_data": {
          "type": "boolean",
          "description": "Include raw JSON in markdown",
          "default": true
        }
      }
    },
    "media": {
      "type": "object",
      "properties": {
        "download_photos": {
          "type": "boolean",
          "description": "Download activity photos",
          "default": true
        },
        "download_videos": {
          "type": "boolean",
          "description": "Download activity videos",
          "default": true
        },
        "generate_maps": {
          "type": "boolean",
          "description": "Generate map images",
          "default": true
        },
        "map_provider": {
          "type": "string",
          "enum": ["mapbox", "osm", "google"],
          "description": "Map tile provider",
          "default": "osm"
        },
        "map_style": {
          "type": "string",
          "description": "Map style identifier",
          "default": "streets"
        },
        "map_width": {
          "type": "integer",
          "description": "Map image width in pixels",
          "default": 800
        },
        "map_height": {
          "type": "integer",
          "description": "Map image height in pixels",
          "default": 600
        },
        "photo_size": {
          "type": "string",
          "enum": ["original", "large", "medium", "thumbnail"],
          "description": "Photo size to download",
          "default": "large"
        }
      }
    },
    "formatting": {
      "type": "object",
      "properties": {
        "units": {
          "type": "string",
          "enum": ["metric", "imperial", "both"],
          "description": "Unit system for display",
          "default": "both"
        },
        "date_format": {
          "type": "string",
          "description": "Date format string",
          "default": "%Y-%m-%d"
        },
        "time_format": {
          "type": "string",
          "description": "Time format string",
          "default": "%H:%M"
        },
        "include_tags": {
          "type": "boolean",
          "description": "Add Obsidian tags to frontmatter",
          "default": true
        },
        "custom_tags": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Additional tags to add to all activities",
          "default": ["strava"]
        }
      }
    },
    "sync": {
      "type": "object",
      "properties": {
        "mode": {
          "type": "string",
          "enum": ["full", "incremental", "update"],
          "description": "Sync mode",
          "default": "incremental"
        },
        "update_existing": {
          "type": "boolean",
          "description": "Update existing activity files",
          "default": false
        },
        "delete_removed": {
          "type": "boolean",
          "description": "Delete files for removed activities",
          "default": false
        }
      }
    },
    "api_keys": {
      "type": "object",
      "properties": {
        "mapbox_token": {
          "type": "string",
          "description": "Mapbox API token (if using Mapbox maps)"
        },
        "google_maps_key": {
          "type": "string",
          "description": "Google Maps API key (if using Google maps)"
        }
      }
    }
  }
}
```

### 8.2 Command Line Interface

The script supports the following commands:

```
strava-to-obsidian [OPTIONS] COMMAND

Commands:
  auth          Authenticate with Strava OAuth
  export        Export activities to Markdown
  sync          Sync new activities (incremental)
  status        Show authentication and export status

Auth Options:
  --manual              Use manual code entry (for environments without localhost)

Export/Sync Options:
  --output, -o PATH     Output directory (default: ./activities)
  --days N              Number of days to look back (default: 30)

Global Options:
  --help, -h            Show help message
  --version             Show version
```

**Example Usage:**

```bash
# Initial authentication (standard)
strava-to-obsidian auth

# Authentication in restricted environments (codespaces, remote)
strava-to-obsidian auth --manual

# Export last 30 days
strava-to-obsidian export --output ./activities

# Export last 90 days
strava-to-obsidian export --output ./activities --days 90

# Incremental sync (new activities only)
strava-to-obsidian sync --output ./activities

# Check status
strava-to-obsidian status
```

### 8.3 Environment Variables

The script reads credentials from a `.env` file (via python-dotenv):

```bash
# .env file
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

| Variable | Description | Required |
|----------|-------------|----------|
| `STRAVA_CLIENT_ID` | Strava API client ID | Yes |
| `STRAVA_CLIENT_SECRET` | Strava API client secret | Yes |

---

## 9. Error Handling and Logging

### 9.1 Error Categories

#### 9.1.1 Authentication Errors

| Error | Handling |
|-------|----------|
| Invalid credentials | Prompt user to re-authenticate |
| Expired token | Automatic refresh using refresh token |
| Refresh token expired | Prompt for full re-authentication |
| Invalid scope | Request required permissions |

#### 9.1.2 API Errors

| Error | Handling |
|-------|----------|
| 400 Bad Request | Log error, skip activity, continue |
| 401 Unauthorized | Attempt token refresh, then re-auth |
| 403 Forbidden | Log error, check permissions |
| 404 Not Found | Log warning, skip resource |
| 429 Rate Limited | Exponential backoff, resume later |
| 500+ Server Error | Retry with backoff, max 3 attempts |

#### 9.1.3 File System Errors

| Error | Handling |
|-------|----------|
| Permission denied | Log error, prompt user |
| Disk full | Log error, stop export |
| Invalid path | Sanitize path, retry |
| File exists | Based on config (skip/overwrite) |

#### 9.1.4 Network Errors

| Error | Handling |
|-------|----------|
| Connection timeout | Retry with exponential backoff |
| DNS resolution failure | Log error, check network |
| SSL/TLS error | Log error, check certificates |

### 9.2 Logging

#### 9.2.1 Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging information |
| INFO | General operational messages |
| WARNING | Non-critical issues |
| ERROR | Errors that prevent specific operations |
| CRITICAL | Errors that prevent script execution |

#### 9.2.2 Log Format

```
[TIMESTAMP] [LEVEL] [MODULE] Message
```

Example:
```
[2025-01-15T10:30:00Z] [INFO] [export] Starting export of 523 activities
[2025-01-15T10:30:01Z] [DEBUG] [api] GET /athlete/activities?page=1&per_page=200
[2025-01-15T10:30:02Z] [INFO] [export] Exported activity 12345678901: Morning Run
[2025-01-15T10:30:05Z] [WARNING] [media] Photo download failed for activity 12345678902, retrying...
[2025-01-15T10:30:10Z] [ERROR] [api] Rate limit exceeded, waiting 900 seconds
```

#### 9.2.3 Log Output

- Console output (configurable verbosity)
- Log file: `<output_directory>/.strava-export/export.log`
- Support log rotation (keep last 5 log files, max 10MB each)

### 9.3 Progress Reporting

The script SHALL provide progress feedback:

```
Strava to Obsidian Export
=========================

Authenticating... ✓
Fetching activity list... 523 activities found

Exporting activities:
[████████████████████░░░░░░░░░░░░░░░░░] 230/523 (44%)
Current: Morning Run (2024-01-15)
Downloading media: map ✓ photos (2/3)

Rate limit: 45/100 requests (15 min) | 234/1000 (daily)
ETA: 15 minutes
```

---

## 10. Security Requirements

### 10.1 Token Security

#### 10.1.1 Token Storage

- Store tokens in configuration file with restricted permissions (600)
- Do NOT log access tokens
- Support encryption for stored credentials (optional)

#### 10.1.2 Token Handling

- Transmit tokens only over HTTPS
- Clear tokens from memory after use
- Validate token format before use

### 10.2 Input Validation

- Sanitize activity names for file system safety
- Validate URLs before downloading
- Verify file paths are within output directory

### 10.3 API Security

- Use HTTPS for all API communications
- Validate SSL certificates
- Do not disable certificate verification

### 10.4 Data Privacy

- Support excluding private activities
- Do not expose personal data in logs
- Provide option to anonymize location data

---

## 11. Technical Requirements

### 11.1 Python Version

- **Minimum:** Python 3.9
- **Recommended:** Python 3.11+

### 11.2 Dependencies

#### 11.2.1 Required Dependencies (Current Implementation)

| Package | Version | Purpose |
|---------|---------|---------|
| `click` | >=8.0.0 | CLI framework |
| `requests` | >=2.28.0 | HTTP client for API calls |
| `python-dateutil` | >=2.8.0 | Date/time parsing |
| `python-slugify` | >=8.0.0 | Filename slugification |
| `python-dotenv` | >=1.0.0 | Environment variable loading |

#### 11.2.2 Optional/Future Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `polyline` | >=2.0.0 | Polyline encoding/decoding (for maps) |
| `folium` | >=0.14.0 | Local map generation |
| `rich` | >=12.0.0 | Enhanced terminal output |

### 11.3 System Requirements

- **OS:** Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Disk Space:** ~1KB per activity, plus photos (~100KB each)
- **Memory:** Minimum 256MB RAM
- **Network:** Internet connection required for export

### 11.4 Installation

Install from source:

```bash
git clone https://github.com/user/strava-to-obsidian.git
cd strava-to-obsidian
pip install -e .
```

Create `.env` file with Strava credentials:
```bash
cp .env.example .env
# Edit .env with your Client ID and Secret
```

---

## 12. Non-Functional Requirements

### 12.1 Performance

- Process minimum 10 activities per minute (excluding media download)
- Support concurrent media downloads (configurable, default 3)
- Minimize API calls by using batch endpoints where available

### 12.2 Reliability

- Graceful handling of interruptions (Ctrl+C, network failure)
- Resumable exports from last successful point
- Data integrity validation after export

### 12.3 Usability

- Clear, informative error messages
- Progress indication for long operations
- Comprehensive help documentation
- Example configuration files

### 12.4 Maintainability

- Modular code architecture
- Comprehensive docstrings and comments
- Unit tests for core functionality
- Integration tests for API interactions

### 12.5 Compatibility

- Output files compatible with Obsidian 1.0+
- Markdown files viewable in any Markdown editor
- Cross-platform file paths

---

## 13. Appendix

### 13.1 Strava Activity Types

| API Value | Display Name |
|-----------|--------------|
| `Run` | Run |
| `Ride` | Ride |
| `Swim` | Swim |
| `Walk` | Walk |
| `Hike` | Hike |
| `AlpineSki` | Alpine Ski |
| `BackcountrySki` | Backcountry Ski |
| `Canoeing` | Canoeing |
| `Crossfit` | Crossfit |
| `EBikeRide` | E-Bike Ride |
| `Elliptical` | Elliptical |
| `Golf` | Golf |
| `GravelRide` | Gravel Ride |
| `Handcycle` | Handcycle |
| `HighIntensityIntervalTraining` | HIIT |
| `IceSkate` | Ice Skate |
| `InlineSkate` | Inline Skate |
| `Kayaking` | Kayaking |
| `Kitesurf` | Kitesurf |
| `MountainBikeRide` | Mountain Bike |
| `NordicSki` | Nordic Ski |
| `Pilates` | Pilates |
| `RockClimbing` | Rock Climbing |
| `RollerSki` | Roller Ski |
| `Rowing` | Rowing |
| `Sail` | Sail |
| `Skateboard` | Skateboard |
| `Snowboard` | Snowboard |
| `Snowshoe` | Snowshoe |
| `Soccer` | Soccer |
| `StairStepper` | Stair Stepper |
| `StandUpPaddling` | Stand Up Paddling |
| `Surfing` | Surfing |
| `TableTennis` | Table Tennis |
| `Tennis` | Tennis |
| `TrailRun` | Trail Run |
| `Velomobile` | Velomobile |
| `VirtualRide` | Virtual Ride |
| `VirtualRow` | Virtual Row |
| `VirtualRun` | Virtual Run |
| `WeightTraining` | Weight Training |
| `Wheelchair` | Wheelchair |
| `Windsurf` | Windsurf |
| `Workout` | Workout |
| `Yoga` | Yoga |

### 13.2 Sample Configuration File

```json
{
  "strava": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  },
  "output": {
    "base_directory": "/Users/athlete/ObsidianVault/Fitness",
    "activities_folder": "activities",
    "media_folder": "media",
    "organize_by_year": true,
    "organize_by_month": true
  },
  "export": {
    "include_private": true,
    "include_manual": true,
    "activity_types": [],
    "include_raw_data": false
  },
  "media": {
    "download_photos": true,
    "download_videos": false,
    "generate_maps": true,
    "map_provider": "osm",
    "map_width": 800,
    "map_height": 600,
    "photo_size": "large"
  },
  "formatting": {
    "units": "both",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M",
    "include_tags": true,
    "custom_tags": ["strava", "fitness"]
  },
  "sync": {
    "mode": "incremental",
    "update_existing": false,
    "delete_removed": false
  }
}
```

### 13.3 Example Workflow

1. **Initial Setup**
   ```bash
   pip install strava-to-obsidian
   strava-to-obsidian auth
   ```

2. **Configure**
   ```bash
   # Edit configuration file
   nano ~/.config/strava-to-obsidian/config.json
   ```

3. **Full Export**
   ```bash
   strava-to-obsidian export --output ~/ObsidianVault/Fitness
   ```

4. **Incremental Sync**
   ```bash
   strava-to-obsidian sync
   ```

5. **Status Check**
   ```bash
   strava-to-obsidian status
   ```

### 13.4 Obsidian Integration Tips

1. **Linking Activities**
   - Use `[[2024-01-15_Morning_Run]]` to link to activities
   - Create daily notes that reference activities

2. **Tagging**
   - Use the `tags` frontmatter for Obsidian tag searches
   - Filter activities by type, year, or custom tags

3. **Dataview Queries**
   ```dataview
   TABLE distance_km as "Distance", duration_formatted as "Duration", avg_heartrate as "Avg HR"
   FROM "activities"
   WHERE type = "Run"
   SORT date DESC
   LIMIT 10
   ```

4. **Graph View**
   - Activities link to gear notes
   - Activities can link to location/route notes
   - Build a connected fitness knowledge base

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | November 2025 | - | Initial document |

---

*This requirements document is subject to updates as the project evolves.*
