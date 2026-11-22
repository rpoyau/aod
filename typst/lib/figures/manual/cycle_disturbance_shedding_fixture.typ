// Audited S1b native Typst vector figure: cycle-disturbance-shedding-fixture (Manual)
// Provenance: DATA_BACKED_VERIFIED (wavelet_shedding_simulation.csv, 90 native ticks)
// Historical raster retained byte-for-byte: figures_jpg/cycle_disturbance_shedding_fixture.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 11.4

#let rows = csv("/wavelet_shedding_simulation.csv", row-type: dictionary)
#let ts = rows.map(r => float(r.tick))
#let lead = rows.map(r => float(r.lead))
#let lag = rows.map(r => float(r.lag))
#let span = rows.map(r => float(r.span))
#let burden = rows.map(r => float(r.padar_burden))
#let compat = rows.map(r => float(r.compatibility))
#let out-rem = rows.map(r => float(r.outward_shedding))
#let loc-rec = rows.map(r => float(r.local_reclosure))
#let excess = rows.map(r => float(r.shed_excess))
#let xticks-blank = (0, 10, 20, 30, 40, 50, 60, 70, 80).map(v => (float(v), []))
#let xticks-lbl = (0, 10, 20, 30, 40, 50, 60, 70, 80)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(7.5, 0.36, [*Retained cycle-shedding fixture: 90 native ticks*], size: 10.4pt, box-w: 13.8, box-h: 0.48)

  // Panel 1: Lead L_t and Lag G_t
  #aod-xy-plot(
    x0: 0.0, y0: 0.56, w: fig-width-cm, h: 3.30,
    pad: (left: 1.50, right: 0.35, top: 0.14, bottom: 0.32),
    ylabel: [Component],
    ylabel-dx: 1.05,
    xlim: (0.0, 89.0),
    ylim: (0.28, 0.69),
    xticks: xticks-blank,
    yticks: ((0.3, [0.3]), (0.4, [0.4]), (0.5, [0.5]), (0.6, [0.6])),
    grid-y: true,
    frame: "L",
    layers: (
      (type: "line", xs: ts, ys: lead, stroke: 1.25pt + aod-pal.blue),
      (type: "line", xs: ts, ys: lag, stroke: 1.25pt + aod-pal.orange),
    ),
    legend: (
      pos: "top-right",
      cols: 2,
      col-w: 1.72,
      size: 7.4pt,
      frame: false,
      items: (
        (kind: "line", color: aod-pal.blue, label: [Lead $L_t$]),
        (kind: "line", color: aod-pal.orange, label: [Lag $G_t$]),
      ),
    ),
  )

  // Panel 2: Span, post-clipping burden, compatibility
  #aod-xy-plot(
    x0: 0.0, y0: 3.92, w: fig-width-cm, h: 3.70,
    pad: (left: 1.50, right: 0.35, top: 0.52, bottom: 0.32),
    ylabel: [Span / burden],
    ylabel-dx: 1.05,
    xlim: (0.0, 89.0),
    ylim: (0.0, 0.59),
    xticks: xticks-blank,
    yticks: ((0.0, [0.0]), (0.1, [0.1]), (0.2, [0.2]), (0.3, [0.3]), (0.4, [0.4]), (0.5, [0.5])),
    grid-y: true,
    frame: "L",
    layers: (
      (type: "line", xs: ts, ys: span, stroke: 1.2pt + aod-pal.blue),
      (type: "line", xs: ts, ys: burden, stroke: 1.2pt + aod-pal.orange),
      (type: "line", xs: ts, ys: compat, stroke: (paint: aod-pal.teal, thickness: 1.2pt, dash: "dashed")),
    ),
    legend: (
      pos: "above",
      cols: 3,
      col-w: 3.80,
      size: 7.3pt,
      frame: false,
      items: (
        (kind: "line", color: aod-pal.blue, label: [Span $S_t$]),
        (kind: "line", color: aod-pal.orange, label: [Post-clipping burden $P_t$]),
        (kind: "line", color: aod-pal.teal, dash: "dashed", label: [Compatibility $C_t$]),
      ),
    ),
  )

  // Panel 3: Stacked outward remainder + local fraction + total excess
  #aod-xy-plot(
    x0: 0.0, y0: 7.66, w: fig-width-cm, h: 3.72,
    pad: (left: 1.50, right: 0.35, top: 0.14, bottom: 0.92),
    xlabel: [Native tick $t$],
    ylabel: [Sheddic excess],
    ylabel-dx: 1.15,
    xlabel-dy: 0.62,
    xlim: (0.0, 89.0),
    ylim: (0.0, 0.063),
    xticks: xticks-lbl,
    yticks: ((0.0, [0.00]), (0.02, [0.02]), (0.04, [0.04]), (0.06, [0.06])),
    grid-y: true,
    frame: "L",
    layers: (
      (
        type: "stacked-area",
        xs: ts,
        series: (
          (ys: out-rem, fill: rgb("#70BDE9")),
          (ys: loc-rec, fill: rgb("#EAA626")),
        ),
      ),
      (type: "line", xs: ts, ys: excess, stroke: 0.9pt + black),
    ),
    legend: (
      pos: "top-right",
      cols: 1,
      col-w: 3.55,
      size: 7.3pt,
      frame: false,
      items: (
        (kind: "patch", color: rgb("#70BDE9"), label: [Outward remainder $O_t$]),
        (kind: "patch", color: rgb("#EAA626"), label: [Local fraction $R_t$]),
        (kind: "line", color: black, label: [Excess $X_t = O_t + R_t$]),
      ),
    ),
  )
]
