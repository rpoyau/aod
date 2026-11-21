// Native Typst port of manual/sections/01_cell_measures.tex (verbatim scientific content).
#import "../preamble.typ": *

= Cell measures and geometric comparisons <manual:m3-cells>


#aod-paragraph[Construction.]
The model uses axis boxes with the cells of #mainsection("main:sec:m3-cells")
and boundary #mainequation("main:eq:m3-cubical-boundary").
Each coordinate is a vertex or a unit interval before scaling.
Increasing active-axis order fixes orientation.
The closure of one filled square contains four vertices, four
edges and one interior cell. The filled four-cube contains, by dimension,
$(16,32,24,8,1)$ cells. These fillings and their metric are model choices;
the inherited $Q_4$ graph supplies vertices and edges.


#aod-paragraph[Independent measures.]
For these boxes, a $d$-cell's weight is the product of its $d$ side lengths.
The interior measure adds the weights of occupied $d$-cells, counting each
cell once. A zero weight leaves the cell present.
The boundary operator cancels shared faces; the boundary measure adds the
weights of exposed faces. An independent check finds those faces from
neighbouring occupied cells. Shared faces remain in the complex.
At four-cube edge length $a = 3 slash 2$
in coordinate units $u$, literal enumeration gives

#math.equation(block: true, numbering: none, $ V_4 = frac(81, 16) thin u^4 , wide B_3 = 27 thin u^3 . $)

These are the four-volume $a^4$ and boundary three-measure $8 a^3$.


#aod-paragraph[Circle comparison.]#aod-anchor(<prop:m3-staircase>)
Use the full-turn constant $tau = 2 pi$: a Euclidean circle has
circumference $tau r$ and disk area $( tau slash 2)r^2$.
A monotone axial quarter path with coordinate displacements $r,r$,
$r > 0$, has length $2 r$ when its length is the sum of axial displacements.
Four quarters therefore have length $8 r$ at every subdivision, retaining
the discrepancy $(8 - tau )r$. Increasing numerical precision does not
change this axial length.

The fixed comparison object is the unit disk $x^2 + y^2 lt.eq 1$.
At resolution $n$, square cells have side $1 slash n$.
The outer staircase includes cells whose minimum squared corner radius is
strictly below one. The inner staircase includes cells whose maximum squared
corner radius is at most one. Integer inequalities select both supports before
any evaluation of $tau$. The radius report is the common maximum absolute
vertex coordinate on the two axes.

An independent quarter-column calculation defines upper and lower
rectangle heights
$u_i = ceil.l sqrt(n^2 - i^2) ceil.r$ and
$ell_i = floor.l sqrt(n^2 - (i + 1)^2) floor.r$, $0 lt.eq i < n$.
Monotonicity of the circle graph encloses its area between the two rectangle
sums. Writing each ceiling as its floor plus a number in $[0,1]$, the
floor differences telescope to $n$. Consequently

$ A_n^(-) lt.eq A_(upright("disk")) lt.eq A_n^(+) , wide A_n^(+) - A_n^(-) = frac(4, n^2) sum_(i = 0)^(n - 1) (u_i - ell_i ) lt.eq frac(8, n). $ <eq:m3-disk-enclosure>

Thus $A_n^(-) lt.eq tau slash 2 lt.eq A_n^(+)$,
while the exposed axial boundary has length $C_n = 8$ at every level.


#align(center)[
#{
  set text(size: 9.5pt)
  set par(justify: false)
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (right, right, right, right, right),
    table.header(
      toprule,
      [$n$], [$A_n^(-)$], [$A_n^(+)$], [$C_n$], [$C_n r_n - 2 A_n^(+)$],
      midrule,
    ),
    [1], [0], [4], [8], [0],
    [2], [1], [4], [8], [0],
    [4], [2], [$15 slash 4$], [8], [$1 slash 2$],
    [8], [$41 slash 16$], [$7 slash 2$], [8], [1],
    [16], [$183 slash 64$], [$107 slash 32$], [8], [$21 slash 16$],
    [32], [$385 slash 128$], [$833 slash 256$], [8], [$191 slash 128$],
    bottomrule,
  )
}
]

Area and the last column use $u^2$, length uses $u$, and $r_n = 1 u$.
The area enclosure narrows while the axial perimeter stays fixed.
Rational alternating-series enclosures for
$tau slash 2 = 16 arctan (1 slash 5) - 4 arctan (1 slash 239)$, with 4, 8 and 16 terms per series,
separately bound numerical reference error. Their lower bound for
$C_n - tau r_n$ remains positive.
The shared-coefficient controls $C = 2 q r$, $A = q r^2$, with
$q in brace.l 2,3,355 slash 113,7 slash 2 brace.r$, all give $C r - 2 A = 0$.
Each fails comparison with the independently computed finite measures.
The identity holds for every $q$, so that zero residual cannot identify
a common coefficient.


#aod-paragraph[Fold and projection.]
#mainequation("main:eq:m3-chain-map") is instantiated by two
adjacent unit squares, folded by $x arrow.r.bar min (x,2 - x)$ with $y$ fixed.
The right square reverses orientation. The complete induced maps commute with
boundary; the oriented top image is zero. The input occupied area remains
$2 u^2$ and the image support has area $1 u^2$. Every source cell retains
its inner scope, identity, construction lineage and outer image. Distinct
projected event identities cannot be merged to certify native closure.
Retaining both occurrences on the image gives multiplicity two.
This certifies boundary commutation for the declared fold, with retained
lineage; it certifies neither occupied-area preservation nor future response.
For a dynamical reduction, the retained state must distinguish histories with
different relevant next responses. The temporal finite control gives the same
current with different retained pressure and different next currents. Keeping
pressure resolves that collision on the enumerated states; it does not prove
a universal reduced dynamics.
For a two-by-one rectangle with axis weights $(2,1)$, the boundary measure
is $10 u$. Swapping only its coordinates gives $8 u$; swapping the metric
with the coordinates restores $10 u$.


#aod-paragraph[Execution and falsification.]
The contract is #raw("contracts/scientific/CELL_MEASURE_SPEC.json").
The command
#raw("python3") #raw("manual/scripts/aod_cell_measures.py") #raw("--check-data")
reproduces #raw("manual/data/cell_measures/cells_geometry.json") from the declared
construction. Reversing one face incidence while retaining its endpoint
incidences can make $partial^2 c eq.not 0$. Reversing a folded face without
its induced edge map can violate #mainequation("main:eq:m3-chain-map").
The implementation executes mutations of incidence, fold orientation, integer
chain coefficients, duplicate
occupancy, dimension, native metric promotion, projection reconstruction,
projected closure and refinement inputs. The companion tests also mutate face
counts and metric weights and isolate evaluation constants from construction.
