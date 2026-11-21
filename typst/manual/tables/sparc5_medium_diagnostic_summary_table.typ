// Native Typst port of manual/data/lensing/sparc5_medium_diagnostic_summary_table.tex (verbatim scientific content).
#import "../preamble.typ": *

#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (10.00fr, 5.00fr, 5.00fr, 6.00fr, 6.00fr, 10.00fr, 9.00fr, 18.00fr, 15.00fr),
    align: (left, left, left, left, left, left, left, left, left),
    table.header(
      toprule,
      [Galaxy], [Bins], [Gates], [Events], [Caustic], [Median $bar.v Delta A_(gamma) bar.v$], [Max $bar.v Delta A_(gamma) bar.v$], [Dominant class], [Status],
      midrule,
    ),
    [NGC2403], [73], [32], [44], [12], [1.1667], [1.9], [exoshedding deflection], [lens-medium],
    [NGC3198], [43], [32], [44], [12], [1.2721], [2.0], [exoshedding deflection], [lens-medium],
    [NGC6503], [31], [32], [44], [12], [1.3801], [2.4706], [exoshedding deflection], [lens-medium],
    [NGC2841], [50], [32], [41], [9], [1.2416], [1.7647], [exoshedding deflection], [lens-medium],
    [DDO154], [12], [32], [46], [14], [1.2941], [2.625], [exoshedding deflection], [lens-medium],
    bottomrule,
  )
},
  caption: [SPARC5 lens-medium summary.],
) <tab:manual-lensing-sparc5-summary>
