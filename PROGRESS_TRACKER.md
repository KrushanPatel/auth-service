# Progress Tracker

## ✅ Completed

* User Registration
* User Login
* Password Hashing (Argon2id)
* JWT Access Token Generation
* JWT Refresh Token Generation & Storage
* Refresh Token Rotation & Reuse Detection
* Logout / Refresh Token Revocation
* Immediate Access Token Invalidation on Logout
* JWT Verification
* Protected API Endpoints
* User Profile Retrieval & Update
* Pydantic Request Validation
* Pydantic Response Validation
* AsyncPG Connection Pool
* Amazon RDS Integration
* Forgot Password / Password Reset (single-use token, revokes sessions)
* Email Verification (login blocked until verified; verify-email/resend-verification)
* SMTP Email Delivery for Password Reset and Email Verification (falls back to server-side logging)
* Rate Limiting (register/login/forgot-password/resend-verification/mfa-verify/oauth-google, by IP and by account, backed by Redis)
* Multi-Factor Authentication (TOTP via pyotp, encrypted secret at rest, single-use recovery codes)
* Background Cleanup of Expired Refresh Tokens, Password Reset Tokens, and Email Verification Tokens
* Health Check Endpoint
* Swagger API Documentation
* Alembic Migrations
* CI Pipeline (GitHub Actions: lint, type-check, migration check, tests)
* AWS ECS (Fargate) Deployment with ECR & Secrets Manager
* Linting & Formatting (Ruff)
* Static Type Checking (Mypy)
* Role-Based Access Control (RBAC)
* OAuth2 / Social Login (Google, auto-link by verified email)
* Redis Integration (rate limiting)
* CD Pipeline (deploy on merge, via GitHub Actions OIDC + ECS)

---

## 🚧 Upcoming Features

* Kubernetes Deployment
