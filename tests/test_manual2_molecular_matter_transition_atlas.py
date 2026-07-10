import csv, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual-2" / "data" / "molecular"

def rows(name):
    with (DATA/name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_molecular_matter_atlas_counts_and_closed_lanes():
    occ = rows("molecular_matter_transition_occurrence_cards.csv")
    transitions = rows("molecular_matter_transition_packets.csv")
    flows = rows("molecular_matter_sadar_flow_declarations.csv")
    summary = rows("molecular_matter_transition_atlas_summary.csv")[0]
    assert len(occ) == 23
    assert len(transitions) == 23
    assert len(flows) == 23
    assert summary["target_join_count"] == "0"
    assert summary["si_report_count"] == "0"
    assert summary["metric_report_count"] == "0"
    assert summary["residual_count"] == "0"
    assert summary["score_count"] == "0"
    assert {"mol_component_water", "mol_component_methane", "mol_chain_chain_GA_peptide_seed", "mol_chain_chain_AU_dinucleotide_seed"} <= {r["occurrence_id"] for r in occ}
    for row in transitions:
        assert row["target_value_read_status"] == "not_read"
        assert row["si_report_status"] == "closed"
        assert row["metric_report_status"] == "closed"
        assert row["subject_reference_phase_lock_status"] == "closed"
        assert row["residual_status"] == "not_computed"
        assert row["score_status"] == "no_score"

def test_molecular_counterfactuals_fail_closed():
    cf = rows("molecular_matter_counterfactual_audit.csv")
    assert len(cf) == 5
    failures = [r for r in cf if r["counterfactual_id"] != "cf_unchanged_control"]
    assert all(r["expected_result"] == "failed" and r["observed_result"] == "failed" and r["audit_status"] == "passed" for r in failures)
    control = next(r for r in cf if r["counterfactual_id"] == "cf_unchanged_control")
    assert control["observed_result"] == "passed"

def test_molecular_manifest_and_generator_idempotent(tmp_path):
    before = {p.name: p.read_bytes() for p in DATA.glob("molecular_matter_*.*")}
    subprocess.run([sys.executable, "manual-2/scripts/build_molecular_matter_transition_atlas.py"], cwd=ROOT, check=True)
    after = {p.name: p.read_bytes() for p in DATA.glob("molecular_matter_*.*")}
    assert before == after
    manifest = json.loads((DATA/"molecular_matter_transition_atlas_manifest.json").read_text())
    assert manifest["milestone"] == "v40.03r25.1"
    assert manifest["occurrence_card_count"] == 23
    assert manifest["target_join_count"] == 0
