// Authored native Typst vector figure: wire-moving-boundary-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.1
#let y-off = 0.54

#let rows = csv("/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv", row-type: dictionary)
#let r-mov = rows.at(0)
#let w-rows = rows.slice(1)
#let xs = w-rows.map(r => float(r.cut))
#let ys-cur = w-rows.map(r => float(r.later_electron_current))
#let ys-union = w-rows.map(r => float(r.union_boundary))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Moving-boundary Stokes balance & scoped $1":"2":"6$ electron-above-wire SADAR walk],
    subtitle: [Active $5$-boundary spine $B_(upright("wire")) -> B_(e) -> B_(upright("int")) -> B_(upright("union")) -> B_(upright("ext"))$: internal pair cancels in union while electron current grows.],
    top-y: 0.28,
    pad-x: 0.35,
    title-size: 9.4pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.14,
  )

  // Panel A (Left): Moving-Boundary R_1 -> R_2 Stokes Decomposition
  #aod-box-tl(0.38, 1.34 + y-off, 6.70, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.73, 1.64 + y-off, [*(a) Moving boundary $R_1 -> R_2$: $Phi^D_(upright("mov")) = #r-mov.Phi_moving$*], size: 7.9pt, box-w: 6.3, box-h: 0.34)

  // Region R_1 expanding to R_2 via swept strip Delta R (clean label top band + 3 arrow lanes)
  #aod-box-tl(0.62, 2.02 + y-off, 1.94, 2.16, [], stroke: 1.05pt + aod-pal.navy, fill: white, radius: 3pt)
  #aod-text(1.59, 2.30 + y-off, [*$R_1$*], size: 7.6pt, box-w: 1.7, box-h: 0.28)
  #aod-box-tl(2.56, 2.02 + y-off, 1.90, 2.16, [], stroke: (paint: aod-pal.purple, thickness: 1.05pt, dash: "dashed"), fill: aod-pal.tint-purple, radius: 3pt)
  #aod-text(3.51, 2.30 + y-off, [*$Delta R$ sweep*], size: 7.1pt, box-w: 1.75, box-h: 0.28)

  // Lane 1: Crossing (+8) across partial R_1 -> Delta R
  #aod-text(1.40, 2.86 + y-off, [$Phi_(upright("cross")) = +#r-mov.Phi_cross$], size: 6.8pt, weight: "bold", box-w: 1.50, box-h: 0.28)
  #aod-arrow(2.16, 2.86 + y-off, 3.24, 2.86 + y-off, stroke: 1.15pt + aod-pal.blue)

  // Lane 2: Sweep (-3) inward from right edge of Delta R
  #aod-arrow(4.36, 3.36 + y-off, 3.20, 3.36 + y-off, stroke: 1.15pt + aod-pal.purple)
  #aod-text(4.58, 3.36 + y-off, [$-Phi_(upright("sweep")) = -#r-mov.Phi_sweep$], size: 6.8pt, weight: "bold", anchor: "left", box-w: 2.36, box-h: 0.28)

  // Lane 3: Shedding (+2) wavy emission outward from Delta R
  #aod-wavy-arrow(3.48, 3.88 + y-off, 4.86, 3.88 + y-off, amp: 0.05, waves: 2.5, stroke: 1.05pt + aod-pal.orange)
  #aod-text(4.96, 3.88 + y-off, [$+Phi_(upright("shed")) = +#r-mov.Phi_shedding$], size: 6.8pt, weight: "bold", anchor: "left", box-w: 2.04, box-h: 0.28)

  #aod-box-tl(
    0.62, 4.46 + y-off, 6.22, 2.44,
    [#text(size: 6.9pt)[
      *Moving-boundary & wire-electron laws:* \
      *(1)* Moving-boundary balance: $Phi^D_(upright("mov")) = #r-mov.Phi_cross - #r-mov.Phi_sweep + #r-mov.Phi_shedding = #r-mov.Phi_moving$ ($!= 8$, falsifying static-boundary omission of sweep and shedding). \
      *(2)* Scoped wire-electron encounter (cuts $52..55$): wire $+4, 0, +4, +5$ and electron $-4, 0, -4, -5$ cancel on $partial(R_(upright("wire")) union R_e) = 0$, while realized electron current advances $4 -> 4 -> 8 -> 13$ (held constant at uncoupled cut $53$).
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    align-mode: left + horizon,
    inset: 4.5pt,
    leading: 0.36em,
  )

  // Panel B (Right): 4-Cut Electron Current vs Union Boundary Cancellation Plot
  #aod-box-tl(7.28, 1.34 + y-off, 7.32, 5.78, [], stroke: 0.85pt + aod-pal.teal, fill: white, radius: 4pt)
  #aod-text(10.94, 1.64 + y-off, [*(b) Electron current vs enclosing Stokes sum (cuts $52..55$)*], size: 7.1pt, box-w: 7.10, box-h: 0.34)
  #aod-xy-plot(
    x0: 7.36,
    y0: 1.44 + y-off,
    w: 7.14,
    h: 5.56,
    pad: (left: 1.06, right: 0.36, top: 0.68, bottom: 0.98),
    title: none,
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
    0.38, 7.88, 14.22, 0.76,
    [#text(size: 7.1pt, weight: "bold")[Engine vector RC-032: exact moving-boundary balance $Phi^D_(upright("mov")) = 7$, union cancellation $+4 - 4 = 0$, and operative trajectory $4 -> 4 -> 8 -> 13$.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
