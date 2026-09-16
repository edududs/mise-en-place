"""O cardápio: 3 entradas, 5 principais, 2 sobremesas, 4 drinks.

`RECEITAS` é a fonte única. Todos os índices (`MENU`, `ITENS_POR_CURSO`) são
DERIVADOS dela por compreensão — ninguém digita o nome de um item duas vezes,
então não existe divergência possível entre menu e índice.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Final

from .courses import Course, Section, Station
from .recipe import Recipe, Step

# ─────────────────────────── entradas ───────────────────────────


def bruschetta() -> Iterator[Step]:
    yield Step("montar as fatias", Station.COLD_LINE, minutes=2.0)
    yield Step("gratinar", Station.OVEN, minutes=3.0)


def carpaccio() -> Iterator[Step]:
    yield Step("fatiar e temperar", Station.COLD_LINE, minutes=4.0)


def soup_of_the_day() -> Iterator[Step]:
    yield Step("aquecer e finalizar", Station.STOVE, minutes=3.0)


# ──────────────────────── pratos principais ────────────────────────


def _fries_side() -> Iterator[Step]:
    """Sub-plano reaproveitado — NÃO é item de menu, é componente."""
    yield Step("descascar e cortar", Station.COLD_LINE, minutes=2.0)
    yield Step("fritar", Station.FRYER, minutes=5.0)


def mushroom_risotto() -> Iterator[Step]:
    yield Step("refogar", Station.STOVE, minutes=4.0)
    yield Step("cozinhar mexendo", Station.STOVE, minutes=12.0)


def steak_and_fries() -> Iterator[Step]:
    yield Step("selar o bife", Station.GRIDDLE, minutes=6.0)
    yield from _fries_side()  # `yield from`: a guarnição tem UMA fonte
    yield Step("emplatar", Station.COLD_LINE, minutes=1.0)


def grilled_salmon() -> Iterator[Step]:
    yield Step("grelhar", Station.GRIDDLE, minutes=7.0)
    yield Step("finalizar no forno", Station.OVEN, minutes=4.0)


def pasta_carbonara() -> Iterator[Step]:
    yield Step("cozinhar a massa", Station.STOVE, minutes=8.0)
    yield Step("montar com o molho", Station.COLD_LINE, minutes=2.0)


def roast_chicken() -> Iterator[Step]:
    yield Step("selar", Station.GRIDDLE, minutes=3.0)
    yield Step("assar", Station.OVEN, minutes=18.0)  # o item mais lento


# ────────────────────────── sobremesas ──────────────────────────


def petit_gateau() -> Iterator[Step]:
    yield Step("assar", Station.OVEN, minutes=8.0)
    yield Step("montar com sorvete", Station.COLD_LINE, minutes=2.0)


def pudim() -> Iterator[Step]:
    yield Step("desenformar e servir", Station.COLD_LINE, minutes=3.0)


# ──────────────────────── drinks (no BAR) ────────────────────────


def caipirinha() -> Iterator[Step]:
    yield Step("macerar e bater", Station.SHAKER, minutes=3.0)


def draft_beer() -> Iterator[Step]:
    yield Step("tirar do barril", Station.TAP, minutes=1.0)


def orange_juice() -> Iterator[Step]:
    yield Step("espremer", Station.BAR_COUNTER, minutes=2.0)


def sparkling_water() -> Iterator[Step]:
    yield Step("abrir e servir", Station.BAR_COUNTER, minutes=1.0)


# ───────────────────── a fonte única do cardápio ─────────────────────
RECIPES: Final[tuple[Recipe, ...]] = (
    Recipe("bruschetta", Course.STARTER, Section.KITCHEN, bruschetta),
    Recipe("carpaccio", Course.STARTER, Section.KITCHEN, carpaccio),
    Recipe("sopa do dia", Course.STARTER, Section.KITCHEN, soup_of_the_day),
    Recipe("risoto de funghi", Course.MAIN, Section.KITCHEN, mushroom_risotto),
    Recipe("bife com fritas", Course.MAIN, Section.KITCHEN, steak_and_fries),
    Recipe("salmão grelhado", Course.MAIN, Section.KITCHEN, grilled_salmon),
    Recipe("massa carbonara", Course.MAIN, Section.KITCHEN, pasta_carbonara),
    Recipe("frango assado", Course.MAIN, Section.KITCHEN, roast_chicken),
    Recipe("petit gâteau", Course.DESSERT, Section.KITCHEN, petit_gateau),
    Recipe("pudim", Course.DESSERT, Section.KITCHEN, pudim),
    Recipe("caipirinha", Course.DRINK, Section.BAR, caipirinha),
    Recipe("chopp", Course.DRINK, Section.BAR, draft_beer),
    Recipe("suco de laranja", Course.DRINK, Section.BAR, orange_juice),
    Recipe("água com gás", Course.DRINK, Section.BAR, sparkling_water),
)

# Índices DERIVADOS. Se um dia divergirem da tupla acima, é porque alguém
# editou o índice em vez da fonte — e não há como, porque não existe índice
# editável: ele nasce da compreensão.
MENU: Final[Mapping[str, Recipe]] = {recipe.name: recipe for recipe in RECIPES}

ITEMS_BY_COURSE: Final[Mapping[Course, tuple[str, ...]]] = {
    course: tuple(r.name for r in RECIPES if r.course is course) for course in Course
}
