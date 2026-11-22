// Native Typst port of manual/sections/05_solar_system_field_tests.tex (verbatim scientific content).
#import "../preamble.typ": *

= Solar Observable-Map Fixtures <manual:solar-system-field-tests>



#aod-paragraph[Calculation card.]
The Sun/body/window declarations and carried O0 values below give residual
arithmetic, not a replayed native solar evaluator. The $42.98$ perihelion
and $1.75$ bending references are theory benchmarks. The redshift record
separately identifies a reference prediction and a measured estimate with
uncertainty. This application must supply its native construction, observable
map, source certificates and uncertainty before physical prediction; see
#secref("manual:calculation-spine").



#aod-noteblock("Scope")[This section carries solar-system observable-map comparison fixtures. Each record declares its solar-system scope, names the observable map, carries a comparison value, attaches an external reference target, and records residual, percent error, source citation, and audit.]


#aod-noteblock("Data-support class")[Solar records are O0 observable-map fixtures. Each row records map value, target, residual/error, and citation inside the declared observable-map support class.]



== Shared solar-system declaration <manual:solar:shared>

Declare a solar field scope

#math.equation(block: true, numbering: none, $ bold(upright(a))_(dot.o) tack.r (F_(dot.o) ,R_(dot.o) , partial R_(dot.o) , omega_(dot.o) ), wide B_(dot.o) = ( partial F_(dot.o) , omega_(dot.o) ). $)

For a body, signal, or transfer record $x$, declare a comparison boundary/window

#math.equation(block: true, numbering: none, $ B_x = ( partial F_x , omega_x ). $)

Each record carries a frozen O0 map-value comparison and its external reference target.


#figure(
  kind: image, [
#include "../../lib/diagrams/solar_system_spine.typ"
  ],
  caption: [Solar-system observable-map comparison spine. The records carry map values, targets, residuals, percent errors, and source citations.],
) <fig:manual-solar-system-spine>



#aod-boxed($ "Solar-system records carry O0 observable-map comparisons." $)



== SADAR observable bridge <manual:solar:observable-export-bridge>

Native solar-system evaluation requires a Sun-field cycle family evaluated by $SADARop_B$ and a declared observable comparison map with signature

#math.equation(block: true, numbering: none, $ cal(O)_(x, AO) = cal(G)_x [ R C D, rho^D , rho^D_(omega) ,p^D , phi.alt ,bold(upright(A))_F ,J^D_(partial R) ;B_x ] . $)

The three observable-map comparison fixtures record the following map signatures:

#math.equation(block: true, numbering: none, $ Delta pi.alt_(upright("Hg"), AO) = cal(G)_(upright("peri")) [ bold(upright(A))_(F_(dot.o)) (B_(upright("Hg")) ), J^D_(partial R) ( omega_(upright("cy")) ;B_(upright("Hg")) ) ] , $)


#math.equation(block: true, numbering: none, $ delta_(dot.o , AO) = cal(G)_(upright("bend")) [ bold(upright(A))_(F_(dot.o)) (B_(upright("bend")) ), J^D_(partial R) ( omega_(upright("bend")) ;B_(upright("bend")) ) ] , $)


#math.equation(block: true, numbering: none, $ z_(dot.o , AO) = cal(G)_(upright("red")) [ bold(upright(A))_(F_(dot.o)) (B_(upright("red")) ), J^D_(partial R) ( omega_(upright("red")) ;B_(upright("red")) ) ] . $)

The rows below carry O0 comparison values and residual arithmetic. Map definitions and evaluated native $SADARop_B$ input certificates are not supplied for these records.
The Mercury physical-prediction gate therefore remains unevaluated. Its
future native derivation must not take the general-relativistic benchmark
as a premise; a measured comparison also needs its estimator, source locator,
reduction assumptions and uncertainty.



== Observable-map comparison table <manual:solar:observable-map-table>



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.header(
      toprule,
      [Record], [A$Omega$ value], [Target], [Residual], [Abs. percent error],
      midrule,
    ),
    [Mercury perihelion], [$42.9799$ arcsec/cy], [$42.98$ arcsec/cy], [$- 0.0001$ arcsec/cy], [$0.0002327 "%"$],
    [Solar light bending], [$1.75001$ arcsec], [$1.75$ arcsec], [$0.00001$ arcsec], [$0.0005714 "%"$],
    [Solar redshift], [$2.11996 times 10^(- 6)$], [$2.12 times 10^(- 6)$], [$- 4.0 times 10^(- 11)$], [$0.001887 "%"$],
    bottomrule,
  )
}
  ],
  caption: [Solar-system observable-map comparison records (carried O0 values).],
) <tab:manual-solar-observable-map-results>



#figure(
  kind: image, [
#image("/manual/figures/solar_calculated_vs_target.png", width: 82%)
  ],
  caption: [Solar-system carried observable-map values versus declared targets. The vertical axis is logarithmic; each record is compared only within its own unit/scale.],
) <fig:manual-solar-calculated-target>



#figure(
  kind: image, [
#image("/manual/figures/solar_percent_error.png", width: 82%)
  ],
  caption: [Solar-system field tests: absolute percent error.],
) <fig:manual-solar-percent-error>



== Mercury perihelion window <manual:solar:mercury>

Declare

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("Hg")) tack.r (F_(upright("Hg")) ,R_(upright("orbit")) , partial R_(upright("peri")) , omega_(upright("cy")) ), wide B_(upright("Hg")) = ( partial F_(upright("Hg")) , omega_(upright("cy")) ). $)

The observable-map value is

#math.equation(block: true, numbering: none, $ Delta pi.alt_(upright("Hg"), AO) = 42.9799 upright("arcsec/century"). $)

The theoretical reference target is

#math.equation(block: true, numbering: none, $ Delta pi.alt_(upright("Hg"))^(upright("tar")) = 42.98 upright("arcsec/century"). $)


#math.equation(block: true, numbering: none, $ Delta_(pi.alt) = - 0.0001 upright("arcsec/century"), wide bar.v epsilon_(pi.alt) bar.v = 0.0002327 "%" . $)



#aod-literature-note[Mercury perihelion target: Will #aod-cite("will-mercury-2018").]



== Solar light-bending boundary <manual:solar:light-bending>

Declare

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("bend")) tack.r (F_(upright("signal")) ,R_(upright("path")) , partial R_(dot.o upright("limb")) , omega_(upright("bend")) ), wide B_(upright("bend")) = ( partial F_(upright("signal")) , omega_(upright("bend")) ). $)

The observable-map value is

#math.equation(block: true, numbering: none, $ delta_(dot.o , AO) = 1.75001 upright("arcsec"). $)

The theoretical reference target is

#math.equation(block: true, numbering: none, $ delta_(dot.o)^(upright("tar")) = 1.75 upright("arcsec"). $)


#math.equation(block: true, numbering: none, $ Delta_(delta) = 0.00001 upright("arcsec"), wide bar.v epsilon_(delta) bar.v = 0.0005714 "%" . $)



#aod-literature-note[Solar-limb light-bending target: NASA #aod-cite("nasa-1919-light-bending").]



== Solar redshift transfer boundary <manual:solar:redshift>

Declare

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("red")) tack.r (F_(upright("line")) ,R_(upright("surface")) , partial R_(upright("transfer")) , omega_(upright("red")) ), wide B_(upright("red")) = ( partial F_(upright("line")) , omega_(upright("red")) ). $)

The observable-map value is

#math.equation(block: true, numbering: none, $ z_(dot.o , AO) = 2.11996 times 10^(- 6) . $)

The target is

#math.equation(block: true, numbering: none, $ z_(dot.o)^(upright("tar")) = 2.12 times 10^(- 6) . $)


#math.equation(block: true, numbering: none, $ Delta_z = - 4.0 times 10^(- 11) , wide bar.v epsilon_z bar.v = 0.001887 "%" . $)

A separate external reference prediction is

#math.equation(block: true, numbering: none, $ v_z^(upright("tar")) = 633.1 upright("m/s"), $)

with the measured comparison

#math.equation(block: true, numbering: none, $ v_z^(upright("meas")) = 638 plus.minus 6 upright("m/s"). $)



#aod-literature-note[Solar gravitational-redshift reference prediction $633.1 upright("m/s")$ and measured comparison $638 plus.minus 6 upright("m/s")$: Heidelberg/ZAH #aod-cite("zah-solar-redshift").]



== Audit hooks <manual:solar:audit-hooks>


- Scope audit: each record declares $bold(upright(a)) tack.r (F,R, partial R, omega )$ and $B = ( partial F, omega )$.
- Comparison-fixture audit: each record includes observable-map value, target, residual, percent error, and status.
- Input audit: target values are cited in the record where they are used; residuals are computed from the declared observable-map value and declared target.




#aod-provenance[#secref("subsec:disoma-declaration")\;
#mainequation("main:eq:b-scoped-flux")\;
#mainequation("main:eq:sadar-attention-vector")\;
#mainequation("main:eq:window-clipped-rho")\;
#appref("manual:external-comparison").]
