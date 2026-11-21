// Native Typst port of appendices/G_symbolic_cancellation_check.tex (verbatim scientific content).
#import "../preamble.typ": *

= Scoped flux cancellation <app:scoped-flux-cancellation>



== Scope <app:scoped-flux:scope>

This appendix records symbolic support for finite Stokes with separately typed A$Omega$D pressure-resolved flux values. The scope is a finite declared region $R$ and boundary/window $B = ( partial F, omega )$.


== Scoped pairing and Stokes residual <app:scoped-flux:statements>



#aod-paragraph[Setup.]

#math.equation(block: true, numbering: none, $ phi.alt_(i j) arrow.r.bar phi.alt_(i j) (B), wide phi.alt_(i j, AO) (B) = p^D_(i j, AO) (B)A_(i j, AO) (B). $)


#aod-paragraph[Derivation.]
The scoped boundary pairing is retained through the AFC Stokes identity:

$ sum_(i in R) op("div")(i;B) = sum_(i in R \ j in.not R) phi.alt_(i j) (B). $ <app:scoped-flux:eq:afc-pairing>

The Stokes residual is

$ cal(E)(R,B) = sum_(i in R) op("div")(i;B) - sum_(i in R \ j in.not R) phi.alt_(i j) (B). $ <app:scoped-flux:eq:residual>

A valid declared scope has $cal(E)(R,B) = 0$.


== Falsification <app:scoped-flux:falsification>

If the symbolic residual is nonzero, the declared scope has a missing channel, sign error, incomplete boundary, or undeclared sheddic path.


#aod-provenance[#eqnref("eq:b-scoped-flux"),
#eqnref("eq:b-scoped-flux-antisymmetry"),
#eqnref("eq:b-scoped-divergence"),
#eqnref("eq:b-scoped-stokes"),
#eqnref("eq:stokes-audit-residual").]
