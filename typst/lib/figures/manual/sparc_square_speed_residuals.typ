// Audited S1b native Typst vector figure: sparc-square-speed-residuals (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/sparc_five_galaxy_per_bin.csv, NGC3198)
// Historical raster retained byte-for-byte: manual/figures/sparc_square_speed_residuals.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 8.0

#let rows = csv("/manual/data/derived/sparc_five_galaxy_per_bin.csv", row-type: dictionary).filter(r => r.galaxy == "NGC3198").sorted(key: r => float(r.R))
#let rs = rows.map(r => float(r.R))
#let du = rows.map(r => float(r.Delta_U))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.95, right: 0.45, top: 0.78, bottom: 1.05),
    title: [SPARC square-speed residuals],
    title-size: 10.2pt,
    xlabel: [R [kpc]],
    ylabel: [$Delta U$ [$("km/s")^2$]],
    ylabel-dx: 1.48,
    xlim: (-1.9, 46.3),
    ylim: (-4750.0, 21800.0),
    xticks: (0, 10, 20, 30, 40),
    yticks: (0, 5000, 10000, 15000, 20000),
    grid-y: false,
    layers: (
      (type: "hline", y: 0.0, stroke: 0.85pt + rgb("#1F77B4")),
      (type: "line", xs: rs, ys: du, stroke: 1.35pt + rgb("#1F77B4")),
    ),
    legend: (
      pos: "top-left",
      col-w: 4.10,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#1F77B4"), label: [$Delta U$, primary declaration]),
      ),
    ),
  )
]
