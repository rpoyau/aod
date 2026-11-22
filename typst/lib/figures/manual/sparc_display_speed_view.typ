// Audited S1b native Typst vector figure: sparc-display-speed-view (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/derived/sparc_five_galaxy_per_bin.csv, NGC3198)
// Historical raster retained byte-for-byte: manual/figures/sparc_display_speed_view.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 8.0

#let rows = csv("/manual/data/derived/sparc_five_galaxy_per_bin.csv", row-type: dictionary).filter(r => r.galaxy == "NGC3198").sorted(key: r => float(r.R))
#let rs = rows.map(r => float(r.R))
#let v-obs = rows.map(r => float(r.Vobs))
#let v-disp = rows.map(r => float(r.V_disp))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.65, right: 0.45, top: 0.78, bottom: 1.05),
    title: [Display speed view (not scoring coordinate)],
    title-size: 10.2pt,
    xlabel: [R [kpc]],
    ylabel: [Display speed [km/s]],
    ylabel-dx: 1.20,
    xlim: (-1.9, 46.3),
    ylim: (15.0, 216.0),
    xticks: (0, 10, 20, 30, 40),
    yticks: (25, 50, 75, 100, 125, 150, 175, 200),
    grid-y: false,
    layers: (
      (type: "line", xs: rs, ys: v-obs, stroke: 1.35pt + rgb("#1F77B4")),
      (type: "line", xs: rs, ys: v-disp, stroke: 1.35pt + rgb("#FF7F0E")),
    ),
    legend: (
      pos: "top-left",
      col-w: 4.10,
      size: 7.4pt,
      items: (
        (kind: "line", color: rgb("#1F77B4"), label: [benchmark target speed]),
        (kind: "line", color: rgb("#FF7F0E"), label: [A$Omega$ display speed]),
      ),
    ),
  )
]
