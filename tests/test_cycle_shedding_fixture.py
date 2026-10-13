"""Check the retained run and reject a corrupted post-clipping record."""
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cycle_fixture", ROOT / "manual/scripts/generate_cycle_shedding_fixture.py"
)
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)


def test_retained_cycle_run_matches_its_clipping_model_and_summary():
    rows, metrics = FIXTURE.load_fixture(FIXTURE.CSV_PATH, FIXTURE.SUMMARY_PATH)
    assert len(rows) == 90
    assert all(row["padar_burden"] <= row["compatibility"] for row in rows)
    assert all(row["state"] == "open" for row in rows)
    assert metrics["summary_values"]["Maximum sheddic excess"] == "0.061"


def test_cycle_run_rejects_corrupted_post_clipping_burden(tmp_path):
    with FIXTURE.CSV_PATH.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    rows[31]["padar_burden"] = str(float(rows[31]["compatibility"]) + 0.1)
    corrupted = tmp_path / "corrupted.csv"
    with corrupted.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="tick 31"):
        FIXTURE.load_fixture(corrupted, FIXTURE.SUMMARY_PATH)
