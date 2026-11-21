// Native Typst Main publication driver (mirrors main.tex).
#import "preamble.typ": *
#show: aod-main-doc

#include "sections/00_title.typ"
#include "sections/01_abstract.typ"
#outline(title: "Contents", depth: 3, indent: 1.5em)
#pagebreak()
#include "sections/03_afc_basis.typ"
#include "sections/04_cut_running_fractal_tesseract.typ"
#include "sections/05_curl_closure_duon_current.typ"
#include "sections/06_wave_state_relational_time.typ"
#include "sections/06_field.typ"
#include "sections/08_awareness_learning_mindfulness.typ"
#include "sections/07_cell_measures_mappings.typ"

#aod-start-appendix()
#set heading(numbering: aod-appendix-numbering)
#include "appendices/A_fractal_address_bip_biz.typ"
#include "appendices/B_curling_curls.typ"
#include "appendices/C_stochastic_crowning.typ"
#include "appendices/D_cycle_shedding_demonstration.typ"
#include "appendices/E_glossary.typ"
#include "appendices/F_wave.typ"
#include "appendices/G_symbolic_cancellation_check.typ"
#include "appendices/H_combinatorics_rd_tests.typ"
#include "appendices/I_path_complexity_prototype_quarantine.typ"
#include "appendices/J_ao_field_fractal_properties.typ"

#aod-render-bibliography(title: "References")
