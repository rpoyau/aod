"""Regression tests for the proposed publication-field URL deduplication.

This file runs against the adjacent candidate script and reads the repository's
unchanged BibTeX sources. It can also run from tests/ after an approved change.
"""
import importlib.util
from pathlib import Path

import pytest


SUPPORT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "refs.bib").is_file() and (parent / "manual" / "refs.bib").is_file()
)
SPEC = importlib.util.spec_from_file_location(
    "reference_url_deduplication_candidate",
    SUPPORT_ROOT / "scripts" / "sync_zenodo_references.py",
)
formatter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(formatter)
formatter.BIB_FILES = [SOURCE_ROOT / "refs.bib", SOURCE_ROOT / "manual" / "refs.bib"]


@pytest.fixture(scope="module")
def bib_fields():
    fields = {}
    for path in formatter.BIB_FILES:
        for _, key, body in formatter.iter_bib_entries(path.read_text(encoding="utf-8")):
            fields.setdefault(key, formatter.parse_fields(body))
    return fields


@pytest.mark.parametrize("key", [
    "bipm-si-defining-constants", "nist-alpha-inverse", "nist-proton-mass-energy",
    "nist-neutron-mass-energy", "nist-electron-mass-energy", "nist-muon-mass-energy",
    "nist-neutron-greene", "psi-mumass", "pdg-bmeson-2025", "nist-asd",
    "nist-tau-mass-energy", "desy-belle-tau", "nasa-1919-light-bending",
    "zah-solar-redshift", "sparc-database", "nasa-moon-by-numbers",
    "nasa-cassini-division", "atlas-higgs-diphoton-2023",
])
def test_real_web_references_include_their_url_once(bib_fields, key):
    fields = bib_fields[key]
    result = formatter.reference_from_fields(fields)
    assert result.count(fields["url"]) == 1
    assert formatter.latex_to_text(fields["title"]).rstrip(".") in result


def test_nist_query_and_publication_punctuation_are_preserved(bib_fields):
    assert formatter.reference_from_fields(bib_fields["nist-alpha-inverse"]) == (
        "National Institute of Standards and Technology. "
        "CODATA Value: Inverse Fine-Structure Constant. NIST CODATA, "
        "https://physics.nist.gov/cgi-bin/cuu/Value?alphinv, 2022."
    )


def test_publisher_field_also_prevents_an_identical_url_suffix(bib_fields):
    fields = dict(bib_fields["nasa-moon-by-numbers"])
    fields["publisher"] = fields.pop("howpublished")
    assert formatter.reference_from_fields(fields) == (
        "NASA. Moon by the Numbers. NASA Science, "
        "https://science.nasa.gov/moon/by-the-numbers/, n.d."
    )


@pytest.mark.parametrize("suffix", [".json", "/appendix", "?download=1", "#page=2"])
def test_distinct_urls_sharing_a_prefix_are_both_preserved(bib_fields, suffix):
    fields = dict(bib_fields["nist-neutron-greene"])
    publication_url = fields["url"]
    fields["url"] = publication_url + suffix
    result = formatter.reference_from_fields(fields)
    assert f"{publication_url}, 2009." in result
    assert result.endswith(f". {publication_url}{suffix}.")


def test_distinct_query_values_are_both_preserved(bib_fields):
    fields = dict(bib_fields["nist-alpha-inverse"])
    fields["url"] = "https://physics.nist.gov/cgi-bin/cuu/Value?mpc2mev"
    result = formatter.reference_from_fields(fields)
    assert "https://physics.nist.gov/cgi-bin/cuu/Value?alphinv, 2022." in result
    assert result.endswith(". https://physics.nist.gov/cgi-bin/cuu/Value?mpc2mev.")


def test_doi_still_takes_priority_over_the_url_field(bib_fields):
    fields = dict(bib_fields["heisse-proton-mass"])
    assert formatter.reference_from_fields(fields).endswith(
        ". https://doi.org/10.1103/PhysRevLett.119.033001."
    )
    assert fields["url"] not in formatter.reference_from_fields(fields)


def test_doi_priority_keeps_an_existing_publication_url(bib_fields):
    fields = dict(bib_fields["nist-alpha-inverse"])
    fields["doi"] = "10.1103/PhysRevLett.119.033001"
    result = formatter.reference_from_fields(fields)
    assert fields["url"] + ", 2022." in result
    assert result.endswith(". https://doi.org/10.1103/PhysRevLett.119.033001.")


def test_other_punctuation_survives_the_duplicate_removal(bib_fields):
    fields = dict(bib_fields["nist-alpha-inverse"])
    fields["howpublished"] = (
        "NIST CODATA (U.S. edition); values: "
        r"\url{https://physics.nist.gov/cgi-bin/cuu/Value?alphinv}"
    )
    assert formatter.reference_from_fields(fields) == (
        "National Institute of Standards and Technology. "
        "CODATA Value: Inverse Fine-Structure Constant. "
        "NIST CODATA (U.S. edition); values: "
        "https://physics.nist.gov/cgi-bin/cuu/Value?alphinv, 2022."
    )


def test_explicit_references_and_note_fallback_are_preserved(bib_fields):
    explicit = dict(bib_fields["weissteinHypercubeGraph"])
    assert formatter.reference_from_fields(explicit) == (
        "Weisstein, E. W. Hypercube Graph. Wolfram MathWorld. "
        "https://mathworld.wolfram.com/HypercubeGraph.html. Accessed 2026-06-09."
    )
    note = {"note": r"U.S. archive; see \url{https://example.org/v1.2}, pp. 1--3."}
    assert formatter.reference_from_fields(note) == (
        "U.S. archive; see https://example.org/v1.2, pp. 1–3."
    )


def test_canonical_generation_keeps_43_references_and_existing_order(bib_fields):
    references = formatter.generated_references()
    assert len(references) == 43
    # These source positions span both bibliographies and their shared entries.
    for index, key in [
        (0, "afc"), (1, "reginald2025af"), (2, "weissteinHypercubeGraph"),
        (9, "lawlerLimic"), (10, "bipm-si-defining-constants"),
        (11, "nist-alpha-inverse"), (14, "base-cyclotron-relation"),
        (33, "sparc-database"), (37, "nasa-moon-by-numbers"),
        (42, "atlas-higgs-diphoton-2023"),
    ]:
        assert references[index] == formatter.reference_from_fields(bib_fields[key])
