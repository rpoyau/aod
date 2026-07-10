#!/usr/bin/env python3
"""Build the Manual-II Hydrogen Transition and SADAR-Lock Atlas repair lane.

The generator is target-blind. It binds the prior H-1 native occurrence gate,
materializes native transition/lock declaration packets, and writes optional
projection and notation links to separate downstream/index ledgers. Native packet
row hashes are computed only from native packet columns. The counterfactual audit
is executed by local mutation evaluators before the audit rows are written.
"""
from __future__ import annotations

import csv
import copy
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manual-2" / "data" / "hydrogen_transition"
VERSION = "v40.03r08.1"
MANIFEST = OUT / "hydrogen_transition_sadar_lock_manifest.json"

H1_DETECTOR = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_returned_current_detection.csv"
H1_TRACE = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_read_only_trace.csv"
H1_OCCURRENCE = ROOT / "manual" / "data" / "hydrogen" / "hydrogen1_occurrence_card.csv"
ELEMENTS = ROOT / "manual-2" / "data" / "elementary" / "element_registry_118.csv"
LADDER_336 = ROOT / "manual-2" / "data" / "elementary" / "fusion_ladder_336.csv"
LADDER_346 = ROOT / "manual-2" / "data" / "elementary" / "fusion_ladder_346.csv"
FORMULA_RESIDUALS = ROOT / "manual-2" / "data" / "molecular" / "formula_residuals.csv"
CHAIN_PREDICTIONS = ROOT / "manual-2" / "data" / "molecular" / "chain_formula_predictions.csv"
NUCLEOTIDES = ROOT / "manual-2" / "data" / "bio_chain" / "nucleotide_candidates.csv"
PEPTIDES = ROOT / "manual-2" / "data" / "bio_chain" / "peptide_candidates.csv"
PROTEIN_CHAINS = ROOT / "manual-2" / "data" / "bio_chain" / "protein_chain_candidates.csv"

FILES = {
    "native": OUT / "hydrogen_transition_native_packets.csv",
    "si_second": OUT / "hydrogen_transition_si_second_projection_packets.csv",
    "projection_index": OUT / "hydrogen_transition_projection_index.csv",
    "tau": OUT / "tau_cycle_notation_registry.csv",
    "tau_index": OUT / "hydrogen_transition_tau_notation_index.csv",
    "atlas": OUT / "sadar_lock_matter_octave_atlas.csv",
    "audit": OUT / "hydrogen_transition_counterfactual_audit.csv",
}

NATIVE_COLUMNS = [
    "packet_order", "packet_id", "packet_kind", "bound_source_path", "bound_source_sha256",
    "h1_occurrence_id", "h1_detector_id", "boundary_id", "window_id", "native_event_order",
    "native_packet_freeze_status", "target_value_read_status", "observable_join_state", "empirical_score_status",
    "packet_row_sha256",
]

PROJECTION_COLUMNS = [
    "projection_order", "projection_packet_id", "native_packet_id", "projection_layer", "si_temporal_unit",
    "si_unit_symbol", "defining_constant_card", "map_state", "map_coefficient_num", "map_coefficient_den",
    "native_freeze_required", "target_value_read_status", "observable_join_state", "score_status", "projection_row_sha256",
]

PROJECTION_INDEX_COLUMNS = [
    "projection_index_order", "native_packet_id", "projection_packet_id", "projection_link_status",
    "projection_index_row_sha256",
]

TAU_COLUMNS = [
    "notation_order", "notation_id", "native_symbol", "meaning", "cycle_scope", "full_turn_status",
    "pi_native_status", "allowed_rendering_context", "notation_row_sha256",
]

TAU_INDEX_COLUMNS = [
    "notation_index_order", "native_packet_id", "notation_id", "tau_cycle_symbol", "notation_status",
    "notation_index_row_sha256",
]

ATLAS_COLUMNS = [
    "atlas_order", "atlas_lane_id", "matter_scale", "primary_source_path", "primary_source_sha256",
    "source_row_count", "supporting_source_paths", "sadar_lock_packet_id", "tau_cycle_symbol",
    "native_packet_status", "downstream_projection_lanes", "target_value_read_status", "score_status", "atlas_row_sha256",
]

AUDIT_COLUMNS = [
    "counterfactual_order", "counterfactual_id", "mutation_class", "mutated_lane", "evaluation_mode",
    "expected_result", "observed_result", "observed_failure_reasons", "audit_status", "counterfactual_row_sha256",
]

NATIVE_FORBIDDEN_COLUMNS = {
    "tau_cycle_symbol",
    "full_cycle_notation_status",
    "si_second_projection_packet_id",
    "projection_packet_id",
    "si_temporal_unit",
    "si_unit_symbol",
    "map_state",
    "target_value",
    "target_scalar",
    "observed_value",
    "score_status",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def row_hash(row: Mapping[str, str], columns: Sequence[str]) -> str:
    return sha256_text("\x1f".join(row[column] for column in columns) + "\n")


def hash_column_name(columns: Sequence[str]) -> str:
    names = [column for column in columns if column.endswith("_sha256")]
    if not names:
        raise ValueError("no row hash column")
    return names[-1]


def materialize_rows(columns: Sequence[str], rows: Iterable[dict[str, str]], hash_column: str) -> list[dict[str, str]]:
    hash_inputs = [column for column in columns if column != hash_column]
    out_rows: list[dict[str, str]] = []
    for row in rows:
        concrete = {column: str(row.get(column, "")) for column in columns}
        concrete[hash_column] = row_hash(concrete, hash_inputs)
        out_rows.append(concrete)
    return out_rows


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, str]], hash_column: str) -> None:
    out_rows = materialize_rows(columns, rows, hash_column)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out_rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_csv_with_fieldnames(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def source_card(path: Path) -> dict[str, str]:
    rel = path.relative_to(ROOT).as_posix()
    return {"path": rel, "sha256": sha256_file(path), "bytes": str(path.stat().st_size)}


def source_count(path: Path) -> int:
    return len(read_csv(path))


def native_packet_rows() -> list[dict[str, str]]:
    detector_rows = read_csv(H1_DETECTOR)
    trace_rows = read_csv(H1_TRACE)
    occurrence_rows = read_csv(H1_OCCURRENCE)
    if len(detector_rows) != 1 or len(trace_rows) != 1 or len(occurrence_rows) != 1:
        raise ValueError("H-1 native gate must expose exactly one detector, trace, and occurrence row")
    detector = detector_rows[0]
    trace = trace_rows[0]
    occurrence = occurrence_rows[0]
    if detector["target_value_read_status"] != "not_read" or detector["empirical_score_status"] != "not_computed":
        raise ValueError("H-1 detector is not target-blind")
    if trace["trace_freeze_status"] != "frozen_before_detection":
        raise ValueError("H-1 trace is not frozen before detection")
    return [
        {
            "packet_order": "0",
            "packet_id": "H1_transition_anchor_native_packet_v1",
            "packet_kind": "identity_bound_returned_current_anchor",
            "bound_source_path": H1_DETECTOR.relative_to(ROOT).as_posix(),
            "bound_source_sha256": sha256_file(H1_DETECTOR),
            "h1_occurrence_id": detector["occurrence_id"],
            "h1_detector_id": detector["detector_id"],
            "boundary_id": trace["boundary_id"],
            "window_id": trace["window_id"],
            "native_event_order": trace["state_sequence"],
            "native_packet_freeze_status": "frozen_before_optional_projection",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        },
        {
            "packet_order": "1",
            "packet_id": "H1_RD_relation_packet_v1",
            "packet_kind": "returned_duration_relation_declaration",
            "bound_source_path": H1_TRACE.relative_to(ROOT).as_posix(),
            "bound_source_sha256": sha256_file(H1_TRACE),
            "h1_occurrence_id": trace["occurrence_id"],
            "h1_detector_id": detector["detector_id"],
            "boundary_id": trace["boundary_id"],
            "window_id": trace["window_id"],
            "native_event_order": trace["state_sequence"],
            "native_packet_freeze_status": "frozen_native_relation_packet",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        },
        {
            "packet_order": "2",
            "packet_id": "H1_RCD_reclosure_packet_v1",
            "packet_kind": "returned_current_duration_reclosure_declaration",
            "bound_source_path": H1_DETECTOR.relative_to(ROOT).as_posix(),
            "bound_source_sha256": sha256_file(H1_DETECTOR),
            "h1_occurrence_id": detector["occurrence_id"],
            "h1_detector_id": detector["detector_id"],
            "boundary_id": trace["boundary_id"],
            "window_id": trace["window_id"],
            "native_event_order": trace["state_sequence"],
            "native_packet_freeze_status": "frozen_native_reclosure_packet",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        },
        {
            "packet_order": "3",
            "packet_id": "H1_SADAR_lock_packet_v1",
            "packet_kind": "primitive_subject_reference_SADAR_lock_declaration",
            "bound_source_path": H1_OCCURRENCE.relative_to(ROOT).as_posix(),
            "bound_source_sha256": sha256_file(H1_OCCURRENCE),
            "h1_occurrence_id": occurrence["occurrence_id"],
            "h1_detector_id": detector["detector_id"],
            "boundary_id": occurrence["boundary_id"],
            "window_id": occurrence["window_id"],
            "native_event_order": trace["state_sequence"],
            "native_packet_freeze_status": "frozen_SADAR_lock_declaration_before_SI_second_report",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "empirical_score_status": "not_computed",
        },
    ]


def build_native_packets() -> None:
    write_csv(FILES["native"], NATIVE_COLUMNS, native_packet_rows(), "packet_row_sha256")


def si_second_projection_rows() -> list[dict[str, str]]:
    return [
        {
            "projection_order": "0",
            "projection_packet_id": "H1_optional_si_second_projection_contract_v1",
            "native_packet_id": "H1_SADAR_lock_packet_v1",
            "projection_layer": "downstream_metric_report_only",
            "si_temporal_unit": "second",
            "si_unit_symbol": "s",
            "defining_constant_card": "Delta_nu_Cs_exact_9192631770_Hz_reference_card",
            "map_state": "contract_declared_not_instantiated",
            "map_coefficient_num": "",
            "map_coefficient_den": "",
            "native_freeze_required": "true",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "score_status": "no_score",
        },
        {
            "projection_order": "1",
            "projection_packet_id": "H1_optional_light_path_metric_projection_guard_v1",
            "native_packet_id": "H1_transition_anchor_native_packet_v1",
            "projection_layer": "domain_guard_only",
            "si_temporal_unit": "second",
            "si_unit_symbol": "s",
            "defining_constant_card": "c_exact_299792458_m_per_s_domain_guard",
            "map_state": "guard_declared_not_instantiated",
            "map_coefficient_num": "",
            "map_coefficient_den": "",
            "native_freeze_required": "true",
            "target_value_read_status": "not_read",
            "observable_join_state": "closed",
            "score_status": "no_score",
        },
    ]


def build_si_second_projection() -> None:
    write_csv(FILES["si_second"], PROJECTION_COLUMNS, si_second_projection_rows(), "projection_row_sha256")


def projection_index_rows() -> list[dict[str, str]]:
    return [
        {
            "projection_index_order": "0",
            "native_packet_id": "H1_transition_anchor_native_packet_v1",
            "projection_packet_id": "H1_optional_light_path_metric_projection_guard_v1",
            "projection_link_status": "optional_downstream_guard_not_native_hash_input",
        },
        {
            "projection_index_order": "1",
            "native_packet_id": "H1_SADAR_lock_packet_v1",
            "projection_packet_id": "H1_optional_si_second_projection_contract_v1",
            "projection_link_status": "optional_downstream_metric_report_not_native_hash_input",
        },
    ]


def build_projection_index() -> None:
    write_csv(FILES["projection_index"], PROJECTION_INDEX_COLUMNS, projection_index_rows(), "projection_index_row_sha256")


def tau_registry_rows() -> list[dict[str, str]]:
    return [
        {
            "notation_order": "0",
            "notation_id": "Tau_H1",
            "native_symbol": "Tau_H1",
            "meaning": "one scoped H-1 direct-return cycle packet",
            "cycle_scope": "H1_q4_state_origin>H1_q4_state_hinge>H1_q4_state_origin",
            "full_turn_status": "Tau_reports_full_cycle_without_circle_constant",
            "pi_native_status": "forbidden_as_native_primitive",
            "allowed_rendering_context": "manual_exposition_and_tau_notation_index",
        },
        {
            "notation_order": "1",
            "notation_id": "Tau_RD",
            "native_symbol": "Tau_RD",
            "meaning": "returned-duration relation display marker",
            "cycle_scope": "returned_duration_relation_declaration",
            "full_turn_status": "Tau_reports_relation_cycle_without_circle_constant",
            "pi_native_status": "forbidden_as_native_primitive",
            "allowed_rendering_context": "tau_notation_index_only",
        },
        {
            "notation_order": "2",
            "notation_id": "Tau_RCD",
            "native_symbol": "Tau_RCD",
            "meaning": "returned-current-duration reclosure display marker",
            "cycle_scope": "returned_current_duration_reclosure_declaration",
            "full_turn_status": "Tau_reports_reclosure_cycle_without_circle_constant",
            "pi_native_status": "forbidden_as_native_primitive",
            "allowed_rendering_context": "tau_notation_index_only",
        },
        {
            "notation_order": "3",
            "notation_id": "Tau_lock",
            "native_symbol": "Tau_lock",
            "meaning": "SADAR-lock freeze order marker before optional projection",
            "cycle_scope": "native_packet_freeze_before_projection",
            "full_turn_status": "Tau_reports_lock_cycle_without_circle_constant",
            "pi_native_status": "forbidden_as_native_primitive",
            "allowed_rendering_context": "lock_packet_receipt",
        },
        {
            "notation_order": "4",
            "notation_id": "Tau_octave",
            "native_symbol": "Tau_oct",
            "meaning": "octave-lane cycle ledger marker for elementary molecular and biomolecular rows",
            "cycle_scope": "matter_octave_atlas",
            "full_turn_status": "Tau_reports_octave_cycle_without_circle_constant",
            "pi_native_status": "forbidden_as_native_primitive",
            "allowed_rendering_context": "sadar_lock_atlas_registry",
        },
    ]


def build_tau_registry() -> None:
    write_csv(FILES["tau"], TAU_COLUMNS, tau_registry_rows(), "notation_row_sha256")


def tau_notation_index_rows() -> list[dict[str, str]]:
    return [
        {
            "notation_index_order": "0",
            "native_packet_id": "H1_transition_anchor_native_packet_v1",
            "notation_id": "Tau_H1",
            "tau_cycle_symbol": "Tau_H1",
            "notation_status": "display_link_not_native_hash_input",
        },
        {
            "notation_index_order": "1",
            "native_packet_id": "H1_RD_relation_packet_v1",
            "notation_id": "Tau_RD",
            "tau_cycle_symbol": "Tau_RD",
            "notation_status": "display_link_not_native_hash_input",
        },
        {
            "notation_index_order": "2",
            "native_packet_id": "H1_RCD_reclosure_packet_v1",
            "notation_id": "Tau_RCD",
            "tau_cycle_symbol": "Tau_RCD",
            "notation_status": "display_link_not_native_hash_input",
        },
        {
            "notation_index_order": "3",
            "native_packet_id": "H1_SADAR_lock_packet_v1",
            "notation_id": "Tau_lock",
            "tau_cycle_symbol": "Tau_lock",
            "notation_status": "display_link_not_native_hash_input",
        },
    ]


def build_tau_notation_index() -> None:
    write_csv(FILES["tau_index"], TAU_INDEX_COLUMNS, tau_notation_index_rows(), "notation_index_row_sha256")


def matter_atlas_rows() -> list[dict[str, str]]:
    return [
        {
            "atlas_order": "0",
            "atlas_lane_id": "elementary_matter_118",
            "matter_scale": "Elementary Matter 118",
            "primary_source_path": ELEMENTS.relative_to(ROOT).as_posix(),
            "primary_source_sha256": sha256_file(ELEMENTS),
            "source_row_count": str(source_count(ELEMENTS)),
            "supporting_source_paths": ";".join([LADDER_336.relative_to(ROOT).as_posix(), LADDER_346.relative_to(ROOT).as_posix()]),
            "sadar_lock_packet_id": "atlas_lock_elementary_118_v1",
            "tau_cycle_symbol": "Tau_oct",
            "native_packet_status": "typed_atlas_row_hash_locked",
            "downstream_projection_lanes": "pubchem_element_map;stellar_scaled_comparison;SI_second_report_optional_closed",
            "target_value_read_status": "not_read",
            "score_status": "no_score",
        },
        {
            "atlas_order": "1",
            "atlas_lane_id": "molecular_matter",
            "matter_scale": "Molecular Matter",
            "primary_source_path": FORMULA_RESIDUALS.relative_to(ROOT).as_posix(),
            "primary_source_sha256": sha256_file(FORMULA_RESIDUALS),
            "source_row_count": str(source_count(FORMULA_RESIDUALS)),
            "supporting_source_paths": CHAIN_PREDICTIONS.relative_to(ROOT).as_posix(),
            "sadar_lock_packet_id": "atlas_lock_molecular_matter_v1",
            "tau_cycle_symbol": "Tau_oct",
            "native_packet_status": "typed_atlas_row_hash_locked",
            "downstream_projection_lanes": "pubchem_molecule_map;rdkit_graph_descriptors;SI_second_report_optional_closed",
            "target_value_read_status": "not_read",
            "score_status": "no_score",
        },
        {
            "atlas_order": "2",
            "atlas_lane_id": "biomolecular_matter",
            "matter_scale": "Biomolecular Matter",
            "primary_source_path": NUCLEOTIDES.relative_to(ROOT).as_posix(),
            "primary_source_sha256": sha256_file(NUCLEOTIDES),
            "source_row_count": str(source_count(NUCLEOTIDES)),
            "supporting_source_paths": ";".join([PEPTIDES.relative_to(ROOT).as_posix(), PROTEIN_CHAINS.relative_to(ROOT).as_posix()]),
            "sadar_lock_packet_id": "atlas_lock_biomolecular_matter_v1",
            "tau_cycle_symbol": "Tau_oct",
            "native_packet_status": "typed_atlas_row_hash_locked",
            "downstream_projection_lanes": "rdkit_graph_descriptors;uniprot_pdb_alphafold_targets_closed;SI_second_report_optional_closed",
            "target_value_read_status": "not_read",
            "score_status": "no_score",
        },
    ]


def build_matter_atlas() -> None:
    write_csv(FILES["atlas"], ATLAS_COLUMNS, matter_atlas_rows(), "atlas_row_sha256")


def verify_hashes(rows: list[dict[str, str]], columns: Sequence[str], hash_column: str) -> list[str]:
    reasons: list[str] = []
    inputs = [column for column in columns if column != hash_column]
    for row in rows:
        if any(column not in row for column in columns):
            reasons.append(f"{hash_column}_missing_input")
            break
        if row.get(hash_column, "") != row_hash({column: str(row.get(column, "")) for column in columns}, inputs):
            reasons.append(f"{hash_column}_mismatch")
            break
    return reasons


def evaluate_native_packets(fieldnames: Sequence[str], rows: list[dict[str, str]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if list(fieldnames) != NATIVE_COLUMNS:
        if NATIVE_FORBIDDEN_COLUMNS & set(fieldnames):
            reasons.append("native_schema_projection_or_notation_field_present")
        reasons.append("native_schema_extension_forbidden")
    if [row.get("packet_order", "") for row in rows] != ["0", "1", "2", "3"]:
        reasons.append("native_packet_order_not_canonical")
    for row in rows:
        if row.get("target_value_read_status") != "not_read":
            reasons.append("target_value_read_status_not_not_read")
            break
    for row in rows:
        if row.get("observable_join_state") != "closed":
            reasons.append("observable_join_state_not_closed")
            break
    for row in rows:
        if row.get("empirical_score_status") != "not_computed":
            reasons.append("empirical_score_status_not_not_computed")
            break
    if list(fieldnames) == NATIVE_COLUMNS:
        reasons.extend(verify_hashes(rows, NATIVE_COLUMNS, "packet_row_sha256"))
    return ("failed", sorted(set(reasons))) if reasons else ("passed", [])


def evaluate_si_second_projection(fieldnames: Sequence[str], rows: list[dict[str, str]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if list(fieldnames) != PROJECTION_COLUMNS:
        reasons.append("projection_schema_not_exact")
    for row in rows:
        if row.get("projection_layer") not in {"downstream_metric_report_only", "domain_guard_only"}:
            reasons.append("projection_layer_not_downstream")
            break
    for row in rows:
        if row.get("native_freeze_required") != "true":
            reasons.append("native_freeze_required_false")
            break
    for row in rows:
        if not row.get("map_state", "").endswith("declared_not_instantiated"):
            reasons.append("map_state_instantiated")
            break
    for row in rows:
        if row.get("target_value_read_status") != "not_read":
            reasons.append("target_value_read_status_not_not_read")
            break
    for row in rows:
        if row.get("score_status") != "no_score":
            reasons.append("score_status_not_no_score")
            break
    if list(fieldnames) == PROJECTION_COLUMNS:
        reasons.extend(verify_hashes(rows, PROJECTION_COLUMNS, "projection_row_sha256"))
    return ("failed", sorted(set(reasons))) if reasons else ("passed", [])


def evaluate_tau_registry(fieldnames: Sequence[str], rows: list[dict[str, str]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if list(fieldnames) != TAU_COLUMNS:
        reasons.append("tau_schema_not_exact")
    for row in rows:
        if not row.get("native_symbol", "").startswith("Tau"):
            reasons.append("Tau_cycle_status_missing")
            break
    for row in rows:
        if not row.get("full_turn_status", "").startswith("Tau_reports"):
            reasons.append("Tau_cycle_status_missing")
            break
    for row in rows:
        if row.get("pi_native_status") != "forbidden_as_native_primitive":
            reasons.append("pi_native_status_not_forbidden_as_native_primitive")
            break
    if list(fieldnames) == TAU_COLUMNS:
        reasons.extend(verify_hashes(rows, TAU_COLUMNS, "notation_row_sha256"))
    return ("failed", sorted(set(reasons))) if reasons else ("passed", [])


def evaluate_matter_atlas(fieldnames: Sequence[str], rows: list[dict[str, str]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if list(fieldnames) != ATLAS_COLUMNS:
        reasons.append("atlas_schema_not_exact")
    for row in rows:
        if row.get("target_value_read_status") != "not_read":
            reasons.append("target_value_read_status_not_not_read")
            break
    for row in rows:
        if row.get("score_status") != "no_score":
            reasons.append("score_status_not_no_score")
            break
    if list(fieldnames) == ATLAS_COLUMNS:
        reasons.extend(verify_hashes(rows, ATLAS_COLUMNS, "atlas_row_sha256"))
    return ("failed", sorted(set(reasons))) if reasons else ("passed", [])


def mutate_target_value_inserted(fieldnames: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    mutated_fields = list(fieldnames) + ["target_value"]
    mutated = copy.deepcopy(rows)
    mutated[0]["target_value_read_status"] = "read"
    mutated[0]["target_value"] = "external_line_value_forbidden"
    return mutated_fields, mutated


def mutate_si_promoted_to_native(fieldnames: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    mutated = copy.deepcopy(rows)
    mutated[0]["projection_layer"] = "native_premise"
    mutated[0]["native_freeze_required"] = "false"
    return list(fieldnames), mutated


def mutate_pi_promoted_to_native(fieldnames: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    mutated = copy.deepcopy(rows)
    mutated[0]["native_symbol"] = "pi_H1"
    mutated[0]["full_turn_status"] = "circle_constant_reports_native_cycle"
    mutated[0]["pi_native_status"] = "promoted_as_native_primitive"
    return list(fieldnames), mutated


def mutate_target_join_before_freeze(fieldnames: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    mutated = copy.deepcopy(rows)
    mutated[0]["target_value_read_status"] = "read"
    mutated[0]["score_status"] = "computed"
    return list(fieldnames), mutated


def evaluate_control() -> tuple[str, list[str]]:
    native_fields, native_rows = read_csv_with_fieldnames(FILES["native"])
    projection_fields, projection_rows = read_csv_with_fieldnames(FILES["si_second"])
    tau_fields, tau_rows = read_csv_with_fieldnames(FILES["tau"])
    atlas_fields, atlas_rows = read_csv_with_fieldnames(FILES["atlas"])
    results = [
        evaluate_native_packets(native_fields, native_rows),
        evaluate_si_second_projection(projection_fields, projection_rows),
        evaluate_tau_registry(tau_fields, tau_rows),
        evaluate_matter_atlas(atlas_fields, atlas_rows),
    ]
    reasons = [reason for status, subreasons in results if status != "passed" for reason in subreasons]
    return ("failed", sorted(set(reasons))) if reasons else ("passed", [])


def executed_counterfactual_rows() -> list[dict[str, str]]:
    native_fields, native_rows = read_csv_with_fieldnames(FILES["native"])
    projection_fields, projection_rows = read_csv_with_fieldnames(FILES["si_second"])
    tau_fields, tau_rows = read_csv_with_fieldnames(FILES["tau"])
    atlas_fields, atlas_rows = read_csv_with_fieldnames(FILES["atlas"])
    specs = [
        {
            "counterfactual_id": "native_packet_target_value_inserted",
            "mutation_class": "target_quarantine",
            "mutated_lane": "hydrogen_transition_native_packets",
            "expected_result": "failed",
            "evaluator": evaluate_native_packets,
            "fieldnames": native_fields,
            "rows": native_rows,
            "mutation": mutate_target_value_inserted,
        },
        {
            "counterfactual_id": "SI_second_promoted_to_native_premise",
            "mutation_class": "projection_quarantine",
            "mutated_lane": "hydrogen_transition_si_second_projection_packets",
            "expected_result": "failed",
            "evaluator": evaluate_si_second_projection,
            "fieldnames": projection_fields,
            "rows": projection_rows,
            "mutation": mutate_si_promoted_to_native,
        },
        {
            "counterfactual_id": "circle_constant_promoted_to_native_cycle",
            "mutation_class": "notation_quarantine",
            "mutated_lane": "tau_cycle_notation_registry",
            "expected_result": "failed",
            "evaluator": evaluate_tau_registry,
            "fieldnames": tau_fields,
            "rows": tau_rows,
            "mutation": mutate_pi_promoted_to_native,
        },
        {
            "counterfactual_id": "external_target_lane_joined_before_freeze",
            "mutation_class": "observable_join_order",
            "mutated_lane": "sadar_lock_matter_octave_atlas",
            "expected_result": "failed",
            "evaluator": evaluate_matter_atlas,
            "fieldnames": atlas_fields,
            "rows": atlas_rows,
            "mutation": mutate_target_join_before_freeze,
        },
    ]
    rows_out: list[dict[str, str]] = []
    for order, spec in enumerate(specs):
        mutated_fields, mutated_rows = spec["mutation"](list(spec["fieldnames"]), copy.deepcopy(spec["rows"]))
        observed, reasons = spec["evaluator"](mutated_fields, mutated_rows)
        rows_out.append({
            "counterfactual_order": str(order),
            "counterfactual_id": spec["counterfactual_id"],
            "mutation_class": spec["mutation_class"],
            "mutated_lane": spec["mutated_lane"],
            "evaluation_mode": "executed_mutation_evaluator",
            "expected_result": spec["expected_result"],
            "observed_result": observed,
            "observed_failure_reasons": ";".join(reasons),
            "audit_status": "passed" if observed == spec["expected_result"] else "failed",
        })
    observed, reasons = evaluate_control()
    rows_out.append({
        "counterfactual_order": str(len(rows_out)),
        "counterfactual_id": "unchanged_hydrogen_atlas_control",
        "mutation_class": "control",
        "mutated_lane": "all",
        "evaluation_mode": "executed_mutation_evaluator",
        "expected_result": "passed",
        "observed_result": observed,
        "observed_failure_reasons": ";".join(reasons),
        "audit_status": "passed" if observed == "passed" else "failed",
    })
    return rows_out


def build_counterfactual_audit() -> None:
    write_csv(FILES["audit"], AUDIT_COLUMNS, executed_counterfactual_rows(), "counterfactual_row_sha256")


def build_manifest() -> None:
    generated = [
        FILES[key]
        for key in ("native", "si_second", "projection_index", "tau", "tau_index", "atlas", "audit")
    ]
    inputs = [
        H1_DETECTOR, H1_TRACE, H1_OCCURRENCE, ELEMENTS, LADDER_336, LADDER_346,
        FORMULA_RESIDUALS, CHAIN_PREDICTIONS, NUCLEOTIDES, PEPTIDES, PROTEIN_CHAINS,
    ]
    manifest = {
        "manifest_id": "manual2_hydrogen_transition_sadar_lock_atlas_v1",
        "version_scope": VERSION,
        "release_class": "target_blind_native_Hydrogen_transition_and_SADAR_lock_atlas_repair",
        "native_packet_policy": {
            "native_before_projection": True,
            "native_hash_isolation": "projection_and_tau_notation_excluded_from_native_packet_hash",
            "target_value_read_status": "not_read",
            "SI_second_status": "downstream_optional_projection_only",
            "tau_cycle_notation": "Tau_index_not_native_identity",
            "score_status": "no_score",
        },
        "index_ledgers": {
            "projection_index": FILES["projection_index"].relative_to(ROOT).as_posix(),
            "tau_notation_index": FILES["tau_index"].relative_to(ROOT).as_posix(),
        },
        "counterfactual_audit": {
            "audit_file": FILES["audit"].relative_to(ROOT).as_posix(),
            "execution_mode": "executed_mutation_evaluator",
            "control_status": "unchanged_control_must_pass",
        },
        "atlas_lanes": [
            "Hydrogen transition",
            "Elementary Matter 118",
            "Molecular Matter",
            "Biomolecular Matter",
        ],
        "generated_files": [source_card(path) for path in generated],
        "source_inputs": [source_card(path) for path in inputs],
        "deterministic_script": "manual-2/scripts/build_hydrogen_transition_sadar_lock_atlas.py",
        "current_gate_state": {
            "Hydrogen_r08": "r08_1_repair_authored_review_required_before_GO",
            "manual2_pdf": "rebuilt_from_source_after_authoring_repair",
            "comparison_join_state": "closed",
            "metric_projection_unit": "second",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_native_packets()
    build_si_second_projection()
    build_projection_index()
    build_tau_registry()
    build_tau_notation_index()
    build_matter_atlas()
    build_counterfactual_audit()
    build_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
