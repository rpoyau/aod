// Authored native Typst vector figure: hydrogen-shell-wavelet-atlas (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.3
#let y-off = 0.76

#let rows = csv("/manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i + 1))
#let ys = rows.map(r => float(r.R_series_dec6))
#let r-b4 = rows.at(1)
#let r-l3 = rows.at(5)
#let r-p5 = rows.at(8)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Hydrogen concentric shell hierarchy $S_1 dots.h S_6$, wavelet transitions & exact rational ratios],
    subtitle: [Active $5$-boundary spine $B_(upright("core")) -> B_(upright("shell"), n) -> B_(upright("shell"), m) -> B_(upright("sensor")) -> B_(upright("ext"))$: integer shell squares $n^2$ without external Rydberg scale.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.4pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.12,
  )

  // Panel A (Left): Concentric S_1..S_6 shells emitting wavy Lyman/Balmer/Paschen wavelet packets
  #aod-box-tl(0.38, 1.34 + y-off, 6.65, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.70, 1.64 + y-off, [*(a) Shell transitions $S_n -> S_m$ & wavelet emission*], size: 7.3pt, box-w: 6.45, box-h: 0.34)

  // Concentric shell arcs / circles centered at (2.40, 3.74 + y-off)
  #for (rad, col) in ((0.30, aod-pal.navy), (0.58, aod-pal.blue), (0.86, aod-pal.teal), (1.14, aod-pal.purple), (1.40, aod-pal.amber), (1.66, aod-pal.slate)) {
    aod-circle(2.40, 3.74 + y-off, rad, fill: none, stroke: 0.85pt + col)
  }
  #aod-marker(2.40, 3.74 + y-off, kind: "circle", r-pt: 2.6, color: aod-pal.crimson)
  #aod-text(2.40, 5.62 + y-off, [Shells $S_1 dots.h S_6$ ($r_n slash r_1 = n^2$)], size: 6.8pt, weight: "bold", box-w: 3.8, box-h: 0.28)

  // Internal shell jump arrows + outgoing wavy wavelet packets to B_sensor
  #aod-arrow(3.56, 3.74 + y-off, 3.00, 3.74 + y-off, stroke: 1.1pt + aod-pal.blue)
  #aod-boundary-wall(4.74, 2.22 + y-off, 4.74, 5.24 + y-off, stroke: 1.1pt + aod-pal.navy, hatch-side: 1, hatch-count: 8)
  #aod-text(4.74, 2.02 + y-off, [$B_(upright("sensor"))$], size: 6.8pt, weight: "bold", box-w: 1.2, box-h: 0.26)

  #aod-wavy-arrow(3.30, 2.86 + y-off, 4.68, 2.60 + y-off, amp: 0.05, waves: 3.0, stroke: 0.95pt + aod-pal.purple)
  #aod-text(4.92, 2.60 + y-off, [Lyman ($m=1$)], size: 6.6pt, weight: "bold", anchor: "left", box-w: 2.02, box-h: 0.28)
  #aod-wavy-arrow(3.54, 3.74 + y-off, 4.68, 3.74 + y-off, amp: 0.055, waves: 2.5, stroke: 0.95pt + aod-pal.blue)
  #aod-text(4.92, 3.74 + y-off, [Balmer ($m=2$)], size: 6.6pt, weight: "bold", anchor: "left", box-w: 2.02, box-h: 0.28)
  #aod-wavy-arrow(3.82, 4.54 + y-off, 4.68, 4.78 + y-off, amp: 0.06, waves: 2.0, stroke: 0.95pt + aod-pal.teal)
  #aod-text(4.92, 4.78 + y-off, [Paschen ($m=3$)], size: 6.6pt, weight: "bold", anchor: "left", box-w: 2.02, box-h: 0.28)

  #aod-box-tl(
    0.60, 5.88 + y-off, 6.20, 1.04,
    [#text(size: 6.8pt)[
      *Dimensionless ratio law:* $Delta hat(P)_(n -> m) = 1 slash m^2 - 1 slash n^2$ gives Balmer $4->2$: $#r-b4.R_series_exact$, Lyman $3->1$: $#r-l3.R_series_exact$, Paschen $5->3$: $#r-p5.R_series_exact$; NIST $lambda$ enters only in $B_(upright("ext"))$.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    inset: 4pt,
    leading: 0.35em,
  )

  // Panel B (Right): Bar chart of exact within-series ratios R_series
  #aod-box-tl(7.22, 1.34 + y-off, 7.38, 5.78, [], stroke: 0.85pt + aod-pal.blue, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 7.30,
    y0: 1.44 + y-off,
    w: 7.20,
    h: 5.56,
    pad: (left: 1.06, right: 0.36, top: 0.68, bottom: 1.18),
    title: [(b) Exact within-series shell ratios $R_(upright("series"))(n -> m)$],
    title-size: 7.1pt,
    xlabel: [Transition $n -> m$ (Balmer, Lyman, Paschen)],
    ylabel: [Exact ratio $R_(upright("series"))$],
    xlim: (0.3, 9.7),
    ylim: (0.0, 1.88),
    xticks: (
      (1, [$3->2$]),
      (2, [$4->2$]),
      (3, [$5->2$]),
      (4, [$6->2$]),
      (5, [$2->1$]),
      (6, [$3->1$]),
      (7, [$4->1$]),
      (8, [$4->3$]),
      (9, [$5->3$]),
    ),
    x-tick-angle: -30deg,
    x-tick-dy: 0.42,
    xlabel-dy: 0.95,
    yticks: (0.0, 0.5, 1.0, 1.5),
    x-tick-size: 6.8pt,
    y-tick-size: 6.8pt,
    ylabel-dx: 0.84,
    layers: (
      (type: "hline", y: 1.0, stroke: (paint: aod-pal.slate, thickness: 0.8pt, dash: "dashed")),
      (
        type: "bars",
        xs: xs,
        ys: ys,
        bar-w: 0.58,
        fills: (
          aod-pal.blue, aod-pal.blue, aod-pal.blue, aod-pal.blue,
          aod-pal.purple, aod-pal.purple, aod-pal.purple,
          aod-pal.teal, aod-pal.teal,
        ),
        stroke: 0.5pt + aod-pal.axis,
      ),
    ),
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34 + y-off, 14.22, 0.78,
    [#text(size: 7.1pt, weight: "bold")[Engine vector RC-039: exact rational shell transitions $Delta hat(P)_(n -> m)$, baseline-normalized series ratios, and inverse wavelength ratios $lambda_n slash lambda_(m+1) = 1 slash R_(upright("series"))$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.35em,
  )
]
