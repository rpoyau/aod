#!/usr/bin/env python3
"""Build the Manual-I consequent six-slot compatibility gate.

The gate verifies the carried 3:3:6 and 3:4:6 accessor rows against the
frozen C6 support policy.  Pi_alpha=q^p+q is represented as the disjoint
finite support family F_{p,q}=D_q^p sqcup S_q: q^p direction words and q
retained support-shell members.  The uniform counting measure on that family
is exact but is not a local Q4 AFC/D.E.C. kernel.

This revision binds every consumed packet to one scoped occurrence, verifies
all attached row hashes before semantic access, recomputes enumeration
completeness and exact mass, recomputes the inverse solution set on the frozen
domain, enforces exact global packet-set closure and canonical row identity,
and makes counterfactual audit success part of the fail-closed gate.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual" / "data" / "c6"
SOURCE_TEX = ROOT / "appendices" / "J_ao_field_fractal_properties.tex"
SUPPORT_POLICY = DATA / "c6_recurrence_support_policy.csv"
ENUMERATION_LEDGER = DATA / "consequent_six_slot_support_family_enumeration.csv"
VERSION = "v40.03r06.3.1"
GATE_ID = "aod_consequent_six_slot_form_compatibility_gate_v5"
POLICY_VALIDATION_MODE = "hash_verified_semantically_consumed_and_release_pinned"

FORMS = (
    {"form_id": "form_3_3_6", "route_form": "3:3:6", "p": 3, "q": 3, "name": "Tritriohexon"},
    {"form_id": "form_3_4_6", "route_form": "3:4:6", "p": 3, "q": 4, "name": "Tetratriohexon"},
)

FORM_BY_ID = {str(item["form_id"]): item for item in FORMS}
EXPECTED_FORM_IDS = tuple(str(item["form_id"]) for item in FORMS)
EXPECTED_ROUTE_FORMS = tuple(str(item["route_form"]) for item in FORMS)

OLD_RETYPE_FILES = (
    "consequent_six_slot_kernel_contract.csv",
    "consequent_six_slot_dec_execution_ledger.csv",
    "consequent_six_slot_stage_mass_audit.csv",
    "consequent_six_slot_read_only_trace.csv",
)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def packet_digest(packet: object) -> str:
    return sha_bytes(canonical_json(packet))


def attach(row: Mapping[str, object], field: str) -> dict[str, str]:
    out = {k: str(v) for k, v in row.items()}
    out[field] = sha_bytes(canonical_json({k: out[k] for k in sorted(out) if k != field}))
    return out


def verify_attached_row(row: Mapping[str, str], field: str) -> None:
    expected = attach({k: v for k, v in row.items() if k != field}, field)[field]
    if row.get(field) != expected:
        raise ValueError(f"row hash mismatch: {field}")


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: str(row.get(key, "")) for key in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_one(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if len(rows) != 1:
        raise ValueError(f"expected one row in {path}")
    return rows[0]


def reduced(numerator: int, denominator: int) -> tuple[int, int]:
    if denominator <= 0:
        raise ValueError("positive denominator required")
    divisor = math.gcd(numerator, denominator)
    return numerator // divisor, denominator // divisor


def fraction_text(numerator: int, denominator: int) -> str:
    num, den = reduced(numerator, denominator)
    return str(num) if den == 1 else f"{num}/{den}"


def safe_int(value: object, label: str, reasons: list[str]) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        reasons.append(f"malformed_integer_{label}")
        return None


def safe_fraction(num: object, den: object, label: str, reasons: list[str]) -> Fraction | None:
    numerator = safe_int(num, f"{label}_num", reasons)
    denominator = safe_int(den, f"{label}_den", reasons)
    if numerator is None or denominator is None:
        return None
    if denominator <= 0:
        reasons.append(f"nonpositive_denominator_{label}")
        return None
    return Fraction(numerator, denominator)


def load_support_policy() -> dict[str, str]:
    policy = read_one(SUPPORT_POLICY)
    verify_attached_row(policy, "support_policy_sha256")
    required = {
        "primitive_support_id": "00o8_C6_1_2_6",
        "fractal_octave_coordinate": "00_(8)",
        "declared_scope_L": "6",
        "outer_enclosure_id": "C6",
        "inverse_solver_p_min": "1",
        "inverse_solver_q_min": "2",
        "inverse_solver_q_max": "4",
        "inverse_solver_domain_basis": "Q4_directional_support",
        "local_Q4_edge_slots": "4",
    }
    for key, expected in required.items():
        if policy.get(key) != expected:
            raise ValueError(f"support-policy semantic mismatch: {key}={policy.get(key)!r}, expected {expected!r}")
    return policy


def parse_main_source_rows() -> dict[str, dict[str, str]]:
    text = SOURCE_TEX.read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    for form in FORMS:
        route = str(form["route_form"])
        needle = rf"\mathfrak f_{{{route}}}"
        line = next((item for item in text.splitlines() if needle in item), None)
        if line is None:
            raise ValueError(f"source row missing: {route}")
        cells = [cell.strip() for cell in line.rstrip(" \\").split("&")]
        if len(cells) != 11:
            raise ValueError((route, len(cells), cells))
        values: list[int] = []
        for index in (3, 5, 6, 7, 8, 9, 10):
            match = re.search(r"-?\d+", cells[index])
            if not match:
                raise ValueError((route, index, cells[index]))
            values.append(int(match.group()))
        pi, rd, outer_length, rho, pressure, burden, surplus = values
        result[route] = {
            "source_file": SOURCE_TEX.relative_to(ROOT).as_posix(),
            "source_file_sha256": sha_file(SOURCE_TEX),
            "source_table_label": "tab:ao-field-fractal-properties",
            "source_row_text_sha256": sha_bytes(line.encode("utf-8")),
            "Pi_alpha": str(pi),
            "H_mu": "1",
            "RD_AO": str(rd),
            "L": str(outer_length),
            "rhoD_omega": str(rho),
            "PD": str(pressure),
            "QD": str(burden),
            "X_shedding": str(surplus),
        }
    return result


def branch_solutions(pi_value: int, *, p_min: int, q_min: int, q_max: int) -> list[tuple[int, int]]:
    """Solve q**p+q=Pi on the frozen finite directional-support domain."""
    if pi_value <= 0 or p_min < 1 or q_min < 2 or q_max < q_min:
        raise ValueError("invalid inverse-solver domain")
    solutions: list[tuple[int, int]] = []
    for q_value in range(q_min, q_max + 1):
        p_value = p_min
        while q_value**p_value + q_value <= pi_value:
            if q_value**p_value + q_value == pi_value:
                solutions.append((p_value, q_value))
            p_value += 1
    return solutions


def build_rule_contract(policy: Mapping[str, str]) -> list[dict[str, str]]:
    rules = [
        (0, "branch_support", "Pi_alpha=q^p+q", "positive_integer", "finite support-family cardinality"),
        (1, "support_decomposition", "F_pq=D_q^p disjoint_union S_q", "finite_disjoint_union", "q^p direction words plus q retained support-shell members"),
        (2, "reflection_duration", "RD_AO=2*Pi_alpha+1", "positive_integer", "single-hinge accessor"),
        (3, "local_coupling", "C3=p+q", "positive_integer", "declared occurrence p,q"),
        (4, "window_participation", "rhoD_omega=min(RD_AO,L)", "nonnegative_integer", "declared window L"),
        (5, "duonic_pressure", "PD=C3*rhoD_omega", "nonnegative_integer", "exact accessor"),
        (6, "pending_burden", "QD=C3*max(0,RD_AO-L)", "nonnegative_integer", "exact accessor"),
        (7, "capacity_fill", "capacity_fill_residual=PD-C3*L", "integer", "not recurrence closure"),
        (8, "sheddic_surplus", "X_shedding=max(0,capacity_fill_residual)", "nonnegative_integer", "scalar surplus only"),
        (9, "compatibility", "all scoped packet identities, cardinalities, hashes, accessors, and inverse rows agree", "boolean", "support/enclosure only"),
    ]
    return [
        attach(
            {
                "rule_order": order,
                "rule_id": rule_id,
                "exact_rule": expression,
                "codomain": codomain,
                "role": role,
                "support_policy_id": policy["support_policy_id"],
                "support_policy_sha256": policy["support_policy_sha256"],
                "support_policy_validation_mode": POLICY_VALIDATION_MODE,
                "local_DEC_status": "separate_not_materialized",
                "temporal_status": "does_not_define_time_or_recurrence",
                "target_value_input_status": "absent",
            },
            "rule_row_sha256",
        )
        for order, rule_id, expression, codomain, role in rules
    ]


def build_occurrences(source_rows: Mapping[str, Mapping[str, str]], policy: Mapping[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for order, specification in enumerate(FORMS):
        source = source_rows[str(specification["route_form"])]
        rows.append(
            attach(
                {
                    "occurrence_order": order,
                    "occurrence_id": f"aod_{specification['form_id']}_00o8",
                    "form_id": specification["form_id"],
                    "form_name": specification["name"],
                    "route_form": specification["route_form"],
                    "fractal_octave_coordinate": policy["fractal_octave_coordinate"],
                    "declared_p": specification["p"],
                    "declared_q": specification["q"],
                    "declared_L": policy["declared_scope_L"],
                    "outer_enclosure_id": policy["outer_enclosure_id"],
                    "primitive_support_id": policy["primitive_support_id"],
                    "support_policy_id": policy["support_policy_id"],
                    "support_policy_sha256": policy["support_policy_sha256"],
                    "source_file": source["source_file"],
                    "source_file_sha256": source["source_file_sha256"],
                    "source_row_text_sha256": source["source_row_text_sha256"],
                    "form_identity_source": "declared_scoped_occurrence_not_inferred_from_support_family",
                    "local_DEC_status": "not_materialized",
                    "target_value_input_status": "absent",
                },
                "occurrence_row_sha256",
            )
        )
    return rows


def expected_ids(form_id: str) -> tuple[str, str]:
    return f"{form_id}_support_family", f"{form_id}_uniform_support_family_measure"


def expected_occurrence_id(form_id: str) -> str:
    return f"aod_{form_id}_00o8"


def expected_route_form(p_value: int, q_value: int, outer_length: int) -> str:
    return f"{p_value}:{q_value}:{outer_length}"


def form_global_start(form_id: str) -> int:
    start = 0
    for specification in FORMS:
        current_id = str(specification["form_id"])
        if current_id == form_id:
            return start
        start += int(specification["q"]) ** int(specification["p"]) + int(specification["q"])
    raise KeyError(form_id)


def canonical_member_rows(form_id: str, outer_length: int) -> list[dict[str, str]]:
    """Return the canonical identity/order/type fields for one support family."""
    specification = FORM_BY_ID[form_id]
    p_value = int(specification["p"])
    q_value = int(specification["q"])
    route_form = expected_route_form(p_value, q_value, outer_length)
    family_id, measure_id = expected_ids(form_id)
    rows: list[dict[str, str]] = []
    global_index = form_global_start(form_id)
    family_order = 0
    for word_tuple in itertools.product(range(q_value), repeat=p_value):
        word = ".".join(str(value) for value in word_tuple)
        rows.append(
            {
                "enumeration_row_index": str(global_index),
                "support_member_order": str(family_order),
                "support_family_id": family_id,
                "support_measure_id": measure_id,
                "form_id": form_id,
                "route_form": route_form,
                "member_class": "walk_history",
                "member_class_order": str(family_order),
                "support_member_id": f"{form_id}_walk_{word.replace('.', '_')}",
                "history_word": word,
                "history_length": str(p_value),
                "direction_alphabet_size": str(q_value),
                "support_shell_member_index": "",
                "analysis_weight_num": "1",
                "analysis_weight_den": "1",
                "local_Q4_edge_status": "not_a_local_hamming1_edge",
                "row_time_semantics": "non_temporal_support_family_enumeration",
                "target_value_input_status": "absent",
            }
        )
        global_index += 1
        family_order += 1
    for shell_index in range(q_value):
        rows.append(
            {
                "enumeration_row_index": str(global_index),
                "support_member_order": str(family_order),
                "support_family_id": family_id,
                "support_measure_id": measure_id,
                "form_id": form_id,
                "route_form": route_form,
                "member_class": "retained_support_shell",
                "member_class_order": str(shell_index),
                "support_member_id": f"{form_id}_support_shell_{shell_index}",
                "history_word": "",
                "history_length": "0",
                "direction_alphabet_size": str(q_value),
                "support_shell_member_index": str(shell_index),
                "analysis_weight_num": "1",
                "analysis_weight_den": "1",
                "local_Q4_edge_status": "retained_support_shell_member_not_local_successor_edge",
                "row_time_semantics": "non_temporal_support_family_enumeration",
                "target_value_input_status": "absent",
            }
        )
        global_index += 1
        family_order += 1
    return rows


def build_support_family_registry() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        form_id = str(specification["form_id"])
        family_id, measure_id = expected_ids(form_id)
        p_value = int(specification["p"])
        q_value = int(specification["q"])
        walk_count = q_value**p_value
        shell_count = q_value
        total = walk_count + shell_count
        classes = (
            ("walk_history", walk_count, "D_q^p: all length-p words over the q-direction alphabet"),
            ("retained_support_shell", shell_count, "S_q: q declared disjoint retained support-shell members; not local edges"),
        )
        for class_order, (member_class, count, definition) in enumerate(classes):
            rows.append(
                attach(
                    {
                        "support_family_id": family_id,
                        "support_measure_id": measure_id,
                        "form_id": form_id,
                        "route_form": specification["route_form"],
                        "support_family_definition": "F_pq=D_q^p_disjoint_union_S_q",
                        "class_order": class_order,
                        "member_class": member_class,
                        "member_count": count,
                        "class_definition": definition,
                        "walk_word_length": p_value if member_class == "walk_history" else 0,
                        "direction_alphabet_size": q_value,
                        "total_support_family_count": total,
                        "Pi_alpha": total,
                        "local_DEC_edge_status": "not_a_local_Q4_edge_inventory",
                        "row_time_semantics": "non_temporal_support_family_card",
                    },
                    "support_family_registry_row_sha256",
                )
            )
    return rows


def build_support_family_measure_contract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        form_id = str(specification["form_id"])
        family_id, measure_id = expected_ids(form_id)
        p_value = int(specification["p"])
        q_value = int(specification["q"])
        walk_count = q_value**p_value
        shell_count = q_value
        total = walk_count + shell_count
        rows.append(
            attach(
                {
                    "support_measure_id": measure_id,
                    "support_family_id": family_id,
                    "form_id": form_id,
                    "route_form": specification["route_form"],
                    "support_family_definition": "F_pq=D_q^p_disjoint_union_S_q",
                    "analysis_domain": "finite_support_family",
                    "walk_history_count": walk_count,
                    "retained_support_shell_count": shell_count,
                    "support_member_count": total,
                    "member_weight_num": 1,
                    "member_weight_den": 1,
                    "normalizer_num": total,
                    "normalizer_den": 1,
                    "member_measure_num": 1,
                    "member_measure_den": total,
                    "member_measure_exact": fraction_text(1, total),
                    "measure_sum_num": 1,
                    "measure_sum_den": 1,
                    "measure_semantics": "uniform_support_family_analysis_measure",
                    "uniform_weighting_status": "declared_definitional_not_physical_probability_law",
                    "relation_to_DEC_kernel": "distinct_not_a_local_Q4_kernel",
                    "execution_mode": "support_family_enumeration",
                    "row_time_semantics": "non_temporal_analysis_measure",
                    "target_value_input_status": "absent",
                },
                "support_measure_sha256",
            )
        )
    return rows


def build_support_family_enumeration(measures: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    by_form = {row["form_id"]: row for row in measures}
    rows: list[dict[str, str]] = []
    global_index = 0
    for specification in FORMS:
        form_id = str(specification["form_id"])
        p_value = int(specification["p"])
        q_value = int(specification["q"])
        measure = by_form[form_id]
        family_order = 0
        for word_tuple in itertools.product(range(q_value), repeat=p_value):
            word = ".".join(str(value) for value in word_tuple)
            rows.append(
                attach(
                    {
                        "enumeration_row_index": global_index,
                        "support_member_order": family_order,
                        "support_family_id": measure["support_family_id"],
                        "support_measure_id": measure["support_measure_id"],
                        "form_id": form_id,
                        "route_form": specification["route_form"],
                        "member_class": "walk_history",
                        "member_class_order": family_order,
                        "support_member_id": f"{form_id}_walk_{word.replace('.', '_')}",
                        "history_word": word,
                        "history_length": p_value,
                        "direction_alphabet_size": q_value,
                        "support_shell_member_index": "",
                        "analysis_weight_num": 1,
                        "analysis_weight_den": 1,
                        "measure_num": 1,
                        "measure_den": measure["support_member_count"],
                        "measure_exact": measure["member_measure_exact"],
                        "local_Q4_edge_status": "not_a_local_hamming1_edge",
                        "row_time_semantics": "non_temporal_support_family_enumeration",
                        "target_value_input_status": "absent",
                    },
                    "support_member_row_sha256",
                )
            )
            global_index += 1
            family_order += 1
        for shell_index in range(q_value):
            rows.append(
                attach(
                    {
                        "enumeration_row_index": global_index,
                        "support_member_order": family_order,
                        "support_family_id": measure["support_family_id"],
                        "support_measure_id": measure["support_measure_id"],
                        "form_id": form_id,
                        "route_form": specification["route_form"],
                        "member_class": "retained_support_shell",
                        "member_class_order": shell_index,
                        "support_member_id": f"{form_id}_support_shell_{shell_index}",
                        "history_word": "",
                        "history_length": 0,
                        "direction_alphabet_size": q_value,
                        "support_shell_member_index": shell_index,
                        "analysis_weight_num": 1,
                        "analysis_weight_den": 1,
                        "measure_num": 1,
                        "measure_den": measure["support_member_count"],
                        "measure_exact": measure["member_measure_exact"],
                        "local_Q4_edge_status": "retained_support_shell_member_not_local_successor_edge",
                        "row_time_semantics": "non_temporal_support_family_enumeration",
                        "target_value_input_status": "absent",
                    },
                    "support_member_row_sha256",
                )
            )
            global_index += 1
            family_order += 1
    return rows


def build_support_family_mass_audit(enumeration: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        form_id = str(specification["form_id"])
        family_id, measure_id = expected_ids(form_id)
        group = [row for row in enumeration if row["form_id"] == form_id]
        total = sum((Fraction(int(row["measure_num"]), int(row["measure_den"])) for row in group), Fraction(0, 1))
        residual = total - 1
        rows.append(
            attach(
                {
                    "support_family_id": family_id,
                    "support_measure_id": measure_id,
                    "form_id": form_id,
                    "route_form": specification["route_form"],
                    "support_member_count": len(group),
                    "analysis_mass_expected_num": 1,
                    "analysis_mass_expected_den": 1,
                    "analysis_mass_sum_num": total.numerator,
                    "analysis_mass_sum_den": total.denominator,
                    "analysis_mass_residual_num": residual.numerator,
                    "analysis_mass_residual_den": residual.denominator,
                    "support_measure_conservation_status": "passed" if residual == 0 else "failed",
                    "mass_semantics": "support_family_analysis_mass_not_DEC_branch_mass",
                    "temporal_status": "not_time_measurement",
                },
                "support_mass_audit_row_sha256",
            )
        )
    return rows


def build_support_family_read_only_packet(
    enumeration_path: Path,
    enumeration: Sequence[Mapping[str, str]],
    mass_audit: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    file_hash = sha_file(enumeration_path)
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        form_id = str(specification["form_id"])
        family_id, measure_id = expected_ids(form_id)
        group = [row for row in enumeration if row["form_id"] == form_id]
        audit = next(row for row in mass_audit if row["form_id"] == form_id)
        rows.append(
            attach(
                {
                    "packet_id": f"{form_id}_read_only_support_family_packet",
                    "support_family_id": family_id,
                    "support_measure_id": measure_id,
                    "form_id": form_id,
                    "route_form": specification["route_form"],
                    "walk_history_count": sum(row["member_class"] == "walk_history" for row in group),
                    "retained_support_shell_count": sum(row["member_class"] == "retained_support_shell" for row in group),
                    "support_member_count": len(group),
                    "support_family_subset_sha256": sha_bytes(canonical_json(group)),
                    "enumeration_ledger_sha256": file_hash,
                    "support_measure_conservation_status": audit["support_measure_conservation_status"],
                    "freeze_status": "frozen_before_compatibility_audit",
                    "event_order_status": "not_applicable_non_temporal_support_family",
                    "local_DEC_trace_status": "not_materialized",
                    "target_value_read_status": "not_read",
                },
                "read_only_packet_row_sha256",
            )
        )
    return rows


def build_local_dec_admission_contract(policy: Mapping[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        rows.append(
            attach(
                {
                    "local_DEC_contract_id": f"{specification['form_id']}_local_Q4_DEC_admission",
                    "form_id": specification["form_id"],
                    "route_form": specification["route_form"],
                    "primitive_support_id": policy["primitive_support_id"],
                    "local_state_space": "Q4",
                    "vertex_domain": "{0,1}^4",
                    "epsilon_Q4_required": "yes",
                    "source_vertex_required": "yes",
                    "target_vertex_required": "yes",
                    "hamming_distance_rule": "exactly_1",
                    "connected_target_source_rule": "target_i_equals_source_i_plus_1",
                    "epsilon_rule": "one_hot_signed_or_TXOR_consistent",
                    "local_admissible_edge_slots_max": policy["local_Q4_edge_slots"],
                    "exact_per_step_kernel_required": "yes",
                    "kernel_probability_domain": "nonnegative_reduced_rational_sum_exactly_1",
                    "connected_event_order_required": "yes",
                    "unique_event_id_required": "yes",
                    "fail_closed_malformed_or_zero_denominator": "yes",
                    "support_family_member_reuse_as_edge_status": "forbidden",
                    "current_local_DEC_status": "not_materialized",
                    "hydrogen_gate_admission_status": "blocked_until_connected_local_Q4_DEC_is_materialized",
                    "target_value_input_status": "absent",
                },
                "local_DEC_contract_row_sha256",
            )
        )
    return rows


def recompute_accessors(p_value: int, q_value: int, outer_length: int) -> dict[str, int]:
    pi_value = q_value**p_value + q_value
    rd_value = 2 * pi_value + 1
    coupling = p_value + q_value
    participation = min(rd_value, outer_length)
    pressure = coupling * participation
    burden = coupling * max(0, rd_value - outer_length)
    capacity = coupling * outer_length
    residual = pressure - capacity
    surplus = max(0, residual)
    return {
        "Pi_alpha": pi_value,
        "H_mu": 1,
        "RD_AO": rd_value,
        "C3": coupling,
        "rhoD_omega": participation,
        "PD": pressure,
        "QD": burden,
        "capacity_fill_num": capacity,
        "capacity_fill_den": 1,
        "capacity_fill_residual": residual,
        "X_shedding": surplus,
    }


def build_accessor_audit(
    source_rows: Mapping[str, Mapping[str, str]],
    occurrences: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    by_form = {row["form_id"]: row for row in occurrences}
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        occurrence = by_form[str(specification["form_id"])]
        p_value = int(occurrence["declared_p"])
        q_value = int(occurrence["declared_q"])
        outer_length = int(occurrence["declared_L"])
        computed = recompute_accessors(p_value, q_value, outer_length)
        source = source_rows[str(specification["route_form"])]
        source_keys = ("Pi_alpha", "H_mu", "RD_AO", "rhoD_omega", "PD", "QD", "X_shedding")
        match = all(str(computed[key]) == source[key] for key in source_keys) and str(outer_length) == source["L"]
        rows.append(
            attach(
                {
                    "form_id": specification["form_id"],
                    "route_form": specification["route_form"],
                    "declared_p": p_value,
                    "declared_q": q_value,
                    "declared_L": outer_length,
                    **computed,
                    "source_Pi_alpha": source["Pi_alpha"],
                    "source_RD_AO": source["RD_AO"],
                    "source_L": source["L"],
                    "source_rhoD_omega": source["rhoD_omega"],
                    "source_PD": source["PD"],
                    "source_QD": source["QD"],
                    "source_X_shedding": source["X_shedding"],
                    "source_accessor_match_status": "passed" if match else "failed",
                    "capacity_residual_semantics": "window_capacity_fill_not_recurrence_closure",
                    "temporal_inference_status": "not_admitted",
                    "target_value_input_status": "absent",
                },
                "accessor_audit_row_sha256",
            )
        )
    return rows


def build_inverse_domain_contract(policy: Mapping[str, str]) -> list[dict[str, str]]:
    row = attach(
        {
            "inverse_solver_domain_id": "consequent_form_Q4_directional_support_domain_v2",
            "support_policy_id": policy["support_policy_id"],
            "support_policy_sha256": policy["support_policy_sha256"],
            "policy_validation_mode": POLICY_VALIDATION_MODE,
            "p_min": policy["inverse_solver_p_min"],
            "q_min": policy["inverse_solver_q_min"],
            "q_max": policy["inverse_solver_q_max"],
            "domain_basis": policy["inverse_solver_domain_basis"],
            "local_Q4_edge_slots": policy["local_Q4_edge_slots"],
            "equation": "q^p+q=Pi_alpha",
            "identity_use_policy": "diagnostic_only_declared_occurrence_remains_primary",
            "target_value_input_status": "absent",
        },
        "inverse_domain_row_sha256",
    )
    return [row]


def build_inverse_audit(policy: Mapping[str, str], domain_row: Mapping[str, str]) -> list[dict[str, str]]:
    p_min = int(policy["inverse_solver_p_min"])
    q_min = int(policy["inverse_solver_q_min"])
    q_max = int(policy["inverse_solver_q_max"])
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        pi_value = int(specification["q"]) ** int(specification["p"]) + int(specification["q"])
        solutions = branch_solutions(pi_value, p_min=p_min, q_min=q_min, q_max=q_max)
        for order, (p_value, q_value) in enumerate(solutions):
            rows.append(
                attach(
                    {
                        "inverse_solver_domain_id": domain_row["inverse_solver_domain_id"],
                        "inverse_domain_row_sha256": domain_row["inverse_domain_row_sha256"],
                        "form_id": specification["form_id"],
                        "route_form": specification["route_form"],
                        "Pi_alpha": pi_value,
                        "solution_order": order,
                        "solution_count": len(solutions),
                        "candidate_p": p_value,
                        "candidate_q": q_value,
                        "candidate_form_core": f"{p_value}:{q_value}",
                        "declared_occurrence_candidate": "yes" if (p_value, q_value) == (specification["p"], specification["q"]) else "no",
                        "solution_domain": f"p>={p_min}_{q_min}<=q<={q_max}_{policy['inverse_solver_domain_basis']}",
                        "inverse_status": "unique_within_frozen_domain" if len(solutions) == 1 else "multiple_within_frozen_domain",
                        "form_identity_detection_status": "diagnostic_only_declared_occurrence_not_replaced",
                    },
                    "inverse_audit_row_sha256",
                )
            )
    return rows


def build_retyping_registry() -> list[dict[str, str]]:
    mappings = (
        ("consequent_six_slot_kernel_contract.csv", "consequent_six_slot_support_family_measure_contract.csv", "local_DEC_kernel", "support_family_analysis_measure"),
        ("consequent_six_slot_dec_execution_ledger.csv", "consequent_six_slot_support_family_enumeration.csv", "local_DEC_execution", "non_temporal_support_family_enumeration"),
        ("consequent_six_slot_stage_mass_audit.csv", "consequent_six_slot_support_family_mass_audit.csv", "DEC_branch_mass", "support_family_analysis_mass"),
        ("consequent_six_slot_read_only_trace.csv", "consequent_six_slot_support_family_read_only_packet.csv", "DEC_trace", "read_only_support_family_packet"),
    )
    return [
        attach(
            {
                "retyping_order": order,
                "superseded_artifact": old,
                "replacement_artifact": new,
                "superseded_type": old_type,
                "replacement_type": new_type,
                "scientific_accessor_row_change": "none",
                "status": "superseded_removed_from_current_gate",
            },
            "retyping_row_sha256",
        )
        for order, (old, new, old_type, new_type) in enumerate(mappings)
    ]


def validate_accessor_packet(
    occurrence: Mapping[str, str],
    accessor: Mapping[str, str],
    source: Mapping[str, str],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for key in ("form_id", "route_form"):
        if accessor.get(key) != occurrence.get(key):
            reasons.append(f"accessor_{key}_identity_mismatch")
    for accessor_key, occurrence_key in (("declared_p", "declared_p"), ("declared_q", "declared_q"), ("declared_L", "declared_L")):
        if accessor.get(accessor_key) != occurrence.get(occurrence_key):
            reasons.append(f"accessor_{accessor_key}_identity_mismatch")
    try:
        computed = recompute_accessors(int(occurrence["declared_p"]), int(occurrence["declared_q"]), int(occurrence["declared_L"]))
    except (KeyError, ValueError):
        reasons.append("occurrence_accessor_inputs_malformed")
        return False, sorted(set(reasons))
    for field, expected in computed.items():
        if accessor.get(field) != str(expected):
            reasons.append(f"accessor_{field}_mismatch")
    source_pairs = {
        "Pi_alpha": "source_Pi_alpha",
        "RD_AO": "source_RD_AO",
        "L": "source_L",
        "rhoD_omega": "source_rhoD_omega",
        "PD": "source_PD",
        "QD": "source_QD",
        "X_shedding": "source_X_shedding",
    }
    for source_field, accessor_field in source_pairs.items():
        if accessor.get(accessor_field) != source[source_field]:
            reasons.append(f"stored_source_{source_field}_mismatch")
    semantic_fields = {
        "capacity_residual_semantics": "window_capacity_fill_not_recurrence_closure",
        "temporal_inference_status": "not_admitted",
        "target_value_input_status": "absent",
    }
    for key, expected in semantic_fields.items():
        if accessor.get(key) != expected:
            reasons.append(f"accessor_{key}_mismatch")
    expected_status = "passed" if not reasons else "failed"
    if accessor.get("source_accessor_match_status") != expected_status:
        reasons.append("source_accessor_status_inconsistent")
    return not reasons, sorted(set(reasons))


def blank_evaluation(reasons: Sequence[str]) -> dict[str, object]:
    return {
        "passed": False,
        "policy_match": False,
        "accessor_pass": False,
        "cross_packet_binding_pass": False,
        "registry_pass": False,
        "measure_contract_pass": False,
        "enumeration_completeness_pass": False,
        "read_only_binding_pass": False,
        "support_measure_pass": False,
        "inverse_audit_pass": False,
        "declared_in_domain": False,
        "canonical_identity_pass": False,
        "canonical_enumeration_mapping_pass": False,
        "closed_semantics_binding_pass": False,
        "failure_reasons": sorted(set(reasons)),
    }


def evaluate_form_state(
    *,
    policy: Mapping[str, str],
    occurrence: Mapping[str, str],
    accessor: Mapping[str, str],
    source: Mapping[str, str],
    registry_rows: Sequence[Mapping[str, str]],
    measure_contract: Mapping[str, str],
    enumeration_rows: Sequence[Mapping[str, str]],
    read_only_packet: Mapping[str, str],
    support_mass: Mapping[str, str],
    inverse_domain: Mapping[str, str],
    inverse_rows: Sequence[Mapping[str, str]],
    enumeration_path: Path = ENUMERATION_LEDGER,
) -> dict[str, object]:
    """Fail-closed compatibility evaluation for one scoped occurrence."""
    reasons: list[str] = []

    # Hashes are verified before any semantic fields are consumed.
    hash_items: list[tuple[Mapping[str, str], str, str]] = [
        (policy, "support_policy_sha256", "support_policy"),
        (occurrence, "occurrence_row_sha256", "occurrence"),
        (accessor, "accessor_audit_row_sha256", "accessor"),
        (measure_contract, "support_measure_sha256", "support_measure"),
        (read_only_packet, "read_only_packet_row_sha256", "read_only_packet"),
        (support_mass, "support_mass_audit_row_sha256", "support_mass"),
        (inverse_domain, "inverse_domain_row_sha256", "inverse_domain"),
    ]
    hash_items.extend((row, "support_family_registry_row_sha256", f"registry_{index}") for index, row in enumerate(registry_rows))
    hash_items.extend((row, "support_member_row_sha256", f"enumeration_{index}") for index, row in enumerate(enumeration_rows))
    hash_items.extend((row, "inverse_audit_row_sha256", f"inverse_{index}") for index, row in enumerate(inverse_rows))
    for row, hash_field, label in hash_items:
        try:
            verify_attached_row(row, hash_field)
        except (KeyError, ValueError):
            reasons.append(f"{label}_row_hash_mismatch")
    if reasons:
        return blank_evaluation(reasons)

    form_id = occurrence.get("form_id", "")
    specification = FORM_BY_ID.get(form_id)
    if specification is None:
        reasons.append("occurrence_form_id_not_in_release_contract")
        return blank_evaluation(reasons)

    route_form = occurrence.get("route_form", "")
    p_value = safe_int(occurrence.get("declared_p"), "occurrence_p", reasons)
    q_value = safe_int(occurrence.get("declared_q"), "occurrence_q", reasons)
    outer_length = safe_int(occurrence.get("declared_L"), "occurrence_L", reasons)
    if None in (p_value, q_value, outer_length):
        return blank_evaluation(reasons)
    assert p_value is not None and q_value is not None and outer_length is not None

    # Bind the occurrence to the release specification before any exponentiation.
    expected_p = int(specification["p"])
    expected_q = int(specification["q"])
    expected_L = safe_int(policy.get("declared_scope_L"), "policy_declared_scope_L", reasons)
    if expected_L is None:
        return blank_evaluation(reasons)
    expected_route = expected_route_form(expected_p, expected_q, expected_L)
    expected_occurrence_fields = {
        "occurrence_order": str(EXPECTED_FORM_IDS.index(form_id)),
        "occurrence_id": expected_occurrence_id(form_id),
        "form_name": str(specification["name"]),
        "route_form": expected_route,
        "declared_p": str(expected_p),
        "declared_q": str(expected_q),
        "declared_L": str(expected_L),
        "form_identity_source": "declared_scoped_occurrence_not_inferred_from_support_family",
        "local_DEC_status": "not_materialized",
        "target_value_input_status": "absent",
        "source_file": source.get("source_file", ""),
        "source_file_sha256": source.get("source_file_sha256", ""),
        "source_row_text_sha256": source.get("source_row_text_sha256", ""),
    }
    canonical_identity_pass = True
    for key, expected in expected_occurrence_fields.items():
        if occurrence.get(key) != expected:
            canonical_identity_pass = False
            reasons.append(f"occurrence_{key}_release_contract_mismatch")

    p_min = safe_int(policy.get("inverse_solver_p_min"), "policy_inverse_p_min", reasons)
    q_min = safe_int(policy.get("inverse_solver_q_min"), "policy_inverse_q_min", reasons)
    q_max = safe_int(policy.get("inverse_solver_q_max"), "policy_inverse_q_max", reasons)
    if None in (p_min, q_min, q_max):
        return blank_evaluation(reasons)
    assert p_min is not None and q_min is not None and q_max is not None
    if not (p_min <= p_value and q_min <= q_value <= q_max and outer_length == expected_L):
        canonical_identity_pass = False
        reasons.append("occurrence_outside_frozen_release_domain")
    if not canonical_identity_pass:
        return blank_evaluation(reasons)

    # Counts are derived from the release specification, not untrusted occurrence values.
    expected_family_id, expected_measure_id = expected_ids(form_id)
    expected_walk_count = expected_q**expected_p
    expected_shell_count = expected_q
    expected_count = expected_walk_count + expected_shell_count
    expected_measure = Fraction(1, expected_count)

    policy_match = all(
        (
            canonical_identity_pass,
            occurrence.get("primitive_support_id") == policy.get("primitive_support_id"),
            occurrence.get("support_policy_id") == policy.get("support_policy_id"),
            occurrence.get("support_policy_sha256") == policy.get("support_policy_sha256"),
            occurrence.get("fractal_octave_coordinate") == policy.get("fractal_octave_coordinate"),
            occurrence.get("declared_L") == policy.get("declared_scope_L"),
            occurrence.get("outer_enclosure_id") == policy.get("outer_enclosure_id"),
        )
    )
    if not policy_match:
        reasons.append("primitive_support_policy_semantic_mismatch")

    accessor_pass, accessor_reasons = validate_accessor_packet(occurrence, accessor, source)
    reasons.extend(accessor_reasons)

    # Registry binding and exact class cardinalities.
    registry_pass = True
    if len(registry_rows) != 2:
        registry_pass = False
        reasons.append("registry_row_count_mismatch")
    registry_by_class: dict[str, Mapping[str, str]] = {}
    for row in registry_rows:
        member_class = row.get("member_class", "")
        if member_class in registry_by_class:
            registry_pass = False
            reasons.append("duplicate_registry_member_class")
        registry_by_class[member_class] = row
        for key, expected in (
            ("form_id", form_id),
            ("route_form", route_form),
            ("support_family_id", expected_family_id),
            ("support_measure_id", expected_measure_id),
            ("support_family_definition", "F_pq=D_q^p_disjoint_union_S_q"),
            ("total_support_family_count", str(expected_count)),
            ("Pi_alpha", str(expected_count)),
        ):
            if row.get(key) != expected:
                registry_pass = False
                reasons.append(f"registry_{key}_binding_mismatch")
    expected_classes = {
        "walk_history": {
            "count": expected_walk_count,
            "word_length": p_value,
            "class_order": 0,
            "definition": "D_q^p: all length-p words over the q-direction alphabet",
        },
        "retained_support_shell": {
            "count": expected_shell_count,
            "word_length": 0,
            "class_order": 1,
            "definition": "S_q: q declared disjoint retained support-shell members; not local edges",
        },
    }
    if set(registry_by_class) != set(expected_classes):
        registry_pass = False
        reasons.append("registry_class_set_mismatch")
    for member_class, expected_class in expected_classes.items():
        row = registry_by_class.get(member_class)
        if row is None:
            continue
        if row.get("member_count") != str(expected_class["count"]):
            registry_pass = False
            reasons.append(f"registry_{member_class}_count_mismatch")
        if row.get("walk_word_length") != str(expected_class["word_length"]):
            registry_pass = False
            reasons.append(f"registry_{member_class}_word_length_mismatch")
        if row.get("class_order") != str(expected_class["class_order"]):
            registry_pass = False
            reasons.append(f"registry_{member_class}_class_order_mismatch")
        if row.get("class_definition") != str(expected_class["definition"]):
            registry_pass = False
            reasons.append(f"registry_{member_class}_class_definition_mismatch")
        if row.get("direction_alphabet_size") != str(q_value):
            registry_pass = False
            reasons.append(f"registry_{member_class}_alphabet_mismatch")
        if row.get("local_DEC_edge_status") != "not_a_local_Q4_edge_inventory":
            registry_pass = False
            reasons.append(f"registry_{member_class}_local_DEC_edge_status_mismatch")
        if row.get("row_time_semantics") != "non_temporal_support_family_card":
            registry_pass = False
            reasons.append(f"registry_{member_class}_row_time_semantics_mismatch")

    # Measure contract binding.
    measure_contract_pass = True
    measure_expected_fields = {
        "form_id": form_id,
        "route_form": route_form,
        "support_family_id": expected_family_id,
        "support_measure_id": expected_measure_id,
        "support_family_definition": "F_pq=D_q^p_disjoint_union_S_q",
        "walk_history_count": str(expected_walk_count),
        "retained_support_shell_count": str(expected_shell_count),
        "support_member_count": str(expected_count),
        "normalizer_num": str(expected_count),
        "normalizer_den": "1",
        "member_measure_num": str(expected_measure.numerator),
        "member_measure_den": str(expected_measure.denominator),
        "member_measure_exact": fraction_text(expected_measure.numerator, expected_measure.denominator),
        "measure_sum_num": "1",
        "measure_sum_den": "1",
        "measure_semantics": "uniform_support_family_analysis_measure",
        "uniform_weighting_status": "declared_definitional_not_physical_probability_law",
        "relation_to_DEC_kernel": "distinct_not_a_local_Q4_kernel",
        "execution_mode": "support_family_enumeration",
        "row_time_semantics": "non_temporal_analysis_measure",
        "target_value_input_status": "absent",
    }
    for key, expected in measure_expected_fields.items():
        if measure_contract.get(key) != expected:
            measure_contract_pass = False
            reasons.append(f"measure_contract_{key}_mismatch")

    # Enumeration must match the frozen ledger and complete the exact disjoint union.
    enumeration_completeness_pass = True
    if not enumeration_path.is_file():
        enumeration_completeness_pass = False
        reasons.append("enumeration_ledger_missing")
        actual_group: list[dict[str, str]] = []
        ledger_sha = ""
    else:
        all_actual = read_csv(enumeration_path)
        actual_group = [row for row in all_actual if row.get("form_id") == form_id]
        ledger_sha = sha_file(enumeration_path)
        if canonical_json(actual_group) != canonical_json(list(enumeration_rows)):
            enumeration_completeness_pass = False
            reasons.append("enumeration_packet_not_equal_to_frozen_ledger_subset")

    if len(enumeration_rows) != expected_count:
        enumeration_completeness_pass = False
        reasons.append("enumeration_member_count_mismatch")
    member_ids = [row.get("support_member_id", "") for row in enumeration_rows]
    if len(member_ids) != len(set(member_ids)) or "" in member_ids:
        enumeration_completeness_pass = False
        reasons.append("enumeration_support_member_id_not_unique")
    member_orders: list[int] = []
    for row in enumeration_rows:
        parsed = safe_int(row.get("support_member_order"), "support_member_order", reasons)
        if parsed is not None:
            member_orders.append(parsed)
    if sorted(member_orders) != list(range(expected_count)):
        enumeration_completeness_pass = False
        reasons.append("enumeration_support_member_order_incomplete")

    canonical_rows = canonical_member_rows(form_id, expected_L)
    canonical_enumeration_mapping_pass = len(enumeration_rows) == len(canonical_rows)
    if not canonical_enumeration_mapping_pass:
        reasons.append("canonical_enumeration_row_count_mismatch")
    canonical_fields = (
        "enumeration_row_index",
        "support_member_order",
        "support_family_id",
        "support_measure_id",
        "form_id",
        "route_form",
        "member_class",
        "member_class_order",
        "support_member_id",
        "history_word",
        "history_length",
        "direction_alphabet_size",
        "support_shell_member_index",
        "analysis_weight_num",
        "analysis_weight_den",
        "local_Q4_edge_status",
        "row_time_semantics",
        "target_value_input_status",
    )
    for index, expected_row in enumerate(canonical_rows):
        if index >= len(enumeration_rows):
            break
        row = enumeration_rows[index]
        for key in canonical_fields:
            if row.get(key) != expected_row[key]:
                canonical_enumeration_mapping_pass = False
                reasons.append(f"canonical_enumeration_{key}_mismatch")

    expected_words = {".".join(str(value) for value in values) for values in itertools.product(range(q_value), repeat=p_value)}
    observed_words: set[str] = set()
    observed_shells: set[int] = set()
    recomputed_mass = Fraction(0, 1)
    for row in enumeration_rows:
        for key, expected in (
            ("form_id", form_id),
            ("route_form", route_form),
            ("support_family_id", expected_family_id),
            ("support_measure_id", expected_measure_id),
            ("direction_alphabet_size", str(q_value)),
        ):
            if row.get(key) != expected:
                enumeration_completeness_pass = False
                reasons.append(f"enumeration_{key}_binding_mismatch")
        measure_value = safe_fraction(row.get("measure_num"), row.get("measure_den"), "enumeration_measure", reasons)
        if measure_value is None or measure_value != expected_measure:
            enumeration_completeness_pass = False
            reasons.append("enumeration_measure_mismatch")
        else:
            recomputed_mass += measure_value
        if row.get("measure_exact") != fraction_text(expected_measure.numerator, expected_measure.denominator):
            enumeration_completeness_pass = False
            reasons.append("enumeration_measure_exact_mismatch")
        if row.get("analysis_weight_num") != "1" or row.get("analysis_weight_den") != "1":
            enumeration_completeness_pass = False
            reasons.append("enumeration_analysis_weight_mismatch")
        member_class = row.get("member_class")
        if member_class == "walk_history":
            word = row.get("history_word", "")
            parts = word.split(".") if word else []
            if len(parts) != p_value or any(not part.isdigit() for part in parts):
                enumeration_completeness_pass = False
                reasons.append("malformed_direction_word")
            else:
                symbols = [int(part) for part in parts]
                if any(symbol < 0 or symbol >= q_value for symbol in symbols):
                    enumeration_completeness_pass = False
                    reasons.append("direction_word_symbol_out_of_domain")
            if row.get("history_length") != str(p_value):
                enumeration_completeness_pass = False
                reasons.append("direction_word_length_mismatch")
            if row.get("support_shell_member_index", "") != "":
                enumeration_completeness_pass = False
                reasons.append("walk_history_has_support_shell_index")
            observed_words.add(word)
        elif member_class == "retained_support_shell":
            if row.get("history_word", "") != "" or row.get("history_length") != "0":
                enumeration_completeness_pass = False
                reasons.append("support_shell_has_history_word")
            shell_index = safe_int(row.get("support_shell_member_index"), "support_shell_member_index", reasons)
            if shell_index is not None:
                if shell_index < 0 or shell_index >= q_value:
                    enumeration_completeness_pass = False
                    reasons.append("support_shell_index_out_of_domain")
                observed_shells.add(shell_index)
        else:
            enumeration_completeness_pass = False
            reasons.append("enumeration_member_class_invalid")
    if observed_words != expected_words:
        enumeration_completeness_pass = False
        reasons.append("direction_word_cartesian_set_mismatch")
    if observed_shells != set(range(q_value)):
        enumeration_completeness_pass = False
        reasons.append("support_shell_set_mismatch")
    if recomputed_mass != 1:
        enumeration_completeness_pass = False
        reasons.append("recomputed_support_mass_not_one")

    # Read-only binding to the exact enumeration and identities.
    read_only_binding_pass = True
    read_only_expected = {
        "form_id": form_id,
        "route_form": route_form,
        "support_family_id": expected_family_id,
        "support_measure_id": expected_measure_id,
        "walk_history_count": str(expected_walk_count),
        "retained_support_shell_count": str(expected_shell_count),
        "support_member_count": str(expected_count),
        "support_family_subset_sha256": sha_bytes(canonical_json(list(enumeration_rows))),
        "enumeration_ledger_sha256": ledger_sha,
        "support_measure_conservation_status": "passed",
        "freeze_status": "frozen_before_compatibility_audit",
        "event_order_status": "not_applicable_non_temporal_support_family",
        "local_DEC_trace_status": "not_materialized",
        "target_value_read_status": "not_read",
    }
    for key, expected in read_only_expected.items():
        if read_only_packet.get(key) != expected:
            read_only_binding_pass = False
            reasons.append(f"read_only_{key}_mismatch")

    # Recompute mass from enumeration; summary status is not trusted.
    support_measure_pass = recomputed_mass == 1
    mass_expected = {
        "form_id": form_id,
        "route_form": route_form,
        "support_family_id": expected_family_id,
        "support_measure_id": expected_measure_id,
        "support_member_count": str(expected_count),
        "analysis_mass_expected_num": "1",
        "analysis_mass_expected_den": "1",
        "analysis_mass_sum_num": str(recomputed_mass.numerator),
        "analysis_mass_sum_den": str(recomputed_mass.denominator),
        "analysis_mass_residual_num": str((recomputed_mass - 1).numerator),
        "analysis_mass_residual_den": str((recomputed_mass - 1).denominator),
        "support_measure_conservation_status": "passed" if recomputed_mass == 1 else "failed",
        "mass_semantics": "support_family_analysis_mass_not_DEC_branch_mass",
        "temporal_status": "not_time_measurement",
    }
    for key, expected in mass_expected.items():
        if support_mass.get(key) != expected:
            support_measure_pass = False
            reasons.append(f"support_mass_{key}_mismatch")

    # Frozen inverse-domain and complete inverse solution-set audit.
    inverse_audit_pass = True
    domain_expected = {
        "support_policy_id": policy.get("support_policy_id", ""),
        "support_policy_sha256": policy.get("support_policy_sha256", ""),
        "policy_validation_mode": POLICY_VALIDATION_MODE,
        "p_min": policy.get("inverse_solver_p_min", ""),
        "q_min": policy.get("inverse_solver_q_min", ""),
        "q_max": policy.get("inverse_solver_q_max", ""),
        "domain_basis": policy.get("inverse_solver_domain_basis", ""),
        "local_Q4_edge_slots": policy.get("local_Q4_edge_slots", ""),
        "equation": "q^p+q=Pi_alpha",
        "identity_use_policy": "diagnostic_only_declared_occurrence_remains_primary",
        "target_value_input_status": "absent",
    }
    for key, expected in domain_expected.items():
        if inverse_domain.get(key) != expected:
            inverse_audit_pass = False
            reasons.append(f"inverse_domain_{key}_mismatch")
    p_min = safe_int(inverse_domain.get("p_min"), "inverse_p_min", reasons)
    q_min = safe_int(inverse_domain.get("q_min"), "inverse_q_min", reasons)
    q_max = safe_int(inverse_domain.get("q_max"), "inverse_q_max", reasons)
    expected_solutions: list[tuple[int, int]] = []
    if None not in (p_min, q_min, q_max):
        assert p_min is not None and q_min is not None and q_max is not None
        try:
            expected_solutions = branch_solutions(expected_count, p_min=p_min, q_min=q_min, q_max=q_max)
        except ValueError:
            inverse_audit_pass = False
            reasons.append("inverse_domain_invalid")
    if len(inverse_rows) != len(expected_solutions):
        inverse_audit_pass = False
        reasons.append("inverse_solution_row_count_mismatch")
    stored_candidates: list[tuple[int, int]] = []
    expected_domain_text = ""
    if None not in (p_min, q_min, q_max):
        expected_domain_text = f"p>={p_min}_{q_min}<=q<={q_max}_{policy['inverse_solver_domain_basis']}"
    parsed_inverse_rows: list[tuple[int, Mapping[str, str]]] = []
    parsed_orders: list[int] = []
    for row in inverse_rows:
        parsed_order = safe_int(row.get("solution_order"), "inverse_solution_order", reasons)
        if parsed_order is None:
            inverse_audit_pass = False
            continue
        parsed_orders.append(parsed_order)
        parsed_inverse_rows.append((parsed_order, row))
    if len(parsed_orders) != len(set(parsed_orders)):
        inverse_audit_pass = False
        reasons.append("inverse_solution_order_duplicate")
    if sorted(parsed_orders) != list(range(len(expected_solutions))):
        inverse_audit_pass = False
        reasons.append("inverse_solution_order_set_mismatch")
    for order, row in sorted(parsed_inverse_rows, key=lambda item: item[0]):
        candidate_p = safe_int(row.get("candidate_p"), "inverse_candidate_p", reasons)
        candidate_q = safe_int(row.get("candidate_q"), "inverse_candidate_q", reasons)
        if candidate_p is not None and candidate_q is not None:
            stored_candidates.append((candidate_p, candidate_q))
            expected_candidate = expected_solutions[order] if 0 <= order < len(expected_solutions) else None
            if expected_candidate != (candidate_p, candidate_q):
                inverse_audit_pass = False
                reasons.append("inverse_candidate_solution_set_mismatch")
        expected_values = {
            "inverse_solver_domain_id": inverse_domain.get("inverse_solver_domain_id", ""),
            "inverse_domain_row_sha256": inverse_domain.get("inverse_domain_row_sha256", ""),
            "form_id": form_id,
            "route_form": route_form,
            "Pi_alpha": str(expected_count),
            "solution_order": str(order),
            "solution_count": str(len(expected_solutions)),
            "candidate_form_core": f"{candidate_p}:{candidate_q}" if candidate_p is not None and candidate_q is not None else "",
            "declared_occurrence_candidate": "yes" if (candidate_p, candidate_q) == (p_value, q_value) else "no",
            "solution_domain": expected_domain_text,
            "inverse_status": "unique_within_frozen_domain" if len(expected_solutions) == 1 else "multiple_within_frozen_domain",
            "form_identity_detection_status": "diagnostic_only_declared_occurrence_not_replaced",
        }
        for key, expected in expected_values.items():
            if row.get(key) != expected:
                inverse_audit_pass = False
                reasons.append(f"inverse_row_{key}_mismatch")
    if stored_candidates != expected_solutions:
        inverse_audit_pass = False
        reasons.append("inverse_stored_solution_set_mismatch")
    declared_in_domain = (p_value, q_value) in expected_solutions and any(
        row.get("declared_occurrence_candidate") == "yes"
        and row.get("candidate_p") == str(p_value)
        and row.get("candidate_q") == str(q_value)
        for row in inverse_rows
    )
    if not declared_in_domain:
        reasons.append("declared_form_not_in_frozen_inverse_domain")

    closed_semantics_binding_pass = all(
        (
            occurrence.get("form_identity_source") == "declared_scoped_occurrence_not_inferred_from_support_family",
            occurrence.get("local_DEC_status") == "not_materialized",
            occurrence.get("target_value_input_status") == "absent",
            accessor.get("capacity_residual_semantics") == "window_capacity_fill_not_recurrence_closure",
            accessor.get("temporal_inference_status") == "not_admitted",
            accessor.get("target_value_input_status") == "absent",
            read_only_packet.get("support_measure_conservation_status") == "passed",
            read_only_packet.get("local_DEC_trace_status") == "not_materialized",
            read_only_packet.get("target_value_read_status") == "not_read",
            inverse_domain.get("identity_use_policy") == "diagnostic_only_declared_occurrence_remains_primary",
            inverse_domain.get("target_value_input_status") == "absent",
        )
    )
    if not closed_semantics_binding_pass:
        reasons.append("closed_semantics_binding_failure")

    cross_packet_binding_pass = all(
        (
            policy_match,
            accessor_pass,
            registry_pass,
            measure_contract_pass,
            enumeration_completeness_pass,
            read_only_binding_pass,
            support_measure_pass,
            inverse_audit_pass,
            declared_in_domain,
            canonical_identity_pass,
            canonical_enumeration_mapping_pass,
            closed_semantics_binding_pass,
        )
    )
    if not cross_packet_binding_pass:
        reasons.append("cross_packet_binding_failure")

    return {
        "passed": not reasons,
        "policy_match": policy_match,
        "accessor_pass": accessor_pass,
        "cross_packet_binding_pass": cross_packet_binding_pass,
        "registry_pass": registry_pass,
        "measure_contract_pass": measure_contract_pass,
        "enumeration_completeness_pass": enumeration_completeness_pass,
        "read_only_binding_pass": read_only_binding_pass,
        "support_measure_pass": support_measure_pass,
        "inverse_audit_pass": inverse_audit_pass,
        "declared_in_domain": declared_in_domain,
        "canonical_identity_pass": canonical_identity_pass,
        "canonical_enumeration_mapping_pass": canonical_enumeration_mapping_pass,
        "closed_semantics_binding_pass": closed_semantics_binding_pass,
        "expected_support_family_id": expected_family_id,
        "expected_support_measure_id": expected_measure_id,
        "expected_walk_count": expected_walk_count,
        "expected_support_shell_count": expected_shell_count,
        "expected_support_member_count": expected_count,
        "recomputed_mass_num": recomputed_mass.numerator,
        "recomputed_mass_den": recomputed_mass.denominator,
        "failure_reasons": sorted(set(reasons)),
    }


def write_stage_files() -> dict[str, Path]:
    DATA.mkdir(parents=True, exist_ok=True)
    for old_name in OLD_RETYPE_FILES:
        path = DATA / old_name
        if path.exists():
            path.unlink()
    source_rows = parse_main_source_rows()
    policy = load_support_policy()
    outputs: dict[str, Path] = {}

    def emit(name: str, rows: list[dict[str, str]]) -> Path:
        if not rows:
            raise ValueError(f"no rows for {name}")
        path = DATA / name
        write_csv(path, list(rows[0]), rows)
        outputs[name] = path
        return path

    emit("consequent_six_slot_rule_contract.csv", build_rule_contract(policy))
    occurrences = build_occurrences(source_rows, policy)
    emit("consequent_six_slot_occurrence_card.csv", occurrences)
    emit("consequent_six_slot_support_family_registry.csv", build_support_family_registry())
    measures = build_support_family_measure_contract()
    emit("consequent_six_slot_support_family_measure_contract.csv", measures)
    enumeration = build_support_family_enumeration(measures)
    enumeration_path = emit("consequent_six_slot_support_family_enumeration.csv", enumeration)
    mass_audit = build_support_family_mass_audit(enumeration)
    emit("consequent_six_slot_support_family_mass_audit.csv", mass_audit)
    emit(
        "consequent_six_slot_support_family_read_only_packet.csv",
        build_support_family_read_only_packet(enumeration_path, enumeration, mass_audit),
    )
    emit("consequent_six_slot_local_dec_admission_contract.csv", build_local_dec_admission_contract(policy))
    emit("consequent_six_slot_field_accessor_audit.csv", build_accessor_audit(source_rows, occurrences))
    inverse_domain_rows = build_inverse_domain_contract(policy)
    emit("consequent_six_slot_inverse_solver_domain_contract.csv", inverse_domain_rows)
    emit("consequent_six_slot_branch_inverse_audit.csv", build_inverse_audit(policy, inverse_domain_rows[0]))
    emit("consequent_six_slot_artifact_retyping_registry.csv", build_retyping_registry())
    return outputs


def build_pre_audit_manifest(stage_outputs: Mapping[str, Path]) -> Path:
    entries: list[dict[str, str]] = []
    inputs = [
        ("frozen_main_source_table", SOURCE_TEX),
        ("primitive_C6_support_policy", SUPPORT_POLICY),
        ("gate_generator", Path(__file__).resolve()),
        *[(name.removesuffix(".csv"), path) for name, path in sorted(stage_outputs.items())],
    ]
    for role, path in inputs:
        entries.append(
            attach(
                {
                    "artifact_role": role,
                    "artifact_path": path.relative_to(ROOT).as_posix(),
                    "artifact_bytes": path.stat().st_size,
                    "artifact_sha256": sha_file(path),
                    "freeze_status": "frozen_before_compatibility_audit",
                },
                "manifest_row_sha256",
            )
        )
    path = DATA / "consequent_six_slot_pre_audit_freeze_manifest.csv"
    write_csv(path, list(entries[0]), entries)
    return path


def verify_pre_audit_freeze(manifest_path: Path, root: Path = ROOT) -> None:
    for row in read_csv(manifest_path):
        verify_attached_row(row, "manifest_row_sha256")
        path = root / row["artifact_path"]
        if not path.is_file():
            raise ValueError(f"frozen artifact missing: {row['artifact_role']}")
        if sha_file(path) != row["artifact_sha256"] or str(path.stat().st_size) != row["artifact_bytes"]:
            raise ValueError(f"frozen artifact SHA-256 mismatch: {row['artifact_role']}")


def mutate_attached(row: Mapping[str, str], hash_field: str, changes: Mapping[str, object]) -> dict[str, str]:
    body = {key: value for key, value in row.items() if key != hash_field}
    body.update({key: str(value) for key, value in changes.items()})
    return attach(body, hash_field)


PACKET_FILE_SPECS: dict[str, tuple[str, str]] = {
    "occurrences": ("consequent_six_slot_occurrence_card.csv", "occurrence_row_sha256"),
    "accessors": ("consequent_six_slot_field_accessor_audit.csv", "accessor_audit_row_sha256"),
    "registries": ("consequent_six_slot_support_family_registry.csv", "support_family_registry_row_sha256"),
    "measures": ("consequent_six_slot_support_family_measure_contract.csv", "support_measure_sha256"),
    "enumeration": ("consequent_six_slot_support_family_enumeration.csv", "support_member_row_sha256"),
    "read_only": ("consequent_six_slot_support_family_read_only_packet.csv", "read_only_packet_row_sha256"),
    "mass": ("consequent_six_slot_support_family_mass_audit.csv", "support_mass_audit_row_sha256"),
    "inverse_domain": ("consequent_six_slot_inverse_solver_domain_contract.csv", "inverse_domain_row_sha256"),
    "inverse": ("consequent_six_slot_branch_inverse_audit.csv", "inverse_audit_row_sha256"),
}

EXPECTED_PACKET_ROW_COUNTS = {
    "occurrences": 2,
    "accessors": 2,
    "registries": 4,
    "measures": 2,
    "enumeration": 98,
    "read_only": 2,
    "mass": 2,
    "inverse_domain": 1,
    "inverse": 2,
}


def load_raw_packet_rows() -> dict[str, list[dict[str, str]]]:
    return {
        label: read_csv(DATA / filename)
        for label, (filename, _hash_field) in PACKET_FILE_SPECS.items()
    }


def strict_unique_map(
    rows: Sequence[Mapping[str, str]],
    key: str,
    label: str,
) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value:
            raise ValueError(f"global packet-set closure failed: {label}_blank_{key}")
        if value in result:
            raise ValueError(f"global packet-set closure failed: duplicate_{label}_{key}:{value}")
        result[value] = row
    return result


def canonical_global_enumeration_rows(policy: Mapping[str, str]) -> list[dict[str, str]]:
    """Return the complete release-canonical physical serialization.

    The row order is semantic for this gate: form_3_3_6 precedes form_3_4_6,
    and every per-form member follows the canonical Cartesian/shell order.
    """
    reasons: list[str] = []
    outer_length = safe_int(policy.get("declared_scope_L"), "policy_declared_scope_L", reasons)
    if outer_length is None or reasons:
        raise ValueError("invalid support policy for canonical enumeration")
    rows: list[dict[str, str]] = []
    for specification in FORMS:
        form_id = str(specification["form_id"])
        count = int(specification["q"]) ** int(specification["p"]) + int(specification["q"])
        for row in canonical_member_rows(form_id, outer_length):
            full = dict(row)
            full.update(
                {
                    "measure_num": "1",
                    "measure_den": str(count),
                    "measure_exact": fraction_text(1, count),
                }
            )
            rows.append(full)
    return rows


def validate_global_packet_set(
    packet_rows: Mapping[str, Sequence[Mapping[str, str]]],
    policy: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Validate exact global packet-set closure before filtering or map construction."""
    reasons: list[str] = []
    policy = policy or load_support_policy()
    expected_form_set = set(EXPECTED_FORM_IDS)
    expected_route_by_form = {str(item["form_id"]): str(item["route_form"]) for item in FORMS}

    # Hash and exact row-count closure are checked before semantic filtering.
    for label, (_filename, hash_field) in PACKET_FILE_SPECS.items():
        rows = list(packet_rows.get(label, ()))
        if len(rows) != EXPECTED_PACKET_ROW_COUNTS[label]:
            reasons.append(f"global_{label}_row_count_mismatch")
        for index, row in enumerate(rows):
            try:
                verify_attached_row(row, hash_field)
            except (KeyError, ValueError):
                reasons.append(f"global_{label}_{index}_row_hash_mismatch")

    singleton_labels = ("occurrences", "accessors", "measures", "read_only", "mass")
    for label in singleton_labels:
        rows = list(packet_rows.get(label, ()))
        form_ids = [row.get("form_id", "") for row in rows]
        if len(form_ids) != len(set(form_ids)):
            reasons.append(f"global_{label}_duplicate_form_id")
        if set(form_ids) != expected_form_set:
            reasons.append(f"global_{label}_form_set_mismatch")
        for row in rows:
            form_id = row.get("form_id", "")
            if form_id in expected_route_by_form and row.get("route_form") != expected_route_by_form[form_id]:
                reasons.append(f"global_{label}_route_form_mismatch")
            if form_id in expected_form_set and label in ("measures", "read_only", "mass"):
                expected_family_id, expected_measure_id = expected_ids(form_id)
                if row.get("support_family_id") != expected_family_id:
                    reasons.append(f"global_{label}_support_family_id_mismatch")
                if row.get("support_measure_id") != expected_measure_id:
                    reasons.append(f"global_{label}_support_measure_id_mismatch")

    occurrences = list(packet_rows.get("occurrences", ()))
    for order, specification in enumerate(FORMS):
        form_id = str(specification["form_id"])
        matches = [row for row in occurrences if row.get("form_id") == form_id]
        if len(matches) != 1:
            continue
        row = matches[0]
        expected_occurrence = {
            "occurrence_order": str(order),
            "occurrence_id": expected_occurrence_id(form_id),
            "form_name": str(specification["name"]),
            "route_form": str(specification["route_form"]),
            "declared_p": str(specification["p"]),
            "declared_q": str(specification["q"]),
        }
        for key, expected in expected_occurrence.items():
            if row.get(key) != expected:
                reasons.append(f"global_occurrence_{key}_mismatch")

    registries = list(packet_rows.get("registries", ()))
    registry_keys = [(row.get("form_id", ""), row.get("member_class", "")) for row in registries]
    if len(registry_keys) != len(set(registry_keys)):
        reasons.append("global_registry_duplicate_form_class")
    expected_registry_keys = {
        (form_id, member_class)
        for form_id in EXPECTED_FORM_IDS
        for member_class in ("walk_history", "retained_support_shell")
    }
    if set(registry_keys) != expected_registry_keys:
        reasons.append("global_registry_form_class_set_mismatch")
    for row in registries:
        form_id = row.get("form_id", "")
        if form_id not in expected_form_set:
            reasons.append("global_registry_foreign_form_id")
            continue
        family_id, measure_id = expected_ids(form_id)
        if row.get("route_form") != expected_route_by_form[form_id]:
            reasons.append("global_registry_route_form_mismatch")
        if row.get("support_family_id") != family_id:
            reasons.append("global_registry_support_family_id_mismatch")
        if row.get("support_measure_id") != measure_id:
            reasons.append("global_registry_support_measure_id_mismatch")

    enumeration = list(packet_rows.get("enumeration", ()))
    enumeration_indexes: list[int] = []
    enumeration_ids: list[str] = []
    for row in enumeration:
        form_id = row.get("form_id", "")
        if form_id not in expected_form_set:
            reasons.append("global_enumeration_foreign_form_id")
            continue
        family_id, measure_id = expected_ids(form_id)
        if row.get("route_form") != expected_route_by_form[form_id]:
            reasons.append("global_enumeration_route_form_mismatch")
        if row.get("support_family_id") != family_id:
            reasons.append("global_enumeration_support_family_id_mismatch")
        if row.get("support_measure_id") != measure_id:
            reasons.append("global_enumeration_support_measure_id_mismatch")
        try:
            enumeration_indexes.append(int(row.get("enumeration_row_index", "")))
        except ValueError:
            reasons.append("global_enumeration_index_malformed")
        enumeration_ids.append(row.get("support_member_id", ""))
    expected_index_sequence = list(range(EXPECTED_PACKET_ROW_COUNTS["enumeration"]))
    if sorted(enumeration_indexes) != expected_index_sequence:
        reasons.append("global_enumeration_index_set_mismatch")
    if enumeration_indexes != expected_index_sequence:
        reasons.append("global_enumeration_physical_order_mismatch")
    if len(enumeration_indexes) != len(set(enumeration_indexes)):
        reasons.append("global_enumeration_index_duplicate")
    if "" in enumeration_ids or len(enumeration_ids) != len(set(enumeration_ids)):
        reasons.append("global_enumeration_support_member_id_not_unique")

    canonical_global_rows = canonical_global_enumeration_rows(policy)
    canonical_global_fields = (
        "enumeration_row_index",
        "support_member_order",
        "support_family_id",
        "support_measure_id",
        "form_id",
        "route_form",
        "member_class",
        "member_class_order",
        "support_member_id",
        "history_word",
        "history_length",
        "direction_alphabet_size",
        "support_shell_member_index",
        "analysis_weight_num",
        "analysis_weight_den",
        "measure_num",
        "measure_den",
        "measure_exact",
        "local_Q4_edge_status",
        "row_time_semantics",
        "target_value_input_status",
    )
    if len(enumeration) != len(canonical_global_rows):
        reasons.append("global_enumeration_canonical_row_count_mismatch")
    else:
        for actual, expected in zip(enumeration, canonical_global_rows):
            if any(actual.get(key) != expected.get(key) for key in canonical_global_fields):
                reasons.append("global_enumeration_canonical_serialization_mismatch")
                break

    inverse_domain_rows = list(packet_rows.get("inverse_domain", ()))
    if len(inverse_domain_rows) == 1:
        domain = inverse_domain_rows[0]
        if domain.get("identity_use_policy") != "diagnostic_only_declared_occurrence_remains_primary":
            reasons.append("global_inverse_domain_identity_policy_mismatch")
        if domain.get("target_value_input_status") != "absent":
            reasons.append("global_inverse_domain_target_value_input_status_mismatch")

    inverse = list(packet_rows.get("inverse", ()))
    inverse_keys = [(row.get("form_id", ""), row.get("solution_order", "")) for row in inverse]
    if len(inverse_keys) != len(set(inverse_keys)):
        reasons.append("global_inverse_duplicate_form_solution_order")
    if {row.get("form_id", "") for row in inverse} != expected_form_set:
        reasons.append("global_inverse_form_set_mismatch")
    for row in inverse:
        form_id = row.get("form_id", "")
        if form_id not in expected_form_set:
            reasons.append("global_inverse_foreign_form_id")
        elif row.get("route_form") != expected_route_by_form[form_id]:
            reasons.append("global_inverse_route_form_mismatch")

    physical_serialization_pass = not any(
        reason in {
            "global_enumeration_physical_order_mismatch",
            "global_enumeration_canonical_row_count_mismatch",
            "global_enumeration_canonical_serialization_mismatch",
        }
        for reason in reasons
    )
    pre_map_identity_pass = not any(
        reason.startswith("global_measures_")
        or reason.startswith("global_read_only_")
        or reason.startswith("global_mass_")
        for reason in reasons
    )
    passed = not reasons
    return {
        "passed": passed,
        "global_packet_set_closure_status": "passed" if passed else "failed",
        "canonical_identity_status": "passed" if passed else "failed",
        "canonical_physical_serialization_status": "passed" if physical_serialization_pass else "failed",
        "pre_map_identity_closure_status": "passed" if pre_map_identity_pass else "failed",
        "packet_row_count_total": sum(len(list(packet_rows.get(label, ()))) for label in PACKET_FILE_SPECS),
        "expected_packet_row_count_total": sum(EXPECTED_PACKET_ROW_COUNTS.values()),
        "failure_reasons": sorted(set(reasons)),
    }


def load_packet_maps(policy: Mapping[str, str] | None = None) -> dict[str, object]:
    raw = load_raw_packet_rows()
    policy = policy or load_support_policy()
    global_audit = validate_global_packet_set(raw, policy)
    if not global_audit["passed"]:
        raise ValueError(
            "global packet-set closure failed: " + ";".join(global_audit["failure_reasons"])
        )
    occurrences = strict_unique_map(raw["occurrences"], "form_id", "occurrence")
    accessors = strict_unique_map(raw["accessors"], "form_id", "accessor")
    measures = strict_unique_map(raw["measures"], "form_id", "measure")
    read_only = strict_unique_map(raw["read_only"], "form_id", "read_only")
    mass = strict_unique_map(raw["mass"], "form_id", "mass")
    return {
        "raw": raw,
        "global_audit": global_audit,
        "occurrences": occurrences,
        "accessors": accessors,
        "registries": raw["registries"],
        "measures": measures,
        "enumeration": raw["enumeration"],
        "read_only": read_only,
        "mass": mass,
        "inverse_domain": raw["inverse_domain"][0],
        "inverse": raw["inverse"],
    }


def evaluate_with_packet(
    *,
    policy: Mapping[str, str],
    source: Mapping[str, str],
    occurrence: Mapping[str, str],
    accessor: Mapping[str, str],
    registry_rows: Sequence[Mapping[str, str]],
    measure_contract: Mapping[str, str],
    enumeration_rows: Sequence[Mapping[str, str]],
    read_only_packet: Mapping[str, str],
    support_mass: Mapping[str, str],
    inverse_domain: Mapping[str, str],
    inverse_rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    return evaluate_form_state(
        policy=policy,
        occurrence=occurrence,
        accessor=accessor,
        source=source,
        registry_rows=registry_rows,
        measure_contract=measure_contract,
        enumeration_rows=enumeration_rows,
        read_only_packet=read_only_packet,
        support_mass=support_mass,
        inverse_domain=inverse_domain,
        inverse_rows=inverse_rows,
    )


def evaluate_gate(pre_manifest: Path) -> dict[str, Path]:
    verify_pre_audit_freeze(pre_manifest)
    source_rows = parse_main_source_rows()
    policy = load_support_policy()
    packet_maps = load_packet_maps(policy)

    occurrences = packet_maps["occurrences"]
    accessors = packet_maps["accessors"]
    registries = packet_maps["registries"]
    measures = packet_maps["measures"]
    enumeration_all = packet_maps["enumeration"]
    read_only_map = packet_maps["read_only"]
    mass_map = packet_maps["mass"]
    inverse_domain = packet_maps["inverse_domain"]
    inverse_all = packet_maps["inverse"]
    raw_packet_rows = packet_maps["raw"]
    global_audit = packet_maps["global_audit"]

    compatibility_rows: list[dict[str, str]] = []
    binding_rows: list[dict[str, str]] = []
    flow_rows: list[dict[str, str]] = []
    counterfactual_rows: list[dict[str, str]] = []
    global_audit_rows: list[dict[str, str]] = [
        attach(
            {
                "global_packet_set_audit_id": f"{GATE_ID}_global_packet_set_closure",
                "expected_form_ids": ";".join(EXPECTED_FORM_IDS),
                "expected_route_forms": ";".join(EXPECTED_ROUTE_FORMS),
                "expected_occurrence_rows": EXPECTED_PACKET_ROW_COUNTS["occurrences"],
                "expected_accessor_rows": EXPECTED_PACKET_ROW_COUNTS["accessors"],
                "expected_registry_rows": EXPECTED_PACKET_ROW_COUNTS["registries"],
                "expected_measure_rows": EXPECTED_PACKET_ROW_COUNTS["measures"],
                "expected_enumeration_rows": EXPECTED_PACKET_ROW_COUNTS["enumeration"],
                "expected_read_only_rows": EXPECTED_PACKET_ROW_COUNTS["read_only"],
                "expected_mass_rows": EXPECTED_PACKET_ROW_COUNTS["mass"],
                "expected_inverse_domain_rows": EXPECTED_PACKET_ROW_COUNTS["inverse_domain"],
                "expected_inverse_rows": EXPECTED_PACKET_ROW_COUNTS["inverse"],
                "observed_packet_row_count_total": global_audit["packet_row_count_total"],
                "expected_packet_row_count_total": global_audit["expected_packet_row_count_total"],
                "unique_key_policy": "reject_duplicates_before_dictionary_construction",
                "foreign_row_policy": "reject_before_form_filtering",
                "global_enumeration_index_policy": "physical_sequence_exactly_0_through_97",
                "canonical_physical_serialization_policy": "form_3_3_6_block_then_form_3_4_6_block_with_canonical_member_order",
                "global_packet_set_closure_status": global_audit["global_packet_set_closure_status"],
                "canonical_identity_status": global_audit["canonical_identity_status"],
                "canonical_physical_serialization_status": global_audit["canonical_physical_serialization_status"],
                "pre_map_identity_closure_status": global_audit["pre_map_identity_closure_status"],
                "failure_reasons": ";".join(global_audit["failure_reasons"]),
            },
            "global_packet_set_audit_row_sha256",
        )
    ]

    # Global packet-set counterfactuals exercise duplicate/foreign row closure.
    global_counterfactuals: list[tuple[str, str, dict[str, list[dict[str, str]]], bool]] = []
    duplicate_occurrence = deepcopy(raw_packet_rows)
    duplicate_occurrence["occurrences"].append(deepcopy(duplicate_occurrence["occurrences"][0]))
    global_counterfactuals.append(("duplicate_occurrence_row", "global_packet_set_closure", duplicate_occurrence, False))

    duplicate_measure = deepcopy(raw_packet_rows)
    duplicate_measure["measures"].append(deepcopy(duplicate_measure["measures"][0]))
    global_counterfactuals.append(("duplicate_measure_packet", "global_packet_set_closure", duplicate_measure, False))

    unrelated_registry = deepcopy(raw_packet_rows)
    registry_row = unrelated_registry["registries"][0]
    unrelated_registry["registries"].append(
        mutate_attached(
            registry_row,
            "support_family_registry_row_sha256",
            {
                "form_id": "unrelated",
                "route_form": "unrelated",
                "support_family_id": "unrelated",
                "support_measure_id": "unrelated",
            },
        )
    )
    global_counterfactuals.append(("unrelated_registry_row", "global_packet_set_closure", unrelated_registry, False))

    unrelated_enumeration = deepcopy(raw_packet_rows)
    enumeration_row = unrelated_enumeration["enumeration"][0]
    unrelated_enumeration["enumeration"].append(
        mutate_attached(
            enumeration_row,
            "support_member_row_sha256",
            {
                "enumeration_row_index": str(EXPECTED_PACKET_ROW_COUNTS["enumeration"]),
                "support_member_order": "0",
                "form_id": "unrelated",
                "route_form": "unrelated",
                "support_family_id": "unrelated",
                "support_measure_id": "unrelated",
                "support_member_id": "unrelated_member",
            },
        )
    )
    global_counterfactuals.append(("unrelated_enumeration_row", "global_packet_set_closure", unrelated_enumeration, False))

    unexpected_inverse = deepcopy(raw_packet_rows)
    inverse_row = unexpected_inverse["inverse"][0]
    unexpected_inverse["inverse"].append(
        mutate_attached(
            inverse_row,
            "inverse_audit_row_sha256",
            {
                "form_id": "unrelated",
                "route_form": "unrelated",
                "solution_order": "0",
            },
        )
    )
    global_counterfactuals.append(("unexpected_inverse_row", "global_packet_set_closure", unexpected_inverse, False))

    swapped_blocks = deepcopy(raw_packet_rows)
    block_a = [row for row in swapped_blocks["enumeration"] if row.get("form_id") == EXPECTED_FORM_IDS[0]]
    block_b = [row for row in swapped_blocks["enumeration"] if row.get("form_id") == EXPECTED_FORM_IDS[1]]
    swapped_blocks["enumeration"] = block_b + block_a
    global_counterfactuals.append(("swapped_physical_form_blocks", "canonical_serialization", swapped_blocks, False))

    interleaved = deepcopy(raw_packet_rows)
    block_a = [row for row in interleaved["enumeration"] if row.get("form_id") == EXPECTED_FORM_IDS[0]]
    block_b = [row for row in interleaved["enumeration"] if row.get("form_id") == EXPECTED_FORM_IDS[1]]
    interleaved_rows: list[dict[str, str]] = []
    for left, right in itertools.zip_longest(block_a, block_b):
        if left is not None:
            interleaved_rows.append(left)
        if right is not None:
            interleaved_rows.append(right)
    interleaved["enumeration"] = interleaved_rows
    global_counterfactuals.append(("stable_cross_form_interleaving", "canonical_serialization", interleaved, False))

    adjacent_transposition = deepcopy(raw_packet_rows)
    adjacent_transposition["enumeration"][0], adjacent_transposition["enumeration"][1] = (
        adjacent_transposition["enumeration"][1],
        adjacent_transposition["enumeration"][0],
    )
    global_counterfactuals.append(("adjacent_physical_row_transposition", "canonical_serialization", adjacent_transposition, False))

    foreign_measure_identity = deepcopy(raw_packet_rows)
    foreign_measure_identity["measures"][0] = mutate_attached(
        foreign_measure_identity["measures"][0],
        "support_measure_sha256",
        {"support_measure_id": "foreign_measure_identity"},
    )
    global_counterfactuals.append(("foreign_measure_contract_identity", "pre_map_identity", foreign_measure_identity, False))

    foreign_read_only_identity = deepcopy(raw_packet_rows)
    foreign_read_only_identity["read_only"][0] = mutate_attached(
        foreign_read_only_identity["read_only"][0],
        "read_only_packet_row_sha256",
        {"support_family_id": "foreign_family_identity"},
    )
    global_counterfactuals.append(("foreign_read_only_family_identity", "pre_map_identity", foreign_read_only_identity, False))

    foreign_mass_identity = deepcopy(raw_packet_rows)
    foreign_mass_identity["mass"][0] = mutate_attached(
        foreign_mass_identity["mass"][0],
        "support_mass_audit_row_sha256",
        {"support_measure_id": "foreign_measure_identity"},
    )
    global_counterfactuals.append(("foreign_mass_measure_identity", "pre_map_identity", foreign_mass_identity, False))

    global_counterfactuals.append(("frozen_global_packet_set_unchanged", "control", deepcopy(raw_packet_rows), True))

    for order, (counter_id, mutation_class, mutated_rows, expected) in enumerate(global_counterfactuals):
        observed_audit = validate_global_packet_set(mutated_rows, policy)
        observed = bool(observed_audit["passed"])
        counterfactual_rows.append(
            attach(
                {
                    "counterfactual_order": order,
                    "counterfactual_id": f"global_{counter_id}",
                    "form_id": "global_packet_set",
                    "mutation_class": mutation_class,
                    "mutation_fields": counter_id if mutation_class != "control" else "none",
                    "original_packet_sha256": packet_digest(raw_packet_rows),
                    "mutated_packet_sha256": packet_digest(mutated_rows),
                    "packet_hash_change_status": "changed" if packet_digest(mutated_rows) != packet_digest(raw_packet_rows) else "unchanged",
                    "expected_compatibility": "passed" if expected else "failed",
                    "observed_compatibility": "passed" if observed else "failed",
                    "observed_failure_reasons": ";".join(observed_audit["failure_reasons"]),
                    "counterfactual_audit_status": "passed" if observed == expected else "failed",
                    "native_source_row_change_status": "unchanged_source_global_packet_counterfactual_only",
                },
                "counterfactual_row_sha256",
            )
        )

    form_ids = [str(specification["form_id"]) for specification in FORMS]
    for specification in FORMS:
        form_id = str(specification["form_id"])
        other_form_id = next(value for value in form_ids if value != form_id)
        occurrence = occurrences[form_id]
        accessor = accessors[form_id]
        registry_rows = [row for row in registries if row["form_id"] == form_id]
        measure_contract = measures[form_id]
        enumeration_rows = [row for row in enumeration_all if row["form_id"] == form_id]
        read_only_packet = read_only_map[form_id]
        support_mass = mass_map[form_id]
        inverse_rows = [row for row in inverse_all if row["form_id"] == form_id]
        source = source_rows[str(specification["route_form"])]

        packet = {
            "occurrence": occurrence,
            "accessor": accessor,
            "registry_rows": registry_rows,
            "measure_contract": measure_contract,
            "enumeration_rows": enumeration_rows,
            "read_only_packet": read_only_packet,
            "support_mass": support_mass,
            "inverse_domain": inverse_domain,
            "inverse_rows": inverse_rows,
        }
        evaluation = evaluate_with_packet(policy=policy, source=source, **packet)

        compatibility_rows.append(
            attach(
                {
                    "compatibility_gate_id": GATE_ID,
                    "form_id": form_id,
                    "route_form": specification["route_form"],
                    "primitive_support_id": occurrence["primitive_support_id"],
                    "support_policy_validation_mode": POLICY_VALIDATION_MODE,
                    "support_policy_semantic_status": "passed" if evaluation["policy_match"] else "failed",
                    "shared_outer_enclosure_status": "passed" if evaluation["policy_match"] else "failed",
                    "exact_accessor_consistency_status": "passed" if evaluation["accessor_pass"] else "failed",
                    "registry_binding_status": "passed" if evaluation["registry_pass"] else "failed",
                    "measure_contract_binding_status": "passed" if evaluation["measure_contract_pass"] else "failed",
                    "enumeration_completeness_status": "passed" if evaluation["enumeration_completeness_pass"] else "failed",
                    "read_only_binding_status": "passed" if evaluation["read_only_binding_pass"] else "failed",
                    "support_family_measure_status": "passed" if evaluation["support_measure_pass"] else "failed",
                    "inverse_audit_status": "passed" if evaluation["inverse_audit_pass"] else "failed",
                    "canonical_identity_status": "passed" if evaluation["canonical_identity_pass"] else "failed",
                    "canonical_enumeration_mapping_status": "passed" if evaluation["canonical_enumeration_mapping_pass"] else "failed",
                    "closed_semantics_binding_status": "passed" if evaluation["closed_semantics_binding_pass"] else "failed",
                    "cross_packet_binding_status": "passed" if evaluation["cross_packet_binding_pass"] else "failed",
                    "declared_form_solution_membership_status": "passed" if evaluation["declared_in_domain"] else "failed",
                    "compatibility_status": "passed" if evaluation["passed"] else "failed",
                    "compatibility_failure_reasons": ";".join(evaluation["failure_reasons"]),
                    "compatibility_claim": "same_C6_outer_enclosure_exact_accessor_and_fully_bound_support_family_consistency_only",
                    "support_family_status": "materialized_non_temporal",
                    "local_DEC_execution_status": "not_materialized",
                    "recurrence_equivalence_status": "not_evaluated",
                    "temporal_equivalence_status": "not_evaluated",
                    "SADAR_cadence_equivalence_status": "not_evaluated",
                    "monon_to_bip_conversion_status": "not_declared",
                    "target_value_read_status": "not_read",
                    "empirical_score_status": "not_computed",
                },
                "compatibility_row_sha256",
            )
        )
        binding_rows.append(
            attach(
                {
                    "binding_audit_id": f"{form_id}_cross_packet_binding_audit",
                    "form_id": form_id,
                    "route_form": specification["route_form"],
                    "expected_support_family_id": evaluation.get("expected_support_family_id", ""),
                    "expected_support_measure_id": evaluation.get("expected_support_measure_id", ""),
                    "expected_walk_history_count": evaluation.get("expected_walk_count", ""),
                    "expected_retained_support_shell_count": evaluation.get("expected_support_shell_count", ""),
                    "expected_support_member_count": evaluation.get("expected_support_member_count", ""),
                    "registry_binding_status": "passed" if evaluation["registry_pass"] else "failed",
                    "measure_binding_status": "passed" if evaluation["measure_contract_pass"] else "failed",
                    "enumeration_completeness_status": "passed" if evaluation["enumeration_completeness_pass"] else "failed",
                    "read_only_binding_status": "passed" if evaluation["read_only_binding_pass"] else "failed",
                    "mass_recomputation_status": "passed" if evaluation["support_measure_pass"] else "failed",
                    "inverse_binding_status": "passed" if evaluation["inverse_audit_pass"] else "failed",
                    "canonical_identity_status": "passed" if evaluation["canonical_identity_pass"] else "failed",
                    "canonical_enumeration_mapping_status": "passed" if evaluation["canonical_enumeration_mapping_pass"] else "failed",
                    "closed_semantics_binding_status": "passed" if evaluation["closed_semantics_binding_pass"] else "failed",
                    "global_packet_set_closure_status": global_audit["global_packet_set_closure_status"],
                    "cross_packet_binding_status": "passed" if evaluation["cross_packet_binding_pass"] else "failed",
                    "failure_reasons": ";".join(evaluation["failure_reasons"]),
                },
                "binding_audit_row_sha256",
            )
        )
        flow_rows.append(
            attach(
                {
                    "flow_admission_id": f"{form_id}_future_relational_flow_admission",
                    "form_id": form_id,
                    "route_form": specification["route_form"],
                    "compatibility_gate_id": GATE_ID,
                    "support_family_enumeration_status": "materialized_exact_non_temporal",
                    "cross_packet_binding_status": "passed" if evaluation["cross_packet_binding_pass"] else "failed",
                    "local_DEC_execution_status": "not_materialized",
                    "returned_current_detection_status": "not_materialized",
                    "RD_distribution_status": "not_materialized_for_occurrence_flow",
                    "RCD_packet_status": "not_materialized",
                    "duon_pressure_packet_status": "not_materialized",
                    "subject_SADAR_packet_status": "not_materialized",
                    "reference_SADAR_packet_status": "not_materialized",
                    "primitive_phase_lock_status": "not_materialized",
                    "temporal_report_status": "not_materialized",
                    "admission_status": "admitted_as_support_accessor_contract_local_DEC_pending" if evaluation["passed"] else "blocked",
                    "hydrogen_gate_status": "blocked_until_connected_local_Q4_DEC_is_materialized",
                    "target_value_read_status": "not_read",
                },
                "flow_admission_row_sha256",
            )
        )

        # Counterfactual packets are separately rehashed and passed through the
        # same evaluator.  The control must pass; every mutation must fail.
        counterfactuals: list[tuple[str, str, dict[str, object], bool]] = []
        counterfactuals.append(("outer_L_change_to_8", "outer_enclosure", {"occurrence": mutate_attached(occurrence, "occurrence_row_sha256", {"declared_L": "8", "outer_enclosure_id": "C8"})}, False))
        counterfactuals.append(("PD_increment_by_1", "exact_accessor", {"accessor": mutate_attached(accessor, "accessor_audit_row_sha256", {"PD": str(int(accessor["PD"]) + 1)})}, False))
        counterfactuals.append(("QD_increment_by_1", "exact_accessor", {"accessor": mutate_attached(accessor, "accessor_audit_row_sha256", {"QD": str(int(accessor["QD"]) + 1)})}, False))
        counterfactuals.append(("swap_support_mass_packet", "cross_packet_identity", {"support_mass": mass_map[other_form_id]}, False))
        counterfactuals.append(("unrelated_mass_identity", "cross_packet_identity", {"support_mass": mutate_attached(support_mass, "support_mass_audit_row_sha256", {"form_id": "unrelated", "support_family_id": "unrelated"})}, False))
        counterfactuals.append(("missing_enumeration_member", "enumeration_completeness", {"enumeration_rows": enumeration_rows[:-1]}, False))
        counterfactuals.append(("occurrence_local_DEC_materialized", "closed_semantics", {"occurrence": mutate_attached(occurrence, "occurrence_row_sha256", {"local_DEC_status": "materialized"})}, False))
        counterfactuals.append(("occurrence_target_input_present", "closed_semantics", {"occurrence": mutate_attached(occurrence, "occurrence_row_sha256", {"target_value_input_status": "present"})}, False))
        counterfactuals.append(("occurrence_source_row_hash_changed", "source_binding", {"occurrence": mutate_attached(occurrence, "occurrence_row_sha256", {"source_row_text_sha256": "0" * 64})}, False))
        counterfactuals.append(("accessor_recurrence_closure_relabel", "closed_semantics", {"accessor": mutate_attached(accessor, "accessor_audit_row_sha256", {"capacity_residual_semantics": "recurrence_closure_certificate"})}, False))
        counterfactuals.append(("accessor_temporal_inference_admitted", "closed_semantics", {"accessor": mutate_attached(accessor, "accessor_audit_row_sha256", {"temporal_inference_status": "admitted"})}, False))
        counterfactuals.append(("accessor_target_input_present", "closed_semantics", {"accessor": mutate_attached(accessor, "accessor_audit_row_sha256", {"target_value_input_status": "present"})}, False))
        counterfactuals.append(("read_only_conservation_failed", "closed_semantics", {"read_only_packet": mutate_attached(read_only_packet, "read_only_packet_row_sha256", {"support_measure_conservation_status": "failed"})}, False))
        counterfactuals.append(("read_only_local_DEC_materialized", "closed_semantics", {"read_only_packet": mutate_attached(read_only_packet, "read_only_packet_row_sha256", {"local_DEC_trace_status": "materialized"})}, False))
        counterfactuals.append(("read_only_target_read", "closed_semantics", {"read_only_packet": mutate_attached(read_only_packet, "read_only_packet_row_sha256", {"target_value_read_status": "read"})}, False))
        counterfactuals.append(("inverse_domain_identity_policy_changed", "closed_semantics", {"inverse_domain": mutate_attached(inverse_domain, "inverse_domain_row_sha256", {"identity_use_policy": "replace_declared_occurrence"})}, False))
        counterfactuals.append(("inverse_domain_target_input_present", "closed_semantics", {"inverse_domain": mutate_attached(inverse_domain, "inverse_domain_row_sha256", {"target_value_input_status": "present"})}, False))
        mutated_inverse = [deepcopy(row) for row in inverse_rows]
        mutated_inverse[0] = mutate_attached(mutated_inverse[0], "inverse_audit_row_sha256", {"Pi_alpha": "999", "form_id": "unrelated"})
        counterfactuals.append(("inverse_identity_and_Pi_mutation", "inverse_binding", {"inverse_rows": mutated_inverse}, False))
        counterfactuals.append(("frozen_packet_unchanged", "control", {}, True))

        for order, (counter_id, mutation_class, overrides, expected) in enumerate(counterfactuals):
            mutated_packet = deepcopy(packet)
            mutated_packet.update(overrides)
            observed_eval = evaluate_with_packet(policy=policy, source=source, **mutated_packet)
            observed = bool(observed_eval["passed"])
            counterfactual_rows.append(
                attach(
                    {
                        "counterfactual_order": order,
                        "counterfactual_id": f"{form_id}_{counter_id}",
                        "form_id": form_id,
                        "mutation_class": mutation_class,
                        "mutation_fields": ";".join(sorted(overrides)) if overrides else "none",
                        "original_packet_sha256": packet_digest(packet),
                        "mutated_packet_sha256": packet_digest(mutated_packet),
                        "packet_hash_change_status": "changed" if packet_digest(mutated_packet) != packet_digest(packet) else "unchanged",
                        "expected_compatibility": "passed" if expected else "failed",
                        "observed_compatibility": "passed" if observed else "failed",
                        "observed_failure_reasons": ";".join(observed_eval["failure_reasons"]),
                        "counterfactual_audit_status": "passed" if observed == expected else "failed",
                        "native_source_row_change_status": "unchanged_source_counterfactual_packet_only",
                    },
                    "counterfactual_row_sha256",
                )
            )

    outputs: dict[str, Path] = {}
    for name, rows in (
        ("consequent_six_slot_global_packet_set_closure_audit.csv", global_audit_rows),
        ("consequent_six_slot_compatibility_audit.csv", compatibility_rows),
        ("consequent_six_slot_cross_packet_binding_audit.csv", binding_rows),
        ("consequent_six_slot_relational_flow_admission.csv", flow_rows),
        ("consequent_six_slot_counterfactual_audit.csv", counterfactual_rows),
    ):
        path = DATA / name
        write_csv(path, list(rows[0]), rows)
        outputs[name] = path
    return outputs


def derive_gate_statuses(
    compatibility_rows: Sequence[Mapping[str, str]],
    counterfactual_rows: Sequence[Mapping[str, str]],
    global_audit_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    native_pass = bool(compatibility_rows) and all(row.get("compatibility_status") == "passed" for row in compatibility_rows)
    binding_pass = bool(compatibility_rows) and all(row.get("cross_packet_binding_status") == "passed" for row in compatibility_rows)
    enumeration_pass = bool(compatibility_rows) and all(row.get("enumeration_completeness_status") == "passed" for row in compatibility_rows)
    inverse_pass = bool(compatibility_rows) and all(row.get("inverse_audit_status") == "passed" for row in compatibility_rows)
    canonical_identity_pass = bool(compatibility_rows) and all(row.get("canonical_identity_status") == "passed" for row in compatibility_rows)
    canonical_mapping_pass = bool(compatibility_rows) and all(row.get("canonical_enumeration_mapping_status") == "passed" for row in compatibility_rows)
    closed_semantics_pass = bool(compatibility_rows) and all(row.get("closed_semantics_binding_status") == "passed" for row in compatibility_rows)
    global_packet_set_pass = bool(global_audit_rows) and all(row.get("global_packet_set_closure_status") == "passed" for row in global_audit_rows)
    physical_serialization_pass = bool(global_audit_rows) and all(row.get("canonical_physical_serialization_status") == "passed" for row in global_audit_rows)
    pre_map_identity_pass = bool(global_audit_rows) and all(row.get("pre_map_identity_closure_status") == "passed" for row in global_audit_rows)
    counterfactual_pass = bool(counterfactual_rows) and all(row.get("counterfactual_audit_status") == "passed" for row in counterfactual_rows)
    overall = all((native_pass, binding_pass, enumeration_pass, inverse_pass, canonical_identity_pass, canonical_mapping_pass, closed_semantics_pass, global_packet_set_pass, physical_serialization_pass, pre_map_identity_pass, counterfactual_pass))
    return {
        "native_compatibility_status": "passed" if native_pass else "failed",
        "cross_packet_binding_status": "passed" if binding_pass else "failed",
        "enumeration_completeness_status": "passed" if enumeration_pass else "failed",
        "canonical_identity_status": "passed" if canonical_identity_pass else "failed",
        "canonical_enumeration_mapping_status": "passed" if canonical_mapping_pass else "failed",
        "closed_semantics_binding_status": "passed" if closed_semantics_pass else "failed",
        "global_packet_set_closure_status": "passed" if global_packet_set_pass else "failed",
        "canonical_physical_serialization_status": "passed" if physical_serialization_pass else "failed",
        "pre_map_identity_closure_status": "passed" if pre_map_identity_pass else "failed",
        "inverse_audit_status": "passed" if inverse_pass else "failed",
        "counterfactual_status": "passed" if counterfactual_pass else "failed",
        "overall_gate_status": "passed" if overall else "failed",
    }


def build_gate_manifest(pre_manifest: Path) -> Path:
    files: list[dict[str, object]] = []
    for path in sorted(DATA.glob("consequent_six_slot_*")):
        if path.name == "consequent_six_slot_gate_manifest.json":
            continue
        files.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha_file(path)})
    compatibility = read_csv(DATA / "consequent_six_slot_compatibility_audit.csv")
    counterfactual = read_csv(DATA / "consequent_six_slot_counterfactual_audit.csv")
    global_audit = read_csv(DATA / "consequent_six_slot_global_packet_set_closure_audit.csv")
    statuses = derive_gate_statuses(compatibility, counterfactual, global_audit)
    manifest = {
        "manifest_id": "aod_consequent_six_slot_form_compatibility_manifest_v5",
        "version_scope": VERSION,
        "gate_id": GATE_ID,
        "primitive_support_id": load_support_policy()["primitive_support_id"],
        "support_policy_validation_mode": POLICY_VALIDATION_MODE,
        "forms": [form["route_form"] for form in FORMS],
        "compatibility_status": statuses["overall_gate_status"],
        **statuses,
        "claim_scope": "same_C6_outer_enclosure_exact_accessor_and_fully_bound_support_family_consistency_only",
        "support_family_definition": "F_pq=D_q^p_disjoint_union_S_q",
        "support_family_status": "materialized_non_temporal",
        "local_DEC_execution_status": "not_materialized",
        "recurrence_equivalence_status": "not_evaluated",
        "temporal_measurement_status": "not_materialized",
        "target_value_read_status": "not_read",
        "empirical_score_status": "not_computed",
        "pre_audit_freeze_manifest": pre_manifest.relative_to(ROOT).as_posix(),
        "pre_audit_freeze_manifest_sha256": sha_file(pre_manifest),
        "files": files,
    }
    path = DATA / "consequent_six_slot_gate_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def assert_gate_pass(manifest: Mapping[str, object]) -> None:
    required = (
        "native_compatibility_status",
        "counterfactual_status",
        "cross_packet_binding_status",
        "enumeration_completeness_status",
        "canonical_identity_status",
        "canonical_enumeration_mapping_status",
        "closed_semantics_binding_status",
        "global_packet_set_closure_status",
        "canonical_physical_serialization_status",
        "pre_map_identity_closure_status",
        "inverse_audit_status",
        "overall_gate_status",
    )
    failed = [field for field in required if manifest.get(field) != "passed"]
    if failed:
        raise SystemExit("compatibility gate failed: " + ",".join(failed))


def main() -> None:
    stage_outputs = write_stage_files()
    pre_manifest = build_pre_audit_manifest(stage_outputs)
    evaluate_gate(pre_manifest)
    manifest_path = build_gate_manifest(pre_manifest)
    verify_pre_audit_freeze(pre_manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert_gate_pass(manifest)


if __name__ == "__main__":
    main()
