"""Entrada CLI: traduz argumentos, monta colaboradores e apresenta resultados."""

from __future__ import annotations

import argparse
import asyncio
import random
from pathlib import Path
from typing import Final

from .adapters.console import configure_output
from .adapters.demand import PopulationDemand
from .adapters.report import render
from .adapters.storage import JsonResultStore
from .application.archive import archive
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
    """Reutiliza sementes; tempos e entrelaçamento do asyncio ainda podem variar."""
    clock = Clock(minute_s=MEASUREMENT_MINUTE_S)
    master = random.Random(SERVICE_SEED)
    casa = build_restaurant(
        clock,
        rng=random.Random(master.randrange(MAX_SEED)),
        journal=TerminalJournal(clock, verbose=False),  # medição não narra
        cooks=scenario.cooks,
        waiters=scenario.waiters,
        kitchen_slots=scenario.kitchen_slots,
        scheduling=scenario.scheduling,
    )

    return await execute(RunShift(scenario.name), casa, PopulationDemand(clock, master))


async def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(description="Experimentos do restaurante")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--results-dir", type=Path)
    parser.add_argument("--show", type=str, help="identificador de um resultado salvo")
    args = parser.parse_args()
    if args.show:
        if args.results_dir is None:
            parser.error("--show exige --results-dir")
        try:
            saved = JsonResultStore(args.results_dir).load(args.show)
        except (ValueError, OSError) as error:
            parser.error(str(error))
        if saved is None:
            parser.error("resultado não encontrado")
        render((saved,))
        return
    try:
        scenarios = load_scenarios(args.config) if args.config else SCENARIOS
    except (ValueError, OSError) as error:
        parser.error(str(error))
    measurements = tuple([await measure(scenario) for scenario in scenarios])
    if args.results_dir is not None:
        store = JsonResultStore(args.results_dir)
        for index, result in enumerate(measurements, start=1):
            archive(f"scenario-{index}", result, store)
    render(measurements)


if __name__ == "__main__":
    # Troque por `asyncio.run(main(), debug=True)` para ver o Python acusar
    # qualquer coisa que segure o event loop por mais de 100ms.
    asyncio.run(main())
