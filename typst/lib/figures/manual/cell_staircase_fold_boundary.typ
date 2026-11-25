// Authored native Typst vector figure: cell-staircase-fold-boundary (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.5

#let rows = csv("/manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv", row-type: dictionary)
#let xs = rows.map(r => float(r.n))
#let ys-minus = (0.0, 1.0, 2.0, 41.0 / 16.0, 183.0 / 64.0, 385.0 / 128.0)
#let ys-plus = rows.map(r => float(r.A_plus_dec6))
#let ys-c = rows.map(r => float(r.C_axial))
#let r32 = rows.at(5)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.20, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Unit-disk rational cell enclosure, axial staircase boundary $C_n = 8$ & fold chain law*], size: 9.9pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("cell")) -> B_(upright("stair")) -> B_(upright("fold")) -> B_(upright("audit")) -> B_(upright("ext"))$: exact integer cell counts without continuum $pi$ smuggled.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Cartesian plot of A_n^-, A_n^+ vs C_n = 8 across n in {1, 2, 4, 8, 16, 32}
  #aod-box-tl(0.38, 1.34, 7.30, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 0.45,
    y0: 1.44,
    w: 7.12,
    h: 5.56,
    pad: (left: 1.18, right: 0.32, top: 0.68, bottom: 0.96),
    title: [(a) Area bounds $A_n^-, A_n^+$ vs axial boundary $C_n = 8$],
    title-size: 7.9pt,
    xlabel: [Refinement index $n in \{1, 2, 4, 8, 16, 32\}$],
    ylabel: [Exact rational measure],
    xlim: (0.0, 34.0),
    ylim: (0.0, 9.2),
    xticks: (1, 4, 8, 16, 32),
    yticks: (0, 2, 4, 6, 8),
    x-tick-size: 6.9pt,
    y-tick-size: 6.9pt,
    ylabel-dx: 0.86,
    layers: (
      (type: "line", xs: xs, ys: ys-c, stroke: (paint: aod-pal.crimson, thickness: 1.25pt, dash: "dashed"), marker: "cross", marker-color: aod-pal.crimson, marker-r: 2.2),
      (type: "line", xs: xs, ys: ys-plus, stroke: 1.25pt + aod-pal.blue, marker: "circle", marker-color: aod-pal.blue, marker-r: 2.2),
      (type: "line", xs: xs, ys: ys-minus, stroke: 1.25pt + aod-pal.teal, marker: "open-circle", marker-color: aod-pal.teal, marker-r: 2.2),
    ),
    legend: (
      pos: "center",
      cols: 1,
      col-w: 3.85,
      size: 6.8pt,
      items: (
        (kind: "line", color: aod-pal.crimson, dash: "dashed", label: [$C_n = 8$ (invariant staircase)]),
        (kind: "line", color: aod-pal.blue, marker: "circle", label: [$A_n^+$ ($n=32$: $#r32.A_plus_exact$)]),
        (kind: "line", color: aod-pal.teal, marker: "open-circle", label: [$A_n^-$ ($n=32$: $#r32.A_minus_exact$)]),
      ),
    ),
  )

  // Panel B (Right): Two-square fold partial circ f_hash = f_hash circ partial
  #aod-box-tl(7.88, 1.34, 6.72, 5.78, [], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(11.24, 1.66, [*(b) Cellular fold commutation* $partial circle.tiny f_(upright("#")) = f_(upright("#")) circle.tiny partial$], size: 7.8pt, box-w: 6.4, box-h: 0.36)

  // Left pre-fold two oriented squares Q_L + Q_R
  #aod-box-tl(8.18, 2.20, 1.28, 1.28, [$+Q_L$], stroke: 1.05pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 0pt)
  #aod-box-tl(9.46, 2.20, 1.28, 1.28, [$+Q_R$], stroke: 1.05pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 0pt)
  // Shared vertical seam cancels (+1 - 1 = 0)
  #aod-line(9.46, 2.20, 9.46, 3.48, stroke: (paint: aod-pal.crimson, thickness: 1.2pt, dash: "dashed"))
  #aod-text(9.46, 1.98, [seam $+1 - 1 = 0$], size: 6.8pt, box-w: 2.4, box-h: 0.28)
  #aod-text(9.46, 3.74, [Pre-fold $K_2$: $6$ outer edges], size: 6.8pt, box-w: 2.8, box-h: 0.30)

  // Fold arrow f_hash
  #aod-arrow(10.92, 2.84, 12.02, 2.84, stroke: 1.2pt + aod-pal.purple)
  #aod-text(11.47, 2.50, [$f_(upright("#"))$ fold], size: 6.9pt, weight: "bold", box-w: 1.3, box-h: 0.30)

  // Post-fold single target square 2 Q_* with top edge cancelled & 3 edges multiplicity 2
  #aod-box-tl(12.22, 2.20, 1.50, 1.28, [$2 Q_*$], stroke: 1.35pt + aod-pal.purple, fill: white, radius: 0pt)
  // Top edge orientation reversal cancellation (+e_top - e_top = 0)
  #aod-line(12.22, 2.20, 13.72, 2.20, stroke: (paint: aod-pal.crimson, thickness: 1.3pt, dash: "dashed"))
  #aod-text(12.97, 1.98, [top $+1 - 1 = 0$], size: 6.8pt, box-w: 2.2, box-h: 0.28)
  #aod-text(12.97, 3.74, [3 sides weight $2$, top $0$], size: 6.8pt, box-w: 2.6, box-h: 0.30)

  // Boundary firewall & exact audit card
  #aod-boundary-wall(8.14, 4.18, 14.34, 4.18, stroke: 1.05pt + aod-pal.navy, hatch-side: 1, hatch-count: 8)
  #aod-box-tl(
    8.14, 4.38, 6.20, 2.48,
    [#text(size: 6.9pt)[
      *Boundary-audit falsifiers ($B_(upright("audit"))$):* \
      1. Refinement gap $A_(32)^+ - A_(32)^- = #r32.enclosure_width$, while axial $C_n = 8$ for every $n$ ($C_n r - 2 A_(32)^+ = #r32.Cr_minus_2Aplus != 0$). \
      2. Naive support boundary $partial(op("supp") f_(upright("#"))(K_2))$ gives $4$ unit edges ($!= 2 e_b + 2 e_l + 2 e_r$); multiplicity-bearing $f_(upright("#"))$ is mandatory. \
      3. Continuum $pi$ lives only in $B_(upright("ext")) = sans("Q")_(upright("ext"))$, never as a native cell premise.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-035: monotone rational cell bounds $A_n^- <= A_n^+$, invariant staircase $C_n = 8$, and exact chain-map commutation] $partial circle.tiny f_(upright("#")) - f_(upright("#")) circle.tiny partial = 0$.],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
