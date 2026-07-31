# Auth Microservice

A lightweight, production-ready authentication microservice built with **FastAPI**, containerized with **Docker**. Provides user registration, login, token issuance/refresh, and route protection via JWT.

## Features

- User registration & login
- Password hashing with `bcrypt` (via `passlib`)
- JWT-based access & refresh tokens
- Protected route dependency for token validation
- Token blacklisting / logout support
- Role-based access control (optional/extensible)
- Async SQLAlchemy with PostgreSQL
- Alembic migrations
- Dockerized with `docker-compose` for local dev
- Health check endpoint for orchestration (k8s/ECS friendly)
- Environment-based configuration via Pydantic Settings

## Tech Stack

| Component        | Technology            |
|-------------------|-----------------------|
| Framework         | FastAPI               |
| Language          | Python 3.11+          |
| Database          | PostgreSQL            |
| ORM               | SQLAlchemy (async)    |
| Migrations        | Alembic               |
| Auth              | JWT (python-jose)      |
| Password Hashing  | Passlib (bcrypt)      |
| Server            | Uvicorn / Gunicorn    |
| Containerization  | Docker, Docker Compose|

## Project Structure

```
auth-microservice/
├── CLAUDE.md            # Project context/instructions for Claude Code
├── CONTRIBUTION.md      # Contribution guidelines
├── DockerFile           # Container build definition
├── LICENSE
├── README.md
├── SKILLS.md            # Project-specific skills/conventions reference
├── docker-compose.yml   # Local dev orchestration (app + dependencies)
├── pyproject.toml       # Project metadata & dependencies
└── src/                 # Application source code
    ├── main.py              # FastAPI app entrypoint
    ├── api/
    │   └── v1/
    │       ├── auth.py      # Login, register, refresh, logout routes
    │       └── users.py     # User profile / management routes
    ├── core/
    │   ├── config.py        # Settings (env vars)
    │   ├── security.py      # Password hashing, JWT encode/decode
    │   └── dependencies.py  # get_current_user, role checks
    ├── db/
    │   ├── base.py          # SQLAlchemy base
    │   ├── session.py       # Async engine/session
    │   └── models/
    │       └── user.py
    ├── schemas/
    │   ├── user.py          # Pydantic request/response models
    │   └── token.py
    ├── services/
    │   └── auth_service.py  # Business logic
    └── tests/
        ├── test_auth.py
        └── conftest.py
```

> The `src/` layout above reflects a typical structure for this kind of service — adjust to match how the code is actually organized in this repo.

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local, non-Docker development)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/auth-microservice.git
cd auth-microservice
```

### 2. Configure environment variables

Create a `.env` file in the project root with the following values:

```env
# .env
APP_NAME=auth-microservice
ENV=development
SECRET_KEY=change-me-to-a-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/auth_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=auth_db
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

This starts:
- `auth-service` — the FastAPI app (default: `http://localhost:8000`)
- `db` — PostgreSQL database

> Note: the container file is named `DockerFile` (not the default `Dockerfile`). If you ever build it directly rather than through `docker-compose.yml`, point to it explicitly:
> ```bash
> docker build -f DockerFile -t auth-microservice .
> ```

### 4. Run database migrations

```bash
docker compose exec auth-service alembic upgrade head
```

### 5. Access API docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Locally (without Docker)

Dependencies are managed via `pyproject.toml`. Using [uv](https://github.com/astral-sh/uv):

```bash
uv sync
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or with plain `pip`:

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install .

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint                 | Description                        | Auth Required |
|--------|---------------------------|-------------------------------------|----------------|
| POST   | `/api/v1/auth/register`   | Register a new user                | No             |
| POST   | `/api/v1/auth/login`      | Authenticate and get tokens        | No             |
| POST   | `/api/v1/auth/refresh`    | Refresh access token                | No (refresh token) |
| POST   | `/api/v1/auth/logout`     | Invalidate refresh token            | Yes            |
| GET    | `/api/v1/users/me`        | Get current user profile            | Yes            |
| GET    | `/health`                 | Health check                        | No             |

### Example: Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "StrongPass123!"}'
```

### Example: Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "StrongPass123!"}'
```

Response:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### Example: Access a protected route

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

## Running Tests

```bash
docker compose exec auth-service pytest -v
```

Or locally:

```bash
uv run pytest -v --cov=src src/tests/
```

## Docker Details

### DockerFile (multi-stage, production-friendly)

```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml (dev)

```yaml
version: "3.9"

services:
  auth-service:
    build:
      context: .
      dockerfile: DockerFile
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    volumes:
      - ./src:/app/src

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## Security Notes

- Passwords are hashed with bcrypt; plaintext passwords are never stored.
- Access tokens are short-lived; refresh tokens are used to renew sessions.
- Set a strong, random `SECRET_KEY` in production (never commit it).
- Use HTTPS in production; terminate TLS at a reverse proxy/load balancer.
- Consider rate-limiting `/auth/login` to mitigate brute-force attempts.

## Additional Documentation

- [`CONTRIBUTION.md`](./CONTRIBUTION.md) — guidelines for contributing to this repo
- [`SKILLS.md`](./SKILLS.md) — project-specific conventions and reference notes
- [`CLAUDE.md`](./CLAUDE.md) — context/instructions used when working on this repo with Claude

## Roadmap

- [ ] OAuth2 / social login providers
- [ ] Email verification flow
- [ ] Password reset via email
- [ ] Multi-factor authentication (MFA)
- [ ] Redis-based token blacklist for logout at scale

## License

MIT License. See `LICENSE` for details.