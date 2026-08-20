# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Commands

* Install deps: `uv sync` (do not hand-edit `uv.lock`; use `uv add <pkg>` / `uv remove <pkg>`).
* Run dev server: `uv run uvicorn src.main:app --reload` (or `uv run src/main.py`).
* Run via Docker: `docker compose up --build` (reads `.env`, healthcheck hits `/health`).
* Run all tests: `uv run pytest`.
* Run a single test: `uv run pytest src/tests/path/to/test_file.py::test_name` (tests use `pytest-asyncio`, `asyncio_mode = "auto"`). Repository/API tests need Postgres: `docker compose -f docker-compose.test.yml up -d` first.
* Lint: `uv run ruff check .`. Format check: `uv run ruff format --check .` (apply with `uv run ruff format .`).
* Type-check: `uv run mypy src`.
* Migrations: `uv run alembic upgrade head` / `uv run alembic downgrade base`; new revision: `uv run alembic revision -m "..."`.
* CI (`.github/workflows/ci.yml`) runs ruff check, ruff format --check, mypy, an alembic upgrade+downgrade round-trip, then pytest, all against a `postgres:16-alpine` service container.

## Architecture

Strict layered flow, top to bottom:

```
api/v1/*.py (routers, request/response schemas)
  → services/*.py       (business logic; raises HTTPException)
    → repositories/*.py (parameterized raw SQL only; raises ValueError on invalid data)
      → db/session.py   (fetch_one / fetch_all / execute helpers)
        → db/connection.py (asyncpg pool; module-level singleton created/closed in main.py's lifespan)
```

* **No ORM for queries.** SQLAlchemy is a dependency only for Alembic's async engine (`alembic/env.py`) — all application queries are raw asyncpg with `$1, $2, ...` params (see `repositories/`). Schema changes go through Alembic migrations in `alembic/versions/`.
* **Import style:** modules are imported relative to `src/` without a `src.` prefix (e.g. `from core.jwt import ...`, not `from src.core.jwt import ...`) — this only resolves when `src/` is the working directory / on the path (as uvicorn and pytest are invoked here).
* **Auth tokens** (`core/jwt.py`, PyJWT, HS256): access tokens expire in 15 min; refresh tokens in 7 days and carry a `jti`, hashed with Argon2id (`core/security.py`, same hasher used for user passwords) before being stored via `repositories/refresh_token_repository.py`. Password reset tokens are a separate, non-JWT scheme (see below).
* **Refresh rotation & reuse detection** (`services/refresh_token_service.py`): every `/api/v1/auth/refresh` call validates the token's `jti` against the DB, issues a new access+refresh pair, and revokes the old one. Attempting to reuse an already-revoked token revokes *all* refresh tokens for that user.
* **Password reset** (`services/password_reset_service.py`, `password_resets` table): tokens are a random `secrets.token_urlsafe(32)` string — not a JWT — hashed with SHA-256 (`core/security.py:hash_reset_token`, deterministic so it can be looked up by exact match; unlike Argon2id, which salts per call). This matches the pre-existing `password_resets` table's schema (no `jti` column) rather than the refresh-token pattern. `/api/v1/auth/forgot-password` always returns the same generic response regardless of whether the email is registered (no user enumeration); it logs the raw reset token server-side rather than emailing it, since no email delivery is wired up yet. `/api/v1/auth/reset-password` validates the single-use token, updates the password, and revokes all of that user's refresh tokens.
* **Background cleanup:** `cleanup_task()` in `refresh_token_service.py` runs as an `asyncio` task started in `main.py`'s lifespan, deleting expired refresh tokens and expired password reset tokens once per hour.
* **Config/secrets:** `core/config.py` loads `JWT_SECRET_KEY`/`ALGORITHM` via `python-dotenv`. `core/secrets.py`'s `get_db_secret()` reads `DB_USERNAME`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`/`DB_NAME` directly from the environment (in ECS these are injected by Secrets Manager into the container env — the app does not call boto3 itself).
* **Mutable updates** (e.g. `PATCH /api/v1/users`) build their SQL `SET` clause from an `ALLOWED_FIELDS` whitelist in `repositories/user_repository.py` rather than accepting arbitrary keys.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.