import os
from pathlib import Path

import pytest
from typer import Typer
from typer.testing import CliRunner

from cinema_repertoire_analyzer.cinema_api.cinema_city import CinemaCity
from cinema_repertoire_analyzer.cinema_api.models import MoviePlayDetails, Repertoire
from cinema_repertoire_analyzer.database.database_manager import DatabaseManager
from cinema_repertoire_analyzer.database.models import CinemaVenues
from cinema_repertoire_analyzer.main import make_app
from cinema_repertoire_analyzer.ratings_api.tmdb import TmdbClient
from cinema_repertoire_analyzer.settings import Settings, get_settings


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    db_path = tmp_path / "test_db.sqlite"

    os.environ.pop("ENV_PATH", None)
    os.environ["LOGURU_LEVEL"] = "TRACE"
    os.environ["DB_FILE"] = str(db_path)
    os.environ["USER_PREFERENCES__DEFAULT_CINEMA_VENUE"] = "Wrocław - Wroclavia"
    os.environ["USER_PREFERENCES__DEFAULT_DAY"] = "today"
    os.environ["USER_PREFERENCES__TMDB_ACCESS_TOKEN"] = "1234"
    os.environ["CINEMA_CITY_SETTINGS__REPERTOIRE_URL"] = (
        "https://www.cinema-city.pl/#/buy-tickets-by-cinema?"
        "in-cinema={cinema_venue_id}&at={repertoire_date}"
    )
    os.environ["CINEMA_CITY_SETTINGS__VENUES_LIST_URL"] = (
        "https://www.cinema-city.pl/#/buy-tickets-by-cinema"
    )
    get_settings.cache_clear()
    settings_instance = get_settings()
    DatabaseManager(settings_instance.DB_FILE).update_cinema_venues(
        [
            CinemaVenues(venue_name="Warszawa - Janki", venue_id="1"),
            CinemaVenues(venue_name="Warszawa - Galeria Mokotów", venue_id="2"),
            CinemaVenues(venue_name="Wrocław - Wroclavia", venue_id="3"),
        ]
    )
    return settings_instance


@pytest.fixture(autouse=True)
def stub_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TmdbClient, "verify_api_key", lambda self, access_token: False)
    monkeypatch.setattr(
        CinemaCity,
        "fetch_repertoire",
        lambda self, date, venue_data: [
            Repertoire(
                title="Test Movie",
                genres="Drama",
                play_length="120 min",
                original_language="EN",
                play_details=[
                    MoviePlayDetails(format="2D", play_language="napisy: PL", play_times=["18:00"])
                ],
            )
        ],
    )
    monkeypatch.setattr(
        CinemaCity,
        "fetch_cinema_venues_list",
        lambda self: [
            CinemaVenues(venue_name="Warszawa - Janki", venue_id="1"),
            CinemaVenues(venue_name="Wrocław - Wroclavia", venue_id="2"),
        ],
    )


@pytest.fixture
def typer_app(settings: Settings) -> Typer:
    return make_app(settings)


@pytest.fixture
def db_manager(settings: Settings) -> DatabaseManager:
    return DatabaseManager(db_file_path=settings.DB_FILE)
