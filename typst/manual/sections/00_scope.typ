// Native Typst port of manual/sections/00_scope.tex (verbatim scientific content).
#import "../preamble.typ": *

= Scope <manual:scope>

This manual carries application and prediction-test material downstream from the main A$Omega$D note. The main note carries the AF/AFC/A$Omega$D calculus. This manual carries calculation records, setup diagrams, comparison targets, external-comparison records, error audits, and audit tables.


== Use of this manual <manual:scope:use>

The manual uses the same section / subsection / subsubsection structure as the main note. Rest-energy calculation records are organized under #secref("manual:rest-energy-prediction"). External comparison material remains downstream and quarantined from the A$Omega$-internal scoped-flux calculation.



== Simulation reading route <manual:simulation-reading-route>

Follow Main in its dependency order: specific distinction, closure and recurring wave, motif/field folding, complete wave state and relational time, then Stokes/SADAR/harmonic values. Manual Scope is followed by the consolidated native fixtures, the D.E.C. ledger and the retained applications.






== Calculation spine <manual:calculation-spine>


The common method has five operations. Declare the setup: retained fields,
ancestry, window, boundary, coupled and shed currents, and update law. Admit
source-bound inputs with their roles, acquisition maps and uncertainty.
Compute on that setup, retaining the state needed by its dynamics. Map the
outputs with the declared observation, clock and calibration. Finally join
the frozen comparison evidence, propagate shared dependencies and challenge
the stated claim. Applications below supply their choices and exact values;
the measures and mappings chapters own the map and uncertainty calculations.


The manual uses one active calculation language. A calculation declares

#math.equation(block: true, numbering: none, $ B = ( partial_T F, omega ). $)

It forms retained cycle provenance, evaluates branch/hinge/branch, and computes a SADAR value:

#math.equation(block: true, numbering: none, $ C_f [ Sigma ]_(AO) , wide sans("AO")_(mu) (C) = chevron.l Pi_(alpha) ,H_(mu) , Pi_(Omega) chevron.r , wide SADARop_B (C) = p^D_(C, AO) A_(C, AO) . $)

The boundary value is stored by

#math.equation(block: true, numbering: none, $ Phi^D_(partial_T R) = sum_(e in partial_T R) SADARop_B (C_e ). $)

Tables store evaluated values. Tables are not the calculus.


== Worked-calculation release <manual:worked-calculation-release>

A worked record follows one sequence: question, dependencies, cited input,
declared reduction, local choices, operator chain, exact block, intermediate
table, exact output row, exact-to-report map, comparison, figure,
reproducibility, and falsification hook. Its opening calculation card names
the supplied stages and the unresolved obligations; the detailed calculation
and authoritative tables remain with the application.

For an exact A$Omega$-internal fixture, form

#math.equation(block: true, numbering: none, $ "setup" arrow.r A scripts(arrow.l.r)_(mu) Omega " calculation" arrow.r "fixture comparator" arrow.r Delta^(bb(Z)) , delta_3 arrow.r "audit". $)


For an external comparison calculation, form

#math.equation(block: true, numbering: none, $ "setup" arrow.r A scripts(arrow.l.r)_(mu) Omega " calculation" arrow.r "observable / target record" arrow.r Delta , epsilon ,z, sigma arrow.r "error audit". $)

The symbols $Delta$, $epsilon$, $z$, and $sigma$ belong to the external comparison layer. A target-only pull uses the declared target standard uncertainty and is
labelled $z_(upright("target"))$. A standardized joint residual additionally
requires the uncertainty of both sides and their dependence.

For a benchmark-dataset calculation, record

#math.equation(block: true, numbering: none, $ bold(upright(a)) tack.r (F,R, partial_T R, omega ), quad cal(D)_(upright("bench")) , quad cal(Q)_(upright("required")) , quad cal(S) = "benchmark manifest". $)

Registry rows carry benchmark calculations until the declared dataset, required coordinate, report map, and audit fields are supplied.


#aod-noteblock("Placement rule")[A worked record carries a complete simulation or comparison row. Registry rows carry declared setup, target, comparator, residual, uncertainty, and audit fields as they are supplied.]


#aod-noteblock("Specification discipline")[A rest or prediction record may use a compact curling-curl specification only after $H T(K;B)$ is declared or inherited.]



== Table discipline <manual:table-discipline>

Tables retain evaluated values, targets, residuals and their provenance. The calculation is the declared boundary computation

#math.equation(block: true, numbering: none, $ bold(upright(a)) tack.r (F,R, partial_T R, omega ), wide B = ( partial_T F, omega ), $)

followed by the A$Omega$ and SADAR calculation on that boundary.



== Provenance-label policy <manual:provenance-label-policy>

Tokens of the form #raw("main:<anchor>") and #raw("manual:<anchor>") are cross-document provenance anchors. They refer to the corresponding source label #raw("<anchor>") in the named document. Reader pointers render the published equation, section, appendix or table number from that label; the full source keys remain in macro arguments or source metadata. Explicit alias labels declare alternate anchors. Provenance records remain internal-reference lists; external sources belong in Literature note records.


== Exact arithmetic and presentation decimals <manual:exact-arithmetic-presentation>

A$Omega$-internal calculations use integer counts and exact rational ratios. Decimal values appear only as external comparison coordinates, presentation values, or plot labels.

#math.equation(block: true, numbering: none, $ #[A$Omega$ side: integers / fractions], wide "external side: value " plus.minus " declared uncertainty". $)

If an external measured decimal is used as a comparison target, the comparison record declares its uncertainty $sigma$ when a $z$-score is formed. Percent errors may be shown as presentation comparisons when the target value is declared.


=== Exact-fixture corollary <subsec:frg-delta-three-corollary>

If an exact fixture declares

#math.equation(block: true, numbering: none, $ T_k^(times) ,O_k in bb(Z), $)

then record the exact ternary signed residual

$ Delta_k^(bb(Z)) = T_k^(times) - O_k , wide s_k^(lr((3))) = op("sgn")( Delta_k^(bb(Z)) ) in brace.l - 1,0, + 1 brace.r , wide m_k = bar.v Delta_k^(bb(Z)) bar.v in bb(Z)_(gt.eq 0) . $ <eq:frg-delta-three-components>

Thus

$ Delta_k^(bb(Z)) = s_k^(lr((3))) m_k . $ <eq:frg-delta-three-signed-product>

The compact residual package is

#tagged-eq("RG10", $ delta_(3,k) (T^(times) ,O) = (s_k^(lr((3))) ,m_k ), wide delta_3 (T^(times) ,O) = ( delta_(3,k) (T^(times) ,O) )_(k in K_(upright("bin"))) . $, <eq:frg-delta-three>)

Normalized decimal summaries belong to declared value maps or external comparison entries.

SYM-A5 checks integer-fixture residuals #eqref("eq:frg-delta-three").
RG-A10 forms $T_k^(times) - T_k^0 = sum C_(i j,k)^(times) (B)$ for
declared exact integer fixtures. RG-A11 records $Delta^(bb(Z))$ and
$delta_3$ using #eqref("eq:frg-delta-three-components")–#eqref("eq:frg-delta-three").


#aod-noteblock("Decimal precision record")[A released decimal presentation value carries

#math.equation(block: true, numbering: none, $ (x_(upright("disp")) ,u_x ,upright("unit")(x),upright("src")(x),upright("round")(x),upright("scope")(x)). $)

Here $upright("scope")(x) in brace.l "internal","external","measured","derived external","value map","demonstration" brace.r$. The precision field $u_x$ records declared display uncertainty.]




== External-comparison quarantine <manual:external-comparison-quarantine>

Measured preparation or boundary inputs may enter through declared acquisition
or reduction maps, with their source assumptions and uncertainty retained.
External laws and constants do not thereby become calculus premises or set
native notation. Calibration inputs and evaluation targets have separate
roles; target exposure during selection remains part of the record. In this manual, an external comparison is written

#math.equation(block: true, numbering: none, $ Qext ( nu_(x, AO) ;cal(T)_x ), $)

where $cal(T)_x$ is a declared measured-sector target record.



== Scoped errors by data-support class <manual:scoped-errors-data-support>


For $r = y_(upright("model")) - y_(upright("observed"))$, the joint variance in
#eqref("eq:manual-m3-residual-dependence") retains shared sources across both sides. Exact
finite laws permit evaluation at every input case; affine maps permit exact
propagation of complete moments; justified intervals give bounds. A nonlinear
moment-only calculation is a linearized diagnostic unless its remainder is
bounded. A source-reported uncertainty alone supplies no probability law.
Unknown components remain unknown; display rounding and exact conditional
arithmetic do not establish physical certainty.


A simulation or comparison is classified by the declared data support it instantiates. Dataset resolution selects the data-support class: radial rows instantiate G0; radial rows plus proxy density/current fields instantiate G1; three-dimensional density/velocity/current fields instantiate G2; time-ordered tracer positions/velocities instantiate G3. Each class reports residuals in its declared coordinate. Projection and marginalization maps carry their own comparison coordinates and uncertainty records.

The scoped-error chain is

#math.equation(block: true, numbering: none, $ D arrow.r R(D) arrow.r cal(M)(D,R) arrow.r Pi_(upright("report")) arrow.r epsilon_(upright("report")) . $)

Here $D$ is the declared data-support distinction layer, $R(D)$ is the induced relation family, $cal(M)(D,R)$ is the AFC/A$Omega$D model evaluated on that cut, $Pi_(upright("report"))$ is the report or projection map, and $epsilon_(upright("report"))$ is the residual relative to the declared output target. Every manual comparison declares its data-support class before residuals are interpreted.


#aod-paragraph[Simulation data card.]
Each simulation or comparison row records

#math.equation(block: true, numbering: none, $ (D, C_(upright("support")) , M_(AO) , Pi_(upright("report")) , sigma_(upright("input")) , epsilon_(upright("report")) , upright("src")). $)

Here $D$ is the declared input data, $C_(upright("support"))$ is the data-support class, $M_(AO)$ is the AFC/A$Omega$D calculation or map, $Pi_(upright("report"))$ is the reported coordinate, $sigma_(upright("input"))$ is the declared input uncertainty when present, $epsilon_(upright("report"))$ is the residual/error coordinate, and $upright("src")$ records the data source or source artifact.




== Manual record forms <manual:record-forms>


Each application card binds its question, fields/window/boundary, inherited
construction and local choices, input roles, exact calculation, observation
and clock, comparison, and falsifier. The associated quantity rows use this
compact form; detailed source identities and covariance remain in the bound
comparison record.

#align(center)[

#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, 1fr, 1fr, 1fr, 1fr),
    align: (left, left, left, left, left),
    table.header(
      toprule,
      [Quantity/role], [Source and unit/domain], [Value/state], [Uncertainty and shared sources], [Map and unresolved input],
      midrule,
    ),
    [Preparation], [Exact, measured or derived], [Admitted input], [Law, moments, bound or unknown], [Acquisition/reduction],
    [Output], [Named conditional law], [Computed value], [Propagated inputs and map], [Model/reduction remainder],
    [Target], [Evaluation or development], [Source value], [Measurement and shared calibration], [Observation reduction],
    [Residual], [Named comparison], [Difference/statistic], [Joint result or partial diagnostic], [Missing dependence],
    bottomrule,
  )
}
]

An exact fixture specifies exact operands; physical preparation and
observation uncertainties are uninstantiated until a physical application
supplies them. Data support, supplied stages, replay and empirical evidence
are recorded separately in #secref("manual:prediction-test-registry").



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.header(
      toprule,
      [Record form], [Active fields],
      midrule,
    ),
    [A$Omega$ field record], [support, carried cycle, pressure/accessor values, and retained A$Omega$ value],
    [Measured target record], [target value, declared uncertainty, measured-sector coordinate, and citation],
    [External comparison record], [map value, target, residual/error coordinate, uncertainty source, and audit hook],
    [Observable-map record], [observable-map value, target, residual, percent error, citation, and audit hook],
    [Exact fixture], [comparator bins, $Delta^(bb(Z))$, $delta_3$, closure residual, and sheddic-route audit],
    [Benchmark manifest], [dataset table, required report coordinate, input data sources, and audit hook],
    [Calibration anchor], [convention value and convention-audit residual],
    bottomrule,
  )
}
  ],
  caption: [Manual record forms.],
) <tab:manual-record-forms>



#aod-paragraph[Construction and record classes.]
Native fixtures establish exact typed relations; declared models specify their
chosen update/coupling law; metrology records add calibration and units;
empirical comparisons additionally bind external data and residuals. Admission
precedes all four projections. The common construction is distinction,
retained relation, admitted motif/closure, recurring wave, scoped field
organization, complete state/trace and native comparison. A field resolves
wave identities and is not retained closure lineage itself. Motion is the
later realized pressure-bearing transition. Modular coordinate phase in the
3D applications is a downstream statistic; sampling interval is an acquisition
coordinate. Native closure counts and RCD are not measured time.



== Five-boundary D.E.C. execution spine and chapter index <manual:scope:five-boundary-spine>

Every worked example across this manual instantiates one uniform five-boundary execution spine on an explicit finite support $R$, its typed boundary $partial_T R$, and an integer window $omega$:

#math.equation(block: true, numbering: none, $ B_(upright("in")) arrow.r B_(upright("core")) arrow.r B_(upright("shed") slash upright("slide")) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext")) = sans("Q")_(upright("ext")). $)

Zero-float evaluations execute in both the Python reference engine (#raw("python3 -B -m manual.engine --sector boundary_sadar")) and the Rust exact core (#raw("aod-core --verify-vectors --check-zero-float")) across all fifty-three locked golden vectors—#raw("RC-001") through #raw("RC-045") ($45$ #raw("rational_core")) and #raw("SD-001") through #raw("SD-008") ($8$ #raw("symbolic_and_display")). No floating-point value, background continuum clock, or external SI constant enters $B_(upright("in")) arrow.r B_(upright("sensor"))$.


#figure(
  kind: image, [
#include "../../lib/figures/manual/five_boundary_calculation_spine.typ"
  ],
  caption: [Five-boundary D.E.C. calculation spine $B_(upright("in")) arrow.r B_(upright("core")) arrow.r B_(upright("shed") slash upright("slide")) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext")) = sans("Q")_(upright("ext"))$ binding all Manual sections and appendices to the zero-float reference engines.],
) <fig:manual-five-boundary-calculation-spine>


#figure(
  kind: table, [
#{
  let raw-wrap(s) = raw(
    s.replace("_", "_\u{200b}")
     .replace("/", "/\u{200b}")
  )
  set text(size: 7.8pt)
  show raw: set text(size: 6.9pt)
  set par(justify: false, leading: 0.44em)
  table(
    columns: (15fr, 32fr, 20fr, 33fr),
    align: (left, left, left, left),
    inset: (x: 3.0pt, y: 3.0pt),
    table.header(
      toprule,
      [Unit], [Declared 5-boundary stack], [Engine vectors], [Frozen D.E.C. / SADAR artifact],
      midrule,
    ),
    [§2 Closure & wave], [$B_(upright("monon")) arrow.r B_(upright("asym")) arrow.r B_(upright("wave")) arrow.r B_(upright("fold")) arrow.r B_(upright("harm"))$], [#raw("RC-033")], [#raw-wrap("native_closure_wave_dec_walk.csv")],
    [§3 Operativity], [$B_(upright("shared")) arrow.r B_(S^+) arrow.r B_(S^(- e)) arrow.r B_(upright("sensor")) arrow.r B_(upright("hold"))$], [#raw("RC-034")], [#raw-wrap("awareness_operativity_dec_walk.csv")],
    [§4 D.E.C. ledger], [$B_(upright("in")) arrow.r B_(upright("flip")) arrow.r B_(upright("slide")) arrow.r B_(upright("disoma")) arrow.r B_(upright("ext"))$], [#raw("RC-025"), #raw("RC-026"), #raw("RC-045")], [#raw-wrap("dec_chiral_flip_continuous_walk.csv"), #raw-wrap("ternary_swar_and_trit_ratio")],
    [§5 Cell measures], [$B_(upright("cell")) arrow.r B_(upright("stair")) arrow.r B_(upright("fold")) arrow.r B_(upright("audit")) arrow.r B_(upright("ext"))$], [#raw("RC-035")], [#raw-wrap("cell_measures_staircase_fold_dec.csv")],
    [§6 Typed maps], [$B_(upright("src")) arrow.r B_(upright("map")) arrow.r B_(upright("joint")) arrow.r B_(upright("role")) arrow.r B_(upright("ext"))$], [#raw("RC-036")], [#raw-wrap("typed_map_joint_law_ledger.csv")],
    [§7 Temporal & SI], [$B_(upright("pair")) arrow.r B_(upright("lag")) arrow.r B_(upright("bridge")) arrow.r B_(upright("val")) arrow.r B_(upright("ext"))$], [#raw("RC-037")], [#raw-wrap("temporal_si_bridge_dec_ledger.csv")],
    [§8 Short-window], [$B_(upright("core")) arrow.r B_(omega) arrow.r B_(upright("close")) arrow.r B_(upright("shed")) arrow.r B_(upright("ext"))$], [#raw("RC-030"), #raw("RC-038")], [#raw-wrap("dimonhexon_double_slit_ring_paths.csv"), #raw-wrap("short_window_rcd_dec_ledger.csv")],
    [§9 Rest energy], [$B_(upright("hard")) arrow.r B_(tau) arrow.r B_(upright("shed")) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext"))$], [#raw("RC-027")--#raw("RC-029"), #raw("SD-007")], [#raw-wrap("tau_five_boundary_sadar_trace.csv"), #raw-wrap("higgs_baryon_overlap_saddle_scan.csv"), #raw-wrap("rest_energy_sadar_debris_atlas.csv")],
    [§10 Hydrogen], [$B_(upright("core")) arrow.r B_(S_n) arrow.r B_(S_m) arrow.r B_(upright("sensor")) arrow.r B_(upright("ext"))$], [#raw("RC-031"), #raw("RC-039")], [#raw-wrap("hydrogen_shell_exact_series.csv"), #raw-wrap("hydrogen_shell_dec_transitions.csv")],
    [§11 Wire & Stokes], [$B_(upright("wire")) arrow.r B_e arrow.r B_(upright("int")) arrow.r B_(R_1 union R_2) arrow.r B_(upright("ext"))$], [#raw("RC-032")], [#raw-wrap("scoped_wire_and_moving_boundary_walk.csv")],
    [§12 Solar O0], [$B_(upright("Sun")) arrow.r B_(upright("Hg/bend/red")) arrow.r B_(upright("gate")) arrow.r B_(upright("O0")) arrow.r B_(upright("ext"))$], [#raw("RC-040")], [#raw-wrap("solar_o0_boundary_dec_audit.csv")],
    [§13 Field dynamics], [$B_(Q_4) arrow.r B_(upright("hinge")) arrow.r B_(upright("ring")) arrow.r B_(upright("pool")) arrow.r B_(upright("ext"))$], [#raw("RC-041"), #raw("SD-008")], [#raw-wrap("run_tumble_q4_dec_walk.csv"), #raw-wrap("sparc_pooled_primary_exact.csv")],
    [§14 Lensing plan], [$B_(upright("src")) arrow.r B_(upright("shell"),k) arrow.r B_(upright("FRG")) arrow.r B_(delta_3) arrow.r B_(upright("SWELLS"))$], [#raw("RC-020"), #raw("RC-042")], [#raw-wrap("lensing_ray_chiral_dec_walk.csv")],
    [App. A Shedding], [$B_(upright("span")) arrow.r B_(upright("clip")) arrow.r B_(upright("shed")) arrow.r B_(upright("reclose")) arrow.r B_(upright("ext"))$], [#raw("RC-014"), #raw("RC-043")], [#raw-wrap("cycle_shedding_exact_rational_summary.csv")],
    [App. B Quarantine], [$B_(upright("core")) arrow.r B_(upright("sensor")) arrow.r B_(upright("map")) arrow.r B_(upright("tar")) arrow.r sans("Q")_(upright("ext"))$], [#raw("SD-007")], [#raw-wrap("rest_energy_sadar_debris_atlas.csv")],
    [App. C 3D phase], [$B_(bb(Z)^3) arrow.r B_(upright("lag")) arrow.r B_(upright("phase")) arrow.r B_(upright("oct")) arrow.r B_(delta_3)$], [#raw("RC-044")], [#raw-wrap("coordinate_phase_3d_dec_walk.csv")],
    bottomrule,
  )
}
  ],
  caption: [Uniform five-boundary D.E.C. calculation index across Manual sections and appendices.],
) <tab:manual-chapter-dec-boundary-index>


