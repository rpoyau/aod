// Authored native Typst vector figure: typed-map-variance-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/typed_map_joint_law_ledger.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.5

#let rows = csv("/manual/data/boundary_sadar/typed_map_joint_law_ledger.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i + 1))
#let ys = rows.map(r => float(r.log10_ratio_plot))
#let r-f = rows.at(1)
#let r-rf = rows.at(2)
#let r-v = rows.at(4)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.20, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Typed boundary-provenance DAG, evaluation-role firewall & exact joint-law variance*], size: 9.9pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("src")) -> B_(upright("map")) -> B_(upright("joint")) -> B_(upright("role")) -> B_(upright("ext"))$: shared ancestry retained; naive first-order linearization falsified.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Typed Provenance DAG & Deduplication / Role Firewall
  #aod-box-tl(0.38, 1.34, 6.85, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.80, 1.66, [*(a) Provenance-tagged map chain & role firewall*], size: 7.9pt, box-w: 6.5, box-h: 0.36)

  // Source s_x (x = 3) -> f (u = 6) -> g (z = 12) + diamond join
  #aod-chiral-vertex(1.25, 2.78, [$x=3$], r: 0.35, fill: white, stroke: 1.1pt + aod-pal.navy, text-size: 7.0pt)
  #aod-arrow(1.62, 2.62, 3.22, 2.28, stroke: 1.1pt + aod-pal.blue)
  #aod-arrow(1.62, 2.94, 3.22, 3.28, stroke: 1.1pt + aod-pal.teal)
  #aod-box-tl(3.26, 1.98, 1.45, 0.58, [$f_1: u=6$], stroke: 0.95pt + aod-pal.blue, fill: white)
  #aod-box-tl(3.26, 3.00, 1.45, 0.58, [$f_2: v=6$], stroke: 0.95pt + aod-pal.teal, fill: white)
  #aod-arrow(4.74, 2.28, 5.76, 2.66, stroke: 1.1pt + aod-pal.purple)
  #aod-arrow(4.74, 3.28, 5.76, 2.90, stroke: 1.1pt + aod-pal.purple)
  #aod-chiral-vertex(6.18, 2.78, [$z=12$], r: 0.38, fill: aod-pal.tint-amber, stroke: 1.1pt + aod-pal.gold, text-size: 7.0pt)

  #aod-text(3.80, 3.92, [Unique source set $\{s_x\}$ deduplicates ($1$ source, not $2$ independent copies)], size: 6.8pt, weight: "bold", box-w: 6.4, box-h: 0.32)

  // Evaluation-role boundary wall (calibration != validation != held_out)
  #aod-boundary-wall(0.62, 4.28, 6.98, 4.28, stroke: 1.05pt + aod-pal.crimson, hatch-side: 1, hatch-count: 8)
  #aod-box-tl(
    0.62, 4.46, 6.36, 2.42,
    [#text(size: 6.9pt)[
      *Role & cancellation falsifiers ($B_(upright("joint")) -> B_(upright("role"))$):* \
      1. Shared disturbance $R_f = (1+d)(1-d)$: exact mean $#r-rf.exact_mean$, exact var $#r-rf.exact_var$, while naive first-order linear var $= 0$. \
      2. Near-cancellation $F$: exact-to-linear ratio $= #r-f.var_over_lin_exact approx 50.90$. \
      3. Role tags (calibration, validation, held-out) are disjoint boundary scopes; cross-role reuse is rejected.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Panel B (Right): Bar chart of log10(Var_exact / Var_linear) across all 5 laws
  #aod-box-tl(7.45, 1.34, 7.15, 5.78, [], stroke: 0.85pt + aod-pal.purple, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 7.52,
    y0: 1.44,
    w: 6.98,
    h: 5.56,
    pad: (left: 1.18, right: 0.28, top: 0.68, bottom: 1.02),
    title: [(b) Exact vs linearized variance gap $log_(10)(op("Var") slash op("Lin"))$],
    title-size: 7.8pt,
    xlabel: [Joint-law fixture (capped at $6.0$ where $op("Lin") = 0$)],
    ylabel: [$log_(10)$ variance ratio],
    xlim: (0.3, 5.7),
    ylim: (0.0, 6.9),
    xticks: (
      (1, [$T_(100)$]),
      (2, [$F_(100)$]),
      (3, [$R_f$]),
      (4, [$U_(1000)$]),
      (5, [$V_(1000)$]),
    ),
    yticks: (0, 2, 4, 6),
    x-tick-size: 6.9pt,
    y-tick-size: 6.9pt,
    ylabel-dx: 0.84,
    layers: (
      (
        type: "bars",
        xs: xs,
        ys: ys,
        bar-w: 0.54,
        fills: (aod-pal.crimson, aod-pal.blue, aod-pal.crimson, aod-pal.crimson, aod-pal.purple),
        stroke: 0.65pt + aod-pal.axis,
        value-labels: ([$infinity$], [$1.71$], [$infinity$], [$infinity$], [$5.70$]),
      ),
    ),
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-036: exact rational pushforward moments ($V_(1000)$ ratio $#r-v.var_over_lin_exact$), shared-source DAG deduplication, and strict role-scope separation.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
