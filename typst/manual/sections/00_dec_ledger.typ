// Native Typst authority for Manual §4: pen-and-paper AFC raw execution, D.E.C. ledger, and RC-025/026/045.
#import "../preamble.typ": *

= Pen-and-Paper AFC Raw Execution and D.E.C. Ledger <manual:dec-ledger>


#aod-paragraph[Setup and calculation card.]
Declared $Q_4$ edge slots, integer weights, admissibility masks, and boundary/window
declarations serve as exact inputs under #secref("manual:calculation-spine").
Exact rational normalization, window clipping, and oriented flux evaluation produce
all inline fractions and ledger rows, audited directly against kernel, reversal, and
boundary-closure identities. This is a conditional D0 fixture with no measured target
or physical uncertainty model.

#aod-noteblock("Scope")[This section establishes the hand-calculation spine from one declared AFC edge computation to the A$Omega$D motif names used across the manual. It is a manual value ledger: it records exact edge weights, kernel fractions, route status, and boundary audits without introducing external postulates.]

#aod-provenance[#mainsection("main:sec:afc-stokes-seed")\;
#mainsection("main:subsec:q4-four-edge-implementation")\;
#mainsection("main:subsec:hinge-slide")\;
#mainsection("main:subsec:sadar")\;
#secref("manual:exact-arithmetic-presentation")\;
#secref("manual:cross-return-short-window").]

AFC runs raw; the committed trace records the run; A$Omega$D detectors read the trace
and name motifs (cross-return, yro route, duration-clipping, sheddic route, terminal
split, Tau-ring support, orbital retention, and collision-support status). A fixture
first declares the AFC scope $B$, boundary/region data, admissible channels, and
update rule before any normalization or motif detection occurs. D.E.C. denotes the
*Declared Edge Computation* ledger (always written in dotted form)—the manual value
container exposing one declared AFC edge computation step by step:

#math.equation(block: true, numbering: none, $ "AFC raw node" & arrow.r "D.E.C. ledger" arrow.r "exact kernel" arrow.r "blocked hinge" arrow.r "hinge slide", \ & arrow.r "oriented ADAR component" arrow.r "SADAR value" arrow.r "boundary audit". $)

Fixture-comparator rows form exact $delta_3$ tallies.


== D.E.C. row format <manual:dec-ledger:row-format>

#aod-paragraph[Setup.]
Each D.E.C. row records nine exact coordinates:

#math.equation(block: true, numbering: none, $ B, quad v, quad e, quad v_e , quad sigma (e), quad op("adm")(e;B), quad w(e;B), quad P(e;B), quad op("route")(e;B). $)

Here $B$ is the declared boundary/window, $v$ is the active node, $e$ is an
admissible edge slot, $v_e$ is the Hamming–1 neighbor reached by $e$,
$sigma (e) in brace.l - 1,0, + 1 brace.r$ is the local signed ternary state,
$op("adm")(e;B)$ records admissibility on $B$, $w(e;B)$ is the declared integer
weight, $P(e;B)$ is the exact normalized kernel fraction, and $op("route")(e;B)$
records returned, outgoing, blocked, slide, hinge, or pending route status.

At the register level, the reference engine verifies the exact 2-bit ternary lane
encoding via vector #raw("RC-045") (#raw("ternary_swar_and_trit_ratio")):
#raw("00") encodes optional dwell $0_D$, #raw("01") encodes $+1$ ($alpha$),
#raw("10") encodes $-1$ ($Omega$), and #raw("11") is preserved as the mandatory
structural hinge / carry barrier $0_H$. Both #raw("00") and #raw("11") read out as
signed value $0$, so preserving #raw("11") keeps removable dwell strictly separated
from the structural hinge under SWAR negation and dwell compaction.

#aod-paragraph[Signed channel views.]
An oriented ledger channel fixes one signed value; its reverse bookkeeping view has
equal magnitude and opposite sign, instantiating
#mainequation("main:eq:b-scoped-flux-antisymmetry"). A separately constructed
reverse channel retains its own directional RCD and must be evaluated independently.
Component-valued rows apply sign reversal and finite Stokes checks componentwise,
with #mainequation("main:eq:b-scoped-stokes") supplying the boundary sum.


== One-node D.E.C. ledger <manual:dec-ledger:one-node>

#aod-paragraph[Specialization.]
Declare one $Q_4$ vertex and its four Hamming–1 edge slots:

#math.equation(block: true, numbering: none, $ v = (0,0,0,0), wide brace.l e_1 ,e_2 ,e_3 ,e_4 brace.r . $)

Assign ternary edge states $sigma (e_i ) in brace.l - 1,0, + 1 brace.r$ and
anisotropic integer weights as recorded in the one-node D.E.C. ledger below.

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: (left, center, center, center, right, center, center),
    table.header(
      toprule,
      [edge], [neighbor], [$sigma (e)$], [admissible], [weight], [probability], [route],
      midrule,
    ),
    [$e_1$], [$(1,0,0,0)$], [$+ 1$], [1], [1], [$1 slash 8$], [outgoing],
    [$e_2$], [$(0,1,0,0)$], [$- 1$], [1], [1], [$1 slash 8$], [returned],
    [$e_3$], [$(0,0,1,0)$], [$0$], [1], [4], [$1 slash 2$], [hinge],
    [$e_4$], [$(0,0,0,1)$], [$+ 1$], [1], [2], [$1 slash 4$], [outgoing],
    bottomrule,
  )
}
  ],
  caption: [One-node D.E.C. ledger.],
) <tab:manual-dec-one-node-ledger>


== Exact kernel normalization <manual:dec-ledger:kernel>

#aod-paragraph[Derivation.]
For isotropic admissible branching over four successors,

#math.equation(block: true, numbering: none, $ P^(upright("iso")) (e_i ;B) = frac(1, 4). $)

For the declared anisotropic integer weights above,

#math.equation(block: true, numbering: none, $ w = (1,1,4,2), wide Z = 1 + 1 + 4 + 2 = 8, $)

yielding the exact normalized rational kernel

#math.equation(block: true, numbering: none, $ P^(upright("ani")) = (1 slash 8,1 slash 8,1 slash 2,1 slash 4). $)

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto),
    align: (left, right, center),
    table.header(
      toprule,
      [edge], [weight], [probability],
      midrule,
    ),
    [$e_1$], [1], [$1 slash 8$],
    [$e_2$], [1], [$1 slash 8$],
    [$e_3$], [4], [$1 slash 2$],
    [$e_4$], [2], [$1 slash 4$],
    bottomrule,
  )
}
  ],
  caption: [Exact anisotropic kernel fractions.],
) <tab:manual-dec-kernel-fractions>

#aod-literature-note[Markov kernels and random walks: Norris #aod-cite("norrisMarkov"), Levin–Peres–Wilmer #aod-cite("levinPeresWilmer"), Lawler–Limic #aod-cite("lawlerLimic").]


== Blocking rule <manual:dec-ledger:blocking-rule>

#aod-paragraph[Setup and falsification boundary.]
Blocking is zero admissibility. Once same-resolution optional dwell is blocked on
the declared scope, the dwell row is removed structurally from the successor pool and
the kernel is renormalized over the remaining admitted branch continuations,
instantiating #mainequation("main:eq:hinge-saturation"). An admitted dwell assigned
weight zero instead stays inside the structural family and satisfies only the
positive-support statement #mainequation("main:eq:hinge-saturation-weighted"): for
example, a weight-zero dwell alongside two branches of weights $1$ and $2$ satisfies
the weighted condition while leaving the admitted dwell family nonempty. The blocking
fixture below uses structural zero admissibility, not weight zero.

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto),
    align: (left, left),
    table.header(
      toprule,
      [rule], [meaning],
      midrule,
    ),
    [isotropic], [equal probability over admissible successors],
    [anisotropic], [unequal declared weights over admissible successors],
    [blocked], [zero admissibility on the declared scope],
    [hinge slide], [renormalization after same-resolution dwell is removed],
    [continuation trace], [repeated admitted node updates after hinge slide],
    bottomrule,
  )
}
  ],
  caption: [D.E.C. blocking and slide rules.],
) <tab:manual-dec-blocking-rules>


== Blocked hinge and hinge slide <manual:dec-ledger:hinge-slide>

#aod-paragraph[Derivation.]
When the prior hinge-state row $(e_3 ,0)$ attempts additional same-resolution dwell,
the declared scope sets $op("adm")(e_3 ,0_D ;B) = 0$. Only the optional-dwell row
$(e_3 ,0_D )$ (#raw("00") in the preserved 2-bit encoding of #raw("RC-045"),
#raw("ternary_swar_and_trit_ratio")) is removed before renormalization; the
mandatory structural hinge $0_H$ (#raw("11")) remains intact, and edge slot $e_3$
may re-enter only as an admitted branch state (#raw("01") or #raw("10")). Declare
the post-block slide pool

#math.equation(block: true, numbering: none, $ brace.l (e_1 , - 1),(e_2 , - 1),(e_3 , + 1) brace.r $)

with integer weights

#math.equation(block: true, numbering: none, $ w'((e_1 , - 1),(e_2 , - 1),(e_3 , + 1)) = (3,3,1), wide Z' = 3 + 3 + 1 = 7, $)

giving exact slide probabilities

#math.equation(block: true, numbering: none, $ P(e_1 , - 1) = 3 slash 7, wide P(e_2 , - 1) = 3 slash 7, wide P(e_3 , + 1) = 1 slash 7, $)

and returned versus outgoing projections

#math.equation(block: true, numbering: none, $ P_(upright("returned")) = 3 slash 7 + 3 slash 7 = 6 slash 7, wide P_(upright("outgoing")) = 1 slash 7. $)

#aod-paragraph[Falsification: three roles, two branch roles, and capacity counterexample.]
The four-channel kernel in #secref("manual:dec-ledger:kernel"),
#tabref("tab:manual-dec-kernel-fractions"), has role probabilities
$(P_(-) ,P_0 ,P_(+) ) = (1 slash 8,1 slash 2,3 slash 8)$. After blocking optional
dwell, three channel rows remain while their two-role projection is
$(P_(-) ,P_(+) ) = (6 slash 7,1 slash 7)$ and the structural hinge remains. Its
conditional binary role entropy
$- (6 slash 7) log_3 (6 slash 7) - (1 slash 7) log_3 (1 slash 7)$ lies below the
uniform maximum $log_3 2$ stated in
#mainsection("main:subsec:q4-hamming-ternary-kernel"). This conditional role entropy
is distinct from channel cardinality, $C_3 (k) = k$, and channel mutual information:
declaring the deterministic ternary permutation channel
$P_(01) = P_(12) = P_(20) = 1$ (all other entries zero) with uniform input gives
degree one per row while preserving the input bijectively, so
$I(X;Y) = H(X) = 1$ trit, exceeding $log_3 2$. No row-degree bound alone establishes
a universal channel-capacity bound.


== Field tunnelling: hinge-slide window clip <manual:dec-ledger:field-tunnelling>

#aod-noteblock("Data-support class")[Field tunnelling is a D0 exact internal fixture. It combines declared hinge-slide admissibility, exact slide-kernel fractions, window-clipped duration participation, and scalar tunnel contribution.]

#aod-paragraph[Setup.]
Field tunnelling is the retained passage of a field route through a blocked dwell
by slide-compatible successor support inside a declared boundary/window
$B = ( partial F, omega )$:

#math.equation(block: true, numbering: none, $ "blocked direct hinge" & arrow.r "declared slide pool" arrow.r "exact slide kernel" arrow.r "window clip", \ & arrow.r "tunnel contribution" arrow.r "boundary audit". $)

Fix the declared boundary/window

#math.equation(block: true, numbering: none, $ B = ( partial F, omega ). $)

The short-window examples declare neutral reflection, the native count duration
interface, and a same-domain window, clipping only
$rho^D = op("dur")(R D bowtie_B R^(upright("asym")) )$ while leaving $R D$ and
$upright("RCD")$ intact. At cut $B bar.v k$, declare a blocked direct dwell route
$e_0$ with

#math.equation(block: true, numbering: none, $ op("adm")(e_0 ;B bar.v k) = 0, $)

and declare the slide pool

#math.equation(block: true, numbering: none, $ op("Slide")_(mu) (B bar.v k) = brace.l s_1 , dots.h ,s_n brace.r . $)

#aod-paragraph[Derivation.]
Normalize strictly after the slide pool is declared:

#math.equation(block: true, numbering: none, $ Z_(upright("slide")) (B bar.v k) = sum_(s_i in op("Slide")_(mu) (B bar.v k)) w(s_i ;B bar.v k), wide P_(upright("slide")) (s_i ;B bar.v k) = frac(w(s_i ;B bar.v k), Z_(upright("slide")) (B bar.v k)). $)

For each slide-compatible successor $s_i$, clip duration participation and form pressure:

#math.equation(block: true, numbering: none, $ rho^D_(omega ,s_i) (B) = min (R D_(s_i) (B), bar.v omega bar.v_(s_i) ), wide p^D_(s_i) (B) = C_(3,s_i) rho^D_(omega ,s_i) (B). $)

Let $op("Out")_(mu) (B bar.v k) subset.eq op("Slide")_(mu) (B bar.v k)$ contain the
declared outgoing successors. Their scalar tunnel projection is

#math.equation(block: true, numbering: none, $ T^D_(upright("tunnel")) (B bar.v k) = sum_(s_i in op("Out")_(mu) (B bar.v k)) P_(upright("slide")) (s_i ;B bar.v k) thin p^D_(s_i) (B), $)

and with oriented attention declared, the oriented tunnel flux is

#math.equation(block: true, numbering: none, $ Phi^D_(upright("tunnel")) (B bar.v k) = sum_(s_i in op("Out")_(mu) (B bar.v k)) P_(upright("slide")) (s_i ;B bar.v k) thin p^D_(s_i) (B) thin A_(s_i) (B). $)

#aod-paragraph[Specialization.]
Using the hinge-slide pool from #secref("manual:dec-ledger:hinge-slide"), declare
the outgoing tunnel branch

#math.equation(block: true, numbering: none, $ s_(upright("tunnel")) = (e_3 , + 1), wide P_(upright("tunnel")) = 1 slash 7, $)

with support, window, and channel factor

#math.equation(block: true, numbering: none, $ R D_(s_(upright("tunnel"))) = 5, wide bar.v omega bar.v_(s_(upright("tunnel"))) = 2, wide C_(3,s) = 3. $)

Then

#math.equation(block: true, numbering: none, $ rho^D_(omega ,s_(upright("tunnel"))) = min (5,2) = 2, wide p^D_(s_(upright("tunnel"))) = 3 dot.op 2 = 6, $)

yielding

#math.equation(block: true, numbering: none, $ T^D_(upright("tunnel")) = (1 slash 7) dot.op 6 = 6 slash 7. $)

If all three slide successors carry pressure $6$, total expected pressure across the
normalized pool is $(3 slash 7 + 3 slash 7 + 1 slash 7) dot.op 6 = 6$, while the
outgoing projection remains $6 slash 7$ under the same kernel.

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto),
    align: (left, left),
    table.header(
      toprule,
      [row], [value],
      midrule,
    ),
    [direct hinge admissibility], [$op("adm")(e_0 ;B bar.v k) = 0$],
    [slide pool], [$brace.l (e_1 , - 1),(e_2 , - 1),(e_3 , + 1) brace.r$],
    [slide weights], [$(3,3,1)$],
    [slide probabilities], [$(3 slash 7,3 slash 7,1 slash 7)$],
    [tunnel branch], [$(e_3 , + 1)$],
    [$P_(upright("tunnel"))$], [$1 slash 7$],
    [$R D_s$], [$5$],
    [$bar.v omega bar.v_s$], [$2$],
    [$rho^D_(omega ,s)$], [$2$],
    [$C_(3,s)$], [$3$],
    [$p^D_s$], [$6$],
    [$T^D_(upright("tunnel"))$], [$6 slash 7$],
    bottomrule,
  )
}
  ],
  caption: [Field tunnelling hinge-slide window-clip fixture.],
) <tab:manual-field-tunnelling-fixture>


== D.E.C. row-pair to ADAR and SADAR <manual:dec-ledger:adar-sadar>

#aod-paragraph[Specialization.]
A routed D.E.C. row-pair supplies the declared returned-current pair promoted to an
oriented ADAR component on $B$. Declaring

#math.equation(block: true, numbering: none, $ A_(12) = 1 slash 3, wide rho^D_(omega) = 4, wide C_3 = 3 $)

produces

#math.equation(block: true, numbering: none, $ p^D = C_3 rho^D_(omega) = 12, wide SADARop_B = p^D A_(12) = 12(1 slash 3) = 4, $)

and reversing orientation yields exact antisymmetry:

#math.equation(block: true, numbering: none, $ A_(21) = - 1 slash 3, wide SADARop_B = - 4. $)


== Continuous $Q_4$ chiral-flip walk and Disoma Stokes balance <manual:dec-ledger:chiral-flips>

#aod-paragraph[Setup and engine verification.]
The reference engine (#raw("python3 -B -m manual.engine --sector boundary_sadar")
and #raw("aod-core --verify-vectors --check-zero-float")) executes the
single-carrier boundary chiral flip via vector #raw("RC-025")
(#raw("dec_chiral_flip_walk"), cuts $1$–$2$: #raw("B_flip|1"), #raw("B_flip|2"))
and the two-carrier Disoma Stokes encounter via vector #raw("RC-026")
(#raw("dec_two_carrier_chiral_stokes"), cut $3$: #raw("B_disoma|3")), cross-referenced
with the preserved 2-bit ternary lane codec of #raw("RC-045")
(#raw("ternary_swar_and_trit_ratio")). Both walks reside together in the single
deterministic CSV ledger
#raw("manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv") without
hidden state mutation.

#aod-paragraph[Single-carrier $Q_4$ boundary walk (#raw("RC-025")).]
Declare interior region $R_(upright("core")) = brace.l 0000, 0001, 0010, 0011 brace.r subset V(Q_4)$,
typed boundary $partial_T R_(upright("core"))$, active vertex $v_0 = 0000$, and
committed incoming ancestor leg $e_3$ carrying $D_(alpha) = ( + 1, - 1)$.
At cut $1$ (#raw("B_flip|1")), the four candidate rows across the three fresh
Hamming–1 slots carry integer weights $(3, 3, 4, 1)$ on $(e_0 , - 1)$, $(e_1 , - 1)$,
optional dwell $(e_2 , 0_D)$, and boundary-crossing branch $(e_2 , + 1)$, giving
$Z = 11$ and exact fractions $(3 slash 11, 3 slash 11, 4 slash 11, 1 slash 11)$.
At cut $2$ (#raw("B_flip|2")), active #raw("xxxxx... is x") sameness reduction blocks
optional dwell—$op("adm")(e_2 , 0_D ; B_(upright("flip")) bar.v 2) = 0$ removes
lane #raw("00") ($m = 0$) while preserving the mandatory structural hinge $0_H$
(#raw("11") in #raw("RC-045")) and keeping pre-block integer weights $(3, 3, 1)$
intact with $Z' = 7$. Traversing the boundary-crossing slide branch $(e_2 , + 1)$
across $partial_T R_(upright("core"))$ into exterior vertex $0100$ flips chirality
across $0_H$ from $D_(alpha) = ( + 1, - 1)$ to $D_(Omega) = ( - 1, + 1)$ with
$P_(upright("tunnel")) = 1 slash 7$ and $T^D_(upright("tunnel")) = 6 slash 7$; the
prior interior trace on cuts $1$–$2$ remains committed without retroactive overwrite.

#figure(
  kind: image, [
#include "../../lib/figures/manual/dec_hinge_slide_chiral_vertex.typ"
  ],
  caption: [Boundary-Feynman $Q_4$ D.E.C. walk across $partial_T R_(upright("core"))$ (#raw("RC-025")): live #raw("xxxxx... is x") dwell block ($m = 0$, structural $0_H$ preserved), exact slide renormalization ($Z' = 7$), and post-hinge chiral flip $D_(alpha) arrow.r D_(Omega)$ into vertex $0100$.],
) <fig:manual-dec-chiral-flip-walk>

#aod-paragraph[Two-carrier Disoma Stokes encounter (#raw("RC-026")).]
At cut $3$ (#raw("B_disoma|3")), declare enclosing scope
$cal(B)_(12) = ( partial F_(12) , omega_(12) )$ with $bar.v omega_(12) bar.v = 4$,
$upright("RCD")_(12) = 5 arrow.r.double rho^D_(omega) = 4$,
$C_3 = 3 arrow.r.double p^D_(12) = 12$, and six shared interface seats
($i_(12) = 1 slash 6$). Opposing chiralities $chi_1 = + 1$ ($D_(alpha)$ in $R_1$)
and $chi_2 = - 1$ ($D_(Omega)$ in $R_2$) yield $Delta chi^(upright("lag"))_(12) = + 2$,
$A_(12) = + 1 slash 3$, $phi.alt_(12) = + 4$, and $phi.alt_(21) = - 4$. Finite
Stokes cancels opposite oriented interface contributions in the enclosing sum,

#math.equation(block: true, numbering: none, $ S_(upright("int")) (R_1 union R_2 ; cal(B)_(12) ) = phi.alt_(12) + phi.alt_(21) = + 4 + ( - 4) = 0, $)

while both channel histories remain causally operative at cut $k + 1$: with both
channels present, $(S_(1,k + 1) , S_(2,k + 1) ) = ( - 4, + 4)$, whereas structural
removal of $phi.alt_(21)$ changes Carrier 1's realized next state to $0$.
Zero enclosing sum does not erase operative history.

#figure(
  kind: image, [
#include "../../lib/figures/manual/chiral_flip_boundary_stokes.typ"
  ],
  caption: [Two-carrier Disoma chiral exchange across $partial R_1 inter partial R_2$ (#raw("RC-026")). Opposite oriented interface fluxes cancel in $cal(B)_(12)$ ($+ 4 - 4 = 0$) while both bound channel histories remain operative at cut $k + 1$.],
) <fig:manual-chiral-stokes-feynman>


== Boundary closure and sheddic route audit <manual:dec-ledger:boundary-audit>

#aod-paragraph[Specialization.]
Declare total active pressure and closure threshold

#math.equation(block: true, numbering: none, $ P^D = 27, wide C_(upright("close")) = 24. $)

Then exact signed closure residual and nonnegative shedding surplus are

#math.equation(block: true, numbering: none, $ Delta_(upright("close")) = P^D - C_(upright("close")) = 3, wide X_(upright("shedding")) = max (0, Delta_(upright("close")) ) = 3. $)

This positive surplus matches the Dimonnanyro row, while explicit route identity and
retained-form witnesses remain separate audit obligations:

#math.equation(block: true, numbering: none, $ 1":"2":"9_(upright("yro")) = upright("Dimonnanyro"). $)

Fixture-comparator rows record exact $delta_3$ residuals; boundary-route rows record
boundary values and route audits separately.


== D.E.C. audit invariants <manual:dec-ledger:audit-hooks>

#aod-paragraph[Falsification invariants.]
Every valid D.E.C. ledger row carries the nine-tuple

#math.equation(block: true, numbering: none, $ B, quad v, quad e, quad v_e , quad sigma (e), quad op("adm")(e;B), quad w(e;B), quad P(e;B), quad op("route")(e;B), $)

and fails audit if any of the following four invariants is broken: exact kernel
normalization over admissible rows,

#math.equation(block: true, numbering: none, $ sum_e P(e;B) = 1, $)

structural zero probability for zero admissibility,

#math.equation(block: true, numbering: none, $ op("adm")(e;B) = 0 arrow.r.double P(e;B) = 0, $)

empty admitted optional-dwell family prior to hinge-slide renormalization,

#math.equation(block: true, numbering: none, $ upright("Adm")^0_B (e, sigma ) = emptyset, $)

and oriented SADAR antisymmetry across reverse channel views,

#math.equation(block: true, numbering: none, $ SADARop_B (C_(macron(e)) ) = - SADARop_B (C_e ). $)

Fixture-comparator rows form exact $delta_3$ tallies, and every Tau missing-burden
row preserves integer numerator/denominator provenance

#math.equation(block: true, numbering: none, $ upright("miss")_(tau) (K) = M_(upright("miss")) (K) slash M_(upright("ref")) (K), $)

with any decimal value treated strictly as a display coordinate.


== Tau missing-burden exact ratio <manual:dec-ledger:tau-ratio>

#aod-paragraph[Specialization.]
The Tau missing-burden diagnostic records exact rational provenance:

#math.equation(block: true, numbering: none, $ upright("miss")_(tau) (K) = frac(M_(upright("miss")) (K), M_(upright("ref")) (K)). $)

For the Dimonnanyro row ($1":"2":"9_(upright("yro"))$),

#math.equation(block: true, numbering: none, $ M_(upright("miss")) = 31, wide M_(upright("ref")) = 50, wide upright("miss")_(tau) (1":"2":"9_(upright("yro")) ) = frac(31, 50), $)

with decimal presentation coordinate

#math.equation(block: true, numbering: none, $ upright("missing_fraction_display") = 0.62. $)

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto),
    align: (left, left),
    table.header(
      toprule,
      [field], [meaning],
      midrule,
    ),
    [#raw("missing_num")], [numerator $M_(upright("miss"))$],
    [#raw("missing_den")], [denominator $M_(upright("ref"))$],
    [#raw("missing_frac_exact")], [exact ratio],
    [#raw("missing_fraction_display")], [decimal presentation field],
    bottomrule,
  )
}
  ],
  caption: [Tau missing-burden exact-ratio fields.],
) <tab:manual-dec-tau-missing-ratio-fields>


#aod-paragraph[Atomic leg and hinge role.]
Each D.E.C. row records the Hamming–1 base traversal separately from its ternary role.
Removing optional dwell sets $m = 0$ in $epsilon.alt 0_H (0_D )^m ( - epsilon.alt )$
while preserving the mandatory structural hinge $0_H$—verified in exact 2-bit
SWAR arithmetic by #raw("RC-045") (#raw("ternary_swar_and_trit_ratio")), where
live dwell compaction burns #raw("00") ($0_D$) while preserving #raw("11") ($0_H$)
and polar lanes #raw("01")/$+1$ and #raw("10")/$-1$. A slide pool is entered only
after that hinge, kernel normalization uses already admissible support, and repeated
updates remain continuation traces until actual closure and distinct-reclosure
witnesses establish wave admission.

