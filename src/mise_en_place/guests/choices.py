"""O que o cliente decide pedir. Política de GOSTO, isolada do resto.

Está separado do `Grupo` de propósito: mudar "como as pessoas escolhem prato"
(por exemplo, para o comportamento mais previsível que o curso quer mais
adiante — preferência por estilo, memória de visita anterior, reação a demora)
não deve tocar em uma linha da jornada da mesa.
"""

from __future__ import annotations

import random

from ..restaurant import ITEMS_BY_COURSE, Course
from .profiles import Profile


def item_count(course: Course, size: int, rng: random.Random) -> int:
    """Quantos itens desse curso o grupo pede."""
    if course is Course.MAIN:
        return size  # cada um pede o seu
    if course is Course.STARTER:
        return max(1, size // 2)  # entrada se divide
    return max(1, rng.randint(1, size))


def pick_items(course: Course, count: int, rng: random.Random) -> tuple[str, ...]:
    """Escolhe do cardápio. O cliente conhece o MENU (nomes), não a receita."""
    options = ITEMS_BY_COURSE[course]
    return tuple(rng.choice(options) for _ in range(count))


def drink_rounds(profile: Profile, rng: random.Random) -> int:
    return rng.randint(*profile.drink_rounds)
