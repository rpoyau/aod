// Audited S1b native Typst vector figure: higgs-tritrioseptyro-trace-flow (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/higgs/higgs_trace_internal_candidates_selection.csv + manual/data/higgs/higgs_external_map_after_candidate_freeze.csv)
// Historical raster retained byte-for-byte: manual/figures/higgs/higgs_tritrioseptyro_trace_flow.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.8
#let fig-height-cm = 9.0

#let cand-rows = csv("/manual/data/higgs/higgs_trace_internal_candidates_selection.csv", row-type: dictionary)
#let sel = cand-rows.find(r => r.rank == "1")
#let ext-rows = csv("/manual/data/higgs/higgs_external_map_after_candidate_freeze.csv", row-type: dictionary)
#let pred-gev = ext-rows.find(r => r.quantity == "E_H_0" and r.unit == "GeV").value

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(7.4, 0.45, [*Tritrioseptyro ($#sel.candidate_K _upright("yro")$) overlap-saddle trace & quarantine boundary*], size: 10.8pt, box-w: 14.2, box-h: 0.52)
  #aod-text(7.4, 0.86, [Two-baryon $3":"3$ overlap selects the unique lineage-conserved $sans("C")_6 slash sans("C")_8$ midpoint saddle before external map freeze.], size: 7.5pt, box-w: 14.2, box-h: 0.42)

  // Left Zone: Active internal AOmegaD SADAR overlap & midpoint saddle
  #aod-box-tl(0.30, 1.25, 9.55, 6.75, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-text(5.08, 1.58, [*1. Internal $A Omega D$ collision-pocket trace (zero external mass inputs)*], size: 8.3pt, box-w: 9.2, box-h: 0.40)

  // Opposing 3:3:6 parents converging into 3:3:7_yro odd-window overlap pocket
  #aod-box-tl(0.58, 2.05, 2.55, 0.96, [#text(size: 7.7pt)[Stream A \ $3":"3":"6$ ($p=3, q=3$)]], stroke: 0.9pt + aod-pal.blue, fill: white)
  #aod-box-tl(0.58, 3.35, 2.55, 0.96, [#text(size: 7.7pt)[Stream B \ $3":"3":"6$ ($p=3, q=3$)]], stroke: 0.9pt + aod-pal.blue, fill: white)
  #aod-arrow(3.15, 2.53, 4.02, 2.98, stroke: 1.0pt + aod-pal.navy)
  #aod-arrow(3.15, 3.83, 4.02, 3.38, stroke: 1.0pt + aod-pal.navy)

  // Overlap vertex + support accessors
  #aod-box-tl(
    4.05, 2.15, 5.50, 2.08,
    [#text(size: 8.0pt)[
      *Selected overlap candidate:* $#sel.candidate_K _upright("yro")$ \
      $Pi = #sel.q ^#sel.p + #sel.q = #sel.Pi_qp_plus_q$, $quad R D = 2 Pi + 1 = #sel.RD_accessor$ \
      $rho_omega^D = #sel.rhoD_omega$, $quad C_(3, H) = #sel.C3_H_scoped$ \
      $P_H^D = #sel.PD_window_pressure$, $quad Q_H^D = #sel.QD_pending_overhang$
    ]],
    stroke: 1.05pt + aod-pal.gold,
    fill: aod-pal.tint-amber,
    radius: 4pt,
  )

  // Visual C6 / PD_H / C8 symmetric midpoint gauge
  #aod-box-tl(0.58, 4.65, 8.97, 3.05, [], stroke: 0.8pt + aod-pal.slate, fill: white, radius: 3.5pt)
  #aod-text(5.06, 5.00, [*Symmetric $sans("C")_6 slash sans("C")_8$ midpoint saddle balance: $(P_H^D - sans("C")_6) + (P_H^D - sans("C")_8) = 0$*], size: 7.9pt, box-w: 8.6, box-h: 0.40)

  // Horizontal closure-pressure axis from 15 to 27
  #let gx1 = 1.35
  #let gx2 = 8.75
  #let map-p(pv) = gx1 + ((pv - 15.0) / 12.0) * (gx2 - gx1)
  #aod-line(gx1, 6.15, gx2, 6.15, stroke: 1.1pt + aod-pal.axis)
  // C6 = 18, PD_H = 21, C8 = 24, C10 = 27 ticks
  #for (pv, lbl, col) in (
    (18.0, [$sans("C")_6 = 18$], aod-pal.teal),
    (21.0, [$P_H^D = #sel.PD_window_pressure$], aod-pal.orange),
    (24.0, [$sans("C")_8 = 24$], aod-pal.blue),
    (27.0, [$sans("C")_(10) = 27$], aod-pal.slate),
  ) {
    let px = map-p(pv)
    aod-line(px, 5.95, px, 6.35, stroke: 1.2pt + col)
    aod-circle(px, 6.15, 0.085, fill: col, stroke: 0.5pt + white)
    aod-text(px, 6.66, lbl, size: 7.5pt, weight: "bold", box-w: 1.9, box-h: 0.38)
  }
  // Balanced +3 and -3 arrows around PD_H = 21
  #aod-arrow(map-p(18.0) + 0.14, 5.72, map-p(21.0) - 0.14, 5.72, stroke: 1.0pt + aod-pal.teal, both: true)
  #aod-text((map-p(18.0) + map-p(21.0)) / 2.0, 5.44, [$+#sel.delta_lower$ above $sans("C")_6$], size: 7.2pt, box-w: 2.2, box-h: 0.35)
  #aod-arrow(map-p(21.0) + 0.14, 5.72, map-p(24.0) - 0.14, 5.72, stroke: 1.0pt + aod-pal.blue, both: true)
  #aod-text((map-p(21.0) + map-p(24.0)) / 2.0, 5.44, [$-#{int(calc.abs(float(sel.delta_upper)))}$ below $sans("C")_8$], size: 7.2pt, box-w: 2.2, box-h: 0.35)
  #aod-text(5.06, 7.28, [Parent $q = 3$ conservation isolates $3":"3":"7_(upright("yro"))$ uniquely from $\{3":"2":"7, med 3":"3":"7, med 3":"4":"7\}$.], size: 7.2pt, box-w: 8.6, box-h: 0.38)

  // Candidate-freeze quarantine wall
  #aod-boundary-wall(10.22, 1.25, 10.22, 7.92, stroke: 1.35pt + aod-pal.crimson, hatch-side: 1, hatch-count: 11, double-line: true)
  #aod-text(10.22, 8.14, [*freeze wall*], size: 7.3pt, weight: "bold", box-w: 1.8, box-h: 0.34)
  #aod-arrow(9.88, 3.20, 10.58, 3.20, stroke: 1.15pt + aod-pal.crimson)

  // Right Zone: Quarantined external map after candidate freeze
  #aod-box-tl(10.62, 1.25, 3.88, 6.75, [], stroke: 0.9pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-text(12.56, 1.66, [*2. Post-freeze $B_(upright("ext"))$*], size: 8.3pt, box-w: 3.6, box-h: 0.40)

  #aod-box-tl(
    10.86, 2.25, 3.40, 1.95,
    [#text(size: 7.9pt)[
      Frozen candidate \
      $K_H^(star) = #sel.candidate_K _upright("yro")$ \
      $R D_H = #sel.RD_accessor$, $quad L = #sel.L_window$
    ]],
    stroke: 0.85pt + aod-pal.purple,
    fill: white,
  )
  #aod-arrow(12.56, 4.24, 12.56, 4.82, stroke: 1.0pt + aod-pal.purple)
  #aod-box-tl(
    10.86, 4.86, 3.40, 2.68,
    [#text(size: 8.0pt)[
      *External energy map:* \
      $E_H^((0)) = R D_H thin 2^(L + 4)$ \
      $= 61 dot 2^(11) thin upright("MeV")$ \
      $= 124928 thin upright("MeV")$ \
      $=$ *#pred-gev GeV*
    ]],
    stroke: 1.0pt + aod-pal.purple,
    fill: white,
  )

  #aod-text(7.4, 8.60, [Internal trace freezes $K_H^(star) = 3":"3":"7_(upright("yro"))$ before external LHC mass targets enter comparison.], size: 8.0pt, box-w: 14.0, box-h: 0.40)
]
