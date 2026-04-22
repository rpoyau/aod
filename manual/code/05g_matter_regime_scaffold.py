#!/usr/bin/env python3
"""Phase IV matter-regime scaffold rows.

The rows remain integer/rational/cycle/topology-facing classification data.  They
are not external-sector benchmarks and do not validate a material model.
"""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SCRIPT_DIR.parent
RAW_PATH = MANUAL_DIR / "data" / "raw" / "05g_matter_regime_setup.json"
DERIVED_PATH = MANUAL_DIR / "data" / "derived" / "05g_matter_regime_scaffold.csv"
FIGURE_PATH = MANUAL_DIR / "figures" / "matter" / "01_matter_transport_scaffold.png"


def load_setup(path: Path = RAW_PATH) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def rat(num: int, den: int) -> Fraction:
    if den <= 0:
        raise ValueError(f"denominator must be positive, got {den}")
    return Fraction(num, den)


def rows(setup: dict | None = None) -> list[dict[str, object]]:
    setup = load_setup() if setup is None else setup
    out: list[dict[str, object]] = []
    for row in setup["regimes"]:
        q_eff = rat(int(row["Q"]), int(row["S"])) if int(row["Q"]) != 0 else Fraction(0, 1)
        torsion = rat(int(row["torsion_num"]), int(row["torsion_den"]))
        persistence = rat(int(row["persistence_num"]), int(row["persistence_den"]))
        transport_balance = rat(int(row["mobility_count"]) - int(row["reclosure_count"]), int(setup["window_bip_0"]))
        out.append({
            "row_id": row["row_id"],
            "regime": row["regime"],
            "retained_field": row["retained_field"],
            "dominant_variables": row["dominant_variables"],
            "carrier_family": row["carrier_family"],
            "mobility_count": int(row["mobility_count"]),
            "reclosure_count": int(row["reclosure_count"]),
            "q_eff_num": q_eff.numerator,
            "q_eff_den": q_eff.denominator,
            "torsion_num": torsion.numerator,
            "torsion_den": torsion.denominator,
            "persistence_num": persistence.numerator,
            "persistence_den": persistence.denominator,
            "transport_balance_num": transport_balance.numerator,
            "transport_balance_den": transport_balance.denominator,
            "status": row["status"],
        })
    return out


def write_csv(records: list[dict[str, object]], path: Path = DERIVED_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def write_figure(records: list[dict[str, object]], path: Path = FIGURE_PATH) -> None:
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    names = [str(r["regime"]) for r in records]
    mobility = [int(r["mobility_count"]) for r in records]
    reclosure = [int(r["reclosure_count"]) for r in records]
    x = list(range(len(records)))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.bar([i - width / 2 for i in x], mobility, width, label="mobility count")
    ax.bar([i + width / 2 for i in x], reclosure, width, label="reclosure count")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_ylabel("integer count")
    ax.set_title("Matter-regime scaffold counts")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> int:
    records = rows()
    write_csv(records)
    write_figure(records)
    print(DERIVED_PATH)
    print(FIGURE_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
