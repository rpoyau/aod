// Authored native Typst vector figure: temporal-si-bridge-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.6

#let rows = csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)
#let r-pair = rows.at(0)
#let r-lag = rows.at(1)
#let r-cs = rows.at(2)
#let r-trA = rows.at(3)
#let r-trB = rows.at(4)
#let r-cut = rows.at(5)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Relational closure-beat time, conditional SI bridge $B_(upright("bridge"))$ & held-out transfer rejection*], size: 9.8pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("pair"))(0,30] -> B_(upright("lag")) -> B_(upright("bridge")) -> B_(upright("val")) -> B_(upright("ext"))$: zero background clock $t$; exact rational ratios.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Left Zone: Native coupled lineages on integer window (0, 30]
  #aod-box-tl(0.38, 1.36, 5.30, 5.82, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.03, 1.68, [*(a) Coupled lineages on $B_(upright("pair"))(0, 30]$*], size: 7.9pt, box-w: 5.0, box-h: 0.36)

  // Compared lineage i: closures at 2, 10, 18, 26 -> Delta bip = 3
  #aod-text(3.03, 2.12, [Compared $i$: cuts $(2, 10, 18, 26)$, $Delta op("bip")_i = 3$], size: 6.9pt, weight: "bold", box-w: 4.9, box-h: 0.30)
  #aod-line(0.85, 2.52, 5.20, 2.52, stroke: 1.05pt + aod-pal.blue)
  #for cx in (1.10, 2.32, 3.54, 4.76) {
    aod-chiral-vertex(cx, 2.52, [$C$], r: 0.19, fill: white, stroke: 0.95pt + aod-pal.blue, text-size: 6.8pt)
  }

  // Reference lineage j: closures at 2, 12, 22 -> Delta bip = 2
  #aod-text(3.03, 3.06, [Reference $j$: cuts $(2, 12, 22)$, $Delta op("bip")_j = 2$], size: 6.9pt, weight: "bold", box-w: 4.9, box-h: 0.30)
  #aod-line(0.85, 3.46, 5.20, 3.46, stroke: 1.05pt + aod-pal.teal)
  #for cx in (1.10, 2.93, 4.76) {
    aod-chiral-vertex(cx, 3.46, [$R$], r: 0.19, fill: white, stroke: 0.95pt + aod-pal.teal, text-size: 6.8pt)
  }
  // Shared contact arrows between lineages
  #aod-wavy-arrow(1.10, 2.73, 1.10, 3.25, amp: 0.04, waves: 1.5, stroke: 0.85pt + aod-pal.gold)
  #aod-wavy-arrow(4.76, 2.73, 4.76, 3.25, amp: 0.04, waves: 1.5, stroke: 0.85pt + aod-pal.gold)

  #aod-box-tl(
    0.60, 4.02, 4.86, 2.92,
    [#text(size: 6.9pt)[
      *Authenticated native observables:* \
      $op("biz")_(i bar.v j) = #r-pair.exact_quantity$, reverse $= #r-pair.reverse_or_resid$. \
      Unwrapped lag $= #r-lag.exact_quantity$ (anti-sym $#r-lag.reverse_or_resid$). \
      *Causal cut-$40$ intervention ($B_(upright("causal"))$):* \
      Pre-cut $k <= 40$ invariant; response appears strictly later at $k = 41$: $(6,5) -> (2,5)$ ($#r-cut.exact_quantity -> #r-cut.reverse_or_resid$).
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Boundary Wall B_bridge
  #aod-boundary-wall(5.92, 1.36, 5.92, 7.18, stroke: 1.2pt + aod-pal.purple, hatch-side: 1, hatch-count: 10, double-line: true)
  #aod-text(5.92, 1.18, [$B_(upright("bridge"))$], size: 7.0pt, weight: "bold", box-w: 1.2, box-h: 0.28)

  // Middle Zone: Conditional SI Cesium vs Hydrogen Bridge Chains
  #aod-box-tl(6.18, 1.36, 4.10, 5.82, [], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(8.23, 1.68, [*(b) Stipulated SI chains*], size: 7.9pt, box-w: 3.8, box-h: 0.36)

  #aod-box-tl(
    6.38, 2.06, 3.70, 2.28,
    [#text(size: 6.9pt)[
      *Cesium-$133$ chain:* \
      $Delta nu_(upright("Cs")) = 9,192,631,770$ Hz \
      Gain $a_c = a_r = 1$: \
      $Delta t_(upright("SI")) = #r-cs.exact_quantity$ s \
      $nu_c = #r-cs.reverse_or_resid$ Hz
    ]],
    stroke: 0.8pt + aod-pal.purple,
    fill: white,
  )
  #aod-box-tl(
    6.38, 4.58, 3.70, 2.36,
    [#text(size: 6.9pt)[
      *Hydrogen $1 S$-$2 S$ chain:* \
      Separate bridge chain \
      with explicit residual \
      budget $(u_(upright("bridge")), u_(upright("cal")))$; \
      never fused into Cs \
      without declared adapter.
    ]],
    stroke: 0.8pt + aod-pal.gold,
    fill: aod-pal.tint-amber,
  )

  #aod-wavy-arrow(5.68, 3.10, 6.36, 3.10, amp: 0.05, waves: 1.5, stroke: 0.95pt + aod-pal.purple)

  // Boundary Wall B_val (Held-out cross-field transfer gate)
  #aod-boundary-wall(10.52, 1.36, 10.52, 7.18, stroke: 1.2pt + aod-pal.crimson, hatch-side: 1, hatch-count: 10)
  #aod-text(10.52, 1.18, [$B_(upright("val"))$], size: 7.0pt, weight: "bold", box-w: 1.1, box-h: 0.28)

  // Right Zone: Held-out cross-field transfer falsifier
  #aod-box-tl(10.76, 1.36, 3.84, 5.82, [], stroke: 0.85pt + aod-pal.crimson, fill: aod-pal.tint-orange, radius: 4pt)
  #aod-text(12.68, 1.68, [*(c) Held-out transfer audit*], size: 7.9pt, box-w: 3.6, box-h: 0.36)

  #aod-box-tl(
    10.96, 2.06, 3.44, 2.30,
    [#text(size: 6.9pt)[
      *Field A ($3":"3":"6$ vs $1":"2":"6$):* \
      Calibrated pred $= #r-trA.exact_quantity$ \
      Held-out obs $= 26$ \
      Residual $= #r-trA.reverse_or_resid != 0$ \
      *Constant gain rejected*
    ]],
    stroke: 0.8pt + aod-pal.crimson,
    fill: white,
  )
  #aod-box-tl(
    10.96, 4.58, 3.44, 2.36,
    [#text(size: 6.9pt)[
      *Field B ($3":"2":"6$ vs $3":"3":"6$):* \
      Calibrated pred $= #r-trB.exact_quantity$ \
      Held-out obs $= 21$ \
      Residual $= #r-trB.reverse_or_resid != 0$ \
      *Universal SI clock blocked*
    ]],
    stroke: 0.8pt + aod-pal.crimson,
    fill: white,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.40, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-037: relational time from $>= 2$ coupled lineages, conditional SI stipulation at $B_(upright("bridge"))$, and nonzero held-out residuals $(#r-trA.reverse_or_resid, #r-trB.reverse_or_resid)$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
