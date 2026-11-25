// Authored native Typst vector figure: field-dynamics-boundary-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv, manual/data/boundary_sadar/sparc_pooled_primary_exact.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.6

#let rt-rows = csv("/manual/data/boundary_sadar/run_tumble_q4_dec_walk.csv", row-type: dictionary)
#let sp-rows = csv("/manual/data/boundary_sadar/sparc_pooled_primary_exact.csv", row-type: dictionary)
#let sp0 = sp-rows.at(0)
#let xs-t = rt-rows.map(r => float(r.t))
#let ys-q4 = rt-rows.map(r => float(r.Q4))
#let ys-q3 = rt-rows.map(r => float(r.Q3))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*$Q_4 -> bb(Z)^3$ hinge-saturation run-tumble D.E.C. stepper & galactic ring-shell SPARC audit*], size: 9.8pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("Q4")) -> B_(upright("hinge")) -> B_(upright("ring")) -> B_(upright("pool")) -> B_(upright("ext"))$: exact $2$-step run-tumble law & exact rational pooled $U = V^2$.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Q4 vs Z3 norm trajectory over 20 ticks from 2-step hinge-saturation stepper
  #aod-box-tl(0.38, 1.36, 7.25, 5.82, [], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 0.46,
    y0: 1.46,
    w: 7.06,
    h: 5.60,
    pad: (left: 1.15, right: 0.28, top: 0.68, bottom: 0.98),
    title: [(a) $2$-step hinge-saturation walk ($Q_4$ vs projected $Q_3$)],
    title-size: 7.7pt,
    xlabel: [Discrete tick $t in \{0, dots.h, 20\}$ (closed $16$-tick cycle)],
    ylabel: [Squared norm $Q_4, Q_3$],
    xlim: (0.0, 20.4),
    ylim: (0.0, 17.8),
    xticks: (0, 4, 8, 12, 16, 20),
    yticks: (0, 4, 8, 12, 16),
    x-tick-size: 6.9pt,
    y-tick-size: 6.9pt,
    ylabel-dx: 0.84,
    layers: (
      (type: "line", xs: xs-t, ys: ys-q4, stroke: 1.25pt + aod-pal.purple, marker: "circle", marker-color: aod-pal.purple, marker-r: 2.0),
      (type: "line", xs: xs-t, ys: ys-q3, stroke: (paint: aod-pal.teal, thickness: 1.15pt, dash: "dashed"), marker: "open-circle", marker-color: aod-pal.teal, marker-r: 2.0),
    ),
    legend: (
      pos: "top-left",
      cols: 1,
      col-w: 4.10,
      size: 6.8pt,
      items: (
        (kind: "line", color: aod-pal.purple, marker: "circle", label: [$Q_4 = h_1^2 + h_2^2 + h_3^2 + h_4^2$]),
        (kind: "line", color: aod-pal.teal, dash: "dashed", marker: "open-circle", label: [$Q_3 = h_1^2 + h_2^2 + h_3^2$]),
      ),
    ),
  )

  // Panel B (Right): Galactic Radial-Ring Shell Stack B_r -> Pooled Exact SPARC Score
  #aod-box-tl(7.84, 1.36, 6.76, 5.82, [], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(11.22, 1.68, [*(b) Galactic shell stack $B_r$ & pooled SPARC score*], size: 7.9pt, box-w: 6.4, box-h: 0.36)

  // Concentric galactic radial rings B_{r_1}, B_{r_2}, B_{r_3}
  #for (rad, col) in ((0.38, aod-pal.navy), (0.76, aod-pal.blue), (1.14, aod-pal.purple), (1.48, aod-pal.teal)) {
    aod-circle(9.75, 3.55, rad, fill: none, stroke: 0.9pt + col)
  }
  #aod-marker(9.75, 3.55, kind: "circle", r-pt: 2.8, color: aod-pal.gold)
  #aod-arrow(9.75, 3.55, 11.23, 3.55, stroke: 1.05pt + aod-pal.crimson)
  #aod-text(9.75, 5.26, [Radial shells $B_(upright("ring"), k)$ ($G 0$)], size: 7.0pt, weight: "bold", box-w: 3.3, box-h: 0.28)

  // Boundary wall B_pool -> B_ext
  #aod-boundary-wall(11.55, 2.08, 11.55, 5.18, stroke: 1.15pt + aod-pal.navy, hatch-side: 1, hatch-count: 8)
  #aod-box-tl(
    11.78, 2.12, 2.60, 3.06,
    [#text(size: 6.8pt)[
      *Exact Pooled $B_(upright("pool"))$:* \
      Quantity: $#sp0.quantity$ \
      Scored bins: $#sp0.N_scored slash #sp0.N_total$ \
      Exact $bb(Q)$ fraction \
      ($840$-digit num/den) \
      Display: \
      *$#sp0.MAPE_U_display_8dp$ %*
    ]],
    stroke: 0.85pt + aod-pal.navy,
    fill: white,
  )

  #aod-box-tl(
    8.06, 5.56, 6.32, 1.40,
    [#text(size: 6.8pt)[
      *D.E.C. stepper & G0 limits:* Run-tumble tumbles fire strictly when $2$-step run exhausts same-axis dwell ($op("adm") = 0$ at odd $t=3,5,dots.h,19$), returning to $0000$ at $t=16$. Galactic $G 0$ radial-ring projection leaves a $64.70291920$ % pooled residual without free halo fitting.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.40, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vectors RC-032 & RC-041: deterministic $21$-row hinge-saturation stepper ($Q_4 - Q_3 = h_4^2 >= 0$) and exact $209$-bin rational SPARC audit.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
