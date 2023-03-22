import json
import logging
import os
import re
from datetime import date
from json import JSONDecodeError
from pathlib import Path
from typing import List, Optional, Union

from _typeshed import AnyPath
from requests_html import HTMLSession

_json_default_path = Path(
    os.getcwd(), "cinemas_list.json"
)  # default path is in the project directory


def get_repertoire(
    cinema: str,
    path: AnyPath = _json_default_path,
    repertoire_date: str = date.today(),
) -> Optional[List[str]]:
    """
    Get repertoire for a specified cinema and date from www.cinema-city.pl
    :param cinema: name of a cinema for which you want to check the repertoire
    :param path: path to json file containing cinemas and their respective IDs
    :param repertoire_date: date for which to check the repertoire, defaults to today
    :return: a list of films names in the repertoire
             or an empty list if the operation failed
             or if there are no films available in that date
    """
    cinema_id = _match_cinema_name_id(cinema, path)

    # TODO: Add exception handling
    session = HTMLSession()
    response_html = session.get(
        f"https://www.cinema-city.pl/#/buy-tickets-by-cinema?in-cinema={cinema_id}&at={repertoire_date}"
    )
    # render JS elements, required to get full page with films
    response_html.html.render()

    # from downloaded website select only elements containing films titles
    films = response_html.html.find(selector="h3.qb-movie-name")
    return [film.text for film in films]  # Convert HTML Elements into strings


def get_cinemas_list(
    path: AnyPath = _json_default_path,
) -> Optional[dict[str, int]]:
    """
    Get all available cinemas with their respective IDs from a json file
    :return: dictionary with cinema name as a key and ID as a value
    """
    _path = Path(path)
    try:
        with open(file=_path, mode="r", encoding="utf8") as f:
            return json.load(f).get("cinema-city")
    except JSONDecodeError:
        logging.error(f"Incorrect JSON file {path}")
    except FileNotFoundError:
        logging.error(f"Missing {path}")


def download_cinemas_list() -> dict:
    """
    Get all available cinemas with their respective IDs from www.cinema-city.pl
    and parse it to a dictionary.

    :return: a dictionary with <cinema_name>: <cinema_id> items
    """
    # TODO: Add exception handling
    session = HTMLSession()
    response_html = session.get(
        "https://www.cinema-city.pl/#/buy-tickets-by-cinema", verify=False
    )
    # render JS elements, required to get full
    response_html.html.render()
    # from downloaded website select only elements containing films titles
    cinemas = response_html.html.find(selector="option[value][data-tokens]")

    # get a list of cinema names from the elements
    venues = [cinema.element.get("data-tokens") for cinema in cinemas]
    # get a list of cinema ids from the elements (needed to construct a valid url to get repertoire)
    ids = [int(cinema.element.get("value")) for cinema in cinemas]
    # make dictionary of venue name - id pairs
    return dict(zip(venues, ids))


def _update_cinemas_list(
    updated_cinemas: dict, path: Union[str, Path] = _json_default_path
) -> None:
    """
    Get all available cinemas with their respective IDs from www.cinema-city.pl
    :updated_cinemas:
    :path: a path to json file to store a list of cinema venues in
    :return: None
    """
    _path = Path(path)

    # TODO: Add exception handling
    cinemas = {}
    with open(file=_path, mode="r", encoding="utf8") as f:
        try:
            cinemas = json.load(fp=f)
        except JSONDecodeError:
            logging.info("Missing json file with cinemas list. Populating content")

    with open(file=_path, mode="w", encoding="utf8") as f:
        try:
            cinemas["cinema-city"].update(updated_cinemas)
        except KeyError:
            cinemas["cinema-city"] = updated_cinemas
        json.dump(obj=cinemas, fp=f, ensure_ascii=False, indent=4)


def _match_cinema_name_id(
    name: str, path: AnyPath = _json_default_path
) -> Optional[int]:
    """
    Returns id of a cinema specified by name. Based on cinema-list.json
    :param name: name of a cinema, case insensitive
    :return: id of a cinema or None if no match
    """
    _path = Path(path)
    # TODO: Add exception handling
    with open(file=_path, mode="a+", encoding="utf8") as f:
        cinema_city = json.load(f).get("cinema-city")
        for cinema, id in cinema_city.items():
            if re.search(name.lower(), cinema.lower()) is not None:
                return id
    return None
