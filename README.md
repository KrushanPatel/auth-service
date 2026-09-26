# Auth Microservice

FastAPI · PostgreSQL · AsyncPG · JWT · Docker

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](pyproject.toml)
[![CI](https://github.com/KrushanPatel/auth-service/actions/workflows/ci.yml/badge.svg)](https://github.com/KrushanPatel/auth-service/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/deployment-Docker-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![AWS ECS](https://img.shields.io/badge/deployment-AWS%20ECS-FF9900?logo=amazonaws&logoColor=white)](task-definition.json)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A lightweight, production-ready authentication microservice built with **FastAPI**, **PostgreSQL**, and **AWS**. See [ABOUT.md](ABOUT.md) for the full feature list and tech stack.

---

## Quickstart

Prerequisites: Python 3.14+, [uv](https://docs.astral.sh/uv/), and Docker Compose.
From a fresh clone, start the local PostgreSQL and Redis services, install the
dependencies, apply the migrations, and run the API:

```bash
cp .env.example .env
docker compose -f docker-compose.test.yml up -d
uv sync
uv run alembic upgrade head
REDIS_URL=redis://localhost:6380/0 uv run uvicorn src.main:app --reload
```

The Compose file starts disposable local services; the Redis URL override uses
its published port. Open <http://localhost:8000/docs> to explore the API.

## Features

- Refresh-token rotation with reuse detection
- TOTP multi-factor authentication
- Google OAuth sign-in
- Redis-backed rate limiting
- Role-based access control (RBAC)

---

## Documentation

* **[ABOUT.md](ABOUT.md)** – What this project is, implemented/planned features, tech stack.
* **[SETUP.md](SETUP.md)** – Prerequisites, environment configuration, running the app, API reference, tests, linting.
* **[ARCHITECTURE.md](ARCHITECTURE.md)** – Project structure, request flow, auth/refresh-token flows, security design.
* **[PROGRESS_TRACKER.md](PROGRESS_TRACKER.md)** – Completed vs. upcoming work.
* **[CLAUDE.md](CLAUDE.md)** – Claude Code project context.
* **[CONTRIBUTING.md](CONTRIBUTING.md)** – Contribution guidelines.
* **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** – Code of conduct.
* **[SECURITY.md](SECURITY.md)** – Reporting a vulnerability.
* **[SKILLS.md](SKILLS.md)** – Project conventions (partly outdated; `pyproject.toml` and CI are authoritative for tooling).

---

## License

Licensed under the **Apache License 2.0**. See the `LICENSE` file for details.
