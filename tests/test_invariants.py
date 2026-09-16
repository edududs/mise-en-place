"""O domínio se protege mesmo quando nenhuma entrada Pydantic foi usada."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mise_en_place.restaurant import Clock, Course, RawOrder
from mise_en_place.restaurant.core.values import Duration
from mise_en_place.restaurant.menu import MENU, Station
from mise_en_place.restaurant.menu.recipe import Step
from mise_en_place.restaurant.orders import Validator


@pytest.mark.parametrize("minutes", [-1.0, float("nan"), float("inf")])
def test_invalid_duration_is_rejected_without_pydantic(minutes: float) -> None:
    with pytest.raises(ValueError, match="duração"):
        Step("assar", Station.OVEN, minutes)


def test_recipe_duration_has_value_semantics() -> None:
    assert MENU["bruschetta"].duration() == Duration(5)


def test_valid_fields_can_form_invalid_ticket() -> None:
    ticket = Validator(Clock()).validate(RawOrder(1, Course.DRINK, ("chopp",)))
    with pytest.raises(ValueError, match="mesa e ao curso"):
        replace(ticket, course=Course.MAIN)
    with pytest.raises(ValueError, match="anteceder"):
        replace(ticket, deadline=ticket.ordered_at - 1)
    with pytest.raises(ValueError, match="itens"):
        replace(ticket, items=())
