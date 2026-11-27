// Native Typst vector figure: duon-current-boundary-accounting (Main §5)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.95

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [Duon-current boundary accounting],
    subtitle: [Cross-section across $partial R(t)$: core retention, exoshedding, shell return, pending overhang, and window slices],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Main Cross-Section Stage (y = 1.24 .. 6.72, h = 5.48, x = 0.30 .. 14.70) ---
  #let y0 = 1.24
  #let yh = 5.48
  #let wx = 6.50

  // Interior Region R background
  #place(top + left, dx: 0.30cm, dy: y0 * 1cm, rect(width: (wx - 0.30) * 1cm, height: yh * 1cm, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.navy, radius: (left: 4pt)))
  // Exterior / Shell Region V \ R background
  #place(top + left, dx: wx * 1cm, dy: y0 * 1cm, rect(width: (14.70 - wx) * 1cm, height: yh * 1cm, fill: aod-pal.tint-gray, stroke: 0.85pt + aod-pal.slate, radius: (right: 4pt)))

  // Region Headers
  #aod-text(0.55, y0 + 0.30, [*Interior Region $R$*], size: 8.6pt, anchor: "left", box-w: 3.6, box-h: 0.40)
  #aod-text(14.45, y0 + 0.30, [*Exterior / Shell $V without R$*], size: 8.6pt, anchor: "right", box-w: 4.4, box-h: 0.40)

  // 1. Internal Retained Core (concentric oriented loops around 0_H)
  #let cx-core = 2.05
  #let cy-core = y0 + 2.38
  #aod-arc-arrow(cx-core, cy-core, 0.90, 170, 10, stroke: 1.05pt + aod-pal.navy, head-len: 3.8, head-half: 1.8)
  #aod-arc-arrow(cx-core, cy-core, 0.90, 350, 190, stroke: 1.05pt + aod-pal.navy, head-len: 3.8, head-half: 1.8)
  #aod-arc-arrow(cx-core, cy-core, 0.54, 160, 20, stroke: 1.0pt + aod-pal.blue, head-len: 3.4, head-half: 1.6)
  #aod-arc-arrow(cx-core, cy-core, 0.54, 340, 200, stroke: 1.0pt + aod-pal.blue, head-len: 3.4, head-half: 1.6)
  #aod-chiral-vertex(cx-core, cy-core, [$0_H$], r: 0.27, text-size: 8.8pt)
  #aod-box-tl(0.48, y0 + 3.92, 3.30, 1.32, [
    #text(size: 8.0pt, weight: "bold")[(1) Internal retained] \
    #v(3pt)
    #text(size: 8.6pt)[core burden $J^D_(upright("in"))$]
  ], stroke: 0.85pt + aod-pal.blue, fill: white, radius: 3.5pt, inset: 4pt)

  // 4. Pending Return Dashed Arc inside R
  #aod-curve-arrow(3.92, y0 + 2.98, 4.92, y0 + 3.80, 6.24, y0 + 3.36, stroke: (paint: aod-pal.purple, thickness: 1.1pt, dash: "dashed"), head-len: 4.0, head-half: 1.9)
  #aod-box-tl(3.96, y0 + 3.92, 2.36, 1.32, [
    #text(size: 8.0pt, weight: "bold")[(4) Pending] \
    #v(3pt)
    #text(size: 8.6pt)[$J^D_(upright("pending"))$ over $omega$]
  ], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3.5pt, inset: 4pt)

  // Double-Hatched Retained Boundary Wall partial R(t)
  #aod-boundary-wall(wx, y0 + 0.04, wx, y0 + yh - 0.04, stroke: 1.25pt + aod-pal.navy, hatch-side: -1, hatch-count: 15, hatch-len: 0.13, double-line: true)
  #aod-box(wx, y0 + 0.34, 1.42, 0.44, [#text(size: 8.6pt, weight: "bold")[$partial R(t)$]], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 3pt, inset: 2pt)

  // Moving-Boundary Ghost Wall partial R(t+1)
  #let gx-wall = 7.12
  #aod-line(gx-wall, y0 + 0.68, gx-wall, y0 + yh - 0.22, stroke: (paint: aod-pal.teal, thickness: 0.95pt, dash: "dashed"))
  #aod-arrow(wx + 0.08, y0 + 0.88, gx-wall - 0.02, y0 + 0.88, stroke: 0.9pt + aod-pal.teal, head-len: 3.4, head-half: 1.6)
  #aod-box-tl(7.24, y0 + 0.64, 2.48, 0.50, [#text(size: 8.6pt)[sweep $Phi^D_(upright("sweep"))$]], stroke: 0.75pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 3pt, inset: 2pt)

  // Outer C_6 Seat-Ring Shell in Exterior
  #let sx-shell = 9.48
  #let sy-shell = y0 + 2.34
  #aod-circle(sx-shell, sy-shell, 0.34, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-seat-ring(sx-shell, sy-shell, 0.68, 6, ring-stroke: 1.25pt + aod-pal.gold, seat-r: 0.068)
  #aod-text(sx-shell, sy-shell, [$sans("C")_6$], size: 8.8pt, weight: "bold", box-w: 0.8, box-h: 0.44)
  #aod-text(sx-shell, sy-shell + 0.98, [outer shell $sans("C")_6$], size: 8.6pt, box-w: 2.4, box-h: 0.38)

  // 2. Exoshedding Wavy Orange Arrow crossing partial R(t) into C_6 shell
  #aod-wavy-arrow(3.04, y0 + 2.08, sx-shell - 0.76, y0 + 2.08, amp: 0.072, waves: 5.5, stroke: 1.25pt + aod-pal.orange, head-len: 4.5, head-half: 2.1)
  #aod-box-tl(3.46, y0 + 0.72, 2.86, 1.12, [
    #text(size: 8.0pt, weight: "bold")[(2) Exoshedding] \
    #v(3pt)
    #text(size: 8.6pt)[crosses $partial R$ ($J^D_(upright("out"))$)]
  ], stroke: 0.85pt + aod-pal.orange, fill: aod-pal.tint-orange, radius: 3.5pt, inset: 4pt)

  // 3. Reflected Return Curved Green Arrow from C_6 shell back into R
  #aod-curve-arrow(sx-shell - 0.62, y0 + 2.80, 6.10, y0 + 3.30, 3.04, y0 + 2.72, stroke: 1.2pt + aod-pal.green, head-len: 4.4, head-half: 2.0)
  #aod-box-tl(7.30, y0 + 3.92, 3.68, 1.32, [
    #text(size: 8.0pt, weight: "bold")[(3) Reflected return] \
    #v(3pt)
    #text(size: 7.5pt)[re-enters $R$ via shell; \ feeds next emission]
  ], stroke: 0.85pt + aod-pal.green, fill: aod-pal.tint-green, radius: 3.5pt, inset: 4pt, leading: 0.45em)

  // Stacked Window Slice Frames (t_1 .. t_m in omega) on Far Right (clean staggered labels)
  #let fx0 = 11.42
  #aod-text(13.02, y0 + 0.86, [*Window slices $t in omega$*], size: 8.0pt, box-w: 3.1, box-h: 0.38)
  #for (idx, lbl) in ((0, [$t_1$]), (1, [$t_2$]), (2, [$t_m$])) {
    let bx = fx0 + idx * 0.34
    let by = y0 + 1.18 + idx * 0.86
    aod-box-tl(bx, by, 2.34, 1.04, [], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 3pt)
    aod-line(bx + 0.90, by + 0.14, bx + 0.90, by + 0.90, stroke: 0.9pt + aod-pal.navy)
    aod-arrow(bx + 0.38, by + 0.38, bx + 1.42, by + 0.38, stroke: 0.9pt + aod-pal.orange, head-len: 3.2, head-half: 1.5)
    aod-arrow(bx + 1.42, by + 0.68, bx + 0.38, by + 0.68, stroke: 0.9pt + aod-pal.green, head-len: 3.2, head-half: 1.5)
    aod-text(bx + 1.92, by + 0.32, lbl, size: 8.6pt, weight: "bold", box-w: 0.68, box-h: 0.38)
  }
  #aod-text(13.02, y0 + 4.62, [sum slice fluxes \ across $omega = (u, v]$], size: 8.6pt, box-w: 3.1, box-h: 0.80)

  // --- Bottom Accounting Formula Band (2x2 Grid, y = 6.96 .. 9.70) ---
  #let fy1 = 6.96
  #let fy2 = 8.40
  #let fh = 1.28

  #aod-box-tl(0.30, fy1, 7.05, fh, [
    #text(size: 8.6pt, weight: "bold")[Slice flux ($B bar.v_t = (partial F, {t})$)] \
    #v(2pt)
    #text(size: 8.8pt)[$Phi^D_(partial R)(t; B bar.v_t) = sum_(e in partial R(t)) phi.alt_e (B bar.v_t)$]
  ], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 3.5pt, inset: 4pt)

  #aod-box-tl(7.65, fy1, 7.05, fh, [
    #text(size: 8.6pt, weight: "bold")[Window duon current ($omega$)] \
    #v(2pt)
    #text(size: 8.8pt)[$J^D_(partial R)(omega; B) = sum_(t in omega) Phi^D_(partial R)(t; B bar.v_t)$]
  ], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 3.5pt, inset: 4pt)

  #aod-box-tl(0.30, fy2, 7.05, fh, [
    #text(size: 8.6pt, weight: "bold")[Declared magnitude partition] \
    #v(2pt)
    #text(size: 8.8pt)[$J^D_(upright("mag")) = J^D_(upright("in")) + J^D_(upright("out")) + J^D_(upright("pending"))$]
  ], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3.5pt, inset: 4pt)

  #aod-box-tl(7.65, fy2, 7.05, fh, [
    #text(size: 8.6pt, weight: "bold")[Moving retained boundary law] \
    #v(2pt)
    #text(size: 8.7pt)[$Phi^D_(partial R, upright("mov"))(t) = Phi^D_(upright("cross"))(t) - Phi^D_(upright("sweep"))(t) + Phi^D_(upright("shedding"))(t)$]
  ], stroke: 0.85pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 3.5pt, inset: 4pt)
]
