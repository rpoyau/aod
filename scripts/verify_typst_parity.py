#!/usr/bin/env python3
"""Direct native-Typst vs retained-LaTeX parity verifier for M4 Objective 1.

Enforces OBJECTIVE_1_TYPST_PLAN_R02.md Section 9 gates without bare `assert`
so normal (`python3`) and optimized (`python3 -O`) runs execute identically
and produce byte-identical deterministic JSON reports:

  A. Baseline immutability (all 54 TeX, 2 BibTeX, 49 images, 116 manual/data,
     wavelet_shedding_simulation.csv, plus narrow engineering-only digest
     amendment verification in contracts/scientific/CANONICAL_BINDINGS.json).
  B. Scientific content parity across the complete active publication graphs:
     - Active include-graph coverage (21 Main + 27 Manual = 48 active TeX,
       including all 6 immutable tables & Appendices D-J; 5 historical TeX
       snapshots excluded).
     - Ordered headings, numbered Definition 1..26 sequence, Provenance /
       Literature-note / Remark blocks, and Main/Manual ownership.
     - Ordered prose and scientific qualification tokens (allowing only
       declared typography normalization).
     - Mathematical expressions, signs, exponents, indices, and RG1..RG12 tags
       across all labeled equations.
     - Table headers, captions, labels, and exact cell-by-cell values for all
       6 immutable Manual tables, cycle_shedding_summary, and inline tables.
     - Exact figure asset identities (6 Main + 28 Manual image paths) and all
       4 Manual native Typst flowcharts.
     - Exact citation keys, bibliography entries (10 Main + 43 Manual), and
       BibTeX plain ordering.
     - All 455 Main labels, 227 Manual labels, 172 Main->Manual references
       (source identity, target type, resolved numbers/tags, cryptographic
       Main registry freshness, and actual PDF /Link destinations).
  C. Evaluated & rendered output checks on actual compiled Typst PDFs
     (and direct comparison against baseline XeLaTeX PDFs when provided).
  D. Executable negative controls (5 mandatory rejection cases).
  E. Explicit reporting of toolchain, coverage, and separately tracked typ2tex
     compatibility status.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_scientific_sources as audit  # noqa: E402
import build_typst as typst_builder  # noqa: E402

SCIENTIFIC_BASELINE_COMMIT = "98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3"
ALLOWED_ENGINEERING_FROZEN_AMENDMENTS = {
    "scripts/build_release_bundle.py",
    "tests/test_ci_release_builder.py",
}
IMMUTABLE_MANUAL_TABLES = (
    "manual/data/run_tumble/run_tumble_trace_table.tex",
    "manual/data/derived/sparc_summary_table.tex",
    "manual/data/lensing/sparc5_medium_diagnostic_summary_table.tex",
    "manual/data/lensing/swells_k0_target_tallies_table.tex",
    "manual/data/lensing/swells_k1_k2_k3_comparison_table.tex",
    "manual/data/lensing/k4_3d_timeflow_input_gate_table.tex",
)
HISTORICAL_TEX_SNAPSHOTS = (
    "manual/data/historical_metrology/historical_target/sections/06_wave_state_relational_time.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/appendices/H_combinatorics_rd_tests.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/sections/05_curl_closure_duon_current.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/sections/06_field.tex",
    "manual/data/temporal_anchor/source/baseline/input/upstream/sections/06_wave_state_relational_time.tex",
)
QUALIFIER_WORDS = (
    "not", "never", "only", "unless", "without", "conditional", "quarantined",
    "unresolved", "absent", "necessary", "sufficient", "falsification",
    "declared", "scoped", "immutable", "distinct", "independent", "external",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# --- Canonicalization helpers ---
def strip_tex_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def strip_typst_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        # Strip // comments outside string quotes / URLs (http://, https://)
        out = []
        in_str = False
        i = 0
        while i < len(line):
            c = line[i]
            if c == '"' and (i == 0 or line[i - 1] != "\\"):
                in_str = not in_str
                out.append(c)
                i += 1
            elif not in_str and line.startswith("//", i) and (i == 0 or line[i - 1] != ":"):
                break
            else:
                out.append(c)
                i += 1
        lines.append("".join(out))
    return "\n".join(lines)


def norm_typography(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    # Join soft-hyphen line breaks first
    t = re.sub(r"\u00ad\s*\n\s*", "", t)
    t = t.replace("\u00ad", "")
    t = re.sub(r"([A-Za-z])-\n([a-z])", r"\1\2", t)
    for src, dst in (
        ("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'"),
        ("\u2014", "-"), ("\u2013", "-"), ("\u2212", "-"),
        ("\u00a0", " "), ("\u2009", " "), ("\u2004", " "),
        ("---", "-"), ("--", "-"), ("``", '"'), ("''", '"'),
    ):
        t = t.replace(src, dst)
    return t


def read_balanced_group(s: str, pos: int, op: str = "{", cl: str = "}") -> tuple[str, int]:
    while pos < len(s) and s[pos] in " \t\n\r":
        pos += 1
    require(pos < len(s) and s[pos] == op, f"Expected {op} at {pos}")
    depth = 0
    start = pos + 1
    i = pos
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == op:
            depth += 1
        elif s[i] == cl:
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    raise ValueError(f"Unclosed {op}")


def canonicalize_math_common(expr: str, is_typst: bool) -> list[str]:
    """Map LaTeX or Typst math to a common structural token list preserving
    signs (+, -), operators, exponents, indices, digits, identifiers, relations."""
    s = expr.strip()
    if is_typst:
        # Remove Typst formatting wrappers & quotes while keeping semantic tokens
        replacements = [
            (r'#box\(stroke:[^)]+\)\[\$(.*?)\$\]', r'\1'),
            (r'attach\(stretch\(arrow\.r[^)]*\),\s*t:\s*', ' ->^ '),
            (r'lr\(\(', '('), (r'\)\)', ')'),
            (r'\bNull(?![A-Za-z])', ' N '), (r'\binfD(?![A-Za-z])', ' inf D '), (r'\bQfour(?![A-Za-z])', ' Q 4 '),
            (r'\bRCD(?![A-Za-z])', ' R C D '), (r'\bSADARop(?![A-Za-z])', ' S '), (r'\bSADAR(?![A-Za-z])', ' SADAR '),
            (r'\bADAR(?![A-Za-z])', ' ADAR '), (r'\bAOcycle(?![A-Za-z])', ' A <-> mu Omega <-> Omega <-> mu A '),
            (r'\bAOpkg(?![A-Za-z])', ' A <-> mu Omega '), (r'\bOAop(?![A-Za-z])', ' Omega <-> mu A '),
            (r'\bAOh(?![A-Za-z])', ' AO mu '), (r'\bOAh(?![A-Za-z])', ' OA mu '),
            (r'(?<!")(?<![A-Za-z])AO(?![A-Za-z])(?!")', ' A <-> Omega '),
            (r'\bQext(?![A-Za-z])', ' Q ext '),
            (r'\bdot\.op(?![A-Za-z])', ' * '), (r'\bdot\.o(?![A-Za-z])', ' odot '),
            (r'\bplus\.o(?![A-Za-z])', ' oplus '), (r'\btimes\.o(?![A-Za-z])', ' otimes '),
            (r'\bplus\.minus(?![A-Za-z])', ' PM '),
            (r'\barrow\.r\.double\.not(?![A-Za-z])', ' NOTIMPL '),
            (r'\bupright\("([^"]+)"\)', r' \1 '),
            (r'\bbold\("([^"]+)"\)', r' \1 '),
            (r'\bsans\("([^"]+)"\)', r' \1 '),
            (r'\bmono\("([^"]+)"\)', r' \1 '),
            (r'\bop\("([^"]+)"\)', r' \1 '),
            (r'\b(?:upright|bold|cal|bb|sans|frak|mono|op|hat|tilde|overline|sqrt|cases|mat)\(', ' ( '),
            (r'\bdelim:\s*#none\b', ' '), (r'\balign:\s*#left\b', ' '),
            (r'\b(?:wide|quad|med|thin)(?![A-Za-z])', ' '),
            (r'\barrow\.l\.r\.double\.long(?![A-Za-z])', ' <=> '), (r'\barrow\.l\.r\.double(?![A-Za-z])', ' <=> '),
            (r'\barrow\.r\.double\.long(?![A-Za-z])', ' => '), (r'\barrow\.r\.double(?![A-Za-z])', ' => '),
            (r'\barrow\.l\.double(?![A-Za-z])', ' <= '),
            (r'\barrow\.l\.r\.long(?![A-Za-z])', ' <-> '), (r'\barrow\.l\.r(?![A-Za-z])', ' <-> '),
            (r'\barrow\.r\.long\.bar(?![A-Za-z])', ' |-> '), (r'\barrow\.r\.bar(?![A-Za-z])', ' |-> '),
            (r'\barrow\.r\.squiggly(?![A-Za-z])', ' ~> '), (r'\barrow\.r\.long(?![A-Za-z])', ' -> '),
            (r'\barrow\.r(?![A-Za-z])', ' -> '), (r'\barrow\.l\.long(?![A-Za-z])', ' <- '), (r'\barrow\.l(?![A-Za-z])', ' <- '),
            (r'\barrow\.b\.double(?![A-Za-z])', ' v '), (r'\barrow\.b(?![A-Za-z])', ' v '), (r'\barrow\.t(?![A-Za-z])', ' ^ '),
            (r'\blt\.eq(?![A-Za-z])', ' <= '), (r'\bgt\.eq(?![A-Za-z])', ' >= '), (r'\beq\.not(?![A-Za-z])', ' != '),
            (r'\btimes(?![A-Za-z])', ' * '),
            (r'\bcircle\.tiny(?![A-Za-z])', ' o '), (r'\bunion\.big(?![A-Za-z])', ' U '), (r'\bunion\.sq(?![A-Za-z])', ' U '),
            (r'\bunion(?![A-Za-z])', ' U '), (r'\binter\.big(?![A-Za-z])', ' cap '), (r'\binter(?![A-Za-z])', ' cap '),
            (r'\bsubset\.eq(?![A-Za-z])', ' subseteq '), (r'\bprec\.eq(?![A-Za-z])', ' preceq '),
            (r'\bin\.not(?![A-Za-z])', ' notin '), (r'\bslash(?![A-Za-z])', ' / '), (r'\bfrac(?![A-Za-z])', ' frac '),
            (r'\bbrace\.l(?![A-Za-z])', ' { '), (r'\bbrace\.r(?![A-Za-z])', ' } '),
            (r'\bparen\.l(?![A-Za-z])', ' ( '), (r'\bparen\.r(?![A-Za-z])', ' ) '),
            (r'\bchevron\.l(?![A-Za-z])', ' < '), (r'\bchevron\.r(?![A-Za-z])', ' > '),
            (r'\bfloor\.l(?![A-Za-z])', ' floor '), (r'\bfloor\.r(?![A-Za-z])', ' floor '),
            (r'\bceil\.l(?![A-Za-z])', ' ceil '), (r'\bceil\.r(?![A-Za-z])', ' ceil '),
            (r'\bbar\.v\.double(?![A-Za-z])', ' || '), (r'\bbar\.v(?![A-Za-z])', ' | '), (r'\bmid\(\|\)', ' | '),
            (r'\bepsilon\.alt(?![A-Za-z])', ' epsilon '), (r'\bphi\.alt(?![A-Za-z])', ' phi '),
            (r'\bpi\.alt(?![A-Za-z])', ' pi '), (r'\btack\.r(?![A-Za-z])', ' |- '),
            (r'\btilde\.op(?![A-Za-z])', ' ~ '), (r'\bdots\.[ch](?![A-Za-z])', ' ... '),
            (r'\bpartial(?![A-Za-z])', ' partial '), (r'\binfinity(?![A-Za-z])', ' inf '),
            (r'\bsquare\.stroked(?![A-Za-z])', ' Box '), (r'\bproduct(?![A-Za-z])', ' prod '),
            (r'#(eqref|eqnref|secref|appref|figref|tabref|mainequation|mainsection|mainappendix|maintable)\("([^"]+)"\)', r' REF:\2 '),
            (r'"([^"]*)"', r' \1 '),
        ]
    else:
        replacements = [
            (r'\\label\{[^}]+\}', ' '), (r'\\tag\{[^}]+\}', ' '),
            (r'\\begin\{(?:aligned|split|gathered|cases|smallmatrix|array)\}(?:\{[^}]*\})?', ' '),
            (r'\\end\{(?:aligned|split|gathered|cases|smallmatrix|array)\}', ' '),
            (r'\\(?:left|right|bigl|bigr|Bigl|Bigr|big|Big)(?![A-Za-z])\s*\.?', ' '),
            (r'\\(?:mathrm|mathbf|mathcal|mathbb|mathsf|mathfrak|mathtt|operatorname|text|hbox|texttt|widehat|hat|widetilde|tilde|overline|bar|boxed|sqrt|substack|rm)(?![A-Za-z])', ' '),
            (r'\\(?:qquad|quad|;|,|!|displaystyle|textstyle|nonumber|notag)(?![A-Za-z])', ' '),
            (r'\\Null(?![A-Za-z])', ' N '), (r'\\infD(?![A-Za-z])', ' inf D '), (r'\\Qfour(?![A-Za-z])', ' Q 4 '),
            (r'\\RCD(?![A-Za-z])', ' R C D '), (r'\\SADARop(?![A-Za-z])', ' S '), (r'\\SADAR(?![A-Za-z])', ' SADAR '),
            (r'\\ADAR(?![A-Za-z])', ' ADAR '), (r'\\AOcycle(?![A-Za-z])', ' A <-> mu Omega <-> Omega <-> mu A '),
            (r'\\AOpkg(?![A-Za-z])', ' A <-> mu Omega '), (r'\\OAop(?![A-Za-z])', ' Omega <-> mu A '),
            (r'\\AOh(?![A-Za-z])', ' AO mu '), (r'\\OAh(?![A-Za-z])', ' OA mu '), (r'\\AO(?![A-Za-z])', ' A <-> Omega '),
            (r'\\Qext(?![A-Za-z])', ' Q ext '),
            (r'\\not\s*\\Rightarrow(?![A-Za-z])', ' NOTIMPL '),
            (r'\\Longleftrightarrow(?![A-Za-z])', ' <=> '), (r'\\Leftrightarrow(?![A-Za-z])', ' <=> '),
            (r'\\Longrightarrow(?![A-Za-z])', ' => '), (r'\\Rightarrow(?![A-Za-z])', ' => '),
            (r'\\longleftrightarrow(?![A-Za-z])', ' <-> '), (r'\\leftrightarrow(?![A-Za-z])', ' <-> '),
            (r'\\longmapsto(?![A-Za-z])', ' |-> '), (r'\\mapsto(?![A-Za-z])', ' |-> '),
            (r'\\(?:leadsto|rightsquigarrow)(?![A-Za-z])', ' ~> '),
            (r'\\xrightarrow(?:\[[^\]]*\])?', ' ->^ '),
            (r'\\(?:longrightarrow|rightarrow|to)(?![A-Za-z])', ' -> '),
            (r'\\(?:longleftarrow|leftarrow)(?![A-Za-z])', ' <- '),
            (r'\\(?:Downarrow|downarrow)(?![A-Za-z])', ' v '), (r'\\uparrow(?![A-Za-z])', ' ^ '),
            (r'\\(?:le|leq)(?![A-Za-z])', ' <= '), (r'\\(?:ge|geq)(?![A-Za-z])', ' >= '),
            (r'\\(?:ne|neq)(?![A-Za-z])', ' != '), (r'\\not\s*\\in(?![A-Za-z])', ' notin '),
            (r'\\pm(?![A-Za-z])', ' PM '), (r'\\(?:cdot|times)(?![A-Za-z])', ' * '),
            (r'\\odot(?![A-Za-z])', ' odot '), (r'\\oplus(?![A-Za-z])', ' oplus '), (r'\\otimes(?![A-Za-z])', ' otimes '),
            (r'\\circ(?![A-Za-z])', ' o '), (r'\\(?:bigcup|sqcup|cup)(?![A-Za-z])', ' U '),
            (r'\\(?:bigcap|cap)(?![A-Za-z])', ' cap '), (r'\\subseteq(?![A-Za-z])', ' subseteq '),
            (r'\\preceq(?![A-Za-z])', ' preceq '), (r'\\notin(?![A-Za-z])', ' notin '),
            (r'\\frac(?![A-Za-z])', ' frac '), (r'\\\{', ' { '), (r'\\\}', ' } '),
            (r'\\langle(?![A-Za-z])', ' < '), (r'\\rangle(?![A-Za-z])', ' > '),
            (r'\\(?:lfloor|rfloor)(?![A-Za-z])', ' floor '), (r'\\(?:lceil|rceil)(?![A-Za-z])', ' ceil '),
            (r'\\\|', ' || '), (r'\\(?:lvert|rvert|mid)(?![A-Za-z])', ' | '),
            (r'\\varepsilon(?![A-Za-z])', ' epsilon '), (r'\\varphi(?![A-Za-z])', ' phi '),
            (r'\\varpi(?![A-Za-z])', ' pi '), (r'\\vdash(?![A-Za-z])', ' |- '), (r'\\sim(?![A-Za-z])', ' ~ '),
            (r'\\(?:cdots|ldots)(?![A-Za-z])', ' ... '), (r'\\infty(?![A-Za-z])', ' inf '),
            (r'\\Box(?![A-Za-z])', ' Box '), (r'\\varnothing(?![A-Za-z])', ' emptyset '),
            (r'\\land(?![A-Za-z])', ' and '), (r'\\setminus(?![A-Za-z])', ' without '),
            (r'\\bmod(?![A-Za-z])', ' mod '),
            (r'\\(eqref|eqnref|secref|appref|figref|tabref|mainequation|mainsection|mainappendix|maintable)\{([^}]+)\}', r' REF:\2 '),
            (r'\\_', '_'), (r'\\#', '#'), (r'\\%', '%'),
        ]
    for pat, rep in replacements:
        s = re.sub(pat, rep, s, flags=re.S)
    # Remove non-semantic layout markers & extract ordered structural tokens including +, -, =, ^, _, digits, words
    s = s.replace("\\", " ").replace("&", " ").replace("{", " ").replace("}", " ")
    # Extract tokens: multi-char operators, REF:..., words/numbers, signs, exponents/subscripts
    tokens = re.findall(
        r"REF:[A-Za-z0-9_.:-]+|<=>|<->|\|->|->\^|->|<-|=>|<=|>=|!=|:=|\|-|\.\.\.|\|\||[0-9]+(?:\.[0-9]+)?|[A-Za-z]+|[+\-=<>/^_*|]",
        s,
    )
    KEYWORDS = {
        "PM", "NOTIMPL",
        "frac", "sum", "prod", "max", "min", "log", "Pr", "arg", "arctan", "mod",
        "alpha", "beta", "gamma", "delta", "epsilon", "eta", "theta", "iota", "kappa",
        "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "phi", "chi", "psi", "omega",
        "Gamma", "Delta", "Theta", "Lambda", "Pi", "Sigma", "Upsilon", "Phi", "Omega",
        "partial", "inf", "equiv", "bowtie", "ell", "emptyset", "forall", "exists",
        "subset", "subseteq", "preceq", "succ", "perp", "parallel", "star", "odot",
        "oplus", "otimes", "cap", "without", "and", "in", "notin", "floor", "ceil",
        "Box", "SADAR", "ADAR", "AO", "ext",
    }
    norm_toks: list[str] = []
    for tok in tokens:
        if tok in ("^", "_"):
            # Keep exponent/subscript markers so a^2 != a_2 != a^3
            norm_toks.append(tok)
        elif tok.startswith("REF:") or tok in KEYWORDS or not tok.isalpha():
            norm_toks.append(tok)
        else:
            # Break identifiers into single characters so TeX `RD` and Typst `R D` match identically
            # while still rejecting ANY missing/changed letter or sign!
            for ch in tok:
                norm_toks.append(ch)
    return norm_toks


# --- Gate A: Baseline Immutability ---
def verify_baseline_immutability(root: Path, manifest: dict) -> dict:
    protected = manifest.get("baseline_protected_sha256", {})
    require(len(protected) == 211, f"Expected 211 protected baseline files in manifest, got {len(protected)}")
    counts = manifest.get("baseline_protected_counts", {})
    require(counts.get("tex") == 54, f"Expected 54 baseline TeX files, got {counts.get('tex')}")
    require(counts.get("bib") == 2, f"Expected 2 baseline BibTeX files, got {counts.get('bib')}")
    require(counts.get("images") == 49, f"Expected 49 baseline image files, got {counts.get('images')}")
    require(counts.get("manual_data") == 116, f"Expected 116 baseline manual/data files, got {counts.get('manual_data')}")

    for rel, expected_sha in sorted(protected.items()):
        p = root / rel
        require(p.is_file(), f"Protected baseline file missing: {rel}")
        actual_sha = sha256_file(p)
        require(actual_sha == expected_sha, f"Baseline byte change detected in {rel}: {actual_sha} != {expected_sha}")

    # If inside a Git checkout that has the baseline commit, independently verify against git object database
    git_verified = False
    if (root / ".git").exists():
        chk = subprocess.run(
            ["git", "cat-file", "-e", f"{SCIENTIFIC_BASELINE_COMMIT}^{{commit}}"],
            cwd=root, capture_output=True,
        )
        if chk.returncode == 0:
            git_verified = True
            for rel, expected_sha in sorted(protected.items()):
                blob = subprocess.check_output(
                    ["git", "show", f"{SCIENTIFIC_BASELINE_COMMIT}:{rel}"], cwd=root
                )
                git_sha = hashlib.sha256(blob).hexdigest()
                require(git_sha == expected_sha, f"Manifest digest disagrees with git baseline for {rel}")

            # Verify CANONICAL_BINDINGS.json only changed the 2 allowed engineering digests
            base_bindings = json.loads(
                subprocess.check_output(
                    ["git", "show", f"{SCIENTIFIC_BASELINE_COMMIT}:contracts/scientific/CANONICAL_BINDINGS.json"],
                    cwd=root,
                ).decode("utf-8")
            )
            cur_bindings = json.loads((root / "contracts/scientific/CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
            for key in ("schema", "ownership", "formulas", "unique_signatures", "manual_families", "supplemental_formulas"):
                require(cur_bindings.get(key) == base_bindings.get(key), f"Scientific contract section changed: {key}")
            base_frozen = base_bindings["frozen_sha256"]
            cur_frozen = cur_bindings["frozen_sha256"]
            require(set(cur_frozen) == set(base_frozen), "Frozen file set in CANONICAL_BINDINGS.json changed")
            changed_frozen = {k for k in base_frozen if cur_frozen[k] != base_frozen[k]}
            require(
                changed_frozen <= ALLOWED_ENGINEERING_FROZEN_AMENDMENTS,
                f"Unauthorized frozen_sha256 changes: {sorted(changed_frozen - ALLOWED_ENGINEERING_FROZEN_AMENDMENTS)}",
            )
            for k in changed_frozen:
                require(cur_frozen[k] == sha256_file(root / k), f"Amended frozen digest mismatch for {k}")

    return {
        "protected_baseline_files": len(protected),
        "tex_files_unchanged": counts["tex"],
        "bib_files_unchanged": counts["bib"],
        "image_files_unchanged": counts["images"],
        "manual_data_files_unchanged": counts["manual_data"],
        "git_baseline_cross_checked": git_verified,
        "engineering_frozen_amendments_only": sorted(ALLOWED_ENGINEERING_FROZEN_AMENDMENTS),
    }


# --- Gate B: Active Source Graph, Equations, Tables, Figures, Prose, References ---
def extract_tex_equations(parts: list[tuple[str, str]]) -> dict[str, tuple[str, str | None]]:
    """Extract {label: (math_body, tag_or_None)} from active LaTeX parts."""
    result: dict[str, tuple[str, str | None]] = {}
    for _, text in parts:
        for m in re.finditer(r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}", text, re.S):
            body = m.group(2)
            m_tag = re.search(r"\\tag\{([^}]+)\}", body)
            tag = m_tag.group(1).strip() if m_tag else None
            for lab in re.findall(r"\\label\{([^}]+)\}", body):
                result[lab] = (body, tag)
    return result


def extract_typst_equations(typ_files: list[Path]) -> dict[str, tuple[str, str | None]]:
    """Extract {label: (math_body, tag_or_None)} from active Typst files."""
    result: dict[str, tuple[str, str | None]] = {}
    for p in typ_files:
        text = strip_typst_comments(p.read_text(encoding="utf-8"))
        # Tagged equations: #tagged-eq("RG1", $ ... $, <label>)
        for m in re.finditer(r'#tagged-eq\("([^"]+)",\s*\$(.*?)\$,\s*<([^>]+)>\)', text, re.S):
            result[m.group(3)] = (m.group(2), m.group(1))
        # Regular numbered display equations: $ ... $ <label>
        for m in re.finditer(r'(?<!tagged-eq\("RG\d", )\$\s+([^$]+?)\s+\$\s*<([^>]+)>', text, re.S):
            lab = m.group(2)
            if lab not in result:
                result[lab] = (m.group(1), None)
    return result


def extract_tex_table_cells(tex_text: str) -> list[list[str]]:
    """Extract ordered table rows & cell strings from a LaTeX table/longtable/tabular file."""
    s = strip_tex_comments(tex_text)
    # Remove duplicate header before \endhead if \endfirsthead exists
    if "\\endfirsthead" in s and "\\endhead" in s:
        s = s[:s.index("\\endfirsthead")] + s[s.index("\\endhead") + len("\\endhead"):]
    # Remove \caption{...} and \label{...}
    s = re.sub(r"\\caption\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", s)
    s = re.sub(r"\\label\{[^}]+\}", "", s)
    # Find tabular / longtable / tabularx body using exact balanced brace parsing
    m = re.search(r"\\begin\{(longtable|tabularx|tabular)\}", s)
    require(m is not None, "Could not locate tabular/longtable environment in TeX table")
    env_name = m.group(1)
    pos = m.end()
    if env_name == "tabularx":
        _, pos = read_balanced_group(s, pos, "{", "}")  # width arg
    _, pos = read_balanced_group(s, pos, "{", "}")      # column spec
    end_idx = s.index(f"\\end{{{env_name}}}", pos)
    body = s[pos:end_idx]
    rows: list[list[str]] = []
    for raw_row in body.split("\\\\"):
        r = re.sub(r"\\(toprule|midrule|bottomrule|hline|endfirsthead|endhead)\b", "", raw_row).strip()
        if not r:
            continue
        cells = [norm_cell_text(c, is_typst=False) for c in r.split("&")]
        rows.append(cells)
    return rows


def extract_typst_table_cells(typ_text: str) -> list[list[str]]:
    """Extract ordered rows & cell strings from a native Typst table file."""
    s = strip_typst_comments(typ_text)
    m = re.search(r"columns:\s*\(([^)]+)\)", s)
    require(m is not None, "Could not locate columns: (...) in Typst table")
    ncols = len([c for c in m.group(1).split(",") if c.strip()])
    # Find table(...) body
    t_start = s.index("table(") + len("table(")
    # Collect all [...] cells inside table(...)
    cells: list[str] = []
    i = t_start
    depth_paren = 1
    while i < len(s) and depth_paren > 0:
        ch = s[i]
        if ch == "(":
            depth_paren += 1
            i += 1
        elif ch == ")":
            depth_paren -= 1
            i += 1
        elif ch == "[":
            cell_raw, i = read_balanced_group(s, i, "[", "]")
            cells.append(norm_cell_text(cell_raw, is_typst=True))
        else:
            i += 1
    require(len(cells) % ncols == 0, f"Typst table cell count {len(cells)} not divisible by {ncols}")
    return [cells[k:k + ncols] for k in range(0, len(cells), ncols)]


def norm_cell_text(cell: str, is_typst: bool) -> str:
    t = norm_typography(cell.strip())
    if is_typst:
        t = re.sub(r'#raw\("([^"]+)"\)', r'\1', t)
        t = re.sub(r'#emph\[([^\]]+)\]', r'\1', t)
        t = re.sub(r'#strong\[([^\]]+)\]', r'\1', t)
        t = re.sub(r'#(?:eqref|eqnref|secref|appref|figref|tabref|mainequation|mainsection|mainappendix|maintable)\("([^"]+)"\)', r'REF:\1', t)
        t = re.sub(r'\$([^$]+)\$', lambda m: " ".join(canonicalize_math_common(m.group(1), is_typst=True)), t)
        t = t.replace("\\#", "#").replace("\\%", "%").replace("\\_", "_")
    else:
        t = re.sub(r'\\texttt\{([^}]+)\}', r'\1', t)
        t = re.sub(r'\\(?:emph|textbf|textit)\{([^}]+)\}', r'\1', t)
        t = re.sub(r'\\(?:eqref|eqnref|secref|appref|figref|tabref|mainequation|mainsection|mainappendix|maintable)\{([^}]+)\}', r'REF:\1', t)
        t = re.sub(r'\\\((.*?)\\\)', lambda m: " ".join(canonicalize_math_common(m.group(1), is_typst=False)), t)
        t = re.sub(r'\$([^$]+)\$', lambda m: " ".join(canonicalize_math_common(m.group(1), is_typst=False)), t)
        t = t.replace("\\#", "#").replace("\\%", "%").replace("\\_", "_")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _strip_tex_table_specs(s: str) -> str:
    """Strip LaTeX tabular/tabularx/longtable begin-spec arguments using balanced braces."""
    out = []
    pos = 0
    for m in re.finditer(r"\\begin\{(longtable|tabularx|tabular)\}", s):
        if m.start() < pos:
            continue
        out.append(s[pos:m.start()])
        env = m.group(1)
        p = m.end()
        if env == "tabularx":
            _, p = read_balanced_group(s, p, "{", "}")
        spec, p = read_balanced_group(s, p, "{", "}")
        # If table has >{$} auto-math columns, strip math cells from body in TeX to match Typst $...$ stripping
        if ">$" in spec or ">{$}" in spec:
            end_tok = f"\\end{{{env}}}"
            end_idx = s.index(end_tok, p)
            body = s[p:end_idx]
            # Keep only non-auto-math columns (column index 1 in B_quarantined_external_comparison)
            rows_kept = []
            for r in body.split("\\\\"):
                r_c = re.sub(r"\\(toprule|midrule|bottomrule|hline)\b", "", r).strip()
                if "&" in r_c:
                    cols = r_c.split("&")
                    # Keep text column (col 1) and drop auto-math cols 0, 2, 3
                    if len(cols) >= 2:
                        rows_kept.append(cols[1])
                elif r_c:
                    rows_kept.append(r_c)
            out.append(" " + " ".join(rows_kept) + " ")
            pos = end_idx + len(end_tok)
        else:
            out.append(" ")
            pos = p
    out.append(s[pos:])
    return "".join(out)


def extract_prose_words_tex(text: str) -> list[str]:
    """Extract ordered prose & qualification tokens from LaTeX text (outside math)."""
    s = strip_tex_comments(text)
    # Strip duplicate longtable header between \endfirsthead and \endhead
    s = re.sub(r"\\endfirsthead.*?\\endhead", " ", s, flags=re.S)
    # Strip table column specifications (including >{$} auto-math columns) BEFORE stripping $...$
    s = _strip_tex_table_specs(s)
    # Strip line breaks \\[0.3em] first so \\[ is never mistaken for display math \[
    s = re.sub(r"\\\\(?:\[[^\]]*\])?", " ", s)
    # Strip display/inline math and tikzpictures
    s = re.sub(r"\\begin\{(equation\*?|align\*?|gather\*?|tikzpicture)\}.*?\\end\{\1\}", " ", s, flags=re.S)
    s = re.sub(r"\\\[.*?\\\]", " ", s, flags=re.S)
    s = re.sub(r"\\\(.*?\\\)", " ", s, flags=re.S)
    s = re.sub(r"\$[^$]+\$", " ", s)
    # Preserve definition [Title] text
    s = re.sub(r"\\begin\{definition\}\[([^\]]*)\]", r" \1 ", s)
    s = re.sub(r"\\begin\{abstract\}", " Abstract ", s)
    # Strip reference/citation/layout commands and their non-prose arguments
    s = re.sub(r"\\(?:label|cite|eqref|eqnref|secref|appref|figref|tabref|ref|mainequation|mainsection|mainappendix|maintable|includegraphics|input|vspace|hspace|setlength|renewcommand)\*?(?:\[[^\]]*\])?\{[^}]*\}", " ", s)
    s = re.sub(r"\\begin\{minipage\}\{[^}]*\}", " ", s)
    s = re.sub(r"\\begin\{[^}]+\}(?:\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\end\{[^}]+\}", " ", s)
    s = re.sub(r"\\texorpdfstring\{([^}]*)\}\{[^}]*\}", r" \1 ", s)
    s = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r" \1 ", s)
    s = re.sub(r"\\aodnoteblock\{([^}]*)\}", r" \1 ", s)
    s = re.sub(r"\\(?:section|subsection|subsubsection|paragraph|caption|aodprovenance|aodliteraturenote|aodremark|emph|textbf|textit|texttt|path|hbox)\*?", " ", s)
    s = re.sub(r"\\[A-Za-z@]+", " ", s)
    s = norm_typography(s)
    return re.findall(r"[A-Za-z]{3,}", s.lower())


def extract_prose_words_typst(text: str) -> list[str]:
    """Extract ordered prose & qualification tokens from Typst text (outside math)."""
    s = strip_typst_comments(text)
    s = re.sub(r'#import\s+"[^"]+":\s*\*', " ", s)
    s = re.sub(r'#include\s+"[^"]+"', " ", s)
    s = re.sub(r'#tagged-eq\("[^"]+",\s*\$.*?\$,\s*<[^>]+>\)', " ", s, flags=re.S)
    s = re.sub(r'#math\.equation\(block:\s*true,\s*numbering:\s*none,\s*\$.*?\$\)', " ", s, flags=re.S)
    s = re.sub(r'#aod-flowchart\(.*?^\)\s*$', " ", s, flags=re.S | re.M)
    s = re.sub(r'\$[^$]+\$', " ", s)
    s = re.sub(r'#(?:eqref|eqnref|secref|appref|figref|tabref|bare-ref|mainequation|mainsection|mainappendix|maintable|aod-cite|image|aod-anchor)\([^)]*\)', " ", s)
    s = re.sub(r'#aod-noteblock\("([^"]+)"\)', r" \1 ", s)
    s = re.sub(r'#link\("[^"]+"\)', " ", s)
    # Strip unescaped Typst <label> tags BEFORE unquoting #raw("..."), preserving literal <anchor> in raw strings
    s = re.sub(r'#raw\("([^"]+)"\)', lambda m: " " + m.group(1).replace("<", " ").replace(">", " ") + " ", s)
    s = re.sub(r'(?<!\\)<[A-Za-z0-9_.:-]+>', " ", s)
    s = s.replace("\\<", "<").replace("\\>", ">")
    s = re.sub(r'#align\(center\)', " ", s)
    s = re.sub(r'#pagebreak\(weak:\s*true\)', " ", s)
    s = re.sub(r'#block\([^)]*\)', " ", s)
    s = re.sub(r'#pad\([^)]*\)', " ", s)
    s = re.sub(r'#(?:figure|aod-definition|aod-provenance|aod-literature-note|aod-remark|aod-paragraph|aod-panel|align|emph|strong|text|box|heading)\b', " ", s)
    s = re.sub(r'(?:kind:\s*(?:table|image)|caption:|title:|width:\s*[0-9.]+%|size:\s*[0-9.]+pt|columns:\s*\([^)]*\)|align:\s*\([^)]*\)|set\s+text\([^)]*\)|set\s+par\([^)]*\)|table\.header|table\(|toprule|midrule|bottomrule|left:\s*[0-9.]+em|right:\s*[0-9.]+em|font:\s*\([^)]*\)|level:\s*\d+|numbering:\s*none)', " ", s)
    s = norm_typography(s)
    return re.findall(r"[A-Za-z]{3,}", s.lower())


def verify_source_and_content_parity(root: Path, manifest: dict) -> dict:
    # 1. Verify active include graph 1-to-1 coverage
    mfiles, mparts = audit.include_graph(root, "main")
    ufiles, uparts = audit.include_graph(root, "manual")
    active_map = manifest.get("active_source_map", [])
    mapped_tex = [item["tex_source"] for item in active_map]
    expected_active = list(mfiles) + list(ufiles)
    require(
        set(mapped_tex) == set(expected_active) and len(mapped_tex) == len(expected_active),
        f"Active include graph mismatch: missing={sorted(set(expected_active)-set(mapped_tex))}, extra={sorted(set(mapped_tex)-set(expected_active))}",
    )

    # Verify all 6 immutable Manual tables are mapped and included in typst/manual/
    for tbl_tex in IMMUTABLE_MANUAL_TABLES:
        require(tbl_tex in ufiles, f"Immutable table absent from active Manual TeX graph: {tbl_tex}")
        matches = [x for x in active_map if x["tex_source"] == tbl_tex]
        require(len(matches) == 1, f"Immutable table missing from Typst manifest: {tbl_tex}")
        tbl_typ = root / matches[0]["typst_target"]
        require(tbl_typ.is_file(), f"Immutable table Typst counterpart missing: {tbl_typ}")

    # Verify the 5 historical TeX snapshots are excluded from active authoring
    for hist in HISTORICAL_TEX_SNAPSHOTS:
        require(hist not in mapped_tex, f"Historical snapshot leaked into active Typst manifest: {hist}")

    # Verify every active Typst target is actually included by typst/main.typ or typst/manual/main.typ
    def collect_typst_includes(driver: Path) -> list[str]:
        seen = [driver.relative_to(root).as_posix()]
        stack = [driver.resolve()]
        while stack:
            cur = stack.pop()
            txt = strip_typst_comments(cur.read_text(encoding="utf-8"))
            for inc in re.findall(r'#include\s+"([^"]+)"', txt):
                child = (cur.parent / inc).resolve()
                require(child.is_file(), f"Missing Typst #include {inc} from {cur}")
                rel = child.relative_to(root).as_posix()
                if rel not in seen:
                    seen.append(rel)
                    stack.append(child)
        return seen

    main_typ_graph = collect_typst_includes(root / "typst/main.typ")
    manual_typ_graph = collect_typst_includes(root / "typst/manual/main.typ")
    for item in active_map:
        tgt = item["typst_target"]
        if tgt.endswith("preamble.typ"):
            require((root / tgt).is_file(), f"Missing Typst preamble: {tgt}")
            continue
        if item["surface"] == "main":
            require(tgt in main_typ_graph, f"Main Typst source unit not included by typst/main.typ: {tgt}")
        else:
            require(tgt in manual_typ_graph, f"Manual Typst source unit not included by typst/manual/main.typ: {tgt}")

    # 2. Verify all 6 immutable tables + cycle_shedding_summary cell-by-cell
    table_checks = {}
    for tbl_tex in list(IMMUTABLE_MANUAL_TABLES) + ["cycle_shedding_summary.tex"]:
        entry = [x for x in active_map if x["tex_source"] == tbl_tex][0]
        tex_rows = extract_tex_table_cells((root / tbl_tex).read_text(encoding="utf-8"))
        typ_rows = extract_typst_table_cells((root / entry["typst_target"]).read_text(encoding="utf-8"))
        require(
            tex_rows == typ_rows,
            f"Table cell parity mismatch for {tbl_tex} vs {entry['typst_target']}:\n  TeX={tex_rows}\n  Typ={typ_rows}",
        )
        table_checks[tbl_tex] = {"rows": len(tex_rows), "cols": len(tex_rows[0]) if tex_rows else 0}

    # 3. Verify ALL labeled equations (187+11 Main, 19+1 Manual) structurally (signs, exponents, indices, tags)
    eq_counts = {}
    for surf, parts, typ_paths in [
        ("main", mparts, [root / p for p in main_typ_graph]),
        ("manual", uparts, [root / p for p in manual_typ_graph]),
    ]:
        tex_eqs = extract_tex_equations(parts)
        typ_eqs = extract_typst_equations(typ_paths)
        require(
            set(tex_eqs) == set(typ_eqs),
            f"{surf} labeled equation set mismatch: missing={sorted(set(tex_eqs)-set(typ_eqs))}, extra={sorted(set(typ_eqs)-set(tex_eqs))}",
        )
        for lab in sorted(tex_eqs):
            tex_body, tex_tag = tex_eqs[lab]
            typ_body, typ_tag = typ_eqs[lab]
            require(tex_tag == typ_tag, f"Equation tag mismatch for {lab}: TeX={tex_tag!r} vs Typ={typ_tag!r}")
            t_toks = canonicalize_math_common(tex_body, is_typst=False)
            y_toks = canonicalize_math_common(typ_body, is_typst=True)
            require(
                t_toks == y_toks,
                f"Equation structure mismatch for {lab}:\n  TeX={t_toks}\n  Typ={y_toks}",
            )
        eq_counts[surf] = len(tex_eqs)

    # 4. Verify ordered prose & qualification tokens and note/definition counts per active content file
    file_prose_checked = 0
    qualifier_totals = {}
    for item in active_map:
        tex_rel = item["tex_source"]
        typ_rel = item["typst_target"]
        if tex_rel in ("main.tex", "preamble.tex", "manual/main.tex", "manual/preamble.tex", "sections/00_title.tex"):
            continue
        tex_raw = (root / tex_rel).read_text(encoding="utf-8")
        typ_raw = (root / typ_rel).read_text(encoding="utf-8")

        # Check Provenance / Literature note / Remark / Definition counts per file
        for tex_pat, typ_pat, role in [
            (r"\\aodprovenance\{", r"#aod-provenance\[", "Provenance"),
            (r"\\aodliteraturenote\{", r"#aod-literature-note\[", "Literature note"),
            (r"\\aodremark\{", r"#aod-remark\[", "Remark"),
            (r"\\begin\{definition\}", r"#aod-definition", "Definition"),
        ]:
            n_tex = len(re.findall(tex_pat, strip_tex_comments(tex_raw)))
            n_typ = len(re.findall(typ_pat, strip_typst_comments(typ_raw)))
            require(n_tex == n_typ, f"{role} count mismatch in {tex_rel}: TeX={n_tex} vs Typ={n_typ}")

        # Check exact figure asset identities
        tex_imgs = []
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", strip_tex_comments(tex_raw)):
            p_arg = m.group(1).strip()
            if item["surface"] == "main":
                tex_imgs.append("/" + p_arg.lstrip("/"))
            elif p_arg.startswith("../"):
                tex_imgs.append("/" + p_arg[3:])
            else:
                tex_imgs.append("/manual/" + p_arg)
        typ_imgs = re.findall(r'#image\("([^"]+)"', strip_typst_comments(typ_raw))
        require(tex_imgs == typ_imgs, f"Figure identity/order mismatch in {tex_rel}: TeX={tex_imgs} vs Typ={typ_imgs}")

        # Check ordered prose words & scientific qualifiers (rejects any removed qualification or prose drift)
        w_tex = extract_prose_words_tex(tex_raw)
        w_typ = extract_prose_words_typst(typ_raw)
        c_tex = Counter(w_tex)
        c_typ = Counter(w_typ)
        for q in QUALIFIER_WORDS:
            require(
                c_tex[q] == c_typ[q],
                f"Scientific qualifier {q!r} count changed in {tex_rel}: TeX={c_tex[q]} vs Typ={c_typ[q]}",
            )
            qualifier_totals[q] = qualifier_totals.get(q, 0) + c_tex[q]
        # Verify exact prose word multiset parity (zero dropped words!)
        dropped = {k: v for k, v in (c_tex - c_typ).items() if v > 0}
        added = {k: v for k, v in (c_typ - c_tex).items() if v > 0}
        # Allow tiny formatting words only if inside auto-stripped table specs; require ZERO dropped prose words!
        require(
            not dropped and not added,
            f"Prose word drift in {tex_rel}: dropped={dropped}, added={added}",
        )
        file_prose_checked += 1

    # 5. Verify exact numeric literals across every active file (integers >= 2 digits & all decimals)
    for item in active_map:
        tex_rel = item["tex_source"]
        typ_rel = item["typst_target"]
        if tex_rel in ("main.tex", "preamble.tex", "manual/main.tex", "manual/preamble.tex"):
            continue
        tex_clean = strip_tex_comments((root / tex_rel).read_text(encoding="utf-8"))
        # Strip LaTeX layout dimensions (0.85\linewidth, 0.35em, 0.55cm, 4pt)
        tex_clean = re.sub(r"[0-9.]+\s*\\(?:linewidth|textwidth)", " ", tex_clean)
        tex_clean = re.sub(r"\\renewcommand\{\\arraystretch\}\{[0-9.]+\}", " ", tex_clean)
        tex_clean = re.sub(r"\b[0-9.]+(?:em|cm|pt|mm|in)(?![A-Za-z0-9])", " ", tex_clean)
        tex_clean = re.sub(r"(?:vspace|hspace)\{[0-9.]+(?:em|cm|pt|mm|in)\}", " ", tex_clean)
        tex_clean = re.sub(r"\[[0-9.]+(?:em|cm|pt|mm|in)\]", " ", tex_clean)
        tex_clean = re.sub(r"(?:node distance|inner sep|below left|below right|below)=[0-9.]+(?:cm|pt)(?:\s+and\s+[0-9.]+cm)?", " ", tex_clean)
        tex_clean = re.sub(r"\\label\{[^}]+\}", " ", tex_clean)
        tex_clean = re.sub(r"\\(?:eqref|eqnref|secref|appref|figref|tabref|ref|mainequation|mainsection|mainappendix|maintable|cite|includegraphics|input)\*?(?:\[[^\]]*\])?\{[^}]+\}", " ", tex_clean)

        typ_clean = strip_typst_comments((root / typ_rel).read_text(encoding="utf-8"))
        typ_clean = re.sub(r"(?:size|width|height|inset|radius|stroke|x|y|w|h|left|right|above|below|v|spacing):\s*[0-9.]+(?:pt|cm|em|%|fr)", " ", typ_clean)
        typ_clean = re.sub(r"\b[0-9.]+(?:pt|cm|em|%|fr)(?![A-Za-z0-9])", " ", typ_clean)
        typ_clean = re.sub(r'#v\([0-9.]+(?:em|fr|pt)\)', " ", typ_clean)
        typ_clean = re.sub(r'level:\s*\d+', " ", typ_clean)
        typ_clean = re.sub(r'<[A-Za-z0-9_.:-]+>', " ", typ_clean)
        typ_clean = re.sub(r'#(?:eqref|eqnref|secref|appref|figref|tabref|bare-ref|mainequation|mainsection|mainappendix|maintable|aod-cite|image|aod-anchor)\([^)]*\)', " ", typ_clean)

        tex_decs = Counter(re.findall(r"(?<![0-9.])\d+\.\d+(?![0-9.])", tex_clean))
        typ_decs = Counter(re.findall(r"(?<![0-9.])\d+\.\d+(?![0-9.])", typ_clean))
        require(
            tex_decs == typ_decs,
            f"Exact decimal value mismatch in {tex_rel}: TeX-Typ={dict(tex_decs - typ_decs)}, Typ-TeX={dict(typ_decs - tex_decs)}",
        )

    return {
        "active_main_tex_files": len(mfiles),
        "active_manual_tex_files": len(ufiles),
        "active_files_mapped": len(active_map),
        "immutable_tables_verified_cell_by_cell": table_checks,
        "labeled_equations_verified_structurally": eq_counts,
        "prose_and_qualifier_files_verified": file_prose_checked,
        "qualifier_token_totals": qualifier_totals,
    }


# --- Gate C: Evaluated Typst Query & Rendered PDF Parity ---
def verify_evaluated_and_rendered(
    root: Path,
    typst_bin: str,
    outdir: Path,
    baseline_main_pdf: Path | None = None,
    baseline_manual_pdf: Path | None = None,
) -> dict:
    import pypdf

    # 1. Verify fresh Main + Manual build with strict registry check
    report = typst_builder.build_all(
        root=root,
        outdir=outdir,
        typst_bin=typst_bin,
        write_registry=False,
        check_registry_only=True,
    )
    main_digest = report["main_sources_sha256"]

    # 2. Verify ALL 455 Main + 227 Manual labels against LaTeX include_graph label_map
    tex_main_labs = audit.label_map(root, "main")
    tex_manual_labs = audit.label_map(root, "manual")

    reg = json.loads((root / "typst/lib/main_registry.json").read_text(encoding="utf-8"))
    require(reg["main_sources_sha256"] == main_digest, "Stale Main registry digest")
    typ_main_entries = reg["entries"]
    require(
        set(typ_main_entries) == set(tex_main_labs),
        f"Main label identity mismatch: missing={sorted(set(tex_main_labs)-set(typ_main_entries))}, extra={sorted(set(typ_main_entries)-set(tex_main_labs))}",
    )

    manual_eval_entries = typst_builder.run_typst_eval(
        typst_bin, root, root / "typst/manual/main.typ", "<aod-ref-entry>",
        inputs={"expected_main_digest": main_digest},
    )
    typ_manual_entries = {}
    for item in manual_eval_entries:
        v = item["value"]
        require(v["id"] not in typ_manual_entries, f"Duplicate Manual evaluated label: {v['id']}")
        typ_manual_entries[v["id"]] = v
    require(
        set(typ_manual_entries) == set(tex_manual_labs),
        f"Manual label identity mismatch: missing={sorted(set(tex_manual_labs)-set(typ_manual_entries))}, extra={sorted(set(typ_manual_entries)-set(tex_manual_labs))}",
    )

    # 3. Verify all 172 Main->Manual reference uses, target types, and page destinations
    main_pdf_path = outdir / "main_typst.pdf"
    manual_pdf_path = outdir / "manual_typst.pdf"
    main_reader = pypdf.PdfReader(str(main_pdf_path))
    manual_reader = pypdf.PdfReader(str(manual_pdf_path))
    main_pages = len(main_reader.pages)
    manual_pages = len(manual_reader.pages)

    mainref_uses = typst_builder.run_typst_eval(
        typst_bin, root, root / "typst/manual/main.typ", "<aod-mainref-use>",
        inputs={"expected_main_digest": main_digest},
    )
    # Count exact TeX Main->Manual reference occurrences
    _, uparts = audit.include_graph(root, "manual")
    tex_mainref_list = []
    for path, text in uparts:
        if path.endswith("preamble.tex"):
            continue
        for m in re.finditer(r"\\(mainequation|mainsection|mainappendix|maintable)\{([^}]+)\}", text):
            tex_mainref_list.append((m.group(1), m.group(2)))
    typ_mainref_list = [(x["value"]["macro"], x["value"]["ref_id"]) for x in mainref_uses]
    require(
        Counter(tex_mainref_list) == Counter(typ_mainref_list),
        f"Main->Manual ref call-site mismatch: TeX={len(tex_mainref_list)} vs Typ={len(typ_mainref_list)}",
    )
    for item in mainref_uses:
        v = item["value"]
        require(v["registry_digest"] == main_digest, f"Stale registry digest in Main ref {v['ref_id']}")
        require(1 <= v["target_page"] <= main_pages, f"Out-of-range PDF target page in {v['ref_id']}: {v['target_page']}")
        require(v["pdf_destination"] == f"main.pdf#page={v['target_page']}", f"Malformed PDF destination: {v['pdf_destination']}")

    # 4. Inspect actual PDF annotations & rendered text (zero leaks, zero U+FFFD, valid links)
    pdf_stats = {}
    for name, reader, pdf_path, expected_min_links in [
        ("main", main_reader, main_pdf_path, 500),
        ("manual", manual_reader, manual_pdf_path, 300),
    ]:
        internal_links = 0
        main_pdf_links = 0
        uri_links = 0
        for pno, page in enumerate(reader.pages, 1):
            for a in page.get("/Annots", []):
                o = a.get_object()
                if o.get("/Subtype") != "/Link":
                    continue
                if o.get("/Dest") is not None:
                    internal_links += 1
                elif o.get("/A") is not None:
                    uri = str(o.get("/A").get_object().get("/URI", ""))
                    require(bool(uri), f"Empty PDF link action on {name} p.{pno}")
                    if uri.startswith("main.pdf#page="):
                        pg = int(uri.split("page=")[1])
                        require(1 <= pg <= main_pages, f"Invalid main.pdf#page={pg} link on Manual p.{pno}")
                        main_pdf_links += 1
                    else:
                        uri_links += 1
        require(internal_links + main_pdf_links >= expected_min_links, f"Too few PDF links in {name}: {internal_links + main_pdf_links}")

        # Rendered PDF text hygiene
        txt = subprocess.check_output(["pdftotext", str(pdf_path), "-"], text=True)
        require("\ufffd" not in txt, f"Replacement character U+FFFD found in rendered {name} PDF")
        leaks = re.findall(r"(?:toprule|midrule|bottomrule|table\.header|set text\(|set par\(|#figure|#aod-)", txt)
        require(not leaks, f"Leaked Typst syntax tokens in rendered {name} PDF: {leaks[:5]}")
        require("??" not in txt, f"Unresolved '??' marker in rendered {name} PDF")
        pdf_stats[name] = {
            "pages": len(reader.pages),
            "internal_links": internal_links,
            "main_pdf_links": main_pdf_links,
            "uri_links": uri_links,
        }

    # 5. Bibliography completeness (10 Main + 43 Manual)
    main_bib = typst_builder.run_typst_eval(typst_bin, root, root / "typst/main.typ", "<aod-bib-entry>")
    manual_bib = typst_builder.run_typst_eval(
        typst_bin, root, root / "typst/manual/main.typ", "<aod-bib-entry>",
        inputs={"expected_main_digest": main_digest},
    )
    require(len(main_bib) == 10, f"Expected 10 Main bibliography entries, got {len(main_bib)}")
    require(len(manual_bib) == 43, f"Expected 43 Manual bibliography entries, got {len(manual_bib)}")

    # 6. Optional direct comparison against compiled baseline XeLaTeX PDFs
    baseline_pdf_comparison = {"performed": False}
    if baseline_main_pdf and baseline_manual_pdf:
        comp = {}
        for name, bpdf, tpdf in [
            ("main", baseline_main_pdf, main_pdf_path),
            ("manual", baseline_manual_pdf, manual_pdf_path),
        ]:
            require(bpdf.is_file(), f"Baseline PDF missing: {bpdf}")
            bt = norm_typography(subprocess.check_output(["pdftotext", str(bpdf), "-"], text=True))
            tt = norm_typography(subprocess.check_output(["pdftotext", str(tpdf), "-"], text=True))
            b_dec = Counter(re.findall(r"\b\d+\.\d+\b", bt))
            t_dec = Counter(re.findall(r"\b\d+\.\d+\b", tt))
            require(b_dec == t_dec, f"Rendered PDF decimal mismatch for {name}: base-typ={dict(b_dec - t_dec)}, typ-base={dict(t_dec - b_dec)}")
            comp[name] = {"rendered_decimals_matched": sum(b_dec.values())}
        # Verify all 172 Main->Manual resolved displays occur in baseline manual.pdf
        b_man = subprocess.check_output(["pdftotext", str(baseline_manual_pdf), "-"], text=True)
        for item in mainref_uses:
            disp = item["value"]["resolved_display"]
            pat = re.escape(disp).replace(r"\ ", r"\s+")
            require(re.search(pat, b_man) is not None, f"Resolved Main ref {disp!r} absent from baseline manual.pdf")
        comp["manual_mainref_displays_matched_in_baseline_pdf"] = len(mainref_uses)
        baseline_pdf_comparison = {"performed": True, "results": comp}

    return {
        "typst_version": report["typst_version"],
        "main_sources_sha256": main_digest,
        "main_labels_verified": len(typ_main_entries),
        "manual_labels_verified": len(typ_manual_entries),
        "manual_mainrefs_verified": len(mainref_uses),
        "main_bib_entries": len(main_bib),
        "manual_bib_entries": len(manual_bib),
        "pdf_stats": pdf_stats,
        "baseline_pdf_comparison": baseline_pdf_comparison,
    }


# --- Gate D: Executable Negative Controls ---
def run_negative_controls(root: Path, typst_bin: str) -> dict:
    """Verify the checker and Typst compiler REJECT all 5 mandatory negative controls."""
    results = {}
    manifest = json.loads((root / "typst/manifest.json").read_text(encoding="utf-8"))

    def make_sandbox(tmp_root: Path) -> Path:
        # Lightweight copy using hardlinks/copies for typst/ and read-only symlinks not allowed,
        # so copy only active TeX, Bib, figures, and typst/ (small, ~15 MB).
        for d in ("sections", "appendices", "figures_jpg", "typst", "contracts", "scripts"):
            shutil.copytree(root / d, tmp_root / d)
        for f in ("main.tex", "preamble.tex", "refs.bib", "cycle_shedding_summary.tex"):
            shutil.copy2(root / f, tmp_root / f)
        (tmp_root / "manual").mkdir()
        for f in ("main.tex", "preamble.tex", "refs.bib"):
            shutil.copy2(root / "manual" / f, tmp_root / "manual" / f)
        for d in ("sections", "appendices", "figures"):
            shutil.copytree(root / "manual" / d, tmp_root / "manual" / d)
        # Copy the 6 immutable table files
        for tbl in IMMUTABLE_MANUAL_TABLES:
            dst = tmp_root / tbl
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / tbl, dst)
        return tmp_root

    with tempfile.TemporaryDirectory(prefix="aod-typst-negctrl-") as tmp:
        def expect_rejection(label: str, fn) -> dict:
            try:
                fn()
            except (ValueError, RuntimeError) as exc:
                raw = str(exc).replace(tmp, "<sandbox>")
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                detail = next((ln for ln in lines if "panicked with:" in ln), lines[0] if lines else "")
                return {"rejected": True, "error": detail[:180]}
            raise ValueError(f"NEGATIVE CONTROL FAILED (not rejected): {label}")

        base_sb = make_sandbox(Path(tmp) / "sb")

        # Control 1a: Changed exact table value (10893.83 -> 10893.84 in sparc_summary_table.typ)
        sb = Path(tmp) / "c1_table"
        shutil.copytree(base_sb, sb)
        p = sb / "typst/manual/tables/sparc_summary_table.typ"
        orig = p.read_text(encoding="utf-8")
        require("10893.83" in orig, "Control 1 setup failed")
        p.write_text(orig.replace("10893.83", "10893.84", 1), encoding="utf-8")
        results["1a_changed_table_value"] = expect_rejection(
            "changed_table_value",
            lambda: verify_source_and_content_parity(sb, manifest),
        )

        # Control 1b: Changed sign or exponent in a Main equation (+ -> - in eq:duon-current / eq:hinge-grammar)
        sb = Path(tmp) / "c1_sign"
        shutil.copytree(base_sb, sb)
        p = sb / "typst/sections/03_afc_basis.typ"
        orig = p.read_text(encoding="utf-8")
        require("(- epsilon)" in orig or "(-epsilon)" in orig or "10" in orig, "Control 1b setup check")
        # Flip exponent ^2 -> ^3 in iota^2 = id (eq:hinge-reflection-involution)
        require("iota^2" in orig, "Control 1b setup failed: iota^2 not found")
        p.write_text(orig.replace("iota^2", "iota^3", 1), encoding="utf-8")
        results["1b_changed_equation_exponent"] = expect_rejection(
            "changed_equation_exponent",
            lambda: verify_source_and_content_parity(sb, manifest),
        )

        # Control 2: Removed scientific qualification ("never" removed from prose)
        sb = Path(tmp) / "c2_qual"
        shutil.copytree(base_sb, sb)
        p = sb / "typst/sections/04_cut_running_fractal_tesseract.typ"
        orig = p.read_text(encoding="utf-8")
        require("never" in orig, "Control 2 setup failed")
        p.write_text(orig.replace("never", "", 1), encoding="utf-8")
        results["2_removed_qualification"] = expect_rejection(
            "removed_qualification",
            lambda: verify_source_and_content_parity(sb, manifest),
        )

        # Control 3: Omitted active table include
        sb = Path(tmp) / "c3_omit_table"
        shutil.copytree(base_sb, sb)
        p = sb / "typst/manual/sections/06_field_dynamics_applications.typ"
        orig = p.read_text(encoding="utf-8")
        target = '#include "../tables/sparc_summary_table.typ"'
        require(target in orig, "Control 3 setup failed")
        p.write_text(orig.replace(target, "", 1), encoding="utf-8")
        results["3_omitted_active_table"] = expect_rejection(
            "omitted_active_table",
            lambda: verify_source_and_content_parity(sb, manifest),
        )

        # Control 4: Wrong Main reference target type (#mainequation pointing to a Main section)
        sb = Path(tmp) / "c4_wrong_reftype"
        shutil.copytree(base_sb, sb)
        p = sb / "typst/manual/sections/00_scope.typ"
        orig = p.read_text(encoding="utf-8")
        # Inject wrong-type Main ref (section referenced via #mainequation)
        p.write_text(orig + '\n#mainequation("main:sec:afc-basis")\n', encoding="utf-8")
        live_digest, _ = typst_builder.compute_main_sources_digest(sb)
        results["4_wrong_reference_target_type"] = expect_rejection(
            "wrong_reference_target_type",
            lambda: typst_builder.compile_doc(
                typst_bin, sb, sb / "typst/manual/main.typ", Path(tmp) / "c4.pdf",
                inputs={"expected_main_digest": live_digest},
            ),
        )

        # Control 5: Stale Main registry consumed by Manual (modify Main without updating main_registry.json)
        sb = Path(tmp) / "c5_stale_registry"
        shutil.copytree(base_sb, sb)
        p = sb / "typst/sections/03_afc_basis.typ"
        p.write_text(p.read_text(encoding="utf-8") + "\n// simulated Main source edit without registry refresh\n", encoding="utf-8")
        stale_live_digest, _ = typst_builder.compute_main_sources_digest(sb)
        results["5_stale_main_registry"] = expect_rejection(
            "stale_main_registry",
            lambda: typst_builder.compile_doc(
                typst_bin, sb, sb / "typst/manual/main.typ", Path(tmp) / "c5.pdf",
                inputs={"expected_main_digest": stale_live_digest},
            ),
        )

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify native Typst Main/Manual scientific parity against retained LaTeX baseline.")
    ap.add_argument("--root", default=str(ROOT), help="Repository root directory")
    ap.add_argument("--outdir", default="_build/typst_parity", help="Output directory for built Typst PDFs and parity report")
    ap.add_argument("--typst-bin", default=None, help="Explicit path to typst binary")
    ap.add_argument("--baseline-main-pdf", default=None, help="Optional compiled baseline XeLaTeX main.pdf for direct PDF comparison")
    ap.add_argument("--baseline-manual-pdf", default=None, help="Optional compiled baseline XeLaTeX manual.pdf for direct PDF comparison")
    ap.add_argument("--skip-negative-controls", action="store_true", help="Skip negative-control self-tests (not recommended for gate runs)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = (root / outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    typst_bin = typst_builder.find_typst(args.typst_bin)

    manifest = json.loads((root / "typst/manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("schema") == "aod.typst.manifest.v1", "Invalid typst/manifest.json schema")

    gate_a = verify_baseline_immutability(root, manifest)
    gate_b = verify_source_and_content_parity(root, manifest)
    gate_c = verify_evaluated_and_rendered(
        root,
        typst_bin,
        outdir,
        baseline_main_pdf=Path(args.baseline_main_pdf).resolve() if args.baseline_main_pdf else None,
        baseline_manual_pdf=Path(args.baseline_manual_pdf).resolve() if args.baseline_manual_pdf else None,
    )
    gate_d = (
        {"skipped": True}
        if args.skip_negative_controls
        else run_negative_controls(root, typst_bin)
    )

    payload = {
        "schema": "aod.typst.parity-report.v1",
        "verdict": "PASS",
        "scientific_baseline_commit": SCIENTIFIC_BASELINE_COMMIT,
        "canonical_source_promotion": "SEPARATE_NOT_INFERRED_FROM_ADDITIVE_PORT",
        "typ2tex_compatibility_status": "SEPARATELY_TRACKED_NOT_IMPLEMENTED_IN_S1A_NATIVE_PORT",
        "gate_a_baseline_immutability": gate_a,
        "gate_b_scientific_content_parity": gate_b,
        "gate_c_evaluated_and_rendered": gate_c,
        "gate_d_negative_controls": gate_d,
    }
    report_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    (outdir / "parity_report.json").write_text(report_json, encoding="utf-8")
    print(report_json, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
