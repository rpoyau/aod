from __future__ import annotations

import csv
import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

MANUAL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = MANUAL_DIR / "code" / "05f_wire_current_boundary_transport.py"

spec = importlib.util.spec_from_file_location("wire_current_boundary_transport", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def setup():
    return module.load_setup()


def test_zero_transport_zero_current_flux():
    result = module.compute(setup(), transform="zero_transport")
    assert result["J"] == Fraction(0, 1)
    assert result["w_perp_plus"] == Fraction(0, 1)
    assert result["w_perp_minus"] == Fraction(0, 1)
    assert all(row.u_tr == Fraction(0, 1) for row in result["rows"])


def test_orientation_reversal_reverses_current_flux():
    base = module.compute(setup())
    reversed_result = module.compute(setup(), transform="current_reversal")
    assert reversed_result["J"] == -base["J"]
    assert reversed_result["w_perp_plus"] == -base["w_perp_plus"]
    assert reversed_result["w_perp_minus"] == -base["w_perp_minus"]


def test_chirality_reversal_reverses_witness():
    base = module.compute(setup())
    reversed_result = module.compute(setup(), transform="chirality_reversal")
    assert reversed_result["J"] == base["J"]
    assert reversed_result["w_perp_plus"] == -base["w_perp_plus"]
    assert reversed_result["w_perp_minus"] == -base["w_perp_minus"]


def test_top_bottom_exact_antisymmetry():
    result = module.compute(setup())
    assert result["w_perp_plus"] + result["w_perp_minus"] == Fraction(0, 1)


def test_duon_tetron_decomposition_adds_exactly():
    result = module.compute(setup())
    family_total = sum(result["family_J"].values(), Fraction(0, 1))
    assert family_total == result["J"]


def test_window_rate_normalization():
    result = module.compute(setup())
    assert result["J"] == result["U"] / setup()["window_bip_0"]


def test_bstar_not_transverse_witness():
    result = module.compute(setup())
    assert result["w_perp_plus"] != Fraction(0, 1)
    assert all(Fraction(row.B_star, 1) != result["w_perp_plus"] for row in result["rows"])


def test_trace_declared_as_edge_probe_contribution():
    traces = module.trace_rows(setup())
    active = next(row for row in traces if row["scenario"] == "active_probe_plus")
    assert active["identity"] == "declared"
    assert Fraction(active["w_perp_minus_num"], active["w_perp_minus_den"]) == Fraction(0, 1)


def test_exact_csv_has_num_den_columns():
    module.write_outputs()
    exact_path = MANUAL_DIR / "data" / "derived" / "05f_wire_current_exact.csv"
    with exact_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = set(reader.fieldnames or [])
    required = {
        "u_tr_num", "u_tr_den",
        "J_flux_num", "J_flux_den",
        "w_perp_plus_num", "w_perp_plus_den",
        "w_perp_minus_num", "w_perp_minus_den",
    }
    assert required.issubset(header)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("all 05f wire-current tests passed")
