// Native Typst port of manual/data/lensing/swells_k1_k2_k3_comparison_table.tex (verbatim scientific content).
#import "../preamble.typ": *

#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (auto, 28.0%, auto, auto, auto, auto),
    align: (left, left, center, center, center, left),
    table.header(
      toprule,
      [Run], [Input basis], [$theta_E$ $delta_3$ $m_(upright("tot"))$], [$theta_E$ match [%]], [$sigma$ $delta_3$ $m_(upright("tot"))$], [Decision],
      midrule,
    ),
    [K1], [$sigma_(upright("SDSS"))$ + H$alpha$ + axis ratio], [8], [40.0], [4], [retained baseline],
    [K2], [K1 + redshift geometry context], [18], [40.0], [4], [audit diagnostic],
    [K3], [Paper I Table 2 bulge/disk medium fields], [10], [33.3333], [12], [audit diagnostic],
    bottomrule,
  )
},
  caption: [SWELLS K1/K2/K3 diagnostic comparison.],
) <tab:manual-lensing-swells-k123>



#v(0.4em)

#emph[K1 reason.] Lowest retained $delta_3$ residual. \

#emph[K2 reason.] Over-amplified high-$theta_E$ class. \

#emph[K3 reason.] Under-resolved observable map with current medium data.
