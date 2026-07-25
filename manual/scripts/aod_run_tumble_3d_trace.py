#!/usr/bin/env python3
"""Generate the deterministic run-tumble tracer-current fixture artifacts.

This is a deterministic manual reference fixture.  Q4 remains the
finite Hamming-1 edge-slot support.  The retained trace is accumulated in Z^4,
then a declared pi_3 projection reports the 3D coordinate path.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import math

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual" / "data" / "run_tumble"
FIG = ROOT / "manual" / "figures" / "run_tumble_trace_3d_projection.png"
BETA = 5

# Deterministic released sample path: t=0 is the initial row; t=1..20 update.
SCHEDULE = [
    ("run", 1, +1),
    ("run", 1, +1),
    ("tumble", 2, +1),
    ("run", 2, +1),
    ("tumble", 3, -1),
    ("run", 3, -1),
    ("tumble", 4, +1),
    ("run", 4, +1),
    ("tumble", 1, -1),
    ("run", 1, -1),
    ("tumble", 2, -1),
    ("run", 2, -1),
    ("tumble", 3, +1),
    ("run", 3, +1),
    ("tumble", 4, -1),
    ("run", 4, -1),
    ("tumble", 1, +1),
    ("run", 1, +1),
    ("tumble", 2, +1),
    ("run", 2, +1),
]


def pi3(h: tuple[int, int, int, int]) -> tuple[int, int, int]:
    return (h[0], h[1], h[2])


def octant(z: tuple[int, int, int]) -> int:
    x, y, zc = z
    return (1 if x < 0 else 0) + (2 if y < 0 else 0) + (4 if zc < 0 else 0)


def int_balance(n: int, k: int) -> list[int]:
    base, rem = divmod(n, k)
    return [base + (1 if i < rem else 0) for i in range(k)]


def tuple_tex(values: tuple[int, ...]) -> str:
    return "(" + ",".join(str(v) for v in values) + ")"


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    h = [0, 0, 0, 0]
    z = pi3(tuple(h))
    rows.append({
        "t": 0,
        "mode": "init",
        "edge": "-",
        "sigma": 0,
        "h1": h[0], "h2": h[1], "h3": h[2], "h4": h[3],
        "x": z[0], "y": z[1], "z": z[2],
        "Q3": sum(v*v for v in z),
        "Q4": sum(v*v for v in h),
        "theta": 0,
        "octant": octant(z),
    })
    for t, (mode, edge, sigma) in enumerate(SCHEDULE, start=1):
        h[edge - 1] += sigma
        z = pi3(tuple(h))
        q3 = sum(v*v for v in z)
        q4 = sum(v*v for v in h)
        rows.append({
            "t": t,
            "mode": mode,
            "edge": f"e{edge}",
            "sigma": sigma,
            "h1": h[0], "h2": h[1], "h3": h[2], "h4": h[3],
            "x": z[0], "y": z[1], "z": z[2],
            "Q3": q3,
            "Q4": q4,
            "theta": q3 % BETA,
            "octant": octant(z),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_artifacts(rows: list[dict[str, object]]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    fields = ["t", "mode", "edge", "sigma", "h1", "h2", "h3", "h4", "x", "y", "z", "Q3", "Q4", "theta", "octant", "beta_a"]
    trace_rows = []
    for r in rows:
        rr = dict(r)
        rr["beta_a"] = BETA
        trace_rows.append(rr)
    write_csv(DATA / "run_tumble_trace_20_steps.csv", trace_rows, fields)

    active = rows[1:]
    n = len(active)
    phase_counts = Counter(int(r["theta"]) for r in active)
    phase_comp = int_balance(n, BETA)
    phase_rows = []
    for theta in range(BETA):
        obs = phase_counts.get(theta, 0)
        comp = phase_comp[theta]
        dz = comp - obs
        phase_rows.append({
            "beta_a": BETA,
            "theta": theta,
            "O": obs,
            "O_hat": comp,
            "DeltaZ": dz,
            "s3": 0 if dz == 0 else (1 if dz > 0 else -1),
            "m": abs(dz),
        })
    write_csv(DATA / "run_tumble_phase_cycle_delta3.csv", phase_rows, ["beta_a", "theta", "O", "O_hat", "DeltaZ", "s3", "m"])

    oct_counts = Counter(int(r["octant"]) for r in active)
    oct_comp = int_balance(n, 8)
    oct_rows = []
    for q in range(8):
        obs = oct_counts.get(q, 0)
        comp = oct_comp[q]
        dz = comp - obs
        oct_rows.append({
            "octant": q,
            "O": obs,
            "O_hat": comp,
            "DeltaZ": dz,
            "s3": 0 if dz == 0 else (1 if dz > 0 else -1),
            "m": abs(dz),
        })
    write_csv(DATA / "run_tumble_octant_delta3.csv", oct_rows, ["octant", "O", "O_hat", "DeltaZ", "s3", "m"])

    sum_q3 = sum(int(r["Q3"]) for r in active)
    sum_q4 = sum(int(r["Q4"]) for r in active)
    sx = sum(int(r["x"])**2 for r in active)
    sy = sum(int(r["y"])**2 for r in active)
    sz = sum(int(r["z"])**2 for r in active)
    sh4 = sum(int(r["h4"])**2 for r in active)
    ratio_rows = [
        {"ratio": "R_Q3", "numerator": sum_q3, "denominator": n},
        {"ratio": "R_Q4", "numerator": sum_q4, "denominator": n},
        {"ratio": "R_x", "numerator": sx, "denominator": sum_q3},
        {"ratio": "R_y", "numerator": sy, "denominator": sum_q3},
        {"ratio": "R_z", "numerator": sz, "denominator": sum_q3},
        {"ratio": "R_h4_audit", "numerator": sh4, "denominator": sum_q4},
    ]
    write_csv(DATA / "run_tumble_integer_motion_ratios.csv", ratio_rows, ["ratio", "numerator", "denominator"])

    write_trace_tex(rows)
    write_figure(rows, phase_rows, oct_rows)


def write_trace_tex(rows: list[dict[str, object]]) -> None:
    path = DATA / "run_tumble_trace_table.tex"
    lines = []
    lines.append(r"\scriptsize")
    lines.append(r"\begin{longtable}{@{}rllrllrrrr@{}}")
    lines.append(r"\caption{Run-tumble tracer-current 20-step exact trace.}\label{tab:run-tumble-tracer-current-20step}\\")
    lines.append(r"\toprule")
    lines.append(r"$t$ & mode & edge & $\sigma$ & $h_t$ & $\pi_3(h_t)$ & $Q^2_{3D}$ & $Q^2_4$ & $\theta$ & oct.\\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(r"\toprule")
    lines.append(r"$t$ & mode & edge & $\sigma$ & $h_t$ & $\pi_3(h_t)$ & $Q^2_{3D}$ & $Q^2_4$ & $\theta$ & oct.\\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    for r in rows:
        h = tuple(int(r[k]) for k in ["h1", "h2", "h3", "h4"])
        z = tuple(int(r[k]) for k in ["x", "y", "z"])
        sigma = "--" if int(r["t"]) == 0 else ("+1" if int(r["sigma"]) > 0 else "-1")
        edge = r["edge"]
        line = (
            f"{r['t']} & {r['mode']} & {edge} & {sigma} & "
            f"\\texttt{{{tuple_tex(h)}}} & \\texttt{{{tuple_tex(z)}}} & "
            f"{r['Q3']} & {r['Q4']} & {r['theta']} & {r['octant']}"
            + r"\\"
        )
        lines.append(line)
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    lines.append(r"\normalsize")
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def write_figure(rows: list[dict[str, object]], phase_rows: list[dict[str, object]], oct_rows: list[dict[str, object]]) -> None:
    FIG.parent.mkdir(parents=True, exist_ok=True)
    x = [int(r["x"]) for r in rows]
    y = [int(r["y"]) for r in rows]
    z = [int(r["z"]) for r in rows]
    t = [int(r["t"]) for r in rows]
    q3 = [int(r["Q3"]) for r in rows]
    modes = [r["mode"] for r in rows]
    fig = plt.figure(figsize=(8.0, 6.0))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.4, 1.0, 1.0], hspace=0.55, wspace=0.35)
    ax0 = fig.add_subplot(gs[0, :], projection="3d")
    ax0.plot(x, y, z, marker="o")
    ax0.set_title("Declared pi_3(h_t) path in Z^3")
    ax0.set_xlabel("x")
    ax0.set_ylabel("y")
    ax0.set_zlabel("z")
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.step(t, q3, where="post")
    ax1.set_title("Q^2_3D by update step")
    ax1.set_xlabel("t")
    ax1.set_ylabel("Q^2_3D")
    ax2 = fig.add_subplot(gs[1, 1])
    vals = [0 if m == "init" else (1 if m == "run" else 2) for m in modes]
    ax2.imshow([vals], aspect="auto", interpolation="nearest", extent=[min(t), max(t), 0, 1])
    ax2.set_yticks([])
    ax2.set_xticks([0, 5, 10, 15, 20])
    ax2.set_title("mode strip: init/run/tumble")
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.bar([int(r["theta"]) for r in phase_rows], [int(r["O"]) for r in phase_rows])
    ax3.set_title("coordinate-residue counts Q^2_3D mod beta")
    ax3.set_xlabel("theta")
    ax3.set_ylabel("count")
    ax4 = fig.add_subplot(gs[2, 1])
    ax4.bar([int(r["octant"]) for r in oct_rows], [int(r["m"]) for r in oct_rows])
    ax4.set_title("octant delta_3 magnitudes")
    ax4.set_xlabel("octant")
    ax4.set_ylabel("m")
    fig.suptitle("Run-tumble tracer-current projection", y=0.98)
    fig.savefig(FIG, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = build_rows()
    write_artifacts(rows)


if __name__ == "__main__":
    main()
