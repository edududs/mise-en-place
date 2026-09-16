"""As mesas: recurso físico com ATRIBUTO (capacidade), não trabalho.

Por que `Condition` e não `Event`/`Queue`: o que a mesa espera é um estado
**composto** — "existe mesa livre **e** que caiba o meu grupo". `Event` é
broadcast sem estado (acorda todo mundo e não diz nada); `Queue` modela
trabalho, não recurso com atributo. `Condition.wait_for(predicado)` é
exatamente o primitivo desse caso, e ele reavalia o predicado a cada notify.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Final

from ...contracts.models import Table
from ..core.errors import PartyTooLargeError

DINING_ROOM: Final[tuple[Table, ...]] = (
    Table(1, capacity=2),
    Table(2, capacity=2),
    Table(3, capacity=2),
    Table(4, capacity=2),
    Table(5, capacity=4),
    Table(6, capacity=4),
    Table(7, capacity=4),
    Table(8, capacity=4),
    Table(9, capacity=6),
    Table(10, capacity=6),
)


class Seating:
    """A recepção: quem senta onde, e quem espera na porta."""

    def __init__(self, seating: Sequence[Table] = DINING_ROOM) -> None:
        self._free_tables = set(seating)
        self._largest = max(table.capacity for table in seating)
        self._condition = asyncio.Condition()

    async def seat(self, size: int) -> Table:
        """Espera até existir mesa que caiba o grupo. Quem chama põe o timeout.

        A paciência do cliente NÃO mora aqui: quem decide desistir é o cliente,
        com `asyncio.timeout(paciencia)` em volta desta chamada. Este método é
        mecanismo (alocar mesa); paciência é política (do salão/cliente).
        """
        if size > self._largest:  # guard clause: nunca vai caber, não faz esperar
            raise PartyTooLargeError(
                f"grupo de {size} não cabe na maior mesa ({self._largest} lugares)"
            )
        async with self._condition:
            await self._condition.wait_for(lambda: self._best_fit(size) is not None)
            table = self._best_fit(size)
            assert table is not None  # o predicado acima já garantiu
            self._free_tables.discard(table)
            return table

    async def release(self, table: Table) -> None:
        async with self._condition:
            self._free_tables.add(table)
            self._condition.notify_all()  # a fila da porta reavalia o predicado

    def _best_fit(self, size: int) -> Table | None:
        """Menor mesa que serve: não põe um casal na mesa de 6."""
        candidates = [table for table in self._free_tables if table.capacity >= size]
        if not candidates:
            return None
        return min(candidates, key=lambda table: table.capacity)

    @property
    def occupied(self) -> int:
        return len(DINING_ROOM) - len(self._free_tables)


__all__ = ["DINING_ROOM", "Seating", "Table"]
