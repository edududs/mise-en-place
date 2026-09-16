"""Reexportacao do vocabulario compartilhado; preserva imports anteriores."""

from mise_en_place.contracts.courses import (
    COURSE_LABELS,
    PROMISED_MINUTES,
    Course,
    Section,
    Station,
)

__all__ = ["COURSE_LABELS", "PROMISED_MINUTES", "Course", "Section", "Station"]
