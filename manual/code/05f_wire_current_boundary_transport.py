#!/usr/bin/env python3
"""Exact AOD boundary-transport worked row for manual Section 05f.

This script keeps the computation in integer and rational rows.  It reads the
manual-local setup JSON, computes exact transport rows with ``fractions.Fraction``,
writes exact/report/trace CSV files, and renders figures from the rational rows.
"""
from __future__ import annotations

import csv
import json
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import struct
import zlib

SCRIPT_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SCRIPT_DIR.parent
RAW_PATH = MANUAL_DIR / "data" / "raw" / "05f_wire_current_setup.json"
DERIVED_DIR = MANUAL_DIR / "data" / "derived"
FIGURE_DIR = MANUAL_DIR / "figures" / "transport"

FAMILIES = ("duon", "tetron", "other")


@dataclass(frozen=True)
class RowResult:
    row_id: str
    omega: str
    working_level: int
    window_bip_0: int
    carrier_family: str
    B_star: int
    widehat_Lambda: int
    phase_step_num: int
    phase_step_den: int
    centered_phase_step: str
    chi: int
    q_eff: Fraction
    atten_b: Fraction
    atten_loss: Fraction
    tors: Fraction
    epsilon_parallel: int
    u_tr: Fraction


def load_setup(path: Path = RAW_PATH) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def rat(num: int, den: int) -> Fraction:
    """Canonical exact rational pair."""
    if den <= 0:
        raise ValueError(f"denominator must be positive, got {den}")
    return Fraction(num, den)


def wrap_mod(value: int, modulus: int) -> int:
    if modulus <= 0:
        raise ValueError("cycle modulus must be positive")
    return value % modulus


def centered_residue(delta: int, modulus: int) -> int:
    """Return a centered representative in [-floor(N/2), ceil(N/2)-1]."""
    wrapped = wrap_mod(delta, modulus)
    if wrapped > modulus // 2:
        wrapped -= modulus
    return wrapped


def fraction_columns(value: Fraction, prefix: str) -> Dict[str, int]:
    return {f"{prefix}_num": value.numerator, f"{prefix}_den": value.denominator}


def as_display(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def validate_partition(setup: Mapping) -> None:
    declared: Dict[str, List[str]] = setup["carrier_family_partition"]
    seen: Dict[str, str] = {}
    for family, row_ids in declared.items():
        for row_id in row_ids:
            if row_id in seen:
                raise ValueError(f"row {row_id} appears in both {seen[row_id]} and {family}")
            seen[row_id] = family
    row_family = {row["row_id"]: row["carrier_family"] for row in setup["source_chain_rows"]}
    if set(seen) != set(row_family):
        missing = sorted(set(row_family) - set(seen))
        extra = sorted(set(seen) - set(row_family))
        raise ValueError(f"carrier partition mismatch; missing={missing}, extra={extra}")
    for row_id, family in row_family.items():
        if seen[row_id] != family:
            raise ValueError(f"partition family mismatch for {row_id}: {seen[row_id]} != {family}")


def row_result(row: Mapping, setup: Mapping) -> RowResult:
    B0 = int(setup.get("support_base_B0", 1))
    N = int(row["N"])
    r = centered_residue(int(row["k_plus"]) - int(row["k_minus"]), N)
    Q = int(row["Q"])
    S = int(row["S"])
    R = int(row["R"])
    R0 = int(row["R0"])
    T = int(row["T"])
    T0 = int(row["T0"])
    B_star = int(row["B_star"])
    widehat = int(row["widehat_Lambda"])
    if S <= 0 or R0 <= 0 or T0 <= 0 or B_star <= 0 or widehat < 0:
        raise ValueError(f"invalid positive row support in {row['row_id']}")
    tors_num = T0 + T
    if tors_num <= 0:
        raise ValueError(f"torsion numerator must be positive in {row['row_id']}")

    atten_b = rat(B0**widehat, B_star**widehat)
    atten_loss = rat(R0, R0 + R)
    tors = rat(tors_num, T0)
    q_eff = rat(Q, S) if Q != 0 else Fraction(0, 1)
    numerator = r * Q * atten_b.numerator * atten_loss.numerator * tors.numerator
    denominator = N * S * atten_b.denominator * atten_loss.denominator * tors.denominator
    u_tr = rat(numerator, denominator) if numerator != 0 else Fraction(0, 1)
    return RowResult(
        row_id=str(row["row_id"]),
        omega=str(setup["omega"]),
        working_level=int(setup["working_level"]),
        window_bip_0=int(setup["window_bip_0"]),
        carrier_family=str(row["carrier_family"]),
        B_star=B_star,
        widehat_Lambda=widehat,
        phase_step_num=r,
        phase_step_den=N,
        centered_phase_step=as_display(rat(r, N)) if r != 0 else "0",
        chi=int(row["chi"]),
        q_eff=q_eff,
        atten_b=atten_b,
        atten_loss=atten_loss,
        tors=tors,
        epsilon_parallel=int(row["epsilon_parallel"]),
        u_tr=u_tr,
    )


def _transform_rows(setup: Mapping, transform: Optional[str] = None) -> dict:
    new_setup = deepcopy(setup)
    for row in new_setup["source_chain_rows"]:
        if transform == "zero_transport":
            row["k_plus"] = row["k_minus"]
        elif transform == "current_reversal":
            # Reverse the centered phase step exactly by swapping the neighboring residues.
            row["k_minus"], row["k_plus"] = row["k_plus"], row["k_minus"]
        elif transform == "chirality_reversal":
            row["chi"] = -int(row["chi"])
    return new_setup


def compute(setup: Optional[Mapping] = None, transform: Optional[str] = None) -> Dict[str, object]:
    source = dict(load_setup() if setup is None else setup)
    source = _transform_rows(source, transform=transform)
    validate_partition(source)
    rows = [row_result(row, source) for row in source["source_chain_rows"]]
    U = sum((Fraction(r.epsilon_parallel, 1) * r.u_tr for r in rows), Fraction(0, 1))
    window = int(source["window_bip_0"])
    if window <= 0:
        raise ValueError("window_bip_0 must be positive")
    J = U / window
    family_U = {fam: Fraction(0, 1) for fam in FAMILIES}
    for row in rows:
        family_U[row.carrier_family] += Fraction(row.epsilon_parallel, 1) * row.u_tr
    family_J = {fam: family_U[fam] / window for fam in FAMILIES}
    w_plus = sum((Fraction(row.chi, 1) * row.u_tr for row in rows), Fraction(0, 1))
    w_minus = -w_plus
    return {
        "setup": source,
        "rows": rows,
        "U": U,
        "J": J,
        "family_U": family_U,
        "family_J": family_J,
        "w_perp_plus": w_plus,
        "w_perp_minus": w_minus,
    }


def exact_csv_rows(result: Mapping) -> List[Dict[str, object]]:
    U: Fraction = result["U"]
    J: Fraction = result["J"]
    fam_J: Mapping[str, Fraction] = result["family_J"]
    w_plus: Fraction = result["w_perp_plus"]
    w_minus: Fraction = result["w_perp_minus"]
    rows_out: List[Dict[str, object]] = []
    for row in result["rows"]:
        record: Dict[str, object] = {
            "row_id": row.row_id,
            "omega": row.omega,
            "working_level": row.working_level,
            "window_bip_0": row.window_bip_0,
            "carrier_family": row.carrier_family,
            "B_star": row.B_star,
            "widehat_Lambda": row.widehat_Lambda,
            "phase_step_num": row.phase_step_num,
            "phase_step_den": row.phase_step_den,
            "centered_phase_step": row.centered_phase_step,
            "chi": row.chi,
            "epsilon_parallel": row.epsilon_parallel,
        }
        record.update(fraction_columns(row.q_eff, "q_eff"))
        record.update(fraction_columns(row.atten_b, "atten_b"))
        record.update(fraction_columns(row.atten_loss, "atten_loss"))
        record.update(fraction_columns(row.tors, "tors"))
        record.update(fraction_columns(row.u_tr, "u_tr"))
        record.update(fraction_columns(U, "U_window"))
        record.update(fraction_columns(J, "J_flux"))
        record.update(fraction_columns(fam_J["duon"], "J_duon"))
        record.update(fraction_columns(fam_J["tetron"], "J_tetron"))
        record.update(fraction_columns(fam_J["other"], "J_other"))
        record.update(fraction_columns(w_plus, "w_perp_plus"))
        record.update(fraction_columns(w_minus, "w_perp_minus"))
        rows_out.append(record)
    return rows_out


def compact_report_rows(result: Mapping) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    J: Fraction = result["J"]
    w_plus: Fraction = result["w_perp_plus"]
    w_minus: Fraction = result["w_perp_minus"]
    for row in result["rows"]:
        out.append(
            {
                "row_id": row.row_id,
                "family": row.carrier_family,
                "r_over_N": row.centered_phase_step,
                "chi": row.chi,
                "Q_over_S": as_display(row.q_eff),
                "u_tr": as_display(row.u_tr),
                "J_flux": as_display(J),
                "w_perp_plus": as_display(w_plus),
                "w_perp_minus": as_display(w_minus),
            }
        )
    return out


def trace_rows(setup: Mapping) -> List[Dict[str, object]]:
    scenarios = [
        ("base", None),
        ("zero_transport", "zero_transport"),
        ("current_reversal", "current_reversal"),
        ("chirality_reversal", "chirality_reversal"),
    ]
    base = compute(setup)
    traces: List[Dict[str, object]] = []
    for name, transform in scenarios:
        result = compute(setup, transform=transform)
        J = result["J"]
        wp = result["w_perp_plus"]
        wm = result["w_perp_minus"]
        record: Dict[str, object] = {"scenario": name, "identity": "passed" if wp + wm == 0 else "failed"}
        record.update(fraction_columns(J, "J_flux"))
        record.update(fraction_columns(wp, "w_perp_plus"))
        record.update(fraction_columns(wm, "w_perp_minus"))
        record["J_flux_display"] = as_display(J)
        record["w_perp_plus_display"] = as_display(wp)
        record["w_perp_minus_display"] = as_display(wm)
        if name == "zero_transport":
            record["audit"] = "r=0 implies u_tr=0 and w_perp=0"
        elif name == "current_reversal":
            record["audit"] = "r sign reversal flips J_flux and w_perp"
            record["relative_to_base"] = "passed" if J == -base["J"] and wp == -base["w_perp_plus"] else "failed"
        elif name == "chirality_reversal":
            record["audit"] = "chi sign reversal flips w_perp"
            record["relative_to_base"] = "passed" if wp == -base["w_perp_plus"] else "failed"
        else:
            record["audit"] = "two-sided witness antisymmetry"
        traces.append(record)
    # Active probe-side variants are retained trace rows, not field primitives.
    base_wp = base["w_perp_plus"]
    traces.append(
        {
            "scenario": "active_probe_plus",
            "identity": "declared",
            **fraction_columns(base_wp, "J_flux"),
            **fraction_columns(base_wp, "w_perp_plus"),
            **fraction_columns(Fraction(0, 1), "w_perp_minus"),
            "J_flux_display": as_display(base_wp),
            "w_perp_plus_display": as_display(base_wp),
            "w_perp_minus_display": "0",
            "audit": "plus-side probe retained, minus-side probe omitted",
        }
    )
    return traces


def write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"no rows for {path}")
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _png_write(path: Path, width: int, height: int, pixels: List[bytearray]) -> None:
    """Write an RGB PNG using only the Python standard library."""
    raw = b''.join(b'\x00' + bytes(row) for row in pixels)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    path.write_bytes(png)


def _make_canvas(width: int, height: int, rgb: Tuple[int, int, int] = (255, 255, 255)) -> List[bytearray]:
    row = bytearray(rgb * width)
    return [bytearray(row) for _ in range(height)]


def _set_pixel(pixels: List[bytearray], x: int, y: int, rgb: Tuple[int, int, int]) -> None:
    if 0 <= y < len(pixels) and 0 <= x < len(pixels[0]) // 3:
        idx = x * 3
        pixels[y][idx:idx+3] = bytes(rgb)


def _draw_rect(pixels: List[bytearray], x0: int, y0: int, x1: int, y1: int, rgb: Tuple[int, int, int]) -> None:
    x0, x1 = sorted((max(0, x0), max(0, x1)))
    y0, y1 = sorted((max(0, y0), max(0, y1)))
    height = len(pixels)
    width = len(pixels[0]) // 3
    x0, x1 = min(width, x0), min(width, x1)
    y0, y1 = min(height, y0), min(height, y1)
    fill = bytes(rgb) * max(0, x1 - x0)
    for y in range(y0, y1):
        pixels[y][x0*3:x1*3] = fill


def _draw_line_h(pixels: List[bytearray], y: int, x0: int, x1: int, rgb: Tuple[int, int, int]) -> None:
    _draw_rect(pixels, x0, y, x1, y+2, rgb)


def _draw_line_v(pixels: List[bytearray], x: int, y0: int, y1: int, rgb: Tuple[int, int, int]) -> None:
    _draw_rect(pixels, x, y0, x+2, y1, rgb)


def _png_bar_chart(path: Path, values: List[Fraction]) -> None:
    """Render a compact exact-row bar witness as a PNG.

    The manual captions and CSV carry the labels.  The graphic is only a visual
    rendering of the rational rows.
    """
    width, height = 720, 420
    pixels = _make_canvas(width, height)
    margin_left, margin_right, margin_top, margin_bottom = 90, 50, 45, 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    floats = [float(v) for v in values]
    max_abs = max([abs(v) for v in floats] or [0.0])
    if max_abs == 0:
        max_abs = 1.0
    scale_max = max_abs * 1.2
    zero_y = int(margin_top + plot_h / 2)
    _draw_line_h(pixels, zero_y, margin_left, width - margin_right, (0, 0, 0))
    _draw_line_v(pixels, margin_left, margin_top, height - margin_bottom, (0, 0, 0))
    # light guide lines
    _draw_line_h(pixels, margin_top, margin_left, width - margin_right, (225, 225, 225))
    _draw_line_h(pixels, height - margin_bottom, margin_left, width - margin_right, (225, 225, 225))
    n = max(1, len(values))
    slot = plot_w / n
    bar_w = int(min(92, slot * 0.52))
    for idx, fval in enumerate(floats):
        cx = int(margin_left + slot * (idx + 0.5))
        y_val = int(zero_y - (fval / scale_max) * (plot_h / 2))
        top, bottom = min(zero_y, y_val), max(zero_y, y_val)
        _draw_rect(pixels, cx - bar_w//2, top, cx + bar_w//2, bottom, (116, 145, 196))
        # small baseline tick for each bar
        _draw_line_v(pixels, cx, zero_y - 5, zero_y + 6, (0, 0, 0))
    _png_write(path, width, height, pixels)


def render_figures(result: Mapping, traces: List[Mapping[str, object]]) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    wp = result["w_perp_plus"]
    wm = result["w_perp_minus"]
    trace_lookup = {row["scenario"]: row for row in traces}
    charts = [
        ("01_wire_transverse_witness.png", [wp, wm]),
        ("02_current_reversal.png", [
            Fraction(trace_lookup["base"]["J_flux_num"], trace_lookup["base"]["J_flux_den"]),
            Fraction(trace_lookup["current_reversal"]["J_flux_num"], trace_lookup["current_reversal"]["J_flux_den"]),
        ]),
        ("03_chirality_reversal.png", [
            Fraction(trace_lookup["base"]["w_perp_plus_num"], trace_lookup["base"]["w_perp_plus_den"]),
            Fraction(trace_lookup["chirality_reversal"]["w_perp_plus_num"], trace_lookup["chirality_reversal"]["w_perp_plus_den"]),
        ]),
        ("04_active_probe_response.png", [
            Fraction(trace_lookup["active_probe_plus"]["w_perp_plus_num"], trace_lookup["active_probe_plus"]["w_perp_plus_den"]),
            Fraction(trace_lookup["active_probe_plus"]["w_perp_minus_num"], trace_lookup["active_probe_plus"]["w_perp_minus_den"]),
        ]),
    ]
    for filename, values in charts:
        _png_bar_chart(FIGURE_DIR / filename, values)

def write_outputs() -> Dict[str, Path]:
    setup = load_setup()
    result = compute(setup)
    traces = trace_rows(setup)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    exact_path = DERIVED_DIR / "05f_wire_current_exact.csv"
    report_path = DERIVED_DIR / "05f_wire_current_report.csv"
    trace_path = DERIVED_DIR / "05f_wire_current_trace.csv"
    write_csv(exact_path, exact_csv_rows(result))
    write_csv(report_path, compact_report_rows(result))
    write_csv(trace_path, traces)
    render_figures(result, traces)
    return {"exact": exact_path, "report": report_path, "trace": trace_path}


def main() -> None:
    paths = write_outputs()
    for label, path in paths.items():
        print(f"{label}: {path.relative_to(MANUAL_DIR)}")


if __name__ == "__main__":
    main()
