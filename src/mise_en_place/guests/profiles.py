"""Os perfis de cliente — a política de comportamento das pessoas.

Sobre "zero magic numbers": os literais abaixo ficam no `dataclass` de propósito.
Num literal de estrutura congelada o **nome do campo já nomeia o número**
(`chance_de_sobremesa=0.80` se explica sozinho), e criar 36 constantes `Final`
para os campos de 4 perfis pioraria a leitura em vez de melhorar. `Final` fica
para os botões de regência do serviço (taxa de chegada, tamanho da equipe,
fator de tempo, semente).

Quatro perfis é o teto do KISS aqui: o quinto não ensinaria nada novo.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class Style(StrEnum):
    IN_A_HURRY = "com pressa"
    COUPLE = "casal"
    FAMILY = "família"
    FRIENDS = "amigos"


@dataclass(frozen=True, slots=True)
class Profile:
    """Como esse tipo de cliente se comporta. Tudo em minutos simulados."""

    style: Style
    size: tuple[int, int]
    menu_reading_minutes: tuple[float, float]
    starter_chance: float
    eat_starter_minutes: tuple[float, float]
    eat_main_minutes: tuple[float, float]
    dessert_chance: float
    drink_rounds: tuple[int, int]
    door_patience_minutes: float


PROFILES: Final[tuple[Profile, ...]] = (
    Profile(
        Style.IN_A_HURRY,
        size=(1, 2),
        menu_reading_minutes=(1.0, 3.0),
        starter_chance=0.10,
        eat_starter_minutes=(5.0, 8.0),
        eat_main_minutes=(10.0, 15.0),
        dessert_chance=0.05,
        drink_rounds=(0, 0),
        door_patience_minutes=5.0,
    ),
    Profile(
        Style.COUPLE,
        size=(2, 2),
        menu_reading_minutes=(5.0, 10.0),
        starter_chance=0.80,
        eat_starter_minutes=(12.0, 18.0),
        eat_main_minutes=(25.0, 35.0),
        dessert_chance=0.80,
        drink_rounds=(1, 2),
        door_patience_minutes=25.0,
    ),
    Profile(
        Style.FAMILY,
        size=(3, 5),
        menu_reading_minutes=(4.0, 8.0),
        starter_chance=0.60,
        eat_starter_minutes=(8.0, 12.0),
        eat_main_minutes=(20.0, 30.0),
        dessert_chance=0.70,
        drink_rounds=(0, 1),
        door_patience_minutes=15.0,
    ),
    Profile(
        Style.FRIENDS,
        size=(4, 6),
        menu_reading_minutes=(6.0, 12.0),
        starter_chance=0.70,
        eat_starter_minutes=(10.0, 15.0),
        eat_main_minutes=(25.0, 40.0),
        dessert_chance=0.40,
        drink_rounds=(2, 4),
        door_patience_minutes=30.0,
    ),
)

# Índice DERIVADO da fonte única — o estilo não é digitado duas vezes.
BY_STYLE: Final[Mapping[Style, Profile]] = {profile.style: profile for profile in PROFILES}

# Quantos casais para cada mesa de amigos, etc. Mesma ordem de `PERFIS`.
STYLE_WEIGHTS: Final[tuple[int, ...]] = (2, 3, 3, 2)


def random_profile(rng: random.Random) -> Profile:
    return rng.choices(PROFILES, weights=STYLE_WEIGHTS, k=1)[0]
