// Audited S1b native Typst vector figure: null-four-edge-x-witness (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_null_four_edge.py)
// Historical raster retained byte-for-byte: figures_jpg/null_four_edge_x_witness.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 7.25

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Three rounded panels
  #aod-box-tl(0.20, 0.25, 4.15, 5.85, [], stroke: 0.9pt + rgb("#B9C0CC"), fill: rgb("#FBFBFD"), radius: 4pt)
  #aod-box-tl(4.80, 0.25, 5.05, 5.85, [], stroke: 0.9pt + rgb("#B9C0CC"), fill: rgb("#FBFBFD"), radius: 4pt)
  #aod-box-tl(10.30, 0.25, 4.10, 5.85, [], stroke: 0.9pt + rgb("#B9C0CC"), fill: rgb("#FBFBFD"), radius: 4pt)

  // Inter-panel arrows
  #aod-arrow(4.42, 3.25, 4.74, 3.25, stroke: 1.1pt + aod-pal.slate, head-len: 5.0, head-half: 2.5)
  #aod-arrow(9.92, 3.25, 10.24, 3.25, stroke: 1.1pt + aod-pal.slate, head-len: 5.0, head-half: 2.5)

  // Panel 1: Null potential
  #aod-text(2.275, 0.72, [*1  Null potential*], size: 9.5pt, box-w: 3.9, box-h: 0.5)
  #aod-text(2.275, 1.38, [$x succ x = x$], size: 12pt, box-w: 3.8, box-h: 0.6)
  #aod-text(2.275, 2.02, [same occurrence held in identity \ while cut-running presents], size: 7.4pt, box-w: 3.9, box-h: 0.8)
  #aod-circle(2.275, 3.72, 1.38, fill: none, stroke: 0.75pt + rgb("#C6D4E8"))
  #aod-circle(2.275, 3.72, 1.08, fill: none, stroke: 0.85pt + rgb("#9AB4D6"))
  #aod-circle(2.275, 3.72, 0.70, fill: aod-pal.tint-blue, stroke: 1.2pt + aod-pal.navy)
  #aod-text(2.275, 3.72, [$x$], size: 14pt, box-w: 1.2, box-h: 0.8)
  #aod-text(2.275, 5.56, [retained occurrence], size: 7.6pt, box-w: 3.8, box-h: 0.45)

  // Panel 2: Four-edge x witness
  #aod-text(7.325, 0.72, [*2  Four-edge $x$ witness*], size: 9.5pt, box-w: 4.8, box-h: 0.5)
  #aod-text(7.325, 1.36, [$epsilon in {0, 1}^4$], size: 10.5pt, box-w: 4.2, box-h: 0.55)
  #let cx2 = 7.325
  #let cy2 = 3.55
  #let d2 = 1.25
  #let r-cen = 0.40
  #let r-nb = 0.24
  // Bidirectional edges
  #aod-arrow(cx2, cy2 - r-cen, cx2, cy2 - d2 + r-nb, stroke: 1.0pt + aod-pal.blue, head-len: 4.0, head-half: 1.9, both: true)
  #aod-arrow(cx2 + r-cen, cy2, cx2 + d2 - r-nb, cy2, stroke: 1.0pt + aod-pal.blue, head-len: 4.0, head-half: 1.9, both: true)
  #aod-arrow(cx2, cy2 + r-cen, cx2, cy2 + d2 - r-nb, stroke: 1.0pt + aod-pal.blue, head-len: 4.0, head-half: 1.9, both: true)
  #aod-arrow(cx2 - r-cen, cy2, cx2 - d2 + r-nb, cy2, stroke: 1.0pt + aod-pal.blue, head-len: 4.0, head-half: 1.9, both: true)
  // Neighbor nodes & labels
  #aod-circle(cx2, cy2 - d2, r-nb, fill: aod-pal.tint-amber, stroke: 1.0pt + aod-pal.gold)
  #aod-circle(cx2 + d2, cy2, r-nb, fill: aod-pal.tint-amber, stroke: 1.0pt + aod-pal.gold)
  #aod-circle(cx2, cy2 + d2, r-nb, fill: aod-pal.tint-amber, stroke: 1.0pt + aod-pal.gold)
  #aod-circle(cx2 - d2, cy2, r-nb, fill: aod-pal.tint-amber, stroke: 1.0pt + aod-pal.gold)
  #aod-circle(cx2, cy2, r-cen, fill: aod-pal.tint-green, stroke: 1.2pt + aod-pal.green)
  #aod-text(cx2, cy2, [$x_epsilon$], size: 10.5pt, box-w: 0.9, box-h: 0.6)
  #aod-text(cx2, cy2 - d2 - 0.44, [$epsilon plus.o e_1$], size: 7.4pt, box-w: 1.8, box-h: 0.4)
  #aod-text(cx2 + d2 + 0.34, cy2, [$epsilon plus.o e_2$], size: 7.4pt, anchor: "left", box-w: 1.3, box-h: 0.4)
  #aod-text(cx2, cy2 + d2 + 0.42, [$epsilon plus.o e_3$], size: 7.4pt, box-w: 1.8, box-h: 0.4)
  #aod-text(cx2 - d2 - 0.34, cy2, [$epsilon plus.o e_4$], size: 7.4pt, anchor: "right", box-w: 1.3, box-h: 0.4)
  // Edge labels
  #aod-text(cx2 - 0.28, cy2 - 0.68, [$a_1$], size: 7.6pt, box-w: 0.5, box-h: 0.4)
  #aod-text(cx2 + 0.66, cy2 - 0.24, [$a_2$], size: 7.6pt, box-w: 0.5, box-h: 0.4)
  #aod-text(cx2 - 0.28, cy2 + 0.68, [$a_3$], size: 7.6pt, box-w: 0.5, box-h: 0.4)
  #aod-text(cx2 - 0.66, cy2 - 0.24, [$a_4$], size: 7.6pt, box-w: 0.5, box-h: 0.4)
  #aod-text(cx2, 5.66, [$deg_(Q_4)(x_epsilon) = 4$], size: 10pt, box-w: 4.0, box-h: 0.5)

  // Panel 3: Monon fibre
  #aod-text(12.35, 0.72, [*3  Monon fibre*], size: 9.5pt, box-w: 3.8, box-h: 0.5)
  #aod-text(12.35, 1.36, [$Q_4 times {-1, 0, +1}_mu$], size: 10pt, box-w: 3.8, box-h: 0.55)
  #let cx3 = 11.75
  #let cy3 = 3.55
  #let d3 = 0.92
  #aod-line(cx3, cy3 - d3, cx3, cy3 + d3, stroke: 0.95pt + aod-pal.navy)
  #aod-line(cx3 - d3, cy3, cx3 + d3, cy3, stroke: 0.95pt + aod-pal.navy)
  #aod-circle(cx3, cy3 - d3, 0.16, fill: aod-pal.tint-amber, stroke: 0.85pt + aod-pal.gold)
  #aod-circle(cx3 + d3, cy3, 0.16, fill: aod-pal.tint-amber, stroke: 0.85pt + aod-pal.gold)
  #aod-circle(cx3, cy3 + d3, 0.16, fill: aod-pal.tint-amber, stroke: 0.85pt + aod-pal.gold)
  #aod-circle(cx3 - d3, cy3, 0.16, fill: aod-pal.tint-amber, stroke: 0.85pt + aod-pal.gold)
  #aod-circle(cx3, cy3, 0.25, fill: aod-pal.tint-green, stroke: 1.0pt + aod-pal.green)
  // Vertical ternary fibre
  #let fx = 13.05
  #aod-line(fx, 2.25, fx, 4.85, stroke: (paint: aod-pal.purple, thickness: 1.0pt, dash: "dashed"))
  #for (fy, fl) in ((2.25, [$+1$]), (3.55, [$0$]), (4.85, [$-1$])) {
    aod-circle(fx, fy, 0.23, fill: aod-pal.tint-purple, stroke: 1.0pt + aod-pal.purple)
    aod-text(fx + 0.34, fy, fl, size: 8.2pt, anchor: "left", box-w: 0.8, box-h: 0.45)
  }
  #aod-text(12.35, 5.56, [four tesseract edges \ plus ternary hinge fibre], size: 7.6pt, box-w: 3.8, box-h: 0.8)

  // Bottom lock-in bar
  #aod-box-tl(
    0.85, 6.32, 12.90, 0.72,
    [#text(size: 7.8pt)[Retained $x$ in the finite $Q_4$ witness has four Hamming-1 tesseract edges; the monon hinge remains the ternary fibre.]],
    stroke: 0.85pt + aod-pal.blue,
    fill: aod-pal.tint-blue,
    radius: 3pt,
    inset: 4pt,
  )
]
