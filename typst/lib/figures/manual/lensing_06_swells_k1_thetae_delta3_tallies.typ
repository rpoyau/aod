// Audited S1b native Typst vector figure: lensing-06-swells-k1-thetae-delta3-tallies (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/lensing/swells_k1_thetaE_delta3_scores.csv)
// Historical raster retained byte-for-byte: manual/figures/lensing/06_swells_k1_thetaE_delta3_tallies.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 7.8

#let rows = csv("/manual/data/lensing/swells_k1_thetaE_delta3_scores.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let t-pred = rows.map(r => float(r.T_cross_predicted_tally))
#let o-obs = rows.map(r => float(r.O_observed_tally))
#let m-vals = rows.map(r => float(r.m))
#let bin-label(k) = {
  if k == "theta_low_<0.75" { [$theta_E < 0.75$] }
  else if k == "theta_mid_0.75_1.00" { [$0.75 <= theta_E < 1.00$] }
  else if k == "theta_high_>=1.00" { [$theta_E >= 1.00$] }
  else { [#k] }
}
#let xticks = range(rows.len()).map(i => (float(i), bin-label(rows.at(i).class_k)))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.40, right: 0.45, top: 0.72, bottom: 1.38),
    title: [SWELLS K1 $theta_E$ $delta_3$ tallies],
    title-size: 10.2pt,
    ylabel: [integer tally],
    ylabel-dx: 0.96,
    xlim: (-0.50, 2.50),
    ylim: (0.0, 12.6),
    xticks: xticks,
    yticks: (0, 2, 4, 6, 8, 10, 12),
    x-tick-angle: -20deg,
    x-tick-size: 7.4pt,
    y-tick-size: 7.4pt,
    x-tick-dy: 0.56,
    grid-y: true,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.72,
        series: (
          (ys: t-pred, fill: rgb("#1F77B4")),
          (ys: o-obs, fill: rgb("#FF7F0E")),
        ),
      ),
      (type: "line", xs: xs, ys: m-vals, stroke: 1.25pt + rgb("#1F77B4"), marker: "circle", marker-r: 2.5),
    ),
    legend: (
      pos: "top-right",
      col-w: 2.65,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#1F77B4"), marker: "circle", label: [$m$]),
        (kind: "patch", color: rgb("#1F77B4"), label: [$T^times$ predicted]),
        (kind: "patch", color: rgb("#FF7F0E"), label: [target tally $O$]),
      ),
    ),
  )
]
