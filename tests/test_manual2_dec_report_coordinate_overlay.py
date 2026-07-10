import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEC = ROOT / "manual-2" / "data" / "dec"

def rows(name):
    with (DEC / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_required_conversion_operators_are_declared():
    operators = {r["operator_id"]: r for r in rows("dec_conversion_operator_registry.csv")}
    for op in ["OP_TAU_TO_PI_DISPLAY", "OP_RECIPROCAL_RATIO", "OP_TICK_COUNT_TO_DECLARED_SECOND_CARD", "OP_SPARC_2D_PROJECTION_READOUT"]:
        assert op in operators
    assert operators["OP_SPARC_2D_PROJECTION_READOUT"]["operator_codomain"] == "observable_2d_fixture"
    assert operators["OP_SPARC_2D_PROJECTION_READOUT"]["target_join_opens"] == "no"

def test_overlay_rows_keep_closed_lanes_and_do_not_mutate_native_rows():
    for row in rows("dec_report_coordinate_overlay.csv"):
        assert row["target_join_status"] == "closed"
        assert row["si_report_status"] == "closed"
        assert row["metric_report_status"] == "closed"
        assert row["residual_status"] == "not_computed"
        assert row["score_status"] == "no_score"
        assert row["native_row_mutation_status"] == "not_mutated"

def test_error_budget_policy_forbids_conflations():
    statements = {r["statement"] for r in rows("dec_error_budget_policy.csv")}
    assert "conversion_error != empirical_residual" in statements
    assert "projection_error != target_agreement_score" in statements
    assert "rounding_error != metric_report_value" in statements
    assert "display_decimal != native_exact_value" in statements

def test_named_examples_are_represented_in_overlay():
    examples = {r["worked_example_id"]: r for r in rows("dec_report_coordinate_overlay.csv")}
    assert examples["circle_tau_pi_display"]["declared_report_coordinate"] == "pi_display_coordinate"
    assert examples["hydrogen_balmer_frequency_ratio_display"]["operator_id"] == "OP_RECIPROCAL_RATIO"
    assert examples["circle_tau_pi_display"]["operator_parameter_num"] == "1"
    assert examples["circle_tau_pi_display"]["operator_parameter_den"] == "2"
    assert examples["circle_tau_pi_display"]["enclosure_subject"] == "pi_display_coordinate"
    assert examples["hydrogen_balmer_frequency_ratio_display"]["native_value_expression"] == "1512:1120:1000:945"
    assert examples["hydrogen_balmer_frequency_ratio_display"]["report_value_expression"] == "500:675:756:800"
    assert examples["cs133_second_tick_card"]["reference_card_value"] == "9192631770"
    assert examples["cs133_second_tick_card"]["reference_card_status"] == "available"
    assert examples["cs133_second_tick_card"]["report_activation_status"] == "closed"
    assert examples["sparc_2d_fixture_projection"]["source_snapshot_status"] == "pending_or_declared"
