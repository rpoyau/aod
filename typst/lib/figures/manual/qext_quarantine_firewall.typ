// Authored native Typst vector figure: qext-quarantine-firewall (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.6
#let y-off = 1.02

#let rows = csv("/manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv", row-type: dictionary)
#let r-e = rows.at(0)
#let r-tau = rows.at(2)
#let r-p = rows.at(7)
#let r-h = rows.at(9)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, fig-height-cm - 0.30, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-figure-header(
    fig-width-cm,
    [Quarantined external comparison firewall $B_(upright("ext")) = sans("Q")_(upright("ext"))(nu_(x, A Omega); cal(T)_x)$ & $6$-tuple precision law],
    subtitle: [One-way map from exact $bb(Z) slash bb(Q)$ native accessors into quarantined SI/CODATA/PDG comparison records; reverse import blocked.],
    top-y: 0.26,
    pad-x: 0.35,
    title-size: 9.4pt,
    subtitle-size: 7.2pt,
    gap-cm: 0.12,
  )

  // Left Zone: Exact Z / Q Native Side (Zero Floats, Zero SI Constants)
  #aod-box-tl(0.38, 1.36 + y-off, 5.45, 5.66, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(3.10, 1.68 + y-off, [*(a) Native $bb(Z) slash bb(Q)$ interior*], size: 8.0pt, box-w: 5.1, box-h: 0.36)

  #aod-box-tl(
    0.62, 2.08 + y-off, 4.96, 2.28,
    [#text(size: 6.9pt)[
      *Pure integer / rational accessors:* \
      $e^-$ ($#r-e.support$): $R D = #r-e.Pi dot.op 2 + 1 = #r-e.RD$, $P^D = #r-e.PD_sup$ \
      $tau^-$ ($#r-tau.support$): $X_(upright("shed")) = #r-tau.X_shedding_chan$, $op("miss")_(tau) = 31 slash 50$ \
      $p^+$ ($#r-p.support$): $R D = #r-p.RD$, $R D_p slash R D_e = 61 slash 9$ \
      Higgs ($#r-h.support$): $R D = #r-h.RD$, $P^D_H = 21$
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    inset: 4pt,
    leading: 0.36em,
  )
  #aod-box-tl(
    0.62, 4.58 + y-off, 4.96, 2.20,
    [#text(size: 6.9pt)[
      *Engine enforcement (S2 + S4):* \
      Zero floats, zero $c, h_(upright("ext")), e, alpha_(upright("fs")), K_(upright("ext"))$, and pre-freeze candidate selection before any target join.
    ]],
    stroke: 0.8pt + aod-pal.teal,
    fill: aod-pal.tint-green,
    inset: 4pt,
    leading: 0.36em,
  )

  // Double-line Quarantine Firewall Wall B_ext = Q_ext
  #aod-boundary-wall(6.18, 1.36 + y-off, 6.18, 7.02 + y-off, stroke: 1.3pt + aod-pal.crimson, hatch-side: 1, hatch-count: 11, double-line: true)
  #aod-text(6.18, 1.18 + y-off, [$B_(upright("ext")) = sans("Q")_(upright("ext"))$], size: 7.0pt, weight: "bold", box-w: 1.8, box-h: 0.28)

  // Permitted one-way projection arrow (top) vs Blocked reverse import (bottom)
  #aod-arrow(5.62, 2.95 + y-off, 6.72, 2.95 + y-off, stroke: 1.2pt + aod-pal.teal)
  #aod-text(6.18, 2.62 + y-off, [1-way], size: 6.8pt, weight: "bold", box-w: 1.0, box-h: 0.26)
  #aod-line(5.68, 5.55 + y-off, 6.68, 5.55 + y-off, stroke: (paint: aod-pal.crimson, thickness: 1.1pt, dash: "dashed"))
  #aod-marker(6.18, 5.55 + y-off, kind: "cross", r-pt: 4.0, color: aod-pal.crimson)
  #aod-text(6.18, 5.92 + y-off, [blocked], size: 6.8pt, weight: "bold", box-w: 1.1, box-h: 0.26)

  // Right Zone: Quarantined External Comparison Records + S3 Firewall
  #aod-box-tl(6.78, 1.36 + y-off, 7.82, 5.66, [], stroke: 0.9pt + aod-pal.crimson, fill: aod-pal.tint-orange, radius: 4pt)
  #aod-text(10.69, 1.68 + y-off, [*(b) Quarantined $sans("Q")_(upright("ext"))$ $6$-tuple & cancellation audit*], size: 8.0pt, box-w: 7.5, box-h: 0.36)

  #aod-box-tl(
    7.02, 2.04 + y-off, 7.34, 1.64,
    [#text(size: 6.6pt)[
      *Mandatory $6$-tuple decimal precision record:* \
      $(x_(upright("disp")), u_x, op("unit")(x), op("src")(x), op("round")(x), op("scope")(x))$ \
      $e^-$: $(#r-e.Qext_target_MeV, #r-e.Qext_sigma_MeV, upright("MeV"),$ \
      $upright("CODATA-2022"), upright("half-even"), sans("Q")_(upright("ext")))$; $tau^-$: $#r-tau.Qext_target_MeV plus.minus #r-tau.Qext_sigma_MeV$ MeV.
    ]],
    stroke: 0.8pt + aod-pal.navy,
    fill: white,
    inset: 4.5pt,
    leading: 0.34em,
  )
  #aod-box-tl(
    7.02, 3.82 + y-off, 7.34, 1.44,
    [#text(size: 6.8pt)[
      *Exact $eta_(upright("ext"))$ round-trip cancellation:* \
      For $nu_(upright("sc")) = nu_(A Omega) slash eta_(upright("ext"))$ and $E_(upright("map")) = K_(upright("ext")) eta_(upright("ext")) nu_(upright("sc"))$, the external factor $eta_(upright("ext")) = alpha_(upright("fs"))^(-1)$ cancels identically ($E_(upright("map")) = K_(upright("ext")) nu_(A Omega)$), adding zero independent native degrees of freedom.
    ]],
    stroke: 0.8pt + aod-pal.purple,
    fill: aod-pal.tint-purple,
    inset: 4.5pt,
    leading: 0.35em,
  )
  #aod-box-tl(
    7.02, 5.42 + y-off, 7.34, 1.38,
    [#text(size: 6.8pt)[
      *Standing R04 S3 quarantine:* \
      Simulation-substrate, computational-calculus, and physical-equivalence claims stay strictly quarantined outside Main ontology and native Manual derivations.
    ]],
    stroke: 0.85pt + aod-pal.crimson,
    fill: white,
    inset: 4.5pt,
    leading: 0.35em,
  )

  // Bottom invariant bar
  #aod-box-tl(
    0.38, 7.24 + y-off, 14.22, 0.86,
    [#text(size: 7.0pt, weight: "bold")[Engine vectors SD-007, SD-004/SD-005 & RC-027..RC-029: strict separation between exact $bb(Z) slash bb(Q)$ native invariants and $6$-tuple quarantined $sans("Q")_(upright("ext"))$ display records.]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
    inset: 4pt,
    leading: 0.36em,
  )
]
