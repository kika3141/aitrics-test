# Architecture

## Layered Structure (Single Service)
**Why:** Separation of concerns. One-way dependency minimizes change impact radius.
**How:**
```
app/
├── routes/       # FastAPI route handlers
├── dtos/         # Pydantic Request/Response DTOs
├── services/     # Business logic
├── repositories/ # DB access (SQLModel)
├── models/       # SQLModel ORM models + base classes + domain value objects
├── core/         # Config, auth, exceptions, utils
└── main.py       # FastAPI app entry
```

## Layer Rules
**Why:** Each layer has a single responsibility. Prevents business logic from leaking into data access or vice versa.
**How:**
- Route → Service → Repository (one-way dependency)
- Route: request validation, response only
- Service: business logic, exception handling, entity → DTO conversion
- Repository: DB queries only, commit/rollback handled by session dependency

## Tech Stack
- Python 3.12 + FastAPI
- SQLModel (Pydantic v2 + SQLAlchemy integrated) + asyncpg
- PostgreSQL
- Alembic (migrations)
- Docker Compose (app + db)
- pytest + pytest-asyncio + aiosqlite (test)
- uv (package management)
- ruff (lint + format)

## Transaction Management
**Why:** No transaction code in service/repository. Managed at infrastructure level via FastAPI Dependency. SQLAlchemy implicit transaction handles both reads and writes. For optimization, can upgrade to autocommit + @with_transaction decorator.
**How:**
- Session-per-request via FastAPI Dependency (`get_session`)
- 1 request = 1 session = 1 transaction
- Auto commit on success, auto rollback on exception
- Service/Repository do not call commit/rollback
