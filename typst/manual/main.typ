// Native Typst Manual publication driver (mirrors manual/main.tex).
#import "preamble.typ": *
#show: aod-manual-doc

#page(numbering: none)[
  #v(1fr)
  #align(center)[
    #text(size: 17pt)[Alpha$arrow.l.r$Omega Dynamics (A$Omega$D)]
    #v(0.35em)
    #text(size: 14pt)[The Hidden Temporal Dynamics of Stokes]
    #v(0.45em)
    #text(size: 12pt, style: "italic")[The Art Of The Leprechaun: Fractal Calculus – #SADARop]
    #v(0.65em)
    #text(size: 12pt)[43 $""^(circle.tiny)upright("c")$]
    #v(0.35em)
    #text(size: 14pt)[Manual]
    #v(0.45em)
    #text(size: 12pt)[#AODDocumentAuthor]
    #v(0.25em)
    #text(size: 10pt)[#AODDocumentDate]
    #v(0.55em)
    #math.equation(block: true, numbering: none, $ A scripts(arrow.l.r)_mu Omega med arrow.l.r.long med Omega scripts(arrow.l.r)_mu A $)
    #v(1.35em)
    #text(size: 10pt, style: "italic")[Epitaph]
    #v(0.2em)
    #math.equation(block: true, numbering: none, $ cal(N) equiv infinity wide cal(N) arrow.r cal(N) arrow.r cal(N) equiv cal(N) $)
    #text(size: 10pt, style: "italic")[Comprehension, cooperation, and presence are not prerequisites of AFC.]
    #v(0.2em)
    #text(size: 10pt, style: "italic")[Nuff said.]
  ]
  #v(2fr)
]
#counter(page).update(1)

#outline(title: "Contents", depth: 3, indent: 1.5em)

#include "sections/00_scope.typ"
#include "sections/00_native_closure_wave_temporal_fixtures.typ"
#include "sections/00_awareness_fixtures.typ"
#include "sections/00_dec_ledger.typ"
#include "sections/01_cell_measures.typ"
#include "sections/02_mapping_error.typ"
#include "sections/03_temporal_observation.typ"
#include "sections/03_short_window_rcd_shedding_fixtures.typ"
#include "sections/01_rest_energy_prediction.typ"
#include "sections/02_hydrogen_facing_shell_tests.typ"
#include "sections/04_boundary_current_applications.typ"
#include "sections/05_solar_system_field_tests.typ"
#include "sections/06_field_dynamics_applications.typ"
#include "sections/07_galactic_lensing_plan.typ"
#include "sections/09_prediction_test_fixture_registry.typ"

#aod-start-appendix()
#set heading(numbering: aod-appendix-numbering)
#include "appendices/A_simulation_fixtures_and_tau_prediction_context.typ"
#include "appendices/B_quarantined_external_comparison.typ"
#include "appendices/C_3d_coordinate_phase_cycle_delta3_fixture.typ"

#aod-render-bibliography(title: "References")
