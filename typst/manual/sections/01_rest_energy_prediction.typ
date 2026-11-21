// Native Typst port of manual/sections/01_rest_energy_prediction.tex (verbatim scientific content).
#import "../preamble.typ": *

= Field Rest-Energy Records <manual:rest-energy-prediction>



#aod-paragraph[Calculation card.]
Exact support/window choices produce the accessor table; measured masses
are external targets with the quoted uncertainties. A general rest-energy
prediction still requires this application's shared-history producer,
history-to-rate map, relational reference clock and calibrated energy map.
The Higgs table evaluates a separate declared candidate/map diagnostic;
its target-only pulls do not include model uncertainty. Common comparison
and source roles are in #secref("manual:calculation-spine").




== 0$bar.v -$ scope <manual:rest:scope>

Rest-energy records are split into two tables. The A$Omega$ field-map table records support, carried cycle, and A$Omega$ accessor values. The measured-data comparison table records declared measured-sector target rows.

#math.equation(block: true, numbering: none, $ bold(a) tack.r (F,R, partial_T R, omega ), wide B = ( partial_T F, omega ). $)

The calculation spine is

#math.equation(block: true, numbering: none, $ C_f [M]_(AO) arrow.r.long sans("AO")_(mu) (C) arrow.r.long SADARop_B (C) arrow.r.long nu_(x, AO) arrow.r.long E_(x,upright("ext")) . $)


#aod-noteblock("Data-support class")[Rest-energy records are exact internal A$Omega$ field records or O0 external-map comparisons, depending on the declared measured-sector target rows. Target uncertainties are supplied; input, reduction and value-map contributions remain unresolved where no justified model is supplied.]



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

The added $4$ is retained edge-shell support. The cycle object remains
distinct from this scalar accessor.


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

The displayed $B^(plus.minus)$ and $B^0$ map has the same retained support.
A mass map using only that support cannot distinguish their two targets.
The rest-energy application must supply additional state with a matched
nondegeneracy test, or declare that limited resolution. A target is held out
only when its exclusion from construction, selection and calibration is bound.



== Electron external map <manual:rest:electron-external-map>

The electron comparison record is a manual map from the measured-sector electron to the A$Omega$ Dimonhexon support:

#math.equation(block: true, numbering: none, $ e^(-) arrow.r.long.bar 00 bar.v - med upright("Dimonhexon") equiv 00 bar.v - med (1":"2":"6), wide C_f [1":"2]_(AO) . $)

The charge-orientation tag is

#math.equation(block: true, numbering: none, $ q_(upright("ext")) (e^(-) ) = - 1, wide Q_(upright("ext")) (e^(-) ) = - e. $)

The rest-energy comparison target remains quarantined:

#math.equation(block: true, numbering: none, $ E^(upright("tar"))_e = 0.51099895069 upright("MeV"), wide sigma_(E,e) = 1.6 times 10^(- 10) upright("MeV"). $)



#aod-literature-note[Electron mass-energy: NIST CODATA #aod-cite("nist-electron-mass-energy"), SI defining constants: BIPM #aod-cite("bipm-si-defining-constants").]


#aod-remark[The $00 bar.v -$ tag is a manual measured-sector charge/orientation map carried by the manual comparison record.]




== Measured rest-energy target records <manual:rest:measured-comparison-analysis>

External comparison is quarantined. For records with declared targets,

#math.equation(block: true, numbering: none, $ E_(x,upright("ext")) = K_(upright("ext")) nu_(x, AO) , wide Delta E_x = E_(x,upright("ext")) - E_x^(upright("tar")) , $)


#math.equation(block: true, numbering: none, $ epsilon_x^(upright("sgn")) = 100 frac(Delta E_x, E_x^(upright("tar"))), wide bar.v epsilon_x bar.v = bar.v epsilon_x^(upright("sgn")) bar.v , wide z_(x,upright("target")) = frac(Delta E_x, sigma_(E,x)). $)



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
    [$e$], [0.51099895069], [$1.6 times 10^(- 10)$], [MeV], [NIST CODATA],
    [$mu$], [105.6583755], [$2.3 times 10^(- 6)$], [MeV], [NIST CODATA],
    [$tau$], [1776.86], [0.12], [MeV], [NIST / PDG target record],
    [$B^(plus.minus)$], [5279.41], [0.07], [MeV], [PDG 2025],
    [$B^0$], [5279.72], [0.08], [MeV], [PDG 2025],
    [$B_s^0$], [5366.93], [0.10], [MeV], [PDG 2025],
    [$B_c^(plus.minus)$], [6274.47], [0.32], [MeV], [PDG 2025],
    [$p$], [938.27208943], [$2.9 times 10^(- 7)$], [MeV], [NIST CODATA],
    [$n$], [939.56542194], [$4.8 times 10^(- 7)$], [MeV], [NIST CODATA],
    bottomrule,
  )
}
  ],
  caption: [Measured rest-energy target records.],
) <tab:manual-measured-comparison-analysis>



#aod-provenance[#mainappendix("main:app:ao-field-fractal-properties")\;
#appref("manual:external-comparison").]



#aod-literature-note[Lepton/baryon targets: NIST CODATA #aod-cite("nist-electron-mass-energy,nist-muon-mass-energy,nist-tau-mass-energy,nist-proton-mass-energy,nist-neutron-mass-energy"), meson targets: PDG 2025 #aod-cite("pdg-bmeson-2025").]



== Tritrioseptyro Higgs-support diagnostic fixture <manual:tritrioseptyro-higgs-support-fixture>

The supplied candidate rows and scoring formula reproduce the ranking. They
do not supply the originating history producer, detector thresholds or the
exposure history of the scale/exponent choice. Recovering those artifacts is
this application's next step before an independent prediction claim. The
freeze below is the declared evaluation order; it does not establish a
historical pre-exposure freeze.

Tritrioseptyro is the $3":"3":"7_(upright("yro"))$ Higgs-support prediction candidate selected by the internal AFC trace. The AFC run produces the trace rows; A$Omega$ detectors read the trace and name the retained route status. The selected candidate is joined to the frozen external mass map $E_H = R D thin 2^(L + 4)$ MeV. Production-channel and decay-channel residual tables carry the next comparison layer.

#math.equation(block: true, numbering: none, $ "AFC run" arrow.r.long "read-only trace" arrow.r.long #[A$Omega$ route-status naming]. $)

The trace is read-only for this record. Feedback experiments use separately declared write-back maps.

The candidate set is

#math.equation(block: true, numbering: none, $ cal(K)_H = brace.l 3":"1":"7,3":"1":"9,3":"2":"7,3":"2":"9, 3":"3":"7,3":"3":"9,3":"4":"7,3":"4":"9 brace.r . $)

For each candidate $K = (p,q,L)$, compute

#math.equation(block: true, numbering: none, $ Pi = q^p + q, wide R D = 2 Pi + 1, wide rho^D_(omega) = min (R D,L). $)

The scoped collision capacity is

#math.equation(block: true, numbering: none, $ C_(3,H) = 3. $)

With this scoped collision capacity,

#math.equation(block: true, numbering: none, $ P^D_H & = C_(3,H) rho^D_(omega) , \ Q^D_H & = C_(3,H) max (0,R D - L). $)

The retained candidate is

#math.equation(block: true, numbering: none, $ K_H^(star) = 3":"3":"7_(upright("yro")) = upright("Tritrioseptyro"). $)

For Tritrioseptyro,

#math.equation(block: true, numbering: none, $ Pi = 30, wide R D = 61, wide rho^D_(omega) = 7, wide P^D_H = 21, wide Q^D_H = 162. $)

Against adjacent even support-enclosure closures,

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
    [$3":"3":"7_(upright("yro"))$], [61], [21], [$+ 3 slash - 3$], [162], [0.00],
    [$3":"2":"7_(upright("yro"))$], [21], [21], [$+ 3 slash - 3$], [42], [1.58],
    [$3":"3":"9_(upright("yro"))$], [61], [27], [$+ 3 slash 0$], [156], [2.25],
    [$3":"4":"7_(upright("yro"))$], [137], [21], [$+ 3 slash - 3$], [390], [2.40],
    [$3":"2":"9_(upright("yro"))$], [21], [27], [$+ 3 slash 0$], [36], [2.89],
    [$3":"1":"7_(upright("yro"))$], [5], [15], [$- 3 slash - 9$], [0], [3.00],
    [$3":"4":"9_(upright("yro"))$], [137], [27], [$+ 3 slash 0$], [384], [3.59],
    [$3":"1":"9_(upright("yro"))$], [5], [15], [$- 9 slash - 12$], [0], [4.75],
    bottomrule,
  )
}
  ],
  caption: [Higgs-support candidate ranking. This table carries the active trace coordinates used by the internal selection rule.],
) <tab:manual-higgs-internal-candidates>



The trace score is reproducible under the internal selection rule:

#math.equation(block: true, numbering: none, $ S_H (K) = frac(d_(upright("saddle")), 12) + frac(d_Q, 100) + frac(d_L, 2) + d_(upright("route")) . $)

The scoring gate requires

#math.equation(block: true, numbering: none, $ arg min_(K in cal(K)_H) S_H (K) = 3":"3":"7_(upright("yro")) . $)



#aod-noteblock("Source artifacts")[The score-component definitions and candidate rows are supplied under #raw("manual/data/higgs") as #raw("higgs_trace_score_formula.md") and #raw("higgs_trace_internal_candidates_selection.csv"), respectively.]



#figure(
  kind: image, [
#image("/manual/figures/higgs/higgs_yro_saddle_signature.png", width: 72%)
  ],
  caption: [Tritrioseptyro yro saddle signature. The internal AFC trace gives $P^D_H = 21$, placing the selected $3":"3":"7_(upright("yro"))$ candidate between $C_6 = 18$ and $C_8 = 24$ with residuals $+ 3$ and $- 3$.],
) <fig:manual-higgs-yro-saddle>



#figure(
  kind: image, [
#image("/manual/figures/higgs/higgs_tritrioseptyro_trace_flow.png", width: 92%)
  ],
  caption: [Tritrioseptyro trace flow. The AFC run produces $Pi = 30$, $R D = 61$, $rho^D_(omega) = 7$, $P^D_H = 21$, and $Q^D_H = 162$. A$Omega$ names the detected $3":"3":"7_(upright("yro"))$ route status as Tritrioseptyro.],
) <fig:manual-higgs-trace-flow>



=== External mass map after candidate freeze <manual:higgs-external-map-after-freeze>

The external mass map is frozen after the internal candidate is selected:

#math.equation(block: true, numbering: none, $ E_H^(lr((0))) [upright("MeV")] = R D_H thin 2^(L + 4) . $)

For Tritrioseptyro,

#math.equation(block: true, numbering: none, $ E_H^(lr((0))) = 61 dot.op 2^(11) upright("MeV") = 124928 upright("MeV") = 124.928 upright("GeV"). $)

The frozen $R D thin 2^(L + 4)$ map sends Tritrioseptyro to $124.928 thin upright("GeV")$. Declared Higgs mass targets enter after the candidate and external map are frozen. The comparison table reports $Delta E$, absolute percent error, and the target-only pull $z_(upright("target")) = Delta E slash sigma_(upright("target"))$ for each target record.


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
    [$R D_H$], [61], [frozen internal accessor],
    [$L$], [7], [declared odd window],
    [$E_H^(lr((0)))$], [$61 dot.op 2^(11) thin upright("MeV") = 124.928 thin upright("GeV")$], [external map after freeze],
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
    [ATLAS+CMS Run-1 combined], [125.09], [0.24], [-0.162], [0.1295], [-0.675],
    [CMS $H arrow.r 4 ell$], [125.04], [0.12], [-0.112], [0.0896], [-0.933],
    [ATLAS Run-1+2 combined], [125.11], [0.11], [-0.182], [0.1455], [-1.655],
    [ATLAS $H arrow.r gamma gamma$], [125.22], [0.14], [-0.292], [0.2332], [-2.086],
    bottomrule,
  )
}
  ],
  caption: [LHC mass comparison after frozen external map.],
) <tab:manual-higgs-lhc-comparison>



#figure(
  kind: image, [
#image("/manual/figures/higgs/higgs_mass_comparison.png", width: 88%)
  ],
  caption: [Tritrioseptyro mass comparison. The frozen external map $E_H = R D thin 2^(L + 4)$ MeV sends the selected candidate to $124.928 thin upright("GeV")$. Target records enter as declared external comparison rows.],
) <fig:manual-higgs-mass-comparison>


These target records overlap in experiment, run or channel; their four
pulls are not four independent tests. A joint comparison needs their shared
covariance and the model/map uncertainty. The quoted values remain
target-only diagnostics.


#aod-paragraph[External data-comparison record.]
The internal trace selects $K^(star)_H = 3":"3":"7_(upright("yro"))$. The frozen external map gives

#math.equation(block: true, numbering: none, $ E_H^(lr((0))) = R D_H 2^(L + 4) = 61 dot.op 2^(11) thin upright("MeV") = 124.928 thin upright("GeV"). $)

Table #bare-ref("tab:manual-higgs-lhc-comparison") records the declared Higgs mass-input rows, their quoted uncertainties, and the resulting $Delta E$, $bar.v epsilon bar.v$, and $z_(upright("target"))$ coordinates. The mapped value $124.928 thin upright("GeV")$ lies within $1 sigma$ of the ATLAS+CMS Run-1 combined mass record and the CMS Run-2 $H arrow.r 4 ell$ mass record. Production-channel and decay-channel residual tables carry the next comparison layer.




#aod-provenance[#mainsection("main:subsec:yro-odd-window-route-status")\; #mainappendix("main:app:ao-field-fractal-properties")\; #tabref("tab:manual-higgs-internal-candidates")\; #tabref("tab:manual-higgs-external-map").]


#aod-literature-note[ATLAS+CMS Run-1 combined mass #aod-cite("atlas-cms-higgs-run1"). CMS $H arrow.r 4 ell$ mass #aod-cite("cms-hig-21-019"). ATLAS combined Run-1+Run-2 mass #aod-cite("atlas-higgs-mass-combined-2023"). ATLAS diphoton mass #aod-cite("atlas-higgs-diphoton-2023").]
