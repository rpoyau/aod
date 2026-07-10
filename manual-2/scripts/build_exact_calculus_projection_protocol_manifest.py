#!/usr/bin/env python3
"""Build the Manual II exact-calculus/projection protocol manifest offline."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTEIN = ROOT / "manual-2" / "data" / "protein"
OUT = PROTEIN / "aod_exact_calculus_projection_protocol_manifest.json"
FILES = {
    "protocol": PROTEIN / "aod_exact_calculus_projection_protocol.csv",
    "uncertainty_field_registry": PROTEIN / "aod_observation_uncertainty_field_registry.csv",
    "typed_residual_registry": PROTEIN / "aod_typed_residual_component_registry.csv",
    "double_blind_state": PROTEIN / "aod_double_blind_comparison_protocol_state.csv",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build() -> dict[str, object]:
    protocol = rows(FILES["protocol"])
    state_rows = rows(FILES["double_blind_state"])
    if [int(row["stage_order"]) for row in protocol] != list(range(1, 10)):
        raise ValueError("protocol stage_order must be the exact sequence 1..9")
    if len(state_rows) != 1:
        raise ValueError("double-blind protocol state must contain exactly one row")
    state = state_rows[0]
    if state["selected_accession"] != "none":
        raise ValueError("appendix protocol must not select an accession")
    if state["target_value_read_status"] != "not_read":
        raise ValueError("appendix protocol must not read target values")
    if state["comparison_join_state"] != "closed":
        raise ValueError("appendix protocol must preserve the closed comparison gate")
    if state.get("comparison_protocol_name") != "hash_locked_branch_isolated_comparison":
        raise ValueError("canonical comparison protocol name is not frozen")
    if state.get("octave_refinement_contract_state") != "declared_not_instantiated":
        raise ValueError("octave refinement contract must remain declared but uninstantiated")
    if state.get("projection_information_loss_state") != "intentional_noninjectivity_recorded_outside_E_proj":
        raise ValueError("projection information-loss policy is not frozen")

    return {
        "appendix_role": "protocol_only_no_empirical_gate_activation",
        "calculus_exactness": "declared_fractal_coordinate_octave_boundary_temporal_order_window_and_policy",
        "temporal_exactness_rule": "ordered_DEC_trace_and_declared_window_are_part_of_native_scope",
        "octave_refinement_rule": "Delta_oct_records_lawful_change_and_E_oct_requires_explicit_failure_condition",
        "metric_projection_exactness": "declared_integer_rational_map_may_be_noninjective",
        "projection_information_loss_rule": "declared_noninjectivity_is_metadata_not_E_proj",
        "observation_uncertainty_rule": "freeze_from_observation_lineage_before_prediction_join",
        "comparison_rule": "hash_locked_branch_isolated_unseal_then_typed_residual",
        "current_state": state,
        "files": {key: str(path.relative_to(ROOT)) for key, path in FILES.items()},
        "sha256": {key: sha256(path) for key, path in FILES.items()},
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
