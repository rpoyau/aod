#!/usr/bin/env python3
"""Generate the K4 3D + time-flow input-gate figure.

Public labels use singular/plural field counts:
  1 field, 2 fields, ...
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "manual" / "data" / "lensing" / "k4_3d_timeflow_input_gate.csv"
OUT_PATH = ROOT / "manual" / "figures" / "lensing" / "07_k4_3d_timeflow_input_gate.png"

BLUE = "#1f4e79"
LIGHT = "#e6eef5"
EDGE = "#4d4d4d"
TEXT = "#111111"


def count_label(n: int) -> str:
    return "1 field" if n == 1 else f"{n} fields"


def load_counts(path: Path) -> list[tuple[str, int]]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    counts = Counter(row["input_group"] for row in rows)
    # Keep the established display order from the prior figure.
    order = [
        "3D density fields",
        "audit controls",
        "lensing target side",
        "momentum fields",
        "time-window state",
        "velocity and flow fields",
    ]
    return [(name, counts[name]) for name in order if counts[name]]


def main() -> None:
    items = load_counts(CSV_PATH)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 6), dpi=144)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(
        5,
        9.45,
        "K4 3D + time-flow input gate",
        ha="center",
        va="center",
        fontsize=18,
        color=BLUE,
    )

    y = 8.45
    row_h = 0.70
    gap = 0.36
    x0, w = 1.25, 7.5
    for name, n in items:
        ax.add_patch(Rectangle((x0, y - row_h), w, row_h, facecolor=LIGHT, edgecolor=EDGE, linewidth=1.2))
        ax.text(x0 + 0.20, y - row_h / 2, name, ha="left", va="center", fontsize=12.5, color=TEXT)
        ax.text(x0 + w - 0.60, y - row_h / 2, count_label(n), ha="center", va="center", fontsize=12.5, color=TEXT)
        y -= row_h + gap

    ax.text(
        5,
        0.70,
        "Release condition: all K4 inputs declared before scoring; target side remains quarantined.",
        ha="center",
        va="center",
        fontsize=11.5,
        color="#4c4c4c",
    )

    fig.savefig(OUT_PATH, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


if __name__ == "__main__":
    main()
