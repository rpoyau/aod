// Authored native Typst vector figure: dec-hinge-slide-chiral-vertex (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 9.5
#let y-off = 0.76

#let walk = csv("/manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv", row-type: dictionary)
#let c1-hinge = walk.at(2)
#let c2-block = walk.at(4)
#let c2-ret0 = walk.at(5)
#let c2-ret1 = walk.at(6)
#let c2-tun = walk.at(7)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.50, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Boundary-Feynman $Q_4$ D.E.C. walk: blocked dwell, slide renormalization & chiral flip],
    subtitle: [Active region $R_(upright("core")) = \{0000, 0001, 0010, 0011\} subset V(Q_4)$, committed incoming ancestor $e_3$, window $|omega|_s = 2$, $R D_s = 5$.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.6pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.12,
  )

  // Left region R_core shading (x: 0.45..8.85) vs Exterior R_ext (x: 8.85..14.35)
  #aod-box-tl(0.45, 1.35 + y-off, 8.30, 5.85, [], stroke: 0.8pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-box-tl(9.05, 1.35 + y-off, 5.30, 5.85, [], stroke: 0.8pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(4.60, 1.66 + y-off, [*Interior region $R_(upright("core"))$ (cuts $1 -> 2$)*], size: 8.2pt, box-w: 7.8, box-h: 0.38)
  #aod-text(11.70, 1.66 + y-off, [*Exterior across $partial_T R_(upright("core"))$ (cut $3$)*], size: 8.2pt, box-w: 5.0, box-h: 0.38)

  // Explicit typed boundary wall partial_T R_core at x = 8.90
  #aod-boundary-wall(8.90, 1.32 + y-off, 8.90, 7.16 + y-off, stroke: 1.35pt + aod-pal.crimson, hatch-side: 1, hatch-count: 10, double-line: true)
  #aod-text(8.90, 7.42 + y-off, [$partial_T R_(upright("core"))$], size: 7.6pt, weight: "bold", box-w: 1.8, box-h: 0.34)

  // Incoming ancestor leg e3 into active vertex v0 = 0000
  #let vx = 3.25
  #let vy = 4.35 + y-off
  #aod-arrow(0.75, vy, vx - 0.36, vy, stroke: 1.15pt + aod-pal.slate)
  #aod-text(1.85, vy - 0.36, [incoming $e_3$ \ $D_alpha (+1, -1)$], size: 7.2pt, box-w: 2.2, box-h: 0.65)
  #aod-text(1.85, vy + 0.42, [(excluded for H1)], size: 6.7pt, box-w: 2.2, box-h: 0.34)

  // Active Q4 vertex 0000 + structural hinge 0_H
  #aod-chiral-vertex(vx, vy, [$0000$ \ $0_H$], r: 0.40, fill: aod-pal.tint-amber, stroke: 1.15pt + aod-pal.gold, text-size: 7.2pt)

  // Optional dwell loop (e2, 0_D): Cut 1 weight 4 (4/11), Cut 2 blocked adm=0 -> 0/1
  #aod-arc-arrow(vx, vy - 0.72, 0.42, -55, 235, stroke: (paint: aod-pal.crimson, thickness: 0.95pt, dash: "dashed"))
  #aod-marker(vx, vy - 1.14, kind: "cross", r-pt: 3.4, color: aod-pal.crimson)
  #aod-box-tl(
    0.66, 1.92 + y-off, 4.78, 1.04,
    [#text(size: 6.7pt)[
      Dwell $(e_2, 0_D)$: Cut 1 $P = #c1-hinge.prob_exact$ \
      Cut 2 ($x x x dots.h$ is $x$) $-> op("adm") = #c2-block.adm$, $P = #c2-block.prob_exact$ \
      *(structural $0_H$ preserved; $m = 0$)*
    ]],
    stroke: 0.75pt + aod-pal.crimson,
    fill: white,
    inset: 3pt,
    leading: 0.32em,
  )

  // Returned slide branch 1: e0 -> 0001 (prob 3/7)
  #let r1x = 7.35
  #let r1y = 2.55 + y-off
  #aod-arrow(vx + 0.35, vy - 0.18, r1x - 0.92, r1y + 0.10, stroke: 1.1pt + aod-pal.teal)
  #aod-text(5.78, 3.68 + y-off, [$e_0, sigma = -1$ \ $w = #c2-ret0.weight_w -> P = #c2-ret0.prob_exact$], size: 6.7pt, box-w: 2.3, box-h: 0.60)
  #aod-box(r1x, r1y, 1.80, 0.88, [#text(size: 7.0pt)[$0001$ \ returned \ $D_alpha (+1,-1)$]], stroke: 0.9pt + aod-pal.teal, fill: aod-pal.tint-green, inset: 3.5pt, leading: 0.34em)

  // Returned slide branch 2: e1 -> 0010 (prob 3/7)
  #let r2x = 7.35
  #let r2y = 6.18 + y-off
  #aod-arrow(vx + 0.35, vy + 0.18, r2x - 0.92, r2y - 0.10, stroke: 1.1pt + aod-pal.teal)
  #aod-text(4.55, 5.72 + y-off, [$e_1, sigma = -1$ \ $w = #c2-ret1.weight_w -> P = #c2-ret1.prob_exact$], size: 6.7pt, box-w: 2.3, box-h: 0.60)
  #aod-box(r2x, r2y, 1.80, 0.88, [#text(size: 7.0pt)[$0010$ \ returned \ $D_alpha (+1,-1)$]], stroke: 0.9pt + aod-pal.teal, fill: aod-pal.tint-green, inset: 3.5pt, leading: 0.34em)

  // Boundary-crossing slide branch 3: e2, sigma=+1 -> 0100 across partial_T R_core with chiral flip!
  #let tx = 11.75
  #let ty = 3.72 + y-off
  #aod-wavy-arrow(vx + 0.42, vy, 8.58, vy, amp: 0.075, waves: 4.5, stroke: 1.15pt + aod-pal.orange)
  #aod-text(6.65, vy + 0.48, [slide tunnel $(e_2, +1)$: \ $w = #c2-tun.weight_w -> P = #c2-tun.prob_exact$], size: 6.9pt, weight: "bold", box-w: 3.2, box-h: 0.60)
  #aod-chiral-vertex(8.90, vy, [$0_H$], r: 0.28, fill: white, stroke: 1.1pt + aod-pal.crimson, text-size: 7.0pt)
  #aod-wavy-arrow(9.22, vy, 10.18, vy, amp: 0.075, waves: 2.0, stroke: 1.15pt + aod-pal.purple)

  // Exterior flipped state card at vertex 0100
  #aod-box-tl(
    10.22, 2.58 + y-off, 3.85, 2.38,
    [#text(size: 6.9pt)[
      *Vertex $0100$* \
      Chiral flip across $0_H$: \
      *$D_Omega (-1, +1)$* \
      $rho_omega^D = min(5, 2) = 2$ \
      $p_s^D = 6$, $T_(upright("tunnel"))^D = 6 slash 7$
    ]],
    stroke: 1.0pt + aod-pal.purple,
    fill: white,
    inset: 4pt,
    leading: 0.35em,
  )

  // Exterior audit note on retained prior history
  #aod-box-tl(
    9.32, 5.26 + y-off, 4.78, 1.66,
    [#text(size: 6.9pt)[
      *No retroactive overwrite:* \
      Prior interior word $(+1, 0_H, -1)$ remains committed on cuts $1..2$; flipped $(-1, +1)$ applies from cut $3$ onward.
    ]],
    stroke: 0.8pt + aod-pal.slate,
    fill: white,
    inset: 4.5pt,
    leading: 0.36em,
  )

  // Bottom exact conservation strip
  #aod-box-tl(
    0.45, 7.68 + y-off, 13.90, 0.68,
    [#text(size: 7.3pt, weight: "bold")[Exact slide renormalization: pre-block integer weights $(3, 3, 1)$ unchanged; $Z' = 7$; $P_(upright("returned")) = 6 slash 7$, $P_(upright("tunnel")) = 1 slash 7$, $T_(upright("tunnel"))^D = 6 slash 7$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
