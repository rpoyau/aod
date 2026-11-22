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
