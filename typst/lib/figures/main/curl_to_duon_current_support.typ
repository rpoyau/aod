// Native Typst vector figure: curl-to-duon-current-support (Main §3)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 9.15

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [Curl-to-duon-current support chain],
    subtitle: [Oriented branch–hinge–return closure through $0_H$ builds dions, duon currents, waves, and scoped fields],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Row 1: Panels 1, 2, 3 (y = 1.24 .. 4.18, h = 2.94) ---
  #let r1-y = 1.24
  #let r1-h = 2.94
  #let pw = 4.45
  #let x1 = 0.24
  #let x2 = 5.17
  #let x3 = 10.10

  // Panel 1: Branch-Hinge-Return
  #aod-box-tl(x1, r1-y, pw, r1-h, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 4pt)
  #aod-circle(x1 + 0.34, r1-y + 0.30, 0.18, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.navy)
  #aod-text(x1 + 0.34, r1-y + 0.30, [*1*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(x1 + 0.62, r1-y + 0.30, [*Branch–Hinge–Return*], size: 8.0pt, anchor: "left", box-w: 3.7, box-h: 0.42)

  // Dwell dashed loop above 0_H
  #aod-arc-arrow(x1 + 2.225, r1-y + 1.22, 0.22, -25, 215, stroke: (paint: aod-pal.slate, thickness: 0.8pt, dash: "dashed"), head-len: 3.2, head-half: 1.5)
  #aod-text(x1 + 2.225, r1-y + 0.78, [$(0_D)^m$], size: 8.6pt, box-w: 1.5, box-h: 0.38)
  // Nodes +1 -> 0_H -> -1
  #aod-circle(x1 + 0.82, r1-y + 1.62, 0.28, fill: aod-pal.tint-blue, stroke: 1.0pt + aod-pal.blue)
  #aod-text(x1 + 0.82, r1-y + 1.62, [$+1$], size: 8.6pt, weight: "bold", box-w: 0.7, box-h: 0.45)
  #aod-chiral-vertex(x1 + 2.225, r1-y + 1.62, [$0_H$], r: 0.29, text-size: 8.8pt)
  #aod-circle(x1 + 3.63, r1-y + 1.62, 0.28, fill: aod-pal.tint-orange, stroke: 1.0pt + aod-pal.orange)
  #aod-text(x1 + 3.63, r1-y + 1.62, [$-1$], size: 8.6pt, weight: "bold", box-w: 0.7, box-h: 0.45)
  #aod-arrow(x1 + 1.12, r1-y + 1.62, x1 + 1.91, r1-y + 1.62, stroke: 1.0pt + aod-pal.blue, head-len: 4.0, head-half: 1.9)
  #aod-arrow(x1 + 2.54, r1-y + 1.62, x1 + 3.33, r1-y + 1.62, stroke: 1.0pt + aod-pal.orange, head-len: 4.0, head-half: 1.9)
  #aod-text(x1 + 2.225, r1-y + 2.28, [$epsilon.alt thin 0_H thin (0_D)^m thin (-epsilon.alt)$], size: 8.8pt, box-w: 4.1, box-h: 0.44)
  #aod-text(x1 + 2.225, r1-y + 2.66, [mandatory $0_H$ retained], size: 8.6pt, box-w: 4.1, box-h: 0.40)

  // Inter-panel arrow 1 -> 2
  #aod-arrow(x1 + pw + 0.05, r1-y + r1-h / 2, x2 - 0.05, r1-y + r1-h / 2, stroke: 1.1pt + aod-pal.navy)

  // Panel 2: Oriented Curl
  #aod-box-tl(x2, r1-y, pw, r1-h, [], stroke: 0.9pt + aod-pal.blue, fill: white, radius: 4pt)
  #aod-circle(x2 + 0.34, r1-y + 0.30, 0.18, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.blue)
  #aod-text(x2 + 0.34, r1-y + 0.30, [*2*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(x2 + 0.62, r1-y + 0.30, [*Oriented Curl*], size: 8.0pt, anchor: "left", box-w: 3.6, box-h: 0.42)

  #let cx2 = x2 + pw / 2
  #let cy2 = r1-y + 1.46
  #aod-arc-arrow(cx2, cy2, 0.58, 215, 40, stroke: 1.15pt + aod-pal.blue, head-len: 4.0, head-half: 1.9)
  #aod-arc-arrow(cx2, cy2, 0.58, 20, -135, stroke: 1.15pt + aod-pal.teal, head-len: 4.0, head-half: 1.9)
  #aod-chiral-vertex(cx2, cy2, [$0_H$], r: 0.27, text-size: 8.8pt)
  #aod-text(cx2 - 1.05, cy2 - 0.12, [$Pi^-$], size: 8.8pt, box-w: 0.9, box-h: 0.45)
  #aod-text(cx2 + 1.08, cy2 + 0.10, [$Pi^+$], size: 8.8pt, box-w: 0.9, box-h: 0.45)
  #aod-text(cx2, r1-y + 2.34, [$R D_gamma = Pi^- + H_mu + Pi^+$], size: 8.7pt, box-w: 4.2, box-h: 0.45)
  #aod-text(cx2, r1-y + 2.68, [returned closure through hinge], size: 7.5pt, box-w: 4.2, box-h: 0.36)

  // Inter-panel arrow 2 -> 3
  #aod-arrow(x2 + pw + 0.05, r1-y + r1-h / 2, x3 - 0.05, r1-y + r1-h / 2, stroke: 1.1pt + aod-pal.navy)

  // Panel 3: Dion Dipole Pair
  #aod-box-tl(x3, r1-y, pw, r1-h, [], stroke: 0.9pt + aod-pal.teal, fill: white, radius: 4pt)
  #aod-circle(x3 + 0.34, r1-y + 0.30, 0.18, fill: aod-pal.tint-green, stroke: 0.85pt + aod-pal.teal)
  #aod-text(x3 + 0.34, r1-y + 0.30, [*3*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(x3 + 0.62, r1-y + 0.30, [*Dion Dipole Pair*], size: 8.0pt, anchor: "left", box-w: 3.6, box-h: 0.42)

  // Row A: D_alpha = (+1, -1)
  #let ya3 = r1-y + 0.99
  #aod-text(x3 + 0.40, ya3, [$D_alpha$], size: 8.8pt, weight: "bold", box-w: 0.7, box-h: 0.42)
  #aod-circle(x3 + 1.09, ya3, 0.21, fill: aod-pal.tint-blue, stroke: 0.9pt + aod-pal.blue)
  #aod-text(x3 + 1.09, ya3, [$+1$], size: 7.6pt, weight: "bold", box-w: 0.5, box-h: 0.38)
  #aod-chiral-vertex(x3 + 1.98, ya3, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-circle(x3 + 2.87, ya3, 0.21, fill: aod-pal.tint-orange, stroke: 0.9pt + aod-pal.orange)
  #aod-text(x3 + 2.87, ya3, [$-1$], size: 7.6pt, weight: "bold", box-w: 0.5, box-h: 0.38)
  #aod-arrow(x3 + 1.33, ya3, x3 + 1.67, ya3, stroke: 0.85pt + aod-pal.blue, head-len: 3.0, head-half: 1.4)
  #aod-arrow(x3 + 2.29, ya3, x3 + 2.63, ya3, stroke: 0.85pt + aod-pal.orange, head-len: 3.0, head-half: 1.4)
  #aod-text(x3 + 3.78, ya3, [$(+1,-1)$], size: 8.0pt, box-w: 1.24, box-h: 0.42)

  // Row B: D_Omega = (-1, +1)
  #let yb3 = r1-y + 1.79
  #aod-text(x3 + 0.40, yb3, [$D_Omega$], size: 8.8pt, weight: "bold", box-w: 0.7, box-h: 0.42)
  #aod-circle(x3 + 1.09, yb3, 0.21, fill: aod-pal.tint-orange, stroke: 0.9pt + aod-pal.orange)
  #aod-text(x3 + 1.09, yb3, [$-1$], size: 7.6pt, weight: "bold", box-w: 0.5, box-h: 0.38)
  #aod-chiral-vertex(x3 + 1.98, yb3, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-circle(x3 + 2.87, yb3, 0.21, fill: aod-pal.tint-blue, stroke: 0.9pt + aod-pal.blue)
  #aod-text(x3 + 2.87, yb3, [$+1$], size: 7.6pt, weight: "bold", box-w: 0.5, box-h: 0.38)
  #aod-arrow(x3 + 1.33, yb3, x3 + 1.67, yb3, stroke: 0.85pt + aod-pal.orange, head-len: 3.0, head-half: 1.4)
  #aod-arrow(x3 + 2.29, yb3, x3 + 2.63, yb3, stroke: 0.85pt + aod-pal.blue, head-len: 3.0, head-half: 1.4)
  #aod-text(x3 + 3.78, yb3, [$(-1,+1)$], size: 8.0pt, box-w: 1.24, box-h: 0.42)

  #aod-box-tl(x3 + 0.24, r1-y + 2.28, pw - 0.48, 0.48, [#text(size: 8.2pt, weight: "bold")[Dion $eq.not$ Dimonon]], stroke: 0.75pt + aod-pal.crimson, fill: aod-pal.tint-orange, radius: 3pt, inset: 2pt)

  // --- Stepped Inter-Row Connector (Panel 3 -> Panel 4) ---
  #let y-mid = 4.54
  #aod-line(x3 + pw / 2, r1-y + r1-h, x3 + pw / 2, y-mid, stroke: 1.05pt + aod-pal.navy)
  #aod-line(x3 + pw / 2, y-mid, x1 + pw / 2, y-mid, stroke: 1.05pt + aod-pal.navy)
  #aod-arrow(x1 + pw / 2, y-mid, x1 + pw / 2, 4.90, stroke: 1.05pt + aod-pal.navy)
  #aod-box(7.40, y-mid, 6.40, 0.46, [#text(size: 8.2pt)[*pivot assembly:* $2 times 3 times 2 = 12$ variants]], stroke: 0.85pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 4pt, inset: 2pt)

  // --- Row 2: Panels 4, 5, 6 (y = 4.94 .. 7.88, h = 2.94) ---
  #let r2-y = 4.94
  #let r2-h = 2.94

  // Panel 4: Duon Current
  #aod-box-tl(x1, r2-y, pw, r2-h, [], stroke: 0.9pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-circle(x1 + 0.34, r2-y + 0.30, 0.18, fill: white, stroke: 0.85pt + aod-pal.purple)
  #aod-text(x1 + 0.34, r2-y + 0.30, [*4*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(x1 + 0.62, r2-y + 0.30, [*Duon Current ($E_2^0$)*], size: 8.6pt, anchor: "left", box-w: 3.7, box-h: 0.44)

  #let cy4 = r2-y + 1.26
  #aod-circle(x1 + 0.72, cy4, 0.30, fill: aod-pal.tint-blue, stroke: 1.0pt + aod-pal.blue)
  #aod-text(x1 + 0.72, cy4, [$D_i$], size: 8.8pt, weight: "bold", box-w: 0.7, box-h: 0.45)
  #aod-circle(x1 + 2.225, cy4, 0.43, fill: none, stroke: (paint: aod-pal.gold, thickness: 0.9pt, dash: "dashed"))
  #aod-chiral-vertex(x1 + 2.225, cy4, [$mu_M$], r: 0.28, text-size: 8.8pt)
  #aod-circle(x1 + 3.73, cy4, 0.30, fill: aod-pal.tint-green, stroke: 1.0pt + aod-pal.teal)
  #aod-text(x1 + 3.73, cy4, [$D_j$], size: 8.8pt, weight: "bold", box-w: 0.7, box-h: 0.45)
  #aod-wavy-arrow(x1 + 1.04, cy4, x1 + 1.77, cy4, amp: 0.055, waves: 2.5, stroke: 1.05pt + aod-pal.purple, head-len: 3.6, head-half: 1.7)
  #aod-wavy-arrow(x1 + 2.68, cy4, x1 + 3.41, cy4, amp: 0.055, waves: 2.5, stroke: 1.05pt + aod-pal.purple, head-len: 3.6, head-half: 1.7)
  #aod-text(x1 + 2.225, r2-y + 2.10, [$D_i thin mu_M thin D_j$, $med mu_M in {-1, 0, +1}$], size: 8.6pt, box-w: 4.2, box-h: 0.44)
  #aod-text(x1 + 2.225, r2-y + 2.58, [open $E_2^0$ vs seated Duad $E_2^(plus.minus)$], size: 8.6pt, box-w: 4.2, box-h: 0.44)

  // Inter-panel arrow 4 -> 5
  #aod-arrow(x1 + pw + 0.05, r2-y + r2-h / 2, x2 - 0.05, r2-y + r2-h / 2, stroke: 1.1pt + aod-pal.navy)

  // Panel 5: Admitted Wave & Cadence
  #aod-box-tl(x2, r2-y, pw, r2-h, [], stroke: 0.9pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-circle(x2 + 0.34, r2-y + 0.30, 0.18, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.navy)
  #aod-text(x2 + 0.34, r2-y + 0.30, [*5*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(x2 + 0.62, r2-y + 0.30, [*Admitted Wave & Cadence*], size: 7.6pt, anchor: "left", box-w: 3.75, box-h: 0.42)

  #let ay5 = r2-y + 1.66
  #aod-arrow(x2 + 0.28, ay5, x2 + 4.18, ay5, stroke: 0.85pt + aod-pal.axis, head-len: 3.8, head-half: 1.8)
  #aod-line(x2 + 1.06, ay5, x2 + 3.80, ay5, stroke: 1.8pt + aod-pal.blue)
  #aod-marker(x2 + 1.06, ay5, kind: "open-circle", r-pt: 2.7, color: aod-pal.blue)
  #aod-marker(x2 + 3.80, ay5, kind: "circle", r-pt: 2.7, color: aod-pal.blue)
  #let k0x = x2 + 0.64
  #let k1x = x2 + 2.02
  #let k2x = x2 + 3.40
  #aod-curve-arrow(k0x, ay5 - 0.06, (k0x + k1x) / 2, r2-y + 0.70, k1x - 0.04, ay5 - 0.06, stroke: 1.05pt + aod-pal.blue, head-len: 3.6, head-half: 1.7)
  #aod-curve-arrow(k1x + 0.04, ay5 - 0.06, (k1x + k2x) / 2, r2-y + 0.70, k2x - 0.04, ay5 - 0.06, stroke: 1.05pt + aod-pal.teal, head-len: 3.6, head-half: 1.7)
  #aod-marker(k0x, ay5, kind: "circle", r-pt: 2.6, color: aod-pal.gold)
  #aod-marker(k1x, ay5, kind: "circle", r-pt: 2.6, color: aod-pal.blue)
  #aod-marker(k2x, ay5, kind: "circle", r-pt: 2.6, color: aod-pal.teal)
  #aod-text(k0x - 0.04, r2-y + 0.90, [$C_0$], size: 8.6pt, box-w: 0.7, box-h: 0.38)
  #aod-text((k0x + k1x) / 2, r2-y + 0.86, [$C_1$], size: 8.6pt, box-w: 0.7, box-h: 0.38)
  #aod-text((k1x + k2x) / 2, r2-y + 0.86, [$C_2$], size: 8.6pt, box-w: 0.7, box-h: 0.38)
  #aod-text(k0x, ay5 + 0.34, [$k_0$], size: 8.6pt, box-w: 0.7, box-h: 0.38)
  #aod-text(k1x, ay5 + 0.34, [$k_1$], size: 8.6pt, box-w: 0.7, box-h: 0.38)
  #aod-text(k2x, ay5 + 0.34, [$k_2$], size: 8.6pt, box-w: 0.7, box-h: 0.38)
  #aod-text(x2 + pw / 2, r2-y + 2.54, [$W^(upright("id"))_(B,i)$ on $omega = (u, v]$], size: 8.8pt, box-w: 4.2, box-h: 0.45)

  // Inter-panel arrow 5 -> 6
  #aod-arrow(x2 + pw + 0.05, r2-y + r2-h / 2, x3 - 0.05, r2-y + r2-h / 2, stroke: 1.1pt + aod-pal.navy)

  // Panel 6: Scoped Field Organization
  #aod-box-tl(x3, r2-y, pw, r2-h, [], stroke: 0.9pt + aod-pal.green, fill: aod-pal.tint-green, radius: 4pt)
  #aod-circle(x3 + 0.34, r2-y + 0.30, 0.18, fill: white, stroke: 0.85pt + aod-pal.green)
  #aod-text(x3 + 0.34, r2-y + 0.30, [*6*], size: 7.4pt, box-w: 0.4, box-h: 0.4)
  #aod-text(x3 + 0.62, r2-y + 0.30, [*Scoped Field Organization*], size: 7.6pt, anchor: "left", box-w: 3.75, box-h: 0.42)

  #let wl6 = x3 + 0.60
  #let wr6 = x3 + 3.85
  #let wt6 = r2-y + 0.70
  #let wb6 = r2-y + 2.04
  #aod-boundary-wall(wl6, wt6, wl6, wb6, stroke: 1.05pt + aod-pal.navy, hatch-side: 1, hatch-count: 6, hatch-len: 0.11)
  #aod-boundary-wall(wr6, wt6, wr6, wb6, stroke: 1.05pt + aod-pal.navy, hatch-side: -1, hatch-count: 6, hatch-len: 0.11)
  #aod-line(wl6, wt6, wr6, wt6, stroke: (paint: aod-pal.navy, thickness: 0.75pt, dash: "dashed"))
  #aod-line(wl6, wb6, wr6, wb6, stroke: (paint: aod-pal.navy, thickness: 0.75pt, dash: "dashed"))
  #let cy6 = (wt6 + wb6) / 2
  #aod-circle(x3 + 1.44, cy6, 0.34, fill: aod-pal.tint-blue, stroke: 1.0pt + aod-pal.blue)
  #aod-text(x3 + 1.44, cy6, [$W_1$], size: 8.8pt, weight: "bold", box-w: 0.7, box-h: 0.45)
  #aod-circle(x3 + 3.01, cy6, 0.34, fill: aod-pal.tint-purple, stroke: 1.0pt + aod-pal.purple)
  #aod-text(x3 + 3.01, cy6, [$W_2$], size: 8.8pt, weight: "bold", box-w: 0.7, box-h: 0.45)
  #aod-curve-arrow(x3 + 1.76, cy6 - 0.16, x3 + 2.225, cy6 - 0.50, x3 + 2.68, cy6 - 0.16, stroke: 0.95pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-curve-arrow(x3 + 2.68, cy6 + 0.16, x3 + 2.225, cy6 + 0.50, x3 + 1.76, cy6 + 0.16, stroke: 0.95pt + aod-pal.purple, head-len: 3.4, head-half: 1.6)
  #aod-text(x3 + pw / 2, r2-y + 2.54, [$F_(B, lambda)$, $med B = (partial_T F, omega)$], size: 8.8pt, box-w: 4.2, box-h: 0.45)

  // --- Bottom Invariant Bar ---
  #aod-box-tl(
    0.24, 8.12, 14.32, 0.84,
    [#text(size: 8.6pt)[*Retained invariant:* Structural hinge $0_H$ and lineage persist across every stage; $op("id")(op("Seat")(u)) = op("id")(u)$; no scalar count replaces construction witness.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
    inset: 5pt,
  )
]
