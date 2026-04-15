---
inclusion: auto
---

# Project Overview — Necsor

Full-stack web application designed for high throughput, strong concurrency, and fast response times.

## Tech Stack

### Backend (`Backend/`)
- **Language:** Python 3.12
- **Framework:** FastAPI (async, high-performance)
- **Database:** MongoDB (local service, via motor async driver)
- **Cache:** Redis (local service, via redis-py async with hiredis)
- **ODM:** Beanie (async MongoDB ODM built on motor + pydantic)
- **Auth:** JWT (python-jose) + bcrypt (passlib)
- **Config:** pydantic-settings, python-dotenv
- **Logging:** loguru (console + daily rotated file)
- **Testing:** pytest + pytest-asyncio
- **Virtual Env:** `Backend/venv/` (Python 3.12)

### Frontend (`Frontend/`)
- **Runtime:** Node.js 22 LTS (managed via nvm)
- **Framework:** Nuxt 3 (Vue 3, SSR-capable)
- **State:** Pinia (`@pinia/nuxt`)
- **Utilities:** VueUse (`@vueuse/nuxt`)
- **HTTP:** ofetch (Nuxt built-in + composable wrapper)
- **Styling:** SCSS (sass-embedded), global variables via `_variables.scss`
- **Linting:** @nuxt/eslint
- **Package Manager:** npm

## Architecture Principles

1. **Separation of concerns** — API routes, business logic (services), data models, and schemas are in distinct layers.
2. **Async everywhere** — Both backend (FastAPI + motor + redis async) and frontend (Nuxt SSR) are fully async.
3. **Centralized config** — Backend settings in `Backend/app/core/config.py` loaded from `.env`. Frontend runtime config in `nuxt.config.ts` loaded from `.env`.
4. **API versioning** — Backend routes are prefixed with `/api/v1`. New versions can be added as `v2/` without breaking existing clients.
5. **Dependency injection** — FastAPI `Depends()` pattern for DB and cache access via `Backend/app/api/deps.py`.
