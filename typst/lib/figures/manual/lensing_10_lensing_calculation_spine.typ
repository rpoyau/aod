// Audited S1b native Typst vector figure: lensing-10-lensing-calculation-spine (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (manual/scripts/build_lensing_assets.py)
// Historical raster retained byte-for-byte: manual/figures/lensing/10_lensing_calculation_spine.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 5.4

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(7.3, 0.56, [*Lensing calculation spine*], size: 11.5pt, box-w: 13.8, box-h: 0.55)

  #let boxes = (
    [$B_upright("lens")$],
    [$T_k^0$],
    [$C_(i j, k)^times$],
    [$T_k^times$],
    [$Delta_k^upright("Z")$],
    [$delta_(3, k)$],
    [audit],
  )
  #let bw = 1.68
  #let gap = 0.34
  #let x-start = 0.40
  #for i in range(boxes.len()) {
    let bx = x-start + i * (bw + gap)
    aod-box-tl(bx, 1.75, bw, 1.40, [#text(size: 9.2pt)[#boxes.at(i)]], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
    if i < boxes.len() - 1 {
      aod-arrow(bx + bw + 0.04, 2.45, bx + bw + gap - 0.04, 2.45, stroke: 0.95pt + aod-pal.axis, head-len: 3.8, head-half: 1.8)
    }
  }

  #aod-text(7.3, 4.35, [$T_k^times = T_k^0 + sum C_(i j, k)^times (B_upright("lens"))$], size: 9.5pt, box-w: 12.0, box-h: 0.6)
]
