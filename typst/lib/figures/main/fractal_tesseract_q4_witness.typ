// Audited S1b native Typst vector figure: fractal-tesseract-q4-witness (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_fractal_tesseract_q4_witness.py)
// Historical raster retained byte-for-byte: figures_jpg/fractal_tesseract_q4_witness.jpg
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 7.8

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Title & subtitle
  #aod-text(7.4, 0.42, [*Fractal tesseract support with true 16-vertex $Q_4$ witness*], size: 11.2pt, box-w: 14.2, box-h: 0.55)
  #aod-text(7.4, 0.84, [Recursive cut gives support; 16-vertex, 32-edge $Q_4$ chart witnesses local Hamming-1 degree 4.], size: 7.9pt, box-w: 14.2, box-h: 0.45)

  // Left: Recursive cut-unspooling spine
  #aod-box-tl(0.35, 1.38, 1.70, 0.96, [#text(size: 8.0pt)[Null \ potential]], stroke: 0.95pt + aod-pal.slate, fill: aod-pal.tint-gray)
  #aod-box-tl(2.42, 1.38, 1.52, 0.96, [#text(size: 8.0pt)[$x -> x$ \ $= x$]], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue)
  #aod-box-tl(4.32, 1.28, 1.68, 1.16, [#text(size: 8.0pt)[branch / \ hinge / \ branch]], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green)
  #aod-box-tl(6.38, 1.28, 1.95, 1.16, [#text(size: 8.0pt)[recursive \ cut-unspooling]], stroke: 0.95pt + aod-pal.gold, fill: aod-pal.tint-amber)

  #aod-arrow(2.07, 1.86, 2.40, 1.86, stroke: 1.0pt + aod-pal.slate)
  #aod-arrow(3.96, 1.86, 4.30, 1.86, stroke: 1.0pt + aod-pal.slate)
  #aod-arrow(6.02, 1.86, 6.36, 1.86, stroke: 1.0pt + aod-pal.slate)

  // Left-lower: Local 4-slot star & ternary fibre summary
  #aod-box-tl(
    0.35, 2.95, 6.25, 3.25,
    [],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 4pt,
  )
  #aod-text(3.48, 3.30, [*Local Hamming-1 witness at $v in V(Q_4)$*], size: 8.4pt, box-w: 5.8, box-h: 0.42)
  #aod-text(3.48, 3.84, [$|V(Q_4)| = 16$, $quad |E(Q_4)| = 32$, $quad deg(v) = 4$], size: 7.9pt, box-w: 5.9, box-h: 0.42)
  #aod-text(3.48, 4.44, [Incident slots $\{e_0, e_1, e_2, e_3\}$ highlighted in orange:], size: 7.8pt, box-w: 6.0, box-h: 0.42)
  #aod-text(3.48, 4.98, [committed incoming ancestor excluded from fresh H1 step], size: 7.7pt, box-w: 6.0, box-h: 0.42)
  #aod-text(3.48, 5.56, [Monon fibre $Q_4 times \{-1, 0_H, +1\}$ separates base leg from role], size: 7.8pt, box-w: 6.0, box-h: 0.42)

  // Connector from recursive cut to true 16-vertex Q4 tesseract
  #aod-curve-arrow(8.35, 1.86, 8.95, 1.86, 9.35, 2.30, stroke: 1.0pt + aod-pal.slate)

  // Center-right: True 16-vertex, 32-edge Q4 hypercube
  #aod-text(10.35, 1.48, [*16-vertex $Q_4$ hypercube*], size: 9.2pt, box-w: 3.8, box-h: 0.42)
  #aod-tesseract-q4(10.35, 3.38, scale: 1.18, highlight-vertex: 0)
  #aod-text(10.35, 5.05, [inner $w=0$ cube + outer $w=1$ cube \ $+ 8$ fourth-axis H1 links], size: 7.1pt, box-w: 4.1, box-h: 0.62)

  // Right: Duon current & jittering witness
  #aod-text(12.65, 1.78, [*jittering:*], size: 8.0pt, anchor: "left", box-w: 2.0, box-h: 0.38)
  #aod-text(12.65, 2.30, [unresolved H1 \ successor motion], size: 7.0pt, anchor: "left", box-w: 2.1, box-h: 0.65)
  #aod-box-tl(
    12.35, 3.25, 2.10, 1.05,
    [#text(size: 8.0pt)[duon current \ $D_i thin mu thin D_j$]],
    stroke: 1.0pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
  )
  #aod-wavy-arrow(12.40, 4.78, 14.40, 4.78, amp: 0.065, waves: 3.5, stroke: 1.0pt + aod-pal.purple)
  #aod-text(13.40, 5.26, [retained trace], size: 7.2pt, box-w: 2.1, box-h: 0.38)

  // Bottom lock-in strip
  #aod-box-tl(
    0.35, 6.72, 14.10, 0.66,
    [#text(size: 7.4pt, weight: "bold")[Corrected order: recursive cut $->$ fractal tesseract support; 16-vertex $Q_4$ chart $->$ local witness; duon current $->$ carried history.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
  )
]
