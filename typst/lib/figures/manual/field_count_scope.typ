// Native Typst vector figure: field-count-scope (Manual §2)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 9.2

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [Fixed-scope field count and SADAR scope],
    subtitle: [Recurrence and alias resolution govern $n_F (cal(B)) = bar.v cal(F)_(cal(B)) bar.v$ and $cal(O)_(partial F) (cal(B)) = n_F log n_F$],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Three Side-by-Side Enclosure Panels (y = 1.24 .. 7.42, h = 6.18) ---
  #let py = 1.24
  #let ph = 6.18
  #let pw = 4.46
  #let px0 = 0.34
  #let px1 = 5.17
  #let px2 = 10.00

  // === Case 0: Lone Monon (n_F = 0) ===
  #aod-box-tl(px0, py, pw, ph, [], stroke: 0.95pt + aod-pal.crimson, fill: aod-pal.tint-orange, radius: 4pt)
  #aod-text(px0 + pw / 2, py + 0.32, [*Case 0: Lone Monon*], size: 8.6pt, box-w: 4.2, box-h: 0.40)

  #let c0x = px0 + pw / 2
  #let g0y = py + 2.02
  #aod-circle(c0x, g0y, 1.18, fill: white, stroke: (paint: aod-pal.slate, thickness: 0.9pt, dash: "dashed"))
  #aod-arc-arrow(c0x - 0.22, g0y, 0.56, 170, -170, stroke: 1.05pt + aod-pal.navy, head-len: 3.8, head-half: 1.8)
  #aod-chiral-vertex(c0x - 0.22, g0y, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-text(c0x - 0.22, g0y - 0.80, [$1_C$], size: 8.6pt, weight: "bold", box-w: 0.7, box-h: 0.36)
  // Crimson X non-recurrence marker
  #aod-circle(c0x + 0.74, g0y, 0.23, fill: aod-pal.tint-orange, stroke: 0.95pt + aod-pal.crimson)
  #aod-marker(c0x + 0.74, g0y, kind: "cross", r-pt: 3.6, color: aod-pal.crimson)
  #aod-text(c0x, py + 3.54, [no repeat ($op("bip") = 0$)], size: 8.6pt, box-w: 3.6, box-h: 0.38)

  #aod-box-tl(px0 + 0.22, py + 3.92, pw - 0.44, 2.04, [
    #text(size: 8.6pt)[$N^C = 1$, $med op("bip") = 0$] \
    #v(3pt)
    #text(size: 8.6pt, weight: "bold")[$n_F (cal(B)) = 0$ (not a field)] \
    #v(3pt)
    #text(size: 7.6pt)[One closure-phase cycle; \ field requires recurrence.]
  ], stroke: 0.8pt + aod-pal.crimson, fill: white, radius: 3pt, inset: 4pt)

  // === Case 1: Single Recurrent Field (n_F = 1) ===
  #aod-box-tl(px1, py, pw, ph, [], stroke: 0.95pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(px1 + pw / 2, py + 0.32, [*Case 1: Single Field*], size: 8.6pt, box-w: 4.2, box-h: 0.40)

  #let c1x = px1 + pw / 2
  #let g1y = py + 2.24

  // Solid scope + F_1 ring + self-return ADAR_(1<-1) + 3 return dots
  #aod-circle(c1x, g1y, 1.06, fill: white, stroke: 1.05pt + aod-pal.navy)
  #aod-arc-arrow(c1x, g1y, 0.62, 25, 335, stroke: 1.1pt + aod-pal.blue, head-len: 3.8, head-half: 1.8)
  #aod-chiral-vertex(c1x, g1y, [$0_H$], r: 0.28, text-size: 8.6pt)
  #for deg in (40, 160, 280) {
    let rad = deg * 1deg
    aod-marker(c1x + 0.62 * calc.cos(rad), g1y - 0.62 * calc.sin(rad), kind: "circle", r-pt: 2.8, color: aod-pal.teal)
  }
  #aod-text(c1x, g1y - 0.82, [$F_1$], size: 8.6pt, weight: "bold", box-w: 0.7, box-h: 0.34)
  // Alias tags converging cleanly ONTO outer perimeter (drawn on top of circle!)
  #aod-box(c1x - 1.44, py + 0.82, 1.24, 0.38, [#text(size: 7.4pt)[alias $a$]], stroke: 0.7pt + aod-pal.slate, fill: white, radius: 3pt, inset: 1pt)
  #aod-box(c1x + 1.44, py + 0.82, 1.24, 0.38, [#text(size: 7.4pt)[alias $b$]], stroke: 0.7pt + aod-pal.slate, fill: white, radius: 3pt, inset: 1pt)
  #aod-arrow(c1x - 1.16, py + 1.02, c1x - 0.76, py + 1.45, stroke: (paint: aod-pal.slate, thickness: 0.85pt, dash: "dashed"), head-len: 3.6, head-half: 1.7)
  #aod-arrow(c1x + 1.16, py + 1.02, c1x + 0.76, py + 1.45, stroke: (paint: aod-pal.slate, thickness: 0.85pt, dash: "dashed"), head-len: 3.6, head-half: 1.7)
  #aod-text(c1x, py + 3.58, [self-return $upright("ADAR")_(1 arrow.l 1)$], size: 8.6pt, box-w: 3.4, box-h: 0.38)

  #aod-box-tl(px1 + 0.22, py + 3.92, pw - 0.44, 2.04, [
    #text(size: 8.6pt)[$cal(F)_(cal(B)) = {F_1}$ (resolved)] \
    #v(3pt)
    #text(size: 8.6pt, weight: "bold")[$n_F = 1$, $med cal(O)_(partial F) = 1 log 1 = 0$] \
    #v(3pt)
    #text(size: 7.6pt)[Recurrent monon-mode field; \ aliases collapse before count.]
  ], stroke: 0.8pt + aod-pal.blue, fill: white, radius: 3pt, inset: 4pt)

  // === Case 2: Two-Field Disoma inside B_12 (n_F = 2) ===
  #aod-box-tl(px2, py, pw, ph, [], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green, radius: 4pt)
  #aod-text(px2 + pw / 2, py + 0.32, [*Case 2: Disoma ($n_F = 2$)*], size: 8.6pt, box-w: 4.2, box-h: 0.40)

  #let c2x = px2 + pw / 2
  // Enclosing scope stadium B_12
  #aod-box-tl(px2 + 0.22, py + 0.74, pw - 0.44, 2.94, [], stroke: 1.05pt + aod-pal.navy, fill: white, radius: 18pt)
  #aod-text(c2x, py + 1.00, [scope $B_(12) = (partial F_(12), omega_(12))$], size: 8.6pt, box-w: 3.8, box-h: 0.36)
  // Left field F_1
  #let f1x = c2x - 1.06
  #let fcy = py + 2.28
  #aod-arc-arrow(f1x, fcy, 0.58, 30, 325, stroke: 1.0pt + aod-pal.blue, head-len: 3.4, head-half: 1.6)
  #aod-chiral-vertex(f1x, fcy, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-text(f1x, fcy + 0.84, [$F_1$], size: 8.6pt, weight: "bold", box-w: 0.6, box-h: 0.34)
  // Right field F_2
  #let f2x = c2x + 1.06
  #aod-arc-arrow(f2x, fcy, 0.58, 210, 505, stroke: 1.0pt + aod-pal.teal, head-len: 3.4, head-half: 1.6)
  #aod-chiral-vertex(f2x, fcy, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-text(f2x, fcy + 0.84, [$F_2$], size: 8.6pt, weight: "bold", box-w: 0.6, box-h: 0.34)
  // Cross-return purple arrows
  #aod-curve-arrow(f1x + 0.44, fcy - 0.42, c2x, fcy - 0.90, f2x - 0.44, fcy - 0.42, stroke: 1.0pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-curve-arrow(f2x - 0.44, fcy + 0.42, c2x, fcy + 0.90, f1x + 0.44, fcy + 0.42, stroke: 1.0pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-text(c2x, fcy - 0.86, [cross], size: 7.4pt, box-w: 1.1, box-h: 0.30)

  #aod-box-tl(px2 + 0.22, py + 3.92, pw - 0.44, 2.04, [
    #text(size: 9.0pt)[$cal(F)_(B_#text(size: 12.2pt)[12]) = {F_1, F_2}$] \
    #v(3pt)
    #text(size: 8.6pt, weight: "bold")[$n_F = 2$, $med cal(O)_(partial F) = 2 log 2$] \
    #v(3pt)
    #text(size: 8.6pt)[Self + cross $upright("ADAR")_(i arrow.l j)$]
  ], stroke: 0.8pt + aod-pal.green, fill: white, radius: 3pt, inset: 4pt)

  // --- Bottom Count-Pipeline & Alias-Resolution Bar (y = 7.64 .. 8.98) ---
  #aod-box-tl(
    0.34, 7.64, 14.12, 1.34,
    [
      #text(size: 8.6pt)[*Count pipeline:* $cal(B) -> op("Resolve")(cal(F)_(cal(B))) -> n_F (cal(B)) -> upright("ADAR")_(i arrow.l j) -> cal(O)_(partial F) (cal(B)) -> upright("SADAR")$] \
      #v(4pt)
      #text(size: 8.6pt)[*Calculation split:* Alias resolution precedes counting; shell/enclosure routing ($sans("C")_(2 m) -> upright("SheddicPath")$) is a separate calculation on $cal(B)$.]
    ],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3.5pt,
    inset: 5pt,
  )
]
