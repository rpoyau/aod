// Audited S1b native Typst vector figure: cycle-disturbance-shedding (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (visually audited in S1b-0; zero empirical dataset)
// Historical raster retained byte-for-byte: figures_jpg/cycle_disturbance_shedding.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 7.6

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Title & subtitle
  #aod-text(7.3, 0.40, [*Temporal-cycle disturbance and sheddic routing*], size: 11.5pt, box-w: 14.0, box-h: 0.55)
  #aod-text(7.3, 0.82, [duon current $->$ disturbance span $->$ temporal SADAR burden $->$ shedding $->$ sheddic path], size: 8.0pt, box-w: 14.0, box-h: 0.45)

  // Five numbered stage boxes (badges cleanly offset from titles)
  #let stages = (
    (0.30, "1", [*Temporal cycle group*], [segment of duon current]),
    (3.16, "2", [*Lead-lag span*], [asymmetric return extent]),
    (6.02, "3", [*Temporal SADAR burden*], [duration and chiral mismatch]),
    (8.88, "4", [*Shedding*], [parent surplus process]),
    (11.74, "5", [*Sheddic path*], [endo / exo / redirected / open]),
  )
  #for i in range(stages.len()) {
    let (sx, snum, stitle, ssub) = stages.at(i)
    aod-box-tl(sx, 1.24, 2.56, 1.54, [], stroke: 0.95pt + aod-pal.navy, fill: white, radius: 3.5pt)
    aod-badge(sx + 0.24, 1.48, snum, r: 0.155, fill: aod-pal.tint-blue, stroke: 0.85pt + aod-pal.navy)
    aod-text(sx + 1.45, 1.72, stitle, size: 7.2pt, box-w: 1.96, box-h: 0.58)
    aod-text(sx + 1.28, 2.38, ssub, size: 6.8pt, box-w: 2.38, box-h: 0.52)
    if i < 4 {
      aod-arrow(sx + 2.60, 2.01, sx + 2.83, 2.01, stroke: 0.95pt + aod-pal.slate, head-len: 4.0, head-half: 1.9)
    }
  }

  // Row 2: Five visual motif icons cleanly aligned beneath stages 1-5
  // 1. Duon current wave/helix
  #let wpts = range(61).map(k => {
    let t = k / 60.0
    let ang = t * 5.0 * 360.0 * 1deg
    (0.88 + t * 1.40 + 0.08 * calc.cos(ang), 4.10 - 0.16 * calc.sin(ang))
  })
  #let wsegs = (curve.move((wpts.at(0).at(0) * 1cm, wpts.at(0).at(1) * 1cm)),)
  #for k in range(1, wpts.len()) {
    wsegs.push(curve.line((wpts.at(k).at(0) * 1cm, wpts.at(k).at(1) * 1cm)))
  }
  #place(top + left, curve(stroke: 1.1pt + aod-pal.blue, ..wsegs))

  // 2. Lead-lag span opposing arrows
  #aod-arrow(3.85, 3.96, 4.95, 3.96, stroke: 1.2pt + aod-pal.orange)
  #aod-arrow(5.05, 4.22, 3.95, 4.22, stroke: 1.2pt + aod-pal.purple)
  #aod-text(4.44, 4.52, [span], size: 7.4pt, box-w: 1.5, box-h: 0.35)

  // 3. Concentric dashed temporal SADAR burden + arrow
  #for rr in (0.18, 0.35, 0.52, 0.68) {
    aod-circle(7.05, 4.10, rr, fill: none, stroke: (paint: aod-pal.slate, thickness: 0.75pt, dash: "dashed"))
  }
  #aod-text(7.05, 4.98, [$P_W^S$], size: 8.2pt, box-w: 1.2, box-h: 0.4)
  #aod-arrow(7.86, 4.10, 8.50, 4.10, stroke: 1.0pt + aod-pal.slate)

  // 4. Shedding bifurcation (exo / reclose)
  #aod-circle(9.58, 4.10, 0.24, fill: white, stroke: 1.15pt + aod-pal.purple)
  #aod-arrow(9.80, 4.00, 10.62, 3.56, stroke: 1.15pt + aod-pal.orange)
  #aod-arrow(9.80, 4.20, 10.62, 4.64, stroke: 1.15pt + aod-pal.blue)
  #aod-text(10.68, 3.44, [exo], size: 7.4pt, anchor: "left", box-w: 1.0, box-h: 0.35)
  #aod-text(10.68, 4.74, [reclose], size: 7.4pt, anchor: "left", box-w: 1.2, box-h: 0.35)

  // 5. Sheddic path chain
  #for k in range(4) {
    aod-circle(12.30 + k * 0.38, 3.84, 0.11, fill: white, stroke: 1.0pt + aod-pal.purple)
  }
  #aod-arrow(12.15, 4.25, 13.85, 4.25, stroke: (paint: aod-pal.slate, thickness: 1.0pt, dash: "dashed"))
  #aod-text(13.00, 4.55, [sheddic path], size: 7.4pt, box-w: 2.2, box-h: 0.38)

  // Bottom formula card
  #aod-box-tl(
    0.45, 5.45, 13.70, 1.80,
    [
      #text(size: 8.6pt)[$P_W^S (partial F, omega) = sum_(e in W) C_(3,e) rho_(omega,e)^D (partial F, omega) abs(Delta_e^(chi upright("lag")))$]
      #v(4pt)
      #text(size: 8.4pt)[$X_upright("shedding") = max(0, P_W^S - C_W^upright("close")) quad | quad upright("SheddicPath")(X_upright("shedding")) quad | quad X_W^upright("out") = (1 - lambda_upright("reclose")) X_upright("shedding")$]
    ],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 4pt,
  )
]
