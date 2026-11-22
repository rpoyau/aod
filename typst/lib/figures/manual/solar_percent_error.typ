// Audited S1b native Typst vector figure: solar-percent-error (Manual)
// Provenance: DATA_BACKED_VERIFIED (carried O0 table tab:manual-solar-observable-map-results)
// Historical raster retained byte-for-byte: manual/figures/solar_percent_error.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 8.0

// Exact absolute percent errors [%] from <tab:manual-solar-observable-map-results>
#let xs = (0.0, 1.0, 2.0)
#let errs = (0.0002327, 0.0005714, 0.001887)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 2.15, right: 0.45, top: 0.78, bottom: 1.48),
    title: [Solar-system field tests: percent error],
    title-size: 10.2pt,
    ylabel: [$abs("percent error")$ [%], log scale],
    ylabel-dx: 1.65,
    xlim: (-0.54, 2.54),
    ylim: (2.08e-4, 2.10e-3),
    ylog: true,
    xticks: ((0.0, [Mercury perihelion]), (1.0, [Light bending]), (2.0, [Solar redshift])),
    yticks: (
      (3e-4, [$3 times 10^(-4)$]),
      (4e-4, [$4 times 10^(-4)$]),
      (6e-4, [$6 times 10^(-4)$]),
      (1e-3, [$10^(-3)$]),
      (2e-3, [$2 times 10^(-3)$]),
    ),
    x-tick-angle: -18deg,
    x-tick-size: 7.6pt,
    y-tick-size: 7.4pt,
    x-tick-dy: 0.56,
    grid-y: false,
    layers: (
      (type: "bars", xs: xs, ys: errs, bar-w: 0.78, base: 2.08e-4, fills: rgb("#1F77B4")),
    ),
  )
]
