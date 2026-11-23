// Audited S1b native Typst vector figure: tau-declaration-controls (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/tau_declaration_controls.csv)
// Historical raster retained byte-for-byte: manual/figures/tau_declaration_controls.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 8.0

#let rows = csv("/manual/data/derived/tau_declaration_controls.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let ys = rows.map(r => float(r.winner_margin_percent))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).declaration]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.60, right: 0.45, top: 0.78, bottom: 1.62),
    title: [Tau declaration controls],
    title-size: 10.2pt,
    ylabel: [winner margin [%]],
    ylabel-dx: 1.15,
    xlim: (-0.56, 3.56),
    ylim: (0.0, 174.5),
    xticks: xticks,
    yticks: (0, 20, 40, 60, 80, 100, 120, 140, 160),
    x-tick-angle: -20deg,
    x-tick-size: 7.5pt,
    y-tick-size: 7.6pt,
    x-tick-dy: 0.66,
    grid-y: false,
    layers: (
      (type: "bars", xs: xs, ys: ys, bar-w: 0.80, fills: rgb("#1F77B4")),
    ),
  )
]
