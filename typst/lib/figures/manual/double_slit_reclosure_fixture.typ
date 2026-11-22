// Audited S1b native Typst vector figure: double-slit-reclosure-fixture (Manual)
// Provenance: DATA_BACKED_VERIFIED (exact integer table tab:manual-dimonhexon-double-slit-fixture)
// Historical raster retained byte-for-byte: manual/figures/double_slit_reclosure_fixture.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.0
#let fig-height-cm = 8.4

// Exact integer fixture bins from <tab:manual-dimonhexon-double-slit-fixture>
#let ks = (-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5)
#let s-single = (4, 9, 16, 25, 31, 35, 31, 25, 16, 9, 4)
#let t-no-cross = (8, 18, 32, 50, 62, 70, 62, 50, 32, 18, 8)
#let t-cross = (8, 10, 20, 58, 80, 96, 80, 58, 20, 10, 8)
#let o-comp = (8, 11, 19, 59, 79, 95, 80, 58, 21, 10, 8)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.45, right: 0.45, top: 0.78, bottom: 1.05),
    title: [Dimonhexon double-slit reclosure fixture],
    title-size: 10.2pt,
    xlabel: [bin],
    ylabel: [counts],
    ylabel-dx: 1.00,
    xlim: (-5.5, 5.5),
    ylim: (-0.8, 101.0),
    xticks: (-4, -2, 0, 2, 4),
    yticks: (0, 20, 40, 60, 80, 100),
    grid-y: false,
    layers: (
      (type: "line", xs: ks, ys: s-single, stroke: 1.25pt + rgb("#1F77B4"), marker: "circle", marker-r: 2.3),
      (type: "line", xs: ks, ys: t-no-cross, stroke: 1.25pt + rgb("#FF7F0E"), marker: "circle", marker-r: 2.3),
      (type: "line", xs: ks, ys: t-cross, stroke: 1.25pt + rgb("#2CA02C"), marker: "circle", marker-r: 2.3),
      (type: "line", xs: ks, ys: o-comp, stroke: (paint: rgb("#D62728"), thickness: 1.2pt, dash: "dashed"), marker: "cross", marker-r: 2.7),
    ),
    legend: (
      pos: "top-right",
      col-w: 3.15,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#1F77B4"), marker: "circle", label: [single]),
        (kind: "line", color: rgb("#FF7F0E"), marker: "circle", label: [two/no cross]),
        (kind: "line", color: rgb("#2CA02C"), marker: "circle", label: [two/cross calc]),
        (kind: "line", color: rgb("#D62728"), dash: "dashed", marker: "cross", label: [fixture comparator]),
      ),
    ),
  )
]
