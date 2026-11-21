// Native Typst port of sections/07_cell_measures_mappings.tex (verbatim scientific content).
#import "../preamble.typ": *

= Cell measures and mappings <sec:m3-cells>

Wave and coupling histories are governed by #eqref("eq:wave-update-trace")
and #eqref("eq:coupling-trace"). An observation map selects quantities from
those histories.


== Finite cells and weighted support <def:m3-cell-complex>


#aod-paragraph[Setup.]
Let $K_d$ be a finite set of oriented $d$-cells, with free chain group
$C_d = bb(Z)[K_d ]$, and let $B_d :C_d arrow.r C_(d - 1)$ be its
integer incidence map. A chain complex requires $B_(d - 1) B_d = 0$.
The vertices and edges of #eqref("eq:atomic-h1") specify a graph; additional
cells, their incidences and their admission hypotheses are separate choices.
For occupied support $S subset.eq K_d$, cell weights $w_d (c) gt.eq 0$, and
multiplicities $m(c) in bb(N)$, define

$ mu_d (S) = sum_(c in S) w_d (c), wide mu_d (S,m) = sum_(c in S) m(c)w_d (c). $ <eq:m3-support-measure>

Cell identity defines support; zero weight does not remove a cell from it.
The signed chain $z = sum_c n_c c$, its boundary $B_d z$, and occupied
support are distinct objects. A signed coefficient cancelling to zero
does not imply that either contributing occurrence was absent.


#aod-paragraph[Derivation.]
For disjoint supports, finite summation in #eqref("eq:m3-support-measure")
is additive. For overlapping supports it gives
$mu_d (S union T) = mu_d (S) + mu_d (T) - mu_d (S inter T)$.
An occurrence sum instead counts its declared multiplicities. Neither
identity relates a $d$-measure to a $(d - 1)$-measure without additional
weights and geometric hypotheses.


#aod-paragraph[Cubical boundary.]#aod-anchor(<prop:m3-cell-boundary>)
For an ordered product of vertices and oriented intervals, let
$i_1 < dots.c < i_d$ denote the interval coordinates and $c_(j, plus.minus)$
the endpoint faces. Set

$ partial c = sum_(j = 1)^d ( - 1)^(j - 1) (c_(j, +) - c_(j, -) ), wide partial^2 c = 0. $ <eq:m3-cubical-boundary>

Indeed, fixing two distinct interval coordinates in either order produces
the same face. Removing the earlier coordinate changes the later index by
one, so the two incidence products have opposite signs. Each codimension-two
face cancels exactly once. Including all faces gives a cubical chain complex.


#aod-paragraph[Falsification.]
Counting $S inter T$ twice changes the support
measure whenever its weight is positive. A zero-weight shared face still
participates in #eqref("eq:m3-cubical-boundary").

#aod-provenance[#eqref("eq:atomic-h1"); #eqref("eq:afc-stokes-used");
#eqref("eq:m3-support-measure").]



== Folds and projections <prop:m3-fold-support>


#aod-paragraph[Setup.]
A family of group homomorphisms $F_d :C_d (K) arrow.r C_d (L)$ is a chain map precisely when

$ B_d^L F_d = F_(d - 1) B_d^K . $ <eq:m3-chain-map>

Such maps may supplement the retained inner identities and scope maps of
#eqref("eq:fold-outer-closure"). That construction alone does not assert
#eqref("eq:m3-chain-map") or preservation of #eqref("eq:m3-support-measure").


#aod-paragraph[Derivation.]
Commutation sends cycles to cycles, since $B^K z = 0$ implies
$B^L F z = F B^K z = 0$.


#aod-paragraph[Falsification.]
Identify distinct preimages through their equal projected coordinates:
unique reconstruction fails. Cubical incidence ($f = (16,32,24,8,1)$,
$partial^2 = 0$), 4D-to-3D trace projections, FRG ring fixtures and downstream
Euclidean $tau = 2 pi$ report coordinates remain separate declared
representations; structural fold/enclosure scale, localization-window extent,
native cadence and measured frequency carry distinct types so a scale label
alone never asserts a frequency law.

#aod-provenance[#eqref("eq:fold-outer-closure"); #eqref("eq:expose-inner-lineage");
#eqref("eq:m3-support-measure"); #eqref("eq:m3-chain-map").]



== Typed mappings and conditional error bounds <sec:m3-maps>
#aod-anchor(<def:m3-map>)


#aod-paragraph[Setup.]
Let $f:D subset.eq X arrow.r Y$ and $g:E subset.eq Y arrow.r Z$, with specified
quantity dimensions, units and admissibility conditions. Composition requires
$f(D) subset.eq E$. A projection may be exact and many-to-one: its fibres
state the lost distinctions. A reconstruction error requires a specified
reconstruction map and a comparison metric; it is not implied by noninjectivity.


#aod-paragraph[Derivation.]#aod-anchor(<prop:m3-composed-bound>)
Suppose $Y,Z$ are normed spaces, both $f(D)$ and $tilde(f)(D)$
lie in $E$, and on the relevant domains
$bar.v.double tilde(f) - f bar.v.double lt.eq b_f$,
$bar.v.double tilde(g) - g bar.v.double lt.eq b_g$, and
$bar.v.double g(y) - g(y') bar.v.double lt.eq L_g bar.v.double y - y' bar.v.double$.
Inserting $g(tilde(f)(x))$ and applying the triangle inequality gives

$ bar.v.double tilde(g)(tilde(f)(x)) - g(f(x)) bar.v.double lt.eq b_g + L_g b_f . $ <eq:m3-composed-bound>

These are deterministic bounds in the specified output units.


#aod-paragraph[Falsification.]
An approximation taking an intermediate value outside $E$ violates the
composition hypotheses even if its error is small.

#aod-provenance[The declared domains and norm inequalities of
#secref("sec:m3-maps"); #eqref("eq:m3-composed-bound").]



== Finite joint laws and approximation scope <prop:m3-finite-law>


#aod-paragraph[Setup.]
Let a joint input $X$ have finite support $x_s$, probabilities
$p_s gt.eq 0$, $sum_s p_s = 1$, and let every $x_s$ be in the domain
of $h$. Shared coordinates refer to the same input variable throughout
a composition. The output moments are

$ overline(y) = sum_s p_s h(x_s ), wide Sigma_y = sum_s p_s (h(x_s ) - overline(y))(h(x_s ) - overline(y))^T . $ <eq:m3-finite-law>


#aod-paragraph[Derivation.]
Finite expectation gives #eqref("eq:m3-finite-law") directly. For any vector
$v$, $v^T Sigma_y v = sum_s p_s [v^T (h(x_s ) - overline(y))]^2 gt.eq 0$, so
singular positive-semidefinite covariance is admissible. If $h$ is affine,
$h(x) = A x + b$, substitution gives $Sigma_y = A Sigma_x A^T$ exactly.
If a nonlinear $h$ is differentiable at the input mean $overline(x)$,
its Jacobian gives the first-order covariance:

$ Sigma_(y,upright("lin")) = J(overline(x)) Sigma_x J(overline(x))^T . $ <eq:m3-linear-covariance>

Adequacy for a specified output requires control of the omitted remainder
or a comparison with the full joint law. The exact output moments use
the specified joint law. A constant output on the entire supplied support
has zero variance, since every deviation in #eqref("eq:m3-finite-law") vanishes.


#aod-provenance[#eqref("eq:m3-finite-law"); #eqref("eq:m3-linear-covariance").]



== Observation-map identifiability <prop:m3-atomic-gain>


#aod-paragraph[Setup.]
Use two already admitted recurrent coupled lineages compared by
#eqref("eq:relational-time"), with positive window counts $N_i ,N_j$.
Suppose an observation law has free positive gains $g_i ,g_j$ and assigns
equivalent cycles $C_i = g_i N_i$, $C_j = g_j N_j$.
Fixing a reference scale fixes $g_j$ but supplies no constraint on $g_i slash g_j$.

#aod-paragraph[Derivation.]
For any positive proposed ratio $R$, choosing
$g_i = R g_j N_j slash N_i$ gives $C_i slash C_j = R$, preserving both native
histories and the reference normalization. Within this free-gain observation
family, the ratio is underdetermined until an independently specified
observation law fixes the relative gain.

#aod-paragraph[Falsification.]
Selecting $g_i$ from an evaluation value of $R$ makes the resulting
ratio a calibration. Changing evaluation data alone must leave a previously
fixed model output unchanged.

#aod-provenance[#eqref("eq:relational-time"); #eqref("eq:cadence-ratio");
#eqref("eq:complete-wave-state"); #eqref("eq:complete-coupling-state").]



== Conditional SI observation interface <subsec:m3-conditional-si-interface>


#aod-paragraph[Setup.]
On a common compatible native window $omega$, bind physical turns through
an explicit apparatus observation map $cal(O)_i$ consuming the committed
current, lineage, contact, preparation and apparatus records, with exact
rational output $C_i in bb(Q)$ (allowing signed compared advance under a
signed net-winding plus endpoint-phase convention
$delta_(upright("end"),i) = phi.alt_(i,1) - phi.alt_(i,0)$, $phi.alt_(i,0) , phi.alt_(i,1) in [0,1)$):

$ C_i = cal(O)_i ( Gamma^W_i , Gamma^(times) , omega ,upright("preparation"),upright("apparatus")) in bb(Q), wide C_i^(upright("aff")) = g_i q_i ( omega ) + delta_(upright("end"),i) quad (g_i > 0). $ <eq:m3-observation-map>

The affine form $C_i^(upright("aff"))$ is an explicit specialization used only
when an independently bound apparatus model establishes a positive gain $g_i > 0$
and endpoint-phase correction on native reclosures $q_i ( omega )$; no physical
gain is selected by this interface, and distinct apparatuses keep calibration
uncertainty and shared-source dependence explicit.


#aod-paragraph[Derivation.]
Given a strictly positive calibrated reference advance $C_r > 0$ and calibrated
reference mean frequency $overline(f)^(upright("SI"))_r > 0$ over the same physical
interval, conditional interval duration $T_(omega) > 0$ and signed compared mean
rate $overline(f)^(upright("SI"))_a in bb(Q) upright("s")^(- 1)$ are

$ T_(omega) = frac(C_r, overline(f)^(upright("SI"))_r), wide overline(f)^(upright("SI"))_a = frac(C_a, C_r)overline(f)^(upright("SI"))_r , wide C_r > 0, overline(f)^(upright("SI"))_r > 0, C_a in bb(Q). $ <eq:m3-conditional-si-anchor>

Here $overline(f)^(upright("SI"))_a$ is a signed mean phase-advance rate over
$omega$; any unsigned or positive atomic resonance-frequency interpretation
additionally requires restricting to the narrower nonnegative specialization
$C_a gt.eq 0$ (or $C_a > 0$) and separate physical-realization premises. When
the affine specialization applies with one physical turn per certified native
reclosure and aligned endpoints ($g_a = g_r = 1$,
$delta_(upright("end"),a) = delta_(upright("end"),r) = 0$), $C_i = q_i ( omega ) gt.eq 0$
and #eqref("eq:m3-conditional-si-anchor") specializes to
$T_(omega) = q_r ( omega ) slash overline(f)^(upright("SI"))_r$ and
$overline(f)^(upright("SI"))_a = r_(a bar.v r) ( omega )overline(f)^(upright("SI"))_r$ via
#eqref("eq:wavelet-reference-timing"). Whenever $C_i eq.not q_i ( omega )$, gain and
endpoint terms remain explicit. A nonrecurrent shed wavelet with
$q_a ( omega ) = 0$ and $delta_(upright("end"),a) = 0$ still receives window
duration $T_(omega) > 0$ and zero mean rate without acquiring an intrinsic
resonance frequency.


#aod-paragraph[Specialization.]
Under the exact SI defining Cs-133 hyperfine anchor
$Delta nu_(upright("Cs")) = 9 thin 192 thin 631 thin 770 thin upright("s")^(- 1)$ and strictly
positive corrected Cs-equivalent reference advance $C_(upright("Cs")) > 0$, with
full-turn angular constant $tau = 2 pi$, #eqref("eq:m3-conditional-si-anchor")
specializes for signed $C_a in bb(Q)$ to

$ T_(omega) = frac(C_(upright("Cs")), Delta nu_(upright("Cs"))), wide overline(f)_a = Delta nu_(upright("Cs")) frac(C_a, C_(upright("Cs"))), wide Delta theta_a = tau C_a , wide overline(Omega)_a = tau overline(f)_a . $ <eq:m3-cs133-tau-interface>

Conditional SI anchoring is a typed mapping interface; independent empirical
frequency validation and physical realization budgets remain separate
evidenced claims.


#aod-paragraph[Falsification.]
Setting $C_r lt.eq 0$ or $C_(upright("Cs")) lt.eq 0$, equating a signed phase-advance
rate with an unsigned atomic resonance frequency without the nonnegative
domain and realization premises, claiming the affine form $C_i^(upright("aff"))$
for a nonlinear apparatus without independent binding, hiding nonzero endpoint
corrections or gain factors inside $q_i$, treating reproducing
$Delta nu_(upright("Cs"))$ as an independent prediction, or fitting $g_a slash g_r$
from evaluation data violates #eqref("eq:m3-observation-map")–#eqref("eq:m3-cs133-tau-interface")
and #secref("prop:m3-atomic-gain").

#aod-provenance[#eqref("eq:cadence-ratio"); #eqref("eq:wavelet-reference-timing");
#secref("prop:m3-atomic-gain"); #eqref("eq:m3-observation-map");
#eqref("eq:m3-conditional-si-anchor"); #eqref("eq:m3-cs133-tau-interface").]
