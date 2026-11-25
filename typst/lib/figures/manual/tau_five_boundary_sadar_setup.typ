// Authored native Typst vector figure: tau-five-boundary-sadar-setup (Manual)
// Provenance: DATA_BACKED_VERIFIED (manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.2

#let trace = csv("/manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv", row-type: dictionary)
#let sterile = trace.at(0)
#let c126 = trace.at(2)
#let c127 = trace.at(3)
#let c128 = trace.at(4)
#let c129 = trace.at(5)
#let c1210 = trace.at(6)

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-box-tl(0.15, 0.15, 14.70, 8.90, [], stroke: 0.85pt + aod-pal.axis, fill: white, radius: 2pt)
  #aod-text(7.50, 0.54, [*Five-boundary $A Omega D$ SADAR collision-shedding stack for Tau ($1":"2":"9_(upright("yro"))$ Dimonnanyro)*], size: 10.1pt, box-w: 14.4, box-h: 0.48)
  #aod-text(7.50, 0.94, [$B_(upright("hard")) -> B_tau -> B_(upright("shed")) -> B_(upright("sensor")) -> B_(upright("ext"))$: outcome derived from boundary competition, never hardcoded.], size: 7.5pt, box-w: 14.4, box-h: 0.40)

  // Stage 1: B_hard (x: 0.35..3.05)
  #aod-box-tl(0.35, 1.35, 2.68, 6.20, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 4pt)
  #aod-badge(0.68, 1.66, [1], r: 0.18)
  #aod-text(1.82, 1.66, [*$B_(upright("hard"))$ ($p p$)*], size: 8.0pt, box-w: 2.0, box-h: 0.38)
  #aod-box-tl(0.52, 2.08, 2.34, 1.35, [#text(size: 7.1pt)[Opposing streams \ $3":"3":"6 + 3":"3":"6$ \ $+ E_2$ BETWEEN \ duon chiral flips]], stroke: 0.8pt + aod-pal.blue, fill: white)
  #aod-wavy-arrow(1.69, 3.48, 1.69, 4.12, amp: 0.06, waves: 2.5, stroke: 0.95pt + aod-pal.orange)
  #aod-box-tl(0.52, 4.16, 2.34, 1.35, [#text(size: 7.0pt)[Live cavity: \ early coupling \ cut $1$, raw $26$, \ quotient $11$]], stroke: 0.8pt + aod-pal.gold, fill: aod-pal.tint-amber)
  #aod-box-tl(0.52, 5.75, 2.34, 1.56, [#text(size: 6.9pt)[*Sterile control:* \ duons $= 0$ \ cut $#sterile.window_L$, $X = #sterile.X_shedding$ \ (no shedding)]], stroke: 0.8pt + aod-pal.slate, fill: aod-pal.tint-gray)

  // Stage 2: B_tau pocket competition (x: 3.25..6.35)
  #aod-arrow(3.04, 3.20, 3.24, 3.20, stroke: 1.0pt + aod-pal.navy)
  #aod-box-tl(3.26, 1.35, 3.12, 6.20, [], stroke: 0.9pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 4pt)
  #aod-badge(3.58, 1.66, [2], r: 0.18, fill: white, stroke: 0.9pt + aod-pal.teal)
  #aod-text(4.96, 1.66, [*$B_tau$ ($1":"2":"L$)*], size: 8.0pt, box-w: 2.4, box-h: 0.38)
  #aod-text(4.82, 2.12, [$R D(1":"2) = 9$, $C_3 = 3$], size: 7.1pt, weight: "bold", box-w: 2.9, box-h: 0.34)

  #aod-box-tl(3.42, 2.38, 2.80, 0.80, [#text(size: 6.8pt)[$1":"2":"6$: $P^D=#c126.PD = sans("C")_6$ \ $Q^D=#c126.QD$, $X=#c126.X_shedding$ (closed)]], stroke: 0.7pt + aod-pal.slate, fill: white)
  #aod-box-tl(3.42, 3.28, 2.80, 0.80, [#text(size: 6.8pt)[$1":"2":"7$: $P^D=#c127.PD < sans("C")_8$ \ $Q^D=#c127.QD$, $X=#c127.X_shedding$ (deficit)]], stroke: 0.7pt + aod-pal.slate, fill: white)
  #aod-box-tl(3.42, 4.18, 2.80, 0.80, [#text(size: 6.8pt)[$1":"2":"8$: $P^D=#c128.PD = sans("C")_8$ \ $Q^D=#c128.QD$, $X=#c128.X_shedding$ (closed)]], stroke: 0.7pt + aod-pal.slate, fill: white)
  #aod-box-tl(3.42, 5.08, 2.80, 1.24, [#text(size: 6.9pt)[*$1":"2":"9_(upright("yro"))$: $P^D=#c129.PD > sans("C")_8$* \ *$Q^D=#c129.QD$, $X=#c129.X_shedding$ (UNIQUE)*]], stroke: 1.15pt + aod-pal.orange, fill: aod-pal.tint-amber)
  #aod-box-tl(3.42, 6.44, 2.80, 0.88, [#text(size: 6.8pt)[$1":"2":"10$: clips $rho_omega^D=#c1210.rhoD_omega$ \ $P^D=#c1210.PD = sans("C")_(10)$, $X=#c1210.X_shedding$]], stroke: 0.7pt + aod-pal.slate, fill: white)

  // Stage 3: B_shed 2500-denominator split (x: 6.60..9.25)
  #aod-wavy-arrow(6.24, 5.70, 6.60, 5.70, amp: 0.055, waves: 1.5, stroke: 1.05pt + aod-pal.orange)
  #aod-box-tl(6.62, 1.35, 2.62, 6.20, [], stroke: 0.9pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 4pt)
  #aod-badge(6.94, 1.66, [3], r: 0.18, fill: white, stroke: 0.9pt + aod-pal.gold)
  #aod-text(8.08, 1.66, [*$B_(upright("shed"))$ split*], size: 8.0pt, box-w: 2.1, box-h: 0.38)

  #aod-box-tl(6.78, 2.18, 2.30, 2.12, [#text(size: 7.1pt)[*Endoshedding* \ (inner retained) \ $#c129.endo_retained_frac = 13 slash 50$ \ stays inside cavity]], stroke: 0.85pt + aod-pal.slate, fill: white)
  #aod-box-tl(6.78, 4.62, 2.30, 2.58, [#text(size: 7.1pt)[*Exoshedding* \ (outward $upright("Exo")$) \ $#c129.exo_outward_frac = 37 slash 50$ \ crosses to \ sensor wall]], stroke: 1.0pt + aod-pal.orange, fill: white)

  // Stage 4: Passive ReadOnly 3:4:6 Sensor Wall B_sensor (x: 9.52..12.18)
  #aod-boundary-wall(9.44, 1.35, 9.44, 7.55, stroke: 1.35pt + aod-pal.crimson, hatch-side: 1, hatch-count: 11, double-line: true)
  #aod-arrow(9.09, 5.85, 9.64, 5.85, stroke: 1.1pt + aod-pal.orange)

  #aod-box-tl(9.66, 1.35, 2.52, 6.20, [], stroke: 0.9pt + aod-pal.crimson, fill: white, radius: 4pt)
  #aod-badge(9.98, 1.66, [4], r: 0.18, fill: aod-pal.tint-orange, stroke: 0.9pt + aod-pal.crimson)
  #aod-text(11.08, 1.66, [*$B_(upright("sensor"))$*], size: 8.0pt, box-w: 1.8, box-h: 0.38)
  #aod-text(10.92, 2.08, [ReadOnly $3":"4":"6$ wall], size: 6.9pt, weight: "bold", box-w: 2.3, box-h: 0.34)

  #aod-box-tl(9.82, 2.48, 2.20, 2.08, [#text(size: 7.0pt)[*Visible seated:* \ $703 slash 2500$ \ $= #c129.sensor_visible_cond_exo |_(upright("Exo"))$ \ ($0.38$ seated)]], stroke: 0.85pt + aod-pal.teal, fill: aod-pal.tint-green)
  #aod-box-tl(9.82, 4.84, 2.20, 2.36, [#text(size: 7.0pt)[*Unseated pass:* \ $1147 slash 2500$ \ *$op("miss")_tau = #c129.sensor_missing_cond_exo$* \ ($0.62$ on $upright("Exo")$)]], stroke: 1.05pt + aod-pal.crimson, fill: aod-pal.tint-orange)

  // Stage 5: Quarantined External Comparison B_ext (x: 12.42..14.65)
  #aod-arrow(12.19, 3.52, 12.40, 3.52, stroke: 1.0pt + aod-pal.purple)
  #aod-box-tl(12.42, 1.35, 2.23, 6.20, [], stroke: 0.9pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 4pt)
  #aod-badge(12.74, 1.66, [5], r: 0.18, fill: white, stroke: 0.9pt + aod-pal.purple)
  #aod-text(13.68, 1.66, [*$B_(upright("ext"))$ ($Q_(upright("ext"))$)*], size: 7.8pt, box-w: 1.7, box-h: 0.38)
  #aod-box-tl(
    12.56, 2.22, 1.95, 5.00,
    [#text(size: 6.9pt)[
      Quarantined \
      comparator: \ \
      $E_tau^(upright("tar")) =$ \
      $1776.86$ MeV \
      $plus.minus 0.12$ MeV \ \
      $nu_(tau, upright("tar")) =$ \
      $3.135255$ \
      $times 10^(21) thin upright("s")^(-1)$ \ \
      Zero sensor \
      back-reaction
    ]],
    stroke: 0.8pt + aod-pal.purple,
    fill: white,
  )

  // Bottom 2500-denominator conservation bar
  #aod-box-tl(
    0.35, 7.85, 14.30, 0.92,
    [#text(size: 7.3pt)[
      *Exact 2500-slot cavity conservation:* $quad 650 slash 2500_("endo") + 703 slash 2500_("vis") + 1147 slash 2500_("miss") = 1$. $quad$
      Conditioned on outward $upright("Exo")$ ($1850 slash 2500 = 37 slash 50$): $quad (703 slash 1850, med 1147 slash 1850) = (19 slash 50, med 31 slash 50)$. \
      Recipient lattice: emitted #sym.arrow.r delivered #sym.arrow.r accepted #sym.arrow.r seated #sym.arrow.r closed\_origin ($Delta op("bip") = 0$) #sym.arrow.r reclosed ($Delta op("bip") = +1$).
    ]],
    stroke: 0.85pt + aod-pal.navy,
    fill: aod-pal.tint-gray,
    radius: 3pt,
  )
]
