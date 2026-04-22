from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MANUAL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = MANUAL_DIR / "code" / "05i_integer_collision_vertex.py"

spec = importlib.util.spec_from_file_location("integer_collision_vertex", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_balanced_ternary_closure():
    vals = {-1, 0, 1}
    for a in vals:
        for b in vals:
            assert module.balanced_ternary_add(a, b) in vals
    assert module.balanced_ternary_add(1, -1) == 0
    assert module.balanced_ternary_add(1, 1) == -1
    assert module.balanced_ternary_add(-1, -1) == 1


def test_collision_outcomes_cover_declared_classes():
    rows = module.rows()
    outcomes = {row["outcome"] for row in rows}
    assert {"balanced", "push", "pull", "reclosure", "export", "rupture/refinement"}.issubset(outcomes)


def test_rupture_requires_zero_incidence_in_examples():
    for row in module.rows():
        if row["outcome"] == "rupture/refinement":
            assert row["incidence"] == 0


def test_balanced_example_has_zero_total_charge_and_phase():
    row = next(row for row in module.rows() if row["row_id"] == "C_balanced")
    assert row["c"] == 0
    assert row["Q_sum"] == 0
    assert row["K_sum_centered"] == 0
    assert row["outcome"] == "balanced"


def test_collision_script_writes_outputs():
    module.main()
    expected = [
        MANUAL_DIR / "data" / "derived" / "05i_duon_collision_exact.csv",
        MANUAL_DIR / "data" / "derived" / "05i_duon_collision_trace.csv",
        MANUAL_DIR / "figures" / "collision" / "01_integer_collision_outcomes.png",
    ]
    assert all(path.exists() for path in expected)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("all 05i integer collision tests passed")
