"""Ponto de integração para uma futura política de demanda."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ..contracts.models import RawOrder
from ..contracts.ports import FrontOfHouse


class DemandPlanner(Protocol):
    def plan(self) -> Iterable[RawOrder]:
        """Plano finito de intenções. Não autoriza nem executa pedidos."""
        ...


@dataclass(frozen=True, slots=True)
class PlannedDemand:
    planner: DemandPlanner

    async def run(self, house: FrontOfHouse) -> None:
        for intent in self.planner.plan():
            await house.order(intent)


# As lições: esta fronteira inicial não modela feedback, pathfinding ou ticks.
# Uma IA reativa exigirá contrato de observação explícito; não acesso ao runtime.
