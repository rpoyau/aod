// Authored native Typst vector figure: five-boundary-calculation-spine (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (master 5-boundary Manual 1 calculation spine)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.8
#let y-off = 0.25

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Master five-boundary calculation spine across all Manual 1 examples],
    subtitle: [$bold(upright(a)) tack.r (F, R, partial_T R, omega) ==> B_(upright("in")) -> B_(upright("core")) -> B_(upright("shed")) -> B_(upright("sensor")) -> B_(upright("ext"))$],
    top-y: 0.28,
    pad-x: 0.35,
    title-size: 9.8pt,
    subtitle-size: 7.4pt,
    gap-cm: 0.14,
  )

  // Stage 1: B_in (Concrete Support & Window)
  #aod-box-tl(0.35, 1.40 + y-off, 2.62, 5.55, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-badge(0.68, 1.72 + y-off, [1], r: 0.18)
  #aod-text(1.82, 1.72 + y-off, [*$B_(upright("in"))$ Setup*], size: 8.0pt, box-w: 1.9, box-h: 0.36)
  #aod-box-tl(0.50, 2.15 + y-off, 2.32, 2.15, [#text(size: 7.0pt)[*Finite support:* \ $R subset.eq V(Q_4)$ \ Typed cut slots: \ $partial_T R subset.eq E(Q_4) times$ \ $\{-1, 0, +1\}$]], stroke: 0.8pt + aod-pal.blue, fill: white, inset: 3.5pt, leading: 0.36em)
  #aod-box-tl(0.50, 4.52 + y-off, 2.32, 2.15, [#text(size: 7.0pt)[*Integer window:* \ $omega = (u, v]$ \ Ancestor slot \ excluded on $H 1$ \ (no clock $t$)]], stroke: 0.8pt + aod-pal.slate, fill: white, inset: 3.5pt, leading: 0.36em)

  // Stage 2: B_core (9-Column D.E.C. & SADAR Kernel)
  #aod-arrow(2.99, 4.18 + y-off, 3.23, 4.18 + y-off, stroke: 1.05pt + aod-pal.navy)
  #aod-box-tl(3.25, 1.40 + y-off, 2.86, 5.55, [], stroke: 0.9pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 4pt)
  #aod-badge(3.58, 1.72 + y-off, [2], r: 0.18, fill: white, stroke: 0.9pt + aod-pal.teal)
  #aod-text(4.86, 1.72 + y-off, [*$B_(upright("core"))$ D.E.C.*], size: 8.0pt, box-w: 2.2, box-h: 0.36)
  #aod-box-tl(3.40, 2.15 + y-off, 2.56, 2.20, [#text(size: 6.9pt)[*9-column step:* \ $(B, v, e, v_e, sigma,$ \ $op("adm"), w, P, op("route"))$ \ Live $x x x dots.h -> x$ \ burns $0_D^m$, keeps $0_H$]], stroke: 0.8pt + aod-pal.teal, fill: white, inset: 3.5pt, leading: 0.35em)
  #aod-chiral-vertex(4.68, 4.83 + y-off, [$0_H$], r: 0.28, fill: aod-pal.tint-amber, stroke: 1.0pt + aod-pal.gold, text-size: 7.2pt)
  #aod-box-tl(3.40, 5.30 + y-off, 2.56, 1.42, [#text(size: 6.9pt)[*SADAR flux:* \ $frak(S)_B = C_3 rho_omega^D A_(i j)$ \ Exact $bb(Z) slash bb(Q)$ only]], stroke: 0.8pt + aod-pal.gold, fill: aod-pal.tint-amber, inset: 3.5pt, leading: 0.36em)

  // Stage 3: B_shed (Slide, Clipping, Stokes & Shedding)
  #aod-wavy-arrow(6.13, 4.18 + y-off, 6.45, 4.18 + y-off, amp: 0.055, waves: 1.5, stroke: 1.05pt + aod-pal.orange)
  #aod-box-tl(6.47, 1.40 + y-off, 2.74, 5.55, [], stroke: 0.9pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 4pt)
  #aod-badge(6.80, 1.72 + y-off, [3], r: 0.18, fill: white, stroke: 0.9pt + aod-pal.gold)
  #aod-text(8.02, 1.72 + y-off, [*$B_(upright("shed"))$ Audit*], size: 8.0pt, box-w: 2.1, box-h: 0.36)
  #aod-box-tl(6.62, 2.15 + y-off, 2.44, 2.15, [#text(size: 6.9pt)[*Window clip:* \ $rho_omega^D = min(rho^D, |omega|)$ \ Overhang $Q^D$ \ $p^D + Q^D = C_3 R D$]], stroke: 0.8pt + aod-pal.gold, fill: white, inset: 3.5pt, leading: 0.36em)
  #aod-box-tl(6.62, 4.52 + y-off, 2.44, 2.15, [#text(size: 6.9pt)[*Finite Stokes:* \ $phi.alt_(i j) + phi.alt_(j i) = 0$ \ Shedding surplus: \ $X = max(0, P^D - C)$]], stroke: 0.85pt + aod-pal.orange, fill: white, inset: 3.5pt, leading: 0.36em)

  // Stage 4: Passive ReadOnly Sensor Wall B_sensor
  #aod-boundary-wall(9.40, 1.40 + y-off, 9.40, 6.95 + y-off, stroke: 1.35pt + aod-pal.crimson, hatch-side: 1, hatch-count: 10, double-line: true)
  #aod-arrow(9.22, 4.18 + y-off, 9.58, 4.18 + y-off, stroke: 1.05pt + aod-pal.crimson)
  #aod-box-tl(9.60, 1.40 + y-off, 2.52, 5.55, [], stroke: 0.9pt + aod-pal.crimson, fill: white, radius: 4pt)
  #aod-badge(9.92, 1.72 + y-off, [4], r: 0.18, fill: aod-pal.tint-orange, stroke: 0.9pt + aod-pal.crimson)
  #aod-text(11.04, 1.72 + y-off, [*$B_(upright("sensor"))$*], size: 8.0pt, box-w: 1.8, box-h: 0.36)
  #aod-box-tl(9.75, 2.15 + y-off, 2.22, 2.22, [#text(size: 6.9pt)[*ReadOnly wall:* \ Witness-ordered \ recipient stages \ (zero observer \ back-reaction)]], stroke: 0.85pt + aod-pal.teal, fill: aod-pal.tint-green, inset: 3.5pt, leading: 0.36em)
  #aod-box-tl(9.75, 4.58 + y-off, 2.22, 2.09, [#text(size: 6.9pt)[*Hostile controls:* \ Reject bypass, \ same-cut leak, \ or target feedback]], stroke: 0.85pt + aod-pal.crimson, fill: aod-pal.tint-orange, inset: 3.5pt, leading: 0.36em)

  // Stage 5: Quarantined External Comparison B_ext
  #aod-boundary-wall(12.28, 1.40 + y-off, 12.28, 6.95 + y-off, stroke: 1.2pt + aod-pal.purple, hatch-side: 1, hatch-count: 10)
  #aod-arrow(12.13, 4.18 + y-off, 12.43, 4.18 + y-off, stroke: 1.05pt + aod-pal.purple)
  #aod-box-tl(12.45, 1.40 + y-off, 2.20, 5.55, [], stroke: 0.9pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-badge(12.76, 1.72 + y-off, [5], r: 0.18, fill: white, stroke: 0.9pt + aod-pal.purple)
  #aod-text(13.70, 1.72 + y-off, [*$B_(upright("ext"))$ ($Q_(upright("ext"))$)*], size: 7.7pt, box-w: 1.7, box-h: 0.36)
  #aod-box-tl(12.58, 2.15 + y-off, 1.94, 4.52, [#text(size: 6.9pt)[*Permanent S3* \ *quarantine:* \ \ Freeze native \ $bb(Z) slash bb(Q)$ output \ *before* joining \ external SI / \ PDG / NIST / \ SPARC / SWELLS \ targets \ \ Explicit HOLD \ on missing \ producers]], stroke: 0.8pt + aod-pal.purple, fill: white, inset: 3.5pt, leading: 0.36em)

  // Bottom engine parity bar
  #aod-box-tl(
    0.35, 7.47, 14.30, 0.90,
    [#text(size: 7.2pt)[
      *Dual Reference Engine execution:* Every Manual 1 example executes in zero-float Python ($bb(Z) slash bb(Q)$) and zero-float Rust ($53 slash 53$ cross-language golden vectors RC-001..RC-045 + SD-001..SD-008, including TritWord/TritRatio SWAR; tables store evaluated outputs, never replace the calculus).
    ]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
