<!--
Guidance for AI coding agents working in the GynSys repository.
Keep this file short, concrete, and focused on repository-specific patterns.
--> 

# GynSys — Copilot Instructions (concise)

Purpose: help an AI coding agent become productive quickly in this repo.

- **Big picture**: This repo contains two related projects:
  - The Telegram bot (root `gynsys/`): a Python bot using `python-telegram-bot`, aiosqlite and sqlite DB (`database/medical_bot.db`). Entry points: `main.py`, `webhook_server.py`, `wsgi.py`.
  - A separate SaaS app (under `appgynsys/`): a FastAPI backend in `appgynsys/backend/` (entry `app.main`) and a React/Vite frontend in `appgynsys/frontend/`.

- **Key files to read before editing or implementing behavior**:
  - `config.py` — required env vars: `BOT_TOKEN`, `SUPER_ADMIN_ID`, `ENCRYPTION_KEY`, `DB_PATH`, and `WEBHOOK` mode. Changes here are high impact.
  - `requirements.txt` — primary Python dependencies (telegram, aiosqlite, sqlalchemy, alembic).
  - `database/` — sqlite DB used by the bot plus DB helper modules in `database/*.py`.
  - `features/` — bot features split by domain. Convention: `*.user_handler.py` and `*.admin_handlers.py` (see `features/main_menu/user_handler.py`).
  - `common/texts.py` and `features/*/texts.json` — where user-facing messages are stored.
  - `alembic/` — migrations for SQLAlchemy (used by `appgynsys/backend`).

- **Patterns & conventions (project-specific)**:
  - Callback routing uses `callback_data` strings with prefixes. Example prefixes in `features/main_menu/user_handler.py`: `doctor_panel`, `doctor_share_link`, `citas_*`, `resched_cal_`, `reschedule_`.
  - Feature handlers are split: user-facing flows live in `*.user_handler(s).py`; admin flows live in `*.admin_handlers.py`. Preserve these splits when adding functionality.
  - DB access is frequently async and uses `aiosqlite` in the bot; in other parts FastAPI + SQLAlchemy async APIs are used (`appgynsys/backend`). Follow the existing async patterns.
  - Sensitive configuration must come from env vars or `.env` (see `config.py`). Do not hardcode secrets. `ENCRYPTION_KEY` must be present — changing it will break existing encrypted data.

- **Developer workflows and run commands** (tested/expected):
  - Bot (development, polling): set `.env` with `BOT_TOKEN`, `SUPER_ADMIN_ID`, `ENCRYPTION_KEY`, `WEBHOOK=OFF`. Then run `python main.py` or run from your IDE.
  - Bot (webhook): set `WEBHOOK=ON`, `WEBHOOK_URL` and `WEBHOOK_PORT` and use `webhook_server.py` / `wsgi.py` as appropriate.
  - FastAPI backend: from `appgynsys/backend`: `uvicorn app.main:app --reload`.
  - Alembic migrations (backend): run `alembic upgrade head` from `appgynsys/backend` (or root where alembic.ini points).
  - Celery workers (backend tasks): see `appgynsys/backend/README.md` and run `celery -A app.tasks.celery_app worker --loglevel=info`.

- **When modifying handlers or messages**:
  - Keep `callback_data` tokens stable — frontend keyboards and callback routers depend on exact strings.
  - Use `common/texts.py` for translated/writable messages when available rather than inlining strings.
  - When adding DB schema changes, add an Alembic migration and avoid in-place schema edits for deployed DBs.

- **Where to look for examples**:
  - `features/main_menu/user_handler.py` — keyboard construction, callback routing and permission checks (RoleManager usage).
  - `utils/role_manager.py` — how doctor/user roles are read from DB and used to gate UI.
  - `database/` modules — how aiosqlite connections and queries are performed.
  - `appgynsys/backend/app/tasks/email_tasks.py` — Celery task examples.

- **Common pitfalls**:
  - Forgetting required env vars (`BOT_TOKEN`, `ENCRYPTION_KEY`, `SUPER_ADMIN_ID`) will raise on startup (see `config.py`).
  - Mixing sync DB access with async patterns in the bot — prefer `aiosqlite` usage as in the repo.
  - Changing `ENCRYPTION_KEY` without data migration will make encrypted records unreadable.

If anything in these instructions seems incomplete or you want more detail (e.g., sample `.env`, CI steps, or how a specific feature routes callbacks), tell me which area to expand and I will iterate.
