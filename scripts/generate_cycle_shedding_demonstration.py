#!/usr/bin/env python3
"""Render the cycle-shedding demonstration from its exact update rows."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "wavelet_shedding_simulation.csv"
OUTPUT = ROOT / "figures_jpg" / "cycle_disturbance_shedding_simulation.png"


def read_rows() -> list[dict[str, str]]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def values(rows: list[dict[str, str]], key: str) -> list[float]:
    return [float(row[key]) for row in rows]


def main() -> None:
    rows = read_rows()
    update = [int(row["update_index"]) for row in rows]

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    fig.suptitle("Demonstration run: temporal-cycle disturbance shedding", fontsize=18)

    axes[0].plot(update, values(rows, "lead"), label="lead component")
    axes[0].plot(update, values(rows, "lag"), label="lag component")
    axes[0].set_ylabel("component")
    axes[0].legend(loc="upper right")

    axes[1].plot(update, values(rows, "span"), label="lead-lag span")
    axes[1].plot(update, values(rows, "padar_burden"), label="temporal SADAR burden P_t")
    axes[1].plot(update, values(rows, "compatibility"), "--", color="green", label="closure compatibility")
    axes[1].set_ylabel("burden")
    axes[1].legend(loc="upper right")

    outward = values(rows, "outward_shedding")
    reclosure = values(rows, "local_reclosure")
    axes[2].bar(update, outward, label="exoshedding")
    axes[2].bar(update, reclosure, bottom=outward, label="local reclosure")
    axes[2].set_ylabel("sheddic excess")
    axes[2].set_xlabel("update index")
    axes[2].legend(loc="upper right")

    for axis in axes:
        axis.grid(alpha=0.25)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUTPUT, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
