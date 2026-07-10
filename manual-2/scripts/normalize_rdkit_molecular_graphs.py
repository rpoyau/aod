#!/usr/bin/env python3
"""Refresh offline RDKit graph descriptor scaffold fixtures.

This v40.02r02 script is offline-safe by default: it writes locator/target
packet fixtures and does not download external databases. Full online
acquisition is intentionally deferred to a later controlled target-normalization
gate.
"""
from __future__ import annotations

from run_fractal_fusion_scales import generate_molecular_target_scaffold


def main() -> int:
    generate_molecular_target_scaffold()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
