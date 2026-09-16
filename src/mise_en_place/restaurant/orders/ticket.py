"""Os três estados de um pedido: bruto → validado → item despachável.

São tipos DIFERENTES de propósito (parse, don't validate): depois da fronteira
não existe "talvez o item esteja no menu". Se você tem uma `Comanda` na mão, ela
já é válida — o type checker garante que ninguém pulou o validador.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..menu import Course, Recipe, Section


@dataclass(frozen=True, slots=True)
class RawOrder:
    """O que a mesa FALA. Não confiável: os itens são `str` que alguém digitou.

    É `str` de propósito — o salão não conhece `Receita`. A tradução
    nome → receita é do validador, e é por isso que "a mesa pediu polenta"
    tem um erro de verdade pra levantar.
    """

    table: int
    course: Course
    items: tuple[str, ...]
    size: int = 1


@dataclass(frozen=True, slots=True)
class OrderItem:
    """Item já resolvido: carrega a receita. Só existe depois da validação.

    `indice` é a posição dele na rodada — entra na chave de ordenação da fila
    pra que os itens de uma mesma mesa saiam na ordem em que foram falados.
    """

    table: int
    recipe: Recipe
    index: int

    def __str__(self) -> str:
        return f"{self.recipe.name} (mesa {self.table})"


@dataclass(frozen=True, slots=True)
class Ticket:
    """Rodada VALIDADA de uma mesa: os itens de um curso, com prazo.

    `prazo_min` é absoluto e ESTÁTICO (momento do pedido + promessa do curso).
    É o que torna o EDF starvation-free: um pedido velho só pode virar o de
    prazo mais próximo, nunca o mais distante.
    """

    table: int
    course: Course
    items: tuple[OrderItem, ...]
    ordered_at: float
    deadline: float

    def for_section(self, section: Section) -> tuple[OrderItem, ...]:
        """Os itens desta rodada que pertencem a uma praça."""
        return tuple(item for item in self.items if item.recipe.section is section)

    @property
    def sections(self) -> frozenset[Section]:
        return frozenset(item.recipe.section for item in self.items)
