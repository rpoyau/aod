// Native Typst port of manual/appendices/A_simulation_fixtures_and_tau_prediction_context.tex (verbatim scientific content).
#import "../preamble.typ": *

= Simulation and Prediction-Test Fixtures <manual:simulation-prediction-test-fixtures>



#aod-paragraph[Calculation card.]
Exact support/window fixtures and the declared ninety-tick recurrence give
the outputs below. The supplied CSV, recurrence check and unchanged inline
summary are the evidence; failed recurrence is the falsifier. The chosen
coefficients have no instantiated physical uncertainty or measured target.
The common method and evidence roles are in #secref("manual:calculation-spine").




== Scope <manual:simfix:scope>

This manual appendix preserves simulation fixtures and prediction-test placement context downstream from the main note.


== Statement(s) <manual:simfix:statements>

Required outputs are

#math.equation(block: true, numbering: none, $ R D, wide rho^D , wide rho^D_(omega) , wide Q^D , wide p^D , wide phi.alt , wide P^D_F (B), wide bold(upright(A))_F (B), wide cal(E)(R,B). $)

#aod-anchor(<app:rd-tests:support-reductions>)
Fixtures include

#math.equation(block: true, numbering: none, $ 1":"2":"6, quad 1":"2":"7, quad 1":"2":"8, quad 1":"2":"9, quad 1":"2":"10, quad 3":"3":"6, quad 3":"4":"6, $)


#math.equation(block: true, numbering: none, $ 3":"4_(alpha) , wide 2 times 3":"4_(alpha) , wide 3":"4_(alpha) + 3":"4_(omega) . $)

Separate-scope fixtures include $3":"4_(alpha)$ and $3":"4_(omega)$. The fixture set also includes short-window duration-clipping fixture, pending overhang, current split, and AFC Stokes residual.


The nine-window surplus assertion is

#math.equation(block: true, numbering: none, $ 1":"2":"9: wide P^D = 27, wide C^(upright("close")) = 24, wide X_(upright("shedding")) = 3. $)

The $1":"2":"7$ fixture has $P^D = 21$ and closure-dependent sign.




== Four-step arithmetic fixtures <manual:simfix:four-step-arithmetic>

Specializing #mainappendix("main:app:proto:statements") gives

#math.equation(block: true, numbering: none, $ 6 = 4(1) + 2, wide 7 = 4(1) + 3, wide 8 = 4(2) + 0, $)


#math.equation(block: true, numbering: none, $ 9 = 4(2) + 1, wide 10 = 4(2) + 2. $)



== Demonstration <app:cycle-shedding-demo-demonstration>

The model is #mainappendix("main:app:cycle-shedding-demo-statements").
The retained #raw("wavelet_shedding_simulation.csv") fixture supplies $90$ ticks. Specialize the model to retention coefficient $eta_(upright("ret")) = 41 slash 50$, span gain $gamma_(upright("span")) = 11 slash 20$, reclosure fraction $lambda_(upright("reclose")) = 19 slash 50$, and initial burden $P_(- 1) = 0$. The generator #raw("manual/scripts/generate_cycle_shedding_fixture.py") validates the stored recurrences and summary before plotting the supplied lead and lag streams. All stored states are open; the local fraction $R_t$ does not certify a return. Within this declared ninety-tick model, the stipulated scalar $lambda_(upright("reclose")) = 19 slash 50$ certifies neither a native reclosure beat nor an exoshedding ring projection (#mainequation("main:eq:shed-continuation-witness"), #mainequation("main:eq:recipient-event-lattice")). Separately, the frozen inherited Tau ring records (#raw("manual/data/derived/tau_ring_diagnostic.csv") and #raw("manual/data/tau/aod_tau_fractal_ring_summary.csv")) have no authenticated generator in this source tree: the compact $1":"2":"10$ missing fraction $9 slash 20$ ($0.45$) and the depth-indexed summary value near $23 slash 50$ ($0.46$) remain distinct unmodified records, and any window bit span remains a separate semantic quantity from summed per-lineage closure counts or summed flux totals.


#figure(
  kind: image, [
#include "../../lib/figures/manual/cycle_disturbance_shedding_fixture.typ"
  ],
  caption: [Retained temporal-cycle fixture. The burden $P_t$ is post-clipping, with $P_t lt.eq C_t$; the stacked outward and local fractions sum to $X_t$. Figure and summary use the same CSV. The summary label “Total exoshedding” denotes $sum_t O_t$ in this fixture.],
) <fig:v39-cycle-shedding-simulation>



#align(center)[
#include "../tables/cycle_shedding_summary.typ"
]



== Falsification <manual:cycle-shedding-run-verdict>

If the computed values violate the stated recurrences on the declared ticks, the demonstration fails on that run.


== Data-support class reference <manual:app:data-support-class-reference>

Manual fixtures and comparisons are read together with their declared data-support class. The compact class list is:

#math.equation(block: true, numbering: none, $ mat(delim: #none, augment: #1, align: #left, D 0, "exact internal fixture"\,; O 0, "observable-map fixture"\,; G 0, "radial shell projection"\,; G 1, "radial-medium projection"\,; G 2, "three-dimensional field-dynamics retention"\,; G 3, "time-resolved tracer-current simulation"\,; L 0, "exact lensing toy fixture"\,; L 1, "radial lens-medium diagnostic"\,; L 2, "target-acquisition lane"\,; L 3, "full lensing release class".) $)

Errors and residuals are scoped to the class: $delta_3$ for exact internal comparators, observable-map residuals for O0, radial square-speed residuals for G0/G1, retention and field residuals for G2/G3, and target-side residuals for L2/L3 after prediction values freeze.


== Audit <manual:simfix:falsification>

Fixture audit records signed direction, scalar pressure, scope cancellation inside its declared boundary/window, and $cal(E)(R,B)$ for a declared Stokes-valid scope.


#aod-provenance[#mainequation("main:eq:b-scoped-flux")\; #mainequation("main:eq:sadar-attention-vector")\; #mainequation("main:eq:stokes-audit-residual")\; #mainappendix("main:app:scoped-flux-cancellation")\; #mainappendix("main:app:combinatorics-rd-tests").]



== Prediction-test placement

Prediction tests and any collision-window comparison context belong in this manual scaffold. Application labels and external comparison records are carried by this manual scaffold. The main A$Omega$D note supplies the AF/AFC/A$Omega$D calculus and internal form names.



== Five-boundary exact rational cycle-shedding D.E.C. ledger <manual:simfix:exact-rational-dec>

Declare the four-tick cycle-disturbance shedding stack

#math.equation(block: true, numbering: none, $ B_(upright("span")) arrow.r B_(upright("clip")) arrow.r B_(upright("shed")) arrow.r B_(upright("split")) arrow.r B_(upright("ext")). $)

Whereas the retained ninety-tick CSV and immutable summary table above display rounded decimal coordinates (six-decimal CSV entries summarized at three decimal places), the exact rational oracles #raw("RC-014") (single-step algebraic recurrence check from $P_(t - 1) = 1 slash 2$, lead $4 slash 5$, lag $1 slash 5$, and $C_t = 11 slash 20$, yielding span $3 slash 5$, pre-clip $B_t = 37 slash 50$, clipped $P_t = 11 slash 20$, shed $X_t = 19 slash 100$, outward $O_t = 589 slash 5000$, and local $R_t = 361 slash 5000$ with $589 slash 5000 + 361 slash 5000 = 19 slash 100$) and #raw("RC-043") (four-tick chained exact rational summary in #raw("manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv"), verified by #raw("python3 -B -m manual.engine") #box[#raw("--sector")] #raw("boundary_sadar") and #raw("aod-core") #box[#raw("--verify-vectors")] #box[#raw("--check-zero-float")]) evaluate every step without floating-point rounding: $P_t = min (B_t , C_t )$, shedding surplus $X_t = max (0, B_t - C_t )$, outward fraction $O_t = (31 slash 50) X_t$, and local retention $R_t = (19 slash 50) X_t$, satisfying $O_t + R_t = X_t$ identically at every tick. Across the four ticks of #raw("RC-043"), cumulative exact totals are $sum_t X_t = 6447 slash 15625$, outward $sum_t O_t = 199857 slash 781250$ (exact shed share $sum_t O_t slash sum_t X_t = 31 slash 50$), and local retention $sum_t R_t = 122493 slash 781250$ (exact shed share $sum_t R_t slash sum_t X_t = 19 slash 50$).


#figure(
  kind: table, [
#{
  let rows = csv("/manual/data/boundary_sadar/cycle_shedding_exact_rational_summary.csv", row-type: dictionary)
  set text(size: 8.0pt)
  set par(justify: false, leading: 0.44em)
  table(
    columns: (6fr, 10fr, 15fr, 9fr, 12fr, 14fr, 17fr, 17fr),
    align: (right, right, right, right, right, right, right, right),
    inset: (x: 2.8pt, y: 3.3pt),
    table.header(
      toprule,
      [Tick], [Span], [Pre-clip $B_t$], [$C_t$], [Clipped $P_t$], [Shed $X_t$], [Outward $O_t$], [Local $R_t$],
      midrule,
    ),
    ..rows.map(r => (
      [#r.tick],
      [#r.span_exact],
      [#r.before_clip_exact],
      [#r.C_compat_exact],
      [#r.padar_P_exact],
      [#r.shed_X_exact],
      [#r.outward_O_exact],
      [#r.local_R_exact],
    )).flatten(),
    bottomrule,
  )
}
  ],
  caption: [Engine-bound exact rational four-tick cycle-disturbance clipping and $31 slash 50$ versus $19 slash 50$ shedding split D.E.C. ledger (#raw("RC-014"), #raw("RC-043")\; live from #raw("cycle_shedding_exact_rational_summary.csv")).],
) <tab:manual-app-a-exact-shedding-dec>

