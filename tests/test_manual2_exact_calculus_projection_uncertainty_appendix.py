import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_APP = ROOT / "shared" / "appendices" / "exact_native_dec_and_metric_projection_protocol.tex"
PROT = ROOT / "manual-2" / "data" / "protein"
SHARED_DATA = ROOT / "shared" / "data" / "exact_native_protocol"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def csv_rows(name: str):
    with (PROT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_exact_calculus_projection_appendix_is_shared_and_rendered_after_existing_appendices():
    manual = text(ROOT / "manual" / "main.tex")
    manual2 = text(ROOT / "manual-2" / "main.tex")
    appendix = "../shared/appendices/exact_native_dec_and_metric_projection_protocol.tex"
    assert appendix in manual and appendix in manual2
    assert manual.index("appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex") < manual.index(appendix)
    assert manual2.index("sections/C_roadmap_release_pointer.tex") < manual2.index(appendix)


def test_appendix_separates_native_exactness_projection_observation_and_agreement():
    appendix = text(SHARED_APP)
    for token in [
        "native exactness",
        "projection injectivity",
        "observation certainty",
        "empirical agreement",
        "Native causal-duration packet",
        "Exact metric-projection contract",
        "Observation packet and uncertainty",
        "Typed residual ledger",
    ]:
        assert token in appendix
    assert "Target-informed revisions begin a new frozen run" in appendix


def test_metric_projection_example_uses_integer_rational_threshold_arithmetic():
    appendix = text(SHARED_APP)
    assert "a_i,b_i,c_i,d\\in\\mathbb Z" in appendix
    assert "Both sides are integers" in appendix
    assert "without square roots or floats" in appendix
    assert "integer cross multiplication" in appendix


def test_legacy_manual2_protocol_preserves_branch_read_isolation_and_closed_gate():
    rows = csv_rows("aod_exact_calculus_projection_protocol.csv")
    assert [int(row["stage_order"]) for row in rows] == list(range(1, 10))
    pred = [row for row in rows if row["branch"] == "prediction"]
    obs = [row for row in rows if row["branch"] == "observation"]
    assert pred and obs
    assert all("agreement_scores" in row["forbidden_reads"] for row in pred)
    assert all("AOD_agreement_scores" in row["forbidden_reads"] for row in obs)
    state = csv_rows("aod_double_blind_comparison_protocol_state.csv")[0]
    assert state["candidate_universe_state"] == "not_materialized"
    assert state["selected_accession"] == "none"
    assert state["comparison_join_state"] == "closed"
    assert state["target_value_read_status"] == "not_read"
    assert state["residual_status"] == "not_computed"
    assert state["score_status"] == "no_score"


def test_uncertainty_and_residual_registries_preserve_exact_types():
    uncertainty = csv_rows("aod_observation_uncertainty_field_registry.csv")
    types = {row["exact_type"] for row in uncertainty}
    assert "integer_nonnegative" in types
    assert "integer_positive" in types
    assert "finite_symbol_set" in types
    assert "float" not in " ".join(types).lower()
    residual = {row["component_id"]: row for row in csv_rows("aod_typed_residual_component_registry.csv")}
    assert set(residual) == {"E_calc", "Delta_oct", "E_oct", "E_proj", "I_Pi", "U_obs", "E_lineage", "E_scope", "E_emp", "E_rep"}
    assert residual["U_obs"]["stage"] == "pre_join"
    assert residual["E_emp"]["stage"] == "post_join"


def test_legacy_protocol_manifest_regenerates_and_central_manifest_points_to_shared_canonical_protocol():
    path = PROT / "aod_exact_calculus_projection_protocol_manifest.json"
    before = path.read_bytes()
    script = ROOT / "manual-2" / "scripts" / "build_exact_calculus_projection_protocol_manifest.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert path.read_bytes() == before
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["appendix_role"] == "protocol_only_no_empirical_gate_activation"
    central = json.loads((ROOT / "manual-2" / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert central["exact_calculus_projection_appendix"]["canonical_appendix"].startswith("shared/appendices/")
    assert central["exact_calculus_projection_appendix"]["canonical_manifest"].startswith("shared/data/exact_native_protocol/")
    assert central["shared_exactness_protocol"]["migration_audit"].endswith("aod_existing_prediction_migration_audit.csv")


def test_temporal_order_and_refinement_contract_are_explicit_but_uninstantiated():
    appendix = text(SHARED_APP)
    assert "exact causal/event-order relation" in appendix
    assert "not identified with SI proper time" in appendix
    assert "Delta_{\\mathrm{oct}}" in appendix
    assert "E_{\\mathrm{oct}}" in appendix
    state = csv_rows("aod_double_blind_comparison_protocol_state.csv")[0]
    assert state["temporal_order_contract_state"] == "declared_ordered_DEC_trace_contract"
    assert state["octave_refinement_contract_state"] == "declared_not_instantiated"


def test_projection_noninjectivity_is_not_mislabeled_as_projection_error():
    appendix = text(SHARED_APP)
    assert "Declared non-injectivity is never entered as $E_{\\mathrm{proj}}$" in appendix
    shared = {row["component_id"]: row for row in csv.DictReader((SHARED_DATA / "aod_typed_residual_registry.csv").open(newline="", encoding="utf-8"))}
    assert shared["E_proj"]["correction_target"] == "projection_operator"
    assert shared["I_Pi"]["correction_target"] == "projection_metadata"
    state = csv_rows("aod_double_blind_comparison_protocol_state.csv")[0]
    assert state["projection_information_loss_state"] == "intentional_noninjectivity_recorded_outside_E_proj"


def test_branch_isolation_is_canonical_comparison_protocol_name():
    appendix = text(SHARED_APP)
    assert "hash-locked branch-isolated comparison" in appendix
    state = csv_rows("aod_double_blind_comparison_protocol_state.csv")[0]
    assert state["comparison_protocol_name"] == "hash_locked_branch_isolated_comparison"
