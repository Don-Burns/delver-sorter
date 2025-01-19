import pytest

from delver_sorter import (
    Card,
    parse_color,
    sort_by_wubrg,
    sort_cards_by_defaults,
    trim_unchanged_cards,
)


@pytest.mark.parametrize(
    ("input_", "expected"),
    (
        pytest.param(r"{1}", "", id="Colourless"),
        pytest.param(r"{1}{U}", "U", id="Blue"),
        pytest.param(r"{1}{G}", "G", id="Green"),
        pytest.param(r"{1}{B}{G}", "BG", id="Golgari"),
        pytest.param(r"{1}{G}{G}", "G", id="Double Color"),
        pytest.param(r"{U}{B}{R}{W}{G}", "WUBRG", id="WUBRG"),
    ),
)
def test_color_parsing(input_: str, expected: str):
    assert parse_color(input_) == expected


@pytest.mark.parametrize(
    ("input_", "expected"),
    (
        pytest.param("BURGW", "WUBRG", id="WUBRG"),
        pytest.param("GRW", "WRG", id="Naya"),
        pytest.param("GB", "BG", id="Golgari"),
    ),
)
def test_sort_wubrg(input_: str, expected: str):
    assert sort_by_wubrg(input_) == expected


def gen_card(
    *,
    color: str,
    cmc: int,
    card_name: str,
    owned: int | None = None,
    incoming: int | None = None,
) -> Card:
    color = sort_by_wubrg(color)
    return Card(
        color=color,
        cmc=cmc,
        card_name=card_name,
        mana_cost="".join(f"{{{c}}}" for c in color),
        owned=owned,
        incoming=incoming,
    )


@pytest.mark.parametrize(
    ("input_", "expected"),
    (
        pytest.param(
            [
                gen_card(color="W", cmc=1, card_name=""),
                gen_card(color="U", cmc=1, card_name=""),
                gen_card(color="WUBR", cmc=1, card_name=""),
                gen_card(color="UBRG", cmc=1, card_name=""),
                gen_card(color="WUBRG", cmc=1, card_name=""),
            ],
            [
                gen_card(color="W", cmc=1, card_name=""),
                gen_card(color="U", cmc=1, card_name=""),
                gen_card(color="WUBR", cmc=1, card_name=""),
                gen_card(color="UBRG", cmc=1, card_name=""),
                gen_card(color="WUBRG", cmc=1, card_name=""),
            ],
            id="No Change",
        ),
        pytest.param(
            [
                gen_card(color="B", cmc=1, card_name=""),
                gen_card(color="R", cmc=1, card_name=""),
                gen_card(color="G", cmc=1, card_name=""),
                gen_card(color="U", cmc=1, card_name=""),
                gen_card(color="W", cmc=1, card_name=""),
            ],
            [
                gen_card(color="W", cmc=1, card_name=""),
                gen_card(color="U", cmc=1, card_name=""),
                gen_card(color="B", cmc=1, card_name=""),
                gen_card(color="R", cmc=1, card_name=""),
                gen_card(color="G", cmc=1, card_name=""),
            ],
            id="Test Mono color order",
        ),
        # Below are specific bugs that were found as I used the process
        pytest.param(
            [
                gen_card(color="RG", cmc=4, card_name="Rosheen, Roaring Prophet"),
                gen_card(color="RG", cmc=4, card_name="Radha, Coalition Warlord"),
                gen_card(color="WUB", cmc=4, card_name="Sidar Jabari of Zhalfir"),
                gen_card(color="RG", cmc=4, card_name="Tana, the Bloodsower	"),
            ],
            [
                gen_card(color="RG", cmc=4, card_name="Radha, Coalition Warlord"),
                gen_card(color="RG", cmc=4, card_name="Rosheen, Roaring Prophet"),
                gen_card(color="RG", cmc=4, card_name="Tana, the Bloodsower	"),
                gen_card(color="WUB", cmc=4, card_name="Sidar Jabari of Zhalfir"),
            ],
            id="Test Multi color order 1",
        ),
        pytest.param(
            [
                gen_card(color="UG", cmc=4, card_name="Jyoti, Moag Ancient"),
                gen_card(color="UG", cmc=3, card_name="Primal Empathy"),
                gen_card(color="UR", cmc=3, card_name="Pain Magnification"),
                gen_card(color="UR", cmc=3, card_name="Mayhem Devil"),
                gen_card(color="UG", cmc=3, card_name="Edric, Spymaster of Trest"),
            ],
            [
                gen_card(color="UR", cmc=3, card_name="Mayhem Devil"),
                gen_card(color="UR", cmc=3, card_name="Pain Magnification"),
                gen_card(color="UG", cmc=3, card_name="Edric, Spymaster of Trest"),
                gen_card(color="UG", cmc=3, card_name="Primal Empathy"),
                gen_card(color="UG", cmc=4, card_name="Jyoti, Moag Ancient"),
            ],
            id="Test Multi color order 2",
        ),
        pytest.param(
            [
                gen_card(
                    card_name="Baleful Strix", cmc=2, color="UB", owned=1, incoming=1
                ),
                gen_card(
                    card_name="Boros Charm", cmc=2, color="WR", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Heartflame Duelist // Heartflame Slash",
                    cmc=2,
                    color="WR",
                    owned=1,
                    incoming=0,
                ),
                gen_card(
                    card_name="Inkfathom Witch", cmc=2, color="UB", owned=0, incoming=1
                ),
                gen_card(
                    card_name="Lightning Helix", cmc=2, color="WR", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Lightning Helix", cmc=2, color="WR", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Likeness Looter", cmc=2, color="UB", owned=0, incoming=1
                ),
                gen_card(
                    card_name="Mask of Riddles", cmc=2, color="UB", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Mirror-Shield Hoplite",
                    cmc=2,
                    color="WR",
                    owned=1,
                    incoming=0,
                ),
                gen_card(
                    card_name="Obyra, Dreaming Duelist",
                    cmc=2,
                    color="UB",
                    owned=0,
                    incoming=1,
                ),
                gen_card(card_name="Rip Apart", cmc=2, color="WR", owned=1, incoming=0),
            ],
            [
                gen_card(
                    card_name="Baleful Strix", cmc=2, color="UB", owned=1, incoming=1
                ),
                gen_card(
                    card_name="Inkfathom Witch", cmc=2, color="UB", owned=0, incoming=1
                ),
                gen_card(
                    card_name="Likeness Looter", cmc=2, color="UB", owned=0, incoming=1
                ),
                gen_card(
                    card_name="Mask of Riddles", cmc=2, color="UB", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Obyra, Dreaming Duelist",
                    cmc=2,
                    color="UB",
                    owned=0,
                    incoming=1,
                ),
                gen_card(
                    card_name="Boros Charm", cmc=2, color="WR", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Heartflame Duelist // Heartflame Slash",
                    cmc=2,
                    color="WR",
                    owned=1,
                    incoming=0,
                ),
                gen_card(
                    card_name="Lightning Helix", cmc=2, color="WR", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Lightning Helix", cmc=2, color="WR", owned=1, incoming=0
                ),
                gen_card(
                    card_name="Mirror-Shield Hoplite",
                    cmc=2,
                    color="WR",
                    owned=1,
                    incoming=0,
                ),
                gen_card(card_name="Rip Apart", cmc=2, color="WR", owned=1, incoming=0),
            ],
            id="Test Multi color order 3",
        ),
        pytest.param(
            [
                gen_card(
                    card_name="Nature's Will", cmc=4, color="G", owned=0, incoming=1
                ),
                gen_card(
                    card_name="Ruxa, Patient Professor",
                    cmc=4,
                    color="G",
                    owned=1,
                    incoming=0,
                ),
                gen_card(
                    card_name="Neva, Stalked by Nightmares",
                    cmc=4,
                    color="WB",
                    owned=1,
                    incoming=0,
                ),
            ],
            [
                gen_card(
                    card_name="Nature's Will", cmc=4, color="G", owned=0, incoming=1
                ),
                gen_card(
                    card_name="Ruxa, Patient Professor",
                    cmc=4,
                    color="G",
                    owned=1,
                    incoming=0,
                ),
                gen_card(
                    card_name="Neva, Stalked by Nightmares",
                    cmc=4,
                    color="WB",
                    owned=1,
                    incoming=0,
                ),
            ],
            id="Test Multi color order 3",
        ),
    ),
)
def test_sort_by_defaults(input_: list[Card], expected: list[Card]):
    assert sort_cards_by_defaults(input_) == expected


@pytest.mark.parametrize(
    ("input_", "expected"),
    (
        pytest.param([], [], id="empty"),
        pytest.param(
            [
                gen_card(color="U", cmc=2, card_name="1", owned=1),
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
                gen_card(color="U", cmc=2, card_name="4", owned=1),
                gen_card(color="U", cmc=2, card_name="5", owned=1),
            ],
            [
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
                gen_card(color="U", cmc=2, card_name="4", owned=1),
            ],
            id="normal_case",
        ),
        pytest.param(
            [
                gen_card(color="U", cmc=2, card_name="1", owned=1),
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", owned=1, incoming=1),
                gen_card(color="U", cmc=2, card_name="4", owned=1),
                gen_card(color="U", cmc=2, card_name="5", owned=1),
            ],
            [
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", owned=1, incoming=1),
                gen_card(color="U", cmc=2, card_name="4", owned=1),
            ],
            id="mix_incoming_and_owned_of_same_card",
        ),
        pytest.param(
            [
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
                gen_card(color="U", cmc=2, card_name="4", owned=1),
                gen_card(color="U", cmc=2, card_name="5", owned=1),
            ],
            [
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
                gen_card(color="U", cmc=2, card_name="4", owned=1),
            ],
            id="start_with_incoming",
        ),
        pytest.param(
            [
                gen_card(color="U", cmc=2, card_name="1", owned=1),
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
            ],
            [
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
            ],
            id="end_with_incoming",
        ),
        pytest.param(
            [
                gen_card(color="U", cmc=2, card_name="1", owned=1),
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
                gen_card(color="U", cmc=2, card_name="4", incoming=1),
                gen_card(color="U", cmc=2, card_name="5", owned=1),
            ],
            [
                gen_card(color="U", cmc=2, card_name="2", owned=1),
                gen_card(color="U", cmc=2, card_name="3", incoming=1),
                gen_card(color="U", cmc=2, card_name="4", incoming=1),
                gen_card(color="U", cmc=2, card_name="5", owned=1),
            ],
            id="back_to_back_incoming",
        ),
    ),
)
def test_trim_unchanged_cards(input_: list[Card], expected: list[Card]):
    assert trim_unchanged_cards(input_) == expected
