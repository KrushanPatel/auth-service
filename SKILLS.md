# SKILLS.md — Project Conventions

Conventions and guidelines for working in this repository. Read this before modifying code.

---

## Architecture

Layered architecture. Requests flow top-down; each layer has a single responsibility.

```text
API Routes (src/api/v1/)
    ↓
Services (src/services/)          → business logic, orchestration, HTTPException mapping
    ↓
Repositories (src/repositories/)  → raw SQL only, no business logic
    ↓
DB Session (src/db/session.py)    → thin asyncpg query helpers (fetch_one / fetch_all / execute)
    ↓
AsyncPG Connection Pool (src/db/connection.py)
```

* **`api/v1`** — FastAPI routers, request/response schema wiring, status codes.
* **`core/`** — cross-cutting concerns: config, JWT, hashing, auth dependencies, secrets.
* **`schemas/`** — Pydantic v2 models for request and response validation.
* **`services/`** — business logic; raises `HTTPException` for API-facing errors.
* **`repositories/`** — parameterized SQL queries; never import services or raise API errors (other than validation guards).
* **`db/`** — connection pool lifecycle and session helpers.

---

## Python & Tooling

* **Python 3.14+** (see `.python-version`).
* **uv** is the package manager. `pyproject.toml` is the source of truth; `uv.lock` must stay in sync.
  * `uv sync` — install dependencies.
  * `uv add <pkg>` / `uv remove <pkg>` — manage dependencies (do not hand-edit `uv.lock`).
* Framework: **FastAPI**, server: **Uvicorn**.
* No type-checker or linter is configured yet. Keep code readable and consistent with existing files.

---

## Dependencies & Libraries

| Concern            | Library          | Notes                                             |
| ------------------ | ---------------- | ------------------------------------------------- |
| Web framework      | FastAPI          | Pydantic v2 schemas for request/response          |
| DB driver          | asyncpg          | Async PostgreSQL, connection pool (5–20)          |
| SQL                | raw SQL          | No ORM. Use `$1, $2, ...` parameters              |
| Password hashing   | pwdlib           | Argon2id (`PasswordHash.recommended()`)           |
| JWT                | PyJWT            | HS256                                             |
| Migrations         | alembic          | Installed but not yet configured                  |
| Tests              | pytest           | `pytest-asyncio`, `pytest-cov`, `httpx` (dev)     |

---

## Code Style

* Follow the style of the file you are editing (import grouping, spacing, naming).
* Absolute imports relative to `src/`, **without** the `src.` prefix:
  `from core.jwt import ...`, `from schemas.auth import ...`.
* Do **not** add comments unless asked; the existing code is comment-light.
* Use Pydantic v2:
  * Request models: plain `BaseModel` with `Field(min_length=..., max_length=..., examples=[...])`.
  * Response models: `model_config = ConfigDict(from_attributes=True)` so DB rows can be returned directly.
* Errors:
  * Lower layers raise `ValueError` for invalid tokens / missing records.
  * Services catch and re-raise as `HTTPException` with appropriate status codes (`400`, `401`, `403`, `404`, `409`, `422`).
* Endpoints are declared with `@router.<method>("<path>", response_model=..., status_code=...)`.

---

## Security

* Hash passwords and refresh tokens with **Argon2id** (`core/security.py`).
* Never store plaintext secrets. DB credentials come from env vars (`DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`).
* JWT access tokens: 15 min expiry. Refresh tokens: 7 days, hashed and stored in DB with a `jti`.
* Refresh tokens rotate on every refresh; old tokens are revoked.
* Reuse of a revoked refresh token revokes **all** of the user's tokens.
* Protect endpoints with `Depends(get_current_user)` from `core/dependencies.py`.
* `.env` and AWS ECS task definitions are git-ignored; never commit secrets.

---

## Database

* Raw asyncpg SQL, always parameterized (`$1`, `$2`, ...).
* Use `fetch_one` for single-row SELECT / INSERT / UPDATE ... RETURNING, `fetch_all` for lists, `execute` for writes.
* Column names returned by queries must match response schema field names.
* Dynamic updates (e.g. `users`) use a whitelist (`ALLOWED_FIELDS`) and build the SET clause from validated fields.

---

## Testing

* Tests live under `src/tests/` (pytest with `pytest-asyncio`).
* Run with:
  ```bash
  uv run pytest
  ```
* Write async tests for services/repositories with `@pytest.mark.asyncio`.

---

## Running Locally

```bash
uv sync
uv run src/main.py            # or
uv run uvicorn src.main:app --reload
```

* API docs: `http://localhost:8000/docs` (Swagger), `/redoc` (ReDoc).
* Health check: `GET /health` (includes PostgreSQL version).

---

## Docker / Deployment

* **Local:** `docker compose up --build` (uses `.env`, healthcheck on `/health`).
* **Production:** AWS ECS Fargate via `task-definition.json`; image pushed to ECR.
  * Secrets (`JWT_SECRET_KEY`, `DB_*`) injected from AWS Secrets Manager at runtime.
* Container runs as non-root user (`appuser`), read-only filesystem, resource limits.

---

## Git

* Commit messages use **Conventional Commits**:
  `feat(<scope>): <summary>`, `fix(<scope>): <summary>`, `docs(...): ...`, `chore(...): ...`.
* Scope examples seen in history: `auth`, `users`, `health`, `docker`, `readme`.
* Branch: `main`. Push to `origin/main`.
