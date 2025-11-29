# Software Requirements Document
## Strava to Obsidian Activity Exporter

**Version:** 1.0  
**Last Updated:** November 2025

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
- Retrieve all user activities from Strava
- Convert activity data to Obsidian-flavored Markdown files
- Download and organize associated media (photos, videos, map images)
- Support incremental updates to avoid re-downloading existing activities
- Maintain a local archive that can be used with Obsidian or any Markdown-compatible tool

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

| Field | Type | Description |
|-------|------|-------------|
| `laps` | Array | Array of lap objects |
| `lap.name` | String | Lap name |
| `lap.elapsed_time` | Integer | Lap elapsed time |
| `lap.moving_time` | Integer | Lap moving time |
| `lap.distance` | Float | Lap distance |
| `lap.average_speed` | Float | Lap average speed |
| `lap.average_heartrate` | Float | Lap average heart rate |

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

The script SHALL create the following directory structure:

```
<output_directory>/
├── .strava-export/
│   ├── config.json          # Configuration and tokens
│   ├── state.json            # Export state and last sync
│   └── activity_index.json   # Index of exported activities
├── media/
│   ├── maps/
│   │   └── <activity_id>_map.png
│   ├── photos/
│   │   └── <activity_id>/
│   │       ├── photo_001.jpg
│   │       └── photo_002.jpg
│   └── videos/
│       └── <activity_id>/
│           └── video_001.mp4
└── activities/
    ├── 2024/
    │   ├── 2024-01/
    │   │   ├── 2024-01-15_Morning_Run.md
    │   │   └── 2024-01-16_Evening_Ride.md
    │   └── 2024-02/
    │       └── 2024-02-01_Long_Run.md
    └── 2025/
        └── 2025-01/
            └── 2025-01-05_New_Year_Ride.md
```

### 5.2 File Naming Conventions

#### 5.2.1 Activity Files

Activity Markdown files SHALL be named using the pattern:
```
YYYY-MM-DD_<sanitized_activity_name>.md
```

Sanitization rules:
- Replace spaces with underscores
- Remove or replace special characters: `/ \ : * ? " < > |`
- Truncate to maximum 100 characters (before extension)
- Append numeric suffix if duplicate: `_2`, `_3`, etc.

#### 5.2.2 Media Files

**Map Images:**
```
<activity_id>_map.png
```

**Photos:**
```
<activity_id>/<sequential_number>_<original_filename>
```

**Videos:**
```
<activity_id>/<sequential_number>_<original_filename>
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

Each activity Markdown file SHALL include YAML frontmatter with the following structure:

```yaml
---
# Core Identification
strava_id: 12345678901
strava_url: "https://www.strava.com/activities/12345678901"
title: "Morning Run"
date: 2024-01-15
datetime: 2024-01-15T07:30:00-05:00
timezone: "America/New_York"

# Activity Classification
type: Run
sport_type: Run
activity_type: run
is_race: false
is_commute: false
is_trainer: false
is_manual: false
is_private: false

# Performance Metrics
distance_km: 10.5
distance_mi: 6.52
duration_minutes: 52
duration_formatted: "52:30"
moving_time_minutes: 50
moving_time_formatted: "50:15"
pace_per_km: "5:00"
pace_per_mi: "8:03"
speed_kmh: 12.0
speed_mph: 7.46
elevation_gain_m: 125
elevation_gain_ft: 410
calories: 650

# Heart Rate (if available)
avg_heartrate: 152
max_heartrate: 175

# Power Data (if available)
avg_watts: null
max_watts: null
weighted_avg_watts: null

# Cadence (if available)
avg_cadence: 180

# Location
start_location: [40.7128, -74.0060]
end_location: [40.7580, -73.9855]
city: "New York"
state: "New York"
country: "United States"

# Gear
gear: "Nike Pegasus 40"
gear_id: "g12345678"

# Social
kudos: 15
comments: 3
achievements: 2
pr_count: 1

# Strava Scores
suffer_score: 85
relative_effort: 85

# Media
has_photos: true
photo_count: 2
has_map: true

# Tags for Obsidian
tags:
  - strava
  - run
  - morning-run
  - 2024
  - january

# Aliases for Obsidian linking
aliases:
  - "Morning Run 2024-01-15"
  - "Run 10.5km"

# Custom fields
weather: null
notes: null
---
```

### 6.2 Markdown Body Structure

The body of each activity file SHALL follow this template:

```markdown
# Morning Run

> 🏃 **Run** on **Monday, January 15, 2024** at **7:30 AM**

## Summary

| Metric | Value |
|--------|-------|
| 📏 Distance | 10.5 km (6.52 mi) |
| ⏱️ Duration | 52:30 |
| 🏃 Moving Time | 50:15 |
| ⚡ Pace | 5:00 /km (8:03 /mi) |
| ⛰️ Elevation | +125 m (+410 ft) |
| 🔥 Calories | 650 kcal |
| ❤️ Avg HR | 152 bpm |
| 💪 Relative Effort | 85 |

## Description

User's activity description appears here if provided.

## Route Map

![[media/maps/12345678901_map.png]]

## Photos

![[media/photos/12345678901/001_photo.jpg]]
![[media/photos/12345678901/002_photo.jpg]]

## Laps

| Lap | Distance | Time | Pace | Avg HR |
|-----|----------|------|------|--------|
| 1 | 1.0 km | 5:05 | 5:05 /km | 145 |
| 2 | 1.0 km | 4:58 | 4:58 /km | 150 |
| 3 | 1.0 km | 4:55 | 4:55 /km | 154 |
| ... | ... | ... | ... | ... |

## Segments

### Segment Name 1
- **Time:** 2:45
- **Rank:** 15 / 1,234 (Top 1.2%)
- **PR:** Yes ⭐

### Segment Name 2
- **Time:** 1:30
- **Rank:** 234 / 5,678

## Best Efforts

| Effort | Time | Date |
|--------|------|------|
| 1 km | 4:32 | PR! |
| 1 mile | 7:25 | - |
| 5 km | 24:15 | - |

## Achievements

- 🏆 New 1 km PR: 4:32
- 🥈 2nd fastest 5 km this year

## Gear

**Nike Pegasus 40** (Total: 523.4 km)

## Raw Data

<details>
<summary>View raw Strava data</summary>

```json
{
  "id": 12345678901,
  "name": "Morning Run",
  ...
}
```

</details>

---

*Exported from Strava on 2025-01-15 | [View on Strava](https://www.strava.com/activities/12345678901)*
```

### 6.3 Activity Type Icons

The script SHALL use appropriate icons for different activity types:

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

### 7.1 Map Generation

#### 7.1.1 Map Image Requirements

The script SHALL generate static map images for activities with GPS data:

- **Image Format:** PNG
- **Resolution:** 800 x 600 pixels (configurable)
- **Style:** Clean, readable with route overlay
- **Route Color:** Activity type-specific (configurable)
- **Background:** Street map or satellite (configurable)

#### 7.1.2 Map Generation Options

**Option 1: Mapbox Static Images API**
```
https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/
  path-{strokeWidth}+{strokeColor}({encodedPolyline})/
  auto/{width}x{height}?access_token={token}
```

**Option 2: OpenStreetMap with Folium**
- Generate maps locally using Python Folium library
- Export as PNG using browser automation

**Option 3: Google Static Maps API**
```
https://maps.googleapis.com/maps/api/staticmap?
  size={width}x{height}&
  path=enc:{encodedPolyline}&
  key={api_key}
```

#### 7.1.3 Polyline Decoding

The script SHALL:
- Decode Strava's encoded polyline format
- Support both summary and detailed polylines
- Handle activities without GPS data gracefully

### 7.2 Photo Handling

#### 7.2.1 Photo Download

The script SHALL download activity photos:
- Download full-resolution photos when available
- Fall back to largest available size
- Preserve original file format (JPEG, PNG)
- Include photo metadata (EXIF) when available

#### 7.2.2 Photo Sources

| Source | Access | Notes |
|--------|--------|-------|
| Primary photos | API `/activities/{id}/photos` | Direct Strava photos |
| Instagram photos | May be linked | Requires additional handling |

#### 7.2.3 Photo Metadata

Store photo metadata for each image:
```json
{
  "photo_id": "12345",
  "activity_id": 12345678901,
  "caption": "Beautiful sunrise",
  "location": [40.7128, -74.0060],
  "taken_at": "2024-01-15T07:45:00Z",
  "urls": {
    "100": "https://...",
    "600": "https://...",
    "2048": "https://..."
  },
  "local_path": "media/photos/12345678901/001_sunrise.jpg"
}
```

### 7.3 Video Handling

#### 7.3.1 Video Download

The script SHALL attempt to download activity videos:
- Check for video attachments in activity
- Download highest quality available
- Store in activity-specific subfolder

#### 7.3.2 Video Limitations

Note: Strava's API has limited video support. The script SHALL:
- Document known limitations
- Handle missing video gracefully
- Log when videos cannot be downloaded

### 7.4 Media Storage Optimization

#### 7.4.1 Deduplication

- Check if media file already exists before downloading
- Use file hash (MD5/SHA256) for duplicate detection
- Skip download if identical file exists

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

The script SHALL support the following command line arguments:

```
strava-to-obsidian [OPTIONS] [COMMAND]

Commands:
  auth          Authenticate with Strava
  export        Export activities
  sync          Sync new activities (incremental)
  update        Update existing activities
  status        Show export status

Options:
  --config, -c PATH       Configuration file path
  --output, -o PATH       Output directory
  --verbose, -v           Enable verbose logging
  --quiet, -q             Suppress non-essential output
  --dry-run               Show what would be done without making changes
  --force                 Force re-export of all activities
  --after DATE            Only export activities after date (YYYY-MM-DD)
  --before DATE           Only export activities before date (YYYY-MM-DD)
  --type TYPE             Only export specific activity type(s)
  --limit N               Limit number of activities to export
  --no-media              Skip media download
  --no-maps               Skip map generation
  --help, -h              Show help message
  --version               Show version
```

### 8.3 Environment Variables

The script SHALL support configuration via environment variables:

| Variable | Description |
|----------|-------------|
| `STRAVA_CLIENT_ID` | Strava API client ID |
| `STRAVA_CLIENT_SECRET` | Strava API client secret |
| `STRAVA_ACCESS_TOKEN` | Current access token |
| `STRAVA_REFRESH_TOKEN` | Refresh token |
| `STRAVA_EXPORT_OUTPUT` | Output directory path |
| `MAPBOX_ACCESS_TOKEN` | Mapbox API token |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key |

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

#### 11.2.1 Required Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.28.0 | HTTP client for API calls |
| `python-dateutil` | >=2.8.0 | Date/time parsing |
| `pyyaml` | >=6.0 | YAML frontmatter handling |
| `polyline` | >=2.0.0 | Polyline encoding/decoding |

#### 11.2.2 Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `folium` | >=0.14.0 | Local map generation (OSM) |
| `selenium` | >=4.0.0 | Map image export (with Folium) |
| `pillow` | >=9.0.0 | Image processing |
| `tqdm` | >=4.64.0 | Progress bars |
| `rich` | >=12.0.0 | Enhanced terminal output |

### 11.3 System Requirements

- **OS:** Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Disk Space:** Varies by activity count and media
- **Memory:** Minimum 512MB RAM
- **Network:** Internet connection required for export

### 11.4 Installation

The script SHALL be installable via pip:

```bash
pip install strava-to-obsidian
```

Or from source:

```bash
git clone https://github.com/user/strava-to-obsidian.git
cd strava-to-obsidian
pip install -e .
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
