from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv()

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-in-production",
)
JWT_ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

class Settings:
    AWS_REGION = os.getenv("AWS_REGION")
    SECRET_NAME = os.getenv("SECRET_NAME")


settings = Settings()