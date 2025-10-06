# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trunk Player v2 is a Django web application for playing recorded radio transmissions captured by [Trunk Recorder](https://github.com/robotastic/trunk-recorder). It provides a modern web interface with real-time WebSocket support, transcription support, and Progressive Web App (PWA) capabilities.

**Stack:** Python 3.12, Django 5.1, Django Channels, Django REST Framework, PostgreSQL, Redis, HTMX, Alpine.js, Tailwind CSS

## Common Commands

### Docker (Recommended)
```bash
docker compose up                              # Production
docker compose -f docker-compose-devel.yml up  # Development (with code volume mount)
```

### Local Development
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Testing
```bash
python manage.py test                # Run all tests
python manage.py test radio          # Run radio app tests only
python manage.py test radio.tests.TestClassName  # Run specific test class
```

### Management Commands
```bash
python manage.py import_talkgroups --system "System Name" file.csv   # Import talkgroup data
python manage.py import_units --system "System Name" file.csv        # Import radio unit data
python manage.py prune_database --days 30                            # Clean up old data
python manage.py prune_database --days 30 --dry-run                  # Preview cleanup
```

## Architecture

### Core Components
- **`trunk_player/`** - Django project configuration (settings, urls, wsgi/asgi)
- **`radio/`** - Main Django app containing all business logic

### Key Files in `radio/`
- `models.py` - Database models: System, TalkGroup, Unit, Transmission, Transcription, ScanList, Incident, Profile, Plan, TalkGroupAccess
- `views/` - View package with modules for main views, user views, auth, incidents, PWA
- `api/` - REST API viewsets and URLs
- `serializers.py` - DRF serializers for REST API
- `consumers.py` - WebSocket consumers for live call streaming
- `routing.py` - WebSocket URL routing
- `auth.py` - Fief authentication backend
- `forms.py` - Django forms
- `management/commands/` - Custom management commands for data import/export

### API Endpoints
REST API available at `/api/v2/` with endpoints for:
- `/api/v2/systems/` - Radio systems
- `/api/v2/talkgroups/` - Talkgroups
- `/api/v2/units/` - Radio units
- `/api/v2/transmissions/` - Transmissions
- `/api/v2/transcriptions/` - Transcriptions
- `/api/v2/scanlists/` - User scan lists
- `/api/v2/incidents/` - Incidents
- `/api/v2/import_transmission/` - Transmission import (for Trunk Recorder)

API documentation available at `/api/docs/` (Swagger) and `/api/redoc/` (ReDoc).

### Real-Time Features
WebSocket connections at `/ws/` using Django Channels with Redis backend:
- `/ws/` - All transmissions
- `/ws/tg/<slug>/` - Specific talkgroup
- `/ws/scan/<slug>/` - Specific scanlist
- `/ws/unit/<slug>/` - Specific unit
- `/ws/inc/<slug>/` - Specific incident

### Frontend
- HTMX for dynamic page updates
- Alpine.js for client-side interactivity
- Tailwind CSS for styling (via CDN)
- PWA support with manifest and service worker

### Templates
Templates are in `/templates/` with:
- `base.html` - Base layout with navigation
- `radio/player.html` - Audio player with Alpine.js
- `radio/home.html` - Home page
- `radio/talkgroup_list.html` - Talkgroup listing
- `radio/auth/` - Authentication templates

## Key Environment Variables

| Variable | Description |
|----------|-------------|
| `DEBUG` | Enable debug mode (True/False) |
| `SECRET_KEY` | Django secret key |
| `SQL_ENGINE`, `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`, `SQL_HOST` | Database config |
| `REDIS_URL` | Redis connection (default: redis://127.0.0.1:6379) |
| `AUDIO_URL_BASE` | Base URL for audio files (S3 or local path) |
| `ALLOW_ANONYMOUS` | Allow anonymous access (True/False) |
| `ACCESS_TG_RESTRICT` | Enable per-user talkgroup access restrictions |
| `OPEN_REGISTRATION` | Allow user self-registration (True/False) |
| `SITE_TITLE` | Site branding title |
| `ADD_TRANS_AUTH_TOKEN` | API token for transmission import |
| `FIEF_BASE_URL`, `FIEF_CLIENT_ID`, `FIEF_CLIENT_SECRET` | Fief OAuth configuration |

## Authentication

Trunk Player v2 supports multiple authentication methods:
1. **Local email/password** - Traditional Django authentication
2. **Fief OAuth** - Open-source auth platform integration (configure via FIEF_* env vars)

## Access Control

- **Plans** - Define history access limits (minutes of transmission history visible)
- **TalkGroupAccess** - Groups of talkgroups users can access
- **Profiles** - User preferences including unit ID visibility
- **Registration modes** - Open (self-registration) or closed (admin approval)

## Local Settings

Create `trunk_player/settings_local.py` for local configuration overrides (automatically imported by settings.py).
