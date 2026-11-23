// Native Typst port of manual/sections/03_short_window_rcd_shedding_fixtures.tex (verbatim scientific content).
#import "../preamble.typ": *

= Exact Internal Fixtures <manual:cross-return-short-window>



#aod-paragraph[Calculation card.]
Declared gates, windows and signed integer bins give the slit accounting
identity and exact residuals; declared support, capacity and closure target
give clipped pressure, pending overhang and surplus. Their uncertainty is
conditional fixture arithmetic. The tables supply the comparators and
falsifiers, not a measured probability law or a routed lifetime prediction.
Use the common method in #secref("manual:calculation-spine").



#aod-noteblock("Scope")[This section carries exact A$Omega$-internal fixtures: cross-return, duration-clipping, exact $delta_3$ residual tally, and sheddic route audit.]


#aod-noteblock("Data-support class")[These are D0 exact internal fixtures. Input data are declared integer gates, channels, windows, and comparator bins. Comparator fixtures record $O_k , Delta^(bb(Z))_k , delta_(3,k)$. Route-audit fixtures record $Delta_(upright("close"))$, $X_(upright("shedding"))$, and $op("SheddicPath")$.]



== Dimonhexon cross-return fixture <manual:cross-return:dimonhexon-slit>


#aod-noteblock("Scope")[This subsection is a boundary-restriction test. A stable Dimonhexon closure enters a slit boundary, becomes a duon-cycle handoff across the restricted boundary/window, and recloses into target bins.]


#aod-provenance[#mainsection("main:subsec:fractal-field-ring-gate")\;
#mainequation("main:eq:sadar-operator-cycle").]


Declare the slit scope

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("slit")) tack.r (F_(1":"2":"6) ,R_(upright("slit")) , partial R_(upright("slit")) , omega_(upright("slit")) ), wide B_(upright("slit")) = ( partial F_(1":"2":"6) , omega_(upright("slit")) ). $)

The carried form is

#math.equation(block: true, numbering: none, $ 1":"2":"6 = upright("Dimonhexon"). $)

The boundary-restricted handoff is recorded as

#math.equation(block: true, numbering: none, $ upright("Dimonhexon") arrow.r.long W_(omega) [D_i mu D_j ] arrow.r.long Delta^(chi upright("lag")) arrow.r.long bold(upright(A))_F (B_(upright("slit")) ) arrow.r.long "local reclosure bins". $)


For one gate $g_a$, the target-bin contribution is

#math.equation(block: true, numbering: none, $ S^(lr((a)))_k = sum_(t in omega) sum_(gamma :g_a arrow.r.squiggly k) kappa_k SADARop_(B bar.v t) (C_(gamma) ). $)

For a second gate $g_b$, define $S^(lr((b)))_k$ analogously.


#aod-remark[The particle-like term is retained closure. The wave-like term is boundary-constrained handoff. The hit-like term is local reclosure.]



== Recurrent-ring double-slit cross-return <manual:cross-return:ring-double-slit>


#aod-noteblock("Scope")[This subsection applies the main-note fractal field ring gate to the Dimonhexon slit handoff.]

Declare a recurrent ring field

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("ring")) tack.r (F_(upright("ring")) ,R_(upright("ring")) , partial R_(upright("ring")) , omega_(upright("ring")) ), wide B_(upright("ring")) = ( partial_T F_(upright("ring")) , omega_(upright("ring")) ). $)

Let

#math.equation(block: true, numbering: none, $ V_N = brace.l 0,1, dots.h ,N - 1 brace.r , $)

with ring adjacency

#math.equation(block: true, numbering: none, $ E_N = brace.l (i,i + 1 mod N),(i,i - 1 mod N):i in V_N brace.r . $)

Declare two boundary gates

#math.equation(block: true, numbering: none, $ g_a ,g_b in partial_T R_(upright("ring")) . $)

The target bins are

#math.equation(block: true, numbering: none, $ k in K_(upright("bin")) . $)




#figure(
  kind: image, [
#include "../../lib/figures/manual/double_slit_cross_return_setup.typ"
  ],
  caption: [Recurrent-ring double-slit cross-return setup. Two boundary gates produce independent one-gate contributions; the no-cross baseline is the sum of one-gate contributions, and the cross-return contribution produces the declared cross-return fixture.],
) <fig:manual-recurrent-ring-double-slit>


The independent two-gate baseline is

#math.equation(block: true, numbering: none, $ T^0_k = S^(lr((a)))_k + S^(lr((b)))_k . $)

The cross-return contribution is

#math.equation(block: true, numbering: none, $ C^(times)_k (B) = C_(a b,k)^(times) (B) = sum_(t in omega) sum_(gamma :g_a arrow.l.r g_b arrow.r.squiggly k) kappa_k SADARop_(B bar.v t) (C_(gamma) ). $)

The recurrent ring value is

#math.equation(block: true, numbering: none, $ T^(times)_k = T^0_k + C^(times)_k . $)

Thus the audit identity is

#aod-boxed($ display(T^(times)_k - T^0_k = C^(times)_k .) $)




=== Exact double-slit fixture <manual:cross-return:exact-double-slit-fixture>

The following fixture is a released A$Omega$-internal exact integer bin test. The independent gate-sum value is $T_k^0$. The recurrent ring value is $T_k^(times)$. The declared fixture comparator is $O_k$. The comparison is the exact $delta_3$ tally $delta_(3,k) (T^(times) ,O) = (s_k^(lr((3))) ,m_k )$.


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto),
    align: (right, right, right, right, right, right, right, right),
    table.header(
      toprule,
      [$k$], [$S_k$], [$T^0_k$], [$C^(times)_k$], [$T^(times)_k$], [$O_k$], [$Delta^(bb(Z))_k$], [$delta_(3,k)$],
      midrule,
    ),
    [$- 5$], [4], [8], [0], [8], [8], [0], [$(0,0)$],
    [$- 4$], [9], [18], [-8], [10], [11], [-1], [$( - 1,1)$],
    [$- 3$], [16], [32], [-12], [20], [19], [1], [$( + 1,1)$],
    [$- 2$], [25], [50], [8], [58], [59], [-1], [$( - 1,1)$],
    [$- 1$], [31], [62], [18], [80], [79], [1], [$( + 1,1)$],
    [$0$], [35], [70], [26], [96], [95], [1], [$( + 1,1)$],
    [$1$], [31], [62], [18], [80], [80], [0], [$(0,0)$],
    [$2$], [25], [50], [8], [58], [58], [0], [$(0,0)$],
    [$3$], [16], [32], [-12], [20], [21], [-1], [$( - 1,1)$],
    [$4$], [9], [18], [-8], [10], [10], [0], [$(0,0)$],
    [$5$], [4], [8], [0], [8], [8], [0], [$(0,0)$],
    bottomrule,
  )
}
  ],
  caption: [Dimonhexon slit handoff: exact $delta_3$ reclosure-bin fixture.],
) <tab:manual-dimonhexon-double-slit-fixture>


Here $C^(times)_k = T^(times)_k - T^0_k$. The center-bin fixture is

#math.equation(block: true, numbering: none, $ T^(times)_0 = 96, wide O_0 = 95, wide Delta^(bb(Z))_0 = 1, wide delta_(3,0) = ( + 1,1). $)

The full-fixture checks are

#math.equation(block: true, numbering: none, $ sum_k T_k^(times) = 448, wide sum_k O_k = 448, wide sum_k Delta^(bb(Z))_k = 0, wide sum_k m_k = 6. $)



#figure(
  kind: image, [
#include "../../lib/figures/manual/double_slit_reclosure_fixture.typ"
  ],
  caption: [Dimonhexon double-slit reclosure fixture. Cross-return changes the two-gate distribution; the exact internal comparison is recorded by $delta_3$.],
) <fig:manual-double-slit-reclosure-fixture>



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
      [Symbol], [Meaning],
      midrule,
    ),
    [$S^(lr((a)))_k$], [one-gate contribution from $g_a$ into bin $k$],
    [$S^(lr((b)))_k$], [one-gate contribution from $g_b$ into bin $k$],
    [$T^0_k$], [independent gate-sum value],
    [$C_(a b,k)^(times) (B)$], [cross-return contribution from $g_a arrow.l.r g_b$ into bin $k$],
    [$T^(times)_k$], [recurrent ring value],
    [$O_k$], [declared fixture comparator, if used],
    [$Delta_k^(bb(Z))$], [exact signed integer fixture residual],
    [$delta_(3,k) (T^(times) ,O)$], [exact ternary signed residual tally],
    bottomrule,
  )
}
  ],
  caption: [Recurrent-ring cross-return symbol table.],
) <tab:manual-recurrent-ring-symbols>



#aod-noteblock("Status")[Released A$arrow.l.r Omega$-internal field-ring fixture.]

The signed-bin identity preserves total baseline $410$ and cross contribution
$38$, giving $448$. The application still needs a frozen nested-path
generator binding gates, coupling, window and observation/exposure rules
before these bins are a generated prediction. Signed contributions are not
probabilities. A probability comparison must distinguish expected counts,
unconditional detection including loss, and detected-bin conditional
normalization; normalization must not erase throughput.


#aod-provenance[#mainsection("main:subsec:fractal-field-ring-gate")\;
#mainequation("main:eq:b-scoped-flux")\;
#mainequation("main:eq:frg-cross-return-contribution")\;
#secref("manual:cross-return:dimonhexon-slit").]


#aod-remark[The independent gate-sum value records independent reclosure. The recurrent ring value records redistributed returned-current coupling.]



== Short-window fixture scope <manual:short-window:scope>


#aod-noteblock("Scope")[This section is A$Omega$-internal. It tests short-window $rho^D$-clipping, pending overhang, closure residual, and sheddic path status without external comparison.]


Declare the short-window fixture scope

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("sw")) tack.r (F_(upright("sw")) ,R_(upright("sw")) , partial R_(upright("sw")) , omega_(upright("sw")) ), wide B_(upright("sw")) = ( partial F_(upright("sw")) , omega_(upright("sw")) ). $)



#aod-paragraph[Duration-domain declaration.]
These reductions declare $R^(upright("asym")) = upright("id")$ and the additive native
count realization, so $rho^D = R D$ in this specialization. The window is a
count in that same domain; $rho^D_(omega) = min ( rho^D , bar.v omega bar.v )$ is scalar
participation. Neither support RD nor the coupled RCD object is clipped.
The baseline Dimonon support used below is

#math.equation(block: true, numbering: none, $ Pi (1":"2) = 2^1 + 2 = 4, wide H_(mu) = 1, wide rho^D_(1":"2) = R D^(lr((1))) (1":"2) = 2 dot.op 4 + 1 = 9. $)

The record length is denoted by $L_M$. It is distinct from the path-derived scalar $rho^D$.


#figure(
  kind: image, [
#include "../../lib/diagrams/short_window_setup.typ"
  ],
  caption: [Short-window RCD fixture flow. The path-derived $rho^D$ is clipped by the declared window to produce $rho^D_(omega)$, while pending overhang $Q^D$ and closure residual $Delta^(upright("close"))$ are kept separate from shedding excess.],
) <fig:manual-short-window-setup>



== Shared fixture equations <manual:short-window:equations>

For a candidate record $M$ in a declared scope $B$, use

#math.equation(block: true, numbering: none, $ rho^D_(omega) (M;B) = min ( rho^D (M;B), bar.v omega bar.v ), $)


#math.equation(block: true, numbering: none, $ Q^D (M;B) = C_3 max (0, rho^D (M;B) - bar.v omega bar.v ), $)


#math.equation(block: true, numbering: none, $ P^D (M;B) = C_3 rho^D_(omega) (M;B), $)


#math.equation(block: true, numbering: none, $ Delta^(upright("close")) (M;B) = P^D (M;B) - C^(upright("close")) (M;B), $)


#math.equation(block: true, numbering: none, $ X_(upright("shedding")) (M;B) = max (0, Delta^(upright("close")) (M;B)). $)


#aod-noteblock("Remark")[$Delta^(upright("close"))$ records signed closure residual. $X_(upright("shedding"))$ records only positive surplus. Negative closure residuals are retained as deficits or open checks, not as sheddic surplus.]



== Closure-dependent and surplus fixtures <manual:short-window:fixture-table>

The following table keeps $Delta^(upright("close"))$ and $X_(upright("shedding"))$ separate. This prevents closure-deficit records from being misread as sheddic surplus.


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
    align: (center, center, center, center, center, center, center, center, center, center),
    table.header(
      toprule,
      [Row], [$C_3$], [$rho^D$], [$L_M$], [$bar.v omega bar.v$], [$rho^D_(omega)$], [$Q^D$], [$P^D$], [$C^(upright("close"))$], [$Delta^(upright("close")) ,X_(upright("shedding"))$],
      midrule,
    ),
    [$1":"2":"7 arrow.r C_6$], [3], [9], [7], [7], [7], [6], [21], [18], [$3,3$],
    [$1":"2":"7 arrow.r C_8$], [3], [9], [7], [7], [7], [6], [21], [24], [$- 3,0$],
    [$1":"2":"9 arrow.r C_8$], [3], [9], [9], [9], [9], [0], [27], [24], [$3,3$],
    [$1":"2":"10 arrow.r C_(10)$], [3], [9], [10], [10], [9], [0], [27], [27], [$0,0$],
    bottomrule,
  )
}
  ],
  caption: [Short-window RCD and shedding fixtures. All records use $C_3 = 3$ and $rho^D = R D^(lr((1))) (1":"2) = 9$.],
) <tab:manual-short-window-fixtures>



== The $1":"2":"7$ closure-dependent fixture <manual:short-window:127>

For $1":"2":"7$, the window is shorter than the path-derived support:

#math.equation(block: true, numbering: none, $ rho^D_(omega) = min (9,7) = 7, wide Q^D = 3(9 - 7) = 6, wide P^D = 3 dot.op 7 = 21. $)

Against lower closure $C_6 = 18$, the fixture carries surplus:

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 21 - 18 = 3, wide X_(upright("shedding")) = 3. $)

Against upper closure $C_8 = 24$, the fixture is closure-deficient:

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 21 - 24 = - 3, wide X_(upright("shedding")) = 0. $)

Thus $1":"2":"7$ is closure-dependent.


== The $1":"2":"9$ surplus fixture <manual:short-window:129>

For $1":"2":"9$, the candidate window reaches the path-derived support:

#math.equation(block: true, numbering: none, $ rho^D_(omega) = min (9,9) = 9, wide Q^D = 0, wide P^D = 3 dot.op 9 = 27. $)

Against the $C_8 = 24$ closure record,

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 27 - 24 = 3, wide X_(upright("shedding")) = 3. $)

This is the nine-window surplus fixture.


== The $1":"2":"10$ clipped retained fixture <manual:short-window:1210>

For $1":"2":"10$, the candidate record length exceeds the path-derived support:

#math.equation(block: true, numbering: none, $ rho^D_(omega) = min (9,10) = 9, wide Q^D = 0, wide P^D = 27. $)

Against $C_(10) = 27$,

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 0, wide X_(upright("shedding")) = 0. $)

The fixture is a clipped retained check.


== Sheddic path audit <manual:short-window:shedpath-audit>

The sheddic path audit uses

#math.equation(block: true, numbering: none, $ upright("SheddicPath")(X_(upright("shedding")) ) in brace.l E_2 ,sans("C")_6 ,sans("C")_8 ,sans("C")_(10) , dots.h ,sans("C")_(2 n) brace.r . $)

The four pressure tuples above supply amounts. The short-window application
must additionally bind route identity, allocated amount and conservation,
then a retained-form and lifetime/window witness when retention is claimed.
Those certificates are not supplied by a positive surplus alone. When a routed
surplus emits a shed continuation (#mainequation("main:eq:shed-continuation-witness")),
downstream delivery, acceptance, seating, initial recipient origin closure and
later compatible reclosure remain separate witness-ordered stages
(#mainequation("main:eq:recipient-event-lattice")); routed surplus alone proves
no recipient reclosure. A missing route leaves only that stage incomplete; a
deficit remains an open check or requires a declared closure completion.


== Audit hooks <manual:short-window:audit-hooks>


#aod-noteblock("Audit")[A short-window fixture records $rho^D_(omega)$, $Q^D$, $Delta^(upright("close"))$, and $X_(upright("shedding"))$ separately. Sheddic surplus is positive only; completed routing additionally requires a declared sheddic path and its conservation witness.]


#aod-provenance[#mainequation("main:eq:window-clipped-rho")\;
#mainequation("main:eq:burden-overhang")\;
#mainequation("main:eq:sheddic-path")\;
#mainequation("main:eq:shed-continuation-witness")\;
#mainequation("main:eq:recipient-event-lattice")\;
#secref("manual:short-window:scope").]


#aod-remark[This section is A$Omega$-internal. It prepares the mechanics used by rest-energy records and boundary-current records without adding an external comparison target.]
