import re
from datetime import datetime, timedelta

import rich
import typer
from rich.table import Table

from cinema_repertoire_analyzer.cinema_api.models import Repertoire, RepertoireCliTableMetadata
from cinema_repertoire_analyzer.database.models import CinemaVenuesBase
from cinema_repertoire_analyzer.enums import CinemaChain
from cinema_repertoire_analyzer.ratings_api.models import TmdbMovieDetails


def cinema_input_parser(cinema_name: str) -> CinemaChain:
    """Parse cinema name input to match the format of the config file."""
    try:
        return CinemaChain[cinema_name.upper().replace(" ", "_").replace("-", "_")]
    except KeyError:
        raise typer.BadParameter(
            f'Kino "{cinema_name}" nie jest wspierane. Wybierz jedno z: '
            f'{", ".join(CinemaChain.__members__.values())}'
        )


def cinema_venue_input_parser(cinema_venue: str) -> str:
    """Parse cinema venue input to prepare it for querying the db in a permissive way."""
    non_letters_removed = re.sub(r"\W", " ", cinema_venue)
    whitespaces_trimmed = re.sub(r"\s+", ",", non_letters_removed)
    nonascii_removed = re.sub(r"[^\x00-\x7F]", "_", whitespaces_trimmed)
    return f"%{nonascii_removed.replace(",", "%")}%"


def date_input_parser(date: str) -> str:
    """Parse date input to match the expected format.

    Returns:
        Date in the format YYYY-MM-DD.
    """
    if date in {"dziś", "dzis", "dzisiaj", "today"}:
        return datetime.now().strftime("%Y-%m-%d")
    if date in {"jutro", "tomorrow"}:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        # If date is given, verify if it's in the expected format
        datetime.strptime(date, "%Y-%m-%d")
        return date
    except ValueError:
        raise typer.BadParameter(
            f"Data: {date} nie jest we wspieranym formacie: YYYY-MM-DD | dzis | jutro | itp..."
        )


def _venue_results_to_table_title(venue: CinemaVenuesBase) -> str:
    """Convert venue results to a table title."""
    venues_class_to_table_title_mapping = {
        "cinema_city_venues": "Cinema City",
        "multikino_venues": "Multikino",
        "helios_venues": "Helios",
    }
    return f"Lokale sieci {venues_class_to_table_title_mapping[venue.__table__.name]}"


def db_venues_to_cli(venues: list[CinemaVenuesBase], sink: rich.console.Console) -> None:
    """Print cinema venues as a pretty-printed table in a console."""
    if not venues:
        sink.print("Brak kin tej sieci w bazie danych.")
        return
    table = Table(title=_venue_results_to_table_title(venues[0]))
    for column in venues[0].__table__.columns:
        table.add_column(column.name)
    for venue in venues:
        table.add_row(*venue.list_values())

    sink.print(table)


def repertoire_to_cli(
    repertoire: list[Repertoire],
    table_metadata: RepertoireCliTableMetadata,
    ratings: dict[str, TmdbMovieDetails],
    sink: rich.console.Console,
) -> None:
    """Print a repertoire as a pretty-printed table in a console."""
    if not repertoire:
        sink.print("Brak repertuaru do wyświetlenia.")
        return
    table = Table(
        title=f"Repertuar dla {table_metadata.cinema_chain_name} "
        f"({table_metadata.cinema_venue_name}) na dzień: {table_metadata.repertoire_date}",
        show_lines=True,
        header_style="bold",
    )
    table.add_column("Tytuł", max_width=20)
    table.add_column("Gatunki", max_width=15)
    table.add_column("Długość")
    table.add_column("Język\noryg.")
    table.add_column("Seanse", max_width=20)
    if ratings:
        table.add_column("Ocena z TMDB")
        table.add_column("Opis z TMDB")
    for movie in repertoire:
        row_content = [
            movie.title,
            movie.genres,
            movie.play_length,
            movie.original_language,
            "\n".join(
                [
                    f"[{play.format}, {play.play_language}]:\n{" ".join(play.play_times)}"
                    for play in movie.play_details
                ]
            ),
        ]
        if ratings:
            row_content.append(ratings[movie.title].rating)
            row_content.append(ratings[movie.title].summary)

        table.add_row(*row_content)
    sink.print(table)
