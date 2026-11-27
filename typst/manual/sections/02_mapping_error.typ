// Native Typst authority for Manual §6: typed maps, provenance DAG, and exact joint-law uncertainty.
#import "../preamble.typ": *

= Typed maps and exact uncertainty examples <manual:m3-mapping-error>


#aod-paragraph[Setup: typed-map arithmetic and five-boundary provenance stack.]
These examples instantiate #mainsection("main:sec:m3-maps") using exact rational
addition, subtraction, multiplication, and division under #secref("manual:calculation-spine"):
declare the inputs and map, compute exact outputs, and compare under a stated joint
uncertainty model. The examples below are conditional calculations; the published-input
example retains its measurement provenance. To separate source ancestry, map composition,
exact pushforward moments, evaluation-role isolation, and external reporting without silent
conflation, declare the five-boundary provenance stack

#math.equation(block: true, numbering: none, $ B_(upright("src")) arrow.r B_(upright("map")) arrow.r B_(upright("joint")) arrow.r B_(upright("role")) arrow.r B_(upright("ext")) . $)

Every input and output record across $B_(upright("src")) arrow.r B_(upright("map"))$ retains
quantity kind, dimension, unit, admissible bounds, scope, and lineage. Dimensions use the
declared ordered basis length, time, and count; native counts, cycle counts, and
dimensionless report coordinates remain distinct through kind and unit checks. Every
parameter binds a source identity, payload key, exact value, dimension, and origin. Raw
inputs bind their values to trusted source payloads, intermediate values carry a
reproducible upstream execution, and map versions, code, specifications, inputs, and source
payloads receive separate digests.


#aod-paragraph[Derivation: typed composition, role firewalls, and exact projection.]
In the worked composition $x = 3$, $f(x) = 2 x$, and $g(y) = 2 y$, the output is $12$.
Both stages retain the same factor-source identity, so that source appears once in the
composed dependency set rather than being duplicated as two independent inputs. Composition
requires the complete first codomain to lie inside the second domain, and mismatched
dimensions, units, scopes, or lineages reject composition. At $B_(upright("role"))$,
evaluation-role sources reject both direct use in a prediction and indirect use through
upstream provenance; fitted parameters require declared calibration exposure and an
applicable calibration budget component.

Information loss under projection is tracked without inventing scalar errors. The map
$P(x, h) = x$ sends $(3, 0)$ and $(3, 1)$ to the same scalar while retaining both original
input records in execution provenance. Its arithmetic error is zero, recovering $h$ from
the projected scalar is nonunique, and no scalar reconstruction error is assigned without
a declared task metric. Affine injectivity is checked by exact matrix rank, whereas
unproved nonlinear injectivity remains unknown.


#aod-paragraph[Derivation: finite joint laws versus linearized diagnostics.]
Across $B_(upright("joint"))$, all finite probabilities are declared model inputs. For each
stated finite joint law, the implementation enumerates all atoms and computes the exact
mean and variance of #mainequation("main:eq:m3-finite-law"), alongside the distinct
first-order diagnostic #mainequation("main:eq:m3-linear-covariance"). Covariance validation
uses exact rational Schur complements and retains singular positive-semidefinite matrices;
missing covariance is never replaced by zero, and any supplied covariance matrix that
disagrees with the supplied joint law is rejected.

Two finite controls share the law
$Pr(delta = - 1 slash 100) = Pr(delta = 1 slash 100) = 1 slash 4$ and
$Pr(delta = 0) = 1 slash 2$. For the dimensionless interval model
$T = 1 slash [(1 + delta)(1 - delta)]$, the first-order variance vanishes while exact
enumeration gives

#math.equation(block: true, numbering: none, $ bb(E)[T] = frac(19999, 19998), wide op("Var")(T) = frac(1, 399920004) > 0. $)

For the near-cancelled product $F = (1 + delta)(1 - 999 delta slash 1000)$, exact
evaluation gives

#math.equation(block: true, numbering: none, $ bb(E)[F] = frac(19999001, 20000000), wide op("Var")(F) = frac(1018001, 400000000000000), wide J Sigma J^(sans("T")) = frac(1, 20000000000). $)

The full variance is more than forty times the nonzero linearized diagnostic
($1018001 slash 20000$), with exact mean shift $- 999 slash 20000000$: small marginal
uncertainties therefore do not certify an omitted nonlinear contribution.
A third control takes $R = 1 + delta$ and $f = 1 - delta$ with probabilities
$(1 slash 4, 1 slash 2, 1 slash 4)$ at $delta = (- 1 slash 2, 0, 1 slash 2)$, yielding
$bb(E)[R f] = 7 slash 8$, $op("Var")(R f) = 1 slash 64$, and zero first-order variance.

For the original reciprocal interval example, let $y = d slash s = plus.minus a$ with equal
probabilities, $a = 1 slash 1000$, and $U = T slash s = 1 slash (1 + y) + y$. Direct
enumeration gives

$ bb(E)[U] = frac(1, 1 - a^2) = frac(1000000, 999999), wide op("Var")(U) = frac(a^6, (1 - a^2 )^2) = frac(1, 999998000001000000). $ <eq:manual-m3-original-interval>

Its linearized variance is zero because the two input corrections are the same random
variable. For the original product, let $x = (- epsilon, 0, epsilon)$ have probabilities
$(1 slash 4, 1 slash 2, 1 slash 4)$ with $epsilon = 1 slash 1000$,
$delta = 1 slash 1000000$, $b = 1 - delta$, and $V = F \/ upright("Hz") = (1 + x)(1 - b x)$.
Then

$ bb(E)[V] = 1 - frac(b epsilon^2, 2), wide op("Var")(V) = frac(delta^2 epsilon^2, 2) + frac(b^2 epsilon^4, 4). $ <eq:manual-m3-original-product>

The first term is the linearized variance; the full variance is $500000.0000005$ times as
large. These two original joint laws retain input dependence and remain distinct from the
three controls above. The authenticated original probe and its unchanged failing historical
implementation are retained with their source and output bindings; the successor computes
exact finite-law moments, while covariance alone still leaves nonlinear output moments
unresolved.


#aod-paragraph[Derivation: legitimate cancellation, moment limits, and composed bounds.]
Zero derivatives do not certify zero dispersion. Let $X$ take $- epsilon, 0, epsilon$ with
probabilities $1 slash 4, 1 slash 2, 1 slash 4$ ($epsilon > 0$): for $h(X) = X^2$, the
linearized variance at zero vanishes while the exact mean and variance are
$epsilon^2 slash 2$ and $epsilon^4 slash 4$, contradicting any zero-spread claim under
#mainequation("main:eq:m3-finite-law"). Conversely, genuine shared-disturbance cancellation
holds in $(a + X) - (b + X) = a - b$ (replacing $X$ by two independent copies alters the
joint law): an affine endpoint difference with means $(7, 2)$ and covariance
$( mat(delim: #none, 4, 4; 4, 4) )$ yields mean $5$ and exact variance $0$, and $x slash x$
is constant on nonzero support with variance $0$. For a nonlinear map supplied only with
input moments, the first-order diagnostic is retained while output uncertainty remains
unresolved: two laws sharing mean $0$ and variance $1$—mass $1 slash 2$ at $- 1, 1$ versus
masses $(1 slash 8, 3 slash 4, 1 slash 8)$ at $(- 2, 0, 2)$—produce squared-output variances
$0$ and $3$, respectively, demonstrating that input means and covariances do not determine
nonlinear output uncertainty.

Deterministic error envelopes instantiate #mainequation("main:eq:m3-composed-bound"). For
$g(y) = 1 slash y$ on a positive interval with lower endpoint $a > 0$, $L_g = a^(- 2)$
suffices. Assuming uniform bounds $b_f = 1 slash 100$ and $b_g = 1 slash 1000$, an inner
image in $[1, 2]$, and the outer reciprocal law on $[1 slash 2, 3]$, the enlarged image
remains inside the outer domain with $L_g = 4$, giving the composed bound $41 slash 1000$.
As admissible intermediate values approach zero, no finite uniform bound follows: a
denominator domain containing zero returns an undefined-or-unbounded status with no finite
symmetric interval. A discrete joint law can still be evaluated whenever its actual
denominator support excludes zero, even if its mean lies at an invalid linearization point
(in which case the first-order diagnostic is unavailable).

Each output carries a separate budget with matching dimensions and units across arithmetic,
resolution, window, model discrepancy, calibration, propagation, solver, and comparison
contributions. Bounds and standard uncertainties bind evidence directly to that output;
unknown and inapplicable components carry reasons and no numerical values. A finite-law
standard uncertainty binds the declared law and its variance, whereas the affine moment
route binds complete input moments, and a deterministic bound cannot be relabelled as a
standard deviation. Defining constants have zero measurement variance while absent
realization uncertainty remains unknown; because these examples supply no physical
discrepancy model, their physical budget remains partial despite exact finite arithmetic.
Synthetic printed-decimal controls test units and half-last-place bounds under nearest
rounding, printed zero requires a source convention or remains unknown, and numerical
interpretation is checked separately from raw-byte integrity.


#aod-paragraph[Specialization: source quantities and worked experimental routes.]#aod-anchor(<manual:m3-experimental-inputs>)
A source quantity binds its payload, locator, kind, dimension, unit, domain, meaning, and
uncertainty category, and any separately supplied trusted source must agree with that
binding; relabelling a dimensionless input as a frequency therefore fails even when its
numerical distribution is unchanged. Every conversion is a declared map with its own source
and uncertainty, and an aggregate and its components cannot both contribute to the same
budget.

The reusable record preserves original inputs, operator, intermediate moments or intervals,
exact outputs, and reporting convention. For a declared input with mean $0$ and variance
$2$, affine propagation returns those moments exactly; two uses of the same input give
variance $0$ for their difference and $8$ for their sum. Under declared conversion laws
$2 X thin upright("Hz")$ and $3 X thin upright("s")$, the variances are
$8 thin upright("Hz")^2$ and $18 thin upright("s")^2$ with covariance
$12 thin upright("Hz") thin upright("s")$. For $X in [1, 3]$, reciprocal interval
evaluation returns $[1 slash 3, 1]$, whereas an interval containing zero yields no finite
reciprocal enclosure. The nonlinear moment-only route retains its diagnostic and leaves
uncomputed output moments unresolved; variances remain exact rationals without rounding a
square root into a claimed exact standard uncertainty.

The published hydrogen example uses the corrected Table VI value and keeps the reference
and wall corrections already included in its input. Its quoted uncertainty remains a source
report that supplies neither missing raw campaign data nor a joint law, while correction
execution and passive comparison assessment remain separate. The paper's mean
$1420405751.768 thin upright("Hz")$ and one-sigma uncertainty
$0.002 thin upright("Hz")$ #aod-cite("hellwig-hydrogen-1970") also provide a
single-quantity moment example: treating the reported value as its mean, the identity map
retains variance $1 slash 250000 thin upright("Hz")^2$ without reconstructing component
covariance or a probability distribution. These routes and reduction controls are
reproduced by #raw("python3") #raw("manual/scripts/aod_experimental_comparison.py")
#raw("--check") from
#raw("manual/data/experimental_comparison/experimental_input_comparison.json").


#aod-paragraph[Falsification: execution checks and mutation guards.]
Running #raw("python3 manual/scripts/aod_mapping_error.py --check") reconstructs
#raw("manual/data/mapping_error/mapping_error.json"). The test suite mutates source
payloads, input values, upstream execution digests, parameter origins, dimensions, domain
bounds, projection claims, covariance matrices, missing error components, and purported
physical completion, executing the affected validator on every mutation with identical
guards active under Python optimization (#raw("-O")).


== Five-boundary provenance DAG and exact joint-law variance ledger <manual:m3-maps:dec-joint-laws>

Across the five-boundary stack
$B_(upright("src")) arrow.r B_(upright("map")) arrow.r B_(upright("joint")) arrow.r B_(upright("role")) arrow.r B_(upright("ext"))$,
vector #raw("RC-036") (#raw("manual/data/boundary_sadar/typed_map_joint_law_ledger.csv"),
verified by #raw("python3 -B -m manual.engine") #raw("--sector") #raw("boundary_sadar")
and #raw("aod-core") #raw("--verify-vectors") #raw("--check-zero-float")) compiles the
exact rational means, exact pushforward variances, and naive first-order linearized
variances across all five nonlinear and shared-disturbance fixtures (@tab:manual-typed-map-joint-laws),
while deduplicating diamond provenance ($x = 3 arrow.r 6 arrow.r 12$ retains one unique
source rather than two independent copies) and enforcing disjoint calibration, validation,
and held-out boundary scopes (@fig:manual-typed-map-variance-feynman).


#figure(
  kind: image, [
#include "../../lib/figures/manual/typed_map_variance_feynman.typ"
  ],
  caption: [Typed boundary-provenance DAG, evaluation-role firewall, and exact versus linearized variance ratios across all five joint-law fixtures (#raw("typed_map_joint_law_ledger.csv")).],
) <fig:manual-typed-map-variance-feynman>


#figure(
  kind: table, [
#{
  set text(size: 7.8pt)
  set par(justify: false)
  table(
    columns: (1.50fr, 1.45fr, 1.25fr, 1.65fr, 0.95fr, 1.40fr),
    align: (left, left, right, right, right, right),
    inset: (x: 3.5pt, y: 4pt),
    table.header(
      toprule,
      [Law ID], [Map formula], [Exact mean], [Exact variance], [Linear var], [Exact / linear],
      midrule,
    ),
    [#raw("T_interval_100")], [$frac(1, (1 + d)(1 - d))$], [$frac(19999, 19998)$], [$frac(1, 399920004)$], [$frac(0, 1)$], [div-by-zero ($op("Lin") = 0$)],
    [#raw("F_near_cancel_100")], [$(1 + d)(1 - frac(999 d, 1000))$], [$frac(19999001, 20000000)$], [$frac(1018001, 4 dot.op 10^(14))$], [$frac(1, 2 dot.op 10^(10))$], [$frac(1018001, 20000)$],
    [#raw("Rf_symmetric_2")], [$(1 + d)(1 - d)$], [$frac(7, 8)$], [$frac(1, 64)$], [$frac(0, 1)$], [div-by-zero ($op("Lin") = 0$)],
    [#raw("U_orig_recip_1000")], [$frac(1, 1 + y) + y$], [$frac(1000000, 999999)$], [$frac(1, 999998000001000000)$], [$frac(0, 1)$], [div-by-zero ($op("Lin") = 0$)],
    [#raw("V_orig_prod_1000")], [$(1 + x)(1 - b x)$], [$frac(1999999000001, 2 dot.op 10^(12))$], [$frac(1000000000001, 4 dot.op 10^(24))$], [$frac(1, 2 dot.op 10^(18))$], [$frac(1000000000001, 2000000)$],
    bottomrule,
  )
}
  ],
  caption: [Exact rational pushforward moments versus naive first-order linearization across typed-map joint laws (#raw("RC-036")).],
) <tab:manual-typed-map-joint-laws>
