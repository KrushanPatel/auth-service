# Setup

## Prerequisites

* Python 3.14+
* Docker & Docker Compose
* AWS Account
* Amazon RDS PostgreSQL
* AWS Secrets Manager

---

## Clone Repository

```bash
git clone https://github.com/KrushanPatel/auth-service.git
cd auth-service
```

---

## Configure Environment Variables

Create a `.env` file.

```env
JWT_SECRET_KEY=<32-byte-random-secret>
ALGORITHM=HS256

DB_USERNAME=<rds-username>
DB_PASSWORD=<rds-password>
DB_HOST=<rds-host>
DB_PORT=5432
DB_NAME=<database-name>

SMTP_HOST=<smtp-host>
SMTP_PORT=587
SMTP_USERNAME=<smtp-username>
SMTP_PASSWORD=<smtp-password>
EMAIL_FROM_ADDRESS=no-reply@yourdomain.com
PASSWORD_RESET_URL_BASE=https://yourapp.com/reset-password
EMAIL_VERIFICATION_URL_BASE=https://yourapp.com/verify-email

MFA_ENCRYPTION_KEY=<fernet-key>
```

Database credentials are read directly from environment variables. When deploying to AWS ECS, they are injected at runtime from **AWS Secrets Manager** (see `task-definition.json`).

`SMTP_*` configures delivery of password reset and email verification emails. If `SMTP_HOST` is unset, the link is logged server-side instead of emailed (useful for local development). Any SMTP provider works, including [Amazon SES's SMTP interface](https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html) for production.

`MFA_ENCRYPTION_KEY` is the Fernet key that encrypts TOTP secrets at rest — generate one with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. It has an insecure hardcoded default for local dev only; the app refuses to start with that default when `ENV=production`.

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

## Running the Application

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

## API Documentation

Swagger UI

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

## API Endpoints

| Method | Endpoint                       | Description                    | Authentication |
| ------ | ------------------------------- | ------------------------------- | -------------- |
| POST   | `/api/v1/auth/register`        | Register a new user             | No             |
| POST   | `/api/v1/auth/login`           | Authenticate user                | No             |
| POST   | `/api/v1/auth/refresh`         | Refresh & rotate tokens          | No             |
| POST   | `/api/v1/auth/logout`          | Logout (revoke refresh token, invalidate access tokens) | No |
| POST   | `/api/v1/auth/forgot-password` | Request a password reset token   | No             |
| POST   | `/api/v1/auth/reset-password`  | Reset password using a token     | No             |
| POST   | `/api/v1/auth/verify-email`    | Verify email using a token       | No             |
| POST   | `/api/v1/auth/resend-verification` | Re-send the verification email | No         |
| POST   | `/api/v1/auth/mfa/verify`      | Complete login with a TOTP or recovery code | No (needs the `mfa_token` from `/login`) |
| POST   | `/api/v1/mfa/enroll`           | Start TOTP enrollment (returns secret + `otpauth://` URI) | Yes |
| POST   | `/api/v1/mfa/enroll/confirm`   | Confirm enrollment with a TOTP code (returns recovery codes) | Yes |
| POST   | `/api/v1/mfa/disable`          | Disable MFA (requires current password) | Yes    |
| GET    | `/api/v1/users/profile`        | Get current user profile         | Yes            |
| PATCH  | `/api/v1/users`                | Update current user profile      | Yes            |
| GET    | `/api/v1/admin/users`          | List all users                   | Yes (admin)    |
| PATCH  | `/api/v1/admin/users/{id}/role` | Change a user's role            | Yes (admin)    |
| GET    | `/health`                      | Health check (with DB status)    | No             |

`/register`, `/login`, `/forgot-password`, `/resend-verification`, and `/mfa/verify` are rate limited by client IP, and (except `/register`) by the target account — see [ARCHITECTURE.md](ARCHITECTURE.md#security).

New accounts must verify their email before `/login` will succeed — see [Verify Email](#verify-email) below. If the account has MFA enabled, `/login` returns `{mfa_required: true, mfa_token}` instead of tokens; exchange that for the real access/refresh pair via `/api/v1/auth/mfa/verify`.

Every account starts with `role = "user"`. There's no self-service way to become `"admin"` — promote the first admin directly in the database:

```sql
UPDATE users SET role = 'admin' WHERE email = 'krushan@gmail.com';
```

Once you have one admin account, use it to promote others via `PATCH /api/v1/admin/users/{id}/role` (see below).

---

## Example Requests

### Register

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

### Verify Email

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
-H "Content-Type: application/json" \
-d '{
    "token":"<verification-token>"
}'
```

Response: `204 No Content`. Required before `/login` will succeed for a new account.

### Resend Verification

```bash
curl -X POST http://localhost:8000/api/v1/auth/resend-verification \
-H "Content-Type: application/json" \
-d '{
    "email":"krushan@gmail.com"
}'
```

Returns the same generic message whether or not the email is registered or already verified (no enumeration).

### Login

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
    "refresh_token":"<jwt>",
    "token_type":"bearer"
}
```

### Refresh Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
-H "Content-Type: application/json" \
-d '{
    "refresh_token":"<refresh-jwt>"
}'
```

Response

```json
{
    "access_token":"<new-jwt>",
    "refresh_token":"<new-refresh-jwt>",
    "token_type":"bearer"
}
```

The old refresh token is **revoked** on refresh (rotation). Reusing it returns `400`.

### Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
-H "Content-Type: application/json" \
-d '{
    "refresh_token":"<refresh-jwt>"
}'
```

Response: `204 No Content`. The refresh token is revoked, and any access token issued to that user before this call stops working immediately.

### Access Protected Endpoint

```bash
curl http://localhost:8000/api/v1/users/profile \
-H "Authorization: Bearer <jwt>"
```

### Update User Profile

```bash
curl -X PATCH http://localhost:8000/api/v1/users \
-H "Authorization: Bearer <jwt>" \
-H "Content-Type: application/json" \
-d '{
    "first_name":"New",
    "last_name":"Name"
}'
```

### List Users (admin only)

```bash
curl http://localhost:8000/api/v1/admin/users \
-H "Authorization: Bearer <admin-jwt>"
```

### Change a User's Role (admin only)

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/users/<user-id>/role \
-H "Authorization: Bearer <admin-jwt>" \
-H "Content-Type: application/json" \
-d '{
    "role":"admin"
}'
```

A non-admin caller gets `403`. Role changes are read fresh from the database on every request, so a promoted/demoted user's access changes on their very next request — no need to log out and back in.

---

## Running Tests

Unit tests (`src/tests/test_core`, `src/tests/test_services`) run standalone. Repository and API tests need a real Postgres instance — start the disposable test database first:

```bash
docker compose -f docker-compose.test.yml up -d
uv run pytest
```

---

## Linting & Type Checking

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src
```
