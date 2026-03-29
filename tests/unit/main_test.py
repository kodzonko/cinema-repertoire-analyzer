import pytest

from cinema_repertoire_analyzer.database.models import CinemaVenues
from cinema_repertoire_analyzer.exceptions import AmbiguousVenueMatchError, VenueNotFoundError
from cinema_repertoire_analyzer.main import _resolve_single_venue


@pytest.mark.unit
def test_resolve_single_venue_returns_single_match() -> None:
    venue = CinemaVenues(venue_name="Warszawa - Janki", venue_id="1")

    assert _resolve_single_venue([venue]) == venue


@pytest.mark.unit
def test_resolve_single_venue_raises_not_found_for_empty_result() -> None:
    with pytest.raises(VenueNotFoundError):
        _resolve_single_venue([])


@pytest.mark.unit
def test_resolve_single_venue_raises_ambiguous_for_multiple_matches() -> None:
    with pytest.raises(AmbiguousVenueMatchError):
        _resolve_single_venue(
            [
                CinemaVenues(venue_name="Warszawa - Janki", venue_id="1"),
                CinemaVenues(venue_name="Warszawa - Arkadia", venue_id="2"),
            ]
        )
