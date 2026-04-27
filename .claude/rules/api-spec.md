# API Spec

## Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/patients | Register patient |
| PUT | /api/v1/patients/{patient_id} | Update patient (optimistic lock) |
| POST | /api/v1/vitals | Vital UPSERT (optimistic lock) |
| GET | /api/v1/patients/{patient_id}/vitals | Query vitals (from, to, vital_type?) |
| POST | /api/v1/inference/vital-risk | Calculate risk score |

## Auth
**Why:** All APIs handle sensitive medical data. Simple Bearer token for this project scope (not JWT).
**How:**
- All APIs require `Authorization: Bearer <token>`
- Auth failure: 401 Unauthorized
- Token managed via env var `API_TOKEN`

## Optimistic Lock (required at 2 points)
**Why:** Ensures data integrity on concurrent modifications. No lock waiting (unlike pessimistic lock) — immediate 409 on conflict, better performance.
**How:**
1. **PUT /patients/{id}**: request.version != db.version → 409 Conflict
2. **POST /vitals**: on UPDATE, request.version != db.version → 409 Conflict
   - Composite identifier: `(patient_id, recorded_at, vital_type)` — `patient_id` here is the internal FK (int), resolved via external ID JOIN
   - INSERT if not exists (version starts at 1)
   - UPDATE if exists (version check required)

## Vital Types
HR, RR, SBP, DBP, SpO2, BT

## Inference Rules
**Why:** Simplified rule-based risk scoring for hospital vital signs monitoring. Evaluates patient condition from time-windowed vital data averages.
**How:**
- Mean HR > 120 → risk increased
- Mean SBP < 90 → risk increased
- Mean SpO2 < 90 → risk increased
- 0 triggered: LOW / 1-2: MEDIUM / 3: HIGH
- Time window: env var `VITAL_RISK_TIME_WINDOW_HOURS` (default 24)

## Vital Query Parameters
- `from` (required): start datetime
- `to` (required): end datetime
- `vital_type` (optional): filter by type
