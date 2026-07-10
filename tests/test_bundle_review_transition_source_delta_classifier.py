import importlib.util
from pathlib import Path


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, Path(path).resolve())
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_transition_and_complete_validator_share_source_delta_classification():
    materializer = _load('review_materializer_classifier', 'tools/run_bundle_transition.py')
    validator = _load('complete_validator_classifier', 'tools/validate_complete_bundle.py')
    paths = [
        'manual-2/data/dec/dec_report_coordinate_overlay.csv',
        'manual-2/data/foundation/foundation_release_milestone_plan.csv',
        'manual-2/data/molecular/molecular_matter_transition_packets.csv',
        'manual-2/sections/00_dec_report_coordinate_overlay.tex',
        'manual/sections/00_foundation_doctrine_tick_tau_sparc.tex',
        'sections/03_foundation_doctrine_tick_tau_sparc.tex',
        'tools/validate_surface_synchronization.py',
    ]
    for path in paths:
        assert materializer._classify_source_delta_path(path) == validator._classify_source_delta_path(path), path
