// Native Typst vector figure: sadar-boundary-relative-balance (Main §5)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.7

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [SADAR boundary-relative balance],
    subtitle: [Coexisting scopes ($B_1, B_2, cal(B)_(12)$), committed causal update ($k -> k+1$), and declared sheddic excess],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Left: Nested Scope Geometry (x = 0.30 .. 8.80, y = 1.28 .. 8.28) ---
  #aod-box-tl(0.30, 1.28, 8.50, 7.00, [], stroke: 1.2pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 22pt)
  #aod-box(4.55, 1.60, 5.50, 0.46, [
    #text(size: 8.6pt)[*Enclosing scope* $cal(B)_(12) = (partial F_(12), omega_(12))$]
  ], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 4pt, inset: 2pt)

  // Component Field F_1 on B_1
  #let x1 = 2.40
  #let cy = 4.46
  #aod-circle(x1, cy, 1.60, fill: white, stroke: 1.1pt + aod-pal.blue)
  #aod-text(x1, cy - 0.98, [*Field $F_1$* on $B_1$], size: 8.6pt, box-w: 2.3, box-h: 0.38)
  #aod-arc-arrow(x1, cy - 0.04, 0.50, 25, 325, stroke: 0.95pt + aod-pal.blue, head-len: 3.6, head-half: 1.7)
  #aod-chiral-vertex(x1, cy - 0.04, [$0_H$], r: 0.27, text-size: 8.6pt)
  #aod-text(x1, cy + 0.68, [$upright("ADAR")_(1 arrow.l 1)$], size: 8.6pt, box-w: 2.2, box-h: 0.38)
  #aod-text(x1, cy + 1.14, [$bold(upright(A))_(F_#text(size: 12.2pt)[1]) (B_1)$], size: 9.0pt, box-w: 2.2, box-h: 0.42)

  // Component Field F_2 on B_2
  #let x2 = 6.70
  #aod-circle(x2, cy, 1.60, fill: white, stroke: 1.1pt + aod-pal.teal)
  #aod-text(x2, cy - 0.98, [*Field $F_2$* on $B_2$], size: 8.6pt, box-w: 2.3, box-h: 0.38)
  #aod-arc-arrow(x2, cy - 0.04, 0.50, 205, 505, stroke: 0.95pt + aod-pal.teal, head-len: 3.6, head-half: 1.7)
  #aod-chiral-vertex(x2, cy - 0.04, [$0_H$], r: 0.27, text-size: 8.6pt)
  #aod-text(x2, cy + 0.68, [$upright("ADAR")_(2 arrow.l 2)$], size: 8.6pt, box-w: 2.2, box-h: 0.38)
  #aod-text(x2, cy + 1.14, [$bold(upright(A))_(F_#text(size: 12.2pt)[2]) (B_2)$], size: 9.0pt, box-w: 2.2, box-h: 0.42)

  // Purple Cross-Return Arrows between F_1 and F_2 (0.23cm clear white gap to pill borders)
  #aod-curve-arrow(3.62, 3.36, 4.55, 2.52, 5.48, 3.36, stroke: 1.1pt + aod-pal.purple, head-len: 4.0, head-half: 1.9)
  #aod-box(4.55, 2.48, 2.18, 0.46, [#text(size: 8.6pt)[$upright("ADAR")_(2 arrow.l 1)$]], stroke: 0.75pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3pt, inset: 2pt)
  #aod-curve-arrow(5.48, 5.56, 4.55, 6.40, 3.62, 5.56, stroke: 1.1pt + aod-pal.purple, head-len: 4.0, head-half: 1.9)
  #aod-box(4.55, 6.44, 2.18, 0.46, [#text(size: 8.6pt)[$upright("ADAR")_(1 arrow.l 2)$]], stroke: 0.75pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3pt, inset: 2pt)

  // Enclosing Resultant Pill
  #aod-box-tl(0.88, 7.04, 7.34, 1.02, [
    #text(size: 9.0pt)[*Enclosing resultant:* $bold(upright(A))_(F_#text(size: 12.2pt)[1] parallel F_#text(size: 12.2pt)[2]) (cal(B)_(12))$] \
    #v(2pt)
    #text(size: 8.6pt)[evaluated on $partial F_(12)$ after membership resolves]
  ], stroke: 0.9pt + aod-pal.navy, fill: white, radius: 4pt, inset: 4pt)

  // Connector arrow from Left Scopes -> Right Causal Stack
  #aod-arrow(8.84, 4.46, 9.26, 4.46, stroke: 1.15pt + aod-pal.navy)

  // --- Right: Causal Update & Sheddic Excess Stack (x = 9.30 .. 14.70) ---
  #let rx = 9.30
  #let rw = 5.40
  #let rcx = rx + rw / 2

  // Stage 1: Committed Attention (<= k)
  #aod-box-tl(rx, 1.28, rw, 2.12, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 4pt)
  #aod-circle(rx + 0.34, 1.60, 0.18, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.navy)
  #aod-text(rx + 0.34, 1.60, [*1*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(rx + 0.62, 1.60, [*Committed Attention ($lt.eq k$)*], size: 8.6pt, anchor: "left", box-w: 4.6, box-h: 0.42)
  #aod-text(rcx, 2.38, [$bold(upright(A))_(F, k) (B) = sum_(e in F(B)) C_(3, e) rho^D_(omega, e) Delta chi^(upright("lag"))_(e, k) i_(e, k)$], size: 8.6pt, box-w: 5.2, box-h: 0.56)
  #aod-text(rcx, 3.06, [pressure, lag & duration ($lt.eq k$)], size: 8.6pt, box-w: 5.1, box-h: 0.40)

  // Causal Transition Arrow (k -> k+1)
  #let tax = 11.40
  #aod-arrow(tax, 3.43, tax, 3.98, stroke: 1.15pt + aod-pal.green, head-len: 4.4, head-half: 2.1)
  #aod-text(tax + 0.26, 3.70, [cut $k -> k+1$], size: 8.6pt, anchor: "left", box-w: 2.6, box-h: 0.38)

  // Stage 2: Causal Motion (k -> k+1)
  #aod-box-tl(rx, 4.02, rw, 1.98, [], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green, radius: 4pt)
  #aod-circle(rx + 0.34, 4.34, 0.18, fill: white, stroke: 0.85pt + aod-pal.green)
  #aod-text(rx + 0.34, 4.34, [*2*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(rx + 0.62, 4.34, [*Realized Causal Motion*], size: 8.4pt, anchor: "left", box-w: 4.6, box-h: 0.42)
  #aod-text(rcx, 5.04, [$S^W_(F, k+1) = cal(U)^(upright("SADAR"))_B (S^W_(lt.eq k), S^(times)_(lt.eq k), bold(upright(A))_(F, lt.eq k))$], size: 8.6pt, box-w: 5.2, box-h: 0.50)
  #aod-text(rcx, 5.66, [realized motion; no same-step feedback], size: 7.5pt, box-w: 5.1, box-h: 0.38)

  // Wavy Orange Shedding Excess Arrow (kept cleanly inside right canvas edge)
  #aod-wavy-arrow(tax, 6.03, tax, 6.62, amp: 0.065, waves: 2.5, stroke: 1.15pt + aod-pal.orange, head-len: 4.2, head-half: 2.0)
  #aod-text(tax + 0.26, 6.32, [excess $X_(upright("shedding")) > 0$], size: 8.6pt, anchor: "left", box-w: 2.95, box-h: 0.40)

  // Stage 3: Declared Sheddic Path
  #aod-box-tl(rx, 6.66, rw, 1.62, [], stroke: 0.95pt + aod-pal.orange, fill: aod-pal.tint-orange, radius: 4pt)
  #aod-circle(rx + 0.34, 6.98, 0.18, fill: white, stroke: 0.85pt + aod-pal.orange)
  #aod-text(rx + 0.34, 6.98, [*3*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(rx + 0.62, 6.98, [*Declared Sheddic Path*], size: 8.2pt, anchor: "left", box-w: 3.6, box-h: 0.40)
  #aod-text(rx + 2.22, 7.56, [$upright("SheddicPath") in {E_2, sans("C")_6, sans("C")_8, dots}$], size: 8.6pt, box-w: 4.1, box-h: 0.42)
  #aod-text(rx + 2.22, 8.00, [seat-compatible outer routing], size: 7.5pt, box-w: 4.0, box-h: 0.34)
  // Mini C_6 seat-ring glyph on right inside card
  #aod-seat-ring(rx + 4.74, 7.48, 0.34, 6, ring-stroke: 1.05pt + aod-pal.gold, seat-r: 0.048)
  #aod-text(rx + 4.74, 7.48, [$sans("C")_6$], size: 8.6pt, box-w: 0.6, box-h: 0.38)

  // --- Bottom Projection Guard Bar ---
  #aod-box-tl(
    0.30, 8.54, 14.40, 0.88,
    [#text(size: 8.2pt)[*Projection guard:* Component projections select declared components of the already-fixed SADAR attention vector; they never introduce a separate motion law.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
    inset: 5pt,
  )
]
