# Execution Plan: `BND-P3-01` (`P3-relational-time`)

## Scope Check & Spec Discrepancies

- **Write-set completeness (`scope.write_set`)**: No missing files identified across the read inputs. All edits remain strictly inside the five authorized files:
  1. `typst/sections/06_wave_state_relational_time.typ`
  2. `contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json`
  3. `scripts/audit_ontology_compaction.py`
  4. `typst/representation_change_ledger.json`
  5. `typst/lib/main_registry.json`
- **Read-only boundary guard**: Never edit `typst/preamble.typ`, `typst/main.typ`, `contracts/scientific/CANONICAL_BINDINGS.json`, or any file outside `scope.write_set`. If `audit_scientific_sources.py` unexpectedly reports a source-digest mismatch in any contract outside `scope.write_set`, halt and escalate to Role 1 rather than editing out of scope.
- **Verified label & notation resolutions against `typst/sections/06_wave_state_relational_time.typ` (L1–95)**:
  1. **Label name**: `00_bundle.toml` refers to `eq:coupling-state`, whereas L19 defines `<eq:complete-coupling-state>`. Use `#eqref("eq:complete-coupling-state")` (do **not** emit `#eqref("eq:coupling-state")`, which would fail Typst resolution).
  2. **Coupling superscript**: `00_bundle.toml` writes ASCII `S_{I,B,k}^x`; L19 and L28 define `S^(times)_(I,B,k)` and `S^(times)_(lt.eq k)`. Use native Typst `S^(times)_(I,B,k)` and `S^(times)_(I,B,lt.eq k)`.
  3. **Update operator macro**: `00_bundle.toml` writes `mathcal(U)_B`; native Typst at L28 uses `cal(U)_B`. Use `cal(U)_B`.

---

## Execution DAG

```text
[N1] Edit typst/sections/06_wave_state_relational_time.typ (L237-250 only)
       │
       ├──► compute SHA_06 = sha256(06_wave_state_relational_time.typ)
       │      │
       │      ▼
       │    [N2] Update contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json (L9)
       │           │
       │           ├──► compute SHA_M3 = sha256(M3_WAVELET_COMPACTION_BINDINGS.json)
       │           │      │
       │           │      ├──► [N3A] Update scripts/audit_ontology_compaction.py (L26)
       │           │      │
       │           │      └──► [N3B] Update typst/representation_change_ledger.json (L41)
       │           │
       └──► [N3C] Refresh & verify typst/lib/main_registry.json via build_publication.py
                     │
                     ▼
            [N4] Full offline validation gate (N3A, N3B, N3C converged) & hygiene check
```

---

## Step-by-Step Specification

### Node N1 — Surgical Replacement in `typst/sections/06_wave_state_relational_time.typ`

- **Target file**: `typst/sections/06_wave_state_relational_time.typ`
- **Edit boundary**: Replace **only** lines 237–250 (strictly inside L236–253). Lines 1–236 (ending at `#aod-provenance[...]` on L229–233 plus blank lines L234–236) and lines 251–340 (starting with blank lines L251–253 and `== Downstream continuation model <subsec:q4-hamming-ternary-kernel>` on L254) remain byte-for-byte unchanged.
- **Mathematical bindings**:
  - Complete wave state (`eq:complete-wave-state`, L13):
    `S^W_(B,i,k) = (W^(upright("id"))_(B,i), K^(upright("adm"))_i, sigma^C, J, p, partial B, Phi, op("Cad"), epsilon.alt, upright("memory"), upright("capacity"), upright("context"))_k`
  - Companion coupling state (`eq:complete-coupling-state`, L19):
    `S^(times)_(I,B,k) = (E, psi^(upright("bias")), Lambda, Delta Lambda, op("RCD"), rho^D, upright("provenance"))_k`
  - Declared update law and wave trace (`eq:wave-update-trace`, L28):
    `S^W_(k + 1) = cal(U)_B (S^W_(lt.eq k), S^(times)_(lt.eq k), upright("input")_(lt.eq k))`
  - Pair coupling trace (`eq:coupling-trace`, L36):
    `e_s^(times)` with cut coordinate `k_s` and trace `Gamma^(times) = (e_s^(times))_s`
- **Numbering & label discipline**:
  - Preserve exact headings and labels `<subsec:duon-tick-click>` and `<subsec:duon-continuity>`.
  - Wrap every display equation in `#math.equation(block: true, numbering: none, $ ... $)` with **no** `<eq:...>` label so Main numbered equations stay `198` and Main labels stay `455`.
  - Use `#aod-paragraph[Setup.]`, `#aod-paragraph[Derivation.]`, and `#aod-paragraph[Falsification.]` (unlabeled run-in paragraphs, matching L45/L70/L95/L258).
  - Zero unbound variable `t` (`$t$`, `_t`, `t + 1`, `lt.eq t`) anywhere in prose or math.

#### Exact Replacement for Lines 237–250

```typst
=== Tick/click <subsec:duon-tick-click>

#aod-paragraph[Setup.]
Index the tick/click alternation strictly by the integer cut index $k in bb(Z)$
of #eqref("eq:wave-update-trace"), without introducing any external or
continuous background clock parameter. Pair the complete wave state
#eqref("eq:complete-wave-state") and companion coupling state
#eqref("eq:complete-coupling-state") at cut $k$ into the complete cut state
$K_k := (S^W_(B,i,k) , S^(times)_(I,B,k) )$, with scope-$B$ emission map $E_B$,
received returned Duon $Y_k$, coupling bias $beta_k$ (carried by
$psi^(upright("bias"))_k$ in $S^(times)_(I,B,k)$), and committed lead–lag trace
$Delta_(upright("lead/lag"), lt.eq k)$ assembled from $S^(times)_(I,B,lt.eq k)$
and committed pair-event records $e_s^(times)$ ($k_s lt.eq k$) of
#eqref("eq:coupling-trace").

#aod-paragraph[Derivation.]
Specializing the declared update law #eqref("eq:wave-update-trace") on integer
cut transitions $k arrow.r k + 1$ with the cut-$k$ input slot carrying the
received returned Duon $Y_k$, bias $beta_k$, and committed lead–lag trace
$Delta_(upright("lead/lag"), lt.eq k)$ yields the cut-indexed tick/click
recurrence:

#math.equation(block: true, numbering: none, $ K_k := (S^W_(B,i,k) , S^(times)_(I,B,k) ), wide X_k = E_B (K_k ), \ S^W_(B,i,k + 1) = cal(U)_B (S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) , (Y_k , beta_k , Delta_(upright("lead/lag"), lt.eq k) ) ), \ K_(k + 1) := (S^W_(B,i,k + 1) , S^(times)_(I,B,k + 1) ), wide X_(k + 1) = E_B (K_(k + 1) ). $)

A tick at cut $k$ emits the Duon event $X_k = E_B (K_k )$; the click receives
the bound returned Duon $Y_k$ and updates the wave state through $cal(U)_B$ to
$S^W_(B,i,k + 1)$, pairing it with the post-click committed coupling state
$S^(times)_(I,B,k + 1)$ to form
$K_(k + 1) := (S^W_(B,i,k + 1) , S^(times)_(I,B,k + 1) )$ before the next tick
$X_(k + 1)$.

#aod-paragraph[Falsification.]
Any update requiring an external clock coordinate not determined by the integer
cut index $k$, committed prefixes $(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) )$,
and committed pair records $Gamma^(times)$ with $k_s lt.eq k$ violates
#eqref("eq:wave-update-trace"). Likewise, emitting $X_(k + 1)$ before receiving
the bound click return $Y_k$, or reading an uncommitted future record
($k_s > k$) or absent precondition in $S^(times)_(I,B,k)$ as committed,
falsifies the declared tick/click ordering.


=== Markovian and retained-history continuity <subsec:duon-continuity>

#aod-paragraph[Setup.]
At integer cut $k in bb(Z)$, let $Pi_(upright("cut")) (S^W_(B,i,k) )$ denote the
present-cut projection of #eqref("eq:complete-wave-state") onto its present-cut
cycle coordinates (excluding closure memory, retained context, prior prefix cuts
$lt.eq k - 1$, and companion coupling records). Contrast this projection with
the full retained-history state $(S^W_(B,i,k) , S^(times)_(I,B,k) )$ of
#eqref("eq:complete-wave-state") and #eqref("eq:complete-coupling-state") and
its committed prefix $(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) )$ in
#eqref("eq:wave-update-trace") and #eqref("eq:coupling-trace"), which retain
prior return records, lead–lag burden, jitter, shell residue, duration, or SADAR
channel memory.

#aod-paragraph[Derivation.]
A realization exhibits Markovian continuity when next-cut transitions under
$cal(U)_B$ factor entirely through the present-cut projection and present-cut
input via a reduced map $cal(U)_B^(upright("M"))$:

#math.equation(block: true, numbering: none, $ S^W_(B,i,k + 1) = cal(U)_B^(upright("M")) (Pi_(upright("cut")) (S^W_(B,i,k) ) , upright("input")_k ). $)

When prior return records, coupling burden, or retained memory/context enter
$cal(U)_B$ nontrivially, continuation is retained-history over
$(S^W_(B,i,k) , S^(times)_(I,B,k) )$ and its committed prefix. Both regimes carry
wave continuity whenever distinction-information persists across integer cuts
through recurring Duon cycle form.

#aod-paragraph[Falsification.]
Markovian closure at cut $k$ is falsified whenever two admissible committed
histories $(S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) )$ and
$(tilde(S)^W_(B,i,lt.eq k) , tilde(S)^(times)_(I,B,lt.eq k) )$ share equal
present-cut state and identical cut-$k$ input $upright("input")_k$, differ in
retained burden or prior return, and yield distinct next-cut states:

#math.equation(block: true, numbering: none, $ Pi_(upright("cut")) (S^W_(B,i,k) ) = Pi_(upright("cut")) (tilde(S)^W_(B,i,k) ) quad "and" quad S^W_(B,i,k + 1) eq.not tilde(S)^W_(B,i,k + 1) \ "with" quad (S^W_(B,i,lt.eq k) , S^(times)_(I,B,lt.eq k) ) eq.not (tilde(S)^W_(B,i,lt.eq k) , tilde(S)^(times)_(I,B,lt.eq k) ). $)

Any witnessed pair satisfying these conditions refutes Markovian closure and
requires retained-history continuation over $(S^W_(B,i,k) , S^(times)_(I,B,k) )$.
Conversely, failure of recurring Duon cycle form to preserve
distinction-information across cuts falsifies wave continuity under either
regime.
```

---

### Node N2 — Update `contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json`

- Update **only** line 9 (`sources["typst/sections/06_wave_state_relational_time.typ"]`) to `SHA_06`.
- Preserve all other 5 `sources` digests, all 11 `equations`, both `relocated_figures`, all 6 `retained_anchors`, both `new_anchors`, formatting, and trailing newline byte-for-byte.

### Node N3A — Update `scripts/audit_ontology_compaction.py`

- Update **only** line 26 (`CONTRACT_SHA256["M3_WAVELET_COMPACTION_BINDINGS.json"]`) to `SHA_M3`.

### Node N3B — Update `typst/representation_change_ledger.json`

- Update **only** line 41 (`new_sha256` on the `M3_WAVELET_COMPACTION_BINDINGS.json` entry) to `SHA_M3`, leaving `old_sha256` byte-for-byte unchanged.

### Node N3C — Refresh `typst/lib/main_registry.json`

- Run `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub` (to refresh `typst/lib/main_registry.json` if needed), then verify `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub --check-registry` exits `0` with `entry_count == 455`, numbered equations `== 198`, and Manual `mainref_uses == 172`.

### Node N4 — Validation Gate, Policy Checks & Edge-Case Verification

1. `python3 -B scripts/audit_scientific_sources.py .`
2. `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub --check-registry`
3. `python3 -B -m pytest -q tests/test_active_scientific_sources.py tests/test_mathematical_bindings.py` and `python3 -O -B -m pytest -q tests/test_active_scientific_sources.py tests/test_mathematical_bindings.py`
4. Verify diff restricted to `scope.write_set`, L236–253 only in `06_wave_state_relational_time.typ`, zero unbound `t`, clean `git status` (remove `_build/pub` before returning).
