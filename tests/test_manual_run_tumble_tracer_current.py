from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def manual_text() -> str:
    return read("manual/sections/06_field_dynamics_applications.tex")


def main_text() -> str:
    chunks = [read("main.tex")]
    chunks.extend(p.read_text(encoding="utf-8") for p in sorted((ROOT / "sections").glob("*.tex")))
    chunks.extend(p.read_text(encoding="utf-8") for p in sorted((ROOT / "appendices").glob("*.tex")))
    return "\n".join(chunks)


def test_run_tumble_section_exists():
    text = manual_text()
    assert r"\label{manual:run-tumble-tracer-current-fixture}" in text
    assert "Run-tumble tracer-current fixture" in text
    assert "G3 time-resolved tracer-current fixture" in text


def test_run_tumble_layer_separation_terms():
    text = manual_text()
    required = [
        r"h_t\in\mathbb Z^4",
        r"\pi_3:\mathbb Z^4\to\mathbb Z^3",
        r"z_t=\pi_3(h_t)",
        r"Q^2_{3D}",
        r"Q^2_4",
        r"m_t\in\{\mathrm{run},\mathrm{tumble}\}",
        "The fourth trace channel remains part of the \\(Q^2_4\\) audit",
        "not \\(Q^D\\) pending-overhang notation",
    ]
    for term in required:
        assert term in text
    assert text.index(r"h_t\in\mathbb Z^4") < text.index(r"\pi_3:\mathbb Z^4\to\mathbb Z^3") < text.index(r"Q^2_{3D}")


def test_forbidden_q4_position_language_absent():
    text = manual_text() + "\n" + main_text()
    forbidden = [
        "Q4 position",
        "Q4 Position",
        "Q_4 position",
        "Q_4 Position",
        "crude 3D",
        "toy 3D simulation",
        "Wiener process",
        "Itô calculus",
        "Ito calculus",
    ]
    for term in forbidden:
        assert term not in text


def test_run_tumble_csv_consistency():
    csv_path = ROOT / "manual" / "data" / "run_tumble" / "run_tumble_trace_20_ticks.csv"
    assert csv_path.exists()
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert len(rows) == 21
    assert rows[0]["t"] == "0"
    prev = [0, 0, 0, 0]
    beta = 5
    for row in rows:
        t = int(row["t"])
        h = [int(row[f"h{i}"]) for i in range(1, 5)]
        z = [int(row[k]) for k in ["x", "y", "z"]]
        if t == 0:
            assert h == [0, 0, 0, 0]
            assert row["mode"] == "init"
        else:
            edge = int(row["edge"][1:])
            sigma = int(row["sigma"])
            expected = prev.copy()
            expected[edge - 1] += sigma
            assert h == expected
            assert row["mode"] in {"run", "tumble"}
        assert z == h[:3]
        q3 = sum(v*v for v in z)
        q4 = sum(v*v for v in h)
        assert int(row["Q3"]) == q3
        assert int(row["Q4"]) == q4
        assert int(row["theta"]) == q3 % beta
        prev = h


def test_run_tumble_phase_and_octant_delta3_conservation():
    data_dir = ROOT / "manual" / "data" / "run_tumble"
    phase = list(csv.DictReader((data_dir / "run_tumble_phase_cycle_delta3.csv").open(encoding="utf-8")))
    octs = list(csv.DictReader((data_dir / "run_tumble_octant_delta3.csv").open(encoding="utf-8")))
    assert len(phase) == 5
    assert len(octs) == 8
    assert sum(int(r["DeltaZ"]) for r in phase) == 0
    assert sum(int(r["DeltaZ"]) for r in octs) == 0
    assert all(int(r["m"]) == abs(int(r["DeltaZ"])) for r in phase + octs)
    assert all(r["beta_a"] == "5" for r in phase)


def test_run_tumble_artifacts_present():
    files = [
        "manual/scripts/aod_run_tumble_3d_trace.py",
        "manual/data/run_tumble/run_tumble_trace_20_ticks.csv",
        "manual/data/run_tumble/run_tumble_phase_cycle_delta3.csv",
        "manual/data/run_tumble/run_tumble_octant_delta3.csv",
        "manual/data/run_tumble/run_tumble_integer_motion_ratios.csv",
        "manual/data/run_tumble/run_tumble_trace_table.tex",
        "manual/figures/run_tumble_trace_3d_projection.png",
    ]
    for rel in files:
        assert (ROOT / rel).exists(), rel
    script = read("manual/scripts/aod_run_tumble_3d_trace.py")
    assert "SCHEDULE" in script
    assert "pi3" in script


def test_appendix_c_cross_reference_and_registry_row():
    app = read("manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex")
    assert r"\secref{manual:run-tumble-tracer-current-fixture}" in app
    reg = read("manual/sections/09_prediction_test_fixture_registry.tex")
    assert "Run-tumble tracer-current fixture" in reg
    assert r"h_t\in\mathbb Z^4" in reg
    assert r"\pi_3(h_t)\in\mathbb Z^3" in reg
    assert "run-tumble trace CSV" in reg


def test_main_note_unchanged_by_run_tumble():
    text = main_text().lower()
    assert "run-tumble" not in text
    assert "run tumble" not in text


def test_run_tumble_registry_class_exact():
    reg = read("manual/sections/09_prediction_test_fixture_registry.tex")
    assert "Run-tumble tracer-current fixture & G3/D0 &" in reg
    assert "G3/D0 audit" not in reg
