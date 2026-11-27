// Native Typst vector figure: cycle-wave-identity (Main §5)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 9.55

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [SADAR value trace of admitted recurrence],
    subtitle: [Chiral return alternation ($op("flip")_mu$) projects onto signed discrete cut trace $v_B (W)$ over $omega = (u, v]$],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Tier 1: Chiral Hinge-Return Package Alternation (y = 1.24 .. 3.60) ---
  #let t1-y = 1.24
  #let t1-h = 2.36
  #let sw = 3.92
  #let sx1 = 0.34
  #let sx2 = 5.44
  #let sx3 = 10.54
  #let gy = t1-y + 1.20

  // Stage 1: A <->_mu Omega (+1)
  #aod-box-tl(sx1, t1-y, sw, t1-h, [], stroke: 0.9pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(sx1 + sw / 2, t1-y + 0.28, [*1. Open ($chi_mu = +1$)*], size: 8.6pt, box-w: 3.7, box-h: 0.38)
  #aod-circle(sx1 + 0.80, gy, 0.26, fill: white, stroke: 1.0pt + aod-pal.blue)
  #aod-text(sx1 + 0.80, gy, [$A$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-chiral-vertex(sx1 + sw / 2, gy, [$mu$], r: 0.25, text-size: 8.8pt)
  #aod-circle(sx1 + sw - 0.80, gy, 0.26, fill: aod-pal.tint-orange, stroke: 1.0pt + aod-pal.orange)
  #aod-text(sx1 + sw - 0.80, gy, [$Omega$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-arrow(sx1 + 1.08, gy, sx1 + sw / 2 - 0.28, gy, stroke: 0.95pt + aod-pal.blue, head-len: 3.4, head-half: 1.6, both: true)
  #aod-arrow(sx1 + sw / 2 + 0.28, gy, sx1 + sw - 1.08, gy, stroke: 0.95pt + aod-pal.orange, head-len: 3.4, head-half: 1.6, both: true)
  #aod-curve-arrow(sx1 + 0.88, gy - 0.28, sx1 + sw / 2, t1-y + 0.54, sx1 + sw - 0.88, gy - 0.28, stroke: 0.9pt + aod-pal.navy, head-len: 3.4, head-half: 1.6)
  #aod-text(sx1 + sw / 2, t1-y + 2.00, [$A scripts(arrow.l.r)_mu Omega$ (forward order)], size: 8.8pt, box-w: 3.7, box-h: 0.44)

  // Curved flip_mu arrow 1 -> 2
  #aod-curve-arrow(sx1 + sw + 0.06, gy - 0.10, (sx1 + sw + sx2) / 2, t1-y + 0.44, sx2 - 0.06, gy - 0.10, stroke: 1.05pt + aod-pal.purple, head-len: 4.0, head-half: 1.9)
  #aod-text((sx1 + sw + sx2) / 2, t1-y + 0.56, [$op("flip")_mu$], size: 8.8pt, weight: "bold", box-w: 1.1, box-h: 0.42)

  // Stage 2: Omega <->_mu A (-1)
  #aod-box-tl(sx2, t1-y, sw, t1-h, [], stroke: 0.9pt + aod-pal.orange, fill: aod-pal.tint-orange, radius: 4pt)
  #aod-text(sx2 + sw / 2, t1-y + 0.28, [*2. Return ($chi_mu = -1$)*], size: 8.6pt, box-w: 3.7, box-h: 0.38)
  #aod-circle(sx2 + 0.80, gy, 0.26, fill: white, stroke: 1.0pt + aod-pal.orange)
  #aod-text(sx2 + 0.80, gy, [$Omega$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-chiral-vertex(sx2 + sw / 2, gy, [$mu$], r: 0.25, text-size: 8.8pt)
  #aod-circle(sx2 + sw - 0.80, gy, 0.26, fill: aod-pal.tint-blue, stroke: 1.0pt + aod-pal.blue)
  #aod-text(sx2 + sw - 0.80, gy, [$A$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-arrow(sx2 + 1.08, gy, sx2 + sw / 2 - 0.28, gy, stroke: 0.95pt + aod-pal.orange, head-len: 3.4, head-half: 1.6, both: true)
  #aod-arrow(sx2 + sw / 2 + 0.28, gy, sx2 + sw - 1.08, gy, stroke: 0.95pt + aod-pal.blue, head-len: 3.4, head-half: 1.6, both: true)
  #aod-curve-arrow(sx2 + sw - 0.88, gy + 0.28, sx2 + sw / 2, t1-y + 1.84, sx2 + 0.88, gy + 0.28, stroke: 0.9pt + aod-pal.orange, head-len: 3.4, head-half: 1.6)
  #aod-text(sx2 + sw / 2, t1-y + 2.00, [$Omega scripts(arrow.l.r)_mu A$ (reversed order)], size: 8.8pt, box-w: 3.7, box-h: 0.44)

  // Curved flip_mu arrow 2 -> 3
  #aod-curve-arrow(sx2 + sw + 0.06, gy - 0.10, (sx2 + sw + sx3) / 2, t1-y + 0.44, sx3 - 0.06, gy - 0.10, stroke: 1.05pt + aod-pal.purple, head-len: 4.0, head-half: 1.9)
  #aod-text((sx2 + sw + sx3) / 2, t1-y + 0.56, [$op("flip")_mu$], size: 8.8pt, weight: "bold", box-w: 1.1, box-h: 0.42)

  // Stage 3: A <->_mu Omega (+1, reclosure)
  #aod-box-tl(sx3, t1-y, sw, t1-h, [], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green, radius: 4pt)
  #aod-text(sx3 + sw / 2, t1-y + 0.28, [*3. Reclosed ($chi_mu = +1$)*], size: 8.6pt, box-w: 3.7, box-h: 0.38)
  #aod-circle(sx3 + 0.80, gy, 0.26, fill: white, stroke: 1.0pt + aod-pal.blue)
  #aod-text(sx3 + 0.80, gy, [$A$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-chiral-vertex(sx3 + sw / 2, gy, [$mu$], r: 0.25, text-size: 8.8pt)
  #aod-circle(sx3 + sw - 0.80, gy, 0.26, fill: aod-pal.tint-orange, stroke: 1.0pt + aod-pal.orange)
  #aod-text(sx3 + sw - 0.80, gy, [$Omega$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-arrow(sx3 + 1.08, gy, sx3 + sw / 2 - 0.28, gy, stroke: 0.95pt + aod-pal.blue, head-len: 3.4, head-half: 1.6, both: true)
  #aod-arrow(sx3 + sw / 2 + 0.28, gy, sx3 + sw - 1.08, gy, stroke: 0.95pt + aod-pal.orange, head-len: 3.4, head-half: 1.6, both: true)
  #aod-curve-arrow(sx3 + 0.88, gy - 0.28, sx3 + sw / 2, t1-y + 0.54, sx3 + sw - 0.88, gy - 0.28, stroke: 0.95pt + aod-pal.green, head-len: 3.4, head-half: 1.6)
  #aod-text(sx3 + sw / 2, t1-y + 2.00, [$A scripts(arrow.l.r)_mu Omega$ (reclosed on $B$)], size: 8.8pt, box-w: 3.7, box-h: 0.44)

  // --- Projection Bridge (y = 3.64 .. 4.62) ---
  #aod-line(sx1 + sw / 2, t1-y + t1-h, sx1 + sw / 2, 4.10, stroke: 0.85pt + aod-pal.slate)
  #aod-line(sx3 + sw / 2, t1-y + t1-h, sx3 + sw / 2, 4.10, stroke: 0.85pt + aod-pal.slate)
  #aod-line(sx1 + sw / 2, 4.10, sx3 + sw / 2, 4.10, stroke: 0.85pt + aod-pal.slate)
  #aod-arrow(7.40, t1-y + t1-h, 7.40, 4.68, stroke: 1.1pt + aod-pal.navy, head-len: 4.2, head-half: 2.0)
  #aod-box(7.40, 4.10, 9.80, 0.50, [
    #text(size: 8.6pt)[*Temporal SADAR projection:* $frak(S)_(B bar.v t) (C_t)$ evaluated at cuts $t in omega$]
  ], stroke: 0.85pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 4pt, inset: 2pt)

  // --- Tier 2: Signed Discrete Cut Stem Plot + Value Trace Card (y = 4.72 .. 8.32) ---
  #let t2-y = 4.72
  #let t2-h = 3.60

  // Left: Signed Discrete Cut Stem Plot (x = 0.34 .. 8.78, w = 8.44)
  #aod-box-tl(0.34, t2-y, 8.44, t2-h, [], stroke: 0.9pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-text(4.56, t2-y + 0.28, [*Signed discrete cut trace on half-open $omega = (u, v]$*], size: 8.6pt, box-w: 8.0, box-h: 0.40)

  #let ax-l = 1.44
  #let ax-r = 8.36
  #let ax-y = t2-y + 2.12
  #aod-line(ax-l, t2-y + 1.04, ax-l, t2-y + 3.20, stroke: 0.8pt + aod-pal.axis)
  #aod-line(ax-l, ax-y - 0.72, ax-r, ax-y - 0.72, stroke: (paint: aod-pal.grid, thickness: 0.55pt, dash: "dashed"))
  #aod-line(ax-l, ax-y + 0.72, ax-r, ax-y + 0.72, stroke: (paint: aod-pal.grid, thickness: 0.55pt, dash: "dashed"))
  #aod-arrow(ax-l, ax-y, ax-r, ax-y, stroke: 0.85pt + aod-pal.axis, head-len: 3.8, head-half: 1.8)
  #aod-text(ax-l - 0.16, ax-y - 0.72, [$+$], size: 8.8pt, anchor: "right", box-w: 0.7, box-h: 0.36)
  #aod-text(ax-l - 0.16, ax-y, [$0_H$], size: 8.6pt, anchor: "right", box-w: 0.8, box-h: 0.38)
  #aod-text(ax-l - 0.16, ax-y + 0.72, [$-$], size: 8.8pt, anchor: "right", box-w: 0.7, box-h: 0.36)

  // Half-open window highlight bar (u, v]
  #let ux = 1.82
  #let vx = 7.78
  #aod-line(ux, ax-y, vx, ax-y, stroke: 1.7pt + aod-pal.blue)
  #aod-marker(ux, ax-y, kind: "open-circle", r-pt: 2.9, color: aod-pal.blue)
  #aod-marker(vx, ax-y, kind: "circle", r-pt: 2.9, color: aod-pal.blue)
  #aod-text(ux, ax-y + 0.36, [$u$], size: 8.6pt, box-w: 0.5, box-h: 0.36)
  #aod-text(vx + 0.22, ax-y + 0.36, [$v$], size: 8.6pt, box-w: 0.5, box-h: 0.36)

  // Four alternating signed stems at t_1 .. t_4
  #let stems = (
    (2.64, 1, [$t_1$], [$+1$], aod-pal.blue),
    (4.14, -1, [$t_2$], [$-1$], aod-pal.orange),
    (5.64, 1, [$t_3$], [$+1$], aod-pal.blue),
    (7.14, -1, [$t_4$], [$-1$], aod-pal.orange),
  )
  #for (sx, sgn, tlbl, slbl, col) in stems {
    let tipy = ax-y - sgn * 0.72
    aod-line(sx, ax-y, sx, tipy, stroke: 1.55pt + col)
    aod-marker(sx, tipy, kind: "circle", r-pt: 3.1, color: col)
    aod-text(sx, ax-y + sgn * 0.34, tlbl, size: 8.6pt, box-w: 0.7, box-h: 0.36)
    aod-text(sx, tipy - sgn * 0.24, slbl, size: 8.0pt, weight: "bold", box-w: 0.8, box-h: 0.34)
  }
  // Retained 0_H hinge beads on baseline between sign inversions
  #for hx in (3.39, 4.89, 6.39) {
    aod-circle(hx, ax-y, 0.085, fill: aod-pal.tint-amber, stroke: 0.85pt + aod-pal.gold)
  }
  // Place parity note cleanly in empty upper-right quadrant above downward stem t_4
  #aod-box(7.34, t2-y + 1.03, 2.48, 0.94, [
    #text(size: 8.6pt)[$A Omega = -Omega A$ \ ($0_H$ retained)]
  ], stroke: 0.75pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 3.5pt, inset: 4pt, leading: 0.50em)

  // Right: Downstream Value-Trace Card (x = 9.02 .. 14.46, w = 5.44)
  #aod-box-tl(9.02, t2-y, 5.44, t2-h, [], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(11.74, t2-y + 0.34, [*Downstream Value Trace*], size: 8.8pt, box-w: 5.1, box-h: 0.40)
  #aod-box-tl(9.22, t2-y + 0.72, 5.04, 0.72, [
    #text(size: 8.6pt)[$v_B (W) = { (t, frak(S)_(B bar.v t) (C_t)) : t in omega }$]
  ], stroke: 0.85pt + aod-pal.blue, fill: white, radius: 3pt, inset: 3pt)
  #aod-text(9.30, t2-y + 1.84, [$C_t$: bound cycle on committed cut $t$], size: 8.6pt, anchor: "left", box-w: 5.0, box-h: 0.42)
  #aod-text(9.30, t2-y + 2.44, [Parity: $A Omega = -Omega A$ ($0_H$ retained)], size: 8.6pt, anchor: "left", box-w: 5.0, box-h: 0.42)
  #aod-text(9.30, t2-y + 3.04, [Window: half-open $u in.not omega, med v in omega$], size: 8.6pt, anchor: "left", box-w: 5.0, box-h: 0.42)

  // --- Bottom Admission Guard Bar ---
  #aod-box-tl(
    0.34, 8.54, 14.12, 0.82,
    [#text(size: 8.6pt)[*Admission guard:* $v_B (W)$ records downstream SADAR values of an already-admitted recurrent wave $W$; a signed trace alone confers no wave admission.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3.5pt,
    inset: 5pt,
  )
]
