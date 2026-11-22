// Native Typst port of appendices/C_stochastic_crowning.tex (verbatim scientific content).
#import "../preamble.typ": *

= Stochastic crowning <app:stochastic-crowning>



== Scope <app:stoch-scope>

A$Omega$D stochastic accounting is count-normalized boundary accounting over a declared field, boundary, window, and fractal address.



== Setup <app:stoch-setup>

Declare a finite history family on the field and window:

#math.equation(block: true, numbering: none, $ cal(H)_(cal(F)) ( omega ). $)

Each history has the form

#math.equation(block: true, numbering: none, $ h = (h_(upright("past")) ,h_(upright("present")) ,h_(upright("future")) ). $)



== Crowning and retained-history counts <app:stoch-statements>



=== History family <app:stoch-history-family>

The family $cal(H)_(cal(F)) ( omega )$ is the declared finite support for stochastic crowning on the window.


=== Crowning <app:stoch-crowning>

The crowning map selects the present:

#math.equation(block: true, numbering: none, $ op("Crown")(h) = h_(upright("present")) . $)



=== Alpha advantage <app:stoch-alpha-advantage>

At one declared observation restriction, partition histories into mutually
exclusive statuses: crowned-alpha and not yet returned, completed Omega
return, or unresolved. A history is counted in exactly one current status;
its earlier alpha event remains in provenance but is not counted again as a
second current history. With this partition, define

#math.equation(block: true, numbering: none, $ N_(alpha) = "#" brace.l h: h" has current alpha status" brace.r , $)


#math.equation(block: true, numbering: none, $ N_(Omega) = "#" brace.l h: h" has completed-return status" brace.r , $)


#math.equation(block: true, numbering: none, $ N_0 = "#" brace.l h: h" remains unresolved" brace.r . $)

The total count is

#math.equation(block: true, numbering: none, $ N_(upright("tot")) = N_(alpha) + N_(Omega) + N_0 , wide N_(upright("tot")) > 0. $)

The alpha advantage is

$ Delta_(alpha) ( omega ) = frac(N_(alpha) - N_(Omega), N_(upright("tot"))). $ <app:stochastic:eq:alpha-advantage>



=== Retained-history family <app:stoch-retained-history-family>

For channel $e$, the retained-window indicator is

#math.equation(block: true, numbering: none, $ bold(1)_(upright("ret")) (e, omega ) = cases(1\, & upright("TTL")_e ( omega ) gt.eq bar.v omega bar.v_e\,, 0\, & upright("TTL")_e ( omega ) < bar.v omega bar.v_e .) $)

The history retention indicator is

#math.equation(block: true, numbering: none, $ bold(1)_(upright("ret")) (h, omega ) = 1 $)

when every retained channel required by $h$ satisfies the declared TTL policy on $omega$. The same mutually exclusive status partition is used after filtering. The retained-history family is

#math.equation(block: true, numbering: none, $ cal(H)_(cal(F))^(upright("ret")) ( omega ) = brace.l h in cal(H)_(cal(F)) ( omega ): bold(1)_(upright("ret")) (h, omega ) = 1 brace.r . $)

Define

#math.equation(block: true, numbering: none, $ N_(alpha)^(upright("ret")) = "#" brace.l h in cal(H)_(cal(F))^(upright("ret")) ( omega ): h" has current alpha status" brace.r , $)


#math.equation(block: true, numbering: none, $ N_(Omega)^(upright("ret")) = "#" brace.l h in cal(H)_(cal(F))^(upright("ret")) ( omega ): h" has completed-return status" brace.r , $)


#math.equation(block: true, numbering: none, $ N_(upright("tot"))^(upright("ret")) = bar.v cal(H)_(cal(F))^(upright("ret")) ( omega ) bar.v . $)

The retained alpha advantage is defined when $N_(upright("tot"))^(upright("ret")) > 0$:

$ Delta_(alpha)^(upright("ret")) ( omega ) = frac(N_(alpha)^(upright("ret")) - N_(Omega)^(upright("ret")), N_(upright("tot"))^(upright("ret"))). $ <app:stochastic:eq:ret-alpha-advantage>



== Derivation <app:stoch-derivation>

For each history, let $P_W (h)$ be the restriction of
#eqref("eq:temporal-sadar-burden") to its temporal cycle group.
The notation $bb(E)_(cal(H))$ denotes finite arithmetic average over the declared history family $cal(H)_(cal(F)) ( omega )$:

#math.equation(block: true, numbering: none, $ bb(E)_(cal(H)) [P_W ] = frac(1, N_(upright("tot"))) sum_(h in cal(H)_(cal(F)) ( omega )) P_W (h). $)



== Falsification <app:stoch-falsification>

If a declared history family has $N_(upright("tot")) = 0$, the alpha-advantage expression is undefined on that scope. If TTL filtering changes the retained support, retained counts must be recomputed before using $Delta_(alpha)^(upright("ret"))$.


#aod-provenance[#secref("subsec:crown"),
#eqnref("app:stochastic:eq:alpha-advantage"),
#eqnref("app:stochastic:eq:ret-alpha-advantage"),
#secref("subsec:support-enclosure-retention-condition").]



#aod-remark[The probability terms are normalized counts on the declared history family.]



#aod-literature-note[Finite Markov kernels: Norris #aod-cite("norrisMarkov"), Levin–Peres–Wilmer #aod-cite("levinPeresWilmer").]
