from core.config import ENV, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


def validate_google_oauth_config() -> None:
    """
    Fail fast at startup rather than silently running production with a
    Google OAuth login that can never complete the token exchange.
    """
    if ENV == "production" and not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        raise RuntimeError(
            "GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are not set; "
            "cannot use Google OAuth login in production"
        )
