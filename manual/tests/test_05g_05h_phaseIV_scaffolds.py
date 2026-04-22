from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

MANUAL_DIR = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, MANUAL_DIR / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

matter = load_module("matter_regime_scaffold", "code/05g_matter_regime_scaffold.py")
planetary = load_module("planetary_shell_scaffold", "code/05h_planetary_shell_scaffold.py")


def test_matter_rows_are_scaffold_or_existing_worked_link():
    rows = matter.rows()
    assert rows
    allowed = {"scaffold", "worked_in_05f"}
    assert all(row["status"] in allowed for row in rows)


def test_matter_rows_have_exact_fraction_columns():
    for row in matter.rows():
        assert int(row["q_eff_den"]) > 0
        assert int(row["torsion_den"]) > 0
        assert int(row["persistence_den"]) > 0
        assert int(row["transport_balance_den"]) > 0


def test_planetary_q_eff_is_boundary_polarization_pair():
    rows = planetary.shell_rows()
    assert rows
    assert all(row["q_eff_role"] == "boundary_polarization_pair" for row in rows)
    assert all(row["status"] == "scaffold" for row in rows)


def test_planetary_shell_rows_have_exact_pairs():
    for row in planetary.shell_rows():
        Fraction(int(row["Phi_num"]), int(row["Phi_den"]))
        Fraction(int(row["q_eff_num"]), int(row["q_eff_den"]))
        Fraction(int(row["loss_num"]), int(row["loss_den"]))
        Fraction(int(row["torsion_num"]), int(row["torsion_den"]))
        Fraction(int(row["P_shell_num"]), int(row["P_shell_den"]))


def test_ring_refinements_are_not_validated_benchmarks():
    rows = planetary.ring_rows()
    assert rows
    assert all(row["status"] in {"scaffold", "source_normalized_pending"} for row in rows)


def test_scripts_write_phaseiv_outputs():
    matter.main()
    planetary.main()
    expected = [
        MANUAL_DIR / "data" / "derived" / "05g_matter_regime_scaffold.csv",
        MANUAL_DIR / "figures" / "matter" / "01_matter_transport_scaffold.png",
        MANUAL_DIR / "data" / "derived" / "05h_planetary_shell_scaffold.csv",
        MANUAL_DIR / "data" / "derived" / "05h_saturn_galactic_ring_refinements.csv",
        MANUAL_DIR / "figures" / "planetary" / "01_earth_moon_shell_scaffold.png",
        MANUAL_DIR / "figures" / "planetary" / "02_saturn_galactic_ring_refinements.png",
    ]
    assert all(path.exists() for path in expected)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("all 05g/05h Phase IV scaffold tests passed")
