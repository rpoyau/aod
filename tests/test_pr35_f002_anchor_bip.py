from pathlib import Path
import csv
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "phase_temporal"
FROZEN_BINDING_SHA256 = (
    "9834e8ac7a45d90d6e3a10f6386595b8544c51296d5292e6f71221c2ff9fdb0a"
)


def rows():
    with (DATA / "anchor_bip_temporal_flow.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        return {row["case_id"]: row for row in csv.DictReader(handle)}


def test_f002_t01_anchor_bip_is_one_hamming_incidence_from_null():
    anchor = rows()["anchor_only"]
    assert anchor["anchor_bip"] == "00_8"
    assert anchor["source_potential"] == "Null"
    assert anchor["d_H"] == "1"
    assert anchor["native_incidence"] == "1"


def test_f002_t02_anchor_has_no_intrinsic_elapsed_duration():
    anchor = rows()["anchor_only"]
    assert anchor["second_bip"] == ""
    assert anchor["relation_present"] == "false"
    assert anchor["return_or_closure"] == "false"
    assert anchor["extractor"] == ""
    assert anchor["reported_duration"] == ""


def test_f002_t03_same_anchor_incidence_admits_different_reported_durations():
    fixture = rows()
    a = fixture["duration_a"]
    b = fixture["duration_b"]
    assert (a["anchor_bip"], a["d_H"]) == (b["anchor_bip"], b["d_H"]) == (
        "00_8",
        "1",
    )
    assert a["report_unit"] == b["report_unit"] == "declared_report_unit"
    assert a["reported_duration"] != b["reported_duration"]


def test_f002_t04_second_bip_is_required_for_relational_temporal_flow():
    fixture = rows()
    anchor = fixture["anchor_only"]
    related = fixture["duration_a"]
    assert anchor["second_bip"] == ""
    assert anchor["relation_present"] == "false"
    assert anchor["x_T"] == ""
    assert related["second_bip"] != ""
    assert related["relation_present"] == "true"
    assert related["x_T"] != ""


def test_f002_t05_same_ternary_flow_count_can_have_different_extractor_count():
    fixture = rows()
    a = fixture["duration_a"]
    b = fixture["duration_b"]
    assert a["x_T"] == b["x_T"] == "3"
    assert a["N_C"] == b["N_C"] == ""
    assert a["N_kappa"] == "1"
    assert b["N_kappa"] == "2"
    assert a["N_kappa"] != b["N_kappa"]


def test_f002_t06_kernel_threshold_changes_weighting_only():
    fixture = rows()
    iso = fixture["kernel_iso"]
    aniso = fixture["kernel_aniso"]
    invariant_fields = [
        "anchor_bip",
        "source_potential",
        "d_H",
        "native_incidence",
        "second_bip",
        "relation_present",
        "return_or_closure",
        "extractor",
        "x_T",
        "N_C",
        "N_kappa",
        "reported_duration",
        "report_unit",
        "engine_output",
    ]
    assert all(iso[field] == aniso[field] for field in invariant_fields)
    assert iso["d_phi"] == "0"
    assert aniso["d_phi"] == "1"
    assert iso["kernel_weighting"] == "isotropic"
    assert aniso["kernel_weighting"] == "anisotropic"


def test_f002_t07_passive_trace_leaves_engine_output_byte_identical():
    fixture = rows()
    bare = fixture["trace_bare"]
    passive = fixture["trace_passive"]
    assert bare["passive_trace"] == "false"
    assert passive["passive_trace"] == "true"
    assert bare["engine_output"].encode() == passive["engine_output"].encode()
    assert json.loads(bare["engine_output"]) == {
        "closure": True,
        "events": [1, 0, -1],
        "x_T": 9,
    }


def test_f002_t08_frozen_scientific_result_bindings_are_byte_unchanged():
    binding = DATA / "scientific_result_bindings.json"
    assert hashlib.sha256(binding.read_bytes()).hexdigest() == FROZEN_BINDING_SHA256
    data = json.loads(binding.read_text(encoding="utf-8"))
    hashes = {
        artifact["id"]: artifact["archive_sha256"]
        for artifact in data["artifacts"]
    }
    assert hashes == {
        "r07_1_phase_temporal": "060df61f65be3fa8325ad2d5be127c00303a7d280e512e36588553df0009eb8c",
        "r08_finite_pi_error": "422d09b62b529dbb1246b768cd1022737cfb9093789bd078c25f266827af6ec1",
        "r08_1_temporal_cadence": "6f0e19b3ffaab2f696192bb4236a2c9f19887abdede209ccd98252df9918e7a6",
        "integrated_scientific_review": "6f0e19b3ffaab2f696192bb4236a2c9f19887abdede209ccd98252df9918e7a6",
    }


def test_f002_main_and_manual_carry_the_repaired_types_and_downstream_boundary():
    address = (ROOT / "appendices" / "A_fractal_address_bip_biz.tex").read_text(
        encoding="utf-8"
    )
    field = (ROOT / "sections" / "06_field.tex").read_text(encoding="utf-8")
    manual = (
        ROOT / "manual" / "sections" / "08_phase_temporal_flow_audit.tex"
    ).read_text(encoding="utf-8")
    for token in [
        r"\mathtt{00}_8",
        r"d_H(\mathcal N,\mathtt{00}_8)=1",
        "native incidence",
    ]:
        assert token in address
    assert "intrinsic elapsed duration" in address.lower()
    for token in [
        r"x_T=3n",
        r"N_C",
        r"N_\kappa",
        r"d_H",
        r"2d_\varphi\ge1",
        "bip-to-bip",
    ]:
        assert token in field
    for token in [
        "declared report unit",
        "same ternary temporal-flow count",
        "kernel-selector control",
        "diagonal irrational completion",
        "transcendental",
    ]:
        assert token in manual
