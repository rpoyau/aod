from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "manual-2" / "data" / "foundation"


def rows(name: str):
    with (FOUNDATION / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_tick_oriented_doctrine_rows_are_positive_and_ordered():
    data = rows("tick_oriented_temporal_foundation_doctrine.csv")
    assert [r["doctrine_id"] for r in data][:4] == [
        "null_cut_running",
        "monon_beat",
        "duon_current_cadence",
        "boundary_window",
    ]
    assert any("dynamic relational distinction-current" in r["positive_statement"] for r in data)
    assert any("Measured time is relational tick count" in r["positive_statement"] for r in data)


def test_foundation_release_points_are_staged_before_matter_expansion():
    data = rows("foundation_release_milestone_plan.csv")
    assert data[0]["release_point"] == "v40.04r01"
    assert "Tick-Oriented Temporal" in data[0]["title"]
    assert data[1]["release_point"] == "v40.04r02"
    assert "Hypersphere" in data[1]["title"]
    assert data[2]["release_point"] == "v40.04r03"
    assert "Elementary Matter 118" in data[2]["title"]


def test_hydrogen_tick_ratio_is_native_before_inverted_report():
    data = {r["row_id"]: r for r in rows("hydrogen_balmer_tick_ratio_plan.csv")}
    assert data["hydrogen_balmer_native_tick_interval_ratio"]["native_ratio"] == "1512:1120:1000:945"
    assert data["hydrogen_balmer_inverted_frequency_report"]["report_ratio"] == "500:675:756:800"
    assert data["hydrogen_balmer_inverted_frequency_report"]["native_status"] == "not_native_premise"


def test_cs_reference_tick_card_is_report_card_plan():
    data = rows("cs_reference_tick_card_plan.csv")
    assert data[0]["reference_tick_statement"] == "1 s = 9192631770 Cs reference ticks"
    assert data[0]["si_second_report_status"] == "metrological_report_card"
    assert data[0]["frequency_report_status"] == "downstream_report"


def test_manifest_hashes_all_foundation_plan_files():
    manifest = json.loads((FOUNDATION / "tick_oriented_temporal_foundation_release_plan_manifest.json").read_text(encoding="utf-8"))
    expected = {
        "manual-2/data/foundation/tick_oriented_temporal_foundation_doctrine.csv",
        "manual-2/data/foundation/foundation_release_milestone_plan.csv",
        "manual-2/data/foundation/hydrogen_balmer_tick_ratio_plan.csv",
        "manual-2/data/foundation/cs_reference_tick_card_plan.csv",
    }
    assert set(manifest["files"]) == expected
    assert manifest["next_release_points"][0].startswith("v40.04r01")
