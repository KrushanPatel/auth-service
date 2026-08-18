from core.security import hash_password, hash_reset_token, verify_password


def test_hash_password_does_not_return_plaintext():
    hashed = hash_password("Password@123")

    assert hashed != "Password@123"


def test_hash_password_is_salted():
    first = hash_password("Password@123")
    second = hash_password("Password@123")

    assert first != second
    assert verify_password("Password@123", first)
    assert verify_password("Password@123", second)


def test_verify_password_accepts_correct_password():
    hashed = hash_password("Password@123")

    assert verify_password("Password@123", hashed) is True


def test_verify_password_rejects_incorrect_password():
    hashed = hash_password("Password@123")

    assert verify_password("wrong-password", hashed) is False


def test_hash_reset_token_is_deterministic():
    assert hash_reset_token("a-reset-token") == hash_reset_token("a-reset-token")


def test_hash_reset_token_differs_for_different_tokens():
    assert hash_reset_token("token-one") != hash_reset_token("token-two")
