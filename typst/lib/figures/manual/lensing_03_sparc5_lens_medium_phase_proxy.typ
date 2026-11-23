// Audited S1b native Typst vector figure: lensing-03-sparc5-lens-medium-phase-proxy (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/lensing/sparc5_medium_diagnostic_summary.csv)
// Historical raster retained byte-for-byte: manual/figures/lensing/03_sparc5_lens_medium_phase_proxy.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.4
#let fig-height-cm = 7.4

#let rows = csv("/manual/data/lensing/sparc5_medium_diagnostic_summary.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let med-v = rows.map(r => float(r.at("median_abs_ΔAγ")))
#let max-v = rows.map(r => float(r.at("max_abs_ΔAγ")))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).galaxy]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.50, right: 0.45, top: 0.72, bottom: 0.85),
    title: [SPARC5 lens-medium diagnostic],
    title-size: 10.0pt,
    ylabel: [diagnostic magnitude],
    ylabel-dx: 1.05,
    xlim: (-0.58, 4.58),
    ylim: (0.0, 2.76),
    xticks: xticks,
    yticks: ((0.0, [0.0]), (0.5, [0.5]), (1.0, [1.0]), (1.5, [1.5]), (2.0, [2.0]), (2.5, [2.5])),
    x-tick-size: 7.6pt,
    y-tick-size: 7.4pt,
    grid-y: true,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.70,
        series: (
          (ys: med-v, fill: rgb("#1F77B4")),
          (ys: max-v, fill: rgb("#FF7F0E")),
        ),
      ),
    ),
    legend: (
      pos: "top-left",
      col-w: 2.65,
      size: 7.4pt,
      items: (
        (kind: "patch", color: rgb("#1F77B4"), label: [median $abs(Delta A_gamma)$]),
        (kind: "patch", color: rgb("#FF7F0E"), label: [max $abs(Delta A_gamma)$]),
      ),
    ),
  )
]
