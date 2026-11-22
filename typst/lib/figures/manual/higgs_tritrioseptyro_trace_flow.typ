// Audited S1b native Typst vector figure: higgs-tritrioseptyro-trace-flow (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/higgs/higgs_trace_internal_candidates_selection.csv + external comparison CSV)
// Historical raster retained byte-for-byte: manual/figures/higgs/higgs_tritrioseptyro_trace_flow.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 13.8
#let fig-height-cm = 11.4

#let cand-rows = csv("/manual/data/higgs/higgs_trace_internal_candidates_selection.csv", row-type: dictionary)
#let sel = cand-rows.find(r => r.rank == "1")
#let ext-rows = csv("/manual/data/higgs/higgs_external_map_after_candidate_freeze.csv", row-type: dictionary)
#let pred-gev = ext-rows.find(r => r.quantity == "E_H_0" and r.unit == "GeV").value

#let steps = (
  ("1. Candidate", [$#sel.candidate_K _upright("yro")$]),
  ("2. Branch support", [$Pi = #sel.p ^#sel.q + #sel.q = #sel.Pi_qp_plus_q$ \ $R D = 2 Pi + 1 = #sel.RD_accessor$]),
  ("3. Window", [$rho_omega^D = #sel.rhoD_omega$ \ $C_(3, H) = #sel.C3_H_scoped$]),
  ("4. Pressure", [$P_H^D = #sel.PD_window_pressure$ \ $Q_H^D = #sel.QD_pending_overhang$]),
  ("5. Saddle", [$C_6 : +#sel.delta_lower$ \ $C_8 : -#{int(calc.abs(float(sel.delta_upper)))}$]),
  ("6. Frozen map", [$E_H^((0)) = R D thin 2^(L + 4)$ \ $#pred-gev thin upright("GeV")$]),
)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-text(6.9, 0.52, [*Tritrioseptyro trace flow*], size: 11.8pt, box-w: 12.5, box-h: 0.55)

  #let y0 = 1.15
  #let bh = 1.24
  #let gap = 0.34
  #for i in range(steps.len()) {
    let (st-lbl, st-val) = steps.at(i)
    let by = y0 + i * (bh + gap)
    aod-box-tl(1.65, by, 10.50, bh, [], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 5pt)
    aod-text(2.25, by + bh / 2, [*#st-lbl*], size: 8.8pt, anchor: "left", box-w: 3.6, box-h: 0.6)
    aod-text(7.90, by + bh / 2, [#text(size: 9.0pt)[#st-val]], box-w: 6.2, box-h: 1.05)
    if i < steps.len() - 1 {
      aod-arrow(6.90, by + bh + 0.03, 6.90, by + bh + gap - 0.03, stroke: 0.95pt + aod-pal.navy, head-len: 4.0, head-half: 2.0)
    }
  }

  #aod-text(6.9, 10.85, [Internal trace freezes before external LHC targets join.], size: 8.6pt, box-w: 12.5, box-h: 0.5)
]
