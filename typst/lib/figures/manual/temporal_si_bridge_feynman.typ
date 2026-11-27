// Authored native Typst vector figure: temporal-si-bridge-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 10.1
#let y-off = 0.60

#let rows = csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)
#let r-pair = rows.at(0)
#let r-lag = rows.at(1)
#let r-cs = rows.at(2)
#let r-trA = rows.at(3)
#let r-trB = rows.at(4)
#let r-cut = rows.at(5)
#let r-rcd = rows.at(6)
#let r-adv = rows.at(7)
#let r-hos = rows.at(8)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.14, 0.14, 14.72, fig-height-cm - 0.28, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Relational closure-beat time, conditional SI bridge $B_(upright("bridge"))$ & transfer audit],
    subtitle: [Active $5$-boundary spine $B_(upright("pair"))(0, 30] -> B_(upright("lag")) -> B_(upright("bridge")) -> B_(upright("val")) -> B_(upright("ext"))$: zero background clock $t$; exact rational ratios.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.3pt,
    subtitle-size: 7.0pt,
    gap-cm: 0.12,
  )

  // Left Zone: Native coupled lineages on half-open integer window (0, 30]
  #aod-box-tl(0.36, 1.34 + y-off, 5.36, 6.86, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.04, 1.58 + y-off, [*(a) Coupled lineages on $B_(upright("pair"))(0, 30]$*], size: 7.4pt, box-w: 5.15, box-h: 0.30)

  // Compared lineage i: closures at 2, 10, 18, 26 -> Delta bip = 3
  #aod-text(3.04, 1.92 + y-off, [Compared $i$: cuts $(2, 10, 18, 26)$, $Delta op("bip")_i = 3$], size: 6.7pt, weight: "bold", box-w: 5.05, box-h: 0.26)
  #aod-line(0.80, 2.28 + y-off, 5.28, 2.28 + y-off, stroke: 1.05pt + aod-pal.blue)
  #for cx in (1.08, 2.38, 3.68, 4.98) {
    aod-chiral-vertex(cx, 2.28 + y-off, [$C$], r: 0.19, fill: white, stroke: 0.95pt + aod-pal.blue, text-size: 6.7pt)
  }

  // Clear middle corridor for shared contact arrows between lineages
  #aod-wavy-arrow(1.08, 2.49 + y-off, 1.08, 2.91 + y-off, amp: 0.04, waves: 1.5, stroke: 0.85pt + aod-pal.gold)
  #aod-wavy-arrow(4.98, 2.49 + y-off, 4.98, 2.91 + y-off, amp: 0.04, waves: 1.5, stroke: 0.85pt + aod-pal.gold)
  #aod-text(3.04, 2.70 + y-off, [repeated bound contacts on $[0, 30]$], size: 6.6pt, style: "italic", box-w: 3.55, box-h: 0.24)

  // Reference lineage j: closures at 2, 12, 22 -> Delta bip = 2 (label below track, zero arrow overlap)
  #aod-line(0.80, 3.12 + y-off, 5.28, 3.12 + y-off, stroke: 1.05pt + aod-pal.teal)
  #for cx in (1.08, 3.03, 4.98) {
    aod-chiral-vertex(cx, 3.12 + y-off, [$R$], r: 0.19, fill: white, stroke: 0.95pt + aod-pal.teal, text-size: 6.7pt)
  }
  #aod-text(3.04, 3.48 + y-off, [Reference $j$: cuts $(2, 12, 22)$, $Delta op("bip")_j = 2$], size: 6.7pt, weight: "bold", box-w: 5.05, box-h: 0.26)

  // Sub-box 1: T1, T2, T7, T8 native observables & observed advance
  #aod-box-tl(
    0.54, 3.74 + y-off, 5.00, 2.10,
    [#text(size: 6.7pt)[
      *Native observables (T1, T2, T7, T8):* \
      $op("biz")_(i bar.v j) = #r-pair.exact_quantity$, rev $#r-pair.reverse_or_resid$; lag $#r-lag.exact_quantity$ ($#r-lag.reverse_or_resid$). \
      Directional RCD ($R D = 3$): $#r-rcd.exact_quantity$ vs $#r-rcd.reverse_or_resid$. \
      Advance ($7 slash 2$ vs $17 slash 2$): $#r-adv.exact_quantity$, signed $#r-adv.reverse_or_resid$. \
      ($A = C + phi.alt_1 - phi.alt_0$; split $7 slash 2$, clipped $0$).
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    inset: 3.5pt,
    leading: 0.35em,
  )

  // Sub-box 2: T6, T9 causal cut-40 intervention & hostile disconnect control
  #aod-box-tl(
    0.54, 5.98 + y-off, 5.00, 2.06,
    [#text(size: 6.7pt)[
      *Causal cut-$40$ control (T6, T9):* \
      Prefix $k <= 39$ invariant; drop at $k = 40$. \
      Cut-$41$ shift: #r-cut.delta_bip ($#r-cut.exact_quantity -> #r-cut.reverse_or_resid$). \
      Hostile disconnect #r-hos.delta_bip ($#r-hos.exact_quantity$): \
      rejected by replay validation at T9.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    inset: 3.5pt,
    leading: 0.35em,
  )

  // Boundary Wall B_bridge
  #aod-boundary-wall(5.96, 1.34 + y-off, 5.96, 8.20 + y-off, stroke: 1.2pt + aod-pal.purple, hatch-side: 1, hatch-count: 11, double-line: true)
  #aod-text(5.96, 1.14 + y-off, [$B_(upright("bridge"))$], size: 7.0pt, weight: "bold", box-w: 1.2, box-h: 0.24)

  // Middle Zone: Conditional SI Cesium vs Hydrogen Hyperfine Bridge Chains
  #aod-box-tl(6.20, 1.34 + y-off, 4.10, 6.86, [], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(8.25, 1.58 + y-off, [*(b) Stipulated SI chains*], size: 7.4pt, box-w: 3.90, box-h: 0.30)

  #aod-box-tl(
    6.38, 1.94 + y-off, 3.74, 2.86,
    [#text(size: 6.8pt)[
      *Cesium-$133$ chain (T3):* \
      $Delta nu_(upright("Cs")) =$ 9,192,631,770 Hz \
      Stipulated gain $a_c = a_r = 1$ \
      ($N_r = 2, N_c = 3$): \
      $Delta t_(upright("SI")) = #r-cs.exact_quantity$ s \
      $macron(nu)_c = #r-cs.reverse_or_resid$ Hz
    ]],
    stroke: 0.8pt + aod-pal.purple,
    fill: white,
    inset: 4pt,
    leading: 0.35em,
  )
  #aod-box-tl(
    6.38, 5.02 + y-off, 3.74, 3.02,
    [#text(size: 6.7pt)[
      *Hydrogen hyperfine chain:* \
      *1420.4 MHz* (Hellwig 1970) \
      21 cm maser heterodyne: \
      $284 nu_R + nu_S + nu_B + delta$. \
      Separate residual budget \
      $(u_(upright("bridge")), u_(upright("cal")))$; never fused into \
      Cs without declared adapter.
    ]],
    stroke: 0.8pt + aod-pal.gold,
    fill: aod-pal.tint-amber,
    inset: 4pt,
    leading: 0.35em,
  )

  #aod-wavy-arrow(5.72, 3.05 + y-off, 6.36, 3.05 + y-off, amp: 0.05, waves: 1.5, stroke: 0.95pt + aod-pal.purple)

  // Boundary Wall B_val (Held-out cross-field transfer gate)
  #aod-boundary-wall(10.54, 1.34 + y-off, 10.54, 8.20 + y-off, stroke: 1.2pt + aod-pal.crimson, hatch-side: 1, hatch-count: 11)
  #aod-text(10.54, 1.14 + y-off, [$B_(upright("val"))$], size: 7.0pt, weight: "bold", box-w: 1.1, box-h: 0.24)

  // Right Zone: Held-out cross-field transfer falsifier
  #aod-box-tl(10.78, 1.34 + y-off, 3.86, 6.86, [], stroke: 0.85pt + aod-pal.crimson, fill: aod-pal.tint-orange, radius: 4pt)
  #aod-text(12.71, 1.58 + y-off, [*(c) Held-out transfer audit*], size: 7.3pt, box-w: 3.76, box-h: 0.30)

  #aod-box-tl(
    10.96, 1.94 + y-off, 3.50, 2.86,
    [#text(size: 6.8pt)[
      *Field A ($3":"3":"6$ vs $1":"2":"6$, T4):* \
      Counts: #r-trA.delta_bip \
      Held-out ref $N_(0,upright("val")) = 32$ \
      Calibrated pred $= #r-trA.exact_quantity$ \
      Residual $= #r-trA.reverse_or_resid != 0$ \
      *Constant gain rejected*
    ]],
    stroke: 0.8pt + aod-pal.crimson,
    fill: white,
    inset: 4pt,
    leading: 0.35em,
  )
  #aod-box-tl(
    10.96, 5.02 + y-off, 3.50, 3.02,
    [#text(size: 6.8pt)[
      *Field B ($3":"2":"6$ vs $3":"3":"6$, T5):* \
      Counts: #r-trB.delta_bip \
      Held-out ref $N_(0,upright("val")) = 32$ \
      Calibrated pred $= #r-trB.exact_quantity$ \
      Residual $= #r-trB.reverse_or_resid != 0$ \
      *Universal SI clock blocked*
    ]],
    stroke: 0.8pt + aod-pal.crimson,
    fill: white,
    inset: 4pt,
    leading: 0.35em,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.36, 8.38 + y-off, 14.28, 0.74,
    [#text(size: 6.9pt, weight: "bold")[Engine vector RC-037 (T1–T9): relational time from $>= 2$ coupled lineages on $(0, 30]$, conditional SI stipulation at $B_(upright("bridge"))$, nonzero held-out residuals $(#r-trA.reverse_or_resid, #r-trB.reverse_or_resid)$, and cut-$40 -> 41$ causal audit.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 3.5pt,
    leading: 0.35em,
  )
]
