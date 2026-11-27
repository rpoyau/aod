// Authored native Typst vector figure: cell-staircase-fold-boundary (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.2

#let rows = csv("/manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv", row-type: dictionary)
#let parse-rat(s) = {
  let t = str(s).trim()
  if "/" in t {
    let parts = t.split("/")
    float(parts.at(0)) / float(parts.at(1))
  } else {
    float(t)
  }
}

#let ks = rows.map(r => calc.log(float(r.n), base: 2))
#let x-ticks-n = rows.map(r => (calc.log(float(r.n), base: 2), [#r.n]))
#let ys-a-lo = rows.map(r => parse-rat(r.A_minus_exact))
#let ys-a-hi = rows.map(r => parse-rat(r.A_plus_exact))
#let ys-pi-lo = rows.map(r => parse-rat(r.pi_4d_lower_exact))
#let ys-pi-hi = rows.map(r => parse-rat(r.pi_4d_upper_exact))
#let ys-4v4-lo = rows.map(r => 4.0 * parse-rat(r.V4_minus_exact))
#let ys-4v4-hi = rows.map(r => 4.0 * parse-rat(r.V4_plus_exact))
#let ys-b3-stair = rows.map(r => parse-rat(r.B3_staircase_exact))
#let ys-b3-box = rows.map(r => parse-rat(r.B3_tesseract_box))
#let r32 = rows.at(rows.len() - 1)

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Outer border and title header
  #aod-box-tl(0.12, 0.12, 14.76, 8.96, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.40, [*4D Tesseract-to-$pi$ Microcell Enclosure, 3-Boundary Staircase & Fold Chain Law*], size: 8.6pt, box-w: 14.4, box-h: 0.40)
  #aod-text(7.50, 0.78, [Five-boundary spine $B_(upright("cell")) -> B_(upright("stair")) -> B_(upright("fold")) -> B_(upright("audit")) -> B_(upright("ext"))$: exact integer counts in $B_(upright("core"))$ without Machin $pi$ smuggled.], size: 6.9pt, box-w: 14.4, box-h: 0.34)

  // =========================================================================
  // Panel (a) top-left: Projected 4D Schlegel tesseract + microcell B^4 slice
  // =========================================================================
  #aod-box-tl(0.28, 1.02, 4.44, 3.52, [], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-text(2.50, 1.22, [*(a) 4D tesseract $B^4$ microcells*], size: 7.3pt, box-w: 4.25, box-h: 0.30)

  #{
    let cx = 2.46
    let cy = 2.82
    let cell-r = 0.72
    let step = cell-r / 4.0

    // Exact n=4 equatorial microcells inside [-1,1]^2 slice of [-1,1]^4
    // Outer cells: i^2 + j^2 < 16; Inner cells: (i+1)^2 + (j+1)^2 <= 16
    for sx in (-1.0, 1.0) {
      for sy in (-1.0, 1.0) {
        for i in range(4) {
          for j in range(4) {
            let min-r2 = i * i + j * j
            let max-r2 = (i + 1) * (i + 1) + (j + 1) * (j + 1)
            if min-r2 < 16 {
              let x-left = if sx > 0 { cx + i * step } else { cx - (i + 1) * step }
              let y-top = if sy > 0 { cy - (j + 1) * step } else { cy + j * step }
              let is-in = max-r2 <= 16
              let fl = if is-in { aod-pal.tint-green } else { aod-pal.tint-blue }
              let st = if is-in { 0.45pt + aod-pal.teal } else { 0.45pt + aod-pal.blue }
              place(top + left, dx: x-left * 1cm, dy: y-top * 1cm, rect(width: step * 1cm, height: step * 1cm, fill: fl, stroke: st))
            }
          }
        }
      }
    }

    // Projected 4D Schlegel tesseract [-1,1]^4 wireframe (outer 3-cube + inner 3-cube + 8 struts)
    let cube-pts(s, ox, oy) = range(8).map(u => {
      let bx = if calc.rem(u, 2) == 1 { 1.0 } else { -1.0 }
      let by = if calc.rem(calc.quo(u, 2), 2) == 1 { -1.0 } else { 1.0 }
      let bz = if calc.rem(calc.quo(u, 4), 2) == 1 { 1.0 } else { -1.0 }
      (cx + ox + (bx * 0.78 + bz * 0.28) * s, cy + oy + (by * 0.70 - bz * 0.22) * s)
    })
    let outer = cube-pts(0.96, 0.0, 0.0)
    let inner = cube-pts(0.37, 0.03, -0.02)
    let c-edges = (
      (0, 1), (2, 3), (4, 5), (6, 7),
      (0, 2), (1, 3), (4, 6), (5, 7),
      (0, 4), (1, 5), (2, 6), (3, 7),
    )
    for u in range(8) {
      let p1 = inner.at(u)
      let p2 = outer.at(u)
      aod-line(p1.at(0), p1.at(1), p2.at(0), p2.at(1), stroke: 0.50pt + aod-pal.slate)
    }
    for e in c-edges {
      let p1 = inner.at(e.at(0))
      let p2 = inner.at(e.at(1))
      aod-line(p1.at(0), p1.at(1), p2.at(0), p2.at(1), stroke: 0.65pt + aod-pal.purple)
    }
    for e in c-edges {
      let p1 = outer.at(e.at(0))
      let p2 = outer.at(e.at(1))
      aod-line(p1.at(0), p1.at(1), p2.at(0), p2.at(1), stroke: 0.85pt + aod-pal.navy)
    }
    for p in inner {
      aod-circle(p.at(0), p.at(1), 0.034, fill: aod-pal.purple, stroke: 0.3pt + white)
    }
    for p in outer {
      aod-circle(p.at(0), p.at(1), 0.042, fill: aod-pal.navy, stroke: 0.3pt + white)
    }
    // Inscribed 4-ball equatorial boundary B^4
    aod-circle(cx, cy, cell-r, fill: none, stroke: (paint: aod-pal.crimson, thickness: 1.05pt, dash: "dashed"))
  }

  // Panel (a) crisp perimeter callouts (all strictly outside wireframe)
  #aod-text(0.38, 1.56, [$[-1,1]^4$], size: 6.6pt, anchor: "left", box-w: 1.05, box-h: 0.28)
  #aod-line(1.10, 1.64, 1.71, 2.15, stroke: 0.55pt + aod-pal.navy)

  #aod-text(0.38, 2.46, [$V_(4,n)^+$], size: 6.6pt, anchor: "left", box-w: 0.85, box-h: 0.28)
  #aod-line(0.92, 2.48, 1.76, 2.48, stroke: 0.55pt + aod-pal.blue)

  #aod-text(0.38, 3.16, [$V_(4,n)^-$], size: 6.6pt, anchor: "left", box-w: 0.85, box-h: 0.28)
  #aod-line(0.92, 3.14, 1.98, 3.04, stroke: 0.55pt + aod-pal.teal)

  #aod-text(4.62, 1.54, [$B_(3,upright("box")) = 64$], size: 6.6pt, anchor: "right", box-w: 1.40, box-h: 0.28)
  #aod-line(3.86, 1.72, 3.52, 1.94, stroke: 0.55pt + aod-pal.navy)

  #aod-text(4.62, 2.76, [$B^4$], size: 6.6pt, anchor: "right", box-w: 0.65, box-h: 0.28)
  #aod-line(4.24, 2.76, 3.20, 2.76, stroke: 0.55pt + aod-pal.crimson)

  #aod-text(4.62, 3.74, [side $1 slash n$], size: 6.6pt, anchor: "right", box-w: 1.15, box-h: 0.28)

  #aod-text(2.50, 4.30, [$(2n)^4$ cells: $V_(4,n)^- subset B^4 subset V_(4,n)^+ subset [-1,1]^4$], size: 6.6pt, box-w: 4.30, box-h: 0.28)

  // =========================================================================
  // Panel (b) top-middle: Pure 4D pi_4D & 2D A_2 dyadic convergence
  // =========================================================================
  #aod-box-tl(4.86, 1.02, 5.02, 3.52, [], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-text(7.37, 1.20, [*(b) 4D $pi_(upright("4D"),n)^plus.minus$ & 2D $A_(2,n)^plus.minus$ convergence*], size: 7.2pt, box-w: 4.88, box-h: 0.28)

  // Manual above-plot legend strip for Panel (b) (clear vertical separation)
  #aod-line(5.04, 1.54, 5.38, 1.54, stroke: 1.2pt + aod-pal.blue)
  #aod-marker(5.21, 1.54, kind: "circle", r-pt: 1.8, color: aod-pal.blue)
  #aod-text(5.44, 1.54, [$pi_(upright("4D"),n)^+$], size: 6.6pt, anchor: "left", box-w: 1.05, box-h: 0.26)

  #aod-line(6.54, 1.54, 6.88, 1.54, stroke: (paint: aod-pal.orange, thickness: 1.1pt, dash: "dashed"))
  #aod-marker(6.71, 1.54, kind: "cross", r-pt: 1.8, color: aod-pal.orange)
  #aod-text(6.94, 1.54, [$A_(2,n)^+$], size: 6.6pt, anchor: "left", box-w: 0.95, box-h: 0.26)

  #aod-line(7.96, 1.54, 8.30, 1.54, stroke: (paint: aod-pal.crimson, thickness: 1.0pt, dash: "densely-dotted"))
  #aod-text(8.36, 1.54, [$pi$ ($B_(upright("ext"))$)], size: 6.6pt, anchor: "left", box-w: 1.40, box-h: 0.26)

  #aod-line(5.04, 1.82, 5.38, 1.82, stroke: 1.2pt + aod-pal.purple)
  #aod-marker(5.21, 1.82, kind: "open-circle", r-pt: 1.8, color: aod-pal.purple)
  #aod-text(5.44, 1.82, [$pi_(upright("4D"),n)^-$], size: 6.6pt, anchor: "left", box-w: 1.05, box-h: 0.26)

  #aod-line(6.54, 1.82, 6.88, 1.82, stroke: (paint: aod-pal.teal, thickness: 1.1pt, dash: "dashed"))
  #aod-marker(6.71, 1.82, kind: "open-circle", r-pt: 1.8, color: aod-pal.teal)
  #aod-text(6.94, 1.82, [$A_(2,n)^-$], size: 6.6pt, anchor: "left", box-w: 0.95, box-h: 0.26)

  #aod-xy-plot(
    x0: 4.92,
    y0: 1.98,
    w: 4.90,
    h: 2.52,
    pad: (left: 0.90, right: 0.42, top: 0.08, bottom: 0.60),
    xlabel: none,
    ylabel: none,
    xlim: (-0.25, 5.25),
    ylim: (0.0, 6.4),
    xticks: x-ticks-n,
    yticks: (0, 2, 4, 6),
    x-tick-size: 6.7pt,
    y-tick-size: 6.7pt,
    x-tick-dy: 0.20,
    layers: (
      (type: "hline", y: calc.pi, stroke: (paint: aod-pal.crimson, thickness: 0.95pt, dash: "densely-dotted")),
      (type: "line", xs: ks, ys: ys-pi-hi, stroke: 1.2pt + aod-pal.blue, marker: "circle", marker-color: aod-pal.blue, marker-r: 2.0),
      (type: "line", xs: ks, ys: ys-pi-lo, stroke: 1.2pt + aod-pal.purple, marker: "open-circle", marker-color: aod-pal.purple, marker-r: 2.0),
      (type: "line", xs: ks, ys: ys-a-hi, stroke: (paint: aod-pal.orange, thickness: 1.05pt, dash: "dashed"), marker: "cross", marker-color: aod-pal.orange, marker-r: 1.9),
      (type: "line", xs: ks, ys: ys-a-lo, stroke: (paint: aod-pal.teal, thickness: 1.05pt, dash: "dashed"), marker: "open-circle", marker-color: aod-pal.teal, marker-r: 1.9),
    ),
  )
  // Compact Panel (b) axis titles & right-edge pi reference tick label
  #aod-text(7.61, 4.36, [Dyadic level $n$], size: 7.0pt, box-w: 3.6, box-h: 0.28)
  #aod-text(5.16, 2.98, [Enclosure], size: 7.0pt, box-w: 2.0, box-h: 0.28, angle: -90deg)
  #{
    let pb = 1.98 + 2.52 - 0.60
    let ph = 2.52 - 0.08 - 0.60
    let y-pi = pb - (calc.pi / 6.4) * ph
    aod-text(9.46, y-pi, [$pi$], size: 6.7pt, anchor: "left", box-w: 0.36, box-h: 0.26)
  }

  // =========================================================================
  // Panel (c) bottom-left: 4 V_4 -> 2 pi^2 vs B_3,stair -> 32 pi/3 & box 64
  // =========================================================================
  #aod-box-tl(0.28, 4.68, 9.60, 3.52, [], stroke: 0.85pt + aod-pal.navy, fill: white, radius: 4pt)
  #aod-text(5.08, 4.90, [*(c) 4D volume $4 V_(4,n)^plus.minus -> 2 pi^2$ vs exposed staircase $B_(3,upright("stair"),n)^+ -> 32 pi slash 3$ & box $64$*], size: 7.0pt, box-w: 9.40, box-h: 0.30)

  // Manual above-plot legend strip for Panel (c) (well clear below single-line title)
  #aod-line(0.56, 5.24, 0.96, 5.24, stroke: (paint: aod-pal.gold, thickness: 1.2pt, dash: "dashed"))
  #aod-text(1.03, 5.24, [$B_(3,upright("box")) = 64$], size: 6.6pt, anchor: "left", box-w: 1.65, box-h: 0.26)

  #aod-line(2.86, 5.24, 3.26, 5.24, stroke: 1.25pt + aod-pal.crimson)
  #aod-marker(3.06, 5.24, kind: "cross", r-pt: 2.0, color: aod-pal.crimson)
  #aod-text(3.33, 5.24, [$B_(3,upright("stair"),n)^+ = 8 V_(3,n)^+$], size: 6.6pt, anchor: "left", box-w: 2.40, box-h: 0.26)

  #aod-line(5.90, 5.24, 6.30, 5.24, stroke: 1.2pt + aod-pal.blue)
  #aod-marker(6.10, 5.24, kind: "circle", r-pt: 1.9, color: aod-pal.blue)
  #aod-text(6.37, 5.24, [$4 V_(4,n)^+$], size: 6.6pt, anchor: "left", box-w: 1.20, box-h: 0.26)

  #aod-line(7.72, 5.24, 8.12, 5.24, stroke: 1.2pt + aod-pal.teal)
  #aod-marker(7.92, 5.24, kind: "open-circle", r-pt: 1.9, color: aod-pal.teal)
  #aod-text(8.19, 5.24, [$4 V_(4,n)^-$], size: 6.6pt, anchor: "left", box-w: 1.20, box-h: 0.26)

  #aod-xy-plot(
    x0: 0.34,
    y0: 5.40,
    w: 9.48,
    h: 2.76,
    pad: (left: 1.05, right: 2.38, top: 0.12, bottom: 0.62),
    xlabel: none,
    ylabel: none,
    xlim: (-0.25, 5.25),
    ylim: (0.0, 68.0),
    xticks: x-ticks-n,
    yticks: (0, 20, 40, 60),
    x-tick-size: 6.7pt,
    y-tick-size: 6.7pt,
    x-tick-dy: 0.19,
    layers: (
      (type: "hline", y: 32.0 * calc.pi / 3.0, stroke: (paint: aod-pal.crimson, thickness: 0.75pt, dash: "dotted")),
      (type: "hline", y: 2.0 * calc.pi * calc.pi, stroke: (paint: aod-pal.blue, thickness: 0.75pt, dash: "dotted")),
      (type: "line", xs: ks, ys: ys-b3-box, stroke: (paint: aod-pal.gold, thickness: 1.2pt, dash: "dashed")),
      (type: "line", xs: ks, ys: ys-b3-stair, stroke: 1.3pt + aod-pal.crimson, marker: "cross", marker-color: aod-pal.crimson, marker-r: 2.1),
      (type: "line", xs: ks, ys: ys-4v4-hi, stroke: 1.2pt + aod-pal.blue, marker: "circle", marker-color: aod-pal.blue, marker-r: 2.0),
      (type: "line", xs: ks, ys: ys-4v4-lo, stroke: 1.2pt + aod-pal.teal, marker: "open-circle", marker-color: aod-pal.teal, marker-r: 2.0),
    ),
  )
  // Panel (c) axis labels
  #aod-text(4.42, 8.00, [Dyadic refinement level $n in {1, 2, 4, 8, 16, 32}$], size: 7.0pt, box-w: 6.2, box-h: 0.28)
  #aod-text(0.66, 6.53, [Measure ($r = 1 u$)], size: 7.0pt, box-w: 2.4, box-h: 0.28, angle: -90deg)

  // Panel (c) right-margin asymptotic labels with >= 0.45 cm vertical clearance
  // Plot box: pr = 7.44, pt = 5.52, pb = 7.54, ph = 2.02
  #{
    let pr = 7.44
    let pb = 7.54
    let ph = 2.02
    let my(v) = pb - (v / 68.0) * ph
    let y-box = my(64.0)
    let y-stair = my(32.0 * calc.pi / 3.0)
    let y-vol = my(2.0 * calc.pi * calc.pi)
    let lbl-stair = y-stair - 0.12
    let lbl-vol = y-vol + 0.02
    aod-line(pr, y-box, pr + 0.14, y-box, stroke: 0.65pt + aod-pal.gold)
    aod-text(pr + 0.18, y-box, [$B_(3,upright("box")) = 64$], size: 6.6pt, anchor: "left", box-w: 2.20, box-h: 0.26)

    aod-line(pr, y-stair, pr + 0.14, lbl-stair, stroke: 0.65pt + aod-pal.crimson)
    aod-text(pr + 0.18, lbl-stair, [$32 pi slash 3 approx 33.51$], size: 6.6pt, anchor: "left", box-w: 2.22, box-h: 0.26)

    aod-line(pr, y-vol, pr + 0.14, lbl-vol, stroke: 0.65pt + aod-pal.blue)
    aod-text(pr + 0.18, lbl-vol, [$2 pi^2 approx 19.74$], size: 6.6pt, anchor: "left", box-w: 2.20, box-h: 0.26)

    aod-text(pr + 0.18, 7.44, [$Delta_(32) = #r32.B3_stair_minus_4V4plus$], size: 6.6pt, anchor: "left", box-w: 2.22, box-h: 0.26)
  }

  // =========================================================================
  // Panel (d) right: Two-square cellular fold chain map & falsifier audit card
  // =========================================================================
  #aod-box-tl(10.04, 1.02, 4.68, 7.18, [], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(12.38, 1.22, [*(d) Cellular fold chain map*], size: 7.3pt, box-w: 4.45, box-h: 0.28)
  #aod-text(12.38, 1.47, [$B_d^L F_d = F_(d-1) B_d^K$ ($x arrow.r.bar min(x, 2 - x)$)], size: 6.6pt, box-w: 4.45, box-h: 0.26)

  // Pre-fold K_2 = Q_L cup Q_R
  #aod-text(12.38, 1.72, [shared seam $+1 - 1 = 0$], size: 6.6pt, box-w: 3.4, box-h: 0.24)
  #aod-box-tl(10.88, 1.88, 1.50, 0.92, [], stroke: 1.0pt + aod-pal.blue, fill: aod-pal.tint-blue, radius: 0pt)
  #aod-box-tl(12.38, 1.88, 1.50, 0.92, [], stroke: 1.0pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 0pt)
  #aod-line(12.38, 1.88, 12.38, 2.80, stroke: (paint: aod-pal.crimson, thickness: 1.25pt, dash: "dashed"))
  // CCW orientation arcs inside Q_L and Q_R
  #aod-arc-arrow(11.63, 2.34, 0.31, 25.0, 325.0, stroke: 0.85pt + aod-pal.blue, head-len: 3.0, head-half: 1.4)
  #aod-text(11.63, 2.34, [$+Q_L$], size: 6.6pt, weight: "bold", box-w: 0.70, box-h: 0.26)
  #aod-arc-arrow(13.13, 2.34, 0.31, 25.0, 325.0, stroke: 0.85pt + aod-pal.teal, head-len: 3.0, head-half: 1.4)
  #aod-text(13.13, 2.34, [$+Q_R$], size: 6.6pt, weight: "bold", box-w: 0.70, box-h: 0.26)
  // Axis vertices & K_2 summary
  #aod-text(10.88, 2.95, [$x=0$], size: 6.6pt, box-w: 0.85, box-h: 0.24)
  #aod-text(12.38, 2.95, [$x=1$], size: 6.6pt, box-w: 0.85, box-h: 0.24)
  #aod-text(13.88, 2.95, [$x=2$], size: 6.6pt, box-w: 0.85, box-h: 0.24)
  #aod-text(12.38, 3.18, [Pre-fold $K_2$: area $2 u^2$, exposed $partial = 6 u$], size: 6.6pt, box-w: 4.40, box-h: 0.24)

  // Fold arrow F from K_2 to L_2 = Q_*
  #aod-arrow(11.24, 3.33, 11.24, 3.85, stroke: 1.15pt + aod-pal.purple)
  #aod-text(11.06, 3.59, [$F$], size: 7.0pt, weight: "bold", anchor: "right", box-w: 0.55, box-h: 0.26)
  #aod-text(11.46, 3.45, [$F_2(Q_L) = +Q_*$], size: 6.6pt, anchor: "left", box-w: 2.95, box-h: 0.24)
  #aod-text(11.46, 3.73, [$F_2(Q_R) = -Q_*$ (orient. rev.)], size: 6.6pt, anchor: "left", box-w: 3.15, box-h: 0.24)

  // Post-fold target L_2 = Q_* + retained-lineage summary
  #aod-box-tl(10.48, 3.92, 1.50, 0.92, [], stroke: 1.2pt + aod-pal.purple, fill: white, radius: 0pt)
  #aod-arc-arrow(11.23, 4.38, 0.32, 25.0, 165.0, stroke: 0.85pt + aod-pal.blue, head-len: 2.9, head-half: 1.4)
  #aod-arc-arrow(11.23, 4.38, 0.32, 335.0, 195.0, stroke: 0.85pt + aod-pal.crimson, head-len: 2.9, head-half: 1.4)
  #aod-text(11.23, 4.38, [$plus.minus Q_*$], size: 6.6pt, weight: "bold", box-w: 0.80, box-h: 0.26)

  #aod-box-tl(
    12.12, 3.92, 2.42, 0.92,
    [#text(size: 6.6pt)[
      Top: $F_2(K_2) = 0$ \
      Support: $1 u^2$, $partial = 4 u$ \
      Mult. $2$; lineage kept
    ]],
    stroke: 0.70pt + aod-pal.purple,
    fill: white,
    radius: 2pt,
    inset: 3pt,
    align-mode: left + horizon,
  )
  #aod-text(12.38, 5.04, [Exact commutation: $B_d^L F_d - F_(d-1) B_d^K = 0$], size: 6.6pt, box-w: 4.40, box-h: 0.24)

  // Boundary firewall & compact 4-point falsifier audit card
  #aod-boundary-wall(10.22, 5.26, 14.54, 5.26, stroke: 1.0pt + aod-pal.navy, hatch-side: 1, hatch-count: 8)
  #aod-box-tl(
    10.22, 5.48, 4.32, 2.60,
    [#text(size: 6.6pt)[
      *Falsifier audit ($B_(upright("audit"))$):* \
      *(1)* 4D: $B_(3,upright("stair"),32)^+ - 4 V_(4,32)^+ = #r32.B3_stair_minus_4V4plus > 0$ ($!= 2 pi^2$). \
      *(2)* 2D: $C_(32) r - 2 A_(32)^+ = #r32.Cr_minus_2Aplus > 0$ ($C_n = 8$). \
      *(3)* Fold: mutating $F_2(Q_R)$ breaks $B_d^L F_d = F_(d-1) B_d^K$. \
      *(4)* Scope: Machin $pi$ stays in $B_(upright("ext"))$, never $B_(upright("core"))$.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    radius: 3pt,
    inset: 4pt,
    align-mode: left + horizon,
    leading: 0.38em,
  )

  // =========================================================================
  // Bottom invariant bar summarizing live RC-035 (n = 32) exact fractions
  // =========================================================================
  #aod-box-tl(0.28, 8.32, 14.44, 0.64, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 3pt)
  #aod-text(7.50, 8.50, [*RC-035 ($n = 32$):* $V_(4,32)^- = #r32.V4_minus_exact <= pi^2 slash 2 <= #r32.V4_plus_exact = V_(4,32)^+$ | $pi_(upright("4D"),32) in [#r32.pi_4d_lower_exact, #r32.pi_4d_upper_exact]$ | $B_(3,upright("stair"),32)^+ = #r32.B3_staircase_exact != 64$], size: 6.6pt, box-w: 14.25, box-h: 0.28)
  #aod-text(7.50, 8.78, [2D disk: $A_(32)^- = #r32.A_minus_exact <= pi <= #r32.A_plus_exact = A_(32)^+$ (width $#r32.enclosure_width$, $C_n = 8$) | Fold chain map: $B_d^L F_d = F_(d-1) B_d^K$ ($12$ negative controls verified).], size: 6.6pt, box-w: 14.25, box-h: 0.28)
]
