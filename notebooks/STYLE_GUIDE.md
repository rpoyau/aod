# AOD Notebook Style Guide
## Version 2.3 — Cited-row-first / temporal-conversion only
**Maintainer:** P. Reginald  
**Status:** Official style for root and manual-owned notebooks

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
- Manual notebooks = active downstream/public notebook layer
- Archived supplement notebooks = source fragments and support material

---



## 2.5 Notebook provenance block
The first markdown cell of every notebook should identify:
- notebook title
- package role
- source of truth = the relevant manual section
- repo provenance path
- historical lineage only if needed for source traceability

## 3. Notebook alignment rules
- The source of truth is the matching manual section, not the notebook file.
- Manual notebook titles and headings should use semantic section names.
- Do not use supplement-era numbering such as E4, C1, E10, or E11D in notebook titles or headings.
- Tables and figures in the notebook should match the corresponding manual section names.

## 4. Cited-row-first rule
- The cited row is always recorded first.
- Verification labels, decimal renderings, and temporal-unit conversions are attached only after the cited row.
- Root notebooks support the main note; manual notebooks are the active downstream notebook layer; archived supplement notebooks remain source fragments only.

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

Manual-owned notebooks should use paths under `manual/notebooks/` and cite the matching manual section as their source of truth. Avoid supplement-era numbering in notebook titles and headings.
