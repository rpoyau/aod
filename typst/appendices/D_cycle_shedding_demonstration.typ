// Native Typst port of appendices/D_cycle_shedding_demonstration.tex (verbatim scientific content).
#import "../preamble.typ": *

= Cycle-shedding burden and reclosure model <app:cycle-shedding-demonstration>



== Scope <app:cycle-shedding-demo-scope>

This declared A$Omega$D model relates lead–lag span, temporal SADAR
burden, sheddic excess, outward remainder and local reclosure on one retained
field. The coefficients are model parameters.


== Setup <app:cycle-shedding-demo-setup>

For native index $t$, let $L_t$ be the lead component, $G_t$ the lag component, $S_t$ the disturbance span, $P_t$ the burden, $C_t$ local closure compatibility, $X_t$ sheddic excess, $O_t$ outward remainder, and $R_t$ local reclosure.


== Burden and reclosure recurrence <app:cycle-shedding-demo-statements>


#math.equation(block: true, numbering: none, $ S_t = bar.v L_t - G_t bar.v , wide tilde(P)_t = eta_(upright("ret")) P_(t - 1) + gamma_(upright("span")) S_t , $)


#math.equation(block: true, numbering: none, $ X_t = max (0,tilde(P)_t - C_t ), wide P_t = tilde(P)_t - X_t , $)


#math.equation(block: true, numbering: none, $ O_t = (1 - lambda_(upright("reclose")) )X_t , wide R_t = lambda_(upright("reclose")) X_t . $)

Here $O_t$ is the non-reclosed outward remainder; route placement may later split it into exoshedding, redirected support routing, and open loss.


== Falsification <app:cycle-shedding-demo-falsification>

A proposed burden/reclosure sequence that violates any stated recurrence
for the declared parameters is not a solution of this model.


#aod-provenance[#secref("subsec:temporal-sadar-burden"),
#secref("subsec:shedding"),
#secref("subsec:sheddic-path").]
