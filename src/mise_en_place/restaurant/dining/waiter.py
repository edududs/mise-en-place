"""Os garçons: fila de chamados + N workers com IDENTIDADE.

Por que não `Semaphore(3)`: o semáforo daria "3 atendimentos por vez" e perderia
a *pessoa*. Sem identidade não existe "Ana atendeu 17 chamados", não existe
ocupação por garçom e não existe a lição do relatório final — que é justamente
*o gargalo pode não ser a cozinha*.

E repare: isto é o MESMO par balcão/cozinheiro do `ex1.py`, num segundo nível.
A repetição do padrão é a lição, não preguiça: fila + workers é a forma canônica
de "recurso humano escasso" em asyncio.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from ..core.clock import Clock


class Reason(StrEnum):
    TAKE_ORDER = "anotar o pedido"
    DELIVER = "servir a rodada"
    BILL = "levar a conta"


# Quanto tempo o garçom gasta em cada viagem. Aumentar isto satura a equipe
# sem tocar em uma linha de código — é o botão de regência do gargalo.
MINUTES_BY_REASON: Final[Mapping[Reason, float]] = {
    Reason.TAKE_ORDER: 2.0,
    Reason.DELIVER: 1.5,
    Reason.BILL: 2.0,
}


@dataclass(frozen=True, slots=True)
class Call:
    """Mão levantada. O `Future` é como a mesa sabe que foi atendida."""

    table: int
    reason: Reason
    handled: asyncio.Future[None]


class Waiter:
    """Um garçom: puxa chamados da fila até a equipe encerrar o turno."""

    def __init__(
        self,
        name: str,
        *,
        calls: asyncio.Queue[Call],
        clock: Clock,
    ) -> None:
        self.name = name
        self.calls_handled = 0
        self.busy_minutes = 0.0
        self._calls = calls
        self._clock = clock

    async def work(self) -> None:
        while True:
            try:
                chamado = await self._calls.get()
            except asyncio.QueueShutDown:  # fim de turno, sem `cancel()`
                return
            try:
                minutes = MINUTES_BY_REASON[chamado.reason]
                await self._clock.wait(minutes)
                self.calls_handled += 1
                self.busy_minutes += minutes
                if not chamado.handled.done():  # guard: a mesa já foi embora
                    chamado.handled.set_result(None)
            finally:
                self._calls.task_done()


class WaitStaff:
    """A escala de garçons. Mecanismo: enfileirar chamado, esperar atendimento."""

    def __init__(self, clock: Clock, *, count: int, names: tuple[str, ...]) -> None:
        self._queue: asyncio.Queue[Call] = asyncio.Queue()
        self._clock = clock
        self.waiters = tuple(
            Waiter(names[index % len(names)], calls=self._queue, clock=clock)
            for index in range(count)
        )

    async def call(self, table: int, reason: Reason) -> None:
        """Levanta a mão e ESPERA. É aqui que o gargalo do garçom aparece."""
        handled: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        await self._queue.put(Call(table=table, reason=reason, handled=handled))
        await handled

    @property
    def raised_hands(self) -> int:
        return self._queue.qsize()

    async def drain(self) -> None:
        await self._queue.join()

    def close(self) -> None:
        self._queue.shutdown()
