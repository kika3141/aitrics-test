# Vital Risk API

병원 환자의 Vital Signs(생체징후) 데이터를 관리하고, 규칙 기반 위험도 스코어링을 제공하는 REST API입니다.

## 도메인 — Vital Signs

병원에서는 환자의 상태 변화를 모니터링하기 위해 다양한 생체징후 데이터를 실시간 수집합니다.
본 프로젝트에서 다루는 6개 Vital 유형은 다음과 같습니다.

| Vital Type | 설명 | 단위 | 비고 |
|---|---|---|---|
| HR | 심박수 (Heart Rate) | bpm | 위험도 평가 대상 (> 120) |
| RR | 호흡수 (Respiratory Rate) | breaths/min | |
| SBP | 수축기 혈압 (Systolic Blood Pressure) | mmHg | 위험도 평가 대상 (< 90) |
| DBP | 이완기 혈압 (Diastolic Blood Pressure) | mmHg | |
| SpO2 | 산소포화도 (Oxygen Saturation) | % | 위험도 평가 대상 (< 90) |
| BT | 체온 (Body Temperature) | C | |

Vital 데이터는 시간에 따라 수집되는 시계열(Time-series) 데이터이며, 의료 AI 모델의 입력으로 사용됩니다.

## 기술 스택

| 항목 | 기술 |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLModel (Pydantic v2 + SQLAlchemy) |
| Database | PostgreSQL 16 + asyncpg |
| Migration | Alembic |
| Package | uv |
| Lint/Format | ruff |
| Test | pytest + pytest-asyncio + aiosqlite |
| Container | Docker Compose |

## 실행 방법

### Docker Compose (권장)

```bash
./scripts/setup.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
1. `.env.example` → `.env` 복사
2. Docker 이미지 빌드
3. PostgreSQL + App 컨테이너 실행
4. Alembic 마이그레이션 (`alembic upgrade head`)
5. API 서버 헬스체크

완료 후:
- API: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8000/docs

종료:
```bash
docker compose down
```

### 로컬 실행

```bash
docker compose up db -d                  # PostgreSQL 시작
cp .env.example .env                     # 환경변수 설정
uv venv && uv pip install -e ".[dev]"    # 의존성 설치
source .venv/bin/activate
alembic upgrade head                     # DB 마이그레이션
uvicorn app.main:app --reload            # 서버 시작
```

## 환경변수

| 변수 | 설명 | 기본값 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 접속 URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/vitalrisk` |
| `API_TOKEN` | Bearer 인증 토큰 | `your-secret-token` |
| `VITAL_RISK_TIME_WINDOW_HOURS` | 위험도 분석 시간 범위(시간) | `24` |
| `LOG_LEVEL` | 로그 레벨 | `DEBUG` |

## API 명세

모든 API는 `Authorization: Bearer <API_TOKEN>` 헤더가 필수입니다.
인증 실패 시 `401 Unauthorized`를 반환합니다.

Swagger UI: http://localhost:8000/docs

### 환자 관리

#### POST /api/v1/patients — 환자 등록

```json
// Request
{
  "patient_id": "P00001234",
  "name": "홍길동",
  "gender": "M",
  "birth_date": "1975-03-01"
}

// Response 201
{
  "patient_id": "P00001234",
  "name": "홍길동",
  "gender": "M",
  "birth_date": "1975-03-01",
  "version": 1,
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-01T10:00:00Z"
}
```

#### PUT /api/v1/patients/{patient_id} — 환자 수정 (Optimistic Lock)

```json
// Request
{
  "name": "홍길동",
  "gender": "M",
  "birth_date": "1975-03-01",
  "version": 1
}

// Response 200 — version이 증가하여 반환
// Response 409 — version mismatch 시
```

### Vital 데이터

#### POST /api/v1/vitals — Vital UPSERT (Optimistic Lock)

```json
// Request
{
  "patient_id": "P00001234",
  "recorded_at": "2025-12-01T10:15:00Z",
  "vital_type": "HR",
  "value": 110.0,
  "version": 1
}

// Response 201 (INSERT) / 200 (UPDATE)
// Response 409 — UPDATE 시 version mismatch
// Response 404 — 미등록 환자
```

- 복합 식별자: `(patient_id, recorded_at, vital_type)`
- INSERT: version 1부터 시작
- UPDATE: version 검증 후 increment
- Vital Type: `HR`, `RR`, `SBP`, `DBP`, `SpO2`, `BT`

#### GET /api/v1/patients/{patient_id}/vitals — Vital 조회

Query Parameters:
- `time_from` (필수): 시작 시각
- `time_to` (필수): 종료 시각
- `vital_type` (선택): Vital 유형 필터

```json
// Response 200
{
  "patient_id": "P00001234",
  "items": [
    { "recorded_at": "2025-12-01T10:15:00Z", "value": 110.0 }
  ]
}
```

### Inference

#### POST /api/v1/inference/vital-risk — 위험도 분석

```json
// Request
{ "patient_id": "P00001234" }

// Response 200
{
  "patient_id": "P00001234",
  "risk_level": "HIGH",
  "triggered_rules": ["HR > 120", "SBP < 90", "SpO2 < 90"],
  "vital_averages": { "HR": 135.2, "SBP": 82.5, "SpO2": 87.3 },
  "data_points_analyzed": 48,
  "time_range": {
    "from": "2025-11-30T10:20:00Z",
    "to": "2025-12-01T10:20:00Z"
  },
  "evaluated_at": "2025-12-01T10:20:00Z"
}
```

위험 규칙:

| 조건 | 의미 |
|---|---|
| 평균 HR > 120 | 위험 증가 |
| 평균 SBP < 90 | 위험 증가 |
| 평균 SpO2 < 90 | 위험 증가 |

스코어링: 0개 충족 → `LOW` / 1~2개 → `MEDIUM` / 3개 → `HIGH`

## DB 스키마

### patient 테이블

```sql
CREATE TABLE patient (
    id            SERIAL       PRIMARY KEY,
    version       INTEGER      NOT NULL DEFAULT 1,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    external_id   VARCHAR(20)  NOT NULL,
    name          VARCHAR(100) NOT NULL,
    gender        VARCHAR(1)   NOT NULL,
    birth_date    DATE         NOT NULL,
    CONSTRAINT uix_patient_external_id UNIQUE (external_id)
);
```

### vital 테이블

```sql
CREATE TABLE vital (
    id            SERIAL       PRIMARY KEY,
    version       INTEGER      NOT NULL DEFAULT 1,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    patient_id    INTEGER      NOT NULL REFERENCES patient(id),
    recorded_at   TIMESTAMP    NOT NULL,
    vital_type    VARCHAR      NOT NULL,
    value         FLOAT        NOT NULL,
    CONSTRAINT uix_vital_patient_id_recorded_at_vital_type
        UNIQUE (patient_id, recorded_at, vital_type)
);

CREATE INDEX ix_vital_patient_id ON vital (patient_id);
CREATE INDEX ix_vital_vital_type ON vital (vital_type);
```

### ER Diagram

```
patient (1) ──── (N) vital
  id (PK)              id (PK)
  version              version
  external_id (UQ)     patient_id (FK → patient.id)
  name                 recorded_at
  gender               vital_type
  birth_date           value
  created_at           created_at
  updated_at           updated_at

UNIQUE(patient_id, recorded_at, vital_type)
```

## Optimistic Lock 설계

### 왜 Optimistic Lock인가?

의료 데이터는 동시 수정 가능성이 있으나, 충돌 빈도는 낮습니다.
Pessimistic Lock(SELECT FOR UPDATE)은 DB 행 잠금으로 대기가 발생하지만,
Optimistic Lock은 잠금 없이 동작하여 더 높은 동시성을 제공합니다.

### 동작 원리

모든 엔티티에 `version` 컬럼이 존재합니다 (`BaseIntIDModel`에서 제공, 기본값 1).

```
Client                           Server                         DB
  │                                │                              │
  │  PUT /patients/P001            │                              │
  │  { version: 1, name: "김" }    │                              │
  │ ─────────────────────────────> │                              │
  │                                │  SELECT ... WHERE            │
  │                                │  external_id = 'P001'        │
  │                                │ ────────────────────────────> │
  │                                │  patient.version = 1         │
  │                                │ <──────────────────────────── │
  │                                │                              │
  │                                │  request.version(1) ==       │
  │                                │  db.version(1) → OK          │
  │                                │                              │
  │                                │  UPDATE patient SET           │
  │                                │  version=2, name='김' ...    │
  │                                │ ────────────────────────────> │
  │                                │                              │
  │  200 OK { version: 2 }        │                              │
  │ <───────────────────────────── │                              │
```

version mismatch 시:

```
Client A: PUT { version: 1 }  → version 1 == 1 → OK → version 2로 업데이트
Client B: PUT { version: 1 }  → version 1 != 2 → 409 Conflict
```

### 적용 지점

#### 1. 환자 수정 — `PUT /api/v1/patients/{patient_id}`

`app/services/patient_service.py:36`:
```python
if patient.version != request.version:
    raise ConflictException(
        message=f"Version conflict: expected {patient.version}, got {request.version}"
    )
request.update_entity(patient)
patient.version += 1
```

#### 2. Vital UPSERT (UPDATE 시) — `POST /api/v1/vitals`

`app/services/vital_service.py:65`:
```python
if existing.version != request.version:
    raise ConflictException(
        message=f"Version conflict: expected {existing.version}, got {request.version}"
    )
request.update_entity(existing)
existing.version += 1
```

INSERT 시에는 충돌 검증 없이 `version = 1`로 생성됩니다.

## 아키텍처

### Layered Architecture

단일 서비스 내에서 계층을 분리하여 관심사를 격리합니다.
의존 방향은 단방향(Route → Service → Repository)이며, 역방향 의존은 금지합니다.

```
Request
  │
  ▼
Route (routes/)          요청 검증, 응답 반환만 담당
  │
  ▼
Service (services/)      비즈니스 로직, 예외 처리, Entity↔DTO 변환
  │
  ▼
Repository (repos/)      DB 접근만 담당, commit/rollback 하지 않음
  │
  ▼
Database (PostgreSQL)    Session-per-request, 자동 commit/rollback
```

### 주요 설계 결정

| 결정 | 이유 |
|---|---|
| **SQLModel** | Pydantic v2 + SQLAlchemy 기반 ORM. 모델은 DB 전용, DTO는 BaseDto 기반으로 완전 분리 |
| **Session-per-request** | FastAPI Dependency로 트랜잭션 관리. Service/Repository에 commit/rollback 코드 없음 |
| **BaseEnum + VARCHAR** | PostgreSQL enum은 ALTER TYPE 필요 — VARCHAR 저장으로 코드 변경만으로 enum 추가/제거 가능 |
| **Base Pattern** | 도메인 필드(`*Base`)와 인프라 필드(PK, version, timestamp)를 분리하여 테이블 모델을 조합 방식으로 구성 |
| **Naive UTC datetime** | timezone 정보 없이 UTC 가정 — 온프레미스 환경에서 일관성 확보 |
| **Bearer Token** | 과제 범위에 맞춘 단순 인증 (JWT 미적용) |

## 프로젝트 구조

```
app/
├── main.py                          # FastAPI 앱 엔트리
├── core/                            # 설정, 인증, 예외, 유틸
│   ├── config.py                    # 환경변수 (pydantic-settings)
│   ├── auth.py                      # Bearer Token 인증
│   ├── database.py                  # 세션 관리
│   ├── enums.py                     # BaseEnum, Gender, etc.
│   ├── error_code.py                # 에러 코드 정의
│   ├── exceptions.py                # 커스텀 예외 클래스
│   └── utils.py                     # 유틸리티
├── models/                          # SQLModel ORM 모델
│   ├── base.py                      # BaseSQLModel, BaseIntIDModel
│   ├── patient.py                   # Patient 모델
│   └── vital.py                     # Vital 모델 + VitalType enum
├── dtos/                            # Request/Response DTO
│   ├── base.py                      # BaseDto (datetime/UUID 직렬화)
│   ├── patient/
│   │   ├── patients.py              # 환자 등록/수정 DTO
│   │   └── patients_vitals.py       # 환자 Vital 조회 DTO
│   ├── vital/
│   │   └── vitals.py                # Vital UPSERT DTO
│   └── inference/
│       └── inference.py             # 위험도 분석 DTO
├── repositories/                    # DB 접근 계층
│   ├── patient_repository.py
│   └── vital_repository.py
├── services/                        # 비즈니스 로직 계층
│   ├── patient_service.py
│   ├── vital_service.py
│   └── inference_service.py
└── routes/                          # API 라우트 계층
    ├── patient/
    │   ├── patients.py              # POST, PUT /patients
    │   └── patients_vitals.py       # GET /patients/{id}/vitals
    ├── vital/
    │   └── vitals.py                # POST /vitals
    └── inference/
        └── inference.py             # POST /inference/vital-risk

alembic/                             # DB 마이그레이션
tests/                               # 테스트
scripts/
└── setup.sh                         # 원클릭 셋업 스크립트
```

## 테스트

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## Claude 활용 기록

본 프로젝트는 Claude Code (claude-opus-4-6)를 활용하여 개발했습니다.
상세 활용 기록은 `CLAUDE.md`에 기록되어 있습니다.
