// Native Typst port of manual/sections/02_hydrogen_facing_shell_tests.tex (verbatim scientific content).
#import "../preamble.typ": *

= Hydrogen-facing Shell Tests <manual:hydrogen-shell-tests>



#aod-paragraph[Calculation card.]
The declared signed shell ladder gives exact transition differences and
ratios. The wavelength rows are carried external comparisons, sharing each
series baseline; their display precision is not a measurement uncertainty.
This application's source adapter still needs exact source rows, observed
versus Ritz and line/component conventions, uncertainty semantics and
covariance. The common method is #secref("manual:calculation-spine")\; the
existing ratio audit checks the stated arithmetic only.




== Shared hydrogen-facing shell declaration <manual:hydrogen:scope>


#aod-noteblock("Scope")[This section declares a signed shell comparison ladder,
computes its exact transition differences, and then records
wavelength/frequency/energy comparisons.]


#aod-noteblock("Data-support class")[Hydrogen shell tests instantiate D0 exact shell-ratio fixtures and O0 shell observable-map comparisons. Error quantities are shell-ratio or spectral-map residuals.]


The shared declaration is

#math.equation(block: true, numbering: none, $ bold(upright(a))_H tack.r (F_H ,R_H , partial R_H , omega_H ), wide B_H = ( partial F_H , omega_H ). $)

The shell family is indexed by an integer shell number

#math.equation(block: true, numbering: none, $ S_n , wide n in bb(Z)_(gt.eq 1) . $)

For the hydrogen-facing comparison records, the normalized shell-pressure ladder is declared by

#math.equation(block: true, numbering: none, $ hat(P)^D_(S_n) := - frac(1, n^2). $)

For a downward transition $n arrow.r m$, with $n > m$, declare the released normalized pressure magnitude

#math.equation(block: true, numbering: none, $ Delta hat(P)^D (n arrow.r m) := hat(P)^D_(S_n) - hat(P)^D_(S_m) = frac(1, m^2) - frac(1, n^2) > 0. $)

The signed state change is $hat(P)^D_(S_m) - hat(P)^D_(S_n) = - Delta hat(P)^D (n arrow.r m)$.



#aod-boxed($ "Hydrogen shell tests use a declared signed comparison ladder." $)


#aod-noteblock("Remark")[The normalized ladder is a manual comparison choice. The main-note pressure definition remains $p^D = C_3 rho^D_(omega)$.]



#aod-noteblock("Presentation policy")[The A$Omega$ ratios in the spectral tables are exact rational values. Decimal target ratios, wavelengths, frequencies, and percent errors are external presentation values. A $z$-score is recorded when the record carries an explicit uncertainty.]




#figure(
  kind: image, [
#include "../../lib/diagrams/hydrogen_shell_setup.typ"
  ],
  caption: [Hydrogen-facing shell-cycle ladder. The released shell-pressure magnitude is calculated before measured wavelengths and external energy-coordinate comparisons are attached.],
) <fig:manual-hydrogen-shell-setup>



== Shell-radius comparison <manual:hydrogen:radii>

The radius-ratio check records the standard shell scaling

#math.equation(block: true, numbering: none, $ frac(r_n, r_1) = n^2 . $)

The radius-ratio record is carried as a geometry comparison record.


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto),
    align: (center, center, center, center),
    table.header(
      toprule,
      [Shell], [A$Omega$ shell], [Ratio target], [Status],
      midrule,
    ),
    [1], [$S_1$], [$1$], [baseline],
    [2], [$S_2$], [$4$], [comparison record],
    [3], [$S_3$], [$9$], [comparison record],
    [4], [$S_4$], [$16$], [comparison record],
    bottomrule,
  )
}
  ],
  caption: [Hydrogen-facing shell-radius ratios.],
) <tab:manual-hydrogen-shell-radii>



== Shell-pressure table <manual:hydrogen:pressure-table>

The Balmer comparison records use downward transitions into $S_2$. The normalized released-pressure magnitudes are

#math.equation(block: true, numbering: none, $ Delta hat(P)^D (n arrow.r 2) = frac(1, 2^2) - frac(1, n^2). $)

The ratio to the $3 arrow.r 2$ record is

#math.equation(block: true, numbering: none, $ cal(R)_(n arrow.r 2) = frac(Delta hat(P)^D (n arrow.r 2), Delta hat(P)^D (3 arrow.r 2)). $)



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (center, center, center, center, center, center),
    table.header(
      toprule,
      [Line], [Transition], [$Delta hat(P)^D$], [A$Omega$ ratio], [Target ratio], [Error [%]],
      midrule,
    ),
    [H$alpha$], [$3 arrow.r 2$], [$5 slash 36$], [$1$], [$1.00000000$], [$0.000000$],
    [H$beta$], [$4 arrow.r 2$], [$3 slash 16$], [$27 slash 20$], [$1.34999075$], [$0.000685$],
    [H$gamma$], [$5 arrow.r 2$], [$21 slash 100$], [$189 slash 125$], [$1.51198839$], [$0.000768$],
    [H$delta$], [$6 arrow.r 2$], [$2 slash 9$], [$8 slash 5$], [$1.59999025$], [$0.000609$],
    bottomrule,
  )
}
  ],
  caption: [Hydrogen-facing Balmer released-pressure ratios. Targets are ratio comparisons against cited Balmer wavelengths.],
) <tab:manual-hydrogen-pressure-ratios>



== Shell-energy transitions <manual:hydrogen:energy-transitions>

The measured comparison is downstream. Given a cited vacuum wavelength $lambda$, the comparison sequence is

#math.equation(block: true, numbering: none, $ f = frac(c, lambda), wide E = h_(upright("ext")) f. $)

This sequence uses the quarantine of #appref("manual:external-comparison").


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (center, center, center, center, center),
    table.header(
      toprule,
      [Line], [Transition], [$lambda_(upright("vac"))$ [nm]], [$f$ [Hz]], [$E$ [eV]],
      midrule,
    ),
    [H$alpha$], [$3 arrow.r 2$], [$656.46$], [$4.56680465 times 10^(14)$], [$1.88867865$],
    [H$beta$], [$4 arrow.r 2$], [$486.27$], [$6.16514401 times 10^(14)$], [$2.54969869$],
    [H$gamma$], [$5 arrow.r 2$], [$434.17$], [$6.90495562 times 10^(14)$], [$2.85566019$],
    [H$delta$], [$6 arrow.r 2$], [$410.29$], [$7.30684292 times 10^(14)$], [$3.02186742$],
    bottomrule,
  )
}
  ],
  caption: [Hydrogen Balmer comparison targets. Wavelength records follow the NIST Atomic Spectra Database target convention.],
) <tab:manual-hydrogen-balmer-targets>





== Hydrogen spectral-series extension <manual:hydrogen:spectral-extension>


#aod-noteblock("Choice")[The Lyman and Paschen records use the same normalized shell-pressure ladder as the Balmer records. The destination shell $S_m$ is declared before each transition table. Ratio comparison is performed before wavelength, frequency, or energy export.]


For a fixed destination shell $S_m$ and a transition $n arrow.r m$, with $n > m$, define the A$Omega$-internal series ratio

#math.equation(block: true, numbering: none, $ cal(R)_(n arrow.r m, AO) = frac(Delta hat(P)^D (n arrow.r m), Delta hat(P)^D ((m + 1) arrow.r m)). $)

For wavelength comparison, use the inverse-wavelength relation

#math.equation(block: true, numbering: none, $ cal(R)^(lambda ,upright("tar"))_(n arrow.r m) = frac(lambda_((m + 1) arrow.r m), lambda_(n arrow.r m)). $)

Thus the A$Omega$-internal pressure ratio is compared against the measured inverse-wavelength ratio. external frequency coordinate and energy export remain downstream. The reference engine (#raw("manual/data/boundary_sadar/hydrogen_shell_exact_series.csv"), vector #raw("RC-031")) evaluates all Lyman ($m = 1$), Balmer ($m = 2$), and Paschen ($m = 3$) transitions in reduced exact rational arithmetic before wavelength comparison.


=== Lyman series <manual:hydrogen:lyman>

For Lyman records, the destination shell is $S_1$. The baseline is $2 arrow.r 1$, with

#math.equation(block: true, numbering: none, $ Delta hat(P)^D (2 arrow.r 1) = 1 - frac(1, 4) = frac(3, 4). $)



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: (center, center, center, center, center, center, center),
    table.header(
      toprule,
      [Line], [Transition], [$Delta hat(P)^D$], [A$Omega$ ratio], [$lambda_(upright("vac"))$ [nm]], [Target ratio], [Error [%]],
      midrule,
    ),
    [Ly$alpha$], [$2 arrow.r 1$], [$3 slash 4$], [$1$], [$121.56701$], [$1.00000000$], [$0.000000$],
    [Ly$beta$], [$3 arrow.r 1$], [$8 slash 9$], [$32 slash 27$], [$102.57225$], [$1.18518420$], [$0.000083$],
    [Ly$gamma$], [$4 arrow.r 1$], [$15 slash 16$], [$5 slash 4$], [$97.2537$], [$1.24999882$], [$0.000095$],
    [Ly$delta$], [$5 arrow.r 1$], [$24 slash 25$], [$32 slash 25$], [$94.9740$], [$1.28000305$], [$- 0.000239$],
    [Ly$epsilon$], [$6 arrow.r 1$], [$35 slash 36$], [$35 slash 27$], [$93.7803$], [$1.29629581$], [$0.000037$],
    [Limit], [$infinity arrow.r 1$], [$1$], [$4 slash 3$], [series limit], [$4 slash 3$], [audit record],
    bottomrule,
  )
}
  ],
  caption: [Hydrogen Lyman released-pressure ratio audit. Vacuum wavelength targets are downstream comparison records carried by the NIST-ASD target convention.],
) <tab:manual-hydrogen-lyman-ratios>



=== Paschen series <manual:hydrogen:paschen>

For Paschen records, the destination shell is $S_3$. Pa$alpha$, Pa$beta$, and Pa$epsilon$ carry the NIST Hydrogen Handbook air wavelengths. Pa$gamma$ and Pa$delta$ remain carried targets with source-row and medium bindings unverified. The baseline is $4 arrow.r 3$, with

#math.equation(block: true, numbering: none, $ Delta hat(P)^D (4 arrow.r 3) = frac(1, 9) - frac(1, 16) = frac(7, 144). $)



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: (center, center, center, center, center, center, center),
    table.header(
      toprule,
      [Line], [Transition], [$Delta hat(P)^D$], [A$Omega$ ratio], [$lambda_(upright("tar"))$ [nm]], [Target ratio], [Error [%]],
      midrule,
    ),
    [Pa$alpha$], [$4 arrow.r 3$], [$7 slash 144$], [$1$], [$1875.101$], [$1.00000000$], [$0.000000$],
    [Pa$beta$], [$5 arrow.r 3$], [$16 slash 225$], [$256 slash 175$], [$1281.807$], [$1.46285751$], [$- 0.000025$],
    [Pa$gamma$], [$6 arrow.r 3$], [$1 slash 12$], [$12 slash 7$], [$1093.808$], [$1.71428715$], [$- 0.000084$],
    [Pa$delta$], [$7 arrow.r 3$], [$40 slash 441$], [$640 slash 343$], [$1004.938$], [$1.86588725$], [$0.000105$],
    [Pa$epsilon$], [$8 arrow.r 3$], [$55 slash 576$], [$55 slash 28$], [$954.597$], [$1.96428545$], [$0.000013$],
    [Limit], [$infinity arrow.r 3$], [$1 slash 9$], [$16 slash 7$], [series limit], [$16 slash 7$], [audit record],
    bottomrule,
  )
}
  ],
  caption: [Hydrogen Paschen released-pressure ratio audit. Wavelengths are carried comparison targets with the source-medium bindings declared in this subsection.],
) <tab:manual-hydrogen-paschen-ratios>



=== Series-ratio audit <manual:hydrogen:series-audit>

Retain one source identity for the shared denominator when propagating the
ratios. Air wavelengths require source-bound vacuum conversion or a declared
model-to-air observation map, including refractive-index applicability and
uncertainty; $c slash lambda_(upright("air"))$ is not a vacuum frequency. Until
those bindings are supplied, the current inverse-wavelength ratios remain
carried-coordinate diagnostics, with physical uncertainty unresolved.


#aod-noteblock("Audit")[A spectral-series record carries the destination shell $S_m$, the computed $Delta hat(P)^D (n arrow.r m)$, and the inverse-wavelength ratio $lambda_((m + 1) arrow.r m) slash lambda_(n arrow.r m)$.]


#aod-provenance[#secref("subsec:shared-shell-path-declaration")\;
#appref("manual:external-comparison").]


#aod-literature-note[Hydrogen spectral-line targets: NIST Atomic Spectra Database #aod-cite("nist-asd")\; Paschen Pa$alpha$, Pa$beta$, Pa$epsilon$ air rows: NIST Hydrogen Handbook #aod-cite("nist-hydrogen-handbook").]




== Error audit <manual:hydrogen:error-audit>

For a transition record $x$, record

#math.equation(block: true, numbering: none, $ Delta cal(R)_x = cal(R)_(x, AO) - cal(R)_x^(upright("tar")) , wide epsilon_x^(upright("sgn")) = 100 frac(Delta cal(R)_x, cal(R)_x^(upright("tar"))). $)

The ratio audits in #tabref("tab:manual-hydrogen-pressure-ratios"), #tabref("tab:manual-hydrogen-lyman-ratios") and #tabref("tab:manual-hydrogen-paschen-ratios") use this formula. Energy errors may be recorded only after the wavelength target and external conversion are declared.


== Audit hooks <manual:hydrogen:audit-hooks>


#aod-noteblock("Audit")[A hydrogen-facing shell record carries the released-pressure magnitude before external comparison, its ratio record, and the wavelength target with its declared source-medium binding.]


#aod-provenance[#secref("subsec:shared-shell-path-declaration")\;
#appref("manual:external-comparison")\;
#secref("manual:hydrogen:scope").]


#aod-literature-note[Hydrogen Balmer targets: NIST Atomic Spectra Database #aod-cite("nist-asd").]
