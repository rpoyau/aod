// Authored native Typst vector figure: solar-boundary-scopes-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.5

#let rows = csv("/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv", row-type: dictionary)
#let r-hg = rows.at(0)
#let r-bend = rows.at(1)
#let r-red = rows.at(2)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.20, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Solar O0 boundary scopes ($B_(upright("Hg")), B_(upright("bend")), B_(upright("red"))$), missing-producer gate & rational audit*], size: 9.8pt, box-w: 14.3, box-h: 0.46)
  #aod-text(7.50, 0.94, [Active $5$-boundary spine $B_(upright("Sun")) -> (B_(upright("Hg")), B_(upright("bend")), B_(upright("red"))) -> B_(upright("gate")) -> B_(upright("O0")) -> B_(upright("ext"))$: O0 observable-map audit held honest.], size: 7.3pt, box-w: 14.3, box-h: 0.38)

  // Panel A (Left): Solar support R_Sun + three typed boundary scopes + HOLD firewall
  #aod-box-tl(0.38, 1.34, 6.85, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-amber, radius: 4pt)
  #aod-text(3.80, 1.66, [*(a) Three typed solar boundary scopes & producer gate*], size: 7.9pt, box-w: 6.5, box-h: 0.36)

  // Central Solar support R_Sun
  #aod-chiral-vertex(2.15, 3.85, [$R_(upright("Sun"))$], r: 0.48, fill: white, stroke: 1.25pt + aod-pal.gold, text-size: 7.2pt)

  // 1. Mercury orbital return shell B_Hg (ellipse/circle arc)
  #aod-circle(2.15, 3.85, 1.18, fill: none, stroke: (paint: aod-pal.blue, thickness: 1.0pt, dash: "dashed"))
  #aod-text(2.15, 2.42, [$B_(upright("Hg"))$ orbital return shell], size: 6.8pt, weight: "bold", box-w: 3.2, box-h: 0.28)

  // 2. Grazing light-bending chord B_bend
  #aod-curve-arrow(0.72, 4.92, 2.15, 4.38, 4.55, 4.88, stroke: 1.1pt + aod-pal.purple)
  #aod-text(2.68, 5.26, [$B_(upright("bend"))$ grazing ray chord], size: 6.8pt, weight: "bold", box-w: 3.3, box-h: 0.28)

  // 3. Radial climb window B_red
  #aod-wavy-arrow(2.66, 3.70, 4.55, 3.12, amp: 0.05, waves: 3.0, stroke: 1.05pt + aod-pal.teal)
  #aod-text(3.82, 3.68, [$B_(upright("red"))$ climb], size: 6.8pt, weight: "bold", box-w: 1.9, box-h: 0.28)

  // Honest HOLD_MISSING_NATIVE_SOLAR_PRODUCER boundary wall
  #aod-boundary-wall(4.85, 2.08, 4.85, 5.56, stroke: 1.25pt + aod-pal.crimson, hatch-side: 1, hatch-count: 8, double-line: true)
  #aod-box-tl(
    5.06, 2.22, 1.96, 3.28,
    [#text(size: 6.8pt)[
      *Producer Gate $B_(upright("gate"))$:* \
      Native $A Omega$ solar producer unsupplied. \
      Status: *HOLD* \
      (O0 comparison fixture only; no native derivation claimed).
    ]],
    stroke: 0.85pt + aod-pal.crimson,
    fill: white,
  )

  #aod-box-tl(
    0.60, 5.76, 6.42, 1.16,
    [#text(size: 6.8pt)[
      *Scope firewall:* $B_(upright("Hg"))$ (closed bound orbit), $B_(upright("bend"))$ (open grazing chord), and $B_(upright("red"))$ (radial potential climb) carry distinct boundary topologies and cannot be collapsed into a single scalar without a declared producer.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
  )

  // Panel B (Right): Exact Rational O0 Residual Audit Cards
  #aod-box-tl(7.45, 1.34, 7.15, 5.78, [], stroke: 0.85pt + aod-pal.crimson, fill: white, radius: 4pt)
  #aod-text(11.02, 1.66, [*(b) Exact rational O0 comparison ledger ($B_(upright("O0")) -> B_(upright("ext"))$)*], size: 7.9pt, box-w: 6.8, box-h: 0.36)

  #aod-box-tl(
    7.68, 2.04, 6.68, 1.50,
    [#text(size: 6.9pt)[
      *1. Mercury perihelion ($B_(upright("Hg"))$):* \
      Mapped $= #r-hg.ao_exact$, Target $= #r-hg.target_exact$ arcsec/cy \
      Exact residual $= #r-hg.residual_exact$, $|epsilon| = #r-hg.abs_pct_error_exact$ % ($#r-hg.abs_pct_error_7dp$ %)
    ]],
    stroke: 0.85pt + aod-pal.blue,
    fill: aod-pal.tint-blue,
  )
  #aod-box-tl(
    7.68, 3.72, 6.68, 1.50,
    [#text(size: 6.9pt)[
      *2. Solar light bending ($B_(upright("bend"))$):* \
      Mapped $= #r-bend.ao_exact$, Target $= #r-bend.target_exact$ arcsec \
      Exact residual $= +#r-bend.residual_exact$, $|epsilon| = #r-bend.abs_pct_error_exact$ % ($#r-bend.abs_pct_error_7dp$ %)
    ]],
    stroke: 0.85pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
  )
  #aod-box-tl(
    7.68, 5.40, 6.68, 1.50,
    [#text(size: 6.9pt)[
      *3. Solar gravitational redshift ($B_(upright("red"))$):* \
      Mapped $= #r-red.ao_exact$, Target $= #r-red.target_exact$ \
      Exact residual $= #r-red.residual_exact$, $|epsilon| = #r-red.abs_pct_error_exact$ % ($#r-red.abs_pct_error_7dp$ %)
    ]],
    stroke: 0.85pt + aod-pal.teal,
    fill: aod-pal.tint-green,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34, 14.22, 0.74,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-040: exact rational O0 residuals $(-1 slash 10000, +1 slash 100000, -1 slash 25000000000)$ with explicit HOLD\_MISSING\_NATIVE\_SOLAR\_PRODUCER gate.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
