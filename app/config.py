"""Application settings read from environment variables (standard library only)."""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "sqlite:///./netmon.db"


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application configuration."""

    app_name: str = "NetMon"
    app_version: str = "0.1.0"
    database_url: str = DEFAULT_DATABASE_URL
    debug: bool = False


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable such as '1', 'true', 'yes' or 'on'."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """Build Settings from the current environment."""
    return Settings(
        app_name=os.environ.get("NETMON_APP_NAME", "NetMon"),
        app_version=os.environ.get("NETMON_APP_VERSION", "0.1.0"),
        database_url=os.environ.get("NETMON_DATABASE_URL", DEFAULT_DATABASE_URL),
        debug=_env_flag("NETMON_DEBUG"),
    )
