"""A praça: uma fila priorizada + estações próprias + brigada própria.

A cozinha é uma praça, o bar é outra, e elas **não compartilham nada**. É isso —
e só isso — que faz "o drink chega enquanto o risoto ainda está no fogo"
funcionar sem um único `if curso == DRINK` em lugar nenhum do código.

Topologia escolhida: **uma fila por praça, estação como `Semaphore` adquirido
sob demanda** — e não uma fila por estação. A regra que sustenta a decisão:
*o prato é a unidade de trabalho; a estação é recurso, não fila.* Prioridade só
significa alguma coisa se existir UMA fila onde comparar.
Trade-off nomeado: perde-se afinidade e batching por estação (assar 3 frangos
no mesmo ciclo do forno). Fica registrado como possível evolução.
"""

from __future__ import annotations

import asyncio
import itertools
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Final

from ..core.clock import Clock
from ..core.errors import UnknownStationError
from ..menu import Course, Section, Station
from ..orders import OrderItem

QUEUE_SIZE: Final = 40


@dataclass(frozen=True, slots=True, order=True)
class Dispatch:
    """O que entra na fila — e a CHAVE de ordenação são os 4 primeiros campos.

        (prazo_min, curso, indice, sequencia)

    EDF (earliest deadline first): quem prometi entregar primeiro sai primeiro.
    É starvation-free **por construção**, porque o prazo é absoluto e estático:
    um pedido velho só pode virar o de prazo mais próximo, nunca o mais distante.
    Prioridade estrita (VIP sempre na frente) deixaria o pedido comum eternamente
    parado — medido: `NUNCA SERVIDO`.

    `sequencia` NÃO é enfeite: sem um desempate único, dois despachos com a mesma
    chave fazem o heap comparar o payload e estourar
    `TypeError: '<' not supported between instances of 'Despacho'`. Ela também
    torna o desempate FIFO-estável.

    `compare=False` nos dois últimos campos: eles viajam, não ordenam.
    """

    deadline: float
    course: Course
    index: int
    sequence: int
    item: OrderItem = field(compare=False)
    ready: asyncio.Future[float] = field(compare=False)


class Line:
    """Mecanismo puro: enfileirar, ordenar, emprestar estação, fechar o turno."""

    def __init__(
        self,
        section: Section,
        clock: Clock,
        *,
        slots: Mapping[Station, int],
        tamanho_da_fila: int = QUEUE_SIZE,
    ) -> None:
        self.section = section
        self._clock = clock
        self._queue: asyncio.PriorityQueue[Dispatch] = asyncio.PriorityQueue(
            maxsize=tamanho_da_fila
        )
        self._slots = {station: asyncio.Semaphore(count) for station, count in slots.items()}
        self._busy_minutes: defaultdict[Station, float] = defaultdict(float)
        self._sequence = itertools.count()

    async def enqueue(self, item: OrderItem, *, deadline: float) -> asyncio.Future[float]:
        """Põe o item na fila e devolve o `Future` que o chamador aguarda.

        O `await` do `put` É o backpressure: com a fila cheia, quem pediu espera
        aqui em vez de o restaurante aceitar trabalho que não vai dar conta.
        """
        ready: asyncio.Future[float] = asyncio.get_running_loop().create_future()
        await self._queue.put(
            Dispatch(
                deadline=deadline,
                course=item.recipe.course,
                index=item.index,
                sequence=next(self._sequence),
                item=item,
                ready=ready,
            )
        )
        return ready

    async def next_dispatch(self) -> Dispatch:
        """Levanta `asyncio.QueueShutDown` quando a praça fecha."""
        return await self._queue.get()

    def complete(self) -> None:
        self._queue.task_done()

    async def drain(self) -> None:
        await self._queue.join()

    def close(self) -> None:
        """`shutdown()` (novidade do 3.13) aposenta o `cancel()` do ex1/ex2:
        os preparadores saem por `except asyncio.QueueShutDown`, sozinhos.
        """
        self._queue.shutdown()

    @asynccontextmanager
    async def occupy(self, station: Station) -> AsyncIterator[Station]:
        """Uma vaga da estação, devolvida SEMPRE — inclusive sob cancelamento."""
        slot = self._slots.get(station)
        if slot is None:  # guard clause: cardápio pedindo estação que não existe
            raise UnknownStationError(
                f"a praça {self.section} não tem {station} — cardápio e inventário divergiram"
            )
        async with slot:
            started_s = time.perf_counter()
            try:
                yield station
            finally:
                # roda no sucesso, no erro e no cancelamento: sem isto um prato
                # cancelado deixaria a chapa "ocupada" no relatório pra sempre
                self._busy_minutes[station] += self._clock.minutes_from(
                    time.perf_counter() - started_s
                )

    def busy_minutes(self) -> Mapping[Station, float]:
        """Quanto tempo cada estação passou realmente ocupada."""
        return dict(self._busy_minutes)
