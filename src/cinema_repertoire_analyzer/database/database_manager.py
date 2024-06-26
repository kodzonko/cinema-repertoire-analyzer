"""Module containing SQLite connection and operations wrappers.

In general, functions in this class will call the database directly.
"""

from pathlib import Path
from sqlite3 import Error

import sqlalchemy
import typer
from loguru import logger

from cinema_repertoire_analyzer.database.models import CinemaVenues


class DatabaseManager:
    """Class responsible for connecting to the database and executing queries."""

    def __init__(self, db_file_path: Path | str) -> None:
        sqlite_uri = f"sqlite:///{db_file_path}"
        try:
            engine = sqlalchemy.create_engine(sqlite_uri)
            self._session_constructor = sqlalchemy.orm.sessionmaker(engine)
            logger.debug(f"Connection to the database {sqlite_uri} successful.")
        except Error as e:
            typer.echo(f"Nie udało się połączyć z bazą danych {sqlite_uri}. Spróbuj jeszcze raz.")
            raise typer.Exit(code=1) from e

    def get_all_venues(self) -> list[CinemaVenues]:
        """Get all venues for a specified cinema chain from the database."""
        with self._session_constructor() as session:
            results = session.query(CinemaVenues).all()
            return results

    def update_cinema_venues(self, venues: list[CinemaVenues]) -> None:
        """Update cinema venues in the database.

        Function will remove all records from the table and insert new ones.
        """
        with self._session_constructor() as session:
            session.query(CinemaVenues).delete()
            session.add_all(venues)
            session.commit()

    def find_venues_by_name(self, search_string: str) -> CinemaVenues | list[CinemaVenues]:
        """Find a venue of a specified cinema chain by name.

        Conducts a permissive search

        Raises:
        typer.Exit: If no venue is found.
        """
        with self._session_constructor() as session:
            results = (
                session.query(CinemaVenues)
                .filter(CinemaVenues.venue_name.ilike(f"%{search_string}%"))
                .all()
            )
            if len(results) == 1:
                return results[0]
            elif len(results) == 0:
                typer.echo("Nie znaleziono żadnego lokalu o podanej nazwie.")
                raise typer.Exit(code=1)
            return results
