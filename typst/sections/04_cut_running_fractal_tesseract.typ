// Native Typst port of sections/04_cut_running_fractal_tesseract.tex (verbatim scientific content).
#import "../preamble.typ": *

= Closure-phase cycle and recurring wave <sec:closure-phase-wave>



== Completed retained return <subsec:monon-beat>
#aod-anchor(<subsec:monon-cycle>)

A closure trace retains its start even as the current crown advances:

$ Gamma_C = (B,r,i,a_0 ,(e_0 , dots.h ,e_n ),M_(epsilon.alt ,m) ,cal(W)_C ). $ <eq:closure-trace>

Here $r$ is scale, $i$ is lineage, the events are strictly committed in
order, and $cal(W)_C$ binds the hinge and return to the retained start.
All traversals satisfy #eqref("eq:atomic-h1"). The closure certificate is

$ op("Cert")(C) = (B,r,i,op("id")(e_0 ),op("id")(e_n ), op("digest") Gamma_C ,cal(W)_C ,upright("closed")), quad op("end")(C) tilde.op_(B,i,cal(W)_C) op("start")(C). $ <eq:closure-certificate>

The witness preserves start and ancestry: closure is certified end at that
retained start. Endpoint equality alone is insufficient. The primitive closure
of #eqref("eq:hinge-grammar") is the monon:

$ upright("Monon")(x) = op("cycle")_(sans("H")_3) (x succ x = x). $ <eq:monon-cycle>

Its phase-bearing step count is the number of committed atomic traversals,
excluding hinge dwell, certificate wrapping and replay:

$ m(C) := "#" brace.l "committed phase-bearing traversals in " Gamma_C brace.r gt.eq 2. $ <eq:closure-phase-step-count>

At least one outbound and one return traversal are required; further traversals
may precede the first certified return. Completion contributes one complete
closure-phase cycle:

$ Delta Phi (C) = 1_C . $ <eq:closure-phase>

The accessor $Phi$ counts this completion once, including both reflected
legs. Dwell, replay and further traversals within the same first return add no
cycle. The oriented ancestral trace remains retained under either the isotropic
or anisotropic model in #secref("subsec:q4-hamming-ternary-kernel").


#aod-paragraph[Symmetry.]

$ op("Close")(C) = 1 med arrow.r.double.not med op("Isotropic")(C). $ <eq:closure-not-isotropy>

Isotropy refers to a named support, model and relabelling action. Cancellation
of aggregate values preserves the contributing oriented histories. Neither
symmetry nor anisotropy changes #eqref("eq:closure-phase").


== Advance and closure memory <subsec:crown>

An admitted successor becomes the next crown through a committed advance:

$ op("Adv")_k (x_k^0 ) = x_(k + 1)^(-) , wide op("Adv")_k (h_k^(+) ) = x_(k + 1)^0 , wide h_k^(+) in cal(H)_k^(+) . $ <eq:crown-advance>

Advance carries the selected member into the next crown. A later
lineage-bound return can re-crown the retained start:

$ op("Crown")(sans("H")_3^(upright("role")) (k + L)) tilde.op_(B,i,cal(W)_C) op("Crown")(sans("H")_3^(upright("role")) (k)), wide L > 0. $ <eq:closure-memory>

Open advance is a continuation; the further return witness establishes closure.
Solitonic recurrence names preservation of certified relational form through
the stated advance and reclosure, with the ancestry and scope map retained.


== Return identity, beat and cadence

Give each completed return immutable identity

$ op("id")_(upright("return")) (C) = (B,r,i,op("id")(e_0 ),op("id")(e_n ), op("digest") Gamma_C ). $ <eq:return-identity>

Wrapping, observation and replay retain this identity. Each distinct compatible
certified reclosure contributes a beat. For completions
$k_0 < k_1 < dots.c < k_m$, define

$ upright("bip")_i ( omega ) = "#" brace.l C_(i,j) :j gt.eq 1, k_j in omega , op("id")_(upright("return")) (C_(i,j) ) " is distinct" brace.r , wide op("Sep")_(i,j) = k_(j + 1) - k_j > 0. $ <eq:beat-reclosure>

The initial closure supplies the origin of this reclosure count. At an integer
cut $k$, the cumulative accessor counts distinct committed return identities:

$ N_i^C (k) & = "#" brace.l op("id")_(upright("return")) (C_(i,j) ):k_j lt.eq k brace.r , \ Phi_i (k) & = N_i^C (k)1_C , wide upright("bip")^(lt.eq)_i (k) = max (N_i^C (k) - 1,0). $ <eq:cumulative-closure-counts>

Thus $N gt.eq 1$ completed closures give $N$ complete closure-phase cycles and $N - 1$
reclosure beats from the lineage origin. For an arbitrary native window
$omega = (u,v]$, $u,v in bb(Z)$, $u < v$, the same distinct-return count gives

$ Phi_i (v) - Phi_i (u) = (upright("bip")_i ((u,v]) + bold(1)_(brace.l u < k_0 lt.eq v brace.r) )1_C . $ <eq:closure-phase-window>

The origin contributes the indicator; later windows do not subtract another
initial closure. The exact ordered separations form cadence $op("Cad")_i = (op("Sep")_(i,j) )_j$.
It may be nonuniform; RD support and harmonic display period are separate
quantities. Recurrence is not inferred from a repeated value alone.


#aod-paragraph[Recurring wave.]
For a compatible certified closure/current lineage with distinct reclosure,
fix immutable wave identity and its growing admitted history:

$ W^(upright("id"))_(B,i) = (B,r,i,K_i^(upright("id")) , op("id")_(upright("return")) (C_(i,0) )), wide W_(B,i) bar.v_k = (W^(upright("id"))_(B,i) ,(C_(i,j) )_(k_j lt.eq k) ,op("Cad")_i bar.v_k ). $ <eq:wave-identity>

Compatibility preserves the origin's ancestor at fixed scope and representation;
a changed representation requires an identity-preserving scope map. At least two
compatible distinct completions admit the recurring wave. Field organization
then resolves those identities.


#aod-paragraph[Native running and standing classifications.]
#aod-anchor(<eq:native-running-standing>)
A running-wave classification retains an oriented recurring current lineage;
recurring oriented Duon current is the inherited running-Duon construction.
A standing organization binds compatible oppositely oriented recurrent
lineages under a declared coupling and balance condition. Zero aggregate
current by itself supplies neither recurrence nor that coupling witness.
Both classifications retain their individual return identities and histories;
the character and running/standing coordinates in #eqref("eq:fourier-transform")
and #eqref("eq:fourier-running-standing") represent these admitted organizations.


#aod-paragraph[Continuation.]
Hinge saturation restricts further same-resolution dwell. A later hinge and
an admitted continuation may follow; only a certified retained-start return
adds closure, and only a distinct compatible reclosure adds recurrence.

#aod-paragraph[Localized recurrence.]#aod-anchor(<subsec:localized-wavelet>)
A native wavelet is a localized segment of an already admitted recurrent wave:
it retains that wave's identity, its adjacent certified return events and their
positive local separation. Localization selects a segment of retained recurrence;
it does not promote an isolated monon or an arbitrary scalar pulse into a wave.
Its general localized continuation family (covering both recurrent-wave segments
and finite/shed continuations) is constructed in #secref("subsec:aod-wavelet-continuation")
by #eqref("eq:aod-wavelet-continuation"); this paragraph is its recurrent-wave
specialization. Its later harmonic representation, when used, binds that same
finite segment.

#aod-paragraph[Falsification of wave admission.]
An isolated closure, a replayed certificate, an unbound lineage, or an
unrealized successor horizon cannot satisfy #eqref("eq:wave-identity").


== Reflected-leg comparison <subsec:reflected-leg-phase>


#aod-paragraph[Setup.]
Declare a uniform atomic-event support comparison, with formal quantum
$h$ in the ordered additive domain $cal(L) = bb(N)_0 h, h > 0$.
Write $Delta phi.alt_(upright("step")) := h$ for this declared phase-bearing step
quantum. It is not a Fourier coefficient phase or a normalized circle
coordinate.
A target closure and a primitive reference are already certified at the same
scope and scale. Their reflection witnesses bind the outbound events, committed
hinge/turnaround, returning events and retained target start. Both legs are
nonempty; an arbitrary cut of a word is not that witness. Count each atomic
traversal once, excluding hinge dwell and replay:

$ delta phi.alt^(arrow.r) = n_(arrow.r) h, wide delta phi.alt^(arrow.l) = n_(arrow.l) h, wide n_(arrow.r) ,n_(arrow.l) in bb(Z)_(gt.eq 1) . $ <eq:directed-leg-operands>

The reference is a certified two-edge retained-start return with mandatory
hinge. Its support is $2 h$. Fix the comparison embedding before examining
the target:

$ iota_(upright("ref")) :bb(N)_0 1_C arrow.r.long cal(L), wide iota_(upright("ref")) (n 1_C ) = 2 n h. $ <eq:phase-unit-embedding>

This embedding compares two distinct domains: closure count and declared
event support. Uniform weighting and this reference are model choices.


#aod-paragraph[Derivation.]
Each committed leg has at least one atomic traversal, so addition in
$cal(L)$ gives

$ delta phi.alt^(arrow.r) + delta phi.alt^(arrow.l) = (n_(arrow.r) + n_(arrow.l) )h gt.eq 2 Delta phi.alt_(upright("step")) = 2 h = iota_(upright("ref")) (1_C ). $ <eq:reflected-leg-bound>

Thus, with the comparison embedding stated locally, the minimal native
shorthand is

$ 2 Delta phi.alt_(upright("step")) gt.eq 1_C . $ <eq:minimal-phase-quantum-bound>

This is a necessary phase-support conjunct of the reflected closure
certificate, never sufficient closure admission. Its other premises remain
the retained-start return, explicit event convention, lineage, reflection
witness, commitment order and certificate integrity.


#aod-paragraph[Specialization.]
Under declared reflected-path symmetry and equal operands,

$ delta phi.alt^(arrow.r) = delta phi.alt^(arrow.l) = delta phi.alt quad arrow.r.double.long quad delta phi.alt^(arrow.r) + delta phi.alt^(arrow.l) = 2 delta phi.alt gt.eq iota_(upright("ref")) (1_C ). $ <eq:equal-leg-factorization>

For unequal leg counts, the sum equals neither doubled leg. Each doubled
leg may separately satisfy the lower bound, but factorization of the sum
requires equal operands. With the embedding understood, $2 delta phi.alt gt.eq 1_C$
denotes this equal-whole-leg specialization. It is distinct from the
minimal-step shorthand in #eqref("eq:minimal-phase-quantum-bound").


#aod-paragraph[Falsification.]
A missing or misbound reflection witness, signed branch cancellation used as
support, incompatible reference scale, nonminimal reference, or unequal-leg
factorization violates the derivation. Passing the phase-support bound while
the endpoint remains open, the lineage is unbound, or the witness/certificate
is absent does not admit closure. The comparison supplies no duration,
stochastic weight or flux.


#aod-provenance[#eqref("eq:atomic-h1"),
#eqref("eq:hinge-grammar"),
#eqref("eq:closure-certificate"),
#eqref("eq:phase-unit-embedding").]
