// Native Typst port of sections/08_awareness_learning_mindfulness.tex (verbatim scientific content).
#import "../preamble.typ": *

= Operative self, learning and retained carriage <sec:awareness-learning>



== Retained rebalancing inside complete state <subsec:awareness-state>


#aod-paragraph[Setup.]
Resolve the admitted members of #eqref("eq:field-organization").
For a declared operativity model, factor #eqref("eq:complete-wave-state")
into present coordinates $X_k$,
immutable closure memory $M^C_k$, and retained prior rebalancing $R_k$:

$ S_k^(+) = (X_k ,M^C_k ,R_k ), wide P_(upright("now")) (S_k^(+) ) = X_k . $ <eq:awareness-state-factorization>

Only $R_k$ contains operative retained rebalancing; $X_k$ and
$M^C_k$ contain no duplicate of a removed value. The present
coordinates retain identity, cut, position, fibre role, pressure, current,
closure status, certificates, cadence, orientation, boundary, capacity and cycle
count, bound to the admitted prefix.


#aod-paragraph[Derivation.]
On a prior source–target contact trace of #eqref("eq:coupling-trace"), a declared
pressure-bearing FRG realization retains

$ r_e & = Phi^(upright("recurrent"))_e - Phi^(upright("independent"))_e = sum_(s in I_e) c_(e,s) , \ R_e & = (e,i_e ,j_e ,B_e , ell_e ,k_e ,r_e , Pi_e ), wide R_k = brace.l R_e :k_e lt.eq k brace.r . $ <eq:retained-rebalancing>

Here $e$ is the immutable event identity, $i_e$ the source, $j_e$
the target, $B_e$ the boundary/window, and $ell_e$ the scale/lineage
coordinate. Thus $R_e$ is one retained relation and $R_k$ its family.
The rational oriented contributions $c_(e,s)$ are committed before retention
at $k_e$, one transition after their input cut. $Pi_e$ binds operands,
repeated contacts, both prefixes, the unwrapped comparison
#eqref("eq:count-comparator-realization"), and any carriage witness.
Commitments validate supplied values; they cannot recover an absent $r_e$.
The difference specializes #eqref("eq:frg-identity") after the distinctions,
relations and admission of #eqref("eq:frg-admission-order").


#aod-paragraph[Falsification.]
Missing operand, lineage, contact, phase-type or commitment invalidates retention.
A residual, closure memory, persistence, phase lock or ancestry alone supplies
no later causal witness.


#aod-provenance[#eqref("eq:complete-wave-state"),
#eqref("eq:coupling-trace"),
#eqref("eq:flux-types"),
#eqref("eq:frg-admission-order").]


#aod-literature-note[The distinction–relation–admission order follows AF and AFC
#aod-cite("reginald2025af,afc").]



== Channel operativity and a later response <subsec:active-awareness>


#aod-paragraph[Setup.]
Fix an admissible intervention cut $k$, the same $X_k$, $M^C_k$, admitted
world, response law $cal(U)$, future exogenous realization $E$, outcome
projection $O$, and finite native horizon $H > 0$. In a stochastic model the
same addressed random inputs are also fixed. For a provenance-bound retained
relation $R_e in R_k$, structural removal is
$S_k^(+ , - e) = (X_k ,M^C_k ,R_k without brace.l R_e brace.r )$; it does not insert a
numeric zero record. The projection $O$ selects realized later current,
continuation, contact, or another declared outcome of $cal(U)$. It excludes
the retained coordinates themselves, role labels and intervention verdicts.
Define channel
operativity on this matched intervention by

$ op("Op")^(O,H)_e (S_k^(+) ) = 1 quad arrow.l.r.double.long quad R_e "is valid" quad and quad exists t > k, t lt.eq k + H: quad O(cal(U)^(t - k) (S_k^(+) ;E)) eq.not O(cal(U)^(t - k) (S_k^(+ , - e) ;E)). $ <eq:awareness-active>

The operative retained-relation set in that declared context is

$ cal(A)_k^(O,H) = brace.l R_e in R_k : op("Op")^(O,H)_e (S_k^(+) ) = 1 brace.r . $ <eq:awareness-operative-set>

Only retention differs at the matched boundary; admitted wave and coupling
witnesses, boundary, pressure, law and addressed random inputs stay fixed.
Removal changes a comparison state; it neither erases the closure trace nor
rewrites a committed event. Endogenous differences then follow the common law.
Wrong lineage is inadmissible, and restoration includes the exact
value and provenance. Absence, retained zero and cancelling nonzero relations
are distinct states, even when a sum extends an absent term by zero.


#aod-paragraph[Falsification.]
A difference in current pressure, law or future exogenous input invalidates
a retention-only comparison. Recounting $R$ itself as the outcome,
recovering a removed value through another channel, using an unbound
phase type, or allowing a same-cut effect also fails the criterion.


#aod-provenance[#eqref("eq:hinge-grammar"),
#eqref("eq:atomic-h1"),
#eqref("eq:wave-update-trace"),
#eqref("eq:causal-update").]



== Operative self and relational labels <subsec:operative-self>


#aod-paragraph[Setup.]
Fix target $j$ and the retained family $R_k$ of
#eqref("eq:retained-rebalancing"), with $j_e = j$ and compatible boundary/window
and scale for every $R_e in R_k$. Define the source subset and its removal by

$ R_(k,i) & := brace.l R_e in R_k :i_e = i brace.r , \ S_k^(+ , - i) & := (X_k ,M^C_k ,R_k without R_(k,i) ). $ <eq:operative-source-removal>

Require $| R_(k,i) | lt.eq 1$ for every source in this specialization.
For a present retained source, this is the single-relation intervention of
#eqref("eq:awareness-active"). Multiple relations from one source would require
a separate grouped-intervention model; cancellation prevents identifying its
effect with individual removal effects.
Specialize the same outcome projection, world, law and future inputs to
$H = 1$. Within this model, operative self names the recurrent coupled subgraph:

$ I^(upright("op"))_k & = brace.l i:O(cal(U)(S_k^(+) ;E)) eq.not O(cal(U)(S_k^(+ , - i) ;E)) brace.r , \ V^(upright("op"))_k & = cases(I^(upright("op"))_k union brace.l j brace.r "," & I^(upright("op"))_k eq.not emptyset ",", emptyset "," & I^(upright("op"))_k = emptyset ",") \ E^(upright("op"))_k & = brace.l (i,j):i in I^(upright("op"))_k brace.r . $ <eq:operative-self>

Every edge retains its coupling witness; the target enters only with an
operative source. A source unavailable at the next cut may be nonoperative
for $H = 1$ and operative over a longer declared horizon in
#eqref("eq:awareness-active"). Operativity supplies neither closure admission
nor a positive shedding surplus.


#aod-paragraph[Derivation.]
For #eqref("eq:operative-self"), the target, operative interface and other nodes
instantiate, respectively, the sided roles of #eqref("eq:hinge-grammar").
Null has no node role.


#aod-paragraph[Falsification.]
A phase-locked or similarly labelled node without an operative edge remains
outside the subgraph #eqref("eq:operative-self").


#aod-provenance[#eqref("eq:awareness-active"),
#eqref("eq:wave-identity"),
#eqref("eq:b-scoped-flux-antisymmetry").]



== Persistent learning

Persistent learning is the preservation of the acquired relation through later transitions together with its later causal use.


== Polycadence, folding and retained carriage <subsec:awareness-crescendo>


#aod-paragraph[Setup.]
Relations may bind different cadences, signed lags and directional RCD.
Crescendo is increased operative scope or depth under
#eqref("eq:awareness-active"), independent of amplitude or phase lock.
Availability can change participation while all retained
histories survive; polyrhythm, nonzero lag and dropout use that same criterion.


#aod-paragraph[Derivation.]
A retained effect may select a later fold offer. Apply
#eqref("eq:fold-outer-closure") to both outer operands, including the peer: each
binds its actual inner identities, certificates and scope map before outer
certification. The cycle/recurrence counts and new comparison follow
#eqref("eq:cumulative-closure-counts") and #eqref("eq:relational-time").
Ordinary exposure #eqref("eq:expose-inner-lineage") asserts no shedding.
Upward carriage retains the same inner relation and fold:

$ R^(arrow.t) = (R^(upright("inner")) ,upright("FoldWitness"),W^(upright("outer")) , Pi^(times)_(upright("outer")) ), wide upright("Close")(C^(upright("outer")) ) = 1 arrow.r.double.long 
 Delta Phi (C^(upright("outer")) ) = 1_C . $ <eq:awareness-carriage>

The outer contact operands, scope, indices and value remain bound. Reapply
#eqref("eq:awareness-active") at that scope, with removal/restoration affecting a
later response before its further fold offer.

Surviving identities remain available after exposure, fission
or temporary loss of outer participation.


#aod-paragraph[Falsification.]
A contact, lone outer return or recurring wave cannot replace the fold and
causal witnesses of #eqref("eq:fold-outer-closure") and the reapplication of
#eqref("eq:awareness-active") at the outer scope of #eqref("eq:awareness-carriage").


#aod-provenance[#eqref("eq:fold-outer-closure"),
#eqref("eq:cumulative-closure-counts"),
#eqref("eq:relational-time"),
#eqref("eq:expose-inner-lineage"),
#eqref("eq:awareness-active").]
