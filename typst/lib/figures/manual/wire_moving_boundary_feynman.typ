// Authored native Typst vector figure: wire-moving-boundary-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.5

#let rows = csv("/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv", row-type: dictionary)
#let r-mov = rows.at(0)
#let w-rows = rows.slice(1)
#let xs = w-rows.map(r => float(r.cut))
#let ys-cur = w-rows.map(r => float(r.later_electron_current))
#let ys-union = w-rows.map(r => float(r.union_boundary))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.20, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Moving-boundary Stokes balance & scoped $1":"2":"6$ electron-above-wire SADAR walk*], size: 9.8pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("wire")) -> B_(e) -> B_(upright("int")) -> B_(upright("union")) -> B_(upright("ext"))$: internal pair cancels in union while electron current grows.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Moving-Boundary R_1 -> R_2 Stokes Decomposition
  #aod-box-tl(0.38, 1.34, 6.70, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.73, 1.66, [*(a) Moving boundary $R_1 -> R_2$: $Phi^D_(upright("mov")) = #r-mov.Phi_moving$*], size: 7.9pt, box-w: 6.3, box-h: 0.36)

  // Region R_1 expanding to R_2
  #aod-box-tl(0.74, 2.18, 2.55, 2.00, [$R_1$], stroke: 1.05pt + aod-pal.navy, fill: white, radius: 3pt)
  #aod-box-tl(3.29, 2.18, 1.85, 2.00, [$Delta R$ \ sweep], stroke: (paint: aod-pal.purple, thickness: 1.05pt, dash: "dashed"), fill: aod-pal.tint-purple, radius: 3pt)

  // Crossing (+8), Sweep (-3), Shedding (+2) arrows
  #aod-arrow(2.75, 2.55, 4.15, 2.55, stroke: 1.15pt + aod-pal.blue)
  #aod-text(2.05, 2.55, [$Phi_(upright("cross")) = +#r-mov.Phi_cross$], size: 6.8pt, weight: "bold", box-w: 2.1, box-h: 0.28)
  #aod-arrow(4.95, 3.18, 3.55, 3.18, stroke: 1.15pt + aod-pal.purple)
  #aod-text(5.85, 3.18, [$-Phi_(upright("sweep")) = -#r-mov.Phi_sweep$], size: 6.8pt, weight: "bold", box-w: 2.0, box-h: 0.28)
  #aod-wavy-arrow(4.55, 3.82, 6.20, 3.82, amp: 0.05, waves: 2.5, stroke: 1.05pt + aod-pal.orange)
  #aod-text(5.80, 3.52, [$+Phi_(upright("shed")) = +#r-mov.Phi_shedding$], size: 6.8pt, weight: "bold", box-w: 2.1, box-h: 0.28)

  #aod-box-tl(
    0.62, 4.46, 6.22, 2.44,
    [#text(size: 6.9pt)[
      *Moving-boundary & wire-electron laws:* \
      1. Moving-boundary balance: $Phi^D_(upright("mov")) = #r-mov.Phi_cross - #r-mov.Phi_sweep + #r-mov.Phi_shedding = #r-mov.Phi_moving$ ($!= 8$, falsifying static-boundary omission of sweep and shedding). \
      2. Scoped wire-electron encounter (cuts $52..55$): wire $+4, 0, +4, +5$ and electron $-4, 0, -4, -5$ cancel on $partial(R_(upright("wire")) union R_e) = 0$, while realized electron current advances $4 -> 4 -> 8 -> 13$ (held constant at uncoupled cut $53$).
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Panel B (Right): 4-Cut Electron Current vs Union Boundary Cancellation Plot
  #aod-box-tl(7.28, 1.34, 7.32, 5.78, [], stroke: 0.85pt + aod-pal.teal, fill: white, radius: 4pt)
  #aod-xy-plot(
    x0: 7.36,
    y0: 1.44,
    w: 7.14,
    h: 5.56,
    pad: (left: 1.15, right: 0.28, top: 0.68, bottom: 0.98),
    title: [(b) Electron current vs enclosing Stokes sum (cuts $52..55$)],
    title-size: 7.7pt,
    xlabel: [Discrete integer cut $k in \{52, 53, 54, 55\}$],
    ylabel: [Oriented SADAR current],
    xlim: (51.6, 55.4),
    ylim: (-1.5, 15.0),
    xticks: (52, 53, 54, 55),
    yticks: (0, 4, 8, 13),
    x-tick-size: 6.9pt,
    y-tick-size: 6.9pt,
    ylabel-dx: 0.84,
    layers: (
      (type: "hline", y: 0.0, stroke: (paint: aod-pal.slate, thickness: 0.75pt, dash: "dashed")),
      (type: "line", xs: xs, ys: ys-cur, stroke: 1.3pt + aod-pal.blue, marker: "circle", marker-color: aod-pal.blue, marker-r: 2.5),
      (type: "line", xs: xs, ys: ys-union, stroke: 1.2pt + aod-pal.crimson, marker: "cross", marker-color: aod-pal.crimson, marker-r: 2.5),
    ),
    legend: (
      pos: "top-left",
      cols: 1,
      col-w: 4.15,
      size: 6.8pt,
      items: (
        (kind: "line", color: aod-pal.blue, marker: "circle", label: [Electron current $(4, 4, 8, 13)$]),
        (kind: "line", color: aod-pal.crimson, marker: "cross", label: [Union boundary $partial(R_w union R_e) = 0$]),
      ),
    ),
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vectors RC-030 & RC-031: exact moving-boundary balance $Phi^D_(upright("mov")) = 7$, union cancellation $+4 - 4 = 0$, and operative trajectory $4 -> 4 -> 8 -> 13$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
