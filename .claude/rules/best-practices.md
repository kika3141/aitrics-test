# Best Practices

## Do's
- Always use type hints — catch errors at IDE level, not runtime
- Service methods: wrap in try-catch (see exception.md) — prevents unhandled exceptions from reaching route
- Entity → DTO conversion in Service layer — route stays thin, repository returns raw models
- Use specific exception subclasses — caller can handle different errors differently
- Log before raising exception (first catch only) — ensures traceable error chain
- Descriptive method names with verb prefixes — see conventions.md
- Verify resource existence before mutation — prevents silent failures on missing data

## Don'ts
- Mix business logic and data access — violates single responsibility, makes testing harder
- Return raw ORM models from Routes — exposes internal structure, breaks API contract
- Suppress exceptions (`except: pass`) — hides bugs, makes debugging impossible
- Use generic names like `get()`, `process()` — ambiguous, forces reading implementation to understand intent
- Hard-code DB queries in Service — delegate to Repository for testability and reuse
- Call commit/rollback in Repository — session dependency handles transaction lifecycle
- Use global mutable state — causes race conditions in async context

## New Feature Checklist
1. [ ] Model definition (`app/models/`)
2. [ ] DTO definition (`app/dtos/`)
3. [ ] Repository implementation (`app/repositories/`)
4. [ ] Service implementation (`app/services/`)
5. [ ] Route definition (`app/routes/`)
6. [ ] Alembic migration (`alembic/versions/`)
7. [ ] Tests (`tests/`)
