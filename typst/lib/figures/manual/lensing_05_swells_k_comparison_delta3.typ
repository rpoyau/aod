// Audited S1b native Typst vector figure: lensing-05-swells-k-comparison-delta3 (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/lensing/swells_k1_k2_k3_delta3_comparison.csv)
// Historical raster retained byte-for-byte: manual/figures/lensing/05_swells_k_comparison_delta3.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 7.6

#let rows = csv("/manual/data/lensing/swells_k1_k2_k3_delta3_comparison.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let th-m = rows.map(r => float(r.thetaE_delta3_total_m))
#let sig-m = rows.map(r => float(r.sigma_delta3_total_m))
#let xticks = range(rows.len()).map(i => (float(i), [#rows.at(i).run]))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.55, right: 0.45, top: 0.72, bottom: 0.85),
    title: [SWELLS K1/K2/K3 $delta_3$ comparison],
    title-size: 10.2pt,
    ylabel: [$delta_3$ residual magnitude],
    ylabel-dx: 1.12,
    xlim: (-0.50, 2.50),
    ylim: (0.0, 18.9),
    xticks: xticks,
    yticks: ((0.0, [0.0]), (2.5, [2.5]), (5.0, [5.0]), (7.5, [7.5]), (10.0, [10.0]), (12.5, [12.5]), (15.0, [15.0]), (17.5, [17.5])),
    grid-y: true,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.70,
        series: (
          (ys: th-m, fill: rgb("#1E4E79")),
          (ys: sig-m, fill: rgb("#B28400")),
        ),
      ),
    ),
    legend: (
      pos: "top-right",
      col-w: 2.35,
      size: 7.4pt,
      items: (
        (kind: "patch", color: rgb("#1E4E79"), label: [$theta_E$ total $m$]),
        (kind: "patch", color: rgb("#B28400"), label: [$sigma$ total $m$]),
      ),
    ),
  )
]
