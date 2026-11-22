// Audited S1b native Typst vector figure: lensing-02-frg-value-identity-delta3 (Manual)
// Provenance: CONCEPTUAL_SCHEMATIC (manual/scripts/build_lensing_assets.py)
// Historical raster retained byte-for-byte: manual/figures/lensing/02_frg_value_identity_delta3.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.4
#let fig-height-cm = 6.5

#aod-canvas(fig-width-cm, fig-height-cm)[
  // Top value identity equation
  #aod-text(7.2, 0.66, [$T_k^times = T_k^0 + sum_((i, j) in E_upright("return")) C_(i j, k)^times (B_upright("lens"))$], size: 11.2pt, box-w: 13.4, box-h: 0.95)

  // Row 1 boxes
  #aod-box-tl(0.70, 1.55, 3.05, 1.25, [$T_k^0$ \ #text(size: 7.8pt)[independent gate sum]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
  #aod-box-tl(4.65, 1.55, 3.70, 1.25, [$C_(i j, k)^times (B_upright("lens"))$ \ #text(size: 7.8pt)[returned-current coupling]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
  #aod-box-tl(9.25, 1.55, 3.05, 1.25, [$T_k^times$ \ #text(size: 7.8pt)[recurrent value]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)

  #aod-arrow(3.80, 2.175, 4.60, 2.175, stroke: 1.0pt + aod-pal.axis)
  #aod-arrow(8.40, 2.175, 9.20, 2.175, stroke: 1.0pt + aod-pal.axis)

  // Diagonal arrow to residual row
  #aod-arrow(10.775, 2.83, 6.75, 4.02, stroke: 1.0pt + aod-pal.axis)

  // Row 2 boxes
  #aod-box-tl(5.15, 4.05, 3.05, 1.25, [$Delta_k^upright("Z")$ \ #text(size: 7.8pt)[integer residual]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
  #aod-box-tl(9.55, 4.05, 3.05, 1.25, [$delta_(3, k)$ \ #text(size: 7.8pt)[$(s_k^((3)), m_k)$]], stroke: 1.0pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 2pt)
  #aod-arrow(8.25, 4.675, 9.50, 4.675, stroke: 1.0pt + aod-pal.axis)

  // Bottom residual equations
  #aod-text(7.2, 5.95, [$Delta_k^upright("Z") = T_k^times - O_k, wide s_k^((3)) = op("sgn")(Delta_k^upright("Z")), wide m_k = abs(Delta_k^upright("Z"))$], size: 8.8pt, box-w: 13.4, box-h: 0.6)
]
