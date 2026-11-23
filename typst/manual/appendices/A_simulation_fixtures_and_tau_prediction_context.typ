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
