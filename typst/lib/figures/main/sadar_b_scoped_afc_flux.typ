// Native Typst vector figure: sadar-b-scoped-afc-flux (Main §5)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 11.55

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [SADAR as $B$-scoped A$Omega$D flux],
    subtitle: [Magnitude $p^D_(i j)$ and chiral direction $A_(i j)$ compose into antisymmetric flux $phi.alt_(i j)(B)$ on $B = (partial F, omega)$],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Top Typed-Flux Firewall Banner (y = 1.24 .. 1.88) ---
  #aod-box-tl(0.30, 1.24, 6.80, 0.64, [
    #text(size: 8.6pt)[*AFC:* $phi.alt^(upright("AFC"))_(i j) = p^(upright("mem"))_i P_(i j) - p^(upright("mem"))_j P_(j i) in [-1, 1]$]
  ], stroke: 0.85pt + aod-pal.slate, fill: aod-pal.tint-gray, radius: 3pt, inset: 3pt)
  #aod-circle(7.50, 1.56, 0.25, fill: aod-pal.tint-orange, stroke: 1.05pt + aod-pal.crimson)
  #aod-text(7.50, 1.56, [$eq.not$], size: 9.5pt, weight: "bold", box-w: 0.5, box-h: 0.45)
  #aod-box-tl(7.90, 1.24, 6.80, 0.64, [
    #text(size: 8.6pt)[*A$Omega$D:* $phi.alt^(upright("AOD"))_(i j)(B) = p^D_(i j)(B) A_(i j)(B)$ (count-domain)]
  ], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-amber, radius: 3pt, inset: 3pt)

  // --- Double-Hatched Outer Scope Frame B = (partial F, omega) (y = 2.12 .. 8.16) ---
  #aod-boundary-wall(0.34, 2.12, 0.34, 8.16, stroke: 1.1pt + aod-pal.navy, hatch-side: 1, hatch-count: 15, hatch-len: 0.12, double-line: true)
  #aod-boundary-wall(14.66, 2.12, 14.66, 8.16, stroke: 1.1pt + aod-pal.navy, hatch-side: -1, hatch-count: 15, hatch-len: 0.12, double-line: true)
  #aod-line(0.34, 2.12, 14.66, 2.12, stroke: (paint: aod-pal.navy, thickness: 0.85pt, dash: "dashed"))
  #aod-line(0.34, 8.16, 14.66, 8.16, stroke: (paint: aod-pal.navy, thickness: 0.85pt, dash: "dashed"))
  #aod-box(7.50, 2.12, 4.45, 0.44, [#text(size: 8.6pt)[*Declared scope* $B = (partial F, omega)$]], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 3.5pt, inset: 2pt)

  // --- Upper Magnitude Branch (y = 2.48 .. 5.14, h = 2.66) ---
  #let my0 = 2.48
  #let mh = 2.66
  #let mcy = my0 + mh / 2

  // M1: RCD & Duration (widened so RCD equation sits cleanly on 1 line)
  #aod-box-tl(0.56, my0, 4.06, mh, [], stroke: 0.9pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 3.5pt)
  #aod-text(2.59, my0 + 0.28, [*RCD & Duration*], size: 8.2pt, box-w: 3.9, box-h: 0.36)
  #aod-text(2.59, my0 + 0.78, [$op("RCD")_(i j) = R D_B (C_(i j)) bowtie_B R^(upright("asym"))_(i j)$], size: 8.6pt, box-w: 3.98, box-h: 0.48)
  #aod-arrow(2.59, my0 + 1.16, 2.59, my0 + 1.54, stroke: 0.85pt + aod-pal.blue, head-len: 3.4, head-half: 1.6)
  #aod-text(2.59, my0 + 1.88, [$rho^D_(i j)(B) = op("dur")(op("RCD")_(i j))$], size: 8.6pt, box-w: 3.9, box-h: 0.42)
  #aod-text(2.59, my0 + 2.34, [neutral: $rho^D_(i j) = D_(i j)$], size: 8.6pt, box-w: 3.9, box-h: 0.38)

  #aod-arrow(4.64, mcy, 4.88, mcy, stroke: 1.0pt + aod-pal.blue)

  // M2: Window Clip
  #aod-box-tl(4.90, my0, 3.44, mh, [], stroke: 0.9pt + aod-pal.blue, fill: white, radius: 3.5pt)
  #aod-text(6.62, my0 + 0.28, [*Window Clip*], size: 8.2pt, box-w: 3.3, box-h: 0.36)
  // Geometric bar-clip glyph (taller 0.56cm bar for clean subscript clearance)
  #place(top + left, dx: 5.14cm, dy: (my0 + 0.58) * 1cm, rect(width: 1.82cm, height: 0.56cm, fill: aod-pal.tint-blue, stroke: 0.9pt + aod-pal.blue))
  #place(top + left, dx: 6.96cm, dy: (my0 + 0.58) * 1cm, rect(width: 1.14cm, height: 0.56cm, fill: aod-pal.tint-orange, stroke: (paint: aod-pal.orange, thickness: 0.9pt, dash: "dashed")))
  #aod-line(6.96, my0 + 0.50, 6.96, my0 + 1.24, stroke: 1.25pt + aod-pal.crimson)
  #aod-text(6.05, my0 + 0.85, [$rho^D_(omega, i j)$], size: 8.6pt, box-w: 1.75, box-h: 0.44)
  #aod-text(7.53, my0 + 0.85, [$Q^D$], size: 8.6pt, box-w: 1.05, box-h: 0.44)
  #aod-text(6.96, my0 + 1.46, [clip $bar.v omega bar.v_(i j)$], size: 8.6pt, box-w: 2.0, box-h: 0.36)
  #aod-text(6.62, my0 + 1.92, [$rho^D_(omega, i j) = min(rho^D_(i j), bar.v omega bar.v_(i j))$], size: 8.6pt, box-w: 3.36, box-h: 0.44)
  #aod-text(6.62, my0 + 2.34, [overhang $Q^D$ separate], size: 8.6pt, box-w: 3.3, box-h: 0.38)

  #aod-arrow(8.36, mcy, 8.60, mcy, stroke: 1.0pt + aod-pal.blue)

  // M3: Count-domain Magnitude p^D
  #aod-box-tl(8.62, my0, 2.68, mh, [], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 3.5pt)
  #aod-text(9.96, my0 + 0.32, [*Magnitude*], size: 8.4pt, box-w: 2.5, box-h: 0.40)
  #aod-text(9.96, my0 + 1.20, [$p^D_(i j)(B) =$ \ $C_(3, i j) thin rho^D_(omega, i j)(B)$], size: 8.8pt, box-w: 2.58, box-h: 0.96)
  #aod-text(9.96, my0 + 2.18, [count-domain \ channel pressure], size: 7.4pt, box-w: 2.5, box-h: 0.65)

  // --- Lower Direction Branch (y = 5.36 .. 7.98, h = 2.62) ---
  #let dy0 = 5.36
  #let dh = 2.62
  #let dcy = dy0 + dh / 2

  // D1: Oriented Incidence Cut
  #aod-box-tl(0.56, dy0, 4.06, dh, [], stroke: 0.9pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 3.5pt)
  #aod-text(2.59, dy0 + 0.28, [*Oriented Cut Incidence*], size: 7.8pt, box-w: 3.9, box-h: 0.36)
  #aod-boundary-wall(2.59, dy0 + 0.60, 2.59, dy0 + 1.78, stroke: 1.0pt + aod-pal.navy, hatch-side: -1, hatch-count: 5, hatch-len: 0.10)
  #aod-circle(1.44, dy0 + 1.14, 0.25, fill: white, stroke: 0.95pt + aod-pal.green)
  #aod-text(1.44, dy0 + 1.14, [$i$], size: 8.8pt, weight: "bold", box-w: 0.5, box-h: 0.4)
  #aod-text(1.44, dy0 + 1.60, [$i in R$], size: 8.6pt, box-w: 1.1, box-h: 0.36)
  #aod-circle(3.74, dy0 + 1.14, 0.25, fill: white, stroke: 0.95pt + aod-pal.slate)
  #aod-text(3.74, dy0 + 1.14, [$j$], size: 8.8pt, weight: "bold", box-w: 0.5, box-h: 0.4)
  #aod-text(3.74, dy0 + 1.60, [$j in.not R$], size: 8.6pt, box-w: 1.2, box-h: 0.36)
  #aod-arrow(1.72, dy0 + 1.02, 3.46, dy0 + 1.02, stroke: 1.05pt + aod-pal.blue, head-len: 3.6, head-half: 1.7)
  #aod-arrow(3.46, dy0 + 1.26, 1.72, dy0 + 1.26, stroke: (paint: aod-pal.orange, thickness: 0.9pt, dash: "dashed"), head-len: 3.4, head-half: 1.6)
  #aod-text(2.59, dy0 + 2.22, [$phi.alt_(j i) = -phi.alt_(i j)$, $med phi.alt_(i i) = 0$], size: 8.6pt, box-w: 3.9, box-h: 0.44)

  #aod-arrow(4.64, dcy, 4.88, dcy, stroke: 1.0pt + aod-pal.teal)

  // D2: Chiral Lead-Lag Pair around 0_H
  #aod-box-tl(4.90, dy0, 3.44, dh, [], stroke: 0.9pt + aod-pal.teal, fill: white, radius: 3.5pt)
  #aod-text(6.62, dy0 + 0.28, [*Chiral Lead–Lag Pair*], size: 7.8pt, box-w: 3.3, box-h: 0.36)
  #let lcx = 6.62
  #let lcy = dy0 + 1.22
  #aod-arc-arrow(lcx, lcy, 0.55, 175, 25, stroke: 1.15pt + aod-pal.blue, head-len: 3.8, head-half: 1.8)
  #aod-arc-arrow(lcx, lcy, 0.55, 345, 210, stroke: 1.15pt + aod-pal.orange, head-len: 3.8, head-half: 1.8)
  #aod-chiral-vertex(lcx, lcy, [$0_H$], r: 0.27, text-size: 8.6pt)
  #aod-text(lcx - 1.10, lcy - 0.14, [lead], size: 7.5pt, box-w: 0.95, box-h: 0.36)
  #aod-text(lcx + 1.10, lcy + 0.14, [lag], size: 7.5pt, box-w: 0.95, box-h: 0.36)
  #aod-text(6.62, dy0 + 2.22, [lead–lag $Delta chi^(upright("lag"))_(i j)$ & $i_(i j)(B)$], size: 8.6pt, box-w: 3.36, box-h: 0.44)

  #aod-arrow(8.36, dcy, 8.60, dcy, stroke: 1.0pt + aod-pal.teal)

  // D3: Direction A_{ij}
  #aod-box-tl(8.62, dy0, 2.68, dh, [], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green, radius: 3.5pt)
  #aod-text(9.96, dy0 + 0.32, [*Direction*], size: 8.4pt, box-w: 2.5, box-h: 0.40)
  #aod-text(9.96, dy0 + 1.20, [$A_(i j)(B) =$ \ $Delta chi^(upright("lag"))_(i j)(B) thin i_(i j)(B)$], size: 8.8pt, box-w: 2.58, box-h: 0.96)
  #aod-text(9.96, dy0 + 2.18, [signed boundary \ orientation sense], size: 7.4pt, box-w: 2.5, box-h: 0.65)

  // --- Right Product Vertex x -> Channel Flux ---
  #let px = 11.78
  #let py = 5.25
  #aod-arrow(11.33, mcy, px - 0.14, py - 0.24, stroke: 1.05pt + aod-pal.blue, head-len: 3.8, head-half: 1.8)
  #aod-arrow(11.33, dcy, px - 0.14, py + 0.24, stroke: 1.05pt + aod-pal.teal, head-len: 3.8, head-half: 1.8)
  #aod-chiral-vertex(px, py, [$times$], r: 0.26, fill: aod-pal.tint-amber, stroke: 1.1pt + aod-pal.gold, text-size: 11pt)
  #aod-arrow(px + 0.28, py, 12.28, py, stroke: 1.1pt + aod-pal.navy, head-len: 4.0, head-half: 1.9)

  #aod-box-tl(12.31, 3.88, 2.08, 2.74, [
    #text(size: 8.4pt, weight: "bold")[Channel Flux] \
    #v(4pt)
    #text(size: 8.8pt)[$phi.alt_(i j)(B)$ \ $= p^D_(i j) A_(i j)$] \
    #v(4pt)
    #text(size: 7.4pt)[antisymmetric \ $B$-scoped value]
  ], stroke: 1.05pt + aod-pal.navy, fill: aod-pal.tint-purple, radius: 4pt, inset: 4pt)

  // Connector from Channel Flux to Bottom Triad
  #aod-line(13.35, 6.62, 13.35, 8.42, stroke: 1.05pt + aod-pal.navy)
  #aod-line(13.35, 8.42, 2.48, 8.42, stroke: 1.05pt + aod-pal.navy)
  #aod-arrow(2.48, 8.42, 2.48, 8.68, stroke: 1.05pt + aod-pal.navy, head-len: 4.0, head-half: 1.9)

  // --- Bottom Triad: Finite Stokes -> Attention Vector -> Causal Motion (y = 8.70 .. 11.26) ---
  #let by = 8.70
  #let bh = 2.56

  #aod-box-tl(0.30, by, 4.28, bh, [
    #text(size: 8.2pt, weight: "bold")[(1) Finite Stokes] \
    #v(4pt)
    #text(size: 8.6pt)[$sum_(i in R) op("div")(i; B) =$ \ $sum_(i in R, j in.not R) phi.alt_(i j)(B)$] \
    #v(4pt)
    #text(size: 7.4pt)[internal pairs cancel; lineage kept]
  ], stroke: 0.9pt + aod-pal.navy, fill: white, radius: 3.5pt, inset: 5pt, leading: 0.65em)

  #aod-arrow(4.61, by + bh / 2, 4.92, by + bh / 2, stroke: 1.05pt + aod-pal.navy)

  #aod-box-tl(4.95, by, 4.62, bh, [
    #text(size: 8.0pt, weight: "bold")[(2) SADAR Attention Vector] \
    #v(5pt)
    #text(size: 8.6pt)[$bold(upright(A))_F (B) = sum_((i, j) in F(B)) phi.alt_(i j)(B)$] \
    #v(5pt)
    #text(size: 8.6pt)[committed through cut $k$]
  ], stroke: 0.9pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3.5pt, inset: 5pt, leading: 0.65em)

  #aod-arrow(9.60, by + bh / 2, 9.91, by + bh / 2, stroke: 1.05pt + aod-pal.navy)

  #aod-box-tl(9.94, by, 4.76, bh, [
    #text(size: 8.0pt, weight: "bold")[(3) Causal Motion ($k -> k+1$)] \
    #v(4pt)
    #text(size: 8.6pt)[$S^W_(F, k+1) =$ \ $cal(U)^(upright("SADAR"))_B (S^W_(lt.eq k), S^(times)_(lt.eq k), bold(upright(A))_(F, lt.eq k))$] \
    #v(4pt)
    #text(size: 7.4pt)[committed history precedes transition]
  ], stroke: 0.95pt + aod-pal.green, fill: aod-pal.tint-green, radius: 3.5pt, inset: 5pt, leading: 0.68em)
]
