"""Apresentacao dos resultados do experimento."""

from __future__ import annotations

from ..restaurant.results import Measurement

SOLVED_THRESHOLD = 0.5
EASED_THRESHOLD = 0.15
REPORT_WIDTH = 92


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
        ratio = gain / baseline.main_wait if baseline.main_wait else 0.0
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
