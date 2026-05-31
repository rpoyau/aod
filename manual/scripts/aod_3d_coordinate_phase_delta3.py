#!/usr/bin/env python3
"""Generate the manual 3D coordinate phase-cycle delta_3 fixture assets.

The coordinate fixture is integer-native: a track is mapped to Z^3, lagged displacements
produce Q=a^2+b^2+c^2, phase residues Q mod beta_a, octant counts, and exact
ternary signed residuals against integer-balanced comparators.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List, Tuple

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "brownian"
FIG_DIR = ROOT / "figures"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

BETA_A = 5
LAG = 1
TRACK = [
    ("b1", 0, 0, 0, 0),
    ("b1", 1, 1, 1, 0),
    ("b1", 2, 2, 1, 1),
    ("b1", 3, 3, 2, 1),
    ("b1", 4, 2, 3, 2),
    ("b1", 5, 3, 4, 3),
    ("b1", 6, 4, 3, 4),
    ("b1", 7, 5, 4, 4),
    ("b1", 8, 6, 5, 5),
]


def int_balance(n: int, k: int) -> List[int]:
    base = n // k
    rem = n % k
    return [base + (1 if i < rem else 0) for i in range(k)]


def sign3(x: int) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def sign0(x: int) -> int:
    # zero-axis convention for octant display: zero component is assigned to the nonnegative side
    return 1 if x >= 0 else -1


def octant(a: int, b: int, c: int) -> int:
    sx, sy, sz = sign0(a), sign0(b), sign0(c)
    mapping = {
        (1, 1, 1): 0,
        (1, 1, -1): 1,
        (1, -1, 1): 2,
        (1, -1, -1): 3,
        (-1, 1, 1): 4,
        (-1, 1, -1): 5,
        (-1, -1, 1): 6,
        (-1, -1, -1): 7,
    }
    return mapping[(sx, sy, sz)]


def pattern(q: int) -> str:
    patterns = {
        0: "(+,+,+)", 1: "(+,+,-)", 2: "(+,-,+)", 3: "(+,-,-)",
        4: "(-,+,+)", 5: "(-,+,-)", 6: "(-,-,+)", 7: "(-,-,-)",
    }
    return patterns[q]


def compute_rows():
    rows = []
    coords = [(tid, t, x, y, z) for (tid, t, x, y, z) in TRACK]
    for i in range(len(coords) - LAG):
        tid, t0, x0, y0, z0 = coords[i]
        _, t1, x1, y1, z1 = coords[i + LAG]
        a, b, c = x1 - x0, y1 - y0, z1 - z0
        qval = a * a + b * b + c * c
        rows.append({
            "track_id": tid,
            "i": i,
            "lag_n": LAG,
            "t0": t0,
            "t1": t1,
            "X0": x0,
            "Y0": y0,
            "Z0": z0,
            "X1": x1,
            "Y1": y1,
            "Z1": z1,
            "a": a,
            "b": b,
            "c": c,
            "Q": qval,
            "theta": qval % BETA_A,
            "octant": octant(a, b, c),
            "octant_pattern": pattern(octant(a, b, c)),
        })
    return rows


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_data():
    # input track
    write_csv(
        DATA_DIR / "brownian_sample_track.csv",
        [{"track_id": tid, "t": t, "x": x, "y": y, "z": z} for tid, t, x, y, z in TRACK],
        ["track_id", "t", "x", "y", "z"],
    )
    disp_rows = compute_rows()
    write_csv(
        DATA_DIR / "brownian_displacements.csv",
        disp_rows,
        ["track_id", "i", "lag_n", "t0", "t1", "X0", "Y0", "Z0", "X1", "Y1", "Z1", "a", "b", "c", "Q", "theta", "octant", "octant_pattern"],
    )

    N = len(disp_rows)
    max_q = max(r["Q"] for r in disp_rows)
    q_counts = {q: 0 for q in range(max_q + 1)}
    for r in disp_rows:
        q_counts[r["Q"]] += 1
    q_rows = [{"lag_n": LAG, "Q": q, "observed_count": q_counts[q]} for q in sorted(q_counts)]
    write_csv(DATA_DIR / "displacement_q_counts.csv", q_rows, ["lag_n", "Q", "observed_count"])

    phase_counts = {theta: 0 for theta in range(BETA_A)}
    for r in disp_rows:
        phase_counts[r["theta"]] += 1
    phase_comp = int_balance(N, BETA_A)
    phase_rows = []
    for theta in range(BETA_A):
        delta = phase_comp[theta] - phase_counts[theta]
        phase_rows.append({
            "lag_n": LAG,
            "beta_a": BETA_A,
            "theta": theta,
            "observed_count": phase_counts[theta],
            "comparator_count": phase_comp[theta],
            "DeltaZ": delta,
            "s3": sign3(delta),
            "m": abs(delta),
        })
    write_csv(DATA_DIR / "phase_cycle_delta3.csv", phase_rows, ["lag_n", "beta_a", "theta", "observed_count", "comparator_count", "DeltaZ", "s3", "m"])

    oct_counts = {q: 0 for q in range(8)}
    for r in disp_rows:
        oct_counts[r["octant"]] += 1
    oct_comp = int_balance(N, 8)
    oct_rows = []
    for q in range(8):
        delta = oct_comp[q] - oct_counts[q]
        oct_rows.append({
            "lag_n": LAG,
            "octant": q,
            "sign_pattern": pattern(q),
            "observed_count": oct_counts[q],
            "comparator_count": oct_comp[q],
            "DeltaZ": delta,
            "s3": sign3(delta),
            "m": abs(delta),
        })
    write_csv(DATA_DIR / "octant_delta3.csv", oct_rows, ["lag_n", "octant", "sign_pattern", "observed_count", "comparator_count", "DeltaZ", "s3", "m"])

    sum_q = sum(r["Q"] for r in disp_rows)
    sum_x = sum(r["a"] * r["a"] for r in disp_rows)
    sum_y = sum(r["b"] * r["b"] for r in disp_rows)
    sum_z = sum(r["c"] * r["c"] for r in disp_rows)
    ratio_rows = [
        {"lag_n": LAG, "ratio": "R_Q", "numerator": sum_q, "denominator": N, "description": "total squared displacement per displacement count"},
        {"lag_n": LAG, "ratio": "R_x", "numerator": sum_x, "denominator": sum_q, "description": "x-axis squared share"},
        {"lag_n": LAG, "ratio": "R_y", "numerator": sum_y, "denominator": sum_q, "description": "y-axis squared share"},
        {"lag_n": LAG, "ratio": "R_z", "numerator": sum_z, "denominator": sum_q, "description": "z-axis squared share"},
        {"lag_n": LAG, "ratio": "R_theta", "numerator": ":".join(str(phase_counts[t]) for t in range(BETA_A)), "denominator": N, "description": "phase-cycle count ratio"},
        {"lag_n": LAG, "ratio": "R_oct", "numerator": ":".join(str(oct_counts[q]) for q in range(8)), "denominator": N, "description": "octant count ratio"},
    ]
    write_csv(DATA_DIR / "integer_motion_ratios.csv", ratio_rows, ["lag_n", "ratio", "numerator", "denominator", "description"])


def generate_figure():
    rows = compute_rows()
    points = [(x, y, z) for _, _, x, y, z in TRACK]
    fig = plt.figure(figsize=(12.5, 7.0), dpi=180)

    # 3D wireframe trajectory panel
    ax = fig.add_axes([0.035, 0.31, 0.42, 0.56], projection="3d")
    ax.set_title("Integerized 3D trajectory", fontsize=12, pad=8, fontweight="bold")
    xs, ys, zs = zip(*points)
    ax.plot(xs, ys, zs, marker="o", color="black", linewidth=2)
    ax.plot([points[0][0], points[-1][0]], [points[0][1], points[-1][1]], [points[0][2], points[-1][2]], linestyle="--", color="0.35", linewidth=1.5)
    # wireframe cube/grid
    for x in range(0, 7):
        ax.plot([x, x], [0, 5], [0, 0], color="0.78", linewidth=0.6)
        ax.plot([x, x], [0, 0], [0, 5], color="0.78", linewidth=0.6)
    for y in range(0, 6):
        ax.plot([0, 6], [y, y], [0, 0], color="0.78", linewidth=0.6)
        ax.plot([0, 0], [y, y], [0, 5], color="0.78", linewidth=0.6)
    for z in range(0, 6):
        ax.plot([0, 6], [0, 0], [z, z], color="0.78", linewidth=0.6)
        ax.plot([0, 0], [0, 5], [z, z], color="0.78", linewidth=0.6)
    ax.text(points[0][0], points[0][1], points[0][2]-0.35, r"$z_i$", fontsize=11)
    ax.text(points[-1][0], points[-1][1], points[-1][2]+0.3, r"$z_{i+n}$", fontsize=11)
    ax.text(2.5, 2.4, 2.1, r"$\Delta z_i^{(n)}$", fontsize=11)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5)
    ax.set_zlim(0, 5)
    ax.view_init(elev=22, azim=-58)

    # formula / counts panel
    ax2 = fig.add_axes([0.49, 0.66, 0.47, 0.22])
    ax2.axis("off")
    ax2.set_title("Integer squared displacement and phase", fontsize=12, fontweight="bold", pad=6)
    ax2.text(0.02, 0.82, r"$\Delta z_i^{(n)}=(a_i^{(n)},b_i^{(n)},c_i^{(n)})\in\mathbb{Z}^3$", fontsize=11)
    ax2.text(0.02, 0.62, r"$Q_i^{(n)}=(a_i^{(n)})^2+(b_i^{(n)})^2+(c_i^{(n)})^2\in\mathbb{Z}_{\geq 0}$", fontsize=11)
    ax2.text(0.02, 0.42, r"$\theta_i^{(n)}=Q_i^{(n)}\,\mathrm{mod}\,\beta_a$", fontsize=11)
    ax2.text(0.02, 0.20, r"Active fixture: counts on $Q$, phase, and octant bins; no radial-distance fit.", fontsize=10)
    ax2.text(0.72, 0.68, r"$\delta_{3,k}=(s^{(3)}_k,m_k)$", fontsize=11, bbox=dict(boxstyle="round", facecolor="white", edgecolor="0.3"))

    # phase/octal small bar charts
    ax3 = fig.add_axes([0.51, 0.34, 0.20, 0.23])
    phase_counts = {theta: 0 for theta in range(BETA_A)}
    for r in rows:
        phase_counts[r["theta"]] += 1
    ax3.bar(range(BETA_A), [phase_counts[t] for t in range(BETA_A)], color="0.72", edgecolor="black")
    ax3.set_title(r"Phase counts $O_\theta$", fontsize=10)
    ax3.set_xlabel(r"$\theta$")
    ax3.set_ylabel("count")
    ax3.set_xticks(range(BETA_A))

    ax4 = fig.add_axes([0.76, 0.34, 0.20, 0.23])
    oct_counts = {q: 0 for q in range(8)}
    for r in rows:
        oct_counts[r["octant"]] += 1
    ax4.bar(range(8), [oct_counts[q] for q in range(8)], color="0.82", edgecolor="black")
    ax4.set_title(r"Octant counts $O_q$", fontsize=10)
    ax4.set_xlabel(r"$q$")
    ax4.set_ylabel("count")
    ax4.set_xticks(range(8))

    # bottom flow
    ax5 = fig.add_axes([0.05, 0.05, 0.90, 0.16])
    ax5.axis("off")
    labels = [r"$z_i\in\mathbb{Z}^3$", r"$\Delta z_i^{(n)}$", r"$Q_i^{(n)}$", r"$Q\,\mathrm{mod}\,\beta_a$", "octant counts", r"$\delta_3$", "integer ratios"]
    x0 = 0.01
    dx = 0.14
    for i, lab in enumerate(labels):
        x = x0 + i*dx
        ax5.text(x, 0.55, lab, fontsize=10, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="0.3"))
        if i < len(labels)-1:
            ax5.annotate("", xy=(x+0.10,0.55), xytext=(x+0.07,0.55), arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))
    ax5.text(0.5, 0.08, "3D coordinate phase-cycle delta_3 fixture: integer counts first; continuous summaries only after exact fixture", ha="center", fontsize=10, fontweight="bold")

    fig.suptitle(r"3D Coordinate Phase-Cycle $\delta_3$ Fixture", fontsize=16, fontweight="bold", y=0.985)
    fig.savefig(FIG_DIR / "coordinate_phase_delta3_wireframe.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    generate_data()
    generate_figure()
