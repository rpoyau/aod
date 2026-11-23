// Audited S1b native Typst vector figure: lensing-01-toy1-delta3-class-tallies (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/lensing/toy1_delta3_class_tallies.csv)
// Historical raster retained byte-for-byte: manual/figures/lensing/01_toy1_delta3_class_tallies.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.4
#let fig-height-cm = 7.8

#let rows = csv("/manual/data/lensing/toy1_delta3_class_tallies.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let t-pred = rows.map(r => float(r.T_cross_predicted_tally))
#let o-fix = rows.map(r => float(r.O_fixture_tally))
#let m-vals = rows.map(r => float(r.m))
#let pretty(k) = {
  if k == "open_loss_scatter" { [open-loss scatter] }
  else { [#k.replace("_", " ")] }
}
#let xticks = range(rows.len()).map(i => (float(i), pretty(rows.at(i).class_k)))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.35, right: 0.45, top: 0.72, bottom: 1.80),
    title: [Toy 1 exact internal $delta_3$ fixture],
    title-size: 10.0pt,
    ylabel: [integer tally],
    ylabel-dx: 0.90,
    xlim: (-0.65, 6.65),
    ylim: (0.0, 5.25),
    xticks: xticks,
    yticks: (0, 1, 2, 3, 4, 5),
    x-tick-angle: -30deg,
    x-tick-size: 7.0pt,
    y-tick-size: 7.4pt,
    x-tick-dy: 0.72,
    grid-y: true,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.72,
        series: (
          (ys: t-pred, fill: rgb("#1F77B4")),
          (ys: o-fix, fill: rgb("#FF7F0E")),
        ),
      ),
      (type: "line", xs: xs, ys: m-vals, stroke: 1.1pt + rgb("#1F77B4"), marker: "circle", marker-r: 2.2),
    ),
    legend: (
      pos: "top-right",
      col-w: 3.10,
      size: 7.2pt,
      items: (
        (kind: "line", color: rgb("#1F77B4"), marker: "circle", label: [$m = abs(Delta^bb(Z))$]),
        (kind: "patch", color: rgb("#1F77B4"), label: [$T^times$ predicted]),
        (kind: "patch", color: rgb("#FF7F0E"), label: [fixture comparator $O$]),
      ),
    ),
  )
]
