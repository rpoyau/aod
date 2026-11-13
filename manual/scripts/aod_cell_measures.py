"""M3 exact finite cubical verification models; no native metric is inferred.

Cell incidence, unsigned support, signed chains, and report-space weights are
distinct objects. Disk generation does not consume pi or evaluation targets.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from itertools import product
import json
from math import isqrt
from pathlib import Path
from typing import Callable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual/data/m3/cells_geometry.json"
SPEC = ROOT / "contracts/scientific/CELL_MEASURE_SPEC.json"


class CellError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CellError(message)


def exact(value):
    require(type(value) in (int, str, Fraction), "exact rational required")
    return Fraction(value)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


@dataclass(frozen=True, order=True)
class Cell:
    """An oriented elementary axis box; increasing active axes set orientation."""
    spans: tuple[tuple[int, int], ...]

    def __post_init__(self):
        require(bool(self.spans), "positive ambient dimension required")
        require(all(type(a) is int and type(b) is int and b-a in (0, 1)
                    for a, b in self.spans), "elementary integer intervals required")

    @property
    def dimension(self):
        return sum(a != b for a, b in self.spans)

    @property
    def identity(self):
        return "x".join(f"[{a},{b}]" for a, b in self.spans)


Chain = dict[Cell, Fraction]


def clean(chain):
    """Zero coefficients leave a chain; occupied support is stored separately."""
    return {cell: exact(value) for cell, value in chain.items() if exact(value)}


def boundary_cell(cell: Cell) -> Chain:
    result = {}
    active = 0
    for axis, (a, b) in enumerate(cell.spans):
        if a == b:
            continue
        for endpoint, side in ((a, -1), (b, 1)):
            spans = list(cell.spans)
            spans[axis] = (endpoint, endpoint)
            result[Cell(tuple(spans))] = Fraction(side * (-1)**active)
        active += 1
    return result


def boundary(chain: Mapping[Cell, Fraction], incidence=boundary_cell) -> Chain:
    result = defaultdict(Fraction)
    for cell, coefficient in chain.items():
        for face, sign in incidence(cell).items():
            result[face] += exact(coefficient) * exact(sign)
    return clean(result)


def closure(tops):
    cells = set()
    for cell in tops:
        choices = [[(a, a)] if a == b else [(a, a), (a, b), (b, b)]
                   for a, b in cell.spans]
        cells.update(Cell(tuple(spans)) for spans in product(*choices))
    return frozenset(cells)


@dataclass(frozen=True)
class CubicalComplex:
    scope: str
    tops: tuple[Cell, ...]
    admission: str = "declared_verification_model"

    def __post_init__(self):
        require(bool(self.scope) and bool(self.tops), "scope and top support required")
        require(len(self.tops) == len(set(self.tops)), "duplicate occupied support")
        ambient = len(self.tops[0].spans)
        require(all(len(c.spans) == ambient and c.dimension == ambient for c in self.tops),
                "pure full-dimensional elementary support required")
        require(self.admission == "declared_verification_model", "unlicensed native metric promotion")

    @property
    def cells(self):
        return closure(self.tops)

    @property
    def dimension(self):
        return self.tops[0].dimension

    @property
    def top_chain(self):
        return {c: Fraction(1) for c in self.tops}


def check_complex(complex_, incidence=boundary_cell):
    cells = complex_.cells
    for cell in cells:
        first = incidence(cell)
        require(all(exact(v).denominator == 1 for v in first.values()),
                "integer incidence coefficients required")
        require(all(f in cells and f.dimension == cell.dimension-1 for f in first),
                "incidence outside complex or wrong dimension")
        require(not boundary(first, incidence), "boundary squared is nonzero")
    return True


@dataclass(frozen=True)
class Measure:
    value: Fraction
    dimension: int
    unit: str
    support: tuple[str, ...]


def support_measure(visits, weights: Mapping[Cell, Fraction], dimension, unit="u"):
    support = frozenset(visits)
    require(all(c.dimension == dimension for c in support), "measure dimension mismatch")
    require(all(c in weights for c in support), "missing support weight")
    values = [exact(weights[c]) for c in support]
    require(all(v >= 0 for v in values), "unsigned weight must be nonnegative")
    return Measure(sum(values, Fraction(0)), dimension, f"{unit}^{dimension}",
                   tuple(sorted(c.identity for c in support)))


def metric_weights(cells, axis_lengths):
    lengths = tuple(exact(v) for v in axis_lengths)
    require(all(v > 0 for v in lengths), "metric axis lengths must be positive")
    result = {}
    for c in cells:
        require(len(c.spans) == len(lengths), "metric ambient dimension mismatch")
        value = Fraction(1)
        for axis, (a, b) in enumerate(c.spans):
            if a != b:
                value *= lengths[axis]
        result[c] = value
    return result


def exposed_faces_by_occupancy(complex_):
    """Independent neighbour route: no boundary operator or target formula."""
    occupied = {tuple(a for a, _ in c.spans) for c in complex_.tops}
    result = set()
    for origin in occupied:
        for axis in range(complex_.dimension):
            for direction in (-1, 1):
                neighbor = list(origin)
                neighbor[axis] += direction
                if tuple(neighbor) in occupied:
                    continue
                spans = [(x, x+1) for x in origin]
                endpoint = origin[axis] + (direction == 1)
                spans[axis] = (endpoint, endpoint)
                result.add(Cell(tuple(spans)))
    return frozenset(result)


def measures(complex_, axis_lengths):
    weights = metric_weights(complex_.cells, axis_lengths)
    exterior = boundary(complex_.top_chain)
    require(all(abs(v) == 1 for v in exterior.values()), "non-unit exposed multiplicity")
    neighbor_faces = exposed_faces_by_occupancy(complex_)
    require(set(exterior) == set(neighbor_faces), "independent boundary disagreement")
    # Interior uses unsigned occupied top cells, never boundary or perimeter.
    interior = support_measure(complex_.tops, weights, complex_.dimension)
    skin = support_measure(exterior, weights, complex_.dimension-1)
    return interior, skin


def cell_record(cell):
    return {"id": cell.identity, "dimension": cell.dimension,
            "spans": [list(pair) for pair in cell.spans],
            "boundary": {f.identity: str(s) for f, s in sorted(boundary_cell(cell).items())}}


def finite_record(complex_, lengths):
    check_complex(complex_)
    interior, skin = measures(complex_, lengths)
    cells = sorted(complex_.cells)
    return {"scope": complex_.scope, "admission": complex_.admission,
            "ambient_dimension": complex_.dimension,
            "construction": "closure of the listed elementary top cells",
            "top_support": [c.identity for c in sorted(complex_.tops)],
            "cells": [cell_record(c) for c in cells],
            "counts_by_dimension": dict(sorted(Counter(c.dimension for c in cells).items())),
            "axis_lengths": [str(exact(x)) for x in lengths],
            "interior": {"value": str(interior.value), "dimension": interior.dimension,
                         "unit": interior.unit, "route": "unsigned occupied-cell weight sum"},
            "boundary": {"value": str(skin.value), "dimension": skin.dimension,
                         "unit": skin.unit, "route": "oriented incidence cancellation"},
            "independent_boundary_route": "top-cell neighbour occupancy",
            "boundary_squared_zero": True}


def apply_map(chain, images):
    result = defaultdict(Fraction)
    for cell, coefficient in chain.items():
        require(cell in images, "missing fold source identity")
        for image, sign in images[cell].items():
            result[image] += exact(coefficient) * exact(sign)
    return clean(result)


def check_chain_map(source, target, images):
    require(set(images) == set(source.cells), "fold must retain every source identity")
    for cell in source.cells:
        require(all(exact(v).denominator == 1 for v in images[cell].values()),
                "integer chain-map coefficients required")
        require(all(c in target.cells and c.dimension == cell.dimension for c in images[cell]),
                "fold target or dimension mismatch")
        require(boundary(images[cell]) == apply_map(boundary_cell(cell), images),
                "fold does not commute with boundary")
    return True


def reflected_two_square_fold():
    left = Cell(((0, 1), (0, 1)))
    right = Cell(((1, 2), (0, 1)))
    source = CubicalComplex("two-square-inner", (left, right))
    target = CubicalComplex("single-square-outer", (left,))
    images = {}
    for cell in source.cells:
        a, b = cell.spans[0]
        x, y = min(a, 2-a), min(b, 2-b)
        spans = ((min(x, y), max(x, y)), cell.spans[1])
        sign = -1 if x > y else 1
        images[cell] = {Cell(spans): Fraction(sign)}
    check_chain_map(source, target, images)
    return source, target, images


def unique_preimage(images, target_identity):
    candidates = [key for key, value in images.items() if value == target_identity]
    require(len(candidates) == 1, "many-to-one projection has no unique reconstruction")
    return candidates[0]


def require_closed_identity(start_id, end_id, projected_start, projected_end):
    require(start_id == end_id, "coincident projected endpoints do not certify native closure")
    return projected_start == projected_end


def fold_record():
    source, target, images = reflected_two_square_fold()
    before, before_skin = measures(source, (1, 1))
    after, after_skin = measures(target, (1, 1))
    retained = [{"inner_scope": source.scope, "inner_cell_id": c.identity,
                 "construction_lineages": ["square-left" if top.spans[0][0] == 0
                                            else "square-right" for top in source.tops
                                            if c in closure((top,))],
                 "outer_scope": target.scope,
                 "image": {t.identity: str(s) for t, s in sorted(images[c].items())}}
                for c in sorted(source.cells)]
    return {"source_scope": source.scope, "target_scope": target.scope,
            "law": "x maps to min(x,2-x); y fixed; active-axis reversal supplies sign",
            "chain_map": check_chain_map(source, target, images),
            "retained_inner_to_outer": retained,
            "input_occupancy_area": str(before.value),
            "image_support_area": str(after.value),
            "input_exposed_boundary_length": str(before_skin.value),
            "image_exposed_boundary_length": str(after_skin.value),
            "oriented_top_image": {c.identity: str(v) for c, v in
                                   apply_map(source.top_chain, images).items()},
            "preserves": ["chain boundary", "source identity and scope records"],
            "does_not_preserve": ["injectivity", "unsigned area", "oriented multiplicity"],
            "native_certificates": "not applicable: conditional cells add no native admission"}


def disk_tops(n, kind="outer"):
    """Fixed unit disk: rational cells selected using integer inequalities only."""
    require(type(n) is int and n > 0, "positive integer refinement required")
    require(kind in ("inner", "outer"), "unknown disk estimator")
    cells = []
    for i in range(-n, n):
        for j in range(-n, n):
            spans = ((i, i+1), (j, j+1))
            near = sum(min(abs(a), abs(b))**2 for a, b in spans)
            far = sum(max(abs(a), abs(b))**2 for a, b in spans)
            if (kind == "outer" and near < n*n) or (kind == "inner" and far <= n*n):
                cells.append(Cell(spans))
    return tuple(cells)


def independent_disk_count(n, kind):
    """Quarter-column integer roots; independent of literal-cell enumeration."""
    count = 0
    for i in range(n):
        square = n*n - (i if kind == "outer" else i+1)**2
        h = isqrt(square)
        if kind == "outer" and h*h != square:
            h += 1
        count += h
    return 4*count


def radius_from_vertices(complex_, scale):
    """Axis extent report, independent of boundary-length and area routines."""
    vertices = [c for c in complex_.cells if c.dimension == 0]
    extents = [max(abs(c.spans[axis][0]) for c in vertices) * exact(scale)
               for axis in range(complex_.dimension)]
    require(len(set(extents)) == 1, "radius extent convention requires equal axis extents")
    return extents[0]


def validate_disk_refinement(coarse_n, fine_n, coarse_cells, fine_cells):
    require(fine_n == 2*coarse_n, "declared refinement is dyadic")
    require(tuple(coarse_cells) == disk_tops(coarse_n), "changed coarse object or estimator")
    require(tuple(fine_cells) == disk_tops(fine_n), "changed fine object or estimator")
    coarse_set = set(coarse_cells)
    for cell in fine_cells:
        parent = Cell(tuple((a//2, a//2+1) for a, _ in cell.spans))
        require(parent in coarse_set, "outer refinement leaves parent support")
    return True


def disk_level(n):
    tops = disk_tops(n)
    model = CubicalComplex(f"unit-disk-outer-n{n}", tops)
    interior, skin = measures(model, (Fraction(1, n),)*2)
    inner_count = len(disk_tops(n, "inner"))
    require(len(tops) == independent_disk_count(n, "outer"), "outer count route disagreement")
    require(inner_count == independent_disk_count(n, "inner"), "inner count route disagreement")
    r = radius_from_vertices(model, Fraction(1, n))
    return {"n": n, "object": "closed unit disk x^2+y^2<=1",
            "comparison_scope": "same Euclidean coordinate unit u at every level",
            "estimator": "fixed outer axial staircase; cell side 1/n",
            "outer_support_count": len(tops), "inner_support_count": inner_count,
            "outer_support_sha256": digest([c.identity for c in tops]),
            "A_outer": str(interior.value), "A_inner": str(Fraction(inner_count, n*n)),
            "area_enclosure_width": str(interior.value-Fraction(inner_count, n*n)),
            "certified_area_gap_bound": str(Fraction(8, n)),
            "C_axial": str(skin.value), "r_axis_extent": str(r),
            "Cr_minus_2A": str(skin.value*r-2*interior.value),
            "units": {"C_axial": "u^1", "r_axis_extent": "u^1", "A_outer": "u^2",
                      "Cr_minus_2A": "u^2"},
            "area_claim": "certified inclusion enclosure with width <= 8/n; interval width is not sigma",
            "boundary_claim": "exact axial perimeter 8, independent of n",
            "coefficient_claim": "no common circle coefficient determined"}


def arctan_bounds(inverse, terms):
    require(type(inverse) is int and inverse > 1 and type(terms) is int and terms > 0,
            "arctangent bound requires integer inverse>1 and terms>0")
    partial = sum((Fraction((-1)**k, (2*k+1)*inverse**(2*k+1))
                   for k in range(terms)), Fraction(0))
    next_sum = partial + Fraction((-1)**terms, (2*terms+1)*inverse**(2*terms+1))
    return min(partial, next_sum), max(partial, next_sum)


def pi_reference_bounds(terms):
    """Downstream Machin identity and alternating-series rational enclosure."""
    lo5, hi5 = arctan_bounds(5, terms)
    lo239, hi239 = arctan_bounds(239, terms)
    return 16*lo5-4*hi239, 16*hi5-4*lo239


def compare_disk_reference(level, pi_bounds):
    lo, hi = map(exact, pi_bounds)
    require(0 < lo <= hi < 4, "pi comparison enclosure outside declared domain")
    c, r = exact(level["C_axial"]), exact(level["r_axis_extent"])
    return {"reference_only": True, "pi_lower": str(lo), "pi_upper": str(hi),
            "C_minus_2pi_r_lower": str(c-2*hi*r),
            "C_minus_2pi_r_upper": str(c-2*lo*r),
            "arithmetic": "exact rational enclosure; numerical precision is separate from metric mismatch"}


def shared_coefficient_control(level, q):
    q = exact(q)
    radius = exact(level["r_axis_extent"])
    c, area = 2*q*radius, q*radius**2
    return {"q": str(q), "C": str(c), "A": str(area),
            "Cr_minus_2A": str(c*radius-2*area),
            "agrees_with_independent_measures":
                c == exact(level["C_axial"]) and area == exact(level["A_outer"]),
            "determines_q": False}


def anisotropy_record():
    horizontal = CubicalComplex("rectangle-horizontal",
                                (Cell(((0, 1), (0, 1))), Cell(((1, 2), (0, 1)))))
    vertical = CubicalComplex("rectangle-vertical",
                              (Cell(((0, 1), (0, 1))), Cell(((0, 1), (1, 2)))))
    _, h = measures(horizontal, (2, 1))
    _, v = measures(vertical, (2, 1))
    _, covariant = measures(vertical, (1, 2))
    return {"fixed_axis_weights": ["2", "1"],
            "horizontal_boundary": str(h.value), "swapped_cells_only_boundary": str(v.value),
            "swapped_cells_and_metric_boundary": str(covariant.value),
            "isotropic_claim_rejected": h.value != v.value,
            "joint_relabelling_invariant": h.value == covariant.value}


def expect_rejection(action: Callable[[], object]):
    try:
        action()
    except CellError as error:
        return str(error)
    raise CellError("negative control survived")


def negative_controls():
    source, target, images = reflected_two_square_fold()
    square = target.tops[0]
    edge = Cell(((0, 1), (0, 0)))

    def bad_incidence(cell):
        output = boundary_cell(cell)
        if cell == edge:
            vertex = min(output)
            output[vertex] *= -1
        return output

    corrupted_images = dict(images)
    corrupted_images[source.tops[1]] = {square: Fraction(1)}
    half_identity = {c: {c: Fraction(1, 2)} for c in target.cells}
    coordinates = {"inner-event-A": (0,), "inner-event-B": (0,)}
    return {
        "orientation_mutation": expect_rejection(lambda: check_complex(target, bad_incidence)),
        "fold_orientation_mutation": expect_rejection(
            lambda: check_chain_map(source, target, corrupted_images)),
        "noninteger_chain_map": expect_rejection(
            lambda: check_chain_map(target, target, half_identity)),
        "duplicate_occupancy": expect_rejection(
            lambda: CubicalComplex("duplicate", (square, square))),
        "dimension_mutation": expect_rejection(
            lambda: support_measure((square,), {square: Fraction(1)}, 3)),
        "native_metric_promotion": expect_rejection(
            lambda: CubicalComplex("unlicensed", (square,), "native_physical_cell")),
        "many_to_one_reconstruction": expect_rejection(lambda: unique_preimage(coordinates, (0,))),
        "projected_closure_promotion": expect_rejection(
            lambda: require_closed_identity("inner-event-A", "inner-event-B", (0,), (0,))),
        "refitted_refinement": expect_rejection(
            lambda: validate_disk_refinement(2, 4, disk_tops(2), disk_tops(4)[:-1])),
    }


def build_report():
    spec = json.loads(SPEC.read_text())
    levels = [disk_level(n) for n in spec["disk"]["levels"]]
    for first, second in zip(levels, levels[1:]):
        validate_disk_refinement(first["n"], second["n"],
                                 disk_tops(first["n"]), disk_tops(second["n"]))
    square = CubicalComplex("G1-filled-square", (Cell(((0, 1), (0, 1))),))
    tesseract = CubicalComplex("G2-filled-tesseract", (Cell(((0, 1),)*4),))
    zero_cell = square.tops[0]
    zero = support_measure((zero_cell, zero_cell), {zero_cell: Fraction(0)}, 2)
    comparisons = []
    for terms in spec["pi_reference"]["terms"]:
        comparisons.append({"terms_per_arctangent": terms,
                            **compare_disk_reference(levels[-1], pi_reference_bounds(terms))})
    return {"schema": "aod-m3-cells-geometry-v1", "status": "conditional_verification_executed",
            "spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(),
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "native_higher_cell_status": "not established by this completion",
            "physical_metric_status": "unknown; declared Euclidean and axial report models only",
            "G1": finite_record(square, (1, 1)),
            "G2": finite_record(tesseract, (exact(spec["tesseract"]["edge_length"]),)*4),
            "G3_G4": {"levels": levels, "refinement": "dyadic same-disk inclusion",
                       "shared_q_controls": [shared_coefficient_control(levels[-1], q)
                                             for q in ("2", "3", "355/113", "7/2")],
                       "reference_comparisons": comparisons},
            "G5": {"fold": fold_record(), "anisotropy": anisotropy_record(),
                   "structural_zero": {"measure": str(zero.value), "support": list(zero.support),
                                       "visit_policy": "unsigned union; duplicate visits do not multiply area"}},
            "G6": {"status": "not_opened", "reason": "no sphere estimator/refinement claim selected"},
            "negative_controls": negative_controls()}


def report_bytes(report):
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-data", action="store_true")
    group.add_argument("--write-data", action="store_true")
    args = parser.parse_args()
    result = report_bytes(build_report())
    if args.write_data:
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_bytes(result)
    else:
        require(DATA.read_bytes() == result, "frozen cells/geometry report differs")
    print(json.dumps({"report": str(DATA.relative_to(ROOT)), "sha256": hashlib.sha256(result).hexdigest(),
                      "conditional_geometry": "reproduced", "native_metric": "not_established"}))


if __name__ == "__main__":
    main()
