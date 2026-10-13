import pytest

from backtest_badger.config import load_settings


def test_defaults_and_password_redaction(config_env):
    settings = load_settings(config_env)
    assert (settings.host, settings.port, settings.log_level) == (
        "127.0.0.1",
        5432,
        "INFO",
    )
    assert settings.database == "test_badger"
    assert settings.password == config_env["POSTGRES_PASSWORD"]
    assert settings.password not in repr(settings)


def test_environment_overrides(monkeypatch, config_env):
    config_env.update(
        POSTGRES_HOST="localhost", POSTGRES_PORT="55432", LOG_LEVEL="debug"
    )
    for name, value in config_env.items():
        monkeypatch.setenv(name, value)
    settings = load_settings()
    assert (settings.host, settings.port, settings.log_level) == (
        "localhost",
        55432,
        "DEBUG",
    )


@pytest.mark.parametrize("name", ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"])
@pytest.mark.parametrize("value", [None, "", "  "])
def test_missing_or_blank_required_settings(config_env, name, value):
    if value is None:
        del config_env[name]
    else:
        config_env[name] = value
    with pytest.raises(ValueError, match=name):
        load_settings(config_env)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("POSTGRES_PORT", "secret-not-a-port"),
        ("POSTGRES_PORT", "0"),
        ("POSTGRES_PORT", "65536"),
        ("POSTGRES_HOST", "  "),
        ("LOG_LEVEL", "secret-not-a-level"),
    ],
)
def test_invalid_settings_do_not_echo_values(config_env, name, value):
    config_env[name] = value
    with pytest.raises(ValueError, match=name) as error:
        load_settings(config_env)
    assert "secret" not in str(error.value)
