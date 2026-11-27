// Native Typst authority for Manual §10: hydrogen-facing shell tests, exact rational series (RC-031), and concentric shell wavelet D.E.C. ledger (RC-039).
#import "../preamble.typ": *

= Hydrogen-facing Shell Tests <manual:hydrogen-shell-tests>


#aod-paragraph[Setup and calculation card.]
The declared signed shell ladder generates exact zero-float D0 rational transition
differences and within-series ratios verified independently by reference-engine vectors
#raw("RC-031") (#raw("hydrogen_shell_exact_series.csv")) and #raw("RC-039")
(#raw("hydrogen_shell_dec_transitions.csv")) across the Lyman, Balmer, and Paschen
series before any external constant or scale enters. Carried wavelength, frequency, and
energy targets remain quarantined external O0 comparisons at
$B_(upright("ext")) = sans("Q")_(upright("ext"))$ sharing each series baseline; their
display precision is not a measurement uncertainty. Full experimental comparison still
requires a source adapter binding exact NIST-ASD / Hydrogen Handbook rows,
observed-versus-Ritz and air-versus-vacuum conventions, uncertainty semantics, and
shared-denominator covariance under #secref("manual:calculation-spine").


== Shared hydrogen-facing shell declaration <manual:hydrogen:scope>

#aod-noteblock("Scope")[This section declares a signed shell comparison ladder, derives its exact rational transition differences and series ratios in D0 arithmetic (#raw("RC-031"), #raw("RC-039")), and quarantines downstream NIST wavelength, frequency, and energy comparisons at $B_(upright("ext")) = sans("Q")_(upright("ext"))$.]

#aod-noteblock("Data-support class")[Hydrogen shell tests separate D0 exact rational shell-ratio fixtures (#raw("RC-031"), #raw("RC-039")) from O0 quarantined spectral observable-map comparisons. Error quantities are shell-ratio or spectral-map residuals.]

#aod-paragraph[Setup.]
Declare the hydrogen-facing shell scope and integer shell family:

#math.equation(block: true, numbering: none, $ bold(upright(a))_H tack.r (F_H ,R_H , partial R_H , omega_H ), wide B_H = ( partial F_H , omega_H ), wide S_n , med n in bb(Z)_(gt.eq 1) . $)

For the hydrogen-facing comparison records, declare the normalized signed shell-pressure ladder

#math.equation(block: true, numbering: none, $ hat(P)^D_(S_n) := - frac(1, n^2). $)

#aod-paragraph[Derivation.]
For any downward transition $n arrow.r m$ with $n > m$, the released normalized pressure magnitude is

#math.equation(block: true, numbering: none, $ Delta hat(P)^D (n arrow.r m) := hat(P)^D_(S_n) - hat(P)^D_(S_m) = frac(1, m^2) - frac(1, n^2) > 0, $)

with signed state change $hat(P)^D_(S_m) - hat(P)^D_(S_n) = - Delta hat(P)^D (n arrow.r m)$.

#aod-boxed($ "Hydrogen shell tests use a declared signed comparison ladder." $)

#aod-noteblock("Remark")[The normalized ladder is a manual comparison choice. The main-note pressure definition remains $p^D = C_3 rho^D_(omega)$.]

#aod-noteblock("Presentation policy")[All A$Omega$ shell ratios in the spectral tables are exact rational D0 values (#raw("RC-031"), #raw("RC-039")). Decimal target ratios, wavelengths, frequencies, and percent errors are quarantined external presentation coordinates; a $z$-score is recorded only when a row carries an explicit uncertainty.]




#figure(
  kind: image, [
#include "../../lib/diagrams/hydrogen_shell_setup.typ"
  ],
  caption: [Hydrogen-facing shell-cycle ladder. The released shell-pressure magnitude is calculated before measured wavelengths and external energy-coordinate comparisons are attached.],
) <fig:manual-hydrogen-shell-setup>



== Shell-radius comparison <manual:hydrogen:radii>

#aod-paragraph[Specialization.]
The shell-radius geometry comparison records the standard quadratic shell scaling

#math.equation(block: true, numbering: none, $ frac(r_n, r_1) = n^2 . $)


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
    [$1$], [$S_1$], [$1$], [baseline],
    [$2$], [$S_2$], [$4$], [comparison record],
    [$3$], [$S_3$], [$9$], [comparison record],
    [$4$], [$S_4$], [$16$], [comparison record],
    bottomrule,
  )
}
  ],
  caption: [Hydrogen-facing shell-radius ratios.],
) <tab:manual-hydrogen-shell-radii>


== Shell-pressure table <manual:hydrogen:pressure-table>

#aod-paragraph[Specialization (#raw("RC-031")).]
Balmer comparison records fix destination shell $S_2$ ($m = 2$). The exact D0 released-pressure
magnitudes and baseline ratios against $3 arrow.r 2$ (verified in zero-float rational
arithmetic by #raw("RC-031"), #raw("hydrogen_shell_exact_series.csv")) are

#math.equation(block: true, numbering: none, $ Delta hat(P)^D (n arrow.r 2) = frac(1, 2^2) - frac(1, n^2), wide cal(R)_(n arrow.r 2) = frac(Delta hat(P)^D (n arrow.r 2), Delta hat(P)^D (3 arrow.r 2)). $)



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

#aod-paragraph[Quarantined external map.]
Measured frequency and energy coordinates enter strictly downstream under the quarantine
of #appref("manual:external-comparison"). Given a cited vacuum wavelength $lambda$,

#math.equation(block: true, numbering: none, $ f = frac(c, lambda), wide E = h_(upright("ext")) f. $)


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

#aod-noteblock("Choice")[The Lyman and Paschen records use the same normalized shell-pressure ladder as the Balmer records. The destination shell $S_m$ is declared before each transition table; exact D0 ratio evaluation precedes any quarantined wavelength, frequency, or energy export.]

#aod-paragraph[Derivation.]
For a fixed destination shell $S_m$ and downward transition $n arrow.r m$ ($n > m$),
define the exact D0 A$Omega$-internal series ratio $R_(upright("series")) (n arrow.r m) = cal(R)_(n arrow.r m, AO) gt.eq 1$
and its reciprocal baseline-wavelength ratio $lambda_n slash lambda_(m + 1) = 1 slash R_(upright("series")) lt.eq 1$:

#math.equation(block: true, numbering: none, $ R_(upright("series")) (n arrow.r m) = cal(R)_(n arrow.r m, AO) = frac(Delta hat(P)^D (n arrow.r m), Delta hat(P)^D ((m + 1) arrow.r m)) gt.eq 1, wide frac(lambda_n, lambda_(m + 1)) = frac(1, R_(upright("series")) (n arrow.r m)) lt.eq 1. $)

Against quarantined wavelength targets at $B_(upright("ext")) = sans("Q")_(upright("ext"))$,
the inverse-wavelength target ratio is

#math.equation(block: true, numbering: none, $ cal(R)^(lambda ,upright("tar"))_(n arrow.r m) = frac(lambda_((m + 1) arrow.r m), lambda_(n arrow.r m)). $)

Thus the A$Omega$-internal pressure ratio $R_(upright("series")) = cal(R)_(n arrow.r m, AO) gt.eq 1$
compares directly against the measured inverse-wavelength ratio
$cal(R)^(lambda ,upright("tar"))_(n arrow.r m)$, while its reciprocal
$lambda_n slash lambda_(m + 1) = 1 slash R_(upright("series")) lt.eq 1$ records the
dimensionless wavelength contraction across the wavelet D.E.C. ledger below.
External frequency-coordinate and energy export remain downstream. The reference engine
(#raw("manual/data/boundary_sadar/hydrogen_shell_exact_series.csv"), vector
#raw("RC-031")) evaluates all Lyman ($m = 1$), Balmer ($m = 2$), and Paschen ($m = 3$)
transitions in reduced exact rational arithmetic prior to quarantined NIST-ASD
wavelength comparison.


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

#aod-paragraph[Falsification.]
Retain one source identity for the shared denominator when propagating within-series
ratios. Air wavelengths require source-bound vacuum conversion or a declared
model-to-air observation map with refractive-index applicability and uncertainty;
$c slash lambda_(upright("air"))$ is not a vacuum frequency. Until those bindings are
supplied, the inverse-wavelength comparisons remain quarantined O0 carried-coordinate
diagnostics with physical uncertainty unresolved, strictly separated from the D0 exact
rational ratios of #raw("RC-031") and #raw("RC-039").

#aod-noteblock("Audit")[A spectral-series record carries the destination shell $S_m$, the exact D0 quantity $Delta hat(P)^D (n arrow.r m)$, and—inside $B_(upright("ext"))$—the inverse-wavelength ratio $lambda_((m + 1) arrow.r m) slash lambda_(n arrow.r m)$.]

#aod-provenance[#secref("subsec:shared-shell-path-declaration")\;
#appref("manual:external-comparison").]

#aod-literature-note[Hydrogen spectral-line targets: NIST Atomic Spectra Database #aod-cite("nist-asd")\; Paschen #aod-nowrap[Pa$alpha$], #aod-nowrap[Pa$beta$], #aod-nowrap[Pa$epsilon$] air rows: NIST Hydrogen Handbook #aod-cite("nist-hydrogen-handbook").]




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



== Five-boundary concentric shell transition and wavelet D.E.C. ledger <manual:hydrogen:dec-wavelet-transitions>

#aod-paragraph[Setup and engine verification (#raw("RC-039")).]
Declare the concentric shell-hierarchy boundary stack separating D0 exact rational shell
ratios from quarantined NIST-ASD wavelength targets:

#math.equation(block: true, numbering: none, $ B_(upright("core")) arrow.r B_(S_n) arrow.r B_(S_m) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext")) = sans("Q")_(upright("ext")). $)

Vector #raw("RC-039") (#raw("dec_hydrogen_shell_wavelet_step")) is verified alongside
#raw("RC-031") by #raw("python3 -B -m manual.engine --sector boundary_sadar") and
#raw("aod-core --verify-vectors --check-zero-float") against
#raw("manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv"). It evaluates exact
dimensionless shell-step pressure differences $Delta hat(P)_(n arrow.r m) = 1 slash m^2 - 1 slash n^2$,
baseline-normalized series ratios
$R_(upright("series")) (n arrow.r m) = cal(R)_(n arrow.r m, AO) = Delta hat(P)_(n arrow.r m) slash Delta hat(P)_(m + 1 arrow.r m) gt.eq 1$
(with $6$-decimal display coordinates kept separate from exact rationals), and exact
reciprocal wavelength ratios
$lambda_n slash lambda_(m + 1) = 1 slash R_(upright("series")) lt.eq 1$ across Balmer
($m = 2$), Lyman ($m = 1$), and Paschen ($m = 3$) transitions strictly inside
$B_(upright("core")) arrow.r B_(upright("sensor"))$ without importing an external
Rydberg constant.


#figure(
  kind: image, [
#include "../../lib/figures/manual/hydrogen_shell_wavelet_atlas.typ"
  ],
  caption: [Concentric hydrogen shell boundaries $S_1 dots.h S_6$, outgoing Lyman/Balmer/Paschen wavelet packets across $B_(upright("sensor"))$, and exact within-series rational ratios (#raw("RC-039"), #raw("hydrogen_shell_dec_transitions.csv")).],
) <fig:manual-hydrogen-shell-wavelet-atlas>


#figure(
  kind: table, [
#aod-csv-table(
  "/manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv",
  columns: (1.40fr, 1.15fr, 1.45fr, 1.45fr, 1.45fr, 1.55fr, 1.55fr),
  align: (left, center, right, right, right, right, right),
  size: 8.5pt,
  inset: (x: 3.0pt, y: 3.2pt),
  headers: (
    [Series], [$n arrow.r m$], [$r_n slash r_1 = n^2$], [$Delta hat(P)_(n arrow.r m)$], [$R_(upright("series"))$ (exact)], [$R_(upright("series"))$ (6dp)], [$lambda_n slash lambda_(m + 1)$],
  ),
  cells: (
    "series",
    (kind: "arrow", left: "n", right: "m"),
    "r_n_over_r1",
    "delta_P_hat",
    "R_series_exact",
    "R_series_dec6",
    "lambda_over_base_exact",
  ),
)
  ],
  caption: [Engine-bound exact rational hydrogen shell-transition and wavelet series D.E.C. ledger (#raw("RC-039"), live from #raw("hydrogen_shell_dec_transitions.csv")).],
) <tab:manual-hydrogen-dec-transitions>

