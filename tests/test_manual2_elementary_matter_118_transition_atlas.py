from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ELEM = ROOT / "manual-2" / "data" / "elementary"


def row_hash(row: dict[str, str]) -> str:
    payload = {k: row[k] for k in row if k != "row_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (ELEM / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_elementary_118_atlas_rows_are_materialized_and_target_blind():
    occurrences = read_csv("elementary_matter_118_occurrence_cards.csv")
    transitions = read_csv("elementary_matter_118_transition_packets.csv")
    sadar = read_csv("elementary_matter_118_sadar_flow_declarations.csv")
    assert len(occurrences) == 118
    assert len(transitions) == 118
    assert len(sadar) == 118
    assert occurrences[0]["symbol"] == "H"
    assert occurrences[-1]["symbol"] == "Og"
    for row in occurrences:
        assert row["native_flow_status"] == "native_occurrence_card_materialized"
        assert row["target_value_read_status"] == "not_read"
        assert row["metric_report_status"] == "closed"
        assert row["residual_status"] == "not_computed"
        assert row["score_status"] == "no_score"
        assert row["row_sha256"] == row_hash(row)
    for row in transitions:
        assert row["target_value_read_status"] == "not_read"
        assert row["si_report_status"] == "closed"
        assert row["metric_report_status"] == "closed"
        assert row["residual_status"] == "not_computed"
        assert row["score_status"] == "no_score"
        assert row["hyperfine_c6_divisibility_status"] == "not_evaluated_until_native_resonance_packet_exists"
        assert row["row_sha256"] == row_hash(row)
    for row in sadar:
        assert row["duon_current_flow_status"] == "declared_not_executed"
        assert row["sadar_temporal_flow_status"] == "declared_not_executed"
        assert row["subject_reference_phase_lock_status"] == "not_materialized"
        assert row["row_sha256"] == row_hash(row)


def test_elementary_118_manifest_hashes_and_summary_are_consistent():
    manifest = json.loads((ELEM / "elementary_matter_118_transition_atlas_manifest.json").read_text())
    assert manifest["row_counts"]["occurrence_cards"] == 118
    assert manifest["row_counts"]["transition_packets"] == 118
    assert manifest["row_counts"]["sadar_flow_declarations"] == 118
    assert manifest["closed_lanes"]["target_join"] == "closed"
    assert manifest["closed_lanes"]["SI_report_values"] == "closed"
    assert manifest["closed_lanes"]["scores"] == "no_score"
    for rel, expected in manifest["files"].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual == expected
    summary = read_csv("elementary_matter_118_transition_atlas_summary.csv")
    assert summary == [{
        "summary_id": "elementary_matter_118_transition_atlas_summary",
        "occurrence_count": "118",
        "transition_packet_count": "118",
        "sadar_declaration_count": "118",
        "target_join_count": "0",
        "si_report_count": "0",
        "metric_report_count": "0",
        "residual_count": "0",
        "score_count": "0",
        "row_sha256": row_hash({k:v for k,v in summary[0].items() if k != "row_sha256"}),
    }]


def test_elementary_118_counterfactuals_fail_closed():
    rows = read_csv("elementary_matter_118_counterfactual_audit.csv")
    assert len(rows) == 5
    by_id = {r["counterfactual_id"]: r for r in rows}
    assert by_id["cf_target_value_inserted_into_elementary_packet"]["observed_result"] == "failed"
    assert by_id["cf_si_frequency_promoted_to_native_premise"]["observed_result"] == "failed"
    assert by_id["cf_metric_report_value_materialized"]["observed_result"] == "failed"
    assert by_id["cf_hyperfine_divisibility_claim_assumed"]["observed_result"] == "failed"
    assert by_id["cf_unchanged_control"]["observed_result"] == "passed"
    for row in rows:
        assert row["audit_status"] == "passed"
        assert row["row_sha256"] == row_hash(row)


def test_generator_is_idempotent_for_elementary_118_atlas():
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ELEM.glob("elementary_matter_118_*") if p.is_file()}
    subprocess.run([sys.executable, "manual-2/scripts/build_elementary_matter_118_transition_atlas.py"], cwd=ROOT, check=True)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ELEM.glob("elementary_matter_118_*") if p.is_file()}
    assert after == before


def test_manual2_includes_elementary_118_section():
    main = (ROOT / "manual-2" / "main.tex").read_text(encoding="utf-8")
    section = (ROOT / "manual-2" / "sections" / "04_elementary_matter_118_transition_atlas.tex").read_text(encoding="utf-8")
    assert "sections/04_elementary_matter_118_transition_atlas.tex" in main
    assert "Elementary Matter 118 Transition Atlas Materialization" in section
    assert "hyperfine" in section.lower()
