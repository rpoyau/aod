// Audited S1b native Typst vector figure: curling-curl-layers (Main)
// Provenance: CONCEPTUAL_SCHEMATIC (scripts/generate_curl_support_figures.py)
// Historical raster retained byte-for-byte: figures_jpg/curling_curl_layers.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.6
#let fig-height-cm = 8.8

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Title & subtitle
  #aod-text(7.3, 0.42, [*Curling-curl shell families*], size: 12pt, box-w: 14.0, box-h: 0.55)
  #aod-text(7.3, 0.84, [cycle $->$ inner enclosure $->$ core family $->$ outer shell path], size: 8.2pt, box-w: 14.0, box-h: 0.45)

  // Top layer taxonomy boxes
  #let top-boxes = (
    (0.35, [*Tetrion*], [four-cycle closure \ cycle term]),
    (3.92, [*Tetron*], [inner four-seat enclosure \ $E_4$]),
    (7.49, [*Core families*], [Dimonon 1:2 \ Tritrion 3:3 \ Tetratrion 3:4]),
    (11.06, [*Outer shell paths*], [hexon 6 \ octon 8 \ decon 10]),
  )
  #for i in range(top-boxes.len()) {
    let (bx, bt, bd) = top-boxes.at(i)
    aod-box-tl(bx, 1.14, 3.18, 1.56, [#text(size: 8.4pt)[#bt] \ #text(size: 7.4pt)[#bd]], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, inset: 4pt)
    if i < 3 {
      aod-arrow(bx + 3.22, 1.92, bx + 3.53, 1.92, stroke: 0.95pt + aod-pal.slate)
    }
  }

  // Row of 5 enclosed examples
  #let exs = (
    (0.35, [*Dimonhexon*], [1:2:6 \ hexon path]),
    (3.17, [*Dimonocton*], [1:2:8 \ octon path]),
    (5.99, [*Dimondecon*], [1:2:10 \ decon path]),
    (8.81, [*Tritriohexon*], [3:3:6 \ hexon path]),
    (11.63, [*Tetratriohexon*], [3:4:6 \ hexon path]),
  )
  #for (ex, et, ed) in exs {
    aod-box-tl(ex, 2.98, 2.62, 1.18, [#text(size: 8.1pt)[#et] \ #v(1pt) #text(size: 7.3pt)[#ed]], stroke: 0.85pt + aod-pal.blue, fill: white)
  }

  // Three distinct concentric seat-ring diagrams (non-overlapping labels below rings)
  #let rings = (
    (3.30, [*$C_6$ hexon*], 6, 0.56, [default closure]),
    (7.30, [*$C_8$ octon*], 8, 0.74, [lifted retention path]),
    (11.30, [*$C_(10)$ decon*], 10, 0.92, [lifted retention path]),
  )
  #let rcy = 5.75
  #for (rcx, rlbl, rn, rr, rsub) in rings {
    aod-text(rcx, 4.54, rlbl, size: 8.6pt, box-w: 3.0, box-h: 0.42)
    aod-circle(rcx, rcy, 0.24, fill: none, stroke: 1.0pt + aod-pal.purple)
    aod-circle(rcx, rcy, 0.42, fill: none, stroke: 0.95pt + aod-pal.blue)
    aod-seat-ring(rcx, rcy, rr, rn, ring-stroke: 1.25pt + aod-pal.gold, seat-r: 0.065)
    aod-text(rcx, 7.00, rsub, size: 7.4pt, box-w: 3.2, box-h: 0.38)
    aod-arrow(rcx - 1.35, 7.28, rcx + 1.35, 7.28, stroke: 1.1pt + aod-pal.orange)
  }

  // Bottom legend strip
  #aod-box-tl(
    0.45, 7.72, 13.70, 0.74,
    [#text(size: 7.8pt)[$alpha$ outward dressing  $|$  $Omega$ return dressing  $|$  polychiral return clocks  $|$  field outer dressing  $|$  retention-conditioned shell path]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
  )
]
