// Audited S1b native Typst vector figure: run-tumble-trace-3d-projection (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/run_tumble/{run_tumble_trace_20_ticks,run_tumble_phase_cycle_delta3,run_tumble_octant_delta3}.csv)
// Historical raster retained byte-for-byte: manual/figures/run_tumble_trace_3d_projection.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.4
#let fig-height-cm = 12.2

#let tr = csv("/manual/data/run_tumble/run_tumble_trace_20_ticks.csv", row-type: dictionary)
#let pts3d = tr.map(r => (float(r.x), float(r.y), float(r.z)))
#let ts = tr.map(r => float(r.t))
#let q3 = tr.map(r => float(r.Q3))
#let modes = tr.map(r => r.mode)
#let ph = csv("/manual/data/run_tumble/run_tumble_phase_cycle_delta3.csv", row-type: dictionary)
#let ph-x = ph.map(r => float(r.theta))
#let ph-y = ph.map(r => float(r.O))
#let oc = csv("/manual/data/run_tumble/run_tumble_octant_delta3.csv", row-type: dictionary)
#let oc-x = oc.map(r => float(r.octant))
#let oc-m = oc.map(r => float(r.m))

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Main title
  #aod-text(7.2, 0.36, [*Run-tumble tracer-current projection*], size: 11.4pt, box-w: 13.6, box-h: 0.5)

  // Top center: 3D declared pi_3(h_t) path in Z^3
  #aod-3d-wireframe(
    x0: 4.15, y0: 0.78, w: 6.10, h: 4.15,
    title: [Declared $pi_3(h_t)$ path in $bb(Z)^3$],
    xlim: (0, 2), ylim: (0, 2), zlim: (-2, 0),
    xticks: (0, 1, 2),
    yticks: (0, 1, 2),
    zticks: (-2, -1, 0),
    elev: 25.0,
    azim: -60.0,
    points: pts3d,
    stroke: 1.35pt + rgb("#1F77B4"),
    marker-color: rgb("#1F77B4"),
    chord: false,
  )

  // Mid-left: Q^2_3D step plot by tick
  #aod-xy-plot(
    x0: 0.15, y0: 5.10, w: 6.85, h: 3.35,
    pad: (left: 1.25, right: 0.28, top: 0.52, bottom: 0.78),
    title: [$Q_(3 D)^2$ by tick],
    title-size: 9.0pt,
    xlabel: [$t$],
    ylabel: [$Q_(3 D)^2$],
    xlabel-dy: 0.50,
    ylabel-dx: 0.85,
    xlim: (-1.0, 21.0),
    ylim: (-0.6, 12.6),
    xticks: (0, 5, 10, 15, 20),
    yticks: (0, 5, 10),
    grid-y: false,
    layers: (
      (type: "step", xs: ts, ys: q3, stroke: 1.25pt + rgb("#1F77B4")),
    ),
  )

  // Mid-right: Discrete mode strip (init / run / tumble)
  #aod-mode-strip(
    x0: 7.45, y0: 5.10, w: 6.70, h: 3.35,
    pad: (left: 0.45, right: 0.28, top: 0.52, bottom: 0.78),
    title: [mode strip: init/run/tumble],
    modes: modes,
    color-map: ("init": rgb("#440154"), "run": rgb("#21918C"), "tumble": rgb("#FDE725")),
    xticks: (0, 5, 10, 15, 20),
  )

  // Bottom-left: Phase counts Q^2_3D mod beta
  #aod-xy-plot(
    x0: 0.15, y0: 8.65, w: 6.85, h: 3.35,
    pad: (left: 1.25, right: 0.28, top: 0.52, bottom: 0.82),
    title: [phase counts $Q_(3 D)^2 mod beta$],
    title-size: 9.0pt,
    xlabel: [$theta$],
    ylabel: [count],
    xlabel-dy: 0.52,
    ylabel-dx: 0.85,
    xlim: (-0.65, 4.65),
    ylim: (0.0, 6.35),
    xticks: (0, 1, 2, 3, 4),
    yticks: ((0.0, [0.0]), (2.5, [2.5]), (5.0, [5.0])),
    grid-y: false,
    layers: (
      (type: "bars", xs: ph-x, ys: ph-y, bar-w: 0.78, fills: rgb("#1F77B4")),
    ),
  )

  // Bottom-right: Octant delta_3 magnitudes
  #aod-xy-plot(
    x0: 7.45, y0: 8.65, w: 6.70, h: 3.35,
    pad: (left: 1.05, right: 0.28, top: 0.52, bottom: 0.82),
    title: [octant $delta_3$ magnitudes],
    title-size: 9.0pt,
    xlabel: [octant],
    ylabel: [$m$],
    xlabel-dy: 0.52,
    ylabel-dx: 0.68,
    xlim: (-0.65, 7.65),
    ylim: (0.0, 8.45),
    xticks: (0, 2, 4, 6),
    yticks: (0, 5),
    grid-y: false,
    layers: (
      (type: "bars", xs: oc-x, ys: oc-m, bar-w: 0.78, fills: rgb("#1F77B4")),
    ),
  )
]
