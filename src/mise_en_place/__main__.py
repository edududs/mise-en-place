"""
AULA 5 — Medir antes de otimizar: onde está o gargalo
=====================================================

Rode:  python3 -m ex5

A aula 4 deixou um restaurante que *funciona* e ainda assim quebra a promessa:
principal prometido em 20 min, entregue em ~53. A pergunta desta aula não é
"como deixar mais rápido" — é **onde exatamente está o gargalo**.

E a primeira lição é um erro real, cometido de propósito e mantido aqui: o
relatório da aula 4 media a ocupação das ESTAÇÕES (forno, chapa, fogão) e não
media a dos COZINHEIROS. Com esse instrumento, o forno aparecia como suspeito
e o experimento apontava pro lugar errado. O cozinheiro fica com o item do
início ao fim — inclusive enquanto espera vaga na estação — e é ele que
satura primeiro. **Instrumento errado produz conclusão errada com números
convincentes**, e isso é pior que não medir.

O EXPERIMENTO: a mesma noite (mesma semente, mesmas chegadas, mesmas escolhas)
rodada quatro vezes, mudando UMA coisa por vez.

O QUE ESTA AULA ENSINA:

1. **Meça o recurso certo.** Se o que segura o trabalho é a PESSOA e você
   instrumentou a MÁQUINA, todo o resto da análise é ficção.
2. **O gargalo é um lugar só.** Melhorar qualquer outro ponto muda o número
   daquele ponto e não move o resultado (Teoria das Restrições) — e você vai
   ver isso na tabela, não num parágrafo.
3. **Fila satura de forma não-linear.** Perto de 100% de utilização, uma
   melhora pequena na capacidade produz uma queda enorme na espera; longe da
   saturação, capacidade extra não compra nada.
4. **O relógio é injetável.** As medições rodam com `minuto_s` menor, então a
   noite inteira cabe em segundos — sem tocar em uma linha do restaurante.
5. **A ferramenta antes da técnica**: `asyncio.run(main(), debug=True)` grita
   quando algo segura o expedidor por mais de 100 ms. Rode isso ANTES de
   otimizar qualquer coisa.
"""

from __future__ import annotations

import argparse
import asyncio
import random
from contextlib import aclosing
from pathlib import Path
from typing import Final

from .bootstrap import build_restaurant
from .configuration import load_scenarios
from .guests import party_stream
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

    async with casa:
        async with asyncio.TaskGroup() as service:
            async with aclosing(party_stream(clock, master)) as arrivals:
                async for party in arrivals:
                    service.create_task(party.dine(casa), name=f"grupo-{party.number}")

    return casa.measurement(scenario.name)


def render(measurements: tuple[Measurement, ...]) -> None:
    print("═" * REPORT_WIDTH)
    print(
        f"{'cenário':<32}{'entrada':>9}{'principal':>11}"
        f"{'chef':>7}{'forno':>7}{'garçom':>8}{'rodadas':>9}{'noite':>8}"
    )
    print("─" * REPORT_WIDTH)
    for m in measurements:
        print(
            f"{m.scenario:<32}{m.starter_wait:>7.1f}m{m.main_wait:>9.1f}m"
            f"{m.cook_utilization:>7.0%}{m.oven_utilization:>7.0%}{m.waiter_utilization:>8.0%}"
            f"{m.rounds:>9}{m.minutes:>7.0f}m"
        )
    print("═" * REPORT_WIDTH)

    baseline, *others = measurements
    print("\n--- a leitura ---")
    for m in others:
        gain = baseline.main_wait - m.main_wait
        ratio = gain / baseline.main_wait
        if ratio > SOLVED_THRESHOLD:
            verdict = "RESOLVEU"
        elif ratio > EASED_THRESHOLD:
            verdict = "aliviou"
        else:
            verdict = "quase nada"
        print(f"  {m.scenario:<32} {gain:+6.1f}min no principal  → {verdict}")
    print(
        f"\n  Utilização no cenário base — cozinheiro: "
        f"{baseline.cook_utilization:.0%}, forno: {baseline.oven_utilization:.0%}, "
        f"garçom: {baseline.waiter_utilization:.0%}.\n"
        "  O recurso saturado é a RESTRIÇÃO; investir em qualquer outro lugar\n"
        "  melhora o número daquele lugar e não move o resultado. Em cozinha e\n"
        "  em software vale a mesma regra — e é por isso que 'medir antes de\n"
        "  otimizar' não é conselho de bom-mocismo, é o que separa a correção\n"
        "  que funciona da que só consome dinheiro."
    )


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
