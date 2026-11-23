// Audited S1b native Typst vector figure: higgs-mass-comparison (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv)
// Historical raster retained byte-for-byte: manual/figures/higgs/higgs_mass_comparison.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.0
#let fig-height-cm = 7.6

#let rows = csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv", row-type: dictionary)
#let xs = range(rows.len()).map(i => float(i))
#let ys = rows.map(r => float(r.mass_GeV))
#let yerrs = rows.map(r => float(r.sigma_GeV))
#let pred = float(rows.at(0).prediction_GeV)
#let pred-str = rows.at(0).prediction_GeV

#let short-label(name) = {
  if name == "ATLAS_CMS_Run1_combined" { [ATLAS+CMS \ Run 1] }
  else if name == "CMS_H_to_4l_Run2_on_shell" { [CMS \ $H -> 4 ell$] }
  else if name == "ATLAS_Run1_Run2_combined" { [ATLAS \ Run 1+2] }
  else if name == "ATLAS_H_to_gammagamma" { [ATLAS \ $H -> gamma gamma$] }
  else { [#name] }
}
#let xticks = range(rows.len()).map(i => (float(i), short-label(rows.at(i).target_name)))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-xy-plot(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.75, right: 0.45, top: 0.78, bottom: 1.38),
    title: [Tritrioseptyro external-map Higgs mass comparison],
    title-size: 10.2pt,
    ylabel: [mass (GeV)],
    ylabel-dx: 1.30,
    xlim: (-0.28, 3.28),
    ylim: (124.825, 125.39),
    xticks: xticks,
    yticks: ((124.9, [124.9]), (125.0, [125.0]), (125.1, [125.1]), (125.2, [125.2]), (125.3, [125.3])),
    x-tick-angle: -20deg,
    x-tick-size: 7.4pt,
    y-tick-size: 7.6pt,
    x-tick-dy: 0.56,
    grid-y: true,
    layers: (
      (type: "hline", y: pred, stroke: (paint: rgb("#C46326"), thickness: 1.4pt, dash: "dashed")),
      (type: "errorbar", xs: xs, ys: ys, yerrs: yerrs, color: rgb("#2D5678"), lw: 1.2pt, cap-cm: 0.14, marker-r: 2.6),
    ),
    legend: (
      pos: "bottom-right",
      col-w: 4.55,
      size: 7.3pt,
      items: (
        (kind: "line", color: rgb("#C46326"), dash: "dashed", label: [frozen external map: #pred-str GeV]),
        (kind: "errorbar", color: rgb("#2D5678"), label: [LHC target $plus.minus sigma$]),
      ),
    ),
  )
]
