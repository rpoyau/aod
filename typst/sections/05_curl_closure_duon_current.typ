// Native Typst port of sections/05_curl_closure_duon_current.tex (verbatim scientific content).
#import "../preamble.typ": *

= Curl closure and duon current <sec:motif-field-folding>
#aod-anchor(<sec:curl-closure-duon-current>)


== Curl forms <subsec:curl-closure>


=== Curl <subsec:curl>


#aod-definition(title: [Curl. #appref("app:cc-curl")])[
Curl is returned closure through a hinge on its certified support. A$Omega$D calculates its hinge return, reclosure, duration, orientation, and returned current on declared windows.
]



=== Nested curl <subsec:nested-curl>


#aod-definition(title: [Nested curl. #appref("app:cc-nested-curl")])[
A nested curl is a curl carried inside another curl.
]



=== Pin-curl <subsec:pin-curl>


#aod-definition(title: [Pin-curl. #appref("app:cc-pin-curl")])[
A pin-curl is a returned curl whose residue seats, delays, or fixes a hinge.
]



=== Curling curls <subsec:curling-curls>


#aod-definition(title: [Curling curls. #appref("app:cc-curling-curls")])[
Curling curls are recursive returns that become active path structure inside the fractal tesseract topology.
]



== Dion <subsec:dion>


#aod-definition(title: [Dion. #appref("app:cc-dion")])[
A dion is an oriented two-position branch pattern around the retained monon hinge. Its compressed signature is

#math.equation(block: true, numbering: none, $ D_(alpha) = ( + 1, - 1), wide D_(Omega) = ( - 1, + 1). $)

]



== Duon <subsec:duon>


#aod-definition(title: [Duon. #appref("app:cc-duon-duad-cycle")])[
A duon is Dion–hinge–Dion returned-current support. In seat-compatibility notation, write $E_2 = upright("duon")$ and $E_2^0 = "open-seat duon"$. A compact unresolved form is

#math.equation(block: true, numbering: none, $ upright("duon") = D_i square.stroked D_j , wide D_i ,D_j in brace.l D_(alpha) ,D_(Omega) brace.r . $)

A resolved duon carries the monon hinge / pivot value:

$ D_i mu_M D_j , wide D_i ,D_j in brace.l D_(alpha) ,D_(Omega) brace.r , wide mu_M in brace.l - 1,0, + 1 brace.r . $ <eq:duon-current>

]



=== Current cell <subsec:duon-current-cell>

A duon current is carried hinge-current through cycle support. The primitive resolved family has

#math.equation(block: true, numbering: none, $ 2 times 3 times 2 = 12 $)

variants. Duon, duad, and temporal cycle presentation. #appref("app:cc-duon-duad-cycle").


#aod-paragraph[Finite unspooling chart.]#aod-anchor(<subsec:finite-q4-witness>)
In the inherited finite chart, a resolved Duon has four active Dion positions
and one carried monon hinge. Declaring a retained/unspooled marker at each of
the four positions gives the chart $brace.l 0,1 brace.r^4$; one-marker updates have
Hamming distance one. The marker independence is a declared chart convention,
not an extra primitive distinction or a proof that all chart words are admitted
Duon motifs. The twelve oriented Dion–pivot–Dion variants in
#eqref("eq:duon-current") are a separate grammar count.


=== Branch/hinge/branch reflection duration <subsec:branch-hinge-rd>

Reflection duration is counted on branch/hinge/branch return support. For a returned-current path history $gamma$ on $B$,

$ R D_(gamma) (B) = Pi^(-)_(gamma) (B) + H_(mu , gamma) (B) + Pi^(+)_(gamma) (B). $ <eq:branch-hinge-rd>

Here $Pi^(-)_(gamma)$ is the first-branch support, $H_(mu , gamma)$ is the hinge recurrence contribution, and $Pi^(+)_(gamma)$ is the reflected return-branch support. If the branch supports are symmetric, $Pi^(-)_(gamma) = Pi^(+)_(gamma) = Pi$, then

$ R D_(gamma) (B) = 2 Pi + H_(mu , gamma) (B). $ <eq:branch-hinge-rd-symmetric>

The familiar $R D = 2 Pi + 1$ is the single-hinge reduction $H_(mu , gamma) = 1$, not a universal hinge rule. For a retained cycle, use $R D_B (C)$ for #eqref("eq:branch-hinge-rd").
This support accessor precedes directional coupling and scalar duration in
#secref("sec:wave-state-relational-time").


== Duad <subsec:duad>


#aod-definition(title: [Duad. #appref("app:cc-duad")])[
A duad is the seat-taken state of the same duon current.
]

Seating changes state from open-seat $E_2^0$ to seated $E_2^(plus.minus)$ while preserving the identical Duon current, lineage, committed prefix and structural hinge $0_H$:

$ E_2^(plus.minus) = upright("Duad"), wide op("id") ( op("Seat")(u) ) = op("id")(u), wide sigma_(upright("seat")) (u):upright("open_seat") arrow.r.long.bar upright("seated_duad"). $ <eq:duad-same-current>




#aod-paragraph[Admission binding.]
The complete admitted motif record is

$ K_(upright("adm")) (B,i;upright("cert")) = & paren.l i,s_(upright("core")) ,cal(C)_L , chi_(mu) ,bold(upright(a)),r, sigma^C_B , \ & H T(K;i,B),op("Cert")(K;i,B) paren.r . $ <eq:motif-admission>

Admission binds identity, scope, lineage, exact trace, certificate and closure
witness. An absent or mismatched binding excludes model or harmonic use. A core signature is syntax until its construction witness is bound.
Names, enclosure, chirality and scalar RD cannot supply missing lineage. Primitive components share the target's scope, lineage and
resolution; folding instead declares the maps in #eqref("eq:fold-outer-closure").
Every consumed component is already committed and certificate-bound. Returned
current, later recurrence and Duad seating retain that identity.

$ upright("Dimonon") = 2 thin upright("Monon") eq.not upright("Dion"), wide upright("Duon") "has the support of "#eqref("eq:duon-current"). $ <eq:motif-grammar>

The carried monon pivot $mu_M$ and its state are distinct from omission of
the mandatory temporal hinge. Dion endpoint adjacency never licenses a direct
temporal branch reversal. Duad names a seated state of the same Duon current;
a generic two-cycle $C_2$ supplies neither the Duon grammar nor its witness.
Standalone trion names the threefold core unit; $3:j$ composes $j$ such
units with inherited construction provenance.


#figure(
  kind: image, [
#aod-panel(width: 90%)[




#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (auto,),
    align: (center,),
    [Branch–hinge–counterbranch: #eqref("eq:hinge-grammar")],
    [$arrow.b.double$],
    [Curl],
    [$arrow.b.double$],
    [Dion $D_(alpha) = ( + 1, - 1), med D_(Omega) = ( - 1, + 1)$],
    [$arrow.b.double$],
    [Duon current $D_i mu_M D_j$],
    [$arrow.b.double$],
    [Certified distinct reclosure and cadence: $W^(upright("id"))_(B,i)$],
    [$arrow.b.double$],
    [Scoped field organization $F_(B, lambda)$, scope $B = ( partial_T F, omega )$],
  )
}


]
  ],
  caption: [Curl-to-duon-current support.],
) <fig:curl-to-duon-current-support>



#figure(
  kind: image, [
#aod-panel(width: 88%)[

Monon: primitive completed branch–hinge–counterbranch closure \

Dion: two-position support $( + 1, - 1)$ or $( - 1, + 1)$ \

Every temporal realization retains the structural hinge. \

Dimonon: two Monon closures; Duon current: $D_i mu_M D_j$ \

Duad: seated state of that Duon current \

Distinct compatible reclosures and cadence admit a running Duon wave.

]
  ],
  caption: [Primitive closure ladder.],
) <fig:closure-ladder>



== Curling-curl support forms <subsec:curling-curl-support-forms>


A compact specification $p":"q":"L$ proposes a retained support form
$p":"q$ with enclosure/window qualifier $L$. Admission uses
#eqref("eq:motif-admission"). Declare the finite support model

$ Pi (p":"q) = q^p + q. $ <eq:curling-support-model>

Its edge-shell derivation is in #appref("app:rd-tests:corollaries").
The symmetric single-hinge reduction uses #eqref("eq:branch-hinge-rd-symmetric").
Trace, kernel choice, hinge slide, jitter, capacity and admission remain explicit.


#aod-definition(title: [Support expression])[
A support expression is formal syntax

$ Sigma = (s_1 , dots.h ,s_m ;L), $ <eq:support-expression>

where each $s_i = p_i ":"q_i$ and $L$ is an optional shared enclosure qualifier.
]



#aod-definition(title: [Curling-curl support form])[
A curling-curl support form is the retained recursive curl/cycle form proposed by a support expression and admitted on a declared boundary/window after its construction trace is declared or inherited.
]


A compact support expression proposes a specification $K_(upright("prop"))$.
Admission is a traced calculation on the declared scope:

$ K_(upright("prop")) attach(stretch(arrow.r, size: #180%), t: thin H T(K;B) thin) K_(upright("adm")) (B). $ <eq:key-proposed-admitted-trace>

Here $H T(K;B)$ is the construction trace. Closure, pressure, shedding and
comparison values follow that trace; a specification alone supplies none.

The downstream value construction is given in #eqref("eq:support-trace-spine"), after its duration, pressure and response interfaces.



#aod-provenance[#eqnref("eq:duon-current"), #eqnref("eq:duad-same-current"), #eqnref("eq:branch-hinge-rd"), #eqnref("eq:motif-admission"), #eqnref("eq:curling-support-model").]



== Scoped field organization <sec:field>
#aod-anchor(<sec:field-disposition>)
#aod-anchor(<subsec:declared-field-choice>)

A field organizes admitted recurrent wave identities at a declared scope:

$ F_(B, lambda) bar.v_k = (B, lambda ,I_B (k), brace.l W^(upright("id"))_(B,i) brace.r_(i in I_B (k)) ). $ <eq:field-organization>

Here $(B, lambda )$ is field identity and $I_B (k)$ is present membership.
Member state remains in $S^W$, not in the identity. Alias resolution maps
names to this record and then to unique wave identities; two aliases of one
wave do not supply two cadences. Existing certificates validate membership.
That validation adds no closure, recurrence or wavehood.

$ C^(upright("ret")) = "retained closure lineage", wide op("Resolve")(F_(B, lambda) ) = brace.l W^(upright("id"))_(B,i) brace.r_(i in I_B) . $ <eq:retained-lineage-field-separation>


#aod-paragraph[Memorum.]#aod-anchor(<subsec:field-memorum>)
The organization exposes members' retained predecessor closures, present
boundaries and successor horizons. Finer wave organizations can be retained
inside it. Their membership and evidence persist when a next enclosing scope
is proposed.

=== Region <subsec:field-region>


#aod-definition(title: [Region])[
A region is a declared retained part of a field. Regions carry current, closure, pressure, and returned-current orientation.
]



=== Boundary <subsec:field-boundary>


#aod-definition(title: [Boundary])[
A boundary is the retained interface of a declared region or field. Boundary accounting records current and closure across the boundary.
]



=== Tesseract-admissible field boundary <subsec:tesseract-admissible-boundary>

For a field, specialize #eqref("eq:tesseract-admissible-boundary") to
$partial_T F$ and $B = ( partial_T F, omega )$.


=== Polychiral shell dressing <subsec:polychiral-shell-dressing>


#aod-definition(title: [Polychiral shell dressing])[
A polychiral shell dressing is field outer dressing. It carries Capital-Alpha/Omega return orientation, polarization imbalance, return duration, pressure, and SADAR coupling.
]


Support expressions follow #secref("subsec:curling-curl-support-forms")\;
shared enclosure naming follows #appref("app:cc-count-compression").


#figure(
  kind: image, [
#include "../lib/figures/main/curling_curl_layers.typ"
  ],
  caption: [Curling-curl shell families.],
) <fig:curling-curl-shell-families>



#aod-paragraph[Support-enclosure integrity.]
A tetron is $E_4$: the default inner enclosure with four seats. Hexon, octon, and decon name outer shell paths. #appref("app:cc-support-enclosure-names"). A boundary can cut through a retained enclosure for accounting. That partial boundary is a sample of the enclosure structure. The complete enclosure identity follows the retained even-address topology.


== Folded outer closure <subsec:field-as-monon-compression>

A next-scope boundary enclosing retained wave organization $cal(F)$
proposes an outer return. Conditional on its successful trace and certificate,
$upright("monon")_(cal(F))$ is the enclosing instance of
#eqref("eq:monon-cycle"), carrying the internal curls, shells, cycle presentations,
duration, pressure and SADAR. This certified outer object is the premise of the
compression #eqref("eq:cycle-valued-field-compression")\; the full fold and exposure
witnesses are #eqref("eq:fold-outer-closure") and #eqref("eq:expose-inner-lineage").



== Cycle-valued field compression <subsec:cycle-valued-field-compression>


#aod-definition(title: [Cycle-valued field compression])[
Let $f = partial_T cal(F)$ be a tesseract-admissible boundary and let $B_f = (f, omega_f )$. For an internal support expression $Sigma$, the certified cycle-valued compression, conditional on an actual outer return witness, is

$ C_f [ Sigma ]_(AO) := op("cycle")_(partial_T cal(F)) [ x succ x = x; op("int") = Sigma , omega_f ]_(AO) . $ <eq:cycle-valued-field-compression>

The enclosing closure binds one next-scope closure-phase cycle; the boundary alone supplies a proposal. The internal support expression remains carried as cycle provenance.
]




#aod-paragraph[Fold and exposure.]

$ brace.l C^(upright("ret"))_(B_(ell) ,i) brace.r_i attach(stretch(arrow.r, size: #180%), t: op("Fold")^(arrow.t))K^(upright("prop"))_(B_(ell + 1)) attach(stretch(arrow.r, size: #180%), t: upright("OuterClose") + upright("OuterCert"))C^(upright("ret"))_(B_(ell + 1)) . $ <eq:fold-outer-closure>

Contact, adjacency, superposition and mixing can propose an outer structure.
The proposal binds the exact inner identities, their certificates and the map
from each inner scope to the proposed outer scope. The outer certificate commits
that construction witness; attaching an unrelated higher-scale loop afterward
does not establish the fold. Each consumed inner input precedes its consumption.
The certified outer closure contributes one complete closure-phase cycle. Its distinct compatible
outer reclosures are required for an outer wave and then field organization.

$ op("Expose")^(arrow.b) (C^(upright("ret"))_(B_(ell + 1)) ) = brace.l C^(upright("ret"))_(B_(ell) ,i) ,upright("lineage"),upright("orientation"), upright("history"),upright("certificates") brace.r_i . $ <eq:expose-inner-lineage>

For an outer wave the same exposure additionally returns each inner wave,
cadence, self-separation, current and memory. Outer shedding preserves
surviving certified inner closures and waves. Outer and inner return-identity sets
remain strictly disjoint ($op("id")_(upright("return")) (C^(upright("outer")) ) eq.not op("id")_(upright("return")) (C^(upright("inner")) )$):
inner beats cannot be reused as new outer returns, and separate cubical
chain-map commutation (#secref("prop:m3-fold-support")) supplies no outer closure
admission. Fusion applies this closure construction to a folded
complex; its pressure-resolved routing model is derived in Section #bare-ref("sec:fusion-closure-chain-reclosure").

Specialize #eqref("eq:branch-hinge-rd") to the certified single-support object:

$ R D_(AO) ( C_f [p":"q];B_f ) = Pi^(-)_f (p":"q) + H_(mu ,f) (p":"q) + Pi^(+)_f (p":"q). $ <eq:cycle-rd-accessor>

The subsequent $R D_(AO) , rho^D_(omega) ,P^D ,Q^D$ accessors consume
$C_f [ Sigma ]_(AO)$; none replaces that certified object.


== Alpha–Omega hinge kernel <subsec:ao-kernel>


#aod-definition(title: [Alpha–Omega hinge kernel])[
The explicit hinge presentations are

#math.equation(block: true, numbering: none, $ A scripts(arrow.l.r)_(mu) Omega & := "Alpha/Omega branch order through hinge " mu , \ Omega scripts(arrow.l.r)_(mu) A & := "Omega/Alpha branch order through hinge " mu . $)

For a retained cycle $C$, define the compact branch/hinge/branch operators

$ sans("AO")_(mu) (C) := op(A scripts(arrow.l.r)_(mu) Omega)(C) = chevron.l Pi_(alpha) (C), H_(mu) (C), Pi_(Omega) (C) chevron.r . $ <eq:ao-kernel>


$ sans("OA")_(mu) (C) := op(Omega scripts(arrow.l.r)_(mu) A)(C) = chevron.l Pi_(Omega) (C), H_(mu) (C), Pi_(alpha) (C) chevron.r . $ <eq:omega-alpha-hinge-kernel>

The hinge $mu$ supports handed return. The chirality tag records the branch-order orientation:

$ chi_(mu) (C) = + 1 arrow.l.r.double.long C:A scripts(arrow.l.r)_(mu) Omega , wide chi_(mu) (C) = - 1 arrow.l.r.double.long C: Omega scripts(arrow.l.r)_(mu) A. $ <eq:hinge-chirality-tag>

The hinge flip exchanges the branch order:

$ op("flip")_(mu) (A scripts(arrow.l.r)_(mu) Omega ) = Omega scripts(arrow.l.r)_(mu) A, wide op("flip")_(mu) ( Omega scripts(arrow.l.r)_(mu) A) = A scripts(arrow.l.r)_(mu) Omega . $ <eq:hinge-chirality-flip>

The compact qualifier $AO$ marks the Alpha–Omega hinge presentation in subscripts, as in $C_f [ Sigma ]_(AO)$. The forms $A Omega$ and $Omega A$ are implicit-hinge shorthand only after the explicit hinge presentation has been declared.
The $Omega$-branch is closure-subservient:

$ Pi_(Omega) (C) = op("Close")_B ( Pi_(alpha) (C),H_(mu) (C)). $ <eq:omega-close>

With branch support cardinalities, #eqref("eq:branch-hinge-rd") specializes to

$ R D_(AO) (C;B) = bar.v Pi_(alpha) (C) bar.v + H_(mu) (C) + bar.v Pi_(Omega) (C) bar.v . $ <eq:ao-rd-accessor-kernel>

]


Equation #eqref("eq:branch-hinge-rd-symmetric") then gives the single-hinge specialization

$ H_(mu) = 1, wide Pi_(Omega) = Pi_(alpha) , wide R D^(lr((1)))_(AO) = 2 bar.v Pi_(alpha) bar.v + 1. $ <eq:single-hinge-symmetric-fixture>

When the hinge recurrence is explicitly attributed to free-seat provenance, write

$ H_(mu)^([s]) (C;B), wide s(C) = "declared free-seat provenance of "C. $ <eq:free-seat-hinge-provenance>

For a full-seated single-hinge cycle, $H_(mu) (C;B) = 1$; the
notation $H_(mu)^(upright("cyc")) = 1$ attributes the hinge to that cycle.
Free-seat provenance requires its separate declaration.
