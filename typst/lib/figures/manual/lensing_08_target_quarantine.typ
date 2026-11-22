// Audited S1b native Typst vector figure: lensing-08-target-quarantine (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (visually audited historical schematic; no generator script in repo)
// Historical raster retained byte-for-byte: manual/figures/lensing/08_target_quarantine.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.2
#let fig-height-cm = 4.6

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(7.1, 0.56, [*Target-side quarantine*], size: 11.5pt, box-w: 13.0, box-h: 0.55)

  #aod-box-tl(0.75, 1.60, 3.70, 1.85, [#text(size: 8.6pt)[A$Omega$ input side \ medium fields only]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
  #aod-box-tl(5.25, 1.60, 3.70, 1.85, [#text(size: 8.6pt)[A$Omega$ values freeze \ $T^0, C^times, T^times$]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
  #aod-box-tl(9.75, 1.60, 3.70, 1.85, [#text(size: 8.6pt)[target side quarantine \ $O_k$, image bins, $theta_E$]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)

  #aod-arrow(4.50, 2.525, 5.20, 2.525, stroke: 1.05pt + aod-pal.axis)
  #aod-arrow(9.00, 2.525, 9.70, 2.525, stroke: 1.05pt + aod-pal.axis)
]
