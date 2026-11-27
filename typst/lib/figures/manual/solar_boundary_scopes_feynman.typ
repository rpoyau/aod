// Authored native Typst vector figure: solar-boundary-scopes-feynman (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.3
#let y-off = 0.76

#let rows = csv("/manual/data/boundary_sadar/solar_o0_boundary_dec_audit.csv", row-type: dictionary)
#let r-hg = rows.at(0)
#let r-bend = rows.at(1)
#let r-red = rows.at(2)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Solar O0 boundary scopes ($B_(upright("Hg")), B_(upright("bend")), B_(upright("red"))$), missing-producer gate & rational audit],
    subtitle: [Active $5$-boundary spine $B_(upright("Sun")) -> (B_(upright("Hg")), B_(upright("bend")), B_(upright("red"))) -> B_(upright("gate")) -> B_(upright("O0")) -> B_(upright("ext"))$: O0 observable-map audit held honest.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.4pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.12,
  )

  // Panel A (Left): Solar support R_Sun + three typed boundary scopes + HOLD firewall
  #aod-box-tl(0.38, 1.34 + y-off, 6.85, 5.78, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-amber, radius: 4pt)
  #aod-text(3.80, 1.64 + y-off, [*(a) Three typed solar boundary scopes & producer gate*], size: 6.9pt, box-w: 6.72, box-h: 0.34)

  // Central Solar support R_Sun
  #aod-chiral-vertex(2.15, 3.85 + y-off, [$R_(upright("Sun"))$], r: 0.48, fill: white, stroke: 1.25pt + aod-pal.gold, text-size: 7.2pt)

  // (1) Mercury orbital return shell B_Hg (ellipse/circle arc)
  #aod-circle(2.15, 3.85 + y-off, 1.18, fill: none, stroke: (paint: aod-pal.blue, thickness: 1.0pt, dash: "dashed"))
  #aod-text(2.15, 2.42 + y-off, [$B_(upright("Hg"))$ orbital return shell], size: 6.8pt, weight: "bold", box-w: 3.2, box-h: 0.28)

  // (2) Grazing light-bending chord B_bend
  #aod-curve-arrow(0.72, 4.92 + y-off, 2.15, 4.38 + y-off, 4.55, 4.88 + y-off, stroke: 1.1pt + aod-pal.purple)
  #aod-text(2.68, 5.26 + y-off, [$B_(upright("bend"))$ grazing ray chord], size: 6.8pt, weight: "bold", box-w: 3.3, box-h: 0.28)

  // (3) Radial climb window B_red
  #aod-wavy-arrow(2.66, 3.70 + y-off, 4.55, 3.12 + y-off, amp: 0.05, waves: 3.0, stroke: 1.05pt + aod-pal.teal)
  #aod-text(4.02, 3.68 + y-off, [$B_(upright("red"))$ climb], size: 6.8pt, weight: "bold", box-w: 1.50, box-h: 0.28)

  // Honest HOLD_MISSING_NATIVE_SOLAR_PRODUCER boundary wall
  #aod-boundary-wall(4.85, 2.08 + y-off, 4.85, 5.56 + y-off, stroke: 1.25pt + aod-pal.crimson, hatch-side: 1, hatch-count: 8, double-line: true)
  #aod-box-tl(
    5.06, 2.22 + y-off, 1.96, 3.28,
    [#text(size: 6.8pt)[
      *Producer Gate $B_(upright("gate"))$:* \
      Native $A Omega$ solar producer unsupplied. \
      Status: *HOLD* \
      (O0 comparison fixture only; no native derivation claimed).
    ]],
    stroke: 0.85pt + aod-pal.crimson,
    fill: white,
    inset: 3.5pt,
    leading: 0.35em,
  )

  #aod-box-tl(
    0.60, 5.76 + y-off, 6.42, 1.16,
    [#text(size: 6.8pt)[
      *Scope firewall:* $B_(upright("Hg"))$ (closed bound orbit), $B_(upright("bend"))$ (open grazing chord), and $B_(upright("red"))$ (radial potential climb) carry distinct boundary topologies and cannot be collapsed into a single scalar without a declared producer.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    inset: 4pt,
    leading: 0.35em,
  )

  // Panel B (Right): Exact Rational O0 Residual Audit Cards
  #aod-box-tl(7.45, 1.34 + y-off, 7.15, 5.78, [], stroke: 0.85pt + aod-pal.crimson, fill: white, radius: 4pt)
  #aod-text(11.02, 1.64 + y-off, [*(b) Exact rational O0 comparison ledger ($B_(upright("O0")) -> B_(upright("ext"))$)*], size: 7.1pt, box-w: 6.95, box-h: 0.34)

  #aod-box-tl(
    7.68, 2.04 + y-off, 6.68, 1.50,
    [#text(size: 6.6pt)[
      *(1) Mercury perihelion ($B_(upright("Hg"))$):* \
      Mapped $= #r-hg.ao_exact$, Target $= #r-hg.target_exact$ arcsec/cy \
      Exact residual $= #r-hg.residual_exact$, $|epsilon| = #r-hg.abs_pct_error_exact$ % ($#r-hg.abs_pct_error_7dp$ %)
    ]],
    stroke: 0.85pt + aod-pal.blue,
    fill: aod-pal.tint-blue,
    align-mode: left + horizon,
    inset: 4pt,
    leading: 0.36em,
  )
  #aod-box-tl(
    7.68, 3.72 + y-off, 6.68, 1.50,
    [#text(size: 6.6pt)[
      *(2) Solar light bending ($B_(upright("bend"))$):* \
      Mapped $= #r-bend.ao_exact$, Target $= #r-bend.target_exact$ arcsec \
      Exact residual $= +#r-bend.residual_exact$, $|epsilon| = #r-bend.abs_pct_error_exact$ % ($#r-bend.abs_pct_error_7dp$ %)
    ]],
    stroke: 0.85pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
    align-mode: left + horizon,
    inset: 4pt,
    leading: 0.36em,
  )
  #aod-box-tl(
    7.68, 5.40 + y-off, 6.68, 1.50,
    [#text(size: 6.45pt)[
      *(3) Solar gravitational redshift ($B_(upright("red"))$):* \
      Mapped $= #r-red.ao_exact$, Target $= #r-red.target_exact$ \
      Exact residual $= #r-red.residual_exact$, $|epsilon| = #r-red.abs_pct_error_exact$ % ($#r-red.abs_pct_error_7dp$ %)
    ]],
    stroke: 0.85pt + aod-pal.teal,
    fill: aod-pal.tint-green,
    align-mode: left + horizon,
    inset: 3.5pt,
    leading: 0.36em,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.34 + y-off, 14.22, 0.78,
    [#text(size: 7.1pt, weight: "bold")[Engine vector RC-040: exact rational O0 residuals $(-1 slash 10000, +1 slash 100000, -1 slash 25000000000)$ with explicit HOLD\_MISSING\_NATIVE\_SOLAR\_PRODUCER gate.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
