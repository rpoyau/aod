// Audited S1b native Typst vector figure: sparc-declaration-controls (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/sparc_declaration_controls.csv)
// Historical raster retained byte-for-byte: manual/figures/sparc_declaration_controls.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 8.0

#let rows = csv("/manual/data/derived/sparc_declaration_controls.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let ys = rows.map(r => float(r.MAPE_U_percent))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).declaration]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.50, right: 0.45, top: 0.78, bottom: 1.85),
    title: [SPARC declaration controls],
    title-size: 10.2pt,
    ylabel: [$M A P E_U$ [%]],
    ylabel-dx: 1.05,
    xlim: (-0.56, 3.56),
    ylim: (0.0, 40.8),
    xticks: xticks,
    yticks: (0, 5, 10, 15, 20, 25, 30, 35, 40),
    x-tick-angle: -22deg,
    x-tick-size: 7.4pt,
    y-tick-size: 7.6pt,
    x-tick-dy: 0.80,
    grid-y: false,
    layers: (
      (type: "bars", xs: xs, ys: ys, bar-w: 0.80, fills: rgb("#1F77B4")),
    ),
  )
]
