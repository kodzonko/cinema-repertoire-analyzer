from http import HTTPStatus
from typing import Any

import pytest
import requests

from cinema_repertoire_analyzer.ratings_api.models import TmdbMovieDetails
from cinema_repertoire_analyzer.ratings_api.tmdb import (
    TmdbClient,
    parse_movie_rating,
    parse_movie_summary,
)


class DummyResponse:
    def __init__(
        self, status_code: int = HTTPStatus.OK, payload: dict[str, Any] | None = None
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload


class DummySession:
    def __init__(self, responses: list[DummyResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, headers: dict[str, str], timeout: int) -> DummyResponse:
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def access_token() -> str:
    return "1234"


@pytest.fixture
def no_results_response_body() -> dict[str, Any]:
    return {"page": 1, "results": [], "total_pages": 1, "total_results": 0}


@pytest.fixture
def single_result_response_body() -> dict[str, Any]:
    return {
        "page": 1,
        "results": [{"overview": "Opis filmu.", "vote_average": 7.504, "vote_count": 4445}],
        "total_pages": 1,
        "total_results": 1,
    }


@pytest.fixture
def multiple_results_response_body() -> dict[str, Any]:
    return {
        "page": 1,
        "results": [
            {"overview": "Opis 1", "vote_average": 6.772, "vote_count": 4553},
            {"overview": "Opis 2", "vote_average": 0, "vote_count": 0},
        ],
        "total_pages": 1,
        "total_results": 2,
    }


@pytest.mark.unit
def test_verify_api_key_returns_true_for_successful_response(access_token: str) -> None:
    client = TmdbClient(session=DummySession([DummyResponse(status_code=HTTPStatus.OK)]))

    assert client.verify_api_key(access_token) is True


@pytest.mark.unit
def test_verify_api_key_returns_false_for_unsuccessful_response(access_token: str) -> None:
    client = TmdbClient(session=DummySession([DummyResponse(status_code=HTTPStatus.UNAUTHORIZED)]))

    assert client.verify_api_key(access_token) is False


@pytest.mark.unit
def test_verify_api_key_returns_false_without_access_token() -> None:
    client = TmdbClient(session=DummySession([]))

    assert client.verify_api_key(None) is False


@pytest.mark.unit
def test_verify_api_key_returns_false_when_request_fails(access_token: str) -> None:
    client = TmdbClient(session=DummySession([requests.RequestException("boom")]))

    assert client.verify_api_key(access_token) is False


@pytest.mark.unit
def test_fetch_movie_details_returns_response_body(access_token: str) -> None:
    session = DummySession([DummyResponse(payload={"results": [{"title": "Garfield"}]})])
    client = TmdbClient(session=session)

    assert client.fetch_movie_details("Garfield", access_token) == {
        "results": [{"title": "Garfield"}]
    }
    assert session.calls[0]["headers"]["Authorization"] == f"Bearer {access_token}"


@pytest.mark.unit
def test_fetch_all_movie_details_handles_request_failures(access_token: str) -> None:
    session = DummySession(
        [
            DummyResponse(payload={"results": [{"title": "Garfield"}]}),
            requests.RequestException("boom"),
        ]
    )
    client = TmdbClient(session=session)

    assert client.fetch_all_movie_details(["Garfield", "Hannibal"], access_token) == {
        "Garfield": {"results": [{"title": "Garfield"}]},
        "Hannibal": {},
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("response", "outcome"),
    [
        pytest.param("no_results_response_body", "0.0/10"),
        pytest.param("single_result_response_body", "7.504/10\n(głosy: 4445)"),
        pytest.param("multiple_results_response_body", "0.0/10"),
    ],
)
def test_parse_movie_rating_parses_rating_correctly(
    response: str, outcome: str, request: pytest.FixtureRequest
) -> None:
    assert parse_movie_rating(request.getfixturevalue(response)) == outcome


@pytest.mark.unit
@pytest.mark.parametrize(
    ("response", "outcome"),
    [
        pytest.param("no_results_response_body", "Brak opisu filmu."),
        pytest.param("single_result_response_body", "Opis filmu."),
        pytest.param("multiple_results_response_body", "Brak opisu filmu."),
    ],
)
def test_parse_movie_summary_parses_summary_correctly(
    response: str, outcome: str, request: pytest.FixtureRequest
) -> None:
    assert parse_movie_summary(request.getfixturevalue(response)) == outcome


@pytest.mark.unit
def test_get_movie_ratings_and_summaries_maps_results_to_models(access_token: str) -> None:
    client = TmdbClient(
        session=DummySession(
            [
                DummyResponse(
                    payload={
                        "results": [
                            {"overview": "Opis filmu.", "vote_average": 7.5, "vote_count": 5}
                        ]
                    }
                )
            ]
        )
    )

    assert client.get_movie_ratings_and_summaries(["Garfield"], access_token) == {
        "Garfield": TmdbMovieDetails(rating="7.5/10\n(głosy: 5)", summary="Opis filmu.")
    }
