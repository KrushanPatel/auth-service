# Architecture

## Project Structure

```text
auth-microservice/
├── ABOUT.md
├── ARCHITECTURE.md
├── CLAUDE.md
├── CONTRIBUTION.md
├── Dockerfile
├── LICENSE
├── PROGRESS_TRACKER.md
├── README.md
├── SETUP.md
├── SKILLS.md
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── task-definition.json
├── task-role-trust-policy.json
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
    │   ├── email.py
    │   ├── jwt.py
    │   ├── secrets.py
    │   └── security.py
    ├── db/
    │   ├── connection.py
    │   └── session.py
    ├── repositories/
    │   ├── password_reset_repository.py
    │   ├── rate_limit_repository.py
    │   ├── refresh_token_repository.py
    │   └── user_repository.py
    ├── schemas/
    │   ├── auth.py
    │   ├── health.py
    │   ├── refresh_token.py
    │   └── user.py
    ├── services/
    │   ├── auth_service.py
    │   ├── password_reset_service.py
    │   ├── rate_limit_service.py
    │   └── refresh_token_service.py
    ├── tests/
    └── main.py
```

---

## Layered Flow

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

## Refresh Token Flow

```text
Login
  │
  ▼
Generate Access Token + Refresh Token (JTI)
  │
  ▼
Hash Refresh Token → Store in DB
  │
  ▼
POST /api/v1/auth/refresh
  │
  ▼
Verify Refresh Token Signature
  │
  ▼
Lookup Token by JTI → Check Expiry & Revocation
  │
  ▼
Issue New Access Token + New Refresh Token
  │
  ▼
Revoke Old Refresh Token (rotation)

POST /api/v1/auth/logout
  │
  ▼
Revoke Refresh Token
  │
  ▼
Stamp user's tokens_valid_after = now()
  │
  ▼
Any access token issued before that instant is rejected on next use
```

## Authentication Flow

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
Generate JWT Access Token + Refresh Token
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
Check tokens_valid_after (rejects tokens issued before last logout)
    │
    ▼
Protected Endpoint
    │
    ▼
Access Token Expires
    │
    ▼
POST /api/v1/auth/refresh
    │
    ▼
Validate Refresh Token (DB check)
    │
    ├── Valid ──► Issue New Access Token + New Refresh Token
    │                  │
    │                  ▼
    │            Revoke Old Refresh Token (rotation)
    │
    └── Invalid/Revoked ──► 400 Bad Request

POST /api/v1/auth/logout
    │
    ▼
Revoke Refresh Token + Invalidate Access Tokens
    │
    ▼
204 No Content
```

---

## Security

* Passwords are hashed using **Argon2id**.
* Plaintext passwords are never stored.
* Refresh tokens are hashed (Argon2id) before being stored in the database.
* Refresh tokens are **rotated** on every refresh — old tokens are revoked immediately, limiting the damage of token theft.
* **Reuse detection** — reusing an already-rotated/revoked refresh token revokes *all* of that user's tokens.
* **Logout invalidates access tokens immediately** — a per-user `tokens_valid_after` timestamp is checked on every request, so a stolen/copied access token stops working the moment its owner logs out, not just when it naturally expires (up to 15 minutes later).
* JWT authentication uses **HS256**.
* **Rate limiting** on `/register`, `/login`, and `/forgot-password` — both by client IP and by target account — to blunt brute-force login attempts and password-reset email spam.
* Database credentials are injected at runtime from **AWS Secrets Manager** (ECS) or `.env`.
* PostgreSQL connections are managed using an **AsyncPG connection pool**.
* Protected endpoints require a valid Bearer JWT.
* Secrets are never committed to source control.
