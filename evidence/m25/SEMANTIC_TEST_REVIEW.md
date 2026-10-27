# M2.5 test evidence

New suite: 9 tests; source-contract/heading replacements: 2 existing tests.

Focused run including existing awareness suite: 97 passed (4.85s).

Baseline new-suite run at 0f18cf5da316f27050c3dffd3838a39ccf13fca4: 3 failed, 6 passed, as expected; log /tmp/m25-semantic-baseline.txt. The baseline has no weighted support equivalence.

Mutation of the new weighted conclusion A_0\cap A_+ to A_0 is parsed successfully but rejected by the actual admitted zero-weight counterexample. Negative dwell weights similarly fail the equivalence; native kernel rejects negative weights.

Finite positive checks exhaust 9 + 27 + 81 = 117 exact assignments of 0, 1/2, 2 across two branch channels and 0, 1 or 2 distinct admitted dwell channels. Each fibre event uses the existing fibre_step() API. Atomic kernel checks remain separate.

The operative() spy verifies actual comparison copies remove exactly one source subset while preserving present/closure objects and matched world/law/input. Exact restoration includes provenance. Duplicate-source cancellation is rejected even though each retained record separately validates. H=1 unavailable source becomes operative at H=2 with a later available input.

Reused unchanged tests cover missing/zero/cancelling states, pressure mismatch, passive traces, renamed identities, hidden-cache prohibition, strict later cuts and existing fixture rows.

Source consumer retains Main/Manual ownership checks, adds explicit source subset and factored removal with both outcome states, and tracks harmless S^+_k -> S_k^+ standardization. Heading consumer preserves subsection hierarchy, original semantic anchor, and all four awareness falsification/provenance stages.


## tests/test_active_scientific_sources.py

Old SHA-256: 37d15a97ea79e01c9628d667ed575d4a1f9d588222fc151e7d31cff189b4e6fe

New SHA-256: f97b56b22d38ae7a609e57b6be1eb8aca70b2a6868c12b5223fdf5f0e59be055

```diff

diff --git a/tests/test_active_scientific_sources.py b/tests/test_active_scientific_sources.py
index 9159433..ae4abed 100644
--- a/tests/test_active_scientific_sources.py
+++ b/tests/test_active_scientific_sources.py
@@ -91,11 +91,12 @@ def test_m2_canonical_science_and_manual_fixture_are_rendered():
     fixture='manual/sections/00_awareness_fixtures.tex';assert fixture in uf
     assert uf.index('manual/sections/00_native_closure_wave_temporal_fixtures.tex')<uf.index(fixture)<uf.index('manual/sections/00_dec_ledger.tex')
     equations=a.equations(ROOT)
-    bindings={'eq:awareness-state-factorization':r'S^+_k=(X_k,M^C_k,R_k)',
+    bindings={'eq:awareness-state-factorization':r'S_k^+=(X_k,M^C_k,R_k)',
               'eq:awareness-active':r'\exists t>k',
               'eq:awareness-response':r'J_{k+1}=J_k+\frac{A_k+q_k+g\sum',
               'eq:awareness-causal-difference':r'\frac{g}{p}',
-              'eq:operative-self':r'S_k\setminus R_i',
+              'eq:operative-source-removal':r'R_{k,i}&:=\{R_e\in R_k:i_e=i\}',
+              'eq:operative-self':r'S_k^{+,-i}',
               'eq:action-return-retention':r'r_a=y-u',
               'eq:awareness-carriage':r'R^{\uparrow}',
               'eq:mindfulness-stability':r'J_{k+1}-b='}
@@ -107,6 +108,11 @@ def test_m2_canonical_science_and_manual_fixture_are_rendered():
         other = equations if lab in moved else local
         assert lab not in other
         assert a.normalize_math(formula) in a.normalize_math(owner[lab])
+    removal = a.normalize_math(equations['eq:operative-source-removal'])
+    assert a.normalize_math(r'S_k^{+,-i}&:=(X_k,M^C_k,R_k\setminus R_{k,i})') in removal
+    operative = a.normalize_math(equations['eq:operative-self'])
+    assert a.normalize_math(r'\mathcal U(S_k^+;E)') in operative
+    assert a.normalize_math(r'\mathcal U(S_k^{+,-i};E)') in operative
     assert 'manual:m2-awareness-fixtures' in a.label_map(ROOT,'manual')



```


## tests/test_pr39_format_style.py

Old SHA-256: 830bc95b484e1a37724edaa6ed6e0d4b769d40ddb320c1295047eeffadb688ed

New SHA-256: 95809ffd500415e3b51932713ffa39e784b7bfc945b91d68c70d4efd0ae03055

```diff

diff --git a/tests/test_pr39_format_style.py b/tests/test_pr39_format_style.py
index df59c4e..c855f0b 100644
--- a/tests/test_pr39_format_style.py
+++ b/tests/test_pr39_format_style.py
@@ -126,13 +126,13 @@ def test_afc_citation_variants_are_confined_to_literature_notes():
     assert not any(provenance < match.start() < literature for match in citations)


-def test_historical_role_headings_and_separate_awareness_stages_are_preserved():
+def test_content_headings_keep_historical_anchors_and_separate_awareness_stages():
     appendix = (ROOT / "appendices/A_fractal_address_bip_biz.tex").read_text()
     assert re.search(
         r"\\subsection\{Setup\}\s*\\label\{app:fractal-address:setup\}", appendix
     )
     assert re.search(
-        r"\\subsection\{Statement\(s\)\}\s*\\label\{app:fractal-address:statements\}", appendix
+        r"\\subsection\{Bound bip and biz accessors\}\s*\\label\{app:fractal-address:statements\}", appendix
     )
     awareness = (ROOT / "sections/08_awareness_learning_mindfulness.tex").read_text()
     assert r"\paragraph{Falsification and provenance.}" not in awareness

```

Coordinator follow-up: the final reference-inventory test also adds exactly eq:hinge-saturation, eq:hinge-saturation-weighted, and eq:operative-source-removal, matching the three new Manual references. Final exact old/new bytes and hashes are in BINDING_SUCCESSOR.json. The full final suite includes 8 additional conservation controls, for 559 passing tests.
