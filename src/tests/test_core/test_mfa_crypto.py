from core.mfa_crypto import decrypt_secret, encrypt_secret


def test_encrypt_secret_does_not_return_plaintext():
    encrypted = encrypt_secret("JBSWY3DPEHPK3PXP")

    assert encrypted != "JBSWY3DPEHPK3PXP"


def test_decrypt_secret_recovers_original_value():
    encrypted = encrypt_secret("JBSWY3DPEHPK3PXP")

    assert decrypt_secret(encrypted) == "JBSWY3DPEHPK3PXP"
