// Audited S1b native Typst vector figure: coordinate-phase-delta3-wireframe (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/brownian/{brownian_sample_track,phase_cycle_delta3,octant_delta3}.csv)
// Historical raster retained byte-for-byte: manual/figures/coordinate_phase_delta3_wireframe.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 8.6

#let track = csv("/manual/data/brownian/brownian_sample_track.csv", row-type: dictionary)
#let pts3d = track.map(r => (float(r.x), float(r.y), float(r.z)))
#let ph = csv("/manual/data/brownian/phase_cycle_delta3.csv", row-type: dictionary)
#let ph-x = ph.map(r => float(r.theta))
#let ph-y = ph.map(r => float(r.observed_count))
#let oc = csv("/manual/data/brownian/octant_delta3.csv", row-type: dictionary)
#let oc-x = oc.map(r => float(r.octant))
#let oc-y = oc.map(r => float(r.observed_count))

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Main title
  #aod-text(7.3, 0.36, [*3D Coordinate Phase-Cycle $delta_3$ Fixture*], size: 11.4pt, box-w: 14.0, box-h: 0.5)

  // Left: 3D integerized trajectory (elev=22, azim=-58)
  #aod-3d-wireframe(
    x0: 0.25, y0: 0.78, w: 6.45, h: 5.55,
    title: [Integerized 3D trajectory],
    xlim: (0, 6), ylim: (0, 5), zlim: (0, 5),
    xticks: (0, 1, 2, 3, 4, 5, 6),
    yticks: (0, 1, 2, 3, 4, 5),
    zticks: (0, 1, 2, 3, 4, 5),
    elev: 22.0,
    azim: -58.0,
    points: pts3d,
    stroke: 1.35pt + black,
    marker-color: black,
    chord: true,
    annotations: (
      (0, 0, 0, 0.16, 0.22, [$z_i$]),
      (3, 2.5, 2.5, 0.45, -0.05, [$Delta z_i^((n))$]),
      (6, 5, 5, -0.22, -0.36, [$z_(i + n)$]),
    ),
  )

  // Top-right: Equations + delta_3 badge (cleanly separated from Q_i^(n) equation)
  #aod-text(10.8, 0.96, [*Integer squared displacement and phase*], size: 8.8pt, box-w: 7.4, box-h: 0.42)
  #aod-text(7.15, 1.44, [$Delta z_i^((n)) = (a_i^((n)), b_i^((n)), c_i^((n))) in bb(Z)^3$], size: 7.4pt, anchor: "left", box-w: 5.8, box-h: 0.4)
  #aod-text(7.15, 1.90, [$Q_i^((n)) = (a_i^((n)))^2 + (b_i^((n)))^2 + (c_i^((n)))^2 in bb(Z)_(>= 0)$], size: 7.4pt, anchor: "left", box-w: 7.2, box-h: 0.4)
  #aod-text(7.15, 2.38, [$theta_i^((n)) = Q_i^((n)) mod beta_a$], size: 7.4pt, anchor: "left", box-w: 4.3, box-h: 0.4)
  #aod-box-tl(11.65, 2.12, 2.75, 0.54, [#text(size: 7.2pt)[$delta_(3, k) = (s_k^((3)), m_k)$]], stroke: 0.75pt + aod-pal.axis, fill: white, radius: 3pt, inset: 2pt)
  #aod-text(7.15, 2.88, [Active fixture: counts on $Q$, phase, and octant bins; no radial-distance fit.], size: 6.3pt, anchor: "left", box-w: 7.4, box-h: 0.40)

  // Bottom-right left: Phase counts O_theta
  #aod-xy-plot(
    x0: 6.95, y0: 3.30, w: 3.72, h: 3.12,
    pad: (left: 0.85, right: 0.18, top: 0.48, bottom: 0.74),
    title: [Phase counts $O_theta$],
    title-size: 7.8pt,
    xlabel: [$theta$],
    ylabel: [count],
    xlabel-dy: 0.48,
    ylabel-dx: 0.58,
    xlim: (-0.65, 4.65),
    ylim: (0.0, 4.25),
    xticks: (0, 1, 2, 3, 4),
    yticks: (0, 2, 4),
    x-tick-size: 6.8pt,
    y-tick-size: 6.8pt,
    x-tick-dy: 0.22,
    grid-y: false,
    layers: (
      (type: "bars", xs: ph-x, ys: ph-y, bar-w: 0.78, fills: rgb("#C4C4C4"), stroke: 0.7pt + black),
    ),
  )

  // Bottom-right right: Octant counts O_q
  #aod-xy-plot(
    x0: 10.75, y0: 3.30, w: 3.72, h: 3.12,
    pad: (left: 0.85, right: 0.18, top: 0.48, bottom: 0.74),
    title: [Octant counts $O_q$],
    title-size: 7.8pt,
    xlabel: [$q$],
    ylabel: [count],
    xlabel-dy: 0.48,
    ylabel-dx: 0.58,
    xlim: (-0.65, 7.65),
    ylim: (0.0, 6.35),
    xticks: (0, 1, 2, 3, 4, 5, 6, 7),
    yticks: (0, 2, 4, 6),
    x-tick-size: 6.6pt,
    y-tick-size: 6.8pt,
    x-tick-dy: 0.22,
    grid-y: false,
    layers: (
      (type: "bars", xs: oc-x, ys: oc-y, bar-w: 0.78, fills: rgb("#C4C4C4"), stroke: 0.7pt + black),
    ),
  )

  // Bottom pipeline strip
  #let pipe = (
    (0.35, 1.38, [$z_i in bb(Z)^3$]),
    (2.38, 1.12, [$Delta z_i^((n))$]),
    (4.15, 1.02, [$Q_i^((n))$]),
    (5.82, 1.52, [$Q mod beta_a$]),
    (8.00, 1.98, [octant counts]),
    (10.65, 0.82, [$delta_3$]),
    (12.14, 2.08, [integer ratios]),
  )
  #for i in range(pipe.len()) {
    let (px, pw, pl) = pipe.at(i)
    aod-box-tl(px, 7.18, pw, 0.56, [#text(size: 7.2pt)[#pl]], stroke: 0.7pt + aod-pal.axis, fill: white, radius: 3pt, inset: 2pt)
    if i < pipe.len() - 1 {
      let nx = pipe.at(i + 1).at(0)
      aod-arrow(px + pw + 0.10, 7.46, nx - 0.10, 7.46, stroke: 0.85pt + black, head-len: 3.6, head-half: 1.7)
    }
  }

  #aod-text(7.3, 8.20, [*3D coordinate phase-cycle $delta_3$ fixture: integer counts first; continuous summaries only after exact fixture*], size: 7.4pt, box-w: 14.2, box-h: 0.45)
]
