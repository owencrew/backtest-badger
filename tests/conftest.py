import pytest


@pytest.fixture
def config_env():
    return {
        "POSTGRES_DB": "test_badger",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "private-test-password",
    }
