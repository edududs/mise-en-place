"""Vocabulário comum: erros e tempo. Não importa nada do resto do package."""

from __future__ import annotations

from .clock import SIMULATED_MINUTE_S, Clock
from .errors import RestaurantError

__all__ = ["SIMULATED_MINUTE_S", "Clock", "RestaurantError"]
