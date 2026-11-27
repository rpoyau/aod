// Native Typst authority for Manual §9: field rest-energy records, five-boundary Tau/debris SADAR (RC-027/028/029, SD-007), and Tritrioseptyro Higgs fixture (RC-011, SD-004/005).
#import "../preamble.typ": *

= Field Rest-Energy Records <manual:rest-energy-prediction>


#aod-paragraph[Setup and calculation card.]
Exact support/window declarations and zero-float #raw("TritWord")/#raw("TritRatio")
SADAR evaluations (vectors #raw("RC-027"), #raw("RC-028"), #raw("RC-029"), and
#raw("RC-011")) produce the A$Omega$ accessor, collision-shedding debris, and internal
Higgs-selection records; measured masses remain quarantined external targets at
$B_(upright("ext")) = sans("Q")_(upright("ext"))$ (#raw("SD-007"), #raw("SD-004"),
#raw("SD-005")) with the quoted uncertainties. A general rest-energy prediction still
requires this application's shared-history producer, history-to-rate map, relational
reference clock, and calibrated energy map. The Higgs table evaluates a separate
declared candidate/map diagnostic; its target-only pulls exclude model uncertainty.
Common comparison and source roles follow #secref("manual:calculation-spine").


== 0$bar.v -$ scope <manual:rest:scope>

#aod-paragraph[Setup.]
Rest-energy records separate exact internal A$Omega$ field-map records (support,
carried cycle, and accessor values) from quarantined measured-sector target rows:

#math.equation(block: true, numbering: none, $ bold(upright(a)) tack.r (F,R, partial_T R, omega ), wide B = ( partial_T F, omega ). $)

The calculation spine is

#math.equation(block: true, numbering: none, $ C_f [M]_(AO) arrow.r.long sans("AO")_(mu) (C) arrow.r.long SADARop_B (C) arrow.r.long nu_(x, AO) arrow.r.long E_(x,upright("ext")) . $)

#aod-noteblock("Data-support class")[Rest-energy records are D0 exact internal A$Omega$ field records or O0 external-map comparisons, depending on the declared measured-sector target rows. Target uncertainties are supplied; input, reduction, and value-map contributions remain unresolved where no justified model is supplied.]

#aod-provenance[#mainappendix("main:app:ao-field-fractal-properties").]



== Support notation used by the calculation records <manual:rest:support-notation>

The manual uses compact support notation only where the calculation needs it:

#math.equation(block: true, numbering: none, $ D_i square.stroked D_j = "open-seat duon support", $)


#math.equation(block: true, numbering: none, $ D_i mu D_j , wide mu in brace.l - 1,0, + 1 brace.r , wide = "resolved duon support", $)


#math.equation(block: true, numbering: none, $ E_2^0 = "open-seat duon support", wide E_2^(plus.minus) = "duad / seated duon support". $)

The compact field supports are

#math.equation(block: true, numbering: none, $ 1":"2":"L = "Dimonon support", wide 3":"q":"L = "Trion support". $)

Odd lengths are carried as odd-window route status between adjacent even support enclosures:

#math.equation(block: true, numbering: none, $ L = 2 k + 1 quad arrow.r.double quad C_(2 k) arrow.r.squiggly L arrow.r.squiggly C_(2 k + 2) . $)

When this odd-window instability is retained as a route-status suffix, write $K_(upright("yro"))$. Support-enclosure names remain the even-enclosure names.


#aod-provenance[#mainappendix("main:app:ao-field-fractal-properties").]




#aod-paragraph[Proposed supports and enclosure notation.]
Examples of proposed specifications are

#math.equation(block: true, numbering: none, $ 1":"2":"6 = "Dimonhexon" = "Dimonon curling-curl support form carried on "C_6 , $)

and

#math.equation(block: true, numbering: none, $ 3":"3":"6 = "Tritriohexon", wide 3":"4":"6 = "Tetratriohexon", $)

on $C_6$. SADAR couples their retained beats after admission.

The shared hexon of #mainappendix("main:app:cc-basic-shared-hexon") expands as

#math.equation(block: true, numbering: none, $ (3:3)^1 ::(3:4)^1 ::(1:2)^0 ::6. $)



The separator rule in #mainsection("main:subsec:fractal-tesseract-cycle-range")
gives the following support parse:

$ 3":"4::3":"3::6 equiv (3":"4, 3":"3; C_6 ). $ <eq:double-colon-parse-example>



#figure(
  kind: table, [
#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.header(
      toprule,
      [Compact form], [Name], [Outer enclosure],
      midrule,
    ),
    [$3:3:0::6$], [$upright("Tritrio")^3 ::upright("Tetratrio")^3 ::upright("hexon")$], [hexon],
    [$4:4:0::8$], [$upright("Tritrio")^4 ::upright("Tetratrio")^4 ::upright("octon")$], [octon],
    [$5:5:0::10$], [$upright("Tritrio")^5 ::upright("Tetratrio")^5 ::upright("decon")$], [decon],
    bottomrule,
  )
}
  ],
  caption: [Filled shared enclosure forms.],
) <tab:cc-filled-shared-enclosures>



=== Shared shell-path declaration <subsec:shared-shell-path-declaration>

The shared shell-path declaration may be written

#math.equation(block: true, numbering: none, $ 0 mid(|) - ::Z:A:0:6 chevron.l 1:1:0::6 chevron.r . $)

Named:

#math.equation(block: true, numbering: none, $ 0 mid(|) - ::Z:A:0:upright("hexon") chevron.l upright("Tritrio")::upright("Tetratrio")::upright("hexon") chevron.r . $)

For the filled hexon field, write

#math.equation(block: true, numbering: none, $ 0 mid(|) - ::Z:A:0:6 chevron.l 3:3:0::6 chevron.r . $)

Named:

#math.equation(block: true, numbering: none, $ 0 mid(|) - ::Z:A:0:upright("hexon") chevron.l upright("Tritrio")^3 ::upright("Tetratrio")^3 ::upright("hexon") chevron.r . $)



=== Nested shell-stack pattern <subsec:nested-shell-stack-pattern>

The same curling-curl pattern iterates upward through shared enclosures and filled enclosures:

#math.equation(block: true, numbering: none, $ upright("Tritrio")^3 ::upright("Tetratrio")^3 ::upright("hexon") arrow.r upright("Tritrio")^4 ::upright("Tetratrio")^4 ::upright("octon") arrow.r upright("Tritrio")^5 ::upright("Tetratrio")^5 ::upright("decon"). $)



== Field-property accessor calculations <app:ao-field-fractal-properties:accessors-table>

Under the single-hinge neutral-reflection hypotheses of
#mainappendix("main:app:ao-field-fractal-properties:accessor"), the following
compatible native count windows give these nine accessor rows.
In the declared free-seat fixtures, $1":"2 arrow.r.double s = 2$ and
$H_(mu)^([2]) = 1$, while $3":"3 arrow.r.double s = 1$ and
$H_(mu)^([1]) = 1$. A full-seated single-hinge cycle uses
$H_(mu) = H_(mu)^(upright("cyc")) = 1$ unless free-seat provenance is declared.

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
    align: (center, left, left, center, left, center, center, center, center, center, center),
    table.header(
      toprule,
      [$cal(F)_(AO)$], [$M$], [$C_f [M]_(AO)$], [$Pi_(alpha)$], [$H_(mu)$], [$R D_(AO)$], [$bar.v omega bar.v$], [$rho^D_(omega)$], [$P^D$], [$Q^D$], [$X_(upright("shedding"))$],
      midrule,
    ),
    [$frak(f)_(1:2:6)$], [$1":"2":"6$], [$C_f [1":"2]_(AO)$], [4], [$H_(mu)^([2]) = 1$], [9], [6], [6], [18], [9], [0],
    [$frak(f)_(1:2:8)$], [$1":"2":"8$], [$C_f [1":"2]_(AO)$], [4], [$H_(mu)^([2]) = 1$], [9], [8], [8], [24], [3], [0],
    [$frak(f)_(1:2:9)$], [$1":"2":"9$], [$C_f [1":"2]_(AO)$], [4], [$H_(mu)^([2]) = 1$], [9], [9], [9], [27], [0], [3],
    [$frak(f)_(1:2:10)$], [$1":"2":"10$], [$C_f [1":"2]_(AO)$], [4], [$H_(mu)^([2]) = 1$], [9], [10], [9], [27], [0], [0],
    [$frak(f)_(3:2:6)$], [$3":"2":"6$], [$C_f [3":"2]_(AO)$], [10], [1], [21], [6], [6], [30], [75], [0],
    [$frak(f)_(3:2:8)$], [$3":"2":"8$], [$C_f [3":"2]_(AO)$], [10], [1], [21], [8], [8], [40], [65], [0],
    [$frak(f)_(3:2:10)$], [$3":"2":"10$], [$C_f [3":"2]_(AO)$], [10], [1], [21], [10], [10], [50], [55], [0],
    [$frak(f)_(3:3:6)$], [$3":"3":"6$], [$C_f [3":"3]_(AO)$], [30], [$H_(mu)^([1]) = 1$], [61], [6], [6], [36], [330], [0],
    [$frak(f)_(3:4:6)$], [$3":"4":"6$], [$C_f [3":"4]_(AO)$], [68], [$H_(mu)^(upright("cyc")) = 1$], [137], [6], [6], [42], [917], [0],
    bottomrule,
  )
}
  ],
  caption: [A$Omega$ field fractal properties.],
) <tab:ao-field-fractal-properties>


For $3":"4$, the single-hinge reduction of
#mainappendix("main:app:rd-tests:corollaries") gives

$ Pi (3":"4) = 4^3 + 4 = 68, wide R D(3":"4) = 2 dot.op 68 + 1 = 137. $ <app:rd:eq:three-four-rd>

The added $4$ is retained edge-shell support; the cycle object remains distinct from
this scalar accessor.

#aod-paragraph[Derivation: support-multiplicity atlas and common span (#raw("RC-029")).]
In #tabref("tab:ao-field-fractal-properties"), support-multiplicity pressure uses
$C_(upright("sup")) (p":"q) = p + q in brace.l 3, 5, 6, 7 brace.r$, giving
$P^D_(upright("sup")) = (p + q) rho^D_(omega)$ and
$Q^D_(upright("sup")) = (p + q) max (0, R D - bar.v omega bar.v )$, whereas
single-channel collision-pocket audits use scoped ternary continuation capacity
$C_3 = 3$ ($P^D_(upright("chan")) = 3 rho^D_(omega)$). Verified in exact zero-float
arithmetic by vector #raw("RC-029") (#raw("sadar_rest_energy_atlas"),
#raw("rest_energy_sadar_debris_atlas.csv")), the eight non-null recurring support
half-cycle step periods $2 Pi in brace.l 2, 4, 6, 8, 20, 60, 136 brace.r$ (with $1":"1$
doubled to $8$) fix the common four-phase bit-window span

#math.equation(block: true, numbering: none, $ L_(upright("common")) = 4 dot.op op("lcm")(2, 4, 6, 8, 20, 60, 136) = 8160, $)

strictly distinct from the summed eight-lineage closure tally
$0 + 60 + 136 + 408 + 1020 + 1360 + 2040 + 4080 = 9104$ over that common span, while
preserving exact native reflection-duration ratios
$R D(3":"3) slash R D(1":"2) = 61 slash 9$,
$R D(3":"4) slash R D(3":"3) = 137 slash 61$, and
$R D(3":"2) slash R D(1":"2) = 21 slash 9 = 7 slash 3$.

#figure(
  kind: image, [
#include "../../lib/figures/manual/rest_energy_stability_debris_atlas.typ"
  ],
  caption: [Exact support window pressure $P^D_(upright("sup"))$, pending overhang $Q^D_(upright("sup"))$, and closure counts per $8160$ common bit-window span across all ten rest-energy and collision-shedding debris carriers (#raw("RC-029"), #raw("rest_energy_sadar_debris_atlas.csv")).],
) <fig:manual-rest-energy-debris-atlas>


== A$Omega$ field-map table <manual:rest:ao-field-value-table>

The A$Omega$ field-map table lists the manual mapping from measured-sector names to A$Omega$ field supports. The numerical field-support properties are calculated in
#tabref("tab:ao-field-fractal-properties").


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, left, left, left, left),
    table.header(
      toprule,
      [$x_(upright("ext"))$], [external map], [$M_x$], [$C_f [M_x ]_(AO)$], [$nu_(x, AO)$],
      midrule,
    ),
    [$e^(-)$], [$00 bar.v -$ Dimonhexon], [$1":"2":"6$], [$C_f [1":"2]_(AO)$], [$nu_(e, AO)$],
    [$mu^(-)$], [$00 bar.v -$ Dimonocton], [$1":"2":"8$], [$C_f [1":"2]_(AO)$], [$nu_(mu , AO)$],
    [$tau^(-)$], [$00 bar.v -$ Dimonnanyro], [$1":"2":"9_(upright("yro"))$], [$C_f [1":"2]_(AO)$], [$nu_(tau , AO)$],
    [$B^(plus.minus)$], [Ditrion debris map], [$3":"2":"6$], [$C_f [3":"2]_(AO)$], [$nu_(B, AO)$],
    [$B^0$], [Ditrion debris map], [$3":"2":"6$], [$C_f [3":"2]_(AO)$], [$nu_(B, AO)$],
    [$B_s^0$], [lifted Ditrion map], [$3":"2":"8$], [$C_f [3":"2]_(AO)$], [$nu_(B_s , AO)$],
    [$B_c^(plus.minus)$], [lifted Ditrion map], [$3":"2":"10$], [$C_f [3":"2]_(AO)$], [$nu_(B_c , AO)$],
    [$p^(+)$], [Tritriohexon map], [$3":"3":"6$], [$C_f [3":"3]_(AO)$], [$nu_(p, AO)$],
    [$n^0$], [Tetratriohexon map], [$3":"4":"6$], [$C_f [3":"4]_(AO)$], [$nu_(n, AO)$],
    bottomrule,
  )
}
  ],
  caption: [A$Omega$ field-map table.],
) <tab:manual-ao-field-value-table>



#aod-provenance[#mainappendix("main:app:ao-field-fractal-properties")\; #mainsection("main:subsec:curling-curl-support-forms").]


#aod-remark[The manual declares measured-sector maps such as $e^(-) arrow.r.bar 00 bar.v -$ Dimonhexon. These maps are carried by manual comparison records; #tabref("tab:ao-field-fractal-properties") lists the A$Omega$ field-property calculations.]

#aod-paragraph[Falsification: support degeneracy and held-out discipline.]
The displayed $B^(plus.minus)$ and $B^0$ rows share the same retained support $3":"2":"6$.
Any mass map using support scalar $R D = 21$ alone cannot distinguish those two targets;
a rest-energy application must bind additional shell-seat state with a matched
nondegeneracy witness (supplied below via #raw("RC-028")) or declare limited resolution.
A target is held out only when its exclusion from construction, selection, and
calibration is explicitly bound.


== Boundary-full SADAR rest-energy closures and collision-shedding debris <manual:rest:boundary-sadar-debris>

#aod-paragraph[Setup and engine verification.]
All ten rest-energy and collision-shedding debris carriers in
#tabref("tab:manual-ao-field-value-table") and
#secref("manual:tritrioseptyro-higgs-support-fixture") execute in pure zero-float
#raw("TritWord")/#raw("TritRatio") arithmetic without hardcoded winners or asserted
slot literals via the #raw("boundary_sadar") sector
(#raw("python3 -B -m manual.engine --sector boundary_sadar") and
#raw("aod-core --verify-vectors --check-zero-float")) across vectors #raw("RC-027")
(#raw("sadar_pp_tau_five_boundary")), #raw("RC-028")
(#raw("sadar_hadron_debris_and_higgs_saddle")), #raw("RC-029")
(#raw("sadar_rest_energy_atlas")), and quarantined external target-rate verification
#raw("SD-007") (#raw("sadar_rest_energy_qext")). Their topological regimes partition
into four boundary classes (Figure #bare-ref("fig:manual-collision-debris-feynman")):

1. *Seated inner even closures ($X_(upright("shedding")) = 0$, #raw("RC-029")):* On even support enclosures $sans("C")_6$ and $sans("C")_8$, Dimonhexon ($e^(-)$, $1":"2":"6$, $R D = 9$), Dimonocton ($mu^(-)$, $1":"2":"8$, $R D = 9$), Tritriohexon ($p^(+)$, $3":"3":"6$, $R D = 61$), and Tetratriohexon ($n^0$, $3":"4":"6$, $R D = 137$) close internally without shedding surplus, preserving exact native reflection-duration ratios $R D(3":"3) slash R D(1":"2) = 61 slash 9$ and $R D(3":"4) slash R D(3":"3) = 137 slash 61$.

2. *Five-boundary SADAR collision-shedding stack for Tau ($1":"2":"9_(upright("yro"))$ Dimonnanyro, #raw("RC-027")):* Declare the ordered boundary stack $B_(upright("hard")) arrow.r B_(tau) arrow.r B_(upright("shed")) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext"))$ (Figure #bare-ref("fig:manual-tau-five-boundary-sadar"), #tabref("tab:manual-tau-five-boundary-trace")).
   - *Hard cavity ($B_(upright("hard"))$):* Opposing #raw("pp") $3":"3":"6 + 3":"3":"6$ baryon streams couple across #raw("BETWEEN") $E_2$ duon chiral flips (#raw("window_duons = 3"), #raw("lead_lag = 8")), achieving early coupling at cut $1$ with exact raw cut accounting #raw("raw_cuts = 28 = 11 + 17"): live #raw("TritWord.burn_contiguous_dwell(keep_single_dwell=False)") burns $17$ optional $0_D$ (#raw("00")) dwell lanes while preserving structural $0_H$ (#raw("11")) hinges, leaving $11$ symmetry-quotient cuts ($17$ chiral flips, total attention $24 slash 5$, and moving-boundary Stokes tally $18 - 22 + 3 = - 1$). Removing #raw("BETWEEN") duon coupling (#raw("duons = 0")) yields the sterile negative control, remaining uncoupled through cut $58$ ($48$ H1 moves, $16$ structural $0_H$ hinges, zero chiral flips, $X_(upright("shedding")) = 0$).
   - *Lepton pocket competition ($B_(tau)$):* Evaluating the full $1":"2":"L$ family ($R D = 9$, $C_3 = 3$) across $L in brace.l 2, 6, 7, 8, 9, 10 brace.r$, even windows $1":"2":"2$, $1":"2":"6$, and $1":"2":"8$ close internally ($X_(upright("shedding")) = 0$); short odd window $1":"2":"7$ retains incomplete overhang $Q^D = 6$ with $sans("C")_8$ deficit $Delta^(upright("close")) = - 3$; window $1":"2":"10$ clips at $rho^D_(omega) = min (9, 10) = 9$ and closes on $sans("C")_(10) = 27$ ($X_(upright("shedding")) = 0$); and $1":"2":"9_(upright("yro"))$ uniquely exhausts full Dimonon duration ($Q^D = 0$) while exceeding $sans("C")_8 = 24$ with positive shedding surplus $X_(upright("shedding")) = 27 - 24 = 3$.
   - *Derived $50$-microslot $Q_4 times mu$ impedance rotor ($B_(upright("shed")) arrow.r B_(upright("sensor"))$):* Instead of asserting slot literals, the deterministic $50$-microslot $Q_4 times mu$ impedance rotor (4D capacity $4 times 50 = 200$) steps across the native reflection-duration ladder $R D = 9 arrow.r 61 arrow.r 137$. Stage 1 at $B_(upright("shed"))$ ($1":"2 arrow.r 3":"3$, $Delta R D = 61 - 9 = 52$) dynamically produces exact $(13 slash 50, 37 slash 50)$ for inner endoshedding versus outward exoshedding (#raw("_Exo")). Stage 2 at the passive #raw("ReadOnly") $3":"4":"6$ sensor wall $B_(upright("sensor"))$ ($3":"3 arrow.r 3":"4$, $Delta R D = 137 - 61 = 76$, zero observer back-reaction onto the cavity) dynamically produces conditional #raw("_Exo") fractions $(19 slash 50, 31 slash 50)$ for visible seating versus unseated traversal (exact missing burden $op("miss")_(tau) = 31 slash 50$). Their two-stage product gives exact $2500$-slot conservation $(650 slash 2500, 1850 slash 2500)$ for endoshedding versus #raw("_Exo") and $(703 slash 2500, 1147 slash 2500)$ for visible versus unseated traversal ($650 + 703 + 1147 = 2500$, conditional #raw("_Exo") ratios $703 slash 1850 = 19 slash 50$ and $1147 slash 1850 = 31 slash 50$) along the witness-ordered recipient lattice #raw("emitted -> delivered -> accepted -> seated -> closed_origin") ($Delta op("bip") = 0$) #raw("-> reclosed") ($Delta op("bip") = + 1$). Quarantined target comparison enters only at $B_(upright("ext")) = sans("Q")_(upright("ext"))$ (#raw("SD-007")).

3. *Core-starvation $3":"3 arrow.r 3":"2$ Ditrion collision-shedding debris ($R D = 21$, #raw("RC-028") and #raw("RC-029")):* When a hard baryon collision pocket sheds one inner branch role from $3":"3$ ($Pi = 30$, $R D = 61$) into $3":"2$ Ditrion support ($Pi = 2^3 + 2 = 10$, $R D = 21$), the debris enters even enclosures as transient meson remnants (#raw("rest_energy_sadar_debris_atlas.csv"), vectors #raw("RC-028") and #raw("RC-029")). On $3":"2":"6$, support scalar $R D = 21$ alone is degenerate between $B^(plus.minus)$ and $B^0$; shell-dressing chirality in #raw("ChiralPair4") resolves $B^(plus.minus)$ as seated duad $E_2^(plus.minus)$ ($chi_(upright("shell")) = plus.minus 1$, structural $0_H$ present) and $B^0$ as open-seat duon $E_2^0$ ($chi_(upright("shell")) = 0$, structural $0_H$ absent). Under higher collision-pocket pressure, exoshedding lifts the $3":"2$ Ditrion core across adjacent even enclosures $3":"2":"6 arrow.r 3":"2":"8$ ($B_s^0$, $P^D_(upright("sup")) = 40$, $Q^D_(upright("sup")) = 65$) $arrow.r 3":"2":"10$ ($B_c^(plus.minus)$, $P^D_(upright("sup")) = 50$, $Q^D_(upright("sup")) = 55$).

4. *Symmetric $sans("C")_6 slash sans("C")_8$ baryon-overlap saddle ($3":"3":"7_(upright("yro"))$, #raw("RC-028")):* Two-baryon $3":"3 + 3":"3$ overlap midpoint selection is audited in the Tritrioseptyro Higgs-support diagnostic below.


#figure(
  kind: image, [
#include "../../lib/figures/manual/tau_five_boundary_sadar_setup.typ"
  ],
  caption: [Five-boundary A$Omega$D SADAR stack $B_(upright("hard")) arrow.r B_(tau) arrow.r B_(upright("shed")) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext"))$ for $1":"2":"9_(upright("yro"))$ Dimonnanyro (#raw("RC-027"), #raw("tau_five_boundary_sadar_trace.csv")).],
) <fig:manual-tau-five-boundary-sadar>


#figure(
  kind: image, [
#include "../../lib/figures/manual/collision_shedding_debris_feynman.typ"
  ],
  caption: [Boundary-Feynman branching of inner even closures (#raw("RC-029")), $3":"3":"7_(upright("yro"))$ overlap-saddle selection and $3":"2$ Ditrion core-starvation debris (#raw("RC-028")), and $1":"2":"9_(upright("yro"))$ odd-window lepton shedding (#raw("RC-027")) into the witness-ordered recipient event lattice.],
) <fig:manual-collision-debris-feynman>


#figure(
  kind: table, [
#{
  let rows = csv("/manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv", row-type: dictionary)
  let wrap-id(s) = (
    s.replace("_", "_\u{200b}")
     .replace("->", "->\u{200b}")
     .replace("+", "+\u{200b}")
  )
  set text(size: 7.5pt)
  show raw: set text(size: 6.7pt)
  set par(justify: false, leading: 0.42em)
  table(
    columns: (1.10fr, 0.38fr, 0.45fr, 0.42fr, 0.42fr, 0.58fr, 0.58fr, 1.15fr, 1.42fr, 3.50fr),
    align: (left, right, right, right, right, right, right, right, right, left),
    inset: (x: 2.8pt, y: 2.9pt),
    table.header(
      toprule,
      [Candidate], [$L$], [$rho^D_(omega)$], [$P^D$], [$Q^D$], [$C_(upright("close"))$], [$X_(upright("shed"))$], [Endo / Exo], [Vis / Miss $|_(upright("Exo"))$], [Boundary stack & SADAR verdict],
      midrule,
    ),
    ..rows.map(r => (
      [#raw(wrap-id(r.candidate))],
      [#r.window_L],
      [#r.rhoD_omega],
      [#r.PD],
      [#r.QD],
      [#r.C_close],
      [#r.X_shedding],
      [#r.endo_retained_frac \ #r.exo_outward_frac],
      [#r.sensor_visible_cond_exo \ #r.sensor_missing_cond_exo],
      [#raw(wrap-id(r.boundary_chain)) \ #raw(wrap-id(r.sadar_verdict))],
    )).flatten(),
    bottomrule,
  )
}
  ],
  caption: [Engine-bound five-boundary SADAR competition table (#raw("RC-027"), live from #raw("manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv")).],
) <tab:manual-tau-five-boundary-trace>



== Electron external map <manual:rest:electron-external-map>

#aod-paragraph[Specialization.]
The electron comparison record is a manual map from the measured-sector electron to the A$Omega$ Dimonhexon support:

#math.equation(block: true, numbering: none, $ e^(-) arrow.r.long.bar 00 bar.v - med upright("Dimonhexon") equiv 00 bar.v - med (1":"2":"6), wide C_f [1":"2]_(AO) . $)

The charge-orientation tag is

#math.equation(block: true, numbering: none, $ q_(upright("ext")) (e^(-) ) = - 1, wide Q_(upright("ext")) (e^(-) ) = - e. $)

The rest-energy comparison target remains quarantined at $B_(upright("ext")) = sans("Q")_(upright("ext"))$ (#raw("SD-007")):

#math.equation(block: true, numbering: none, $ E^(upright("tar"))_e = 0.51099895069 upright("MeV"), wide sigma_(E,e) = 1.6 times 10^(- 10) upright("MeV"). $)

#aod-literature-note[Electron mass-energy: NIST CODATA #aod-cite("nist-electron-mass-energy"), SI defining constants: BIPM #aod-cite("bipm-si-defining-constants").]

#aod-remark[The $00 bar.v -$ tag is a manual measured-sector charge/orientation map carried by the manual comparison record.]


== Measured rest-energy target records <manual:rest:measured-comparison-analysis>

#aod-paragraph[Quarantined external comparison (#raw("SD-007")).]
External comparison enters strictly at $B_(upright("ext")) = sans("Q")_(upright("ext"))$.
For records with declared targets,

#math.equation(block: true, numbering: none, $ E_(x,upright("ext")) = K_(upright("ext")) nu_(x, AO) , wide Delta E_x = E_(x,upright("ext")) - E_x^(upright("tar")) , $)

#math.equation(block: true, numbering: none, $ epsilon_x^(upright("sgn")) = 100 frac(Delta E_x, E_x^(upright("tar"))), wide bar.v epsilon_x bar.v = bar.v epsilon_x^(upright("sgn")) bar.v , wide z_(x,upright("target")) = frac(Delta E_x, sigma_(E,x)). $)

Vector #raw("SD-007") (#raw("sadar_rest_energy_qext")) verifies exact BIPM 2019 SI
rational $K_(upright("ext"))$ target-rate inversion and zero round-trip
$eta_(upright("ext"))$ residual across all nine measured target rows below (tabulated
alongside native invariants in #raw("rest_energy_sadar_debris_atlas.csv")).

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, left, left),
    table.header(
      toprule,
      [Record], [Target [MeV]], [$sigma_E$ [MeV]], [Unit], [Source],
      midrule,
    ),
    [$e$], [$0.51099895069$], [$1.6 times 10^(- 10)$], [MeV], [NIST CODATA],
    [$mu$], [$105.6583755$], [$2.3 times 10^(- 6)$], [MeV], [NIST CODATA],
    [$tau$], [$1776.86$], [$0.12$], [MeV], [NIST / PDG target record],
    [$B^(plus.minus)$], [$5279.41$], [$0.07$], [MeV], [PDG 2025],
    [$B^0$], [$5279.72$], [$0.08$], [MeV], [PDG 2025],
    [$B_s^0$], [$5366.93$], [$0.10$], [MeV], [PDG 2025],
    [$B_c^(plus.minus)$], [$6274.47$], [$0.32$], [MeV], [PDG 2025],
    [$p$], [$938.27208943$], [$2.9 times 10^(- 7)$], [MeV], [NIST CODATA],
    [$n$], [$939.56542194$], [$4.8 times 10^(- 7)$], [MeV], [NIST CODATA],
    bottomrule,
  )
}
  ],
  caption: [Measured rest-energy target records (quarantined $B_(upright("ext"))$ audit in #raw("SD-007")).],
) <tab:manual-measured-comparison-analysis>

#aod-provenance[#mainappendix("main:app:ao-field-fractal-properties")\;
#appref("manual:external-comparison").]

#aod-literature-note[Lepton/baryon targets: NIST CODATA #aod-cite("nist-electron-mass-energy,nist-muon-mass-energy,nist-tau-mass-energy,nist-proton-mass-energy,nist-neutron-mass-energy"), meson targets: PDG 2025 #aod-cite("pdg-bmeson-2025").]



== Tritrioseptyro Higgs-support diagnostic fixture <manual:tritrioseptyro-higgs-support-fixture>

#aod-paragraph[Setup and falsification boundary.]
The supplied candidate rows and scoring formula reproduce the internal ranking; they do
not supply the originating history producer, detector thresholds, or exposure history of
the scale/exponent choice. Recovering those artifacts remains this application's next
step before an independent prediction claim, and the freeze order below states the
declared evaluation order rather than a historical pre-exposure freeze.

Tritrioseptyro is the $3":"3":"7_(upright("yro"))$ Higgs-support prediction candidate
selected by the internal AFC trace. The AFC run produces the read-only trace rows;
A$Omega$ detectors read the trace and name the retained route status before joining to
the frozen external mass map $E_H = R D thin 2^(L + 4)$ MeV. Production-channel and
decay-channel residual tables carry the next comparison layer.

#math.equation(block: true, numbering: none, $ "AFC run" arrow.r.long "read-only trace" arrow.r.long #[A$Omega$ route-status naming]. $)

The trace is read-only for this record; feedback experiments require separately declared
write-back maps.

#aod-paragraph[Derivation.]
Declare the odd-window trion candidate set

#math.equation(block: true, numbering: none, $ cal(K)_H = brace.l 3":"1":"7,3":"1":"9,3":"2":"7,3":"2":"9, 3":"3":"7,3":"3":"9,3":"4":"7,3":"4":"9 brace.r . $)

For each candidate $K = (p,q,L)$, compute

#math.equation(block: true, numbering: none, $ Pi = q^p + q, wide R D = 2 Pi + 1, wide rho^D_(omega) = min (R D,L), $)

with scoped collision capacity

#math.equation(block: true, numbering: none, $ C_(3,H) = 3, $)

giving active window pressure and pending overhang

#math.equation(block: true, numbering: none, $ P^D_H & = C_(3,H) rho^D_(omega) , \ Q^D_H & = C_(3,H) max (0,R D - L). $)

#aod-paragraph[Specialization (#raw("RC-011") and #raw("RC-028")).]
The retained candidate is

#math.equation(block: true, numbering: none, $ K_H^(star) = 3":"3":"7_(upright("yro")) = upright("Tritrioseptyro"). $)

For Tritrioseptyro,

#math.equation(block: true, numbering: none, $ Pi = 30, wide R D = 61, wide rho^D_(omega) = 7, wide P^D_H = 21, wide Q^D_H = 162, $)

with symmetric residuals against adjacent even support-enclosure closures:

#math.equation(block: true, numbering: none, $ P^D_H - C_6 = + 3, wide P^D_H - C_8 = - 3. $)

The trace places Tritrioseptyro on the $C_6 slash C_8$ saddle with pressure residuals $+ 3$ and $- 3$ and pending overhang $Q^D_H = 162$.

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    table.header(
      toprule,
      [Candidate], [$R D$], [$P^D_H$], [saddle], [$Q^D_H$], [score],
      midrule,
    ),
    [$3":"3":"7_(upright("yro"))$], [$61$], [$21$], [$+ 3 slash - 3$], [$162$], [$0.00$],
    [$3":"2":"7_(upright("yro"))$], [$21$], [$21$], [$+ 3 slash - 3$], [$42$], [$1.58$],
    [$3":"3":"9_(upright("yro"))$], [$61$], [$27$], [$+ 3 slash 0$], [$156$], [$2.25$],
    [$3":"4":"7_(upright("yro"))$], [$137$], [$21$], [$+ 3 slash - 3$], [$390$], [$2.40$],
    [$3":"2":"9_(upright("yro"))$], [$21$], [$27$], [$+ 3 slash 0$], [$36$], [$2.89$],
    [$3":"1":"7_(upright("yro"))$], [$5$], [$15$], [$- 3 slash - 9$], [$0$], [$3.00$],
    [$3":"4":"9_(upright("yro"))$], [$137$], [$27$], [$+ 3 slash 0$], [$384$], [$3.59$],
    [$3":"1":"9_(upright("yro"))$], [$5$], [$15$], [$- 9 slash - 12$], [$0$], [$4.75$],
    bottomrule,
  )
}
  ],
  caption: [Higgs-support candidate ranking. This table carries the active trace coordinates used by the internal selection rule (#raw("RC-011")).],
) <tab:manual-higgs-internal-candidates>

The trace score is verified in exact zero-float rational arithmetic by vector
#raw("RC-011") (#raw("higgs_trace_score_and_freeze"), yielding $S_H (3":"3":"7) = 0$
versus runner-up $S_H (3":"2":"7) = 79 slash 50 = 1.58$) under the internal selection rule:

#math.equation(block: true, numbering: none, $ S_H (K) = frac(d_(upright("saddle")), 12) + frac(d_Q, 100) + frac(d_L, 2) + d_(upright("route")) , wide arg min_(K in cal(K)_H) S_H (K) = 3":"3":"7_(upright("yro")) . $)

#aod-noteblock("Source artifacts")[The score-component definitions and candidate rows are supplied under #raw("manual/data/higgs") as #raw("higgs_trace_score_formula.md") and #raw("higgs_trace_internal_candidates_selection.csv"), respectively.]

Alongside the legacy ranking formula $S_H (K)$, vector #raw("RC-028")
(#raw("sadar_hadron_debris_and_higgs_saddle"),
#raw("manual/data/boundary_sadar/higgs_baryon_overlap_saddle_scan.csv")) evaluates the
full $20$-candidate trion grid $3":"q":"L$ ($q in brace.l 1, 2, 3, 4 brace.r$,
$L in brace.l 6, 7, 8, 9, 10 brace.r$) without empirical overhang-band thresholds: exact
symmetric $sans("C")_6 slash sans("C")_8$ midpoint balance
$(P^D_H - sans("C")_6 ) + (P^D_H - sans("C")_8 ) = 0$ ($P^D_H = 21$) holds only on
$brace.l 3":"2":"7, 3":"3":"7, 3":"4":"7 brace.r$, and two-baryon $3":"3 + 3":"3$ parent
lineage conservation ($q = 3$) isolates $3":"3":"7_(upright("yro"))$ uniquely prior to
external map freeze.



#figure(
  kind: image, [
#include "../../lib/figures/manual/higgs_yro_saddle_signature.typ"
  ],
  caption: [Tritrioseptyro yro saddle signature. The internal AFC trace gives $P^D_H = 21$, placing the selected $3":"3":"7_(upright("yro"))$ candidate between $C_6 = 18$ and $C_8 = 24$ with residuals $+ 3$ and $- 3$.],
) <fig:manual-higgs-yro-saddle>



#figure(
  kind: image, [
#include "../../lib/figures/manual/higgs_tritrioseptyro_trace_flow.typ"
  ],
  caption: [Tritrioseptyro trace flow. The AFC run produces $Pi = 30$, $R D = 61$, $rho^D_(omega) = 7$, $P^D_H = 21$, and $Q^D_H = 162$. A$Omega$ names the detected $3":"3":"7_(upright("yro"))$ route status as Tritrioseptyro.],
) <fig:manual-higgs-trace-flow>



=== External mass map after candidate freeze <manual:higgs-external-map-after-freeze>

#aod-paragraph[Specialization (#raw("RC-011"), #raw("SD-004"), #raw("SD-005")).]
The external mass map is frozen strictly after the internal candidate is selected:

#math.equation(block: true, numbering: none, $ E_H^(lr((0))) [upright("MeV")] = R D_H thin 2^(L + 4) . $)

For Tritrioseptyro (verified in exact rational arithmetic by #raw("RC-011") as
$15616 slash 125 thin upright("GeV")$),

#math.equation(block: true, numbering: none, $ E_H^(lr((0))) = 61 dot.op 2^(11) upright("MeV") = 124928 upright("MeV") = 124.928 upright("GeV"). $)

Declared LHC Higgs mass targets enter strictly after candidate and map freeze. Each
comparison row reports $Delta E$, absolute percent error $bar.v epsilon bar.v$, and
target-only pull $z_(upright("target")) = Delta E slash sigma_(upright("target"))$,
with exact rational half-even $6$-decimal display rounding audited by #raw("SD-004")
(CMS $H arrow.r 4 ell$: $Delta E = - 14 slash 125 thin upright("GeV")$,
$z = - 14 slash 15 approx - 0.933333$) and #raw("SD-005") (ATLAS
$H arrow.r gamma gamma$: $Delta E = - 73 slash 250 thin upright("GeV")$,
$z = - 73 slash 35 approx - 2.085714$).

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.header(
      toprule,
      [Quantity], [Value], [Record],
      midrule,
    ),
    [$K_H^(star)$], [$3":"3":"7_(upright("yro"))$], [frozen internal candidate],
    [$R D_H$], [$61$], [frozen internal accessor],
    [$L$], [$7$], [declared odd window],
    [$E_H^(lr((0)))$], [$61 dot.op 2^(11) thin upright("MeV") = 124.928 thin upright("GeV")$], [external map after freeze (#raw("RC-011"))],
    bottomrule,
  )
}
  ],
  caption: [Frozen external map for Tritrioseptyro.],
) <tab:manual-higgs-external-map>


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    table.header(
      toprule,
      [Target], [Mass [GeV]], [$sigma$ [GeV]], [$Delta E$ [GeV]], [$bar.v epsilon bar.v$ [%]], [$z_(upright("target"))$],
      midrule,
    ),
    [ATLAS+CMS Run-1 combined], [$125.09$], [$0.24$], [$- 0.162$], [$0.1295$], [$- 0.675$],
    [CMS $H arrow.r 4 ell$], [$125.04$], [$0.12$], [$- 0.112$], [$0.0896$], [$- 0.933$],
    [ATLAS Run-1+2 combined], [$125.11$], [$0.11$], [$- 0.182$], [$0.1455$], [$- 1.655$],
    [ATLAS $H arrow.r gamma gamma$], [$125.22$], [$0.14$], [$- 0.292$], [$0.2332$], [$- 2.086$],
    bottomrule,
  )
}
  ],
  caption: [LHC mass comparison after frozen external map (rounded display verified by #raw("SD-004") and #raw("SD-005")).],
) <tab:manual-higgs-lhc-comparison>


#figure(
  kind: image, [
#include "../../lib/figures/manual/higgs_mass_comparison.typ"
  ],
  caption: [Tritrioseptyro mass comparison. The frozen external map $E_H = R D thin 2^(L + 4)$ MeV sends the selected candidate to $124.928 thin upright("GeV")$. Target records enter as declared external comparison rows.],
) <fig:manual-higgs-mass-comparison>


#aod-paragraph[Falsification and external data-comparison record.]
The four target rows overlap in experiment, run, or channel, so their pulls are not four
independent tests; a joint test requires shared covariance and explicit model/map
uncertainty. The internal trace selects $K^(star)_H = 3":"3":"7_(upright("yro"))$ with
frozen map

#math.equation(block: true, numbering: none, $ E_H^(lr((0))) = R D_H 2^(L + 4) = 61 dot.op 2^(11) thin upright("MeV") = 124.928 thin upright("GeV"). $)

Table #bare-ref("tab:manual-higgs-lhc-comparison") records the declared Higgs mass-input rows, their quoted uncertainties, and the resulting $Delta E$, $bar.v epsilon bar.v$, and $z_(upright("target"))$ coordinates. The mapped value $124.928 thin upright("GeV")$ lies within $1 sigma$ of the ATLAS+CMS Run-1 combined mass record and the CMS Run-2 $H arrow.r 4 ell$ mass record while remaining a target-only diagnostic. Production-channel and decay-channel residual tables carry the next comparison layer.

#aod-provenance[#mainsection("main:subsec:yro-odd-window-route-status")\; #mainappendix("main:app:ao-field-fractal-properties")\; #tabref("tab:manual-higgs-internal-candidates")\; #tabref("tab:manual-higgs-external-map").]

#aod-literature-note[ATLAS+CMS Run-1 combined mass #aod-cite("atlas-cms-higgs-run1"). CMS $H arrow.r 4 ell$ mass #aod-cite("cms-hig-21-019"). ATLAS combined Run-1+Run-2 mass #aod-cite("atlas-higgs-mass-combined-2023"). ATLAS diphoton mass #aod-cite("atlas-higgs-diphoton-2023").]
