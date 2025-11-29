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
A Python CLI tool that exports Strava activities via the official API and stores them as Obsidian-flavored Markdown files for personal archiving.

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

## 3. Data Model

### 3.1 Required Activity Fields

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

## 4. File Structure

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

### 4.2 File Naming Convention
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

## 5. Obsidian Markdown Format

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

### 8.1 Config File
Location: `~/.config/strava-to-obsidian/config.yaml` or project root `.strava-export.yaml`

```yaml
# Strava API credentials
strava:
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"

# Export settings
export:
  output_dir: "/path/to/obsidian/vault/activities"
  date_format: "%Y-%m-%d"
  
# Unit preferences
units:
  distance: "km"  # km or mi (affects which is shown first in summary)
  elevation: "m"  # m or ft
  speed: "pace"   # pace or speed (for run/walk activities)

# Media settings
media:
  download_photos: true   # Primary photo only (API limitation)
  generate_maps: false    # Future feature

# Sync settings
sync:
  default_days: 30
  skip_existing: true
```

### 8.2 Environment Variables
Alternative credential storage:
```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
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
| 401 Unauthorized | Attempt token refresh; if fails, prompt re-auth |
| 403 Forbidden | Log warning, skip activity (likely permission issue) |
| 404 Not Found | Log warning, skip (deleted activity) |
| 429 Rate Limited | Wait per `Retry-After` header, then continue |

### 9.3 Data Errors
- Missing required fields: Use sensible defaults or skip with warning
- Invalid coordinates: Omit from frontmatter
- Photo download failure: Log error, continue without photo

### 9.4 File System Errors
- Permission denied: Exit with clear error message
- Disk full: Exit with clear error message
- Invalid filename characters: Sanitize automatically

---

## 10. Security Considerations

### 10.1 Credential Storage
- Never commit credentials to version control
- Store tokens in user-only readable file (chmod 600)
- Support environment variables for CI/automation
- Document `.gitignore` requirements

### 10.2 API Credentials
- Client secret should never be logged
- Token refresh happens automatically; user shouldn't see tokens

### 10.3 Data Privacy
- GPS coordinates may reveal home location
- Option to redact start coordinates within configurable radius (future)
- Private activities exported by default (with proper scope)

---

## 11. Development Requirements

### 11.1 Python Version
- Minimum: Python 3.9
- Target: Python 3.11+

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

## 12. Future Enhancements (Post-MVP)

- [ ] Map image generation from GPS polylines (using `summary_polyline`)
- [ ] Segment effort details
- [ ] Gear tracking (which shoes/bike used)
- [ ] Training load / fitness metrics
- [ ] Bulk historical export with progress bar and resume capability
- [ ] Home location privacy zone (redact start coordinates within radius)
- [ ] Custom Markdown templates
- [ ] Multiple output format support (JSON, CSV)
- [ ] Obsidian plugin for direct sync
- [ ] Heart rate zone breakdown (via `GET /activities/{id}/zones`)
- [ ] Activity comments export

---

## Appendix A: Strava Sport Types Reference

Complete list of Strava sport types for icon mapping:

```
AlpineSki, BackcountrySki, Badminton, Canoeing, Crossfit, EBikeRide, Elliptical,
EMountainBikeRide, Golf, GravelRide, Handcycle, HighIntensityIntervalTraining,
Hike, IceSkate, InlineSkate, Kayaking, Kitesurf, MountainBikeRide, NordicSki,
Pickleball, Pilates, Racquetball, Ride, RockClimbing, RollerSki, Rowing, Run,
Sail, Skateboard, Snowboard, Snowshoe, Soccer, Squash, StairStepper,
StandUpPaddling, Surfing, Swim, TableTennis, Tennis, TrailRun, Velomobile,
VirtualRide, VirtualRow, VirtualRun, Walk, WeightTraining, Wheelchair,
Windsurf, Workout, Yoga
```

---

## Appendix B: Sample API Responses

### Activity Summary (List endpoint)
```json
{
  "id": 12345678901,
  "name": "Morning Run",
  "distance": 5000.0,
  "moving_time": 1800,
  "elapsed_time": 1845,
  "total_elevation_gain": 45.0,
  "sport_type": "Run",
  "start_date": "2025-11-29T15:30:00Z",
  "start_date_local": "2025-11-29T07:30:00Z",
  "start_latlng": [47.6062, -122.3321],
  "average_speed": 2.78,
  "max_speed": 3.5
}
```

### Activity Detail (Individual endpoint)
Includes additional fields:
```json
{
  "description": "Easy recovery run",
  "calories": 320.0,
  "average_heartrate": 145.0,
  "max_heartrate": 165,
  "photos": {
    "count": 2,
    "primary": { "urls": { "600": "https://..." } }
  }
}
```
