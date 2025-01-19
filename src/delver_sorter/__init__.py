import argparse
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

import jinja2
from pydantic import BaseModel

if TYPE_CHECKING:
    import sqlite3
else:
    # use pysqlite3 instead of sqlite3 since full outer join is not supported in sqlite3<=3.39.0 which python<=3.13 uses it seems?
    # the lib is not typed so just use std lib for types, they are meant to be compatible
    import pysqlite3 as sqlite3

logger = logging.getLogger(__name__)

Connection: TypeAlias = sqlite3.Connection
Cursor: TypeAlias = sqlite3.Cursor


WUBRG_PRIORITY_DICT = {"W": 1, "U": 2, "B": 3, "R": 4, "G": 5}


class Card(BaseModel):
    card_name: str
    cmc: int
    color: str
    mana_cost: str
    owned: int | None
    incoming: int | None
    # For debugging
    sort_score: tuple[int, int, str] | None = None


@dataclass
class Args:
    db: Path


def get_args() -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("db", type=Path)
    args = parser.parse_args()

    return Args(**args.__dict__)


def dict_factory(cursor: Cursor, row: tuple[object, ...]) -> dict[str, object]:
    fields = [column[0] for column in cursor.description]
    if len(fields) != len(set(fields)):
        raise ValueError(f"Duplicate fields in cursor description: {sorted(fields)=}")

    return {key: value for key, value in zip(fields, row)}


def pull_card_data(conn: Connection) -> list[Card]:

    cur = conn.cursor()
    cur.execute(
        """
                WITH all_cards AS (
                    SELECT
                        dn.name AS card_name
                        , c._id as card_id
                        , dn.cmana AS cmc
                        , dn.color AS color_id
                        , dn.mana AS mana_cost
                        , c.quantity
                        , l.name AS list_name
                    FROM lists l
                    JOIN cards c ON c.list = l._id
                    JOIN data_cards dc ON dc._id = c.card
                    JOIN data_names dn ON dn._id = dc.name
                    /*
                    * 1 = List
                    * 2 = Deck
                    */
                    WHERE l.category = 1
                )
                , collection AS (
                    SELECT *
                    FROM all_cards
                    WHERE list_name = 'Owned'
                )
                , incoming AS (
                    SELECT *
                    FROM all_cards
                    WHERE list_name <> 'Owned'
                )
                , out_list AS (
                    SELECT
                        COALESCE(c.card_name, i.card_name) AS card_name
                        , COALESCE(c.card_id, i.card_id) AS card_id
                        , COALESCE(c.cmc, i.cmc) AS cmc
                        , COALESCE(c.color_id, i.color_id) AS color_id
                        , COALESCE(c.mana_cost, i.mana_cost) AS mana_cost
                        , c.quantity AS owned
                        , i.quantity AS incoming
                    FROM collection c
                    FULL OUTER JOIN incoming i ON c.card_name = i.card_name AND c.card_id = i.card_id
                )
                SELECT
                    card_name
                    , cmc
                    , mana_cost
                    , SUM(owned) AS owned
                    , SUM(incoming) AS incoming
                FROM out_list
                GROUP BY card_name, cmc, mana_cost
                ORDER BY color_id, cmc, card_name
                """
    )
    res = cur.fetchall()
    cur.close()

    for row in res:
        row["color"] = parse_color(row["mana_cost"])

    return [Card.model_validate(row) for row in res]


def build_html(cards: list[Card]) -> str:
    """
    Function to build the html file based on the template and input cards

    Args:
        cards (list[Card]): Cards to be included in the html

    Returns:
        str: html file as a string
    """

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(__file__).parent))
    template = env.get_template("output.tmpl.html")
    return template.render(cards=cards)


def trim_unchanged_cards(cards: list[Card]) -> list[Card]:
    prev: Card | None = None
    next_: Card | None = None
    output: list[Card] = []
    for i, c in enumerate(cards):
        if i > 0:
            prev = cards[i - 1]
        if i < len(cards) - 1:
            next_ = cards[i + 1]
        else:
            next_ = None

        if prev is not None and prev.incoming is not None:
            prev = None
        if next_ is not None and next_.incoming is not None:
            next_ = None

        if c.incoming is not None:
            if prev is not None:
                output.append(prev)
            output.append(c)
            if next_ is not None:
                output.append(next_)

    return output


def sort_by_wubrg(s: Iterable[str]) -> str:
    return "".join(sorted(s, key=lambda x: WUBRG_PRIORITY_DICT.get(x, 999)))


def parse_color(card_cost: str) -> str:
    out: set[str] = set()
    for char in card_cost:
        char = char.upper()
        if char in "WUBRG":
            out.add(char)

    return sort_by_wubrg(out)


SortScore: TypeAlias = tuple[int, int, str]


def _calculate_sort_score(card: Card) -> SortScore:

    return (
        # Need to prevent sort order from conflicting with certain combinations of colours
        # while also make sure that more colours are sorted after less colours
        sum((WUBRG_PRIORITY_DICT[c] ** 2) for c in card.color) * len(card.color) ** 10,
        card.cmc,
        card.card_name,
    )


def sort_cards_by_defaults(cards: list[Card]) -> list[Card]:
    # for card in cards:
    #     card.sort_score = key_func(card)

    return sorted(
        cards,
        key=_calculate_sort_score,
    )


def main() -> int:

    args = get_args()

    if not args.db.exists():
        logger.error("Database file does not exist - file: %s", args.db)
        return 1

    logger.info("Reading data from %s", args.db)
    with sqlite3.connect(args.db) as conn:
        conn.row_factory = dict_factory
        card_data = pull_card_data(conn)

    logger.info("Converting color_ids")
    for card in card_data:
        card.color = parse_color(card.mana_cost)

    # TODO: remove the sorting once I figure out the HTML sorting issue
    card_data = sort_cards_by_defaults(card_data)
    # add sort score
    for card in card_data:
        card.sort_score = _calculate_sort_score(card)

    logger.info("Trimming unchanged cards")
    card_data = trim_unchanged_cards(card_data)
    output_path = Path("output.html")
    logger.info("Writing output to %s", output_path.absolute())
    with output_path.open("w", encoding="utf-8") as f:
        f.write(build_html(card_data))

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
