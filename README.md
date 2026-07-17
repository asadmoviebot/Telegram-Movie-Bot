# Telegram Movie Platform

A production-ready Telegram bot for discovering, watching and managing movies, built with
Clean Architecture (Repository + Service layers), SQLAlchemy 2.x, python-telegram-bot v22 and APScheduler.

## Features

**Users**
`/start`, full-text search, search by code, categories, genres, top rated, latest, random movie,
favorites, watch history, 1–10 ratings, comments, personalized recommendations, profile, premium
status, referral links, and language selection (Uzbek / English / Russian).

**Admin panel** (inline, `/start` → ⚙️ Admin Panel for configured admin IDs)
Movie CRUD, category & genre management, statistics, broadcast messaging, premium management,
advertisement management, referral statistics, user management with ban/unban, force-subscribe
channel management, database backup & restore, statistics export (CSV), and a log viewer.

## Architecture

```
app/
  config.py            # env-based settings
  logging_config.py    # structured JSON logging
  database/             # SQLAlchemy models + session/engine
  repositories/         # data access layer (Repository Pattern)
  services/              # business logic (Service Layer)
  bot/
    handlers/            # Telegram handlers, grouped by feature
    keyboards.py          # inline keyboard builders
    locales.py            # uz/en/ru translations
    states.py             # ConversationHandler states
  utils/                 # decorators (auth/ban/subscription gating) + helpers
scheduler/jobs.py        # APScheduler: nightly backups, premium expiry sweep
```

## Getting started

```bash
cp .env.example .env
# edit .env: set BOT_TOKEN, ADMIN_IDS, BOT_USERNAME

pip install -r requirements.txt
python -m app.main
```

The SQLite database and its tables are created automatically on first run. To migrate to
PostgreSQL, just change `DATABASE_URL` in `.env` (e.g.
`postgresql+psycopg://user:pass@host:5432/movies`) — the Repository/Service layers do not change.

## Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## Admin panel quick reference

| Action | How |
|---|---|
| Open admin panel | Tap "⚙️ Admin Panel" in the main menu (admin IDs only) |
| Add / edit / delete movie | Admin Panel → Movies |
| Manage categories / genres | Admin Panel → Categories / Genres |
| Broadcast a message | Admin Panel → Broadcast |
| Grant / revoke premium | `/grant <telegram_id> <days>` (`0` = lifetime), `/revoke <telegram_id>` |
| Ban / unban a user | `/ban <telegram_id>`, `/unban <telegram_id>` |
| Find a user | `/finduser <name or username>` |
| Backup / restore database | Admin Panel → Backup DB / Restore DB |
| Export statistics | Admin Panel → Export stats |
| View logs | Admin Panel → Logs |
| Manage force-subscribe channels | Admin Panel → Channels |
| Manage advertisements | Admin Panel → Advertisements |
| Referral leaderboard | Admin Panel → Referral stats |

## CI/CD

`.github/workflows/ci.yml` installs dependencies, byte-compiles the codebase and builds the
Docker image on every push/PR to `main`.
