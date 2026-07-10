from pathlib import Path
import csv, json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual-2" / "data" / "rest_cycle"


def read_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_rest_cycle_manifest_exists_and_no_target_join():
    manifest = json.loads((DATA / "native_rest_cycle_relational_atlas_manifest.json").read_text(encoding="utf-8"))
    assert manifest["target_value_read_status"] == "not_read"
    assert manifest["residual_status"] == "not_computed"
    assert manifest["score_status"] == "no_score"
    assert "temporal_flow_is_native_SADAR_current" in manifest["core_rule"]


def test_rest_cycle_type_separation():
    rows = {r["object_id"]: r for r in read_csv("rest_cycle_type_card.csv")}
    for key in ["bip", "trace_count", "cycle", "RD", "RCD", "duon_current", "duonic_pressure", "SADAR_flow", "temporal_flow", "temporal_measurement", "metric_report"]:
        assert key in rows
    assert "temporal_measurement" in rows["bip"]["not_equal_to"]
    assert rows["temporal_measurement"]["object_class"] == "relational_lock"
    assert rows["metric_report"]["object_class"] == "downstream_projection"


def test_matter_octave_atlas_rows_target_blind():
    rows = read_csv("matter_octave_rest_cycle_atlas.csv")
    assert {r["matter_octave"] for r in rows} == {"Elementary Matter 118", "Molecular Matter", "Biomolecular Matter"}
    assert all("no_target_join" in r["current_state"] for r in rows)


def test_relational_measurement_packets_are_reserved_not_computed():
    rows = read_csv("relational_measurement_packets.csv")
    assert all(r["primitive_phase_lock_status"] == "not_materialized" for r in rows)
    assert all(r["metric_report_status"] == "closed" for r in rows)
    assert all(r["target_value_read_status"] == "not_read" for r in rows)
