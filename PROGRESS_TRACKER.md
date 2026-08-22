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
* Rate Limiting (register/login/forgot-password/resend-verification, by IP and by account)
* Background Cleanup of Expired Refresh Tokens, Password Reset Tokens, Email Verification Tokens, and Rate-Limit Windows
* Health Check Endpoint
* Swagger API Documentation
* Alembic Migrations
* CI Pipeline (GitHub Actions: lint, type-check, migration check, tests)
* AWS ECS (Fargate) Deployment with ECR & Secrets Manager
* Linting & Formatting (Ruff)
* Static Type Checking (Mypy)

---

## 🚧 Upcoming Features

* Multi-Factor Authentication (MFA)
* Role-Based Access Control (RBAC)
* OAuth2 / Social Login
* Redis Integration
* CD Pipeline (deploy on merge)
* Kubernetes Deployment
