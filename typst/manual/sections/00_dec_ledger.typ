// Native Typst port of manual/sections/00_dec_ledger.tex (verbatim scientific content).
#import "../preamble.typ": *

= Pen-and-Paper AFC Raw Execution and D.E.C. Ledger <manual:dec-ledger>



#aod-paragraph[Calculation card.]
The declared edge slots, integer weights, admissibility and boundary/window
are exact inputs. Normalization, clipping and oriented flux produce the
inline fractions and values, compared with kernel, reversal and boundary
identities. This is a conditional D0 fixture with no measured target or
physical uncertainty model; see #secref("manual:calculation-spine").



#aod-noteblock("Scope")[This section gives a hand-calculation path from one declared AFC edge computation into the A$Omega$D motif names used later in the manual. It is a manual ledger section: it records exact edge weights, kernel fractions, route status, and boundary values.]


#aod-provenance[#mainsection("main:sec:afc-stokes-seed");
#mainsection("main:subsec:q4-four-edge-implementation");
#mainsection("main:subsec:hinge-slide");
#mainsection("main:subsec:sadar");
#secref("manual:exact-arithmetic-presentation");
#secref("manual:cross-return-short-window").]


AFC runs raw. The trace records the run. A$Omega$D names detected motifs. A simulation fixture first declares the AFC scope $B$, boundary/region data, admissible channels, and update rule. The AFC run produces trace rows. A$Omega$D detectors read the trace and classify motifs such as cross-return, yro route, duration-clipping, sheddic route, terminal split, Tau-ring support, orbital retention, and collision-support trace status.

D.E.C. means Declared Edge Computation ledger. In this manual section, D.E.C. is the manual ledger format used to expose one declared AFC edge computation. Use the dotted form D.E.C.; the ledger is a manual value container for declared edge data.


#math.equation(block: true, numbering: none, $ "AFC raw node" & arrow.r "D.E.C. ledger" arrow.r "exact kernel" arrow.r "blocked hinge" arrow.r "hinge slide", \ & arrow.r "oriented ADAR component" arrow.r "SADAR value" arrow.r "boundary audit". $)

Fixture-comparator rows form exact $delta_3$ tallies.


== D.E.C. row format <manual:dec-ledger:row-format>

Each D.E.C. row records

#math.equation(block: true, numbering: none, $ B, quad v, quad e, quad v_e , quad sigma (e), quad op("adm")(e;B), quad w(e;B), quad P(e;B), quad op("route")(e;B). $)

Here $B$ is the declared boundary/window, $v$ is the active node, $e$ is an admissible edge slot, $v_e$ is the Hamming–1 neighbor reached by that slot, $sigma (e) in brace.l - 1,0, + 1 brace.r$ is the local ternary state, $op("adm")(e;B)$ records admissibility on the declared scope, $w(e;B)$ is the declared integer weight, $P(e;B)$ is the exact normalized kernel fraction, and $op("route")(e;B)$ records returned, outgoing, blocked, slide, hinge, or pending route status.


#aod-paragraph[Signed channel views.]
An oriented ledger channel fixes one signed value. Its reverse bookkeeping
view has equal magnitude and opposite sign, implementing
#mainequation("main:eq:b-scoped-flux-antisymmetry"). A separately constructed
reverse channel retains its own directional RCD and must be evaluated
independently. Component-valued rows apply the sign and Stokes checks
componentwise; #mainequation("main:eq:b-scoped-stokes") gives their boundary sum.


== One-node D.E.C. ledger <manual:dec-ledger:one-node>

Declare one $Q_4$ node and four Hamming–1 edge slots:

#math.equation(block: true, numbering: none, $ v = (0,0,0,0), wide brace.l e_1 ,e_2 ,e_3 ,e_4 brace.r . $)

Declare ternary edge states $sigma (e_i ) in brace.l - 1,0, + 1 brace.r$. The following ledger records one declared anisotropic kernel.

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: (left, center, center, center, right, center, center),
    table.header(
      toprule,
      [edge], [neighbor], [$sigma (e)$], [admissible], [weight], [probability], [route],
      midrule,
    ),
    [$e_1$], [$(1,0,0,0)$], [$+ 1$], [1], [1], [$1 slash 8$], [outgoing],
    [$e_2$], [$(0,1,0,0)$], [$- 1$], [1], [1], [$1 slash 8$], [returned],
    [$e_3$], [$(0,0,1,0)$], [$0$], [1], [4], [$1 slash 2$], [hinge],
    [$e_4$], [$(0,0,0,1)$], [$+ 1$], [1], [2], [$1 slash 4$], [outgoing],
    bottomrule,
  )
}
  ],
  caption: [One-node D.E.C. ledger.],
) <tab:manual-dec-one-node-ledger>



== Exact kernel normalization <manual:dec-ledger:kernel>

For isotropic admissible branching over four successors,

#math.equation(block: true, numbering: none, $ P^(upright("iso")) (e_i ;B) = frac(1, 4). $)

For the declared anisotropic weights,

#math.equation(block: true, numbering: none, $ w = (1,1,4,2), wide Z = 1 + 1 + 4 + 2 = 8. $)

The anisotropic kernel is

#math.equation(block: true, numbering: none, $ P^(upright("ani")) = (1 slash 8,1 slash 8,1 slash 2,1 slash 4). $)


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto),
    align: (left, right, center),
    table.header(
      toprule,
      [edge], [weight], [probability],
      midrule,
    ),
    [$e_1$], [1], [$1 slash 8$],
    [$e_2$], [1], [$1 slash 8$],
    [$e_3$], [4], [$1 slash 2$],
    [$e_4$], [2], [$1 slash 4$],
    bottomrule,
  )
}
  ],
  caption: [Exact anisotropic kernel fractions.],
) <tab:manual-dec-kernel-fractions>



#aod-literature-note[Markov kernels and random walks: Norris #aod-cite("norrisMarkov"), Levin–Peres–Wilmer #aod-cite("levinPeresWilmer"), Lawler–Limic #aod-cite("lawlerLimic").]



== Blocking rule <manual:dec-ledger:blocking-rule>

Blocking is zero admissibility. Once same-resolution hinge dwell is blocked on the declared scope, the hinge-state row is removed from the successor pool and the kernel is renormalized over branch-oriented continuations.
This structural removal instantiates #mainequation("main:eq:hinge-saturation").
An admitted dwell assigned weight zero instead remains in the structural
family and satisfies only the positive-support statement
#mainequation("main:eq:hinge-saturation-weighted"); the blocking example below
uses zero admissibility.
A dwell of weight zero and two branches of weights one and two satisfy
the weighted condition while the admitted dwell family remains nonempty.

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
      [rule], [meaning],
      midrule,
    ),
    [isotropic], [equal probability over admissible successors],
    [anisotropic], [unequal declared weights over admissible successors],
    [blocked], [zero admissibility on the declared scope],
    [hinge slide], [renormalization after same-resolution dwell is removed],
    [continuation trace], [repeated admitted node updates after hinge slide],
    bottomrule,
  )
}
  ],
  caption: [D.E.C. blocking and slide rules.],
) <tab:manual-dec-blocking-rules>



== Blocked hinge and hinge slide <manual:dec-ledger:hinge-slide>

In the following block event, the prior hinge-state row $(e_3 ,0)$ attempts same-resolution dwell, but the declared scope sets $op("adm")(e_3 ,0;B) = 0$. The additional-dwell row $(e_3 ,0_D )$, not the edge slot $e_3$ itself, is removed before renormalization; the $e_3$ slot may re-enter only as an admitted branch state. Declare the post-block slide pool

#math.equation(block: true, numbering: none, $ brace.l (e_1 , - 1),(e_2 , - 1),(e_3 , + 1) brace.r $)

with weights

#math.equation(block: true, numbering: none, $ w'((e_1 , - 1),(e_2 , - 1),(e_3 , + 1)) = (3,3,1), wide Z' = 3 + 3 + 1 = 7. $)

Then

#math.equation(block: true, numbering: none, $ P(e_1 , - 1) = 3 slash 7, wide P(e_2 , - 1) = 3 slash 7, wide P(e_3 , + 1) = 1 slash 7. $)

The returned and outgoing slide fractions are

#math.equation(block: true, numbering: none, $ P_(upright("returned")) = 3 slash 7 + 3 slash 7 = 6 slash 7, wide P_(upright("outgoing")) = 1 slash 7. $)



#aod-paragraph[Three roles and two branch roles.]
The four-channel kernel in #secref("manual:dec-ledger:kernel"),
#tabref("tab:manual-dec-kernel-fractions"), has role probabilities
$(P_(-) ,P_0 ,P_(+) ) = (1 slash 8,1 slash 2,3 slash 8)$. After blocking additional dwell,
three channel rows remain, while their two-role projection is
$(P_(-) ,P_(+) ) = (6 slash 7,1 slash 7)$. The structural hinge remains. The binary role entropy
$- (6 slash 7) log_3 (6 slash 7) - (1 slash 7) log_3 (1 slash 7)$ is below the uniform maximum
$log_3 2$ stated in #mainsection("main:subsec:q4-hamming-ternary-kernel").
This is conditional role entropy, separate from channel cardinality,
$C_3 (k) = k$, and channel mutual information.
For a capacity counterexample, declare the deterministic ternary channel
$P_(01) = P_(12) = P_(20) = 1$, all other entries zero, with uniform input.
It has one successor per row but preserves the input bijectively, so
$I(X;Y) = H(X) = 1$ trit, exceeding $log_3 2$.
No row-degree bound alone establishes that universal channel-capacity bound.


== Field tunnelling: hinge-slide window clip <manual:dec-ledger:field-tunnelling>


#aod-noteblock("Data-support class")[Field tunnelling is a D0 exact internal fixture. It uses declared hinge-slide admissibility, exact slide-kernel fractions, window-clipped duration participation, and scalar tunnel contribution.]


Field tunnelling is the retained passage of a field route through a blocked hinge by slide-compatible successor support inside the declared window. The manual spine is

#math.equation(block: true, numbering: none, $ "blocked direct hinge" & arrow.r "declared slide pool" arrow.r "exact slide kernel" arrow.r "window clip", \ & arrow.r "tunnel contribution" arrow.r "boundary audit". $)

Fix the declared boundary/window

#math.equation(block: true, numbering: none, $ B = ( partial F, omega ). $)

The short-window examples declare neutral reflection,
the native count duration interface and a same-domain window. They clip only
$rho^D = op("dur")(R D bowtie_B R^(upright("asym")) )$, leaving RD and RCD intact.
At cut-frame $B bar.v t$, declare a direct hinge route $e_0$ with

#math.equation(block: true, numbering: none, $ op("adm")(e_0 ;B bar.v t) = 0. $)

Declare the slide pool

#math.equation(block: true, numbering: none, $ op("Slide")_(mu) (B bar.v t) = brace.l s_1 , dots.h ,s_n brace.r . $)

Normalize only after the slide pool is declared:

#math.equation(block: true, numbering: none, $ Z_(upright("slide")) (B bar.v t) = sum_(s_i in op("Slide")_(mu) (B bar.v t)) w(s_i ;B bar.v t), wide P_(upright("slide")) (s_i ;B bar.v t) = frac(w(s_i ;B bar.v t), Z_(upright("slide")) (B bar.v t)). $)

For each slide-compatible successor,

#math.equation(block: true, numbering: none, $ rho^D_(omega ,s_i) (B) = min (R D_(s_i) (B), bar.v omega bar.v_(s_i) ), wide p^D_(s_i) (B) = C_(3,s_i) rho^D_(omega ,s_i) (B). $)

Let $op("Out")_(mu) (B bar.v t) subset.eq op("Slide")_(mu) (B bar.v t)$ contain the declared outgoing successors.
The scalar tunnel contribution is their projection,

#math.equation(block: true, numbering: none, $ T^D_(upright("tunnel")) (B bar.v t) = sum_(s_i in op("Out")_(mu) (B bar.v t)) P_(upright("slide")) (s_i ;B bar.v t) thin p^D_(s_i) (B). $)

When oriented attention is declared, the oriented tunnel flux is

#math.equation(block: true, numbering: none, $ Phi^D_(upright("tunnel")) (B bar.v t) = sum_(s_i in op("Out")_(mu) (B bar.v t)) P_(upright("slide")) (s_i ;B bar.v t) thin p^D_(s_i) (B) thin A_(s_i) (B). $)

Using the hinge-slide pool from #secref("manual:dec-ledger:hinge-slide"), declare the tunnel branch

#math.equation(block: true, numbering: none, $ s_(upright("tunnel")) = (e_3 , + 1), wide P_(upright("tunnel")) = 1 slash 7. $)

Declare

#math.equation(block: true, numbering: none, $ R D_(s_(upright("tunnel"))) = 5, wide bar.v omega bar.v_(s_(upright("tunnel"))) = 2, wide C_(3,s) = 3. $)

Then

#math.equation(block: true, numbering: none, $ rho^D_(omega ,s_(upright("tunnel"))) = min (5,2) = 2, wide p^D_(s_(upright("tunnel"))) = 3 dot.op 2 = 6, $)

and

#math.equation(block: true, numbering: none, $ T^D_(upright("tunnel")) = (1 slash 7) dot.op 6 = 6 slash 7. $)

The tunnel contribution is the window-clipped pressure carried by the slide-compatible outgoing successor.
If all three successors have pressure $6$, their total expected pressure
is $(3 slash 7 + 3 slash 7 + 1 slash 7)6 = 6$; the outgoing projection remains $6 slash 7$.
The same normalized kernel is used in both sums.


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
      [row], [value],
      midrule,
    ),
    [direct hinge admissibility], [$op("adm")(e_0 ;B bar.v t) = 0$],
    [slide pool], [$brace.l (e_1 , - 1),(e_2 , - 1),(e_3 , + 1) brace.r$],
    [slide weights], [$(3,3,1)$],
    [slide probabilities], [$(3 slash 7,3 slash 7,1 slash 7)$],
    [tunnel branch], [$(e_3 , + 1)$],
    [$P_(upright("tunnel"))$], [$1 slash 7$],
    [$R D_s$], [$5$],
    [$bar.v omega bar.v_s$], [$2$],
    [$rho^D_(omega ,s)$], [$2$],
    [$C_(3,s)$], [$3$],
    [$p^D_s$], [$6$],
    [$T^D_(upright("tunnel"))$], [$6 slash 7$],
    bottomrule,
  )
}
  ],
  caption: [Field tunnelling hinge-slide window-clip fixture.],
) <tab:manual-field-tunnelling-fixture>



== D.E.C. row-pair to ADAR and SADAR <manual:dec-ledger:adar-sadar>

A routed D.E.C. row-pair supplies the declared returned-current pair. That pair is promoted to an oriented ADAR component on the declared boundary/window. Declare

#math.equation(block: true, numbering: none, $ A_(12) = 1 slash 3, wide rho^D_(omega) = 4, wide C_3 = 3. $)

Then

#math.equation(block: true, numbering: none, $ p^D = C_3 rho^D_(omega) = 12, wide SADARop_B = p^D A_(12) = 12(1 slash 3) = 4. $)

Reverse orientation gives

#math.equation(block: true, numbering: none, $ A_(21) = - 1 slash 3, wide SADARop_B = - 4. $)



== Boundary closure and sheddic route audit <manual:dec-ledger:boundary-audit>

Declare

#math.equation(block: true, numbering: none, $ P^D = 27, wide C_(upright("close")) = 24. $)

Then

#math.equation(block: true, numbering: none, $ Delta_(upright("close")) = P^D - C_(upright("close")) = 3, wide X_(upright("shedding")) = max (0, Delta_(upright("close")) ) = 3. $)

This is the positive surplus amount used in the Dimonnanyro row; a route and retained-form witness are separate obligations:

#math.equation(block: true, numbering: none, $ 1":"2":"9_(upright("yro")) = upright("Dimonnanyro"). $)

Fixture-comparator rows record exact $delta_3$ residuals. Boundary-route rows record boundary values and route audits.



== D.E.C. audit invariants <manual:dec-ledger:audit-hooks>

A D.E.C. row records

#math.equation(block: true, numbering: none, $ B, quad v, quad e, quad v_e , quad sigma (e), quad op("adm")(e;B), quad w(e;B), quad P(e;B), quad op("route")(e;B). $)

The normalized kernel satisfies

#math.equation(block: true, numbering: none, $ sum_e P(e;B) = 1. $)

Zero admissibility gives zero probability:

#math.equation(block: true, numbering: none, $ op("adm")(e;B) = 0 arrow.r.double P(e;B) = 0. $)

A hinge-slide row records

#math.equation(block: true, numbering: none, $ upright("Adm")^0_B (e, sigma ) = emptyset $)

and the renormalized branch-continuation kernel. Blocking is zero admissibility.

A SADAR row records an oriented ADAR pair and satisfies

#math.equation(block: true, numbering: none, $ SADARop_B (C_(overline(e)) ) = - SADARop_B (C_e ). $)


Fixture-comparator rows form exact $delta_3$ tallies. A Tau missing-burden row carries integer provenance

#math.equation(block: true, numbering: none, $ upright("miss")_(tau) (K) = M_(upright("miss")) (K) slash M_(upright("ref")) (K), $)

with any decimal shown only as a display coordinate.


== Tau missing-burden exact ratio <manual:dec-ledger:tau-ratio>

The Tau missing-burden diagnostic is recorded with exact provenance:

#math.equation(block: true, numbering: none, $ upright("miss")_(tau) (K) = frac(M_(upright("miss")) (K), M_(upright("ref")) (K)). $)

For the displayed Dimonnanyro row,

#math.equation(block: true, numbering: none, $ M_(upright("miss")) = 31, wide M_(upright("ref")) = 50, wide upright("miss")_(tau) (1":"2":"9_(upright("yro")) ) = frac(31, 50). $)

The decimal presentation field is

#math.equation(block: true, numbering: none, $ upright("missing_fraction_display") = 0.62. $)


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
      [field], [meaning],
      midrule,
    ),
    [missing\_num], [numerator $M_(upright("miss"))$],
    [missing\_den], [denominator $M_(upright("ref"))$],
    [missing\_frac\_exact], [exact ratio],
    [missing\_fraction\_display], [decimal presentation field],
    bottomrule,
  )
}
  ],
  caption: [Tau missing-burden exact-ratio fields.],
) <tab:manual-dec-tau-missing-ratio-fields>



#aod-paragraph[Atomic leg and hinge role.]
Each D.E.C. row records the H1 base traversal separately from the ternary role.
Removing optional dwell sets $m = 0$ in $epsilon.alt 0_H (0_D )^m ( - epsilon.alt )$;
the structural hinge remains. A slide pool is entered only after that hinge.
Kernel normalization uses already admissible support. Repeated updates are
continuation traces until the actual closure and distinct-reclosure witnesses
establish wave admission.
