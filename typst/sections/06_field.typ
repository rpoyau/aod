// Native Typst port of sections/06_field.tex (verbatim scientific content).
#import "../preamble.typ": *

= Field and SADAR <sec:stokes-sadar-harmonic>
#aod-anchor(<sec:afc-stokes-seed>)
#aod-anchor(<subsec:afc-stokes-identity>)

The finite flux and response constructions retain their declared channel histories.
For a committed value trace of #eqref("eq:wave-identity"), the harmonic
representation begins at #eqref("eq:fourier-transform").

== Typed finite flux


#aod-paragraph[Setup.]
AFC declares normalized memory $p_i^(upright("mem")) gt.eq 0$, $sum_i p_i^(upright("mem")) = 1$,
and a stochastic kernel $P$. A$Omega$D separately resolves pressure-bearing
values of admitted returned channels. Keep their types explicit:

$ phi.alt^(upright("AFC"))_(i j) = p_i^(upright("mem")) P_(i j) - p_j^(upright("mem")) P_(j i) , wide phi.alt^(upright("AOD"))_(i j) (B) = p^D_(i j) (B)A_(i j) (B). $ <eq:flux-types>

Each normalized product lies in $[0,1]$, hence
$bar.v phi.alt^(upright("AFC"))_(i j) bar.v lt.eq 1$. A$Omega$D pressure-bearing channel values
use their declared count domain. Orientation reversal of a
fixed antisymmetric flux changes its sign. A separately constructed reverse
channel retains its own directional RCD and need not have the same magnitude.


#aod-paragraph[Joint invariance.]
For a relabelling $g$, $p^(upright("mem"))_(g i) = p^(upright("mem"))_i$ and
$P_(g i,g j) = P_(i j)$ imply $phi.alt^(upright("AFC"))_(g i,g j) = phi.alt^(upright("AFC"))_(i j)$
by substitution. With only kernel invariance, the flux difference is

#math.equation(block: true, numbering: none, $ phi.alt^(upright("AFC"))_(g i,g j) - phi.alt^(upright("AFC"))_(i j) = (p^(upright("mem"))_(g i) - p^(upright("mem"))_i )P_(i j) - (p^(upright("mem"))_(g j) - p^(upright("mem"))_j )P_(j i) , $)

which need not vanish.


#aod-paragraph[Region and boundary.]
Let $V$ be the finite vertex set, $R subset.eq V$, and
$partial R = brace.l (i,j):i in R,j in.not R brace.r$ its oriented cut.

$ op("div")(i;B) = sum_(j in V) phi.alt_(i j) (B). $ <eq:b-scoped-divergence>


=== Finite Stokes


#aod-paragraph[Derivation.]
For either one declared antisymmetric flux type, split the double sum:

$ sum_(i in R) op("div")(i;B) & = sum_(i,j in R) phi.alt_(i j) (B) + sum_(i in R,j in.not R) phi.alt_(i j) (B) \ & = sum_(i in R,j in.not R) phi.alt_(i j) (B). $ <eq:afc-stokes-used>

The internal sum is zero because each ordered pair cancels its reverse and
diagonal entries are zero. Cancellation removes a summed value, not the
two contributing lineage records. The same finite argument holds componentwise.

$ phi.alt^(upright("AOD"))_(i j, AO) (B) = p^D_(i j, AO) (B)A_(i j, AO) (B). $ <eq:afc-flux-ao-resolution>

In the remaining pressure formulas $phi.alt$ abbreviates $phi.alt^(upright("AOD"))$.

#aod-paragraph[Falsification.] Wrong antisymmetry or an omitted boundary channel
breaks the finite identity.


#aod-provenance[#eqref("eq:rcd-coupling"),
#eqref("eq:flux-types"),
#eqref("eq:afc-stokes-used").]




#aod-literature-note[AFC Choices (memory, stochastic kernel, flux) and
Stokes corollary, finite internal-pair cancellation: Poyau #aod-cite("afc"),
Choices 1–5, Corollary 1 and equation (1),
source revision #link("https://github.com/rpoyau/afc/commit/5a25e8bd5bbc3f20ec4413a6b63abc420b7a54cb")[#raw("5a25e8bd5bbc")].]


=== $B$-scoped flux contents <subsec:b-scoped-flux-contents>

Resolve the A$Omega$D channel operands of #eqref("eq:flux-types") on
$B = ( partial F, omega )$.

For a declared path-history family $cal(H)_(i j) (B)$, the path-history pressure is

$ p^D_(i j) (B) = sum_(h in cal(H)_(i j) (B)) C_(3,h) rho^D_(omega ,h) (B). $ <eq:path-history-pressure>

A compressed channel form is licensed only after the declared compression

$ sans("Comp")_(i j) : brace.l (C_(3,h) ,R D_h ,R^(upright("asym"))_h ,A_h ) brace.r_(h in cal(H)_(i j) (B)) arrow.r.bar (C_(3,i j) , rho^D_(i j) ,A_(i j) ). $ <eq:path-history-compression>

Under that declared compression,

$ p^D_(i j) (B) = C_(3,i j) rho^D_(omega ,i j) (B) = C_(3,i j) min ( rho^D_(i j) (B), bar.v omega bar.v_(i j) ) . $ <eq:b-scoped-channel-pressure>

The bare-duration form is the neutral-reflection reduction:

#math.equation(block: true, numbering: none, $ R^(upright("asym"))_(i j) (B) = upright("id") quad arrow.r.double quad rho^D_(i j) (B) = D_(i j) (B). $)

The direction term is

$ A_(i j) (B) = Delta chi^(upright("lag"))_(i j) (B)i_(i j) (B). $ <eq:b-scoped-channel-attention>

The A$Omega$D branch of #eqref("eq:flux-types") gives

$ phi.alt_(i j) (B) = p^D_(i j) (B)A_(i j) (B). $ <eq:b-scoped-flux>

Equivalently,

$ phi.alt_(i j) (B) = C_(3,i j) rho^D_(omega ,i j) (B) Delta chi^(upright("lag"))_(i j) (B)i_(i j) (B). $ <eq:b-scoped-flux-expanded>


#aod-paragraph[Magnitude and direction.]
In #eqref("eq:b-scoped-flux"), $p^D$ is magnitude and $A$ is direction.
Scaling every $p^D$ by $lambda$ at fixed orientation and channel family
scales both $phi.alt$ and its attention sum $bold(upright(A))_F$ by $lambda$.

For a fixed antisymmetric flux on the oriented pair $(i,j)$:

$ phi.alt_(j i) (B) = - phi.alt_(i j) (B), wide phi.alt_(i i) (B) = 0. $ <eq:b-scoped-flux-antisymmetry>

When $i_(i j) (B)$ has components, the antisymmetry and Stokes identity are evaluated componentwise.

The divergence is the sum defined in #eqref("eq:b-scoped-divergence").

Specializing #eqref("eq:afc-stokes-used") to this flux gives

$ sum_(i in R) op("div")(i;B) = sum_(i in R \ j in.not R) phi.alt_(i j) (B). $ <eq:b-scoped-stokes>


#figure(
  kind: image, [
#aod-panel(width: 94%)[



#strong[SADAR as $B$-scoped A$Omega$D flux] \


#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (28.0%, 5.0%, 1fr),
    align: (left, left, left),
    [Scope], [$arrow.r$], [$B = ( partial F, omega )$],
    [RCD], [$arrow.r$], [$op("RCD")_(i j) (B) = R D_B (C_(i j) ) bowtie_B R^(upright("asym"))_(i j) (B)$],
    [Scalar duration], [$arrow.r$], [$rho^D_(i j) (B) = op("dur")(op("RCD")_(i j) (B))$],
    [Window clip], [$arrow.r$], [$rho^D_(omega ,i j) (B) = min ( rho^D_(i j) (B), bar.v omega bar.v_(i j) )$],
    [Magnitude], [$arrow.r$], [$p^D_(i j) (B) = C_(3,i j) rho^D_(omega ,i j) (B)$],
    [Direction], [$arrow.r$], [$A_(i j) (B) = Delta chi^(upright("lag"))_(i j) (B)i_(i j) (B)$],
    [Flux], [$arrow.r$], [$phi.alt_(i j) (B) = p^D_(i j) (B)A_(i j) (B)$],
    [Attention], [$arrow.r$], [$bold(upright(A))_F (B) = sum_((i,j) in F(B)) phi.alt_(i j) (B)$],
    [Motion], [$arrow.r$], [$(S^W_k ,S^W_(k + 1) )" under "cal(U)_B$],
  )
}


]
  ],
  caption: [SADAR as $B$-scoped A$Omega$D flux.],
) <fig:sadar-b-scoped-afc-flux>



#aod-provenance[#eqnref("eq:afc-stokes-used")\; #eqnref("eq:afc-flux-ao-resolution")\; #eqnref("eq:b-scoped-flux")\; #eqnref("eq:b-scoped-stokes").]



=== Slice flux <subsec:slice-flux>


#aod-definition(title: [Duon slice flux])[
For a declared cut-frame $t$, let

#math.equation(block: true, numbering: none, $ B bar.v_t = ( partial F, brace.l t brace.r ). $)

The duon-current slice flux is the one cut-frame crossing

$ Phi^D_(partial R) (t;B bar.v_t ) = sum_(e in partial R(t)) phi.alt_e (B bar.v_t ). $ <eq:slice-flux>

When the scope is fixed, write $Phi^D_(partial R) (t)$. For raw duon-current content, $phi.alt_e (B bar.v_t ) = epsilon_e C_(3,e)$.
]



=== Window current <subsec:window-current>


#aod-definition(title: [Window duon current])[
The window current is the retained many-frame continuation

$ J^D_(partial R) ( omega ;B) = sum_(t in omega) Phi^D_(partial R) (t;B bar.v_t ). $ <eq:window-current>

When the scope is fixed, write $J^D_(partial R) ( omega )$.
]

The raw capacity crossing count is

$ N^D_(partial R) ( omega ;B) = sum_(t in omega) sum_(e in partial R(t)) C_(3,e) . $ <eq:raw-capacity-crossing-count>

The magnitude current is

$ J^D_(upright("mag")) ( omega ;B) = sum_(t in omega) sum_(e in partial R(t)) p^D_e (B bar.v_t ). $ <eq:magnitude-current>

When the declared boundary/window partitions current status, require

$ J^D_(upright("mag")) = J^D_(upright("in")) + J^D_(upright("out")) + J^D_(upright("pending")) . $ <eq:current-magnitude-split>



=== Moving boundary <subsec:moving-boundary>

For a moving retained boundary, the window may record crossing, sweep, and shedding terms as

$ Phi^D_(partial R,upright("mov")) (t) = Phi^D_(upright("cross")) (t) - Phi^D_(upright("sweep")) (t) + Phi^D_(upright("shedding")) (t). $ <eq:moving-boundary>

Here crossing is duon current crossing the retained boundary, sweep is support swept by boundary motion, and shedding is disturbance that breaks from the retained boundary.


=== Regional boundary template <subsec:regional-boundary-template>

The same boundary/current form applies across familiar region choices. Declare a region, declare $partial R$, and account for current crossing, returning, and remaining pending.


#figure(
  kind: image, [
#aod-panel(width: 94%)[



#strong[Duon-current boundary accounting] \


#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (1fr, 1fr, 1fr, 1fr),
    align: (left, left, left, left),
    [#strong[Internal retained]], [#strong[Exoshedding]], [#strong[Reflected return]], [#strong[Pending return]],
    [recurring core], [crosses $partial R$], [returns through shell], [remains over $omega$],
    [scalar burden], [shell crossing], [next emission], [duration overlap],
  )
}
 \


$Phi^D_(partial R) (t;B bar.v_t ) = sum_(e in partial R(t)) phi.alt_e (B bar.v_t )$ \

$J^D_(partial R) ( omega ;B) = sum_(t in omega) Phi^D_(partial R) (t;B bar.v_t )$

]
  ],
  caption: [Duon-current boundary accounting.],
) <fig:v39-duon-current-boundary-accounting>



#aod-provenance[#eqnref("eq:duon-current"),
#eqnref("eq:slice-flux"),
#eqnref("eq:window-current"),
#eqnref("eq:moving-boundary").]



== Field count <sec:field-count-sadar-scope>



=== Scope <subsec:field-count-fixed-scope>

Fix a boundary/window scope

#math.equation(block: true, numbering: none, $ cal(B) = ( partial F, omega ). $)

All quantities in this subsection are evaluated with respect to $cal(B)$.


=== Retained field family <subsec:retained-field-family>

Let

#math.equation(block: true, numbering: none, $ cal(F)_(cal(B)) = brace.l F_1 , dots.h ,F_(n_F) brace.r $)

be the retained field family, and define

$ n_F (cal(B)) := bar.v cal(F)_(cal(B)) bar.v . $ <eq:field-count>

Here $n_F$ is retained field count, $T$ is path/account duration or tick count, $m$ is enclosure order in $sans("C")_(2 m)$, and $p$ is rotor or cycle completion period.


=== Returned-current channels <subsec:returned-current-channels>

For $F_i ,F_j in cal(F)_(cal(B))$, write

#math.equation(block: true, numbering: none, $ ADAR_(i arrow.l j) $)

for the returned-current channel from $F_j$ into $F_i$. The diagonal terms are self-return terms; off-diagonal terms are cross-return terms. A retained field family may carry field-ring returned-current relations when $E_(upright("return"))$ is declared on the fixed boundary/window.


=== Field-count term <subsec:field-count-term>

For $n_F (cal(B)) gt.eq 1$, the declared count-weighting model is

$ cal(O)_(partial F) (cal(B)) = n_F (cal(B)) log n_F (cal(B)), $ <eq:field-count-term>

with the logarithm base fixed by the declared calculation. Alias names are
resolved before counting; an isolated monon is not a field. Coupled-field
counting requires at least two resolved organizations.


#aod-paragraph[Calculation split.]
Field-count scaling and shell/enclosure routing are connected by the declared boundary/window, but they are separate calculations:

#math.equation(block: true, numbering: none, $ B arrow.r cal(F)_B arrow.r n_F (B) arrow.r ADAR_(i arrow.l j) arrow.r cal(O)_(partial F) (B) arrow.r SADAR . $)

Shell/enclosure routing fixes

#math.equation(block: true, numbering: none, $ cal(C)_(2 m) & arrow.r X_(upright("shedding")) arrow.r upright("SheddicPath")(X_(upright("shedding")) ), \ upright("SheddicPath") & arrow.r brace.l "rebalancing", "exoshedding", "endoshedding", "redirected support routing" brace.r . $)





#aod-provenance[#eqnref("eq:field-count"),
#eqnref("eq:field-count-term"),
#eqnref("eq:field-organization").]



== Duonic pressure <sec:duonic-pressure-inertia>



=== Scalar burden <subsec:duonic-pressure-scalar-burden>


#aod-definition(title: [Channel pressure])[
Channel pressure is #eqref("eq:b-scoped-channel-pressure") on the declared
compression. Duration participation is #eqref("eq:window-clipped-rho")\;
seat retention has the distinct interface #eqref("eq:support-enclosure-retention").
]


#aod-definition(title: [Duonic pressure])[
The scalar pressure of a field is

$ P^D_F (B) = sum_(e in F(B)) p^D_e (B). $ <eq:duonic-pressure>

It records the retained/clipped duon/trit burden carried on the declared boundary/window; pending overhang is recorded separately by $Q^D$.
]



=== Pressure weighting <subsec:duonic-pressure-weighting>

When $P^D_F (B) > 0$, a normalized orientation $theta_F^(lr((q)))$ may be weighted by scalar pressure to provide scalar factors later used in $bold(upright(A))_F (B)$ in #secref("sec:field:sadar").


=== Inertial burden <subsec:inertial-burden>

Duonic pressure resists change of attention orientation. In the declared inverse-pressure response model with $P^D_F (B) > 0$, a committed perturbing current supplies the next-transition orientation increment:

#math.equation(block: true, numbering: none, $ Delta theta_(F,k + 1)^(lr((q))) = frac(Delta J_(upright("duon"))^(lr((q))), P^D_F (B)). $)



#aod-provenance[#eqnref("eq:b-scoped-channel-pressure"),
#eqnref("eq:window-clipped-rho"),
#eqnref("eq:duonic-pressure").]





== SADAR value operator <subsec:sadar-operator>


#aod-definition(title: [SADAR operator])[
Write $SADARop_B$ for the scalar value operator of SADAR, defined in #secref("subsec:sadar-balance"), on the declared boundary/window $B$. For a retained cycle $C$,

$ SADARop_B (C) = phi.alt_(C, AO) (B) = p^D_(C, AO) (B)A_(C, AO) (B). $ <eq:sadar-operator-cycle>

Expanded,

$ SADARop_B (C) = C_(3,C) rho^D_(omega ,C) (B) thin Delta chi_C^(upright("lag")) (B)i_C (B). $ <eq:sadar-operator-expanded>

For two committed SADAR-coupled recurrent lineages $C_u ,C_v$,

$ SADARop_B (C_u ,C_v ) = phi.alt^(upright("beat"))_(u v, AO) (B) = p^D_(u v, AO) (B)A_(u v, AO) (B). $ <eq:sadar-operator-beat-coupling>

]

If $macron(e)$ is the reversed oriented boundary element of $e$, then

$ SADARop_B (C_(macron(e)) ) = - SADARop_B (C_e ). $ <eq:sadar-orientation-antisymmetry>




== SADAR <sec:field:sadar>
#aod-anchor(<subsec:sadar>)



=== ADAR channel <subsec:adar-channel>


#aod-definition(title: [ADAR])[
ADAR is one local returned-current channel:

$ ADAR_(i j) (B) = (A_(i j) (B),D_(i j) (B),R^(upright("asym"))_(i j) (B)). $ <eq:adar-channel>

Its operands are attention orientation #eqref("eq:b-scoped-channel-attention"),
returned duration #eqref("eq:returned-duration"), and the channel's asymmetric
reflection on $B$.
]



=== SADAR balance <subsec:sadar-balance>


#aod-definition(title: [SADAR])[
SADAR is Symmetric Attention–Duration–Asymmetric Reflection. It is the field's symmetry-chasing returned-current dynamic on a declared boundary/window. For $B = ( partial F, omega )$,

$ SADAR_F (B) = ( ADAR_(i j) (B))_((i,j) in F(B)) . $ <eq:sadar-field>

]

The family retains incidence, phase relation and pressure. Relative balance
uses attention, duration, asymmetric reflection, phase bias, reseating and shedding.


=== SADAR attention vector <subsec:sadar-attention-vector>


#aod-definition(title: [SADAR attention vector])[
The SADAR attention vector is the boundary/window-specific codification of SADAR dynamics. It records pressure-weighted response input of returned duon current on the declared boundary/window:

$ bold(upright(A))_F (B) = sum_((i,j) in F(B)) phi.alt_(i j) (B). $ <eq:sadar-attention-vector>

Equivalently,

$ bold(upright(A))_F (B) = sum_((i,j) in F(B)) C_(3,i j) rho^D_(omega ,i j) (B) Delta chi^(upright("lag"))_(i j) (B)i_(i j) (B). $ <eq:sadar-attention-vector-expanded>

]

The expanded sum substitutes #eqref("eq:b-scoped-flux-expanded")\; pressure and
orientation retain their separate channel types.


=== Phase bias, push/pull, and motion <subsec:phase-bias-motion>

Phase bias is the signed lead–lag imbalance of returned-current channels. Push and pull are signed phase-biased components of the same SADAR attention vector.

#aod-paragraph[Realized motion.]
The pressure-bearing attention vector is an input to the declared update.
Motion is its realized state transition:


$ op("motion")_(F,k + 1) (B) = (S^W_(F,k) ,S^W_(F,k + 1) ), wide S^W_(F,k + 1) = cal(U)^(SADAR)_B (S^W_(lt.eq k) ,S^(times)_(lt.eq k) ,bold(upright(A))_(F, lt.eq k) ). $ <eq:causal-update>

All pressure, lag and directional-duration inputs are committed through
$k$; the response is at $k + 1$. No coordinate is generated by the same
response that consumes it. A zero scalar residual alone does not witness
an admissible closure transition. 
The support triples AO and OA exchange branches; their
oriented signed values obey $A O = - O A$, with the hinge count retained.#aod-anchor(<eq:ao-oa-oriented-value>)


#aod-paragraph[Incident return shift.]
If $bold(upright(A))_F (B) = 0$ and an unmatched incident returned duon $e$ contributes

#math.equation(block: true, numbering: none, $ phi.alt_e (B) = p^D_e (B)A_e (B), $)

then

$ bold(upright(A))_(F + e) (B) = phi.alt_e (B). $ <eq:incident-return-shift>

If a matching return $macron(e)$ is declared and $phi.alt_(macron(e)) (B) = - phi.alt_e (B)$, then

$ bold(upright(A))_(F + e + macron(e)) (B) = 0. $ <eq:matched-return-cancellation>



#aod-paragraph[Short window and high incident current.]
If $bar.v omega bar.v_h < rho^D_h (B)$, then $rho^D_(omega ,h) (B) = bar.v omega bar.v_h$ and $Q^D_h (B) > 0$. For a short window,

#math.equation(block: true, numbering: none, $ p^D_h (B) = C_(3,h) bar.v omega bar.v_h . $)

Many incident histories or large $C_(3,h)$ can still shift the SADAR attention vector when

#math.equation(block: true, numbering: none, $ sum_h p^D_h (B)A_h (B) eq.not 0. $)


The channel-level rate form is

#math.equation(block: true, numbering: none, $ Delta phi.alt_(i j) = p^D_(i j) Delta A_(i j) $)

when retained pressure is fixed across the compared restrictions. Pending overhang separates from clipped pressure:

$ Q^(D,upright("dur"))_(i j) (B) = max ( 0, rho^D_(i j) (B) - bar.v omega bar.v_(i j) ) , $ <eq:duration-overhang>


$ Q^D_(i j) (B) = C_(3,i j) Q^(D,upright("dur"))_(i j) (B). $ <eq:burden-overhang>

A falling field may remain internally balanced relative to its own boundary/window while its SADAR attention vector is phase-biased relative to another declared boundary.


=== Self-return and cross-return <subsec:self-cross-return>

A single declared field carries self-return symmetry:

#math.equation(block: true, numbering: none, $ ADAR_(i arrow.l i) = "self-return channel". $)

When another field is included in the same accounting scope, cross-return channels are added:

#math.equation(block: true, numbering: none, $ ADAR_(i arrow.l j) = "cross-return channel", wide i eq.not j. $)

Self-return and cross-return are channel forms inside the same SADAR balance. The field ring gate has the declared boundary gates, returned-current relations and value domain of #secref("subsec:fractal-field-ring-gate").


=== Boundary-relative simultaneity <subsec:boundary-relative-simultaneity>

Boundary-relative simultaneity names the coexistence of component-field and enclosing-field SADAR balances. Component fields and enclosing fields may each carry their own SADAR attention vector because each vector is scoped by its declared boundary/window. For the enclosing two-field scope, write

#math.equation(block: true, numbering: none, $ cal(B)_(12) = ( partial F_(12) , omega_(12) ). $)

Then

#math.equation(block: true, numbering: none, $ bold(upright(A))_(F_1) (B_1 ), wide bold(upright(A))_(F_2) (B_2 ), wide bold(upright(A))_(F_1 parallel F_2) (cal(B)_(12) ). $)

For three fields, write

#math.equation(block: true, numbering: none, $ cal(B)_(123) = ( partial F_(123) , omega_(123) ), $)

and

#math.equation(block: true, numbering: none, $ bold(upright(A))_(F_1) (B_1 ), quad bold(upright(A))_(F_2) (B_2 ), quad bold(upright(A))_(F_3) (B_3 ), quad bold(upright(A))_(F_(12)) (cal(B)_(12) ), quad bold(upright(A))_(F_(123)) (cal(B)_(123) ). $)



#figure(
  kind: image, [
#aod-panel(width: 91%)[

#strong[Component scopes.]
$bold(upright(A))_(F_1) (B_1 )$ and $bold(upright(A))_(F_2) (B_2 )$ retain their own
boundary/window and wave participants.



#v(0.8em)

#strong[Enclosing scope.]
$bold(upright(A))_(F_1 parallel F_2) (cal(B)_(12) )$ is evaluated on its declared
enclosing boundary after recurrent membership is resolved.



#v(0.8em)

#strong[Committed attention and later motion.]

#math.equation(block: true, numbering: none, $ bold(upright(A))_(F,k) (B) = sum_(e in F(B)) C_(3,e) rho^D_(omega ,e) (B) Delta chi^(upright("lag"))_(e,k) (B)i_(e,k) (B), $)


#math.equation(block: true, numbering: none, $ S^W_(F,k + 1) = cal(U)_B^(SADAR) (S^W_(lt.eq k) ,S^(times)_(lt.eq k) ,bold(upright(A))_(F, lt.eq k) ). $)

The realized transition is motion. Unresolved excess follows a declared
sheddic path. Component projections are taken from the already declared
attention vector; they do not create a separate motion law.

]
  ],
  caption: [SADAR boundary-relative balance. Component fields carry local SADAR attention vectors on their own declared boundaries. An enclosing boundary binds them as a super-field with its own SADAR attention vector. Phase bias shifts the boundary/window-specific SADAR balance; unresolved excess follows a sheddic path.],
) <fig:sadar-boundary-relative-balance>



=== Sheddic route reference <subsec:sadar-sheddic-route-reference>

Computed excess follows #eqnref("eq:shedding-excess") and the declared route
#eqnref("eq:sheddic-path").


=== Component projection <subsec:component-projection>

Component projections select declared components of the already-fixed SADAR attention vector.


#aod-provenance[#eqnref("eq:adar-channel"),
#eqnref("eq:sadar-field"),
#eqnref("eq:sadar-attention-vector"),
#eqnref("eq:rcd-coupling"),
#eqnref("eq:causal-update"),
#eqnref("eq:incident-return-shift"),
#eqnref("eq:matched-return-cancellation"),
#appref("app:curling-curls").]



== Cycle-shedding and temporal SADAR burden <sec:cycle-shedding-temporal-sadar-burden>



=== Temporal cycle group <subsec:temporal-cycle-group>


#aod-definition(title: [Temporal cycle group])[
A temporal cycle group is the recurrent-wave specialization of the A$Omega$D wavelet #eqref("eq:aod-wavelet-continuation") (#secref("subsec:aod-wavelet-continuation")): a carried segment of duon current participating in the admitted wave continuity of #eqref("eq:wave-identity") and #appref("app:wave").
]



=== Lead-lag burden <subsec:lead-lag-burden>


#aod-definition(title: [Lead–lag disturbance span])[
The lead–lag disturbance span is the carried asymmetric return extent of a temporal cycle group on the declared cut lineage.
]



=== Temporal SADAR burden <subsec:temporal-sadar-burden>

For a temporal cycle group $W$ on a declared boundary/window $B = ( partial F, omega )$, its temporal SADAR burden is

$ P^(SADARop)_W ( partial F, omega ) = sum_(e in W) C_(3,e) rho^D_(omega ,e) ( partial F, omega ) bar.v Delta chi_e^(upright("lag")) (B) bar.v . $ <eq:temporal-sadar-burden>

This burden is taken up by SADAR balance in #secref("sec:field:sadar").


=== Shedding <subsec:shedding>


#aod-definition(title: [Shedding])[
Shed is the verb. Shedding is the direction-neutral noun for the parent surplus process. Sheddic is the adjective for path, route, value, and audit descriptors. Endoshedding and exoshedding carry directionality.

Shedding is the break of excess carried disturbance from local closure compatibility. If $C^(upright("close"))_W ( partial F, omega )$ is local closure compatibility, then

$ Delta_(upright("close")) ( partial F, omega ) = P_W^(SADARop) ( partial F, omega ) - C^(upright("close"))_W ( partial F, omega ). $ <eq:closure-residual>


$ X_(upright("shedding")) ( partial F, omega ) = max ( 0, Delta_(upright("close")) ( partial F, omega ) ) $ <eq:shedding-excess>

records sheddic excess. A negative closure residual is a deficit/open check, not sheddic surplus.
]



=== Sheddic path <subsec:sheddic-path>

Seat-compatible retention places the computed #eqref("eq:shedding-excess") on
a declared path:

$ upright("SheddicPath")(X_(upright("shedding")) ) in brace.l E_2 ,sans("C")_6 ,sans("C")_8 ,sans("C")_(10) , dots.h ,sans("C")_(2 n) brace.r . $ <eq:sheddic-path>

After a route partition is declared, the parent surplus may be placed as

$ X_(upright("shedding")) = X_(upright("endo")) + X_(upright("exo")) + X_(upright("redir")) + X_(upright("open")) . $ <eq:shedding-route-partition>

The terms are endoshedding, exoshedding, redirected support and unretained open
loss, assigned only after declaring $op("SheddicPath")$.
With reclosure fraction $lambda_(upright("reclose")) in [0,1]$, write

#math.equation(block: true, numbering: none, $ X_W^(upright("reclose")) = lambda_(upright("reclose")) X_(upright("shedding")) , wide X_W^(upright("out")) = (1 - lambda_(upright("reclose")) )X_(upright("shedding")) . $)

Here $X_W^(upright("out"))$ is the non-reclosed outward remainder. After route placement,

#math.equation(block: true, numbering: none, $ X_W^(upright("out")) = X_(upright("exo")) + X_(upright("redir")) + X_(upright("open")) . $)

A sheddic path may reclose, continue outward, or carry decay status according to seat-compatible retention and support-enclosure compatibility.


#aod-paragraph[Shed continuation witness and recipient stages.]
When $X_(upright("shedding")) ( partial F, omega ) > 0$ emits a shed wavelet continuation
#eqref("eq:aod-wavelet-continuation"), the shed continuation binds its parent identity,
emission boundary, cut, route tag, routed surplus and post-shed parent state:

$ w_(upright("shed")) = (W_(upright("parent")) , partial_T R_(upright("emit")) ,k_(upright("emit")) , upright("route") in brace.l upright("endo"),upright("exo"),upright("redir"),upright("open") brace.r , X_(upright("route")) ,S^W_(upright("post")) ). $ <eq:shed-continuation-witness>

At any downstream recipient scope $B_(upright("rec")) = ( partial_T R_(upright("rec")) , omega_(upright("rec")) )$ of recipient lineage $i_(upright("rec"))$, delivery, acceptance, seating, initial origin closure, and later compatible reclosure are strictly distinct, witness-ordered passive observations at the cut:

$ & upright("emitted") arrow.r.long upright("delivered") arrow.r.long cases(upright("accepted") arrow.r.long brace.l upright("seated")\, thin upright("pending_unseated") brace.r\,, upright("unaccepted_pass")\,) \ & upright("seated")attach(stretch(arrow.r, size: #180%), t: op("Cert")(C_(i_(upright("rec")) ,j) )) cases(upright("closed_origin") ( Delta Phi = 1_C , Delta op("bip") = 0)\, & j = 0\,, upright("reclosed") ("distinct compatible "op("id")_(upright("return")) , k_j in omega_(upright("rec")) , Delta op("bip") = 1)\, & j gt.eq 1.) $ <eq:recipient-event-lattice>

No earlier stage implies a later stage, and recording $upright("pending_unseated")$ or $upright("seated")$ at a cut states the observed record without imposing a future execution ban. Delivery, acceptance and seating contribute $Delta op("bip") = 0$. A full closure certificate #eqref("eq:closure-certificate") establishes completion ($Delta Phi = 1_C$): when it is the recipient lineage's initial closure $C_(i_(upright("rec")) ,0)$ ($N^C_(i_(upright("rec"))) = 1$), #eqref("eq:cumulative-closure-counts") gives $upright("bip")^(lt.eq)_(i_(upright("rec"))) = max (1 - 1,0) = 0$ beats; a reclosure beat ($Delta op("bip") = + 1$) is awarded only relative to an existing compatible recipient origin $C_(i_(upright("rec")) ,0)$ via a later completion $C_(i_(upright("rec")) ,j)$ ($j gt.eq 1$, $k_j in omega_(upright("rec"))$) of compatible lineage and scope whose immutable return identity $op("id")_(upright("return")) (C_(i_(upright("rec")) ,j) )$ #eqref("eq:return-identity") has not already been counted on $omega_(upright("rec"))$ (replay adds $0$ beats, and a mismatched lineage or scope confers no recipient closure claim).



=== Yro odd-window route-status suffix <subsec:yro-odd-window-route-status>

For an odd declared window length $L = 2 k + 1$, write

#math.equation(block: true, numbering: none, $ op("Yro")_L (K;B). $)

This is an odd-window unstable route-status suffix for a compact curling-curl specification $K$ on the declared boundary/window $B$. It records route status between adjacent even support enclosures $sans("C")_(2 k)$ and $sans("C")_(2 k + 2)$. The support-enclosure ladder remains the even sequence

#math.equation(block: true, numbering: none, $ sans("C")_6 , sans("C")_8 , sans("C")_(10) , dots.h ,sans("C")_(2 n) . $)

The yro status may be driven by surplus, deficit, pending overhang, hinge slide, seat-compatible retention cutoff, terminal split, or another declared route instability. The construction trace and sheddic-route audit fix which condition applies on the declared scope.


#aod-paragraph[Naming audit.]
A yro suffix is audited as route status on a declared boundary/window and is recorded separately from support-enclosure names.


=== Entropic duon current <sec:entropic-duon-current>


#aod-definition(title: [Entropic duon current])[
Entropic duon current is retained duon current carrying unresolved return burden. It carries retained ternary capacity through shell return, shedding, reclosure, and SADAR dynamics.
]

For a declared field and boundary/window $B = ( partial F, omega )$, one local scalar form is

$ J^D_(upright("ent")) ( partial F, omega ) = sum_(e in F( partial F, omega )) C_(3,e) rho^D_(omega ,e) ( partial F, omega ) bar.v Delta chi_e^(upright("lag")) (B) bar.v . $ <eq:entropic-duon-current>

The sum specializes #eqref("eq:temporal-sadar-burden") to the field's retained
current family. Coherent continuity can accumulate the unresolved lead–lag burden.


#figure(
  kind: image, [
#image("/figures_jpg/cycle_disturbance_shedding.png", width: 96%)
  ],
  caption: [Temporal cycle lead–lag disturbance and shedding. On the declared boundary/window $B = ( partial F, omega )$, the schematic $Delta_e^(chi upright("lag"))$ denotes the signed lag accessor $Delta chi_e^(upright("lag")) (B)$; the absolute-value bars take its magnitude.],
) <fig:v39-cycle-disturbance-shedding>



#aod-provenance[#eqnref("eq:closure-certificate"),
#eqnref("eq:return-identity"),
#eqnref("eq:beat-reclosure"),
#eqnref("eq:cumulative-closure-counts"),
#eqnref("eq:closure-phase-window"),
#eqnref("eq:duon-current"),
#eqnref("eq:aod-wavelet-continuation"),
#eqnref("eq:returned-duration"),
#eqnref("eq:temporal-sadar-burden"),
#eqnref("eq:shedding-excess"),
#eqnref("eq:sheddic-path"),
#eqnref("eq:shed-continuation-witness"),
#eqnref("eq:recipient-event-lattice"),
#eqnref("eq:sadar-attention-vector"),
#eqnref("eq:entropic-duon-current"),
#eqnref("eq:sadar-field"),
#appref("app:wave"),
#appref("app:curling-curls").]



== Seat compatibility and shell/enclosure routing <sec:seat-shell-enclosure-routing>



=== Even sequence <subsec:support-enclosure-even-sequence>

The even sequence separates the current-side double form, the inner enclosure, and the outer enclosures.


=== E2 duon <subsec:e2-duon>

In seat-compatibility routing, $E_2$ and $E_2^0$ invoke the canonical Duon
support owned in #secref("subsec:duon") (#eqref("eq:duon-current")).


=== E2$""^(plus.minus)$ duad <subsec:e2-duad>

In seat-compatibility routing, $E_2^(plus.minus)$ invokes the canonical same-current
Duad seating state owned in #secref("subsec:duad") (#eqref("eq:duad-same-current")).


=== E4 tetron <subsec:e4-tetron>


#math.equation(block: true, numbering: none, $ E_4 = upright("tetron"). $)

Tetron is the default inner enclosure with four seats.


=== Outer enclosures <subsec:outer-enclosures>

A support enclosure is an outer even enclosure available to shell/enclosure routing:

#math.equation(block: true, numbering: none, $ sans("C")_(2 m) = "support enclosure of order "2 m, wide m gt.eq 3. $)



=== Hexon <subsec:hexon>


#math.equation(block: true, numbering: none, $ sans("C")_6 = upright("hexon"). $)

Hexon is the first outer enclosure because the hinge triad supplies left/right threefold closure: $sans("H")_3 + sans("H")_3 = 6$.


=== Octon <subsec:octon>


#math.equation(block: true, numbering: none, $ sans("C")_8 = upright("octon"). $)



=== Decon <subsec:decon>


#math.equation(block: true, numbering: none, $ sans("C")_(10) = upright("decon"). $)



=== Higher even enclosures <subsec:higher-even-enclosures>

Higher even enclosures continue the outer sheddic path sequence:

#math.equation(block: true, numbering: none, $ sans("C")_(2 n) , wide n > 5. $)

Outer enclosures are retained forms of sheddic paths. Hexon is the first outer enclosure; octon and decon are higher sheddic path forms; $sans("C")_(2 n)$ records the higher even sequence.


=== Filled shared enclosure <subsec:filled-shared-enclosures>

A filled shared enclosure has

#math.equation(block: true, numbering: none, $ m:m:0::2 m, wide m gt.eq 3. $)


=== Closure excess <subsec:support-enclosure-sadar-closure>

For a support-enclosure declaration $cal(C) = a:b:c::L$ on $B = ( partial F, omega )$, shell/enclosure routing carries the already-declared sheddic excess on the available route $cal(C)$. The routed closure excess is

$ X_(cal(C)) (B) = op("route")_(cal(C)) ( X_(upright("shedding")) (B) ) . $ <eq:support-enclosure-excess>

The value and placement of $X_(cal(C))$ determine local rebalancing, exoshedding, endoshedding, or redirected support routing.


=== Seat-compatible retention duration <subsec:support-enclosure-retention-condition>

For a support-enclosure declaration $cal(C) = a:b:c::L$, write

$ upright("TTL")_(cal(C)) ( partial F, omega ) = "retained tick duration available for seat-compatible SADAR rebalancing". $ <eq:support-enclosure-retention>

This is distinct from $rho^D_(omega ,i j) (B)$, the window-clipped duration participation for a channel.
Retention on the declared window is $upright("TTL")_(cal(C)) ( partial F, omega ) gt.eq bar.v omega bar.v$. If $upright("TTL")_(cal(C)) ( partial F, omega ) < bar.v omega bar.v$, the sheddic path continues through re-entry, reclosure, or decay status before the window closes.


#figure(
  kind: image, [
#image("/figures_jpg/support_enclosure_retention.png", width: 96%)
  ],
  caption: [Seat compatibility and support-retention duration for sheddic paths.],
) <fig:support-enclosure-retention>



=== Coord-0 grouping <subsec:coord-zero-support-enclosure-grouping>

At coordinate $0$, write coord-0 shell-stack declarations as

#math.equation(block: true, numbering: none, $ 0 mid(|) - ::Z:A:0:L chevron.l a:b:c::L chevron.r . $)

For filled support-enclosure grouping,

#math.equation(block: true, numbering: none, $ 0 mid(|) - ::Z:A:0:2 m chevron.l m:m:0::2 m chevron.r . $)

Define the cumulative group boundary

#math.equation(block: true, numbering: none, $ Gamma_m = sum_(k = 3)^m 2 k = m(m + 1) - 6, wide Gamma_2 = 0. $)

Then $Gamma_(m - 1) < Z lt.eq Gamma_m$ selects the coord-0 support-enclosure group.


#aod-provenance[#eqnref("eq:sadar-field"),
#eqnref("eq:support-enclosure-excess"),
#eqnref("eq:support-enclosure-retention"),
#appref("app:curling-curls").]




== Shell paths <sec:shell-paths>



=== Shell-path closure references <subsec:shell-path-closure-references>

Shell paths retain channel pressure #eqref("eq:b-scoped-channel-pressure") and
flux #eqref("eq:b-scoped-flux"). Their closure controls are in
#appref("app:combinatorics-rd-tests") and
#appref("app:path-complexity-quarantine").



== Fusion closure and chain reclosure <sec:fusion-closure-chain-reclosure>



=== Fusion closure <subsec:fusion-closure>

Fusion is branch/hinge/branch closure of admitted curling-curl support forms. For admitted forms $F$ and $G$, define

$ op("Fuse")_B (F,G) := op("Close")_B ( hat(F) med mu med hat(G) ) , $ <eq:fusion-closure>

where $hat(F) = op("Compress")(F)$ and $hat(G) = op("Compress")(G)$. Closed forms fuse; exposed fragments do not.
The inherited fusion operator consumes closed or reclosed admitted inputs.
Each input compression must have its complete inner construction and certificate
bound before consumption. The outer certificate binds both compressed inputs;
an incomplete compression or an open proposal is outside this operator's domain.

The branch/hinge/branch fusion duration is

$ R D_(upright("fuse")) (F,G;B) = Pi^(-)_(hat(F)) (B) + H_(mu ,hat(F),hat(G)) (B) + Pi^(+)_(hat(G)) (B). $ <eq:fusion-branch-hinge-duration>


For a closure rung,

$ C^(upright("ret"))_(n + 1) = op("Close")_(B_(n + 1)) ( hat(F)_n med mu med hat(G)_n ) . $ <eq:fusion-ladder-rung>

The rung residual is

$ S_(n + 1) = P^D_(n + 1) - C_(upright("close"),n + 1) . $ <eq:fusion-rung-residual>

If $S_(n + 1) > 0$, the rung is surplus-producing; if $S_(n + 1) = 0$, its scalar residual is neutral; if $S_(n + 1) < 0$, it is deficit/open. Every claimed closure also requires its independent trace certificate. The sheddic surplus is

$ X_(upright("shedding"),n + 1) = max (0,S_(n + 1) ). $ <eq:fusion-rung-shedding-surplus>



=== Exoshedding lift <subsec:exoshedding-lift>

Exoshedding routes surplus support outside the current closure. At scope $B_r$, nonzero $X_(upright("exo"),r)$ supplies proposed lifted support

$ K^(r + 1)_(upright("prop")) = op("Lift")_(B_r arrow.r B_(r + 1)) ( X_(upright("exo"),r) ) . $ <eq:exoshedding-lift>

The construction trace admits it by

$ K^(r + 1)_(upright("prop")) attach(stretch(arrow.r, size: #180%), t: thin H T(K;B_(r + 1) ) thin) K^(r + 1)_(upright("adm")) (B_(r + 1) ). $ <eq:lifted-support-admission>

Higher-scope fusion closes the admitted lifted support:

$ C^(upright("ret"))_(r + 1) = op("Close")_(B_(r + 1)) ( hat(F)_r med mu med K^(r + 1)_(upright("adm")) (B_(r + 1) ) ) . $ <eq:higher-scope-fusion>

Thus exoshedding supplies lifted support; fusion closes it.


=== Link-closure ladder <subsec:link-closure-ladder>

Chain reclosure is iterated higher-scope fusion over admitted supports routed by exoshedding. A local adjacent link closure is

$ L_(i,i + 1) = op("Close")_(B_(i,i + 1)) ( hat(F)_i med mu med hat(F)_(i + 1) ) . $ <eq:link-closure-ladder>

Its residual is

$ Delta_(upright("link")) = P^D_(upright("link")) - C_(upright("close,link")) , wide X_(upright("shedding"),upright("link")) = max (0, Delta_(upright("link")) ). $ <eq:link-closure-residual>



#aod-provenance[#secref("subsec:curling-curl-support-forms"), #secref("subsec:sheddic-path"), #eqnref("eq:branch-hinge-rd").]




== Fractal Field Ring Gate <subsec:fractal-field-ring-gate>


#aod-noteblock("Scope")[A fractal field ring gate is a declared recurrence motif on $B = ( partial_T F, omega )$.]


Declare

$ frak(a) subset cal(A)^(upright("ret"))_8 , wide B = ( partial_T F, omega ). $ <eq:frg-scope>

The AF recurrence is typed here: the distinctions are declared in #eqnref("eq:frg-distinctions")\; the relations are declared in #eqnref("eq:frg-ring-adjacency")–#eqnref("eq:frg-return-relation")\; the retained relation family is the FRG; $SADARop_B$ forms the A$Omega$ value.


=== Distinctions <subsec:frg-distinctions>

Declare

$ D_(upright("FRG")) = (frak(a), B,V_N ,I,G). $ <eq:frg-distinctions>

with

#math.equation(block: true, numbering: none, $ V_N = brace.l 0,1, dots.h ,N - 1 brace.r , wide R_(upright("ring")) subset F, $)


#math.equation(block: true, numbering: none, $ partial_T R_(upright("ring")) = "the tesseract-admissible boundary induced on "R_(upright("ring")) , $)


#math.equation(block: true, numbering: none, $ I subset.eq V_N , wide G = brace.l g_i :i in I brace.r , wide g_i in partial_T R_(upright("ring")) , $)


#math.equation(block: true, numbering: none, $ k in K_(upright("bin")) . $)



=== Relations <subsec:frg-relations>

The ring adjacency relation is

$ E_N = brace.l (i,i + 1 mod N),(i,i - 1 mod N):i in V_N brace.r . $ <eq:frg-ring-adjacency>

The returned-current relation is

$ E_(upright("return")) subset.eq I times I. $ <eq:frg-return-relation>

Under the adjacent-only restriction,

$ (i,j) in E_(upright("return")) arrow.r.double (i,j) in E_N . $ <eq:frg-adjacent-only-condition>

Gate-to-bin and cross-return path relations are written directly as

#math.equation(block: true, numbering: none, $ gamma :g_i arrow.r.squiggly k, wide gamma :g_i arrow.l.r g_j arrow.r.squiggly k. $)

The retained path-cycle carried by $gamma$ is $C_(gamma)$.


#aod-paragraph[Retained relation, admission and model.]

$ D_(upright("FRG")) arrow.r.long R^(upright("ret"))_(upright("FRG")) arrow.r.long K_(upright("FRG,adm")) (B,i;upright("cert")) arrow.r.long (K_(upright("bin")) , kappa , lambda_(cal(Y)) ). $ <eq:frg-admission-order>

The retained ring adjacency and return paths carry distinction identities.
After #eqref("eq:motif-admission"), choose
$kappa :K_(upright("bin")) arrow.r bb(Q)$, $kappa_k = kappa (k)$, and the
value map $lambda_(cal(Y))$. The sums consume paths committed through
the current cut; response follows at the next transition.


=== Gate contribution <subsec:frg-gate-contribution>

For a declared gate $g_i$, define the bin contribution

#tagged-eq("RG1", $ S_k^(lr((i))) = sum_(t in omega) sum_(gamma :g_i arrow.r.squiggly k) kappa_k thin SADARop_(B bar.v t) (C_(gamma) ). $, <eq:frg-gate-contribution>)



=== Independent gate-sum value <subsec:frg-independent-gate-sum>

The independent gate-sum value is

#tagged-eq("RG2", $ T_k^0 = sum_(i in I) S_k^(lr((i))) . $, <eq:frg-independent-gate-sum>)

For two gates,

#tagged-eq("RG3", $ T_k^0 = S_k^(lr((a))) + S_k^(lr((b))) . $, <eq:frg-independent-two-gate>)



=== Cross-return contribution <subsec:frg-cross-return-contribution>

For a returned-current pair $(i,j) in E_(upright("return"))$, define

#tagged-eq("RG4", $ C_(i j,k)^(times) (B) = sum_(t in omega) sum_(gamma :g_i arrow.l.r g_j arrow.r.squiggly k) kappa_k thin SADARop_(B bar.v t) (C_(gamma) ). $, <eq:frg-cross-return-contribution>)

For the two-gate specialization with
$E_(upright("return")) = brace.l (a,b) brace.r$,

#tagged-eq("RG5", $ C_(a b,k)^(times) (B) = sum_(t in omega) sum_(gamma :g_a arrow.l.r g_b arrow.r.squiggly k) kappa_k thin SADARop_(B bar.v t) (C_(gamma) ). $, <eq:frg-cross-return-two-gate>)



=== Recurrent ring value <subsec:frg-recurrent-ring-value>

The recurrent ring value is

#tagged-eq("RG6", $ T_k^(times) = T_k^0 + sum_((i,j) in E_(upright("return"))) C_(i j,k)^(times) (B). $, <eq:frg-recurrent-ring-value>)

Under the specialization of #eqnref("eq:frg-cross-return-two-gate"),

#tagged-eq("RG7", $ T_k^(times) = T_k^0 + C_(a b,k)^(times) (B). $, <eq:frg-recurrent-two-gate>)



=== Field-ring identity <subsec:frg-identity>

The field-ring identity is

#tagged-eq("RG8", $ T_k^(times) - T_k^0 = sum_((i,j) in E_(upright("return"))) C_(i j,k)^(times) (B). $, <eq:frg-identity>)

Under the specialization of #eqnref("eq:frg-cross-return-two-gate"),

#tagged-eq("RG9", $ T_k^(times) - T_k^0 = C_(a b,k)^(times) (B). $, <eq:frg-identity-two-gate>)

(The exact-fixture residual tag $upright("RG10")$ belongs to the downstream Manual fixture layer.)



=== FRG value package <subsec:frg-value-package>

The compact FRG value package is

#tagged-eq("RG11", $ cal(V)_(upright("FRG")) = (frak(a), B, R_(upright("ring")) , partial_T R_(upright("ring")) , V_N ,E_N ,I,G,K_(upright("bin")) , kappa ,E_(upright("return")) , lambda_(cal(Y)) ). $, <eq:frg-value-package>)

The declared value map is

#tagged-eq("RG12", $ lambda_(cal(Y)) : (T_k^(times) )_(k in K_(upright("bin"))) arrow.r.bar cal(Y). $, <eq:frg-value-map>)



#aod-remark[FRG supplies gated recurrent cross-return; fusion closes admitted support.]



== Field dynamics <sec:field-dynamics>



=== Field-fluid regime <subsec:field-fluid-regime>

Field dynamics is the A$Omega$D calculation of retained field, current-cycle, background-continuation, and shell-support participants on declared $B = ( partial_T F, omega )$. A field-fluid regime is the local declaration in which those participants couple through finite SADAR capacity. For a moving or nested cell boundary, write

#math.equation(block: true, numbering: none, $ B_c bar.v t = ( partial_T R_c (t), omega_c bar.v t). $)

The retained cycle family is

#math.equation(block: true, numbering: none, $ cal(C)_c (t) = cal(C)_(upright("field"),c) union cal(C)_(upright("current"),c) union cal(C)_(upright("bg"),c) union cal(C)_(upright("shell"),c) . $)

Here

#math.equation(block: true, numbering: none, $ C_J = "retained current-cycle participant", wide J^D = "accumulated current value". $)



=== Support-resolution model <subsec:cycle-beat-resolution-gate>

Let

#math.equation(block: true, numbering: none, $ cal(C)_(a,r, Sigma) = op("cycle") chevron.l a,r chevron.r ( Sigma_(upright("support")) ), $)

where $Sigma_(upright("support"))$ is the declared support-expression family,
with structural support multiplicity $N_(upright("support")) (a,r, Sigma ;B)$
defined by #eqref("eq:beat-count").
The monitored reflection-duration accessor is selected by the declared rule

#math.equation(block: true, numbering: none, $ R D_(upright("mon")) (a,r, Sigma ;B) = max_(C_u in cal(C)_(a,r, Sigma)) R D_(AO) (C_u ;B). $)

Resolution is chosen by a declared coarseness order $prec.eq_(upright("coarse"))$. Tie-breakers are declared before application. The selected $q$ is the coarsest resolution among already admitted candidates under $prec.eq_(upright("coarse"))$ after declared tie-breakers. No measured residual or score enters this gate.


=== Medium declaration and field count <subsec:medium-declaration-field-count>

Declare $N_(upright("candidate"),c) ,N_(upright("support"),c) in bb(Z)_(gt.eq 0)$, $cal(K)^(upright("raw"))_c in bb(Q)_(gt.eq 0)$, and $macron(k)_F ,macron(rho)^D_F in bb(Q)_(> 0)$ before application. The raw maximum supported field count is

#math.equation(block: true, numbering: none, $ N^(max ,0)_(F,c) = min ( N_(upright("candidate"),c) , N_(upright("support"),c) , floor.l frac(cal(K)^(upright("raw"))_c, macron(k)_F) floor.r , floor.l frac(bar.v omega_c bar.v, macron(rho)^D_F) floor.r ) . $)

Subject to actual recurrent member admission, the retained field family is then bounded as

#math.equation(block: true, numbering: none, $ F_(B_c) = brace.l F_1 , dots.h ,F_(n_F (c)) brace.r , wide n_F (c) lt.eq N^(max ,0)_(F,c) . $)

A gas/fluid classifier is a declaration on $B_c$, not an external material label. Chiral flip, background-continuation jitter, slosh, semi-coupling, and lead-lag are boundary-current features of the declared regime.



#aod-remark[A field-fluid regime may distinguish locally seated, unresolved-jitter, pending, and sheddic chiral events by declared boundary status.]



=== Nested boundary and inter-layer SADAR coupling <subsec:interlayer-sadar-coupling>

For nested boundaries

#math.equation(block: true, numbering: none, $ R_0 subset R_1 subset dots.c subset R_m , wide B_(ell) = ( partial_T R_(ell) , omega_(ell) ), $)

the inter-layer coupling value is

#math.equation(block: true, numbering: none, $ G^(frak(S))_(ell arrow.r m) (B) = sum_((u,v) in E^(frak(S))_(ell ,m) (B)) SADARop_B (C_u ,C_v ). $)

Range-prioritized coupling orders admissible $E^(frak(S))_(ell ,m) (B)$ by the declared boundary range before summation. When a magnitude is needed, use the declared magnitude functional

#math.equation(block: true, numbering: none, $ J^(D,upright("try"))_(r,c) = sum_((u,v) in E_r (B_c )) bar.v.double SADARop_(B_c) (C_u ,C_v ) bar.v.double_(upright("decl")) . $)



=== Capacity residual and exoshedding lift <subsec:capacity-residual-exoshedding-lift>

Declare the capacity residual $Delta^(upright("cap"))_(ell) = P^D_(ell) - C^(upright("cap"))_(ell)$.
The separate closure residual, surplus and route partition use
#eqref("eq:closure-residual"), #eqref("eq:shedding-excess") and
#eqref("eq:shedding-route-partition") on $B_(ell)$.
For $X_(upright("exo"), ell) > 0$, apply #eqref("eq:exoshedding-lift"),
then #eqref("eq:lifted-support-admission") before
#eqref("eq:higher-scope-fusion"). Capacity and closure compatibility retain
their distinct operands.


=== FRG-mediated cross-return in nested boundaries <subsec:frg-nested-boundary>

A ring-gated layer instantiates #eqref("eq:frg-distinctions") and
#eqref("eq:frg-admission-order") with its own
$N_(ell) ,I_(ell) ,G_(ell) ,K_(upright("bin"), ell) , kappa_(ell) ,E_(upright("return"), ell)$.
Its cross terms and recurrent value are
#eqref("eq:frg-cross-return-contribution") and #eqref("eq:frg-recurrent-ring-value")
on $B_(ell)$. FRG supplies gated cross-return; the preceding lift and fusion
construct the higher closure, and their iteration gives chain reclosure.


#figure(
  kind: image, [
#image("/figures_jpg/field_dynamics_layered_main.png", width: 82%)
  ],
  caption: [Layered field dynamics. Boundaries separate layers; same-sense circulation remains on each layer; coupling arrows cross declared inter-layer channels; decoupling/lift arrows indicate exoshedding after closure surplus.],
) <fig:field-dynamics-layered>



=== Finite SADAR moving-boundary dictionary <subsec:finite-sadar-moving-boundary-dictionary>

On $B_c bar.v t$, substitute $phi.alt_e = SADARop (C_e )$ into
#eqref("eq:slice-flux")\; sum with #eqref("eq:window-current") and retain the
crossing/sweep/shedding split of #eqref("eq:moving-boundary").
This finite dictionary expresses bobbing as signed sweep/shedding modulation
on the declared moving or nested cell boundary.


#figure(
  kind: image, [
#aod-panel(width: 94%)[



#strong[Fractal-calculus spine] \


#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, 1fr),
    align: (center, center, left),
    [Declared distinction], [$arrow.b$], [$x succ x = x" with retained hinge/trace"$],
    [Declared scope], [$arrow.b$], [$B = ( partial_T F, omega )$],
    [Certified closure/recurrence], [$arrow.b$], [$C_f [ Sigma ]_(AO)$],
    [$sans("AO")_(mu) (C)$], [$arrow.b$], [$sans("AO")_(mu) (C) = chevron.l Pi_(alpha) ,H_(mu) , Pi_(Omega) chevron.r$],
    [SADAR value], [$arrow.b$], [$SADARop_B (C) = p^D A$],
    [Boundary accumulation], [$arrow.b$], [$Phi^D_(partial_T R) = sum_(e in partial_T R) SADARop_B (C_e )$],
  )
}


]
  ],
  caption: [Fractal-cycle calculus spine.],
) <fig:fractal-calculus-spine>



== SADAR value trace of admitted recurrence <subsec:cycle-wave-identity>

For an already admitted wave $W$ of #eqref("eq:wave-identity"), let $C_t$
denote its bound retained cycle on each committed cut. This closure/current
contribution is the operand of #eqref("eq:sadar-operator-cycle"). Its value
projection is


$ v_B (W) = brace.l (t, SADARop_(B bar.v t) (C_t )):t in omega brace.r . $ <eq:wave-sadar-presentation>

The wave's admission and lineage are those of #eqref("eq:wave-identity")\; this
projection records their SADAR values.

The hinge $mu$ implicitly supports chirality: it carries the handed return of the branch/hinge/branch package. The chiral cycle presentation is

$ A scripts(arrow.l.r)_(mu) Omega arrow.r Omega scripts(arrow.l.r)_(mu) A arrow.r A scripts(arrow.l.r)_(mu) Omega . $ <eq:ao-chiral-cycle-presentation>

This presentation is part of the admitted recurring lineage: $A scripts(arrow.l.r)_(mu) Omega$ opens the returned package, $Omega scripts(arrow.l.r)_(mu) A$ carries the handed return, and $A scripts(arrow.l.r)_(mu) Omega$ records reclosure on the declared boundary/window.


#figure(
  kind: image, [
#aod-panel(width: 88%)[


#strong[SADAR value trace of admitted recurrence] \


#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (auto,),
    align: (center,),
    [$C_t$ = retained branch/hinge/branch package on the committed cut],
    [$A scripts(arrow.l.r)_(mu) Omega arrow.r Omega scripts(arrow.l.r)_(mu) A arrow.r A scripts(arrow.l.r)_(mu) Omega$ = chiral hinge return presentation],
    [$arrow.b$ temporal SADAR presentation on $omega$],
    [$v_B (W) = brace.l (t, SADARop_(B bar.v t) (C_t )):t in omega brace.r$],
  )
}


]
  ],
  caption: [An admitted recurring lineage has a chiral hinge-return presentation and a downstream SADAR value trace.],
) <fig:cycle-wave-identity>



== Fractal-tesseract cycle range <subsec:fractal-tesseract-cycle-range>

For finite $frak(a) subset cal(A)^(upright("ret"))_8$, section grade
$r$, and support expression $Sigma$ of #eqref("eq:support-expression"), define

$ cal(C)_(frak(a),r, Sigma) = op("cycle") chevron.l frak(a),r chevron.r ( Sigma ) = cal(P)^(lr((r)))_(frak(a)) ( Sigma ). $ <eq:fractal-tesseract-cycle-range>

The fractal coordinate range selects retained addresses. The tesseract section grade selects retained sections. The support expression assigns cycle types.

The separator $::$ joins support clauses. If the final clause is a bare even
shell number $L$, parse it as the shared enclosure qualifier $C_L$.

The structural support multiplicity is

$ N_(upright("support")) = bar.v op("Sec")^(lr((r)))_(T,upright("ret")) (frak(a);B) bar.v thin bar.v Sigma_(upright("support")) bar.v . $ <eq:beat-count>

Tesseract sections count support occurrences. Distinct certified reclosures count beats; SADAR couples their bound recurrent lineages.

The trace discipline is

$ Sigma slash K_(upright("prop")) & attach(stretch(arrow.r, size: #180%), t: "construction trace") H T(K;B) attach(stretch(arrow.r, size: #180%), t: "admission on "B) K_(upright("adm")) (B) \ & attach(stretch(arrow.r, size: #180%), t: "return-current trace") R D_h (B) attach(stretch(arrow.r, size: #180%), t: bowtie_B R^(upright("asym"))_h) R C D_h (B) attach(stretch(arrow.r, size: #180%), t: op("dur")) rho_h^D (B) \ & attach(stretch(arrow.r, size: #180%), t: min ( dot.op , bar.v omega_h bar.v )) rho^D_(omega ,h) (B) attach(stretch(arrow.r, size: #180%), t: C_(3,h)) p_h^D attach(stretch(arrow.r, size: #180%), t: A_h) SADARop_B (C_h ) attach(stretch(arrow.r, size: #180%), t: "closure test") Delta_(upright("close")) \ & attach(stretch(arrow.r, size: #180%), t: max (0, dot.op )) X_(upright("shedding")) attach(stretch(arrow.r, size: #180%), t: "declared route") op("SheddicPath"). $ <eq:support-trace-spine>


== Fractal-cycle finite accumulation <subsec:fractal-cycle-finite-accumulation>

For a retained cycle family $cal(C) = cal(C)_(frak(a),r, Sigma)$,
let $V_(upright("beat"))$ be the finite index set of its supplied certificate-bound cycle
contributions $C_u$. The declared coupling family $E_(SADARop) (B)$
consists of supplied pairs of these contributions in the recurrent-lineage
domain of #eqref("eq:sadar-operator-beat-coupling"). Define the finite SADAR
accumulation

$ cal(I)^(SADARop)_B (cal(C)) = sum_(u in V_(upright("beat"))) SADARop_B (C_u ) + sum_((u,v) in E_(SADARop) (B)) SADARop_B (C_u ,C_v ), $ <eq:fractal-cycle-finite-accumulation>

This is finite SADAR accumulation of the supplied retained-cycle and
coupled-lineage values; it is not continuous integration.

A fractal field ring gate is the ring specialization of finite SADAR accumulation when $E_(upright("return"))$ is declared by returned-current ring relations.


#aod-provenance[#eqnref("eq:afc-stokes-used"), #eqnref("eq:branch-hinge-rd"), #eqnref("eq:branch-hinge-rd-symmetric"), #eqnref("eq:tesseract-admissible-boundary"), #secref("subsec:q4-hamming-ternary-kernel").]



== Polyrhythm coupling <subsec:polyrhythm-coupling>

A polyrhythm coupling retains the cadences of a finite family
#eqref("eq:fractal-tesseract-cycle-range") on a common boundary/window.
In the explicitly periodic RD-as-period specialization, its display coordinate is

$ theta_u (t) = t mod R D_(AO) (C_u ), wide t in omega . $ <eq:polyrhythm-phase-coordinate>

The display period is a model choice. On the declared $E_(SADARop) (B)$,
#eqref("eq:sadar-operator-beat-coupling") specializes directly to

$ SADARop_B (C_u ,C_v ) = phi.alt^(upright("beat"))_(u v, AO) (B) = p^D_(u v, AO) (B)A_(u v, AO) (B). $ <eq:polyrhythm-sadar-coupling>

The polyrhythm SADAR value is the finite accumulation in #eqnref("eq:fractal-cycle-finite-accumulation"). Ring-adjacent SADAR coupling gives the fractal field ring gate of #secref("subsec:fractal-field-ring-gate").


#aod-remark[A scalar duration projection of a retained cycle omits branch/hinge/branch information needed by later coupling, seat compatibility, shedding, or SADAR calculations.]



#aod-provenance[#eqnref("eq:cut-running-form"),
#eqnref("eq:monon-cycle"),
#eqnref("eq:duon-current"),
#eqnref("eq:sadar-operator-beat-coupling"),
#appref("app:curling-curls").]


== Finite harmonic coordinates of admitted recurrence <sec:finite-harmonics>


#aod-paragraph[Setup.]
Let $G$ be a declared finite abelian index group of order $N > 0$, and
$hat(G)$ its exact character group. Each $chi :G arrow.r bb(C)$
satisfies $chi (g + h) = chi (g) chi (h)$ and $bar.v chi (g) bar.v = 1$.
Fix an admitted recurrent lineage and a value trace $v:G arrow.r bb(C)$
bound to its committed history. Translation means $T_a v(g) = v(g - a)$.
Native A$Omega$D wavelets #eqref("eq:aod-wavelet-continuation") precede any
analytical wavelet or finite harmonic readout; using $G$ to index a finite
record is a downstream representation choice whose analyzing family,
normalization, and subgroup or aliasing hypotheses supply no proof of periodic
dynamics or native wave admission.


=== Definition and normalization


#aod-paragraph[Setup.]

$ hat(v)( chi ) = frac(1, N) sum_(g in G) v(g)overline(chi (g)), wide chevron.l v,w chevron.r_G = frac(1, N) sum_(g in G) v(g)overline(w(g)). $ <eq:fourier-transform>

All corollaries in #secref("sec:finite-harmonics") share this group, committed trace and normalization;
local extra hypotheses are stated at their use. These value identities,
including inversion, neither admit motifs/waves nor supply a response law.



=== Orthogonality


#aod-paragraph[Setup.]
For a nontrivial character $eta$, choose $a$ with $eta (a) eq.not 1$.

#aod-paragraph[Derivation.]
Translation of the finite sum gives $S = sum_g eta (g) = eta (a)S$, hence
$S = 0$. For the trivial character the sum is $N$. Thus

$ frac(1, N) sum_(g in G) chi (g)overline(xi (g)) = bold(1)_(chi = xi) , wide frac(1, N) sum_(chi in hat(G)) chi (g)overline(chi (h)) = bold(1)_(g = h) . $ <eq:fourier-orthogonality>

For a cyclic factor of order $L$, its $L$ characters are the powers of
an exact primitive $L$-th root; products over a cyclic decomposition give
exactly $bar.v hat(G) bar.v = N$ characters. Orthogonality therefore gives a basis
of the $N$-dimensional function space and the second identity by the same
translation argument on the dual. This establishes completeness.


=== Inversion and uniqueness


#aod-paragraph[Derivation.]
Substitute #eqref("eq:fourier-transform") and apply the second identity:

$ sum_(chi) hat(v)( chi ) chi (g) = frac(1, N) sum_h v(h) sum_(chi) chi (g)overline(chi (h)) = v(g). $ <eq:fourier-inversion>

Taking the inner product with any character recovers its coefficient, so
no second coefficient family represents a different trace with the same
full transform. Distinct provenance can still accompany equal value traces.

#aod-paragraph[Falsification.] A missing coefficient, altered normalization or
unbound trace fails the corresponding representation or admission premise.


#aod-provenance[#eqref("eq:fourier-transform"),
#eqref("eq:fourier-orthogonality"),
#eqref("eq:wave-identity"),
#eqref("eq:motif-admission").]



=== Linearity


#aod-paragraph[Derivation.]
Distribute the defining finite sum:

$ hat(a v + b w) = a hat(v) + b hat(w). $ <eq:fourier-linearity>


#aod-paragraph[Falsification.] Applying this value identity to infer a linear
closure or update law changes its domain.


#aod-provenance[#eqref("eq:fourier-transform").]



=== Shift and modulation


#aod-paragraph[Setup.]
For $a in G$ and $eta in hat(G)$, set $M_(eta) v(g) = eta (g)v(g)$.

#aod-paragraph[Derivation.]
Substitution $h = g - a$ and character multiplication give

$ hat(T_a v)( chi ) = overline(chi (a))hat(v)( chi ), wide hat(M_(eta) v)( chi ) = hat(v)( chi overline(eta)). $ <eq:fourier-shift-modulation>


#aod-paragraph[Specialization.] A shift preserves coefficient magnitudes while
changing phase. Equal power therefore does not identify return phase or lineage.

#aod-paragraph[Falsification.] A shift with the opposite translation convention
requires the opposite character factor; replacing both by one untyped shift fails.


#aod-provenance[#eqref("eq:fourier-transform").]



=== Convolution and product


#aod-paragraph[Setup.]
Use unnormalized convolution $(v * w)(g) = sum_h v(h)w(g - h)$ and pointwise
product $(v w)(g) = v(g)w(g)$ on the same finite group.

#aod-paragraph[Derivation.] Substituting $u = g - h$ factors the convolution sum;
substituting both inversions and using orthogonality gives the product sum:

$ hat(v * w)( chi ) = N hat(v)( chi )hat(w)( chi ), wide hat(v w)( chi ) = sum_(eta in hat(G)) hat(v)( eta )hat(w)( chi overline(eta)). $ <eq:fourier-convolution-product>


#aod-paragraph[Falsification.] Omitting $N$ violates the shared normalization.


#aod-provenance[#eqref("eq:fourier-transform"),
#eqref("eq:fourier-inversion"),
#eqref("eq:fourier-orthogonality").]



=== Correlation and power


#aod-paragraph[Setup.]
Set $R_(v w) (a) = sum_g v(g + a)overline(w(g))$.

#aod-paragraph[Derivation.] Substitute the inversions;
the sum over $g$ removes unequal characters:

$ R_(v w) (a) = N sum_(chi) hat(v)( chi )overline(hat(w)( chi )) chi (a), quad hat(R)_(v w) ( chi ) = N hat(v)( chi )overline(hat(w)( chi )). $ <eq:fourier-correlation-power>

For $v = w$, the power coefficients are $N bar.v hat(v)( chi ) bar.v^2$.

#aod-paragraph[Falsification.] Equal power is insufficient for equal complex
coefficients, equal phase, or equal construction provenance.


#aod-provenance[#eqref("eq:fourier-inversion"),
#eqref("eq:fourier-orthogonality").]



=== Parseval


#aod-paragraph[Derivation.]
At zero shift the same calculation, or direct orthogonality, gives

$ frac(1, N) sum_g v(g)overline(w(g)) = sum_(chi) hat(v)( chi )overline(hat(w)( chi )), wide frac(1, N) sum_g bar.v v(g) bar.v^2 = sum_(chi) bar.v hat(v)( chi ) bar.v^2 . $ <eq:fourier-parseval>


#aod-paragraph[Falsification.] Changing normalization on one side breaks equality.


#aod-provenance[#eqref("eq:fourier-orthogonality").]



=== Real traces and standing coordinates


#aod-paragraph[Derivation.]
For real $v$, complex conjugation of the defining sum gives

$ hat(v)(overline(chi)) = overline(hat(v)( chi )). $ <eq:fourier-real-symmetry>

For a non-self-conjugate pair define real coordinates

$ c_(chi) = ( chi + overline(chi)) slash 2, quad s_(chi) = ( chi - overline(chi)) slash (2 upright("i")), wide a chi + overline(a) thin overline(chi) = 2 op("Re")(a)c_(chi) - 2 op("Im")(a)s_(chi) . $ <eq:fourier-running-standing>

Running character and standing pair coordinates represent the same admitted
trace. Self-conjugate characters are already real and occur once.

#aod-paragraph[Falsification.] This coordinate change cannot classify an open
word as a running wave.


#aod-provenance[#eqref("eq:fourier-transform"),
#eqref("eq:fourier-inversion"),
#eqref("eq:fourier-real-symmetry").]



=== Recurrence subgroup


#aod-paragraph[Setup.]
Let $H lt.eq G$, and assume the bound value trace is invariant under every
translation in $H$.

#aod-paragraph[Derivation.] Shift covariance gives
$(1 - overline(chi (h)))hat(v)( chi ) = 0$. Therefore

$ v(g + h) = v(g) (h in H) quad arrow.l.r.double.long quad op("supp")hat(v) subset.eq H^(perp) , quad H^(perp) = brace.l chi : chi (h) = 1 forall h in H brace.r . $ <eq:fourier-recurrence-support>

The converse follows by translating each term in the inversion.

#aod-paragraph[Specialization.] Exact periodic values on a declared cyclic
index may satisfy this hypothesis. Jittered cadence need not do so.

#aod-paragraph[Falsification.] A finite observation window alone supplies no
translation invariance or exact dynamical recurrence subgroup.


#aod-provenance[#eqref("eq:fourier-shift-modulation"),
#eqref("eq:fourier-inversion").]



=== Direct products


#aod-paragraph[Setup.]
For $G = G_1 times dots.c times G_s$, characters factor as
$chi (g) = product_j chi_j (g_j )$, and $N = product_j bar.v G_j bar.v$.

#aod-paragraph[Derivation.]
If, additionally, the trace is separable, finite sums factor:

$ v(g) = product_j v_j (g_j ) quad arrow.r.double.long quad hat(v)( chi_1 , dots.h , chi_s ) = product_j hat(v)_j ( chi_j ). $ <eq:fourier-product-factorization>


#aod-paragraph[Specialization.] Declared independent recurrence orders may use
a product group. A coupled trace generally has nonseparable coefficients.

#aod-paragraph[Falsification.] Product index alone does not imply separability.


#aod-provenance[#eqref("eq:fourier-transform"),
#eqref("eq:fourier-orthogonality").]


=== Finite cancellation residuals <subsec:afc-flux-stokes-audit>

For a declared region $R$ and scope $B$, define

$ S_(upright("int")) (R;B) = sum_(i in R) sum_(j in R) phi.alt_(i j) (B), $ <eq:stokes-audit-internal>


$ S_(upright("div")) (R;B) = sum_(i in R) op("div")(i;B), wide S_(partial) (R;B) = sum_(i in R \ j in.not R) phi.alt_(i j) (B). $ <eq:stokes-audit-sums>

A valid declaration satisfies internal cancellation,

$ S_(upright("int")) (R;B) = 0, $ <eq:stokes-audit-internal-zero>

and boundary balance,

$ cal(E)(R,B) = S_(upright("div")) (R;B) - S_(partial) (R;B) = 0. $ <eq:stokes-audit-residual>

If $S_(upright("int")) (R;B) eq.not 0$, the declared orientation, sign, or antisymmetry fails on that scope. If $cal(E)(R,B) eq.not 0$, the declaration has a missing returned-current channel, incomplete boundary/window, undeclared sheddic path, or wrong channel content.


#aod-paragraph[Wave slice and window projection.]
For an already admitted wave, the slice projection is #eqref("eq:slice-flux")
and its retained window sum is #eqref("eq:window-current"). These are downstream
value coordinates of #eqref("eq:wave-identity").

#aod-paragraph[Comparison scope.]#aod-anchor(<subsec:external-comparison-quarantine>)
Native counts and admitted harmonic coordinates retain their exact finite
domains.


== Audit hooks <sec:audit-hooks>

Audit hooks preserve structural checks.


=== Spine audit <subsec:spine-audit>

The audit passes when every retained occurrence at every finite depth has branch/hinge/branch incidence.


=== Boundary audit <subsec:boundary-audit>

Check the window sum #eqref("eq:window-current") on its declared slices
#eqref("eq:slice-flux").


=== SADAR audit <subsec:sadar-audit>

Check the #eqref("eq:adar-channel") operands and repeated balance of the declared
#eqref("eq:sadar-field") family on its retained topology.


=== Seat/enclosure routing audit <subsec:support-enclosure-audit>

The audit passes when field-count scaling and seat-compatible shell/enclosure routing remain distinct calculations on the same declared boundary/window.


=== Sheddic path audit <subsec:sheddic-path-audit>

On a declared field and window, if $X_(upright("shedding")) ( partial F, omega ) > 0$ and no sheddic path is declared through $E_2$, $sans("C")_6$, $sans("C")_8$, $sans("C")_(10)$, or a higher even $sans("C")_(2 n)$ form, the shedding statement fails on that scope. A sheddic path fails on the declared scope if its retained form violates the stated $T T L_(cal(C))$ condition.




=== Symbol audit <subsec:symbol-audit>

SYM-A1–A4 check, in order, support #eqref("eq:branch-hinge-rd"), constructor
#eqref("eq:rcd-coupling"), scalar interface #eqref("eq:rcd-duration-participation"),
and compatible clipping #eqref("eq:window-clipped-rho").


=== Cycle and polyrhythm audit <subsec:cycle-polyrhythm-audit>

The cycle audit is certified when a retained field cycle is declared before any scalar duration accessor:

#math.equation(block: true, numbering: none, $ cal(C)_f [p":"q] quad "before" quad R D ( cal(C)_f [p":"q] ) . $)

The polyrhythm audit binds each coupled cycle, its boundary/window,
its reflection-duration accessor, and the pressure and attention operands
of #eqref("eq:sadar-operator-beat-coupling") before forming the SADAR coupling term.



=== Fusion closure audit <subsec:fusion-closure-audit>

The fusion closure audit passes when admitted curling-curl support forms, hinge $mu$, closure scope $B$, branch/hinge/branch returned duration, and closure residual are declared before $X_(upright("shedding"))$ or any lifted support is formed. Chain reclosure is audited as iterated higher-scope fusion over admitted lifted supports. FRG-mediated reclosure is audited by the declared relation family and the computed identity $T^(times) = T^0 + C^(times)$.


=== Fractal field ring-gate audit <subsec:fractal-field-ring-gate-audit>

RG-A1. $frak(a) subset cal(A)^(upright("ret"))_8$ is declared.

RG-A2. $B = ( partial_T F, omega )$ is declared.

RG-A3. $(V_N ,E_N )$ is declared.

RG-A4. $partial_T R_(upright("ring"))$ is declared.

RG-A5. $I subset.eq V_N$ and $G = brace.l g_i :i in I brace.r$ are declared.

RG-A6. $kappa_k$ is declared for every $k in K_(upright("bin"))$.

RG-A7. $E_(upright("return")) subset.eq I times I$ is declared.

RG-A8. Each path contribution uses $SADARop_(B bar.v t) (C_(gamma) )$ or declared $phi.alt_(gamma) (B bar.v t)$.

RG-A9. $lambda_(cal(Y)) :(T_k^(times) )_k arrow.r.bar cal(Y)$ is declared as a value map.

RG-A10. The retained value difference obeys #eqref("eq:frg-identity").



=== Naming audit <subsec:naming-audit>

A label identifies a declared distinction, relation, motif or dynamic;
its defining construction fixes its properties and scope. Measured-sector
carrier names belong to applications.


=== Wave audit <subsec:wave-audit>

For an already admitted recurrent wave, its value/state projection may be recorded as:

#math.equation(block: true, numbering: none, $ Z_f = (frak(c)_f ,I^c_f ,B^e_f ) arrow.r Z_(f + 1) = (frak(c)_(f + 1) ,I^c_(f + 1) ,B^e_(f + 1) ). $)

Cycle compatibility carries wave continuity. Changed cycle compatibility routes excess burden into shedding, reclosure, pending return, or entropic duon current.
