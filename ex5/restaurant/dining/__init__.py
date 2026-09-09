"""O salão: mesas (recurso físico) e garçons (recurso humano)."""

from __future__ import annotations

from .seating import DINING_ROOM, Seating, Table
from .waiter import MINUTES_BY_REASON, Call, Reason, Waiter, WaitStaff

__all__ = [
    "DINING_ROOM",
    "MINUTES_BY_REASON",
    "Call",
    "Reason",
    "Seating",
    "Table",
    "WaitStaff",
    "Waiter",
]
