// Authored native Typst vector figure: lensing-ray-boundary-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.5

#let rows = csv("/manual/data/boundary_sadar/lensing_ray_chiral_dec_walk.csv", row-type: dictionary)
#let xs = rows.map(r => float(r.shell_k))
#let ys-t0 = rows.map(r => float(r.T0_base))
#let ys-tx = rows.map(r => float(r.T_cross))
#let ys-o = rows.map(r => float(r.O_comparator))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.20, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Galactic lensing shell ray walk ($k = 1 dots.h 4$), FRG cross-shell gate & $L 3 slash K 4$ quarantine*], size: 9.8pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("src")) -> B_(upright("shell"),k) -> B_(upright("FRG")) -> B_(delta, 3) -> B_(upright("SWELLS"))$: $3$ chiral flips; target acquisition quarantined.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Concentric Lens Shells k=1..4 with Grazing Ray & 3 Chiral-Flip Vertices
  #aod-box-tl(0.38, 1.34, 6.85, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.80, 1.66, [*(a) Ray chord across $k = 1 dots.h 4$ & chiral flips*], size: 7.9pt, box-w: 6.5, box-h: 0.36)

  // Concentric lens shells centered at (2.85, 3.85)
  #for (rad, col) in ((0.42, aod-pal.navy), (0.82, aod-pal.blue), (1.22, aod-pal.purple), (1.62, aod-pal.teal)) {
    aod-circle(2.75, 3.88, rad, fill: none, stroke: 0.85pt + col)
  }
  #aod-marker(2.75, 3.88, kind: "circle", r-pt: 2.8, color: aod-pal.navy)

  // Grazing ray chord with 4 shell encounters (k=1,2,4 flip; k=3 no flip)
  #aod-line(0.75, 2.72, 4.75, 2.72, stroke: 1.2pt + aod-pal.orange)
  #aod-arrow(4.45, 2.72, 4.92, 2.72, stroke: 1.2pt + aod-pal.orange)
  #aod-chiral-vertex(1.48, 2.72, [$0_H$], r: 0.21, fill: aod-pal.tint-amber, stroke: 0.95pt + aod-pal.gold, text-size: 6.8pt)
  #aod-chiral-vertex(2.32, 2.72, [$0_H$], r: 0.21, fill: aod-pal.tint-amber, stroke: 0.95pt + aod-pal.gold, text-size: 6.8pt)
  #aod-chiral-vertex(3.18, 2.72, [$0$], r: 0.20, fill: white, stroke: 0.9pt + aod-pal.slate, text-size: 6.8pt)
  #aod-chiral-vertex(4.02, 2.72, [$0_H$], r: 0.21, fill: aod-pal.tint-amber, stroke: 0.95pt + aod-pal.gold, text-size: 6.8pt)
  #aod-text(2.75, 2.24, [Shells $k = 1, 2, 4$ flip ($+1 -> -1 -> +1 -> -1$); $k = 3$ keeps $+1$], size: 6.8pt, weight: "bold", box-w: 4.5, box-h: 0.28)

  // Quarantine Wall before SWELLS / L3-K4 target join
  #aod-boundary-wall(5.12, 2.10, 5.12, 5.56, stroke: 1.2pt + aod-pal.crimson, hatch-side: 1, hatch-count: 8, double-line: true)
  #aod-box-tl(
    5.32, 2.20, 1.70, 3.30,
    [#text(size: 6.8pt)[
      *$B_(upright("SWELLS"))$ Gate:* \
      Pre-target $L 0$ fixture only. \
      $L 3 slash K 4$ 3D+time-flow inputs *HOLD* until bound.
    ]],
    stroke: 0.85pt + aod-pal.crimson,
    fill: white,
  )

  #aod-box-tl(
    0.60, 5.72, 6.42, 1.20,
    [#text(size: 6.8pt)[
      *FRG & $delta_3$ invariants:* Every shell satisfies $T_k^times - T_k^0 = C_k^times$ ($7-4=3$, $11-6=5$, $3-5=-2$, $12-8=4$). Comparator $O_k = (7, 10, 3, 11)$ yields $Delta_Z = (0, 1, 0, 1)$ and $3$ active chiral flips.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Panel B (Right): Grouped Bar Chart of T_k^0, T_k^x, and O_k across shells k=1..4
  #aod-box-tl(7.45, 1.34, 7.15, 5.78, [], stroke: 0.85pt + aod-pal.purple, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 7.52,
    y0: 1.44,
    w: 6.98,
    h: 5.56,
    pad: (left: 1.12, right: 0.28, top: 0.68, bottom: 0.98),
    title: [(b) FRG shell totals $T_k^0, T_k^times$ vs comparator $O_k$],
    title-size: 7.8pt,
    xlabel: [Concentric lens shell index $k in \{1, 2, 3, 4\}$],
    ylabel: [Exact integer count],
    xlim: (0.4, 4.6),
    ylim: (0.0, 13.8),
    xticks: (1, 2, 3, 4),
    yticks: (0, 4, 8, 12),
    x-tick-size: 6.9pt,
    y-tick-size: 6.9pt,
    ylabel-dx: 0.82,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.68,
        series: (
          (ys: ys-t0, fill: aod-pal.sky, stroke: 0.45pt + aod-pal.axis),
          (ys: ys-tx, fill: aod-pal.purple, stroke: 0.45pt + aod-pal.axis),
          (ys: ys-o, fill: aod-pal.amber, stroke: 0.45pt + aod-pal.axis),
        ),
      ),
    ),
    legend: (
      pos: "top-left",
      cols: 1,
      col-w: 3.15,
      size: 6.8pt,
      items: (
        (kind: "patch", color: aod-pal.sky, label: [Uncoupled $T_k^0$]),
        (kind: "patch", color: aod-pal.purple, label: [Coupled $T_k^times$]),
        (kind: "patch", color: aod-pal.amber, label: [Comparator $O_k$]),
      ),
    ),
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-042: exact FRG cross-shell law $T_k^times - T_k^0 = C_k^times$, $3$ chiral flips, $sum T_k^times = 33$, and pre-SWELLS target quarantine.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
