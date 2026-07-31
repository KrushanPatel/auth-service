from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    AWS_REGION = os.getenv("AWS_REGION")
    SECRET_NAME = os.getenv("SECRET_NAME")


settings = Settings()