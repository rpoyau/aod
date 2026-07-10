#!/usr/bin/env python3
"""Build Manual-I relational temporal semantics schemas.

This generator is protocol-only. It separates D.E.C. execution structure,
monon cycle classification, path-conditioned RD/RCD, duonic pressure, SADAR
flow, relational temporal lock, sheddic exchange, and downstream observation
cards. It does not execute a new scientific simulation or read target values.
"""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manual" / "data" / "temporal_relational"
VERSION = "v40.03r06.3.1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def row_hash(row: Mapping[str, object], hash_field: str) -> str:
    payload = {k: str(v) for k, v in sorted(row.items()) if k != hash_field}
    return sha256_bytes(canonical_json_bytes(payload))


def attach_hash(row: Mapping[str, object], hash_field: str) -> dict[str, str]:
    out = {k: str(v) for k, v in row.items()}
    out[hash_field] = row_hash(out, hash_field)
    return out


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: str(row.get(k, "")) for k in fields})


def schema_rows(schema_id: str, fields: list[tuple[str, str, str, str, str]]) -> list[dict[str, str]]:
    rows = []
    for i, (field, dtype, required, role, allowed) in enumerate(fields):
        rows.append(attach_hash({
            "schema_id": schema_id,
            "field_order": i,
            "field": field,
            "type": dtype,
            "required": required,
            "role": role,
            "allowed_values": allowed,
        }, "schema_row_sha256"))
    return rows


def emit_schema(filename: str, schema_id: str, fields: list[tuple[str, str, str, str, str]]) -> None:
    rows = schema_rows(schema_id, fields)
    write_csv(OUT / filename,
              ["schema_id","field_order","field","type","required","role","allowed_values","schema_row_sha256"],
              rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    emit_schema("relational_temporal_type_registry.csv", "aod_relational_temporal_type_registry_v1", [
        ("bip", "executed_directed_beat_token", "yes", "one admitted executed or propagated directed beat; not a CSV row count and not temporal magnitude", ""),
        ("trace_count", "nonnegative_integer", "yes", "combinatorial execution/path length or resolution", ""),
        ("monon", "cycle_class", "yes", "primitive completed outbound-hinge-return cycle class", ""),
        ("minimal_direct_witness_bip_count", "positive_integer", "yes", "shortest direct monon witness contains one outbound and one inbound executed bip", "2"),
        ("minimal_witness_temporal_status", "enum", "yes", "minimal witness is not a universal monon duration", "witness_only_not_duration"),
        ("duon", "returned_current_relation", "yes", "returned-current form carried by the completed cycle", ""),
        ("C_n", "support_enclosure_object", "yes", "support/enclosure object; not a temporal unit", ""),
        ("L", "enclosure_or_window_qualifier", "yes", "outer/shared enclosure qualifier", ""),
        ("RD", "path_conditioned_accessor", "yes", "reflection duration accessor on an admitted path", ""),
        ("RCD", "coupled_relation", "yes", "RD coupled to asymmetric return", ""),
        ("rhoD_omega", "window_participation", "yes", "window-clipped current participation", ""),
        ("pD", "duonic_pressure", "yes", "local coupling load; not cadence", ""),
        ("SADAR", "directed_boundary_current_flow", "yes", "pressure-weighted returned-current flow", ""),
        ("temporal_measurement", "relational_phase_lock", "yes", "primitive phase/cadence lock between recurrent SADAR flow packets", ""),
    ])

    emit_schema("relational_temporal_measurement_packet.csv", "aod_relational_temporal_measurement_packet_v1", [
        ("temporal_measurement_id", "string", "yes", "packet identity", ""),
        ("subject_sadar_packet_id", "string", "yes", "subject recurrent flow packet", ""),
        ("reference_sadar_packet_id", "string", "yes", "reference recurrent flow packet", ""),
        ("subject_phase_extractor_id", "string", "yes", "frozen subject phase extractor", ""),
        ("reference_phase_extractor_id", "string", "yes", "frozen reference phase extractor", ""),
        ("coupling_boundary_id", "string", "yes", "declared coupling boundary", ""),
        ("coupling_window_id", "string", "yes", "declared coupling window", ""),
        ("subject_recurrence_count", "positive_integer", "yes", "primitive lock count m", ""),
        ("reference_recurrence_count", "positive_integer", "yes", "primitive lock count n", ""),
        ("phase_residual_num", "integer", "yes", "exact phase residual numerator", ""),
        ("phase_residual_den", "positive_integer", "yes", "exact phase residual denominator", ""),
        ("phase_modulus", "positive_integer_or_symbolic", "yes", "declared phase modulus", ""),
        ("proper_prefix_lock_count", "nonnegative_integer", "yes", "primitive-lock minimality audit", "0_for_primitive_lock"),
        ("primitive_lock_status", "enum", "yes", "primitive relation status", "passed;failed;candidate_set;unresolved"),
        ("alias_class_status", "enum", "yes", "phase alias treatment", "unique;equivalent_class;unresolved"),
        ("support_state", "enum", "yes", "support admission", "supported;ambiguous;excluded"),
        ("uncertainty_state", "enum", "yes", "observation-independent native uncertainty state", "exact;set_valued;unresolved"),
        ("temporal_ratio_num", "positive_integer", "yes_when_locked", "T_subject/T_reference numerator n", ""),
        ("temporal_ratio_den", "positive_integer", "yes_when_locked", "T_subject/T_reference denominator m", ""),
        ("frequency_ratio_num", "positive_integer", "yes_when_locked", "nu_subject/nu_reference numerator m", ""),
        ("frequency_ratio_den", "positive_integer", "yes_when_locked", "nu_subject/nu_reference denominator n", ""),
        ("target_value_read_status", "enum", "yes", "target quarantine", "not_read"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("duon_pressure_packet.csv", "aod_duon_pressure_packet_v1", [
        ("pressure_packet_id", "string", "yes", "packet identity", ""),
        ("duon_current_id", "string", "yes", "returned-current relation", ""),
        ("boundary_id", "string", "yes", "declared boundary", ""),
        ("window_id", "string", "yes", "declared window", ""),
        ("RD_packet_id", "string", "yes", "path-conditioned RD source", ""),
        ("RCD_packet_id", "string", "yes", "coupled RD/asymmetric-return source", ""),
        ("rhoD_omega_num", "integer", "yes", "window participation numerator", ""),
        ("rhoD_omega_den", "positive_integer", "yes", "window participation denominator", ""),
        ("C_num", "integer", "yes", "coupling coefficient numerator", ""),
        ("C_den", "positive_integer", "yes", "coupling coefficient denominator", ""),
        ("pD_num", "integer", "yes", "duonic pressure numerator", ""),
        ("pD_den", "positive_integer", "yes", "duonic pressure denominator", ""),
        ("cadence_status", "enum", "yes", "pressure is not cadence", "not_inferred_from_pressure"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("sadar_flow_packet.csv", "aod_sadar_flow_packet_v1", [
        ("sadar_packet_id", "string", "yes", "packet identity", ""),
        ("boundary_id", "string", "yes", "boundary scope", ""),
        ("window_id", "string", "yes", "window scope", ""),
        ("event_order_relation_id", "string", "yes", "exact execution order", ""),
        ("duon_pressure_packet_ids", "list[string]", "yes", "local pressure packets", ""),
        ("orientation_packet_ids", "list[string]", "yes", "directed ADAR orientation values", ""),
        ("flow_term_num", "list[integer]", "yes", "exact SADAR term numerators", ""),
        ("flow_term_den", "list[positive_integer]", "yes", "exact SADAR term denominators", ""),
        ("flow_sum_num", "integer", "yes", "exact SADAR sum numerator", ""),
        ("flow_sum_den", "positive_integer", "yes", "exact SADAR sum denominator", ""),
        ("kernel_weighted_status", "enum", "yes", "distinguish direct SADAR from expected kernel-weighted SADAR", "direct;kernel_weighted_expected"),
        ("trace_count_role", "enum", "yes", "trace count does not define flow magnitude", "execution_structure_only"),
        ("recurrence_status", "enum", "yes", "flow recurrence state", "not_evaluated;candidate;primitive;nonprimitive;unresolved"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("sadar_phase_lock_packet.csv", "aod_sadar_phase_lock_packet_v1", [
        ("phase_lock_packet_id", "string", "yes", "packet identity", ""),
        ("subject_sadar_packet_id", "string", "yes", "subject flow", ""),
        ("reference_sadar_packet_id", "string", "yes", "reference flow", ""),
        ("subject_recurrence_count", "positive_integer", "yes", "coprime lock count m", ""),
        ("reference_recurrence_count", "positive_integer", "yes", "coprime lock count n", ""),
        ("gcd_count", "positive_integer", "yes", "must equal one for primitive lock", "1"),
        ("proper_prefix_lock_count", "nonnegative_integer", "yes", "primitive-lock minimality audit", "0_for_primitive_lock"),
        ("phase_residual_num", "integer", "yes", "exact residual numerator", ""),
        ("phase_residual_den", "positive_integer", "yes", "exact residual denominator", ""),
        ("close_status", "enum", "yes", "RelLock closure", "passed;failed;unresolved"),
        ("primitive_lock_status", "enum", "yes", "no proper prefix lock", "passed;failed;unresolved"),
        ("temporal_ratio_num", "positive_integer", "yes_when_passed", "n", ""),
        ("temporal_ratio_den", "positive_integer", "yes_when_passed", "m", ""),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("rd_path_distribution_packet.csv", "aod_rd_path_distribution_packet_v1", [
        ("rd_distribution_id", "string", "yes", "packet identity", ""),
        ("dec_path_family_id", "string", "yes", "admitted exact path family", ""),
        ("path_id", "string", "yes", "individual path", ""),
        ("path_probability_num", "integer", "yes", "exact path probability numerator", ""),
        ("path_probability_den", "positive_integer", "yes", "exact path probability denominator", ""),
        ("RD_value_num", "integer", "yes", "path-conditioned RD numerator", ""),
        ("RD_value_den", "positive_integer", "yes", "path-conditioned RD denominator", ""),
        ("RCD_packet_id", "string", "yes", "formed after RD", ""),
        ("distribution_mass_status", "enum", "yes", "exact distribution normalization", "passed;failed"),
        ("temporal_measurement_status", "enum", "yes", "RD is not itself time", "path_conditioned_observable_only"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("sheddic_exchange_flux_packet.csv", "aod_sheddic_exchange_flux_packet_v1", [
        ("sheddic_flux_packet_id", "string", "yes", "packet identity", ""),
        ("source_sadar_packet_id", "string", "yes", "source directed flow", ""),
        ("target_sadar_packet_id", "string", "yes", "receiving directed flow", ""),
        ("sheddic_channel_id", "string", "yes", "declared sheddic exchange channel", ""),
        ("sheddic_exchange_source", "enum", "yes", "source class for transfer", "surplus_routing;externally_driven_exchange;balanced_return_exchange;reclosure_exchange"),
        ("capacity_surplus_num", "integer", "yes", "X_shedding scalar surplus numerator", ""),
        ("capacity_surplus_den", "positive_integer", "yes", "X_shedding scalar surplus denominator", ""),
        ("flux_num", "integer", "yes", "directed sheddic flux numerator", ""),
        ("flux_den", "positive_integer", "yes", "directed sheddic flux denominator", ""),
        ("zero_surplus_nonzero_flux_admission", "enum", "yes", "requires declared non-surplus exchange source", "allowed_only_for_declared_exchange_source"),
        ("physical_interpretation_status", "enum", "yes", "physical label attaches downstream", "native_sheddic_only"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("cs_sheddic_drive_temporal_reference_packet.csv", "aod_cs_sheddic_drive_temporal_reference_packet_v1", [
        ("reference_packet_id", "string", "yes", "packet identity", ""),
        ("cs_occurrence_id", "string", "yes", "Cs-scoped occurrence", ""),
        ("cs_sadar_packet_id", "string", "yes", "Cs recurrent SADAR flow", ""),
        ("drive_sadar_packet_id", "string", "yes", "declared sheddic-drive SADAR flow", ""),
        ("sheddic_flux_packet_id", "string", "yes", "state-transfer exchange flux", ""),
        ("primitive_phase_lock_packet_id", "string", "yes", "native relational lock", ""),
        ("native_reference_period_id", "string", "yes_when_locked", "primitive relational period", ""),
        ("physical_drive_label_status", "enum", "yes", "microwave/clock terminology attaches downstream", "downstream_metrology_only"),
        ("SI_reference_card_status", "enum", "yes", "optional metrological realization", "inactive;declared;active"),
        ("bips_per_second_status", "enum", "yes", "no native identity", "not_a_native_definition"),
        ("target_value_read_status", "enum", "yes", "target quarantine", "not_read"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("hydrogen_balmer_relational_ratio_packet.csv", "aod_hydrogen_balmer_relational_ratio_packet_v1", [
        ("ratio_packet_id", "string", "yes", "packet identity", ""),
        ("transition_ids", "list[string]", "yes", "3->2;4->2;5->2;6->2", ""),
        ("native_phase_lock_packet_ids", "list[string]", "yes", "four frozen native relational periods", ""),
        ("native_period_ratio_integers", "list[positive_integer]", "yes", "native derived ratio", ""),
        ("comparison_period_ratio_integers", "list[positive_integer]", "yes", "downstream exact ratio card", "1512;1120;1000;945"),
        ("comparison_frequency_ratio_integers", "list[positive_integer]", "yes", "downstream exact ratio card", "500;675;756;800"),
        ("ratio_cross_multiplication_status", "enum", "yes", "exact ratio audit", "pending;passed;mismatch;unresolved"),
        ("SI_unit_status", "enum", "yes", "dimensionless before optional report", "not_required"),
        ("target_value_read_status", "enum", "yes", "target card joins after native packet freeze", "not_read_during_generation"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("tau_survival_hazard_packet.csv", "aod_tau_survival_hazard_packet_v1", [
        ("tau_survival_packet_id", "string", "yes", "packet identity", ""),
        ("tau_occurrence_id", "string", "yes", "native Tau support occurrence", ""),
        ("reference_sadar_packet_id", "string", "yes", "reference recurrent flow", ""),
        ("reference_interval_index", "nonnegative_integer", "yes", "n reference periods", ""),
        ("survival_num", "integer", "yes", "exact survival probability numerator", ""),
        ("survival_den", "positive_integer", "yes", "exact survival probability denominator", ""),
        ("hazard_num", "integer", "yes", "exact conditional hazard numerator", ""),
        ("hazard_den", "positive_integer", "yes", "exact conditional hazard denominator", ""),
        ("mean_lifetime_ratio_num", "integer", "yes_when_defined", "E[T_tau/T_ref] numerator", ""),
        ("mean_lifetime_ratio_den", "positive_integer", "yes_when_defined", "E[T_tau/T_ref] denominator", ""),
        ("fixed_tau_bip_count_status", "enum", "yes", "Tau is not a fixed periodic count", "forbidden"),
        ("target_value_read_status", "enum", "yes", "target quarantine", "not_read"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    emit_schema("element_transition_relational_atlas_schema.csv", "aod_element_transition_relational_atlas_schema_v1", [
        ("element_Z", "integer", "yes", "element identity", ""),
        ("isotope_A", "integer", "yes", "isotope identity", ""),
        ("state_id", "string", "yes", "native state packet", ""),
        ("transition_id", "string", "yes", "native transition occurrence", ""),
        ("subject_sadar_packet_id", "string", "yes", "element transition flow", ""),
        ("drive_sadar_packet_id", "string", "yes", "declared sheddic-drive reference flow", ""),
        ("phase_lock_packet_id", "string", "yes", "primitive relational lock", ""),
        ("native_period_ratio_num", "integer", "yes_when_compared", "exact ratio numerator", ""),
        ("native_period_ratio_den", "positive_integer", "yes_when_compared", "exact ratio denominator", ""),
        ("reference_protocol_id", "string", "yes", "one shared relational reference protocol", ""),
        ("private_bip_to_second_coefficient_status", "enum", "yes", "per-element conversion forbidden", "forbidden"),
        ("optional_SI_report_status", "enum", "yes", "downstream only", "inactive;available_after_reference_lock"),
        ("native_packet_sha256", "sha256", "yes", "native packet lock", ""),
    ])

    emit_schema("circle_relational_audit_packet.csv", "aod_circle_relational_audit_packet_v1", [
        ("circle_audit_packet_id", "string", "yes", "packet identity", ""),
        ("radius_report_packet_id", "string", "yes", "declared geometry/report radius", ""),
        ("circumference_trace_packet_id", "string", "yes", "independent circumference trace", ""),
        ("area_trace_packet_id", "string", "yes", "independent area trace", ""),
        ("C_num", "integer", "yes", "circumference rational numerator", ""),
        ("C_den", "positive_integer", "yes", "circumference rational denominator", ""),
        ("r_num", "integer", "yes", "radius rational numerator", ""),
        ("r_den", "positive_integer", "yes", "radius rational denominator", ""),
        ("A_num", "integer", "yes", "area rational numerator", ""),
        ("A_den", "positive_integer", "yes", "area rational denominator", ""),
        ("R_CA_num", "integer", "yes", "exact Cr-2A residual numerator", ""),
        ("R_CA_den", "positive_integer", "yes", "exact residual denominator", ""),
        ("zero_identity_status", "enum", "yes", "zero is audited not imposed", "audited_result_not_assumed"),
        ("pi_report_status", "enum", "yes", "dimensionless report/refinement lane", "downstream_geometry_report"),
        ("packet_sha256", "sha256", "yes", "canonical packet hash", ""),
    ])

    files = []
    for p in sorted(OUT.glob("*.csv")):
        files.append({"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest = {
        "manifest_id": "aod_relational_temporal_semantics_protocol_v1",
        "version_scope": VERSION,
        "release_role": "semantic_type_repair_no_new_scientific_result",
        "central_rule": "executed_bip_structure_plus_duonic_pressure_plus_SADAR_flow_plus_primitive_reference_lock",
        "monon_semantics": "cycle_class_with_two_bip_minimal_direct_witness_not_duration",
        "trace_count_temporal_status": "execution_structure_not_temporal_magnitude",
        "sheddic_terminology": "native_sheddic_only",
        "target_value_read_status": "not_read",
        "residual_status": "not_computed",
        "score_status": "not_computed",
        "files": files,
    }
    (OUT / "relational_temporal_semantics_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
