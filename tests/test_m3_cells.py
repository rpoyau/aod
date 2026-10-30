"""Independent finite geometry, chain algebra and hostile M3 controls."""
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m3_cells", ROOT / "manual/scripts/aod_cell_measures.py")
cells = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cells
SPEC.loader.exec_module(cells)


def square():
    return cells.CubicalComplex("square", (cells.Cell(((0, 1), (0, 1))),))


def test_literal_square_oracle_and_oriented_boundary():
    model = square()
    # Literal independent oracle: four vertices, four edges, one interior.
    expected = {
        "[0,0]x[0,0]", "[0,0]x[1,1]", "[1,1]x[0,0]", "[1,1]x[1,1]",
        "[0,1]x[0,0]", "[0,1]x[1,1]", "[0,0]x[0,1]", "[1,1]x[0,1]",
        "[0,1]x[0,1]",
    }
    assert {c.identity for c in model.cells} == expected
    skin = {c.identity: v for c, v in cells.boundary(model.top_chain).items()}
    assert skin == {"[0,0]x[0,1]": -1, "[1,1]x[0,1]": 1,
                    "[0,1]x[0,0]": 1, "[0,1]x[1,1]": -1}
    assert cells.check_complex(model)


def test_tesseract_enumeration_dimensions_and_exact_weights():
    model = cells.CubicalComplex("tesseract", (cells.Cell(((0, 1),)*4),))
    assert [sum(c.dimension == d for c in model.cells) for d in range(5)] == [16, 32, 24, 8, 1]
    assert cells.check_complex(model)
    for length in (Fraction(1), Fraction(3, 2), Fraction(7, 3)):
        volume, surface = cells.measures(model, (length,)*4)
        assert (volume.value, surface.value) == (length**4, 8*length**3)
        assert (volume.dimension, surface.dimension) == (4, 3)
        assert (volume.unit, surface.unit) == ("u^4", "u^3")


def test_boundary_orientation_corruption_and_face_omission_fail():
    model = square()
    edge = cells.Cell(((0, 1), (0, 0)))

    def corrupt(cell):
        result = cells.boundary_cell(cell)
        if cell == edge:
            result[min(result)] *= -1
        return result

    def omit(cell):
        result = cells.boundary_cell(cell)
        if cell == model.tops[0]:
            result.pop(edge)
        return result

    for incidence in (corrupt, omit):
        with pytest.raises(cells.CellError, match="boundary squared"):
            cells.check_complex(model, incidence)


def test_boundary_independence_neighbor_oracle_survives_incidence_mutation(monkeypatch):
    model = square()
    before = cells.exposed_faces_by_occupancy(model)
    monkeypatch.setattr(cells, "boundary", lambda chain: {})
    assert cells.exposed_faces_by_occupancy(model) == before
    with pytest.raises(cells.CellError, match="independent boundary disagreement"):
        cells.measures(model, (1, 1))


def test_interior_measure_independent_of_boundary_and_radius(monkeypatch):
    model = square()
    weights = cells.metric_weights(model.cells, (2, 3))
    def fail(*args, **kwargs):
        raise RuntimeError("boundary/radius must not be used")
    monkeypatch.setattr(cells, "boundary", fail)
    monkeypatch.setattr(cells, "boundary_cell", fail)
    monkeypatch.setattr(cells, "radius_from_vertices", fail)
    assert cells.support_measure(model.tops, weights, 2).value == 6


def test_duplicate_visits_structural_zero_and_signed_chain_are_distinct():
    cell = square().tops[0]
    repeated = cells.support_measure((cell, cell), {cell: Fraction(2)}, 2)
    zero = cells.support_measure((cell,), {cell: Fraction(0)}, 2)
    assert repeated.value == 2
    assert zero.value == 0 and zero.support == (cell.identity,)
    assert cells.clean({cell: Fraction(0)}) == {}
    with pytest.raises(cells.CellError, match="duplicate occupied support"):
        cells.CubicalComplex("duplicate", (cell, cell))


def test_shared_face_cancellation_preserves_interior_occupancy():
    source, _, _ = cells.reflected_two_square_fold()
    shared = cells.Cell(((1, 1), (0, 1)))
    assert shared in source.cells
    assert shared not in cells.boundary(source.top_chain)
    volume, skin = cells.measures(source, (1, 1))
    assert volume.value == 2 and skin.value == 6
    assert len(volume.support) == 2
    assert shared not in cells.exposed_faces_by_occupancy(source)


@pytest.mark.parametrize("dimension", [1, 3, 4])
def test_wrong_measure_dimension_rejects(dimension):
    cell = square().tops[0]
    with pytest.raises(cells.CellError, match="dimension mismatch"):
        cells.support_measure((cell,), {cell: Fraction(1)}, dimension)


def test_bad_metric_weights_and_native_promotion_reject():
    with pytest.raises(cells.CellError, match="exact rational"):
        cells.metric_weights(square().cells, (1.0, 1))
    with pytest.raises(cells.CellError, match="positive"):
        cells.metric_weights(square().cells, (0, 1))
    with pytest.raises(cells.CellError, match="ambient dimension"):
        cells.metric_weights(square().cells, (1, 1, 1))
    with pytest.raises(cells.CellError, match="native metric promotion"):
        cells.CubicalComplex("graph-promoted", square().tops, "native_physical_cell")


def test_tesseract_wrong_metric_changes_both_expected_reports():
    model = cells.CubicalComplex("tesseract", (cells.Cell(((0, 1),)*4),))
    volume, skin = cells.measures(model, (Fraction(3, 2),)*3 + (Fraction(2),))
    assert volume.value != Fraction(81, 16)
    assert skin.value != 27


def test_fold_commutation_retention_and_nonpreserved_measure():
    source, target, images = cells.reflected_two_square_fold()
    assert cells.check_chain_map(source, target, images)
    assert cells.apply_map(source.top_chain, images) == {}
    # Cancellation of the oriented top image cannot erase occupied preimages.
    assert cells.measures(source, (1, 1))[0].value == 2
    assert cells.measures(target, (1, 1))[0].value == 1
    record = cells.fold_record()
    assert len(record["retained_inner_to_outer"]) == len(source.cells)
    assert {row["inner_cell_id"] for row in record["retained_inner_to_outer"]} == {
        c.identity for c in source.cells}
    assert all(row["inner_scope"] == source.scope for row in record["retained_inner_to_outer"])
    assert all(row["construction_lineages"] for row in record["retained_inner_to_outer"])
    assert images[source.tops[1]] == {target.tops[0]: -1}
    assert cells.boundary(images[source.tops[1]]) == {
        c: -v for c, v in cells.boundary_cell(target.tops[0]).items()}


def test_fold_mutations_and_projection_identity_control():
    source, target, images = cells.reflected_two_square_fold()
    changed = dict(images)
    changed[source.tops[1]] = {target.tops[0]: Fraction(1)}
    with pytest.raises(cells.CellError, match="commute"):
        cells.check_chain_map(source, target, changed)
    del changed[source.tops[0]]
    with pytest.raises(cells.CellError, match="every source identity"):
        cells.check_chain_map(source, target, changed)
    with pytest.raises(cells.CellError, match="unique reconstruction"):
        cells.unique_preimage({"event-A": (0,), "event-B": (0,)}, (0,))
    with pytest.raises(cells.CellError, match="native closure"):
        cells.require_closed_identity("event-A", "event-B", (0,), (0,))


def test_rational_scaling_does_not_define_an_integer_chain_map():
    model = square()
    half_identity = {c: {c: Fraction(1, 2)} for c in model.cells}
    with pytest.raises(cells.CellError, match="integer chain-map coefficients"):
        cells.check_chain_map(model, model, half_identity)
    def fractional_boundary(cell):
        return {c: v/2 for c, v in cells.boundary_cell(cell).items()}
    with pytest.raises(cells.CellError, match="integer incidence coefficients"):
        cells.check_complex(model, fractional_boundary)


@pytest.mark.parametrize("n", [1, 2, 4, 8, 16, 32])
def test_disk_literal_cells_and_independent_columns(n):
    result = cells.disk_level(n)
    assert result["outer_support_count"] == cells.independent_disk_count(n, "outer")
    assert result["inner_support_count"] == cells.independent_disk_count(n, "inner")
    assert Fraction(result["C_axial"]) == 8
    assert Fraction(result["r_axis_extent"]) == 1
    assert Fraction(result["area_enclosure_width"]) <= Fraction(8, n)
    assert Fraction(result["certified_area_gap_bound"]) == Fraction(8, n)


def test_same_disk_refinement_enclosures_and_fixed_staircase_mismatch():
    levels = [cells.disk_level(n) for n in (1, 2, 4, 8, 16, 32)]
    for a, b in zip(levels, levels[1:]):
        assert cells.validate_disk_refinement(a["n"], b["n"],
                                             cells.disk_tops(a["n"]), cells.disk_tops(b["n"]))
        assert Fraction(a["A_inner"]) <= Fraction(b["A_inner"])
        assert Fraction(b["A_outer"]) <= Fraction(a["A_outer"])
        assert Fraction(b["area_enclosure_width"]) < Fraction(a["area_enclosure_width"])
    lo, hi = cells.pi_reference_bounds(16)
    for level in levels:
        assert Fraction(level["A_inner"]) <= lo < hi <= Fraction(level["A_outer"])
    assert Fraction(levels[-1]["A_outer"]) == Fraction(833, 256)
    assert Fraction(levels[-1]["A_inner"]) == Fraction(385, 128)
    assert Fraction(levels[-1]["Cr_minus_2A"]) == Fraction(191, 128)


def test_refitted_estimator_or_object_rejects_refinement_claim():
    with pytest.raises(cells.CellError, match="changed fine object or estimator"):
        cells.validate_disk_refinement(2, 4, cells.disk_tops(2), cells.disk_tops(4)[:-1])
    with pytest.raises(cells.CellError, match="dyadic"):
        cells.validate_disk_refinement(2, 8, cells.disk_tops(2), cells.disk_tops(8))


def test_shared_coefficient_mutations_pass_identity_but_fail_independent_geometry():
    level = cells.disk_level(16)
    for q in ("2", "3", "355/113", "7/2", "4"):
        control = cells.shared_coefficient_control(level, q)
        assert Fraction(control["Cr_minus_2A"]) == 0
        assert not control["agrees_with_independent_measures"]
        assert not control["determines_q"]


def test_pi_precision_is_downstream_and_cannot_fix_metric_mismatch(monkeypatch):
    frozen = cells.disk_level(16)
    before = cells.digest(frozen)
    widths = []
    for terms in (4, 8, 16):
        bounds = cells.pi_reference_bounds(terms)
        comparison = cells.compare_disk_reference(frozen, bounds)
        widths.append(bounds[1]-bounds[0])
        assert Fraction(comparison["C_minus_2pi_r_lower"]) > 1
        assert cells.digest(frozen) == before
    assert widths[2] < widths[1] < widths[0]
    def forbidden(*args):
        raise RuntimeError("reference leaked upstream")
    monkeypatch.setattr(cells, "pi_reference_bounds", forbidden)
    monkeypatch.setattr(cells, "compare_disk_reference", forbidden)
    assert cells.disk_level(16) == frozen


def test_pi_enclosure_contains_independent_high_precision_reference():
    from sympy import N, pi
    independent = Fraction(str(N(pi, 100)))
    for terms in (4, 8, 16):
        lower, upper = cells.pi_reference_bounds(terms)
        assert lower < independent < upper


def test_anisotropic_mutation_and_joint_relabelling():
    result = cells.anisotropy_record()
    assert result["horizontal_boundary"] == "10"
    assert result["swapped_cells_only_boundary"] == "8"
    assert result["swapped_cells_and_metric_boundary"] == "10"
    assert result["isotropic_claim_rejected"]
    assert result["joint_relabelling_invariant"]


def test_frozen_report_reproduces_and_negative_controls_execute():
    report = cells.build_report()
    assert cells.report_bytes(report) == cells.DATA.read_bytes()
    assert len(report["negative_controls"]) == 9
    assert all(report["negative_controls"].values())
    assert report["native_higher_cell_status"] == "not established by this completion"
    assert report["G6"]["status"] == "not_opened"


def test_optimized_checker_keeps_runtime_guards():
    result = subprocess.run([sys.executable, "-O", str(ROOT / "manual/scripts/aod_cell_measures.py"),
                             "--check-data"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["conditional_geometry"] == "reproduced"
