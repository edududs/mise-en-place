"""Entrada CLI: traduz argumentos, monta colaboradores e apresenta resultados."""

from __future__ import annotations

import argparse
import asyncio
import random
from pathlib import Path
from typing import Final

from .adapters.demand import PopulationDemand
from .adapters.report import render
from .application.run_shift import RunShift, execute
from .bootstrap import build_restaurant
from .configuration import load_scenarios
from .guests.arrivals import MAX_SEED
from .restaurant import Clock, Station, TerminalJournal
from .restaurant.layout import KITCHEN_STATIONS
from .restaurant.results import Measurement
from .scenarios import Scenario

SERVICE_SEED: Final = 7
MEASUREMENT_MINUTE_S: Final = 0.01
# Quanto da espera original precisa cair para o cenário "ter resolvido".
SOLVED_THRESHOLD: Final = 0.5
EASED_THRESHOLD: Final = 0.15  # 1 min simulado = 10 ms: a noite em ~3s
REPORT_WIDTH: Final = 92


SCENARIOS: Final[tuple[Scenario, ...]] = (
    Scenario("como está (3 chefs, 2 fornos)"),
    Scenario("+1 cozinheiro", cooks=4),
    Scenario("+1 vaga no forno", kitchen_slots={**KITCHEN_STATIONS, Station.OVEN: 3}),
    Scenario("+1 garçom", waiters=4),
    Scenario("+3 cozinheiros", cooks=6),
    Scenario(
        "+3 cozinheiros e +1 forno",
        cooks=6,
        kitchen_slots={**KITCHEN_STATIONS, Station.OVEN: 3},
    ),
)


async def measure(scenario: Scenario) -> Measurement:
    """Roda a MESMA noite com uma configuração diferente.

    A semente é a mesma em todos os cenários: as chegadas, os perfis e as
    escolhas são idênticos. Sem isso, a comparação não vale nada — seria
    ruído de simulação passando por resultado.
    """
    clock = Clock(minute_s=MEASUREMENT_MINUTE_S)
    master = random.Random(SERVICE_SEED)
    casa = build_restaurant(
        clock,
        rng=random.Random(master.randrange(MAX_SEED)),
        journal=TerminalJournal(clock, verbose=False),  # medição não narra
        cooks=scenario.cooks,
        waiters=scenario.waiters,
        kitchen_slots=scenario.kitchen_slots,
    )

    return await execute(RunShift(scenario.name), casa, PopulationDemand(clock, master))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Experimentos do restaurante")
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    scenarios = load_scenarios(args.config) if args.config else SCENARIOS
    measurements = tuple([await measure(scenario) for scenario in scenarios])
    render(measurements)


if __name__ == "__main__":
    # Troque por `asyncio.run(main(), debug=True)` para ver o Python acusar
    # qualquer coisa que segure o event loop por mais de 100ms.
    asyncio.run(main())
