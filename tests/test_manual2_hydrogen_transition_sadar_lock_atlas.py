import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def current_version():
    import re
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    m = re.search(r"Canonical version:\s*(\S+)", text)
    assert m
    return m.group(1)
HYDROGEN = ROOT / "manual-2" / "data" / "hydrogen_transition"
SCRIPT = ROOT / "manual-2" / "scripts" / "build_hydrogen_transition_sadar_lock_atlas.py"
SECTION = ROOT / "manual-2" / "sections" / "01_hydrogen_transition_sadar_lock_atlas.tex"
MANIFEST = HYDROGEN / "hydrogen_transition_sadar_lock_manifest.json"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_csv_with_fieldnames(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated_paths():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [ROOT / row["path"] for row in manifest["generated_files"]]


def load_generator():
    spec = importlib.util.spec_from_file_location("hydrogen_transition_builder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_hydrogen_transition_generator_is_byte_deterministic():
    before = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in generated_paths()}
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    after = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in generated_paths()}
    assert after == before


def test_hydrogen_transition_manifest_binds_generated_files_and_source_inputs():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["manifest_id"] == "manual2_hydrogen_transition_sadar_lock_atlas_v1"
    assert manifest["version_scope"] == "v40.03r08.1"
    assert manifest["release_class"] == "target_blind_native_Hydrogen_transition_and_SADAR_lock_atlas_repair"
    assert manifest["native_packet_policy"] == {
        "SI_second_status": "downstream_optional_projection_only",
        "native_before_projection": True,
        "native_hash_isolation": "projection_and_tau_notation_excluded_from_native_packet_hash",
        "score_status": "no_score",
        "target_value_read_status": "not_read",
        "tau_cycle_notation": "Tau_index_not_native_identity",
    }
    assert manifest["counterfactual_audit"]["execution_mode"] == "executed_mutation_evaluator"
    assert manifest["current_gate_state"]["metric_projection_unit"] == "second"
    assert "Elementary Matter 118" in manifest["atlas_lanes"]
    assert "Molecular Matter" in manifest["atlas_lanes"]
    assert "Biomolecular Matter" in manifest["atlas_lanes"]
    for key in ["projection_index", "tau_notation_index"]:
        assert (ROOT / manifest["index_ledgers"][key]).exists()
    for card in manifest["generated_files"] + manifest["source_inputs"]:
        path = ROOT / card["path"]
        assert path.exists(), card["path"]
        assert card["sha256"] == sha256_file(path)
        assert card["bytes"] == str(path.stat().st_size)


def test_native_hydrogen_packets_are_hash_isolated_and_target_blind():
    fields, rows = read_csv_with_fieldnames(HYDROGEN / "hydrogen_transition_native_packets.csv")
    assert fields == [
        "packet_order", "packet_id", "packet_kind", "bound_source_path", "bound_source_sha256",
        "h1_occurrence_id", "h1_detector_id", "boundary_id", "window_id", "native_event_order",
        "native_packet_freeze_status", "target_value_read_status", "observable_join_state", "empirical_score_status",
        "packet_row_sha256",
    ]
    assert [row["packet_order"] for row in rows] == ["0", "1", "2", "3"]
    assert [row["packet_id"] for row in rows] == [
        "H1_transition_anchor_native_packet_v1",
        "H1_RD_relation_packet_v1",
        "H1_RCD_reclosure_packet_v1",
        "H1_SADAR_lock_packet_v1",
    ]
    assert {row["packet_kind"] for row in rows} == {
        "identity_bound_returned_current_anchor",
        "returned_duration_relation_declaration",
        "returned_current_duration_reclosure_declaration",
        "primitive_subject_reference_SADAR_lock_declaration",
    }
    for forbidden in ["tau_cycle_symbol", "full_cycle_notation_status", "si_second_projection_packet_id", "projection_packet_id"]:
        assert forbidden not in fields
    for row in rows:
        assert row["target_value_read_status"] == "not_read"
        assert row["observable_join_state"] == "closed"
        assert row["empirical_score_status"] == "not_computed"
        assert row["native_packet_freeze_status"].startswith("frozen")
        assert row["bound_source_sha256"] == sha256_file(ROOT / row["bound_source_path"])


def test_native_packet_hash_is_unchanged_when_projection_index_changes():
    module = load_generator()
    native_rows = read_csv(HYDROGEN / "hydrogen_transition_native_packets.csv")
    native_hashes_before = [row["packet_row_sha256"] for row in native_rows]
    index_rows = read_csv(HYDROGEN / "hydrogen_transition_projection_index.csv")
    mutated = deepcopy(index_rows[0])
    mutated["projection_packet_id"] = "H1_optional_si_second_projection_contract_v2"
    changed_index_hash = module.row_hash(mutated, [c for c in module.PROJECTION_INDEX_COLUMNS if c != "projection_index_row_sha256"])
    assert changed_index_hash != index_rows[0]["projection_index_row_sha256"]
    native_hashes_after = [row["packet_row_sha256"] for row in native_rows]
    assert native_hashes_after == native_hashes_before


def test_native_packet_hash_is_unchanged_when_tau_display_symbol_changes():
    module = load_generator()
    native_rows = read_csv(HYDROGEN / "hydrogen_transition_native_packets.csv")
    native_hashes_before = [row["packet_row_sha256"] for row in native_rows]
    index_rows = read_csv(HYDROGEN / "hydrogen_transition_tau_notation_index.csv")
    mutated = deepcopy(index_rows[0])
    mutated["tau_cycle_symbol"] = "Tau_H1_display_variant"
    changed_index_hash = module.row_hash(mutated, [c for c in module.TAU_INDEX_COLUMNS if c != "notation_index_row_sha256"])
    assert changed_index_hash != index_rows[0]["notation_index_row_sha256"]
    native_hashes_after = [row["packet_row_sha256"] for row in native_rows]
    assert native_hashes_after == native_hashes_before


def test_si_second_projection_packets_are_downstream_contracts_not_native_inputs():
    rows = read_csv(HYDROGEN / "hydrogen_transition_si_second_projection_packets.csv")
    assert rows
    assert {row["si_temporal_unit"] for row in rows} == {"second"}
    assert {row["si_unit_symbol"] for row in rows} == {"s"}
    assert {row["native_freeze_required"] for row in rows} == {"true"}
    for row in rows:
        assert row["projection_layer"] in {"downstream_metric_report_only", "domain_guard_only"}
        assert row["map_state"].endswith("declared_not_instantiated")
        assert row["map_coefficient_num"] == ""
        assert row["map_coefficient_den"] == ""
        assert row["target_value_read_status"] == "not_read"
        assert row["observable_join_state"] == "closed"
        assert row["score_status"] == "no_score"


def test_projection_index_changes_when_projection_packet_id_changes():
    module = load_generator()
    rows = read_csv(HYDROGEN / "hydrogen_transition_projection_index.csv")
    assert {row["projection_link_status"] for row in rows} == {
        "optional_downstream_guard_not_native_hash_input",
        "optional_downstream_metric_report_not_native_hash_input",
    }
    mutated = deepcopy(rows[1])
    mutated["projection_packet_id"] = "H1_optional_si_second_projection_contract_v2"
    changed_hash = module.row_hash(mutated, [c for c in module.PROJECTION_INDEX_COLUMNS if c != "projection_index_row_sha256"])
    assert changed_hash != rows[1]["projection_index_row_sha256"]


def test_tau_registry_forbids_circle_constant_as_native_cycle_primitive():
    rows = read_csv(HYDROGEN / "tau_cycle_notation_registry.csv")
    assert [row["native_symbol"] for row in rows] == ["Tau_H1", "Tau_RD", "Tau_RCD", "Tau_lock", "Tau_oct"]
    for row in rows:
        assert row["native_symbol"].startswith("Tau")
        assert row["full_turn_status"].startswith("Tau_reports")
        assert row["pi_native_status"] == "forbidden_as_native_primitive"


def test_tau_notation_index_changes_when_display_symbol_changes():
    module = load_generator()
    rows = read_csv(HYDROGEN / "hydrogen_transition_tau_notation_index.csv")
    assert [row["tau_cycle_symbol"] for row in rows] == ["Tau_H1", "Tau_RD", "Tau_RCD", "Tau_lock"]
    mutated = deepcopy(rows[0])
    mutated["tau_cycle_symbol"] = "Tau_H1_display_variant"
    changed_hash = module.row_hash(mutated, [c for c in module.TAU_INDEX_COLUMNS if c != "notation_index_row_sha256"])
    assert changed_hash != rows[0]["notation_index_row_sha256"]


def test_sadar_lock_matter_octave_atlas_covers_manual2_goal_scales():
    rows = read_csv(HYDROGEN / "sadar_lock_matter_octave_atlas.csv")
    assert [row["atlas_lane_id"] for row in rows] == [
        "elementary_matter_118",
        "molecular_matter",
        "biomolecular_matter",
    ]
    by_id = {row["atlas_lane_id"]: row for row in rows}
    assert by_id["elementary_matter_118"]["matter_scale"] == "Elementary Matter 118"
    assert by_id["elementary_matter_118"]["source_row_count"] == "118"
    assert by_id["molecular_matter"]["matter_scale"] == "Molecular Matter"
    assert by_id["biomolecular_matter"]["matter_scale"] == "Biomolecular Matter"
    for row in rows:
        assert row["tau_cycle_symbol"] == "Tau_oct"
        assert row["native_packet_status"] == "typed_atlas_row_hash_locked"
        assert "SI_second_report_optional_closed" in row["downstream_projection_lanes"]
        assert row["target_value_read_status"] == "not_read"
        assert row["score_status"] == "no_score"
        assert row["primary_source_sha256"] == sha256_file(ROOT / row["primary_source_path"])


def test_hydrogen_counterfactual_audit_is_executed_fail_closed_with_one_control():
    rows = read_csv(HYDROGEN / "hydrogen_transition_counterfactual_audit.csv")
    assert len(rows) == 5
    assert [row["counterfactual_order"] for row in rows] == ["0", "1", "2", "3", "4"]
    assert all(row["evaluation_mode"] == "executed_mutation_evaluator" for row in rows)
    assert all(row["audit_status"] == "passed" for row in rows)
    failures = [row for row in rows if row["mutation_class"] != "control"]
    controls = [row for row in rows if row["mutation_class"] == "control"]
    assert len(failures) == 4
    assert len(controls) == 1
    assert all(row["expected_result"] == row["observed_result"] == "failed" for row in failures)
    assert controls[0]["expected_result"] == controls[0]["observed_result"] == "passed"
    assert "target_value_read_status_not_not_read" in rows[0]["observed_failure_reasons"]
    assert "projection_layer_not_downstream" in rows[1]["observed_failure_reasons"]
    assert "pi_native_status_not_forbidden_as_native_primitive" in rows[2]["observed_failure_reasons"]
    assert "score_status_not_no_score" in rows[3]["observed_failure_reasons"]


def test_counterfactual_mutations_are_actually_evaluated_and_rejected():
    module = load_generator()
    native_fields, native_rows = read_csv_with_fieldnames(HYDROGEN / "hydrogen_transition_native_packets.csv")
    mutated_fields, mutated_rows = module.mutate_target_value_inserted(native_fields, deepcopy(native_rows))
    status, reasons = module.evaluate_native_packets(mutated_fields, mutated_rows)
    assert status == "failed"
    assert "target_value_read_status_not_not_read" in reasons

    projection_fields, projection_rows = read_csv_with_fieldnames(HYDROGEN / "hydrogen_transition_si_second_projection_packets.csv")
    mutated_fields, mutated_rows = module.mutate_si_promoted_to_native(projection_fields, deepcopy(projection_rows))
    status, reasons = module.evaluate_si_second_projection(mutated_fields, mutated_rows)
    assert status == "failed"
    assert "projection_layer_not_downstream" in reasons

    tau_fields, tau_rows = read_csv_with_fieldnames(HYDROGEN / "tau_cycle_notation_registry.csv")
    mutated_fields, mutated_rows = module.mutate_pi_promoted_to_native(tau_fields, deepcopy(tau_rows))
    status, reasons = module.evaluate_tau_registry(mutated_fields, mutated_rows)
    assert status == "failed"
    assert "pi_native_status_not_forbidden_as_native_primitive" in reasons

    atlas_fields, atlas_rows = read_csv_with_fieldnames(HYDROGEN / "sadar_lock_matter_octave_atlas.csv")
    mutated_fields, mutated_rows = module.mutate_target_join_before_freeze(atlas_fields, deepcopy(atlas_rows))
    status, reasons = module.evaluate_matter_atlas(mutated_fields, mutated_rows)
    assert status == "failed"
    assert "target_value_read_status_not_not_read" in reasons

    status, reasons = module.evaluate_control()
    assert status == "passed"
    assert reasons == []


def test_manual2_section_renders_hydrogen_transition_policy_without_native_pi_symbol_or_versioned_body():
    text = SECTION.read_text(encoding="utf-8")
    assert "Hydrogen transition and SADAR-lock atlas" in text
    assert "hydrogen_transition_projection_index.csv" in text
    assert "hydrogen_transition_tau_notation_index.csv" in text
    assert "executed by the generator" in text
    assert "\\Tau_{H1}" in text
    assert "second" in text
    assert "Elementary Matter 118" in text
    assert "Molecular Matter" in text
    assert "Biomolecular Matter" in text
    assert "\\pi" not in text
    assert "This r08 lane" not in text
    assert "The r08 atlas" not in text
    assert "r08 authoring claim" not in text
    assert "Balmer" in text
    assert "target-value" in text or "target value" in text


def test_manifest_exposes_baseline_and_active_authoring_overlay_without_mutating_original_manual2_lanes():
    manifest = json.loads((ROOT / "manual-2" / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["lanes"]) == {
        "elementary",
        "molecular",
        "bio_chain",
        "protein",
        "dec_pen_paper",
        "ontology_to_dec_occurrence_overlay",
        "temporal",
    }
    assert manifest["manual2_baseline_milestone"].startswith("v40.03r01")
    assert manifest["manual2_active_authoring_lane"].startswith("v40.03r11")
    assert manifest["manual2_rendered_artifact_status"] == "rebuilt_for_r10_authoring_native_packet_materialization"
    assert "current_manual_ii_milestone" not in manifest
    assert "current_package_version_scope" not in manifest
    overlay = manifest["r08_authoring_overlay"]
    assert overlay["lane_id"] == "hydrogen_transition_sadar_lock_atlas"
    assert overlay["version_scope"] == "v40.03r08.1"
    assert overlay["target_value_read_status"] == "not_read"
    assert overlay["manual2_pdf_status"] == "rebuilt_for_r08_1_authoring_repair"
    assert overlay["native_hash_isolation_status"] == "projection_and_tau_notation_excluded_from_native_packet_hash"
    assert overlay["counterfactual_audit_status"] == "executed_mutation_evaluator"
    for key in [
        "native_packets", "si_second_projection_packets", "projection_index", "tau_cycle_notation_registry",
        "tau_notation_index", "matter_octave_atlas", "counterfactual_audit", "manifest",
    ]:
        assert (ROOT / overlay[key]).exists()

    r10_overlay = manifest["r10_authoring_overlay"]
    assert r10_overlay["lane_id"] == "hydrogen_transition_native_packets"
    assert r10_overlay["version_scope"] == "v40.03r11"
    assert r10_overlay["target_value_read_status"] == "not_read"
    assert r10_overlay["manual2_pdf_status"] == "rebuilt_for_r10_authoring_native_packet_materialization"
    assert r10_overlay["native_materialization_status"] == "RD_RCD_pressure_SADAR_phase_lock_materialized"
    for key in [
        "RD_RCD_packets", "duonic_pressure_packets", "SADAR_flow_packets",
        "phase_lock_packets", "counterfactual_audit", "manifest",
    ]:
        assert (ROOT / r10_overlay[key]).exists()
