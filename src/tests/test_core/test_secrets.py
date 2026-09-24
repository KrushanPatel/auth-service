import pytest

from core.secrets import get_db_secret


@pytest.fixture
def db_env(monkeypatch):
    for key, value in {
        "DB_USERNAME": "u",
        "DB_PASSWORD": "p",
        "DB_HOST": "h",
        "DB_PORT": "5432",
        "DB_NAME": "d",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("DB_SSL", raising=False)


def test_ssl_defaults_to_require(db_env):
    assert get_db_secret()["ssl"] == "require"


def test_ssl_can_be_disabled(db_env, monkeypatch):
    monkeypatch.setenv("DB_SSL", "disable")
    assert get_db_secret()["ssl"] == "disable"
