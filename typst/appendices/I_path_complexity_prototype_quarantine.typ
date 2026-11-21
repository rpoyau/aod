// Native Typst port of appendices/I_path_complexity_prototype_quarantine.tex (verbatim scientific content).
#import "../preamble.typ": *

= Path Complexity and 4-Step Closure <app:path-complexity-quarantine>



== Scope <app:proto:scope>

This declared model specifies integer path complexity and a four-step load
convention on finite path histories.


== Four-step closure load <app:proto:statements>

Write an outer index as

#math.equation(block: true, numbering: none, $ L = 4 c_L + r_L , wide r_L in brace.l 0,1,2,3 brace.r . $)

For a path history $h$, the 4-step closure load is

#math.equation(block: true, numbering: none, $ Lambda_4 (h;B) = c_h (B). $)

For a field family,

$ Lambda_4 (F;B) = sum_(h in cal(H)_F (B)) C_(3,h) c_h (B). $ <app:proto:eq:four-step-load>



== Path-growth reference <app:proto:path-growth>

The raw ternary assignment space is

#math.equation(block: true, numbering: none, $ 3^n . $)

The AFC path-growth bound is recorded as

#math.equation(block: true, numbering: none, $ O(n log n). $)

The four-step decomposition is a declared load convention, not a restriction on all closure lengths. The AFC path-growth statement concerns its declared compressed information bound, not the raw number of ternary words. These statements concern finite path histories and the declared compressed information bound.


== Falsification <app:proto:falsification>

A declared 4-step closure reduction is contradicted on a scope when its $L = 4 c_L + r_L$ decomposition is not integer-valued, its history weights are undeclared, or its compressed value is not traceable to $Lambda_4 (F;B)$.


#aod-provenance[#appref("app:combinatorics-rd-tests"), #eqnref("eq:path-history-pressure"), #eqnref("eq:path-history-compression").]


#aod-literature-note[AFC scale-invariant branching and compressed path-information
bound: Poyau #aod-cite("afc", supplement: [§3.1; Choice 6; Consequence 3]), source revision
#link("https://github.com/rpoyau/afc/commit/5a25e8bd5bbc3f20ec4413a6b63abc420b7a54cb")[#raw("5a25e8bd5bbc")].]
