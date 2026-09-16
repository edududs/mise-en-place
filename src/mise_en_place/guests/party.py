"""O grupo de clientes: a jornada da mesa, de chegar a pagar.

A máquina de estados é a própria coroutine `viver()` — `await` **é** o estado.
Não existe `while` com `Enum` de estado aqui, e isso é decisão registrada: numa
aula de asyncio, reimplementar à mão o que a linguagem já dá seria ensinar a
desconfiar da ferramenta. O `Enum` de estado voltaria a fazer sentido se alguém
de fora precisasse OBSERVAR a transição (aí ele é dado, não controle de fluxo).

Trade-off nomeado: para uma simulação de eventos discretos de verdade
(determinística, com heap de eventos), o certo seria um gerador de intenções
dirigido por um escalonador próprio — é o que o SimPy faz. Aí a aula deixaria
de ser sobre asyncio.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Final

from ..restaurant import Course, DishBurnedError, LeftTheQueueError, RawOrder
from ..restaurant.dining import Table
from .choices import drink_rounds, item_count, pick_items
from .ports import FrontOfHouse
from .profiles import Profile

MINUTES_BETWEEN_DRINKS: Final[tuple[float, float]] = (8.0, 20.0)
DESSERT_MINUTES: Final[tuple[float, float]] = (8.0, 14.0)


@dataclass(slots=True)
class Party:
    """As PESSOAS (não a mesa física — essa é do salão)."""

    number: int
    size: int
    profile: Profile
    rng: random.Random
    gave_up: bool = False
    complained: bool = False

    async def dine(self, casa: FrontOfHouse) -> None:
        """A noite dessa mesa, de cima pra baixo.

        Repare que o tipo do parâmetro é a PORTA (`Atendimento`), não
        `Restaurante`: este arquivo não conhece nenhuma implementação.
        """
        try:
            table = await casa.seat(self.size, self.profile.door_patience_minutes)
        except LeftTheQueueError:  # guard clause: acabou a paciência, foi embora
            self.gave_up = True
            return

        try:
            await casa.clock.wait(self._between(self.profile.menu_reading_minutes))

            async with asyncio.TaskGroup() as dinner:
                # Os drinks correm ao lado da refeição inteira — é isso que faz
                # "pediu um chopp enquanto comia a entrada e esperava o prato".
                # Drink é TASK PARALELA, não estado da mesa.
                drink_task = dinner.create_task(
                    self._drink_rounds_loop(casa, table),
                    name=f"drinks-mesa{table.number}",
                )
                await self._eat(casa, table)
                # acabou a comida: as rodadas de bebida que sobraram morrem aqui.
                # Cancelar um irmão dentro do TaskGroup é seguro — ele ignora
                # filhos cancelados (mesma lição do ex1).
                drink_task.cancel()

            await casa.ask_for_bill(table.number)
        finally:
            # a mesa física TEM que voltar pro salão, inclusive se esta task for
            # cancelada no meio — senão o restaurante "perde" uma mesa pra sempre
            await casa.release(table)

    async def _eat(self, casa: FrontOfHouse, table: Table) -> None:
        if self.rng.random() < self.profile.starter_chance:
            await self._order(casa, table, Course.STARTER)
            await casa.clock.wait(self._between(self.profile.eat_starter_minutes))

        await self._order(casa, table, Course.MAIN)
        await casa.clock.wait(self._between(self.profile.eat_main_minutes))

        if self.rng.random() < self.profile.dessert_chance:
            await self._order(casa, table, Course.DESSERT)
            await casa.clock.wait(self._between(DESSERT_MINUTES))

    async def _drink_rounds_loop(self, casa: FrontOfHouse, table: Table) -> None:
        for _ in range(drink_rounds(self.profile, self.rng)):
            await casa.clock.wait(self._between(MINUTES_BETWEEN_DRINKS))
            await self._order(casa, table, Course.DRINK)

    async def _order(self, casa: FrontOfHouse, table: Table, course: Course) -> None:
        count = item_count(course, self.size, self.rng)
        items = pick_items(course, count, self.rng)
        try:
            await casa.order(RawOrder(table.number, course, items, self.size))
        except* DishBurnedError:
            # `except*` porque a rodada é um TaskGroup: o erro vem embalado.
            # E `return`/`break`/`continue` são SyntaxError dentro de `except*`
            # (o bloco pode rodar mais de uma vez) — por isso, flag.
            self.complained = True

    def _between(self, range_: tuple[float, float]) -> float:
        return self.rng.uniform(*range_)
