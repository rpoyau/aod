from __future__ import annotations

import csv
import json
import subprocess
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "manual-2" / "data" / "hydrogen_transition"
SCRIPT = ROOT / "manual-2" / "scripts" / "materialize_hydrogen_transition_native_packets_r10.py"


def rows(name: str):
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_generator_runs_and_manifest_is_target_blind():
    subprocess.run(["python3", str(SCRIPT)], check=True, cwd=ROOT)
    manifest = json.loads((DATA / "hydrogen_transition_native_materialization_manifest.json").read_text())
    assert manifest["native_materialization_status"] == "passed"
    assert manifest["target_value_read_status"] == "not_read"
    assert manifest["observable_join_state"] == "closed"
    assert manifest["residual_status"] == "not_computed"
    assert manifest["score_status"] == "no_score"


def test_rd_rcd_packets_are_exact_single_path_rows():
    rd_rows = rows("hydrogen_transition_rd_rcd_packets.csv")
    assert [r["packet_kind"] for r in rd_rows] == ["RD_path_distribution", "RCD_single_path_coupling"]
    for row in rd_rows:
        assert row["target_value_read_status"] == "not_read"
        assert row["observable_join_state"] == "closed"
        assert row["empirical_score_status"] == "not_computed"
        assert Fraction(int(row["path_probability_num"]), int(row["path_probability_den"])) == Fraction(1, 1)
        assert row["realized_bip_count_semantics"] == "execution_structure_not_temporal_magnitude"
        assert Fraction(int(row["rd_value_num"]), int(row["rd_value_den"])) == Fraction(2, 1)


def test_duonic_pressure_is_not_cadence():
    [row] = rows("hydrogen_transition_duonic_pressure_packets.csv")
    assert row["pressure_semantics"] == "local_coupling_load_not_cadence"
    assert Fraction(int(row["rhoD_num"]), int(row["rhoD_den"])) == Fraction(2, 1)
    assert Fraction(int(row["capacity_factor_num"]), int(row["capacity_factor_den"])) == Fraction(1, 1)
    assert Fraction(int(row["duonic_pressure_num"]), int(row["duonic_pressure_den"])) == Fraction(2, 1)
    assert row["target_value_read_status"] == "not_read"


def test_sadar_flow_and_phase_lock_statuses():
    [flow] = rows("hydrogen_transition_sadar_flow_packets.csv")
    assert flow["flow_semantics"] == "native_SADAR_flow_not_metric_time"
    assert flow["native_temporal_flow_status"] == "materialized_as_single_subject_flow_packet"
    assert flow["metric_time_report_status"] == "not_materialized"
    assert Fraction(int(flow["sadar_flux_num"]), int(flow["sadar_flux_den"])) == Fraction(2, 1)

    [lock] = rows("hydrogen_transition_phase_lock_packets.csv")
    assert lock["primitive_lock_status"] == "materialized_native_self_reference_lock_for_H1_packet"
    assert lock["temporal_measurement_status"] == "relational_lock_declared_without_metric_unit"
    assert lock["metrological_reference_status"] == "not_declared"
    assert lock["metric_time_report_status"] == "not_materialized"
    assert Fraction(int(lock["phase_residual_num"]), int(lock["phase_residual_den"])) == Fraction(0, 1)


def test_counterfactuals_executed_and_fail_closed():
    audit = rows("hydrogen_transition_native_materialization_counterfactual_audit.csv")
    assert len(audit) == 5
    failed = [r for r in audit if r["expected_result"] == "failed"]
    assert len(failed) == 4
    for row in failed:
        assert row["observed_result"] == "failed"
        assert row["audit_status"] == "passed"
    controls = [r for r in audit if r["expected_result"] == "passed"]
    assert len(controls) == 1
    assert controls[0]["observed_result"] == "passed"
