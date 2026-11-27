// Native Typst authority for Manual §8: exact internal double-slit cross-return (RC-030) and short-window RCD shedding (RC-038).
#import "../preamble.typ": *

= Exact Internal Fixtures <manual:cross-return-short-window>


#aod-paragraph[Setup and calculation card.]
Declared gates, windows, and signed integer bins determine the slit accounting
identity and exact $delta_3$ residuals (#raw("RC-030")); declared motif support,
channel capacity, and closure targets determine clipped pressure, pending overhang,
and shedding surplus (#raw("RC-038")). All evaluations are conditional exact
zero-float arithmetic under #secref("manual:calculation-spine"). These tables supply
internal comparators and falsifiers—never an empirical probability law or a routed
lifetime prediction.

#aod-noteblock("Scope")[This section carries exact A$Omega$-internal fixtures: Dimonhexon double-slit cross-return, short-window duration-clipping, exact $delta_3$ residual tallies, and sheddic route audits.]

#aod-noteblock("Data-support class")[These are D0 exact internal fixtures. Inputs are declared integer gates, channels, windows, and comparator bins. Comparator fixtures record $O_k , Delta^(bb(Z))_k , delta_(3,k)$; route-audit fixtures record $Delta_(upright("close"))$, $X_(upright("shedding"))$, and $op("SheddicPath")$.]


== Dimonhexon cross-return fixture <manual:cross-return:dimonhexon-slit>

#aod-noteblock("Scope")[This subsection is a boundary-restriction test: a stable Dimonhexon closure enters a slit boundary, undergoes duon-cycle handoff across the restricted boundary/window, and recloses into target bins.]

#aod-provenance[#mainsection("main:subsec:fractal-field-ring-gate")\;
#mainequation("main:eq:sadar-operator-cycle").]

#aod-paragraph[Setup.]
Declare the slit scope and carried form:

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("slit")) tack.r (F_(1":"2":"6) ,R_(upright("slit")) , partial R_(upright("slit")) , omega_(upright("slit")) ), wide B_(upright("slit")) = ( partial F_(1":"2":"6) , omega_(upright("slit")) ), $)

#math.equation(block: true, numbering: none, $ 1":"2":"6 = upright("Dimonhexon"). $)

The boundary-restricted handoff follows the exact chain

#math.equation(block: true, numbering: none, $ upright("Dimonhexon") arrow.r.long W_(omega) [D_i mu D_j ] arrow.r.long Delta^(chi upright("lag")) arrow.r.long bold(upright(A))_F (B_(upright("slit")) ) arrow.r.long "local reclosure bins". $)

For one gate $g_a$ and target bin $k in K_(upright("bin"))$, summing over the bound
discrete-window cut index $t in omega$ (kept strictly distinct from the bin index $k$)
gives the one-gate contribution

#math.equation(block: true, numbering: none, $ S^(lr((a)))_k = sum_(t in omega) sum_(gamma :g_a arrow.r.squiggly k) kappa_k SADARop_(B bar.v t) (C_(gamma) ), $)

with $S^(lr((b)))_k$ defined analogously for the second gate $g_b$.

#aod-remark[Retained closure supplies the particle-like term, boundary-constrained handoff supplies the wave-like term, and local reclosure supplies the hit-like term.]


== Recurrent-ring double-slit cross-return <manual:cross-return:ring-double-slit>

#aod-noteblock("Scope")[This subsection applies the main-note fractal field ring gate to the Dimonhexon slit handoff.]

#aod-paragraph[Setup.]
Declare the recurrent ring field on cyclic vertex set $V_N$ and adjacency $E_N$:

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("ring")) tack.r (F_(upright("ring")) ,R_(upright("ring")) , partial R_(upright("ring")) , omega_(upright("ring")) ), wide B_(upright("ring")) = ( partial_T F_(upright("ring")) , omega_(upright("ring")) ), $)

#math.equation(block: true, numbering: none, $ V_N = brace.l 0,1, dots.h ,N - 1 brace.r , wide E_N = brace.l (i,i + 1 mod N),(i,i - 1 mod N):i in V_N brace.r . $)

Fix two boundary gates and the discrete target-bin set:

#math.equation(block: true, numbering: none, $ g_a ,g_b in partial_T R_(upright("ring")) , wide k in K_(upright("bin")) . $)

#figure(
  kind: image, [
#include "../../lib/figures/manual/double_slit_cross_return_setup.typ"
  ],
  caption: [Recurrent-ring double-slit cross-return setup. Two boundary gates produce independent one-gate contributions; the no-cross baseline is the sum of one-gate contributions, and the cross-return contribution produces the declared cross-return fixture.],
) <fig:manual-recurrent-ring-double-slit>

#aod-paragraph[Derivation.]
The independent two-gate baseline is

#math.equation(block: true, numbering: none, $ T^0_k = S^(lr((a)))_k + S^(lr((b)))_k . $)

Summing coupled paths across the bound discrete-window cut dummy $t in omega$
(distinct from target bin $k in K_(upright("bin"))$) defines the cross-return term

#math.equation(block: true, numbering: none, $ C^(times)_k (B) = C_(a b,k)^(times) (B) = sum_(t in omega) sum_(gamma :g_a arrow.l.r g_b arrow.r.squiggly k) kappa_k SADARop_(B bar.v t) (C_(gamma) ). $)

Adding the baseline and cross-return yields the recurrent ring value

#math.equation(block: true, numbering: none, $ T^(times)_k = T^0_k + C^(times)_k , $)

and therefore the exact bin-level audit identity

#aod-boxed($ display(T^(times)_k - T^0_k = C^(times)_k .) $)


=== Exact double-slit fixture <manual:cross-return:exact-double-slit-fixture>

#aod-paragraph[Specialization (#raw("RC-030")).]
The released A$Omega$-internal integer-bin fixture compares the recurrent ring value
$T_k^(times) = T_k^0 + C_k^(times)$ against the declared comparator $O_k$ via the
exact signed residual $Delta^(bb(Z))_k = T^(times)_k - O_k$ and ternary tally
$delta_(3,k) (T^(times) ,O) = (s_k^(lr((3))) ,m_k )$.

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
  caption: [Dimonhexon slit handoff: exact $delta_3$ reclosure-bin fixture (#raw("RC-030")).],
) <tab:manual-dimonhexon-double-slit-fixture>

Here $C^(times)_k = T^(times)_k - T^0_k$. At the center bin ($k = 0$),

#math.equation(block: true, numbering: none, $ T^(times)_0 = 96, wide O_0 = 95, wide Delta^(bb(Z))_0 = 1, wide delta_(3,0) = ( + 1,1), $)

and across all eleven bins $k in brace.l - 5, dots.h , + 5 brace.r$,

#math.equation(block: true, numbering: none, $ sum_k T_k^(times) = 448, wide sum_k O_k = 448, wide sum_k Delta^(bb(Z))_k = 0, wide sum_k m_k = 6. $)

#figure(
  kind: image, [
#include "../../lib/figures/manual/double_slit_reclosure_fixture.typ"
  ],
  caption: [Dimonhexon double-slit reclosure fixture (#raw("RC-030")). Cross-return changes the two-gate distribution; the exact internal comparison is recorded by $delta_3$.],
) <fig:manual-double-slit-reclosure-fixture>

#figure(
  kind: table, [
#{
  set text(size: 8.3pt)
  set par(justify: false)
  table(
    columns: (auto, auto),
    align: (left, left),
    inset: (x: 4.5pt, y: 2.6pt),
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

#aod-noteblock("Status")[Released A$arrow.l.r Omega$-internal field-ring fixture verified in exact zero-float ternary arithmetic (#raw("RC-030")).]

#aod-paragraph[Engine path-pair generator and physical-law separation.]
Vector #raw("RC-030") genuinely executes the finite $C_6$ ($(V_6 , E_6 )$) two-step
path-pair generator (#raw("frg_dimonhexon_double_slit_ring"), tabulated in
#raw("manual/data/boundary_sadar/dimonhexon_double_slit_ring_paths.csv") and
verified by #raw("python3 -B -m manual.engine --sector boundary_sadar") and
#raw("aod-core --verify-vectors --check-zero-float")) across symmetric gates
$g_a = - 2, g_b = + 2$ and bins $k in brace.l - 5, dots.h , + 5 brace.r$ in exact
zero-float #raw("TritWord")/#raw("TritRatio") arithmetic: single-gate path pairs
burn contiguous optional dwell (#raw("00") / $0_D$) under hexon aperture
saturation live via #raw("TritWord.burn_contiguous_dwell") while preserving the
mandatory structural hinge (#raw("11") / $0_H$), two-gate cross-return pairs
pack into 4-bit #raw("ChiralPair4") registers, and exact summation reproduces
$sum_k T^0_k = 410$, $sum_k C^(times)_k = 38$,
$sum_k T^(times)_k = 448$ ($410 + 38 = 448$), $sum_k Delta^(bb(Z))_k = 0$, and
$sum_k m_k = 6$.

External physical detector and exposure probability laws remain strictly separated
from this internal path-pair generator. Signed internal contributions are not
physical probabilities: any downstream empirical comparison must declare separate
detector, loss/throughput, and exposure rules distinguishing expected counts,
unconditional detection including loss, and detected-bin conditional normalization
so normalization never erases throughput.

#aod-provenance[#mainsection("main:subsec:fractal-field-ring-gate")\;
#mainequation("main:eq:b-scoped-flux")\;
#mainequation("main:eq:frg-cross-return-contribution")\;
#secref("manual:cross-return:dimonhexon-slit").]

#aod-remark[The independent gate-sum value records independent reclosure; the recurrent ring value records redistributed returned-current coupling.]


== Short-window fixture scope <manual:short-window:scope>

#aod-noteblock("Scope")[This section is A$Omega$-internal. It tests short-window $rho^D$-clipping, pending overhang, closure residual, and sheddic path status without external comparison.]

#aod-paragraph[Setup.]
Declare the short-window fixture scope

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("sw")) tack.r (F_(upright("sw")) ,R_(upright("sw")) , partial R_(upright("sw")) , omega_(upright("sw")) ), wide B_(upright("sw")) = ( partial F_(upright("sw")) , omega_(upright("sw")) ). $)

#aod-paragraph[Duration-domain declaration.]
These reductions declare $R^(upright("asym")) = upright("id")$ and the additive
native count realization, so $rho^D = R D$ in this specialization. The window is a
count in that same domain, giving scalar participation
$rho^D_(omega) = min ( rho^D , bar.v omega bar.v )$; neither structural support
$R D$ nor the coupled $upright("RCD")$ object is clipped. The baseline Dimonon
support used below is

#math.equation(block: true, numbering: none, $ Pi (1":"2) = 2^1 + 2 = 4, wide H_(mu) = 1, wide rho^D_(1":"2) = R D^(lr((1))) (1":"2) = 2 dot.op 4 + 1 = 9, $)

while record length $L_M$ remains distinct from path-derived scalar $rho^D$.

#figure(
  kind: image, [
#include "../../lib/diagrams/short_window_setup.typ"
  ],
  caption: [Short-window RCD fixture flow. The path-derived $rho^D$ is clipped by the declared window to produce $rho^D_(omega)$, while pending overhang $Q^D$ and closure residual $Delta^(upright("close"))$ are kept separate from shedding excess.],
) <fig:manual-short-window-setup>


== Shared fixture equations <manual:short-window:equations>

#aod-paragraph[Derivation.]
For a candidate record $M$ in declared scope $B$, evaluate the five exact integer
quantities:

#math.equation(block: true, numbering: none, $ rho^D_(omega) (M;B) = min ( rho^D (M;B), bar.v omega bar.v ), $)

#math.equation(block: true, numbering: none, $ Q^D (M;B) = C_3 max (0, rho^D (M;B) - bar.v omega bar.v ), $)

#math.equation(block: true, numbering: none, $ P^D (M;B) = C_3 rho^D_(omega) (M;B), $)

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) (M;B) = P^D (M;B) - C^(upright("close")) (M;B), $)

#math.equation(block: true, numbering: none, $ X_(upright("shedding")) (M;B) = max (0, Delta^(upright("close")) (M;B)). $)

#aod-noteblock("Remark")[$Delta^(upright("close"))$ records signed closure residual, whereas $X_(upright("shedding"))$ records nonnegative surplus only. Negative closure residuals remain deficits or open checks, never sheddic surplus.]


== Closure-dependent and surplus fixtures <manual:short-window:fixture-table>

Keeping $Delta^(upright("close"))$ and $X_(upright("shedding"))$ distinct prevents
closure-deficit records from being misread as sheddic surplus.

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

For $1":"2":"7$, the window is shorter than path-derived support:

#math.equation(block: true, numbering: none, $ rho^D_(omega) = min (9,7) = 7, wide Q^D = 3(9 - 7) = 6, wide P^D = 3 dot.op 7 = 21. $)

Against lower closure $C_6 = 18$, the fixture carries surplus ($Delta^(upright("close")) = 3$, $X_(upright("shedding")) = 3$):

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 21 - 18 = 3, wide X_(upright("shedding")) = 3, $)

whereas against upper closure $C_8 = 24$, it is closure-deficient:

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 21 - 24 = - 3, wide X_(upright("shedding")) = 0. $)

Hence $1":"2":"7$ is closure-dependent.


== The $1":"2":"9$ surplus fixture <manual:short-window:129>

For $1":"2":"9$, the window matches full path-derived support:

#math.equation(block: true, numbering: none, $ rho^D_(omega) = min (9,9) = 9, wide Q^D = 0, wide P^D = 3 dot.op 9 = 27. $)

Against $C_8 = 24$,

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 27 - 24 = 3, wide X_(upright("shedding")) = 3, $)

producing the nine-window surplus fixture.


== The $1":"2":"10$ clipped retained fixture <manual:short-window:1210>

For $1":"2":"10$, candidate record length exceeds path-derived support, so clipping
caps participation at $9$:

#math.equation(block: true, numbering: none, $ rho^D_(omega) = min (9,10) = 9, wide Q^D = 0, wide P^D = 27. $)

Against $C_(10) = 27$,

#math.equation(block: true, numbering: none, $ Delta^(upright("close")) = 0, wide X_(upright("shedding")) = 0, $)

yielding a clipped retained check.


== Sheddic path audit <manual:short-window:shedpath-audit>

#aod-paragraph[Falsification and witness ordering.]
The sheddic path audit requires an explicit target channel from

#math.equation(block: true, numbering: none, $ upright("SheddicPath")(X_(upright("shedding")) ) in brace.l E_2 ,sans("C")_6 ,sans("C")_8 ,sans("C")_(10) , dots.h ,sans("C")_(2 n) brace.r . $)

The four pressure tuples above supply amounts only. Complete routing must separately
bind route identity, allocated amount, conservation, and—whenever retention is
claimed—a retained-form and lifetime/window witness; positive surplus alone supplies
none of those certificates. When a routed surplus emits a shed continuation
(#mainequation("main:eq:shed-continuation-witness")), downstream delivery, acceptance,
seating, initial recipient origin closure, and later compatible reclosure remain
separate witness-ordered stages (#mainequation("main:eq:recipient-event-lattice"));
routed surplus alone proves no recipient reclosure. A missing route leaves that stage
incomplete, and a deficit remains an open check unless a declared closure completion
is supplied.


== Audit hooks <manual:short-window:audit-hooks>

#aod-noteblock("Audit")[Every short-window fixture records $rho^D_(omega)$, $Q^D$, $Delta^(upright("close"))$, and $X_(upright("shedding"))$ separately. Sheddic surplus is nonnegative only; completed routing additionally requires a declared sheddic path and its conservation witness.]

#aod-provenance[#mainequation("main:eq:window-clipped-rho")\;
#mainequation("main:eq:burden-overhang")\;
#mainequation("main:eq:sheddic-path")\;
#mainequation("main:eq:shed-continuation-witness")\;
#mainequation("main:eq:recipient-event-lattice")\;
#secref("manual:short-window:scope").]

#aod-remark[This section is A$Omega$-internal: it prepares the exact clipping and conservation mechanics reused by rest-energy and boundary-current records without introducing an external comparison target.]


== Five-boundary short-window clipping and shedding D.E.C. ledger <manual:short-window:dec-clipping-ledger>

#aod-paragraph[Setup and engine verification (#raw("RC-038")).]
Declare the short-window clipping and enclosure boundary stack

#math.equation(block: true, numbering: none, $ B_(upright("core")) arrow.r B_(omega) arrow.r B_(upright("close")) arrow.r B_(upright("shed")) arrow.r B_(upright("ext")). $)

Vector #raw("RC-038") (#raw("dec_short_window_rcd_clipping")), verified alongside
#raw("RC-030") by #raw("python3 -B -m manual.engine --sector boundary_sadar") and
#raw("aod-core --verify-vectors --check-zero-float") in
#raw("manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv"), evaluates exact
single-channel window clipping $rho^D_(omega) = min (R D, bar.v omega bar.v )$,
active pressure $p^D = 3 rho^D_(omega)$, pending overhang
$Q^D = 3 max (0, R D - bar.v omega bar.v )$, and odd-window shedding
$X_(upright("shedding")) = max (0, p^D - C_(upright("close")) )$ across $1":"2$
($R D = 9$), $3":"3$ ($R D = 61$), and $3":"4$ ($R D = 137$). Every row satisfies
exact integer conservation $p^D + Q^D = 3 R D$ ($27$, $183$, and $411$), while
positive shedding $X_(upright("shedding")) = 3$ activates uniquely on the full odd
Dimonon window $(1":"2, bar.v omega bar.v = 9)$ exceeding $sans("C")_8 = 24$.

#figure(
  kind: image, [
#include "../../lib/figures/manual/short_window_boundary_feynman.typ"
  ],
  caption: [Short-window boundary gate $B_(omega)$ clipping $3 R D$ into active pressure $p^D = 3 rho^D_(omega)$ and retained overhang $Q^D$ with exact conservation $p^D + Q^D = 3 R D$ (#raw("RC-038"), #raw("short_window_rcd_dec_ledger.csv")).],
) <fig:manual-short-window-boundary-feynman>

#figure(
  kind: table, [
#{
  let rows = csv("/manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv", row-type: dictionary)
  set text(size: 8.2pt)
  set par(justify: false)
  table(
    columns: (1.10fr, 0.90fr, 0.95fr, 0.95fr, 0.90fr, 1.00fr, 1.15fr, 1.55fr, 1.50fr),
    align: (left, right, right, right, right, right, right, right, right),
    inset: (x: 3.0pt, y: 3.5pt),
    table.header(
      toprule,
      [Support], [$R D$], [$bar.v omega bar.v$], [$rho^D_(omega)$], [$p^D$], [$Q^D$], [$C_(upright("close"))$], [$X_(upright("shedding"))$], [$p^D + Q^D$],
      midrule,
    ),
    ..rows.map(r => (
      [#r.support],
      [#r.RD],
      [#r.window_len],
      [#r.rho_omega],
      [#r.p_D],
      [#r.Q_D],
      [#r.C_close],
      [#r.X_shedding],
      [#r.total_3RD],
    )).flatten(),
    bottomrule,
  )
}
  ],
  caption: [Engine-bound short-window RCD clipping, overhang conservation, and odd-window shedding D.E.C. ledger (#raw("RC-038"), live from #raw("short_window_rcd_dec_ledger.csv")).],
) <tab:manual-short-window-dec-ledger>


