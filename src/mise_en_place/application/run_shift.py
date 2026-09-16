"""Executar um turno é uma intenção acionável por CLI, script ou teste."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.ports import DemandSource, ShiftOperation
from ..contracts.results import Measurement


@dataclass(frozen=True, slots=True)
class RunShift:
    name: str


async def execute(request: RunShift, house: ShiftOperation, demand: DemandSource) -> Measurement:
    async with house:
        await demand.run(house)
    return house.measurement(request.name)


# As lições: um caso de uso pode ser função; não precisa de classe com um único método.
