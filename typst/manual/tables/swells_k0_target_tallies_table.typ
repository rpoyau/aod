// Native Typst port of manual/data/lensing/swells_k0_target_tallies_table.tex (verbatim scientific content).
#import "../preamble.typ": *

#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (34.00fr, 34.00fr, 16.00fr),
    align: (left, left, left),
    table.header(
      toprule,
      [Target family], [Class $k$], [$O$ tally],
      midrule,
    ),
    [strong-lens presence], [modelled lens], [20],
    [grade], [A], [19],
    [grade], [B], [1],
    [Einstein radius bin], [$theta_E < 0.75$], [3],
    [Einstein radius bin], [$0.75 lt.eq theta_E < 1.00$], [9],
    [Einstein radius bin], [$theta_E gt.eq 1.00$], [8],
    [$sigma_(upright("SIE"))$ bin], [$sigma < 200$], [8],
    [$sigma_(upright("SIE"))$ bin], [$200 lt.eq sigma < 230$], [7],
    [$sigma_(upright("SIE"))$ bin], [$sigma gt.eq 230$], [5],
    bottomrule,
  )
},
  caption: [SWELLS K0 target-side acquisition fields.],
) <tab:manual-lensing-swells-k0>
