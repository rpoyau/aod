// Audited S1b native Typst vector figure: tau-ring-support-score (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/tau_ring_diagnostic.csv)
// Historical raster retained byte-for-byte: manual/figures/tau_ring_support_score.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.0
#let fig-height-cm = 7.8

#let rows = csv("/manual/data/derived/tau_ring_diagnostic.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let s-cell = rows.map(r => float(r.S_tau))
#let s-ring = rows.map(r => float(r.S_tau_ring))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).K]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.60, right: 0.45, top: 0.78, bottom: 1.05),
    title: [Tau ring support score],
    title-size: 10.2pt,
    xlabel: [candidate],
    ylabel: [$S_tau$ [lower is better]],
    ylabel-dx: 1.15,
    xlim: (-0.15, 3.15),
    ylim: (-0.23, 2.39),
    xticks: xticks,
    yticks: ((0.0, [0.0]), (0.5, [0.5]), (1.0, [1.0]), (1.5, [1.5]), (2.0, [2.0])),
    grid-y: false,
    layers: (
      (type: "hline", y: 0.0, stroke: 0.8pt + aod-pal.slate),
      (type: "line", xs: xs, ys: s-cell, stroke: 1.3pt + rgb("#1F77B4"), marker: "circle", marker-r: 2.5),
      (type: "line", xs: xs, ys: s-ring, stroke: 1.3pt + rgb("#FF7F0E"), marker: "circle", marker-r: 2.5),
    ),
    legend: (
      pos: "top-left",
      col-w: 2.95,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#1F77B4"), marker: "circle", label: [A$Omega$ cell score]),
        (kind: "line", color: rgb("#FF7F0E"), marker: "circle", label: [A$Omega$ ring score]),
      ),
    ),
  )
]
