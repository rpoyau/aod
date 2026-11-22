// Audited S1b native Typst vector figure: lensing-07-k4-3d-timeflow-input-gate (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/lensing/k4_3d_timeflow_input_gate.csv)
// Historical raster retained byte-for-byte: manual/figures/lensing/07_k4_3d_timeflow_input_gate.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 7.8

#let rows = csv("/manual/data/lensing/k4_3d_timeflow_input_gate.csv", row-type: dictionary)
#let counts = (:)
#for r in rows {
  let g = r.input_group
  counts.insert(g, counts.at(g, default: 0) + 1)
}
#let groups = counts.keys().sorted()

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(7.1, 0.62, [*K4 3D + time-flow input gate*], size: 12.2pt, box-w: 13.4, box-h: 0.6)

  #let y0 = 1.35
  #let rh = 0.62
  #let gap = 0.24
  #for i in range(groups.len()) {
    let g = groups.at(i)
    let c = counts.at(g)
    let lbl = if c == 1 { [#c field] } else { [#c fields] }
    let ry = y0 + i * (rh + gap)
    aod-box-tl(1.65, ry, 10.90, rh, [], stroke: 0.85pt + aod-pal.axis, fill: aod-pal.tint-blue, radius: 0pt)
    aod-text(1.98, ry + rh / 2, [#g], size: 9.0pt, anchor: "left", box-w: 7.4, box-h: 0.5)
    aod-text(12.22, ry + rh / 2, lbl, size: 9.0pt, anchor: "right", box-w: 2.8, box-h: 0.5)
  }

  #aod-text(7.1, 7.12, [Release condition: all K4 inputs declared before scoring; target side remains quarantined.], size: 8.2pt, box-w: 13.4, box-h: 0.5)
]
