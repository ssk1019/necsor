---
inclusion: fileMatch
fileMatchPattern: "Backend/**"
---

# Backend Development Guide

## Directory Structure

```
Backend/
├── app/
│   ├── api/                  # HTTP layer
│   │   ├── deps.py           # Shared FastAPI dependencies (get_db, get_cache)
│   │   └── v1/
│   │       ├── router.py     # Aggregates all v1 endpoint routers
│   │       └── endpoints/    # One file per resource (health.py, users.py, etc.)
│   ├── core/                 # Cross-cutting infrastructure
│   │   ├── config.py         # Settings singleton (pydantic-settings from .env)
│   │   ├── database.py       # MongoDB + Redis connect/close/get helpers
│   │   ├── logging.py        # loguru setup
│   │   └── security.py       # JWT create/decode, password hash/verify
│   ├── middleware/            # Custom ASGI middleware
│   ├── models/               # MongoDB document models (Beanie / Pydantic)
│   │   └── base.py           # TimestampMixin (created_at, updated_at)
│   ├── schemas/              # Pydantic request/response schemas
│   │   └── common.py         # ResponseBase[T], PaginatedResponse[T]
│   ├── services/             # Business logic (one file per domain)
│   ├── utils/                # Shared helpers
│   │   └── cache.py          # cache_get / cache_set / cache_delete
│   └── main.py               # App factory + lifespan (startup/shutdown)
├── tests/                    # pytest test files
├── .env                      # Local environment variables (not committed)
├── .env.example              # Template for .env
└── requirements.txt          # Pinned dependencies
```

## Conventions

- **Adding a new resource:**
  1. Create model in `models/` (extend TimestampMixin if needed)
  2. Create schemas in `schemas/` (request + response)
  3. Create service in `services/` (business logic, DB queries)
  4. Create endpoint in `api/v1/endpoints/`
  5. Register router in `api/v1/router.py`

- **Database access:** Always use `Depends(get_db)` or `Depends(get_cache)` from `api/deps.py`. Never import database globals directly in endpoints.

- **Response format:** Wrap responses with `ResponseBase[T]` or `PaginatedResponse[T]` from `schemas/common.py`.

- **Environment variables:** Add new vars to both `.env` and `.env.example`, and add the field to `core/config.py` Settings class.

## Running

**Important:** Must `cd Backend` first. On Windows PowerShell, use `.\venv\Scripts\` prefix (not `Backend\venv\Scripts\` from root — PowerShell misinterprets it as a module import).

```powershell
# Activate venv (from Backend/)
.\venv\Scripts\Activate.ps1

# Start dev server (auto-reload)
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

# Or if venv is activated:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
```

**Prerequisites:** Local MongoDB and Redis services must be running before startup.

## Key Dependencies

| Package | Purpose |
|---------|---------|
| fastapi 0.115.12 | Web framework |
| uvicorn 0.34.2 | ASGI server |
| motor 3.7.1 | Async MongoDB driver |
| beanie 1.29.0 | MongoDB ODM |
| redis 5.3.0 | Async Redis client (with hiredis) |
| pydantic-settings 2.9.1 | Config from env |
| python-jose 3.4.0 | JWT tokens |
| passlib 1.7.4 | Password hashing (bcrypt) |
| loguru 0.7.3 | Logging |
