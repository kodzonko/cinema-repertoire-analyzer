import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

import typer
from loguru import logger
from pydantic import FilePath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parents[2]

AllowedDefaultDays = Literal["dziś", "dzis", "dzisiaj", "today", "jutro", "tomorrow"]
LOG_LVLS = Literal["TRACE", "WARNING", "DEBUG", "INFO", "ERROR", "CRITICAL"]


class UserPreferences(BaseSettings):
    """User preferences for the application."""

    DEFAULT_CINEMA_VENUE: str
    DEFAULT_DAY: AllowedDefaultDays
    TMDB_ACCESS_TOKEN: str | None = None


class CinemaCitySettings(BaseSettings):
    """Settings for Cinema City cinema chain."""

    REPERTOIRE_URL: str
    VENUES_LIST_URL: str


class Settings(BaseSettings):
    """Settings for the application."""

    DB_FILE: FilePath
    USER_PREFERENCES: UserPreferences
    CINEMA_CITY_SETTINGS: CinemaCitySettings
    LOGURU_LEVEL: LOG_LVLS = "INFO"

    @field_validator("LOGURU_LEVEL")
    def set_env_for_loguru(cls, LOGURU_LEVEL: LOG_LVLS) -> LOG_LVLS:  # noqa: N803, N805
        """Set the loguru handler according to log level.

        This handles clearing loguru log handlers and adding the one with appropriate log level.
        """
        logger.remove()
        logger.add(sys.stdout, level=LOGURU_LEVEL)
        return LOGURU_LEVEL

    model_config = SettingsConfigDict(extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Get the settings for the application."""
    ENV_PATH = None  # noqa: N806
    if os.environ.get("ENV_PATH") and Path(os.environ["ENV_PATH"]).exists():
        ENV_PATH = Path(os.environ["ENV_PATH"])  # noqa: N806
    elif Path(PROJECT_ROOT / "run.env").exists():
        ENV_PATH = PROJECT_ROOT / "run.env"  # noqa: N806
    else:
        typer.echo(f"Podany plik konfiguracyjny: {ENV_PATH=} nie istnieje.")
        # attempt loading variables from environment
        return Settings(_env_nested_delimiter="__")  # type: ignore[call-arg]
    return Settings(_env_file=ENV_PATH, _env_file_encoding="utf-8", _env_nested_delimiter="__")  # type: ignore
