#!/usr/bin/env python3
"""Regenerate the SPARC five-galaxy field dynamics square-speed outputs.

This script uses only the included SPARC rotation-curve files and the frozen
manual declaration constants. It regenerates the per-bin CSV, per-galaxy CSV,
summary table, and SPARC figures used by the manual.
"""
from __future__ import annotations
from pathlib import Path
import csv
import math
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sparc"
DER = ROOT / "data" / "derived"
FIG = ROOT / "figures"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

GALAXIES = ["NGC2403", "NGC3198", "NGC6503", "NGC2841", "DDO154"]
UPSILON_D = 0.5
UPSILON_B = 0.7
K_EXT_U = 8.0
J_NORM = 1.0
# Frozen primary-lane declarations for v39.99r1.
LAMBDA_RET = 1.0
DENSITY = 0.0
GAS_STAR = 0.0
BOBBING = 0.0


def read_rotmod(galaxy: str) -> pd.DataFrame:
    path = DATA / f"{galaxy}_rotmod.dat"
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        rows.append([float(x) for x in parts[:8]])
    df = pd.DataFrame(rows, columns=["R","Vobs","errV","Vgas","Vdisk","Vbul","SBdisk","SBbul"])
    df.insert(0, "galaxy", galaxy)
    return df


def compute() -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows = []
    for g in GALAXIES:
        df = read_rotmod(g)
        df["U_obs"] = df["Vobs"] ** 2
        df["sigma_U"] = 2 * df["Vobs"] * df["errV"]
        df["U_gas"] = df["Vgas"] ** 2
        df["U_disk"] = df["Vdisk"] ** 2
        df["U_bulge"] = df["Vbul"] ** 2
        df["U_bar"] = df["U_gas"] + UPSILON_D * df["U_disk"] + UPSILON_B * df["U_bulge"]
        df["lambda_ret"] = LAMBDA_RET
        df["density_index"] = DENSITY
        df["gas_star_index"] = GAS_STAR
        df["bobbing_index"] = BOBBING
        df["C_cap"] = df["R"] * (df["Vgas"].abs() + df["Vdisk"].abs() + df["Vbul"].abs())
        df["D_BF"] = df["C_cap"] * df["lambda_ret"] * (1 + df["density_index"]/16.0) * (1 + df["gas_star_index"]/16.0) * (1 + df["bobbing_index"]/64.0) * J_NORM
        df["U_AO"] = df["U_bar"] + K_EXT_U * df["D_BF"]
        df["V_disp"] = df["U_AO"].clip(lower=0).pow(0.5)
        df["Delta_U"] = df["U_AO"] - df["U_obs"]
        df["z_U"] = df["Delta_U"] / df["sigma_U"]
        all_rows.append(df)
    per_bin = pd.concat(all_rows, ignore_index=True)
    per_gal = []
    for g, df in per_bin.groupby("galaxy", sort=True):
        N = len(df)
        chi2 = float((df["z_U"]**2).sum())
        mae = float(df["Delta_U"].abs().mean())
        mse = float((df["Delta_U"]**2).mean())
        valid = df["U_obs"] > 0
        mape = float((100.0 * (df.loc[valid,"Delta_U"].abs() / df.loc[valid,"U_obs"])).mean())
        per_gal.append({"galaxy": g, "N": N, "chi2_U": chi2, "MAE_U": mae, "MSE_U": mse, "MAPE_U": mape})
    return per_bin, pd.DataFrame(per_gal)


def write_outputs(per_bin: pd.DataFrame, per_gal: pd.DataFrame) -> None:
    per_bin.to_csv(DER / "sparc_five_galaxy_per_bin.csv", index=False)
    per_gal.to_csv(DER / "sparc_five_galaxy_per_galaxy.csv", index=False)
    # Controls are declared comparison variants from the v39.99 diagnostic run.
    controls = pd.DataFrame([
        {"declaration": "radial only", "MAPE_U_percent": 38.67004681721992},
        {"declaration": "z-layer slow", "MAPE_U_percent": 33.267659551663},
        {"declaration": "boundary-face slow (primary)", "MAPE_U_percent": 26.571059127273696},
        {"declaration": "boundary + z + slow", "MAPE_U_percent": 34.81241347331653},
    ])
    controls.to_csv(DER / "sparc_declaration_controls.csv", index=False)
    lines = []
    lines.append(r"\begin{table}[H]")
    lines.append(r"\centering")
    lines.append(r"\scriptsize")
    lines.append(r"\caption{SPARC five-galaxy scored records.}")
    lines.append(r"\begin{tabular}{lrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"$G$ & $N$ & $\chi^2_U$ & $MAE_U$ & $MSE_U$ & $MAPE_U$ [\%]\\")
    lines.append(r"\midrule")
    for _, row in per_gal.sort_values("galaxy").iterrows():
        lines.append(f"{row['galaxy']} & {int(row['N'])} & {row['chi2_U']:.2f} & {row['MAE_U']:.1f} & {row['MSE_U']:.1f} & {row['MAPE_U']:.2f}\\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\label{tab:manual-sparc-five-galaxy-scores}")
    lines.append(r"\end{table}")
    (DER / "sparc_summary_table.tex").write_text("\n".join(lines) + "\n")


def make_figures(per_bin: pd.DataFrame, per_gal: pd.DataFrame) -> None:
    controls = pd.read_csv(DER / "sparc_declaration_controls.csv")
    plt.figure(figsize=(8,4.5))
    plt.bar(controls["declaration"], controls["MAPE_U_percent"])
    plt.ylabel(r"$MAPE_U$ [%]")
    plt.title("SPARC declaration controls")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(FIG / "sparc_declaration_controls.png", dpi=180)
    plt.close()

    # Display one galaxy used by earlier manual figures.
    g = "NGC3198"
    df = per_bin[per_bin["galaxy"] == g].sort_values("R")
    plt.figure(figsize=(8,4.5))
    plt.plot(df["R"], df["U_obs"], label=r"benchmark $U_{\mathrm{obs}}$")
    plt.plot(df["R"], df["U_AO"], label=r"A$\Omega$ boundary-derived $U$")
    plt.xlabel("R [kpc]")
    plt.ylabel(r"$U=V^2$ [(km/s)$^2$]")
    plt.title("SPARC square-speed comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "sparc_square_speed_comparison.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8,4.5))
    plt.axhline(0, linewidth=1)
    plt.plot(df["R"], df["Delta_U"], label=r"$\Delta U$, primary declaration")
    plt.xlabel("R [kpc]")
    plt.ylabel(r"$\Delta U$ [(km/s)$^2$]")
    plt.title("SPARC square-speed residuals")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "sparc_square_speed_residuals.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8,4.5))
    plt.plot(df["R"], df["Vobs"], label="benchmark target speed")
    plt.plot(df["R"], df["V_disp"], label=r"A$\Omega$ display speed")
    plt.xlabel("R [kpc]")
    plt.ylabel("Display speed [km/s]")
    plt.title("Display speed view (not scoring coordinate)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "sparc_display_speed_view.png", dpi=180)
    plt.close()


def main() -> None:
    per_bin, per_gal = compute()
    write_outputs(per_bin, per_gal)
    make_figures(per_bin, per_gal)

if __name__ == "__main__":
    main()
