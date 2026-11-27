// Native Typst vector figure: closure-ladder (Main §3)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 12.10

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [Primitive closure ladder],
    subtitle: [Retained hinge $0_H$ across Monon, Dion ($eq.not$ Dimonon), open Duon $E_2^0$, seated Duad $E_2^(plus.minus)$, and wave],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Left Continuous Gold Structural-Hinge Rail ---
  #let rail-x = 1.05
  #aod-box-tl(0.24, 1.24, 1.62, 9.58, [], stroke: 0.95pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 4pt)
  #aod-box-tl(0.32, 1.32, 1.46, 0.44, [#text(size: 7.4pt, weight: "bold")[Hinge rail]], stroke: 0.75pt + aod-pal.gold, fill: white, radius: 3pt, inset: 2pt)
  #aod-line(rail-x, 1.82, rail-x, 9.97, stroke: 2.0pt + aod-pal.gold)

  // Rung geometry constants (5 spacious rungs, rh = 1.70 cm)
  #let gx = 2.12
  #let gw = 4.48
  #let dx = 6.76
  #let dw = 7.80
  #let rh = 1.70
  #let ys = (1.52, 3.42, 5.32, 7.22, 9.12)

  // Hinge rail beads + horizontal leader lines + inter-rung down arrows
  #for idx in range(5) {
    let ry = ys.at(idx)
    let rcy = ry + rh / 2
    aod-line(rail-x + 0.28, rcy, gx - 0.04, rcy, stroke: 0.95pt + aod-pal.gold)
    aod-chiral-vertex(rail-x, rcy, [$0_H$], r: 0.28, fill: white, stroke: 1.05pt + aod-pal.gold, text-size: 8.6pt)
    if idx < 4 {
      aod-arrow(gx + gw / 2, ry + rh + 0.02, gx + gw / 2, ys.at(idx + 1) - 0.02, stroke: 0.95pt + aod-pal.slate, head-len: 3.6, head-half: 1.7)
    }
  }

  // --- Rung 1: Monon ---
  #let y1 = ys.at(0)
  #let c1 = y1 + rh / 2 + 0.12
  #aod-box-tl(gx, y1, gw, rh, [], stroke: 0.9pt + aod-pal.navy, fill: white, radius: 3.5pt)
  #aod-circle(gx + 0.92, c1, 0.25, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-text(gx + 0.92, c1, [$+1$], size: 8.0pt, weight: "bold", box-w: 0.6, box-h: 0.4)
  #aod-chiral-vertex(gx + 2.24, c1, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-circle(gx + 3.56, c1, 0.25, fill: aod-pal.tint-orange, stroke: 0.95pt + aod-pal.orange)
  #aod-text(gx + 3.56, c1, [$-1$], size: 8.0pt, weight: "bold", box-w: 0.6, box-h: 0.4)
  #aod-arrow(gx + 1.20, c1, gx + 1.94, c1, stroke: 0.95pt + aod-pal.blue, head-len: 3.4, head-half: 1.6)
  #aod-arrow(gx + 2.54, c1, gx + 3.28, c1, stroke: 0.95pt + aod-pal.orange, head-len: 3.4, head-half: 1.6)
  #aod-curve-arrow(gx + 3.56, c1 - 0.28, gx + 2.24, y1 + 0.12, gx + 0.92, c1 - 0.28, stroke: 0.9pt + aod-pal.navy, head-len: 3.4, head-half: 1.6)
  #aod-box-tl(dx, y1, dw, rh, [
    #text(size: 8.6pt)[*1. Monon* — primitive completed branch–hinge–counterbranch closure; $Delta Phi = 1_C$, $med op("bip") = 0$; a lone Monon supplies one cycle, not a field.]
  ], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 3.5pt, inset: 5pt, align-mode: left + horizon, leading: 0.48em)

  // --- Rung 2: Dion != Dimonon ---
  #let y2 = ys.at(1)
  #let c2 = y2 + 1.04
  #aod-box-tl(gx, y2, gw, rh, [], stroke: 0.9pt + aod-pal.teal, fill: white, radius: 3.5pt)
  #aod-text(gx + 1.02, y2 + 0.28, [*Dion*], size: 7.6pt, box-w: 1.8, box-h: 0.34)
  #aod-circle(gx + 0.34, c2, 0.18, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.blue)
  #aod-text(gx + 0.34, c2, [$+$], size: 8.0pt, weight: "bold", box-w: 0.4, box-h: 0.36)
  #aod-chiral-vertex(gx + 1.02, c2, [$0_H$], r: 0.29, text-size: 8.6pt)
  #aod-circle(gx + 1.70, c2, 0.18, fill: aod-pal.tint-orange, stroke: 0.85pt + aod-pal.orange)
  #aod-text(gx + 1.70, c2, [$-$], size: 8.0pt, weight: "bold", box-w: 0.4, box-h: 0.36)
  #aod-line(gx + 0.52, c2, gx + 0.73, c2, stroke: 0.85pt + aod-pal.blue)
  #aod-line(gx + 1.31, c2, gx + 1.52, c2, stroke: 0.85pt + aod-pal.orange)
  // Center crimson != divider
  #aod-line(gx + 2.20, y2 + 0.14, gx + 2.20, y2 + rh - 0.14, stroke: (paint: aod-pal.crimson, thickness: 0.8pt, dash: "dashed"))
  #aod-circle(gx + 2.20, c2, 0.21, fill: aod-pal.tint-orange, stroke: 0.95pt + aod-pal.crimson)
  #aod-text(gx + 2.20, c2, [$eq.not$], size: 9.2pt, weight: "bold", box-w: 0.5, box-h: 0.42)
  // Right half: Dimonon (two separate Monon loops)
  #aod-text(gx + 3.43, y2 + 0.28, [*Dimonon*], size: 7.6pt, box-w: 1.9, box-h: 0.34)
  #aod-circle(gx + 2.94, c2, 0.42, fill: aod-pal.tint-blue, stroke: 0.9pt + aod-pal.navy)
  #aod-chiral-vertex(gx + 2.94, c2, [$0_H$], r: 0.29, text-size: 8.6pt)
  #aod-circle(gx + 3.92, c2, 0.42, fill: aod-pal.tint-blue, stroke: 0.9pt + aod-pal.navy)
  #aod-chiral-vertex(gx + 3.92, c2, [$0_H$], r: 0.29, text-size: 8.6pt)
  #aod-box-tl(dx, y2, dw, rh, [
    #text(size: 8.6pt)[*2. Dion $eq.not$ Dimonon* — Dion: oriented pair $(+1,-1)$ or $(-1,+1)$ on one shared $0_H$; Dimonon $= 2 thin upright("Monon")$ carries two separate Monon closures.]
  ], stroke: 0.85pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 3.5pt, inset: 5pt, align-mode: left + horizon, leading: 0.48em)

  // --- Rung 3: Duon current (E_2^0) ---
  #let y3 = ys.at(2)
  #let c3 = y3 + 0.68
  #aod-box-tl(gx, y3, gw, rh, [], stroke: 0.9pt + aod-pal.purple, fill: white, radius: 3.5pt)
  #aod-circle(gx + 0.72, c3, 0.26, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-text(gx + 0.72, c3, [$D_i$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-circle(gx + 2.24, c3, 0.42, fill: none, stroke: (paint: aod-pal.gold, thickness: 0.95pt, dash: "dashed"))
  #aod-chiral-vertex(gx + 2.24, c3, [$mu_M$], r: 0.27, text-size: 8.8pt)
  #aod-circle(gx + 3.76, c3, 0.26, fill: aod-pal.tint-green, stroke: 0.95pt + aod-pal.teal)
  #aod-text(gx + 3.76, c3, [$D_j$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-wavy-arrow(gx + 1.00, c3, gx + 1.79, c3, amp: 0.055, waves: 2.5, stroke: 1.0pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-wavy-arrow(gx + 2.69, c3, gx + 3.48, c3, amp: 0.055, waves: 2.5, stroke: 1.0pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-text(gx + 2.24, y3 + 1.40, [open seat $E_2^0$], size: 8.6pt, box-w: 2.6, box-h: 0.36)
  #aod-box-tl(dx, y3, dw, rh, [
    #text(size: 8.6pt)[*3. Duon current ($E_2^0$)* — $D_i thin mu_M thin D_j$, $med 2 times 3 times 2 = 12$ variants; carried pivot $mu_M in {-1, 0, +1}$ never omits the structural hinge $0_H$.]
  ], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3.5pt, inset: 5pt, align-mode: left + horizon, leading: 0.48em)

  // --- Rung 4: Seated Duad (E_2^+-) ---
  #let y4 = ys.at(3)
  #let c4 = y4 + 0.68
  #aod-box-tl(gx, y4, gw, rh, [], stroke: 0.95pt + aod-pal.gold, fill: white, radius: 3.5pt)
  #aod-seat-ring(gx + 2.24, c4, 0.44, 2, ring-stroke: 1.25pt + aod-pal.gold, seat-r: 0.068)
  #aod-circle(gx + 0.72, c4, 0.26, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-text(gx + 0.72, c4, [$D_i$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-chiral-vertex(gx + 2.24, c4, [$mu_M$], r: 0.27, text-size: 8.8pt)
  #aod-circle(gx + 3.76, c4, 0.26, fill: aod-pal.tint-green, stroke: 0.95pt + aod-pal.teal)
  #aod-text(gx + 3.76, c4, [$D_j$], size: 8.8pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-wavy-arrow(gx + 1.00, c4, gx + 1.77, c4, amp: 0.055, waves: 2.3, stroke: 1.0pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-wavy-arrow(gx + 2.71, c4, gx + 3.48, c4, amp: 0.055, waves: 2.3, stroke: 1.0pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-text(gx + 2.24, y4 + 1.40, [seated Duad $E_2^(plus.minus)$], size: 8.6pt, box-w: 2.8, box-h: 0.36)
  #aod-box-tl(dx, y4, dw, rh, [
    #text(size: 8.6pt)[*4. Seated Duad ($E_2^(plus.minus)$)* — seat-taken state of the identical Duon current; $op("id")(op("Seat")(u)) = op("id")(u)$, $med sigma_(upright("seat")): upright("open_seat") arrow.r.long.bar upright("seated_duad")$, $0_H$ kept.]
  ], stroke: 0.9pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 3.5pt, inset: 5pt, align-mode: left + horizon, leading: 0.48em)

  // --- Rung 5: Running Duon wave ---
  #let y5 = ys.at(4)
  #aod-box-tl(gx, y5, gw, rh, [], stroke: 0.95pt + aod-pal.blue, fill: white, radius: 3.5pt)
  #let wy5 = y5 + 1.02
  #aod-arrow(gx + 0.24, wy5, gx + 4.26, wy5, stroke: 0.85pt + aod-pal.axis, head-len: 3.6, head-half: 1.7)
  #aod-line(gx + 0.92, wy5, gx + 3.92, wy5, stroke: 1.7pt + aod-pal.blue)
  #aod-marker(gx + 0.92, wy5, kind: "open-circle", r-pt: 2.6, color: aod-pal.blue)
  #aod-marker(gx + 3.92, wy5, kind: "circle", r-pt: 2.6, color: aod-pal.blue)
  #aod-curve-arrow(gx + 0.54, wy5 - 0.05, gx + 1.28, y5 + 0.18, gx + 2.00, wy5 - 0.05, stroke: 1.0pt + aod-pal.blue, head-len: 3.4, head-half: 1.6)
  #aod-curve-arrow(gx + 2.04, wy5 - 0.05, gx + 2.75, y5 + 0.18, gx + 3.46, wy5 - 0.05, stroke: 1.0pt + aod-pal.teal, head-len: 3.4, head-half: 1.6)
  #aod-marker(gx + 0.54, wy5, kind: "circle", r-pt: 2.4, color: aod-pal.gold)
  #aod-marker(gx + 2.02, wy5, kind: "circle", r-pt: 2.4, color: aod-pal.blue)
  #aod-marker(gx + 3.46, wy5, kind: "circle", r-pt: 2.4, color: aod-pal.teal)
  #aod-text(gx + 1.28, y5 + 0.34, [$C_1$], size: 8.6pt, box-w: 0.7, box-h: 0.34)
  #aod-text(gx + 2.75, y5 + 0.34, [$C_2$], size: 8.6pt, box-w: 0.7, box-h: 0.34)
  #aod-text(gx + 2.24, y5 + 1.40, [$omega = (u, v]$], size: 8.6pt, box-w: 2.2, box-h: 0.36)
  #aod-box-tl(dx, y5, dw, rh, [
    #text(size: 8.6pt)[*5. Running Duon wave ($W^(upright("id"))_(B,i)$)* — distinct compatible reclosures and cadence on half-open $omega = (u, v]$ admit wavehood ($Delta op("bip") = +1$).]
  ], stroke: 0.9pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 3.5pt, inset: 5pt, align-mode: left + horizon, leading: 0.48em)

  // --- Bottom Lock-In Strip ---
  #aod-box-tl(
    0.24, 11.06, 14.32, 0.84,
    [#text(size: 8.6pt)[*Strict AOD distinction:* Every temporal realization keeps $0_H$; Dion endpoint adjacency never licenses hinge-free reversal; generic $C_2$ supplies no Duon witness.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
    inset: 5pt,
  )
]
