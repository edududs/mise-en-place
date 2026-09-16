"""Pydantic na borda: o arquivo inteiro é validado antes de abrir qualquer turno."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .restaurant.layout import KITCHEN_STATIONS, WAITER_NAMES
from .restaurant.menu import MENU, Section, Station
from .restaurant.service.policies import SchedulingMode
from .scenarios import Scenario

type Capacity = Annotated[int, Field(strict=True, gt=0)]


class ScenarioInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: Annotated[str, Field(min_length=1, strict=True)]
    cooks: Capacity = 3
    waiters: Annotated[int, Field(strict=True, gt=0, le=len(WAITER_NAMES))] = 3
    kitchen_slots: dict[Station, Capacity] = Field(default_factory=lambda: dict(KITCHEN_STATIONS))
    scheduling: SchedulingMode = SchedulingMode.EDF

    @model_validator(mode="after")
    def check_inventory(self) -> Self:
        if not self.name.strip():
            raise ValueError("cenário precisa de nome legível")
        needed = {
            step.station
            for recipe in MENU.values()
            if recipe.section is Section.KITCHEN
            for step in recipe.steps()
        }
        if set(self.kitchen_slots) != needed:
            raise ValueError("inventário deve conter exatamente as estações do cardápio da cozinha")
        return self

    def to_scenario(self) -> Scenario:
        return Scenario(
            self.name, self.cooks, self.waiters, dict(self.kitchen_slots), self.scheduling
        )


class ExperimentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenarios: Annotated[list[ScenarioInput], Field(min_length=1)]


def load_scenarios(path: Path) -> tuple[Scenario, ...]:
    parsed = ExperimentInput.model_validate_json(path.read_text(encoding="utf-8"))
    return tuple(item.to_scenario() for item in parsed.scenarios)


# As lições: validar a borda uma vez; traduzir; não espalhar BaseModel pela operação.
