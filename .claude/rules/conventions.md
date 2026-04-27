# Naming & Code Style Conventions

## Files & Directories
**How:** Lowercase + underscore (`snake_case`). Suffix by purpose: `*_repository.py`, `*_service.py`, `*_dto.py`

## Folder Convention
**Why:** `dtos/` instead of `schemas/` to avoid terminology conflict with DB schema. Each folder has a single responsibility.
**How:**
| Folder | Purpose |
|---|---|
| `app/routes/` | FastAPI route handlers |
| `app/dtos/` | Pydantic Request/Response DTOs |
| `app/services/` | Business logic |
| `app/repositories/` | DB access (SQLModel) |
| `app/models/` | SQLModel ORM models + base classes |
| `app/core/` | Config, auth, exceptions, utils |
| `alembic/` | DB migrations |
| `tests/` | Test files |

## Domain Directory Structure
**Why:** Matching directory structure between `routes/` and `dtos/` makes file lookup predictable. No guessing where a DTO or route lives.
**How:** `routes/` and `dtos/` use identical domain subdirectories. File names match API path resource name. Sub-resource routes live under the parent domain directory.
```
routes/                          dtos/
├── patient/                     ├── patient/
│   ├── patients.py              │   ├── patients.py
│   └── patients_vitals.py       │   └── patients_vitals.py
├── vital/                       ├── vital/
│   └── vitals.py                │   └── vitals.py
└── inference/                   └── inference/
    └── inference.py                 └── inference.py
```
- `patients_vitals.py` → `GET /patients/{patient_id}/vitals` (sub-resource of patient domain)
- File names match API path resource name (e.g. `patients.py` for `/patients`, `inference.py` for `/inference`)

## Classes (PascalCase)
| Suffix | Usage | Layer | Example |
|---|---|---|---|
| `*Service` | Business logic | Service | `VitalService` |
| `*Repository` | Data access | Repository | `PatientRepository` |
| `*Request` | HTTP 요청 DTO (body) | Route | `VitalUpsertRequest` |
| `*RequestQuery` | HTTP 요청 DTO (query params) | Route | `VitalRequestQuery` |
| `*Response` | HTTP 응답 래퍼 | Route | `VitalUpsertResponse` |
| `*Exception` | Custom exception | Core | `NotFoundException` |

## DTO Convention
**Why:** PRD has no separate response wrapper format. Separate Dto-to-Response conversion adds complexity without benefit in this project scope.
**How:**
- **Service** → `*Response` directly (no separate `*Dto` class)
- **Route** → receives `*Response` from Service, returns as-is
- **Repository** → Entity(Model)
- All DTOs must inherit `app.dtos.base.BaseDto` (never inherit Model classes directly — prevents cross-layer dependency)

## DTO Naming by Usage
| Suffix | Usage | Example |
|---|---|---|
| `*Request` | Request body (POST/PUT) | `PatientCreateRequest` |
| `*RequestQuery` | Query parameters (GET) | `VitalRequestQuery` |
| `*Response` | Response body | `PatientResponse` |

## Query Parameter DTO
**Why:** Centralizes query parameter definition in DTO layer. Route stays thin — no scattered `Query()` declarations across function parameters.
**How:**
- Define fields in `*RequestQuery` DTO (inherits `BaseDto`)
- Apply via `Query(...)` in route function signature
```python
# DTO
class VitalRequestQuery(BaseDto):
    time_from: datetime
    time_to: datetime
    vital_type: VitalType | None = None

# Route
async def get_patient_vitals(
    patient_id: str,
    query: VitalRequestQuery = Query(...),
    session: AsyncSession = Depends(get_session),
) -> VitalResponse:
```

## DTO Alias Convention (External ID Mapping)
**Why:** API JSON contract uses `patient_id`, but internal code uses `patient_external_id` to distinguish from the internal int PK (`Patient.id`). Alias bridges the gap without breaking the API contract.
**How:**
- Request DTOs: `Field(alias="patient_id")` — accepts `patient_id` from JSON, stores as `patient_external_id` internally
- Response DTOs: `Field(serialization_alias="patient_id")` — serializes `patient_external_id` as `patient_id` in JSON output
- Both require `model_config = {"populate_by_name": True}` to allow construction by internal field name
- Service/Repository always use `patient_external_id` parameter name for external identifiers

## BaseDto & Serialization
**Why:** PRD response examples use `"Z"` suffix on all datetime fields. BaseDto handles JSON serialization globally so individual DTOs use plain `datetime` without extra annotations.
**How:**
- `BaseDto(BaseModel)` — base class for all DTOs with `from_attributes=True`.
- `@field_serializer("*")` in BaseDto — `datetime` → ISO format + `"Z"` suffix, `UUID` → string
- DTOs use plain `datetime` fields — BaseDto handles serialization automatically
```python
class BaseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*")
    @classmethod
    def serialize_fields(cls, value: object) -> object:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None).isoformat() + "Z"
        if isinstance(value, UUID):
            return str(value)
        return value

class MyResponse(BaseDto):
    created_at: datetime  # serialized as "2025-12-01T10:00:00Z"
```

## DTO ↔ Entity Conversion
**Why:** Field mapping and value transformation between DTO and Model belong in the DTO layer, not in Service. Models are stable (tied to DB schema), so DTOs depending on Models is acceptable. Models must never depend on DTOs (no reverse dependency).
**How:**
- `to_entity()` — instance method on Request DTO. Creates a new entity for INSERT operations. Accepts internal PK as parameter when FK is needed.
- `update_entity(entity)` — instance method on Request DTO. Updates an existing entity's domain fields for UPDATE operations.
- `from_entity(entity, ...)` — classmethod on Response DTO. Creates a response from an entity. Uses explicit field mapping when DTO field names differ from Entity (alias). When additional parameters are needed, accept entities or value objects directly instead of primitive values — extract fields internally.
- Version increment and optimistic lock checks remain in Service (business logic).
- `updated_at` is handled by `BaseCreatedUpdatedModel` event listener — do not set manually.
```python
# Request DTO — alias separates API JSON key (patient_id) from internal field name (patient_external_id)
class PatientCreateRequest(BaseDto):
    model_config = {"populate_by_name": True}
    patient_external_id: str = Field(alias="patient_id")
    ...
    def to_entity(self) -> Patient:
        return Patient(external_id=self.patient_external_id, ...)

class VitalUpsertRequest(BaseDto):
    model_config = {"populate_by_name": True}
    patient_external_id: str = Field(alias="patient_id")
    ...
    def to_entity(self, patient_id: int) -> Vital:
        return Vital(patient_id=patient_id, ...)  # accepts internal PK as parameter

class PatientUpdateRequest(BaseDto):
    ...
    def update_entity(self, entity: Patient) -> Patient:
        entity.name = self.name
        entity.gender = self.gender
        entity.birth_date = self.birth_date
        return entity

# Response DTO — serialization_alias maps internal field name to JSON output key
class PatientResponse(BaseDto):
    model_config = {"populate_by_name": True}
    patient_external_id: str = Field(serialization_alias="patient_id")
    ...
    @classmethod
    def from_entity(cls, entity: Patient) -> "PatientResponse":
        return cls(patient_external_id=entity.external_id, ...)

class VitalUpsertResponse(BaseDto):
    model_config = {"populate_by_name": True}
    patient_external_id: str = Field(serialization_alias="patient_id")
    ...
    @classmethod
    def from_entity(cls, entity: Vital, patient: Patient) -> "VitalUpsertResponse":
        return cls(patient_external_id=patient.external_id, ...)

# Service — uses DTO conversion, handles business logic only
patient = request.to_entity()
request.update_entity(patient)
patient.version += 1
return PatientResponse.from_entity(patient)
```

```
Route: Request → Service → Response
Service: business logic → Response
Repository: DB access → Entity
```

```python
# Service — returns Response directly
async def upsert_vital(self, request: VitalUpsertRequest) -> VitalUpsertResponse: ...

# Service — UPSERT처럼 Route에 부가 정보(생성 여부)가 필요한 경우 tuple 반환 허용
async def upsert_vital(self, request: VitalUpsertRequest) -> tuple[VitalUpsertResponse, bool]: ...

# Route — pass-through, exclude_none으로 null 필드 제거
@vitals_router.post("", response_model=VitalUpsertResponse, response_model_exclude_none=True)
async def upsert_vital(request: VitalUpsertRequest, ...) -> VitalUpsertResponse:
    return await service.upsert_vital(request)

# Route — UPSERT처럼 INSERT/UPDATE 상태코드 분기가 필요한 경우 허용
@vitals_router.post("", response_model=VitalUpsertResponse, response_model_exclude_none=True)
async def upsert_vital(request: VitalUpsertRequest, response: Response, ...) -> VitalUpsertResponse:
    result, created = await service.upsert_vital(request)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return result
```

## Response Null 필드 제외
**Why:** 값이 없는(None) 필드가 `null`로 응답에 포함되면 API 계약이 불명확해진다. 필드 자체를 제외하여 깔끔한 응답을 보장한다.
**How:**
- 모든 라우트 데코레이터에 `response_model_exclude_none=True` 적용
- DTO에서 Optional 필드는 `field: Type | None = None`으로 선언
```python
@router.get("", response_model=MyResponse, response_model_exclude_none=True)
async def get_items(...) -> MyResponse: ...
```

## Functions & Methods (snake_case)
- Verb prefix required
- Naming rules differ by layer (see below)

### Repository (Data Access Layer)
**Why:** Method name alone tells you the return type and not-found behavior. Caller knows whether to check for None.
**How:**
| Prefix | Return | On not found | Usage |
|---|---|---|---|
| `find_one_` | `T \| None` | Returns `None` | Single item by condition |
| `find_` | `list[T]` | Returns `[]` | Multiple items or paginated list |
| `get_` | `T` | Raises exception | Single item guaranteed to exist |
| `create_` | `T` | — | Create resource |
| `update_` | `T` | — | Modify resource |
| `delete_` | `None` | — | Remove resource |
| `count_` | `int` | — | Count query |

### Service / Route (Business Logic / API Layer)
**Why:** Service focuses on business meaning, not return characteristics. Type hints express nullability.
**How:** Use `get_` for all reads. Nullable expressed via type hints.
| Prefix | Usage |
|---|---|
| `get_` | Read (single and list). Distinguish `T \| None` vs `list[T]` via return type |
| `create_` | Create resource |
| `update_` | Modify resource |
| `delete_` | Remove resource |

```python
async def get_patient(self, patient_external_id: str) -> PatientResponse:           # raises if not found
async def get_patient_vitals(self, patient_external_id: str, ...) -> VitalResponse:  # returns list
async def upsert_vital(self, request: VitalUpsertRequest) -> VitalUpsertResponse:
```

## Method Ordering in Class
**Why:** Predictable location when navigating code.
**How:**
1. public → protected (`_`) → private (`__`)
2. Within each group: Read(Multiple) → Read(Single) → Create → Update → Delete

## Variables & Constants
```python
# Variables: snake_case
patient_external_id = "P00001234"
vital_count = 10

# Constants: UPPER_SNAKE_CASE
VITAL_RISK_TIME_WINDOW_HOURS = 24
MAX_RISK_RULES = 3
```

## Type Hints
**Why:** Catch runtime errors at IDE/type-checker level. Improves readability.
**How:**
- Required for all function parameters and return values
- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Use `list[T]`, `dict[str, T]` instead of `List[T]`, `Dict[str, T]`

## Import Order (ruff auto-sorts, but follow when writing manually)
```python
# 1. Standard library
# 2. Third-party libraries
# 3. App internals (from app.*)
# One blank line between groups, two blank lines after all imports
```

## Docstring (Korean)
```python
async def get_patient_vitals(self, patient_external_id: str, ...) -> VitalResponse:
    """
    환자 Vital 데이터 조회

    Args:
        patient_external_id: 환자 외부 식별자

    Returns:
        VitalResponse: Vital 데이터 목록

    Raises:
        NotFoundException: 환자가 없을 때
    """
```

## Inline Comments
- Korean language
- Explain **why**, not what

```python
# 등록된 환자만 Vital 입력 가능
patient = await self.patient_repo.find_one_by_external_id(request.patient_external_id)
if not patient:
    raise NotFoundException(message=f"Patient {request.patient_external_id} not found")
```

## Lint & Format
- `ruff check .` — lint (B008 ignored for FastAPI `Depends()`)
- `ruff format .` — format
- isort: 2 blank lines after imports, combined as-imports

## Forbidden Patterns
**Why:** Each pattern has caused production incidents.
- `except Exception: pass` — swallowed exceptions make root cause untraceable
- Mutable default argument: `def f(items=[])` — shared state between calls
- `print()` debug code in commits — pollutes production logs, use logger
- Magic numbers — unclear meaning, extract to constants
