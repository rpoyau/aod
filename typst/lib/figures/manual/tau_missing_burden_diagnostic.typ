// Audited S1b native Typst vector figure: tau-missing-burden-diagnostic (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/tau_ring_diagnostic.csv + dec exact ratio patch CSV)
// Historical raster retained byte-for-byte: manual/figures/tau_missing_burden_diagnostic.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.0
#let fig-height-cm = 7.8

#let rows = csv("/manual/data/derived/tau_ring_diagnostic.csv", row-type: dictionary)
#let patch = csv("/manual/data/dec/tau_missing_burden_exact_ratio_patch.csv", row-type: dictionary)
#let target = float(patch.at(0).missing_num) / float(patch.at(0).missing_den)
#let xs = range(rows.len()).map(i => float(i))
#let mf = rows.map(r => float(r.missing_fraction))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).K]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.65, right: 0.45, top: 0.78, bottom: 1.05),
    title: [Tau missing-burden diagnostic],
    title-size: 10.2pt,
    xlabel: [candidate],
    ylabel: [missing fraction],
    ylabel-dx: 1.20,
    xlim: (-0.15, 3.15),
    ylim: (0.242, 0.638),
    xticks: xticks,
    yticks: ((0.25, [0.25]), (0.30, [0.30]), (0.35, [0.35]), (0.40, [0.40]), (0.45, [0.45]), (0.50, [0.50]), (0.55, [0.55]), (0.60, [0.60])),
    grid-y: false,
    layers: (
      (type: "hline", y: target, stroke: 1.35pt + rgb("#0D2B45")),
      (type: "line", xs: xs, ys: mf, stroke: 1.35pt + rgb("#C46C2B"), marker: "circle", marker-r: 2.6),
    ),
    legend: (
      pos: "bottom-left",
      col-w: 4.35,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#0D2B45"), label: [Tau missing-burden target]),
        (kind: "line", color: rgb("#C46C2B"), marker: "circle", label: [A$Omega$ missing fraction]),
      ),
    ),
  )
]
