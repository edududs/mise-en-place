"""O orquestrador: dono da ORDEM entre mesas — e de nada mais.

O que ele NÃO sabe, de propósito:

* **o que é curso.** A sequência "entrada → come → principal" é decisão da
  mesa; ele só recebe rodadas prontas e as ordena por prazo. Um
  `if curso == PRINCIPAL` aqui dentro faria a cozinha conhecer política de
  salão — God Object na veia.
* **se o pedido é válido.** Isso é fronteira, e mora no validador.
* **como se cozinha.** Isso é a receita.

O que ele sabe: em qual praça cada item entra, e que **a rodada sai junta**.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

from ..core.clock import Clock
from ..core.errors import RestaurantError
from ..menu import Section
from ..orders import OrderItem, Ticket
from .line import Line


class Expediter:
    """Roteia os itens da rodada para as praças e espera todos ficarem prontos."""

    def __init__(self, lines: Mapping[Section, Line], clock: Clock) -> None:
        self._lines = lines
        self._clock = clock

    async def serve_round(self, ticket: Ticket) -> float:
        """Só retorna quando TODOS os itens da rodada estão prontos.

        `TaskGroup` é o primitivo certo aqui, e não `Barrier`: se um item queimar
        de vez, os irmãos são cancelados (nada de prato órfão esfriando na
        bancada) e sobe um `ExceptionGroup`. `Barrier` sozinho *deadlockaria*
        silenciosamente se uma das partes fosse cancelada antes de chegar nele —
        e ainda reportaria `broken == False`.

        A distinção que vale a aula:
          `Barrier`   sincroniza o FIM DO COZIMENTO (emplatar junto);
          `TaskGroup` sincroniza a ENTREGA (o cliente recebe junto).
        """
        async with asyncio.TaskGroup() as round_group:
            for item in ticket.items:
                round_group.create_task(
                    self._one_item(item, deadline=ticket.deadline),
                    name=f"mesa{item.table}-{item.recipe.name}",
                )
        return self._clock.minutes() - ticket.ordered_at

    async def _one_item(self, item: OrderItem, *, deadline: float) -> None:
        line = self._lines.get(item.recipe.section)
        if line is None:  # guard clause: montagem errada falha alto
            raise RestaurantError(f"não há praça para o setor {item.recipe.section}")
        ready = await line.enqueue(item, deadline=deadline)
        await ready  # a espera do cliente acontece aqui

    async def drain(self) -> None:
        """Espera todas as praças esvaziarem — fim de serviço, não fim de turno."""
        for line in self._lines.values():
            await line.drain()

    def close(self) -> None:
        for line in self._lines.values():
            line.close()
