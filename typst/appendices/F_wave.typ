// Native Typst port of appendices/F_wave.tex (verbatim scientific content).
#import "../preamble.typ": *

= Wave presentation and audit <app:wave>



== Scope <app:wave:scope>

This appendix audits downstream presentations of an already admitted recurrent
wave. Recurrence and semantic admission precede every value transform.


== Cycle and wave identity <app:wave:cycle-wave-identity>

Admission and cycle/reclosure counts are #eqref("eq:wave-identity") and
#eqref("eq:cumulative-closure-counts"). The presentation below consumes those
witnesses.

For an already admitted wave $W_(B,i)$, $C_k$ is its bound retained cycle
from #eqref("eq:wave-sadar-presentation"), with the native index $k$.
Its SADAR-valued presentation may be written

$ op("Present")_B (W_(B,i) ) = brace.l (k, SADARop_(B bar.v k) (C_k )):k in omega brace.r . $ <app:wave:eq:wave-sadar-presentation>



== Continuation and direction <app:wave:fractal-growth-temporal-direction>

Use the advance #eqref("eq:crown-advance") and the native running and standing
classifications in #secref("eq:native-running-standing"), retaining each contributing identity and orientation.


== Flux and window current <app:wave:flux-current>

The slice flux #eqref("eq:slice-flux") and retained window current
#eqref("eq:window-current") are downstream value coordinates of the admitted
wave. Aggregate cancellation preserves both oriented channel histories.


== Falsification <app:wave:falsification>

The audit fails if a presentation is used without an admitted recurring wave,
declared boundary/window, committed values, lineage provenance, or the required
closure and reclosure witnesses. Exact Fourier inversion of an unbound word
does not repair any missing witness.


#aod-provenance[#eqnref("eq:closure-phase"),
#eqnref("eq:beat-reclosure"),
#eqnref("eq:wave-identity"),
#eqnref("eq:wave-sadar-presentation"),
#eqnref("eq:slice-flux"),
#eqnref("eq:window-current"),
#eqnref("eq:fourier-transform").]
