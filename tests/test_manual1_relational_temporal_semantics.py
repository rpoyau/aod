import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "temporal_relational"
SCRIPT = ROOT / "manual" / "scripts" / "build_relational_temporal_semantics.py"


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def by_field(name):
    return {r["field"]: r for r in rows(name)}


def test_bip_trace_monon_types_are_separate():
    reg = by_field("relational_temporal_type_registry.csv")
    assert reg["bip"]["type"] == "executed_directed_beat_token"
    assert "not a CSV row count" in reg["bip"]["role"]
    assert reg["trace_count"]["type"] == "nonnegative_integer"
    assert reg["monon"]["type"] == "cycle_class"
    assert reg["minimal_direct_witness_bip_count"]["allowed_values"] == "2"
    assert reg["minimal_witness_temporal_status"]["allowed_values"] == "witness_only_not_duration"


def test_rd_precedes_rcd_and_pressure_is_not_cadence():
    rd = by_field("rd_path_distribution_packet.csv")
    assert rd["RD_value_num"]["required"] == "yes"
    assert rd["RCD_packet_id"]["role"] == "formed after RD"
    pressure = by_field("duon_pressure_packet.csv")
    assert pressure["cadence_status"]["allowed_values"] == "not_inferred_from_pressure"


def test_sadar_flow_is_independent_of_trace_count():
    s = by_field("sadar_flow_packet.csv")
    assert s["trace_count_role"]["allowed_values"] == "execution_structure_only"
    assert s["flow_sum_num"]["required"] == "yes"
    assert s["recurrence_status"]["type"] == "enum"


def test_temporal_measurement_requires_subject_and_reference_flows():
    t = by_field("relational_temporal_measurement_packet.csv")
    assert t["subject_sadar_packet_id"]["required"] == "yes"
    assert t["reference_sadar_packet_id"]["required"] == "yes"
    assert t["subject_recurrence_count"]["required"] == "yes"
    assert t["reference_recurrence_count"]["required"] == "yes"
    assert t["target_value_read_status"]["allowed_values"] == "not_read"


def test_exact_phase_lock_packet_carries_primitive_ratio():
    p = by_field("sadar_phase_lock_packet.csv")
    assert p["gcd_count"]["allowed_values"] == "1"
    assert p["proper_prefix_lock_count"]["allowed_values"] == "0_for_primitive_lock"
    assert p["temporal_ratio_num"]["required"] == "yes_when_passed"
    assert p["temporal_ratio_den"]["required"] == "yes_when_passed"


def test_native_exchange_is_sheddic_and_surplus_is_separate_from_flux():
    p = by_field("sheddic_exchange_flux_packet.csv")
    assert p["capacity_surplus_num"]["required"] == "yes"
    assert p["flux_num"]["required"] == "yes"
    assert "surplus_routing" in p["sheddic_exchange_source"]["allowed_values"]
    assert p["physical_interpretation_status"]["allowed_values"] == "native_sheddic_only"
    text = "\n".join(x.read_text(encoding="utf-8") for x in DATA.glob("*"))
    assert "native_sheddic_only" in text


def test_cs_reference_is_optional_and_has_no_bips_per_second_identity():
    p = by_field("cs_sheddic_drive_temporal_reference_packet.csv")
    assert p["physical_drive_label_status"]["allowed_values"] == "downstream_metrology_only"
    assert p["bips_per_second_status"]["allowed_values"] == "not_a_native_definition"
    assert p["target_value_read_status"]["allowed_values"] == "not_read"


def test_hydrogen_ratio_is_dimensionless_and_downstream():
    p = by_field("hydrogen_balmer_relational_ratio_packet.csv")
    assert p["comparison_period_ratio_integers"]["allowed_values"] == "1512;1120;1000;945"
    assert p["comparison_frequency_ratio_integers"]["allowed_values"] == "500;675;756;800"
    assert p["SI_unit_status"]["allowed_values"] == "not_required"
    assert p["target_value_read_status"]["allowed_values"] == "not_read_during_generation"


def test_tau_uses_survival_hazard_not_fixed_bip_lifetime():
    p = by_field("tau_survival_hazard_packet.csv")
    assert p["survival_num"]["required"] == "yes"
    assert p["hazard_num"]["required"] == "yes"
    assert p["fixed_tau_bip_count_status"]["allowed_values"] == "forbidden"


def test_circle_zero_is_audited_not_imposed():
    p = by_field("circle_relational_audit_packet.csv")
    assert p["R_CA_num"]["required"] == "yes"
    assert p["zero_identity_status"]["allowed_values"] == "audited_result_not_assumed"


def test_all_elements_share_one_relational_protocol_without_private_conversion():
    p = by_field("element_transition_relational_atlas_schema.csv")
    assert p["subject_sadar_packet_id"]["required"] == "yes"
    assert p["drive_sadar_packet_id"]["required"] == "yes"
    assert p["phase_lock_packet_id"]["required"] == "yes"
    assert p["private_bip_to_second_coefficient_status"]["allowed_values"] == "forbidden"


def test_generator_is_deterministic_and_manifest_hashes_all_schemas():
    before = {p.name: p.read_bytes() for p in DATA.iterdir() if p.is_file()}
    subprocess.run([sys.executable, str(SCRIPT)], check=True)
    after = {p.name: p.read_bytes() for p in DATA.iterdir() if p.is_file()}
    assert before == after
    manifest = json.loads((DATA / "relational_temporal_semantics_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version_scope"] == "v40.03r06.3.1"
    assert manifest["monon_semantics"] == "cycle_class_with_two_bip_minimal_direct_witness_not_duration"
    assert manifest["sheddic_terminology"] == "native_sheddic_only"
    for item in manifest["files"]:
        p = ROOT / item["path"]
        assert p.stat().st_size == item["bytes"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == item["sha256"]


def test_manual_i_renders_relational_temporal_semantics_and_no_bad_equivalence():
    e = (ROOT / "manual/appendices/E_native_si_anchor_iteration_plan.tex").read_text(encoding="utf-8")
    g = (ROOT / "manual/appendices/G_relational_temporal_coupling_semantics.tex").read_text(encoding="utf-8")
    all_text = e + "\n" + g
    assert "Relational Temporal Coupling" in g
    assert "N_{\\mathrm{bip}}^{\\min}(\\mathrm{monon})=2" in all_text
    assert "monon-to-bip conversion" not in all_text
    assert "bip(\\ell)" not in all_text
    assert "Sheddic exchange" in all_text
    assert "R_{CA}=C_\\zeta r_\\zeta-2A_\\zeta" in all_text
