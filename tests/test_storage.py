"""A mesma suíte de contrato em dois meios de armazenamento."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from mise_en_place.adapters.storage import JsonResultStore, MemoryResultStore
from mise_en_place.contracts.results import Measurement
from mise_en_place.contracts.storage import ResultStore


def memory_store(path: Path) -> ResultStore:  # noqa: ARG001
    return MemoryResultStore()


def file_store(path: Path) -> ResultStore:
    return JsonResultStore(path)


@pytest.mark.parametrize("factory", [memory_store, file_store])
def test_result_store_contract(factory: Callable[[Path], ResultStore], tmp_path: Path) -> None:
    store = factory(tmp_path)
    result = Measurement("teste", 1, 0, 0, 0, 0, 0, 1)
    assert store.load("missing") is None
    store.save("turno-1", result)
    assert store.load("turno-1") == result
    updated = replace(result, rounds=2)
    store.save("turno-1", updated)
    assert store.load("turno-1") == updated
    with pytest.raises(ValueError, match="identificador"):
        store.save("../escape", result)


def test_corruption_is_not_absence(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="json_invalid"):
        JsonResultStore(tmp_path).load("broken")


def test_result_survives_new_adapter(tmp_path: Path) -> None:
    result = Measurement("teste", 1, 0, 0, 0, 0, 0, 1)
    JsonResultStore(tmp_path).save("turno", result)
    assert JsonResultStore(tmp_path).load("turno") == result
