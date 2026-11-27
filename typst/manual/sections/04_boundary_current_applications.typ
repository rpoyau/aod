// Native Typst port of manual/sections/04_boundary_current_applications.tex (verbatim scientific content).
#import "../preamble.typ": *

= Boundary Current Applications <manual:boundary-current-applications>



#aod-paragraph[Calculation card.]
The D0 substitution declares $C_3 = 3$, $rho^D = 5$, window length $4$, and
$A_(12) = 1 slash 3$: clipping gives $p^D = 12$, flux $+ 4$, and reverse flux
$- 4$. Executed in exact zero-float arithmetic by vector #raw("RC-032")
(#raw("scoped_wire_and_moving_boundary"),
#raw("scoped_wire_and_moving_boundary_walk.csv")), the moving-boundary balance
evaluates $Phi^D_(partial R,upright("mov")) = 8 - 3 + 2 = 7$, and the four-cut
($52 dots.h 55$) $1":"2":"6$ electron-above-wire walk yields exact union
cancellation $0$ alongside realized electron current trajectory
$4 arrow.r 4 arrow.r 8 arrow.r 13$ (unchanged across uncoupled cut $53$).
These exact D0 conditional results and their orientation/Stokes comparators
remain inline below. External wire, fluid, and plasma apparatus remain
strictly quarantined: any laboratory experiment must supply its own state
preparation, observation adapter, and declared uncertainty; none is
instantiated here. The common method is #secref("manual:calculation-spine").



#aod-noteblock("Data-support class")[Boundary-current applications are D0 exact scoped-flux fixtures. External report maps carry separate comparison rows. Errors are Stokes residuals, moving-boundary identity residuals, current-split residuals, and sheddic-route conservation residuals.]


#aod-noteblock("Scope")[This section applies the same scoped A$Omega$D pressure-resolved flux calculation to wire, fluid, plasma, shell-electromagnetic comparison, and phase-fluid SADAR records. The declared boundary selects the application case of the declared-scope calculus.]



== Shared scoped-flux setup <manual:boundary-current:shared-setup>

Declare an application scope

#math.equation(block: true, numbering: none, $ bold(upright(a)) tack.r (F,R, partial R, omega ), wide B = ( partial F, omega ). $)

The scoped A$Omega$D pressure-resolved flux is

#math.equation(block: true, numbering: none, $ phi.alt_(i j) (B) = p^D_(i j) (B)A_(i j) (B), $)

with

#math.equation(block: true, numbering: none, $ p^D_(i j) (B) = C_(3,i j) rho^D_(omega ,i j) (B), wide rho^D_(omega ,i j) (B) = min ( rho^D_(i j) (B), bar.v omega bar.v_(i j) ), $)


#math.equation(block: true, numbering: none, $ A_(i j) (B) = Delta chi^(upright("lag"))_(i j) (B)i_(i j) (B). $)

The slice flux and window current are

#math.equation(block: true, numbering: none, $ Phi^D_(partial R) (t;B bar.v_t ) = sum_(e in partial R(t)) phi.alt_e (B bar.v_t ), $)


#math.equation(block: true, numbering: none, $ J^D_(partial R) ( omega ;B) = sum_(t in omega) Phi^D_(partial R) (t;B bar.v_t ). $)

For moving boundaries use

#math.equation(block: true, numbering: none, $ Phi^D_(partial R,upright("mov")) (t) = Phi^D_(upright("cross")) (t) - Phi^D_(upright("sweep")) (t) + Phi^D_(upright("shedding")) (t). $)

The directional SADAR quantity remains

#math.equation(block: true, numbering: none, $ bold(upright(A))_F (B) = sum_((i,j) in F(B)) phi.alt_(i j) (B), wide op("motion")_(F,k + 1) (B) = (S^W_(F,k) ,S^W_(F,k + 1) ). $)



#figure(
  kind: image, [
#include "../../lib/diagrams/boundary_current_spine.typ"
  ],
  caption: [Boundary-current application spine. The same scoped flux produces slice flux, moving-boundary flux, window current, and the SADAR attention vector on the declared boundary/window.],
) <fig:manual-boundary-current-spine>



== Canonical worked substitution <manual:boundary-current:worked-substitution>

Use the signed moving-boundary calculation

#math.equation(block: true, numbering: none, $ Phi^D_(upright("cross")) = 8, wide Phi^D_(upright("sweep")) = 3, wide Phi^D_(upright("shedding")) = 2. $)

Then

#math.equation(block: true, numbering: none, $ Phi^D_(partial R,upright("mov")) = 8 - 3 + 2 = 7. $)

For a channel $(1,2)$, declare

#math.equation(block: true, numbering: none, $ C_(3,12) = 3, wide rho^D_(12) (B) = 5, wide bar.v omega bar.v_(12) = 4, wide A_(12) (B) = frac(1, 3). $)

Then

#math.equation(block: true, numbering: none, $ rho^D_(omega ,12) (B) = min (5,4) = 4, $)


#math.equation(block: true, numbering: none, $ p^D_(12) (B) = 3 dot.op 4 = 12, $)


#math.equation(block: true, numbering: none, $ phi.alt_(12) (B) = 12 dot.op frac(1, 3) = 4, wide phi.alt_(21) (B) = - 4. $)



#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto),
    align: (left, center),
    table.header(
      toprule,
      [Quantity], [Value],
      midrule,
    ),
    [$Phi^D_(upright("cross"))$], [$8$],
    [$Phi^D_(upright("sweep"))$], [$3$],
    [$Phi^D_(upright("shedding"))$], [$2$],
    [$Phi^D_(partial R,upright("mov"))$], [$8 - 3 + 2 = 7$],
    [$rho^D_(omega ,12) (B)$], [$min (5,4) = 4$],
    [$p^D_(12) (B)$], [$12$],
    [$A_(12) (B)$], [$1 slash 3$],
    [$phi.alt_(12) (B)$], [$4$],
    [$phi.alt_(21) (B)$], [$- 4$],
    bottomrule,
  )
}
  ],
  caption: [Canonical scoped-flux substitution.],
) <tab:manual-boundary-current-substitution>



== Wire boundary current <manual:boundary-current:wire>

Declare

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("wire")) tack.r (F_(upright("wire")) ,R_(upright("core")) , partial R_(upright("shell")) , omega_(upright("wire")) ), wide B_(upright("wire")) = ( partial F_(upright("wire")) , omega_(upright("wire")) ). $)

Here $F_(upright("wire"))$ is the conductor plus retained field shell, $R_(upright("core"))$ is the conductor/core region, and $partial R_(upright("shell"))$ is the shell boundary.
The wire record computes

#math.equation(block: true, numbering: none, $ Phi^D_(partial R) (t;B bar.v_t ), quad J^D_(partial R) ( omega ;B), quad P^D_F (B), quad bold(upright(A))_F (B), quad X_(upright("shedding")) (B). $)


#aod-remark[The wire case is a boundary-duon-current example. The surrounding field shell carries returned-current duration, pressure, and SADAR attention balance.]



== Fluid interface dynamics <manual:boundary-current:fluid>

Declare

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("fluid")) tack.r (F_(upright("fluid")) ,R_(upright("water")) , partial R_(upright("interface")) , omega_(upright("fluid")) ), wide B_(upright("fluid")) = ( partial F_(upright("fluid")) , omega_(upright("fluid")) ). $)

The moving interface uses

#math.equation(block: true, numbering: none, $ Phi^D_(partial R,upright("mov")) (t) = Phi^D_(upright("cross")) (t) - Phi^D_(upright("sweep")) (t) + Phi^D_(upright("shedding")) (t). $)

Here cross is current crossing the interface, sweep is current displaced by the moving boundary, and shedding is excess crossing or re-routing through the interface.
The output record carries interface current, interface pressure, SADAR attention vector, and sheddic path.


== Plasma shell dynamics <manual:boundary-current:plasma>

Declare

#math.equation(block: true, numbering: none, $ bold(upright(a))_(upright("plasma")) tack.r (F_(upright("plasma")) ,R_(upright("core")) , partial R_(upright("magnetic")) , omega_(upright("plasma")) ), wide B_(upright("plasma")) = ( partial F_(upright("plasma")) , omega_(upright("plasma")) ). $)

The plasma case uses the same scoped-flux calculation as the fluid interface, with the declared boundary now a shell boundary. The calculation changes by boundary declaration, not by introducing a new current object.


== Shell electromagnetic comparison <manual:boundary-current:shell-em>

The shell electromagnetic record is a downstream comparison record. It computes A$Omega$ quantities first:

#math.equation(block: true, numbering: none, $ J^D_(partial R) ( omega ;B), wide P^D_F (B), wide bold(upright(A))_F (B), wide X_(upright("shedding")) (B). $)

Only after these A$Omega$ quantities are declared may a measured-sector comparison be attached.


== Phase-fluid SADAR rebalancing <manual:boundary-current:phase-fluid>

Phase-fluid motion is the realized later response of the declared interface
field to its committed SADAR attention input:

#math.equation(block: true, numbering: none, $ op("motion")_(F,k + 1) (B) = (S^W_(F,k) ,S^W_(F,k + 1) ). $)

The local sequence is

#math.equation(block: true, numbering: none, $ "phase bias" arrow.r.long bold(upright(A))_F (B) arrow.r.long "SADAR balance" arrow.r.long "shedding / reclosure". $)

Push and pull are signed phase-biased components of the same vector.

In #raw("manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv") (vector #raw("RC-032")), the reference engine instantiates both boundary laws on explicit $Q_4$ vertex sets: shifting $R(1) = brace.l 0000, 0001, 0010, 0011 brace.r$ to $R(2) = brace.l 0001, 0010, 0011, 0100 brace.r$ realizes $Phi^D_(upright("mov")) = 8 - 3 + 2 = 7$, and a $4$-cut #raw("1:2:6") Dimonhexon walk above a chiral wire segment across cuts $52..55$ yields outward wire/electron fluxes $( + 4, - 4)$, $(0, 0)$ (decoupled cut-$53$ control), $( + 4, - 4)$, and $( + 5, - 5)$, with exact Stokes cancellation $0$ on the enclosing union boundary and cumulative realized response $+ 13$.


== Audit <manual:boundary-current:falsification>

The boundary-current application record carries the declared scope, antisymmetry $phi.alt_(j i) (B) = - phi.alt_(i j) (B)$, the signed window current as the sum of slice fluxes, and the moving-boundary cross, sweep, and shedding terms.

#math.equation(block: true, numbering: none, $ J^D_(partial R) ( omega ;B) eq.not sum_(t in omega) Phi^D_(partial R) (t;B bar.v_t ) $)

marks a window-current audit residual on the declared scope.


#aod-provenance[#mainequation("main:eq:b-scoped-flux")\; #mainequation("main:eq:rcd-coupling")\; #mainequation("main:eq:window-clipped-rho")\; #mainequation("main:eq:sadar-attention-vector")\; #mainequation("main:eq:moving-boundary").]



#aod-paragraph[Trace and response typing.]
The pressure-resolved flux in these applications is $phi.alt^(upright("AOD")) = p^D A$.
Normalized AFC memory/kernel flux remains separately typed. Pressure, signed
phase bias, directional RCD and current are distinct committed coordinates.
Their response changes state at the next transition; the attention vector
alone does not constitute motion. Opposite oriented values can cancel while
both bound histories remain retained.



== Five-boundary moving-boundary Stokes and wire-electron SADAR ledger <manual:wire:dec-moving-boundary>

#aod-paragraph[Setup and engine verification (#raw("RC-032")).]
Declare the five-boundary Stokes and scoped encounter chain

#math.equation(block: true, numbering: none, $ B_(upright("wire")) arrow.r B_e arrow.r B_(upright("int")) arrow.r B_(R_1 union R_2) arrow.r B_(upright("ext")). $)

Vector #raw("RC-032") (#raw("scoped_wire_and_moving_boundary"))—archived in #raw("manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv") and verified by #raw("python3 -B -m manual.engine --sector boundary_sadar") and #raw("aod-core --verify-vectors --check-zero-float")—executes both the moving-boundary balance $Phi^D_(upright("mov")) = Phi^D_(upright("cross")) - Phi^D_(upright("sweep")) + Phi^D_(upright("shedding")) = 8 - 3 + 2 = 7$ ($eq.not 8$) and the four-cut ($52 dots.h 55$) $1":"2":"6$ electron-above-wire encounter: at coupled cuts $52, 54, 55$ the opposing interface fluxes $( + 4, - 4)$, $( + 4, - 4)$, and $( + 5, - 5)$ cancel identically on $partial (R_(upright("wire")) union R_e ) = 0$ while driving the realized electron current trajectory $4 arrow.r 4 arrow.r 8 arrow.r 13$ (remaining unchanged across uncoupled cut $53$). External physical wire, fluid, or plasma apparatus remains quarantined at $B_(upright("ext"))$ until an explicit acquisition and uncertainty adapter is declared.


#figure(
  kind: image, [
#include "../../lib/figures/manual/wire_moving_boundary_feynman.typ"
  ],
  caption: [Moving-boundary Stokes decomposition ($Phi^D_(upright("mov")) = 8 - 3 + 2 = 7$) and four-cut $1":"2":"6$ electron-above-wire SADAR walk (#raw("RC-032"), #raw("scoped_wire_and_moving_boundary_walk.csv")).],
) <fig:manual-wire-moving-boundary-feynman>


#figure(
  kind: table, [
#aod-csv-table(
  "/manual/data/boundary_sadar/scoped_wire_and_moving_boundary_walk.csv",
  columns: (25fr, 6fr, 6fr, 9fr, 15fr, 20fr, 19fr),
  align: (left, right, right, right, right, right, right),
  size: 8.0pt,
  inset: (x: 3.0pt, y: 3.2pt),
  headers: (
    [Record], [Cut], [$bar.v omega bar.v$], [Coupled], [Wire / cross], [Electron / sweep+shed], [Union / current],
  ),
  cells: (
    (kind: "raw-wrap", col: "record_kind"),
    "cut",
    "window",
    "coupled",
    (
      kind: "when",
      col: "record_kind",
      eq: "moving_boundary_R1_to_R2",
      then: (kind: "signed", col: "Phi_cross"),
      otherwise: (kind: "signed", col: "wire_outward"),
    ),
    (
      kind: "when",
      col: "record_kind",
      eq: "moving_boundary_R1_to_R2",
      then: (kind: "sweep-shed", sweep: "Phi_sweep", shed: "Phi_shedding"),
      otherwise: (kind: "signed", col: "electron_outward"),
    ),
    (
      kind: "when",
      col: "record_kind",
      eq: "moving_boundary_R1_to_R2",
      then: (kind: "math-eq", lhs: [$Phi^D_(upright("mov")) =$], col: "Phi_moving"),
      otherwise: (kind: "union-cur", union: "union_boundary", lhs: [$J_e =$], cur: "later_electron_current"),
    ),
  ),
)
  ],
  caption: [Engine-bound moving-boundary Stokes decomposition and four-cut wire-electron SADAR D.E.C. ledger (#raw("RC-032"), live from #raw("scoped_wire_and_moving_boundary_walk.csv")).],
) <tab:manual-wire-moving-boundary-dec>

