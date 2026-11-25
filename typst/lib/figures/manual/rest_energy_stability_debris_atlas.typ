// Authored native Typst vector figure: rest-energy-stability-debris-atlas (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.4

#let rows = csv("/manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let pd-vals = rows.map(r => float(r.PD_sup))
#let qd-vals = rows.map(r => float(r.QD_sup))
#let span-vals = rows.map(r => float(r.closures_in_8160_span))
#let xticks = (
  (0.0, [$e^-$]),
  (1.0, [$mu^-$]),
  (2.0, [$tau^-$]),
  (3.0, [$B^+$]),
  (4.0, [$B^0$]),
  (5.0, [$B_s^0$]),
  (6.0, [$B_c^+$]),
  (7.0, [$p^+$]),
  (8.0, [$n^0$]),
  (9.0, [$H^0$]),
)

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Panel A (Left): Support window pressure PD_sup vs pending overhang QD_sup (log10-like linear split or grouped)
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: 7.55, h: 7.55,
    pad: (left: 1.35, right: 0.25, top: 0.85, bottom: 1.15),
    title: [(a) Window pressure $P_(upright("sup"))^D$ vs overhang $Q_(upright("sup"))^D$],
    title-size: 8.5pt,
    xlabel: [10 rest-energy & debris carriers],
    ylabel: [exact count],
    ylabel-dx: 0.98,
    x-tick-size: 6.6pt,
    y-tick-size: 6.8pt,
    xlim: (-0.6, 9.6),
    ylim: (0.0, 960.0),
    xticks: xticks,
    yticks: ((0.0, [0]), (200.0, [200]), (400.0, [400]), (600.0, [600]), (800.0, [800]), (917.0, [917])),
    grid-y: true,
    layers: (
      (
        type: "grouped-bars",
        xs: xs,
        group-w: 0.74,
        series: (
          (ys: pd-vals, fill: aod-pal.blue, stroke: 0.4pt + aod-pal.navy),
          (ys: qd-vals, fill: aod-pal.orange, stroke: 0.4pt + aod-pal.crimson),
        ),
      ),
    ),
    legend: (
      pos: "top-left",
      col-w: 3.6,
      size: 6.8pt,
      items: (
        (kind: "patch", color: aod-pal.blue, label: [$P_(upright("sup"))^D = (p+q) rho_omega^D$]),
        (kind: "patch", color: aod-pal.orange, label: [$Q_(upright("sup"))^D$ pending]),
      ),
    ),
  )

  // Panel B (Right): Closures in common 8160 bit-window span across the 10 carriers
  #aod-xy-plot(
    x0: 7.55, y0: 0.0, w: 7.45, h: 7.55,
    pad: (left: 1.35, right: 0.30, top: 0.85, bottom: 1.15),
    title: [(b) Closures in 8160 common bit-window],
    title-size: 8.4pt,
    xlabel: [lineage period $2 Pi in \{8, 20, 60, 136\}$],
    ylabel: [closures in 8160],
    ylabel-dx: 0.98,
    x-tick-size: 6.6pt,
    y-tick-size: 6.8pt,
    xlim: (-0.6, 9.6),
    ylim: (0.0, 1120.0),
    xticks: xticks,
    yticks: ((60.0, [60]), (136.0, [136]), (408.0, [408]), (1020.0, [1020])),
    grid-y: true,
    layers: (
      (
        type: "bars",
        xs: xs,
        ys: span-vals,
        bar-w: 0.56,
        fills: (
          aod-pal.teal, aod-pal.teal, aod-pal.gold,
          aod-pal.crimson, aod-pal.crimson, aod-pal.crimson, aod-pal.crimson,
          aod-pal.navy, aod-pal.purple, aod-pal.gold,
        ),
        stroke: 0.45pt + aod-pal.axis,
      ),
    ),
    legend: (
      pos: "top-right",
      col-w: 3.7,
      size: 6.8pt,
      items: (
        (kind: "patch", color: aod-pal.teal, label: [closed inner carrier]),
        (kind: "patch", color: aod-pal.crimson, label: [$3":"2$ Ditrion debris]),
        (kind: "patch", color: aod-pal.gold, label: [yro shedding / saddle]),
      ),
    ),
  )

  // Bottom span vs closure distinction note
  #aod-box-tl(
    0.30, 7.68, 14.40, 0.56,
    [#text(size: 7.2pt, weight: "bold")[Common 8-lineage bit-window span $= 4 dot op("lcm")(2, 4, 6, 8, 20, 60, 136) = 8160$ (distinct from summed 8-lineage closures $0 + 60 + 136 + 408 + 1020 + 1360 + 2040 + 4080 = 9104$).]],
    stroke: 0.8pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3pt,
  )
]
