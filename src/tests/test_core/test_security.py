from core.security import hash_password, verify_password


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
