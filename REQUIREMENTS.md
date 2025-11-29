# Software Requirements Document: Strava to Obsidian Exporter

## 1. Overview

### 1.1 Purpose
A Python CLI tool that exports Strava activities via the official API and stores them as Obsidian-flavored Markdown files for personal archiving.

### 1.2 Scope
- Export Strava activities to Markdown files with YAML frontmatter
- Download associated media (photos, videos)
- Support incremental sync for ongoing updates
- Future: Generate static map images from GPS data

### 1.3 Target Users
- Primary: Personal use
- Secondary: Public repository for others to use/adapt

---

## 2. Strava API Integration

### 2.1 Authentication
- **Method**: OAuth 2.0 Authorization Code flow
- **Required Scopes**: `read`, `activity:read_all` (to include private activities)
- **Redirect URI**: Local HTTP server on `http://localhost:8080/callback` for token capture
- **Token Storage**: Local file (e.g., `.strava_tokens.json`) with restricted permissions (600)
- **Token Refresh**: Automatic refresh when access token expires (tokens expire after 6 hours)
- **Refresh Token Rotation**: Strava issues a new refresh token with each refresh; always store the latest

**OAuth Flow UX:**
1. CLI starts local HTTP server on port 8080
2. Browser opens Strava authorization URL
3. User approves access (note: users may decline `activity:read_all`, limiting export to public activities)
4. Strava redirects to localhost with authorization code
5. CLI exchanges code for access + refresh tokens
6. Tokens stored locally; server shuts down

### 2.2 API Endpoints Required
| Endpoint | Purpose |
|----------|----------|
| `GET /athlete` | Verify authentication, get athlete ID |
| `GET /athlete/activities` | List activities (paginated, returns `SummaryActivity`) |
| `GET /activities/{id}` | Get detailed activity data (returns `DetailedActivity`) |
| `GET /activities/{id}/streams` | Get GPS/sensor data (future: maps) |

**Important: Two-Phase Fetch Required**

The list endpoint (`/athlete/activities`) returns `SummaryActivity` objects which do **NOT** include:
- `description`
- `calories`
- `average_heartrate` / `max_heartrate`
- `photos`

To get these fields, you **must** call `GET /activities/{id}` for each activity. This means:
- 30 activities = 1 list request + 30 detail requests = **31 API calls**
- Plan accordingly for rate limits when doing bulk exports

### 2.3 Rate Limit Handling
- **Limits**: 100 requests per 15 minutes, 1,000 requests per day
- **Strategy**: 
  - Track usage via response headers (`X-RateLimit-Limit`, `X-RateLimit-Usage`)
  - Implement exponential backoff on 429 responses
  - Log warnings when approaching limits
  - Support resume/continue on rate limit exhaustion

**Bulk Export Implications:**
| Time Range | Est. Activities | API Calls | Daily Limit Impact |
|------------|-----------------|-----------|--------------------|
| 30 days | ~30 | ~31 | 3% of daily limit |
| 1 year | ~365 | ~367 | 37% of daily limit |
| 5 years | ~1,825 | ~1,835 | **Exceeds daily limit** |

For large historical exports, implement:
- Progress saving to resume across days
- `--batch-size` option to limit activities per run

---

## 3. Data Model

### 3.1 Required Activity Fields

| Field | Strava API Field | Type | Description |
|-------|------------------|------|-------------|
| ID | `id` | integer | Unique Strava activity identifier |
| Start Date | `start_date_local` | datetime | Local start time of activity |
| Name | `name` | string | User-defined activity title |
| Description | `description` | string | User-defined description (nullable) |
| Sport Type | `sport_type` | string | Strava sport type (e.g., "Run", "TrailRun", "GravelRide"). Note: Falls back to `type` field if `sport_type` unavailable |
| Elapsed Time | `elapsed_time` | integer | Total time in seconds |
| Moving Time | `moving_time` | integer | Active moving time in seconds |
| Distance | `distance` | float | Distance in meters |
| Max Heart Rate | `max_heartrate` | integer | Max HR in bpm (nullable) |
| Average Heart Rate | `average_heartrate` | float | Avg HR in bpm (nullable) |
| Max Speed | `max_speed` | float | Max speed in m/s (nullable) |
| Average Speed | `average_speed` | float | Avg speed in m/s |
| Elevation Gain | `total_elevation_gain` | float | Total elevation gain in meters |
| Calories | `calories` | float | Estimated calories burned (nullable, often unavailable—requires power meter or specific wearables) |
| Start Coordinates | `start_latlng` | [lat, lng] | Starting point coordinates (nullable) |

### 3.2 Sport Type Icons

Map Strava sport types to emoji icons for Obsidian display:

| Sport Type | Icon | Sport Type | Icon |
|------------|------|------------|------|
| Run | 🏃 | Ride | 🚴 |
| Swim | 🏊 | Walk | 🚶 |
| Hike | 🥾 | Workout | 💪 |
| WeightTraining | 🏋️ | Yoga | 🧘 |
| CrossFit | 🏋️ | Elliptical | 🏃 |
| StairStepper | 🪜 | Rowing | 🚣 |
| Kayaking | 🛶 | Canoeing | 🛶 |
| Skiing | ⛷️ | Snowboard | 🏂 |
| IceSkate | ⛸️ | Golf | ⛳ |
| Soccer | ⚽ | Tennis | 🎾 |
| Pickleball | 🏓 | RockClimbing | 🧗 |
| VirtualRun | 🏃‍♂️ | VirtualRide | 🚴‍♂️ |
| EBikeRide | 🚲 | MountainBikeRide | 🚵 |
| GravelRide | 🚴 | TrailRun | 🏃‍♂️ |
| *Default* | 🏅 | | |

### 3.3 Derived/Computed Fields

| Field | Computation | Unit in Output |
|-------|-------------|----------------|
| `distance_km` | `distance / 1000` | kilometers |
| `distance_mi` | `distance / 1609.344` | miles |
| `elapsed_time_fmt` | Format as `HH:MM:SS` | string |
| `moving_time_fmt` | Format as `HH:MM:SS` | string |
| `pace_min_km` | `moving_time / 60 / distance_km` | min/km |
| `pace_min_mi` | `moving_time / 60 / distance_mi` | min/mi |
| `speed_kph` | `average_speed * 3.6` | km/h |
| `speed_mph` | `average_speed * 2.237` | mph |
| `elevation_gain_ft` | `total_elevation_gain * 3.281` | feet |

---

## 4. File Structure

### 4.1 Directory Layout
```
<obsidian-vault>/
└── activities/
    ├── 2025-11-29-morning-run.md
    ├── 2025-11-28-evening-ride.md
    ├── ...
    └── media/
        ├── 12345678901_photo_1.jpg
        ├── 12345678901_photo_2.jpg
        └── ...
```

### 4.2 File Naming Convention
```
YYYY-MM-DD-<slugified-activity-name>.md
```

**Slugification Rules:**
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters (keep alphanumeric and hyphens)
- Truncate to 50 characters max (before extension)
- Append activity ID if duplicate filename exists: `2025-11-29-morning-run-12345678901.md`

**Examples:**
| Activity Name | Date | Filename |
|---------------|------|----------|
| "Morning Run" | 2025-11-29 | `2025-11-29-morning-run.md` |
| "🏃 5K Race!!!" | 2025-11-28 | `2025-11-28-5k-race.md` |
| "Lunch Run" (duplicate) | 2025-11-29 | `2025-11-29-lunch-run-12345678901.md` |

### 4.3 Media Naming Convention
```
<activity-id>_<media-type>_<index>.<extension>
```

**Examples:**
- `12345678901_photo.jpg` (primary photo only—API limitation)
- `12345678901_map.png` (future)

---

## 5. Obsidian Markdown Format

### 5.1 File Template

```markdown
---
strava_id: 12345678901
date: 2025-11-29T07:30:00
name: "Morning Run"
sport_type: Run
icon: 🏃
description: "Easy recovery run around the neighborhood"
elapsed_time: 1845
elapsed_time_fmt: "00:30:45"
moving_time: 1800
moving_time_fmt: "00:30:00"
distance_m: 5000
distance_km: 5.0
distance_mi: 3.11
average_speed_ms: 2.78
speed_kph: 10.0
speed_mph: 6.21
pace_min_km: 6.0
pace_min_mi: 9.66
max_speed_ms: 3.5
elevation_gain_m: 45
elevation_gain_ft: 147.6
average_heartrate: 145
max_heartrate: 165
calories: 320
coordinates:
    - 47.6062
    - -122.3321
photo: "[[media/12345678901_photo.jpg]]"
tags:
  - activity
  - run
---

# 🏃 Morning Run

**Date:** Saturday, November 29, 2025 at 7:30 AM

## Summary

| Metric | Value |
|--------|-------|
| Distance | 5.0 km (3.11 mi) |
| Duration | 00:30:00 moving / 00:30:45 elapsed |
| Pace | 6:00 /km (9:40 /mi) |
| Elevation | ↑ 45 m (148 ft) |
| Calories | 320 kcal |
| Heart Rate | 145 avg / 165 max bpm |

## Description

Easy recovery run around the neighborhood

## Photo

![[media/12345678901_photo.jpg]]

---
*Exported from Strava activity [12345678901](https://www.strava.com/activities/12345678901)*
```

### 5.2 YAML Frontmatter Fields

**Always Present:**
- `strava_id`, `date`, `name`, `sport_type`, `icon`
- `elapsed_time`, `elapsed_time_fmt`, `moving_time`, `moving_time_fmt`
- `distance_m`, `distance_km`, `distance_mi`
- `average_speed_ms`, `speed_kph`, `speed_mph`
- `tags`

**Present When Available:**
- `description` (if not empty)
- `max_speed_ms` (if recorded)
- `elevation_gain_m`, `elevation_gain_ft` (if > 0)
- `average_heartrate`, `max_heartrate` (if HR data exists)
- `calories` (if recorded)
- `start_lat`, `start_lng` (if GPS data exists)
- `pace_min_km`, `pace_min_mi` (for run/walk activities)
- `photo` (if primary photo exists)

### 5.3 Tags
Auto-generated tags:
- `activity` (always)
- `<sport-type-lowercase>` (e.g., `run`, `ride`, `swim`)

---

## 6. Media Handling

### 6.1 Photos

⚠️ **API Limitation:** Strava's API provides very limited photo access. There is no dedicated photos endpoint.

**What's Available:**
- **Source**: `DetailedActivity.photos.primary.urls` object in activity detail response
- **Access**: Only the **primary photo** (activity cover photo) is accessible
- **Sizes**: Limited to specific sizes (`100`, `600` pixels) — no original resolution
- **Multiple Photos**: If an activity has multiple photos, only the primary is available via API

**Implementation:**
- Check `activity.photos.count` to see if photos exist
- If `photos.primary` exists, download from `photos.primary.urls["600"]`
- Storage: `/activities/media/<activity-id>_photo.jpg`
- Reference: Obsidian wikilink format `![[media/filename.jpg]]`

### 6.2 Videos

❌ **Not Available:** The Strava API does **not** provide access to activity videos. This is a platform limitation with no workaround.

### 6.3 Maps (Future/MVP+)
- **Source**: `DetailedActivity.map.summary_polyline` (encoded polyline string)
- **Decoding**: Use `polyline` library to decode to lat/lng coordinates
- **Generation**: Static image via Mapbox Static API, Google Static Maps, or OpenStreetMap
- **Storage**: `/activities/media/<activity-id>_map.png`
- **Config Options**: 
  - Map style (streets, satellite, dark)
  - Image dimensions
  - Route color

**Note:** The `summary_polyline` is included in the `DetailedActivity` response, so no additional API calls needed for map data.

---

## 7. Sync Behavior

### 7.1 Initial Sync
- **Default**: Export activities from the last 30 days
- **Option**: Specify custom date range via CLI flags
- **Pagination**: Handle Strava's 200 activities per page limit

**Note:** The `after` and `before` API parameters require **epoch timestamps** (seconds since 1970-01-01), not ISO date strings. The CLI accepts human-readable dates and converts internally.

### 7.2 Incremental Sync
- **Tracking**: Store last sync timestamp in `.strava_sync_state.json`
- **Detection**: Use `after` parameter to fetch only new activities
- **Updates**: Re-export if activity `updated_at` > file modification time (optional flag)

### 7.3 State File Format
```json
{
  "last_sync": "2025-11-29T12:00:00Z",
  "exported_activities": {
    "12345678901": {
      "filename": "2025-11-29-morning-run.md",
      "updated_at": "2025-11-29T08:00:00Z"
    }
  }
}
```

### 7.4 Conflict Handling
- **Default**: Skip existing files (preserve manual edits)
- **Option**: `--force` flag to overwrite all files
- **Option**: `--update-frontmatter` to update YAML only, preserve body edits

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

### 8.3 CLI Arguments

```
strava-to-obsidian [OPTIONS] COMMAND [ARGS]

Commands:
  auth        Authenticate with Strava (OAuth flow)
  export      Export activities to Markdown
  sync        Incremental sync (export new activities only)

Export/Sync Options:
  --output, -o PATH       Output directory (default: ./activities)
  --days, -d INT          Export last N days (default: 30)
  --after DATE            Export activities after this date (YYYY-MM-DD)
  --before DATE           Export activities before this date (YYYY-MM-DD)
  --force, -f             Overwrite existing files
  --no-media              Skip media downloads
  --dry-run               Show what would be exported without writing files
  --verbose, -v           Verbose output
  --quiet, -q             Minimal output

Examples:
  strava-to-obsidian auth
  strava-to-obsidian export --days 30
  strava-to-obsidian export --after 2024-01-01 --before 2024-12-31
  strava-to-obsidian sync
  strava-to-obsidian sync --force
```

---

## 9. Error Handling

### 9.1 Network Errors
- Retry transient failures (5xx, timeouts) with exponential backoff
- Max 3 retries per request
- Log failed activity IDs for manual retry

### 9.2 API Errors
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
| Package | Purpose |
|---------|---------|
| `requests` | HTTP client for API calls |
| `click` | CLI framework |
| `pyyaml` | YAML config file parsing |
| `python-dateutil` | Date parsing and formatting |
| `python-slugify` | Filename slugification |

### 11.3 Development Dependencies
| Package | Purpose |
|---------|---------|
| `pytest` | Testing framework |
| `pytest-cov` | Coverage reporting |
| `black` | Code formatting |
| `ruff` | Linting |
| `mypy` | Type checking |

### 11.4 Project Structure
```
strava-to-obsidian/
├── src/
│   └── strava_to_obsidian/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py           # CLI entry point
│       ├── auth.py          # OAuth handling
│       ├── api.py           # Strava API client
│       ├── models.py        # Activity data models
│       ├── exporter.py      # Markdown generation
│       ├── media.py         # Photo/video downloads
│       └── config.py        # Configuration management
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_exporter.py
│   └── fixtures/
├── pyproject.toml
├── README.md
├── REQUIREMENTS.md
└── .gitignore
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
