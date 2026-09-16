"""Quem executa: cozinheiro e barman são a MESMA classe.

A diferença entre os dois é *configuração* (qual praça, quais estações), não
código — o laço é idêntico. Uma hierarquia `Trabalhador → Cozinheiro/Barman`
seria DRY violado com passos extras. Os dois nomes seguem existindo no
vocabulário da aula, como instâncias: `chef-1`, `barman-1`.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Final

from ..core.clock import Clock
from ..core.errors import DishBurnedError
from ..menu import Step
from ..observability import Event, EventKind, Journal
from ..orders import OrderItem
from .line import Dispatch, Line

ITEM_TIMEOUT_MINUTES: Final = 35.0
ATTEMPTS_PER_ITEM: Final = 2
BURN_CHANCE_PER_STEP: Final = 0.02


class Preparer:
    """Puxa da praça, ocupa a estação de cada passo, cronometra, refaz se queimar."""

    def __init__(
        self,
        name: str,
        *,
        line: Line,
        clock: Clock,
        journal: Journal,
        rng: random.Random,
        timeout_minutes: float = ITEM_TIMEOUT_MINUTES,
        attempts: int = ATTEMPTS_PER_ITEM,
    ) -> None:
        self.name = name
        self.section = line.section
        # o cozinheiro FICA com o item do início ao fim, inclusive enquanto
        # espera vaga na estação. É essa a ocupação que importa medir — e era
        # exatamente a que faltava no relatório da aula 4.
        self.busy_minutes = 0.0
        self.items = 0
        self._line = line
        self._clock = clock
        self._journal = journal
        self._rng = rng  # injetado: `random.seed()` global seria 2ª fonte de verdade
        self._timeout_minutes = timeout_minutes
        self._attempts = attempts

    async def work(self) -> None:
        """O turno inteiro. Sai pela porta da frente quando a praça fecha."""
        while True:
            try:
                despacho = await self._line.next_dispatch()
            except asyncio.QueueShutDown:  # fim de turno, sem `cancel()`
                return
            started_s = time.perf_counter()
            try:
                await self._handle(despacho)
            finally:
                self.items += 1
                self.busy_minutes += self._clock.minutes_from(time.perf_counter() - started_s)
                self._line.complete()  # é isso que faz o `drenar()` retornar

    async def _handle(self, despacho: Dispatch) -> None:
        deadline_s = self._clock.deadline_s(self._timeout_minutes)

        for _ in range(self._attempts):
            try:
                async with asyncio.timeout(deadline_s):
                    spent_minutes = await self._run_steps(despacho.item)
            except TimeoutError:
                self._record(EventKind.LATE, despacho.item, "travou na estação")
                break
            except DishBurnedError as error:
                # refaz. O prazo NÃO muda — e é justamente por isso que o EDF
                # coloca a refação na frente da fila sozinho, sem nenhuma regra
                # de "prioridade de retrabalho".
                self._record(EventKind.BURNED, despacho.item, str(error))
                continue
            else:
                self._deliver(despacho, spent_minutes)
                return

        self._fail(despacho)

    async def _run_steps(self, item: OrderItem) -> float:
        """Consome o plano da receita. Nenhum nome de prato aparece aqui."""
        spent_minutes = 0.0
        for step in item.recipe.steps():
            async with self._line.occupy(step.station):
                await self._clock.wait(step.minutes)
                spent_minutes += step.minutes
                self._maybe_burn(step)
        return spent_minutes

    def _maybe_burn(self, step: Step) -> None:
        """Queimar é risco de OPERAÇÃO, não item da receita — por isso mora aqui.

        O sorteio vem de um `random.Random` INJETADO, nunca do `random` global:
        o global é uma segunda fonte de verdade (qualquer código que chame
        `random.*` rouba números da sequência e a aula deixa de sair igual).
        """
        if self._rng.random() < BURN_CHANCE_PER_STEP:
            raise DishBurnedError(f"deu errado ao {step.description}")

    def _deliver(self, despacho: Dispatch, spent_minutes: float) -> None:
        if despacho.ready.done():  # guard: quem pediu já desistiu
            return
        despacho.ready.set_result(spent_minutes)

    def _fail(self, despacho: Dispatch) -> None:
        if despacho.ready.done():
            return
        despacho.ready.set_exception(
            DishBurnedError(f"{despacho.item} perdido após {self._attempts} tentativas")
        )

    def _record(self, kind: EventKind, item: OrderItem, detail: str) -> None:
        self._journal.record(
            Event(
                kind=kind,
                at_minute=self._clock.minutes(),
                who=self.name,
                detail=f"{item}: {detail}",
                course=item.recipe.course,
            )
        )
