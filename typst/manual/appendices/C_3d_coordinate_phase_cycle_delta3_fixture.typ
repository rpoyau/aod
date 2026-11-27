// Native Typst port of manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex (verbatim scientific content).
#import "../preamble.typ": *

= 3D coordinate phase-cycle $delta_3$ fixture specification <manual:app:coordinate-phase-cycle-delta3>



#aod-paragraph[Calculation card.]
The supplied script generates a fixed integer fixture. Its grid, lag, phase
scale and comparator produce exact displacement and tally outputs; count
conservation and transported residuals are the falsifiers. A measured-track
ingest map and physical uncertainty are not yet instantiated. Its required
source roles follow #secref("manual:calculation-spine").


This appendix records the active integer 3D coordinate fixture used by time-ordered trajectory records. It gives the coordinate-level specification: integerized trajectory bins, squared displacement counts, phase-cycle counts, octant counts, integer ratios, and exact $delta_3$ residuals. Continuous-motion summaries are downstream presentation maps and do not enter the exact fixture.
The run-tumble tracer-current fixture in #secref("manual:run-tumble-tracer-current-fixture") is an application of this coordinate phase-cycle specification after its mode, accumulated trace, and projection declarations are fixed.


#figure(
  kind: image, [
#include "../../lib/figures/manual/coordinate_phase_delta3_wireframe.typ"
  ],
  caption: [3D coordinate phase-cycle $delta_3$ fixture. The coordinate fixture maps trajectory positions into $bb(Z)^3$, forms integer squared displacement $Q = a^2 + b^2 + c^2$, records phase residues $Q mod beta_a$, counts octants, and audits integer residuals by $delta_3$. Continuous summaries belong after the exact fixture as presentation or external maps.],
) <fig:manual-coordinate-phase-delta3>



== Active data form

Declare a grid

#math.equation(block: true, numbering: none, $ G = (h_x ,h_y ,h_z , Delta t). $)

A measured-track adapter must specify origin, positive grid spacings,
quantization and tie rule, timing alignment and the admissible input set or
justified joint law before mapping positions into integer lattice coordinates

#math.equation(block: true, numbering: none, $ z_i = (X_i ,Y_i ,Z_i ) in bb(Z)^3 . $)

For lag $n$, write

#math.equation(block: true, numbering: none, $ Delta z_i^(lr((n))) = z_(i + n) - z_i = (a_i^(lr((n))) ,b_i^(lr((n))) ,c_i^(lr((n))) ). $)

The active integer displacement is

#math.equation(block: true, numbering: none, $ Q_i^(lr((n))) = (a_i^(lr((n))) )^2 + (b_i^(lr((n))) )^2 + (c_i^(lr((n))) )^2 in bb(Z)_(gt.eq 0) . $)

This replaces radial-distance fitting in the fixture layer.
For example, a declared nearest-integer rule with ties upward maps
$49 slash 100$ and $51 slash 100$ to $0$ and $1$. An interval crossing that
boundary admits both states; it does not assign probabilities to them.
The acquisition owner must propagate the permitted states through the
actual tally and provide a mass/size-to-$beta_a$ map when used.



== Integer displacement counts

Declare integer bins

#math.equation(block: true, numbering: none, $ I_(ell) = [q_(ell) ,q_(ell + 1) ) inter bb(Z). $)

The observed displacement-bin count is

#math.equation(block: true, numbering: none, $ O_(ell)^(lr((n))) = "#" brace.l i:Q_i^(lr((n))) in I_(ell) brace.r . $)

The comparator count is an integer family

#math.equation(block: true, numbering: none, $ hat(O)_(ell)^(lr((n))) in bb(Z)_(gt.eq 0) , wide sum_(ell) hat(O)_(ell)^(lr((n))) = sum_(ell) O_(ell)^(lr((n))) . $)

Record exact residuals by

#math.equation(block: true, numbering: none, $ Delta_(ell)^(bb(Z),(n)) = hat(O)_(ell)^(lr((n))) - O_(ell)^(lr((n))) , wide delta_(3, ell)^(lr((n))) = ( s_(ell)^((3),(n)) ,m_(ell)^(lr((n))) ) , $)

where

#math.equation(block: true, numbering: none, $ s_(ell)^((3),(n)) = op("sgn")( Delta_(ell)^(bb(Z),(n)) ), wide m_(ell)^(lr((n))) = bar.v Delta_(ell)^(bb(Z),(n)) bar.v . $)

The conservation check and total exact mismatch are

#math.equation(block: true, numbering: none, $ sum_(ell) Delta_(ell)^(bb(Z),(n)) = 0, wide M_(delta_3)^(lr((n))) = sum_(ell) m_(ell)^(lr((n))) . $)



== Phase-cycle fixture

Let the candidate monon-beat scale from mass/size be

#math.equation(block: true, numbering: none, $ beta_a in bb(Z)_(> 0) . $)

Define the phase residue

#math.equation(block: true, numbering: none, $ theta_i^(lr((n))) = Q_i^(lr((n))) mod beta_a . $)

The phase-cycle count is

#math.equation(block: true, numbering: none, $ O_(theta)^(lr((n))) = "#" brace.l i: theta_i^(lr((n))) = theta brace.r , wide theta in brace.l 0,1, dots.h , beta_a - 1 brace.r . $)

Against an integer comparator $hat(O)_(theta)^(lr((n)))$, record

#math.equation(block: true, numbering: none, $ Delta_(theta)^(bb(Z),(n)) = hat(O)_(theta)^(lr((n))) - O_(theta)^(lr((n))) , wide delta_(3, theta)^(lr((n))) = ( op("sgn")( Delta_(theta)^(bb(Z),(n)) ), bar.v Delta_(theta)^(bb(Z),(n)) bar.v ) . $)

The phase-cycle fixture is read as: mass/size data may declare $beta_a$, and the trajectory tests the phase-cycle counts.


== Octant direction counts

Bind bit order and the treatment of zero coordinates with the track.
Brownian and run-tumble encodings may differ; any relabelling transports
both observed and comparator bins, including the integer-balancing remainder
assignment. Rebalancing the comparator in a new label order changes the
test. All eight sign patterns and a common permutation must preserve the
transported residuals before a shared adapter is accepted.

For each displacement vector, declare

#math.equation(block: true, numbering: none, $ q_i^(lr((n))) = op("octant")(a_i^(lr((n))) ,b_i^(lr((n))) ,c_i^(lr((n))) ) in brace.l 0, dots.h ,7 brace.r . $)

The octant count is

#math.equation(block: true, numbering: none, $ O_q^(lr((n))) = "#" brace.l i:q_i^(lr((n))) = q brace.r . $)

The octant-neutral comparator is an integer family

#math.equation(block: true, numbering: none, $ hat(O)_q^(lr((n))) = op("IntBalance")(N_n ,8), wide sum_q hat(O)_q^(lr((n))) = sum_q O_q^(lr((n))) . $)

Then

#math.equation(block: true, numbering: none, $ delta_(3,q)^(lr((n))) = ( op("sgn")(hat(O)_q^(lr((n))) - O_q^(lr((n))) ), bar.v hat(O)_q^(lr((n))) - O_q^(lr((n))) bar.v ) . $)



== Integer-ratio motion summaries

Use integer ratios:

#math.equation(block: true, numbering: none, $ R_Q^(lr((n))) = ( sum_i Q_i^(lr((n))) :N_n ) . $)

Axis ratios are

#math.equation(block: true, numbering: none, $ R_x^(lr((n))) = ( sum_i (a_i^(lr((n))) )^2 : sum_i Q_i^(lr((n))) ) , $)


#math.equation(block: true, numbering: none, $ R_y^(lr((n))) = ( sum_i (b_i^(lr((n))) )^2 : sum_i Q_i^(lr((n))) ) , $)


#math.equation(block: true, numbering: none, $ R_z^(lr((n))) = ( sum_i (c_i^(lr((n))) )^2 : sum_i Q_i^(lr((n))) ) . $)

A three-axis balanced motion fixture records $R_x^(lr((n))) :R_y^(lr((n))) :R_z^(lr((n)))$ against the declared integer target. Phase and octant ratios are

#math.equation(block: true, numbering: none, $ R_(theta)^(lr((n))) = (O_0^(lr((n))) :O_1^(lr((n))) : dots.c :O_(beta_a - 1)^(lr((n))) ), wide R_(upright("oct"))^(lr((n))) = (O_0^(lr((n))) :O_1^(lr((n))) : dots.c :O_7^(lr((n))) ). $)



== Comparator choices

Use integer comparators. The phase-neutral comparator is

#math.equation(block: true, numbering: none, $ hat(O)_(theta)^(lr((n))) = op("IntBalance")(N_n , beta_a ), $)

which distributes $N_n$ counts across $beta_a$ phase classes by a declared integer balancing rule. The octant-neutral comparator is $hat(O)_q^(lr((n))) = op("IntBalance")(N_n ,8)$. Shuffle controls may be declared by time-shuffled increments, sign-shuffled increments, axis-permuted increments, or phase-rotated increments. Each control produces its own $delta_3$ and $M_(delta_3)$.


== AFC/A$Omega$D mapping

The active coordinate-motion boundary is

#math.equation(block: true, numbering: none, $ B_(upright("mot")) = ( partial_T F_(upright("track")) , omega_(upright("track")) ). $)

The exact fixture path is

#math.equation(block: true, numbering: none, $ z_i in bb(Z)^3 arrow.r Delta z_i^(lr((n))) arrow.r Q_i^(lr((n))) arrow.r theta_i^(lr((n))) arrow.r O_(theta)^(lr((n))) arrow.r delta_3 . $)

The retained motion trace is

#math.equation(block: true, numbering: none, $ Delta z_i^(lr((n))) arrow.r H T(h_i ;B_(upright("mot")) ) arrow.r R D_(h_i) arrow.r R C D_(h_i) arrow.r rho^D_(omega ,h_i) arrow.r SADARop_B . $)

Moving-boundary current remains

#math.equation(block: true, numbering: none, $ Phi^D_(partial_T R,upright("mov")) (t) = Phi^D_(upright("cross")) (t) - Phi^D_(upright("sweep")) (t) + Phi^D_(upright("shedding")) (t). $)



== Script target and outputs

The generic coordinate script target is

#math.equation(block: true, numbering: none, $ mono("aod_3d_coordinate_phase_delta3.py"). $)

Inputs are

#math.equation(block: true, numbering: none, $ mono("track_id"), quad mono("t"), quad mono("x"), quad mono("y"), quad mono("z"). $)

Optional fields are

#math.equation(block: true, numbering: none, $ mono("ux"), quad mono("uy"), quad mono("uz"), quad mono("mass"), quad mono("size"), quad mono("beta"). $)

Output files are

#math.equation(block: true, numbering: none, $ mono("displacement_q_counts.csv"), \ mono("phase_cycle_delta3.csv"), \ mono("octant_delta3.csv"), \ mono("integer_motion_ratios.csv"). $)



== Final lock

The 3D coordinate phase-cycle fixture uses integer phase-cycle ratios. It uses $Q = a^2 + b^2 + c^2$, phase residues $Q mod beta_a$, octant counts for three-dimensional direction, and $delta_3$ on integer counts. External continuous-motion summaries live after the exact fixture.



== Five-boundary 3D lag-1 trajectory D.E.C. ledger <manual:app-c:dec-lag1-walk>

Declare the five-boundary three-dimensional trajectory diagnostic stack

#math.equation(block: true, numbering: none, $ B_(upright("lattice")) arrow.r B_(Delta x) arrow.r B_(Q mod 5) arrow.r B_(delta_3) arrow.r B_(upright("ext")). $)

Vector #raw("RC-044") (#raw("manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv"), verified in pure #raw("TritWord")/#raw("TritRatio") arithmetic by #raw("python3 -B -m manual.engine") #aod-nowrap[#raw("--sector")] #raw("boundary_sadar") and #raw("aod-core") #aod-nowrap[#raw("--verify-vectors")] #aod-nowrap[#raw("--check-zero-float")]) evaluates all eight lag-$1$ lattice steps from $(0, 0, 0)$ to $(6, 5, 5)$ at canonical phase modulus $beta_a = 5$ and default octant bit order #raw("msb_x"), matching Brownian canonical vector #raw("RC-012") (#raw("manual/data/brownian/octant_delta3.csv")) identically. The eight squared lag norms are $Q = (2, 2, 2, 3, 3, 3, 2, 3)$ with $sum Q = 20$, giving exact integer ratios $R_Q = 5 slash 2$, $R_x = 2 slash 5$, $R_y = 7 slash 20$, and $R_z = 1 slash 4$ ($R_x + R_y + R_z = 1$), alongside endpoint chord squared norm $6^2 + 5^2 + 5^2 = 86$. Phase residues $theta = Q mod 5$ realize four counts at $theta = 2$ and four at $theta = 3$, giving $O_theta = (0, 0, 4, 4, 0)$, integer-balanced comparator residuals $Delta_theta^(bb(Z)) = (2, 2, -2, -3, 1)$ (conserving $sum Delta_theta^(bb(Z)) = 0$), and $M_(delta_3 , theta) = 10$. Explicitly contrasting octant bit-order conventions: under canonical Brownian MSB-$x$ ordering $4(a < 0) + 2(b < 0) + (c < 0)$ (#raw("RC-012") and default #raw("RC-044")), step $4$ with $Delta z = (-1, 1, 1)$ maps to octant $4$, producing $O_(upright("oct")) = (6, 0, 1, 0, 1, 0, 0, 0)$, $Delta_(upright("oct"))^(bb(Z)) = (-5, 1, 0, 1, 0, 1, 1, 1)$, and $M_(delta_3 , upright("oct")) = 10$; under explicit run-tumble LSB-$x$ ordering $(a < 0) + 2(b < 0) + 4(c < 0)$ (#raw("RC-013") and #raw("octant_bit_order") $=$ #raw("lsb_x")), step $4$ maps to octant $1$ while step $6$ with $Delta z = (1, -1, 1)$ remains at octant $2$, giving $O_(upright("oct")) = (6, 1, 1, 0, 0, 0, 0, 0)$ and $Delta_(upright("oct"))^(bb(Z)) = (-5, 0, 0, 1, 1, 1, 1, 1)$ with transported $M_(delta_3 , upright("oct")) = 10$.


#figure(
  kind: table, [
#aod-csv-table(
  "/manual/data/boundary_sadar/coordinate_phase_3d_dec_walk.csv",
  columns: (7fr, 14fr, 14fr, 14fr, 9fr, 14fr, 14fr, 14fr),
  align: (center, left, left, left, right, right, right, right),
  size: 8.0pt,
  inset: (x: 3.4pt, y: 3.2pt),
  headers: (
    [Step $i$], [From $(x, y, z)$], [To $(x', y', z')$], [$Delta (x, y, z)$], [$Q_(upright("lag") 1)$], [$theta = Q mod 5$], [Octant (MSB-$x$)], [Octant (LSB-$x$)],
  ),
  cells: (
    "step_i",
    (kind: "vec", col: "from_xyz"),
    (kind: "vec", col: "to_xyz"),
    (kind: "vec", col: "delta_xyz"),
    "Q_lag1",
    "theta_mod5",
    "octant_msb_x",
    "octant_lsb_x",
  ),
)
  ],
  caption: [Engine-bound eight-step 3D lag-1 lattice displacement, $Q mod 5$ phase residue, and MSB-$x$ (#raw("RC-012")/#raw("RC-044")) versus LSB-$x$ (#raw("RC-013")) octant D.E.C. ledger (live from #raw("coordinate_phase_3d_dec_walk.csv")).],
) <tab:manual-app-c-3d-dec-ledger>

