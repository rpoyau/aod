// Audited S1b native Typst vector figure: lensing-09-staged-lensing-lane (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (manual/scripts/build_lensing_assets.py)
// Historical raster retained byte-for-byte: manual/figures/lensing/09_staged_lensing_lane.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 4.2

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(7.3, 0.52, [*Staged lensing lane*], size: 11.5pt, box-w: 13.8, box-h: 0.55)

  #let boxes = (
    [Toy 1 \ exact fixture],
    [SPARC5 \ medium diagnostic],
    [SWELLS K0 \ target acquisition],
    [K1 \ retained baseline],
    [K2/K3 \ audit diagnostics],
    [K4 \ 3D + flow gate],
  )
  #let bw = 2.02
  #let gap = 0.34
  #let x-start = 0.39
  #for i in range(boxes.len()) {
    let bx = x-start + i * (bw + gap)
    aod-box-tl(bx, 1.48, bw, 1.65, [#text(size: 7.4pt)[#boxes.at(i)]], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt, inset: 2.5pt)
    if i < boxes.len() - 1 {
      aod-arrow(bx + bw + 0.04, 2.305, bx + bw + gap - 0.04, 2.305, stroke: 0.95pt + aod-pal.axis, head-len: 3.8, head-half: 1.8)
    }
  }
]
