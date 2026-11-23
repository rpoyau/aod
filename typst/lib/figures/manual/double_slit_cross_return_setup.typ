// Audited S1b native Typst vector figure: double-slit-cross-return-setup (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_manual_figures.py)
// Historical raster retained byte-for-byte: manual/figures/double_slit_cross_return_setup.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 7.8

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Outer frame
  #aod-box-tl(0.18, 0.18, 14.24, 7.44, [], stroke: 0.9pt + aod-pal.axis, fill: white, radius: 0pt)

  // Title
  #aod-text(0.55, 0.62, [*Double-slit cross-return fixture*], size: 11.5pt, anchor: "left", box-w: 10.0, box-h: 0.55)

  // Left boundary gates
  #aod-text(0.45, 1.38, [boundary \ gates], size: 8.2pt, anchor: "left", box-w: 2.0, box-h: 0.7)
  #aod-arrow(0.45, 2.38, 1.55, 2.38, stroke: 0.95pt + black)
  #aod-arrow(0.45, 4.18, 1.55, 4.18, stroke: 0.95pt + black)

  #aod-box-tl(1.58, 1.98, 1.48, 0.80, [$g_a$], stroke: 0.9pt + black, fill: white, radius: 4pt)
  #aod-box-tl(1.58, 3.78, 1.48, 0.80, [$g_b$], stroke: 0.9pt + black, fill: white, radius: 4pt)

  // Curved dashed cross-return coupling between g_a and g_b
  #aod-curve-arrow(2.32, 2.78, 1.88, 3.28, 2.32, 3.78, stroke: (paint: black, thickness: 0.85pt, dash: "dashed"), head-len: 4.0, head-half: 1.9, both: true)

  // Gate output boxes S_k^(a) and S_k^(b)
  #aod-arrow(3.06, 2.38, 4.25, 2.38, stroke: 0.95pt + black)
  #aod-arrow(3.06, 4.18, 4.25, 4.18, stroke: 0.95pt + black)
  #aod-box-tl(4.28, 1.90, 2.24, 0.96, [$S_k^((a))$], stroke: 0.9pt + black, fill: white, radius: 4pt)
  #aod-box-tl(4.28, 3.70, 2.24, 0.96, [$S_k^((b))$], stroke: 0.9pt + black, fill: white, radius: 4pt)

  // Additive no-cross baseline T_k^0
  #aod-arrow(6.52, 2.38, 7.55, 2.86, stroke: 0.95pt + black)
  #aod-arrow(6.52, 4.18, 7.55, 3.22, stroke: 0.95pt + black)
  #aod-box-tl(7.58, 2.52, 2.78, 0.96, [$T_k^0 = S_k^((a)) + S_k^((b))$], stroke: 0.9pt + black, fill: white, radius: 4pt)

  // Cross-return combined box T_cross
  #aod-arrow(10.36, 3.00, 10.80, 3.36, stroke: 0.95pt + black)
  #aod-box-tl(10.83, 2.98, 3.22, 0.98, [#text(size: 7.8pt)[$T_upright("cross") = T_upright("no") + C_upright("cross")$]], stroke: 0.9pt + black, fill: white, radius: 4pt)

  // Dashed direct cross-return channel into T_cross (cleanly spaced below T_k^0)
  #aod-arrow(3.98, 3.36, 10.80, 3.68, stroke: (paint: black, thickness: 0.85pt, dash: "dashed"), head-len: 4.2, head-half: 2.0)
  #aod-text(5.85, 3.16, [reclosure bins], size: 7.8pt, box-w: 2.5, box-h: 0.36)

  // Schematic 7-bin reclosure bar profile cleanly below S_k^(b) (zero overlap)
  #let bar-hs = (0.76, 1.15, 1.38, 1.54, 1.38, 1.15, 0.76)
  #let y-base = 6.50
  #for i in range(bar-hs.len()) {
    let bx = 3.25 + i * 1.12
    let bh = bar-hs.at(i)
    place(top + left, dx: bx * 1cm, dy: (y-base - bh) * 1cm, rect(width: 0.64cm, height: bh * 1cm, fill: white, stroke: 0.8pt + black))
  }

  // Bottom identity line
  #aod-text(7.30, 7.06, [fixture identity: $T_upright("cross") - T_upright("no-cross") = C_upright("cross")$], size: 8.6pt, box-w: 11.5, box-h: 0.45)
]
