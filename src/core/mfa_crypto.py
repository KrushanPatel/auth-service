from cryptography.fernet import Fernet

from core.config import DEFAULT_MFA_ENCRYPTION_KEY, ENV, MFA_ENCRYPTION_KEY

_fernet = Fernet(MFA_ENCRYPTION_KEY.encode())


def validate_mfa_config() -> None:
    """
    Fail fast at startup rather than silently running production on the
    insecure default encryption key.
    """
    if ENV == "production" and MFA_ENCRYPTION_KEY == DEFAULT_MFA_ENCRYPTION_KEY:
        raise RuntimeError(
            "MFA_ENCRYPTION_KEY is not set; refusing to use the default key in production"
        )


def encrypt_secret(secret: str) -> str:
    return _fernet.encrypt(secret.encode()).decode()


def decrypt_secret(encrypted_secret: str) -> str:
    return _fernet.decrypt(encrypted_secret.encode()).decode()
