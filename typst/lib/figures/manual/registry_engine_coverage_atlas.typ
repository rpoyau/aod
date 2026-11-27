// Authored native Typst vector figure: registry-engine-coverage-atlas (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv, manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.2
#let y-off = 0.74

#let re-rows = csv("/manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv", row-type: dictionary)
#let so-rows = csv("/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv", row-type: dictionary)
#let n-re = re-rows.len()
#let n-so = so-rows.len()

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Master prediction-test & fixture registry: S2/S4 engine parity & data-support firewall],
    subtitle: [All $18$ Manual units bound to $53$ cross-language golden vectors (RC-001..RC-045, SD-001..SD-008) & $20$ boundary-SADAR CSVs.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.4pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.12,
  )

  // Panel A (Left): Dual S2 Python + S4 Rust Zero-Float Engine Verification Architecture
  #aod-box-tl(0.38, 1.36 + y-off, 6.95, 5.66, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.85, 1.66 + y-off, [*(a) Dual zero-float execution spine (S2 Python $==$ S4 Rust)*], size: 6.9pt, box-w: 6.82, box-h: 0.34)

  #aod-box-tl(
    0.62, 2.08 + y-off, 2.95, 1.85,
    [#text(size: 6.8pt)[
      *S2 Reference Engine:* \
      Pure Python $bb(Z) slash bb(Q)$ \
      $18$ verified sectors \
      Normal $==$ $-O$ byte parity
    ]],
    stroke: 0.85pt + aod-pal.blue,
    fill: white,
    inset: 3.5pt,
    leading: 0.36em,
  )
  #aod-box-tl(
    4.12, 2.08 + y-off, 2.95, 1.85,
    [#text(size: 6.8pt)[
      *S4 Exact Core:* \
      Rust std-only $bb(Z) slash bb(Q)$ \
      Zero floats, zero unsafe \
      Debug $==$ release parity
    ]],
    stroke: 0.85pt + aod-pal.teal,
    fill: white,
    inset: 3.5pt,
    leading: 0.36em,
  )
  #aod-arrow(3.60, 3.00 + y-off, 4.09, 3.00 + y-off, stroke: 1.1pt + aod-pal.navy, both: true)

  #aod-box-tl(
    0.62, 4.20 + y-off, 6.45, 2.58,
    [#text(size: 6.8pt)[
      *Golden-vector & frozen-table invariants:* \
      *(1)* $45$ rational-core vectors (RC-001..RC-045) + $8$ symbolic/display vectors (SD-001..SD-008) $= 53$ locked vectors. \
      *(2)* $20$ deterministic CSVs under boundary\_sadar ($#n-re$ rest-energy/debris carriers, $#n-so$ solar O0 scopes, SPARC $209$ bins, hydrogen $14$ lines, lensing $4$ shells). \
      *(3)* Pre-freeze native candidate selection precedes every $sans("Q")_(upright("ext"))$ target join.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    align-mode: left + horizon,
    inset: 4.5pt,
    leading: 0.36em,
  )

  // Panel B (Right): Data-Support Class Firewall (D0 -> O0 -> G0..G3 -> L0..L3)
  #aod-box-tl(7.55, 1.36 + y-off, 7.05, 5.66, [], stroke: 0.85pt + aod-pal.purple, fill: white, radius: 4pt)
  #aod-text(11.08, 1.66 + y-off, [*(b) Golden-vector coverage by registry tier ($53$ total)*], size: 7.0pt, box-w: 6.85, box-h: 0.34)
  #aod-xy-plot(
    x0: 7.62,
    y0: 1.46 + y-off,
    w: 6.88,
    h: 5.44,
    pad: (left: 1.04, right: 0.34, top: 0.68, bottom: 1.18),
    title: none,
    xlabel: [Registry verification family],
    ylabel: [Locked golden vectors],
    xlim: (0.3, 4.7),
    ylim: (0.0, 29.5),
    xticks: (
      (1, [Core \ $1..24$]),
      (2, [SADAR \ $25..32$]),
      (3, [Manual \ $33..45$]),
      (4, [Display \ SD]),
    ),
    x-tick-dy: 0.38,
    xlabel-dy: 0.90,
    yticks: (0, 8, 16, 24),
    x-tick-size: 6.6pt,
    y-tick-size: 6.8pt,
    ylabel-dx: 0.78,
    layers: (
      (
        type: "bars",
        xs: (1.0, 2.0, 3.0, 4.0),
        ys: (24.0, 8.0, 13.0, 8.0),
        bar-w: 0.56,
        fills: (aod-pal.navy, aod-pal.blue, aod-pal.teal, aod-pal.purple),
        stroke: 0.55pt + aod-pal.axis,
        value-labels: ([$24$], [$8$], [$13$], [$8$]),
      ),
    ),
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.24 + y-off, 14.22, 0.78,
    [#text(size: 7.1pt, weight: "bold")[Registry lock: $18 slash 18$ Manual units carry explicit $5$-boundary stacks, native vector figures, captioned D.E.C. tables, and S2/S4 vectors ($53 slash 53$).]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
