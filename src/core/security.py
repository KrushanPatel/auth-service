import hashlib

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def hash_reset_token(token: str) -> str:
    """
    Deterministic hash for password reset tokens, so a token can be looked
    up directly by its hash (unlike Argon2id, which salts on every call and
    can't be used as a lookup key).
    """
    return hashlib.sha256(token.encode()).hexdigest()
