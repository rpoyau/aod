// Audited S1b native Typst vector figure: solar-calculated-vs-target (Manual)
// Provenance: DATA_BACKED_VERIFIED (carried O0 table tab:manual-solar-observable-map-results)
// Historical raster retained byte-for-byte: manual/figures/solar_calculated_vs_target.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 8.0

// Exact O0 records from <tab:manual-solar-observable-map-results>
#let xs = (0.0, 1.0, 2.0)
#let ao-vals = (42.9799, 1.75001, 2.11996e-6)
#let tgt-vals = (42.98, 1.75, 2.12e-6)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.75, right: 0.45, top: 0.78, bottom: 1.48),
    title: [Solar-system field tests: A$arrow.l.r Omega$ value vs target],
    title-size: 10.2pt,
    ylabel: [value (log scale)],
    ylabel-dx: 1.25,
    xlim: (-0.50, 2.50),
    ylim: (1e-6, 95.0),
    ylog: true,
    xticks: ((0.0, [Mercury perihelion]), (1.0, [Light bending]), (2.0, [Solar redshift])),
    yticks: (
      (1e-6, [$10^(-6)$]),
      (1e-5, [$10^(-5)$]),
      (1e-4, [$10^(-4)$]),
      (1e-3, [$10^(-3)$]),
      (1e-2, [$10^(-2)$]),
      (1e-1, [$10^(-1)$]),
      (1.0, [$10^0$]),
      (10.0, [$10^1$]),
    ),
    x-tick-angle: -18deg,
    x-tick-size: 7.6pt,
    y-tick-size: 7.4pt,
    x-tick-dy: 0.56,
    grid-y: false,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.72,
        base: 1e-6,
        series: (
          (ys: ao-vals, fill: rgb("#1F77B4")),
          (ys: tgt-vals, fill: rgb("#FF7F0E")),
        ),
      ),
    ),
    legend: (
      pos: "top-right",
      col-w: 2.65,
      size: 7.6pt,
      items: (
        (kind: "patch", color: rgb("#1F77B4"), label: [A$arrow.l.r Omega$ value]),
        (kind: "patch", color: rgb("#FF7F0E"), label: [Target]),
      ),
    ),
  )
]
