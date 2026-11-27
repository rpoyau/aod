// Native Typst vector figure: fractal-calculus-spine (Main §5)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.95

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [Fractal-cycle calculus spine],
    subtitle: [Geometric witnesses (left) bound to the six-step finite derivation from distinction to boundary flux],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Left Column: 3 Geometric Witness Panels (x = 0.30 .. 6.26, w = 5.96) ---
  #let lx = 0.30
  #let lw = 5.96
  #let rx = 7.04
  #let rw = 7.66

  // Witness A (paired with Steps 1 & 2): y = 1.24 .. 3.60 (h = 2.36)
  #aod-box-tl(lx, 1.24, lw, 2.36, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 4pt)
  #aod-text(lx + 1.44, 1.50, [*Distinction*], size: 8.2pt, box-w: 2.6, box-h: 0.36)
  #aod-circle(lx + 1.44, 2.46, 0.68, fill: none, stroke: 0.75pt + aod-pal.sky)
  #aod-circle(lx + 1.44, 2.46, 0.46, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-chiral-vertex(lx + 1.44, 2.46, [$x$], r: 0.23, fill: white, stroke: 1.05pt + aod-pal.navy, text-size: 9.0pt)
  #aod-text(lx + 1.44, 3.36, [$x succ x = x, med 0_H$], size: 8.6pt, box-w: 2.6, box-h: 0.36)
  #aod-arrow(lx + 2.24, 2.46, lx + 2.94, 2.46, stroke: 0.95pt + aod-pal.slate, head-len: 3.6, head-half: 1.7)
  // True 16-vertex Q4 hypercube
  #aod-text(lx + 4.46, 1.50, [*16-vertex $Q_4$*], size: 8.6pt, box-w: 2.8, box-h: 0.36)
  #aod-tesseract-q4(lx + 4.46, 2.52, scale: 0.58, highlight-vertex: 0)
  #aod-text(lx + 4.46, 3.36, [$|V|=16, med deg=4$], size: 8.0pt, box-w: 2.6, box-h: 0.36)

  // Witness B (paired with Steps 3 & 4): y = 3.84 .. 6.20 (h = 2.36)
  #aod-box-tl(lx, 3.84, lw, 2.36, [], stroke: 0.9pt + aod-pal.teal, fill: white, radius: 4pt)
  #aod-text(lx + 1.42, 4.10, [*Nested* $C_f [Sigma]$], size: 8.6pt, box-w: 2.6, box-h: 0.38)
  #let bcx = lx + 1.42
  #let bcy = 5.14
  #aod-arc-arrow(bcx, bcy, 0.74, 165, 15, stroke: 1.05pt + aod-pal.navy, head-len: 3.6, head-half: 1.7)
  #aod-arc-arrow(bcx, bcy, 0.74, 345, 195, stroke: 1.05pt + aod-pal.navy, head-len: 3.6, head-half: 1.7)
  #aod-arc-arrow(bcx, bcy, 0.48, 155, 25, stroke: 0.95pt + aod-pal.teal, head-len: 3.2, head-half: 1.5)
  #aod-chiral-vertex(bcx, bcy, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-arrow(lx + 2.26, 5.14, lx + 2.74, 5.14, stroke: 0.95pt + aod-pal.slate, head-len: 3.4, head-half: 1.6)
  // Triad Pi_alpha -> H_mu -> Pi_Omega
  #aod-text(lx + 4.38, 4.10, [*Hinge Triad* $sans("AO")_mu$], size: 8.6pt, box-w: 2.9, box-h: 0.38)
  #aod-circle(lx + 3.16, 5.04, 0.27, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-text(lx + 3.16, 5.04, [$Pi_alpha$], size: 8.6pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-chiral-vertex(lx + 4.36, 5.04, [$H_mu$], r: 0.27, text-size: 8.6pt)
  #aod-circle(lx + 5.56, 5.04, 0.27, fill: aod-pal.tint-orange, stroke: 0.95pt + aod-pal.orange)
  #aod-text(lx + 5.56, 5.04, [$Pi_Omega$], size: 8.6pt, weight: "bold", box-w: 0.6, box-h: 0.42)
  #aod-arrow(lx + 3.45, 5.04, lx + 4.07, 5.04, stroke: 0.95pt + aod-pal.blue, head-len: 3.2, head-half: 1.5)
  #aod-arrow(lx + 4.65, 5.04, lx + 5.27, 5.04, stroke: 0.95pt + aod-pal.orange, head-len: 3.2, head-half: 1.5)
  #aod-curve-arrow(lx + 5.56, 5.34, lx + 4.36, 6.02, lx + 3.16, 5.34, stroke: 0.9pt + aod-pal.teal, head-len: 3.4, head-half: 1.6)

  // Witness C (paired with Steps 5 & 6): y = 6.44 .. 8.80 (h = 2.36)
  #aod-box-tl(lx, 6.44, lw, 2.36, [], stroke: 0.9pt + aod-pal.purple, fill: white, radius: 4pt)
  #aod-text(lx + 2.98, 6.70, [*Hatched Boundary Cut $partial_T R$ & Flux*], size: 8.6pt, box-w: 5.6, box-h: 0.38)
  #place(top + left, dx: (lx + 0.26) * 1cm, dy: 6.98cm, rect(width: 2.52cm, height: 1.38cm, fill: aod-pal.tint-blue, stroke: none))
  #place(top + left, dx: (lx + 2.78) * 1cm, dy: 6.98cm, rect(width: 2.92cm, height: 1.38cm, fill: aod-pal.tint-gray, stroke: none))
  #aod-boundary-wall(lx + 2.78, 6.96, lx + 2.78, 8.38, stroke: 1.1pt + aod-pal.navy, hatch-side: -1, hatch-count: 7, hatch-len: 0.11, double-line: true)
  #aod-text(lx + 0.85, 7.22, [*$R$*], size: 8.8pt, box-w: 0.6, box-h: 0.38)
  #aod-text(lx + 4.95, 7.22, [$V without R$], size: 8.4pt, box-w: 1.4, box-h: 0.38)
  #aod-arrow(lx + 1.35, 7.30, lx + 4.05, 7.30, stroke: 1.05pt + aod-pal.blue, head-len: 3.8, head-half: 1.8)
  #aod-wavy-arrow(lx + 1.35, 7.72, lx + 4.05, 7.72, amp: 0.052, waves: 3.5, stroke: 1.05pt + aod-pal.orange, head-len: 3.8, head-half: 1.8)
  #aod-arrow(lx + 4.05, 8.12, lx + 1.35, 8.12, stroke: 1.05pt + aod-pal.green, head-len: 3.8, head-half: 1.8)
  #aod-text(lx + 4.92, 7.72, [$frak(S)_B (C_e)$], size: 8.8pt, weight: "bold", box-w: 1.5, box-h: 0.44)
  #aod-text(lx + 2.78, 8.56, [$partial_T R$], size: 8.6pt, box-w: 1.2, box-h: 0.36)

  // --- Right Column: 6 Numbered Derivation Cards (x = 7.04 .. 14.70, w = 7.66) ---
  #let steps = (
    (1.24, "1", [*Declared distinction*], [$x succ x = x$ with retained hinge $0_H$ & trace], aod-pal.navy, aod-pal.tint-gray),
    (2.54, "2", [*Declared scope*], [$B = (partial_T F, omega)$ on finite $Q_4$ support], aod-pal.blue, aod-pal.tint-blue),
    (3.84, "3", [*Certified closure / recurrence*], [$C_f [Sigma]_(A arrow.l.r Omega)$ (outer trace + certificate)], aod-pal.teal, aod-pal.tint-green),
    (5.14, "4", [*Alpha–Omega kernel* $sans("AO")_mu (C)$], [$sans("AO")_mu (C) = chevron.l Pi_alpha, H_mu, Pi_Omega chevron.r$], aod-pal.gold, aod-pal.tint-amber),
    (6.44, "5", [*SADAR value operator*], [$frak(S)_B (C) = p^D A$ (magnitude $times$ direction)], aod-pal.purple, aod-pal.tint-purple),
    (7.74, "6", [*Boundary accumulation*], [$Phi^D_(partial_#text(size: 12.2pt)[$T$] R) = sum_(e in partial_#text(size: 12.2pt)[$T$] R) frak(S)_B (C_e)$], aod-pal.navy, aod-pal.tint-blue),
  )

  #for idx in range(steps.len()) {
    let (sy, num, hdr, body, st, fl) = steps.at(idx)
    let scy = sy + 0.53
    aod-box-tl(rx, sy, rw, 1.06, [], stroke: 0.9pt + st, fill: fl, radius: 3.5pt)
    aod-circle(rx + 0.36, scy, 0.20, fill: white, stroke: 0.9pt + st)
    aod-text(rx + 0.36, scy, [*#num*], size: 7.6pt, box-w: 0.45, box-h: 0.45)
    aod-text(rx + 0.72, sy + 0.30, hdr, size: 8.6pt, anchor: "left", box-w: 6.75, box-h: 0.38)
    let bsz = if idx == 5 { 9.0pt } else { 8.6pt }
    aod-text(rx + 0.72, sy + 0.75, body, size: bsz, anchor: "left", box-w: 6.75, box-h: 0.44)
    // Witness connector arrow from left column to each card
    aod-arrow(lx + lw + 0.06, scy, rx - 0.05, scy, stroke: 0.9pt + aod-pal.slate, head-len: 3.6, head-half: 1.7)
    // Downward derivation arrow between cards
    if idx < steps.len() - 1 {
      aod-arrow(rx + rw / 2, sy + 1.07, rx + rw / 2, sy + 1.29, stroke: 1.0pt + aod-pal.navy, head-len: 3.6, head-half: 1.7)
    }
  }

  // --- Bottom Lock-In Strip ---
  #aod-box-tl(
    0.30, 8.98, 14.40, 0.80,
    [#text(size: 8.6pt)[*Finite calculus discipline:* Exact finite boundary accumulation on $B$; no continuous integration, no skipped closure certificate, $0_H$ preserved throughout.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
    inset: 5pt,
  )
]
