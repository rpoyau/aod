// Audited S1b native Typst vector figure: higgs-yro-saddle-signature (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/higgs/higgs_trace_internal_candidates_selection.csv)
// Historical raster retained byte-for-byte: manual/figures/higgs/higgs_yro_saddle_signature.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 13.8
#let fig-height-cm = 7.2

#let rows = csv("/manual/data/higgs/higgs_trace_internal_candidates_selection.csv", row-type: dictionary)
#let sel = rows.find(r => r.rank == "1")
#let d-lo = float(sel.delta_lower)
#let d-hi = float(sel.delta_upper)
#let p-h = int(sel.PD_window_pressure)
#let lbl-lo = if d-lo >= 0 { [$+#int(d-lo)$] } else { [$#int(d-lo)$] }
#let lbl-hi = if d-hi >= 0 { [$+#int(d-hi)$] } else { [$-#int(calc.abs(d-hi))$] }

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.45, right: 0.45, top: 0.78, bottom: 0.95),
    title: [Tritrioseptyro yro saddle signature],
    title-size: 10.2pt,
    ylabel: [closure residual],
    ylabel-dx: 1.02,
    xlim: (-0.52, 1.52),
    ylim: (-4.5, 4.5),
    xticks: ((0.0, [$P_H^D - C_6$]), (1.0, [$P_H^D - C_8$])),
    yticks: (-4, -3, -2, -1, 0, 1, 2, 3, 4),
    x-tick-size: 8.6pt,
    y-tick-size: 8.0pt,
    x-tick-dy: 0.30,
    grid-y: false,
    layers: (
      (type: "hline", y: 0.0, stroke: 0.8pt + aod-pal.axis),
      (
        type: "bars",
        xs: (0.0, 1.0),
        ys: (d-lo, d-hi),
        bar-w: 0.56,
        fills: (rgb("#3B7A47"), rgb("#C46326")),
        value-labels: (lbl-lo, lbl-hi),
      ),
    ),
    annotations: (
      (x: 0.5, y: -3.95, body: [$K_H^star = #sel.candidate_K _upright("yro"), wide P_H^D = #p-h$], size: 8.6pt, box-w: 6.5),
    ),
  )
]
