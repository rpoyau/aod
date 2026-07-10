#!/usr/bin/env python3
"""Build the Manual-II native rest-cycle relational atlas ledgers.

This generator is deterministic. It materializes type cards and atlas rows only;
it does not read target values and does not compute residuals or scores.
"""
from __future__ import annotations

# This file documents the deterministic source of the released CSVs. The current
# release stores the generated ledgers under manual-2/data/rest_cycle/.

if __name__ == "__main__":
    print("native rest-cycle relational atlas ledgers are release-materialized; target join remains closed")
