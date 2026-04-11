# AOD Notebook Style Guide
## Version 2.3 — Cited-row-first / temporal-conversion only
**Maintainer:** P. Reginald  
**Status:** Official style for public notebooks in `notebooks/`

All primary derivation content remains in bip / biz / trit units with exact/default-form rows authoritative:
- trit/bip primitive
- biz derived
- integer ledgers authoritative
- exact rational/logarithmic forms preferred

Notebook language remains on the AOD/AFC line. Exact/default-form rows remain authoritative; converted witnesses follow the cited row when needed.

Where SI reporting is needed, it follows the cited row. Conversion is restricted to:
- duration in **seconds**
- rate in **hertz**
- effective speed as the dimensionless ratio \(\beta\in[0,1]\) with \(c=1\)

---

## 1. Purpose
- Every notebook is executable documentation of the AOD calculus.
- All tests follow the same structure and methodology.
- Cited rows are authoritative.

---

## 2. Package structure
- Main note = compact theorem line
- Supplement A — Worked examples and figure witnesses
- Supplement B — Verification bindings and derived temporal-unit conversions
- Supplement C — Regime tests

---



## 2.5 Notebook provenance block
The first markdown cell of every notebook should carry a package-owned provenance block containing:
- title
- author
- protocol
- package role
- notebook routing
- source-of-truth note/supplement reference
- repo provenance path

This block states the notebook's role in the canonical source tree before any worked content begins.

## 3. Uniform structure for every test
Every test uses this exact structure:

## [Test ID] [Test Title]

**Question**  
[One sentence only.]

**Readout**  
- cited window \(\omega\)
- structural key (tetron:* where applicable)
- frame count / \(T_{\mathrm{eval}}\)
- weighting policy
- shell signature / inputs as needed

**Operator Chain**  
[Short operator chain.]

**Output Row**  
[DataFrame with exact/default-form quantities only.]

**Temporal Conversion Block**  
[Only if needed; convert from cited row into seconds / hertz / \(\beta\) only.]

**Figure Witness**  
[Or “Temporal Conversion Witness” if conversion-only.]

**Hook / Evidence**  
[Reference only to note hooks or checks.]

---

## 4. Cited-row-first rule
- The cited row is always recorded first.
- Verification labels, decimal renderings, and temporal-unit conversions are attached only after the cited row.
- Root notebooks support the main note; supplement-owned notebooks live inside their supplement subpackages.

---

## 5. Temporal conversion rule (verbatim)
**Temporal Conversion Block**  
Cited rows are authoritative.  
When conversion is required, convert only from bip/biz quantities into derived temporal SI forms.  
Duration converts to **seconds**.  
Rate converts to **hertz**.  
Effective speed is reported only as
\[
\beta=\frac{v}{c},\qquad c=1,\qquad 0\le\beta\le1.
\]

---

## 6. Visualization standards
Figures are titled: **Figure Witness — [description]**  
Temporal-conversion figures titled: **Temporal Conversion Witness — [description]**

---

## 7. Code style
- Parameterized reusable functions
- Assertions after every major result
- All tables via `pandas.DataFrame`
- Final cell: `print("ALL AOD TESTS PASSED ✓")`
