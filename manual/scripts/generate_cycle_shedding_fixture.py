#!/usr/bin/env python3
"""Validate and plot the retained 90-tick cycle-shedding CSV fixture.

The figure displays supplied CSV values; it does not regenerate lead/lag inputs
or infer a certified return from the model's local-reclosure fraction.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "wavelet_shedding_simulation.csv"
SUMMARY_PATH = ROOT / "cycle_shedding_summary.tex"
OUT_PATH = ROOT / "figures_jpg" / "cycle_disturbance_shedding_fixture.png"
ETA, GAMMA, LAMBDA = 41 / 50, 11 / 20, 19 / 50
TOLERANCE = 1e-12
NUMERIC_FIELDS = (
    "lead", "lag", "span", "compatibility", "padar_burden",
    "shed_excess", "outward_shedding", "local_reclosure",
)
FIELDS = ("tick", *NUMERIC_FIELDS, "state")


def require_close(actual: float, expected: float, name: str, tick: int) -> None:
    if not math.isclose(actual, expected, rel_tol=TOLERANCE, abs_tol=TOLERANCE):
        raise ValueError(f"tick {tick}: {name} is {actual!r}, expected {expected!r}")


def load_fixture(path: Path, summary_path: Path) -> tuple[list[dict], dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"CSV columns must be {FIELDS!r}")
        raw_rows = list(reader)
    if len(raw_rows) != 90:
        raise ValueError("the retained fixture requires exactly 90 rows")

    rows = []
    previous_burden = 0.0
    for tick, raw in enumerate(raw_rows):
        if tuple(raw) != FIELDS or any(value is None for value in raw.values()):
            raise ValueError(f"row {tick}: missing or extra CSV cell")
        if raw["tick"] != str(tick):
            raise ValueError("ticks must occur exactly once, in order from 0 through 89")
        row = {field: float(raw[field]) for field in NUMERIC_FIELDS}
        row.update(tick=tick, state=raw["state"])
        if not all(math.isfinite(row[field]) for field in NUMERIC_FIELDS):
            raise ValueError(f"tick {tick}: non-finite numeric input")
        for field in NUMERIC_FIELDS[2:]:
            if row[field] < 0:
                raise ValueError(f"tick {tick}: {field} must be nonnegative")
        if row["state"] != "open":
            raise ValueError(f"tick {tick}: the retained fixture's state must be open")
        span = abs(row["lead"] - row["lag"])
        before_clipping = ETA * previous_burden + GAMMA * span
        excess = max(0.0, before_clipping - row["compatibility"])
        burden = before_clipping - excess
        require_close(row["span"], span, "span", tick)
        require_close(row["shed_excess"], excess, "sheddic excess", tick)
        require_close(row["padar_burden"], burden, "post-clipping burden", tick)
        if row["padar_burden"] > row["compatibility"] + TOLERANCE:
            raise ValueError(f"tick {tick}: post-clipping burden exceeds compatibility")
        require_close(row["outward_shedding"], (1 - LAMBDA) * excess, "outward remainder", tick)
        require_close(row["local_reclosure"], LAMBDA * excess, "local-reclosure fraction", tick)
        require_close(row["outward_shedding"] + row["local_reclosure"], excess, "remainder sum", tick)
        previous_burden = row["padar_burden"]
        rows.append(row)

    metrics = {
        "ticks": len(rows),
        "maximum_span": max(row["span"] for row in rows),
        "maximum_burden": max(row["padar_burden"] for row in rows),
        "maximum_excess": max(row["shed_excess"] for row in rows),
        "total_outward": math.fsum(row["outward_shedding"] for row in rows),
        "total_local": math.fsum(row["local_reclosure"] for row in rows),
        "state_counts": {"open": len(rows)},
    }
    expected_summary = {
        "Ticks": str(metrics["ticks"]),
        "Maximum lead-lag span": f'{metrics["maximum_span"]:.3f}',
        "Maximum temporal SADAR burden": f'{metrics["maximum_burden"]:.3f}',
        "Maximum sheddic excess": f'{metrics["maximum_excess"]:.3f}',
        "Total exoshedding": f'{metrics["total_outward"]:.3f}',
        "Total local reclosure": f'{metrics["total_local"]:.3f}',
        "Sheddic path trigger ticks": "0",
        "First reclosure tick": "none",
    }
    summary = summary_path.read_text(encoding="utf-8")
    for label, value in expected_summary.items():
        recorded = re.findall(rf"(?m)^{re.escape(label)}\s*&\s*([^\\\n]+)\\\\\s*$", summary)
        if [item.strip() for item in recorded] != [value]:
            raise ValueError(f"summary {label!r} must occur once with value {value!r}")
    metrics["summary_values"] = expected_summary
    return rows, metrics


def plot_fixture(rows: list[dict], output: Path) -> None:
    # Keep plotting caches outside the manuscript and avoid an unwritable home.
    with tempfile.TemporaryDirectory(prefix="aod-cycle-mpl-") as config_dir:
        os.environ.setdefault("MPLCONFIGDIR", config_dir)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11,
                             "axes.spines.top": False, "axes.spines.right": False}):
            ticks = [row["tick"] for row in rows]
            values = lambda field: [row[field] for row in rows]
            fig, axes = plt.subplots(3, 1, figsize=(9.5, 7.1), sharex=True,
                                     layout="constrained")
            axes[0].plot(ticks, values("lead"), label=r"Lead $L_t$", color="#0072b2", linewidth=1.7)
            axes[0].plot(ticks, values("lag"), label=r"Lag $G_t$", color="#d55e00", linewidth=1.7)
            axes[0].set_ylabel("Component")
            axes[0].set_title("Retained cycle-shedding fixture: 90 native ticks", fontsize=12)
            axes[0].legend(loc="upper right", ncol=2, frameon=False, fontsize=10)

            axes[1].plot(ticks, values("span"), label=r"Span $S_t$", color="#0072b2", linewidth=1.5)
            axes[1].plot(ticks, values("padar_burden"), label=r"Post-clipping burden $P_t$", color="#d55e00", linewidth=1.7)
            axes[1].plot(ticks, values("compatibility"), label=r"Compatibility $C_t$", color="#009e73", linestyle="--", linewidth=1.7)
            axes[1].set_ylabel("Span / burden")
            axes[1].set_ylim(bottom=0)
            axes[1].legend(loc="lower left", bbox_to_anchor=(0, 1.01),
                           ncol=3, frameon=False, fontsize=9.5)

            axes[2].stackplot(ticks, values("outward_shedding"), values("local_reclosure"),
                              labels=(r"Outward remainder $O_t$", r"Local fraction $R_t$"),
                              colors=("#56b4e9", "#e69f00"), alpha=0.85)
            axes[2].plot(ticks, values("shed_excess"), color="#222222", linewidth=1.2,
                         label=r"Excess $X_t=O_t+R_t$")
            axes[2].set_ylabel("Sheddic excess")
            axes[2].set_ylim(bottom=0)
            axes[2].set_xlabel(r"Native tick $t$")
            axes[2].legend(loc="upper right", frameon=False, fontsize=10)
            for axis in axes:
                axis.set_xlim(0, 89)
                axis.grid(axis="y", color="#d8d8d8", linewidth=0.6, alpha=0.7)
            output.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output, dpi=180, metadata={"Software": "AOD retained cycle-shedding fixture"})
            plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--output", type=Path, default=OUT_PATH)
    parser.add_argument("--check-data", action="store_true", help="validate without writing a figure")
    args = parser.parse_args()
    try:
        rows, metrics = load_fixture(args.csv, args.summary)
        if not args.check_data:
            plot_fixture(rows, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
