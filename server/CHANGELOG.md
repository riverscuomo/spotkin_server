# Changelog

All notable changes to the Spotkin server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Freeze Status API**: Jobs now include a `freeze_status` object in the `/jobs/{user_id}` endpoint response
  - Exposes whether a job is frozen due to 21-day inactivity
  - Provides `is_frozen`, `days_since_update`, `days_until_freeze`, and `freeze_threshold_days` fields
  - Enables client applications to display warnings when jobs are approaching freeze status
  - Server-side calculation ensures consistency across all clients

### Changed

- Enhanced `Job.to_dict()` method to calculate and include freeze status information
- Updated job response payload to include `last_updated` timestamp

## [2025-07-23]

### Added

- **Explicit Lyrics Filter**: New `banExplicitLyrics` property added to Jobs
  - Boolean property (default: false) that controls filtering of explicit tracks
  - When set to true, tracks marked as explicit by Spotify will be filtered out
  - No effect on playlists when false or omitted (default behavior)

### Changed

- Removed deprecated audio feature properties from Job model
  - Removed min/max properties for acousticness, danceability, duration, energy, and popularity
  - These properties are no longer settable or used for filtering

### Technical Details
- Jobs freeze after 21 days (1,814,400 seconds) without configuration updates
- `job.last_updated` is only refreshed when job settings are modified, not during processing
- Jobs without a `last_updated` timestamp are considered frozen
- All timestamp calculations handle both millisecond and second formats

### Example Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Daily Mix",
  "last_updated": 1737123456,
  "freeze_status": {
    "is_frozen": false,
    "days_since_update": 15.3,
    "days_until_freeze": 5.7,
    "freeze_threshold_days": 21
  }
}
```
