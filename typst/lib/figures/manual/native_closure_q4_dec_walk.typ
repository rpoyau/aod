// Authored native Typst vector figure: native-closure-q4-dec-walk (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/native_closure_wave_dec_walk.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 8.8
#let y-off = 0.36

#let rows = csv("/manual/data/boundary_sadar/native_closure_wave_dec_walk.csv", row-type: dictionary)
#let r-out = rows.at(0)
#let r-hinge = rows.at(1)
#let r-ret = rows.at(2)
#let r-asym = rows.at(3)
#let r-beat = rows.at(4)
#let r-swap = rows.at(6)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Boundary-Feynman $Q_4$ closure, reflected-leg return, beat cadence & fold shell],
    subtitle: [Active $Q_4$ subcomplex $R_(upright("cl")) = \{0000, 0001, 0011\}$: symmetric $(2, 1)$ Monon vs asymmetric $(4, 1)$ reflected return.],
    top-y: 0.28,
    pad-x: 0.35,
    title-size: 9.8pt,
    subtitle-size: 7.3pt,
    gap-cm: 0.14,
  )

  // Panel A (Left): Symmetric (1+1=2) vs Asymmetric (1+3=4) Q4 closure walks
  #aod-box-tl(0.40, 1.38 + y-off, 6.95, 5.65, [], stroke: 0.85pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.88, 1.66 + y-off, [*(a) $Q_4$ H1 closure witnesses (1 closure-phase cycle)*], size: 7.3pt, box-w: 6.75, box-h: 0.34)

  // Vertices 0000, 0001, 0011
  #aod-chiral-vertex(1.45, 3.35 + y-off, [$#r-out.vertex_v$], r: 0.36, fill: white, stroke: 1.1pt + aod-pal.navy, text-size: 7.0pt)
  #aod-chiral-vertex(4.10, 3.35 + y-off, [$#r-out.target_ve$ \ $0_H$], r: 0.38, fill: aod-pal.tint-amber, stroke: 1.1pt + aod-pal.gold, text-size: 6.9pt)
  #aod-chiral-vertex(6.35, 3.35 + y-off, [$0011$], r: 0.36, fill: white, stroke: 1.0pt + aod-pal.purple, text-size: 7.0pt)

  // Symmetric Monon (1+1 = 2 edges, 1 cycle)
  #aod-arrow(1.83, 3.16 + y-off, 3.70, 3.16 + y-off, stroke: 1.15pt + aod-pal.blue)
  #aod-text(2.76, 2.84 + y-off, [$e_0 (+1)$, $P = #r-out.prob_exact$], size: 6.9pt, weight: "bold", box-w: 2.3, box-h: 0.32)
  #aod-arrow(3.70, 3.54 + y-off, 1.83, 3.54 + y-off, stroke: 1.15pt + aod-pal.teal)
  #aod-text(2.76, 3.88 + y-off, [$e_0 (-1)$, $P = #r-ret.prob_exact$], size: 6.9pt, weight: "bold", box-w: 2.3, box-h: 0.32)

  // Dwell reduction note above 0001
  #aod-arc-arrow(4.10, 2.66 + y-off, 0.30, -50, 230, stroke: (paint: aod-pal.crimson, thickness: 0.9pt, dash: "dashed"))
  #aod-text(4.10, 2.14 + y-off, [live $0_D^2 -> m = 0$ ($0_H$ kept)], size: 6.8pt, box-w: 3.3, box-h: 0.32)

  // Asymmetric extension 0001 <-> 0011 (1 + 3 = 4 edges, still 1 closure-phase cycle!)
  #aod-wavy-arrow(4.50, 3.20 + y-off, 5.97, 3.20 + y-off, amp: 0.055, waves: 2.0, stroke: 1.05pt + aod-pal.purple)
  #aod-wavy-arrow(5.97, 3.50 + y-off, 4.50, 3.50 + y-off, amp: 0.055, waves: 2.0, stroke: 1.05pt + aod-pal.orange)
  #aod-text(5.24, 2.82 + y-off, [$e_1 (+1)$], size: 6.8pt, box-w: 1.5, box-h: 0.30)
  #aod-text(5.24, 3.88 + y-off, [$e_1 (-1)$], size: 6.8pt, box-w: 1.5, box-h: 0.30)

  #aod-box-tl(
    0.65, 4.48 + y-off, 6.45, 2.30,
    [#text(size: 7.0pt)[
      *Reflected-leg & swap falsifiers:* \
      *(1)* Symmetric Monon: $(2, 1)$ edges/cycles ($2 h$). \
      *(2)* Asymmetric $1 + 3$ return: $(4, 1)$ edges/cycles ($4 h != 2 h, 6 h$; equal-leg factorization rejected). \
      *(3)* AFC swap memory $(#r-swap.prob_exact, 1 slash 4)$: flux $+1 slash 2$, exchanged $-1 slash 2$, equal $0$.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    align-mode: left + horizon,
    inset: 4.5pt,
    leading: 0.36em,
  )

  // Panel B (Right): 3-Closure Recurrent Beat Cadence + Fold^up / Expose^down Shell
  #aod-box-tl(7.60, 1.38 + y-off, 7.00, 5.65, [], stroke: 0.85pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 4pt)
  #aod-text(11.10, 1.66 + y-off, [*(b) Recurrent beat cadence, Fold shell & $bb(Z)_4$ harmonics*], size: 6.9pt, box-w: 6.88, box-h: 0.34)

  // Beat timeline: C_1 (cut 0) --10--> C_2 (cut 10) --10--> C_3 (cut 20)
  #aod-box-tl(7.85, 2.12 + y-off, 6.50, 1.85, [], stroke: 0.8pt + aod-pal.teal, fill: white)
  #aod-chiral-vertex(8.65, 2.88 + y-off, [$C_1$], r: 0.27, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue, text-size: 7.0pt)
  #aod-arrow(8.95, 2.88 + y-off, 10.75, 2.88 + y-off, stroke: 1.05pt + aod-pal.teal)
  #aod-text(9.85, 2.55 + y-off, [beat $1$ ($Delta = 10$)], size: 6.8pt, weight: "bold", box-w: 2.0, box-h: 0.30)
  #aod-chiral-vertex(11.08, 2.88 + y-off, [$C_2$], r: 0.27, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue, text-size: 7.0pt)
  #aod-arrow(11.38, 2.88 + y-off, 13.18, 2.88 + y-off, stroke: 1.05pt + aod-pal.teal)
  #aod-text(12.28, 2.55 + y-off, [beat $2$ ($Delta = 10$)], size: 6.8pt, weight: "bold", box-w: 2.0, box-h: 0.30)
  #aod-chiral-vertex(13.50, 2.88 + y-off, [$C_3$], r: 0.27, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue, text-size: 7.0pt)
  #aod-text(11.10, 3.60 + y-off, [$#r-beat.weight_w$ certified closures $=>$ $2$ beats ($n_F = 1$; Disoma $n_F = 2$)], size: 6.9pt, box-w: 6.2, box-h: 0.32)

  // Fold^up / Expose^down boundary shell + Z4 harmonic readout
  #aod-boundary-wall(11.10, 4.18 + y-off, 11.10, 6.78 + y-off, stroke: 1.1pt + aod-pal.purple, hatch-side: 1, hatch-count: 6)
  #aod-box-tl(
    7.85, 4.28 + y-off, 3.05, 2.48,
    [#text(size: 6.9pt)[
      *Preassembled Fold:* \
      $op("Fold")^arrow.t$: inner wave \
      identity committed \
      before outer trace \
      ($1$ outer cycle, \
      inner cycle intact)
    ]],
    stroke: 0.8pt + aod-pal.purple,
    fill: white,
    inset: 4pt,
    leading: 0.36em,
  )
  #aod-box-tl(
    11.32, 4.28 + y-off, 3.03, 2.48,
    [#text(size: 6.9pt)[
      *Downstream $bb(Z)_4$ DFT:* \
      Signal $(1, 0, -1, 0)$ \
      $hat(x) = (0, 2, 0, 2)$ \
      Exact inverse $bb(Z)[i]$ \
      residual $= 0 slash 1$ \
      *(never certifies $C$)*
    ]],
    stroke: 0.8pt + aod-pal.gold,
    fill: aod-pal.tint-amber,
    inset: 4pt,
    leading: 0.36em,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.40, 7.28 + y-off, 14.20, 0.78,
    [#text(size: 7.2pt, weight: "bold")[Engine vector RC-033: H1 atomic support, mandatory $0_H$, live $0_D$ burn, $(2,1)$ vs $(4,1)$ closures, $3$-closure beat cadence, and exact $bb(Z)_4$ reconstruction.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
