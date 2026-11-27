// Native Typst authority for Manual §5: cell measures, 4D tesseract-to-pi enclosures, and cellular fold.
#import "../preamble.typ": *

= Cell measures and geometric comparisons <manual:m3-cells>


#aod-paragraph[Setup: cubical cell complex and five-boundary stack.]
This section instantiates the finite axis-box complex of #mainsection("main:sec:m3-cells")
with cubical boundary #mainequation("main:eq:m3-cubical-boundary") across 2D disk and
4D tesseract-to-$pi$ enclosures and a two-square cellular fold.
Each coordinate span is a vertex or a unit interval before rational scaling, and
increasing active-axis order fixes orientation.
The closure of one filled square contains $(4, 4, 1)$ cells (four vertices, four edges,
and one interior cell), while the filled four-cube contains $(16, 32, 24, 8, 1)$ cells
by dimension. These fillings and their Euclidean or axial report metric in coordinate
units $u$ are explicit conditional model choices: the inherited $Q_4$ graph supplies
vertices and $H_1$ edges, and no native higher-cell admission or physical
length/area/volume is derived here.

To keep integer cell construction strictly isolated from continuum reference constants,
declare the five-boundary stack

#math.equation(block: true, numbering: none, $ B_(upright("cell")) arrow.r B_(upright("stair")) arrow.r B_(upright("fold")) arrow.r B_(upright("audit")) arrow.r B_(upright("ext")) . $)

All integer cell selection, weight sums, staircase boundaries, integer-root enclosures,
and chain-map checks execute inside the core stages $B_(upright("core")) = (B_(upright("cell")), B_(upright("stair")), B_(upright("fold")), B_(upright("audit")))$,
while Machin arctangent bounds for $pi$ enter strictly downstream in $B_(upright("ext"))$
after the finite geometry is frozen.


#aod-paragraph[Derivation: independent measures and filled four-cube.]
For elementary axis boxes, a $d$-cell's weight is the product of its $d$ side lengths.
The interior measure adds the weights of occupied $d$-cells, counting each cell once;
a zero weight leaves the cell present in support.
The signed boundary operator cancels shared codimension-one faces while leaving them
present in the complex, and the boundary measure adds the weights of the remaining
exposed faces. An independent oracle locates those exposed faces directly from absent
top-cell neighbours.
At four-cube edge length $a = 3 slash 2$ in coordinate units $u$, literal enumeration gives

#math.equation(block: true, numbering: none, $ V_4 = frac(81, 16) thin u^4 , wide B_3 = 27 thin u^3 , $)

matching the four-volume $a^4$ and exposed boundary three-measure $8 a^3$.


#aod-paragraph[Derivation: 2D circle enclosure and axial staircase.]#aod-anchor(<prop:m3-staircase>)
Write the full-turn constant $tau = 2 pi$: a Euclidean circle of radius $r$ has
circumference $tau r$ and disk area $(tau slash 2) r^2$.
A monotone axial quarter path with coordinate displacements $r, r$ ($r > 0$) has length
$2 r$ when measured as the sum of axial displacements. Four quarters therefore have
exposed length $8 r$ at every subdivision, retaining the fixed discrepancy $(8 - tau) r$;
increasing numerical precision does not remove this axial-metric mismatch.

Take the closed unit disk $x^2 + y^2 lt.eq 1$ in declared Euclidean report coordinates.
At dyadic resolution $n in brace.l 1, 2, 4, 8, 16, 32 brace.r$, square microcells have
side $1 slash n$ in $[-1, 1]^2$ (equivalently unit integer cells in $[-n, n]^2$).
The outer staircase retains integer cells whose minimum corner squared radius is strictly
below $n^2$; the inner staircase retains cells whose maximum corner squared radius is at
most $n^2$. Integer inequalities fix both supports before any evaluation of $tau$, and
the radius report is the common maximum absolute axis coordinate $r_n = 1 thin u$.
An independent quarter-column calculation defines upper and lower rectangle heights
$u_i = ceil.l sqrt(n^2 - i^2) ceil.r$ and
$ell_i = floor.l sqrt(n^2 - (i + 1)^2) floor.r$, $0 lt.eq i < n$.
Monotonicity of the circle graph encloses the disk area between the two rectangle sums,
and writing each ceiling as its floor plus a remainder in $[0, 1]$ telescopes the floor
differences to $n$. Consequently

$ A_n^(-) lt.eq A_(upright("disk")) lt.eq A_n^(+) , wide A_n^(+) - A_n^(-) = frac(4, n^2) sum_(i = 0)^(n - 1) (u_i - ell_i ) lt.eq frac(8, n). $ <eq:m3-disk-enclosure>

Thus $A_n^(-) lt.eq tau slash 2 lt.eq A_n^(+)$ narrows deterministically with width at
most $8 slash n$ (reaching $63 slash 256$ at $n = 32$), while the exposed axial boundary
remains fixed at $C_n = 8 thin u$ for every $n$ and falsifies $C r = 2 A$ via
$C_n r_n - 2 A_n^(+) > 0$ for all $n gt.eq 4$ (unified 2D and 4D ledger in
@tab:manual-cell-boundary-fold-ledger).


#aod-paragraph[Derivation: 4D tesseract-to-$pi$ enclosure and exposed 3-boundary (opened G6).]
Extend the same declared Euclidean report coordinates to the closed unit four-ball
$B^4 = brace.l x in [-1, 1]^4 : x_1^2 + x_2^2 + x_3^2 + x_4^2 lt.eq 1 brace.r$ inside
the bounding four-cube $[-1, 1]^4$, subdivided into $(2 n)^4$ cubical microcells of side
$1 slash n$ and four-volume $1 slash n^4$ at dyadic levels $n in brace.l 1, 2, 4, 8, 16, 32 brace.r$.
Integer selection rules again act strictly inside $B_(upright("core"))$ without reading
$pi$ or $tau$: an integer microcell in $[-n, n]^4$ belongs to the outer support when its
minimum corner squared radius is strictly below $n^2$, and to the inner support when its
maximum corner squared radius is at most $n^2$.
Let $N_(upright("in"))(n)$ and $N_(upright("out"))(n)$ denote the positive-orthant counts
(computed by 16-orthant sorted multinomial symmetry and cross-checked against independent
3D-column integer-root summation plus literal 4D enumeration for $n in brace.l 1, 2, 4 brace.r$).
The exact rational four-volume inclusion enclosure is

#math.equation(block: true, numbering: none, $ V_(4,n)^(-) = frac(16 N_(upright("in"))(n), n^4) lt.eq frac(pi^2, 2) lt.eq frac(16 N_(upright("out"))(n), n^4) = V_(4,n)^(+) , wide V_(4,n)^(+) - V_(4,n)^(-) lt.eq frac(64, n) . $)

The deterministic width bound $64 slash n$ follows in each orthant by indexing integer
microcells by their minimum corner $(k_1, k_2, k_3, k_4) in brace.l 0, dots.h, n - 1 brace.r^4$
and applying the inward diagonal shift injection
$(k_1, k_2, k_3, k_4) arrow.r.bar m = (k_1 - 1, k_2 - 1, k_3 - 1, k_4 - 1)$ on outer
orthant cells with all $k_j gt.eq 1$ (not on the four coordinate faces $k_j = 0$),
guaranteeing $sum_(i = 1)^4 (m_i + 1)^2 = sum_(i = 1)^4 k_i^2 < n^2$ (hence $m$ is an
inner cell) and leaving at most $n^4 - (n - 1)^4 lt.eq 4 n^3$ boundary cells per orthant
($16 dot.op 4 n^3 slash n^4 = 64 slash n$); no probability distribution or $sigma$ is
supplied.
Because $2 V_4(B^4) = pi^2$, exact integer square roots of the finite four-cube counts
yield a pure 4D enclosure for $pi$ strictly inside $B_(upright("core"))$ with zero Machin
arctangent terms:

#math.equation(block: true, numbering: none, $ pi_(upright("4D"),n)^(-) := frac(floor.l sqrt(32 N_(upright("in"))(n)) floor.r, n^2) lt.eq pi lt.eq frac(ceil.l sqrt(32 N_(upright("out"))(n)) ceil.r, n^2) =: pi_(upright("4D"),n)^(+) . $)

Writing $A_(2,n)^(plus.minus) := A_n^(plus.minus)$ for the 2D disk bounds of
#eqref("eq:m3-disk-enclosure"), for every $n gt.eq 2$ the cross-dimensional ratio
$pi_(times,n)^(-) := 2 V_(4,n)^(-) slash A_(2,n)^(+) lt.eq pi lt.eq 2 V_(4,n)^(+) slash A_(2,n)^(-) =: pi_(times,n)^(+)$
likewise brackets $pi$ without Machin input (null at $n = 1$ where $A_(2,1)^(-) = 0$,
narrowing from $[1 slash 2, 30]$ at $n = 2$ to $[72561 slash 26656, 89701 slash 24640]$ at
$n = 32$).

Crucially, the exposed three-boundary of the outer 4-ball microcell staircase must be
distinguished from the exposed three-boundary of the bounding four-cube $[-1, 1]^4$.
Along each of the four coordinate axes, orthogonal projection of the outer 4-ball support
onto the remaining three coordinates equals the outer 3-ball staircase support
$V_(3,n)^(+) = 8 N_(3,upright("out"))(n) slash n^3$, contributing two exposed 3-faces per
projected 3-column across all four axes. Hence the exact exposed 3-boundary of the outer
4-ball staircase is

#math.equation(block: true, numbering: none, $ B_(3,upright("stair"),n)^(+) = 8 V_(3,n)^(+) = frac(64 N_(3,upright("out"))(n), n^3) arrow.r_(n arrow.r infinity) frac(32 pi, 3) eq.not 2 pi^2 , $)

taking exact values $64, 64, 51, 341 slash 8, 2443 slash 64,$ and $9179 slash 256$ (in $u^3$)
for $n = 1, 2, 4, 8, 16, 32$ and verified by literal neighbour absence on $64, 512,$ and
$3264$ exposed 3-faces at $n in brace.l 1, 2, 4 brace.r$.
By contrast, the bounding four-cube $[-1, 1]^4$ has constant exposed three-boundary
$B_(3,upright("box")) = 8 dot.op 2^3 = 64 thin u^3$ at every level, which is strictly
distinct from $B_(3,upright("stair"),n)^(+)$ for all $n gt.eq 4$.
Both boundaries falsify the Euclidean four-ball identity $B_3 r = 4 V_4$ at every
$n gt.eq 2$: the exposed staircase residual
$B_(3,upright("stair"),n)^(+) - 4 V_(4,n)^(+)$ remains strictly positive (reaching
$57163 slash 4096$ at $n = 32$ and converging to $32 pi slash 3 - 2 pi^2 > 0$), while the
box residual $B_(3,upright("box")) - 4 V_(4,n)^(+)$ grows to $172443 slash 4096$ at $n = 32$.
As in 2D, this opened #raw("G6") extension is a declared verification model only and makes no
physical continuum claim or native higher-cell admission.


#aod-paragraph[Specialization: cellular fold chain map, projection, and anisotropy.]
The chain-map condition #mainequation("main:eq:m3-chain-map") ($B_d^L F_d = F_(d - 1) B_d^K$)
is instantiated by folding two adjacent oriented unit squares
$K_2 = Q_L union Q_R = ([0, 1] times [0, 1]) union ([1, 2] times [0, 1])$ onto the single
unit square $L_2 = Q_* = [0, 1] times [0, 1]$ via $x arrow.r.bar min(x, 2 - x)$ with $y$
fixed. Active reversal along $x$ flips orientation on the right square, giving
$F_2(Q_L) = + Q_*$ and $F_2(Q_R) = - Q_*$. The complete induced integer matrices commute
with boundary identically ($B_d^L F_d - F_(d - 1) B_d^K = 0$ on every vertex, edge, and
2-cell): the shared vertical seam cancels ($+1 - 1 = 0$) in $partial(Q_L + Q_R)$, the
oriented top image vanishes ($F_2(Q_L + Q_R) = 0$), and $F_1(partial(Q_L + Q_R)) = 0$.
Meanwhile, the unsigned input occupied area remains $2 thin u^2$ (exposed boundary $6 thin u$)
and the image support has area $1 thin u^2$ (exposed boundary $4 thin u$). Retaining both
preimage occurrences on $Q_*$ yields unsigned multiplicity two, and every source cell
retains its inner scope, identity, construction lineage, and outer image. Distinct
projected event identities cannot be merged to certify native closure.

This certifies boundary commutation for the declared fold with retained lineage; it
certifies neither occupied-area preservation nor future response. For a dynamical
reduction, the retained state must distinguish histories with different relevant next
responses: the temporal finite control exhibits the same current with different retained
pressure and different next currents, so keeping pressure resolves that collision on the
enumerated states without proving a universal reduced dynamics.
Anisotropy is checked on a $2 times 1$ rectangle with fixed axis weights $(2, 1)$, whose
exposed boundary is $10 thin u$; swapping only its coordinates gives $8 thin u$, whereas
jointly swapping the metric with the coordinates restores $10 thin u$.


#aod-paragraph[Falsification: quarantined Machin bounds, shared-$q$ controls, and execution guards.]
Downstream in $B_(upright("ext"))$, rational alternating-series enclosures for
$tau slash 2 = pi = 16 arctan(1 slash 5) - 4 arctan(1 slash 239)$ with $4, 8,$ and $16$
terms per series separately bound numerical reference error after geometry is frozen.
They certify $C_n - tau r_n > 0$ in 2D together with
$V_(4,n)^(-) lt.eq pi^2 slash 2 lt.eq V_(4,n)^(+)$,
$pi_(upright("4D"),n)^(-) lt.eq pi lt.eq pi_(upright("4D"),n)^(+)$, and
$32 pi slash 3 - 2 pi^2 > 0$ in 4D.
Shared-coefficient controls in 2D ($C = 2 q r$, $A = q r^2 arrow.r.double C r - 2 A = 0$)
and in 4D ($B_3 = 2 q^2 r^3$, $V_4 = (q^2 slash 2) r^4 arrow.r.double B_3 r - 4 V_4 = 0$)
for $q in brace.l 2, 3, 355 slash 113, 7 slash 2 brace.r$ all yield zero residual
identically while failing comparison against the independently computed finite measures;
a zero residual therefore cannot identify a common coefficient.

The governing contract is #raw("contracts/scientific/CELL_MEASURE_SPEC.json").
Running #raw("python3") #raw("manual/scripts/aod_cell_measures.py") #raw("--check-data")
reproduces #raw("manual/data/cell_measures/cells_geometry.json") from the declared
construction. Reversing one face incidence while retaining endpoint incidences makes
$partial^2 c eq.not 0$, and reversing a folded face without its induced edge map violates
#mainequation("main:eq:m3-chain-map"). The implementation executes all twelve negative
controls: incidence orientation, fold orientation, noninteger chain-map coefficients,
duplicate occupancy, dimension mismatch, native metric promotion, many-to-one projection
reconstruction, projected closure promotion, 2D refitted refinement, conflation of
$B_(3,upright("stair"),4)^(+) = 51$ with $64$, fake 4D volume enclosure failing to contain
$pi^2 slash 2$, and 4D refitted refinement. Companion tests further mutate face counts and
metric weights and isolate evaluation constants from construction.


== Five-boundary cell-enclosure and cellular fold D.E.C. ledger <manual:m3-cells:dec-staircase-fold>

Vector #raw("RC-035") (#raw("manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv"),
verified by #raw("python3 -B -m manual.engine") #raw("--sector") #raw("boundary_sadar")
and #raw("aod-core") #raw("--verify-vectors") #raw("--check-zero-float")) binds the
unified 2D disk and 4D tesseract microcell enclosures across $n in brace.l 1, 2, 4, 8, 16, 32 brace.r$
together with the two-square fold chain map $B_d^L F_d = F_(d - 1) B_d^K$ along
$B_(upright("cell")) arrow.r B_(upright("stair")) arrow.r B_(upright("fold")) arrow.r B_(upright("audit")) arrow.r B_(upright("ext"))$.
At $n = 32$, the 2D bracket narrows to $A_(32)^(+) - A_(32)^(-) = 63 slash 256$ with
$C_(32) r - 2 A_(32)^(+) = 191 slash 128 > 0$ ($C_n = 8$), while the 4D tesseract bracket
narrows to $V_(4,32)^(+) - V_(4,32)^(-) = 4285 slash 4096$ with pure finite-4-cube bounds
$pi_(upright("4D"),32) in [3047 slash 1024, 3389 slash 1024]$ ($[2.975586, 3.309570]$),
exposed staircase 3-boundary $B_(3,upright("stair"),32)^(+) = 9179 slash 256 eq.not 64$,
and falsifier residual $B_(3,upright("stair"),32)^(+) - 4 V_(4,32)^(+) = 57163 slash 4096 > 0$,
all computed without importing continuum $pi$ from $B_(upright("ext"))$.


#figure(
  kind: image, [
#include "../../lib/figures/manual/cell_staircase_fold_boundary.typ"
  ],
  caption: [Projected 4D tesseract $B^4$ microcell geometry, dyadic convergence of pure 4D $pi_(upright("4D"),n)^(plus.minus)$ and 2D $A_(2,n)^(plus.minus)$ bounds, 4D volume $4 V_(4,n)^(plus.minus) arrow.r 2 pi^2$ versus exposed staircase $B_(3,upright("stair"),n)^(+) = 8 V_(3,n)^(+) arrow.r 32 pi slash 3$ and box $B_(3,upright("box")) = 64$, and two-square cellular fold commutation $B_d^L F_d = F_(d - 1) B_d^K$ (#raw("cell_measures_staircase_fold_dec.csv")).],
) <fig:manual-cell-staircase-fold>


#figure(
  kind: table, [
#{
  set text(size: 7.6pt)
  set par(justify: false)
  table(
    columns: (0.40fr, 0.78fr, 0.78fr, 1.04fr, 1.04fr, 1.04fr, 0.86fr, 0.86fr, 1.04fr, 1.50fr),
    align: (right, right, right, right, right, right, right, right, right, right),
    inset: (x: 3pt, y: 3.5pt),
    table.header(
      toprule,
      [$n$],
      [$A_n^(-)$],
      [$A_n^(+)$],
      [$C_n r - 2 A_n^(+)$],
      [$V_(4,n)^(-)$],
      [$V_(4,n)^(+)$],
      [$pi_(upright("4D"),n)^(-)$],
      [$pi_(upright("4D"),n)^(+)$],
      [$B_(3,upright("stair"),n)^(+)$],
      [$B_(3,upright("stair"),n)^(+) - 4 V_(4,n)^(+)$],
      midrule,
    ),
    [1], [0], [4], [0], [0], [16], [0], [6], [64], [0],
    [2], [1], [4], [0], [1], [15], [$frac(5, 4)$], [$frac(11, 2)$], [64], [4],
    [4], [2], [$frac(15, 4)$], [$frac(1, 2)$], [2], [10], [2], [$frac(9, 2)$], [51], [11],
    [8], [$frac(41, 16)$], [$frac(7, 2)$], [1], [$frac(201, 64)$], [$frac(931, 128)$], [$frac(5, 2)$], [$frac(245, 64)$], [$frac(341, 8)$], [$frac(433, 32)$],
    [16], [$frac(183, 64)$], [$frac(107, 32)$], [$frac(21, 16)$], [$frac(8127, 2048)$], [$frac(6201, 1024)$], [$frac(721, 256)$], [$frac(891, 256)$], [$frac(2443, 64)$], [$frac(3571, 256)$],
    [32], [$frac(385, 128)$], [$frac(833, 256)$], [$frac(191, 128)$], [$frac(72561, 16384)$], [$frac(89701, 16384)$], [$frac(3047, 1024)$], [$frac(3389, 1024)$], [$frac(9179, 256)$], [$frac(57163, 4096)$],
    bottomrule,
  )
}
  ],
  caption: [Unified 2D unit-disk and opened #raw("G6") 4D tesseract-to-$pi$ dyadic rational enclosure and staircase falsifier ledger (#raw("RC-035")). Throughout, $r = 1 thin u$, the 2D axial perimeter is fixed at $C_n = 8 thin u$, and the bounding 4-cube 3-boundary is fixed at $B_(3,upright("box")) = 64 thin u^3$ (strictly distinct from $B_(3,upright("stair"),n)^(+) = 8 V_(3,n)^(+)$ for all $n gt.eq 4$).],
) <tab:manual-cell-boundary-fold-ledger>
