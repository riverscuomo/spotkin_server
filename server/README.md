# Spotkin Server

A Flask-based backend server for Spotkin, a Spotify playlist management application.

## Overview

Spotkin server provides automated playlist management for Spotify users. It processes scheduled jobs to update playlists based on user-defined criteria.

## Auto-Processing Freeze Logic (Beta Feature)

As a beta application, Spotkin includes an automatic freeze mechanism to prevent processing inactive accounts:

### How it Works
- **Freeze Period**: 21 days (1,814,400 seconds)
- **Trigger**: Jobs are automatically skipped if their `last_updated` timestamp is older than 21 days
- **Location**: The logic is implemented in `src/services/job_service.py` in the `process_scheduled_jobs()` method (around line 185)

### Implementation Details
```python
# In JobService.process_scheduled_jobs():
time_difference = now_timestamp - job_last_updated_seconds

# Skip jobs not updated in last 21 days
if time_difference > 1814400:
    print(f"Skipping job for user: {user_id} because it hasn't been updated in the last 21 days")
    continue
```

### Important Notes
- This is **NOT** a Heroku configuration - it's implemented directly in the server code
- The check is based on `job.last_updated`, not `user.last_updated`
- **Critical**: `job.last_updated` is only refreshed when the job configuration is **UPDATED** (e.g., adding/removing playlists), NOT when it's processed by the scheduler
- This means jobs will freeze after 21 days even if they're running successfully - users must make a configuration change to keep them active
- Jobs without a `last_updated` timestamp are also skipped

## Database Schema

### Models
- **User**: Stores user information and authentication tokens
  - `last_updated`: Timestamp updated when user data changes
- **Job**: Represents a scheduled playlist update task
  - `last_updated`: Timestamp updated when job is processed (used for freeze logic)
  - `last_autorun`: Timestamp of last automatic execution
  - `scheduled_time`: Hour of day (0-23) when job should run
- **Token**: Stores Spotify OAuth tokens for users

## Key Services

### JobService (`src/services/job_service.py`)
- `process_scheduled_jobs()`: Main method that runs scheduled jobs
  - Checks current hour against job scheduled times
  - Implements the 21-day inactivity freeze
  - Processes active jobs to update Spotify playlists

### DataService (`src/services/data_service.py`)
- Handles user and job data management
- Updates `user.last_updated` when user data is modified

## Database Migrations

To set up or update the database schema:

```bash
# Create a new migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

## Environment Variables

Required environment variables:
- `DATABASE_URL`: PostgreSQL database connection string
- `SPOTIFY_CLIENT_ID`: Spotify application client ID
- `SPOTIFY_CLIENT_SECRET`: Spotify application client secret
- `SECRET_KEY`: Flask application secret key

## Deployment

The application is designed to be deployed on Heroku with:
- PostgreSQL database
- Scheduled job processing (likely using Heroku Scheduler or similar)
- The job processor should run hourly to check for jobs scheduled at the current hour

## Development Notes

- Jobs are processed based on their `scheduled_time` (hour of day)
- The server handles timestamp conversion between milliseconds and seconds
- Future timestamps are detected and skipped to prevent processing errors