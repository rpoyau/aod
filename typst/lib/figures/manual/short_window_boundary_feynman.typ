// Authored native Typst vector figure: short-window-boundary-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.5

#let rows = csv("/manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i + 1))
#let ys-p = rows.map(r => float(r.p_D))
#let ys-q = rows.map(r => float(r.Q_D))
#let r-yro = rows.at(3)
#let r-t4 = rows.at(7)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.20, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Short-window RCD gate $bar.v omega bar.v$, exact conservation $p^D + Q^D = 3 R D$ & odd-window shedding*], size: 9.8pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("core")) -> B_(omega) -> B_(upright("close")) -> B_(upright("shed")) -> B_(upright("ext"))$: window clips $rho^D_(omega)$ only; native $R D$ stays intact.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Boundary-Feynman Window-Gate Clipping Schematic
  #aod-box-tl(0.38, 1.34, 6.45, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.60, 1.66, [*(a) Window gate $B_(omega)$ & shedding split*], size: 7.9pt, box-w: 6.1, box-h: 0.36)

  // Core carrier entering window gate B_omega
  #aod-chiral-vertex(1.30, 3.10, [$R D$ \ $9,61,137$], r: 0.44, fill: white, stroke: 1.1pt + aod-pal.navy, text-size: 6.8pt)
  #aod-arrow(1.78, 3.10, 3.02, 3.10, stroke: 1.2pt + aod-pal.blue)
  #aod-text(2.40, 2.76, [$3 R D$], size: 6.9pt, weight: "bold", box-w: 1.2, box-h: 0.28)

  // Window gate wall B_omega
  #aod-boundary-wall(3.12, 2.02, 3.12, 4.30, stroke: 1.2pt + aod-pal.purple, hatch-side: 1, hatch-count: 6, double-line: true)
  #aod-text(3.12, 1.88, [$B_(omega)$], size: 6.9pt, weight: "bold", box-w: 0.9, box-h: 0.26)

  // Clipped active pressure p^D = 3 rho_omega^D -> enclosure C_close -> X_shedding
  #aod-arrow(3.26, 2.66, 4.62, 2.40, stroke: 1.15pt + aod-pal.teal)
  #aod-box-tl(4.66, 2.04, 1.92, 0.72, [$p^D = 3 rho^D_(omega)$], stroke: 0.95pt + aod-pal.teal, fill: white)

  // Retained pending overhang Q^D = 3 max(0, RD - |omega|)
  #aod-wavy-arrow(3.26, 3.54, 4.62, 3.82, amp: 0.05, waves: 2.0, stroke: 1.05pt + aod-pal.amber)
  #aod-box-tl(4.66, 3.46, 1.92, 0.72, [$Q^D$ overhang], stroke: 0.95pt + aod-pal.gold, fill: aod-pal.tint-amber)

  #aod-box-tl(
    0.60, 4.50, 6.00, 2.40,
    [#text(size: 6.9pt)[
      *Exact conservation & yro trigger:* \
      1. Every row satisfies $p^D + Q^D = 3 R D$ ($27, 183, 411$). \
      2. Even/short windows ($bar.v omega bar.v in \{2, 4, 6\}$) have $p^D <= C_(upright("close"))$, so $X_(upright("shedding")) = 0$ (e.g. $3":"4$ at $bar.v omega bar.v = 6$: $p^D = #r-t4.p_D$, $Q^D = #r-t4.Q_D$). \
      3. Full odd window $1":"2":"9$ ($bar.v omega bar.v = 9$) exhausts $Q^D = #r-yro.Q_D$ and exceeds $sans("C")_8 = #r-yro.C_close$ with $X_(upright("shedding")) = #r-yro.X_shedding$.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Panel B (Right): Grouped Bar Chart of p^D and Q^D across all 8 rows
  #aod-box-tl(7.05, 1.34, 7.55, 5.78, [], stroke: 0.85pt + aod-pal.teal, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 7.12,
    y0: 1.44,
    w: 7.38,
    h: 5.56,
    pad: (left: 1.18, right: 0.26, top: 0.68, bottom: 1.16),
    title: [(b) Clipped pressure $p^D$ vs retained overhang $Q^D$],
    title-size: 7.8pt,
    xlabel: [Support : window $(p":"q, bar.v omega bar.v)$],
    ylabel: [Channel counts ($C_3 = 3$)],
    xlim: (0.3, 8.7),
    ylim: (0.0, 440.0),
    xticks: (
      (1, [$1":"2,2$]),
      (2, [$1":"2,4$]),
      (3, [$1":"2,6$]),
      (4, [$1":"2,9$]),
      (5, [$3":"3,4$]),
      (6, [$3":"3,6$]),
      (7, [$3":"4,4$]),
      (8, [$3":"4,6$]),
    ),
    x-tick-angle: -28deg,
    x-tick-dy: 0.42,
    xlabel-dy: 0.94,
    yticks: (0, 100, 200, 300, 400),
    x-tick-size: 6.8pt,
    y-tick-size: 6.8pt,
    ylabel-dx: 0.88,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.72,
        series: (
          (ys: ys-p, fill: aod-pal.teal, stroke: 0.45pt + aod-pal.axis),
          (ys: ys-q, fill: aod-pal.amber, stroke: 0.45pt + aod-pal.axis),
        ),
      ),
    ),
    legend: (
      pos: "top-left",
      cols: 1,
      col-w: 3.15,
      size: 6.8pt,
      items: (
        (kind: "patch", color: aod-pal.teal, label: [Active $p^D = 3 rho^D_(omega)$]),
        (kind: "patch", color: aod-pal.amber, label: [Pending $Q^D$]),
      ),
    ),
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-038: exact window clipping $rho^D_(omega) = min(R D, bar.v omega bar.v)$, strict conservation $p^D + Q^D = 3 R D$, and $X_(upright("shedding")) = 3$ uniquely at $(1":"2, 9)$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
