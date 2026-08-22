# About

A lightweight, production-ready authentication microservice built with **FastAPI**, **PostgreSQL**, and **AWS**. The service provides secure user registration, JWT-based authentication, and protected API endpoints while following a clean layered architecture suitable for production deployments.

---

## Features

### ✅ Implemented

* User registration
* User login
* Password hashing using **Argon2id** (`pwdlib`)
* JWT Access Token authentication using **PyJWT**
* JWT Refresh Token authentication (hashed & stored in database)
* Refresh Token rotation (old tokens revoked on refresh)
* Logout (revokes refresh tokens, and immediately invalidates outstanding access tokens for that user)
* JWT verification
* Protected API endpoints using Bearer authentication
* User profile retrieval & update
* Request validation using **Pydantic v2**
* Response validation using **Pydantic v2**
* Async PostgreSQL access using **AsyncPG**
* Database connection pooling
* Amazon RDS PostgreSQL integration
* Refresh token reuse detection (revokes all user tokens on reuse)
* Password reset (forgot-password/reset-password, single-use token, revokes existing sessions), delivered by email via SMTP (falls back to server-side logging if SMTP isn't configured)
* Rate limiting on register/login/forgot-password, by IP and by account
* Background cleanup of expired refresh tokens, expired password reset tokens, and stale rate-limit windows
* Database-aware health check endpoint
* Docker support
* AWS ECS (Fargate) deployment with ECR & Secrets Manager
* Environment-based configuration
* Linting & formatting (**Ruff**)
* Static type checking (**Mypy**)
* Alembic database migrations
* CI pipeline (GitHub Actions: lint, type-check, migration check, tests)
* Automated test suite (unit, integration, e2e)

### 🚧 Planned

* Role-Based Access Control (RBAC)
* Email verification
* Multi-Factor Authentication (MFA)
* OAuth2 / Social Login
* Redis integration
* CD pipeline (deploy on merge)
* Kubernetes deployment

---

## Tech Stack

| Component          | Technology              |
| ------------------ | ----------------------- |
| Framework          | FastAPI                 |
| Language           | Python 3.14+            |
| Database           | PostgreSQL (Amazon RDS) |
| Database Driver    | AsyncPG                 |
| Authentication     | JWT (PyJWT)             |
| Password Hashing   | Pwdlib (Argon2id)       |
| Validation         | Pydantic v2             |
| Cloud              | AWS ECS (Fargate)       |
| Secrets Management | AWS Secrets Manager     |
| Server             | Uvicorn                 |
| Containerization   | Docker, Docker Compose  |
| Linting/Formatting | Ruff                    |
| Type Checking      | Mypy                    |
