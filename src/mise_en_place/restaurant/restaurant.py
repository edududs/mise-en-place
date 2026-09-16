"""Opera o restaurante com colaboradores montados em bootstrap."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Iterator, Mapping
from types import TracebackType
from typing import Self

from ..contracts.events import RoundPublisher, RoundServed
from .core.clock import Clock
from .core.errors import (
    InvalidOrderError,
    LeftTheQueueError,
    RestaurantClosedError,
)
from .dining import Reason, Seating, Table, WaitStaff
from .menu import Course, Section, Station
from .observability import (
    Event,
    EventKind,
    Journal,
    Metrics,
)
from .orders import RawOrder, Validator
from .results import Measurement, utilization
from .service import Expediter, Line, Preparer


class Restaurant:
    """Abre a casa, escala o turno, atende, fecha e presta contas."""

    def __init__(
        self,
        clock: Clock,
        *,
        seating: Seating,
        wait_staff: WaitStaff,
        lines: Mapping[Section, Line],
        brigade: tuple[Preparer, ...],
        journal: Journal,
        metrics: Metrics,
        oven_slots: int,
        publisher: RoundPublisher,
    ) -> None:
        self.clock = clock
        self.seating = seating
        self.wait_staff = wait_staff
        self.lines = lines
        self.brigade = brigade
        self._journal = journal
        self.metrics = metrics
        self._oven_slots = oven_slots
        self._publisher = publisher
        self._expediter = Expediter(lines, clock)
        self._validator = Validator(clock)
        self._shift: asyncio.TaskGroup | None = None
        self._used = False

    @property
    def is_open(self) -> bool:
        return self._shift is not None

    async def __aenter__(self) -> Self:
        if self._used:
            raise RuntimeError("cada operação representa um único turno; monte outra casa")
        self._used = True
        shift = asyncio.TaskGroup()
        await shift.__aenter__()
        self._shift = shift
        for preparer in self.brigade:
            shift.create_task(preparer.work(), name=preparer.name)
        for waiter in self.wait_staff.waiters:
            shift.create_task(waiter.work(), name=waiter.name)
        try:
            self._record(
                EventKind.OPENED,
                "casa",
                f"{len(self.brigade)} na cozinha/bar, {len(self.wait_staff.waiters)} no salão",
            )
        except BaseException:
            # __aexit__ não é chamado automaticamente se __aenter__ falha.
            self._shift = None
            self._expediter.close()
            self.wait_staff.close()
            await shift.__aexit__(*sys.exc_info())
            raise
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

        try:
            if exc_type is None:
                await self._expediter.drain()
                await self.wait_staff.drain()
            self._record(EventKind.CLOSED, "casa", "")
        except BaseException:
            # Falha de observação ou cancelamento não pode abandonar workers.
            self._expediter.close()
            self.wait_staff.close()
            await shift.__aexit__(*sys.exc_info())
            raise
        self._expediter.close()
        self.wait_staff.close()
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

        self._publisher.publish(
            RoundServed(ticket.table, ticket.course, len(ticket.items), self.clock.minutes())
        )

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
    def measurement(self, scenario: str) -> Measurement:
        """A operação conhece suas peças; o relatório só conhece este resultado."""
        minutes = self.clock.minutes()
        cooks = tuple(p for p in self.brigade if p.section is Section.KITCHEN)
        oven = self.lines[Section.KITCHEN].busy_minutes().get(Station.OVEN, 0.0)
        waiters = self.wait_staff.waiters
        return Measurement(
            scenario=scenario,
            minutes=minutes,
            starter_wait=self.metrics.average_wait(Course.STARTER),
            main_wait=self.metrics.average_wait(Course.MAIN),
            oven_utilization=utilization(oven, minutes, self._oven_slots),
            cook_utilization=utilization(sum(p.busy_minutes for p in cooks), minutes, len(cooks)),
            waiter_utilization=utilization(
                sum(w.busy_minutes for w in waiters), minutes, len(waiters)
            ),
            rounds=self.metrics.served,
        )

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
