"""A receita como SEQUÊNCIA DE PASSOS — política pura, e síncrona.

Repare no que não existe neste módulo: `asyncio`. Nenhum `await`, nenhum
`Semaphore`, nenhuma noção de fila. A receita diz O QUE fazer e ONDE; quem
ocupa a estação, cronometra e trata erro é o `Preparador` (mecanismo).

Consequência prática: dá pra testar a ordem dos passos sem event loop nenhum —
`list(bruschetta())` — e é isso que vai permitir os testes de propriedade da
etapa D do curso.

Por que UM passo ocupa UMA estação: com essa invariante o deadlock por
aquisição cruzada (uma receita pega fogão→forno, outra forno→fogão) fica
impossível por construção. Se um dia um passo precisar de duas estações, a cura
é ordem canônica global de aquisição via `AsyncExitStack` — não é o caso aqui.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from ..core.values import Duration
from .courses import Course, Section, Station


@dataclass(frozen=True, slots=True)
class Step:
    """Uma etapa atômica: o que se faz, onde, e por quanto tempo.

    `duracao_min` está em minutos SIMULADOS — o `Relogio` traduz pra espera
    real. Os números aparecem como literal nos planos abaixo de propósito: num
    argumento nomeado (`duracao_min=3.0`) o nome do campo já documenta o valor,
    e criar 40 constantes `Final` para 40 etapas pioraria a leitura.
    """

    description: str
    station: Station
    minutes: float

    def __post_init__(self) -> None:
        Duration(self.minutes)
        if not self.description.strip():
            raise ValueError("passo precisa de descrição")


# A receita guarda a FÁBRICA de passos, nunca o gerador pronto: gerador é
# consumido uma vez só, e o segundo pedido do mesmo prato sairia vazio.
type RecipePlan = Callable[[], Iterator[Step]]


@dataclass(frozen=True, slots=True)
class Recipe:
    """O item do cardápio: nome, onde é feito, em que curso entra, e o plano."""

    name: str
    course: Course
    section: Section
    plan: RecipePlan

    def steps(self) -> Iterator[Step]:
        """Um plano NOVO a cada chamada — é isso que a fábrica garante."""
        return self.plan()

    def expected_minutes(self) -> float:
        """Soma dos passos: o tempo de FORNO, sem contar fila nem disputa.

        É o piso teórico. A diferença entre isto e o tempo real medido é
        exatamente a fila — e é essa diferença que o relatório final mostra.
        """
        return sum(step.minutes for step in self.steps())

    def duration(self) -> Duration:
        """Expõe a unidade no tipo, preservando a API numérica das aulas anteriores."""
        return Duration(self.expected_minutes())
