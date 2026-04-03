# AOD Notebook Style Guide
## Version 2.3 — Native-first / temporal-conversion only
**Maintainer:** P. Reginald  
**Status:** Official style for public notebooks in `notebooks/`

All primary derivation content remains 100% native AOD/AFC:
- trit/bip primitive
- biz derived
- integer ledgers authoritative
- exact rational/logarithmic forms preferred

Notebook language remains on the AOD/AFC line.

Temporal conversion is allowed only when explicitly needed, and only after the cited native row. Conversion is restricted to:
- duration in **seconds**
- rate in **hertz**
- effective speed as the dimensionless ratio \(\beta\in[0,1]\) with \(c=1\)

---

## 1. Purpose
- Every notebook is executable documentation of the native AOD calculus.
- All tests follow the same structure and methodology.
- Native rows are authoritative.

---

## 2. Package structure
- Main note = compact native theorem line
- Supplement A — Native worked examples and figure witnesses
- Supplement B — Verification bindings and derived temporal-unit conversions
- Supplement C — Additional native regime tests

---

## 3. Uniform structure for every test
Every test uses this exact structure:

## [Test ID] [Native Test Title]

**Native Question**  
[One sentence only.]

**Native Readout**  
- cited window \(\omega\)
- structural key (tetron:* where applicable)
- frame count / \(T_{\mathrm{eval}}\)
- weighting policy
- shell signature / native inputs as needed

**Native Operator Chain**  
[Short native operator chain.]

**Native Output Row**  
[DataFrame with native quantities only.]

**Temporal Conversion Block**  
[Only if needed; convert from cited native row into seconds / hertz / \(\beta\) only.]

**Native Figure Witness**  
[Or “Temporal Conversion Witness” if conversion-only.]

**Hook / Evidence**  
[Reference only to note hooks or native checks.]

---

## 4. Native-first rule
- The native row is always recorded first.
- Verification labels, decimal renderings, and temporal-unit conversions are attached only after the cited native row.

---

## 5. Temporal conversion rule (verbatim)
**Temporal Conversion Block**  
Native rows are authoritative.  
When conversion is required, convert only from native bip/biz quantities into derived temporal SI forms.  
Duration converts to **seconds**.  
Rate converts to **hertz**.  
Effective speed is reported only as
\[
\beta=\frac{v}{c},\qquad c=1,\qquad 0\le\beta\le1.
\]

---

## 6. Visualization standards
Native figures titled: **Native Figure Witness — [description]**  
Temporal-conversion figures titled: **Temporal Conversion Witness — [description]**

---

## 7. Code style
- Parameterized reusable functions
- Assertions after every major result
- All tables via `pandas.DataFrame`
- Final cell: `print("ALL AOD NATIVE TESTS PASSED ✓")`
