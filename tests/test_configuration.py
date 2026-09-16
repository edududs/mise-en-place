"""Entrada inválida não chega ao runtime."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mise_en_place.configuration import ExperimentInput, ScenarioInput, load_scenarios


@pytest.mark.parametrize("count", [0, -1, True, "3"])
def test_rejects_invalid_capacity(count: object) -> None:
    with pytest.raises(ValidationError):
        ScenarioInput.model_validate({"name": "teste", "cooks": count})


def test_rejects_incomplete_inventory() -> None:
    with pytest.raises(ValidationError, match="inventário"):
        ScenarioInput.model_validate({"name": "teste", "kitchen_slots": {}})


def test_rejects_empty_experiment_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ExperimentInput.model_validate({"scenarios": []})
    with pytest.raises(ValidationError):
        ScenarioInput.model_validate({"name": "teste", "cook": 3})


def test_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "scenarios.json"
    path.write_text('{"scenarios": [{"name": "teste", "cooks": 4}]}', encoding="utf-8")
    (scenario,) = load_scenarios(path)
    assert scenario.cooks == 4
