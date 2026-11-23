// Audited S1b native Typst vector figure: field-dynamics-layered-main (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_field_dynamics_layered.py --main)
// Historical raster retained byte-for-byte: figures_jpg/field_dynamics_layered_main.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 13.8
#let fig-height-cm = 15.2

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Title & subtitle
  #aod-text(6.9, 0.46, [*LAYERED FIELD DYNAMICS*], size: 12.5pt, box-w: 13.2, box-h: 0.6)
  #aod-text(6.9, 0.92, [core coupling, support/current lift, and exoshedding], size: 8.8pt, box-w: 13.2, box-h: 0.45)

  // Center of concentric field layers (scale: 1 unit = 4.35 cm)
  #let cx = 6.10
  #let cy = 7.35
  #let sc = 4.35

  // 8 concentric layer boundaries
  #let radii = range(8).map(i => 0.13 + i * (0.88 - 0.13) / 7.0)
  #for i in range(radii.len()) {
    let r = radii.at(i) * sc
    let lw = if i == 0 or i == 7 { 1.35pt } else { 0.8pt }
    let col = if calc.rem(i, 2) == 1 { rgb("#6E8198") } else { rgb("#B9C2CC") }
    aod-circle(cx, cy, r, fill: none, stroke: lw + col)
  }

  // Core
  #aod-circle(cx, cy, 0.05 * sc, fill: rgb("#0B1D34"), stroke: none)
  #aod-text(cx, cy + 0.092 * sc, [core], size: 7.1pt, box-w: 1.4, box-h: 0.36)

  // Same-direction CCW circulation arrows
  #for idx in range(1, radii.len()) {
    let r = radii.at(idx) * sc
    let lw = (0.75 + 0.06 * idx) * 1pt
    for base in (35, 120, 205, 290) {
      aod-arc-arrow(cx, cy, r, base, base + 24, stroke: lw + aod-pal.navy, head-len: 3.3, head-half: 1.5)
    }
  }
  #for rr in (0.18, 0.23, 0.28, 0.34, 0.42, 0.52) {
    for base in (55, 150, 245, 335) {
      aod-arc-arrow(cx, cy, rr * sc, base, base + 25, stroke: 0.8pt + rgb("#0B1D34"), head-len: 3.0, head-half: 1.4)
    }
  }

  // Inter-layer coupling channels (solid teal radial connectors with endpoint dots)
  #for (deg, r0, r1) in ((22, 0.36, 0.64), (62, 0.46, 0.78), (145, 0.30, 0.55), (215, 0.42, 0.68), (302, 0.50, 0.78)) {
    let rad = deg * 1deg
    let x0 = cx + r0 * sc * calc.cos(rad)
    let y0 = cy - r0 * sc * calc.sin(rad)
    let x1 = cx + r1 * sc * calc.cos(rad)
    let y1 = cy - r1 * sc * calc.sin(rad)
    aod-line(x0, y0, x1, y1, stroke: 1.4pt + aod-pal.teal)
    aod-circle(x0, y0, 0.055, fill: aod-pal.teal, stroke: none)
    aod-circle(x1, y1, 0.055, fill: aod-pal.teal, stroke: none)
  }

  // Exoshedding / decoupling dashed arrows outward
  #for (deg, r0, r1) in ((0, 0.82, 1.05), (45, 0.70, 0.98), (90, 0.72, 1.07), (135, 0.72, 0.98), (180, 0.82, 1.05), (225, 0.72, 0.98), (270, 0.72, 1.07), (315, 0.72, 0.98)) {
    let rad = deg * 1deg
    let x0 = cx + r0 * sc * calc.cos(rad)
    let y0 = cy - r0 * sc * calc.sin(rad)
    let x1 = cx + r1 * sc * calc.cos(rad)
    let y1 = cy - r1 * sc * calc.sin(rad)
    aod-arrow(x0, y0, x1, y1, stroke: (paint: aod-pal.teal, thickness: 0.95pt, dash: "dashed"), head-len: 3.8, head-half: 1.8)
  }

  // Four non-overlapping leader callouts
  // Top-left: core coupling
  #aod-line(cx - 0.17 * sc, cy - 0.13 * sc, 2.25, 2.75, stroke: 0.85pt + rgb("#0B1D34"))
  #aod-text(0.45, 2.28, [*core coupling* \ strongest retained coupling; \ seeds retained circulation], size: 7.4pt, anchor: "left", box-w: 3.8, box-h: 1.1)

  // Top-right: inter-layer coupling
  #aod-line(cx + 0.55 * sc, cy - 0.67 * sc, 9.90, 2.65, stroke: 0.85pt + rgb("#0B1D34"))
  #aod-text(9.85, 2.28, [*inter-layer coupling* \ retained transfer through \ declared channels], size: 7.4pt, anchor: "left", box-w: 3.7, box-h: 1.1)

  // Bottom-right: support/current lift
  #aod-line(cx + 0.66 * sc, cy + 0.55 * sc, 10.10, 11.00, stroke: 0.85pt + rgb("#0B1D34"))
  #aod-text(9.85, 11.45, [*support/current lift* \ exoshedding routes surplus \ toward outer boundaries], size: 7.4pt, anchor: "left", box-w: 3.7, box-h: 1.1)

  // Bottom-center: outer-layer coupling
  #aod-line(cx, cy + 0.89 * sc, 5.10, 12.15, stroke: 0.85pt + rgb("#0B1D34"))
  #aod-text(4.85, 12.68, [*outer-layer coupling* \ broader retained circulation; \ redistribution and recycling], size: 7.4pt, anchor: "center", box-w: 4.5, box-h: 1.1)

  // Right inset A: LIFT / EXOSHEDDING VIEW (cleanly sized so title fits inside frame)
  #aod-box-tl(10.15, 3.55, 3.35, 3.60, [], stroke: 0.9pt + rgb("#6E8198"), fill: white, radius: 3.5pt)
  #aod-text(11.825, 4.10, [*A. LIFT / EXOSHEDDING* \ *VIEW*], size: 7.1pt, box-w: 3.15, box-h: 0.72)
  #let icx = 11.12
  #let icy = 5.34
  #for rr in (0.16, 0.29, 0.42, 0.55) {
    aod-circle(icx, icy, rr, fill: none, stroke: 0.7pt + aod-pal.navy)
  }
  #for deg in (-32, 0, 32) {
    let rad = deg * 1deg
    aod-arrow(
      icx + 0.55 * calc.cos(rad), icy - 0.55 * calc.sin(rad),
      icx + 0.92 * calc.cos(rad), icy - 0.92 * calc.sin(rad),
      stroke: (paint: aod-pal.teal, thickness: 0.75pt, dash: "dashed"), head-len: 3.0, head-half: 1.4,
    )
  }
  #for dx in (0.0, 0.28, 0.56) {
    aod-arrow(12.22 + dx, 5.89, 12.22 + dx, 4.79, stroke: 0.85pt + aod-pal.navy, head-len: 3.2, head-half: 1.5)
  }
  #aod-text(11.825, 6.56, [support/current lifts \ from inner layers \ along sheddic routes], size: 7.0pt, box-w: 3.1, box-h: 1.0)

  // Clean 2-row Arrow key legend at bottom (zero overlap)
  #aod-box-tl(1.10, 13.55, 11.60, 1.35, [], stroke: 0.65pt + rgb("#D0D7DE"), fill: aod-pal.tint-gray, radius: 3pt)
  #aod-text(1.40, 14.22, [*Arrow key:*], size: 8.0pt, anchor: "left", box-w: 2.0, box-h: 0.5)
  // Row 1
  #aod-arrow(3.45, 13.92, 4.35, 13.92, stroke: 1.1pt + aod-pal.navy, head-len: 3.8, head-half: 1.8)
  #aod-text(4.52, 13.92, [circulation], size: 7.6pt, anchor: "left", box-w: 2.6, box-h: 0.4)
  #aod-line(7.40, 13.92, 8.30, 13.92, stroke: 1.4pt + aod-pal.teal)
  #aod-circle(7.40, 13.92, 0.05, fill: aod-pal.teal, stroke: none)
  #aod-circle(8.30, 13.92, 0.05, fill: aod-pal.teal, stroke: none)
  #aod-text(8.48, 13.92, [inter-layer coupling], size: 7.6pt, anchor: "left", box-w: 3.8, box-h: 0.4)
  // Row 2
  #aod-arrow(3.45, 14.52, 4.35, 14.52, stroke: (paint: aod-pal.teal, thickness: 0.95pt, dash: "dashed"), head-len: 3.8, head-half: 1.8)
  #aod-text(4.52, 14.52, [decoupling / lift], size: 7.6pt, anchor: "left", box-w: 2.8, box-h: 0.4)
  #aod-line(7.40, 14.52, 8.30, 14.52, stroke: 1.35pt + rgb("#B9C2CC"))
  #aod-text(8.48, 14.52, [layer boundary], size: 7.6pt, anchor: "left", box-w: 3.5, box-h: 0.4)
]
