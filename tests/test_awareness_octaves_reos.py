"""Tests for iterated octave carriage, exact rational field densities and REOS fixtures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "manual/scripts"))
import aod_awareness_octaves_reos as m  # noqa: E402

ROWS = [
    json.loads(line)
    for line in (ROOT / "manual/data/m2/awareness_octave_reos_cases.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]


@pytest.mark.parametrize("row", ROWS, ids=[r["fixture_id"] for r in ROWS])
def test_exact_octave_and_reos_witness(row):
    actual = m.execute_row(row)
    assert actual["expected_matched"], actual


def test_dataset_provenance_source_hash_and_positive_hostile_coverage():
    assert len(ROWS) == 7
    assert len({r["fixture_id"] for r in ROWS}) == 7
    expected_sha = hashlib.sha256((ROOT / "manual/scripts/aod_awareness_octaves_reos.py").read_bytes()).hexdigest()
    claims = {r["claim_id"] for r in ROWS}
    assert claims == {"M2_ITERATED_OCTAVES", "M2_DENSITY_REOS"}
    for claim in claims:
        assert {"positive", "hostile"} <= {r["case_kind"] for r in ROWS if r["claim_id"] == claim}
    for row in ROWS:
        assert row["source"] == "manual/scripts/aod_awareness_octaves_reos.py"
        assert row["source_sha256"] == expected_sha
        assert row["randomness"] == "none"
        assert row["record_class"] == "DECLARED_EXACT_MODEL"


def test_main_and_manual_octave_reos_anchors_are_active_and_owned():
    spec = importlib.util.spec_from_file_location(
        "audit_scientific_sources_oct", ROOT / "scripts/audit_scientific_sources.py"
    )
    audit = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(audit)
    main_eqs = audit.equations(ROOT, "main")
    manual_labels = audit.label_map(ROOT, "manual")
    for label in (
        "eq:awareness-iterated-carriage",
        "eq:awareness-cell-density",
        "eq:awareness-reos-response",
    ):
        assert label in main_eqs
        assert label not in manual_labels
    assert manual_labels["sec:m2-octaves-reos"]["path"] == "manual/sections/00_awareness_fixtures.tex"


def test_reos_and_density_results_are_exact_rationals_without_floats():
    res = m.density_reos()
    assert res["trace_equal"] is True
    for key in (
        "rho_cell_32",
        "rho_cell_64",
        "rho_q4",
        "rho_flux_20",
        "rho_trans_20",
        "rho_bip_10",
        "rho_bip_20",
        "rho_shed_10",
        "rho_shed_20",
        "lambda_cap_32_64",
        "lambda_win_bip_10_20",
        "lambda_win_shed_10_20",
    ):
        assert isinstance(res[key], Fraction), (key, type(res[key]))
    assert res["rho_flux_20"] == Fraction(0)
    assert res["rho_trans_20"] == Fraction(1)
    assert res["lambda_cap_32_64"] == Fraction(17, 2048)
    assert res["lambda_win_bip_10_20"] == Fraction(1, 100)
    assert res["lambda_win_shed_10_20"] == Fraction(1, 100)


def test_live_return_diverges_from_recorded_playback():
    res = m.live_vs_playback()
    assert res["playback_diverges"] is True
    assert res["live_edge"] == [0, 1]
    assert res["playback_edge"] == [0, 2]
    assert res["live_current"] == Fraction(2)
    assert res["playback_current"] == Fraction(0)


def test_hostile_same_scale_and_reos_controls_are_rejected():
    with pytest.raises(m.AdmissionError, match="higher scale"):
        m.octave_ladder(mutation="same_scale_b2")
    with pytest.raises(m.AdmissionError, match="distinct boundary control"):
        m.density_reos(mutation="zero_control_variation")
    with pytest.raises(m.AdmissionError, match="non-retained coordinates differ"):
        m.density_reos(mutation="unmatched_control")
