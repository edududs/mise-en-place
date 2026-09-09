"""Cursos, setores e estações — o vocabulário físico e temporal do serviço."""

from __future__ import annotations

from collections.abc import Mapping
from enum import IntEnum, StrEnum
from typing import Final


class Course(IntEnum):
    """A ORDEM do curso é o próprio valor do enum.

    `IntEnum` (e não `StrEnum`) porque o curso participa da chave de ordenação
    da fila: precisa ser comparável. E o valor sendo a ordem elimina a tabela
    paralela "qual curso vem antes" — que seria uma segunda fonte de verdade.

    DRINK é 0 de propósito: bebida não espera curso nenhum, e num empate de
    prazo ela ganha (cliente com sede é mais impaciente que cliente com fome).
    """

    DRINK = 0
    STARTER = 1
    MAIN = 2
    DESSERT = 3

    @property
    def label(self) -> str:
        """O nome em pt-BR, para a narrativa.

        Aqui mora uma fronteira que vale a aula: o **identificador** é código
        (inglês, `Course.STARTER`) e o **rótulo** é conteúdo (pt-BR, "entrada").
        Num `StrEnum` o próprio `value` faz esse papel — veja `Section` e
        `Station`, cujos valores são exatamente o que aparece no log. Num
        `IntEnum` não dá: o valor já está ocupado sendo a ORDEM do curso. Daí o
        mapa explícito — e é ele que impede um `.name.lower()` de vazar
        "starter" no meio de uma frase em português.
        """
        return COURSE_LABELS[self]


class Section(StrEnum):
    """Praças independentes. O bar não espera a cozinha — é isso que faz o
    "drink durante a espera" funcionar sem um único `if curso == DRINK`.
    """

    KITCHEN = "cozinha"
    BAR = "bar"


class Station(StrEnum):
    """Onde a etapa acontece. Cada estação tem um número de vagas."""

    COLD_LINE = "bancada fria"
    STOVE = "fogão"
    GRIDDLE = "chapa"
    FRYER = "fritadeira"
    OVEN = "forno"
    BAR_COUNTER = "balcão do bar"
    SHAKER = "coqueteleira"
    TAP = "chopeira"


COURSE_LABELS: Final[Mapping[Course, str]] = {
    Course.DRINK: "drink",
    Course.STARTER: "entrada",
    Course.MAIN: "principal",
    Course.DESSERT: "sobremesa",
}

# A PROMESSA feita ao cliente por curso. É daqui que sai o prazo do EDF:
# prazo_absoluto = momento_do_pedido + PROMESSA_MIN[curso].
# Mexer nesses números muda a política de atendimento do restaurante inteiro —
# e não muda uma linha de código do orquestrador. É o ponto de extensão.
PROMISED_MINUTES: Final[Mapping[Course, float]] = {
    Course.DRINK: 4.0,
    Course.STARTER: 10.0,
    Course.MAIN: 20.0,
    Course.DESSERT: 10.0,
}
