#!/usr/bin/env python3
"""Exact integer collision-vertex examples for Appendix D."""
from __future__ import annotations

import csv
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SCRIPT_DIR.parent
RAW_PATH = MANUAL_DIR / "data" / "raw" / "05i_duon_collision_setup.json"
EXACT_CSV = MANUAL_DIR / "data" / "derived" / "05i_duon_collision_exact.csv"
TRACE_CSV = MANUAL_DIR / "data" / "derived" / "05i_duon_collision_trace.csv"
FIGURE_PATH = MANUAL_DIR / "figures" / "collision" / "01_integer_collision_outcomes.png"
BALANCED_VALUES = {-1, 0, 1}


def load_setup(path: Path = RAW_PATH) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def balanced_ternary_add(a: int, b: int) -> int:
    if a not in BALANCED_VALUES or b not in BALANCED_VALUES:
        raise ValueError("balanced ternary signs must lie in {-1,0,+1}")
    residue = (a + b) % 3
    return {-1: -1, 0: 0, 1: 1, 2: -1}[residue]


def centered_mod(value: int, modulus: int) -> int:
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    wrapped = value % modulus
    if wrapped > modulus // 2:
        wrapped -= modulus
    return wrapped


def outcome(c: int, q_sum: int, k_sum_centered: int, chi_product: int, incidence: int) -> str:
    if incidence == 0:
        return "rupture/refinement"
    if c == 0 and q_sum == 0 and k_sum_centered == 0:
        return "balanced"
    if k_sum_centered == 0 and chi_product < 0:
        return "reclosure"
    if q_sum > 0:
        return "push"
    if q_sum < 0:
        return "pull"
    return "export"


def rows(setup: dict | None = None) -> list[dict[str, object]]:
    setup = load_setup() if setup is None else setup
    N = int(setup["N"])
    out: list[dict[str, object]] = []
    for row in setup["examples"]:
        a = int(row["a"])
        b = int(row["b"])
        c = balanced_ternary_add(a, b)
        q_sum = int(row["Q_a"]) + int(row["Q_b"])
        k_sum = (int(row["K_a"]) + int(row["K_b"])) % N
        k_centered = centered_mod(k_sum, N)
        chi_product = int(row["chi_a"]) * int(row["chi_b"])
        incidence = int(row["incidence"])
        out.append({
            "row_id": row["row_id"],
            "a": a,
            "b": b,
            "c": c,
            "Q_sum": q_sum,
            "K_sum_mod_N": k_sum,
            "K_sum_centered": k_centered,
            "N": N,
            "chi_product": chi_product,
            "incidence": incidence,
            "outcome": outcome(c, q_sum, k_centered, chi_product, incidence),
        })
    return out


def write_csv(records: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def write_trace(records: list[dict[str, object]], path: Path = TRACE_CSV) -> None:
    trace = []
    for row in records:
        trace.append({
            "row_id": row["row_id"],
            "ternary_identity": f"{row['a']} oplus_3 {row['b']} = {row['c']}",
            "integer_predicates": f"Q_sum={row['Q_sum']}; K_sum_mod_N={row['K_sum_mod_N']}; chi_product={row['chi_product']}; incidence={row['incidence']}",
            "outcome": row["outcome"],
        })
    write_csv(trace, path)


def write_figure(records: list[dict[str, object]], path: Path = FIGURE_PATH) -> None:
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    outcomes = sorted({str(r["outcome"]) for r in records})
    counts = [sum(1 for r in records if r["outcome"] == o) for o in outcomes]
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    x = list(range(len(outcomes)))
    ax.bar(x, counts)
    ax.set_xticks(x)
    ax.set_xticklabels(outcomes, rotation=20, ha="right")
    ax.set_ylabel("example count")
    ax.set_title("Integer collision-vertex outcome examples")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> int:
    records = rows()
    write_csv(records, EXACT_CSV)
    write_trace(records)
    write_figure(records)
    print(EXACT_CSV)
    print(TRACE_CSV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
