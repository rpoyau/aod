// Authored native Typst vector figure: awareness-matched-operativity-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/awareness_operativity_dec_walk.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.9
#let y-off = 0.42

#let rows = csv("/manual/data/boundary_sadar/awareness_operativity_dec_walk.csv", row-type: dictionary)
#let r-c23 = rows.at(0)
#let r-ret = rows.at(4)
#let r-rem = rows.at(5)
#let r-p2 = rows.at(6)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Boundary-Feynman matched causal operativity across cuts $23 -> 24 -> 33 -> 34$],
    subtitle: [Matched states $S_k^+ = (X_k, M_k^C, R_k)$ vs structural removal $S_k^(-e) = (X_k, M_k^C, R_k without \{R_e\})$ on $R_(upright("op")) subset V(Q_4)$.],
    top-y: 0.28,
    pad-x: 0.35,
    title-size: 9.8pt,
    subtitle-size: 7.3pt,
    gap-cm: 0.14,
  )

  // Cut 23: Shared FRG pair contact
  #aod-box-tl(0.42, 2.55 + y-off, 2.55, 3.10, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(1.70, 2.86 + y-off, [*Cut $#r-c23.cut_k$: Contact*], size: 7.7pt, box-w: 2.3, box-h: 0.34)
  #aod-chiral-vertex(1.70, 3.88 + y-off, [$e_s^times$], r: 0.34, fill: aod-pal.tint-amber, stroke: 1.05pt + aod-pal.gold, text-size: 7.2pt)
  #aod-text(1.70, 4.92 + y-off, [Target $(10,10,10)$ \ Peer $(7,7,7)$ \ $Phi_("rec") - Phi_("ind") = 3 - 2 = 1$], size: 6.5pt, box-w: 2.48, box-h: 0.95)

  // Cut 24: State factorization split (Top: Retained S^+, Bottom: Structural Removal S^{-e})
  #aod-arrow(2.98, 3.65 + y-off, 3.62, 2.55 + y-off, stroke: 1.1pt + aod-pal.teal)
  #aod-arrow(2.98, 4.10 + y-off, 3.62, 5.45 + y-off, stroke: 1.1pt + aod-pal.crimson)

  #aod-box-tl(3.65, 1.55 + y-off, 3.35, 2.05, [#text(size: 7.0pt)[*Cut $24$: Retained $S_(24)^+$* \ $R_(24) = \{r_e = 1\}$ \ Operative rebalancing \ stored in $R$ alone]], stroke: 0.95pt + aod-pal.teal, fill: aod-pal.tint-green, inset: 4pt, leading: 0.36em)
  #aod-box-tl(3.65, 4.55 + y-off, 3.35, 2.05, [#text(size: 7.0pt)[*Cut $24$: Removed $S_(24)^(-e)$* \ $R_(24) without \{r_e\} = emptyset$ \ Structural absence \ *(no numeric $0$ injected)*]], stroke: 0.95pt + aod-pal.crimson, fill: aod-pal.tint-orange, inset: 4pt, leading: 0.36em)

  // Matched Boundary Wall at Cut 33
  #aod-boundary-wall(7.42, 1.38 + y-off, 7.42, 6.74 + y-off, stroke: 1.3pt + aod-pal.navy, hatch-side: 1, hatch-count: 10, double-line: true)
  #aod-text(7.42, 7.02 + y-off, [Cut $33$ $B_(upright("match"))$], size: 7.1pt, weight: "bold", box-w: 2.2, box-h: 0.30)

  #aod-wavy-arrow(7.02, 2.58 + y-off, 7.92, 2.58 + y-off, amp: 0.055, waves: 1.5, stroke: 1.05pt + aod-pal.teal)
  #aod-wavy-arrow(7.02, 5.58 + y-off, 7.92, 5.58 + y-off, amp: 0.055, waves: 1.5, stroke: 1.05pt + aod-pal.crimson)

  // Cut 34: Strictly later Q4 continuation divergence
  #aod-box-tl(
    7.96, 1.55 + y-off, 3.45, 2.15,
    [#text(size: 7.0pt)[
      *Cut $#r-ret.cut_k$: Retained branch* \
      $J_(34)(R) = #r-ret.current_J$ ($p=1$) \
      $J_(34)(R) = #r-p2.current_J$ ($p=2$) \
      Selector $J > 0 =>$ *$v plus.o e_0 = #r-ret.target_ve$*
    ]],
    stroke: 1.0pt + aod-pal.teal,
    fill: white,
    inset: 4pt,
    leading: 0.36em,
  )
  #aod-box-tl(
    7.96, 4.50 + y-off, 3.45, 2.15,
    [#text(size: 7.0pt)[
      *Cut $#r-rem.cut_k$: Removed branch* \
      $J_(34)(R') = #r-rem.current_J$ ($p=1, 2$) \
      $Delta J = 1 slash p > 0$ \
      Selector $J <= 0 =>$ *$v plus.o e_1 = #r-rem.target_ve$*
    ]],
    stroke: 1.0pt + aod-pal.crimson,
    fill: white,
    inset: 4pt,
    leading: 0.36em,
  )

  // Passive ReadOnly Sensor Wall vs Perturbative Query Audit Card
  #aod-boundary-wall(11.68, 1.38 + y-off, 11.68, 6.74 + y-off, stroke: 1.15pt + aod-pal.purple, hatch-side: 1, hatch-count: 10)
  #aod-arrow(11.42, 2.62 + y-off, 11.92, 2.62 + y-off, stroke: 0.95pt + aod-pal.purple)
  #aod-arrow(11.42, 5.58 + y-off, 11.92, 5.58 + y-off, stroke: 0.95pt + aod-pal.purple)

  #aod-box-tl(
    11.95, 1.55 + y-off, 2.68, 5.10,
    [#text(size: 6.9pt)[
      *Sensor & Falsifier Gate* \ \
      *(1) Strictly later:* \
      $t = 34 > k = 24$ \
      $op("Op")_e^(O, H)(S_(24)) = 1$ \ \
      *(2) Passive ReadOnly:* \
      $q_(33) = 0 => Delta cal(U) = 0$ \
      (zero back-reaction) \ \
      *(3) Active query:* \
      $q_(33) = 1 => J_(34) = 2$ \
      (distinct perturbation)
    ]],
    stroke: 0.9pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
    radius: 4pt,
    align-mode: left + horizon,
    inset: 4.5pt,
    leading: 0.36em,
  )

  // Bottom invariant strip
  #aod-box-tl(
    0.42, 7.36 + y-off, 14.21, 0.74,
    [#text(size: 7.1pt, weight: "bold")[Engine vector RC-034: Awareness is branch / boundary / not-branch (SELF / BETWEEN / NOT-SELF); $op("Op")_e = 1$ proved on matched $(X, M^C, p)$ without cache restoration.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
