// Native Typst port of appendices/H_combinatorics_rd_tests.tex (verbatim scientific content).
#import "../preamble.typ": *

= Reflection Duration on $Q_4$ <app:combinatorics-rd-tests>



== Scope <app:rd-tests:scope>

This appendix states graph support, ternary fibre, Markov kernels, path histories,
RD/RCD and integer support reductions for A$Omega$-internal SADAR pressure.


== Setup <app:rd-tests:setup>

Use #eqref("eq:atomic-h1") for the finite graph and
#eqref("eq:hinge-grammar") for the distinct ternary fibre
$sigma_t (e) in brace.l - 1,0, + 1 brace.r$.


== Choice: Markov kernel <app:rd-tests:markov-kernel>

The downstream kernel #eqref("eq:admitted-kernel") is normalized only for
positive total weight on admitted H1 support. Equal weights give the isotropic
$1 slash N_B$; unequal weights, including dependence on committed lag, orientation
and reflection, give its anisotropic specialization. Outside that support its
probability is zero. Additional dwell uses the separate fibre family
#eqref("eq:continuation-domain-split"); an empty positive-weight support supplies
no normalized kernel.


== Path histories and reflected duration <app:rd-tests:statements>

A path history is

#math.equation(block: true, numbering: none, $ h = ((e_0 , sigma_0 ), dots.h ,(e_m , sigma_m )). $)

Equation #eqref("eq:branch-hinge-rd") specializes to this history:

$ R D_h (B) = Pi^(-)_h (B) + H_(mu ,h) (B) + Pi^(+)_h (B). $ <app:rd:eq:branch-hinge-rd>

If the window contains each support occurrence exactly once, the full-trace
specialization is

#math.equation(block: true, numbering: none, $ R D_h (B) = sum_(t in omega) bold(1)[h" retained, pending, or returning at "t]. $)

Outside that full-trace specialization the indicator sum is window participation, not full RD. Couple with #eqref("eq:rcd-coupling") and project duration by
#eqref("eq:rcd-duration-participation"). In a common ordered count domain,
#eqref("eq:window-clipped-rho") clips participation, while
#eqref("eq:duration-overhang") and #eqref("eq:burden-overhang") record pending excess.


== Walk support corollaries <app:rd-tests:corollaries>

The declared model #eqref("eq:curling-support-model") has the walk accounting

$ Pi (p":"q) = q^p + q. $ <app:rd:eq:path-support>

Here $q^p$ is the memoryless $q$-direction walk count and $q$ is the retained Hamming–1 edge-shell term. The branch/hinge/branch reflected-return support is

$ R D(p":"q;B) = 2 Pi (p":"q) + H_(mu) (B) $ <app:rd:eq:reflected-return>

when the branch supports are symmetric. The single-hinge reduction is

$ H_(mu) (B) = 1 quad arrow.r.double.long quad R D(p":"q) = 2 Pi (p":"q) + 1. $ <app:rd:eq:single-hinge-return>

The added $q$ is retained edge-shell support. Symmetry invokes
#eqref("eq:branch-hinge-rd-symmetric"); the unit hinge is an extra hypothesis,
not the general rule.


#aod-remark[The cited combinatorics is introduced at the first $Q_4$ / Hamming–1 derivation in #secref("subsec:four-edge-x-witness"). This appendix uses that support to state A$Omega$D's retained edge-shell term $+ q$ and branch/hinge/branch reflected-return closure $Pi^(-) + H_(mu) + Pi^(+)$. The ternary hinge fibre is carried on the finite tesseract witness; it is not identical with the tesseract support.]



#aod-literature-note[Dyck/Catalan path combinatorics: Stanley #aod-cite("stanleyCatalan"), Flajolet–Sedgewick #aod-cite("flajoletSedgewick"). \

Markov kernels and random walks: Norris #aod-cite("norrisMarkov"), Levin–Peres–Wilmer #aod-cite("levinPeresWilmer"), Lawler–Limic #aod-cite("lawlerLimic").]



== Walk-support audit <app:rd-tests:audit>

A walk-support reduction records declared first-branch support, hinge recurrence, reflected return-branch support, the retained edge-shell term, and the A$Omega$D branch/hinge/branch closure. The single-hinge accessor $2 Pi + 1$ is used when the single-hinge symmetric reduction is declared. A kernel reduction records a normalized probability family over admissible Hamming–1 continuations.


#aod-provenance[#secref("subsec:four-edge-x-witness"), #eqref("eq:tesseract-admissible-boundary"), #eqnref("eq:branch-hinge-rd"), #eqnref("eq:branch-hinge-rd-symmetric"), #appref("app:rd-tests:corollaries").]
