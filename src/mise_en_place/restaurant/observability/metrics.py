"""As métricas são um `Diario`: elas AGREGAM os mesmos eventos que o terminal
imprime. Uma fonte, dois consumidores — nada é contado duas vezes.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from statistics import mean

from ..menu import Course
from .events import Event, EventKind


@dataclass(slots=True)
class Metrics:
    """Contadores do serviço. Sem `Lock`: o expedidor é um só (ver ex2)."""

    tickets: int = 0
    rejected: int = 0
    served: int = 0
    burned: int = 0
    late: int = 0
    parties_seated: int = 0
    walkaways: int = 0
    waits: defaultdict[Course, list[float]] = field(
        default_factory=lambda: defaultdict(list), repr=False
    )

    def record(self, event: Event) -> None:
        match event.kind:
            case EventKind.ORDERED:
                self.tickets += 1
            case EventKind.REJECTED:
                self.rejected += 1
            case EventKind.BURNED:
                self.burned += 1
            case EventKind.LATE:
                self.late += 1
            case EventKind.SEATED:
                self.parties_seated += 1
            case EventKind.LEFT_QUEUE:
                self.walkaways += 1
            case EventKind.SERVED:
                self.served += 1
                if event.course is not None and event.waited is not None:
                    self.waits[event.course].append(event.waited)
            case _:
                pass

    def average_wait(self, course: Course) -> float:
        waits = self.waits[course]
        if not waits:  # guard clause: sem amostra não há média
            return 0.0
        return mean(waits)

    def lines(self) -> Iterator[str]:
        """Gerador de linhas do relatório: quem imprime decide o que fazer com elas."""
        yield (
            f"mesas         {self.parties_seated} sentadas · {self.walkaways} desistiram na porta"
        )
        yield (
            f"comandas      {self.tickets} aceitas · {self.rejected} recusadas · "
            f"{self.served} rodadas entregues · {self.burned} refeitos · "
            f"{self.late} atrasados"
        )
        for course in sorted(self.waits, key=lambda c: c.value):
            samples = len(self.waits[course])
            yield (
                f"espera        {course.label:<10} "
                f"{self.average_wait(course):5.1f}min  (n={samples})"
            )
