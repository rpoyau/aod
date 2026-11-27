// Authored native Typst vector figure: chiral-flip-boundary-stokes (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (exact D0 Disoma two-carrier chiral Stokes encounter)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 8.5
#let y-off = 0.55

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.50, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Feynman-like two-carrier chiral exchange & Disoma Stokes interface cancellation],
    subtitle: [Enclosing scope $cal(B)_(12) = (partial F_(12), omega_(12))$ with $|omega_(12)| = 4$, $op("RCD")_(12) = 5 => rho_omega^D = 4$, $C_3 = 3 => p_(12)^D = 12$, seats $= 6$.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.6pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.12,
  )

  // Enclosing scope B_12 dashed outer boundary
  #aod-box-tl(0.55, 1.35 + y-off, 9.65, 5.35, [], stroke: (paint: aod-pal.navy, thickness: 1.0pt, dash: "dashed"), fill: aod-pal.tint-gray, radius: 5pt)
  #aod-text(5.38, 1.64 + y-off, [*Enclosing Disoma scope $cal(B)_(12)$: $quad S_(upright("int"))(R_1 union R_2; cal(B)_(12)) = +4 + (-4) = 0$*], size: 7.6pt, box-w: 9.4, box-h: 0.36)

  // Sub-regions R_1 (top) and R_2 (bottom) separated by shared interface partial R_1 cap partial R_2
  #aod-box-tl(0.85, 1.94 + y-off, 9.05, 1.86, [], stroke: 0.8pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 3.5pt)
  #aod-box-tl(0.85, 4.56 + y-off, 9.05, 1.90, [], stroke: 0.8pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 3.5pt)
  #aod-boundary-wall(1.15, 4.24 + y-off, 9.60, 4.24 + y-off, stroke: 1.1pt + aod-pal.slate, hatch-side: 1, hatch-count: 14)
  #aod-text(2.45, 4.02 + y-off, [shared interface $partial R_1 inter partial R_2$], size: 6.9pt, box-w: 3.6, box-h: 0.30)

  // Carrier 1 worldline (top): D_alpha (chi_1 = +1) -> chiral exchange vertex -> D_Omega (next state -4)
  #aod-arrow(1.20, 2.92 + y-off, 4.86, 2.92 + y-off, stroke: 1.25pt + aod-pal.blue)
  #aod-text(2.95, 2.52 + y-off, [Carrier 1 in $R_1$: $D_alpha$ ($chi_1 = +1$)], size: 7.2pt, weight: "bold", box-w: 4.1, box-h: 0.34)
  #aod-chiral-vertex(5.20, 2.92 + y-off, [$0_H$], r: 0.28, fill: aod-pal.tint-amber, stroke: 1.05pt + aod-pal.gold, text-size: 7.2pt)
  #aod-arrow(5.54, 2.92 + y-off, 9.55, 2.92 + y-off, stroke: 1.25pt + aod-pal.purple)
  #aod-text(7.65, 2.52 + y-off, [post-cut $D_Omega$: $S_(1, k+1) = -4$], size: 7.5pt, weight: "bold", box-w: 3.8, box-h: 0.38)

  // Carrier 2 worldline (bottom): D_Omega (chi_2 = -1) -> chiral exchange vertex -> D_alpha (next state +4)
  #aod-arrow(1.20, 5.52 + y-off, 5.86, 5.52 + y-off, stroke: 1.25pt + aod-pal.teal)
  #aod-text(3.35, 5.92 + y-off, [Carrier 2 in $R_2$: $D_Omega$ ($chi_2 = -1$)], size: 7.5pt, weight: "bold", box-w: 4.0, box-h: 0.38)
  #aod-chiral-vertex(6.20, 5.52 + y-off, [$0_H$], r: 0.28, fill: aod-pal.tint-amber, stroke: 1.05pt + aod-pal.gold, text-size: 7.2pt)
  #aod-arrow(6.54, 5.52 + y-off, 9.55, 5.52 + y-off, stroke: 1.25pt + aod-pal.blue)
  #aod-text(8.10, 5.92 + y-off, [post-cut $D_alpha$: $S_(2, k+1) = +4$], size: 7.5pt, weight: "bold", box-w: 3.5, box-h: 0.38)

  // Wavy Feynman-like ADAR_12 and ADAR_21 exchange channels crossing shared interface
  #aod-wavy-arrow(5.32, 3.22 + y-off, 6.02, 5.22 + y-off, amp: 0.08, waves: 3.5, stroke: 1.1pt + aod-pal.orange)
  #aod-wavy-arrow(6.08, 5.22 + y-off, 5.42, 3.22 + y-off, amp: 0.08, waves: 3.5, stroke: 1.1pt + aod-pal.crimson)
  #aod-text(4.15, 3.36 + y-off, [$phi.alt_(12) = +4$ \ ($A_(12) = +1 slash 3$)], size: 7.1pt, weight: "bold", box-w: 2.3, box-h: 0.62)
  #aod-text(7.35, 4.92 + y-off, [$phi.alt_(21) = -4$ \ ($A_(21) = -1 slash 3$)], size: 7.1pt, weight: "bold", box-w: 2.3, box-h: 0.62)

  // Right-side audit card: Stokes cancellation vs retained causal operativity
  #aod-box-tl(
    10.45, 1.35 + y-off, 3.90, 5.35,
    [#text(size: 7.2pt)[
      *Exact Disoma Ledger* \ \
      *(1) Lag & intensity:* \
      $Delta chi^(upright("lag"))_(12) = (+1) - (-1) = +2$ \
      $i_(12) = 1 slash 6 => A_(12) = +1 slash 3$ \ \
      *(2) Channel fluxes:* \
      $phi.alt_(12) = 12 dot (1 slash 3) = +4$ \
      $phi.alt_(21) = 12 dot (-1 slash 3) = -4$ \ \
      *(3) Stokes cancellation:* \
      $phi.alt_(12) + phi.alt_(21) = 0$ on $cal(B)_(12)$ \ \
      *(4) Retained operativity:* \
      Removing $phi.alt_(21)$ changes \
      $S_(1, k+1)$ from $-4$ to $0$: \
      *zero sum $!=$ zero history.*
    ]],
    stroke: 0.9pt + aod-pal.navy,
    fill: white,
    radius: 4pt,
    align-mode: left + horizon,
    inset: 4.5pt,
    leading: 0.35em,
  )

  // Bottom summary strip
  #aod-box-tl(
    0.55, 6.90 + y-off, 13.80, 0.62,
    [#text(size: 7.3pt, weight: "bold")[Finite Stokes cancels opposite oriented interface values ($+4 - 4 = 0$) while preserving both contributing channel lineages.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
