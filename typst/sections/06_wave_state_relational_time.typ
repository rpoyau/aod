// Native Typst port of sections/06_wave_state_relational_time.tex (verbatim scientific content).
#import "../preamble.typ": *

= Wave state and relational temporal structure <sec:wave-state-relational-time>



== Complete state before comparison

Wave identity is fixed by #eqref("eq:wave-identity"). Its mutable state retains
all coordinates needed by the declared realization:

$ S^W_(B,i,k) = & paren.l W^(upright("id"))_(B,i) ,K^(upright("adm"))_i , sigma^C ,J,p, partial B, Phi ,op("Cad"), epsilon.alt , \ & upright("memory"),upright("capacity"),upright("context") paren.r _k . $ <eq:complete-wave-state>

The closure state $sigma^C$ may be forming, open, pending, closed, fusing,
reclosed or shedding. Retained context has its own coordinate; it is not
identical with closure memory or pressure. The companion coupling state is

$ S^(times)_(I,B,k) = (E, psi^(upright("bias")) , Lambda , Delta Lambda , op("RCD"), rho^D ,upright("provenance"))_k . $ <eq:complete-coupling-state>

Its fields hold committed comparison records, with absent coordinates typed
as absent until their preconditions have been established.


#aod-paragraph[Declared update and trace.]
Declare an update law on its admissible input domain:

$ S^W_(k + 1) = cal(U)_B (S^W_(lt.eq k) ,S^(times)_(lt.eq k) ,upright("input")_(lt.eq k) ), wide Gamma^W_(B,i) [k_0 ":"k_1 ] = (S^W_(B,i,k) )_(k_0 lt.eq k lt.eq k_1) . $ <eq:wave-update-trace>

In the native event realization, state and input cuts are integers. Initialization
at a completed return retains that return's vertex coordinate; any rebasing uses
a declared coordinate map.
This interface permits different declared realizations. Pair events have
separate immutable records:

$ e_s^(times) = & paren.l op("id")_s ,W_i^(upright("id")) ,W_j^(upright("id")) , B, omega ,upright("direction"),upright("contact"),upright("reflection"), \ & k_s ,op("digest") Gamma^W_(i, lt.eq k_s) , op("digest") Gamma^W_(j, lt.eq k_s) paren.r , wide Gamma^(times) = (e_s^(times) )_s . $ <eq:coupling-trace>

Comparison requires both recurrent lineages, their common committed window
and repeated distinct bound contacts; one contact supplies only a stage.


== Localized wavelets, overlap aggregation and retained history <subsec:aod-wavelet-continuation>


#aod-paragraph[Setup.]
Consolidating #secref("subsec:localized-wavelet") and the temporal cycle group
of #secref("subsec:temporal-cycle-group"), define an A$Omega$D wavelet on a
declared support and boundary/window $B = ( partial_T R, omega )$ as a finite,
localized, lineage-bearing current continuation retaining its seating state
$sigma_(upright("seat"))$ independently of its coupling/route role
$sigma_(upright("role"))$, ordered committed construction records $Gamma_w$,
and relevant closure, coupling, and route witnesses
$cal(W)_w = (cal(W)_w^(upright("ret")) , Gamma^(times)_w ,cal(W)_w^(upright("route")) )$:

$ w_(B,i) & = (op("id")_w ,W_(upright("parent")) ,op("anc")_w ,op("supp")_w ,B, sigma_(upright("seat")) , sigma_(upright("role")) , Gamma_w ,cal(W)_w ), \ sigma_(upright("seat")) & in brace.l upright("open_duon"),upright("seated_duad") brace.r , \ sigma_(upright("role")) & in brace.l upright("local_segment"),upright("coupled_segment"),upright("shed_continuation") brace.r . $ <eq:aod-wavelet-continuation>

A coupled segment may carry either open-Duon or seated-Duad current, and a shed
continuation retains its seating state alongside parent provenance. Restricting
an admitted recurrent wave $W_(B,i)$ of #eqref("eq:wave-identity") to a finite
window $omega = (u,v]$ yields its recurrent-wave wavelet specialization with
$W_(upright("parent")) = W^(upright("id"))_(B,i)$, preserving parent identity,
ancestry and ordered prefix records; finite window selection does not terminate
the underlying continuation beyond $v$. A finite or shed wavelet may carry
zero local certified returns ($q_w ( omega ) = 0$) while retaining seating, parent
ancestry and bound phase/lag provenance; localization never promotes an open
wavelet, a shed fragment or an isolated monon into a recurring wave
#eqref("eq:wave-identity").


#aod-paragraph[Derivation.]
For a wavelet $w_a$ of lineage $i$ observed on a half-open window
$omega_a = (u_a ,v_a ]$ ($u_a < v_a$), its retained witness family
$cal(W)_(w_a)^(upright("ret"))$ may preserve prefix or admission closures
outside $omega_a$ (or origin $C_(i,0)$) as supporting provenance. Separately
from those retained support witnesses, whenever $cal(W)_(w_a)^(upright("ret"))$
is complete for compatible certified returns of lineage $i$ completing in
$omega_a$ under scope $B$ (or an identity-preserving scope map across
compatible representations), define the eligible in-window reclosure-identity set
$R_i ( omega_a )$ and single-interval count $q_i ( omega_a ) := bar.v R_i ( omega_a ) bar.v$;
across any finite same-lineage union $Omega = union.big_(a = 1)^m omega_a$,
counting the union of eligible immutable return identities #eqref("eq:return-identity")
prevents double-counting shared returns without counting out-of-window support
witnesses or the initial origin $j = 0$:

$ R_i ( omega_a ) & := brace.l op("id")_(upright("return")) (C_(i,j) ):C_(i,j) in cal(W)_(w_a)^(upright("ret")) , j gt.eq 1, k_j in paren.l u_a ,v_a ], C_(i,j) " compatible on "B brace.r , \ q_i ( Omega ) & := "#" union.big_(a = 1)^m R_i ( omega_a ) lt.eq sum_(a = 1)^m q_i ( omega_a ). $ <eq:wavelet-overlap-dedup>

For oppositely oriented wavelets $w_(+) ,w_(-)$ whose signed window currents
cancel to zero, aggregate cancellation removes the summed scalar while
retaining both contributing histories distinctly:

$ J(w_(+) ) + J(w_(-) ) = 0 quad arrow.r.double.long quad op("Hist")(w_(+) plus.o w_(-) ) = brace.l (op("anc")_(w_(+)) , Gamma_(w_(+)) ), thin (op("anc")_(w_(-)) , Gamma_(w_(-)) ) brace.r . $ <eq:wavelet-cancellation-retention>



#aod-paragraph[Falsification.]
Counting an out-of-window supporting witness or initial origin $C_(i,0)$,
violating half-open bounds $u_a < k_j lt.eq v_a$, summing per-window return counts
across overlapping windows without $op("id")_(upright("return"))$
deduplication, merging incompatible lineages, erasing either contributing
history when $J(w_(+) ) + J(w_(-) ) = 0$, detaching $sigma_(upright("seat"))$,
$W_(upright("parent"))$ or $Gamma_w$, or promoting a $q_w ( omega ) = 0$
open continuation into #eqref("eq:wave-identity") violates
#eqref("eq:aod-wavelet-continuation")–#eqref("eq:wavelet-cancellation-retention").


#aod-provenance[#eqref("eq:return-identity"),
#eqref("eq:beat-reclosure"),
#eqref("eq:cumulative-closure-counts"),
#eqref("eq:closure-phase-window"),
#eqref("eq:wave-identity"),
#eqref("eq:duon-current"),
#eqref("eq:duad-same-current"),
#eqref("eq:complete-wave-state"),
#eqref("eq:coupling-trace").]



== Directional RCD and duration <sec:boundary-accounting>
#aod-anchor(<subsec:boundary-scope>)

The scoped address binder is $bold(upright(a)) tack.r (cal(F),R, partial R, omega )$.
The field resolves to its wave members before a channel is evaluated.


#aod-paragraph[Constructor.]#aod-anchor(<subsec:reflection-duration-coupling>)
Couple the support accessor #eqref("eq:branch-hinge-rd") before projecting duration:

$ RCD_(i j) (B) = R D_B (C_(i j) ) bowtie_B R^(upright("asym"))_(i j) (B), $ <eq:rcd-coupling>


$ op("dur")_(cal(P)) : RCD_(i j) arrow.r.long cal(D)_(i j) , wide rho^D_(i j) (B) = op("dur")_(cal(P)) ( RCD_(i j) (B)). $ <eq:rcd-duration-participation>

Here $cal(D)_(i j)$ is a declared exact ordered native count domain.
The constructor retains both lineages, direction, repeated contact identities,
scope and reflection witness. An additive-count specialization has domain
$(R D,r_1 , dots.h ,r_m )$ with $r_s gt.eq 0$ and sets

$ op("dur")_(+) (R D bowtie (r_s )_s ) = R D + sum_s r_s . $ <eq:rcd-additive-realization>

This is a declared duration specialization. Neutral reflection $r_s = 0$
specializes it to $rho^D = R D$; the $r_s$ depend on direction,
so reversal can change duration.

For returned channel $e$, the retained duration coordinate is

$ D_e ( partial F, omega ) = op("dur")(op("RCD")_e ), $ <eq:returned-duration>

#aod-anchor(<subsec:returned-current-duration-coordinate>)
with the specific duration interface declared on that channel.


#aod-paragraph[Window participation.]
A window projection requires a compatible count in the same ordered domain:

$ op("Compat")_(cal(D)) ( rho^D_(i j) , bar.v omega bar.v^(cal(D))_(i j) ) quad arrow.r.double.long quad rho^D_(omega ,i j) = min_(cal(D)) ( rho^D_(i j) , bar.v omega bar.v^(cal(D))_(i j) ). $ <eq:window-clipped-rho>

Clipping changes only scalar participation. RD and RCD stay intact;
support-enclosure retention TTL has its own interface in
#eqref("eq:support-enclosure-retention"). Native relational time is constructed in
#eqref("eq:relational-time").


== Comparison from committed recurrence

The phase accessor is #eqref("eq:cumulative-closure-counts"). A native comparison
window has two strictly ordered integer endpoints $u < v$; contact commitments
are integer cuts in $[u,v]$, and reclosures are counted in $(u,v]$ as in
#eqref("eq:closure-phase-window"). For distinct recurrent lineages with repeated
bound contacts in that window, the exact cadence ratio is

$ op("biz")^(T F)_(i bar.v j) ( omega ) = frac(Delta op("bip")_i ( omega ), Delta op("bip")_j ( omega )), wide Delta op("bip")_j ( omega ) > 0. $ <eq:cadence-ratio>

Here $Delta upright("bip")_i ( omega ) = upright("bip")_i ( omega ) = upright("bip")^(lt.eq)_i (v) - upright("bip")^(lt.eq)_i (u)$ uses the window accessor.
A single monon pair supports structural comparison, but lacks the two
cadences required here. A declared comparison protocol $cal(P)$ fixes
the exact ordered domain, orientation and exchange law:

$ op("Compare")^(Phi)_(cal(P),i bar.v j) ( Phi_i , Phi_j ,op("Cad")_i ,op("Cad")_j , Gamma^(times)_(i j) ) = ( psi^(upright("bias"))_(i bar.v j) , Lambda_(i bar.v j) , Delta Lambda_(i bar.v j) ). $ <eq:native-comparator>

The native comparison is unwrapped. One declared count realization is

$ psi_(i bar.v j) = b_i - b_j , quad Lambda_(i bar.v j) = N_i - N_j + b_i - b_j , quad Delta Lambda_(i bar.v j) = Lambda_(i bar.v j) (k) - Lambda_(i bar.v j) (k^(-) ), $ <eq:count-comparator-realization>

Here $N_i ,N_j$ count committed reclosures and
$(b_i ,b_j ) in bb(Q)^2$ are separately declared ordered oriented offsets.
A whole-closure slip changes $Lambda$ by one even if a wrapped display repeats.
Another declared convention is the cadence-qualified $q X_i - p X_j$, whose
reversal retains its coefficient normalization.


$ op("RT")_(I,B) ( omega ) & = Pi^(upright("native"))_(upright("rel")) ( brace.l Gamma^W_(B,i) brace.r_(i in I) , Gamma^(times)_(I,B, omega) ;cal(P)) \ & = brace.l (op("biz")^(T F)_(i bar.v j) , psi_(i bar.v j) , Lambda_(i bar.v j) , Delta Lambda_(i bar.v j) , RCD_(i j) , rho^D_(i j) ,upright("provenance")_(i j) ) brace.r_((i,j) in E) . $ <eq:relational-time>

With positive counts in both directions, cadence ratios reverse reciprocally.
The count comparator reverses bias and lag by sign; the directional RCD is
reconstructed. Three or more waves form an edge-labelled comparison structure.
No global scalar clock is required. Equal temporal coordinates may coexist
with unequal pressure, closure condition or retained context in
#eqref("eq:complete-wave-state").


#aod-paragraph[Reference-window timing of localized and open continuations.]
Write $q_i ( omega ) := Delta op("bip")_i ( omega )$ for the eligible
in-window certified reclosure count #eqref("eq:wavelet-overlap-dedup") on
compatible window $omega$. Whenever a coupled recurrent reference wave $r$
supplies $q_r ( omega ) > 0$ and the compared lineage carries repeated bound
contacts on $omega$ with $r$, the native cadence ratio extends to
localized wavelets #eqref("eq:aod-wavelet-continuation") for both $q_a ( omega ) > 0$
and $q_a ( omega ) = 0$:

$ q_i ( omega ) := Delta op("bip")_i ( omega ), wide r_(a bar.v r) ( omega ) := op("biz")^(T F)_(a bar.v r) ( omega ) = frac(q_a ( omega ), q_r ( omega )), wide q_r ( omega ) > 0, quad q_a ( omega ) in bb(Z)_(gt.eq 0) . $ <eq:wavelet-reference-timing>

Under those repeated-contact coupling hypotheses, a short, open or shed wavelet
with $q_a ( omega ) = 0$ yields $r_(a bar.v r) ( omega ) = 0$ without becoming an
independent clock or allowing $q_r ( omega ) = 0$. By contrast, if a fragment
has only one delivered contact against $r$, that single contact supplies only a
passive window/stage association retaining parent phase/lag provenance
$(w_a , omega , Gamma_(W_(upright("parent"))) )$, never the repeatedly coupled
cadence coordinate $op("biz")^(T F)_(a bar.v r) ( omega )$.


#aod-paragraph[Falsification.]
Aliased wave identities, an uncoupled pair, only one contact for
$op("biz")^(T F)_(a bar.v r) ( omega )$ (even when $q_a ( omega ) = 0$), zero
denominator, unbound prefix, absent duration interface or incompatible clipping
domain invalidate the stated coordinate. Aggregation that discards direction or
ancestry loses part of the relation even when its current sums to zero.


#aod-provenance[#eqref("eq:beat-reclosure"),
#eqref("eq:wave-identity"),
#eqref("eq:wave-update-trace"),
#eqref("eq:coupling-trace"),
#eqref("eq:rcd-coupling").]



=== Tick/click <subsec:duon-tick-click>

#aod-paragraph[Setup.]
Index the tick/click alternation strictly by the integer cut index $k in bb(Z)$
of #eqref("eq:wave-update-trace"), without introducing any external or
continuous background clock parameter. Pair the complete wave state
#eqref("eq:complete-wave-state") and companion coupling state
#eqref("eq:complete-coupling-state") at cut $k$ into the complete cut state
$K_k := (S^W_(B,i,k) , S^(times)_(I,B,k) )$, with scope-$B$ emission map $E_B$,
received returned Duon $Y_k$, coupling bias $beta_k$ (carried by
$psi^(upright("bias"))_k$ in $S^(times)_(I,B,k)$), and committed lead–lag trace
$Delta_(upright("lead/lag"), lt.eq k)$ assembled from $S^(times)_(I,B,lt.eq k)$
and committed pair-event records $e_s^(times)$ ($k_s lt.eq k$) of
#eqref("eq:coupling-trace").

#aod-paragraph[Derivation.]
Specializing the declared update law #eqref("eq:wave-update-trace") on integer
cut transitions $k arrow.r k + 1$ with the cut-$k$ input slot carrying the
received returned Duon $Y_k$, bias $beta_k$, and committed lead–lag trace
$Delta_(upright("lead/lag"), lt.eq k)$ yields the cut-indexed tick/click
recurrence:

#math.equation(block: true, numbering: none, $ K_k := (S^W_(B,i,k) , S^(times)_(I,B,k) ), wide X_k = E_B (K_k ), \ S^W_(B,i,k + 1) = cal(U)_B (S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) , (Y_k , beta_k , Delta_(upright("lead/lag"), lt.eq k) ) ), \ K_(k + 1) := (S^W_(B,i,k + 1) , S^(times)_(I,B,k + 1) ), wide X_(k + 1) = E_B (K_(k + 1) ). $)

A tick at cut $k$ emits the Duon event $X_k = E_B (K_k )$; the click receives
the bound returned Duon $Y_k$ and updates the wave state through $cal(U)_B$ to
$S^W_(B,i,k + 1)$, pairing it with the post-click committed coupling state
$S^(times)_(I,B,k + 1)$ to form
$K_(k + 1) := (S^W_(B,i,k + 1) , S^(times)_(I,B,k + 1) )$ before the next tick
$X_(k + 1)$.

#aod-paragraph[Falsification.]
Any update requiring an external clock coordinate not determined by the integer
cut index $k$, committed prefixes $(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) )$,
and committed pair records $Gamma^(times)$ with $k_s lt.eq k$ violates
#eqref("eq:wave-update-trace"). Likewise, emitting $X_(k + 1)$ before receiving
the bound click return $Y_k$, or reading an uncommitted future record
($k_s > k$) or absent precondition in $S^(times)_(I,B,k)$ as committed,
falsifies the declared tick/click ordering.


=== Markovian and retained-history continuity <subsec:duon-continuity>

#aod-paragraph[Setup.]
At integer cut $k in bb(Z)$, let $Pi_(upright("cut")) (S^W_(B,i,k) )$ denote the
present-cut projection of #eqref("eq:complete-wave-state") onto its present-cut
cycle coordinates (excluding closure memory, retained context, prior prefix cuts
$lt.eq k - 1$, and companion coupling records). Contrast this projection with
the full retained-history state $(S^W_(B,i,k) , S^(times)_(I,B,k) )$ of
#eqref("eq:complete-wave-state") and #eqref("eq:complete-coupling-state") and
its committed prefix $(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) )$ in
#eqref("eq:wave-update-trace") and #eqref("eq:coupling-trace"), which retain
prior return records, lead–lag burden, jitter, shell residue, duration, or SADAR
channel memory.

#aod-paragraph[Derivation.]
A realization exhibits Markovian continuity when next-cut transitions under
$cal(U)_B$ factor entirely through the present-cut projection and present-cut
input via a reduced map $cal(U)_B^(upright("M"))$:

#math.equation(block: true, numbering: none, $ S^W_(B,i,k + 1) = cal(U)_B^(upright("M")) (Pi_(upright("cut")) (S^W_(B,i,k) ) , upright("input")_k ). $)

When prior return records, coupling burden, or retained memory/context enter
$cal(U)_B$ nontrivially, continuation is retained-history over
$(S^W_(B,i,k) , S^(times)_(I,B,k) )$ and its committed prefix. Both regimes carry
wave continuity whenever distinction-information persists across integer cuts
through recurring Duon cycle form.

#aod-paragraph[Falsification.]
Markovian closure at cut $k$ is falsified whenever two admissible committed
histories $(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) )$ and
$(tilde(S)^W_(B,i,lt.eq k) , tilde(S)^(times)_(I,B,lt.eq k) )$ share equal
present-cut state and identical cut-$k$ input $upright("input")_k$, differ in
retained burden or prior return, and yield distinct next-cut states:

#math.equation(block: true, numbering: none, $ Pi_(upright("cut")) (S^W_(B,i,k) ) = Pi_(upright("cut")) (tilde(S)^W_(B,i,k) ) quad "and" quad S^W_(B,i,k + 1) eq.not tilde(S)^W_(B,i,k + 1) \ "with" quad (S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) ) eq.not (tilde(S)^W_(B,i,lt.eq k) , tilde(S)^(times)_(I,B,lt.eq k) ). $)

Any witnessed pair satisfying these conditions refutes Markovian closure and
requires retained-history continuation over $(S^W_(B,i,k) , S^(times)_(I,B,k) )$.
Conversely, failure of recurring Duon cycle form to preserve
distinction-information across cuts falsifies wave continuity under either
regime.



== Downstream continuation model <subsec:q4-hamming-ternary-kernel>
#aod-anchor(<subsec:hinge-slide>)


#aod-paragraph[Setup.]
On already admitted support, choose nonnegative rational weights. The atomic-traversal kernel #eqref("eq:admitted-kernel") records H1 base changes. Fibre-only additional dwell has zero base traversals and uses the separate $0_H arrow.r 0_D$ continuation on an already entered hinge; it is not called an atomic H1 event. With
the typed continuation support split as

$ op("Adm")_B = op("Adm")^(upright("H1"))_B union.sq op("Adm")^(upright("fib"))_B , $ <eq:continuation-domain-split>

the first part contains atomic base traversals and the second contains
zero-base-traversal hinge-fibre continuations. Define the atomic kernel by

$ P_B (e', sigma ' mid(|) e, sigma ) = cases(w_B (e', sigma ') slash Z_B\, & (e', sigma ') in op("Adm")^(upright("H1"))_B\, Z_B > 0\,, 0\, & (e', sigma ') in.not op("Adm")^(upright("H1"))_B\,) quad Z_B = sum_(a in op("Adm")^(upright("H1"))_B) w_B (a). $ <eq:admitted-kernel>

For $Z_B = 0$, report empty positive-weight support; distinguish it from an empty structural admissible set. Neither case is normalized. Equal
positive weights give $1 slash N_B$; unequal weights give the anisotropic model.
Weights may use committed lag, orientation and reflection coordinates.
Both choices preserve #eqref("eq:atomic-probability-one"). Direct branch bypass
has zero support. The kernel neither supplies the first distinction nor
certifies closure from a phase threshold.


=== Hinge saturation


#aod-paragraph[Setup.]
At an already entered mandatory hinge, let $A$ be the declared finite
lawful continuation family in #eqref("eq:continuation-domain-split"), with
nonnegative rational weights $w_B :A arrow.r bb(Q)_(gt.eq 0)$. Its
additional-dwell subfamily is

$ op("Adm")^0_B (e, sigma ) = brace.l (e,0_D ) in op("Adm")^(upright("fib"))_B (e, sigma ) brace.r , $ <eq:hinge-admissible-family>

#aod-anchor(<subsec:fractal-jitter>)
Write $A_0 := op("Adm")^0_B (e, sigma )$ and define positive-weight
support by

$ A_(+) := brace.l a in A:w_B (a) > 0 brace.r . $ <eq:hinge-positive-support>

These aliases preserve the H1/fibre types and define no combined kernel.
Structural saturation is

$ op("Adm")^0_B (e, sigma ) = emptyset , $ <eq:hinge-saturation>

The corresponding weighted condition has the distinct characterization

$ sum_(a in A_0) w_B (a) = 0 quad arrow.l.r.double.long quad A_0 inter A_(+) = emptyset . $ <eq:hinge-saturation-weighted>



#aod-paragraph[Derivation.]
Under #eqref("eq:hinge-saturation"), any remaining structurally admitted
post-hinge continuation has

$ sigma ' in brace.l - 1, + 1 brace.r . $ <eq:hinge-saturation-branch-continuation>

For #eqref("eq:hinge-saturation-weighted"), a finite sum of nonnegative terms
vanishes exactly when every term vanishes. Thus every positive-weight
continuation has branch role $- 1$ or $+ 1$, but zero-weight dwell may
remain structurally admitted.
Equivalence with structural saturation would additionally require strictly
positive weight for every admitted dwell.

If the structural branch support is empty, the declared model reports pending,
reseated, shedding or lifted state. Nonempty structural support with all weights
zero instead has empty positive-weight support. Neither case supplies a
normalization. The mandatory hinge remains in both cases, and additional dwell
still has zero base traversals. Jitter records unresolved lawful continuation
before seating.
The ternary fibre has three roles; the branch-only image in
#eqref("eq:hinge-saturation-branch-continuation") has at most two, regardless of
its number of channel rows. With positive total branch weight, a declared
normalized branch-role distribution $(z,1 - z)$ has conditional choice entropy
$- z log_3 z - (1 - z) log_3 (1 - z) lt.eq log_3 2$: differentiation gives a unique
maximum at $z = 1 slash 2$, with the endpoints defined by continuity and entropy zero
when only one role has positive weight. Zero total branch weight supplies no
such distribution. This scoped role entropy differs from
#eqref("eq:ternary-capacity") and general channel capacity.


#aod-literature-note[Hypercube support: Weisstein #aod-cite("weissteinHypercubeGraph")\;
adjacency walks: MIT OCW #aod-cite("mitAdjacencyWalks"), Duncan #aod-cite("duncanAdjacencyWalks")\;
random walks: Norris #aod-cite("norrisMarkov").
Dyck/Catalan context: Stanley #aod-cite("stanleyCatalan"),
Flajolet–Sedgewick #aod-cite("flajoletSedgewick").]
