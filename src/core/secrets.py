import json
import boto3
from botocore.exceptions import ClientError
from core.config import settings
from pprint import pprint

def get_db_secret() -> dict:
    client = boto3.client(
        "secretsmanager",
        region_name=settings.AWS_REGION,
    )
    try:
        response = client.get_secret_value(
            SecretId=settings.SECRET_NAME
        )
        secret = json.loads(response["SecretString"])
        required = [
            "username",
            "password",
            "host",
            "port",
        ]
        missing = [k for k in required if k not in secret]

        if missing:
            raise RuntimeError(
                f"Missing secret keys: {missing}"
            )

        return secret

    except ClientError as e:
        raise RuntimeError(
            f"SecretsManager Error: {e}"
        ) from e