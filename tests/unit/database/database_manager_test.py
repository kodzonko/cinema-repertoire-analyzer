from sqlite3 import Error

import click
import pytest
import sqlalchemy
from mockito import args, mock, when

from cinema_repertoire_analyzer.database.database_manager import DatabaseManager
from cinema_repertoire_analyzer.database.models import CinemaVenues


@pytest.fixture
def db_manager() -> DatabaseManager:
    return DatabaseManager("test_db.sqlite")


@pytest.fixture
def engine() -> sqlalchemy.Engine:
    return mock(sqlalchemy.Engine)  # type: ignore[no-any-return]


@pytest.fixture
def session() -> sqlalchemy.orm.Session:
    return mock(sqlalchemy.orm.Session)  # type: ignore[no-any-return]


@pytest.fixture
def query() -> sqlalchemy.orm.Query:
    return mock(sqlalchemy.orm.Query)  # type: ignore[no-any-return]


@pytest.fixture
def row_returning_query() -> sqlalchemy.orm.query.RowReturningQuery:
    return mock(sqlalchemy.orm.query.RowReturningQuery)  # type: ignore[no-any-return]


@pytest.fixture
def cinema_venues() -> list[CinemaVenues]:
    return [mock(CinemaVenues), mock(CinemaVenues)]


@pytest.mark.unit
def test_update_cinema_venues_inserts_records_to_db(
    db_manager: DatabaseManager,
    session: sqlalchemy.orm.Session,
    query: sqlalchemy.orm.Query,
    cinema_venues: list[CinemaVenues],
) -> None:
    when(session).__enter__().thenReturn(session)
    when(session).__exit__(*args)
    when(db_manager)._session_constructor().thenReturn(session)
    when(session).query(CinemaVenues).thenReturn(query)
    when(query).delete()
    when(session).add_all(cinema_venues)
    when(session).commit()

    db_manager.update_cinema_venues(cinema_venues)


@pytest.mark.unit
def test_database_manager_fails_to_create_instance_due_to_error() -> None:
    when(sqlalchemy).create_engine("sqlite:///test_db.sqlite").thenRaise(
        Error("some connection error")
    )

    with pytest.raises(click.exceptions.Exit):
        DatabaseManager("test_db.sqlite")


@pytest.mark.unit
def test_get_venue_by_name_returns_venue(
    db_manager: DatabaseManager,
    session: sqlalchemy.orm.Session,
    engine: sqlalchemy.Engine,
    row_returning_query: sqlalchemy.orm.query.RowReturningQuery,
    cinema_venues: CinemaVenues,
) -> None:
    when(session).__enter__().thenReturn(session)
    when(session).__exit__(*args)
    when(sqlalchemy).create_engine("sqlite:///test_db.sqlite").thenReturn(engine)
    when(sqlalchemy.orm).sessionmaker(engine).thenReturn(session)
    when(db_manager)._session_constructor().thenReturn(session)
    when(session).query(CinemaVenues).thenReturn(row_returning_query)
    when(row_returning_query).filter(...).thenReturn(row_returning_query)
    when(row_returning_query).all().thenReturn(cinema_venues)

    assert db_manager.find_venues_by_name("some-name") == cinema_venues
