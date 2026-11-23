// Native Typst port of manual/sections/07_galactic_lensing_plan.tex (verbatim scientific content).
#import "../preamble.typ": *

= Galactic Lensing Diagnostic Plan <manual:galactic-lensing-diagnostic-plan>



#aod-paragraph[Calculation card.]
Toy bins, SPARC medium proxies, SWELLS targets and L3 input requirements have
separate roles. The inline aggregate tables retain their historical results;
per-system inputs, cohort membership, exclusions and evaluator/gate lineage
are still needed for replay. Shared target reductions and uncertainty enter
one joint comparison under #secref("manual:calculation-spine"), not additional
independent medium evidence. The L3 gate below states the missing stages.



#aod-noteblock("Scope")[This section applies the current A$Omega$D field-ring and $delta_3$ notation to a staged galactic-lensing diagnostic plan. It is a manual/application plan with an explicit L3 data-package gate.]


#aod-provenance[#mainsection("main:subsec:fractal-field-ring-gate")\;
#mainsection("main:sec:field-dynamics")\;
#secref("manual:cross-return-short-window")\;
#secref("manual:prediction-test-registry").]


#aod-literature-note[SWELLS target lane: Treu et al. #aod-cite("treu-swells-2011"), Brewer et al. #aod-cite("brewer-swells-2012").]



== Lensing lanes <manual:lensing-status-lock>



#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (24.00fr, 10.00fr, 56.00fr),
    align: (left, left, left),
    table.header(
      toprule,
      [Lane], [Class], [Active fields],
      midrule,
    ),
    [Toy 1], [L0], [exact internal $delta_3$ fixture],
    [SPARC5], [L1], [radial lens-medium data-support class; lens target fields are carried by SWELLS or L3 rows],
    [SWELLS K0], [L2], [target acquisition],
    [SWELLS K1], [L1/L2], [retained baseline],
    [SWELLS K2/K3], [L1/L2], [audit diagnostics],
    [K4], [L3], [higher-resolution lensing input-manifest row],
    [L3 lensing input package], [L3], [L3 input-manifest row; required fields: independent 3D medium fields, time-flow inputs, radiation-current gates, target-side quarantine, null controls, and audit],
    bottomrule,
  )
},
  caption: [Galactic lensing diagnostic lanes.],
) <tab:manual-lensing-status-lock>




== Field-ring spine <manual:lensing-field-ring-spine>

The lensing fixture uses a discrete exoshedding field-ring calculation. The value table records the evaluated gate values.

#math.equation(block: true, numbering: none, $ B_(upright("lens")) = ( partial_T F_(upright("exo")) , omega_(upright("lens")) ). $)


#math.equation(block: true, numbering: none, $ T^0_k = sum_i S^(lr((i)))_k . $)


#math.equation(block: true, numbering: none, $ T^(times)_k = T^0_k + sum_((i,j) in E_(upright("return"))) C^(times)_(i j,k) (B_(upright("lens")) ). $)


#math.equation(block: true, numbering: none, $ T^(times)_k - T^0_k = sum_((i,j) in E_(upright("return"))) C^(times)_(i j,k) (B_(upright("lens")) ). $)


#math.equation(block: true, numbering: none, $ Delta^(bb(Z))_k = T^(times)_k - O_k , wide delta_(3,k) (T^(times) ,O) = (s^(lr((3)))_k ,m_k ), wide m_k = bar.v Delta^(bb(Z))_k bar.v . $)


#math.equation(block: true, numbering: none, $ delta_3 (T^(times) ,O) = ( delta_(3,k) )_(k in K) . $)


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_02_frg_value_identity_delta3.typ"
  ],
  caption: [FRG value identity and $delta_3$ audit. Gate values $T^0$, $C^(times)$, and $T^(times)$ are computed before the fixture comparator joins.],
) <fig:manual-lensing-frg-delta3>



== Toy fixture lane <manual:lensing-toy-fixture-lane>

Toy 1 is the exact internal lensing toy. It belongs to the manual fixture lane and registry.


#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (36.0%, auto),
    align: (left, right),
    table.header(
      toprule,
      [Quantity], [Value],
      midrule,
    ),
    [gates], [16],
    [target bins], [13],
    [events], [18],
    [caustic bins], [0, 2],
    [$delta_3$ total $m$], [0],
    [checks passed], [11/11],
    bottomrule,
  )
},
  caption: [Toy 1 exact internal $delta_3$ fixture summary.],
) <tab:manual-lensing-toy-summary>



#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_01_toy1_delta3_class_tallies.typ"
  ],
  caption: [Toy 1 exact internal $delta_3$ class tallies.],
) <fig:manual-lensing-toy-delta3>



== SPARC5 lens-medium diagnostic <manual:lensing-sparc5-medium-diagnostic>

SPARC5 instantiates a radial lens-medium data-support class. It supplies radial field-medium inputs for diagnostic runs. Image-count, Einstein-radius, image-position, and shear target fields are target-side quantities carried by SWELLS or an L3 input package.

#include "../tables/sparc5_medium_diagnostic_summary_table.typ"


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_03_sparc5_lens_medium_phase_proxy.typ"
  ],
  caption: [SPARC5 radial lens-medium data-support class. The plotted quantities are diagnostic medium proxies; lensing targets are carried by SWELLS or a higher-resolution class.],
) <fig:manual-lensing-sparc5-proxy>


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_04_sparc5_class_tally_heatmap.typ"
  ],
  caption: [SPARC5 lens-medium class tallies. The dominant diagnostic route class is recorded for audit.],
) <fig:manual-lensing-sparc5-classes>



== SWELLS target lane <manual:lensing-swells-lane>

SWELLS supplies target-side acquisition fields for the lensing lane.

#include "../tables/swells_k0_target_tallies_table.typ"


#include "../tables/swells_k1_k2_k3_comparison_table.typ"

K1 is retained as a target-selected development baseline: target residuals
influenced its selection. K2 and K3 remain audit diagnostics. Independent
evaluation requires the full selection/exposure history and a locked recipe
before a new cohort is joined; it cannot reselect on that cohort's targets.

#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_05_swells_k_comparison_delta3.typ"
  ],
  caption: [SWELLS K1/K2/K3 $delta_3$ comparison. K2/K3 are audit diagnostics with $delta_3$ comparison tallies.],
) <fig:manual-lensing-swells-comparison>


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_06_swells_k1_thetae_delta3_tallies.typ"
  ],
  caption: [SWELLS K1 retained-baseline $theta_E$ $delta_3$ tallies.],
) <fig:manual-lensing-swells-k1>



== K4 input gate <manual:lensing-k4-input-gate>

K4 is the higher-resolution lensing input-manifest row for independent 3D and time-flow inputs.

#include "../tables/k4_3d_timeflow_input_gate_table.typ"


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_07_k4_3d_timeflow_input_gate.typ"
  ],
  caption: [K4 higher-resolution lensing data-support gate. The L3 input package records independent 3D + time-flow medium data before the target side joins.],
) <fig:manual-lensing-k4-gate>



== Target-side quarantine and release gate <manual:lensing-release-gate>

A derived $sigma_(upright("SIE"))$ shares the Einstein radius and distance
inputs of its target construction. Its derivation, source assumptions and
covariance/likelihood must travel with those inputs; it is not an independent
medium measurement. The lensing application next needs per-system
input/output and gate records that regenerate the K0/K1 cohort denominators.
Aggregate agreement alone does not supply that evaluator.

The A$Omega$ input side carries medium fields, gate values, and declared prediction values. The target side carries image-position, Einstein-radius, and image-count targets after prediction values freeze.

#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_08_target_quarantine.typ"
  ],
  caption: [Target-side quarantine. A$Omega$ values freeze before target tallies join.],
) <fig:manual-lensing-target-quarantine>


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_09_staged_lensing_lane.typ"
  ],
  caption: [Staged galactic lensing lane. Toy fixtures, SPARC5 diagnostics, SWELLS acquisition, retained baseline, K2/K3 audit diagnostics, and K4 gate are kept distinct.],
) <fig:manual-lensing-staged-lane>


#figure(
  kind: image, [
#include "../../lib/figures/manual/lensing_10_lensing_calculation_spine.typ"
  ],
  caption: [Galactic lensing calculation spine. The $U$-projection and lensing targets remain downstream of declared field-ring values.],
) <fig:manual-lensing-calculation-spine>


A completed L3 lensing record carries declared medium fields, declared radiation-current gates, declared target-side quarantine, computed $T^0$, $C^(times)$, and $T^(times)$, declared $lambda_(upright("lens"))$, $delta_3$ residual table, null controls, audit, and lens residuals after A$Omega$ values freeze.
