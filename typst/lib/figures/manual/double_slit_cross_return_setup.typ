// Audited S1b native Typst vector figure: double-slit-cross-return-setup (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_manual_figures.py)
// Historical raster retained byte-for-byte: manual/figures/double_slit_cross_return_setup.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 8.4

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Outer frame & title
  #aod-box-tl(0.16, 0.16, 14.48, 8.08, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.40, 0.56, [*Recurrent-ring Dimonhexon double-slit setup & cross-return paths*], size: 10.6pt, box-w: 14.0, box-h: 0.50)
  #aod-text(7.40, 0.96, [Scope $B_(upright("ring")) = (partial_T F_(upright("ring")), omega_(upright("ring")))$: $1":"2":"6$ closure $->$ ring gates $g_a, g_b$ $->$ 11-bin screen $k in \{-5, dots, +5\}$.], size: 7.5pt, box-w: 14.0, box-h: 0.42)

  // Left: Recurrent C6 ring source (V_6, E_6)
  #let rcx = 2.15
  #let rcy = 4.35
  #aod-seat-ring(rcx, rcy, 1.25, 6, ring-stroke: 1.2pt + aod-pal.navy, seat-r: 0.095, seat-fill: aod-pal.tint-blue, seat-stroke: 0.85pt + aod-pal.navy)
  #aod-arc-arrow(rcx, rcy, 0.68, 40, 315, stroke: 0.95pt + aod-pal.blue)
  #aod-text(rcx, rcy, [$1":"2":"6$ \ $(V_6, E_6)$], size: 7.4pt, weight: "bold", box-w: 1.5, box-h: 0.85)
  #aod-text(rcx, 6.02, [retained hexon \ closure source], size: 7.2pt, box-w: 2.8, box-h: 0.65)

  // Center-left: Slit barrier wall partial_T R_ring with two open apertures g_a and g_b
  #let wx = 4.85
  #aod-boundary-wall(wx, 1.62, wx, 2.58, stroke: 1.4pt + aod-pal.navy, hatch-side: -1, hatch-count: 4)
  #aod-boundary-wall(wx, 3.45, wx, 5.25, stroke: 1.4pt + aod-pal.navy, hatch-side: -1, hatch-count: 6)
  #aod-boundary-wall(wx, 6.12, wx, 7.18, stroke: 1.4pt + aod-pal.navy, hatch-side: -1, hatch-count: 4)
  #aod-text(wx, 1.38, [$partial_T R_(upright("ring"))$], size: 7.6pt, weight: "bold", box-w: 2.2, box-h: 0.34)

  // Gate badges g_a (y=3.00) and g_b (y=5.70)
  #aod-chiral-vertex(wx, 3.00, [$g_a$], r: 0.28, fill: aod-pal.tint-green, stroke: 1.05pt + aod-pal.teal, text-size: 7.8pt)
  #aod-chiral-vertex(wx, 5.70, [$g_b$], r: 0.28, fill: aod-pal.tint-green, stroke: 1.05pt + aod-pal.teal, text-size: 7.8pt)

  // Incident handoff from C6 ring to gates g_a, g_b
  #aod-arrow(3.32, 3.78, 4.52, 3.08, stroke: 1.0pt + aod-pal.navy)
  #aod-arrow(3.32, 4.92, 4.52, 5.62, stroke: 1.0pt + aod-pal.navy)

  // Cross-return returned-current channel g_a <-> g_b
  #aod-wavy-arrow(5.12, 3.24, 5.12, 5.42, amp: 0.08, waves: 4.0, stroke: 1.0pt + aod-pal.orange)
  #aod-wavy-arrow(5.34, 5.42, 5.34, 3.24, amp: 0.08, waves: 4.0, stroke: 1.0pt + aod-pal.orange)
  #aod-text(6.18, 4.35, [$g_a <-> g_b$ \ $E_(upright("return"))$ \ $C_k^(times)$], size: 7.2pt, box-w: 1.6, box-h: 0.95)

  // Propagation zone: solid independent rays S_k^(a), S_k^(b) + dashed cross-return interference rays
  #let sx = 10.35
  // Direct single-gate rays (blue)
  #aod-arrow(5.16, 2.96, sx - 0.38, 2.35, stroke: 0.9pt + aod-pal.blue)
  #aod-arrow(5.16, 3.04, sx - 0.38, 4.35, stroke: 0.9pt + aod-pal.blue)
  #aod-arrow(5.16, 5.66, sx - 0.38, 4.35, stroke: 0.9pt + aod-pal.blue)
  #aod-arrow(5.16, 5.74, sx - 0.38, 6.35, stroke: 0.9pt + aod-pal.blue)

  // Cross-return redistributed rays (dashed orange)
  #aod-curve-arrow(5.38, 3.95, 7.65, 3.60, sx - 0.38, 4.10, stroke: (paint: aod-pal.orange, thickness: 0.95pt, dash: "dashed"))
  #aod-curve-arrow(5.38, 4.75, 7.65, 5.10, sx - 0.38, 4.60, stroke: (paint: aod-pal.orange, thickness: 0.95pt, dash: "dashed"))
  #aod-curve-arrow(5.38, 3.60, 7.65, 2.50, sx - 0.38, 2.85, stroke: (paint: aod-pal.crimson, thickness: 0.8pt, dash: "dashed"))
  #aod-curve-arrow(5.38, 5.10, 7.65, 6.20, sx - 0.38, 5.85, stroke: (paint: aod-pal.crimson, thickness: 0.8pt, dash: "dashed"))

  #aod-text(7.42, 1.82, [solid: single-gate $S_k^((a)) + S_k^((b)) = T_k^0$ ($410$)], size: 7.1pt, box-w: 4.5, box-h: 0.38)
  #aod-text(7.42, 6.95, [dashed: cross-return $C_k^(times)$ ($+26$ at $0$, $sum = +38$)], size: 7.0pt, box-w: 4.6, box-h: 0.38)

  // Right: 11-bin detector screen k = -5..+5 with exact horizontal T^x_k profile bars (8,10,20,58,80,96,80,58,20,10,8)
  #aod-line(sx, 1.65, sx, 7.05, stroke: 1.25pt + aod-pal.axis)
  #aod-text(12.28, 1.42, [*Screen $T_k^(times)$ ($sum = 448$)*], size: 7.8pt, box-w: 4.1, box-h: 0.38)
  #let tx-vals = (8, 10, 20, 58, 80, 96, 80, 58, 20, 10, 8)
  #let k-lbls = ("-5", "-4", "-3", "-2", "-1", "0", "+1", "+2", "+3", "+4", "+5")
  #for i in range(11) {
    let by = 1.85 + i * 0.48
    let tv = tx-vals.at(i)
    let bw = (tv / 96.0) * 2.55
    let fl = if i == 5 { aod-pal.orange } else if i >= 3 and i <= 7 { aod-pal.blue } else { aod-pal.slate }
    aod-box-tl(sx + 0.06, by - 0.15, bw, 0.30, [], fill: fl, stroke: 0.45pt + aod-pal.axis, radius: 0pt)
    aod-text(sx - 0.28, by, [$#k-lbls.at(i)$], size: 6.6pt, anchor: "right", box-w: 0.6, box-h: 0.30)
    aod-text(sx + 0.16 + bw, by, [#tv], size: 6.6pt, anchor: "left", box-w: 0.8, box-h: 0.30)
  }

  // Bottom exact accounting identity strip
  #aod-box-tl(
    0.45, 7.42, 13.90, 0.58,
    [#text(size: 7.6pt, weight: "bold")[Exact FRG accounting identity: $quad T_k^(times) - T_k^0 = C_k^(times)$, $quad sum_k T_k^0 = 410$, $quad sum_k C_k^(times) = 38$, $quad sum_k T_k^(times) = sum_k O_k = 448$, $quad sum_k m_k = 6$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3pt,
  )
]
