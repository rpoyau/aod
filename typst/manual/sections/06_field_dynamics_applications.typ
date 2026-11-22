// Native Typst port of manual/sections/06_field_dynamics_applications.tex (verbatim scientific content).
#import "../preamble.typ": *

#pagebreak(weak: true)


= Field Dynamics Applications <manual:field-dynamics-applications>



#aod-paragraph[Calculation card.]
The coordinate examples use fixed exact tracks and integer comparators;
SPARC uses source radial rows and declared component proxies, with an
observation-only square-speed diagnostic. Tau retains carried score records,
and the orbital-retention path remains a required-input plan. Each subsection
keeps its scope, operator chain, output and falsifier. Source assumptions,
shared calibration and missing model uncertainty follow
#secref("manual:calculation-spine")\; these evidence classes are distinct.



#aod-noteblock("Scope")[This section uses the main-note field dynamics calculus as an application layer. SPARC uses the square-speed coordinate $U = V^2$. The Tau ring fixture uses $S_(tau)$ and missing-burden diagnostics. Each score coordinate is declared inside its own support class.]



#aod-remark[Field-dynamics simulations are finite compressions of the A$Omega$D ontology. A macroscopic field is simulated by declared clustering, finite boundary windows, support families, and value maps. Output residuals are read against the declared data support: boundary placement, density resolution, time-flow data, angular/radial momentum inputs, slosh windows, capacity seating, and sheddic-route declarations.]


A large field-dynamics system is handled by declared clustering. A cluster records a retained family of distinctions and relations over a boundary/window. The cluster records its support expression, construction trace or inherited trace, capacity rule, coupling family, and route status. The cluster is a finite calculation container recording a declared A$Omega$D form.
A reduction declares its retained and discarded state, lineage and memory,
then tests the intended readout, error bound or future boundary response on
matched windows and interventions. Equal present summaries do not establish
future sufficiency; two histories with that summary and different next
responses refute it. No Markov closure follows from clustering alone.





== Data-support classes for manual simulations and comparisons <manual:field-dynamics-data-support-classes>

The support rule in #secref("manual:scoped-errors-data-support") selects the comparison coordinate; it does not certify replay or physical validation. #tabref("tab:manual-data-support-classes") records the manual classes used by this release.



#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (7.00fr, 17.00fr, 27.00fr, 22.00fr, 12.00fr),
    align: (left, left, left, left, left),
    table.header(
      toprule,
      [Class], [Name], [Declared distinctions], [Relations induced], [Residual],
      midrule,
    ),
    [D0], [exact internal fixture], [exact integer gates, channels, comparator bins], [internal returned-current relations], [$delta_3$ tally],
    [O0], [observable-map fixture], [observable-map value and measured-sector target], [external comparison map], [target residual],
    [G0], [radial shell projection], [galaxy, radial bin, radius, speed, radial gas/disk/bulge support], [radial shell field-dynamics relations], [$U$ residuals],
    [G1], [radial-medium projection], [G0 plus radial density/current proxy fields], [radial medium-support relations], [$U$ + proxy],
    [G2], [3D shell field-dynamics retention], [radial, angular, vertical cells; density, velocity, current, background support], [local/inter/core/long/bg/J range SADAR], [retention / field],
    [G3], [time-resolved tracer-current simulation], [G2 plus tracer positions/velocities through time windows], [slosh, hinge shift, chiral flip, partial coupling], [path / phase],
    [L0], [exact lensing toy fixture], [exact gates and comparator tallies], [field-ring $delta_3$ relations], [$delta_3$ tally],
    [L1], [radial lens-medium diagnostic], [radial medium proxies without image targets], [medium-class relations], [medium tallies],
    [L2], [target-acquisition lane], [image-count, Einstein-radius, image-position, or shear targets], [target-side quarantine], [acquisition],
    [L3], [full lensing input package], [declared medium fields, radiation-current gates, and target side], [prediction before target join; target scoring after freeze], [lens residuals],
    bottomrule,
  )
},
  caption: [Data-support classes for manual simulations and comparisons.],
) <tab:manual-data-support-classes>




#aod-remark[This table records which distinctions are instantiated by a manual calculation. Projection and marginalization maps record comparison coordinates and uncertainty.]




== Data-support and uncertainty budget <manual:field-dynamics-data-support-budget>

A field-dynamics diagnostic records its data-support and uncertainty budget before residuals are interpreted. The budget records the declared distinction family, support class, uncertainty component, and report target.



#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (16.00fr, 8.00fr, 42.00fr, 26.00fr),
    align: (left, left, left, left),
    table.header(
      toprule,
      [Distinction family], [Symbol], [Declared data support], [Support class],
      midrule,
    ),
    [Density], [$epsilon_(rho)$], [$rho (R,z, theta ,t)$ or radial proxy], [3D / 2D / radial / proxy],
    [Velocity], [$epsilon_v$], [$v(R,z, theta ,t)$ or radial speed], [vector / radial / proxy],
    [Time window], [$epsilon_(omega)$], [cadence and duration], [measured / declared / proxy],
    [Boundary], [$epsilon_(partial)$], [$partial_T R_c (t)$], [3D / radial / proxy],
    [Capacity], [$epsilon_C$], [$C^(upright("cap"))$], [typed / scalar / inherited / proxy],
    [Coupling], [$epsilon_E$], [$E^(frak(S)) (B)$], [full / radial / proxy / ablation cut],
    [Sheddic route], [$epsilon_X$], [$op("SheddicPath")$], [declared / inferred],
    [External map], [$epsilon_K$], [$K_(upright("ext"))$ or $lambda$], [frozen / calibrated],
    bottomrule,
  )
},
  caption: [Field dynamics data-support classes.],
) <tab:field-dynamics-data-support-budget-a>



#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (16.00fr, 8.00fr, 32.00fr, 36.00fr),
    align: (left, left, left, left),
    table.header(
      toprule,
      [Distinction family], [Symbol], [Uncertainty], [Report target],
      midrule,
    ),
    [Density], [$epsilon_(rho)$], [$sigma_(rho)$ when declared], [field or $U$],
    [Velocity], [$epsilon_v$], [$sigma_v$], [current, path, or $U$],
    [Time window], [$epsilon_(omega)$], [$sigma_(omega)$], [slosh / retention / path],
    [Boundary], [$epsilon_(partial)$], [$sigma_(partial)$], [boundary audits],
    [Capacity], [$epsilon_C$], [$sigma_C$], [retention / seating],
    [Coupling], [$epsilon_E$], [$sigma_E$], [retention / projection],
    [Sheddic route], [$epsilon_X$], [$sigma_X$], [route / slosh],
    [External map], [$epsilon_K$], [$sigma_(upright("map"))$], [external comparison],
    bottomrule,
  )
},
  caption: [Field dynamics uncertainty and report targets.],
) <tab:field-dynamics-data-support-budget-b>




#aod-remark[A scored diagnostic is interpreted within its declared support class. Projection and marginalization comparisons report their uncertainty records.]



#aod-paragraph[Ablation cut.]
An ablation cut is a declared data-support cut with one distinction family intentionally omitted or marginalized. It records projection or marginalization residuals against a comparison support class. The evaluated A$Omega$D form remains the declared form for that record.


== Scoped error forms by data-support class <manual:field-dynamics-scoped-error-forms>

For a G0 radial shell projection, the score coordinate remains square speed:

#math.equation(block: true, numbering: none, $ U^(upright("obs"))_(g,j) = (V^(upright("obs"))_(g,j) )^2 , wide Delta U_(g,j) = U^(A Omega)_(g,j) - U^(upright("obs"))_(g,j) . $)

When observation, projection and input contributions form a justified joint
moment model with zero cross-covariances, their residual variance reduces to

#math.equation(block: true, numbering: none, $ sigma^2_(upright("total"),g,j) = sigma^2_(upright("obs"),g,j) + sigma^2_(upright("proj"),g,j) + sigma^2_(upright("input"),g,j) , wide z^U_(g,j) = frac(U^(A Omega)_(g,j) - U^(upright("obs"))_(g,j), sigma_(upright("total"),g,j)). $)

For a G1 radial-medium projection, proxy-support residuals may be recorded as

#math.equation(block: true, numbering: none, $ epsilon_(rho ,j) = rho^(A Omega)_j - rho^(upright("proxy"))_j , wide epsilon_(J,j) = J^(A Omega)_j - J^(upright("proxy"))_j . $)

For a G2 three-dimensional field-dynamics retention fixture, exact retention tallies and field residuals may be recorded as

#math.equation(block: true, numbering: none, $ Delta^(bb(Z))_k = T_k - O_k , wide delta_(3,k) = (s^(lr((3)))_k ,m_k ), $)


#math.equation(block: true, numbering: none, $ epsilon_(rho) (c) = rho^(A Omega)_c - rho^(upright("obs"))_c , wide J^(upright("obs"))_c = rho^(upright("obs"))_c v^(upright("obs"))_c , wide epsilon_J (c) = J^(A Omega)_c - J^(upright("obs"))_c . $)

For vector targets, the fixture declares $epsilon.alt gt.eq 0$ with the units of $bar.v.double J^(A Omega)_c bar.v.double thin bar.v.double J^(upright("obs"))_c bar.v.double$ and a positive denominator. The dimensionless regularized alignment score is

#math.equation(block: true, numbering: none, $ c_(epsilon.alt ,c) = frac(J^(A Omega)_c dot.op J^(upright("obs"))_c, bar.v.double J^(A Omega)_c bar.v.double thin bar.v.double J^(upright("obs"))_c bar.v.double + epsilon.alt). $)

For a G3 time-resolved tracer-current fixture, path and velocity residuals such as $epsilon_x$ and $epsilon_v$ are declared against path-coordinate targets. RMSE reports are used only when the fixture declares metric units and path-coordinate targets.

== Two-dimensional slice / three-dimensional field toy <manual:2d-3d-slice-toy>

This toy records how data-support scope changes the reported value when a three-dimensional field is represented by a two-dimensional slice or when the boundary is placed improperly. It is a manual diagnostic container that records declared comparison values.

Let $B_(3 D)$ be the declared three-dimensional boundary/window and let $B_(2 D)$ be the slice boundary obtained by suppressing the vertical/time-flow input. Let $B_(upright("bad"))$ be an intentionally improper setup boundary. The same calculation is evaluated three ways:

#math.equation(block: true, numbering: none, $ U^(3 D)_(AO) = sans("Q")^U_(upright("ext")) (D^(upright("BF")) (B_(3 D) )), wide U^(2 D)_(AO) = sans("Q")^U_(upright("ext")) (D^(upright("BF")) (B_(2 D) )), wide U^(upright("bad"))_(AO) = sans("Q")^U_(upright("ext")) (D^(upright("BF")) (B_(upright("bad")) )). $)

The scoped diagnostics are

#math.equation(block: true, numbering: none, $ Delta U_(2 D arrow.r 3 D) = U^(2 D)_(AO) - U^(3 D)_(AO) , wide Delta U_(partial) = U^(upright("bad"))_(AO) - U^(3 D)_(AO) . $)

For exact internal bins, the same comparison may be recorded by

#math.equation(block: true, numbering: none, $ Delta_k^(bb(Z)) = T_k^(upright("bad")) - T_k^(3 D) , wide delta_(3,k) (T^(upright("bad")) ,T^(3 D) ) = (s_k^(lr((3))) ,m_k ). $)




#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (18.00fr, 22.00fr, 24.00fr, 20.00fr),
    align: (left, left, left, left),
    table.header(
      toprule,
      [Case], [Boundary / data], [Diagnostic], [Interpretation],
      midrule,
    ),
    [3D declared field], [$B_(3 D)$, $rho (R,z, theta ,t)$, velocity and window data], [baseline value $U^(3 D)_(AO)$ or $T^(3 D)$], [retained support reference],
    [2D slice], [$B_(2 D)$, vertical/time-flow suppressed], [$Delta U_(2 D arrow.r 3 D)$], [slice projection residual],
    [Improper boundary], [$B_(upright("bad"))$, wrong boundary/capacity/route], [$Delta U_(partial)$ or $delta_3 (T^(upright("bad")) ,T^(3 D) )$], [boundary-support residual],
    bottomrule,
  )
},
  caption: [Toy data-support cases.],
) <tab:toy-data-support-cases>




#aod-remark[This toy shows why field dynamics must record boundary declarations and data-support class. A two-dimensional slice and a three-dimensional field are different declared support classes; residuals between them are projection or boundary-support residuals before any external target comparison is interpreted.]





== 3D Brownian phase-cycle $delta_3$ fixture <manual:brownian-phase-delta3-fixture>


#aod-noteblock("Data-support class")[This Brownian / tracer-motion fixture is a G3 time-resolved tracer-current fixture when the track declares time-ordered three-dimensional positions. A two-dimensional microscopy slice records its projection map or ablation cut.]


This fixture uses integerized three-dimensional trajectory data. A bacterium or tracer track is binned into $bb(Z)^3$; lagged displacements produce the active integer squared displacement

#math.equation(block: true, numbering: none, $ Q_i^(lr((n))) = (a_i^(lr((n))) )^2 + (b_i^(lr((n))) )^2 + (c_i^(lr((n))) )^2 in bb(Z)_(gt.eq 0) . $)

A declared mass/size adapter may supply a candidate monon-beat scale $beta_a$; the fixed fixture does not instantiate measured acquisition. The trajectory is tested by displacement-bin counts, phase-cycle counts $Q_i^(lr((n))) mod beta_a$, octant direction counts, integer ratios, and exact $delta_3$ residuals. The full 3D coordinate phase-cycle specification is given in #appref("manual:app:coordinate-phase-cycle-delta3").

The exact fixture path is

#math.equation(block: true, numbering: none, $ z_i in bb(Z)^3 arrow.r Delta z_i^(lr((n))) arrow.r Q_i^(lr((n))) arrow.r theta_i^(lr((n))) arrow.r O_(theta)^(lr((n))) arrow.r delta_3 . $)

The retained trace path is

#math.equation(block: true, numbering: none, $ Delta z_i^(lr((n))) arrow.r H T(h_i ;B_(upright("mot")) ) arrow.r R D_(h_i) arrow.r R C D_(h_i) arrow.r rho^D_(omega ,h_i) arrow.r SADARop_B . $)



Continuous summaries belong after the exact fixture as presentation or external maps.


#aod-noteblock("Source artifacts")[The source package includes the Brownian application script under #raw("manual/scripts") and the Brownian CSV rows under #raw("manual/data/brownian"):

#math.equation(block: true, numbering: none, $ mono("aod_brownian_3d_phase_delta3.py"), quad mono("displacement_q_counts.csv"), quad mono("phase_cycle_delta3.csv"), \ mono("octant_delta3.csv"), quad mono("integer_motion_ratios.csv"). $)

These Brownian application artifacts are aliases of the generic 3D coordinate phase-cycle fixture specified in #appref("manual:app:coordinate-phase-cycle-delta3").]


#aod-remark[Active coordinate: integerized three-dimensional displacement and phase-cycle count data,

#math.equation(block: true, numbering: none, $ z_i in bb(Z)^3 arrow.r Delta z_i^(lr((n))) arrow.r Q_i^(lr((n))) arrow.r theta_i^(lr((n))) arrow.r O_(theta)^(lr((n))) arrow.r delta_3 . $)

Continuous Brownian and diffusion-coefficient summaries are downstream presentation maps.]




=== Run-tumble tracer-current fixture <manual:run-tumble-tracer-current-fixture>


#aod-noteblock("Data-support class")[This run-tumble record is a G3 time-resolved tracer-current fixture. Its exact integer tallies are recorded as D0-style internal fixture audit coordinates when a comparator is declared.]


This fixture records a finite D.E.C. trace over four declared Hamming–1 edge slots, stores the selected signed edge steps as a four-channel accumulated trace, and projects that retained trace into a declared three-dimensional coordinate map before phase-cycle, octant, and $delta_3$ summaries are formed. Declare

#math.equation(block: true, numbering: none, $ B_(upright("RT")) = ( partial_T F_(upright("RT")) , omega_(20) ), wide omega_(20) = brace.l 0,1, dots.h ,20 brace.r , wide E_4 = brace.l e_1 ,e_2 ,e_3 ,e_4 brace.r . $)

The accumulated trace is

#math.equation(block: true, numbering: none, $ h_t in bb(Z)^4 , wide h_0 = (0,0,0,0), $)

with update

#math.equation(block: true, numbering: none, $ h_t = h_(t - 1) + sigma_t bold(upright(e))_(j_t) , wide j_t in brace.l 1,2,3,4 brace.r , wide sigma_t in brace.l - 1, + 1 brace.r . $)

The run/tumble mode is

#math.equation(block: true, numbering: none, $ m_t in brace.l upright("run"),upright("tumble") brace.r . $)

Run retains the active channel over the declared short window. Tumble reseats the active channel by the declared isotropic successor rule. The generated trace includes the initial row $t = 0$ with $h_0 = (0,0,0,0)$; run/tumble mode is assigned for the update rows $t gt.eq 1$. The projection map is declared before any three-dimensional quantity is reported:

#math.equation(block: true, numbering: none, $ pi_3 :bb(Z)^4 arrow.r bb(Z)^3 , wide z_t = pi_3 (h_t ). $)

For the released fixture,

#math.equation(block: true, numbering: none, $ pi_3 (h_1 ,h_2 ,h_3 ,h_4 ) = (h_1 ,h_2 ,h_3 ). $)

The fourth trace channel remains part of the $Q^2_4$ audit even when it is not carried by the released $pi_3$ projection. The active three-dimensional squared-displacement audit quantity is

#math.equation(block: true, numbering: none, $ Q^2_(3 D) (t) = x_t^2 + y_t^2 + z_t^2 , wide pi_3 (h_t ) = (x_t ,y_t ,z_t ). $)

The four-channel audit displacement is

#math.equation(block: true, numbering: none, $ Q^2_4 (t) = h_(1,t)^2 + h_(2,t)^2 + h_(3,t)^2 + h_(4,t)^2 . $)

Here $Q^2_(3 D)$ and $Q^2_4$ are local squared-displacement audit quantities, not $Q^D$ pending-overhang notation. The fixture records $Q^2_(3 D)$, $Q^2_4$, phase residues $Q^2_(3 D) mod beta_a$, octant counts, integer ratios, and exact $delta_3$ residuals. Continuous Brownian, diffusion, and stochastic-calculus summaries are downstream presentation maps.


#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (24.0%, 1fr),
    align: (left, left),
    table.header(
      toprule,
      [Item], [Declaration],
      midrule,
    ),
    [support], [four Hamming–1 edge slots $E_4 = brace.l e_1 ,e_2 ,e_3 ,e_4 brace.r$],
    [accumulated trace], [$h_t in bb(Z)^4$],
    [projection], [$pi_3 :bb(Z)^4 arrow.r bb(Z)^3$],
    [projected coordinate], [$z_t = pi_3 (h_t ) in bb(Z)^3$],
    [mode], [$m_t in brace.l upright("run"),upright("tumble") brace.r$],
    [run rule], [retain selected channel over declared short window],
    [tumble rule], [reseat selected channel by isotropic successor rule],
    [3D displacement], [$Q^2_(3 D) (t) = x_t^2 + y_t^2 + z_t^2$],
    [four-channel audit], [$Q^2_4 (t) = sum_(r = 1)^4 h_(r,t)^2$],
    [reports], [phase counts, octant counts, integer ratios, $delta_3$],
    bottomrule,
  )
}
  ],
  caption: [Run-tumble tracer-current declaration.],
) <tab:run-tumble-tracer-declaration>



#include "../tables/run_tumble_trace_table.typ"



#figure(
  kind: image, [
#include "../../lib/figures/manual/run_tumble_trace_3d_projection.typ"
  ],
  caption: [Run-tumble tracer-current projection. The plotted path is the declared $bb(Z)^3$ projection of the retained $bb(Z)^4$ accumulated trace. The finite $Q_4$ support remains the Hamming–1 edge-slot support.],
) <fig:run-tumble-tracer-current-projection>



#aod-noteblock("Source artifacts")[The source package includes the deterministic run-tumble generator #raw("manual/scripts/aod_run_tumble_3d_trace.py"), the generated trace table, the run-tumble CSV outputs under #raw("manual/data/run_tumble"), and the projection figure under #raw("manual/figures").]




== SPARC square-speed diagnostic <manual:sparc-square-speed-diagnostic>

The SPARC five-galaxy square-speed score is the current G0 radial shell field-dynamics diagnostic lane. This record uses SPARC radial rotation-curve rows, scores the coordinate $U = V^2$, forms $sigma_U = 2 V^(upright("obs")) sigma_V$ from the declared data uncertainty, and records $Delta U = U_(AO) - U^(upright("obs"))$ inside the G0 support class.
The SPARC benchmark supplies declared galaxy records

#math.equation(block: true, numbering: none, $ cal(D)_(upright("SPARC")) = brace.l G_i ,r_(i j) ,V^(upright("obs"))_(i j) , sigma_(V,i j) ,V^(upright("gas"))_(i j) ,V^(upright("disk"))_(i j) ,V^(upright("bulge"))_(i j) , dots.h brace.r . $)

The score coordinate is square speed:

#math.equation(block: true, numbering: none, $ U^(upright("obs"))_(g,j) = (V^(upright("obs"))_(g,j) )^2 , wide sigma_(U,g,j) = 2 V^(upright("obs"))_(g,j) sigma_(V,g,j) . $)

The displayed $sigma_U = 2 V^(upright("obs")) sigma_V$ is first-order
propagation about a positive measured speed, appropriate only where its
nonlinear remainder is negligible for the claimed precision. It is not an
exact square-map uncertainty. The present scores use this observation-only
diagnostic; input-proxy, distance, inclination, map and shared-source
contributions are not thereby zero. Exact finite laws or justified bounds
use the M3 routes in #secref("manual:scoped-errors-data-support"). The declared score target is $U^(upright("obs"))_(g,j)$, and benchmark input columns remain input data until the report map is evaluated. This G0 diagnostic uses nonnegative component proxies

#math.equation(block: true, numbering: none, $ U^k_(g,j) := (V^k_(g,j) )^2 , wide k in brace.l upright("gas"),upright("disk"),upright("bulge") brace.r . $)

SPARC's signed gas contribution is $V^(upright("gas")) bar.v V^(upright("gas")) bar.v$. The retained proxy $U^(upright("gas")) = (V^(upright("gas")) )^2$ preserves its magnitude and removes the contribution sign for negative source entries.

#math.equation(block: true, numbering: none, $ U^(upright("bar"))_(g,j) = U^(upright("gas"))_(g,j) + Upsilon_d U^(upright("disk"))_(g,j) + Upsilon_b U^(upright("bulge"))_(g,j) . $)

The release constants are frozen before residuals are computed:

#math.equation(block: true, numbering: none, $ Upsilon_d = frac(1, 2), wide Upsilon_b = frac(7, 10), wide K^U_(upright("ext")) = 8, wide J_(upright("norm")) = 1. $)

The retained-window ratio uses the scalar duration accessor, not the RCD coupling object:

#math.equation(block: true, numbering: none, $ lambda^(upright("ret"))_(g,j) := frac(rho^D_(omega ,g,j), rho^D_(g,j)). $)

The released field-dynamics support term is

#math.equation(block: true, numbering: none, $ D^(upright("BF"))_(g,j) = C_(upright("cap"),g,j) lambda^(upright("ret"))_(g,j) ( 1 + frac(upright("density")_(g,j), 16) ) ( 1 + frac(upright("gas/star")_(g,j), 16) ) ( 1 + frac(upright("bobbing")_(g,j), 64) ) J_(upright("norm")) . $)

In the five-galaxy G0/G1 diagnostic lane, the declared primary projection map uses

#math.equation(block: true, numbering: none, $ C_(upright("cap"),g,j) = r_(g,j) ( bar.v V^(upright("gas"))_(g,j) bar.v + bar.v V^(upright("disk"))_(g,j) bar.v + bar.v V^(upright("bulge"))_(g,j) bar.v ) , quad lambda^(upright("ret"))_(g,j) = 1, quad upright("density")_(g,j) = upright("gas/star")_(g,j) = upright("bobbing")_(g,j) = 0. $)

This neutral modifier convention belongs to the declared radial projection map. G1/G2/G3 packages carry angular, vertical, or time-flow fields through declared source or proxy rows.
The external square-speed map is

#math.equation(block: true, numbering: none, $ U_(g,j, AO) = U^(upright("bar"))_(g,j) + K^U_(upright("ext")) D^(upright("BF"))_(g,j) . $)

Here $K^U_(upright("ext"))$ is a quarantined external map coefficient frozen before scoring and used only by the external-comparison layer.

#math.equation(block: true, numbering: none, $ op("scope")(K^U_(upright("ext")) ) = "external square-speed value map", wide [K^U_(upright("ext")) ] = frac((upright("km/s"))^2, upright("kpc") dot.op (upright("km/s"))) = frac(upright("km/s"), upright("kpc")). $)



#aod-literature-note[SPARC benchmark: SPARC database #aod-cite("sparc-database"), Lelli et al. #aod-cite("lelli-sparc-2016").]


#aod-noteblock("Data-support class")[The SPARC five-galaxy lane instantiates a G0 radial shell data-support class. G0 active input fields are $G_i ,r_(i j) ,V^(upright("obs"))_(i j) , sigma_(V,i j) ,V^(upright("gas"))_(i j) ,V^(upright("disk"))_(i j) ,V^(upright("bulge"))_(i j)$. The report coordinate is $U = (V^(upright("obs")) )^2$, $sigma_U = 2 V^(upright("obs")) sigma_V$, and $Delta U = U_(AO) - U^(upright("obs"))$. G1/G2/G3 packages carry angular, vertical, or time-flow fields through declared source or proxy rows.]



== SPARC five-galaxy scored records <manual:sparc-five-galaxy-scored>

The five scored records are

#math.equation(block: true, numbering: none, $ brace.l upright("NGC2403"),upright("NGC3198"),upright("NGC6503"),upright("NGC2841"),upright("DDO154") brace.r . $)

Data files, scored outputs, and the regeneration script are included in the source package:

#math.equation(block: true, numbering: none, $ & mono("manual/data/sparc"), \ & mono("manual/data/derived/sparc_five_galaxy_per_bin.csv"), \ & mono("manual/data/derived/sparc_five_galaxy_per_galaxy.csv"), \ & mono("manual/scripts/score_sparc_field_dynamics.py"). $)


#aod-remark[The SPARC five-galaxy scored records are generated from the included rotation-curve files and the frozen declaration constants listed in this section.]


#math.equation(block: true, numbering: none, $ Delta U_(g,j) = U_(g,j, AO) - U^(upright("obs"))_(g,j) , wide z^U_(g,j) = frac(Delta U_(g,j), sigma_(U,g,j)). $)


#math.equation(block: true, numbering: none, $ chi^2_(U,g) = sum_j (z^U_(g,j) )^2 , quad M A E_(U,g) = frac(1, N_g) sum_j bar.v Delta U_(g,j) bar.v , quad M S E_(U,g) = frac(1, N_g) sum_j ( Delta U_(g,j) )^2 . $)


#math.equation(block: true, numbering: none, $ M A P E_(U,g) = frac(100, N_g) sum_j bar.v frac(Delta U_(g,j), U^(upright("obs"))_(g,j)) bar.v , wide U^(upright("obs"))_(g,j) > 0. $)

Bins are excluded only by a predeclared data-quality rule or by a predeclared denominator floor.

#include "../tables/sparc_summary_table.typ"


#figure(
  kind: image, [
#include "../../lib/figures/manual/sparc_declaration_controls.typ"
  ],
  caption: [SPARC carried declaration-control scores. The four values in #raw("sparc_declaration_controls.csv") are frozen comparison records; their variant recipes and aggregation rule are not supplied. Primary per-bin and per-galaxy scores are computed separately by the declared map.],
) <fig:manual-sparc-controls>


#figure(
  kind: image, [
#include "../../lib/figures/manual/sparc_square_speed_comparison.typ"
  ],
  caption: [SPARC square-speed comparison for the NGC3198 display record. The scored coordinate is $U = V^2$.],
) <fig:manual-sparc-square-speed-comparison>


#figure(
  kind: image, [
#include "../../lib/figures/manual/sparc_square_speed_residuals.typ"
  ],
  caption: [SPARC square-speed residuals for the NGC3198 display record. The residual is $Delta U = U_(AO) - U_(upright("obs"))$.],
) <fig:manual-sparc-residuals>


#figure(
  kind: image, [
#include "../../lib/figures/manual/sparc_display_speed_view.typ"
  ],
  caption: [Display speed view. This presentation view uses $V_(upright("disp")) = sqrt(U)$ after scoring; the score coordinate is $U$.],
) <fig:manual-sparc-display-speed>



== Tau ring diagnostic fixture <manual:tau-ring-diagnostic>

The Tau ring fixture carries frozen $S_(tau)$, $S_(tau ,upright("ring"))$, missing-fraction, and winner-margin records from #raw("manual/data/derived/tau_ring_diagnostic.csv").

#math.equation(block: true, numbering: none, $ cal(K)_(tau) = brace.l 1":"2":"8,1":"2":"9_(upright("yro")) ,1":"2":"10,3":"3":"8 brace.r . $)


#math.equation(block: true, numbering: none, $ K_(tau)^(star) = arg min_(K in cal(K)_(tau)) bar.v S_(tau ,upright("ring")) (K) bar.v . $)

Winner lookup in the supplied diagnostic selects

#aod-boxed($ display(K_(tau)^(star) = 1":"2":"9_(upright("yro")) = upright("Dimonnanyro").) $)

For the primary lane,

#math.equation(block: true, numbering: none, $ 1":"2":"9: wide S_(tau) = - 0.036807, wide S_(tau ,upright("ring")) = - 0.105804. $)

The missing-burden diagnostic records the exact ratio

#math.equation(block: true, numbering: none, $ upright("miss")_(tau) (1":"2":"9_(upright("yro")) ) = frac(31, 50), wide upright("missing_fraction_display") = 0.62. $)


#aod-noteblock("Precision note")[Support identities and candidate declarations are exact. Plotted scores are presentation decimals carried by the frozen diagnostic CSV.]


#aod-noteblock("Source artifacts")[The depth-3 rows in #raw("manual/data/tau/aod_tau_fractal_ring_summary.csv") preserve this winner. The originating calculation recipe is not supplied. Compact missing fractions and depth-indexed source fractions remain separate records; their adapter is not supplied.]


#figure(
  kind: image, [
#include "../../lib/figures/manual/tau_ring_support_score.typ"
  ],
  caption: [Tau ring support score. The ring diagnostic preserves $1":"2":"9_(upright("yro"))$ / Dimonnanyro as the closest candidate.],
) <fig:manual-tau-ring-score>


#figure(
  kind: image, [
#include "../../lib/figures/manual/tau_missing_burden_diagnostic.typ"
  ],
  caption: [Tau missing-burden diagnostic. The plot renders the exact missing-burden ratio $31 slash 50$ as the presentation value $0.62$ for the $1":"2":"9_(upright("yro"))$ / Dimonnanyro row.],
) <fig:manual-tau-missing>


#figure(
  kind: image, [
#include "../../lib/figures/manual/tau_support_residuals.typ"
  ],
  caption: [Tau-support residuals against the declared support-score target.],
) <fig:manual-tau-residuals>


#figure(
  kind: image, [
#include "../../lib/figures/manual/tau_declaration_controls.typ"
  ],
  caption: [Tau declaration controls. Labels are declaration controls for the internal diagnostic lane.],
) <fig:manual-tau-controls>



== Milky Way / Gaia follow-up declaration <manual:mw-gaia-followup>

The Sol bobbing record is recorded as a field dynamics diagnostic.

#math.equation(block: true, numbering: none, $ B_(upright("Sol")) bar.v t = ( partial_T R_(upright("Sol")) (t), omega_(upright("Sol")) bar.v t). $)


#math.equation(block: true, numbering: none, $ Phi^D_(partial_T R,upright("mov")) (t) = Phi^D_(upright("cross")) (t) - Phi^D_(upright("sweep")) (t) + Phi^D_(upright("shedding")) (t). $)

A Gaia follow-up comparison is recorded after a benchmark target record is supplied.



== Orbital-retention field-dynamics fixture plan <manual:orbital-retention-field-dynamics-fixture>

Data-support class: G2/G3 retention-first field-dynamics fixture. Its sequence is

#math.equation(block: true, numbering: none, $ & "medium setup" arrow.r "flip/fizz classification" arrow.r "range-prioritized SADAR", \ & "capacity seating" arrow.r "orbital retention" arrow.r #[$delta_3$ class tally], \ & "optional "U" diagnostic". $)

The fixture declares the flip classifier inside the manual/application layer:

#math.equation(block: true, numbering: none, $ op("FlipClass")_(e,c,t) in brace.l upright("early_coupling"),upright("fizz"),upright("pending"),upright("sheddic_route") brace.r . $)

The early-coupling indicator is

#math.equation(block: true, numbering: none, $ G^(upright("early"))_(e,c,t) = bold(1)[ rho^D_(omega ,e,c,t) > 0] thin bold(1)[Q^D_(e,c,t) < Q_(max) ] thin C^(theta)_(e,c,t) thin Z^(upright("imp"))_(e,c,t) thin bold(1)[ Delta A_(e,c,t) eq.not 0]. $)

When $G^(upright("early"))_(e,c,t) > 0$, the fixture records early coupling. Fizz records successor motion / background-continuation jitter. Pending records retained return carried over the current window. The class $upright("sheddic_route")$ records a flip carried through a declared sheddic path.



#aod-paragraph[Orbital-retention input provenance gate.]
Before a scored orbital-retention run, the fixture records the data provenance of every field component used by the retained calculation. The input package records radial support rows; three-dimensional density fields; gas/stellar velocity fields; momentum fields; time-window/slosh fields; capacity rule; coupling family; sheddic-route declaration; and external value map when used. SPARC radial rows may populate the radial-support component. Three-dimensional density, velocity, current, and time-flow components are populated by their own declared source rows or proxy rows before scoring.



#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (19.00fr, 17.00fr, 17.00fr, 20.00fr, 9.00fr),
    align: (left, left, left, left, left),
    table.header(
      toprule,
      [Field component], [Source], [Support status], [Uncertainty status], [Scored],
      midrule,
    ),
    [stellar radial support], [SPARC radial model], [SPARC-supported radial], [radial source row], [diagnostic],
    [stars, full medium], [3D stellar density], [external 3D], [measured / proxy], [if declared],
    [gas, full medium], [H I / H$alpha$ / IFU field], [external 3D], [channel / velocity uncertainty], [yes, if declared],
    [core / background], [model or survey], [latent / proxy], [proxy recorded], [conditional],
    [current-cycle family], [A$Omega$D range edges], [declared proxy], [declaration audit], [internal],
    [time-flow / slosh], [kinematic window], [external 3D / latent], [cadence / window], [conditional],
    [external value map], [quarantined map], [declared proxy], [frozen before scoring], [external only],
    bottomrule,
  )
},
  caption: [Orbital-retention input provenance gate.],
) <tab:orbital-retention-input-provenance>




#aod-remark[A scored orbital-retention run records source, support status, uncertainty status, and whether each component is used for scoring before residuals are interpreted.]




#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (8.00fr, 34.00fr, 42.00fr),
    align: (left, left, left),
    table.header(
      toprule,
      [No.], [Sheet], [Purpose],
      midrule,
    ),
    [00], [Declarations], [Freeze declarations before scoring.],
    [01], [Cell grid 3D], [Declare the retained 3D cell grid.],
    [02], [Input density fields], [Declare star/gas/core/background/current density inputs and source/status records.],
    [03], [Fractal range / max field support], [Compute fractal range and maximum supported field count.],
    [04], [Field regime], [Declare gas/fluid/fizz regime.],
    [05], [Chiral flip: early coupling vs fizz], [Classify flips as early coupling, fizz, pending, or sheddic route.],
    [06], [Range edge sets], [Build range-prioritized coupling families.],
    [07], [SADAR coupling / pressure / velocity], [Compute SADAR coupling, pressure, and motion quantities.],
    [08], [Capacity seating], [Seat capacity by range and closure state.],
    [09], [Hinge shift / partial coupling], [Record hinge shift and partial coupling.],
    [10], [Slosh / sheddic / pending], [Record slosh, sheddic routing, and pending return.],
    [11], [Orbital retention class], [Classify orbital retention before projection.],
    [12], [Delta3 retention tallies], [Record exact $delta_3$ retention tallies.],
    [13], [U projection diagnostic], [Optional square-speed diagnostic after retention scoring.],
    [14], [Audit], [Check declaration, retention, projection, and error layers.],
    bottomrule,
  )
},
  caption: [Orbital-retention field-dynamics fixture spine.],
) <tab:orbital-retention-fixture-spine>




#aod-remark[The SPARC square-speed lane is a G0 radial projection diagnostic. The orbital-retention fixture is the G2/G3 retention-first simulation path. Projection to $U$ follows retention, capacity seating, and $delta_3$ tallies.]



== Completion requirements <manual:field-dynamics-completion-requirements>

A SPARC score record is arithmetically complete when the data file, declaration constants, square-speed target, residuals, and score metrics are present. A Tau ring fixture is complete when the candidate set, scores, missing fraction, and precision note are present. Display speed is a presentation view only. The orbital-retention field-dynamics fixture is complete when it records medium setup, flip/fizz classification, range-prioritized SADAR, capacity seating, retention class, and $delta_3$ tallies.
These are record-completeness conditions. Replay also requires the bound
producer and all operands; physical validation additionally requires the
source/uncertainty and independent-comparison evidence in
#secref("manual:prediction-test-registry"). Carried Tau scores and unsupported
declaration-control recipes remain carried records.
