// Audited S1b native Typst vector figure: fractal-tesseract-q4-witness (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_fractal_tesseract_q4_witness.py)
// Historical raster retained byte-for-byte: figures_jpg/fractal_tesseract_q4_witness.jpg
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 7.5

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Title & subtitle
  #aod-text(7.3, 0.42, [*Fractal tesseract support with finite $Q_4$ witness*], size: 11.5pt, box-w: 14.0, box-h: 0.55)
  #aod-text(7.3, 0.84, [Recursive cut gives support; duon current traverses and witnesses it.], size: 8.0pt, box-w: 14.0, box-h: 0.45)

  // Top flow boxes
  #aod-box-tl(0.45, 1.38, 1.75, 0.95, [#text(size: 8.2pt)[Null \ potential]], stroke: 0.95pt + aod-pal.slate, fill: aod-pal.tint-gray)
  #aod-box-tl(2.65, 1.38, 1.55, 0.95, [#text(size: 8.2pt)[$x -> x$ \ $= x$]], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue)
  #aod-box-tl(4.65, 1.28, 1.65, 1.15, [#text(size: 8.2pt)[branch / \ hinge / \ branch]], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green)
  #aod-box-tl(6.75, 1.28, 2.05, 1.15, [#text(size: 8.2pt)[recursive \ cut-unspooling]], stroke: 0.95pt + aod-pal.gold, fill: aod-pal.tint-amber)

  #aod-arrow(2.22, 1.85, 2.62, 1.85, stroke: 1.0pt + aod-pal.slate)
  #aod-arrow(4.22, 1.85, 4.62, 1.85, stroke: 1.0pt + aod-pal.slate)
  #aod-arrow(6.32, 1.85, 6.72, 1.85, stroke: 1.0pt + aod-pal.slate)

  // Curved connector to finite Q4 chart
  #aod-curve-arrow(8.20, 2.52, 8.85, 2.52, 9.42, 2.78, stroke: 1.0pt + aod-pal.slate)
  #aod-text(6.95, 3.08, [branch / hinge / branch support \ can cut again], size: 7.2pt, box-w: 4.5, box-h: 0.65)

  // Finite Q4 cube witness
  #aod-text(10.55, 1.54, [*finite $Q_4$ chart*], size: 9.5pt, box-w: 3.4, box-h: 0.45)
  #let front = ((9.50, 3.60), (11.15, 3.60), (11.15, 2.35), (9.50, 2.35))
  #let back = front.map(p => (p.at(0) + 0.58, p.at(1) - 0.46))
  #let edges = ((0, 1), (1, 2), (2, 3), (3, 0))
  #for arr in (front, back) {
    for e in edges {
      let p1 = arr.at(e.at(0)); let p2 = arr.at(e.at(1))
      aod-line(p1.at(0), p1.at(1), p2.at(0), p2.at(1), stroke: 1.05pt + aod-pal.purple)
    }
  }
  #for i in range(4) {
    let p1 = front.at(i); let p2 = back.at(i)
    aod-line(p1.at(0), p1.at(1), p2.at(0), p2.at(1), stroke: 1.05pt + aod-pal.purple)
  }
  #for p in front + back {
    aod-circle(p.at(0), p.at(1), 0.065, fill: aod-pal.purple, stroke: none)
  }
  #aod-text(10.40, 4.02, [local witness of fractal \ tesseract support], size: 7.3pt, box-w: 3.6, box-h: 0.65)

  // Jittering notes separated cleanly on right
  #aod-text(12.22, 1.94, [*jittering:*], size: 8.0pt, anchor: "left", box-w: 2.2, box-h: 0.38)
  #aod-text(12.22, 2.48, [unresolved successor \ movement], size: 7.1pt, anchor: "left", box-w: 2.3, box-h: 0.68)
  #for (jx, jy) in ((12.75, 3.16), (13.60, 3.40), (12.85, 3.86), (13.65, 4.10)) {
    aod-text(jx, jy, [$+$], size: 8.5pt, box-w: 0.4, box-h: 0.4)
  }

  // Duon current box & chain
  #aod-curve-arrow(10.40, 4.38, 11.00, 4.46, 11.45, 4.78, stroke: 1.15pt + aod-pal.purple)
  #aod-box-tl(
    11.05, 4.80, 2.65, 0.80,
    [#text(size: 8.2pt)[duon current \ $D_i thin mu thin D_j$]],
    stroke: 1.0pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
  )
  #for i in range(5) {
    aod-circle(11.20 + i * 0.44, 5.90, 0.11, fill: white, stroke: 1.0pt + aod-pal.purple)
  }
  #aod-arrow(11.02, 6.22, 13.35, 6.22, stroke: 1.15pt + aod-pal.purple, head-len: 4.8, head-half: 2.3)

  // Bottom lock-in strip
  #aod-box-tl(
    0.40, 6.62, 13.80, 0.62,
    [#text(size: 7.4pt, weight: "bold")[Corrected order: recursive cut $->$ fractal tesseract support; duon current $->$ finite carried witness.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
  )
]
