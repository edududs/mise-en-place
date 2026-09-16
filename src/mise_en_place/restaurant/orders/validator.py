"""A fronteira: transforma o que a mesa falou em comanda, ou recusa na hora.

Cada regra é uma FUNÇÃO injetada, não um método de uma classe gorda: regra nova
entra na tupla `REGRAS` sem tocar no validador (OCP). E o validador não sabe o
que cada regra checa — ele só sabe *aplicar* regras. Mechanism, not policy.

Aqui se verifica a compatibilidade entre item e curso. A sequência temporal entre
cursos é conduzida pela coroutine da mesa; este validador não mantém esse histórico.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import Final

from ..core.clock import Clock
from ..core.errors import (
    EmptyRoundError,
    InvalidOrderError,
    ItemNotOnMenuError,
    WrongCourseError,
)
from ..menu import MENU, PROMISED_MINUTES, Course, Recipe
from .ticket import OrderItem, RawOrder, Ticket

# A regra devolve o ERRO pronto (ou None se passou). Devolver a exceção — e não
# um `bool` ou uma string — é o que deixa cada regra escolher a própria
# consequência, sem um `if` no validador traduzindo motivo em classe de erro.
type Rule = Callable[[RawOrder, Mapping[str, Recipe]], InvalidOrderError | None]


# `menu` não é usado aqui, e é de propósito: toda regra tem a MESMA assinatura
# (o tipo `Regra`), senão o validador precisaria saber o que cada uma consome.
# Interface uniforme > parâmetro economizado.
def _empty_round(
    raw: RawOrder,
    menu: Mapping[str, Recipe],  # noqa: ARG001
) -> InvalidOrderError | None:
    if raw.items:
        return None
    return EmptyRoundError(f"mesa {raw.table} chamou o garçom e não pediu nada")


def _not_on_menu(raw: RawOrder, menu: Mapping[str, Recipe]) -> InvalidOrderError | None:
    unknown = tuple(name for name in raw.items if name not in menu)
    if not unknown:
        return None
    return ItemNotOnMenuError(f"não servimos: {', '.join(unknown)}")


def _wrong_course(raw: RawOrder, menu: Mapping[str, Recipe]) -> InvalidOrderError | None:
    misplaced = tuple(
        f"{name} é {menu[name].course.label}"
        for name in raw.items
        if name in menu and menu[name].course is not raw.course
    )
    if not misplaced:
        return None
    return WrongCourseError(f"pedido no curso errado — {'; '.join(misplaced)}")


RULES: Final[tuple[Rule, ...]] = (_empty_round, _not_on_menu, _wrong_course)


class Validator:
    """Parse, don't validate: devolve `Comanda` ou levanta. Nunca devolve `None`."""

    def __init__(
        self,
        clock: Clock,
        *,
        menu: Mapping[str, Recipe] = MENU,
        rules: tuple[Rule, ...] = RULES,
        promises: Mapping[Course, float] = PROMISED_MINUTES,
    ) -> None:
        self._clock = clock
        self._menu = menu
        self._rules = rules
        self._promises = promises

    def validate(self, raw: RawOrder) -> Ticket:
        # `next(gerador, None)` é fail-fast E preguiçoso: se a 1ª regra barrar,
        # a 2ª nem roda. Trocar por `tuple(self._violacoes(...))` mudaria a
        # semântica pra "colete todos os motivos" — decisão consciente.
        first = next(self._violations(raw), None)
        if first is not None:  # guard clause
            raise first

        ordered_at = self._clock.minutes()
        items = tuple(
            OrderItem(table=raw.table, recipe=self._menu[name], index=index)
            for index, name in enumerate(raw.items)
        )
        return Ticket(
            table=raw.table,
            course=raw.course,
            items=items,
            ordered_at=ordered_at,
            deadline=ordered_at + self._promises[raw.course],
        )

    def _violations(self, raw: RawOrder) -> Iterator[InvalidOrderError]:
        """Gerador: produz um erro por regra violada, sob demanda."""
        for rule in self._rules:
            error = rule(raw, self._menu)
            if error is not None:
                yield error
