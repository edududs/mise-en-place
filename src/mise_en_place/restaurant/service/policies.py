"""A política escolhe a chave; fila e workers continuam donos da execução."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from ..orders import OrderItem

type PriorityKey = tuple[float, int, int, int]


class SchedulingMode(StrEnum):
    EDF = "edf"
    FIFO = "fifo"


class SchedulingPolicy(Protocol):
    def key(self, item: OrderItem, deadline: float, sequence: int) -> PriorityKey: ...


class EarliestDeadline:
    def key(self, item: OrderItem, deadline: float, sequence: int) -> PriorityKey:
        return deadline, int(item.recipe.course), item.index, sequence


class FirstInFirstOut:
    def key(self, item: OrderItem, deadline: float, sequence: int) -> PriorityKey:  # noqa: ARG002
        return 0.0, 0, 0, sequence


POLICIES: dict[SchedulingMode, SchedulingPolicy] = {
    SchedulingMode.EDF: EarliestDeadline(),
    SchedulingMode.FIFO: FirstInFirstOut(),
}


# As lições: chave estática; sequência desempata; política não promete capacidade infinita.
