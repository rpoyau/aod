// Native Typst port of manual/sections/09_prediction_test_fixture_registry.tex (verbatim scientific content).
#import "../preamble.typ": *

= Prediction-Test Fixture Registry <manual:prediction-test-registry>



#aod-paragraph[Reading the registry.]
Data support describes the supplied coordinates. Record completeness lists
the supplied calculation/comparison stages; replay requires their bound
producer and operands; physical evidence requires source uncertainty and a
properly classified comparison. These are separate properties. Each row
below links through its application card to the common method in
#secref("manual:calculation-spine"); a carried map or aggregate is not promoted
by a source-only replay.



#aod-noteblock("Scope")[This registry records completion fields for manual fixtures and comparisons. Rows carry their data-support class, active fields, required A$Omega$ calculation, and audit artifact.]






#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (16.00fr, 8.00fr, 16.00fr, 25.00fr, 18.00fr),
    align: (left, left, left, left, left),
    table.header(
      toprule,
      [Record], [Class], [Active fields], [Required A$Omega$ calculation], [Artifact],
      midrule,
    ),
    [Hydrogen shell radii], [O0], [target rows], [shell-ratio record for $S_n$], [radius-ratio table],
    [Hydrogen shell energies], [O0], [target rows], [$Delta hat(P)^D$, ratio, target], [Lyman / Balmer / Paschen tables],
    [Short-window $1":"2":"7$], [D0], [integer fixture fields], [$P^D , Delta^(upright("close")) ,X_(upright("shedding"))$], [closure table],
    [Short-window $1":"2":"9$], [D0], [integer fixture fields], [$P^D ,C^(upright("close")) ,X_(upright("shedding"))$], [surplus table],
    [Toy 1 field-ring fixture], [D0], [integer comparator bins], [$T^0 ,C^(times) ,T^(times) ,O, Delta^(bb(Z)) , delta_3$], [$delta_3$ fixture table],
    [Neuronal-ring benchmark acquisition], [L2], [acquisition fields], [$cal(S)_(upright("neuro")) ,O_k$], [acquisition declaration],
    [Electron], [O0], [measured target rows], [$nu_(AO) ,E_(upright("ext"))$ for $1":"2":"6$], [external target declared],
    [Muon], [O0], [measured target rows], [$nu_(AO) ,E_(upright("ext"))$ for $1":"2":"8$], [external target declared],
    [Tau], [O0/D0], [measured target rows], [$nu_(AO) ,E_(upright("ext"))$ for $1":"2":"9_(upright("yro"))$ / Dimonnanyro], [surplus fixture + external target declared],
    [Proton], [O0], [measured target rows], [$nu_(AO) ,E_(upright("ext"))$ for $3":"3":"6$], [closed fixture + external target declared],
    [Neutron], [O0], [measured target rows], [$nu_(AO) ,E_(upright("ext"))$ for $3":"4":"6$], [closed fixture + external target declared],
    [B / $B_s$ / $B_c$], [O0], [measured target rows], [$nu_(AO) ,E_(upright("ext"))$ for Ditrion records], [debris fixture + external target declared],
    [Boundary current], [D0], [declared boundary/current fields], [$Phi ,J,P^D ,bold(A)_F$], [substitution table],
    [Field tunnelling hinge-slide fixture], [D0], [integer fixture fields], [$op("adm")(e_0 ;B bar.v t) = 0$, slide kernel, $rho^D_(omega)$, $T^D_(upright("tunnel"))$], [D.E.C. ledger table],
    [3D Brownian phase-cycle fixture], [G3/D0], [3D coordinate track fields], [$z_i in bb(Z)^3$, $Delta z_i^(lr((n)))$, $Q_i^(lr((n)))$, phase counts, octant counts, $delta_3$], [3D coordinate phase-cycle CSVs (Brownian application aliases), integer-ratio audit, and App. #bare-ref("manual:app:coordinate-phase-cycle-delta3")],
    [Run-tumble tracer-current fixture], [G3/D0], [mode $m_t$, selected channel $j_t$, sign $sigma_t$, accumulated trace $h_t in bb(Z)^4$, projection $pi_3 (h_t ) in bb(Z)^3$, $Q^2_(3 D)$, $Q^2_4$, phase counts, octant counts, $delta_3$], [$h_t = h_(t - 1) + sigma_t bold(e)_(j_t)$, $z_t = pi_3 (h_t )$, $Q^2_(3 D)$ and $Q^2_4$ audit calculations, phase-cycle and octant $delta_3$ tallies], [run-tumble trace CSV, phase-cycle $delta_3$, octant $delta_3$, integer-ratio audit, generated trace table, and App. #bare-ref("manual:app:coordinate-phase-cycle-delta3")],
    [Mercury perihelion], [O0], [observable-map target rows], [observable-map value, target, error], [solar table],
    [Solar light bending], [O0], [observable-map target rows], [observable-map value, target, error], [solar table],
    [Solar redshift], [O0], [observable-map target rows], [observable-map value, target, error], [solar table],
    [Earth–Moon orbital shell], [O0], [target data manifest], [Moon distance, speed, period records require numeric A$Omega$ values], [NASA target record],
    [Saturn ring-shell], [O0], [target data manifest], [ring-boundary and Cassini-division records require numeric A$Omega$ values], [NASA / ring-boundary target record],
    [SPARC five-galaxy square-speed diagnostic], [G0], [SPARC radial rows], [$U_(AO) (r)$, $Delta U$, $z^U$, $chi^2_U$, $M A E_U$, $M S E_U$, $M A P E_U$], [per-bin CSV, per-galaxy CSV, score table, and figures],
    [SPARC full-sample / extended benchmark], [G0/G1], [target data manifest], [full-sample $U_(AO) (r)$, $Delta U$, $z^U$, $chi^2_U$, $M A E_U$, $M S E_U$, $M A P E_U$], [extended benchmark package],
    [Orbital-retention field-dynamics fixture], [G2/G3], [G2/G3 input package], [medium setup, input-provenance gate, flip/fizz classifier, range SADAR, capacity seating, retention class, $delta_3$ tallies], [workbook spine and provenance tables],
    [Toy 1 lensing field-ring fixture], [L0], [integer comparator bins], [$T^0 ,C^(times) ,T^(times) ,O, Delta^(bb(Z)) , delta_3$], [manual galactic lensing plan],
    [SPARC5 lens-medium diagnostic], [L1], [radial lens-medium fields], [radial field-medium class tallies], [plan data and figures],
    [SWELLS K0 target acquisition], [L2], [target acquisition fields], [target tallies before prediction join], [target-side quarantine table],
    [SWELLS K1 retained baseline], [L1/L2], [baseline target fields], [$delta_3$ comparison tallies], [K1 diagnostic table],
    [SWELLS K2/K3], [L1/L2], [audit diagnostics], [$delta_3$ comparison tallies], [K2/K3 audit table],
    [K4 galactic lensing gate], [L3], [higher-resolution input manifest], [independent medium data and target quarantine], [K4 input-gate table],
    [L3 lensing input package], [L3], [L3 input manifest], [independent 3D medium fields, time-flow inputs, radiation-current gates, target-side quarantine, null controls], [lens residuals after A$Omega$ values freeze],
    [Tritrioseptyro Higgs-support fixture], [D0/O0], [AFC trace rows + route detector], [candidate: $3":"3":"7_(upright("yro"))$; frozen map: $R D thin 2^(L + 4)$; mapped mass: $124.928$ GeV; comparison layer: declared Higgs mass targets], [next layer: production-channel and decay-channel residual tables],
    bottomrule,
  )
},
  caption: [Prediction-test fixture registry.],
) <tab:manual-prediction-test-registry>




#align(center)[

#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (22.0%, 1fr, 1fr),
    align: (left, left, left),
    table.header(
      toprule,
      [Family], [Supplied stages and owner], [Remaining evidence],
      midrule,
    ),
    [Native closure and recurrence], [Exact native constructors and hostile controls,
#secref("manual:m1-native-fixtures")], [Physical acquisition/calibration when used],
    [Awareness controls], [Matched exact state, removal/restoration and passive controls,
#secref("manual:m2-awareness-fixtures")], [No empirical awareness claim; historical missing sources retained],
    [Measures, mappings and observation], [Cells, typed maps and temporal/metrology records], [Per-route source, uncertainty, context and reduction obligations],
    [Exact applications], [D.E.C., boundary and integer-track fixtures], [Physical adapters; slit path generator and surplus route certificates where absent],
    [Rest energy/hydrogen], [Exact accessors/ratios and target records], [History/rate map, target/source conventions and joint uncertainty],
    [Solar], [Carried O0 values and residuals], [Native evaluator and source-bound observed targets],
    [SPARC], [Source radial rows and replayed map scores], [Proxy/model uncertainty; observation-only scores retained],
    [Tau/lensing], [Carried scores and aggregate tables; staged gates], [Producer/cohort/selection lineage and joint target uncertainty],
    [Neuronal/orbital/L3], [Acquisition and required-input schemas], [Actual input, output, residual, uncertainty and replay records],
    bottomrule,
  )
}
]

Source identity, pre-exposure freeze or retrospective exposure, and
input/output uncertainty belong to each application record. Missing
information remains an explicit obligation; a support-class label does not
complete it.




#aod-noteblock("Data-support registry note")[Registry rows are read together with data-support class. A row carries active fields, an A$Omega$ calculation or report map, and an artifact. Residuals are scoped to the declared class.]



#aod-literature-note[Earth–Moon orbital target: NASA #aod-cite("nasa-moon-by-numbers");
Saturn ring/Cassini target: NASA #aod-cite("nasa-cassini-division");
SPARC five-galaxy diagnostic: SPARC database and Lelli et al. #aod-cite("sparc-database,lelli-sparc-2016").]



== Neuronal-ring benchmark acquisition <manual:registry:neuronal-benchmark-acquisition>

This subsection is an uninstantiated acquisition schema for a field-ring benchmark; no measured dataset or completed comparison is supplied. For a biological benchmark acquisition, declare

#math.equation(block: true, numbering: none, $ cal(S)_(upright("neuro")) = (cal(M), Delta t,cal(B)_(upright("spike")) , kappa_k , Theta_(upright("stim")) , Omega_(upright("meas")) ). $)

Here

#math.equation(block: true, numbering: none, $ cal(M) in brace.l "spike counts", "calcium bins", "voltage bins", "LFP bins" brace.r $)

is the measurement mode, $Delta t$ is the bin width, $cal(B)_(upright("spike"))$ is the bin extraction rule, $kappa_k$ is the declared bin observation factor, $Theta_(upright("stim"))$ is the gate-stimulus declaration, and $Omega_(upright("meas"))$ is the measurement window.
The fixture comparator is

#math.equation(block: true, numbering: none, $ O_k = cal(S)_(upright("neuro")) (k; Omega_(upright("meas")) ). $)



#aod-noteblock("Artifact")[$cal(S)_(upright("neuro")) , T_k^0 , C_(a b,k)^(times) (B), T_k^(times) , O_k , Delta_k^(bb(Z)) , delta_(3,k)$. If $O_k$ is continuous or averaged, write $O_k = x_k plus.minus sigma_k$ and treat the comparison as a measured acquisition value map with a decimal precision record.]


#aod-noteblock("Completion rule")[A completed neuronal benchmark requires bound acquisition data, input/map uncertainty, the independent gate sum $T^0_k = S^(lr((a)))_k + S^(lr((b)))_k$, computed $C_(a b,k)^(times) (B)$ and $T_k^(times)$, observed $O_k$, residuals and their joint uncertainty, with reproducible source records.]


#aod-remark[This schema specifies the recurrent-ring comparison requirements; it becomes a measured benchmark only after the actual acquisition and output stages are supplied.]





== SPARC benchmark declaration <manual:registry:sparc>

The SPARC five-galaxy diagnostic is carried as a current field-dynamics square-speed diagnostic lane. The full protocol and scored records are given in #secref("manual:field-dynamics-applications").

#math.equation(block: true, numbering: none, $ cal(D)_(upright("SPARC")) = brace.l G_i ,r_(i j) ,V^(upright("obs"))_(i j) , sigma_(V,i j) ,V^(upright("gas"))_(i j) ,V^(upright("disk"))_(i j) ,V^(upright("bulge"))_(i j) ,L_(3.6,i) , dots.h brace.r . $)

The active comparison coordinate is square speed:

#math.equation(block: true, numbering: none, $ U^(upright("obs"))_(i j) = (V^(upright("obs"))_(i j) )^2 , wide U_(i j, AO) = SADARop^U_(B_i) (C_(i,j) ). $)

For each radial bin, the completed record carries

#math.equation(block: true, numbering: none, $ U_(i j, AO) , wide Delta U_(i j) = U_(i j, AO) - U^(upright("obs"))_(i j) , wide z^U_(i j) = Delta U_(i j) slash sigma_(U,i j) . $)

For each galaxy, the completed record carries

#math.equation(block: true, numbering: none, $ chi^2_U , wide overline(Delta U), wide M A E_U , wide M S E_U , wide M A P E_U . $)



#aod-literature-note[SPARC benchmark: SPARC database #aod-cite("sparc-database"), Lelli et al. #aod-cite("lelli-sparc-2016").]



#aod-noteblock("Completion rule")[External-comparison rows record numeric map value, target, residual, percent error, and audit hook. Observable-map fixture rows record map value, target, residual, percent error, citation, fixture status, and audit hook. Benchmark-dataset rows record benchmark data table, A$Omega$ calculation row, report coordinate, residual, and audit hook. Cross-return rows record declared $C^(times)_(a b,k) (B)$.]




#aod-noteblock("Registry note")[Decimal precision records accompany manual artifacts that use decimal target/value-map values.]
