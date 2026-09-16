"""O restaurante: composition root + ciclo de vida.

Este módulo é o ÚNICO que sabe montar o sistema — quem é praça, quem é
preparador, quem é garçom, quem valida. Nenhum outro módulo compõe nada. É por
isso que não existe container de injeção de dependência aqui: o `__init__`
abaixo *é* o container, e cabe numa tela.

Detalhe que vale a aula: esta classe implementa a porta `Atendimento` que o
package `clientela` declara — **estruturalmente**. Este arquivo nunca importa
`clientela` e não sabe que a porta existe; a conformidade é conferida pelo type
checker no ponto em que os dois se encontram (`ex4.py`). Quem define o contrato
é quem CONSOME (DIP), e o `Protocol` estrutural torna isso possível sem herança
e sem import — a seta de dependência aponta de fora pra dentro.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Iterator, Mapping, Sequence
from types import TracebackType
from typing import Final, Self

from .core.clock import Clock
from .core.errors import (
    InvalidOrderError,
    LeftTheQueueError,
    RestaurantClosedError,
)
from .dining import DINING_ROOM, Reason, Seating, Table, WaitStaff
from .menu import Course, Section, Station
from .observability import (
    CompositeJournal,
    Event,
    EventKind,
    Journal,
    Metrics,
    TerminalJournal,
)
from .orders import RawOrder, Validator
from .service import Expediter, Line, Preparer

COOKS_ON_SHIFT: Final = 3
BARTENDERS_ON_SHIFT: Final = 1
WAITERS_ON_SHIFT: Final = 3
WAITER_NAMES: Final[tuple[str, ...]] = ("Ana", "Bia", "Caio", "Dora")

# O inventário físico de cada praça. Estes números são o botão de regência do
# gargalo: uma chapa e uma fritadeira criam disputa real; tirar um forno e medir
# de novo é o experimento do ex5.
KITCHEN_STATIONS: Final[Mapping[Station, int]] = {
    Station.COLD_LINE: 2,
    Station.STOVE: 3,
    Station.GRIDDLE: 1,
    Station.FRYER: 1,
    Station.OVEN: 2,
}
BAR_STATIONS: Final[Mapping[Station, int]] = {
    Station.BAR_COUNTER: 2,
    Station.SHAKER: 1,
    Station.TAP: 1,
}


class Restaurant:
    """Abre a casa, escala o turno, atende, fecha e presta contas."""

    def __init__(
        self,
        clock: Clock,
        *,
        rng: random.Random,
        journal: Journal | None = None,
        cooks: int = COOKS_ON_SHIFT,
        bartenders: int = BARTENDERS_ON_SHIFT,
        waiters: int = WAITERS_ON_SHIFT,
        seating: Sequence[Table] = DINING_ROOM,
        kitchen_slots: Mapping[Station, int] = KITCHEN_STATIONS,
        bar_slots: Mapping[Station, int] = BAR_STATIONS,
    ) -> None:
        self.clock = clock
        self.metrics = Metrics()
        # o terminal e as métricas consomem os MESMOS eventos: uma fonte, dois
        # destinos. Nada é contado duas vezes, e trocar o destino não toca em
        # quem emite.
        self._journal: Journal = CompositeJournal(
            journal if journal is not None else TerminalJournal(clock),
            self.metrics,
        )

        self.seating = Seating(seating)
        self.wait_staff = WaitStaff(clock, count=waiters, names=WAITER_NAMES)
        self.lines: Mapping[Section, Line] = {
            Section.KITCHEN: Line(Section.KITCHEN, clock, slots=kitchen_slots),
            Section.BAR: Line(Section.BAR, clock, slots=bar_slots),
        }
        self._expediter = Expediter(self.lines, clock)
        self._validator = Validator(clock)
        self.brigade = (
            *(
                Preparer(
                    f"chef-{number}",
                    line=self.lines[Section.KITCHEN],
                    clock=clock,
                    journal=self._journal,
                    rng=rng,
                )
                for number in range(1, cooks + 1)
            ),
            *(
                Preparer(
                    f"barman-{number}",
                    line=self.lines[Section.BAR],
                    clock=clock,
                    journal=self._journal,
                    rng=rng,
                )
                for number in range(1, bartenders + 1)
            ),
        )
        self._shift: asyncio.TaskGroup | None = None

    # ─────────────────────────── ciclo de vida ───────────────────────────
    @property
    def is_open(self) -> bool:
        return self._shift is not None

    async def __aenter__(self) -> Self:
        shift = asyncio.TaskGroup()
        await shift.__aenter__()
        self._shift = shift
        for preparer in self.brigade:
            shift.create_task(preparer.work(), name=preparer.name)
        for waiter in self.wait_staff.waiters:
            shift.create_task(waiter.work(), name=waiter.name)
        self._record(
            EventKind.OPENED,
            "casa",
            f"{len(self.brigade)} na cozinha/bar, {len(self.wait_staff.waiters)} no salão",
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback_: TracebackType | None,
    ) -> None:
        shift = self._shift
        if shift is None:  # guard clause: fechar duas vezes não explode
            return
        self._shift = None

        if exc_type is None:
            # serviço normal: espera tudo que já entrou sair de verdade
            await self._expediter.drain()
            await self.wait_staff.drain()

        # `shutdown()` no lugar de `cancel()`: os workers saem pela porta da
        # frente (`except asyncio.QueueShutDown`) em vez de serem interrompidos
        # no meio de um prato. É a evolução direta do padrão do ex1/ex2.
        self._expediter.close()
        self.wait_staff.close()
        self._record(EventKind.CLOSED, "casa", "")
        await shift.__aexit__(exc_type, exc_value, traceback_)

    # ─────────────── a porta do salão (o que a clientela usa) ───────────────
    async def seat(self, size: int, patience_minutes: float | None = None) -> Table:
        """Espera por mesa que caiba o grupo, até a paciência do grupo acabar.

        A paciência é POLÍTICA do cliente (vem de fora, por parâmetro); aplicar
        o prazo e registrar a desistência é MECANISMO da casa — e mora aqui
        porque é aqui que existe diário. `Mesas.sentar` segue sem saber o que é
        paciência: ele só aloca mesa.
        """
        try:
            async with asyncio.timeout(self.clock.deadline_s(patience_minutes)):
                table = await self.seating.seat(size)
        except TimeoutError:
            self._record(EventKind.LEFT_QUEUE, f"grupo de {size}", "esperou demais na porta")
            raise LeftTheQueueError(f"grupo de {size} desistiu na porta") from None
        self._record(EventKind.SEATED, str(table), f"{size} pessoas")
        return table

    async def release(self, table: Table) -> None:
        await self.seating.release(table)
        self._record(EventKind.LEFT, str(table), "")

    async def order(self, raw: RawOrder) -> None:
        """Chama garçom → valida → cozinha/bar → garçom serve. Só volta servido.

        Os dois `chamar()` são de propósito: o garçom é gargalo DUAS vezes por
        rodada (anotar e servir). É isso que faz o relatório final às vezes
        acusar o salão, e não a cozinha, como o problema.
        """
        if not self.is_open:  # guard clause
            raise RestaurantClosedError(f"mesa {raw.table} pediu com a casa fechada")

        await self.wait_staff.call(raw.table, Reason.TAKE_ORDER)
        try:
            ticket = self._validator.validate(raw)
        except InvalidOrderError as error:
            self._record(EventKind.REJECTED, f"mesa {raw.table}", str(error), raw.course)
            raise

        items = ", ".join(item.recipe.name for item in ticket.items)
        self._record(EventKind.ORDERED, f"mesa {raw.table}", items, raw.course)

        await self._expediter.serve_round(ticket)
        await self.wait_staff.call(raw.table, Reason.DELIVER)

        self._journal.record(
            Event(
                kind=EventKind.SERVED,
                at_minute=self.clock.minutes(),
                who=f"mesa {raw.table}",
                detail=items,
                course=ticket.course,
                waited=self.clock.minutes() - ticket.ordered_at,
            )
        )

    async def ask_for_bill(self, table: int) -> None:
        await self.wait_staff.call(table, Reason.BILL)

    # ─────────────────────────── prestação de contas ───────────────────────────
    def report(self) -> Iterator[str]:
        """Gerador de linhas: quem imprime decide o que fazer com elas.

        A composição mora aqui, no root, porque é o único lugar que conhece
        métricas E praças E equipe ao mesmo tempo. Nenhum dos três importa os
        outros — se `observabilidade` conhecesse `Praca`, haveria ciclo.
        """
        yield from self.metrics.lines()
        for section, line in self.lines.items():
            utilization = line.busy_minutes()
            detail = " · ".join(
                f"{station} {minutes:.0f}min" for station, minutes in sorted(utilization.items())
            )
            yield f"ocupação      {section:<10} {detail}"
        kitchen = " · ".join(
            f"{p.name} {p.busy_minutes:.0f}min ({p.items} itens)" for p in self.brigade
        )
        yield f"brigada       {kitchen}"
        dining = " · ".join(
            f"{waiter.name} {waiter.busy_minutes:.0f}min ({waiter.calls_handled} chamados)"
            for waiter in self.wait_staff.waiters
        )
        yield f"garçons       {dining}"

    def _record(self, kind: EventKind, who: str, detail: str, course: Course | None = None) -> None:
        self._journal.record(
            Event(
                kind=kind,
                at_minute=self.clock.minutes(),
                who=who,
                detail=detail,
                course=course,
            )
        )
