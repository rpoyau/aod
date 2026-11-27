// Native Typst authority for Manual §7: temporal observation, conditional SI bridge, and RC-037 ledger.
#import "../preamble.typ": *

= Temporal records and SI mapping <manual:m3-temporal>


#aod-paragraph[Setup: native input, observation domain, and five-boundary stack.]
To isolate native coupled recurrence from conditional SI unit stipulation and held-out
transfer falsification, declare the five-boundary metrology stack

#math.equation(block: true, numbering: none, $ B_(upright("pair")) (0, 30] arrow.r B_(upright("lag")) arrow.r B_(upright("bridge")) arrow.r B_(upright("val")) arrow.r B_(upright("ext")) . $)

Inside $B_(upright("pair")) (0, 30] arrow.r B_(upright("lag"))$, the temporal adapter
consumes the admitted recurrent waves and repeated coupled returns of
#mainequation("main:eq:wave-update-trace"), #mainequation("main:eq:coupling-trace"), and
#mainequation("main:eq:rcd-additive-realization"). Every bound record retains population,
preparation, directed couplings, complete committed prefixes, pending returns, integer
window endpoints, signed phase bias, lag, and directional reflection count; directional
RCD, bias, lag, and drift are recomputed directly from those committed records. Structural
RD belongs to each retained support, whereas duration participation requires a compatible
window map and is never supplied by a bare reclosure count. Displacement traversals,
hinges, dwells, emitted ticks, and returned clicks keep separate counts, and positive
reclosure counts without repeated cross-returns do not supply RCD. Two named readouts
replaying one context share its history rather than yielding independent samples, and
changing population, current, or window requires full replay rather than a cached scalar.

On the worked half-open window $(0, 30]$, the compared lineage has four closures at cuts
$2, 10, 18, 26$ and the reference lineage has three closures at cuts $2, 12, 22$.
Excluding the initial origin closure of each recurrent lineage yields reclosure increments
$(3, 2)$, cadence ratio $op("biz")_(i bar.v j) = 3 slash 2$ (reverse $2 slash 3$),
additive directional durations $5$ and $7$ ($R D = 3$ with directional reflection counts
$(1, 1)$ versus $(2, 2)$ in the declared native count domain), and biases
$(1 slash 4, - 1 slash 4)$ giving unwrapped lag $3 slash 2$ (reverse $- 3 slash 2$).


#aod-paragraph[Derivation: declared apparatus bridge, conditional SI units, and gain non-identifiability.]
Crossing $B_(upright("bridge"))$ under
#mainsection("main:subsec:m3-conditional-si-interface"), an explicit apparatus observation
map $cal(O)_i$ (#mainequation("main:eq:m3-observation-map")) sends reference history
$Gamma_R$, window $omega$, population $cal(P)$, coupling history $E$, and preparation to
corrected Cs-referenced cycle equivalents, anchoring conditional duration via
#mainequation("main:eq:m3-conditional-si-anchor") and
#mainequation("main:eq:m3-cs133-tau-interface"):

$ hat(C)_(upright("Cs")) = g_(theta) ( Gamma_R , omega ,cal(P),E,upright("preparation")), wide hat(T) = frac(hat(C)_(upright("Cs")), Delta nu_(upright("Cs"))). $ <eq:manual-m3-cycle-bridge>

The exact defining frequency converts cycle equivalents to seconds, while the first map
requires its own observation and calibration evidence and never assigns a universal
duration to a native cut. The general map $cal(O)_i$ stays distinct from its affine
specialization $C_i^(upright("aff")) = g_i q_i ( omega ) + delta_(upright("end"),i)$
($g_i > 0$), and structural support scale, window extent, native cadence
(#mainequation("main:eq:wavelet-reference-timing")), observed turns, and SI frequency
remain separately typed. For stipulated cycle-equivalent gains $a_c, a_r > 0$ per native
return and defining reference
$f_(upright("Cs")) = 9 thin 192 thin 631 thin 770 thin upright("Hz")$ (without a physical
clock realization), the fixed-window bridge evaluates

#math.equation(block: true, numbering: none, $ T = frac(a_r N_r, f_(upright("Cs"))), wide macron(nu)_c = frac(a_c N_c, T), wide t_1 = t_0 + T. $)

The mapping binds both gains, coordinate and epoch, complete input records, defining
reference, and executable specification. At unit gain $a_c = a_r = 1$, the worked pair
gives $T = 2 slash f_(upright("Cs")) = 1 slash 4596315885 thin upright("s")$ and
$macron(nu)_c = 3 f_(upright("Cs")) slash 2 = 13788947655 thin upright("Hz")$. This
finite-window average and its derived reciprocal $1 slash macron(nu)_c$ supply no
independent validation; physical realization and drift, endpoint-phase, cycle-slip, and
temporal-dependence uncertainties stay unspecified, and gains are stipulated without
fitting hydrogen.

Because the countermodel family $g_(lambda)(Z) = 1 + lambda (55 - Z) slash 54$
($lambda > - 1$) satisfies $g_(lambda)(55) = 1$ and $g_(lambda)(1) = 1 + lambda$, the
$lambda = 0$ and $lambda = 1$ models preserve both the native records and the Cs anchor
while emitting distinct reports; relative gain therefore stays unidentified. Known
hydrogen values remain retrospectively exposed. Evaluation validates each frozen
prediction against its bound model inputs before target comparison, binds separate
prediction and target hashes (changing only the target alters the diagnostic residual
without touching prediction bytes), and freezes the uncertain input model, readouts,
reduction, candidate selection, stopping rule, and comparison criterion in a separately
bound plan whose mutation invalidates replay; a later freeze cannot render earlier target
exposure blind, and an atomic point prediction with complete uncertainty remains
unresolved.


#aod-paragraph[Specialization: held-out cross-field transfer, population controls, and causal intervention.]
At $B_(upright("val"))$, the retained direct-coupling transfer experiment calibrates on
its first half and validates on its second; each half carries exactly
$N_(0,upright("cal")) = N_(0,upright("val")) = 32$ reference reclosures. Freezing
$k_i = 32 slash N_(i,upright("cal"))$ predicts
$hat(N)_(0,upright("val")) = k_i N_(i,upright("val"))$ on the held-out half
(#tabref("tab:manual-m3-anchor-transfer")).

#figure(
  kind: table, [
#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.header(
      toprule,
      [Field], [$N_(i,upright("cal"))$], [$N_(i,upright("val"))$], [$hat(N)_(0,upright("val"))$], [$(hat(N)_(0,upright("val")) - 32) slash 32$],
      midrule,
    ),
    [A], [58], [48], [$768 slash 29$], [$- 5 slash 29$],
    [B], [151], [102], [$3264 slash 151$], [$- 49 slash 151$],
    bottomrule,
  )
}
  ],
  caption: [Frozen gains and subsequent reference-count transfer ($N_(0,upright("val")) = 32$).],
) <tab:manual-m3-anchor-transfer>

Both nonzero residuals ($- 5 slash 29$ and $- 49 slash 151$) falsify constant-gain
transfer and block promotion to a universal SI clock. They are exact count-transfer
discrepancies rather than measured Cs errors; refitting on the validation half removes the
test, and synchronized or overlapping windows retain statistical dependence.

Four population-control executions share two recurring $3":"4":"6$ background supports and
frozen counting windows: comparing $3":"2":"6$ with $3":"3":"6$ against the
$3":"3":"6$ vs $1":"2":"6$ baseline moves A counts from $99$ to $72$ and reference counts
from $31$ to $30$. Two post-prefix interventions activate a prepared $3":"4":"6$ local
support: coupling it only to A yields A counts $45, 42$ with reference $32, 32$; coupling
it only to the reference yields A counts $57, 47$ with reference $23, 23$. Complete
histories retain directed reflections and pending returns, whereas short count projections
never acquire RCD admission. Any physical test requires separately supplied corrected
cycle increments, a pre-registered tolerance, full apparatus/interrogation/endpoint/missed-cycle
accounting, no isotope-retention absorption of residuals, and an eight-component
uncertainty budget per seconds or hertz output.

Causal intervention verification separates two distinct executable surfaces: (1) the
self-contained #raw("RC-037") cut-by-cut causal simulator inside the canonical Python/Rust
reference engine (#raw("manual.engine --sector boundary_sadar") and
#raw("aod-core --verify-vectors --check-zero-float")), in which baseline and capacity-drop
runs share an identical committed prefix through cut $39$ ($k lt.eq 39$), the intervention
acts at cut $40$, and retention loss appears strictly later at cut $41$—changing observed
increments from $(6, 5)$ to $(2, 5)$ and, at unit gain, keeping
$T = 5 slash f_(upright("Cs"))$ fixed while shifting the mean frequency from
$6 f_(upright("Cs")) slash 5$ to $2 f_(upright("Cs")) slash 5$—while a hostile
feedback-disconnect mutation retains the intervention inputs yet leaves increments at
$(6, 5)$ and fails replay validation; and (2) the separately bound Matter I v2
#raw("--consumer-root") replay, which preserves declared-model status (native atomic
admission pending), retains historical v1/v2 fixture bytes, and identifies its two active
Main amendments separately.


#aod-paragraph[Falsification: execution scripts, mutation guards, and source precision.]
Running #raw("manual/scripts/aod_temporal_observation.py --check") rebuilds the native
adapter and mapping report (with #raw("--consumer-root") selecting the separately bound
Matter I replay); #raw("aod_temporal_anchor.py --check-data") replays the anchor transfer
and four population controls; and #raw("aod_manual_wavelet_si_alignment.py --check")
passively checks aligned wavelet, nonrecurrent localization, signed-advance, and
$tau$-angular specializations without mutating native transitions. Mutation tests reject
changed scopes, aliases, uncoupled records, invalid windows, scheduler substitutions,
nonpositive gains, disconnected causal feedback, and evaluation leakage. The BIPM
comparison preserves raw hashes, tests nearest rounding on nonzero entries, and records
conditional point-zero covariance transcriptions whose zero formatting and underflow
remain unresolved by source documents.


== Observed cycles and experimental reductions <manual:m3-metrology>


#aod-paragraph[Setup.]
Relational cadence compares retained closures on a matched bip window
(#mainequation("main:eq:wavelet-reference-timing")), and its apparatus map
(#mainequation("main:eq:m3-observation-map")) must keep current reclosures, shed
continuation, and recipient stages (#mainequation("main:eq:aod-wavelet-continuation"),
#mainequation("main:eq:shed-continuation-witness"),
#mainequation("main:eq:recipient-event-lattice")) distinct from oscillator cycles,
estimated atomic populations, and detector timestamps. A wavelet group can retain source
history without each packet denoting a measured microwave cycle; preparation, lineage,
coordinate, epoch, window, and detector response all belong to the map. The recurring
$3":"4":"6$ construction retains its own reflection-duration conditions, and $2 x = 6 n$ in
a restricted fold defines no universal atomic period.


#aod-paragraph[Derivation.]
For an observer coordinate in turns on $W = (k_0 ,k_1 ]$ with net integer winding
$C(W) in bb(Z)$ and endpoint fractions $0 lt.eq phi.alt_0 , phi.alt_1 < 1$,

$ A(W) = C(W) + phi.alt_1 - phi.alt_0 . $ <eq:manual-m3-observed-advance>

Downstream of Main's closure phase, endpoint terms cancel across shared cuts so adjacent
advances add and orientation reversal negates $A(W)$ while keeping turns and ratios exact;
angular reporting uses $theta = tau phi.alt$ ($tau = 2 pi$). Under passive lossless
transport, event identities satisfy
$N_(upright("emitted")) - N_(upright("arrived")) = P_1 - P_0$ (with endpoint pending
counts $P_i$), so arrival separation equals emission separation plus transit-delay change;
loss and detector inefficiency require separate counts. Observation does not alter source
dynamics, and routed packets alone supply neither recipient seating nor a reclosure beat
(#mainequation("main:eq:recipient-event-lattice")).


#aod-paragraph[Specialization and calibration.]
On $(10, 22]$, choosing compared winding $4$ with endpoints $(2 slash 3, 1 slash 6)$ and
reference winding $8$ with endpoints $(1 slash 4, 3 slash 4)$ gives via
#eqref("eq:manual-m3-observed-advance") the advances $A = 7 slash 2$ (splitting $2 + 2$ at
phase $5 slash 6$ yields $13 slash 6 + 4 slash 3 = 7 slash 2$) and $A_R = 17 slash 2$.
Under an independently justified Cs realization identifying $A_R > 0$ on the matched
coordinate, epoch, and window, #mainequation("main:eq:m3-conditional-si-anchor") and
#mainequation("main:eq:m3-cs133-tau-interface") yield

$ frac(A, A_R) = frac(7, 17), wide T = frac(A_R, f_(upright("Cs"))) = frac(17, 2 f_(upright("Cs"))), wide macron(nu) = frac(A, T) = frac(7 f_(upright("Cs")), 17). $ <eq:manual-m3-accumulated-si>

Full-turn angular reporting gives $Delta theta_a = (7 slash 2) tau$ and
$macron(Omega)_a = (7 slash 17) tau f_(upright("Cs"))$. Two boundary specializations of
#mainequation("main:eq:m3-observation-map") through
#mainequation("main:eq:m3-cs133-tau-interface") remain explicit under the same reference
anchor:

- #emph[Nonrecurrent or clipped localization.] With $q_a ( omega ) = 0$,
  $delta_(upright("end"),a) = 0$, and bound reference $C_(upright("Cs")) = 10$,
  $T_(omega) = 10 slash f_(upright("Cs"))$ and $macron(f)_a = Delta theta_a = macron(Omega)_a = 0$;
  $q_a = 0$ supplies neither intrinsic frequency nor phase lag, and no integer cut becomes
  a universal second.
- #emph[Signed compared advance against positive reference advance.] Using
  #eqref("eq:manual-m3-observed-advance") and
  $C_a^(upright("aff")) = g_a q_a + phi.alt_1 - phi.alt_0$ with $q_a = 0$, $g_a = 1$,
  $phi.alt_0 = 3 slash 4$, $phi.alt_1 = 1 slash 4$, and $C_(upright("Cs")) = 1$ gives
  signed $C_a = - 1 slash 2$, so #mainequation("main:eq:m3-cs133-tau-interface") yields
  $T_(omega) = 1 slash f_(upright("Cs"))$, $macron(f)_a = - f_(upright("Cs")) slash 2$,
  $Delta theta_a = - tau slash 2$, and $macron(Omega)_a = - tau f_(upright("Cs")) slash 2$.
  Nonnegative atomic resonance frequencies instead require $C_a gt.eq 0$ (or $> 0$) plus
  separate realization premises.

These conditional finite-window evaluations supply neither measured realization uncertainty
nor a universal seconds-per-bip conversion; fitting gains to a target cannot yield an
independent prediction.


#aod-paragraph[Specialization: historical H/Cs reductions, dependence, and comparison rules.]
For the hydrogen $21 thin upright("cm")$ ($1420.4 thin upright("MHz")$) hyperfine maser
chain, Hellwig et al. used continuous active masers and a signed heterodyne beat:

$ nu_H = 284 nu_R + nu_S + nu_B + delta_(upright("UTC")) + delta_N + delta_W + delta_D + delta_Z . $ <eq:manual-m3-hydrogen-reduction>

Here $nu_R approx 5 thin 000 thin 000 thin upright("Hz")$, $nu_S$ is the synthesizer
setting, and the $delta$ terms cover UTC transfer, reference, wall collisions,
second-order Doppler, and Zeeman shifts. Tables IV and VI give
$1 thin 420 thin 405 thin 751.7691 thin upright("Hz")$ and
$1 thin 420 thin 405 thin 751.7667 thin upright("Hz")$ (the latter already carries an
NP3-corrected zero-wall intercept, so re-adding $delta_N$ or $delta_W$ double-counts it);
their printed mean is $1 thin 420 thin 405 thin 751.7679 thin upright("Hz")$, reported as
$1 thin 420 thin 405 thin 751.768 plus.minus 0.002 thin upright("Hz")$ #aod-cite("hellwig-hydrogen-1970"),
without reconstructing unavailable raw phase or tuning records.

In a caesium fountain, calibrated population estimates ($N_3 + N_4 > 0$) form
$p = N_4 slash (N_3 + N_4 )$ for line-centre estimation. The August 2013 NIST-F2 evaluation
reports $u_A = 0.44 times 10^(- 15)$ (already containing spin-exchange statistics) and
$u_B = 0.16 times 10^(- 15)$, distinct from Table 1's typical
$u_B = 0.11 times 10^(- 15)$; multiplying by $f_(upright("Cs"))$ converts each to hertz,
upper bounds remain bounds, and rounded synthesizer settings do not specify the exact
carrier #aod-cite("heavner-nist-f2-2014"). Raw replay requires campaign populations, servo
records, and covariance, while gravity and Doppler shifts retain their experimental roles
rather than becoming A$Omega$D dynamical premises.

For model output $A$ and comparison $E$ in common units under a justified joint
second-moment model,

$ op("Var")(A - E) = op("Var")(A) + op("Var")(E) - 2 op("Cov")(A,E). $ <eq:manual-m3-residual-dependence>

Repeated use of one uncertain source retains this covariance ($A = E = X$ cancels, whereas
$A = X, E = - X$ yields $4 op("Var")(X)$). Published uncertainties do not define a finite
probability law; shared windows and references remain correlated, while the defining Cs
integer carries zero uncertainty. Isotope-event timestamps must additionally declare
formation, implantation, or detection origin together with transport, selection, and
censoring; sampling resolution is not timing uncertainty, and this interface supplies no
nuclear decay dynamics.

Every comparison influence records location, mechanism, source, interval, correction
ownership (never double-applying an already included correction or confusing correction
size with remaining uncertainty), and unresolved transfers; Type A and Type B denote
evaluation methods, not error kinds #aod-cite("nist-tn1297-comparison"), and ambient
conditions do not substitute for shielded internal fields at the atoms. Acquisition gate,
interrogation interval, observation window, and directional RCD retain separate domains:
uniform positive scaling cancels in $A slash A_R$, so window-dependent frequency changes
require altered dynamics, endpoints, or readout weights, and cross-isotope comparisons
inherit any shared hydrogen reference. Scoped assessment authenticates declarations
without applying new corrections or combining components; single-influence tolerance
screening requires a source-bound bound in output units and never replaces the joint
budget, while attributing a comparison residual to an apparatus effect requires explicit
calculation and evidence.


#aod-paragraph[Falsification.]
Dropping endpoint fractions fails the $7 slash 2$ advance; mismatched windows invalidate
$7 slash 17$; double-applying $delta_N$ or $delta_W$ fails the historical hydrogen
reduction. Independent physical testing requires frozen dynamics, an explicit observation
map, a held-out measurement, and a pre-registered tolerance: reproducing the Cs definition
is a calibration identity and replaying measured inputs is a reduction, neither of which
supplies the missing physical H/Cs correspondence or an isotope lifetime prediction.


#aod-provenance[#mainsection("main:subsec:m3-conditional-si-interface")\;
#mainequation("main:eq:wave-update-trace")\; #mainequation("main:eq:coupling-trace")\;
#mainequation("main:eq:rcd-additive-realization")\; #mainequation("main:eq:aod-wavelet-continuation")\;
#mainequation("main:eq:wavelet-reference-timing")\; #mainequation("main:eq:shed-continuation-witness")\;
#mainequation("main:eq:recipient-event-lattice")\; #mainequation("main:eq:m3-observation-map")\;
#mainequation("main:eq:m3-conditional-si-anchor")\; #mainequation("main:eq:m3-cs133-tau-interface").]


#aod-literature-note[The BIPM defines the second through
$Delta nu_(upright("Cs")) = 9 thin 192 thin 631 thin 770 thin upright("Hz")$ #aod-cite("bipm-second").
In a fountain clock, microwave interrogation and detected atomic-state populations guide
oscillator tuning; an electronic counter counts microwave cycles #aod-cite("nist-fountain").
These measured quantities require an observation map before comparison with native
reclosures.]


== Five-boundary relational-time and conditional SI bridge D.E.C. ledger <manual:m3-temporal:dec-si-bridge>

Vector #raw("RC-037") (#raw("manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv"),
verified via #raw("manual.engine --sector boundary_sadar") and
#raw("aod-core --verify-vectors --check-zero-float")) compiles all nine exact rational
stages #raw("T1")–#raw("T9") along
$B_(upright("pair"))(0, 30] arrow.r B_(upright("lag")) arrow.r B_(upright("bridge")) arrow.r B_(upright("val")) arrow.r B_(upright("ext"))$
without a background continuum clock $t$ (#figref("fig:manual-temporal-si-bridge-feynman"),
#tabref("tab:manual-temporal-dec-bridge")): coupled closures on half-open $(0, 30]$ give
$op("biz")_(i bar.v j) = 3 slash 2$ ($2 slash 3$ reversed), unwrapped lag $3 slash 2$
($- 3 slash 2$ reversed), and directional RCD $(5, 7)$ at $R D = 3$; stipulated unit gain
$a_c = a_r = 1$ at $B_(upright("bridge"))$ maps the Cs-133 anchor to
$1 slash 4596315885 thin upright("s")$ and $13788947655 thin upright("Hz")$; held-out
transfer at $N_(0,upright("val")) = 32$ rejects constant gain via exact residuals
$- 5 slash 29$ and $- 49 slash 151$; observed-advance verification gives $A_c = 7 slash 2$,
$A_r = 17 slash 2$, ratio $7 slash 17$, and signed control $- 1 slash 2$; and the
self-contained cut-$40$ capacity-drop simulator preserves prefix $k lt.eq 39$, shifts
$(6, 5) arrow.r (2, 5)$ ($6 slash 5 arrow.r 2 slash 5$) strictly at cut $41$, and rejects
hostile feedback disconnection at #raw("T9").


#figure(
  kind: image, [
#include "../../lib/figures/manual/temporal_si_bridge_feynman.typ"
  ],
  caption: [Coupled closure-beat lineages on half-open integer window $B_(upright("pair")) (0, 30]$, conditional Cesium/Hydrogen hyperfine SI bridge chains at $B_(upright("bridge"))$, held-out cross-field transfer audit at $N_(0,upright("val")) = 32$, and cut-$40 arrow.r 41$ causal control (#raw("temporal_si_bridge_dec_ledger.csv")).],
) <fig:manual-temporal-si-bridge-feynman>


#figure(
  kind: table, [
#{
  let rows = csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)
  let wrap-id(s) = s.replace("_", "_\u{200b}")
  let wrap-boundary(s) = s.replace("(", "\u{200b}(")
  let wrap-pair(s) = s.replace("_", "_\u{200b}").replace(";", ";\u{200b}").replace("->", "->\u{200b}")
  set text(size: 7.4pt)
  show raw: set text(size: 6.9pt)
  set par(justify: false, leading: 0.45em)
  table(
    columns: (1.55fr, 1.55fr, 2.40fr, 1.35fr, 1.40fr, 1.75fr),
    align: (left, left, left, right, right, left),
    inset: (x: 3.2pt, y: 3.5pt),
    table.header(
      toprule,
      [Stage], [Boundary $B$], [Lineage / anchor & counts], [Exact quantity], [Reverse / resid], [Gate status],
      midrule,
    ),
    ..rows.map(r => (
      [#raw(wrap-id(r.stage_id))],
      [#wrap-boundary(r.boundary_B)],
      [#wrap-pair(r.lineage_pair) \ #text(size: 6.9pt)[(#wrap-pair(r.delta_bip))]],
      [#r.exact_quantity],
      [#wrap-id(r.reverse_or_resid)],
      [#wrap-id(r.status_gate)],
    )).flatten(),
    bottomrule,
  )
}
  ],
  caption: [Engine-bound nine-stage relational closure-beat time, conditional SI bridge, held-out transfer, and cut-$40 arrow.r 41$ causal audit ledger (#raw("RC-037"), live from #raw("temporal_si_bridge_dec_ledger.csv")).],
) <tab:manual-temporal-dec-bridge>
