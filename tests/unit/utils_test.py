from typing import Any

import click
import pytest

from cinema_repertoire_analyzer.cinema_api.template_utils import fill_string_template


@pytest.mark.unit
@pytest.mark.parametrize(
    "text, variables, expected",
    [
        ("fizz{a}buzz", {"a": "qwerty"}, "fizzqwertybuzz"),
        ("some{a}text{a}", {"a": "qwerty", "b": 123}, "someqwertytextqwerty"),
        (
            "lorem {a_placeholder} dolor://{other_placeholder_11}",
            {"a_placeholder": "ipsum", "other_placeholder_11": "sit", "redundant_var": False},
            "lorem ipsum dolor://sit",
        ),
        ("{} no placeholders", {"fizz": "buzz"}, "{} no placeholders"),
    ],
)
def test_fill_string_template_returns_correctly_filled_string(
    text: str, variables: dict[str, Any], expected: bool
) -> None:
    assert fill_string_template(text, **variables) == expected


@pytest.mark.unit
def test_fill_string_template_raises_error_on_missing_variable() -> None:
    with pytest.raises(click.exceptions.Exit):
        fill_string_template("{missing_variable}", a="sth", b="text")
