// Audited S1b native Typst vector figure: lensing-04-sparc5-class-tally-heatmap (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/lensing/sparc5_lensing_class_tallies.csv)
// Historical raster retained byte-for-byte: manual/figures/lensing/04_sparc5_class_tally_heatmap.png
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 14.4
#let fig-height-cm = 7.6

#let rows = csv("/manual/data/lensing/sparc5_lensing_class_tallies.csv", row-type: dictionary)
#let col-keys = ("caustic_pair", "exoshedding_deflection", "open_loss_scatter", "weak_refraction", "straight", "hinge_slide", "chiral_flip")
#let col-labels = ("caustic pair", "exoshedding deflection", "open-loss scatter", "weak refraction", "straight", "hinge slide", "chiral flip")
#let row-labels = rows.map(r => r.galaxy)
#let matrix = rows.map(r => col-keys.map(k => int(r.at(k))))

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-heatmap(
    x0: 0.0, y0: 0.0, w: fig-width-cm, h: fig-height-cm,
    pad: (left: 1.72, right: 1.75, top: 0.72, bottom: 1.92),
    title: [SPARC5 lens-medium class tallies],
    row-labels: row-labels,
    col-labels: col-labels,
    matrix: matrix,
    vmin: 0.0,
    vmax: 31.0,
    cbar-label: [tally],
    cbar-ticks: (0, 5, 10, 15, 20, 25, 30),
  )
]
