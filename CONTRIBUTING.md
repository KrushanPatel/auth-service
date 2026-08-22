# Contributing Guide

Thank you for your interest in Auth Microservice! We welcome contributions of all kinds:

- Bug reports
- Feature requests
- Documentation improvements
- Code contributions

---

## Development Setup

### Prerequisites

- **Python**: 3.14+
- **uv**: for dependency management ([install instructions](https://docs.astral.sh/uv/getting-started/installation/))
- **PostgreSQL**: for local development, or use `docker compose up --build` which provisions it for you
- **Docker** (optional): for running the full stack via `docker-compose.yml`

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/auth-microservice.git
cd auth-microservice
```

### 2. Install Dependencies

```bash
uv sync
```

Do not hand-edit `uv.lock` — use `uv add <pkg>` / `uv remove <pkg>` to change dependencies.

### 3. Configure Environment

Copy `.env` and set the required variables (`JWT_SECRET_KEY`, `ALGORITHM`, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`). See `core/config.py` and `core/secrets.py` for what's read.

### 4. Run the Service

```bash
# Directly
uv run uvicorn src.main:app --reload

# Or via Docker (reads .env, healthcheck hits /health)
docker compose up --build
```

### 5. Verify

```bash
curl http://localhost:8000/health
```

---

## Project Structure

```
auth-microservice/
├── pyproject.toml        # Project metadata and tooling config (ruff, mypy)
├── docker-compose.yml
├── Dockerfile
├── alembic/               # Migrations (SQLAlchemy/Alembic present as deps, not yet wired in)
└── src/
    ├── api/v1/            # Routers, request/response schemas
    ├── services/          # Business logic; raises HTTPException
    ├── repositories/      # Parameterized raw SQL only; raises ValueError on invalid data
    ├── db/                # asyncpg pool + fetch_one/fetch_all/execute helpers
    ├── core/              # config, secrets, jwt, security, dependencies
    ├── schemas/           # Pydantic models
    └── tests/             # pytest / pytest-asyncio tests
```

The codebase follows a strict layered flow: `api → services → repositories → db`. See `CLAUDE.md` for the full architecture notes (auth token lifetimes, refresh rotation, cleanup task, etc.) before making changes.

**No ORM.** Despite `sqlalchemy`/`alembic` being dependencies, all queries are raw asyncpg with `$1, $2, ...` params — don't introduce ORM usage without discussing it first.

**Import style:** modules are imported relative to `src/` without a `src.` prefix (e.g. `from core.jwt import ...`), which only resolves when `src/` is the working directory / on the path.

---

## Code Style

We use the following tools to maintain code consistency:

| Tool | Purpose | Config |
|------|---------|--------|
| **Ruff** | Linting, Formatting, Import sorting | `pyproject.toml` |
| **mypy** | Type checking | `pyproject.toml` |

### Running Checks

```bash
uv run ruff format src/
uv run ruff check src/
uv run mypy src/
```

### Style Guidelines

1. **Line width**: 100 characters
2. **Indentation**: 4 spaces
3. **Type hints**: required on new code (mypy is enforced)
4. **Mutable updates**: build `SET` clauses from an explicit `ALLOWED_FIELDS` whitelist (see `repositories/user_repository.py`) rather than accepting arbitrary keys

---

## Testing

`src/tests/test_core` and `src/tests/test_services` are pure unit tests (repositories/DB mocked). `src/tests/test_repositories` and `src/tests/test_api` are integration/e2e tests that need a real Postgres — they get one via `docker-compose.test.yml` and bypass `create_pool()`'s AWS-secret/`ssl="require"` requirement by wiring a local asyncpg pool directly into `db.connection` (see `src/tests/conftest.py`).

```bash
# Start the disposable test database (once per session)
docker compose -f docker-compose.test.yml up -d

# Run all tests
uv run pytest

# Run a single test
uv run pytest src/tests/path/to/test_file.py::test_name
```

Tests use `pytest-asyncio` with `asyncio_mode = "auto"` (see `pyproject.toml`) — no `@pytest.mark.asyncio` decorator needed. Add tests alongside new functionality under `src/tests/`.

---

## Contribution Workflow

### 1. Create a Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/xxx` - New features
- `fix/xxx` - Bug fixes
- `docs/xxx` - Documentation updates
- `refactor/xxx` - Code refactoring

### 2. Make Changes

- Follow the code style guidelines and layered architecture above
- Add tests for new functionality
- Update documentation (`README.md`, `CLAUDE.md`) as needed
- Don't touch adjacent code that isn't part of your change

### 3. Commit Changes

```bash
git add .
git commit -m "feat: add password reset endpoint"
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

---

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Code style (no logic change) |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Tests |
| `chore` | Build/tooling |

### Examples

```bash
git commit -m "feat(auth): add refresh token reuse detection"
git commit -m "fix(jwt): correct jti typing on token decode"
git commit -m "docs(readme): document ruff and mypy tooling"
git commit -m "chore(lint): add ruff/mypy config"
```

---

## Pull Request Guidelines

### PR Title

Use the same format as commit messages.

### PR Description Template

```markdown
## Summary

Brief description of the changes and their purpose.

## Type of Change

- [ ] New feature (feat)
- [ ] Bug fix (fix)
- [ ] Documentation (docs)
- [ ] Refactoring (refactor)
- [ ] Other

## Testing

Describe how to test these changes:
- [ ] Unit tests pass (`uv run pytest`)
- [ ] Manual testing completed

## Related Issues

- Fixes #123
- Related to #456

## Checklist

- [ ] Code follows project style guidelines (`ruff`, `mypy` pass)
- [ ] Tests added for new functionality
- [ ] Documentation updated (if needed)
- [ ] All tests pass
```

---

## Issue Guidelines

### Bug Reports

Please provide:

1. **Environment**
   - Python version
   - OS
   - Whether running locally or via Docker

2. **Steps to Reproduce**
   - Detailed steps
   - Request/response examples (curl, HTTP client)

3. **Expected vs Actual Behavior**

4. **Error Logs** (if any)

### Feature Requests

Please describe:

1. **Problem**: What problem are you trying to solve?
2. **Solution**: What solution do you propose?
3. **Alternatives**: Have you considered other approaches?

---

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## Getting Help

If you have questions, open a GitHub Issue on this repository.

---

Thank you for contributing!
