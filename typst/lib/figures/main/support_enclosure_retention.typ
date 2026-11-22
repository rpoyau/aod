// Audited S1b native Typst vector figure: support-enclosure-retention (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_curl_support_figures.py)
// Historical raster retained byte-for-byte: figures_jpg/support_enclosure_retention.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 8.2

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Title & subtitle
  #aod-text(7.3, 0.42, [*Seat-compatible retention and outer path*], size: 11.5pt, box-w: 14.0, box-h: 0.55)
  #aod-text(7.3, 0.84, [inner enclosure $->$ support enclosure $->$ retained $T T L_cal(C)$ or sheddic path], size: 8.2pt, box-w: 14.0, box-h: 0.45)

  // Four stage boxes + concentric seat-ring diagrams directly below
  #let panels = (
    (0.45, [*$E_4$ tetron*], [inner four-seat enclosure], 4, 0.42),
    (4.00, [*$C_6$ hexon*], [first outer enclosure], 6, 0.56),
    (7.55, [*$C_8$ octon*], [lifted outer path], 8, 0.70),
    (11.10, [*$C_(10)$ decon*], [higher outer path], 10, 0.84),
  )
  #for i in range(panels.len()) {
    let (px, pt, ps, pn, pr) = panels.at(i)
    aod-box-tl(px, 1.30, 3.05, 1.12, [#text(size: 8.6pt)[#pt] \ #v(2pt) #text(size: 7.4pt)[#ps]], stroke: 0.95pt + aod-pal.navy, fill: white)
    if i < 3 {
      aod-arrow(px + 3.10, 1.86, px + 3.50, 1.86, stroke: 0.95pt + aod-pal.slate)
    }
    let cx = px + 1.525
    let cy = 3.72
    aod-circle(cx, cy, 0.24, fill: none, stroke: 1.05pt + aod-pal.purple)
    aod-seat-ring(cx, cy, pr, pn, ring-stroke: 1.25pt + aod-pal.gold, seat-r: 0.058)
  }

  // Retention held vs shorter than window branch boxes
  #aod-box-tl(
    0.75, 4.96, 6.20, 1.38,
    [#text(size: 8.3pt, weight: "bold")[retention held over window] \ #text(size: 7.8pt)[$T T L_cal(C)(partial F, omega) >= abs(omega)$] \ #text(size: 7.4pt)[route retained over window]],
    stroke: 0.95pt + aod-pal.green,
    fill: aod-pal.tint-green,
    radius: 3.5pt,
    inset: 4pt,
  )
  #aod-arrow(1.35, 6.58, 6.35, 6.58, stroke: 1.35pt + aod-pal.green)

  #aod-box-tl(
    7.65, 4.96, 6.20, 1.38,
    [#text(size: 8.3pt, weight: "bold")[retention shorter than window] \ #text(size: 7.8pt)[$T T L_cal(C)(partial F, omega) < abs(omega)$] \ #text(size: 7.4pt)[route continues / re-entry / reclosure]],
    stroke: 0.95pt + aod-pal.orange,
    fill: aod-pal.tint-orange,
    radius: 3.5pt,
    inset: 4pt,
  )
  #aod-arrow(8.25, 6.58, 13.25, 6.58, stroke: 1.35pt + aod-pal.orange)

  // Bottom formula bar
  #aod-box-tl(
    0.75, 6.95, 13.10, 0.85,
    [#text(size: 8.2pt)[$X_cal(C)(B) = op("route")_cal(C)(X_upright("shedding")(B)), wide upright("SheddicPath")(X_upright("shedding")) in {E_2, upright("C")_6, upright("C")_8, upright("C")_(10), dots, upright("C")_(2 n)}$]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
  )
]
