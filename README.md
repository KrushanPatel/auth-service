# Auth Microservice

A lightweight, production-ready authentication microservice built with **FastAPI**, **PostgreSQL**, and **AWS**. The service provides secure user registration, JWT-based authentication, and protected API endpoints while following a clean layered architecture suitable for production deployments.

---

# Features

## ✅ Implemented

* User registration
* User login
* Password hashing using **Argon2id** (`pwdlib`)
* JWT Access Token authentication using **PyJWT**
* JWT verification
* Protected API endpoints using Bearer authentication
* Request validation using **Pydantic v2**
* Response validation using **Pydantic v2**
* Async PostgreSQL access using **AsyncPG**
* Database connection pooling
* Amazon RDS PostgreSQL integration
* AWS Secrets Manager integration
* Health check endpoint
* Docker support
* Environment-based configuration

## 🚧 Planned

* Refresh Token authentication
* Refresh Token rotation
* Logout
* Token revocation / blacklisting
* Role-Based Access Control (RBAC)
* Email verification
* Forgot password
* Password reset
* Multi-Factor Authentication (MFA)
* OAuth2 / Social Login
* Alembic database migrations
* Redis integration
* Rate limiting
* CI/CD pipeline
* Kubernetes / Amazon ECS deployment

---

# Tech Stack

| Component          | Technology              |
| ------------------ | ----------------------- |
| Framework          | FastAPI                 |
| Language           | Python 3.14+            |
| Database           | PostgreSQL (Amazon RDS) |
| Database Driver    | AsyncPG                 |
| Authentication     | JWT (PyJWT)             |
| Password Hashing   | Pwdlib (Argon2id)       |
| Validation         | Pydantic v2             |
| Cloud              | AWS EC2                 |
| Secrets Management | AWS Secrets Manager     |
| Server             | Uvicorn                 |
| Containerization   | Docker, Docker Compose  |

---

# Project Structure

```text
auth-microservice/
├── CLAUDE.md
├── CONTRIBUTION.md
├── DockerFile
├── LICENSE
├── README.md
├── SKILLS.md
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── src/
    ├── api/
    │   └── v1/
    │       ├── auth.py
    │       ├── health.py
    │       └── users.py
    ├── core/
    │   ├── config.py
    │   ├── dependencies.py
    │   ├── jwt.py
    │   ├── secrets.py
    │   └── security.py
    ├── db/
    │   ├── connection.py
    │   └── session.py
    ├── repositories/
    │   └── user_repository.py
    ├── schemas/
    │   ├── auth.py
    │   └── user.py
    ├── services/
    │   └── auth_service.py
    ├── tests/
    └── main.py
```

---

# Architecture

```text
                    Client
                       │
                       ▼
                  FastAPI Router
                       │
                       ▼
              Pydantic Validation
                       │
                       ▼
              Authentication Service
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
      JWT Generation      Password Hashing
            │                     │
            └──────────┬──────────┘
                       ▼
                Repository Layer
                       │
                       ▼
                 Database Session
                       │
                       ▼
             AsyncPG Connection Pool
                       │
                       ▼
            Amazon RDS PostgreSQL
```

---

# Getting Started

## Prerequisites

* Python 3.14+
* Docker & Docker Compose
* AWS Account
* Amazon RDS PostgreSQL
* AWS Secrets Manager

---

## Clone Repository

```bash
git clone <repository-url>
cd auth-microservice
```

---

## Configure Environment Variables

Create a `.env` file.

```env
AWS_REGION=ap-south-1
SECRET_NAME=dev/krushan/secrets

JWT_SECRET_KEY=<32-byte-random-secret>
ALGORITHM=HS256
```

Database credentials are securely retrieved from **AWS Secrets Manager**.

Example secret:

```json
{
    "username": "devfastapi",
    "password": "********",
    "host": "fastapi-db.xxxxx.ap-south-1.rds.amazonaws.com",
    "port": 5432,
    "dbname": "auth_db"
}
```

---

# Running the Application

Using **uv**

```bash
uv sync
uv run src/main.py
```

or

```bash
uv run uvicorn src.main:app --reload
```

Using Docker

```bash
docker compose up --build
```

---

# API Documentation

Swagger UI

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# API Endpoints

| Method | Endpoint                | Description              | Authentication |
| ------ | ----------------------- | ------------------------ | -------------- |
| POST   | `/api/v1/auth/register` | Register a new user      | No             |
| POST   | `/api/v1/auth/login`    | Authenticate user        | No             |
| GET    | `/api/v1/users/me`      | Get current user profile | Yes            |
| GET    | `/health`               | Health check             | No             |

---

# Example Requests

## Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
-H "Content-Type: application/json" \
-d '{
    "username":"krushan",
    "email":"krushan@gmail.com",
    "password":"Password@123",
    "first_name":"Krushan",
    "last_name":"Patel"
}'
```

---

## Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
-H "Content-Type: application/json" \
-d '{
    "email":"krushan@gmail.com",
    "password":"Password@123"
}'
```

Response

```json
{
    "access_token":"<jwt>",
    "token_type":"bearer"
}
```

---

## Access Protected Endpoint

```bash
curl http://localhost:8000/api/v1/users/me \
-H "Authorization: Bearer <jwt>"
```

---

# Authentication Flow

```text
Register
    │
    ▼
Store Argon2id Password Hash
    │
    ▼
Login
    │
    ▼
Verify Password
    │
    ▼
Generate JWT Access Token
    │
    ▼
Client Stores JWT
    │
    ▼
Authorization: Bearer <JWT>
    │
    ▼
Verify JWT
    │
    ▼
Load User from Database
    │
    ▼
Protected Endpoint
```

---

# Security

* Passwords are hashed using **Argon2id**.
* Plaintext passwords are never stored.
* JWT authentication uses **HS256**.
* Database credentials are securely retrieved from **AWS Secrets Manager**.
* PostgreSQL connections are managed using an **AsyncPG connection pool**.
* Protected endpoints require a valid Bearer JWT.
* Secrets are never committed to source control.

---

# Running Tests

```bash
uv run pytest
```

---

# Current Progress

## ✅ Completed

* User Registration
* User Login
* Password Hashing (Argon2id)
* JWT Access Token Generation
* JWT Verification
* Protected API Endpoints
* Pydantic Request Validation
* Pydantic Response Validation
* AsyncPG Connection Pool
* Amazon RDS Integration
* AWS Secrets Manager Integration
* Health Check Endpoint
* Swagger API Documentation

---

## 🚧 Upcoming Features

* Refresh Tokens
* Logout
* Refresh Token Rotation
* Email Verification
* Forgot Password
* Password Reset
* Multi-Factor Authentication (MFA)
* Role-Based Access Control (RBAC)
* OAuth2 / Social Login
* Alembic Migrations
* Redis Token Revocation
* Rate Limiting
* CI/CD Pipeline
* Kubernetes / Amazon ECS Deployment

---

# Additional Documentation

* **CLAUDE.md** – Claude Code project context
* **CONTRIBUTION.md** – Contribution guidelines
* **SKILLS.md** – Project conventions

---

# License

Licensed under the **Apache License 2.0**. See the `LICENSE` file for details.
