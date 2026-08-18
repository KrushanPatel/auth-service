import pytest


@pytest.fixture(autouse=True)
def _autouse_clean_db(clean_db):
    pass
