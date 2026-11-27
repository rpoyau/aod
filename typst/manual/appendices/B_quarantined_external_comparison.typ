// Native Typst port of manual/appendices/B_quarantined_external_comparison.tex (verbatim scientific content).
#import "../preamble.typ": *

= Quarantined External Comparison <manual:external-comparison>



#aod-paragraph[Calculation card.]
The candidate rate, measured target energy and measured normalizer have
separate roles; $h_(upright("ext"))$ and $e$ are defining constants.
The declared unit/rate maps produce the inline Tau target coordinates.
Their normalizer is shared across forward and inverse maps. The audit below
checks comparison order and units; physical prediction still needs a bound
candidate and its uncertainty under #secref("manual:calculation-spine").




== Scope <manual:external-comparison:scope>

This appendix compares A$Omega$ outputs against external comparison coordinates. It does not import external units, constants, or symbols into the A$Omega$ calculation. The active calculation produces a candidate such as

#math.equation(block: true, numbering: none, $ nu_(x, AO) . $)

Only after that value is declared may an external comparison record use it:

#math.equation(block: true, numbering: none, $ Qext ( nu_(x, AO) ;cal(T)_x ). $)





== Presentation-numeric policy <manual:external-comparison:presentation-numeric-policy>

A$Omega$-internal arithmetic remains integer/rational. The decimals in this appendix are external comparison presentation values. Measured external values are carried with a declared uncertainty; exact defining constants are marked as exact. The external normalizer $eta_(upright("ext"))$ is measured, so uncertainty propagation for normalized rates may include both the target-energy uncertainty and the uncertainty of $eta_(upright("ext"))$.


== External comparison symbols <manual:external-comparison-symbols>

External constants and measured-sector units are named only inside this quarantine. The active A$Omega$ notation is unaffected by them.


=== Distance comparison

If a bip duration $Delta t_(upright("bip"))$ is declared, an external distance coordinate may be recorded as

#math.equation(block: true, numbering: none, $ d_(upright("ext")) = c thin n thin Delta t_(upright("bip")) , wide n in bb(Z)_(gt.eq 0) . $)

Here $c$ is an external defining constant in the comparison coordinate system.


=== Speed comparison

The active calculation may carry the exact integer pair

#math.equation(block: true, numbering: none, $ ( Delta q, Delta n), wide 0 lt.eq Delta q lt.eq Delta n, wide Delta n > 0. $)

The external speed coordinate is allowed only after the integer pair is declared:

#math.equation(block: true, numbering: none, $ beta_(upright("ext")) = frac(Delta q, Delta n), wide v_(upright("ext")) = beta_(upright("ext")) c. $)



=== Direction comparison

A direction comparison may record cycle count

#math.equation(block: true, numbering: none, $ N_(theta) = frac(Theta, 2 pi), wide 2 pi arrow.r.bar 1 upright("cycle"), wide 4 pi arrow.r.bar 2 upright("cycles"), $)

with an orientation sign

#math.equation(block: true, numbering: none, $ s_(theta) in brace.l - 1, + 1 brace.r . $)



=== Charge comparison

The active calculation carries integer orientation. The external charge coordinate may be recorded as

#math.equation(block: true, numbering: none, $ Q_(upright("ext")) = z e, wide z in bb(Z), $)

where $e$ is an external defining constant in the comparison coordinate system.


== Choice: external rate normalizer <manual:external-comparison:action-normalization>

Define the quarantined external rate normalizer

#math.equation(block: true, numbering: none, $ eta_(upright("ext")) := alpha_(upright("fs"))^(- 1) . $)

Use

#math.equation(block: true, numbering: none, $ alpha_(upright("fs"))^(- 1) = 137.035999177(21) $)

inside this appendix only. This symbol is external and does not set active A$Omega$ notation.

Define the external comparison coefficient

#math.equation(block: true, numbering: none, $ K_(upright("ext")) = frac(h_(upright("ext")) eta_(upright("ext")), 10^6 e) = 5.6673535511200 times 10^(- 19) upright("MeV") thin upright("s"). $)

The uncertainty inherited from $eta_(upright("ext"))$ is

#math.equation(block: true, numbering: none, $ sigma_(K, eta) = 8.68490216354 times 10^(- 29) upright("MeV") thin upright("s"). $)

Here $h_(upright("ext"))$ and $e$ are external exact defining constants, while $eta_(upright("ext"))$ is measured. The active A$Omega$ calculation does not use them.

Given a numeric A$Omega$ candidate $nu_(x, AO)$, the external energy-coordinate comparison is

#math.equation(block: true, numbering: none, $ E_(x,upright("ext")) [upright("MeV")] = K_(upright("ext")) nu_(x, AO) . $)



== Tau target record <manual:external-comparison:tau-target-normalization>

The measured-comparison record in #secref("manual:rest:measured-comparison-analysis"), #tabref("tab:manual-measured-comparison-analysis"), uses the measured target

#math.equation(block: true, numbering: none, $ E_(tau)^(upright("tar")) = 1776.86 upright("MeV"), wide sigma_E = 0.12 upright("MeV"). $)

The target in the external joule coordinate is

#math.equation(block: true, numbering: none, $ E_(tau ,J)^(upright("tar")) = 1776.86 times 10^6 e = 2.84684357388924 times 10^(- 10) upright("J"). $)

The external frequency coordinate is

#math.equation(block: true, numbering: none, $ f_(tau) = frac(E_(tau ,J)^(upright("tar")), h_(upright("ext"))) = 4.2964283646910 times 10^(23) upright("s")^(- 1) . $)

The quarantined external target rate is

#math.equation(block: true, numbering: none, $ nu_(tau ,upright("tar")) = frac(f_(tau), eta_(upright("ext"))) = 3.1352552544544 times 10^(21) upright("s")^(- 1) . $)

The target-energy contribution to the external target-rate uncertainty is

#math.equation(block: true, numbering: none, $ sigma_(nu ,E) = frac(0.12 times 10^6 e, h_(upright("ext")) eta_(upright("ext"))) = 2.11739039955 times 10^(17) upright("s")^(- 1) . $)

The contribution from the measured external normalizer is

#math.equation(block: true, numbering: none, $ sigma_(nu , eta) = nu_(tau ,upright("tar")) frac(0.000000021, 137.035999177) = 4.80460322389 times 10^(11) upright("s")^(- 1) . $)

At first order, assuming zero covariance between the target energy and
measured normalizer, the combined external target-rate uncertainty is

#math.equation(block: true, numbering: none, $ sigma_(nu ,upright("comb")) = sqrt(sigma_(nu ,E)^2 + sigma_(nu , eta)^2) = 2.11739039956 times 10^(17) upright("s")^(- 1) . $)



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, 1fr, auto, auto),
    align: (center, left, center, center),
    table.header(
      toprule,
      [$x$], [$op("def")(x)$], [$op("val")(x)$], [$op("unit")(x)$],
      midrule,
    ),
    [$E_(tau)^(upright("tar"))$], [declared measured target], [$1776.86$], [$upright("MeV")$],
    [$sigma_E$], [declared uncertainty], [$0.12$], [$upright("MeV")$],
    [$E_(tau ,J)^(upright("tar"))$], [$1776.86 times 10^6 e$], [$2.84684357388924 times 10^(- 10)$], [$upright("J")$],
    [$f_(tau)$], [$E_(tau ,J)^(upright("tar")) slash h_(upright("ext"))$], [$4.2964283646910 times 10^(23)$], [$upright("s")^(- 1)$],
    [$eta_(upright("ext"))$], [$alpha_(upright("fs"))^(- 1)$], [$137.035999177(21)$], [$1$],
    [$nu_(tau ,upright("tar"))$], [$f_(tau) slash eta_(upright("ext"))$], [$3.1352552544544 times 10^(21)$], [$upright("s")^(- 1)$],
    [$sigma_(nu ,E)$], [energy uncertainty contribution], [$2.11739039955 times 10^(17)$], [$upright("s")^(- 1)$],
    [$sigma_(nu , eta)$], [normalizer uncertainty contribution], [$4.80460322389 times 10^(11)$], [$upright("s")^(- 1)$],
    [$sigma_(nu ,upright("comb"))$], [combined uncertainty], [$2.11739039956 times 10^(17)$], [$upright("s")^(- 1)$],
    [$K_(upright("ext"))$], [$h_(upright("ext")) eta_(upright("ext")) slash (10^6 e)$], [$5.6673535511200 times 10^(- 19)$], [$upright("MeV") thin upright("s")$],
    [$sigma_(K, eta)$], [normalizer contribution to $K_(upright("ext"))$], [$8.68490216354 times 10^(- 29)$], [$upright("MeV") thin upright("s")$],
    bottomrule,
  )
}
  ],
  caption: [Tau target record in the quarantined external-comparison coordinate.],
)

Using the identical quarantined normalizer $K_(upright("ext")) = h_(upright("ext")) eta_(upright("ext")) slash (10^6 e)$, the reference engine (#raw("manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv"), vector #raw("SD-007")) evaluates the exact rational target rates $nu_(x, upright("tar")) = E_x^(upright("tar")) slash K_(upright("ext"))$ across all nine rest-energy target records ($0.000902$, $0.186433$, $3.135255$, $9.315477$, $9.316024$, $9.469905$, $11.071252$, $1.655574$, and $1.657856$ in units of $10^(21) thin upright("s")^(- 1)$ for $e^(-)$, $mu^(-)$, $tau^(-)$, $B^(plus.minus)$, $B^0$, $B_s^0$, $B_c^(plus.minus)$, $p^(+)$, and $n^0$), keeping SI defining constants and CODATA/PDG targets strictly inside $B_(upright("ext"))$.



== Audit <manual:external-comparison:falsification>

The same normalizer identity must be retained in a round trip:
$K_(upright("ext")) nu_(tau ,upright("tar")) = E_(tau)^(upright("tar"))$.
Its uncertainty cancels exactly in this algebraic composition. Treating
the two appearances of $eta_(upright("ext"))$ as independent would add a
spurious contribution; the joint route of
#secref("manual:scoped-errors-data-support") preserves that dependence.

F1. External-comparison audit records the active $nu_(x, AO)$ candidate before the external comparison.

F2. Speed-comparison audit records integer $Delta q$, integer positive $Delta n$, and $Delta q lt.eq Delta n$.

F3. Direction-cycle audit records direction relative to $2 pi = 1$ cycle.

F4. Charge-comparison audit records integer orientation before the external charge comparison.

F5. Quarantine audit records external constants, units, and measured-sector symbols only after the active A$Omega$ calculation.


#aod-provenance[#mainequation("main:eq:b-scoped-flux")\;
#mainequation("main:eq:sadar-attention-vector")\;
#secref("manual:exact-arithmetic-presentation")\;
#secref("manual:external-comparison-quarantine").]



#aod-literature-note[SI defining constants: BIPM #aod-cite("bipm-si-defining-constants"), inverse fine-structure constant: NIST CODATA #aod-cite("nist-alpha-inverse"), tau target: Zhang/PDG #aod-cite("zhang-tau-pdg"), DESY/Belle #aod-cite("desy-belle-tau").]



#aod-remark[The quarantined external-comparison appendix compares against A$Omega$ outputs. It does not import external constants or symbols into the A$Omega$ calculation.]



== Five-boundary $sans("Q")_(upright("ext"))$ firewall and six-tuple precision ledger <manual:qext:dec-quarantine-firewall>

At the terminal boundary $B_(upright("ext")) = sans("Q")_(upright("ext")) (nu_(x, AO) ; cal(T)_x )$ of every five-boundary stack, native $bb(Z) slash bb(Q)$ invariants from #secref("manual:rest-energy-prediction") — verified by vectors #raw("RC-027") (Tau $1":"2":"9_(upright("yro"))$ $50$-microslot rotor and shedding trace), #raw("RC-028") (core-starvation $3":"2$ Ditrion debris ladder and $3":"3":"7_(upright("yro"))$ Higgs midpoint saddle), and #raw("RC-029") (ten-carrier rest-energy atlas, $8160$ bit-window span versus $9104$ summed lineage closures) — project one-way into six-tuple precision records $(x_(upright("disp")) , u_x , op("unit")(x), op("src")(x), op("round")(x), op("scope")(x))$. External target-rate normalization and exact round-trip $eta_(upright("ext"))$ cancellation across all nine rest-energy target records are verified by vector #raw("SD-007") (#raw("manual/data/boundary_sadar/rest_energy_sadar_debris_atlas.csv")), while post-freeze exact rational half-even six-decimal Higgs LHC comparison displays and rounding residuals are verified by vectors #raw("SD-004") and #raw("SD-005"). In the round-trip expression $nu_(upright("sc")) = nu_(AO) slash eta_(upright("ext"))$ followed by $E_(upright("map")) = K_(upright("ext")) eta_(upright("ext")) nu_(upright("sc")) = K_(upright("ext")) nu_(AO)$, the external constant $eta_(upright("ext")) = alpha_(upright("fs"))^(- 1)$ cancels identically and adds zero native degrees of freedom. Under standing R04 S3 discipline, simulation-substrate and computational-calculus equivalence claims remain permanently quarantined outside Main ontology and native Manual derivations.


#figure(
  kind: image, [
#include "../../lib/figures/manual/qext_quarantine_firewall.typ"
  ],
  caption: [Quarantined external comparison firewall $B_(upright("ext")) = sans("Q")_(upright("ext")) (nu_(x, AO) ; cal(T)_x )$, six-tuple decimal precision record, exact $eta_(upright("ext"))$ cancellation, and standing R04 S3 quarantine (#raw("SD-007"), #raw("rest_energy_sadar_debris_atlas.csv")).],
) <fig:manual-qext-quarantine-firewall>


#figure(
  kind: table, [
#{
  set text(size: 8.0pt)
  set par(justify: false)
  table(
    columns: (9fr, 18fr, 16fr, 16fr, 9fr, 20fr, 12fr),
    align: (left, left, right, right, center, left, left),
    inset: (x: 3.2pt, y: 3.2pt),
    table.header(
      toprule,
      [Carrier], [Native $M_x$ ($R D$)], [$x_(upright("disp"))$], [$u_x$], [Unit], [Source], [Scope],
      midrule,
    ),
    [$e^(-)$], [$1":"2":"6$ ($9$)], [0.51099895069], [0.00000000016], [MeV], [CODATA-2022], [$sans("Q")_(upright("ext"))$],
    [$mu^(-)$], [$1":"2":"8$ ($9$)], [105.6583755], [0.0000023], [MeV], [CODATA-2022], [$sans("Q")_(upright("ext"))$],
    [$tau^(-)$], [$1":"2":"9_(upright("yro"))$ ($9$)], [1776.86], [0.12], [MeV], [PDG-2024], [$sans("Q")_(upright("ext"))$],
    [$p^(+)$], [$3":"3":"6$ ($61$)], [938.27208943], [0.00000029], [MeV], [CODATA-2022], [$sans("Q")_(upright("ext"))$],
    [$n^0$], [$3":"4":"6$ ($137$)], [939.56542194], [0.00000048], [MeV], [CODATA-2022], [$sans("Q")_(upright("ext"))$],
    [Higgs], [$3":"3":"7_(upright("yro"))$ ($61$)], [125090], [240], [MeV], [ATLAS+CMS Run-1], [$sans("Q")_(upright("ext"))$],
    bottomrule,
  )
}
  ],
  caption: [Six-tuple quarantined $sans("Q")_(upright("ext"))$ target-precision records paired with exact native support accessors (#raw("SD-007"), #raw("SD-004"), #raw("SD-005"), #raw("RC-027")–#raw("RC-029")).],
) <tab:manual-qext-precision-ledger>

