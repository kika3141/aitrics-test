# Exception Handling

## Logging Strategy
**Why:** Duplicate logging across layers creates noise and makes tracing harder. Log once at the point of first catch where you have the most context.
**How:**
- Raw exceptions (first catch): log the error, then raise as `ServerException`
- `AppException` subclasses (already converted): do NOT log again — just re-raise
- Never log the same exception at multiple layers

## Exception Hierarchy
**Why:** Custom exception base class (`AppException`) decouples from FastAPI's `HTTPException`. Global exception handlers convert to JSON response uniformly.
**How:** All custom exceptions inherit `AppException`. Each subclass sets `message`, `err_code`, and `status_code`.
```python
class AppException(Exception):
    def __init__(self, message, err_code, status_code): ...

class NotFoundException(AppException):       # 404
class ConflictException(AppException):        # 409
class UnauthorizedException(AppException):    # 401
class ServerException(AppException):          # 500
```

## Error Codes
**Why:** Structured error codes allow clients to handle specific errors programmatically without parsing message strings.
**How:** `ErrorCode` enum in `app/core/error_code.py`. Domain-specific error codes inherit from `ErrorCode`.
```python
class ServerErrorCode(ErrorCode):
    SERVER_ERROR = "SERVER_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    ...
```

## Global Exception Handlers
**Why:** Centralized exception-to-response conversion. Services throw exceptions, handlers format the HTTP response.
**How:** Registered in `main.py` via `app.add_exception_handler()`.
```python
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

## Error Response Format
```json
{
  "success": false,
  "message": "Resource not found",
  "err_code": "NOT_FOUND"
}
```

## Usage Examples
```python
# Resource not found
if not patient:
    raise NotFoundException(message=f"Patient {patient_id} not found")

# Version conflict (Optimistic Lock)
if patient.version != request.version:
    raise ConflictException(
        message=f"Version conflict: expected {patient.version}, got {request.version}"
    )
```

## Selection Guide
| Situation | Exception | Status Code |
|---|---|---|
| Resource not found | `NotFoundException` | 404 |
| Version mismatch (Optimistic Lock) | `ConflictException` | 409 |
| Auth failure | `UnauthorizedException` | 401 |
| Unknown server error | `ServerException` | 500 |
| Validation failure | (handled by FastAPI) | 422 |

## Service Exception Pattern
**Why:** Re-logging converted exceptions creates noise. Only unconverted (raw) exceptions need logging because they represent unexpected failures.
**How:**
```python
try:
    # business logic
    ...
except AppException:
    raise  # already converted — no logging
except Exception as e:
    logging.exception(f"Failed to upsert vital: {request.patient_id} - {str(e)}")
    raise ServerException(message="Failed to upsert vital")
```
