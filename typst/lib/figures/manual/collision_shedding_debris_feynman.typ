// Authored native Typst vector figure: collision-shedding-debris-feynman (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (Boundary-Feynman collision-shedding debris branching topology)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.8
#let y-off = 0.46

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Boundary-Feynman topology of rest-energy closures & collision-shedding debris],
    subtitle: [Opposing $3":"3":"6$ streams across $E_2$ chiral medium branch by exact $(P^D, Q^D, X_(upright("shedding")))$ boundary conditions.],
    top-y: 0.28,
    pad-x: 0.35,
    title-size: 9.8pt,
    subtitle-size: 7.4pt,
    gap-cm: 0.14,
  )

  // Left: Incident opposing baryon streams + BETWEEN E2 chiral vertex
  #aod-arrow(0.45, 3.25 + y-off, 2.72, 4.32 + y-off, stroke: 1.25pt + aod-pal.navy)
  #aod-arrow(0.45, 5.75 + y-off, 2.72, 4.68 + y-off, stroke: 1.25pt + aod-pal.navy)
  #aod-text(1.42, 2.95 + y-off, [$p^+$ ($3":"3":"6$) \ $R D = 61$], size: 7.4pt, weight: "bold", box-w: 2.1, box-h: 0.65)
  #aod-text(1.42, 6.08 + y-off, [$p^+$ ($3":"3":"6$) \ $R D = 61$], size: 7.4pt, weight: "bold", box-w: 2.1, box-h: 0.65)
  #aod-wavy-arrow(1.25, 3.68 + y-off, 1.25, 5.32 + y-off, amp: 0.065, waves: 3.0, stroke: 0.95pt + aod-pal.orange)
  #aod-text(0.72, 4.50 + y-off, [$E_2$ \ flips], size: 6.9pt, box-w: 0.9, box-h: 0.65)

  // Primary collision pocket vertex on partial_T R_coll
  #aod-boundary-wall(3.10, 1.35 + y-off, 3.10, 7.68 + y-off, stroke: 1.1pt + aod-pal.slate, hatch-side: -1, hatch-count: 11)
  #aod-text(3.10, 7.92 + y-off, [$partial_T R_(upright("coll"))$], size: 7.3pt, weight: "bold", box-w: 1.8, box-h: 0.34)
  #aod-chiral-vertex(3.10, 4.50 + y-off, [$cal(V)_(upright("coll"))$], r: 0.36, fill: aod-pal.tint-amber, stroke: 1.15pt + aod-pal.gold, text-size: 7.2pt)

  // Branch 1 (Top): Seated inner even closures (X_shedding = 0)
  #aod-arrow(3.42, 4.26 + y-off, 5.55, 2.00 + y-off, stroke: 1.1pt + aod-pal.teal)
  #aod-box-tl(
    5.60, 1.35 + y-off, 4.55, 1.30,
    [#text(size: 6.7pt)[
      *(1) Inner even closures ($X = 0$):* \
      Lepton: $e^-$ ($1":"2":"6$), $mu^-$ ($1":"2":"8$) \
      Baryon: $p^+$ ($3":"3":"6$), $n^0$ ($3":"4":"6$, $R D = 137$)
    ]],
    stroke: 0.9pt + aod-pal.teal,
    fill: aod-pal.tint-green,
    inset: 3.5pt,
    leading: 0.34em,
  )

  // Branch 2 (Upper-Mid): Symmetric C6/C8 overlap midpoint saddle -> Higgs 3:3:7_yro
  #aod-wavy-arrow(3.46, 4.40 + y-off, 5.55, 3.52 + y-off, amp: 0.07, waves: 3.5, stroke: 1.05pt + aod-pal.purple)
  #aod-box-tl(
    5.60, 2.79 + y-off, 4.55, 1.50,
    [#text(size: 6.7pt)[
      *(2) Overlap midpoint saddle ($3":"3":"7_(upright("yro"))$):* \
      Tritrioseptyro: $P_H^D = 21$ ($+3 slash -3$ on $sans("C")_6 slash sans("C")_8$) \
      Parent $3":"3$ conserved, $Q_H^D = 162$
    ]],
    stroke: 0.95pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
    inset: 3.5pt,
    leading: 0.34em,
  )

  // Branch 3 (Lower-Mid): Core-starvation 3:3 -> 3:2 Ditrion debris + exoshedding lift
  #aod-wavy-arrow(3.46, 4.60 + y-off, 5.55, 5.26 + y-off, amp: 0.075, waves: 3.5, stroke: 1.1pt + aod-pal.crimson)
  #aod-box-tl(
    5.60, 4.43 + y-off, 4.55, 1.66,
    [#text(size: 6.7pt)[
      *(3) Core-starvation $3":"2$ Ditrion debris ($R D = 21$):* \
      $3":"2":"6$ seated $E_2 -> B^+, B^-$ vs open $E_2^0 -> B^0$ \
      Exoshedding lift #sym.arrow.r $3":"2":"8$ ($B_s^0$) #sym.arrow.r $3":"2":"10$ ($B_c^+$)
    ]],
    stroke: 0.95pt + aod-pal.crimson,
    fill: aod-pal.tint-orange,
    inset: 3.5pt,
    leading: 0.34em,
  )

  // Branch 4 (Bottom): Complete-RD odd-window lepton shedding -> Tau 1:2:9_yro
  #aod-wavy-arrow(3.42, 4.74 + y-off, 5.55, 7.00 + y-off, amp: 0.08, waves: 4.0, stroke: 1.15pt + aod-pal.orange)
  #aod-box-tl(
    5.60, 6.23 + y-off, 4.55, 1.58,
    [#text(size: 6.7pt)[
      *(4) Odd-window lepton shedding ($1":"2":"9_(upright("yro"))$):* \
      Dimonnanyro ($tau^-$): $Q^D = 0$, $P^D = 27 > sans("C")_8 = 24$ \
      $X_(upright("shedding")) = 3 -> (19 slash 50, med 31 slash 50) |_(upright("Exo"))$
    ]],
    stroke: 1.05pt + aod-pal.orange,
    fill: aod-pal.tint-amber,
    inset: 3.5pt,
    leading: 0.34em,
  )

  // Right column: Downstream Recipient Event Lattice at passive ReadOnly B_rec
  #aod-boundary-wall(10.52, 1.35 + y-off, 10.52, 7.68 + y-off, stroke: 1.25pt + aod-pal.navy, hatch-side: 1, hatch-count: 11, double-line: true)
  #aod-text(10.52, 7.92 + y-off, [$B_(upright("rec")) slash B_(upright("sensor"))$], size: 7.3pt, weight: "bold", box-w: 2.3, box-h: 0.34)

  #aod-arrow(10.17, 5.24 + y-off, 10.82, 3.60 + y-off, stroke: 0.95pt + aod-pal.crimson)
  #aod-arrow(10.17, 7.05 + y-off, 10.82, 5.10 + y-off, stroke: 1.05pt + aod-pal.orange)

  #aod-box-tl(
    10.86, 1.35 + y-off, 3.72, 6.46,
    [#text(size: 7.1pt)[
      *Recipient Event Lattice* \
      *(strictly witness-ordered)* \ \
      *(1)* *emitted* ($w_(upright("shed"))$) \
      $quad arrow.b$ \
      *(2)* *delivered* at $partial_T R_(upright("rec"))$ \
      $quad arrow.b$ \
      *(3)* *accepted* vs *unaccepted\_pass* \
      $quad$ ($31 slash 50$ Tau missing pass) \
      $quad arrow.b$ \
      *(4)* *seated* ($Delta op("bip") = 0$) \
      $quad arrow.b$ \
      *(5)* *closed\_origin* ($j = 0$, $Delta op("bip") = 0$) \
      $quad arrow.b$ \
      *(6)* *reclosed* ($j >= 1$, $Delta op("bip") = +1$)
    ]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 4pt,
    align-mode: left + horizon,
    inset: 5pt,
    leading: 0.36em,
  )

  // Bottom invariant strip
  #aod-box-tl(
    0.45, 8.28 + y-off, 14.10, 0.64,
    [#text(size: 7.2pt, weight: "bold")[Exact RD ratios: $R D(3":"3) slash R D(1":"2) = 61 slash 9$, $quad R D(3":"4) slash R D(3":"3) = 137 slash 61$, $quad R D(3":"2) slash R D(1":"2) = 21 slash 9$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
