"""Smoke tests: the command-line scripts run headless and exit cleanly."""
import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"script_{name}", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_list_patterns_lists_every_category(capsys):
    assert _load("list_patterns").main([]) in (0, None)
    out = capsys.readouterr().out
    for category in ("guns", "oscillators", "spaceships", "still_lifes"):
        assert f"[{category}]" in out


def test_list_patterns_verify_reports_glider_period(capsys):
    assert _load("list_patterns").main(["--verify", "--max-steps", "40"]) in (0, None)
    assert "glider" in capsys.readouterr().out


def test_analyze_pattern_glider(capsys):
    assert _load("analyze_pattern").main(["glider", "--max-steps", "30"]) == 0
    out = capsys.readouterr().out
    assert "Loaded" in out
    assert "Population trace" in out


def test_analyze_pattern_unknown_name_fails():
    with pytest.raises(Exception):
        _load("analyze_pattern").main(["definitely_not_a_pattern"])


def test_glider_demo_headless_collision(capsys):
    assert _load("glider_demo").main(["collision", "--steps", "20"]) == 0
    assert "Generation" in capsys.readouterr().out


def test_glider_demo_headless_gun(capsys):
    assert _load("glider_demo").main(["gun", "--steps", "40"]) == 0
    assert "Gosper gun" in capsys.readouterr().out


def test_run_simulation_list_patterns(capsys):
    assert _load("run_simulation").main(["--list-patterns"]) in (0, None)
    assert "[guns]" in capsys.readouterr().out
