from fractions import Fraction
from pathlib import Path
import csv
import json
import math


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual" / "data" / "phase_temporal"


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_phase_cycle_closures_are_derived_and_fixture_scoped():
    phase = rows("phase_cycle_closure.csv")
    assert [r["cycle_id"] for r in phase] == ["C_3_4", "C_3_3"]
    for row in phase:
        p = int(row["p"])
        q = int(row["q"])
        branch = q**p + q
        closure = 2 * branch + 1
        assert int(row["branch_support"]) == branch
        assert int(row["hinge_index"]) == branch
        assert int(row["closure_count"]) == closure
        assert row["handed_return_witness"] == "true"
        assert row["relation_destroyed_semantic_closure"] == "false"


def test_relational_recurrence_keeps_local_and_window_counts_typed():
    phase = rows("phase_cycle_closure.csv")
    closures = {r["cycle_id"]: int(r["closure_count"]) for r in phase}
    extracted = {r["cycle_id"]: int(r["common_window_extracted_count"]) for r in phase}
    common = math.lcm(*closures.values())
    assert common == 8357
    assert extracted == {"C_3_4": 61, "C_3_3": 137}
    for cycle_id, closure in closures.items():
        assert extracted[cycle_id] == common // closure


def test_cadence_trace_separates_shedding_retention_and_extractor_ticks():
    trace = rows("cadence_signature_trace.csv")
    counted = [r for r in trace if r["count_scope"] == "true"]
    ordered = sorted(counted, key=lambda r: int(r["logical_index"]))
    g_ticks = [r["event_id"] for r in ordered if r["extractor_G_tick"] == "true"]
    f_ticks = [r["event_id"] for r in ordered if r["extractor_F_tick"] == "true"]
    assert g_ticks == ["p.d0.shed", "p.d1.shed", "p.d2.shed"]
    assert f_ticks == ["p.d0.admit", "p.d1.admit"]
    for row in ordered:
        if row["event_class"] == "shedding_event":
            assert row["retention_before"] == "true"
            assert row["retention_after"] == "false"


def test_cadence_extraction_is_serialization_invariant_and_not_source_unique():
    trace = rows("cadence_signature_trace.csv")

    def extract(records, field):
        return [
            r["event_id"]
            for r in sorted(records, key=lambda r: int(r["logical_index"]))
            if r["count_scope"] == "true" and r[field] == "true"
        ]

    assert extract(trace, "extractor_G_tick") == extract(list(reversed(trace)), "extractor_G_tick")
    assert extract(trace, "extractor_F_tick") == extract(list(reversed(trace)), "extractor_F_tick")
    sigma0_sources = {
        r["source_field"]
        for r in trace
        if r["signature_out"] == "sigma0" and r["source_field"]
    }
    assert {"G0", "G1"}.issubset(sigma0_sources)


def test_five_lane_matrix_separates_trace_report_relation_and_probe():
    matrix = {r["lane"]: r for r in rows("cadence_control_matrix.csv")}
    assert set(matrix) == {"A", "B", "C", "D", "E"}
    assert all(
        r["common_window_extracted_F_3_4"] == "61"
        and r["common_window_extracted_F_3_3"] == "137"
        for r in matrix.values()
    )
    assert matrix["A"]["cadence"] == ""
    assert matrix["B"]["cadence"] == matrix["C"]["cadence"] == matrix["D"]["cadence"] == "3:2"
    assert matrix["E"]["cadence"] == "3:1"
    assert matrix["A"]["core_equals_A"] == matrix["B"]["core_equals_A"] == matrix["C"]["core_equals_A"] == "true"
    assert matrix["C"]["report_emitted"] == "true"
    assert matrix["C"]["report_feedback"] == "false"
    assert matrix["D"]["coupling_witness"] == "true"
    assert matrix["D"]["R_probe"] == "2"
    assert matrix["E"]["coupling_witness"] == "false"
    assert matrix["E"]["R_probe"] == "0"


def test_finite_pi_projection_retains_all_exact_rows_and_identities():
    projection = rows("finite_pi_projection.csv")
    assert [int(r["r"]) for r in projection] == [1, 2, 4, 8, 16, 32, 64, 128, 256]
    assert [int(r["C"]) for r in projection] == [8, 12, 32, 48, 112, 188, 440, 788, 1608]
    assert [int(r["A"]) for r in projection] == [1, 9, 45, 193, 793, 3205, 12849, 51429, 205857]
    for row in projection:
        radius = int(row["r"])
        boundary = int(row["C"])
        interior = int(row["A"])
        residual = radius * boundary - 2 * interior
        pi_c = Fraction(boundary, 2 * radius)
        pi_a = Fraction(interior, radius * radius)
        assert Fraction(row["pi_hat_C"]) == pi_c
        assert Fraction(row["pi_hat_A"]) == pi_a
        assert int(row["R_C_A"]) == residual
        assert Fraction(row["differential_pi"]) == Fraction(residual, 2 * radius * radius)
        assert Fraction(row["differential_tau"]) == Fraction(residual, radius * radius)
    final = projection[-1]
    assert final["pi_hat_C"] == "201/64"
    assert final["pi_hat_A"] == "205857/65536"
    assert final["differential_pi"] == "-33/65536"


def test_projection_scope_records_finite_nonmonotone_and_no_convergence_claim():
    projection = rows("finite_pi_projection.csv")
    pi_a = [Fraction(r["pi_hat_A"]) for r in projection]
    lower = Fraction(103993, 33102)
    upper = Fraction(104348, 33215)
    assert all(value < lower for value in pi_a)
    assert all(a < b for a, b in zip(pi_a, pi_a[1:]))
    boundary_classes = [r["boundary_error_class"] for r in projection]
    assert "ABOVE_REFERENCE_ENCLOSURE" in boundary_classes
    assert "BELOW_REFERENCE_ENCLOSURE" in boundary_classes
    binding = json.loads((DATA / "scientific_result_bindings.json").read_text(encoding="utf-8"))
    qualifications = " ".join(binding["scope_qualifications"])
    assert "no convergence theorem" in qualifications.lower()
    assert "no universal pi derivation" in qualifications.lower()


def test_main_phase_cadence_and_temporal_flow_are_bone_dry_and_typed():
    cycle = (ROOT / "sections" / "05_curl_closure_duon_current.tex").read_text(encoding="utf-8")
    field = (ROOT / "sections" / "06_field.tex").read_text(encoding="utf-8")
    wave = (ROOT / "appendices" / "F_wave.tex").read_text(encoding="utf-8")
    glossary = (ROOT / "appendices" / "E_glossary.tex").read_text(encoding="utf-8")
    assert "A tick emits a duon current" not in cycle
    assert "Cadence diagnostics are" not in cycle
    assert r"\theta_u(t)=t\bmod RD_{\AO}(C_u)" not in cycle
    for token in [r"\kappa_{K,B,\omega}", r"N_C=\min", r"\eta_C(s_i,s_j)"]:
        assert token in cycle
    for token in [r"\mathcal R_\Sigma", r"R_{\mathrm{probe}}", "UncoupledTransit", "SourceUnconditioned"]:
        assert token in field
    assert "SADAR-valued ordered-window presentation" in wave
    assert "temporal SADAR presentation" not in wave
    for term in ["Native phase cycle", "Declared extractor", "Temporal cadence", "Relational temporal flow", "Probe response"]:
        assert term in glossary


def test_legacy_updates_are_not_automatically_named_ticks():
    prohibited = {
        "sections/04_cut_running_fractal_tesseract.tex": ["tick/click"],
        "appendices/D_cycle_shedding_demonstration.tex": ["For tick", "uses \\(90\\) ticks", "declared ticks"],
        "sections/06_field.tex": ["tick count", "retained tick duration"],
        "manual/data/run_tumble/run_tumble_trace_table.tex": ["20-tick"],
        "manual/scripts/aod_run_tumble_3d_trace.py": ["20-tick", "by tick"],
    }
    for rel, phrases in prohibited.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase not in text


def test_manual_operational_record_uses_required_order_and_scope_boundaries():
    manual = (ROOT / "manual" / "sections" / "08_phase_temporal_flow_audit.tex").read_text(encoding="utf-8")
    headings = [
        r"\subsection{Scope}",
        r"\subsection{Declaration}",
        r"\subsection{Fixture}",
        r"\subsection{State row}",
        r"\subsection{Execution}",
        r"\subsection{Passive trace}",
        r"\subsection{Controls}",
        r"\subsection{Exact audit}",
        r"\subsection{Formation}",
        r"\subsection{Falsification}",
        r"\subsection{Provenance}",
    ]
    positions = [manual.index(heading) for heading in headings]
    assert positions == sorted(positions)
    for phrase in [
        "fixture-produced cadence",
        "not a released-source prediction",
        "not a native one-unit-to-one-tick law",
        "Structural keys alone do not constitute cadence",
        "role assignment requires",
        "Hamming distance over the ordered final",
        "physical transducer is not instantiated",
        "reported clock signal is not instantiated",
    ]:
        assert phrase in manual


def test_coordinate_residue_fixture_is_not_native_phase_closure():
    appendix = (ROOT / "manual" / "appendices" / "C_3d_coordinate_phase_cycle_delta3_fixture.tex").read_text(encoding="utf-8")
    assert "downstream coordinate-residue presentation" in appendix
    assert "does not generate the native closure count" in appendix
    assert "is not the native phase-cycle relation" in appendix


def test_scientific_result_bindings_are_content_complete_and_qualified():
    binding = json.loads((DATA / "scientific_result_bindings.json").read_text(encoding="utf-8"))
    assert binding["status"] == "ALL_REQUIRED_RESULTS_CONTENT_BOUND"
    artifacts = {row["id"]: row for row in binding["artifacts"]}
    assert artifacts["r07_1_phase_temporal"]["archive_sha256"] == "060df61f65be3fa8325ad2d5be127c00303a7d280e512e36588553df0009eb8c"
    assert artifacts["r08_finite_pi_error"]["archive_sha256"] == "422d09b62b529dbb1246b768cd1022737cfb9093789bd078c25f266827af6ec1"
    assert artifacts["r08_1_temporal_cadence"]["archive_sha256"] == "6f0e19b3ffaab2f696192bb4236a2c9f19887abdede209ccd98252df9918e7a6"
    assert artifacts["integrated_scientific_review"]["sha256"] == "f4d86556d226c80fd55cabe8b5e94c38efd83844ede947b385fd0fce18a7de78"
    text = " ".join(binding["scope_qualifications"])
    for token in ["R_Sigma", "M0", "3:2", "one-unit-to-one-tick", "transducer", "maser"]:
        assert token in text


def test_v41_release_metadata_surfaces_are_synchronized():
    canonical = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    preamble = (ROOT / "preamble.tex").read_text(encoding="utf-8")
    manual_preamble = (ROOT / "manual" / "preamble.tex").read_text(encoding="utf-8")
    assert "Canonical version: v41.0.0" in canonical
    assert "**Version:** v41.0.0" in readme
    assert zenodo["version"] == "v41.0.0"
    assert zenodo["publication_date"] == "2026-07-20"
    assert r"\newcommand{\AODDocumentDate}{July 20, 2026}" in preamble
    assert r"\newcommand{\AODDocumentDate}{July 20, 2026}" in manual_preamble
