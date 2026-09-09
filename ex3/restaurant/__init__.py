"""O restaurante — facade mínima.

Só sai daqui o que um ponto de entrada precisa montar e observar. `Praca`,
`Preparador`, `Orquestrador` e `Validador` são MECANISMO INTERNO: quem estiver
escrevendo um `exN.py` não deveria precisar tocar neles, e o dia em que
precisar é sinal de que falta uma porta aqui.
"""

from __future__ import annotations

from .core.clock import SIMULATED_MINUTE_S, Clock
from .core.errors import (
    DishBurnedError,
    InvalidOrderError,
    LeftTheQueueError,
    RestaurantClosedError,
    RestaurantError,
)
from .dining import Table
from .menu import ITEMS_BY_COURSE, MENU, Course, Section, Station
from .observability import Event, EventKind, Journal, Metrics, TerminalJournal
from .orders import RawOrder
from .restaurant import Restaurant

__all__ = [
    "ITEMS_BY_COURSE",
    "MENU",
    "SIMULATED_MINUTE_S",
    "Clock",
    "Course",
    "DishBurnedError",
    "Event",
    "EventKind",
    "InvalidOrderError",
    "Journal",
    "LeftTheQueueError",
    "Metrics",
    "RawOrder",
    "Restaurant",
    "RestaurantClosedError",
    "RestaurantError",
    "Section",
    "Station",
    "Table",
    "TerminalJournal",
]
