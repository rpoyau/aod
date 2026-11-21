// Native Typst port of appendices/B_curling_curls.tex (verbatim scientific content).
#import "../preamble.typ": *

= Curling-curls <app:curling-curls>



== Curl-closure names <app:cc-naming-conventions>



=== Hinge triad <app:cc-hinge-triad>

The support relation and its ternary roles are #eqref("eq:hinge-grammar");
committed predecessor/crown/successor-horizon roles are #eqref("eq:hinge-triad").


=== Curl <app:cc-curl>

Definition: #secref("subsec:curl").


=== Nested curl <app:cc-nested-curl>

Definition: #secref("subsec:nested-curl").


=== Pin-curl <app:cc-pin-curl>

Definition: #secref("subsec:pin-curl").


=== Curling curls <app:cc-curling-curls>

Definition: #secref("subsec:curling-curls").


=== Monon <app:cc-monon>

The primitive monon is #eqref("eq:monon-cycle").


=== Dion <app:cc-dion>

Two oriented signatures: #secref("subsec:dion").


=== Duon <app:cc-duon-duad-cycle>

Resolved constructor: #eqref("eq:duon-current"); twelve-variant count:
#secref("subsec:duon-current-cell").


=== Duad <app:cc-duad>

Seating: #secref("subsec:duad"); open/closed notation:
#secref("subsec:e2-duon") and #secref("subsec:e2-duad").


=== Trion / tetrion / tetron / tetratrion / tetrad <app:cc-tetrion-tetron-tetratrion>


#math.equation(block: true, numbering: none, $ upright("tetrion") = "bare four-cycle / four-pivot return closure", $)


#math.equation(block: true, numbering: none, $ upright("tetron") "is the "E_4 " enclosure of "#secref("subsec:e4-tetron"), $)


#math.equation(block: true, numbering: none, $ upright("tetratrion") = 4 times upright("trion") = 3:4. $)

Standalone trion is the threefold core unit. A tetrad is the seated tetron closure. Admission of each named entry resolves its scope, lineage and certificate through #eqref("eq:motif-admission").


== Curling curls <app:cc-families>



#figure(
  kind: table, [
#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (16.00fr, 23.00fr, 18.00fr, 25.00fr),
    align: (left, left, left, left),
    table.header(
      toprule,
      [Numeric form], [Family name], [Stem], [Meaning],
      midrule,
    ),
    [$1:2$], [$upright("Dimonon")$], [$upright("Dimon")$], [$2 times upright("monon")$],
    [$3:1$], [$upright("Trio")$], [$upright("Trio")$], [$1 times upright("trion")$],
    [$3:2$], [$upright("Ditrion")$], [$upright("Ditrio")$], [$2 times upright("trion")$],
    [$3:3$], [$upright("Tritrion")$], [$upright("Tritrio")$], [$3 times upright("trion")$],
    [$3:4$], [$upright("Tetratrion")$], [$upright("Tetratrio")$], [$4 times upright("trion")$],
    bottomrule,
  )
}
  ],
  caption: [Curling-curl family names.],
) <tab:cc-families>




== Support-enclosure names <app:cc-support-enclosure-names>



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
      [Order], [Name], [Role],
      midrule,
    ),
    [$sans("C")_6$], [hexon], [first outer enclosure],
    [$sans("C")_8$], [octon], [lifted outer enclosure],
    [$sans("C")_(10)$], [decon], [higher lifted outer enclosure],
    bottomrule,
  )
}
  ],
  caption: [Outer enclosure names.],
) <tab:cc-support-enclosure-names>



== Count compression <app:cc-count-compression>



=== Count basis <app:cc-count-basis>


#math.equation(block: true, numbering: none, $ cal(B)_(upright("curl")) = (3:3, 3:4, 1:2) = (upright("Tritrio"), upright("Tetratrio"), upright("Dimon")). $)

A count form $a:b:c::L$ means

#math.equation(block: true, numbering: none, $ upright("Tritrio")^a ::upright("Tetratrio")^b ::upright("Dimon")^c ::op("out")(L). $)



=== Basic shared hexon <app:cc-basic-shared-hexon>


#math.equation(block: true, numbering: none, $ 1:1:0::6 = upright("Tritrio")::upright("Tetratrio")::upright("hexon"). $)


=== Filled shared enclosures <app:cc-filled-shared-enclosures>


Filled shared enclosures have count form $m:m:0::2 m$, $m gt.eq 3$, under
#secref("subsec:filled-shared-enclosures") and the count basis above.



== Active naming set <app:cc-active-naming-set>
#aod-anchor(<app:cc-standalone-enclosed-names>)



#figure(
  kind: table, [
#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (22.00fr, 48.00fr, 20.00fr),
    align: (left, left, left),
    table.header(
      toprule,
      [Category], [Entries], [Anchor],
      midrule,
    ),
    [Hinge/closure], [$sans("H")_3$, Monon], [#eqref("eq:hinge-grammar")],
    [Branch pattern], [Dion $D_(alpha) ,D_(Omega)$], [#secref("subsec:dion")],
    [Composite closure], [Dimonon $= 2 thin upright("Monon")$], [#eqref("eq:motif-grammar")],
    [Returned-current support], [Duon $D_i mu_M D_j$, with bound pivot], [#eqref("eq:duon-current")],
    [Realized current], [Carried crossings on admitted Duon support and a declared window], [#eqref("eq:window-current")],
    [Seated current state], [Duad], [#secref("subsec:duad")],
    [Recurring current wave], [Running Duon wave, certified recurrence and orientation], [#eqref("eq:wave-identity")],
    [Standing organization], [Bound opposite recurring lineages with declared balance], [Native running and standing classifications, #secref("eq:native-running-standing")],
    [Four-cycle / four-enclosure terms], [tetrion, tetron $E_4$, tetratrion $3:4$, tetrad], [#appref("app:cc-tetrion-tetron-tetratrion")],
    [Curling curls], [Dimonon, Trio, Ditrion, Tritrion, Tetratrion], [#appref("app:cc-families")],
    [Outer enclosures], [hexon, octon, decon], [#appref("app:cc-support-enclosure-names")],
    [Count forms], [$1:1:0::6$, filled shared enclosures], [#appref("app:cc-count-compression")],
    bottomrule,
  )
}
  ],
  caption: [Active naming index.],
) <tab:cc-active-naming-index>
