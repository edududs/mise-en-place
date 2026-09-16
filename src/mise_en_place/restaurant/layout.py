"""Invent?rio inicial: dados compartilhados pela configura??o e montagem."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from .menu import Station

COOKS_ON_SHIFT: Final = 3
BARTENDERS_ON_SHIFT: Final = 1
WAITERS_ON_SHIFT: Final = 3
WAITER_NAMES: Final[tuple[str, ...]] = ("Ana", "Bia", "Caio", "Dora")

# O inventário físico de cada praça. Estes números são o botão de regência do
# gargalo: uma chapa e uma fritadeira criam disputa real; tirar um forno e medir
# de novo é o experimento do ex5.
KITCHEN_STATIONS: Final[Mapping[Station, int]] = {
    Station.COLD_LINE: 2,
    Station.STOVE: 3,
    Station.GRIDDLE: 1,
    Station.FRYER: 1,
    Station.OVEN: 2,
}
BAR_STATIONS: Final[Mapping[Station, int]] = {
    Station.BAR_COUNTER: 2,
    Station.SHAKER: 1,
    Station.TAP: 1,
}
