"""A entrada real funciona em subprocesso, inclusive com saída Windows cp1252."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from mise_en_place.adapters.storage import JsonResultStore
from mise_en_place.contracts.results import Measurement


def run_cli(module: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", module, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
        env=environment,
    )


def test_demo_is_executable() -> None:
    result = run_cli("mise_en_place.demo")
    assert result.returncode == 0, result.stderr
    assert "meta atingida: True" in result.stdout
    assert "água com gás" in result.stdout


def test_cli_loads_persisted_result(tmp_path: Path) -> None:
    JsonResultStore(tmp_path).save("teste", Measurement("cenário", 1, 0, 0, 0, 0, 0, 1))
    result = run_cli("mise_en_place", "--results-dir", str(tmp_path), "--show", "teste")
    assert result.returncode == 0, result.stderr
    assert "cenário" in result.stdout


def test_invalid_config_fails_before_execution(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"scenarios":[{"name":"teste","cooks":0}]}', encoding="utf-8")
    result = run_cli("mise_en_place", "--config", str(path))
    assert result.returncode == 2
    assert not result.stdout
    assert "Traceback" not in result.stderr
