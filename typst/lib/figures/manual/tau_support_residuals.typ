// Audited S1b native Typst vector figure: tau-support-residuals (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/tau_ring_diagnostic.csv)
// Historical raster retained byte-for-byte: manual/figures/tau_support_residuals.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.0
#let fig-height-cm = 7.8

#let rows = csv("/manual/data/derived/tau_ring_diagnostic.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let s-ring = rows.map(r => float(r.S_tau_ring))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).K]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.55, right: 0.45, top: 0.78, bottom: 1.05),
    title: [Tau-support residuals],
    title-size: 10.2pt,
    xlabel: [candidate],
    ylabel: [$Delta S_tau$],
    ylabel-dx: 1.10,
    xlim: (-0.15, 3.15),
    ylim: (-0.22, 2.26),
    xticks: xticks,
    yticks: ((0.0, [0.0]), (0.5, [0.5]), (1.0, [1.0]), (1.5, [1.5]), (2.0, [2.0])),
    grid-y: false,
    layers: (
      (type: "hline", y: 0.0, stroke: 0.75pt + aod-pal.slate),
      (type: "line", xs: xs, ys: s-ring, stroke: 1.35pt + rgb("#0D2B45"), marker: "circle", marker-r: 2.6),
    ),
    legend: (
      pos: "top-left",
      col-w: 4.10,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#0D2B45"), marker: "circle", label: [$Delta S_tau$, primary declaration]),
      ),
    ),
  )
]
