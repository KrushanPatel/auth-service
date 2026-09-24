import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-in-production",
)

JWT_ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)
PASSWORD_RESET_TOKEN_EXPIRE = timedelta(minutes=30)
EMAIL_VERIFICATION_TOKEN_EXPIRE = timedelta(hours=24)
MFA_TOKEN_EXPIRE = timedelta(minutes=5)
OAUTH_STATE_TOKEN_EXPIRE = timedelta(minutes=5)

DEFAULT_MFA_ENCRYPTION_KEY = "Czneppg-5qf_1mPXKrnuDDhPpt9F5S7IyubAsptiYCE="
MFA_ENCRYPTION_KEY = os.getenv("MFA_ENCRYPTION_KEY", DEFAULT_MFA_ENCRYPTION_KEY)
TOTP_VALID_WINDOW = 1
MFA_RECOVERY_CODE_COUNT = 10

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "no-reply@example.com")
PASSWORD_RESET_URL_BASE = os.getenv(
    "PASSWORD_RESET_URL_BASE", "http://localhost:3000/reset-password"
)
EMAIL_VERIFICATION_URL_BASE = os.getenv(
    "EMAIL_VERIFICATION_URL_BASE", "http://localhost:3000/verify-email"
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/oauth/google/callback"
)
