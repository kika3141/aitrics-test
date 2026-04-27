# Model Patterns

## Naming Convention
**Why:** Ensures consistent index/constraint names in Alembic autogenerate. Prevents manual naming mistakes.
**How:** Apply naming_convention dict to SQLModel metadata.
```python
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uix_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
```
- Unique constraints: use `UniqueConstraint(..., name="uix_...")` in `__table_args__` (not `unique=True` on Field)

## BaseSQLModel
**Why:** Prevents manual tablename errors. Auto-converts PascalCase → snake_case for consistency.
**How:** `@declared_attr` derives tablename from class name.
```python
class BaseSQLModel(SQLModel):
    @declared_attr
    def __tablename__(cls) -> str:
        return underscore(cls.__name__)  # Patient → patient
```

## BaseIntIDModel
**Why:** All tables use auto-increment PK and optimistic lock (version). Centralizes common infrastructure fields.
**How:** Inherits `BaseSQLModel`, provides `id` + `version`.
```python
class BaseIntIDModel(BaseSQLModel):
    """Auto-increment 정수 PK + optimistic lock"""
    id: int | None = Field(default=None, primary_key=True)
    version: int = Field(default=1)
```

## Base Model Classes (Mixins)
**Why:** Independent mixins allow flexible composition. Not all models need timestamps or the same PK type.
**How:** Each mixin inherits from SQLModel directly (not BaseSQLModel). Combined in table models.

```python
class BaseCreatedUpdatedModel(SQLModel):
    """created_at + updated_at with before_update event for auto-refresh"""
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP"), "nullable": False},
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP"), "nullable": False},
    )

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, "before_update")
        def receive_before_update(mapper, connection, target):
            target.updated_at = utcnow()

class BaseCreatedModel(SQLModel):
    """created_at only"""
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP"), "nullable": False},
    )

class DeletedBase(SQLModel):
    """Soft delete support"""
    deleted_at: datetime | None = Field(default=None)
```

## Base Pattern (`*Base`)
**Why:** Separates domain fields (business meaning) from row management (infrastructure: PK, version, timestamps, tablename).
**How:** Define domain fields in `*Base(SQLModel)`. Business identifiers (e.g. `external_id`) are domain fields — include in Base. version is provided by BaseIntIDModel since all tables require optimistic lock.

```python
# Domain fields (business identifiers included, row management excluded)
class PatientBase(SQLModel):
    external_id: str = Field(max_length=20)
    name: str = Field(max_length=100)
    gender: Gender = Field(
        sa_column=Column(ChoiceType(Gender, impl=String()), nullable=False)
    )
    birth_date: date

# Table model = domain + row management (BaseIntIDModel provides id, version)
class Patient(PatientBase, BaseCreatedUpdatedModel, BaseIntIDModel, table=True):
    __table_args__ = (UniqueConstraint("external_id", name="uix_patient_external_id"),)
```

## FK Convention
**Why:** Child tables must reference parent's internal PK (int) as FK to enforce referential integrity and optimize JOIN performance. Using external identifiers (str) as FK violates normalization.
**How:**
- Child model FK references parent's `id` (int PK): `Field(foreign_key="parent_table.id")`
- External identifiers (e.g. `external_id`) exist only as domain fields on the parent model
- Repository accepts external identifier as parameter and JOINs to parent table internally
```python
# Vital은 Patient.id(int PK)를 FK로 참조
class VitalBase(SQLModel):
    patient_id: int = Field(foreign_key="patient.id", index=True)
    ...

# Repository — 외부 식별자로 받아 Patient JOIN 조회
async def find_by_patient_and_time_range(
    self, patient_external_id: str, ...
) -> list[Vital]:
    statement = (
        select(Vital)
        .join(Patient, Vital.patient_id == Patient.id)
        .where(Patient.external_id == patient_external_id, ...)
    )
```

## BaseEnum
**Why:** PostgreSQL native enum requires ALTER TYPE for add/remove — complex migration. VARCHAR storage allows code-only changes.
**How:** Inherit `BaseEnum(str, Enum)`. `_missing_` for case-insensitive lookup. Use `ChoiceType(EnumClass, impl=String())` from sqlalchemy_utils to store as VARCHAR while preserving Python enum type safety.

```python
class BaseEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            upper_value = value.upper()
            if upper_value in cls.__members__:
                return cls.__members__[upper_value]
        raise ValueError(f"Invalid {cls.__name__}: {value}")
```

Usage in model:
```python
from sqlalchemy_utils import ChoiceType

vital_type: VitalType = Field(
    sa_column=Column(ChoiceType(VitalType, impl=String()), nullable=False, index=True)
)
```

## Column Ordering
**Why:** Consistent table structure. Model definition, migration file, and SQL DDL all read in the same order.
**How:**
1. `id` — PK (if exists)
2. `status` — enum (if exists)
3. `created_at`, `updated_at` — timestamps
4. Broad FK — parent entity (`user_id`, `patient_id`)
5. Narrow FK — child/related entity
6. Broad fields — general (`type`, `name`, `count`)
7. Narrow fields — detail (`bio`, `metadata`, JSONB)

## Migration
**Why:** Schema change history. Without downgrade, rollback is impossible.
**How:**
- Auto-generate: `alembic revision --autogenerate -m "description"`
- Always implement downgrade function (`pass` forbidden)
- Large table indexes: `postgresql_concurrently=True` with `disable_ddl_transaction`
- Import all model files in `alembic/env.py` so autogenerate detects all tables

## Session / Transaction
**Why:** No transaction code in service/repository — managed at infrastructure level (FastAPI Dependency). Leverages SQLAlchemy implicit transaction. Can upgrade to autocommit + @with_transaction decorator for optimization.
**How:**
- Session-per-request via FastAPI Dependency (`get_session`)
- 1 request = 1 session = 1 transaction
- Auto commit on success, auto rollback on exception
- Service/Repository do not call commit/rollback
- Use `session.exec()` not `session.execute()` (SQLModel idiom)

## Critical Rules
- **No lazy loading** — always use explicit JOINs
- Relationship data: manual JOIN + manual mapping to prevent N+1
