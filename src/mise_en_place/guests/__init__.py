"""A clientela: as pessoas que chegam, decidem e vão embora.

Este package NÃO conhece asyncio-de-cozinha, praça, orquestrador, garçom ou
métrica. Ele conhece: o cardápio (as pessoas leem o menu), o tipo do pedido, e
a PORTA que declara o que precisa de um restaurante.

Regra verificável da fronteira:
    grep -rE "servico|orquestrador|praca|preparador" ex4/clientela/   # vazio
"""

from __future__ import annotations

from .arrivals import ARRIVAL_RATE_PER_MINUTE, ARRIVAL_WINDOW_MINUTES, party_stream
from .party import Party
from .ports import FrontOfHouse
from .profiles import PROFILES, Profile, Style

__all__ = [
    "ARRIVAL_RATE_PER_MINUTE",
    "ARRIVAL_WINDOW_MINUTES",
    "PROFILES",
    "FrontOfHouse",
    "Party",
    "Profile",
    "Style",
    "party_stream",
]
