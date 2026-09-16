"""Contratos pequenos permitem implementar demanda sem importar a operação."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from .models import RawOrder, Table
from .results import Measurement


class WaitingClock(Protocol):
    async def wait(self, minutes: float) -> None: ...


class FrontOfHouse(Protocol):
    @property
    def clock(self) -> WaitingClock: ...

    async def seat(self, size: int, patience_minutes: float | None = None) -> Table: ...
    async def order(self, raw: RawOrder) -> None: ...
    async def ask_for_bill(self, table: int) -> None: ...
    async def release(self, table: Table) -> None: ...


class ShiftOperation(FrontOfHouse, Protocol):
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback_: TracebackType | None,
    ) -> None: ...
    def measurement(self, scenario: str) -> Measurement: ...


class DemandSource(Protocol):
    async def run(self, house: FrontOfHouse) -> None:
        """Turno finito; aguarda os clientes iniciados e propaga cancelamento."""
        ...


# As lições: quem dirige a operação só enxerga comandos; clock é somente espera aqui.
