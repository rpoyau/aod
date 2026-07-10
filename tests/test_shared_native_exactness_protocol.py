import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "shared" / "data" / "exact_native_protocol"
APP = ROOT / "shared" / "appendices" / "exact_native_dec_and_metric_projection_protocol.tex"


def rows(name: str):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_both_manuals_render_the_same_shared_appendix_source():
    manual = text(ROOT / "manual" / "main.tex")
    manual2 = text(ROOT / "manual-2" / "main.tex")
    include = "../shared/appendices/exact_native_dec_and_metric_projection_protocol.tex"
    assert include in manual
    assert include in manual2
    assert "sections/D_exact_multioctave_calculus_projection_uncertainty.tex" not in manual2
    assert "sections/E_exact_native_causal_duration_si_projection.tex" not in manual2


def test_shared_appendix_declares_one_exact_kernel_family_and_terminal_rule():
    s = text(APP)
    assert "One exact D.E.C. kernel family" in s
    assert "P_t(e\\mid c,B)" in s
    assert "\\operatorname{adm}_t(e;c,B)" in s
    assert "w_t(e;c,B)" in s
    assert "Z_t(c;B)=0" in s
    assert "no division is performed" in s
    kernel = rows("aod_dec_kernel_family_registry.csv")[0]
    assert kernel["kernel_family_id"] == "aod_dec_exact_kernel_v1"
    assert kernel["terminal_rule"] == "if_Z_t_eq_0_no_division_record_terminal_blocked_or_pending"


def test_isotropic_and_anisotropic_are_specializations_of_same_kernel():
    kernel = rows("aod_dec_kernel_family_registry.csv")[0]
    assert kernel["isotropic_specialization"] == "all_admissible_weights_equal_1"
    assert kernel["anisotropic_specialization"] == "declared_positive_rational_weights"
    s = text(APP)
    assert "P^{\\mathrm{iso}}=(1/4,1/4,1/4,1/4)" in s
    assert "P^{\\mathrm{ani}}=(1/8,1/8,1/2,1/4)" in s
    assert "Equal anisotropic weights reduce exactly to the isotropic specialization" in s


def test_execution_modes_are_declared_and_trace_is_distinct_from_kernel():
    modes = rows("aod_dec_execution_mode_registry.csv")
    assert [r["execution_mode"] for r in modes] == [
        "enumerate_all", "deterministic_selector", "sample_one"
    ]
    s = text(APP)
    for token in ["kernel\\_id", "kernel\\_sha256", "execution\\_mode", "selected\\_edge", "incoming\\_mass\\_num/den", "outgoing\\_mass\\_num/den"]:
        assert token in s
    assert "A probability table is therefore never confused with the realized or propagated trace" in s


def test_detection_order_is_trace_first_and_sadar_is_post_detection():
    s = text(APP)
    assert s.index("D.E.C. execution") < s.index("read-only trace")
    assert s.index("read-only trace") < s.index("A$\\Omega$D motif / curling-curls detection")
    assert s.index("A$\\Omega$D motif / curling-curls detection") < s.index("ADAR/SADAR")
    assert "The pre-run motif-family card and the post-trace detected motif are distinct" in s


def test_native_duration_is_separate_from_si_time_and_observation_time():
    s = text(APP)
    assert "\\tau_{\\mathrm{caus}}" in s
    assert "t_{\\mathrm{SI}}" in s
    assert "t_{\\mathrm{obs}}" in s
    assert "not identified with SI proper time" in s
    schema = {r["field_name"] for r in rows("aod_native_causal_duration_packet_schema.csv")}
    assert {"event_order_relation", "event_order_sha256", "bip_duration_num", "bip_duration_den", "native_packet_sha256"} <= schema


def test_cesium_and_si_constant_cards_are_exact_but_bridge_is_empirical_contract():
    reg = {r["registry_row_id"]: r for r in rows("aod_si_defining_constant_projection_registry.csv")}
    assert reg["si_const_delta_nu_Cs"]["exact_numerator"] == "9192631770"
    assert reg["si_const_c"]["exact_numerator"] == "299792458"
    assert reg["si_const_h"]["exact_numerator"] == "662607015"
    assert reg["si_const_N_A"]["exact_numerator"] == "602214076000000000000000"
    assert reg["si_const_delta_nu_Cs"]["map_state"] == "reference_active_bridge_uninstantiated"
    assert "The SI anchor is exact; the A$\\Omega$D-to-SI correspondence is the empirical projection contract being tested" in text(APP)


def test_projection_information_loss_is_not_projection_error():
    info = {r["projection_information_loss_id"]: r for r in rows("aod_projection_information_loss_registry.csv")}
    assert info["native_packet_to_scalar_tau_caus"]["injectivity_status"] == "noninjective"
    assert info["native_packet_to_scalar_tau_caus"]["E_proj_status"] == "not_a_projection_defect"
    residual = {r["component_id"]: r for r in rows("aod_typed_residual_registry.csv")}
    assert residual["E_proj"]["correction_target"] == "projection_operator"
    assert residual["I_Pi"]["correction_target"] == "projection_metadata"


def test_branch_isolated_protocol_freezes_native_projection_observation_and_join_in_order():
    stage = rows("aod_branch_isolated_join_protocol.csv")
    assert [int(r["stage_order"]) for r in stage] == list(range(1, 9))
    assert stage[0]["stage_id"] == "native_scope_freeze"
    assert stage[-1]["stage_id"] == "typed_residual_and_score"
    assert all(r["current_state"] != "active_score" for r in stage)
    assert "hash-locked branch-isolated comparison" in text(APP)


def test_migration_audit_has_typed_layer_dispositions_and_unchanged_native_hashes():
    migration = rows("aod_existing_prediction_migration_audit.csv")
    assert len(migration) >= 8
    ids = {r["lane_id"] for r in migration}
    assert {"elementary_336", "molecular_formula", "field_tunnelling", "tau_boundary_ring", "higgs_support", "sparc_field", "protein_manual_fixture", "protein_external_1CRN"} <= ids
    for row in migration:
        if row["native_change_status"] == "unchanged":
            assert row["old_native_packet_sha256"] == row["new_native_packet_sha256"]
        assert row["typed_change_reason"]
        assert row["audit_disposition"]
    ext = next(r for r in migration if r["lane_id"] == "protein_external_1CRN")
    assert ext["audit_disposition"] == "native_unchanged_target_support_changed"
    assert ext["new_report_value"] == "effective_target_abstain_946"


def test_shared_manifest_regenerates_byte_identically():
    path = DATA / "aod_shared_exactness_protocol_manifest.json"
    before = path.read_bytes()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_shared_exact_native_protocol_manifest.py")],
        cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert path.read_bytes() == before
    m = json.loads(path.read_text(encoding="utf-8"))
    assert m["shared_appendix_sha256"] == hashlib.sha256(APP.read_bytes()).hexdigest()
    assert m["current_empirical_state"]["comparison_join_state"] == "closed"


def test_historical_manual_baseline_is_recorded():
    rows_ = rows("manual_release_baseline_registry.csv")
    by_id = {r["artifact_id"]: r for r in rows_}
    assert by_id["main_pdf"]["sha256"] == "ae8d89e90ece0dcefab83ba44b2fd1e9de73ba7d04abe7501192b085ab652ca0"
    assert by_id["manual_pdf"]["sha256"] == "75bdaf7537abedb98ce27938afc25f37c2cc693be1ab43c23f7f4e1e7af482d9"
    assert by_id["manual_pdf"]["status"] == "historical_baseline_manual_intentionally_unfrozen"
