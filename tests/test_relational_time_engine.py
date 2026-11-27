"""Zero-bare-assert verification suite for RC-037 relational time, causal intervention & SI bridge.

All checks run through ``_check(...)`` so normal Python and ``python3 -B -O``
execute identical verification logic.
"""
from __future__ import annotations

import ast
import csv
import fractions
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from manual.engine.policy import loads_zero_float, require_no_floats
from manual.engine.sectors import manual_dec_examples as mde
from manual.engine.ternary import TritRatio, TritWord

CSV_PATH = ROOT / "manual" / "data" / "boundary_sadar" / "temporal_si_bridge_dec_ledger.csv"
RC_JSONL_PATH = ROOT / "manual" / "engine" / "vectors" / "rational_core.jsonl"
SD_JSONL_PATH = ROOT / "manual" / "engine" / "vectors" / "symbolic_and_display.jsonl"
CARGO_MANIFEST = ROOT / "crates" / "aod-core" / "Cargo.toml"
FORBIDDEN_EXP_TOKEN_RE = re.compile(r"aod[-_]" + r"dec", re.IGNORECASE)

CANONICAL_RC037_INPUTS: dict[str, object] = {
    "compared_cuts": [2, 10, 18, 26],
    "ref_cuts": [2, 12, 22],
    "f_cs_hz": 9192631770,
    "cal_ref": 32,
    "field_a": [58, 48],
    "field_b": [151, 102],
}


def _check(condition: bool, message: str) -> None:
    """Non-strippable check helper identical under normal and ``-O`` Python."""
    if not condition:
        raise AssertionError(message)


def _expect_raises(
    exc_types: type[BaseException] | tuple[type[BaseException], ...],
    fn: object,
    *args: object,
    **kwargs: object,
) -> BaseException:
    if not callable(fn):
        raise TypeError("fn must be callable")
    try:
        fn(*args, **kwargs)
    except exc_types as exc:
        return exc
    raise AssertionError(f"expected {exc_types!r} to be raised, but call succeeded")


def _load_rc037_record() -> dict[str, object]:
    for line in RC_JSONL_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = loads_zero_float(line)
        if isinstance(rec, dict) and rec.get("case_id") == "RC-037":
            return rec
    raise AssertionError("RC-037 missing from rational_core.jsonl")


# ---------------------------------------------------------------------------
# 1. Golden Vector, Exact Types & Source-Binding Component Preservation
# ---------------------------------------------------------------------------


def test_rc037_golden_vector_schema_and_exact_types() -> None:
    """Verify all 28 RC-037 outputs, exact int/bool types, and 100-component binding invariant."""
    rc037 = _load_rc037_record()
    inputs = rc037["inputs"]
    _check(isinstance(inputs, dict), "RC-037 inputs must be dict")
    _check(inputs == CANONICAL_RC037_INPUTS, f"RC-037 inputs drifted: {inputs!r}")

    out = mde.eval_dec_temporal_si_bridge_bounds(inputs)
    require_no_floats(out)
    _check(len(out) == 28, f"expected 28 RC-037 output keys, got {len(out)}")

    expected = rc037["expected_outcome"]["exact_value"]  # type: ignore[index]
    _check(out == expected, f"RC-037 Python S2 output mismatch:\ngot={out}\nexp={expected}")

    # Strict type separation: exact int vs bool
    for int_key in (
        "delta_bip_compared",
        "delta_bip_ref",
        "rcd_c_given_r",
        "rcd_r_given_c",
        "intervention_common_prefix_through",
        "intervention_first_divergent_cut",
    ):
        _check(type(out[int_key]) is int, f"{int_key} must be exact int, got {type(out[int_key])}")
    _check(
        type(out["intervention_disconnect_rejected"]) is bool
        and out["intervention_disconnect_rejected"] is True,
        f"intervention_disconnect_rejected must be True bool, got {out['intervention_disconnect_rejected']!r}",
    )

    # Legacy 14 keys preserved verbatim
    _check(out["delta_bip_compared"] == 3, "delta_bip_compared mismatch")
    _check(out["delta_bip_ref"] == 2, "delta_bip_ref mismatch")
    _check(out["biz_c_over_r"] == ["3", "2"], "biz_c_over_r mismatch")
    _check(out["biz_r_over_c"] == ["2", "3"], "biz_r_over_c mismatch")
    _check(out["lag_forward"] == ["3", "2"], "lag_forward mismatch")
    _check(out["lag_reverse"] == ["-3", "2"], "lag_reverse mismatch")
    _check(out["T_seconds"] == ["1", "4596315885"], "T_seconds mismatch")
    _check(out["nu_bar_hz"] == ["13788947655", "1"], "nu_bar_hz mismatch")
    _check(out["transfer_A_pred"] == ["768", "29"], "transfer_A_pred mismatch")
    _check(out["transfer_A_rel_resid"] == ["-5", "29"], "transfer_A_rel_resid mismatch")
    _check(out["transfer_B_pred"] == ["3264", "151"], "transfer_B_pred mismatch")
    _check(out["transfer_B_rel_resid"] == ["-49", "151"], "transfer_B_rel_resid mismatch")
    _check(out["intervention_ratio_before"] == ["6", "5"], "intervention_ratio_before mismatch")
    _check(out["intervention_ratio_after"] == ["2", "5"], "intervention_ratio_after mismatch")

    # New 14 keys
    _check(out["window"] == [0, 30], "window mismatch")
    _check(out["rcd_c_given_r"] == 5, "rcd_c_given_r mismatch")
    _check(out["rcd_r_given_c"] == 7, "rcd_r_given_c mismatch")
    _check(out["intervention_common_prefix_through"] == 39, "prefix mismatch")
    _check(out["intervention_first_divergent_cut"] == 41, "first_divergent_cut mismatch")
    _check(out["intervention_counts_before"] == [6, 5], "counts_before mismatch")
    _check(out["intervention_counts_after"] == [2, 5], "counts_after mismatch")
    _check(out["observed_advance_compared"] == ["7", "2"], "observed_advance_compared mismatch")
    _check(out["observed_advance_ref"] == ["17", "2"], "observed_advance_ref mismatch")
    _check(out["observed_advance_ratio"] == ["7", "17"], "observed_advance_ratio mismatch")
    _check(out["observed_advance_split_sum"] == ["7", "2"], "observed_advance_split_sum mismatch")
    _check(out["observed_advance_clipped"] == ["0", "1"], "observed_advance_clipped mismatch")
    _check(out["observed_advance_signed"] == ["-1", "2"], "observed_advance_signed mismatch")

    # Total source_binding components across all 53 vectors must remain == 100
    all_lines = [
        line
        for path in (RC_JSONL_PATH, SD_JSONL_PATH)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _check(len(all_lines) == 53, f"expected 53 total vectors, got {len(all_lines)}")
    total_components = sum(
        len(str(loads_zero_float(line)["source_binding"]).split(";"))  # type: ignore[index]
        for line in all_lines
    )
    _check(total_components == 100, f"expected 100 total source_binding components, got {total_components}")


# ---------------------------------------------------------------------------
# 2. Poisoned-Fraction Proof & Strict _parse_trit_pair Validation
# ---------------------------------------------------------------------------


def test_poisoned_fraction_proof_rc037_and_live_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove RC-037 and build_temporal_si_bridge_csv_rows never invoke Fraction."""

    def poisoned_fraction(*args: object, **kwargs: object) -> object:
        raise RuntimeError("Fraction is strictly forbidden inside RC-037 and its CSV builder!")

    monkeypatch.setattr(mde, "Fraction", poisoned_fraction)
    monkeypatch.setattr(fractions, "Fraction", poisoned_fraction)

    out_default = mde.eval_dec_temporal_si_bridge_bounds(dict(CANONICAL_RC037_INPUTS))
    _check(out_default["biz_c_over_r"] == ["3", "2"], "default TritRatio cadence mismatch")
    _check(out_default["intervention_ratio_after"] == ["2", "5"], "default causal ratio mismatch")

    out_perturbed = mde.eval_dec_temporal_si_bridge_bounds(
        {
            **CANONICAL_RC037_INPUTS,
            "window": [0, 25],
            "compared_bias": [3, 4],
            "ref_bias": [-1, 4],
            "a_c": [2, 1],
            "a_r": [3, 2],
            "intervention_cut": 60,
        }
    )
    _check(out_perturbed["delta_bip_compared"] == 2, "perturbed window count mismatch")
    _check(out_perturbed["lag_forward"] == ["1", "1"], "perturbed lag mismatch")
    _check(out_perturbed["intervention_ratio_after"] == ["3", "5"], "perturbed causal ratio mismatch")

    rows = mde.build_temporal_si_bridge_csv_rows()
    _check(len(rows) == 9, f"expected 9 live CSV rows under poisoned Fraction, got {len(rows)}")
    _check(rows[2]["exact_quantity"] == "1/4596315885", "live T3_cs133_bridge T_seconds mismatch")
    _check(rows[8]["stage_id"] == "T9_causal_disconnect_control", "live row 8 stage_id mismatch")


def test_parse_trit_pair_strict_validation() -> None:
    """Verify _parse_trit_pair accepts canonical str/int pairs and rejects invalid encodings."""
    _check(mde._parse_trit_pair(["1", "4"], name="p") == TritRatio(TritWord.ONE, TritWord.from_int(4)), "str pair")
    _check(mde._parse_trit_pair([2, 4], name="p") == TritRatio(TritWord.ONE, TritWord.from_int(2)), "int pair reduced")
    _check(mde._parse_trit_pair(["-3", "6"], name="p") == TritRatio(TritWord.NEG_ONE, TritWord.from_int(2)), "neg pair")
    _check(mde._parse_trit_pair(["0", "5"], name="p") == TritRatio.ZERO, "zero pair")

    # Reject mixed types, bools, non-canonical strings, nonpositive denominators, wrong length
    for bad_type in (["1", 4], [1, "4"], [True, 1], [1, False], ("1", "4"), "1/4", None):
        _expect_raises(TypeError, mde._parse_trit_pair, bad_type, name="p")
    for bad_val in (["01", "4"], ["+1", "4"], ["-0", "4"], ["1", "0"], ["1", "-4"], [1, 0], [1, -2], ["1"], ["1", "2", "3"]):
        _expect_raises(ValueError, mde._parse_trit_pair, bad_val, name="p")


# ---------------------------------------------------------------------------
# 3. Half-Open (u, v] Filtering, Strict Monotonicity & Anchor Exclusion
# ---------------------------------------------------------------------------


def test_half_open_window_boundary_and_anchor_exclusion() -> None:
    """Verify genuine half-open (u, v] filtering, anchor exclusion, and monotonicity checks."""
    # Right endpoint v is included: v=26 includes 26 (count=3); v=25 excludes 26 (count=2)
    out_v26 = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "window": [0, 26]})
    _check(out_v26["delta_bip_compared"] == 3 and out_v26["delta_bip_ref"] == 2, "closed right endpoint failed")

    out_v25 = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "window": [0, 25]})
    _check(out_v25["delta_bip_compared"] == 2 and out_v25["delta_bip_ref"] == 2, "excluding 26 failed")
    _check(out_v25["biz_c_over_r"] == ["1", "1"], "biz_c_over_r should become 1/1")

    # Left endpoint u is excluded: u=2 excludes anchor 2, leaving [10, 18, 26] (3) and [12, 22] (2)
    out_u2 = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "window": [2, 30]})
    _check(out_u2["delta_bip_compared"] == 3 and out_u2["delta_bip_ref"] == 2, "open left endpoint u=2 failed")

    # u=10 excludes 2 and 10, leaving [18, 26] (2) and [12, 22] (2)
    out_u10 = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "window": [10, 30]})
    _check(out_u10["delta_bip_compared"] == 2 and out_u10["delta_bip_ref"] == 2, "open left endpoint u=10 failed")

    # Anchor before window: cuts=[0, 10, 20] on (0, 30] has 2 cuts in window, both post-anchor -> 2
    out_anchor_out = mde.eval_dec_temporal_si_bridge_bounds(
        {**CANONICAL_RC037_INPUTS, "compared_cuts": [0, 10, 20], "window": [0, 30]}
    )
    _check(out_anchor_out["delta_bip_compared"] == 2, "pre-window anchor exclusion failed")

    # Rejects < 2 in-window cuts (e.g. window=[18, 30] leaves only [26], or [0, 10] leaves only [10])
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "window": [18, 30]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "compared_cuts": [0, 10], "window": [0, 30]},
    )

    # Rejects non-strictly-increasing cuts, inverted/degenerate windows, and bool cuts
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "compared_cuts": [2, 10, 10, 26]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "ref_cuts": [2, 22, 12]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "window": [30, 30]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "window": [30, 0]},
    )
    _expect_raises(
        TypeError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "compared_cuts": [True, 10, 18, 26]},
    )
    exc_mixed = _expect_raises(
        TypeError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "compared_cuts": [10, 5, "bad"]},
    )
    _check(type(exc_mixed) is TypeError, f"expected exact TypeError, got {type(exc_mixed).__name__}")


# ---------------------------------------------------------------------------
# 4. Biases, Directional RCD, Stipulated SI Gains & Cross-Field Transfer
# ---------------------------------------------------------------------------


def test_biases_directional_rcd_gains_and_transfer_controls() -> None:
    """Verify explicit biases, asymmetric directional RCD, SI gains, and transfer bounds."""
    out = mde.eval_dec_temporal_si_bridge_bounds(
        {
            **CANONICAL_RC037_INPUTS,
            "compared_bias": ["1", "3"],
            "ref_bias": ["1", "6"],
            "rcd_rd": 4,
            "rcd_c_reflections": [2, 3],
            "rcd_r_reflections": [],
            "a_c": ["2", "1"],
            "a_r": ["3", "2"],
            "field_a": [58, 0],
        }
    )
    # lag = (3 - 2) + (1/3 - 1/6) = 7/6
    _check(out["lag_forward"] == ["7", "6"], f"unexpected lag_forward: {out['lag_forward']}")
    _check(out["lag_reverse"] == ["-7", "6"], f"unexpected lag_reverse: {out['lag_reverse']}")
    _check(out["rcd_c_given_r"] == 9 and out["rcd_r_given_c"] == 4, "directional RCD mismatch")
    # T_sec = 2 * (3/2) / 9192631770 = 3 / 9192631770 = 1 / 3064210590
    _check(out["T_seconds"] == ["1", "3064210590"], f"unexpected T_seconds: {out['T_seconds']}")
    # nu_bar = (3 * 2) / (1 / 3064210590) = 18385263540
    _check(out["nu_bar_hz"] == ["18385263540", "1"], f"unexpected nu_bar_hz: {out['nu_bar_hz']}")
    _check(out["transfer_A_pred"] == ["0", "1"], "zero na_val transfer_A_pred mismatch")
    _check(out["transfer_A_rel_resid"] == ["-1", "1"], "zero na_val transfer_A_rel_resid mismatch")

    # Reject invalid RCD, nonpositive gains, and negative validation counts
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "rcd_rd": 0},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "rcd_c_reflections": [1, -1]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "a_c": ["0", "1"]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "a_r": ["-1", "1"]},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "field_a": [58, -1]},
    )


# ---------------------------------------------------------------------------
# 5. Dynamic Shifted-Cut Causal Sensitivity & Hostile Disconnect Rejection
# ---------------------------------------------------------------------------


def test_dynamic_causal_intervention_and_hostile_disconnect_rejection() -> None:
    """Verify cut-by-cut causal sensitivity across shifted cuts and hostile disconnect rejection."""
    # Direct trace inspection at default intervention_cut = 40
    outer_plus = [16, 32, 48, 64, 80, 96]
    outer_minus = [15, 30, 45, 60, 75]
    base = mde._step_cut40_causal_intervention(
        causal_window=(0, 100),
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=40,
        apply_intervention=False,
        disconnect_feedback=False,
    )
    inter = mde._step_cut40_causal_intervention(
        causal_window=(0, 100),
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=40,
        apply_intervention=True,
        disconnect_feedback=False,
    )
    disc = mde._step_cut40_causal_intervention(
        causal_window=(0, 100),
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=40,
        apply_intervention=True,
        disconnect_feedback=True,
    )

    _check(len(base.records) == 101, f"expected 101 cut records for 0..100, got {len(base.records)}")
    _check(base.counts == (6, 5) and base.ratio == TritRatio.from_ints(6, 5), "baseline mismatch")
    _check(inter.counts == (2, 5) and inter.ratio == TritRatio.from_ints(2, 5), "intervention mismatch")
    _check(disc.counts == (6, 5) and disc.ratio == TritRatio.from_ints(6, 5), "disconnected must collapse to baseline")

    # Strict causality: identical full CutRecord through cut 39, identical observables at cut 40, loss at cut 41
    _check(base.records[:40] == inter.records[:40] == disc.records[:40], "common prefix 0..39 broken")
    _check(inter.records[40].intervention_queued is True, "intervention must queue at cut 40")
    _check(inter.records[40].effective_capacity == 2 and inter.records[40].outer_plus_retained is True, "cut 40 must remain pre-drop")
    _check(inter.records[41].effective_capacity == 1 and inter.records[41].outer_plus_retained is False, "cut 41 must drop retention")
    _check(inter.records[41].retention_status == "lost_by_declared_capacity_rule", "cut 41 retention status mismatch")
    _check(disc.records[41].retention_status == "retained_feedback_disconnected_mutation", "disconnected status mismatch")

    # Replay validation accepts honest traces and rejects disconnected feedback mutation
    mde._validate_causal_capacity_trace(
        base, causal_window=(0, 100), outer_plus_cuts=outer_plus, outer_minus_cuts=outer_minus, intervention_cut=40, apply_intervention=False
    )
    mde._validate_causal_capacity_trace(
        inter, causal_window=(0, 100), outer_plus_cuts=outer_plus, outer_minus_cuts=outer_minus, intervention_cut=40, apply_intervention=True
    )
    _expect_raises(
        ValueError,
        mde._validate_causal_capacity_trace,
        disc,
        causal_window=(0, 100),
        outer_plus_cuts=outer_plus,
        outer_minus_cuts=outer_minus,
        intervention_cut=40,
        apply_intervention=True,
    )

    # Shifted intervention cuts dynamically move prefix, divergence cut, and post-intervention ratio
    out_cut60 = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "intervention_cut": 60})
    _check(out_cut60["intervention_common_prefix_through"] == 59, "cut 60 prefix mismatch")
    _check(out_cut60["intervention_first_divergent_cut"] == 61, "cut 60 first_divergent_cut mismatch")
    _check(out_cut60["intervention_counts_after"] == [3, 5], "cut 60 counts_after mismatch")
    _check(out_cut60["intervention_ratio_after"] == ["3", "5"], "cut 60 ratio_after mismatch")
    _check(out_cut60["intervention_disconnect_rejected"] is True, "cut 60 disconnect must reject")

    out_cut16 = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "intervention_cut": 16})
    _check(out_cut16["intervention_common_prefix_through"] == 15, "cut 16 prefix mismatch")
    _check(out_cut16["intervention_first_divergent_cut"] == 17, "cut 16 first_divergent_cut mismatch")
    _check(out_cut16["intervention_counts_after"] == [1, 5], "cut 16 must still retain cut 16 itself")
    _check(out_cut16["intervention_ratio_after"] == ["1", "5"], "cut 16 ratio_after mismatch")

    # Reject out-of-range intervention_cut and empty-in-window causal_outer_minus
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "intervention_cut": 0},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "intervention_cut": 100},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "causal_window": [0, 10], "intervention_cut": 5, "causal_outer_minus": [15, 30]},
    )


# ---------------------------------------------------------------------------
# 6. Observed-Advance Endpoint Law A(W) = C(W) + phi_1 - phi_0 Controls
# ---------------------------------------------------------------------------


def test_observed_advance_additivity_signed_clipped_and_rejections() -> None:
    """Verify exact observed-advance endpoint additivity, positive/negative clipping, and rejections."""
    custom_oa = {
        "compared": {"winding": 3, "phase_start": ["1", "5"], "phase_end": ["4", "5"]},
        "reference": {"winding": 5, "phase_start": ["1", "10"], "phase_end": ["3", "5"]},
        "split_left": {"winding": 1, "phase_start": ["1", "5"], "phase_end": ["2", "5"]},
        "split_right": {"winding": 2, "phase_start": ["2", "5"], "phase_end": ["4", "5"]},
        "signed_control": {"winding": 0, "phase_start": ["1", "4"], "phase_end": ["3", "4"]},
    }
    out = mde.eval_dec_temporal_si_bridge_bounds({**CANONICAL_RC037_INPUTS, "observed_advance": custom_oa})
    # A_c = 3 + 4/5 - 1/5 = 18/5; A_r = 5 + 3/5 - 1/10 = 11/2; ratio = (18/5)/(11/2) = 36/55
    _check(out["observed_advance_compared"] == ["18", "5"], "custom A_c mismatch")
    _check(out["observed_advance_ref"] == ["11", "2"], "custom A_r mismatch")
    _check(out["observed_advance_ratio"] == ["36", "55"], "custom A_c/A_r mismatch")
    _check(out["observed_advance_split_sum"] == ["18", "5"], "custom split sum mismatch")
    _check(out["observed_advance_signed"] == ["1", "2"], "positive signed advance mismatch")
    _check(out["observed_advance_clipped"] == ["1", "2"], "positive clipped advance must equal signed")

    # Reject broken split continuity (phase seam mismatch & winding mismatch)
    broken_seam = {
        **custom_oa,
        "split_right": {"winding": 2, "phase_start": ["3", "5"], "phase_end": ["4", "5"]},
    }
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": broken_seam},
    )
    broken_winding = {
        **custom_oa,
        "split_right": {"winding": 1, "phase_start": ["2", "5"], "phase_end": ["4", "5"]},
    }
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": broken_winding},
    )
    # Reject phase outside [0, 1), negative winding, A_r <= 0, unknown keys
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": {"signed_control": {"winding": 0, "phase_start": ["1", "1"], "phase_end": ["0", "1"]}}},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": {"signed_control": {"winding": -1, "phase_start": ["0", "1"], "phase_end": ["0", "1"]}}},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": {"reference": {"winding": 0, "phase_start": ["3", "4"], "phase_end": ["1", "4"]}}},
    )
    _expect_raises(
        ValueError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": {"unexpected_key": {"winding": 0, "phase_start": ["0", "1"], "phase_end": ["0", "1"]}}},
    )
    # Explicit None on observed_advance or any optional RC-037 key must raise TypeError (never fall back to defaults)
    for opt_key in (
        "window",
        "compared_bias",
        "ref_bias",
        "rcd_rd",
        "rcd_c_reflections",
        "rcd_r_reflections",
        "a_c",
        "a_r",
        "causal_window",
        "causal_outer_plus",
        "causal_outer_minus",
        "intervention_cut",
        "observed_advance",
    ):
        exc_null = _expect_raises(
            TypeError,
            mde.eval_dec_temporal_si_bridge_bounds,
            {**CANONICAL_RC037_INPUTS, opt_key: None},
        )
        _check(
            type(exc_null) is TypeError,
            f"explicit None for optional key {opt_key!r} must raise TypeError, got {type(exc_null).__name__}",
        )
    _expect_raises(
        TypeError,
        mde.eval_dec_temporal_si_bridge_bounds,
        {**CANONICAL_RC037_INPUTS, "observed_advance": {"compared": None}},
    )


# ---------------------------------------------------------------------------
# 7. Live 9-Row CSV & Static AST Hygiene (Zero Bare Assert, Zero Hardcoding)
# ---------------------------------------------------------------------------


def test_live_9_row_csv_and_static_ast_hygiene() -> None:
    """Verify regenerated 9-row CSV and static AST policy on test and RC-037 implementation."""
    actual_csv = CSV_PATH.read_text(encoding="utf-8")
    expected_csv = mde._rows_to_csv_text(mde.build_temporal_si_bridge_csv_rows())
    _check(actual_csv == expected_csv, "temporal_si_bridge_dec_ledger.csv drifted from live builder")

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        _check(
            reader.fieldnames
            == [
                "stage_id",
                "boundary_B",
                "lineage_pair",
                "delta_bip",
                "exact_quantity",
                "reverse_or_resid",
                "status_gate",
            ],
            f"CSV header mismatch: {reader.fieldnames}",
        )
        rows = list(reader)

    _check(len(rows) == 9, f"expected 9 CSV rows, got {len(rows)}")
    expected_stage_ids = [
        "T1_pair_closures",
        "T2_unwrapped_lag",
        "T3_cs133_bridge",
        "T4_transfer_field_A",
        "T5_transfer_field_B",
        "T6_cut40_intervention",
        "T7_directional_rcd",
        "T8_observed_advance_si",
        "T9_causal_disconnect_control",
    ]
    _check([r["stage_id"] for r in rows] == expected_stage_ids, "CSV stage_id sequence mismatch")
    _check(rows[2]["exact_quantity"] == "1/4596315885", "T3 exact_quantity mismatch")
    _check(rows[2]["reverse_or_resid"] == "13788947655", "T3 reverse_or_resid mismatch")
    _check(rows[5]["exact_quantity"] == "6/5" and rows[5]["reverse_or_resid"] == "2/5", "T6 causal ratios mismatch")
    _check(rows[6]["exact_quantity"] == "5" and rows[6]["reverse_or_resid"] == "7", "T7 directional RCD mismatch")
    _check(rows[7]["exact_quantity"] == "7/17" and rows[7]["reverse_or_resid"] == "-1/2", "T8 observed advance mismatch")
    _check(
        rows[8]["exact_quantity"] == "6/5"
        and rows[8]["reverse_or_resid"] == "REJECTED_REPLAY_VALIDATION"
        and rows[8]["status_gate"] == "HOSTILE_DISCONNECT_REJECTED",
        "T9 disconnect control mismatch",
    )

    # Static AST audit: zero bare assert, zero float literals, zero forbidden imports/tokens
    forbidden_mods = {
        "math",
        "cmath",
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "decimal",
        "importlib",
        "builtins",
    }
    for path in (Path(__file__).resolve(), Path(mde.__file__).resolve()):
        src = path.read_text(encoding="utf-8")
        _check(FORBIDDEN_EXP_TOKEN_RE.search(src) is None, f"forbidden experimental token in {path.name}")
        tree = ast.parse(src, filename=str(path))
        assert_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        _check(not assert_lines, f"bare assert statements in {path.name} at lines {assert_lines}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) in (float, complex):
                _check(False, f"float/complex literal in {path.name} line {node.lineno}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    _check(alias.name.split(".")[0] not in forbidden_mods, f"forbidden import {alias.name} in {path.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                _check(node.module.split(".")[0] not in forbidden_mods, f"forbidden from-import {node.module} in {path.name}")

    # Static AST check on RC-037 functions in manual_dec_examples.py: zero Fraction calls and zero hardcoded ratios/CSV strings
    mde_tree = ast.parse(Path(mde.__file__).read_text(encoding="utf-8"), filename=mde.__file__)
    rc037_fns = {
        "_parse_trit_pair",
        "_fmt_trit_pair",
        "_parse_strict_int_cuts",
        "_parse_int_window",
        "_count_post_anchor_in_half_open_window",
        "_parse_nonneg_int_list",
        "_step_cut40_causal_intervention",
        "_validate_causal_capacity_trace",
        "_observable_cut_tuple",
        "_parse_observed_advance_entry",
        "_eval_observed_advance_block",
        "eval_dec_temporal_si_bridge_bounds",
        "build_temporal_si_bridge_csv_rows",
    }
    forbidden_computed_strings = {
        "3/2",
        "2/3",
        "-3/2",
        "1/4596315885",
        "2/9192631770",
        "13788947655",
        "13788947655/1",
        "768/29",
        "-5/29",
        "3264/151",
        "-49/151",
        "6/5",
        "2/5",
        "7/2",
        "17/2",
        "7/17",
        "-1/2",
        "(6,5)->(2,5)",
        "(6,5)->(6,5)",
        "3 vs 2",
        "1+1/2",
    }
    found_fns: set[str] = set()
    for node in mde_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in rc037_fns:
            found_fns.add(node.name)
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and sub.id == "Fraction":
                    _check(False, f"Fraction reference found in {node.name} line {sub.lineno}")
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    _check(
                        sub.value not in forbidden_computed_strings,
                        f"hardcoded computed string {sub.value!r} in {node.name} line {sub.lineno}",
                    )
    _check(found_fns == rc037_fns, f"missing RC-037 functions in AST audit: {sorted(rc037_fns - found_fns)}")


# ---------------------------------------------------------------------------
# 8. Cross-Language S2 Python vs S4 Rust Exact Parity
# ---------------------------------------------------------------------------


def _eval_rust_rc037(inputs: dict[str, object]) -> subprocess.CompletedProcess[str]:
    if shutil.which("cargo") is None or shutil.which("rustc") is None:
        pytest.skip("optional Rust toolchain not installed")
    env = {**os.environ, "CARGO_TARGET_DIR": str(ROOT / "_build" / "cargo-target")}
    return subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(CARGO_MANIFEST),
            "--offline",
            "--locked",
            "--",
            "--eval-op",
            "dec_temporal_si_bridge_bounds",
            "--input-json",
            json.dumps(inputs, sort_keys=True),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_s2_python_vs_s4_rust_exact_parity_and_rejection_parity() -> None:
    """Verify byte-identical S2 Python vs S4 Rust outputs on default, perturbed, and rejected inputs."""
    cases: list[dict[str, object]] = [
        dict(CANONICAL_RC037_INPUTS),
        {
            **CANONICAL_RC037_INPUTS,
            "window": [2, 26],
            "compared_bias": [1, 3],
            "ref_bias": [-1, 6],
            "rcd_rd": 5,
            "rcd_c_reflections": [2, 1, 1],
            "rcd_r_reflections": [3],
            "a_c": ["3", "2"],
            "a_r": ["5", "4"],
            "causal_window": [0, 100],
            "intervention_cut": 60,
            "observed_advance": {
                "compared": {"winding": 3, "phase_start": ["1", "5"], "phase_end": ["4", "5"]},
                "reference": {"winding": 5, "phase_start": ["1", "10"], "phase_end": ["3", "5"]},
                "split_left": {"winding": 1, "phase_start": ["1", "5"], "phase_end": ["2", "5"]},
                "split_right": {"winding": 2, "phase_start": ["2", "5"], "phase_end": ["4", "5"]},
                "signed_control": {"winding": 0, "phase_start": ["1", "4"], "phase_end": ["3", "4"]},
            },
        },
        {
            **CANONICAL_RC037_INPUTS,
            "compared_cuts": [0, 10, 20, 30],
            "ref_cuts": [0, 15, 30],
            "window": [0, 30],
            "intervention_cut": 16,
        },
    ]

    for idx, inp in enumerate(cases):
        py_out = mde.eval_dec_temporal_si_bridge_bounds(inp)
        proc = _eval_rust_rc037(inp)
        _check(proc.returncode == 0, f"Rust S4 failed on case {idx}: {proc.stderr}")
        rs_out = loads_zero_float(proc.stdout)
        _check(rs_out == py_out, f"S2 vs S4 mismatch on case {idx}:\nPY={py_out}\nRS={rs_out}")
        # Strict JSON string parity under canonical sorting
        _check(
            json.dumps(rs_out, sort_keys=True) == json.dumps(py_out, sort_keys=True),
            f"canonical JSON string mismatch on case {idx}",
        )

    # Exact error-class rejection parity across invalid inputs (TypeError vs ValueError)
    bad_cases: list[tuple[type[BaseException], dict[str, object]]] = [
        (ValueError, {**CANONICAL_RC037_INPUTS, "compared_cuts": [2, 10, 10, 26]}),
        (TypeError, {**CANONICAL_RC037_INPUTS, "compared_cuts": [10, 5, "bad"]}),
        (ValueError, {**CANONICAL_RC037_INPUTS, "window": [18, 30]}),
        (TypeError, {**CANONICAL_RC037_INPUTS, "compared_bias": ["1", 4]}),
        (ValueError, {**CANONICAL_RC037_INPUTS, "a_c": ["0", "1"]}),
        (ValueError, {**CANONICAL_RC037_INPUTS, "intervention_cut": 100}),
        (TypeError, {**CANONICAL_RC037_INPUTS, "observed_advance": None}),
        (
            ValueError,
            {
                **CANONICAL_RC037_INPUTS,
                "observed_advance": {
                    "split_right": {"winding": 1, "phase_start": ["5", "6"], "phase_end": ["1", "6"]}
                },
            },
        ),
    ]
    for idx, (expected_exc, bad_inp) in enumerate(bad_cases):
        exc = _expect_raises(expected_exc, mde.eval_dec_temporal_si_bridge_bounds, bad_inp)
        _check(
            type(exc) is expected_exc,
            f"Python S2 case {idx} raised {type(exc).__name__}, expected {expected_exc.__name__}: {bad_inp}",
        )
        proc = _eval_rust_rc037(bad_inp)
        _check(proc.returncode != 0, f"Rust S4 unexpectedly accepted invalid case {idx}: {bad_inp}")
        expected_tag = f"error ({expected_exc.__name__}):"
        _check(
            expected_tag in proc.stderr,
            f"Rust S4 case {idx} error-class mismatch: expected {expected_tag!r} in stderr, got {proc.stderr!r}",
        )
