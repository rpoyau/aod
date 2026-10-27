# Changelog

## Unreleased

### Source organization and reproducibility

- Separate historical project records from current scientific validation.
- Collect current formula, ownership, source-protection and fixture-provenance contracts under `contracts/scientific/`.
- Validate freshly generated awareness reports without a committed result snapshot.
- Support the full scientific test suite and release packaging from an extracted source archive without Git.
- Preserve manuscript, bibliography, figure, engine, dataset and publication-metadata bytes.
- Keep authoring conventions separate from scientific and publication verification.

The canonical publication version remains the value in `CANONICAL_VERSION.txt`. This source cleanup does not publish a new scientific release.
