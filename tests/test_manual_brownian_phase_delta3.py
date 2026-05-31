from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def brownian_text():
    return read('manual/sections/06_field_dynamics_applications.tex') + '\n' + read('manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex')


def test_brownian_section_present_and_manual_only():
    sec = read('manual/sections/06_field_dynamics_applications.tex')
    app = read('manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex')
    assert r'\subsection{3D Brownian phase-cycle \texorpdfstring{$\delta_3$}{delta3} fixture}' in sec
    assert r'\section{3D coordinate phase-cycle \texorpdfstring{$\delta_3$}{delta3} fixture specification}' in app
    assert r'\label{manual:app:coordinate-phase-cycle-delta3}' in app
    assert r'\appref{manual:app:coordinate-phase-cycle-delta3}' in sec
    assert 'Brownian' not in app
    assert 'brownian' not in app
    assert 'G3 time-resolved tracer-current fixture' in sec
    assert 'A two-dimensional microscopy slice is a projected tracer-current support class or ablation cut' in sec
    main = read('main.tex') + ''.join(p.read_text() for p in (ROOT/'sections').glob('*.tex'))
    assert 'Brownian' not in main


def test_brownian_integerized_trajectory_and_q_active():
    text = brownian_text()
    assert r'z_i=(X_i,Y_i,Z_i)\in\mathbb Z^3' in text
    assert r'\Delta z_i^{(n)}=z_{i+n}-z_i=(a_i^{(n)},b_i^{(n)},c_i^{(n)})' in text
    assert r'Q_i^{(n)}=(a_i^{(n)})^2+(b_i^{(n)})^2+(c_i^{(n)})^2\in\mathbb Z_{\ge0}' in text
    assert 'not radial-distance fit' not in text
    assert 'Active coordinate: integerized three-dimensional displacement and phase-cycle count data' in text
    exact_chunk = read('manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex')
    forbidden = ['radial distance fit', 'diffusion coefficient fit', r'\sqrt']
    for term in forbidden:
        assert term not in exact_chunk


def test_brownian_phase_and_octant_delta3_forms_present():
    text = brownian_text()
    assert r'\theta_i^{(n)}=Q_i^{(n)}\bmod\beta_a' in text
    assert r'O_\theta^{(n)}=\#\{i:\theta_i^{(n)}=\theta\}' in text
    assert r'\delta_{3,\theta}^{(n)}=\left(\operatorname{sgn}(\Delta_\theta^{\mathbb Z,(n)}),|\Delta_\theta^{\mathbb Z,(n)}|\right)' in text
    assert r'\operatorname{octant}(a_i^{(n)},b_i^{(n)},c_i^{(n)})\in\{0,\ldots,7\}' in text
    assert r'\widehat O_q^{(n)}=\operatorname{IntBalance}(N_n,8)' in text
    assert r'\delta_{3,q}^{(n)}=' in text


def test_brownian_integer_ratios_present():
    text = brownian_text()
    assert r'R_Q^{(n)}=\left(\sum_iQ_i^{(n)}:N_n\right)' in text
    assert r'R_x^{(n)}=\left(\sum_i(a_i^{(n)})^2:\sum_iQ_i^{(n)}\right)' in text
    assert r'R_y^{(n)}=\left(\sum_i(b_i^{(n)})^2:\sum_iQ_i^{(n)}\right)' in text
    assert r'R_z^{(n)}=\left(\sum_i(c_i^{(n)})^2:\sum_iQ_i^{(n)}\right)' in text
    assert r'R_{\mathrm{oct}}^{(n)}=(O_0^{(n)}:O_1^{(n)}:\cdots:O_7^{(n)})' in text


def test_brownian_data_outputs_exact_integer_counts():
    data_dir = ROOT / 'manual/data/brownian'
    assert (data_dir / 'brownian_sample_track.csv').exists()
    assert (data_dir / 'brownian_displacements.csv').exists()
    assert (data_dir / 'displacement_q_counts.csv').exists()
    assert (data_dir / 'phase_cycle_delta3.csv').exists()
    assert (data_dir / 'octant_delta3.csv').exists()
    assert (data_dir / 'integer_motion_ratios.csv').exists()

    disp = list(csv.DictReader((data_dir / 'brownian_displacements.csv').open()))
    assert all(int(r['Q']) == int(r['a'])**2 + int(r['b'])**2 + int(r['c'])**2 for r in disp)
    assert all(int(r['theta']) == int(r['Q']) % 5 for r in disp)

    phase = list(csv.DictReader((data_dir / 'phase_cycle_delta3.csv').open()))
    assert sum(int(r['DeltaZ']) for r in phase) == 0
    assert all(int(r['m']) == abs(int(r['DeltaZ'])) for r in phase)
    assert all(r['beta_a'] == '5' for r in phase)

    octs = list(csv.DictReader((data_dir / 'octant_delta3.csv').open()))
    assert len(octs) == 8
    assert sum(int(r['DeltaZ']) for r in octs) == 0
    assert all(int(r['m']) == abs(int(r['DeltaZ'])) for r in octs)


def test_brownian_figure_and_registry_present():
    assert (ROOT / 'manual/figures/coordinate_phase_delta3_wireframe.png').exists()
    reg = read('manual/sections/09_prediction_test_fixture_registry.tex')
    assert '3D Brownian phase-cycle fixture & G3/D0 & 3D coordinate track fields' in reg
    assert '3D coordinate phase-cycle CSVs (Brownian application aliases), integer-ratio audit, and App.~\\ref{manual:app:coordinate-phase-cycle-delta3}' in reg


def test_brownian_script_target_and_continuous_summary_quarantine():
    script = read('manual/scripts/aod_brownian_3d_phase_delta3.py')
    assert 'Q=a^2+b^2+c^2' in script
    assert 'phase residues Q mod beta_a' in script
    sec = read('manual/sections/06_field_dynamics_applications.tex')
    app = read('manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex')
    assert 'Continuous summaries belong after the exact fixture as presentation or external maps.' in sec
    assert 'These Brownian application artifacts are aliases of the generic 3D coordinate phase-cycle fixture' in sec
    assert 'Continuous-motion summaries are downstream presentation maps and do not enter the exact fixture.' in app
    assert 'continuous summaries only after exact fixture' in script
