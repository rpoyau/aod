"""The current score must be calculated, distinct from carried controls."""
from pathlib import Path
import importlib.util
import math

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sparc_primary_scorer", ROOT / "manual/scripts/score_sparc_field_dynamics.py")
scorer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scorer)


def test_primary_weights_bins_instead_of_galaxy_means():
    # One zero-error bin and three unit-relative-error bins: 75%, not the
    # 50% obtained by equally weighting the two galaxy means.
    rows = pd.DataFrame({"galaxy": ["a", "b", "b", "b"],
                         "U_obs": [4, 4, 4, 4], "Delta_U": [0, 4, -4, 4]})
    score = scorer.primary_score(rows)
    assert score["MAPE_U_percent"] == 75
    assert score["N_total"] == score["N_scored"] == 4
    assert score["aggregation"] == "equal_weight_per_positive_U_obs_bin"


def test_primary_preserves_declared_denominator_domain():
    rows = pd.DataFrame({"U_obs": [0, -1, 10, 20], "Delta_U": [3, 4, 10, 10]})
    score = scorer.primary_score(rows)
    assert score["N_total"] == 4
    assert score["N_scored"] == 2
    assert score["MAPE_U_percent"] == 75
    with pytest.raises(ValueError, match="positive U_obs"):
        scorer.primary_score(rows.iloc[:2])


@pytest.mark.parametrize("column", ["U_obs", "Delta_U"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_primary_rejects_nonfinite_values(column, value):
    rows = pd.DataFrame({"U_obs": [1.0], "Delta_U": [0.0]})
    rows.loc[0, column] = value
    with pytest.raises(ValueError, match="finite"):
        scorer.primary_score(rows)


@pytest.mark.parametrize("observed,residual,message", [
    (1e-308, 1e308, "finite computed relative error"),
    (1.0, 1e308, "finite computed MAPE"),
])
def test_primary_rejects_overflow_from_finite_inputs(observed, residual, message):
    rows = pd.DataFrame({"U_obs": [observed], "Delta_U": [residual]})
    with pytest.raises(ValueError, match=message):
        scorer.primary_score(rows)


def test_generated_primary_tracks_input_while_historical_controls_stay_fixed(tmp_path, monkeypatch):
    monkeypatch.setattr(scorer, "DER", tmp_path)
    per_bin, per_gal = scorer.compute()
    scorer.write_outputs(per_bin, per_gal)
    first = pd.read_csv(tmp_path / "sparc_primary_score.csv").iloc[0]
    historical = (tmp_path / "sparc_declaration_controls.csv").read_bytes()
    assert first["record_kind"] == "computed_current_primary"
    assert first["N_total"] == first["N_scored"] == 209
    assert first["MAPE_U_percent"] == pytest.approx(26.570553423860424, rel=0, abs=1e-12)
    assert historical == (ROOT / "manual/data/derived/sparc_declaration_controls.csv").read_bytes()
    # Replace the current comparison with exact agreement; a copied historical
    # literal could not respond to this changed calculation.
    per_bin["Delta_U"] = 0
    scorer.write_outputs(per_bin, per_gal)
    second = pd.read_csv(tmp_path / "sparc_primary_score.csv").iloc[0]
    assert second["MAPE_U_percent"] == 0
    assert (tmp_path / "sparc_declaration_controls.csv").read_bytes() == historical
