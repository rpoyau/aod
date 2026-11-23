"""Alpha Omega Dynamics (AOD) Stage 2 Audited Zero-Float Reference Engine."""
from __future__ import annotations

from manual.engine.numeric import (
    canonical_rational_pair,
    canonical_rational_str,
    exact_isclose,
    format_rational_fixed,
    parse_canonical_rational_pair,
    parse_exact_int,
    parse_printed_rational,
    require,
    require_exact_int,
    round_rational_half_even,
)
from manual.engine.policy import (
    audit_source_tree,
    loads_zero_float,
    reject_json_float,
    require_no_floats,
)
from manual.engine.registry import (
    SECTOR_MAP,
    SECTOR_SPECS,
    SectorSpec,
    get_sector,
    registry_digest,
    verify_data_coverage,
    verify_registry_completeness,
)
from manual.engine.report import build_report, serialize_report
from manual.engine.schema import (
    BASE_COMMIT_BINDING,
    ENGINE_VERSION,
    REPORT_SCHEMA,
    VECTOR_SCHEMA,
    validate_report,
    validate_vector_record,
)
from manual.engine.vectors import verify_all_vectors

__all__ = [
    "BASE_COMMIT_BINDING",
    "ENGINE_VERSION",
    "REPORT_SCHEMA",
    "SECTOR_MAP",
    "SECTOR_SPECS",
    "SectorSpec",
    "VECTOR_SCHEMA",
    "audit_source_tree",
    "build_report",
    "canonical_rational_pair",
    "canonical_rational_str",
    "exact_isclose",
    "format_rational_fixed",
    "get_sector",
    "loads_zero_float",
    "parse_canonical_rational_pair",
    "parse_exact_int",
    "parse_printed_rational",
    "registry_digest",
    "reject_json_float",
    "require",
    "require_exact_int",
    "require_no_floats",
    "round_rational_half_even",
    "serialize_report",
    "validate_report",
    "validate_vector_record",
    "verify_all_vectors",
    "verify_data_coverage",
    "verify_registry_completeness",
]
