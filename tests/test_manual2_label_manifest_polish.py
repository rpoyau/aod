import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROT = ROOT / "manual-2" / "data" / "protein"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_package_version_and_manual2_content_baseline_are_distinct():
    version = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    assert "Canonical version:" in version
    roadmap = (ROOT / "MANUAL_II_ROADMAP.md").read_text(encoding="utf-8")
    assert "Package release: **v40.03r12" in roadmap
    assert "active Manual-II lane = Hydrogen Transition and SADAR-Lock Atlas" in roadmap
    assert "carried source baseline" in roadmap
    assert "lambda_fold     = deferred_not_attached" in roadmap


def test_target_normalization_labels_are_carried_forward_from_v4002r04():
    target_files = [
        "protein_sequence_target_packets.csv",
        "pdb_mmcif_structure_targets.csv",
        "alphafold_structure_targets.csv",
        "protein_contact_map_targets.csv",
        "protein_distance_matrix_targets.csv",
        "protein_structure_target_limitations.csv",
    ]
    for name in target_files:
        text = (PROT / name).read_text(encoding="utf-8")
        assert "v40.02r05_target_normalization_gate" not in text
        assert "v40.02r04_target_normalization_carried_forward" in text


def test_lane_manifests_preserve_origin_and_package_scope():
    folding = json.loads((PROT / "protein_folding_target_manifest.json").read_text(encoding="utf-8"))
    target = json.loads((PROT / "protein_target_manifest.json").read_text(encoding="utf-8"))
    score = json.loads((PROT / "protein_contact_score_manifest.json").read_text(encoding="utf-8"))
    assert folding["version_scope"] == "v40.02r04"
    assert target["version_scope"] == "v40.02r16"
    assert score["version_scope"] == "v40.02r06"
    assert score["package_version_scope"] == "v40.02r16"
    assert "label_polish" in score


def test_label_polish_does_not_change_contact_score_rows():
    rows = read_csv(PROT / "protein_contact_score.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["score_version"] == "v40.02r06"
    assert row["predicted_pairs"] == row["target_pairs"] == row["evaluation_pairs"] == "1-3"
    assert (row["tp"], row["fp"], row["fn"], row["tn"]) == ("1", "0", "0", "0")


def test_lambdas_remain_deferred_in_coordinate_payload_gate():
    rows = read_csv(PROT / "protein_value_map_quarantine.csv")
    assert all(r["status"] == "deferred_not_attached" for r in rows)
    assert all(r["active_value_map"] == "false" for r in rows)
    assert all("v40.02r11" in r["release_status"] for r in rows)
