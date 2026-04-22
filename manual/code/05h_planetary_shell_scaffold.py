#!/usr/bin/env python3
"""Phase IV planetary-shell and ring-refinement scaffold rows."""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SCRIPT_DIR.parent
RAW_PATH = MANUAL_DIR / "data" / "raw" / "05h_planetary_shell_setup.json"
SHELL_CSV = MANUAL_DIR / "data" / "derived" / "05h_planetary_shell_scaffold.csv"
RING_CSV = MANUAL_DIR / "data" / "derived" / "05h_saturn_galactic_ring_refinements.csv"
SHELL_FIGURE = MANUAL_DIR / "figures" / "planetary" / "01_earth_moon_shell_scaffold.png"
RING_FIGURE = MANUAL_DIR / "figures" / "planetary" / "02_saturn_galactic_ring_refinements.png"


def load_setup(path: Path = RAW_PATH) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def rat(num: int, den: int) -> Fraction:
    if den <= 0:
        raise ValueError(f"denominator must be positive, got {den}")
    return Fraction(num, den)


def shell_rows(setup: dict | None = None) -> list[dict[str, object]]:
    setup = load_setup() if setup is None else setup
    out: list[dict[str, object]] = []
    for row in setup["shell_components"]:
        phi = rat(int(row["Phi_num"]), int(row["Phi_den"]))
        q_eff = rat(int(row["Q"]), int(row["S"])) if int(row["Q"]) != 0 else Fraction(0, 1)
        loss = rat(int(row["R0"]), int(row["R0"]) + int(row["R"]))
        torsion = rat(int(row["T0"]) + int(row["T"]), int(row["T0"]))
        momentum_proxy = rat(int(row["P_shell"]), int(row["P0_shell"]))
        out.append({
            "row_id": row["row_id"],
            "component": row["component"],
            "Phi_num": phi.numerator,
            "Phi_den": phi.denominator,
            "chi": int(row["chi"]),
            "q_eff_num": q_eff.numerator,
            "q_eff_den": q_eff.denominator,
            "loss_num": loss.numerator,
            "loss_den": loss.denominator,
            "torsion_num": torsion.numerator,
            "torsion_den": torsion.denominator,
            "B_star": int(row["B_star"]),
            "widehat_Lambda": int(row["widehat_Lambda"]),
            "P_shell_num": momentum_proxy.numerator,
            "P_shell_den": momentum_proxy.denominator,
            "Sigma_tag": row["Sigma_tag"],
            "q_eff_role": "boundary_polarization_pair",
            "status": row["status"],
        })
    return out


def ring_rows(setup: dict | None = None) -> list[dict[str, object]]:
    setup = load_setup() if setup is None else setup
    out: list[dict[str, object]] = []
    for row in setup["ring_refinements"]:
        phase_lock = rat(int(row["phase_lock_num"]), int(row["phase_lock_den"]))
        out.append({
            "row_id": row["row_id"],
            "family": row["family"],
            "retained_extraction": row["retained_extraction"],
            "gap_or_band_witness": row["gap_or_band_witness"],
            "phase_lock_num": phase_lock.numerator,
            "phase_lock_den": phase_lock.denominator,
            "B_star": int(row["B_star"]),
            "widehat_Lambda": int(row["widehat_Lambda"]),
            "status": row["status"],
        })
    return out


def write_csv(records: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def write_figures(shell: list[dict[str, object]], rings: list[dict[str, object]]) -> None:
    import matplotlib.pyplot as plt

    SHELL_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    labels = [str(r["component"]) for r in shell]
    phi = [float(Fraction(int(r["Phi_num"]), int(r["Phi_den"]))) for r in shell]
    q_abs = [abs(float(Fraction(int(r["q_eff_num"]), int(r["q_eff_den"])))) for r in shell]
    x = list(range(len(shell)))
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.plot(x, phi, marker="o", label="Phi pair report")
    ax.plot(x, q_abs, marker="s", label="|Q/S| report")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_title("Earth water-atmosphere-Moon shell scaffold")
    ax.set_ylabel("rational report value")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(SHELL_FIGURE, dpi=160)
    plt.close(fig)

    fam = [str(r["family"]) for r in rings]
    phase = [float(Fraction(int(r["phase_lock_num"]), int(r["phase_lock_den"]))) for r in rings]
    bstar = [int(r["B_star"]) for r in rings]
    x2 = list(range(len(rings)))
    fig2, ax1 = plt.subplots(figsize=(7.5, 3.4))
    ax1.bar(x2, bstar, width=0.45, label="B* count")
    ax2 = ax1.twinx()
    ax2.plot(x2, phase, marker="o", label="phase lock")
    ax1.set_xticks(x2)
    ax1.set_xticklabels(fam, rotation=15, ha="right")
    ax1.set_ylabel("B* count")
    ax2.set_ylabel("phase-lock rational report")
    ax1.set_title("Saturn / galactic ring-refinement scaffold")
    fig2.tight_layout()
    fig2.savefig(RING_FIGURE, dpi=160)
    plt.close(fig2)


def main() -> int:
    setup = load_setup()
    shell = shell_rows(setup)
    rings = ring_rows(setup)
    write_csv(shell, SHELL_CSV)
    write_csv(rings, RING_CSV)
    write_figures(shell, rings)
    print(SHELL_CSV)
    print(RING_CSV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
