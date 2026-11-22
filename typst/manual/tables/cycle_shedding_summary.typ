// Native Typst port of cycle_shedding_summary.tex (verbatim scientific content).
#import "../preamble.typ": *

#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto),
    align: (left, right),
    toprule,
    [Ticks], [90],
    [Maximum lead-lag span], [0.298],
    [Maximum temporal SADAR burden], [0.570],
    [Maximum sheddic excess], [0.061],
    [Total exoshedding], [0.238],
    [Total local reclosure], [0.146],
    [Sheddic path trigger ticks], [0],
    [First reclosure tick], [none],
    bottomrule,
  )
}
