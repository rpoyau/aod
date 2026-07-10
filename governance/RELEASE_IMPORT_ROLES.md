# GitHub Release Import Roles

| Dependency | Binding role | Canonical embedded material |
|---|---|---|
| AF | Authoring and review protocol | Release metadata, source archive, protocol PDF(s), checksums |
| AFC | Procedural calculus basis | Release metadata, source archive, PDF(s), checksums |
| GM | Human-readable style | Release metadata, source archive, PDF(s), checksums |
| AOD | Stable project baseline | Prefer versioned bundle; otherwise coherent source/PDF/manifests release set |

The `latest` endpoint is never written as the resolved identity. AUTHORING resolves it to a candidate-scoped release snapshot when available; otherwise the explicit fallback remains active without claiming latest status.

GM has presentation authority only. AF and AFC have semantic governance roles. AOD is the governed payload and stable-baseline source.
