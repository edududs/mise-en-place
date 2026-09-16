"""
AULA 2 — A cozinha em POO (e onde o `yield` ganha o lugar dele)
===============================================================

Rode:  python3 ex2.py   (leia o ex1.py primeiro)

A aula 1 mostrou o MECANISMO. Aqui ele vira ORGANOGRAMA — e é onde a analogia
começa a pagar, porque cada classe é um cargo com UMA razão pra mudar:

  Prato ......... o menu ................................ POLÍTICA (o que existe)
  Passo ......... "descascar, na bancada fria, 12s" ..... POLÍTICA (etapa atômica)
  Receita ....... a sequência de passos (um gerador!) ... POLÍTICA (como se faz)
  Pedido ........ o ticket do garçom .................... DADO de fronteira
  Estacoes ...... o inventário físico e as vagas ........ RECURSO escasso
  Cozinheiro .... puxa, ocupa estação, cronometra ....... MECANISMO (como operar)
  Cozinha ....... escala a brigada, abre e fecha ........ CICLO DE VIDA
  Metricas ...... conta o serviço ....................... OBSERVABILIDADE
  event loop .... o EXPEDIDOR ........................... não é sua classe: é o asyncio

O que ensina mais é o que NÃO existe aqui:
  • Um `Cozinheiro` que soubesse a receita seria God Object — trocar o menu
    passaria a mexer em quem OPERA a cozinha.
  • Uma `Cozinha` que contasse pratos seria dois cargos na mesma pessoa; por
    isso `Metricas` é objeto próprio, entregue de fora.
  • As estações são do RESTAURANTE, não do cozinheiro: um `Semaphore` por
    cozinheiro não limitaria absolutamente nada.

E O `YIELD`, POR QUE AQUI:
  A receita é uma SEQUÊNCIA DE ETAPAS, e cada etapa ocupa uma estação
  diferente por um tempo diferente. Descrevê-la com `yield` deixa a receita ser
  política PURA — ela diz o que fazer e onde, e não sabe operar nada. Repare
  que `Receita` não tem um único `await`: é código síncrono, testável sem event
  loop. Quem ocupa fogão e cronometra é o `Cozinheiro`. Receita nova não toca o
  cozinheiro; estação nova não toca receita nenhuma.
"""

from __future__ import annotations

import asyncio
import itertools
import random
import time
from collections.abc import AsyncGenerator, Callable, Iterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from types import TracebackType
from typing import Final, Self

# ─────────────────────────────────────────────────────────────────────────────
# Parâmetros do serviço — nomeados, num lugar só
# ─────────────────────────────────────────────────────────────────────────────
RANDOM_SEED: Final = 7

COOKS_ON_SHIFT: Final = 4
PASS_SIZE: Final = 20
TABLES_IN_ROOM: Final = 5
TOTAL_ORDERS: Final = 14

DISH_TIMEOUT_S: Final = 4.0
STOVE_VARIANCE: Final[tuple[float, float]] = (0.8, 1.2)  # ±20% no tempo real
BURN_CHANCE_PER_STEP: Final = 0.04

# Tempos por ETAPA (não por prato): é essa granularidade que libera a estação
# no instante em que ela deixa de ser usada.
WASH_GREENS_S: Final = 0.25
PLATE_S: Final = 0.20
PEEL_S: Final = 0.30
FRY_S: Final = 0.45
SEAR_S: Final = 0.40
REST_MEAT_S: Final = 0.25
SAUTE_S: Final = 0.30
SIMMER_RISOTTO_S: Final = 0.70


# ─────────────────────────────────────────────────────────────────────────────
# Erros de domínio: uma família, um `except` por consequência de negócio
# ─────────────────────────────────────────────────────────────────────────────
class KitchenError(Exception):
    """Base do domínio — dá pra pegar a família inteira quando fizer sentido."""


class DishBurnedError(KitchenError):
    """Deu errado no fogo: o prato se perde, o pedido pode ser refeito."""


class DishNotOnMenuError(KitchenError):
    """Pedido inválido: recusa na hora, não tenta adivinhar."""


class UnknownStationError(KitchenError):
    """A receita pede uma estação que esta cozinha não tem: erro de montagem."""


class KitchenClosedError(KitchenError):
    """Alguém tentou mandar pedido com a cozinha fechada."""


# ─────────────────────────────────────────────────────────────────────────────
# POLÍTICA — o menu, as estações e as receitas
# ─────────────────────────────────────────────────────────────────────────────
class Dish(StrEnum):
    SALAD = "salada"
    FRIES = "batata frita"
    RISOTTO = "risoto"
    STEAK = "bife"
    STEAK_AND_FRIES = "bife com fritas"


class Station(StrEnum):
    """O lugar físico onde a etapa acontece. Cada um tem vagas limitadas."""

    COLD_LINE = "bancada fria"
    STOVE = "fogão"
    GRIDDLE = "chapa"
    FRYER = "fritadeira"


@dataclass(frozen=True, slots=True)
class Step:
    """O passo diz O QUE fazer e ONDE. Não sabe operar nada — é dado, não ação."""

    description: str
    station: Station
    seconds: float


# `Iterator[Passo]` (e não `Generator[...]`) porque é o mínimo que o chamador
# usa: ele só percorre. Pedir menos é ISP aplicado a tipos.
def _salad_steps() -> Iterator[Step]:
    yield Step("lavar as folhas", Station.COLD_LINE, WASH_GREENS_S)
    yield Step("montar", Station.COLD_LINE, PLATE_S)


def _fries_steps() -> Iterator[Step]:
    yield Step("descascar", Station.COLD_LINE, PEEL_S)
    yield Step("fritar", Station.FRYER, FRY_S)


def _risotto_steps() -> Iterator[Step]:
    yield Step("refogar", Station.STOVE, SAUTE_S)
    yield Step("cozinhar mexendo", Station.STOVE, SIMMER_RISOTTO_S)


def _steak_steps() -> Iterator[Step]:
    yield Step("selar", Station.GRIDDLE, SEAR_S)
    yield Step("descansar a carne", Station.COLD_LINE, REST_MEAT_S)


def _steak_and_fries_steps() -> Iterator[Step]:
    yield from _steak_steps()  # `yield from` = delegação: a guarnição
    yield from _fries_steps()  # tem UMA fonte de verdade, reaproveitada
    yield Step("montar", Station.COLD_LINE, PLATE_S)


# A receita guarda a FÁBRICA de passos, nunca o gerador pronto: gerador é
# consumido UMA vez só, e o segundo pedido do mesmo prato sairia vazio.
# (o `main()` no fim do arquivo demonstra essa armadilha ao vivo)
type RecipePlan = Callable[[], Iterator[Step]]


@dataclass(frozen=True, slots=True)
class Recipe:
    """Política pura: a sequência de etapas. Repare: nenhum `await` aqui dentro."""

    dish: Dish
    plan: RecipePlan

    def steps(self) -> Iterator[Step]:
        """Um plano NOVO a cada chamada — é isso que a fábrica garante."""
        return self.plan()


# Fonte única (SSoT): as receitas. O índice por prato é DERIVADO dela —
# ninguém digita o nome do prato duas vezes, então não há como divergir.
RECIPES: Final[tuple[Recipe, ...]] = (
    Recipe(Dish.SALAD, _salad_steps),
    Recipe(Dish.FRIES, _fries_steps),
    Recipe(Dish.RISOTTO, _risotto_steps),
    Recipe(Dish.STEAK, _steak_steps),
    Recipe(Dish.STEAK_AND_FRIES, _steak_and_fries_steps),
)
MENU: Final[Mapping[Dish, Recipe]] = {recipe.dish: recipe for recipe in RECIPES}


# ─────────────────────────────────────────────────────────────────────────────
# DADO de fronteira — o ticket do garçom
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class Order:
    number: int
    table: int
    dish: Dish

    def __str__(self) -> str:
        return f"#{self.number:02d} {self.dish} (mesa {self.table})"


# ─────────────────────────────────────────────────────────────────────────────
# RECURSO — as estações e suas vagas
# ─────────────────────────────────────────────────────────────────────────────
STATION_SLOTS: Final[Mapping[Station, int]] = {
    Station.COLD_LINE: 2,
    Station.STOVE: 3,
    Station.GRIDDLE: 1,  # uma chapa só: aqui a fila aparece de verdade
    Station.FRYER: 1,
}


class Stations:
    """O inventário FÍSICO da cozinha. Muda quando se compra um forno — não
    quando muda o menu, não quando muda o jeito de operar.
    """

    def __init__(self, slots: Mapping[Station, int]) -> None:
        self._slots = {station: asyncio.Semaphore(count) for station, count in slots.items()}

    @asynccontextmanager
    async def occupy(self, station: Station) -> AsyncGenerator[Station]:
        """Uma vaga da estação, devolvida SEMPRE — inclusive sob cancelamento.

        Este é o `yield` mais rentável do arquivo: o que vem ANTES dele é
        "entrar na fila da estação"; o que vem DEPOIS (aqui, o `__aexit__` do
        Semaphore) é "liberar". Sem isso, um prato cancelado no meio deixaria
        a chapa ocupada pra sempre. É a mesma forma do `lifespan` do FastAPI.
        """
        slot = self._slots.get(station)
        if slot is None:  # guard clause: cozinha mal montada falha alto e cedo
            raise UnknownStationError(f"esta cozinha não tem {station}")
        async with slot:
            yield station  # <- o corpo do `async with` de quem chamou roda aqui


# ─────────────────────────────────────────────────────────────────────────────
# OBSERVABILIDADE — o fechamento do caixa
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class Metrics:
    """Cargo separado de propósito: a Cozinha OPERA, ela não faz a contabilidade.

    Por que `self.entregues += 1` é seguro aqui sem nenhum Lock: o expedidor é
    UMA pessoa só. O event loop nunca troca de task no meio de uma linha — a
    troca só acontece num `await`. Com threads, esse mesmo `+= 1` precisaria de
    `threading.Lock`. É a grande vantagem escondida do async: concorrência sem
    corrida de dados, desde que você não bloqueie o expedidor.
    """

    delivered: int = 0
    burned: int = 0
    rejected: int = 0
    late: int = 0
    total_seconds: float = field(default=0.0, repr=False)

    def record_delivery(self, seconds: float) -> None:
        self.delivered += 1
        self.total_seconds += seconds

    @property
    def average_seconds(self) -> float:
        if not self.delivered:  # guard clause: sem prato entregue não há média
            return 0.0
        return self.total_seconds / self.delivered

    def summary(self) -> str:
        return (
            f"entregues={self.delivered} queimados={self.burned} "
            f"recusados={self.rejected} atrasados={self.late} "
            f"tempo_médio={self.average_seconds:.2f}s"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MECANISMO — o cozinheiro
# ─────────────────────────────────────────────────────────────────────────────
class Cook:
    """Sabe OPERAR a cozinha; não sabe cozinhar. A receita vem do menu.

    Um `except` por consequência de negócio: queimou (refaz), fora do menu
    (recusa), atrasou (avisa). Erro sem `except` = cozinheiro que sai calado
    do turno e uma fila que nunca mais anda.
    """

    def __init__(
        self,
        name: str,
        *,
        menu: Mapping[Dish, Recipe],
        stations: Stations,
        metrics: Metrics,
        timeout_s: float = DISH_TIMEOUT_S,
    ) -> None:
        self.name = name
        self._menu = menu
        self._stations = stations
        self._metrics = metrics
        self._timeout_s = timeout_s

    async def work(self, pass_queue: asyncio.Queue[Order]) -> None:
        """O turno inteiro: puxa do balcão até ser mandado pra casa (cancelado)."""
        while True:
            order = await pass_queue.get()  # FORA do try — lição 1 da aula 1
            try:
                await self._handle(order)
            except TimeoutError:
                self._metrics.late += 1
                print(f"  ! [{self.name}] {order} estourou {self._timeout_s}s")
            except DishBurnedError as error:
                self._metrics.burned += 1
                print(f"  ! [{self.name}] {order}: {error} — vai refazer")
            except DishNotOnMenuError as error:
                self._metrics.rejected += 1
                print(f"  ! [{self.name}] recusou: {error}")
            finally:
                pass_queue.task_done()

    async def _handle(self, order: Order) -> None:
        recipe = self._menu.get(order.dish)
        if recipe is None:  # guard clause: falha alto e cedo, não improvisa
            raise DishNotOnMenuError(f"{order.dish} não está no menu")

        async with asyncio.timeout(self._timeout_s):
            seconds = await self._run_steps(recipe.steps())

        self._metrics.record_delivery(seconds)
        print(f"  ✓ [{self.name}] entregou {order} em {seconds:.2f}s")

    async def _run_steps(self, steps: Iterator[Step]) -> float:
        """Consome o plano da receita: ocupa a estação do passo, faz, libera.

        Nenhum nome de prato aparece aqui — e é esse o ponto. A receita decide
        O QUE e ONDE; o cozinheiro decide COMO operar e QUANDO liberar.
        """
        started = time.perf_counter()
        for step in steps:
            async with self._stations.occupy(step.station):
                await asyncio.sleep(step.seconds * random.uniform(*STOVE_VARIANCE))
                if random.random() < BURN_CHANCE_PER_STEP:
                    # queimar é risco de OPERAÇÃO, não item da receita:
                    # por isso o sorteio mora aqui, e não no gerador de passos
                    raise DishBurnedError(f"deu errado ao {step.description}")
        return time.perf_counter() - started


# ─────────────────────────────────────────────────────────────────────────────
# CICLO DE VIDA — a cozinha
# ─────────────────────────────────────────────────────────────────────────────
class Kitchen:
    """Abre a cozinha, escala a brigada, recebe pedidos, fecha no fim do turno.

    É um async context manager — a mesma forma do `lifespan` do FastAPI (ver
    rodapé). O `async with` é o contrato: sair do bloco significa "balcão vazio
    e brigada liberada", nunca "deixei task solta por aí".
    """

    def __init__(
        self,
        *,
        cooks: int = COOKS_ON_SHIFT,
        pass_size: int = PASS_SIZE,
        menu: Mapping[Dish, Recipe] = MENU,
        slots: Mapping[Station, int] = STATION_SLOTS,
    ) -> None:
        self.metrics = Metrics()
        self._pass_queue: asyncio.Queue[Order] = asyncio.Queue(maxsize=pass_size)

        # UM inventário compartilhado pela brigada inteira: as estações são do
        # restaurante. Uma cópia por cozinheiro não limitaria nada.
        stations = Stations(slots)
        self._wait_staff: tuple[Cook, ...] = tuple(
            Cook(
                f"chef-{number}",
                menu=menu,
                stations=stations,
                metrics=self.metrics,
            )
            for number in range(1, cooks + 1)
        )
        self._shift: tuple[asyncio.Task[None], ...] = ()
        self._brigade: asyncio.TaskGroup | None = None

    @property
    def is_open(self) -> bool:
        return self._brigade is not None

    async def __aenter__(self) -> Self:
        # O TaskGroup fica de pé entre __aenter__ e __aexit__: é o que garante
        # que nenhum cozinheiro sobreviva à cozinha fechada.
        brigade = asyncio.TaskGroup()
        await brigade.__aenter__()
        self._brigade = brigade
        self._shift = tuple(
            brigade.create_task(chef.work(self._pass_queue), name=chef.name)
            for chef in self._wait_staff
        )
        print(f"cozinha aberta — {len(self._shift)} cozinheiros no turno")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback_: TracebackType | None,
    ) -> None:
        if self._brigade is None:  # guard clause: fechar duas vezes não explode
            return

        if exc_type is None:
            await self._pass_queue.join()  # serviço normal: espera o balcão esvaziar
        # (se veio exceção, não espera nada: apaga o fogo e vai embora)

        for task in self._shift:
            task.cancel()
        await self._brigade.__aexit__(exc_type, exc_value, traceback_)  # aguarda todos saírem

        self._brigade = None
        self._shift = ()
        print("cozinha fechada")

    async def receber(self, order: Order) -> None:
        """Aceita um pedido. Balcão cheio = o garçom espera AQUI (backpressure)."""
        if not self.is_open:  # guard clause: falha alto, não engole o pedido
            raise KitchenClosedError(f"{order} chegou com a cozinha fechada")
        await self._pass_queue.put(order)


# ─────────────────────────────────────────────────────────────────────────────
# O serviço da noite
# ─────────────────────────────────────────────────────────────────────────────
def orders_for_the_night(count: int) -> Iterator[Order]:
    """Fonte PREGUIÇOSA de pedidos: o próximo só nasce quando alguém pede.

    `count(1)` é a fonte única do número do pedido — sem contador manual pra
    esquecer de incrementar. `islice` recorta a fonte infinita: "hoje a noite
    tem N pedidos". Trocar isso por uma lista pronta funcionaria; a diferença
    aparece quando a fonte é infinita ou vem de fora (aí lista não cabe).
    """
    dishes = tuple(MENU)
    for number in itertools.islice(itertools.count(1), count):
        yield Order(
            number=number,
            table=(number % TABLES_IN_ROOM) + 1,
            dish=random.choice(dishes),
        )


def show_generator_pitfall() -> None:
    """A pegadinha nº1 de gerador, ao vivo — vale mais que qualquer parágrafo."""
    plan = _steak_and_fries_steps()
    print(f"  1ª leitura do plano: {sum(1 for _ in plan)} passos")
    print(f"  2ª leitura do plano: {sum(1 for _ in plan)} passos  ← já consumido")
    print("  por isso `Receita` guarda a FÁBRICA de passos, não o gerador pronto")


async def main() -> None:
    random.seed(RANDOM_SEED)

    print("\n=== armadilha do gerador ===")
    show_generator_pitfall()

    print("\n=== serviço da noite ===")
    async with Kitchen() as kitchen:
        for order in orders_for_the_night(TOTAL_ORDERS):
            await kitchen.receber(order)

    print(f"\nfechamento do caixa: {kitchen.metrics.summary()}")

    # E com a cozinha fechada, o pedido não desaparece em silêncio:
    try:
        await Kitchen().receber(Order(number=0, table=1, dish=Dish.SALAD))
    except KitchenClosedError as error:
        print(f"guard clause em ação: {error}")


if __name__ == "__main__":
    asyncio.run(main())


# ═════════════════════════════════════════════════════════════════════════════
# O QUE O `YIELD` COMPROU NESTE ARQUIVO
#
# 1. A receita virou POLÍTICA PURA e SÍNCRONA. `Receita` não tem `await`, não
#    conhece Semaphore, não conhece asyncio. Dá pra testar a ordem dos passos
#    sem event loop nenhum: `list(_passos_do_bife_com_fritas())`.
#
# 2. A estação virou DADO do passo. No lugar de `usa_fritadeira: bool` + um
#    ternário, cada passo diz onde acontece. Estação nova (forno, salamandra)
#    não mexe em nenhuma receita; receita nova não mexe no cozinheiro.
#
# 3. O recurso é ocupado POR ETAPA, não pelo prato inteiro. O bife solta a
#    chapa quando vai descansar — e outro prato entra na chapa nesse intervalo.
#    É aqui que "otimizar dados os recursos" acontece de verdade, e a
#    granularidade veio de graça com o gerador.
#
# 4. `yield from` deu SSoT aos passos: a batata frita do "bife com fritas" é a
#    mesma batata frita do menu. Muda o corte da batata, muda num lugar só.
#
# ARMADILHAS DE GERADOR (as três que mordem de verdade)
#   • Consumido uma vez só — guarde a fábrica, nunca o gerador (demo no main).
#   • `break` num async generator NÃO roda o `finally` na hora (só quando o GC
#     lembrar): use `contextlib.aclosing` quando o `finally` libera recurso.
#   • `yield` nunca pode ficar dentro de `asyncio.timeout`/`TaskGroup`: escopo
#     de cancelamento não atravessa `yield`, e o consumidor recebe
#     `CancelledError` pelado em vez de `TimeoutError`.
#
# ═════════════════════════════════════════════════════════════════════════════
# ONDE ISSO ENCAIXA NUM FASTAPI
#
#   @asynccontextmanager
#   async def lifespan(app: FastAPI) -> AsyncIterator[None]:
#       async with Cozinha() as cozinha:
#           app.state.cozinha = cozinha
#           yield                      # a brigada fica de pé enquanto a API vive
#
#   app = FastAPI(lifespan=lifespan)
#
#   @app.post("/pedidos", status_code=202)
#   async def criar_pedido(pedido: Pedido, request: Request) -> dict[str, str]:
#       await request.app.state.cozinha.receber(pedido)   # backpressure de graça
#       return {"status": "na fila"}
#
# O `202 Accepted` é o análogo HTTP do garçom dizendo "anotado, já sai" — e o
# `await ... receber(...)` é o que segura a resposta quando o balcão lotou, em
# vez de aceitar 10.000 pedidos que ninguém vai conseguir preparar.
# ═════════════════════════════════════════════════════════════════════════════
