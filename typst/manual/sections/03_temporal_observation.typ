// Native Typst port of manual/sections/03_temporal_observation.tex (verbatim scientific content).
#import "../preamble.typ": *

= Temporal records and SI mapping <manual:m3-temporal>


#aod-paragraph[Constructed input.]
The adapter consumes the admitted recurrent waves and repeated coupled returns of
#mainequation("main:eq:wave-update-trace"),
#mainequation("main:eq:coupling-trace") and
#mainequation("main:eq:rcd-additive-realization").
It retains each complete trace, certificate, lineage, contact prefix, integer
window endpoint, signed phase bias, lag and directional reflection count.
The worked pair has four compared closures at cuts $2,10,18,26$ and three
reference closures at cuts $2,12,22$. Over $(0,30]$, excluding the first
closure of each recurrent lineage, its increments are $(3,2)$.
The comparison ratio is $3 slash 2$, its reverse is $2 slash 3$, and the two
additive directional durations are $5$ and $7$ in their declared native
count domain. Biases $(1 slash 4, - 1 slash 4)$ give lag $3 slash 2$ and reverse lag $- 3 slash 2$.


#aod-paragraph[Observation domain.]
The mapping binds the population, preparation, directed couplings, complete
committed prefixes, pending returns and window convention. Directional RCD, bias, lag and drift are recomputed from those records.
Structural RD belongs to each retained support. Duration participation requires
a compatible window map; a reclosure count alone does not supply it. Displacement traversals, hinges, dwells, emitted ticks and
returned clicks retain their separate counts. A window with positive reclosure
counts can still lack the repeated cross-returns needed for RCD.
Two named readouts replay this same context and retain its identity and
operator version. Their common history does not supply independent samples.
A window projection states the retained lineage, original window, selected
window and count readout. Changing the population, current or window requires
replay; a cached scalar cannot authenticate that change.


#aod-paragraph[Declared observation and units.]
Under #mainsection("main:subsec:m3-conditional-si-interface"), an explicit apparatus
observation map $cal(O)_i$ (#mainequation("main:eq:m3-observation-map"))
first maps reference history $Gamma_R$, window $omega$, population
$cal(P)$, coupling history $E$ and preparation to corrected
Cs-referenced cycle equivalents, anchoring conditional duration via
#mainequation("main:eq:m3-conditional-si-anchor") and
#mainequation("main:eq:m3-cs133-tau-interface"):

$ hat(C)_(upright("Cs")) = g_(theta) ( Gamma_R , omega ,cal(P),E,upright("preparation")), wide hat(T) = frac(hat(C)_(upright("Cs")), Delta nu_(upright("Cs"))). $ <eq:manual-m3-cycle-bridge>

The conversion uses the exact defining frequency; the first map requires
its own observation and calibration evidence. This conversion supplies no
universal duration for a native cut. The general apparatus map $cal(O)_i$
remains distinct from its explicit affine specialization
$C_i^(upright("aff")) = g_i q_i ( omega ) + delta_(upright("end"),i)$ ($g_i > 0$),
and structural support scale, window extent, native cadence
(#mainequation("main:eq:wavelet-reference-timing")), observed turns and SI
frequency retain separate types.
Let $a_c ,a_r > 0$ be stipulated cycle-equivalent gains per native return.
Let $f_(upright("Cs")) = 9 thin 192 thin 631 thin 770 thin upright("Hz")$ denote the defining
reference, without a clock realization. For the fixed window define

#math.equation(block: true, numbering: none, $ T = frac(a_r N_r, f_(upright("Cs"))), wide macron(nu)_c = frac(a_c N_c, T), wide t_1 = t_0 + T. $)

The mapping binds both gains, the time coordinate and epoch, the complete
input records, the defining reference and the executable mapping specification.
The interval and average frequency use only the two window reclosure counts,
stipulated gains and defining reference frequency.
At $a_c = a_r = 1$, $T = 2 slash f_(upright("Cs"))$ seconds and
$macron(nu)_c = 3 f_(upright("Cs")) slash 2$.
The result is a finite-window average.
The reciprocal $1 slash macron(nu)_c$ is a derived period, distinct from $T$
and from an independent validation. Physical realization and uncertainties from
drift, endpoint phase, cycle slips and temporal dependence remain unspecified.
The gains are stipulated without fitting hydrogen.


#aod-paragraph[Identifiability and separated evaluation.]
The family $g_(lambda) (Z) = 1 + lambda (55 - Z) slash 54$, $lambda > - 1$, has
$g_(lambda) (55) = 1$ and $g_(lambda) (1) = 1 + lambda$.
The $lambda = 0,1$ countermodels preserve the native records and Cs anchor
while producing different reports. The relative gain therefore remains free.
The known hydrogen value remains retrospectively exposed. Evaluation validates
the frozen prediction against the original model inputs before comparison,
then binds separate prediction and target hashes. Changing only the
target changes its diagnostic residual and leaves prediction bytes unchanged.
An atomic point prediction and its complete uncertainty remain unresolved.
The complete prediction record also freezes the uncertain input model,
readout definitions, reduction, candidate choice, stopping rule and comparison
criterion. Each derives from a separately bound plan; changing its declarations
or sources invalidates replay. A later freeze retains earlier target exposure
and cannot establish that the calculation was blind.


#aod-paragraph[Frozen transfer test.]
The retained direct-coupling experiment calibrates on its first half and
validates on the second. Each half contains $32$ reference reclosures.
With $k_i = 32 slash N_(i,upright("cal"))$ frozen, the predicted validation count is
$hat(N)_(0,upright("val")) = k_i N_(i,upright("val"))$.

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
  caption: [Frozen gains and subsequent reference-count transfer.],
) <tab:manual-m3-anchor-transfer>

These residuals reject this constant-transfer specialization. They are
count-transfer discrepancies, not measured Cs-frequency errors or standard
uncertainties. Refitting on each validation window would remove the test.
Identical synchronized reference histories do not provide independent
evidence. Overlapping windows and shared calibration sources retain their
dependence.


#aod-paragraph[Population and reference controls.]
Four retained executions use two recurring $3":"4":"6$ background supports
and the same frozen counting windows.
The baseline compares $3":"3":"6$ with $1":"2":"6$; a second construction compares
$3":"2":"6$ with $3":"3":"6$. Its A counts change from $99$ to $72$, while
its reference changes from $31$ to $30$. Two separate interventions
activate a prepared $3":"4":"6$ local support after the common committed prefix.
Coupling it only to A gives A counts $45$ then $42$, with reference
counts $32$ in both windows. Coupling it only to the reference gives A
counts $57$ then $47$, with reference counts $23$ in both windows.
Complete histories retain directed reflections and pending returns; short
count projections do not acquire RCD admission. These are finite-model
controls, without measured cycle calibration.

For a physical test, corrected observed cycle increments must be supplied
separately and compared using a justified tolerance fixed before evaluation.
The oscillator, counter, interrogation, realization corrections, endpoint
resolution and missed-cycle model belong to that observation record.
No isotope retention parameter absorbs the residual.
Each seconds or hertz output keeps its own eight-component budget; missing
physical calibration and discrepancy remain unknown.


#aod-paragraph[Consumer and causal control.]
The separately bound Matter I v2 replay preserves its declared-model status:
its native atomic admission remains pending. The baseline and capacity
intervention share committed history through cut 39. The intervention at 40
causes retention loss at 41, changing observed increments from $(6,5)$ to
$(2,5)$. Applying the same stipulated gain one in both cases leaves
$T = 5 slash f_(upright("Cs"))$ fixed and changes the average from
$6 f_(upright("Cs")) slash 5$ to $2 f_(upright("Cs")) slash 5$.
A hostile mutation disconnects the loss response from the next state while
retaining the intervention inputs. The effect disappears and the original
replay validator rejects that trace.


#aod-paragraph[Reproduction and source precision.]
#raw("manual/scripts/aod_temporal_observation.py --check") reconstructs the native
adapter and mapping report; #raw("--consumer-root") selects the
separately bound Matter I replay.
#raw("aod_temporal_anchor.py --check-data") replays the original scientific anchor calculations and
the four population controls; #raw("aod_manual_wavelet_si_alignment.py --check")
verifies the aligned wavelet, nonrecurrent localization, signed-advance and
$tau$-angular specializations passively without altering native transitions.
The tests reject changed scopes, aliases,
uncoupled records, invalid windows, scheduler substitutions, nonpositive gains,
and evaluation leakage. The consumer preserves historical v1/v2 fixture bytes
and identifies its two active Main amendments separately.
The BIPM comparison retains raw hashes, tests nearest rounding for nonzero
entries and uses conditional point-zero covariance transcriptions.
Its source documents do not specify zero formatting or underflow, so zero
precision remains unresolved.


== Observed cycles and experimental reductions <manual:m3-metrology>


#aod-paragraph[Setup.]
Relational cadence compares retained closures over the same bip window
(#mainequation("main:eq:wavelet-reference-timing")).
Its observation map (#mainequation("main:eq:m3-observation-map")) must distinguish
current reclosures, shed continuation and recipient stages
(#mainequation("main:eq:aod-wavelet-continuation"),
#mainequation("main:eq:shed-continuation-witness"),
#mainequation("main:eq:recipient-event-lattice")),
oscillator cycles, estimated state populations and detector timestamps.
A wavelet group can retain its source history without each packet representing
one measured microwave cycle. Preparation, lineage, coordinate, epoch,
window and detector response belong to the map.
The recurring $3":"4":"6$ construction retains its own reflection-duration
conditions; $2 x = 6 n$ in a restricted fold does not set a universal atomic period.


#aod-paragraph[Derivation.]
For an observer coordinate measured in turns on $W = (k_0 ,k_1 ]$, let
$C(W) in bb(Z)$ be the net winding and let
$0 lt.eq phi.alt_0 , phi.alt_1 < 1$ be the endpoint fractions. Then

$ A(W) = C(W) + phi.alt_1 - phi.alt_0 . $ <eq:manual-m3-observed-advance>

This coordinate is downstream of Main's closure phase.
At a shared cut, the endpoint terms cancel, so adjacent advances add;
reversing the orientation changes the signed advance consistently.
Turns and ratios remain exact. An angular display, when required, uses
$theta = tau phi.alt$, with $tau$ the full-turn angular constant.
For a passive lossless transport example, event identities also give
$N_(upright("emitted")) - N_(upright("arrived")) = P_1 - P_0$, where $P_i$ counts pending
packets at the endpoints. Arrival separation equals emission separation plus
the change in transit delay. Loss and detector inefficiency require their own
counts. Observing these events does not change the source dynamics; routed
packets alone supply neither recipient seating nor a reclosure beat
(#mainequation("main:eq:recipient-event-lattice")).


#aod-paragraph[Specialization and calibration.]
On $(10,22]$, choose compared winding $4$ and endpoints
$2 slash 3,1 slash 6$, and reference winding $8$ and endpoints $1 slash 4,3 slash 4$.
Equation #eqref("eq:manual-m3-observed-advance") gives advances
$A = 7 slash 2$ and $A_R = 17 slash 2$. Splitting the compared winding as $2 + 2$
at phase $5 slash 6$ gives $13 slash 6 + 4 slash 3 = 7 slash 2$.
If an independently justified realization identifies $A_R > 0$ as corrected
Cs-equivalent cycles on that same coordinate, epoch and window, then
#mainequation("main:eq:m3-conditional-si-anchor") and
#mainequation("main:eq:m3-cs133-tau-interface") give

$ frac(A, A_R) = frac(7, 17), wide T = frac(A_R, f_(upright("Cs"))) = frac(17, 2 f_(upright("Cs"))), wide macron(nu) = frac(A, T) = frac(7 f_(upright("Cs")), 17). $ <eq:manual-m3-accumulated-si>

In full-turn angular reporting ($tau = 2 pi$), the same matched window gives
$Delta theta_a = frac(7, 2) tau$ and
$macron(Omega)_a = frac(7, 17) tau f_(upright("Cs"))$.
Two boundary specializations of #mainequation("main:eq:m3-observation-map")
through #mainequation("main:eq:m3-cs133-tau-interface") stay explicit under the
same reference anchor:

- #emph[Nonrecurrent or clipped localization.] A fragment with
$q_a ( omega ) = 0$ and $delta_(upright("end"),a) = 0$ localized on a bound
positive reference window with $C_(upright("Cs")) = 10$ yields
$T_(omega) = 10 slash f_(upright("Cs"))$ and $macron(f)_a = 0$, $Delta theta_a = 0$,
$macron(Omega)_a = 0$; $q_a = 0$ supplies no intrinsic frequency or phase lag,
and no integer cut becomes a universal second.
- #emph[Signed compared advance against positive reference advance.]
Under #eqref("eq:manual-m3-observed-advance") and the explicit affine
specialization $C_a^(upright("aff")) = g_a q_a + phi.alt_1 - phi.alt_0$ with
$q_a = 0$, $g_a = 1$, $phi.alt_0 = 3 slash 4$ and $phi.alt_1 = 1 slash 4$, the compared advance
is signed, $C_a = - 1 slash 2$, while the reference advance remains strictly positive,
$C_(upright("Cs")) = 1$. Then #mainequation("main:eq:m3-cs133-tau-interface")
yields $T_(omega) = 1 slash f_(upright("Cs"))$, signed mean phase-advance rate
$macron(f)_a = - f_(upright("Cs")) slash 2$, angular advance $Delta theta_a = - tau slash 2$ and
$macron(Omega)_a = - tau f_(upright("Cs")) slash 2$. This signed rate is distinct from a
nonnegative atomic resonance frequency, which requires restricting to
$C_a gt.eq 0$ (or $C_a > 0$) together with separate physical-realization premises.


These are conditional finite-window results from declared mathematical inputs.
The exact defining frequency supplies the unit; measured realization and
phase uncertainty remain separate, and choosing gains from a target value
cannot produce an independent prediction. A universal seconds-per-bip
conversion, or a limiting resonance frequency, needs additional premises.


#aod-paragraph[Hydrogen reduction.]
Hellwig et al. used continuous active masers and a signed heterodyne beat,
with the convention

$ nu_H = 284 nu_R + nu_S + nu_B + delta_(upright("UTC")) + delta_N + delta_W + delta_D + delta_Z . $ <eq:manual-m3-hydrogen-reduction>

Here $nu_R$ is nominally $5 thin 000 thin 000 thin upright("Hz")$, $nu_S$ is the
synthesizer setting, and the corrections account for reference transfer,
wall collisions, second-order Doppler and Zeeman effects.
Their Tables IV and VI give $1 thin 420 thin 405 thin 751.7691 thin upright("Hz")$ and
$1 thin 420 thin 405 thin 751.7667 thin upright("Hz")$.
The second uses an NP3-corrected zero-wall intercept: adding $delta_N$
or $delta_W$ again counts it twice. The exact printed-input mean is
$1 thin 420 thin 405 thin 751.7679 thin upright("Hz")$; the paper reports
$1 thin 420 thin 405 thin 751.768 thin upright("Hz")$ with uncertainty
$0.002 thin upright("Hz")$ #aod-cite("hellwig-hydrogen-1970").
This reproduces the published reduction. Unavailable raw phase records,
tuning crossings and unrounded fit inputs are not reconstructed from the mean.


#aod-paragraph[Caesium reduction.]
A fountain interrogates prepared atoms with an applied microwave field.
With compatible calibrated population estimates and $N_3 + N_4 > 0$,
$p = N_4 slash (N_3 + N_4 )$ supplies a population response for line-centre estimation.
The August 2013 NIST-F2 evaluation reports fractional uncertainties
$u_A = 0.44 times 10^(- 15)$ and $u_B = 0.16 times 10^(- 15)$;
Table 1’s typical $u_B = 0.11 times 10^(- 15)$ belongs to a different budget.
Multiplication by $f_(upright("Cs"))$ converts each printed value to hertz.
The spin-exchange statistical contribution is already included in $u_A$.
Quoted upper bounds remain bounds, and rounded synthesizer settings do not
specify the exact carrier #aod-cite("heavner-nist-f2-2014").
Campaign populations, servo records and covariance are needed for raw replay.
The experiment's gravity and Doppler corrections retain their source roles;
they do not become A$Omega$D dynamical premises.


#aod-paragraph[Dependence and event timing.]
An exact conditional trace can have nonzero ensemble spread.
For model output $A$ and comparison $E$ in the same units, a specified
joint distribution with finite second moments, or a justified complete joint
moment model, gives

$ op("Var")(A - E) = op("Var")(A) + op("Var")(E) - 2 op("Cov")(A,E). $ <eq:manual-m3-residual-dependence>

Repeated use of one uncertain source retains that identity. Thus $A = E = X$
cancels, whereas $A = X,E = - X$ gives $4 op("Var")(X)$.
A published uncertainty does not specify a finite probability distribution.
Its category, coverage and provenance therefore remain distinct from an exact
finite-model propagation. Shared windows and reference data retain their
correlations; the defining Cs integer itself has no uncertainty.
For isotope-event comparison, timestamps must additionally identify formation,
implantation or detection as their origin, with transport, selection and
censoring conditions. The event evidence is bound to the containing observation
context. Sampling resolution alone is not timing uncertainty.
This interface supplies no nuclear retention or decay dynamics.


#aod-paragraph[Comparison conditions.]
Each influence records its location in the input, apparatus or output; its
mechanism, source, applicable interval, correction ownership, remaining
uncertainty and unresolved conditions. A correction already included in an
input stays there. Its trusted correction record identifies the owning observation.
Its magnitude is distinct from the uncertainty remaining
after correction. Type A and Type B identify uncertainty evaluation methods,
not kinds of error #aod-cite("nist-tn1297-comparison").
Ambient temperature or Earth's field does not specify the conditions at the
atoms. The comparison needs the applicable internal temperature or field,
including control, shielding and bias-field evidence, or an explicit unresolved
transfer. Unknown contributions retain that status.


#aod-paragraph[Intervals and reference dependence.]
The acquisition gate, interrogation interval, model observation window and
directional reflection duration have separate domains and units. Equating
them requires a declared map. Scaling both accumulated advances by the same
positive factor leaves their ratio unchanged; a window-dependent frequency
therefore requires changed dynamics, phase endpoints or readout weights.
For each comparison, retain the calibration and evaluation source identities
and any shared reference. A target reduced using hydrogen remains dependent
on that hydrogen reference when used in a cross-isotope comparison.
A Cs-normalized equality retains its calibration role. A nuclear-event delay
instead uses the timestamp-origin and selection conditions above.


#aod-paragraph[Scoped assessment.]
The comparison assessment authenticates these declarations separately from
the physical evidence they describe. It applies no additional correction and
does not combine uncertainty components. An influence may be screened against
a stated tolerance only with a source-bound bound in the output unit and an
applicable window. Such a screen concerns that influence alone; the joint
budget still accounts for their combination and dependence.
A missing bound remains unresolved. A discrepancy between a model output and
a corrected measurement is a comparison residual; assigning it to an
apparatus effect requires the corresponding calculation and evidence.


#aod-paragraph[Falsification.]
Dropping endpoint fractions fails the $7 slash 2$ advance; mismatched windows
invalidate the ratio; double-applied corrections fail the historical reduction.
An independent physical test instead requires frozen state dynamics and an
observation map, followed by a held-out measurement and a justified tolerance.
Reproducing the Cs definition is a calibration identity. Replaying measured
inputs is a reduction. Neither establishes the missing physical H/Cs
correspondence or an isotope lifetime prediction.


#aod-provenance[#mainsection("main:subsec:m3-conditional-si-interface")\;
#mainequation("main:eq:wave-update-trace")\; #mainequation("main:eq:coupling-trace")\;
#mainequation("main:eq:rcd-additive-realization")\; #mainequation("main:eq:aod-wavelet-continuation")\;
#mainequation("main:eq:wavelet-reference-timing")\; #mainequation("main:eq:shed-continuation-witness")\;
#mainequation("main:eq:recipient-event-lattice")\; #mainequation("main:eq:m3-observation-map")\;
#mainequation("main:eq:m3-conditional-si-anchor")\; #mainequation("main:eq:m3-cs133-tau-interface").]



#aod-literature-note[The BIPM defines the second through
$Delta nu_(upright("Cs")) = 9 thin 192 thin 631 thin 770 thin upright("Hz")$ #aod-cite("bipm-second").
In a fountain clock, microwave interrogation and detected atomic-state
populations guide oscillator tuning; an electronic counter counts microwave
cycles #aod-cite("nist-fountain"). These measured quantities require an observation
map before comparison with native reclosures.]



== Five-boundary relational-time and conditional SI bridge D.E.C. ledger <manual:m3-temporal:dec-si-bridge>

Declare the five-boundary metrology stack separating native coupled closure beats from conditional SI stipulation and held-out cross-field transfer checks:

#math.equation(block: true, numbering: none, $ B_(upright("pair")) [1, 30] arrow.r B_(upright("lag")) arrow.r B_(upright("bridge")) arrow.r B_(upright("val")) arrow.r B_(upright("ext")). $)

Vector #raw("RC-037") (#raw("manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv"), verified by #raw("python3 -B -m manual.engine") #raw("--sector") #raw("boundary_sadar") and #raw("aod-core") #raw("--verify-vectors") #raw("--check-zero-float")) executes all six boundary stages without a background continuum clock $t$: coupled closures $(2, 10, 18, 26)$ versus $(2, 12, 22)$ yield $op("biz")_(i bar.v j) = 3 slash 2$ ($2 slash 3$ reversed) and unwrapped lag $3 slash 2$ ($- 3 slash 2$ reversed); stipulated unit bridge gain $a_c = a_r = 1$ at $B_(upright("bridge"))$ maps the Cesium-$133$ anchor $Delta nu_(upright("Cs")) = 9 thin 192 thin 631 thin 770 thin upright("Hz")$ to $Delta t_(upright("SI")) = 2 slash 9192631770 thin upright("s")$ and $nu_c = 13788947655 thin upright("Hz")$; held-out cross-field transfer at $B_(upright("val"))$ yields nonzero exact residuals $- 5 slash 29$ and $- 49 slash 151$, rejecting any universal constant-gain SI clock promotion; and a cut-$40$ capacity-drop intervention alters response strictly later at cut $41$ ($6 slash 5 arrow.r 2 slash 5$).


#figure(
  kind: image, [
#include "../../lib/figures/manual/temporal_si_bridge_feynman.typ"
  ],
  caption: [Coupled closure-beat lineages on integer window $B_(upright("pair")) [1, 30]$, conditional Cesium/Hydrogen SI bridge chains at $B_(upright("bridge"))$, and held-out cross-field transfer rejection at $B_(upright("val"))$ (#raw("temporal_si_bridge_dec_ledger.csv")).],
) <fig:manual-temporal-si-bridge-feynman>


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, left, right, right, left),
    table.header(
      toprule,
      [Stage], [Boundary $B$], [Lineage / anchor pair], [Exact quantity], [Reverse / resid], [Gate status],
      midrule,
    ),
    [#raw("T1_pair_closures")], [$B_(upright("pair")) [1, 30]$], [$(2, 10, 18, 26)$ vs $(2, 12, 22)$], [$3 slash 2$], [$2 slash 3$], [authenticated exact RCD],
    [#raw("T2_unwrapped_lag")], [$B_(upright("pair")) [1, 30]$], [bias $( + 1 slash 4, - 1 slash 4)$], [$3 slash 2$], [$- 3 slash 2$], [authenticated exact lag],
    [#raw("T3_cs133_bridge")], [$B_(upright("bridge")) (a_c = a_r = 1)$], [Cs $9192631770$ Hz ($N_r = 2, N_c = 3$)], [$2 slash 9192631770$], [$13788947655 slash 1$], [conditional SI stipulated gain],
    [#raw("T4_transfer_field_A")], [$B_(upright("val"), A)$], [$3":"3":"6$ vs $1":"2":"6$], [$768 slash 29$], [$- 5 slash 29$], [rejects constant transfer],
    [#raw("T5_transfer_field_B")], [$B_(upright("val"), B)$], [$3":"2":"6$ vs $3":"3":"6$], [$3264 slash 151$], [$- 49 slash 151$], [rejects constant transfer],
    [#raw("T6_cut40_intervention")], [$B_(upright("causal")) (40 arrow.r 41)$], [capacity-drop control], [$6 slash 5$], [$2 slash 5$], [strictly later cut-$41$ response],
    bottomrule,
  )
}
  ],
  caption: [Relational closure-beat time, conditional SI bridge, and held-out transfer rejection D.E.C. ledger (#raw("RC-037")).],
) <tab:manual-temporal-dec-bridge>

