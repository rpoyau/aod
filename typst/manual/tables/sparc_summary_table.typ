// Native Typst port of manual/data/derived/sparc_summary_table.tex (verbatim scientific content).
#import "../preamble.typ": *

#figure(
  kind: table, [
#{
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto),
    align: (left, center, center, right, right, right, right, right),
    table.header(
      toprule,
      [$G$], [Class], [$sigma$ policy], [$N$], [$chi^2_U$], [$M A E_U$], [$M S E_U$], [$M A P E_U$ [%]],
      midrule,
    ),
    [DDO154], [G0], [obs-only], [12], [10893.83], [697.2], [602049.7], [41.42],
    [NGC2403], [G0], [obs-only], [73], [22038.64], [2486.2], [7212253.2], [23.31],
    [NGC2841], [G0], [obs-only], [50], [3235.74], [23910.7], [674670051.2], [26.47],
    [NGC3198], [G0], [obs-only], [43], [6352.96], [5478.2], [62935093.1], [37.51],
    [NGC6503], [G0], [obs-only], [31], [718.93], [1697.4], [3689898.7], [13.50],
    bottomrule,
  )
}
  ],
  caption: [SPARC five-galaxy scored records. Data-support class is G0 for this radial shell projection lane; the uncertainty policy is observation-only in this release.],
) <tab:manual-sparc-five-galaxy-scores>
