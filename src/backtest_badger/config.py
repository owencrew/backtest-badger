"""Environment configuration, validated without logging its values."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)
    log_level: str = "INFO"


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Read settings on demand; importing the package has no side effects."""
    env = os.environ if environ is None else environ
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    for name in required:
        if not env.get(name, "").strip():
            raise ValueError(f"{name} must be set and non-blank.")

    host = env.get("POSTGRES_HOST", "127.0.0.1").strip()
    if not host:
        raise ValueError("POSTGRES_HOST must be non-blank.")
    try:
        port = int(env.get("POSTGRES_PORT", "5432"))
    except ValueError:
        raise ValueError("POSTGRES_PORT must be an integer from 1 to 65535.") from None
    if not 1 <= port <= 65535:
        raise ValueError("POSTGRES_PORT must be an integer from 1 to 65535.")

    log_level = env.get("LOG_LEVEL", "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL.")

    return Settings(
        host=host,
        port=port,
        database=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        log_level=log_level,
    )
