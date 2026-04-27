# Vital Risk API

## Project Overview
REST API for hospital vital signs data management and rule-based risk scoring.
Single-service, layered architecture (FastAPI + SQLModel + PostgreSQL).

## Critical Rules
- NEVER commit secrets or API keys
- No lazy loading — always use explicit JOINs
- Use `session.exec()` not `session.execute()` (SQLModel idiom)
- **Answer before acting**: When the user asks a question, stop all work and answer the question or clarify constraints first. Do not assume intent and continue working.
- **Always specify location**: When reporting something is missing, omitted, or wrong, always include the exact location (file path, line number, section name). Never say "X is missing" without saying where.

## Commands
```bash
uv venv && uv pip install -e ".[dev]"   # Install dependencies
source .venv/bin/activate                # Activate venv
uvicorn app.main:app --reload            # Start server
pkill -f "uvicorn app.main"              # Stop server
python -m pytest tests/ -v              # Run tests
ruff check .                             # Lint
ruff format .                            # Format
alembic revision --autogenerate -m "msg" # Generate migration
alembic upgrade head                     # Apply migration
alembic downgrade -1                     # Rollback migration
```

## Quick Start (Docker Compose)
```bash
docker compose up --build
```
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Quick Start (Local)
```bash
docker compose up db -d                  # Start PostgreSQL
uv venv && uv pip install -e ".[dev]"
source .venv/bin/activate && alembic upgrade head
uvicorn app.main:app --reload
```

## Environment Variables (.env)
```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/vitalrisk
API_TOKEN=dev-secret-token
VITAL_RISK_TIME_WINDOW_HOURS=24
LOG_LEVEL=DEBUG
```

## Key Design Decisions
- **Optimistic Locking**: version column on Patient and Vital tables. 409 Conflict on mismatch.
- **Vital UPSERT**: composite key (patient_id, recorded_at, vital_type). INSERT if new, UPDATE with version check if exists.
- **Auth**: simple Bearer token via env var (not JWT — scope is a coding test).
- **SQLModel**: unified Pydantic + SQLAlchemy models, reducing boilerplate.
- **Datetime**: naive UTC throughout. No timezone info stored. All times assumed UTC.
- **Enum**: Python enum only, stored as VARCHAR in DB (no PostgreSQL enum type).
- **Base Pattern**: domain fields (*Base) separated from row management (BaseSQLModel, BaseCreatedUpdatedModel). DTOs inherit Base only.
- **Transaction**: session-per-request via FastAPI Dependency. Can upgrade to autocommit + @with_transaction for optimization.

## Language
- Code comments and documentation: **Korean**
- API responses and error codes: **English**

## Feedback & Learning
- Team rules: `.claude/rules/*.md` — git tracked, shared with team
- Project feedback: `.claude/memory/*.md` — gitignored, project-scoped feedback log
  - When corrected, save feedback as a `.md` file in `.claude/memory/` with frontmatter:
    ```yaml
    ---
    name: feedback title
    description: one-line summary
    type: feedback
    count: 1
    first_seen: 2026-04-26
    last_seen: 2026-04-26
    ---
    ```
  - If the same feedback already exists, increment `count` and update `last_seen`
  - Maintain `.claude/memory/MEMORY.md` as an index of all feedback files
  - When `count >= 3`, flag for promotion to `.claude/rules/` in the MEMORY.md index
- Personal learning: auto-memory (`~/.claude/projects/.../memory/`) — local, auto-managed
  - **IMPORTANT**: Save feedback to `.claude/memory/` first. Do not duplicate in auto-memory.

## Response Format
- At the end of every response, list the `.claude/rules/` files referenced: `📎 Referenced: models.md, conventions.md`
- Only include rules that were actually used to inform the response
- Omit this line if no rules were referenced
