#!/usr/bin/env python3
"""Direct scientific-content, structural-math, diagram, generated-LaTeX, and rendered-PDF
parity verifier for AOD M4 Phase 2 (Typst primary publication + generated LaTeX compatibility
vs the immutable 98ddfa0 historical LaTeX baseline).

Enforces all five verification gates:
  Gate A: Historical 98ddfa0 baseline immutability (211 protected scientific files: 41 archived
          byte-for-byte under archive/latex_baseline_98ddfa0/ and 170 preserved in-place) plus
          representation-only contract change ledger verification.
  Gate A2: Evaluation policy. Manifest typst_sha256 enforced for all 48 units + 4 shared diagram
          components; template and driver files pinned by verifier-internal digests; no undeclared
          .typ files; mode-aware allowlist over content files and diagram components.
  Gate B: Complete ordered source-bound content parity across all 48 active files against the
          materialized 98ddfa0 baseline AND generated latex/ compatibility verification (include
          graph, 7 immutable tables, 218 labeled equations, 455+227 labels, 4 exported vector
          diagram PDFs, and typ2tex --check freshness).
  Gate C: Evaluated & rendered PDF parity:
          - Deterministic Typst build (--creation-timestamp) producing canonical main.pdf and
            manual.pdf with strict committed registry.
          - Delivered peer-PDF link integrity (main.pdf#page=N, zero stale/wrong peer links,
            SHA-256 peer identity, and 172/172 exact target-page anchor landings).
          - Exact numbered block-equation count, per-label equation/Table/Figure/Heading numbers,
            clickable external /URI set, inline citation sequence, case-sensitive bibliography,
            prose clause count parity, insertion detection, glyph parity, decimals, and PDF
            text-paint scan against historical 98ddfa0 XeLaTeX baseline PDFs.
          - Optional generated-LaTeX PDF verification (--generated-latex-main-pdf /
            --generated-latex-manual-pdf) against the historical baseline PDFs + sibling peer links.
  Gate D: Mandatory negative controls (29 isolated mutations), each rejected by its intended check.
  Gate E: Honest coverage, cryptographic bindings, and explicit non-acceptance verdict on partial
          runs.

Uses no bare `assert` statements so normal (`python3`) and optimized (`python3 -O`)
invocations execute identical checks and emit byte-identical JSON reports.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]

SCIENTIFIC_BASELINE_COMMIT = "98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3"
PHASE1_ACCEPTED_COMMIT = "e6f20970c8ac63713c112000e3fe83b9695c7ffc"
PHASE1_ACCEPTED_TREE = "b4df64481b4f1d53b7b2d0fff1c0fd29ab007659"
PHASE1_ORIGIN_INVENTORY_REL = "archive/phase1_e6f2097/PHASE1_ORIGIN_INVENTORY.json"
PHASE1_ORIGIN_INVENTORY_SHA256 = "728df1ba649ba779e8583485ac95ff8927cbec21ddb169b09ef2cae9fd00d60f"

# Bounded R2 generated-LaTeX spacing/unit boundary checks (surface_rel, required_substring, forbidden_glued)
REQUIRED_GENERATED_TEX_BOUNDARIES = (
    ("sections/05_curl_closure_duon_current.tex", r"\mathrm{Duon}\ \text{has the support of }", r"\mathrm{Duon}\text{has"),
    ("sections/08_awareness_learning_mindfulness.tex", r"R_e\ \text{is valid}", r"R_e\text{is valid}"),
    ("appendices/B_curling_curls.tex", r"\mathrm{tetron}\ \text{is the }E_4\text{ enclosure of }", r"\mathrm{tetron}\text{is the"),
    ("manual/appendices/B_quarantined_external_comparison.tex", r"10^{-10}\,\mathrm{J}", r"10^{-10}\mathrm{J}"),
)

# Bounded R3 generated-LaTeX source heading checks (surface_rel, required_texorpdfstring_substring, forbidden_raw_heading)
REQUIRED_GENERATED_TEX_BOOKMARKS = (
    ("sections/06_field.tex", r"\subsubsection{E2\texorpdfstring{$^{\pm}$}{±} duad}", r"\subsubsection{E2$^{\pm}$ duad}"),
    ("appendices/J_ao_field_fractal_properties.tex", r"\section{A\texorpdfstring{$\leftrightarrow\Omega$}{<->Omega} Field Fractal Properties}", r"\section{A$\leftrightarrow\Omega$ Field Fractal Properties}"),
    ("manual/sections/01_rest_energy_prediction.tex", r"\subsection{A\texorpdfstring{$\Omega$}{Omega} field-map table}", r"\subsection{A$\Omega$ field-map table}"),
    ("manual/sections/06_field_dynamics_applications.tex", r"\subsection{3D Brownian phase-cycle \texorpdfstring{$\delta_3$}{delta3} fixture}", r"\subsection{3D Brownian phase-cycle $\delta_3$ fixture}"),
    ("manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex", r"\section{3D coordinate phase-cycle \texorpdfstring{$\delta_3$}{delta3} fixture specification}", r"\section{3D coordinate phase-cycle $\delta_3$ fixture specification}"),
    ("manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.tex", r"\subsection{AFC/A\texorpdfstring{$\Omega$}{Omega}D mapping}", r"\subsection{AFC/A$\Omega$D mapping}"),
)

# Bounded R3 restored mathematical bookmark titles (must appear; symbol-stripped counterparts must not)
REQUIRED_PDF_BOOKMARK_TITLES = {
    "main": (
        ("E2\u00b1 duad", ("E2 duad",)),
        ("A<->Omega Field Fractal Properties", ("A Field Fractal Properties",)),
    ),
    "manual": (
        ("AOmega field-map table", ("A field-map table",)),
        ("3D Brownian phase-cycle delta3 fixture", ("3D Brownian phase-cycle 3 fixture", "3D Brownian phase-cycle fixture")),
        ("3D coordinate phase-cycle delta3 fixture specification", ("3D coordinate phase-cycle 3 fixture specification", "3D coordinate phase-cycle fixture specification")),
        ("AFC/AOmegaD mapping", ("AFC/AD mapping",)),
    ),
}

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
    "cycle_shedding_summary.tex",
)
SCIENTIFIC_QUALIFIERS = (
    "no", "not", "never", "only", "without", "unless", "none", "cannot",
    "neither", "nor", "conditional", "scoped", "quarantined", "declared",
    "unresolved", "absent", "distinct", "independent", "external",
    "immutable", "falsification", "necessary", "sufficient",
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


# =============================================================================
# Comment stripping & balanced delimiter scanning (linear time)
# =============================================================================

def strip_tex_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def strip_typst_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
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


def read_balanced_group(s: str, pos: int, op: str = "{", cl: str = "}") -> tuple[str, int]:
    """Read a balanced group; ignore delimiters inside `"..."` for `(...)` calls and inside `$...$` for `(...)`/`[...]`."""
    while pos < len(s) and s[pos] in " \t\n\r":
        pos += 1
    require(pos < len(s) and s[pos] == op, f"Expected {op!r} at {pos}")
    depth = 0
    start = pos + 1
    i = pos
    in_str = False
    in_math = False
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if op == "(" and not in_math and s[i] == '"':
            in_str = not in_str
            i += 1
            continue
        if op in ("(", "[") and not in_str and s[i] == "$":
            in_math = not in_math
            i += 1
            continue
        if not in_str and not in_math:
            if s[i] == op:
                depth += 1
            elif s[i] == cl:
                depth -= 1
                if depth == 0:
                    return s[start:i], i + 1
        i += 1
    raise ValueError(f"Unclosed {op!r}")


def parse_typ_str_lit(s: str, pos: int) -> tuple[str, int]:
    require(pos < len(s) and s[pos] == '"', f"Expected string literal at {pos}")
    j = pos + 1
    buf: list[str] = []
    while j < len(s):
        if s[j] == "\\" and j + 1 < len(s):
            buf.append(s[j + 1])
            j += 2
            continue
        if s[j] == '"':
            return "".join(buf), j + 1
        buf.append(s[j])
        j += 1
    raise ValueError("Unclosed Typst string literal")


def norm_prose_typography(text: str) -> str:
    """Declared typography-only normalization for prose (never applied to literal code/commands)."""
    t = unicodedata.normalize("NFKC", text)
    for src, dst in (
        ("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'"),
        ("\u2014", "-"), ("\u2013", "-"), ("\u2212", "-"),
        ("\u00a0", " "), ("\u2009", " "), ("\u2004", " "),
        ("---", "-"), ("--", "-"), ("``", '"'), ("''", '"'),
    ):
        t = t.replace(src, dst)
    return t


# =============================================================================
# Bounded Recursive-Descent Math AST Parsers (LaTeX & Typst -> Canonical AST)
# Preserves explicit grouping, fractions, roots, accents, scripts, numbers,
# operators, symbols, and matrix/cases shape. Fail-closed on unknown macros.
# =============================================================================

TEX_MATH_SPACE = {
    "quad", "qquad", ",", ";", ":", "!", " ", "enspace", "thinspace", "medspace", "thickspace",
    "displaystyle", "textstyle", "scriptstyle", "scriptscriptstyle", "limits", "nolimits",
    "notag", "nonumber", "allowdisplaybreaks", "big", "Big", "bigg", "Bigg",
    "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr", "Biggl", "Biggr",
    "bigm", "Bigm", "left", "right", "middle", "cr", "newline", "hfill", "phantom",
    "mathstrut", "strut", "vphantom", "hphantom", "smash", "mathclap", "substack",
    "boldmath", "relax", "allowbreak",
}
TYP_MATH_SPACE = {
    "quad", "wide", "thin", "med", "thick", "space", "display", "inline", "limits", "scripts",
    "stretch", "size", "bold", "italic",
}

NAMED_OPERATORS = {
    "Re", "Im", "Tr", "tr", "det", "dim", "ker", "im", "deg", "min", "max", "sup", "inf",
    "arg", "argmin", "argmax", "log", "ln", "exp", "sin", "cos", "tan", "arctan",
    "sgn", "sign", "supp", "span", "card", "rank", "diag", "mod", "gcd", "lcm", "lim", "Pr",
}

TEX_MATH_SYMS = {
    "to": "->", "rightarrow": "->", "longrightarrow": "->", "mapsto": "|->", "longmapsto": "|->",
    "leftrightarrow": "<->", "longleftrightarrow": "<->", "Leftrightarrow": "<=>", "Longleftrightarrow": "<=>", "iff": "<=>",
    "Rightarrow": "=>", "Longrightarrow": "=>", "nRightarrow": "not=>", "implies": "=>",
    "leftarrow": "<-", "longleftarrow": "<-", "Leftarrow": "<=",
    "uparrow": "up", "downarrow": "down", "Downarrow": "Down", "Uparrow": "Up",
    "leadsto": "~>", "rightsquigarrow": "~>",
    "hookrightarrow": "hook->", "twoheadrightarrow": "->>",
    "equiv": "==", "neq": "!=", "ne": "!=", "le": "<=", "leq": "<=", "ge": ">=", "geq": ">=",
    "nleq": "not<=", "ngeq": "not>=",
    "approx": "approx", "sim": "sim", "simeq": "simeq", "cong": "cong", "propto": "propto", "asymp": "asymp",
    "ll": "<<", "gg": ">>", "prec": "prec", "succ": "succ", "preceq": "preceq", "succeq": "succeq",
    "in": "in", "notin": "notin", "ni": "ni", "subset": "subset", "subseteq": "subseteq",
    "subsetneq": "subsetneq", "supset": "supset", "supseteq": "supseteq",
    "cup": "cup", "cap": "cap", "sqcup": "sqcup",
    "bigcup": "bigcup", "bigcap": "bigcap", "bigsqcup": "bigsqcup", "setminus": "setminus",
    "emptyset": "emptyset", "varnothing": "emptyset",
    "times": "times", "cdot": "cdot", "cdots": "dots", "dots": "dots", "ldots": "dots", "vdots": "vdots", "ddots": "ddots",
    "pm": "pm", "mp": "mp", "circ": "circ", "bullet": "bullet", "star": "star", "ast": "*",
    "oplus": "oplus", "otimes": "otimes", "odot": "odot", "bigoplus": "bigoplus", "bigotimes": "bigotimes",
    "bowtie": "bowtie", "Join": "bowtie", "wr": "wr", "checkmark": "check",
    "Box": "square", "square": "square",
    "wedge": "wedge", "vee": "vee", "land": "wedge", "lor": "vee", "neg": "neg", "lnot": "neg",
    "vdash": "|-", "models": "|=",
    "sum": "sum", "prod": "prod", "int": "int", "oint": "oint",
    "partial": "partial", "nabla": "nabla", "forall": "forall", "exists": "exists",
    "infty": "infty", "perp": "perp", "parallel": "parallel", "mid": "|", "colon": ":",
    "det": "det", "tr": "tr", "Tr": "Tr", "dim": "dim", "ker": "ker", "im": "im", "deg": "deg",
    "min": "min", "max": "max", "sup": "sup", "inf": "inf", "arg": "arg", "argmin": "argmin", "argmax": "argmax",
    "log": "log", "ln": "ln", "exp": "exp", "sin": "sin", "cos": "cos", "tan": "tan", "arctan": "arctan",
    "sgn": "sgn", "sign": "sign", "supp": "supp", "span": "span", "card": "card", "rank": "rank", "diag": "diag",
    "mod": "mod", "bmod": "mod", "pmod": "mod", "gcd": "gcd", "lcm": "lcm", "lim": "lim", "Pr": "Pr",
    "ell": "ell", "hbar": "hbar", "Re": "Re", "Im": "Im", "aleph": "aleph", "wp": "wp",
    "prime": "'", "dagger": "dagger", "top": "top", "bot": "bot", "angle": "angle", "triangle": "triangle",
    "backslash": "setminus", "S": "section", "degree": "circ",
    "lvert": "|", "rvert": "|", "vert": "|", "lVert": "||", "rVert": "||", "Vert": "||",
    "langle": "angle.l", "rangle": "angle.r", "lfloor": "floor.l", "rfloor": "floor.r",
    "lceil": "ceil.l", "rceil": "ceil.r",
    "coloneqq": ":=", "eqqcolon": "=:",
    # Greek (preserving accepted Tau / pi / Pi / Phi / Omega / Delta / delta / iota roles)
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta",
    "epsilon": "epsilon", "varepsilon": "epsilon", "zeta": "zeta", "eta": "eta",
    "theta": "theta", "vartheta": "theta", "iota": "iota", "kappa": "kappa",
    "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi", "pi": "pi", "varpi": "pi",
    "rho": "rho", "varrho": "rho", "sigma": "sigma", "varsigma": "sigma", "tau": "tau",
    "upsilon": "upsilon", "phi": "phi", "varphi": "phi", "chi": "chi", "psi": "psi", "omega": "omega",
    "Gamma": "Gamma", "Delta": "Delta", "Theta": "Theta", "Lambda": "Lambda",
    "Xi": "Xi", "Pi": "Pi", "Sigma": "Sigma", "Upsilon": "Upsilon", "Phi": "Phi", "Psi": "Psi", "Omega": "Omega",
    # AOD declared preamble macros (exact 1-to-1)
    "Null": "AOD:Null", "NullPot": "AOD:Null", "AODNull": "AOD:Null", "infD": "AOD:infD",
    "DistSet": "AOD:DistSet", "RelSet": "AOD:RelSet",
    "Qfour": "AOD:Qfour", "AO": "AOD:AO", "Qext": "AOD:Qext",
    "SADAR": "AOD:SADAR", "ADAR": "AOD:ADAR", "RCD": "AOD:RCD",
    "SADARop": "AOD:SADARop", "ADARop": "AOD:ADARop", "RCDop": "AOD:RCDop",
    "AoD": "AOD:AoD", "AFC": "AOD:AFC", "AOm": "AOD:AOm",
}

TYP_MATH_SYMS = {
    "arrow.r": "->", "arrow.r.long": "->", "arrow.r.bar": "|->", "arrow.r.long.bar": "|->",
    "arrow.l.r": "<->", "arrow.l.r.long": "<->", "arrow.l.r.double": "<=>", "arrow.l.r.double.long": "<=>",
    "arrow.r.double": "=>", "arrow.r.double.long": "=>", "arrow.r.double.not": "not=>",
    "arrow.l": "<-", "arrow.l.long": "<-", "arrow.l.double": "<=",
    "arrow.t": "up", "arrow.b": "down", "arrow.b.double": "Down", "arrow.t.double": "Up",
    "arrow.r.squiggly": "~>", "arrow.r.hook": "hook->", "arrow.r.twohead": "->>",
    "equiv": "==", "eq.not": "!=", "lt.eq": "<=", "gt.eq": ">=",
    "lt.eq.not": "not<=", "gt.eq.not": "not>=",
    "approx": "approx", "tilde.op": "sim", "tilde.eq": "simeq", "tilde.equiv": "cong", "prop": "propto", "asymp": "asymp",
    "lt.double": "<<", "gt.double": ">>", "prec": "prec", "succ": "succ", "prec.eq": "preceq", "succ.eq": "succeq",
    "in": "in", "in.not": "notin", "in.rev": "ni", "subset": "subset", "subset.eq": "subseteq",
    "subset.neq": "subsetneq", "supset": "supset", "supset.eq": "supseteq",
    "union": "cup", "inter": "cap", "union.sq": "sqcup",
    "union.big": "bigcup", "inter.big": "bigcap", "union.sq.big": "bigsqcup", "without": "setminus",
    "emptyset": "emptyset",
    "times": "times", "dot.op": "cdot", "dots.c": "dots", "dots.h": "dots", "dots": "dots", "dots.v": "vdots", "dots.down": "ddots",
    "plus.minus": "pm", "minus.plus": "mp", "circle.small": "circ", "circle.tiny": "circ", "compose": "circ",
    "bullet": "bullet", "star.op": "star", "star": "star", "ast.op": "*",
    "plus.o": "oplus", "times.o": "otimes", "dot.o": "odot", "plus.o.big": "bigoplus", "times.o.big": "bigotimes",
    "bowtie": "bowtie", "join": "bowtie", "checkmark": "check",
    "square.stroked": "square", "square": "square",
    "and": "wedge", "or": "vee", "not": "neg",
    "tack.r": "|-", "tack.r.double": "|=",
    "sum": "sum", "product": "prod", "integral": "int", "integral.cont": "oint",
    "partial": "partial", "nabla": "nabla", "forall": "forall", "exists": "exists",
    "infinity": "infty", "perp": "perp", "parallel": "parallel",
    "det": "det", "tr": "tr", "Tr": "Tr", "dim": "dim", "ker": "ker", "im": "im", "deg": "deg",
    "min": "min", "max": "max", "sup": "sup", "inf": "inf", "arg": "arg", "argmin": "argmin", "argmax": "argmax",
    "log": "log", "ln": "ln", "exp": "exp", "sin": "sin", "cos": "cos", "tan": "tan", "arctan": "arctan",
    "sgn": "sgn", "sign": "sign", "supp": "supp", "span": "span", "card": "card", "rank": "rank", "diag": "diag",
    "mod": "mod", "gcd": "gcd", "lcm": "lcm", "lim": "lim", "Pr": "Pr",
    "ell": "ell", "planck.reduce": "hbar", "Re": "Re", "Im": "Im", "aleph": "aleph",
    "dagger": "dagger", "top": "top", "bot": "bot", "angle": "angle", "triangle": "triangle", "slash": "/",
    "section": "section", "bar.v": "|", "bar.v.double": "||",
    "chevron.l": "angle.l", "chevron.r": "angle.r", "floor.l": "floor.l", "floor.r": "floor.r",
    "ceil.l": "ceil.l", "ceil.r": "ceil.r",
    "paren.l": "(", "paren.r": ")", "bracket.l": "[", "bracket.r": "]", "brace.l": "{", "brace.r": "}",
    "eq.colon": "=:", "colon.eq": ":=", "dif": "d",
    "epsilon.alt": "epsilon", "phi.alt": "phi", "theta.alt": "theta", "rho.alt": "rho", "sigma.alt": "sigma", "pi.alt": "pi",
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta",
    "epsilon": "epsilon", "zeta": "zeta", "eta": "eta", "theta": "theta", "iota": "iota", "kappa": "kappa",
    "lambda": "lambda", "mu": "mu", "nu": "nu", "xi": "xi", "pi": "pi", "rho": "rho",
    "sigma": "sigma", "tau": "tau", "upsilon": "upsilon", "phi": "phi", "chi": "chi", "psi": "psi", "omega": "omega",
    "Gamma": "Gamma", "Delta": "Delta", "Theta": "Theta", "Lambda": "Lambda",
    "Xi": "Xi", "Pi": "Pi", "Sigma": "Sigma", "Upsilon": "Upsilon", "Phi": "Phi", "Psi": "Psi", "Omega": "Omega",
    # AOD declared schema macros (exact 1-to-1)
    "Null": "AOD:Null", "NullPot": "AOD:Null", "AODNull": "AOD:Null", "infD": "AOD:infD",
    "DistSet": "AOD:DistSet", "RelSet": "AOD:RelSet",
    "Qfour": "AOD:Qfour", "AO": "AOD:AO", "Qext": "AOD:Qext",
    "SADAR": "AOD:SADAR", "ADAR": "AOD:ADAR", "RCD": "AOD:RCD",
    "SADARop": "AOD:SADARop", "ADARop": "AOD:ADARop", "RCDop": "AOD:RCDop",
    "AoD": "AOD:AoD", "AFC": "AOD:AFC", "AOm": "AOD:AOm",
}

FONT_MAP_TEX = {
    "mathrm": "text", "text": "text", "textrm": "text", "hbox": "text",
    "operatorname": "op", "operatorname*": "op",
    "mathsf": "text", "textbf": "text", "texttt": "text", "mathtt": "text", "tt": "text",
    "mathbf": "bf", "boldsymbol": "bf", "bm": "bf",
    "mathcal": "cal", "mathscr": "cal", "mathbb": "bb", "mathfrak": "frak",
    "mathit": "it",
}
FONT_MAP_TYP = {
    "upright": "text", "op": "op", "sans": "text", "mono": "text", "bold": "bf",
    "cal": "cal", "bb": "bb", "frak": "frak", "italic": "it",
}
ACCENT_TEX = {
    "hat": "hat", "widehat": "hat", "bar": "bar", "overline": "overline",
    "tilde": "tilde", "widetilde": "tilde", "vec": "vec", "dot": "dot", "ddot": "ddot",
    "underline": "underline", "cancel": "cancel",
    "overbrace": "overbrace", "underbrace": "underbrace", "mathring": "ring",
}
ACCENT_TYP = {
    "hat": "hat", "macron": "bar", "overline": "overline", "tilde": "tilde", "arrow": "vec",
    "dot": "dot", "dot.double": "ddot", "underline": "underline", "cancel": "cancel",
    "overbrace": "overbrace", "underbrace": "underbrace", "circle": "ring",
}


def _norm_math_text(s: str) -> str:
    s = s.replace(r"\,", " ").replace(r"\;", " ").replace(r"\ ", " ")
    s = s.replace(r"\_", "_").replace(r"\-", "-").replace(r"\%", "%").replace(r"\&", "&").replace("~", " ")
    s = s.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()


def _attach_scripts(base, sub=None, sup=None):
    if sub is not None and sup is not None:
        return ("subsup", base, sub, sup)
    if sub is not None:
        return ("sub", base, sub)
    if sup is not None:
        return ("sup", base, sup)
    return base


def _make_seq(items: list) -> tuple:
    flat = []
    for x in items:
        if x is None:
            continue
        if isinstance(x, tuple) and x[0] == "seq":
            flat.extend(x[1])
        else:
            flat.append(x)

    def pair_delims(lst, open_tok, close_tok, kind):
        def unwrap_close(tok):
            if tok == close_tok:
                return True, None, None
            if isinstance(tok, tuple) and len(tok) >= 3 and tok[1] == close_tok:
                if tok[0] == "sub":
                    return True, tok[2], None
                if tok[0] == "sup":
                    return True, None, tok[2]
                if tok[0] == "subsup":
                    return True, tok[2], tok[3]
            return False, None, None

        out = []
        i = 0
        while i < len(lst):
            if lst[i] == open_tok:
                depth = 1
                j = i + 1
                c_sub = c_sup = None
                while j < len(lst) and depth > 0:
                    if lst[j] == open_tok:
                        depth += 1
                    else:
                        is_cl, s1, s2 = unwrap_close(lst[j])
                        if is_cl:
                            depth -= 1
                            if depth == 0:
                                c_sub, c_sup = s1, s2
                    j += 1
                if depth == 0:
                    inner = _make_seq(lst[i + 1:j - 1])
                    out.append(_attach_scripts(("group", kind, inner), c_sub, c_sup))
                    i = j
                    continue
            out.append(lst[i])
            i += 1
        return out

    flat = pair_delims(flat, ("sym", "angle.l"), ("sym", "angle.r"), "angle")
    flat = pair_delims(flat, ("sym", "floor.l"), ("sym", "floor.r"), "floor")
    flat = pair_delims(flat, ("sym", "ceil.l"), ("sym", "ceil.r"), "ceil")
    flat = pair_delims(flat, ("op", "{"), ("op", "}"), "{")
    flat = pair_delims(flat, ("op", "("), ("op", ")"), "(")
    flat = pair_delims(flat, ("op", "["), ("op", "]"), "[")

    merged = []
    i = 0
    while i < len(flat):
        if i + 1 < len(flat) and flat[i] == ("op", ":") and flat[i + 1] == ("op", "="):
            merged.append(("op", ":="))
            i += 2
        elif i + 1 < len(flat) and flat[i] == ("op", "=") and flat[i + 1] == ("op", ":"):
            merged.append(("op", "=:"))
            i += 2
        elif (
            i + 1 < len(flat)
            and isinstance(flat[i], tuple) and flat[i][0] == "text"
            and isinstance(flat[i + 1], tuple) and flat[i + 1][0] == "text"
        ):
            # Merge adjacent upright unit segments (e.g. upright("MeV") thin upright("s") == \mathrm{MeV\,s})
            merged.append(("text", flat[i][1] + " " + flat[i + 1][1]))
            i += 2
        else:
            merged.append(flat[i])
            i += 1
    if len(merged) == 1:
        return merged[0]
    return ("seq", tuple(merged))


def _normalize_ast(node):
    if not isinstance(node, tuple):
        return node
    tag = node[0]
    if tag == "seq":
        return _make_seq([_normalize_ast(x) for x in node[1]])
    if tag == "text" and node[1] in NAMED_OPERATORS:
        return ("sym", node[1])
    if tag == "not":
        inner = _normalize_ast(node[1])
        if inner == ("op", "=>"):
            return ("sym", "not=>")
        if inner == ("op", "="):
            return ("op", "!=")
        if inner == ("sym", "in"):
            return ("sym", "notin")
        return ("not", inner)
    if tag == "group":
        return ("group", node[1], _normalize_ast(node[2]))
    if tag == "font":
        return ("font", node[1], _normalize_ast(node[2]))
    if tag in ("sub", "sup"):
        return (tag, _normalize_ast(node[1]), _normalize_ast(node[2]))
    if tag == "subsup":
        return ("subsup", _normalize_ast(node[1]), _normalize_ast(node[2]), _normalize_ast(node[3]))
    if tag in ("frac", "binom", "root", "overset", "underset"):
        return (tag, _normalize_ast(node[1]), _normalize_ast(node[2]))
    if tag in ("sqrt", "boxed"):
        return (tag, _normalize_ast(node[1]))
    if tag == "accent":
        return ("accent", node[1], _normalize_ast(node[2]))
    if tag == "arrow_labeled":
        return ("arrow_labeled", node[1], _normalize_ast(node[2]))
    if tag == "cases":
        return ("cases", tuple(tuple(_normalize_ast(c) for c in r) for r in node[1]))
    if tag == "matrix":
        return ("matrix", node[1], node[2], tuple(tuple(_normalize_ast(c) for c in r) for r in node[3]))
    return node


TEX_MATRIX_DELIMS: dict[str, str | None] = {
    "pmatrix": "(",
    "bmatrix": "[",
    "vmatrix": "|",
    "Bmatrix": "{",
    "matrix": None,
    "smallmatrix": None,
    "array": None,
}


def _parse_latex_array_augment(col_spec: str) -> int | tuple[int, ...] | None:
    """Return column index (or tuple of indices) of vertical rule(s) `|` in LaTeX array col_spec."""
    bars: list[int] = []
    col_idx = 0
    i = 0
    n = len(col_spec)
    while i < n:
        c = col_spec[i]
        if c in " \t\n\r":
            i += 1
        elif c == "|":
            bars.append(col_idx)
            i += 1
        elif c in "lcr":
            col_idx += 1
            i += 1
        elif c in "pbm@><!":
            _, i = read_balanced_group(col_spec, i + 1, "{", "}")
            if c in "pbm":
                col_idx += 1
        else:
            i += 1
    if not bars:
        return None
    return bars[0] if len(bars) == 1 else tuple(bars)


class TexMathParser:
    def __init__(self, s: str):
        s = re.sub(r"\\label\{[^}]+\}", "", s)
        s = re.sub(r"\\tag\{[^}]+\}", "", s)
        s = re.sub(r"\\begin\{(?:split|aligned|gathered)\}(?:\[[^\]]*\])?", "", s)
        s = re.sub(r"\\end\{(?:split|aligned|gathered)\}", "", s)
        s = re.sub(r"\\(?:hspace|vspace|mkern|mskip|kern)\*?\{[^}]*\}", "", s)
        s = re.sub(r"\\(?:left|right)\.", "", s)
        s = re.sub(r"\{\\(?:rm|tt|sf|bf)\s+([^{}]+)\}", lambda m: r"\mathrm{" + m.group(1) + "}", s)
        self.s = s
        self.n = len(s)
        self.i = 0
        self.unsupported: list[str] = []

    def skip_ws(self) -> None:
        while self.i < self.n and self.s[self.i] in " \t\n\r":
            self.i += 1

    def parse_seq(self, stop_tokens: tuple[str, ...] = ()) -> tuple:
        items = []
        while True:
            self.skip_ws()
            if self.i >= self.n:
                break
            if any(self.s.startswith(st, self.i) for st in stop_tokens):
                break
            if self.s[self.i] == "&" and "&" not in stop_tokens:
                self.i += 1
                continue
            if self.s.startswith(r"\\", self.i) and r"\\" not in stop_tokens:
                self.i += 2
                self.skip_ws()
                if self.i < self.n and self.s[self.i] == "[":
                    eb = self.s.find("]", self.i)
                    if eb >= 0:
                        self.i = eb + 1
                continue
            atom = self.parse_scripted(stop_tokens)
            if atom is not None:
                items.append(atom)
        return _normalize_ast(_make_seq(items))

    def parse_scripted(self, stop_tokens: tuple[str, ...] = ()):
        base = self.parse_atom(stop_tokens)
        if base is None:
            return None
        sub = None
        sup = None
        primes = 0
        while True:
            self.skip_ws()
            if self.i >= self.n:
                break
            if self.s[self.i] == "'":
                primes += 1
                self.i += 1
            elif self.s[self.i] == "_":
                self.i += 1
                sub = self.parse_arg()
            elif self.s[self.i] == "^":
                self.i += 1
                sup = self.parse_arg()
            else:
                break
        if primes:
            p_node = ("sym", "'" * primes)
            sup = _make_seq([sup, p_node]) if sup is not None else p_node
        return _attach_scripts(base, sub, sup)

    def parse_arg(self):
        self.skip_ws()
        if self.i >= self.n:
            return ("seq", ())
        if self.s[self.i] == "{":
            self.i += 1
            inner = self.parse_seq(stop_tokens=("}",))
            if self.i < self.n and self.s[self.i] == "}":
                self.i += 1
            return inner
        # TeX unbraced macro argument rule: \frac14 takes single token '1' then '4'
        if self.s[self.i].isdigit():
            ch = self.s[self.i]
            self.i += 1
            return ("num", ch)
        return self.parse_atom(()) or ("seq", ())

    def read_raw_brace_text(self) -> str:
        self.skip_ws()
        if self.i < self.n and self.s[self.i] != "{":
            ch = self.s[self.i]
            self.i += 1
            return ch
        if self.i < self.n and self.s[self.i] == "{":
            depth = 0
            start = self.i + 1
            while self.i < self.n:
                if self.s[self.i] == "\\" and self.i + 1 < self.n:
                    self.i += 2
                    continue
                if self.s[self.i] == "{":
                    depth += 1
                elif self.s[self.i] == "}":
                    depth -= 1
                    if depth == 0:
                        res = self.s[start:self.i]
                        self.i += 1
                        return res
                self.i += 1
        return ""

    def parse_atom(self, stop_tokens: tuple[str, ...] = ()):
        self.skip_ws()
        if self.i >= self.n:
            return None
        c = self.s[self.i]
        if c == "{":
            self.i += 1
            inner = self.parse_seq(stop_tokens=("}",))
            if self.i < self.n and self.s[self.i] == "}":
                self.i += 1
            return inner
        if c == "(":
            self.i += 1
            inner = self.parse_seq(stop_tokens=(")",))
            if self.i < self.n and self.s[self.i] == ")":
                self.i += 1
                return ("group", "(", inner)
            return _make_seq([("op", "("), inner])
        if c == "[":
            self.i += 1
            inner = self.parse_seq(stop_tokens=("]",))
            if self.i < self.n and self.s[self.i] == "]":
                self.i += 1
                return ("group", "[", inner)
            return _make_seq([("op", "["), inner])
        if c in ")]}":
            self.i += 1
            return ("op", c)
        if c.isdigit():
            m = re.match(r"\d+(?:\.\d+)?", self.s[self.i:])
            self.i += m.end()
            return ("num", m.group(0))
        if c.isalpha():
            self.i += 1
            return ("sym", c)
        if c in "^_":
            self.i += 1
            arg = self.parse_arg()
            return ("sup" if c == "^" else "sub", ("empty",), arg)
        if c in "+-=<>/*|,;:!?~.":
            self.i += 1
            return ("op", c)
        if c == "\\":
            self.i += 1
            if self.i >= self.n:
                return None
            if not self.s[self.i].isalpha():
                ch = self.s[self.i]
                self.i += 1
                if ch in ",;:! \n\t\r":
                    return None
                if ch == "{":
                    return ("op", "{")
                if ch == "}":
                    return ("op", "}")
                if ch == "|":
                    return ("op", "||")
                if ch in "%_$&#":
                    return ("sym", ch)
                return ("op", ch)
            m = re.match(r"[A-Za-z]+\*?", self.s[self.i:])
            cmd = m.group(0)
            self.i += m.end()
            if cmd in TEX_MATH_SPACE:
                return None
            if cmd == "begin":
                env = self.read_raw_brace_text()
                return self.parse_env(env)
            if cmd in ("frac", "dfrac", "tfrac", "cfrac"):
                return ("frac", self.parse_arg(), self.parse_arg())
            if cmd == "binom":
                return ("binom", self.parse_arg(), self.parse_arg())
            if cmd == "sqrt":
                self.skip_ws()
                idx = None
                if self.i < self.n and self.s[self.i] == "[":
                    self.i += 1
                    idx = self.parse_seq(stop_tokens=("]",))
                    if self.i < self.n and self.s[self.i] == "]":
                        self.i += 1
                arg = self.parse_arg()
                return ("root", idx, arg) if idx is not None else ("sqrt", arg)
            if cmd in ACCENT_TEX:
                return ("accent", ACCENT_TEX[cmd], self.parse_arg())
            if cmd == "boxed":
                return ("boxed", self.parse_arg())
            if cmd in FONT_MAP_TEX:
                role = FONT_MAP_TEX[cmd]
                if role in ("text", "op"):
                    raw = self.read_raw_brace_text()
                    if role == "op" and ("\\" in raw and not re.fullmatch(r"[A-Za-z0-9_\\\- ]+", raw)):
                        subp = TexMathParser(raw)
                        res = subp.parse_seq()
                        self.unsupported.extend(subp.unsupported)
                        return res
                    # Normalize inline math snippets inside \text{...} (e.g. \(\Omega\), \(\delta_3\))
                    cleaned = re.sub(r"\\(?:text|mathrm|textbf|texttt)\{([^}]*)\}", r"\1", raw)
                    cleaned = re.sub(r"\\\(\\([A-Za-z]+)(?:_([0-9A-Za-z]+))?\\\)", lambda mm: mm.group(1) + (f"_{mm.group(2)}" if mm.group(2) else ""), cleaned)
                    cleaned = _norm_math_text(cleaned)
                    if cleaned == "":
                        return None
                    return ("text", cleaned)
                return ("font", role, self.parse_arg())
            if cmd == "not":
                return ("not", self.parse_atom(stop_tokens))
            if cmd == "xrightarrow":
                self.skip_ws()
                if self.i < self.n and self.s[self.i] == "[":
                    eb = self.s.find("]", self.i)
                    if eb >= 0:
                        self.i = eb + 1
                return ("arrow_labeled", "->", self.parse_arg())
            if cmd in ("overset", "underset"):
                return (cmd, self.parse_arg(), self.parse_arg())
            if cmd in ("eqref", "ref", "eqnref", "secref", "mainequation"):
                return ("ref", self.read_raw_brace_text())
            if cmd in TEX_MATH_SYMS:
                val = TEX_MATH_SYMS[cmd]
                return ("sym", val) if val[0].isalpha() else ("op", val)
            self.unsupported.append(f"\\{cmd}")
            return ("UNSUPPORTED_TEX", cmd)
        self.i += 1
        return ("sym", c)

    def parse_env(self, env: str):
        end_tag = f"\\end{{{env}}}"
        if env in ("cases", "dcases", "pmatrix", "bmatrix", "vmatrix", "matrix", "Bmatrix", "smallmatrix", "array"):
            augment = _parse_latex_array_augment(self.read_raw_brace_text()) if env == "array" else None
            kind = "cases" if env in ("cases", "dcases") else "matrix"
            delim = TEX_MATRIX_DELIMS.get(env)
            rows = []
            while self.i < self.n and not self.s.startswith(end_tag, self.i):
                row_parts = []
                while self.i < self.n and not self.s.startswith(end_tag, self.i) and not self.s.startswith(r"\\", self.i):
                    cell = self.parse_seq(stop_tokens=("&", r"\\", end_tag))
                    row_parts.append(cell)
                    if self.s.startswith("&", self.i):
                        self.i += 1
                if row_parts and not (len(row_parts) == 1 and row_parts[0] == ("seq", ())):
                    rows.append(tuple(row_parts))
                if self.s.startswith(r"\\", self.i):
                    self.i += 2
                    self.skip_ws()
                    if self.i < self.n and self.s[self.i] == "[":
                        eb = self.s.find("]", self.i)
                        if eb >= 0:
                            self.i = eb + 1
            if self.s.startswith(end_tag, self.i):
                self.i += len(end_tag)
            if kind == "cases":
                return ("cases", tuple(rows))
            return ("matrix", delim, augment, tuple(rows))
        end_idx = self.s.find(end_tag, self.i)
        if end_idx >= 0:
            self.i = end_idx + len(end_tag)
        self.unsupported.append(f"env:{env}")
        return ("UNSUPPORTED_ENV", env)


class TypMathParser:
    def __init__(self, s: str):
        self.s = s
        self.n = len(s)
        self.i = 0
        self.unsupported: list[str] = []

    def skip_ws(self) -> None:
        while self.i < self.n and self.s[self.i] in " \t\n\r":
            self.i += 1

    def parse_seq(self, stop_chars: tuple[str, ...] = ()) -> tuple:
        items = []
        while True:
            self.skip_ws()
            if self.i >= self.n:
                break
            if self.s[self.i] in stop_chars:
                break
            if self.s[self.i] == "&" and "&" not in stop_chars:
                self.i += 1
                continue
            if self.s[self.i] == "\\" and (self.i + 1 >= self.n or self.s[self.i + 1] in " \t\n\r"):
                self.i += 1
                continue
            atom = self.parse_scripted(stop_chars)
            if atom is not None:
                items.append(atom)
        return _normalize_ast(_make_seq(items))

    def parse_scripted(self, stop_chars: tuple[str, ...] = ()):
        base = self.parse_atom(stop_chars)
        if base is None:
            return None
        sub = None
        sup = None
        primes = 0
        while True:
            saved = self.i
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == "'":
                primes += 1
                self.i += 1
                continue
            if self.i < self.n and self.s[self.i] == "_":
                self.i += 1
                sub = self.parse_script_arg()
            elif self.i < self.n and self.s[self.i] == "^":
                self.i += 1
                sup = self.parse_script_arg()
            else:
                self.i = saved
                break
        if primes:
            p_node = ("sym", "'" * primes)
            sup = _make_seq([sup, p_node]) if sup is not None else p_node
        return _attach_scripts(base, sub, sup)

    def parse_script_arg(self):
        self.skip_ws()
        if self.i >= self.n:
            return ("seq", ())
        if self.s[self.i] == "(":
            self.i += 1
            inner = self.parse_seq(stop_chars=(")",))
            if self.i < self.n and self.s[self.i] == ")":
                self.i += 1
            return inner
        return self.parse_atom(()) or ("seq", ())

    def _read_kw_value(self) -> str:
        start = self.i
        depth = 0
        while self.i < self.n:
            ch = self.s[self.i]
            if ch == '"':
                _, self.i = parse_typ_str_lit(self.s, self.i)
                continue
            if ch in "([":
                depth += 1
            elif ch in ")]":
                if depth == 0:
                    break
                depth -= 1
            elif ch == "," and depth == 0:
                val = self.s[start:self.i]
                self.i += 1
                return val.strip()
            self.i += 1
        return self.s[start:self.i].strip()

    def parse_call_args(self) -> list:
        self.i += 1
        args = []
        while self.i < self.n:
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ")":
                self.i += 1
                break
            m_kw = re.match(r"[A-Za-z][A-Za-z0-9_-]*\s*:", self.s[self.i:])
            if m_kw:
                self.i += m_kw.end()
                self._read_kw_value()
                continue
            args.append(self.parse_seq(stop_chars=(",", ")")))
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ",":
                self.i += 1
            elif self.i < self.n and self.s[self.i] == ")":
                self.i += 1
                break
        return args

    def parse_mat_or_cases(self, kind: str) -> tuple:
        self.i += 1
        delim: str | None = "(" if kind == "matrix" else None
        augment: int | str | None = None
        rows = []
        cur_row = []
        while self.i < self.n:
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ")":
                self.i += 1
                break
            m_kw = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*:", self.s[self.i:])
            if m_kw:
                kw_name = m_kw.group(1)
                self.i += m_kw.end()
                raw_v = self._read_kw_value().strip().lstrip("#").strip()
                if kind == "matrix" and kw_name == "delim":
                    if raw_v == "none":
                        delim = None
                    elif len(raw_v) >= 2 and raw_v[0] == '"' and raw_v[-1] == '"':
                        delim = raw_v[1:-1]
                    else:
                        delim = raw_v
                elif kind == "matrix" and kw_name == "augment":
                    if raw_v == "none":
                        augment = None
                    elif raw_v.isdigit():
                        augment = int(raw_v)
                    else:
                        augment = raw_v
                continue
            if kind == "cases":
                cur_row.append(self.parse_seq(stop_chars=("&", ",", ")")))
                self.skip_ws()
                if self.i < self.n and self.s[self.i] == "&":
                    self.i += 1
                elif self.i < self.n and self.s[self.i] == ",":
                    rows.append(tuple(cur_row))
                    cur_row = []
                    self.i += 1
                elif self.i < self.n and self.s[self.i] == ")":
                    rows.append(tuple(cur_row))
                    cur_row = []
                    self.i += 1
                    break
            else:
                cur_row.append(self.parse_seq(stop_chars=(",", ";", ")")))
                self.skip_ws()
                if self.i < self.n and self.s[self.i] == ",":
                    self.i += 1
                elif self.i < self.n and self.s[self.i] == ";":
                    rows.append(tuple(cur_row))
                    cur_row = []
                    self.i += 1
                elif self.i < self.n and self.s[self.i] == ")":
                    rows.append(tuple(cur_row))
                    cur_row = []
                    self.i += 1
                    break
        if cur_row and not (len(cur_row) == 1 and cur_row[0] == ("seq", ())):
            rows.append(tuple(cur_row))
        if kind == "cases":
            return ("cases", tuple(rows))
        return ("matrix", delim, augment, tuple(rows))

    def parse_atom(self, stop_chars: tuple[str, ...] = ()):
        self.skip_ws()
        if self.i >= self.n:
            return None
        c = self.s[self.i]
        if c == "\\" and self.i + 1 < self.n:
            ch = self.s[self.i + 1]
            self.i += 2
            return ("op", ch)
        if c == '"':
            raw_val, self.i = parse_typ_str_lit(self.s, self.i)
            val = _norm_math_text(raw_val)
            if val == "":
                return None
            if val in (",", ";", ".", ":"):
                return ("op", val)
            if val in ("#", "%", "&", "$"):
                return ("sym", val)
            return ("text", val)
        if c == "(":
            self.i += 1
            inner = self.parse_seq(stop_chars=(")",))
            if self.i < self.n and self.s[self.i] == ")":
                self.i += 1
                return ("group", "(", inner)
            return _make_seq([("op", "("), inner])
        if c == "[":
            depth = 0
            j = self.i
            while j < self.n:
                if self.s[j] == "[":
                    depth += 1
                elif self.s[j] == "]":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            raw_in = self.s[self.i + 1:j] if j < self.n else ""
            if "$" in raw_in and j < self.n:
                self.i = j + 1
                cleaned = _norm_math_text(re.sub(r"\$([^$]+)\$", lambda mm: mm.group(1), raw_in))
                return ("text", cleaned)
            self.i += 1
            inner = self.parse_seq(stop_chars=("]",))
            if self.i < self.n and self.s[self.i] == "]":
                self.i += 1
                return ("group", "[", inner)
            return _make_seq([("op", "["), inner])
        if c == "{":
            self.i += 1
            inner = self.parse_seq(stop_chars=("}",))
            if self.i < self.n and self.s[self.i] == "}":
                self.i += 1
                return ("group", "{", inner)
            return _make_seq([("op", "{"), inner])
        if c in ")]}":
            self.i += 1
            return ("op", c)
        if c.isdigit():
            m = re.match(r"\d+(?:\.\d+)?", self.s[self.i:])
            self.i += m.end()
            return ("num", m.group(0))
        if c == "#":
            self.i += 1
            m = re.match(r"[A-Za-z][A-Za-z0-9_.-]*", self.s[self.i:])
            if not m:
                return None
            name = m.group(0)
            self.i += m.end()
            if name == "box":
                if self.i < self.n and self.s[self.i] == "(":
                    self.parse_call_args()
                if self.i < self.n and self.s[self.i] == "[":
                    self.i += 1
                    self.skip_ws()
                    if self.i < self.n and self.s[self.i] == "$":
                        self.i += 1
                        inner = self.parse_seq(stop_chars=("$",))
                        if self.i < self.n and self.s[self.i] == "$":
                            self.i += 1
                    else:
                        inner = self.parse_seq(stop_chars=("]",))
                    self.skip_ws()
                    if self.i < self.n and self.s[self.i] == "]":
                        self.i += 1
                    return ("boxed", inner)
            if name in ("eqref", "eqnref", "secref", "mainequation", "bare-ref") and self.i < self.n and self.s[self.i] == "(":
                args = self.parse_call_args()
                return ("ref", args[0][1] if args and isinstance(args[0], tuple) and args[0][0] == "text" else str(args))
            if name in TYP_MATH_SYMS:
                val = TYP_MATH_SYMS[name]
                return ("sym", val) if val[0].isalpha() else ("op", val)
            if self.i < self.n and self.s[self.i] == "(":
                self.parse_call_args()
            return ("sym", name)
        if c.isalpha():
            m = re.match(r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*", self.s[self.i:])
            ident = m.group(0)
            self.i += m.end()
            if self.i < self.n and self.s[self.i] == "(":
                if ident == "frac":
                    args = self.parse_call_args()
                    return ("frac", args[0] if len(args) > 0 else ("seq", ()), args[1] if len(args) > 1 else ("seq", ()))
                if ident == "binom":
                    args = self.parse_call_args()
                    return ("binom", args[0], args[1])
                if ident == "sqrt":
                    args = self.parse_call_args()
                    return ("sqrt", args[0])
                if ident == "root":
                    args = self.parse_call_args()
                    return ("root", args[0], args[1])
                if ident == "abs":
                    args = self.parse_call_args()
                    return ("group", "|", args[0])
                if ident == "norm":
                    args = self.parse_call_args()
                    return ("group", "||", args[0])
                if ident == "floor":
                    args = self.parse_call_args()
                    return ("group", "floor", args[0])
                if ident == "ceil":
                    args = self.parse_call_args()
                    return ("group", "ceil", args[0])
                if ident in ("mid", "lr", "stretch"):
                    args = self.parse_call_args()
                    return args[0] if len(args) == 1 else _make_seq(args)
                if ident == "mat":
                    return self.parse_mat_or_cases("matrix")
                if ident == "cases":
                    return self.parse_mat_or_cases("cases")
                if ident == "attach":
                    self.i += 1
                    pos_args, kw_args = [], {}
                    while self.i < self.n:
                        self.skip_ws()
                        if self.i < self.n and self.s[self.i] == ")":
                            self.i += 1
                            break
                        m_kw = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*:", self.s[self.i:])
                        if m_kw:
                            k = m_kw.group(1)
                            self.i += m_kw.end()
                            kw_args[k] = self.parse_seq(stop_chars=(",", ")"))
                        else:
                            pos_args.append(self.parse_seq(stop_chars=(",", ")")))
                        self.skip_ws()
                        if self.i < self.n and self.s[self.i] == ",":
                            self.i += 1
                        elif self.i < self.n and self.s[self.i] == ")":
                            self.i += 1
                            break
                    base_a = pos_args[0] if pos_args else ("seq", ())
                    if base_a == ("op", "->") and "t" in kw_args:
                        return ("arrow_labeled", "->", kw_args["t"])
                    return ("attach", base_a, tuple(sorted(kw_args.items())))
                if ident in ACCENT_TYP:
                    args = self.parse_call_args()
                    return ("accent", ACCENT_TYP[ident], args[0] if args else ("seq", ()))
                if ident in FONT_MAP_TYP:
                    role = FONT_MAP_TYP[ident]
                    raw_arg_start = self.i
                    args = self.parse_call_args()
                    raw_arg = self.s[raw_arg_start:self.i]
                    arg0 = args[0] if args else ("seq", ())
                    if role in ("text", "op"):
                        if isinstance(arg0, tuple) and arg0[0] in ("text", "sym"):
                            return arg0
                        if role == "op":
                            return arg0
                        return ("text", str(arg0))
                    if (
                        ident == "bold"
                        and isinstance(arg0, tuple)
                        and arg0[0] == "sym"
                        and len(arg0[1]) == 1
                        and arg0[1].isalpha()
                        and "upright(" not in raw_arg
                    ):
                        return ("font", "bf_it", arg0)
                    return ("font", role, arg0)
                if ident in ("limits", "scripts", "display", "inline", "accent"):
                    args = self.parse_call_args()
                    return args[0] if len(args) == 1 else _make_seq(args)
            if ident in TYP_MATH_SPACE:
                return None
            if ident in TYP_MATH_SYMS:
                val = TYP_MATH_SYMS[ident]
                return ("sym", val) if val[0].isalpha() else ("op", val)
            if len(ident) == 1:
                return ("sym", ident)
            self.unsupported.append(ident)
            return ("UNSUPPORTED_TYP", ident)
        if c in "^_":
            self.i += 1
            arg = self.parse_script_arg()
            return ("sup" if c == "^" else "sub", ("empty",), arg)
        if c in "+-=<>/*|,;:!?~.":
            self.i += 1
            return ("op", c)
        self.i += 1
        return ("sym", c)


def parse_tex_math_ast(expr: str) -> tuple[tuple, list[str]]:
    p = TexMathParser(expr)
    return p.parse_seq(), p.unsupported


def parse_typst_math_ast(expr: str) -> tuple[tuple, list[str]]:
    p = TypMathParser(expr)
    return p.parse_seq(), p.unsupported


# =============================================================================
# Unified Ordered Content Stream Extractors (Prose + Punct + Code + Math AST)
# Preserves ALL words (length >= 1), exact order, exact case, punctuation,
# verbatim CLI commands, refs, citations, and ALL inline/display Math ASTs.
# =============================================================================

def _norm_image_path(path: str, base_dir: str) -> str:
    """Repository-root-relative POSIX path of an included image (TeX relative to its driver dir; Typst root-absolute)."""
    p = path.strip().replace("\\", "/")
    if p.startswith("/"):
        p = p.lstrip("/")
    elif base_dir:
        p = base_dir + "/" + p
    return posixpath.normpath(p)


def _emit_prose_tokens(text: str, tokens: list[tuple]) -> None:
    t = norm_prose_typography(text)
    for m in re.finditer(r"[A-Za-z0-9]+(?:['][A-Za-z]+)?|[;:.,?!]", t):
        tok = m.group(0)
        if tok in ";:.,?!":
            tokens.append(("P", tok))
        else:
            tokens.append(("W", tok))


def _parse_latex_col_math_flags(col_spec: str) -> list[bool]:
    """Return per-column boolean indicating LaTeX `>{$}...<{$}` auto-math columns."""
    flags: list[bool] = []
    i = 0
    n = len(col_spec)
    pending_math = False
    while i < n:
        c = col_spec[i]
        if c in " \t\n\r|!":
            i += 1
            continue
        if c == ">":
            grp, i = read_balanced_group(col_spec, i + 1, "{", "}")
            if "$" in grp:
                pending_math = True
            continue
        if c == "<":
            _, i = read_balanced_group(col_spec, i + 1, "{", "}")
            continue
        if c == "@":
            _, i = read_balanced_group(col_spec, i + 1, "{", "}")
            continue
        if c in "pbm":
            _, i = read_balanced_group(col_spec, i + 1, "{", "}")
            flags.append(pending_math)
            pending_math = False
            continue
        if c in "lcrX":
            flags.append(pending_math)
            pending_math = False
            i += 1
            continue
        i += 1
    return flags


def _is_escaped(s: str, idx: int) -> bool:
    """Return True iff character at s[idx] is preceded by an odd number of backslashes."""
    bs = 0
    k = idx - 1
    while k >= 0 and s[k] == "\\":
        bs += 1
        k -= 1
    return (bs % 2) == 1


def _extract_tex_flowchart(tikz_body: str, fname: str) -> tuple[tuple, list[str]]:
    """Parse a TikZ schematic into ordered node token tuples + index-mapped directed edges."""
    node_ids: dict[str, int] = {}
    nodes: list[tuple] = []
    edges: list[tuple[int, int]] = []
    unsup: list[str] = []
    i = 0
    n = len(tikz_body)
    while i < n:
        if tikz_body.startswith(r"\node", i):
            j = i + len(r"\node")
            while j < n and tikz_body[j] in " \t\n\r":
                j += 1
            if j < n and tikz_body[j] == "[":
                _, j = read_balanced_group(tikz_body, j, "[", "]")
            while j < n and tikz_body[j] in " \t\n\r":
                j += 1
            nid, j = read_balanced_group(tikz_body, j, "(", ")")
            nid = nid.strip()
            body, j = read_balanced_group(tikz_body, j, "{", "}")
            ntoks, nunsup = extract_tex_ordered(body, fname)
            unsup.extend(nunsup)
            require(nid not in node_ids, f"Duplicate TikZ node id {nid!r} in {fname}")
            node_ids[nid] = len(nodes)
            nodes.append(tuple(ntoks))
            i = j
            continue
        if tikz_body.startswith(r"\draw", i):
            j = i + len(r"\draw")
            while j < n and tikz_body[j] in " \t\n\r":
                j += 1
            opts = ""
            if j < n and tikz_body[j] == "[":
                opts, j = read_balanced_group(tikz_body, j, "[", "]")
            semi = tikz_body.find(";", j)
            require(semi >= 0, f"Unterminated \\draw in {fname}")
            stmt = tikz_body[j:semi]
            m_edge = re.fullmatch(r"\s*\(\s*([^)]+?)\s*\)\s*--\s*\(\s*([^)]+?)\s*\)\s*", stmt)
            require(m_edge is not None, f"Unsupported TikZ \\draw statement in {fname}: {stmt!r}")
            src, dst = m_edge.group(1).strip(), m_edge.group(2).strip()
            require(src in node_ids and dst in node_ids, f"Unknown TikZ edge endpoint ({src!r}, {dst!r}) in {fname}")
            if "-{Latex}" in opts or "->" in opts:
                edges.append((node_ids[src], node_ids[dst]))
            elif "{Latex}-" in opts or "<-" in opts:
                edges.append((node_ids[dst], node_ids[src]))
            else:
                raise ValueError(f"Unsupported TikZ arrow direction {opts!r} in {fname}")
            i = semi + 1
            continue
        i += 1
    require(len(nodes) > 0 and len(edges) > 0, f"Empty TikZ flowchart parsed in {fname}")
    return ("FLOWCHART", tuple(nodes), tuple(edges)), unsup


def _extract_typst_flowchart(paren_arg: str, fname: str, root: Path | None = None) -> tuple[tuple, list[str]]:
    """Parse #aod-flowchart(...) into ordered node token tuples + index-mapped directed edges."""
    _, pos = _typ_split_args(paren_arg)
    require(len(pos) == 2, f"Expected 2 positional arguments (nodes, edges) in #aod-flowchart in {fname}, got {len(pos)}")
    nodes_raw, edges_raw = pos[0].strip(), pos[1].strip()
    require(nodes_raw.startswith("(") and nodes_raw.endswith(")"), f"Malformed flowchart nodes tuple in {fname}")
    require(edges_raw.startswith("(") and edges_raw.endswith(")"), f"Malformed flowchart edges tuple in {fname}")
    _, node_entries = _typ_split_args(nodes_raw[1:-1])
    _, edge_entries = _typ_split_args(edges_raw[1:-1])

    node_ids: dict[str, int] = {}
    nodes: list[tuple] = []
    edges: list[tuple[int, int]] = []
    unsup: list[str] = []
    for entry in node_entries:
        e = entry.strip()
        require(e.startswith("(") and e.endswith(")"), f"Malformed flowchart node dict in {fname}: {e[:60]!r}")
        nd, npos = _typ_split_args(e[1:-1])
        require(not npos and "id" in nd and "body" in nd, f"Flowchart node missing id/body in {fname}")
        nid, _ = parse_typ_str_lit(nd["id"].strip(), 0)
        b_raw = nd["body"].strip()
        require(b_raw.startswith("[") and b_raw.endswith("]"), f"Flowchart node body must be [...] in {fname}")
        ntoks, nunsup = extract_typst_ordered(b_raw[1:-1], fname, root=root)
        unsup.extend(nunsup)
        require(nid not in node_ids, f"Duplicate flowchart node id {nid!r} in {fname}")
        node_ids[nid] = len(nodes)
        nodes.append(tuple(ntoks))
    for entry in edge_entries:
        e = entry.strip()
        require(e.startswith("(") and e.endswith(")"), f"Malformed flowchart edge dict in {fname}: {e[:60]!r}")
        ed, epos = _typ_split_args(e[1:-1])
        require(not epos and "from" in ed and "to" in ed, f"Flowchart edge missing from/to in {fname}")
        src, _ = parse_typ_str_lit(ed["from"].strip(), 0)
        dst, _ = parse_typ_str_lit(ed["to"].strip(), 0)
        require(src in node_ids and dst in node_ids, f"Unknown flowchart edge endpoint ({src!r}, {dst!r}) in {fname}")
        edges.append((node_ids[src], node_ids[dst]))
    require(len(nodes) > 0 and len(edges) > 0, f"Empty #aod-flowchart parsed in {fname}")
    return ("FLOWCHART", tuple(nodes), tuple(edges)), unsup


_LATEX_CODE_UNESCAPE_RE = re.compile(
    r"\\allowbreak\{\}|\\allowbreak(?![A-Za-z])"
    r"|\\textasciicircum\{\}|\\textasciitilde\{\}|\\textbackslash\{\}"
    r"|\\([_\-%{}$&#])"
)


def _unescape_latex_code(arg: str) -> str:
    """Invert typ2tex escape_latex_text(..., in_texttt=True) in a single pass."""
    def _repl(m: re.Match) -> str:
        tok = m.group(0)
        if tok.startswith(r"\allowbreak"):
            return ""
        if tok == r"\textasciicircum{}":
            return "^"
        if tok == r"\textasciitilde{}":
            return "~"
        if tok == r"\textbackslash{}":
            return "\\"
        return m.group(1)

    return _LATEX_CODE_UNESCAPE_RE.sub(_repl, arg)


def extract_tex_ordered(tex_raw: str, fname: str = "", emit_boundaries: bool = False) -> tuple[list[tuple], list[str]]:
    t = strip_tex_comments(tex_raw)
    t = re.sub(r"\\endfirsthead.*?\\endhead", "", t, flags=re.S)
    tokens: list[tuple] = []
    unsup_math: list[str] = []
    buf: list[str] = []

    def flush_buf() -> None:
        if buf:
            _emit_prose_tokens("".join(buf), tokens)
            buf.clear()

    def emit_br() -> None:
        if emit_boundaries:
            flush_buf()
            tokens.append(("BR",))

    def emit_math(expr: str) -> None:
        ast_m, u = parse_tex_math_ast(expr)
        unsup_math.extend(u)
        if ast_m == ("sym", "AOD:SADARop"):
            tokens.append(("W", "SADAR"))
        else:
            tokens.append(("MATH", ast_m))

    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if t.startswith(r"\[", i):
            flush_buf()
            end_i = t.find(r"\]", i + 2)
            require(end_i >= 0, f"Unclosed \\[ in {fname}")
            emit_math(t[i + 2:end_i])
            i = end_i + 2
            continue
        if t.startswith(r"\(", i):
            flush_buf()
            end_i = t.find(r"\)", i + 2)
            require(end_i >= 0, f"Unclosed \\( in {fname}")
            emit_math(t[i + 2:end_i])
            i = end_i + 2
            continue
        if c == "$" and not _is_escaped(t, i):
            flush_buf()
            if i + 1 < n and t[i + 1] == "$":
                end_i = t.find("$$", i + 2)
                require(end_i >= 0, f"Unclosed $$ in {fname}")
                body = t[i + 2:end_i]
                i = end_i + 2
            else:
                j = i + 1
                while j < n:
                    if t[j] == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if t[j] == "$":
                        break
                    j += 1
                require(j < n, f"Unclosed $ in {fname}")
                body = t[i + 1:j]
                i = j + 1
            emit_math(body)
            continue
        if c == "\\":
            if i + 1 < n and not t[i + 1].isalpha():
                ch = t[i + 1]
                i += 2
                if ch == "\\":
                    while i < n and t[i] in " \t":
                        i += 1
                    if i < n and t[i] == "[":
                        eb = t.find("]", i)
                        if eb >= 0:
                            i = eb + 1
                    if emit_boundaries:
                        emit_br()
                    else:
                        buf.append(" ")
                elif ch in "_%&$-#{}":
                    buf.append(ch)
                else:
                    buf.append(" ")
                continue
            m = re.match(r"\\([A-Za-z]+\*?)", t[i:])
            if m:
                cmd = m.group(1)
                i += m.end()
                if cmd == "begin":
                    env, i = read_balanced_group(t, i)
                    if env == "tikzpicture":
                        flush_buf()
                        end_tag = r"\end{tikzpicture}"
                        end_i = t.find(end_tag, i)
                        require(end_i >= 0, f"Unclosed tikzpicture in {fname}")
                        if not emit_boundaries:
                            fc_tok, fc_unsup = _extract_tex_flowchart(t[i:end_i], fname)
                            tokens.append(fc_tok)
                            unsup_math.extend(fc_unsup)
                        else:
                            emit_br()
                        i = end_i + len(end_tag)
                        continue
                    if env in ("equation", "equation*", "align", "align*", "gather", "gather*"):
                        flush_buf()
                        end_tag = f"\\end{{{env}}}"
                        end_i = t.find(end_tag, i)
                        require(end_i >= 0, f"Unclosed {env} in {fname}")
                        emit_math(t[i:end_i])
                        i = end_i + len(end_tag)
                        continue
                    if env == "quote":
                        end_tag = r"\end{quote}"
                        end_i = t.find(end_tag, i)
                        qbody = t[i:end_i]
                        if r"\ttfamily" in qbody:
                            flush_buf()
                            cmd_str = re.sub(r"\\(?:small|ttfamily|footnotesize|normalsize)\b", "", qbody)
                            cmd_str = cmd_str.replace(r"\_", "_").strip()
                            tokens.append(("CODE", re.sub(r"\s+", " ", cmd_str)))
                            i = end_i + len(end_tag)
                            continue
                        emit_br()
                    if env == "abstract":
                        emit_br()
                        buf.append(" Abstract ")
                        emit_br()
                    elif env in ("tabular", "longtable", "tabularx"):
                        emit_br()
                        if env == "tabularx":
                            _, i = read_balanced_group(t, i)
                            col_spec, i = read_balanced_group(t, i)
                        else:
                            while i < n and t[i] in " \t\n\r":
                                i += 1
                            if i < n and t[i] == "[":
                                _, i = read_balanced_group(t, i, "[", "]")
                            col_spec, i = read_balanced_group(t, i)
                        col_flags = _parse_latex_col_math_flags(col_spec)
                        if any(col_flags):
                            flush_buf()
                            end_tag = f"\\end{{{env}}}"
                            end_i = t.find(end_tag, i)
                            require(end_i >= 0, f"Unclosed {env} in {fname}")
                            tbody = t[i:end_i]
                            tbody = re.sub(r"\\(?:toprule|midrule|bottomrule|hline)\b", "", tbody)
                            for raw_row in re.split(r"\\\\(?:\[[^\]]*\])?", tbody):
                                row = raw_row.strip()
                                if not row:
                                    continue
                                cells = row.split("&")
                                for ci, cell in enumerate(cells):
                                    c_str = cell.strip()
                                    if not c_str:
                                        continue
                                    if ci < len(col_flags) and col_flags[ci]:
                                        emit_math(c_str)
                                    else:
                                        sub_t, sub_u = extract_tex_ordered(c_str, fname, emit_boundaries=emit_boundaries)
                                        tokens.extend(sub_t)
                                        unsup_math.extend(sub_u)
                                    emit_br()
                                emit_br()
                            i = end_i + len(end_tag)
                            continue
                    elif env in ("table", "table*", "figure", "figure*"):
                        emit_br()
                        while i < n and t[i] in " \t\n\r":
                            i += 1
                        if i < n and t[i] == "[":
                            _, i = read_balanced_group(t, i, "[", "]")
                    elif env == "definition":
                        emit_br()
                        while i < n and t[i] in " \t\n\r":
                            i += 1
                        if i < n and t[i] == "[":
                            title, i = read_balanced_group(t, i, "[", "]")
                            flush_buf()
                            sub_t, sub_u = extract_tex_ordered(title, fname, emit_boundaries=emit_boundaries)
                            tokens.extend(sub_t)
                            unsup_math.extend(sub_u)
                            emit_br()
                    elif env == "noteblock":
                        emit_br()
                        title, i = read_balanced_group(t, i)
                        flush_buf()
                        sub_t, sub_u = extract_tex_ordered(title, fname, emit_boundaries=emit_boundaries)
                        tokens.extend(sub_t)
                        unsup_math.extend(sub_u)
                        emit_br()
                    elif env == "minipage":
                        while i < n and t[i] in " \t\n\r":
                            i += 1
                        if i < n and t[i] == "[":
                            _, i = read_balanced_group(t, i, "[", "]")
                        _, i = read_balanced_group(t, i)
                    elif env in ("enumerate", "itemize"):
                        emit_br()
                        while i < n and t[i] in " \t\n\r":
                            i += 1
                        if i < n and t[i] == "[":
                            _, i = read_balanced_group(t, i, "[", "]")
                    continue
                if cmd == "end":
                    env_end, i = read_balanced_group(t, i)
                    if env_end in ("tabular", "longtable", "tabularx", "table", "table*", "figure", "figure*",
                                   "itemize", "enumerate", "quote", "abstract", "definition", "noteblock"):
                        emit_br()
                    continue
                if cmd in ("texttt", "path", "url"):
                    flush_buf()
                    arg, i = read_balanced_group(t, i)
                    tokens.append(("CODE", _unescape_latex_code(arg).strip()))
                    continue
                if cmd == "texorpdfstring":
                    a_arg, i = read_balanced_group(t, i)
                    _, i = read_balanced_group(t, i)
                    flush_buf()
                    sub_t, sub_u = extract_tex_ordered(a_arg, fname, emit_boundaries=emit_boundaries)
                    tokens.extend(sub_t)
                    unsup_math.extend(sub_u)
                    continue
                if cmd == "href":
                    flush_buf()
                    _, i = read_balanced_group(t, i)
                    disp_arg, i = read_balanced_group(t, i)
                    m_tt = re.fullmatch(r"\\texttt\{(.*)\}", disp_arg.strip())
                    if m_tt:
                        tokens.append(("CODE", _unescape_latex_code(m_tt.group(1))))
                    else:
                        _emit_prose_tokens(disp_arg, tokens)
                    continue
                if cmd in ("eqref", "eqnref", "secref", "appref", "figref", "tabref", "ref",
                           "mainequation", "mainsection", "mainappendix", "maintable"):
                    flush_buf()
                    rid, i = read_balanced_group(t, i)
                    tokens.append(("REF", rid.strip()))
                    continue
                if cmd == "cite":
                    flush_buf()
                    supp = None
                    while i < n and t[i] in " \t\n\r":
                        i += 1
                    if i < n and t[i] == "[":
                        supp, i = read_balanced_group(t, i, "[", "]")
                    keys, i = read_balanced_group(t, i)
                    tokens.append(("CITE", tuple(k.strip() for k in keys.split(",") if k.strip())))
                    if supp:
                        _emit_prose_tokens(re.sub(r"\\S", " ", supp), tokens)
                    continue
                if cmd == "includegraphics":
                    flush_buf()
                    while i < n and t[i] in " \t\n\r":
                        i += 1
                    if i < n and t[i] == "[":
                        _, i = read_balanced_group(t, i, "[", "]")
                    gpath = ""
                    if i < n and t[i] == "{":
                        gpath, i = read_balanced_group(t, i)
                    tokens.append(("IMG", _norm_image_path(gpath.strip(), "manual" if fname.startswith("manual/") else "")))
                    continue
                if cmd in ("label", "input", "include", "vspace", "hspace",
                           "setlength", "addtolength", "renewcommand", "newcommand", "captionsetup",
                           "pagestyle", "thispagestyle", "setcounter", "addtocounter", "phantomsection",
                           "hypersetup", "bibliographystyle", "bibliography", "documentclass", "usepackage"):
                    while i < n and t[i] in " \t\n\r":
                        i += 1
                    if i < n and t[i] == "[":
                        _, i = read_balanced_group(t, i, "[", "]")
                    if i < n and t[i] == "{":
                        _, i = read_balanced_group(t, i)
                    if cmd in ("setlength", "addtolength", "renewcommand", "newcommand", "setcounter", "addtocounter"):
                        if i < n and t[i] == "{":
                            _, i = read_balanced_group(t, i)
                    continue
                if cmd == "item":
                    emit_br()
                    buf.append(" ")
                    continue
                if emit_boundaries and cmd == "aodnoteblock":
                    emit_br()
                    if i < n and t[i] == "{":
                        title_arg, i = read_balanced_group(t, i)
                        sub_t, sub_u = extract_tex_ordered(title_arg, fname, emit_boundaries=True)
                        tokens.extend(sub_t)
                        unsup_math.extend(sub_u)
                    emit_br()
                    if i < n and t[i] == "{":
                        body_arg, i = read_balanced_group(t, i)
                        sub_t, sub_u = extract_tex_ordered(body_arg, fname, emit_boundaries=True)
                        tokens.extend(sub_t)
                        unsup_math.extend(sub_u)
                    emit_br()
                    continue
                if emit_boundaries and cmd in ("section", "subsection", "subsubsection", "paragraph",
                                               "caption", "footnote"):
                    while i < n and t[i] in " \t\n\r":
                        i += 1
                    if i < n and t[i] == "[":
                        _, i = read_balanced_group(t, i, "[", "]")
                    emit_br()
                    if i < n and t[i] == "{":
                        blk_arg, i = read_balanced_group(t, i)
                        sub_t, sub_u = extract_tex_ordered(blk_arg, fname, emit_boundaries=True)
                        tokens.extend(sub_t)
                        unsup_math.extend(sub_u)
                    emit_br()
                    continue
                if cmd in ("section", "subsection", "subsubsection", "paragraph", "textbf", "textit",
                           "emph", "textrm", "textsc", "text", "mathrm", "caption", "footnote", "mbox", "multicolumn"):
                    if cmd == "multicolumn":
                        _, i = read_balanced_group(t, i)
                        _, i = read_balanced_group(t, i)
                    while i < n and t[i] in " \t\n\r":
                        i += 1
                    if i < n and t[i] == "[":
                        _, i = read_balanced_group(t, i, "[", "]")
                    buf.append(" ")
                    continue
                if cmd == "SADARop":
                    buf.append(" SADAR ")
                    continue
                if cmd == "ADARop":
                    buf.append(" ADAR ")
                    continue
                if cmd == "RCDop":
                    buf.append(" RCD ")
                    continue
                if cmd == "AoD":
                    buf.append(" AoD ")
                    continue
                if cmd == "AFC":
                    buf.append(" AFC ")
                    continue
                if cmd == "AOm":
                    buf.append(" AOmega ")
                    continue
                if cmd == "AODDocumentAuthor":
                    buf.append(" Reginald Poyau ")
                    continue
                if cmd == "AODDocumentDate":
                    buf.append(" ")
                    continue
                if cmd in ("textendash", "textemdash"):
                    buf.append("-")
                    continue
                if cmd == "textasciicircum":
                    if i + 1 < n and t[i:i + 2] == "{}":
                        i += 2
                    buf.append("^")
                    continue
                if cmd == "textasciitilde":
                    if i + 1 < n and t[i:i + 2] == "{}":
                        i += 2
                    buf.append("~")
                    continue
                if cmd == "textbackslash":
                    if i + 1 < n and t[i:i + 2] == "{}":
                        i += 2
                    buf.append("\\")
                    continue
                if cmd == "allowbreak":
                    if i + 1 < n and t[i:i + 2] == "{}":
                        i += 2
                    continue
                buf.append(" ")
                continue
        if c == "&":
            if emit_boundaries:
                emit_br()
            else:
                buf.append(" ")
            i += 1
            continue
        if c in "{}~":
            buf.append(" ")
            i += 1
            continue
        buf.append(c)
        i += 1
    flush_buf()
    return tokens, unsup_math


def _parse_csv_cell_spec_parity(raw: str, where: str, depth: int = 0) -> dict:
    """Parse one declarative cell spec from #aod-csv-table(cells: (...)) (fail-closed)."""
    require(depth <= 4, f"{where}: aod-csv-table cell spec recursion depth exceeded")
    s = raw.strip()
    lit = _parse_exact_typ_str_lit(s)
    if lit is not None:
        require(bool(CSV_TABLE_COL_RE.fullmatch(lit)), f"{where}: aod-csv-table column name {lit!r} is invalid")
        return {"kind": "plain", "col": lit}
    require(
        s.startswith("(") and s.endswith(")") and _typ_balanced(s, 0, "(", ")") == len(s),
        f"{where}: malformed aod-csv-table cell spec: {s[:60]!r}",
    )
    nd, npos = _typ_split_args(s[1:-1])
    require(not npos and "kind" in nd, f"{where}: aod-csv-table cell spec requires named `kind:` and no positional args")
    kind = _parse_exact_typ_str_lit(nd["kind"])
    require(kind is not None, f"{where}: aod-csv-table cell spec `kind` must be a string literal")

    def _req_col(key: str) -> str:
        require(key in nd, f"{where}: aod-csv-table `{kind}` spec missing `{key}:`")
        v = _parse_exact_typ_str_lit(nd[key])
        require(
            v is not None and bool(CSV_TABLE_COL_RE.fullmatch(v)),
            f"{where}: aod-csv-table `{kind}` key `{key}` must be a literal column identifier",
        )
        return v

    keys = set(nd)
    if kind in CSV_TABLE_SINGLE_COL_KINDS:
        require(keys == {"kind", "col"}, f"{where}: aod-csv-table `{kind}` spec must have exact keys (kind, col), got {sorted(keys)}")
        return {"kind": kind, "col": _req_col("col")}
    if kind == "arrow":
        require(keys == {"kind", "left", "right"}, f"{where}: aod-csv-table `arrow` spec must have exact keys (kind, left, right)")
        return {"kind": "arrow", "left": _req_col("left"), "right": _req_col("right")}
    if kind == "wrap-paren":
        require(keys == {"kind", "col", "paren"}, f"{where}: aod-csv-table `wrap-paren` spec must have exact keys (kind, col, paren)")
        return {"kind": "wrap-paren", "col": _req_col("col"), "paren": _req_col("paren")}
    if kind == "stack":
        require(
            {"kind", "top", "bottom"} <= keys <= {"kind", "top", "bottom", "style"},
            f"{where}: aod-csv-table `stack` spec keys {sorted(keys)} not allowed",
        )
        style = _parse_exact_typ_str_lit(nd["style"]) if "style" in nd else "plain"
        require(style in CSV_TABLE_STACK_STYLES, f"{where}: unsupported aod-csv-table `stack` style {style!r}")
        return {"kind": "stack", "top": _req_col("top"), "bottom": _req_col("bottom"), "style": style}
    if kind == "tuple":
        require(keys == {"kind", "cols"}, f"{where}: aod-csv-table `tuple` spec must have exact keys (kind, cols)")
        ct = nd["cols"].strip()
        require(
            ct.startswith("(") and ct.endswith(")") and _typ_balanced(ct, 0, "(", ")") == len(ct),
            f"{where}: aod-csv-table `tuple` cols must be a literal tuple",
        )
        cnd, cpos = _typ_split_args(ct[1:-1])
        require(not cnd and bool(cpos), f"{where}: aod-csv-table `tuple` cols must be a non-empty positional tuple")
        cols: list[str] = []
        for item in cpos:
            cname = _parse_exact_typ_str_lit(item)
            require(
                cname is not None and bool(CSV_TABLE_COL_RE.fullmatch(cname)),
                f"{where}: aod-csv-table `tuple` column {item!r} must be a literal column identifier",
            )
            cols.append(cname)
        return {"kind": "tuple", "cols": cols}
    if kind == "slot":
        require(keys == {"kind", "edge", "sigma"}, f"{where}: aod-csv-table `slot` spec must have exact keys (kind, edge, sigma)")
        return {"kind": "slot", "edge": _req_col("edge"), "sigma": _req_col("sigma")}
    if kind == "sweep-shed":
        require(keys == {"kind", "sweep", "shed"}, f"{where}: aod-csv-table `sweep-shed` spec must have exact keys (kind, sweep, shed)")
        return {"kind": "sweep-shed", "sweep": _req_col("sweep"), "shed": _req_col("shed")}
    if kind == "math-eq":
        require(keys == {"kind", "lhs", "col"}, f"{where}: aod-csv-table `math-eq` spec must have exact keys (kind, lhs, col)")
        require(_is_exact_typ_content_block(nd["lhs"]), f"{where}: aod-csv-table `math-eq` lhs must be [...]")
        return {"kind": "math-eq", "lhs": nd["lhs"].strip()[1:-1], "col": _req_col("col")}
    if kind == "union-cur":
        require(
            {"kind", "union", "cur"} <= keys <= {"kind", "union", "cur", "lhs"},
            f"{where}: aod-csv-table `union-cur` spec keys {sorted(keys)} not allowed",
        )
        lhs_inner = None
        if "lhs" in nd:
            require(_is_exact_typ_content_block(nd["lhs"]), f"{where}: aod-csv-table `union-cur` lhs must be [...]")
            lhs_inner = nd["lhs"].strip()[1:-1]
        return {"kind": "union-cur", "union": _req_col("union"), "cur": _req_col("cur"), "lhs": lhs_inner}
    if kind == "when":
        require(
            keys == {"kind", "col", "eq", "then", "otherwise"},
            f"{where}: aod-csv-table `when` spec must have exact keys (kind, col, eq, then, otherwise)",
        )
        eq_val = _parse_exact_typ_str_lit(nd["eq"])
        require(eq_val is not None, f"{where}: aod-csv-table `when` eq must be a string literal")
        return {
            "kind": "when",
            "col": _req_col("col"),
            "eq": eq_val,
            "then": _parse_csv_cell_spec_parity(nd["then"], where, depth + 1),
            "otherwise": _parse_csv_cell_spec_parity(nd["otherwise"], where, depth + 1),
        }
    raise ValueError(f"{where}: unsupported aod-csv-table cell spec kind {kind!r}")


def extract_typst_ordered(typ_raw: str, fname: str = "", root: Path | None = None) -> tuple[list[tuple], list[str]]:
    base_root = (ROOT if root is None else Path(root)).resolve()
    t = strip_typst_comments(typ_raw)
    tokens: list[tuple] = []
    unsup_math: list[str] = []
    buf: list[str] = []

    def flush_buf() -> None:
        if buf:
            _emit_prose_tokens("".join(buf), tokens)
            buf.clear()

    def emit_math(expr: str) -> None:
        ast_m, u = parse_typst_math_ast(expr)
        unsup_math.extend(u)
        tokens.append(("MATH", ast_m))

    def emit_csv_text(text: str) -> None:
        cleaned = text.replace("\u200b", "")
        for part in re.split(r"([\u2212\u2194\u03a9])", cleaned):
            if not part:
                continue
            if part == "\u2212":
                flush_buf()
                tokens.append(("MATH", ("op", "-")))
            elif part == "\u2194":
                flush_buf()
                tokens.append(("MATH", ("op", "<->")))
            elif part == "\u03a9":
                flush_buf()
                tokens.append(("MATH", ("sym", "Omega")))
            else:
                buf.append(part)
        buf.append(" ")

    def emit_csv_cell(row: dict[str, str], spec: dict) -> None:
        def _col(col_name: str) -> str:
            require(col_name in row, f"{fname}: CSV row missing declared column {col_name!r}")
            return row[col_name]

        k = spec["kind"]
        if k in ("plain", "wrap"):
            emit_csv_text(_col(spec["col"]))
            return
        if k in ("raw", "raw-wrap"):
            flush_buf()
            tokens.append(("CODE", _col(spec["col"]).strip()))
            return
        if k == "minus":
            emit_csv_text(_col(spec["col"]).replace("-", "\u2212"))
            return
        if k == "signed":
            v = _col(spec["col"])
            if v == "0":
                emit_csv_text("0")
            elif v.startswith("-"):
                emit_csv_text("\u2212" + v[1:])
            elif v.startswith("+"):
                emit_csv_text(v)
            else:
                emit_csv_text("+" + v)
            return
        if k == "rat":
            emit_csv_text(_col(spec["col"]).replace("-", "\u2212"))
            return
        if k == "vec":
            emit_csv_text(_col(spec["col"]).replace(",", ", ").replace("-", "\u2212"))
            return
        if k == "arrow":
            emit_csv_text(_col(spec["left"]))
            flush_buf()
            tokens.append(("MATH", ("op", "->")))
            emit_csv_text(_col(spec["right"]))
            return
        if k == "wrap-paren":
            emit_csv_text(f"{_col(spec['col'])} ({_col(spec['paren'])})")
            return
        if k == "stack":
            st = spec["style"]
            if st == "plain":
                emit_csv_text(_col(spec["top"]))
                emit_csv_text(_col(spec["bottom"]))
                return
            if st == "raw-wrap":
                flush_buf()
                tokens.append(("CODE", _col(spec["top"]).strip()))
                tokens.append(("CODE", _col(spec["bottom"]).strip()))
                return
            if st == "wrap-sub-paren":
                emit_csv_text(_col(spec["top"]))
                emit_csv_text(f"({_col(spec['bottom'])})")
                return
            raise ValueError(f"{fname}: unsupported aod-csv-table stack style {st!r}")
        if k == "tuple":
            emit_csv_text("(" + ", ".join(_col(c).replace("-", "\u2212") for c in spec["cols"]) + ")")
            return
        if k == "slot":
            e = _col(spec["edge"])
            sig = _col(spec["sigma"])
            if e == "-":
                emit_csv_text("\u2212")
            else:
                s_val = "+1" if sig == "1" else sig.replace("-", "\u2212")
                emit_csv_text(f"({e}, {s_val})")
            return
        if k == "sweep-shed":
            emit_csv_text(f"\u2212{_col(spec['sweep'])} + {_col(spec['shed'])}")
            return
        if k == "math-eq":
            buf.append(" ")
            scan_markup(spec["lhs"])
            buf.append(" ")
            emit_csv_text(_col(spec["col"]))
            return
        if k == "union-cur":
            emit_csv_text(f"{_col(spec['union'])} /")
            lhs_markup = spec["lhs"] if spec["lhs"] is not None else "$J_e =$"
            buf.append(" ")
            scan_markup(lhs_markup)
            buf.append(" ")
            emit_csv_text(_col(spec["cur"]))
            return
        if k == "when":
            branch = spec["then"] if _col(spec["col"]) == spec["eq"] else spec["otherwise"]
            emit_csv_cell(row, branch)
            return
        raise ValueError(f"{fname}: unsupported aod-csv-table cell spec kind {k!r}")

    def emit_csv_table(call_args: str) -> None:
        named, pos = _typ_split_args(call_args)
        require(len(pos) == 1, f"{fname}: #aod-csv-table requires 1 positional CSV path argument")
        csv_uri = _parse_exact_typ_str_lit(pos[0])
        require(
            csv_uri is not None and bool(CSV_TABLE_PATH_RE.fullmatch(csv_uri)),
            f"{fname}: disallowed CSV path in #aod-csv-table: {pos[0]!r}",
        )
        disk_path = (base_root / csv_uri.lstrip("/")).resolve()
        require(
            disk_path.is_file() and disk_path.is_relative_to(base_root),
            f"{fname}: missing CSV asset for #aod-csv-table: {csv_uri}",
        )

        def _req_tuple(arg_name: str) -> list[str]:
            require(arg_name in named, f"{fname}: #aod-csv-table missing required `{arg_name}`")
            raw = named[arg_name].strip()
            require(
                raw.startswith("(") and raw.endswith(")") and _typ_balanced(raw, 0, "(", ")") == len(raw),
                f"{fname}: #aod-csv-table `{arg_name}` must be a literal tuple (...)",
            )
            tnd, items = _typ_split_args(raw[1:-1])
            require(not tnd and bool(items), f"{fname}: #aod-csv-table `{arg_name}` must be a non-empty positional tuple")
            return items

        header_items = _req_tuple("headers")
        cell_items = _req_tuple("cells")
        require(len(header_items) == len(cell_items), f"{fname}: #aod-csv-table header/cell arity mismatch")
        cell_specs = [_parse_csv_cell_spec_parity(c, fname) for c in cell_items]

        with disk_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        if "filter-col" in named or "filter-values" in named:
            require(
                "filter-col" in named and "filter-values" in named,
                f"{fname}: #aod-csv-table requires both filter-col and filter-values",
            )
            fcol = _parse_exact_typ_str_lit(named["filter-col"])
            require(
                fcol is not None and fcol in fieldnames,
                f"{fname}: filter-col {fcol!r} not in CSV header {fieldnames}",
            )
            fval_items = _req_tuple("filter-values")
            fvals: set[str] = set()
            for fv in fval_items:
                lit = _parse_exact_typ_str_lit(fv)
                require(lit is not None, f"{fname}: #aod-csv-table filter-values item {fv!r} must be a string literal")
                fvals.add(lit)
            rows = [r for r in rows if r[fcol] in fvals]

        for h_raw in header_items:
            require(_is_exact_typ_content_block(h_raw), f"{fname}: #aod-csv-table header must be [...]")
            buf.append(" ")
            scan_markup(h_raw.strip()[1:-1])
            buf.append(" ")
        for r in rows:
            for spec in cell_specs:
                emit_csv_cell(r, spec)
        flush_buf()

    def scan_code_block(blk: str) -> None:
        i = 0
        n = len(blk)
        while i < n:
            if blk[i] == '"':
                _, i = parse_typ_str_lit(blk, i)
                continue
            if blk[i] == "[":
                inner, i = read_balanced_group(blk, i, "[", "]")
                buf.append(" ")
                scan_markup(inner)
                buf.append(" ")
                continue
            i += 1

    def scan_figure_args(fargs: str) -> None:
        is_tbl = bool(re.search(r"kind\s*:\s*table\b", fargs))
        cap_blocks, other_blocks = [], []
        i = 0
        n = len(fargs)
        while i < n:
            if fargs[i] == '"':
                _, i = parse_typ_str_lit(fargs, i)
                continue
            m_cap = re.match(r"caption\s*:\s*\[", fargs[i:])
            if m_cap:
                inner, i = read_balanced_group(fargs, i + m_cap.end() - 1, "[", "]")
                cap_blocks.append(inner)
                continue
            if fargs[i] == "[":
                inner, i = read_balanced_group(fargs, i, "[", "]")
                other_blocks.append(inner)
                continue
            i += 1
        ordered = (cap_blocks + other_blocks) if is_tbl else (other_blocks + cap_blocks)
        for blk in ordered:
            buf.append(" ")
            scan_markup(blk)
            buf.append(" ")

    def scan_markup(s: str) -> None:
        i = 0
        end = len(s)
        while i < end:
            c = s[i]
            if c == "#":
                if i + 1 < end and s[i + 1] == "{":
                    blk, i = read_balanced_group(s, i + 1, "{", "}")
                    scan_code_block(blk)
                    continue
                m = re.match(r"#([A-Za-z][A-Za-z0-9_.-]*)", s[i:end])
                if m:
                    name = m.group(1)
                    i += m.end()
                    if name in ("import", "include", "set", "show", "let", "counter"):
                        depth = 0
                        in_s = False
                        while i < end:
                            ch = s[i]
                            if ch == "\\" and i + 1 < end:
                                i += 2
                                continue
                            if ch == '"':
                                in_s = not in_s
                                i += 1
                                continue
                            if not in_s:
                                if ch in "([":
                                    depth += 1
                                elif ch in ")]":
                                    depth = max(0, depth - 1)
                                elif depth == 0 and ch in "\n;":
                                    i += 1
                                    break
                            i += 1
                        continue
                    paren_arg = None
                    if i < end and s[i] == "(":
                        paren_arg, i = read_balanced_group(s, i, "(", ")")
                    bracket_arg = None
                    if i < end and s[i] == "[":
                        bracket_arg, i = read_balanced_group(s, i, "[", "]")
                    # Simulate Typst markup parser consuming an unescaped `;` immediately
                    # after a `#call(...)` expression (only `\;` survives as literal `;`).
                    if i < end and s[i] == ";":
                        i += 1

                    if name in ("raw", "aod-raw-wrap") and paren_arg is not None:
                        flush_buf()
                        p_s = paren_arg.strip()
                        if p_s.startswith('"'):
                            val, _ = parse_typ_str_lit(p_s, 0)
                            tokens.append(("CODE", val))
                        continue
                    if name == "image" and paren_arg is not None:
                        flush_buf()
                        p_s = paren_arg.strip()
                        img_path = None
                        if p_s.startswith('"'):
                            img_path, _ = parse_typ_str_lit(p_s, 0)
                        tokens.append(("IMG", _norm_image_path(img_path or "<non-literal-image-path>", "")))
                        continue
                    if name == "link" and paren_arg is not None:
                        flush_buf()
                        if bracket_arg is not None:
                            scan_markup(bracket_arg)
                        else:
                            p_s = paren_arg.strip()
                            if p_s.startswith('"'):
                                val, _ = parse_typ_str_lit(p_s, 0)
                                tokens.append(("CODE", val))
                        continue
                    if name in ("eqref", "eqnref", "secref", "appref", "figref", "tabref", "bare-ref",
                                "mainequation", "mainsection", "mainappendix", "maintable") and paren_arg is not None:
                        flush_buf()
                        p_s = paren_arg.strip()
                        if p_s.startswith('"'):
                            rid, _ = parse_typ_str_lit(p_s, 0)
                            tokens.append(("REF", rid.strip()))
                        continue
                    if name == "aod-cite" and paren_arg is not None:
                        flush_buf()
                        p_s = paren_arg.strip()
                        keys_s, pos2 = parse_typ_str_lit(p_s, 0)
                        tokens.append(("CITE", tuple(k.strip() for k in keys_s.split(",") if k.strip())))
                        ms = re.search(r"supplement\s*:\s*\[", p_s[pos2:])
                        if ms:
                            supp, _ = read_balanced_group(p_s, pos2 + ms.end() - 1, "[", "]")
                            scan_markup(supp)
                        continue
                    if name == "aod-flowchart" and paren_arg is not None:
                        flush_buf()
                        fc_tok, fc_unsup = _extract_typst_flowchart(paren_arg, fname, root=base_root)
                        tokens.append(fc_tok)
                        unsup_math.extend(fc_unsup)
                        continue
                    if name == "aod-csv-table" and paren_arg is not None:
                        flush_buf()
                        emit_csv_table(paren_arg)
                        continue
                    if name == "aod-boxed" and paren_arg is not None:
                        flush_buf()
                        m_d = paren_arg.find("$")
                        require(m_d >= 0, f"Malformed #aod-boxed without math span in {fname}")
                        end_d = paren_arg.rfind("$")
                        require(end_d > m_d, f"Unclosed math span in #aod-boxed in {fname}")
                        ast_m, u = parse_typst_math_ast(paren_arg[m_d + 1:end_d])
                        unsup_math.extend(u)
                        tokens.append(("MATH", ("boxed", ast_m)))
                        continue
                    if name in ("tagged-eq", "math.equation") and paren_arg is not None:
                        flush_buf()
                        m_d = paren_arg.find("$")
                        if m_d >= 0:
                            end_d = paren_arg.rfind("$")
                            emit_math(paren_arg[m_d + 1:end_d])
                        continue
                    if name == "figure" and paren_arg is not None:
                        flush_buf()
                        scan_figure_args(paren_arg)
                        if bracket_arg is not None:
                            scan_markup(bracket_arg)
                        continue
                    if name == "aod-definition":
                        if paren_arg:
                            mt = re.search(r'title\s*:\s*"', paren_arg)
                            if mt:
                                val, _ = parse_typ_str_lit(paren_arg, mt.end() - 1)
                                buf.append(" " + val + " ")
                            mt2 = re.search(r"title\s*:\s*\[", paren_arg)
                            if mt2:
                                val, _ = read_balanced_group(paren_arg, mt2.end() - 1, "[", "]")
                                scan_markup(val)
                        if bracket_arg is not None:
                            scan_markup(bracket_arg)
                        continue
                    if name == "aod-noteblock":
                        if paren_arg:
                            p_s = paren_arg.strip()
                            if p_s.startswith('"'):
                                val, _ = parse_typ_str_lit(p_s, 0)
                                buf.append(" " + val + " ")
                            elif p_s.startswith("["):
                                val, _ = read_balanced_group(p_s, 0, "[", "]")
                                scan_markup(val)
                        if bracket_arg is not None:
                            scan_markup(bracket_arg)
                        continue
                    if name in ("aod-provenance", "aod-literature-note", "aod-remark", "aod-paragraph",
                                "aod-uncaptioned-longtable", "aod-nowrap", "pad", "align", "emph", "strong",
                                "footnote", "text", "block", "box", "page"):
                        if bracket_arg is not None:
                            buf.append(" ")
                            scan_markup(bracket_arg)
                            buf.append(" ")
                        continue
                    if name == "aod-panel":
                        if paren_arg:
                            mc = re.search(r"caption\s*:\s*\[", paren_arg)
                            if mc:
                                val, _ = read_balanced_group(paren_arg, mc.end() - 1, "[", "]")
                                scan_markup(val)
                        if bracket_arg is not None:
                            scan_markup(bracket_arg)
                        continue
                    if name == "grid" and paren_arg is not None:
                        scan_code_block(paren_arg)
                        continue
                    if name in ("aod-anchor", "v", "h", "pagebreak", "colbreak", "image",
                                "aod-start-appendix", "aod-render-bibliography", "outline"):
                        continue
                    if name == "SADARop":
                        buf.append(" SADAR ")
                        continue
                    if name == "ADARop":
                        buf.append(" ADAR ")
                        continue
                    if name == "RCDop":
                        buf.append(" RCD ")
                        continue
                    if name == "AoD":
                        buf.append(" AoD ")
                        continue
                    if name == "AFC":
                        buf.append(" AFC ")
                        continue
                    if name == "AOm":
                        buf.append(" AOmega ")
                        continue
                    if name == "AODDocumentAuthor":
                        buf.append(" Reginald Poyau ")
                        continue
                    if name == "AODDocumentDate":
                        buf.append(" ")
                        continue
                    if bracket_arg is not None:
                        scan_markup(bracket_arg)
                    continue
            if c == "\\" and i + 1 < end:
                ch = s[i + 1]
                i += 2
                buf.append(" " if ch in " \t\n\r" else ch)
                continue
            if c == "@" and (i == 0 or not (s[i - 1].isalnum() or s[i - 1] == "_")):
                m_at = re.match(r"@((?:tab|fig|sec|eq|app):[A-Za-z0-9:._-]+)", s[i:end])
                if m_at:
                    flush_buf()
                    tokens.append(("REF", m_at.group(1)))
                    i += m_at.end()
                    continue
            if c == "<":
                m_lbl = re.match(r"<[A-Za-z0-9_:.-]+>", s[i:end])
                if m_lbl:
                    i += m_lbl.end()
                    continue
            if c == "=" and (i == 0 or s[i - 1] == "\n"):
                j = i
                while j < end and s[j] == "=":
                    j += 1
                if j < end and s[j] == " ":
                    i = j + 1
                    continue
            if c in "-+" and (i == 0 or s[i - 1] == "\n") and i + 1 < end and s[i + 1] == " ":
                i += 2
                continue
            if c == "*":
                i += 1
                continue
            if c == "_" and (i == 0 or not s[i - 1].isalnum()) and (i + 1 >= end or not s[i + 1].isalnum()):
                i += 1
                continue
            if c == "$":
                flush_buf()
                j = i + 1
                in_s = False
                while j < end:
                    if s[j] == "\\" and j + 1 < end:
                        j += 2
                        continue
                    if s[j] == '"':
                        in_s = not in_s
                        j += 1
                        continue
                    if not in_s and s[j] == "$":
                        break
                    j += 1
                require(j < end, f"Unclosed $ in {fname}")
                emit_math(s[i + 1:j])
                i = j + 1
                continue
            buf.append(c)
            i += 1

    scan_markup(t)
    flush_buf()
    return tokens, unsup_math


# =============================================================================
# Labeled equation extraction & immutable table cell extraction
# =============================================================================

def extract_tex_equations(parts: list[tuple[str, str]]) -> dict[str, tuple[str, str | None]]:
    out: dict[str, tuple[str, str | None]] = {}
    env_pat = re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}", re.S)
    for _, text in parts:
        cleaned = strip_tex_comments(text)
        for m in env_pat.finditer(cleaned):
            body = m.group(2)
            labels = re.findall(r"\\label\{([^}]+)\}", body)
            tag_m = re.search(r"\\tag\{([^}]+)\}", body)
            tag = tag_m.group(1) if tag_m else None
            for lbl in labels:
                out[lbl] = (body, tag)
    return out


def extract_typst_equations(files: list[Path]) -> dict[str, tuple[str, str | None]]:
    out: dict[str, tuple[str, str | None]] = {}
    tagged_pat = re.compile(
        r'#tagged-eq\(\s*"([^"]+)"\s*,\s*\$(.*?)\$\s*(?:,\s*(?:lbl:\s*)?<([^>]+)>)?\s*\)', re.S
    )
    disp_pat = re.compile(r'(?<!\\)\$\s+((?:[^$"\\]|\\.|"[^"]*")*?)\s+\$\s*<([^>]+)>', re.S)
    for p in files:
        text = strip_typst_comments(p.read_text(encoding="utf-8"))
        for m in tagged_pat.finditer(text):
            tag, body, lbl = m.group(1), m.group(2), m.group(3)
            if lbl:
                out[lbl] = (body, tag)
        for m in disp_pat.finditer(text):
            body, lbl = m.group(1), m.group(2)
            if lbl not in out:
                out[lbl] = (body, None)
    return out


def _norm_cell_text(cell: str, is_typst: bool) -> str:
    s = cell.strip()
    if is_typst:
        s = re.sub(r'#raw\("([^"]*)"\)', r"\1", s)
        s = re.sub(r'#(?:eqref|eqnref|secref|appref|figref|tabref|mainequation|mainsection|mainappendix|maintable)\("([^"]+)"\)', r"REF(\1)", s)
        s = re.sub(r'#aod-cite\("([^"]+)"(?:[^)]*)\)', r"CITE(\1)", s)
        s = re.sub(r"\\([_\-$#&%{}])", r"\1", s)
        s = re.sub(r"\$([^$]*)\$", lambda m: " " + str(parse_typst_math_ast(m.group(1))[0]) + " ", s)
    else:
        s = re.sub(r"\\\((.*?)\\\)", lambda m: " " + str(parse_tex_math_ast(m.group(1))[0]) + " ", s)
        s = re.sub(r"\$([^$]*)\$", lambda m: " " + str(parse_tex_math_ast(m.group(1))[0]) + " ", s)
        s = re.sub(r"\\(?:texttt|path|url)\{([^}]*)\}", r"\1", s)
        s = re.sub(r"\\(?:textbf|textit|emph|mathrm|text)\{([^}]*)\}", r"\1", s)
        s = re.sub(r"\\(?:eqref|eqnref|secref|appref|figref|tabref|mainequation|mainsection|mainappendix|maintable)\{([^}]+)\}", r"REF(\1)", s)
        s = re.sub(r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}", r"CITE(\1)", s)
        s = re.sub(r"\\([_\-$#&%{}])", r"\1", s)
    s = norm_prose_typography(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_tex_table_rows(tex_path: Path) -> list[list[str]]:
    text = strip_tex_comments(tex_path.read_text(encoding="utf-8"))
    m = re.search(r"\\begin\{(tabularx?|longtable)\}", text)
    require(m is not None, f"No tabular/longtable found in {tex_path}")
    env = m.group(1)
    pos = m.end()
    if env == "tabularx":
        _, pos = read_balanced_group(text, pos)
        _, pos = read_balanced_group(text, pos)
    else:
        _, pos = read_balanced_group(text, pos)
    end_idx = text.find(f"\\end{{{env}}}", pos)
    require(end_idx >= 0, f"Missing \\end{{{env}}} in {tex_path}")
    body = text[pos:end_idx]
    body = re.sub(r"\\caption\{.*?\}(?:\\label\{[^}]+\})?\s*\\\\", "", body, flags=re.S)
    body = re.sub(r"\\endfirsthead.*?\\endhead", "", body, flags=re.S)
    body = re.sub(r"\\(?:toprule|midrule|bottomrule|hline|endfirsthead|endhead|endfoot|endlastfoot)\b", "", body)
    rows: list[list[str]] = []
    for raw_row in re.split(r"\\\\(?:\[[^\]]*\])?", body):
        r = raw_row.strip()
        if not r or r.startswith("\\multicolumn"):
            continue
        cells = [_norm_cell_text(c, is_typst=False) for c in re.split(r"(?<!\\)&", r)]
        if any(cells):
            rows.append(cells)
    return rows


def extract_typst_table_rows(typ_path: Path) -> list[list[str]]:
    text = strip_typst_comments(typ_path.read_text(encoding="utf-8"))
    m_cols = re.search(r"columns\s*:\s*\(([^)]+)\)", text)
    require(m_cols is not None, f"Missing columns(...) in {typ_path}")
    ncols = len([c for c in m_cols.group(1).split(",") if c.strip()])
    m_tbl = re.search(r"table\s*\(", text)
    require(m_tbl is not None, f"Missing table(...) in {typ_path}")
    tbl_body, _ = read_balanced_group(text, m_tbl.end() - 1, "(", ")")
    cells: list[str] = []
    i = 0
    while i < len(tbl_body):
        if tbl_body[i] == "[":
            content, i = read_balanced_group(tbl_body, i, "[", "]")
            cells.append(_norm_cell_text(content, is_typst=True))
        else:
            i += 1
    require(len(cells) % ncols == 0, f"Typst table cell count {len(cells)} not divisible by {ncols} in {typ_path}")
    return [cells[k:k + ncols] for k in range(0, len(cells), ncols)]


def resolve_typst_includes(root: Path, entry_rel: str) -> list[str]:
    visited: list[str] = []
    seen: set[str] = set()

    def walk(rel: str) -> None:
        if rel in seen:
            return
        seen.add(rel)
        visited.append(rel)
        p = root / rel
        require(p.is_file(), f"Missing Typst included file: {rel}")
        text = strip_typst_comments(p.read_text(encoding="utf-8"))
        for m in re.finditer(r'#(?:include|import)\s+"([^"]+\.typ)"', text):
            target = (p.parent / m.group(1)).resolve()
            t_rel = target.relative_to(root.resolve()).as_posix()
            if not t_rel.startswith("typst/lib/"):
                walk(t_rel)

    walk(entry_rel)
    return visited


def load_module(root: Path, name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, root / rel_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# =============================================================================
# Helpers: Materialized Historical Baseline & Shared Diagram Include Resolution
# =============================================================================

def _resolve_baseline_root(
    root: Path, baseline_root: Path | None = None
) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    """Return a directory containing the historical 98ddfa0 LaTeX tree.

    Uses an explicit --baseline-root if supplied, falls back to `root` if legacy root TeX files
    are still present (e.g., pre-cutover trees), and otherwise materializes the verified 211-file
    snapshot from `archive/latex_baseline_98ddfa0/BASELINE_MANIFEST.json` into a temporary directory.
    """
    if baseline_root is not None:
        return Path(baseline_root).resolve(), None
    if (root / "main.tex").is_file() and (root / "manual/main.tex").is_file():
        return root.resolve(), None
    mat = load_module(root, "aod_materialize_latex_baseline", "scripts/materialize_latex_baseline.py")
    td = tempfile.TemporaryDirectory(prefix="aod_baseline_98ddfa0_")
    mat.materialize_baseline(root, Path(td.name))
    return Path(td.name), td


def _load_figure_inventory_map(root: Path) -> dict[str, dict]:
    inv_path = root / "typst/figure_inventory.json"
    if not inv_path.is_file():
        return {}
    data = json.loads(inv_path.read_text(encoding="utf-8"))
    require(
        data.get("schema") == "aod.m4.s1b.figure-inventory.v1",
        "Invalid typst/figure_inventory.json schema",
    )
    out: dict[str, dict] = {}
    for entry in data.get("figures", []):
        comp = entry.get("target_typst_component")
        require(isinstance(comp, str) and comp not in out, f"Duplicate or missing figure component in inventory: {comp!r}")
        out[comp] = entry
    return out


def _inline_typst_diagram_includes(
    root: Path, typ_rel: str, text: str, *, for_generated_latex: bool = False
) -> str:
    """Expand diagram includes for flowchart AST parity and resolve native vector figure includes
    to their audited historical raster_path (or exported PDF path) via typst/figure_inventory.json."""
    base_dir = posixpath.dirname(typ_rel)
    inv_map = _load_figure_inventory_map(root)

    def _repl(m: re.Match) -> str:
        rel_inc = m.group(1)
        resolved = posixpath.normpath(posixpath.join(base_dir, rel_inc))
        if resolved.startswith("typst/lib/diagrams/") and resolved.endswith(".typ"):
            p = root / resolved
            require(p.is_file(), f"Missing included shared Typst diagram component: {resolved} (from {typ_rel})")
            if for_generated_latex:
                slug = Path(resolved).stem.replace("_", "-")
                prefix = "manual/figures/generated" if typ_rel.startswith("typst/manual/") else "figures/generated"
                return f'#image("/{prefix}/{slug}.pdf", width: 100%)'
            body = p.read_text(encoding="utf-8")
            body = re.sub(r'^\s*#import\s+"[^"]+"\s*:\s*\*\s*\n?', "", body, flags=re.M)
            return body
        if resolved.startswith("typst/lib/figures/") and resolved.endswith(".typ"):
            p = root / resolved
            require(p.is_file(), f"Missing included native Typst vector figure: {resolved} (from {typ_rel})")
            require(
                resolved in inv_map,
                f"Included native Typst vector figure is undeclared in typst/figure_inventory.json: {resolved}",
            )
            entry = inv_map[resolved]
            if for_generated_latex or entry.get("raster_path") is None:
                exp_rel = entry["target_exported_pdf"].removeprefix("latex/")
                return f'#image("/{exp_rel}", width: 100%)'
            raster_path = entry["raster_path"]
            return f'#image("/{raster_path}", width: 100%)'
        return m.group(0)

    return re.sub(r'#include\s+"([^"]+)"', _repl, text)


# =============================================================================
# Gate A: Baseline Immutability (Archived 98ddfa0 Snapshot + Representation Ledger)
# =============================================================================

def _unique_ledger_map(records: list, key_field: str, section_name: str) -> dict[str, dict]:
    """Index ledger records by key_field, explicitly rejecting duplicates and malformed rows."""
    require(isinstance(records, list), f"Representation ledger {section_name} must be a list")
    out: dict[str, dict] = {}
    for rec in records:
        require(isinstance(rec, dict) and isinstance(rec.get(key_field), str) and rec[key_field],
                f"Malformed entry in representation ledger {section_name}: {rec!r}")
        k = rec[key_field]
        require(k not in out, f"Duplicate entry in representation ledger {section_name}: {k}")
        out[k] = rec
    return out


M4_5_SCIENTIFIC_CONTRACT_EXTENSIONS = frozenset({
    "contracts/scientific/CELL_MEASURE_SPEC.json",
})


def verify_baseline_immutability(
    root: Path, manifest: dict, baseline_root: Path | None = None
) -> dict:
    protected = manifest["baseline_protected_sha256"]
    require(len(protected) == 211, f"Expected 211 protected baseline files, got {len(protected)}")

    tex_count = bib_count = img_count = data_count = 0
    for rel in sorted(protected):
        if rel.endswith(".tex"):
            tex_count += 1
        if rel.endswith(".bib"):
            bib_count += 1
        if rel.endswith((".png", ".jpg")):
            img_count += 1
        if rel.startswith("manual/data/"):
            data_count += 1
    require(tex_count == 54, f"Expected 54 protected TeX files, got {tex_count}")
    require(bib_count == 2, f"Expected 2 protected BibTeX files, got {bib_count}")
    require(img_count == 49, f"Expected 49 protected images, got {img_count}")
    require(data_count == 116, f"Expected 116 protected manual/data files, got {data_count}")

    snap_manifest_path = root / "archive/latex_baseline_98ddfa0/BASELINE_MANIFEST.json"
    archived_rel_map: dict[str, str] = {}
    archived_editorial_count = 0
    archived_data_count = 0
    inplace_paths: list[str] = []
    if snap_manifest_path.is_file():
        mat = load_module(root, "aod_materialize_latex_baseline", "scripts/materialize_latex_baseline.py")
        base_manifest = mat.load_and_verify_baseline(root)
        by_orig = {e["original_path"]: e for e in base_manifest["entries"]}
        require(
            set(by_orig) == set(protected),
            f"BASELINE_MANIFEST.json entry set differs from typst/manifest.json: "
            f"missing={sorted(set(protected) - set(by_orig))}, extra={sorted(set(by_orig) - set(protected))}",
        )
        for orig, expected_sha in sorted(protected.items()):
            entry = by_orig[orig]
            require(
                entry["sha256"] == expected_sha,
                f"Baseline digest mismatch between manifest and archive for {orig}",
            )
            if entry["role"] in ("archived_editorial_tex", "archived_baseline_data"):
                archived_rel_map[orig] = entry["retained_location"]
                if entry["role"] == "archived_editorial_tex":
                    archived_editorial_count += 1
                else:
                    archived_data_count += 1
            else:
                inplace_paths.append(orig)
        if baseline_root is not None:
            for key_tex in ("main.tex", "manual/main.tex"):
                p_b = Path(baseline_root) / key_tex
                require(p_b.is_file() and sha256_file(p_b) == protected[key_tex],
                        f"Materialized baseline root digest mismatch for {key_tex}")
    else:
        for rel, expected_sha in sorted(protected.items()):
            p = root / rel
            require(p.is_file(), f"Protected baseline file missing: {rel}")
            actual_sha = sha256_file(p)
            require(actual_sha == expected_sha, f"Protected baseline file modified: {rel}")
            inplace_paths.append(rel)

    # Load independently verifier-pinned Phase 1 origin inventory (works in BOTH Git and non-Git source.zip!)
    origin_inv_path = root / PHASE1_ORIGIN_INVENTORY_REL
    require(
        origin_inv_path.is_file(),
        f"Missing bound accepted Phase 1 origin inventory: {PHASE1_ORIGIN_INVENTORY_REL}",
    )
    actual_origin_sha = sha256_file(origin_inv_path)
    require(
        actual_origin_sha == PHASE1_ORIGIN_INVENTORY_SHA256,
        f"Accepted Phase 1 origin inventory digest mismatch ({PHASE1_ORIGIN_INVENTORY_REL}): "
        f"expected {PHASE1_ORIGIN_INVENTORY_SHA256}, got {actual_origin_sha}",
    )
    origin_inv = json.loads(origin_inv_path.read_text(encoding="utf-8"))
    require(
        origin_inv.get("schema") == "aod.m4.phase1.origin-inventory.v1"
        and origin_inv.get("phase1_accepted_commit") == PHASE1_ACCEPTED_COMMIT
        and origin_inv.get("phase1_accepted_tree") == PHASE1_ACCEPTED_TREE
        and origin_inv.get("historical_scientific_baseline_commit") == SCIENTIFIC_BASELINE_COMMIT,
        "Accepted Phase 1 origin inventory metadata mismatch",
    )

    p1_contracts: dict[str, str] = origin_inv["phase1_contracts_sha256"]
    p1_cb: dict = origin_inv["phase1_canonical_bindings"]
    p1_frozen: dict[str, str] = p1_cb["frozen_sha256"]

    # Cross-check against live Git commits when .git is present (both 98ddfa0 and e6f2097)
    git_hist_checked = False
    git_p1_checked = False
    if (root / ".git").exists():
        chk_hist = subprocess.run(
            ["git", "rev-parse", "--verify", f"{SCIENTIFIC_BASELINE_COMMIT}^{{commit}}"],
            cwd=root, capture_output=True, text=True,
        )
        if chk_hist.returncode == 0:
            git_hist_checked = True
            if inplace_paths:
                diff_proc = subprocess.run(
                    ["git", "diff", "--name-only", SCIENTIFIC_BASELINE_COMMIT, "--", *sorted(inplace_paths)],
                    cwd=root, capture_output=True, text=True, check=True,
                )
                changed = [ln for ln in diff_proc.stdout.splitlines() if ln.strip()]
                require(not changed, f"Preserved baseline files differ from {SCIENTIFIC_BASELINE_COMMIT}: {changed}")
            for orig, retained in sorted(archived_rel_map.items()):
                orig_bytes = subprocess.run(
                    ["git", "show", f"{SCIENTIFIC_BASELINE_COMMIT}:{orig}"],
                    cwd=root, capture_output=True, check=True,
                ).stdout
                require(
                    hashlib.sha256(orig_bytes).hexdigest() == sha256_file(root / retained),
                    f"Archived baseline copy differs from {SCIENTIFIC_BASELINE_COMMIT}:{orig}: {retained}",
                )
            hist_cb_bytes = subprocess.run(
                ["git", "show", f"{SCIENTIFIC_BASELINE_COMMIT}:contracts/scientific/CANONICAL_BINDINGS.json"],
                cwd=root, capture_output=True, check=True,
            ).stdout
            require(
                hashlib.sha256(hist_cb_bytes).hexdigest() == origin_inv["historical_canonical_bindings_sha256"],
                "Historical 98ddfa0 CANONICAL_BINDINGS.json digest disagrees with origin inventory",
            )

        chk_p1 = subprocess.run(
            ["git", "rev-parse", "--verify", f"{PHASE1_ACCEPTED_COMMIT}^{{commit}}"],
            cwd=root, capture_output=True, text=True,
        )
        if chk_p1.returncode == 0:
            git_p1_checked = True
            p1_tree_actual = subprocess.run(
                ["git", "rev-parse", f"{PHASE1_ACCEPTED_COMMIT}^{{tree}}"],
                cwd=root, capture_output=True, text=True, check=True,
            ).stdout.strip()
            require(
                p1_tree_actual == PHASE1_ACCEPTED_TREE,
                f"Accepted Phase 1 tree mismatch: expected {PHASE1_ACCEPTED_TREE}, got {p1_tree_actual}",
            )
            for c_rel, c_sha in sorted(p1_contracts.items()):
                c_bytes = subprocess.run(
                    ["git", "show", f"{PHASE1_ACCEPTED_COMMIT}:{c_rel}"],
                    cwd=root, capture_output=True, check=True,
                ).stdout
                require(
                    hashlib.sha256(c_bytes).hexdigest() == c_sha,
                    f"Phase 1 contract digest mismatch vs Git {PHASE1_ACCEPTED_COMMIT}:{c_rel}",
                )

    # -------------------------------------------------------------------------
    # Relation 1: Historical Scientific Preservation (98ddfa0 -> candidate)
    # Runs identically in BOTH Git and non-Git source.zip contexts.
    # -------------------------------------------------------------------------
    curr_cb = json.loads((root / "contracts/scientific/CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
    tex_to_typ = {e["tex_source"]: e["typst_target"] for e in manifest["active_source_map"]}

    require(curr_cb.get("schema") == p1_cb["contract_schema"], "CANONICAL_BINDINGS.json schema changed")
    require(curr_cb.get("formulas") == p1_cb["formulas"],
            "Scientific formulas in CANONICAL_BINDINGS.json changed")
    require(len(curr_cb.get("ownership", [])) == len(p1_cb["ownership"]),
            "Ownership group count changed in CANONICAL_BINDINGS.json")
    for b_row, c_row in zip(p1_cb["ownership"], curr_cb["ownership"]):
        exp_row = dict(b_row)
        if c_row.get("path") != b_row["path"]:
            exp_row["path"] = tex_to_typ.get(b_row["path"], b_row["path"])
        require(c_row == exp_row, f"Ownership scientific content changed for {b_row.get('concept')}")
    for b_fam, c_fam in zip(p1_cb["manual_families"], curr_cb["manual_families"]):
        exp_fam = dict(b_fam)
        if c_fam.get("manual_path") != b_fam["manual_path"]:
            exp_fam["manual_path"] = tex_to_typ.get(b_fam["manual_path"], b_fam["manual_path"])
        require(c_fam == exp_fam, f"Manual family scientific content changed for {b_fam.get('id')}")
    for b_sig, c_sig in zip(p1_cb["unique_signatures"], curr_cb["unique_signatures"]):
        exp_sig = dict(b_sig)
        if c_sig.get("path") != b_sig["path"]:
            exp_sig["path"] = tex_to_typ.get(b_sig["path"], b_sig["path"])
        require(c_sig == exp_sig, f"Unique signature scientific content changed for {b_sig.get('anchor')}")
    require(set(curr_cb.get("supplemental_formulas", {})) == set(p1_cb["supplemental_formulas"]),
            "Supplemental formula keys changed in CANONICAL_BINDINGS.json")
    for k, b_sup in p1_cb["supplemental_formulas"].items():
        c_sup = curr_cb["supplemental_formulas"][k]
        exp_sup = dict(b_sup)
        if c_sup.get("path") != b_sup["path"]:
            exp_sup["path"] = tex_to_typ.get(b_sup["path"], b_sup["path"])
        require(c_sup == exp_sup, f"Supplemental formula content changed for {k}")

    # -------------------------------------------------------------------------
    # Relation 2: Accepted Phase 1 (e6f2097) -> Phase 2 Representation Transition
    # Runs identically in BOTH Git and non-Git source.zip contexts.
    # -------------------------------------------------------------------------
    ledger_path = root / "typst/representation_change_ledger.json"
    require(ledger_path.is_file(), f"Missing representation change ledger: {ledger_path}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    require(
        ledger.get("schema") == "aod.m4.phase2.representation-change-ledger.v1",
        "Invalid representation_change_ledger.json schema",
    )
    require(
        ledger.get("historical_scientific_baseline_commit") == SCIENTIFIC_BASELINE_COMMIT,
        f"Representation ledger historical_scientific_baseline_commit mismatch: "
        f"expected {SCIENTIFIC_BASELINE_COMMIT}, got {ledger.get('historical_scientific_baseline_commit')!r}",
    )
    require(
        ledger.get("phase1_accepted_commit") == PHASE1_ACCEPTED_COMMIT,
        f"Representation ledger declared origin phase1_accepted_commit mismatch: "
        f"expected {PHASE1_ACCEPTED_COMMIT}, got {ledger.get('phase1_accepted_commit')!r}",
    )

    # 2a. Complete contracts/scientific/ transition check (all 17 contracts vs Phase 1)
    contract_amendments = _unique_ledger_map(
        ledger.get("contract_amendments", []), "contract", "contract_amendments"
    )
    contracts_dir = root / "contracts/scientific"
    on_disk_contracts = {
        p.relative_to(root).as_posix()
        for p in contracts_dir.rglob("*")
        if p.is_file() or p.is_symlink()
    }
    require(
        on_disk_contracts == set(p1_contracts),
        f"contracts/scientific/ inventory changed vs Phase 1: "
        f"extra={sorted(on_disk_contracts - set(p1_contracts))}, "
        f"missing={sorted(set(p1_contracts) - on_disk_contracts)}",
    )
    for c_path, rec in sorted(contract_amendments.items()):
        require(c_path in p1_contracts, f"Contract amendment references unknown Phase 1 contract: {c_path}")
        if c_path in M4_5_SCIENTIFIC_CONTRACT_EXTENSIONS:
            require(
                rec.get("scientific_substance_changed") is True
                and rec.get("scope") == "m4_5_g6_tesseract_extension",
                f"M4.5 scientific contract extension must declare scientific_substance_changed=true "
                f"and scope='m4_5_g6_tesseract_extension': {c_path}",
            )
        else:
            require(rec.get("scientific_substance_changed") is False,
                    f"Contract amendment must declare scientific_substance_changed=false: {c_path}")
        require(
            rec.get("old_sha256") == p1_contracts[c_path],
            f"Contract amendment old_sha256 for {c_path} disagrees with accepted Phase 1 ({PHASE1_ACCEPTED_COMMIT}): "
            f"expected {p1_contracts[c_path]}, got {rec.get('old_sha256')}",
        )
        actual_c_sha = sha256_file(root / c_path)
        require(
            rec.get("new_sha256") == actual_c_sha,
            f"Contract amendment new_sha256 for {c_path} disagrees with current file: "
            f"ledger={rec.get('new_sha256')}, disk={actual_c_sha}",
        )
        require(
            rec.get("old_sha256") != rec.get("new_sha256"),
            f"No-op contract amendment declared in ledger: {c_path}",
        )
    untouched_contracts = 0
    for c_path, p1_sha in sorted(p1_contracts.items()):
        if c_path not in contract_amendments:
            actual_c_sha = sha256_file(root / c_path)
            require(
                actual_c_sha == p1_sha,
                f"Undeclared contract transition outside representation ledger: {c_path} "
                f"(Phase 1={p1_sha}, current={actual_c_sha})",
            )
            untouched_contracts += 1

    # 2b. Complete frozen_sha256 transition check (vs accepted Phase 1 e6f2097, NOT 98ddfa0)
    rel_by_old = _unique_ledger_map(
        ledger.get("frozen_sha256_relocations", []), "old_path", "frozen_sha256_relocations(old_path)"
    )
    rel_by_new = _unique_ledger_map(
        ledger.get("frozen_sha256_relocations", []), "new_path", "frozen_sha256_relocations(new_path)"
    )
    amended = _unique_ledger_map(
        ledger.get("frozen_sha256_amendments", []), "path", "frozen_sha256_amendments"
    )
    added = _unique_ledger_map(
        ledger.get("frozen_sha256_additions", []), "path", "frozen_sha256_additions"
    )

    # Disjointness & domain checks
    overlap_ra = set(rel_by_old) & set(amended)
    require(not overlap_ra, f"Path declared as both relocated and amended: {sorted(overlap_ra)}")
    overlap_add = (set(added) & set(p1_frozen)) | (set(added) & set(rel_by_new))
    require(not overlap_add, f"Added frozen_sha256 path collides with Phase 1 or relocated path: {sorted(overlap_add)}")
    unknown_rel = set(rel_by_old) - set(p1_frozen)
    require(not unknown_rel, f"Relocation references path absent from Phase 1 frozen_sha256: {sorted(unknown_rel)}")
    unknown_amd = set(amended) - set(p1_frozen)
    require(not unknown_amd, f"Amendment references path absent from Phase 1 frozen_sha256: {sorted(unknown_amd)}")

    curr_frozen = curr_cb["frozen_sha256"]
    for p1_k, p1_sha in sorted(p1_frozen.items()):
        if p1_k in rel_by_old:
            rel_rec = rel_by_old[p1_k]
            new_k = rel_rec["new_path"]
            require(
                rel_rec.get("sha256") == p1_sha,
                f"Relocated frozen_sha256 ledger digest mismatch for {p1_k}: "
                f"Phase 1={p1_sha}, ledger={rel_rec.get('sha256')}",
            )
            require(
                curr_frozen.get(new_k) == p1_sha,
                f"Relocated frozen_sha256 entry {p1_k} -> {new_k} digest mismatch in CANONICAL_BINDINGS.json",
            )
            require(
                (root / new_k).is_file() and sha256_file(root / new_k) == p1_sha,
                f"Relocated file on disk disagrees with Phase 1 digest: {new_k}",
            )
        elif p1_k in amended:
            amd_rec = amended[p1_k]
            require(
                amd_rec.get("old_sha256") == p1_sha,
                f"Amended frozen_sha256 old_sha256 for {p1_k} disagrees with accepted Phase 1 "
                f"({PHASE1_ACCEPTED_COMMIT}): expected {p1_sha}, got {amd_rec.get('old_sha256')}",
            )
            require(
                amd_rec.get("new_sha256") == curr_frozen.get(p1_k),
                f"Amended frozen_sha256 new_sha256 for {p1_k} disagrees with CANONICAL_BINDINGS.json: "
                f"ledger={amd_rec.get('new_sha256')}, contract={curr_frozen.get(p1_k)}",
            )
            require(
                (root / p1_k).is_file() and sha256_file(root / p1_k) == amd_rec["new_sha256"],
                f"Amended file on disk disagrees with ledger new_sha256: {p1_k}",
            )
            require(
                amd_rec["old_sha256"] != amd_rec["new_sha256"],
                f"No-op frozen_sha256 amendment declared in ledger: {p1_k}",
            )
        else:
            require(
                curr_frozen.get(p1_k) == p1_sha,
                f"Undeclared frozen_sha256 transition outside representation ledger: {p1_k} "
                f"(Phase 1={p1_sha}, current={curr_frozen.get(p1_k)})",
            )
            require(
                (root / p1_k).is_file() and sha256_file(root / p1_k) == p1_sha,
                f"Untouched frozen_sha256 file on disk disagrees with Phase 1 digest: {p1_k}",
            )

    expected_keys = (set(p1_frozen) - set(rel_by_old)) | set(rel_by_new) | set(added)
    require(
        set(curr_frozen) == expected_keys,
        f"frozen_sha256 key set disagrees with representation ledger: "
        f"extra={sorted(set(curr_frozen) - expected_keys)}, "
        f"missing={sorted(expected_keys - set(curr_frozen))}",
    )
    for add_k, add_rec in sorted(added.items()):
        require(
            curr_frozen.get(add_k) == add_rec.get("sha256"),
            f"Added frozen_sha256 entry {add_k} disagrees with CANONICAL_BINDINGS.json",
        )
        require(
            (root / add_k).is_file() and sha256_file(root / add_k) == add_rec["sha256"],
            f"Added frozen_sha256 file on disk disagrees with ledger: {add_k}",
        )

    expected_summary = {
        "contracts_amended": len(contract_amendments),
        "contracts_untouched": untouched_contracts,
        "frozen_relocations": len(rel_by_old),
        "frozen_additions": len(added),
        "frozen_amendments": len(amended),
        "frozen_total_after": len(curr_frozen),
    }
    require(
        ledger.get("summary") == expected_summary,
        f"Representation ledger summary disagrees with actual entries: "
        f"expected={expected_summary}, got={ledger.get('summary')}",
    )

    return {
        "protected_baseline_files": len(protected),
        "archived_editorial_tex_files": archived_editorial_count,
        "archived_baseline_data_files": archived_data_count,
        "preserved_in_place_files": len(inplace_paths),
        "tex_files_unchanged": tex_count,
        "bib_files_unchanged": bib_count,
        "image_files_unchanged": img_count,
        "manual_data_files_unchanged": data_count,
        "historical_baseline_preservation_verified": True,
        "phase1_transition_verified": True,
        "phase1_accepted_commit": PHASE1_ACCEPTED_COMMIT,
        "phase1_origin_inventory_sha256": PHASE1_ORIGIN_INVENTORY_SHA256,
        "git_baseline_cross_checked": git_hist_checked,
        "git_phase1_cross_checked": git_p1_checked,
        "representation_change_ledger_verified": True,
        "amended_contracts_count": len(contract_amendments),
        "amended_frozen_entries_count": len(amended),
    }


# =============================================================================
# Gate A2: Evaluation Policy (trusted template pins, manifest digests, and a
# mode-aware allowlist for every Typst content file). Typst show rules, local
# definitions, styling and overlays can change the evaluated publication without
# changing source tokens; content files may therefore only use the reviewed,
# content-neutral vocabulary below, and the files that define evaluation
# semantics are pinned byte-for-byte by this verifier.
# =============================================================================

def _math_ast_sha256(mtk: tuple) -> str:
    return hashlib.sha256(repr(mtk).encode("utf-8")).hexdigest()


POST_BASELINE_MANUAL_EXTENSION_UNITS = frozenset({
    "typst/manual/sections/00_scope.typ",
    "typst/manual/sections/06_field_dynamics_applications.typ",
    "typst/manual/sections/07_galactic_lensing_plan.typ",
    "typst/manual/sections/09_prediction_test_fixture_registry.typ",
    "typst/manual/appendices/A_simulation_fixtures_and_tau_prediction_context.typ",
    "typst/manual/appendices/B_quarantined_external_comparison.typ",
    "typst/manual/appendices/C_3d_coordinate_phase_cycle_delta3_fixture.typ",
})

POST_BASELINE_COMPACTED_MAIN_UNITS = frozenset({
    'typst/sections/05_curl_closure_duon_current.typ',
    'typst/sections/06_wave_state_relational_time.typ',
    'typst/sections/06_field.typ',
})

POST_BASELINE_COMPACTED_MAIN_INLINE_MATH: dict[str, frozenset] = {
    'typst/sections/05_curl_closure_duon_current.typ': frozenset(),
    'typst/sections/06_wave_state_relational_time.typ': frozenset({
        ('MATH', ('group', '(', ('seq', (('subsup', ('accent', 'tilde', ('sym', 'S')), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('accent', 'tilde', ('sym', 'S')), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'times')))))),
        ('MATH', ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'times')))))),
        ('MATH', ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'))), ('sym', 'times')))))),
        ('MATH', ('seq', (('op', '<='), ('sym', 'k'), ('op', '-'), ('num', '1')))),
        ('MATH', ('seq', (('sub', ('sym', 'K'), ('seq', (('sym', 'k'), ('op', '+'), ('num', '1')))), ('op', ':='), ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'times')))))))),
        ('MATH', ('seq', (('sub', ('sym', 'K'), ('sym', 'k')), ('op', ':='), ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'))), ('sym', 'times')))))))),
        ('MATH', ('seq', (('sub', ('sym', 'K'), ('sym', 'k')), ('op', ':='), ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'))), ('sym', 'times'))))), ('op', ','), ('sub', ('sym', 'X'), ('sym', 'k')), ('op', '='), ('sub', ('sym', 'E'), ('sym', 'B')), ('group', '(', ('sub', ('sym', 'K'), ('sym', 'k'))), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W')), ('op', '='), ('sub', ('font', 'cal', ('sym', 'U')), ('sym', 'B')), ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'times')), ('op', ','), ('group', '(', ('seq', (('sub', ('sym', 'Y'), ('sym', 'k')), ('op', ','), ('sub', ('sym', 'beta'), ('sym', 'k')), ('op', ','), ('sub', ('sym', 'Delta'), ('seq', (('text', 'lead/lag'), ('op', ','), ('op', '<='), ('sym', 'k')))))))))), ('op', ','), ('sub', ('sym', 'K'), ('seq', (('sym', 'k'), ('op', '+'), ('num', '1')))), ('op', ':='), ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'times'))))), ('op', ','), ('sub', ('sym', 'X'), ('seq', (('sym', 'k'), ('op', '+'), ('num', '1')))), ('op', '='), ('sub', ('sym', 'E'), ('sym', 'B')), ('group', '(', ('sub', ('sym', 'K'), ('seq', (('sym', 'k'), ('op', '+'), ('num', '1'))))), ('op', '.')))),
        ('MATH', ('seq', (('sub', ('sym', 'Pi'), ('text', 'cut')), ('group', '(', ('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W')))))),
        ('MATH', ('seq', (('sub', ('sym', 'Pi'), ('text', 'cut')), ('group', '(', ('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W'))), ('op', '='), ('sub', ('sym', 'Pi'), ('text', 'cut')), ('group', '(', ('subsup', ('accent', 'tilde', ('sym', 'S')), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W'))), ('text', 'and'), ('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W')), ('op', '!='), ('subsup', ('accent', 'tilde', ('sym', 'S')), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W')), ('text', 'with'), ('group', '(', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'times'))))), ('op', '!='), ('group', '(', ('seq', (('subsup', ('accent', 'tilde', ('sym', 'S')), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'W')), ('op', ','), ('subsup', ('accent', 'tilde', ('sym', 'S')), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'times'))))), ('op', '.')))),
        ('MATH', ('seq', (('sub', ('sym', 'X'), ('sym', 'k')), ('op', '='), ('sub', ('sym', 'E'), ('sym', 'B')), ('group', '(', ('sub', ('sym', 'K'), ('sym', 'k')))))),
        ('MATH', ('seq', (('sub', ('sym', 'k'), ('sym', 's')), ('op', '<='), ('sym', 'k')))),
        ('MATH', ('seq', (('sub', ('sym', 'k'), ('sym', 's')), ('op', '>'), ('sym', 'k')))),
        ('MATH', ('seq', (('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W')), ('op', '='), ('subsup', ('font', 'cal', ('sym', 'U')), ('sym', 'B'), ('text', 'M')), ('group', '(', ('seq', (('sub', ('sym', 'Pi'), ('text', 'cut')), ('group', '(', ('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'))), ('sym', 'W'))), ('op', ','), ('sub', ('text', 'input'), ('sym', 'k'))))), ('op', '.')))),
        ('MATH', ('seq', (('sym', 'k'), ('op', '->'), ('sym', 'k'), ('op', '+'), ('num', '1')))),
        ('MATH', ('seq', (('sym', 'k'), ('sym', 'in'), ('font', 'bb', ('sym', 'Z'))))),
        ('MATH', ('sub', ('font', 'cal', ('sym', 'U')), ('sym', 'B'))),
        ('MATH', ('sub', ('sym', 'Delta'), ('seq', (('text', 'lead/lag'), ('op', ','), ('op', '<='), ('sym', 'k'))))),
        ('MATH', ('sub', ('sym', 'E'), ('sym', 'B'))),
        ('MATH', ('sub', ('sym', 'X'), ('seq', (('sym', 'k'), ('op', '+'), ('num', '1'))))),
        ('MATH', ('sub', ('sym', 'Y'), ('sym', 'k'))),
        ('MATH', ('sub', ('sym', 'beta'), ('sym', 'k'))),
        ('MATH', ('sub', ('text', 'input'), ('sym', 'k'))),
        ('MATH', ('subsup', ('font', 'cal', ('sym', 'U')), ('sym', 'B'), ('text', 'M'))),
        ('MATH', ('subsup', ('sym', 'S'), ('seq', (('sym', 'B'), ('op', ','), ('sym', 'i'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'W'))),
        ('MATH', ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('op', '<='), ('sym', 'k'))), ('sym', 'times'))),
        ('MATH', ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'))), ('sym', 'times'))),
        ('MATH', ('subsup', ('sym', 'S'), ('seq', (('sym', 'I'), ('op', ','), ('sym', 'B'), ('op', ','), ('sym', 'k'), ('op', '+'), ('num', '1'))), ('sym', 'times'))),
        ('MATH', ('subsup', ('sym', 'e'), ('sym', 's'), ('sym', 'times'))),
        ('MATH', ('subsup', ('sym', 'psi'), ('sym', 'k'), ('text', 'bias'))),
        ('MATH', ('sup', ('sym', 'Gamma'), ('sym', 'times'))),
        ('MATH', ('sym', 'k')),
    }),
    'typst/sections/06_field.typ': frozenset({
        ('MATH', ('seq', (('op', '|'), ('sym', 'G'), ('op', '|'), ('op', '='), ('sym', 'N')))),
        ('MATH', ('seq', (('sub', ('font', 'cal', ('sym', 'C')), ('sym', 'f')), ('group', '[', ('seq', (('sym', 'p'), ('op', ':'), ('sym', 'q'))))))),
        ('MATH', ('seq', (('sub', ('sym', 'E'), ('num', '4')), ('op', '='), ('text', 'tetron')))),
        ('MATH', ('seq', (('sub', ('sym', 'Z'), ('sym', 'f')), ('op', '='), ('group', '(', ('seq', (('sub', ('font', 'frak', ('sym', 'c')), ('sym', 'f')), ('op', ','), ('subsup', ('sym', 'I'), ('sym', 'f'), ('sym', 'c')), ('op', ','), ('subsup', ('sym', 'B'), ('sym', 'f'), ('sym', 'e'))))), ('op', '->'), ('sub', ('sym', 'Z'), ('seq', (('sym', 'f'), ('op', '+'), ('num', '1')))), ('op', '='), ('group', '(', ('seq', (('sub', ('font', 'frak', ('sym', 'c')), ('seq', (('sym', 'f'), ('op', '+'), ('num', '1')))), ('op', ','), ('subsup', ('sym', 'I'), ('seq', (('sym', 'f'), ('op', '+'), ('num', '1'))), ('sym', 'c')), ('op', ','), ('subsup', ('sym', 'B'), ('seq', (('sym', 'f'), ('op', '+'), ('num', '1'))), ('sym', 'e')))))))),
        ('MATH', ('seq', (('sub', ('text', 'C'), ('num', '10')), ('op', '='), ('text', 'decon')))),
        ('MATH', ('seq', (('sub', ('text', 'C'), ('num', '6')), ('op', '='), ('text', 'hexon')))),
        ('MATH', ('seq', (('sub', ('text', 'C'), ('num', '8')), ('op', '='), ('text', 'octon')))),
        ('MATH', ('seq', (('sub', ('text', 'C'), ('seq', (('num', '2'), ('sym', 'm')))), ('op', '='), ('text', 'support enclosure of order'), ('num', '2'), ('sym', 'm'), ('op', ','), ('sym', 'm'), ('op', '>='), ('num', '3'), ('op', ',')))),
        ('MATH', ('seq', (('sym', 'R'), ('sym', 'D'), ('group', '(', ('seq', (('sub', ('font', 'cal', ('sym', 'C')), ('sym', 'f')), ('group', '[', ('seq', (('sym', 'p'), ('op', ':'), ('sym', 'q')))))))))),
        ('MATH', ('seq', (('sym', 'S'), ('op', '='), ('sub', ('sym', 'sum'), ('sym', 'g')), ('sym', 'eta'), ('group', '(', ('sym', 'g')), ('op', '='), ('sym', 'eta'), ('group', '(', ('sym', 'a')), ('sym', 'S'), ('op', '='), ('num', '0')))),
        ('MATH', ('seq', (('sym', 'm'), ('op', ':'), ('sym', 'm'), ('op', ':'), ('num', '0'), ('op', ':'), ('op', ':'), ('num', '2'), ('sym', 'm')))),
        ('MATH', ('seq', (('sym', 'm'), ('op', '>='), ('num', '3')))),
        ('MATH', ('seq', (('sym', 'n'), ('op', '>'), ('num', '5')))),
    }),
}

POST_BASELINE_COMPACTED_MANUAL_UNITS = frozenset({
    'typst/manual/sections/00_awareness_fixtures.typ',
    'typst/manual/sections/00_dec_ledger.typ',
    'typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ',
    'typst/manual/sections/01_cell_measures.typ',
    'typst/manual/sections/01_rest_energy_prediction.typ',
    'typst/manual/sections/02_hydrogen_facing_shell_tests.typ',
    'typst/manual/sections/02_mapping_error.typ',
    'typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ',
    'typst/manual/sections/03_temporal_observation.typ',
    'typst/manual/sections/04_boundary_current_applications.typ',
    'typst/manual/sections/05_solar_system_field_tests.typ',
})

POST_BASELINE_COMPACTED_MANUAL_INLINE_MATH: dict[str, frozenset[str]] = {
    'typst/manual/sections/00_awareness_fixtures.typ': frozenset({
        '02c15eb75da31d728474a51bf21046f730a182ca9ecd0fa7377c581c5c2bf8f9', '05d795c8215cf2e51b2c47327feb6bb9358a823ef30614cdf16f5b7856cf66dc',
        '0d9bbcd1431e560339c41d69dbf136afd03d6d47e94368d3be03d73df9ce4da2', '1d7cb604bf0197513615eaac0c798c9fbe7fd868cf337ccbc978c46f94377ac1',
        '217c401ad6814365f8234ffca5ba19a85b37e6c48be8d9c49e8155861a43610d', '294f57f3604fc832623b611b2a16b7b9cf9608d41d9ebdb425a128a8246bcfc9',
        '33f5ad116539d52d2422ecabb43a347dd8d149bb0f56c30383630b43d0e5b1ee', '350847076ba28eee4ce821553dec5bbfd66c866c0c66ec159df94258059c339a',
        '3e4177875633200099918bfac5fd1a29bebcfecf8b32f6c6fa73a7c63bde5643', '433e98c29f332169c143c579a5a7e2a2f45919b4b057d05e04a26a0496fe5f63',
        '4cff5fb3141cf8cd834d837b7f0bf0e1c23bb89763d67c0918de2986a9dadbca', '5cd9b4b58d1614de6c4948c009e840d6bdb82560fb11d98b30c0fe8012b0c66d',
        '5d99428870aeacffae98c07e6bfda90a7ff6a51c936897651878825095c3d3b0', '5ed8e6f59469db11e90d0755b8749360fec2dbfb01390390ed556546b146120b',
        '65b2c3513c4d65104ff87be22036c91fb7ab7e7975875c4037d7735acfd3f7e3', '7a872ca9e2cbe83043b8f210aafbf93cc853ab37bc6c1cce9c6d5bc824ba057b',
        '8610d58fc11f34097c21bb7462f517f2a92eda4afb102731cd6871a3b4e5b182', '94948dd4a1746c42f65e7d5ef8fddd797a29b96c6ca8a541e5c4ef7494affda5',
        '9a676c7101c0f8140f82fa9454929f930c16fdc2aad9ed16c3ae4c68f3149c4b', 'a5be827dc485dc0505defd76f82f6f29969fbb0b9497663a77c062a5af525901',
        'a6099fe81e2ef2ca1288cb240c8dc8ae5c4874f1dfe0a176bfd40e3ed8f533d0', 'c171e9240d8fb0afea4324b0fcc0f72051d7b369dcd6873bd7fc864eca8edd1c',
        'c656f67f523d031aa9598a0d94d951358dfe39699e2b3519165d6e2e64fba366', 'd555f66e08c4284391d6c681dfc85b7849e1c5e8ec191cfd952a3e9a25777e48',
        'e9cd25c86b67f7c12073fee722f1d9fb092c98f558bd3a9555ffbca5e6905d94', 'eca5e163ae522b5676d0711e3765f14ab02f96bb42ce4c08b10f0cd1bed5e22d',
        'ed8819fc63fb863c07fdbfbd69beb2e9ac84318dc2f57b633a620ed48a159f74', 'ee39fe655841c9d2e9f70fd33ac508b564bca48461e7d2934b9e3db03863b0be',
        'eee5031080f85fc8d7ed109399d2bc8f8c276fecca5f3bac43bdc09ccdd4ab7c', 'efc46756c2f86ae8eadbd8efcab47b3025c3a64a8f55cc0cb45297b39b58d456',
        'f50d128cdaa67d6907391c56f3e167547422f5e167acafd3c1b894b8d2ad3dc0',
    }),
    'typst/manual/sections/00_dec_ledger.typ': frozenset({
        '017627aee6eefd3b485324f41c11e7833ef6f8858543718bc9de9688281ce766', '040cb1b8a19b3bd8bfcb129bc20216bef1532f5cbca953135b27437afd8644b0',
        '04936eead3086f56a6713a1312fe564b6af9572e72a9388409d61be5dcac539a', '04ca342432ece0d0133d78220f33f28b4a704f08172624a82a2c3d211a6fed6f',
        '072b116ab090f77e74b3bce0ede252cacfa9fb0e10996332bca6c3f80bb28180', '074f5db7faa407dd9137450dfe3481a0e5012c823a8504c057b8e1e71820c544',
        '14864bca73e4115f7af0a5a2229aac0e8997fed3b80b0fd911cc3c0664bd2a7b', '187ba12e478c9aed1ae0ddbb9743577ab288af2bb4be477657a81bdc5e8c005c',
        '1bb9936e26f69d1eae667d296f8b54bffe3607a813bea51f14a68ad6cd48af62', '1d90f23a7adb65a0b078d1db650807fc3d417e43bbca263df564372cd3ebba5a',
        '1daaee068f943888594f0b465a589ae8db8438894c6ab6c6afbab98cdab25d4e', '1fdac62f6319bdc6ae85ed8c5989d4139ed9ae9613b706356d8e87fea4749983',
        '21a653480c7c3e08ba93d7d7f87a67aaa5479d5addee754877812a26a302b3e6', '2a5349cfa49c0804a4ccac9984f8a7446ec3f1bb841fa3a561fa119c8642a0f8',
        '35f6ffe577c718be9d73dce2c5d0b790081d38574db2d831a65144cb5f645902', '363a58f2c226f316862cf47062d1e516df22018a38399ebc573fc8b4b439ca47',
        '36cf5bfeef0ce3483456a1059f8d09d9a5c738521fa8843107b98e1ef7428803', '3979ddfd4eb10c55ec47eefbb659a37236a2572671b411661aa7b7fc42d42912',
        '40955a9b98c072d8e7a67934d5f9bd2c236c984c6569343b77c3127b7871ad4f', '443eb4291c452dbc6822bf101fb78777f94afc979ba861e9868779a00b71b992',
        '447407aef84e9cddd883511e876c9ac6a6962132ac01764d69df28db367fa7a2', '4cd528f4c4c81bb49cfb36a214bd5c8d1a51c0b52fac07e27fdca945bf70e384',
        '51678d8ab013a588644952f7f62e79c1d856f64dec5fa365f4c528d305b48174', '57788e7162edcbc441a8a3e846c4bd570e515698bab962637d27fa4ce7aaaf6e',
        '5916223fc69cd35ec2c4e6e56bd905da8df8fd9b36df80542d9d2b7441920f89', '59257cba7c41af156331c322aa4f97d644656158a3263769a325c60c64830b51',
        '592841ee2f7726067e31daa10926a92220867470cfe9ff914918b7ceaa0cb1ee', '5a590b1dee53874c9745e0b78005970c08908b34ebd824d8fe427c7b185d3677',
        '5ca49d499bfe4328fe61407055f8dd40080ffa56d2f89e944a1ab20e817fe252', '5fa179814c451ee3cd787f0f81443990c29d99a00722d64b0b0ea6b0e97aed25',
        '5fbccc30cbc3da292bb92bc8e483274879cc8100c683b8840beeb8dc5cbf3348', '6006c17d9170fff7e1dbe6fee18d9b46f4e752715ae45d7268564872ad6e66a7',
        '64559747df43dcf396d679a35f533c446d99f85a2e1ed085c837891b566daa03', '666531bc39d30797620515ab02c7ad68f113415a50ed97e365fd763a26030ca7',
        '693e97d8214f4fd911a14626b0cb2f210e67f2fec7d5466b47f66a7b32006959', '6aebac3cb81d60da2442a8a159d3d2211911daf3e8d1691ad7e1820bcc5d8ec5',
        '6b5ee5031d31f88f32ba1a99019ee3305cee8ba986fa3e271f29d4d52c1a31be', '6f597a20dd5871a3fb38f8ed94e9a1f7ea337498e20cf2cf1e958b9629a73e71',
        '6f9c00f1b48e762bd47731379ebdf3f7f9946652ae12f3f5c140dca800f5dbad', '749f6acccd591c1a91bde1a7b52aa9906a2c900bb56b8feb3e0be787be48bec0',
        '8652a549b7f15a7edce0de26965b251e0d4b0a637eacca09da84e5ac94d75ceb', '88733fae8ec2cc9bb1e5120f6073b289707d623626f7eafae00eb4b894a2f0c8',
        '8d919be3c654f199a734da63dd46f8f1e5f13e9a0545bc634faf0f718364506c', '91b0d673f75ba94e5e594abd4a0a55cad7d39bc0d5d8ceceb574219f92a6cfe8',
        '9326b80225af71b04a5843657c51a5bfc706f9add467169f14367c5a989dcc8f', '9379da999737169a864159f444e1b1658e18e71199ca0892cdd7d6e0d95134b5',
        '948d59fbf9e0cf396177c3936e1b43938bbba01449a31d77aeb202fbc68d9b56', '9543b0cd51476fd373469293ff054a983d3cf85435415ab5c9ec65b653b5acfa',
        '9680f074063b729007fbb86b9bc4bd7d166e3943d9a76d7370ab160e655aba8a', '971ccf57afd16655bb459555078ca9024a9aeb74790a3ae43586b35d2b029f45',
        '97d35ef25493c123267e21163cb6fed4cfe63430faa929a101001d41f6aaa3e6', '9e09194b51707d9712aa55fd5e3f6cb351cb47fb48b3583b811a8ec5ee399679',
        '9ef2cddaaf2b93ff20538cba727536c2aa3c72a3a78c48171d0134ce0c04aaab', 'a1e342291cb1ebd2181b5fe3a6f2aecd096e24cc8834f3e6516ff741728f8685',
        'aa0025ea06b76036a16a5114047b92cf4d4275d1ef84b6f9f7019bd2e0955edf', 'ac38678d51f1ef87d8ebc74a2105f4afb4c62f0fa3ba0fd5fa7c492c4362c006',
        'adacfa4cc9deb6a54b4a1fb6774946ef9a71b798cc79969a546d2570cb97bc2f', 'b232dd6ab5455b19ac2fb18e9147a0c09dc155d9cb7740e09e86536559920e5a',
        'b30bb14c338ffb019a2e4827234d29f242d1bb74ae27bed6323f00e678b62191', 'b37be070a2ea14a5842e7cf46e943c7d71f12bfb691d01d9a76a37621dc37275',
        'bfd2d398a87c472e06442fa8940214e14809db1fa305471412a3aece6fea423b', 'c927d4886c8d6f053c26bdf38ca6d5ab3db0afae20c6f0fdee8e5eeaa3cdbc5f',
        'cd988b79bb8c7e2a9029a99219a54c0e3ce274cd1f07c9dd0d67fba120341d47', 'cec6b40fb560b0f5de2530c007d7b58f5606a30ba2400638a1470f6b8708181c',
        'e1d33e02e26094cf592c11fa5bcdd4050c587077b6052afe29ac0e3af18fa435', 'eb9066d4664b38d795b1299e3fa581ad90c79497073ca471f3ff6c1ddaf7085c',
        'ed2f8eeb80bc01dc23ca34373afaf7ddcd4b943025310ac1f17b3fc9de28eb42', 'efdc8c266af561d8a157856ab0b5a0e673174ead13bcbfb72f13d574ac29d961',
        'f2ba7d550b8b9d9ca8d48419d2616ed2077ae8fb842b9e2a6f6e1353e71b7d71', 'fb6bf0e1d86fd8075d1356c97d1883f11ec030a4e09526e2ae4295aec381c821',
    }),
    'typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ': frozenset({
        '074abb31c59379b07f9873f7bcf06aa89bb04cef20b1984592a0acd5aaca404f', '1061adf0ca706820a5271b92185c4e02a5af9fb60fa1b5bb025cbe1af5745f37',
        '1b9f83c566e0b1855a84cd3d177e88c657cb6471430c2200db355bd313ec8399', '217c401ad6814365f8234ffca5ba19a85b37e6c48be8d9c49e8155861a43610d',
        '32f4809f11d7eea47a39085ead05d7b5191dcc965683720484930d7117ae5044', '38c31884e1c8f5ccb9ddbd3295439c1a6e4bd0a195f25922cd0892bae88435c2',
        '43abea9ecc84ba14a9b675862d664e2be4f279181f06fa6e022e92756d15e6e1', '4de6067cdfb004ebf997de5d2f3ad87b5081d04c43b718dd0bc3f9068235ad97',
        '51cf04dbe67addb0c8e4194fefffb1ea058b2ae2437e6d0b906aa39c19259555', '5d2c73b49d42dafe5fdb4563caf6c148cf8754db7fba0aa3f5c6a213cdb7474a',
        '60224bceec46c4987a7d025f9906916e232867ca265dc904e1ee73596249895d', '73d33db66a21d6a3785271c07b11501969831b8b9ca846618d028a54b2e48b71',
        '80b376167d4ecca3c168371f45592e4649c318e134464c257c8dd96f69ddb6da', '88f0c89d9a583b67d40736a4ba9ffb4ee2f97d4f2eecf55b059c5548dd28916c',
        '98df88e59379d71c71de289567d736a45be5a7fa0f421cb11b3c29303c484041', '9acdee0a3f6f3cf769b698dd46d1b1a06a0e7c398d4cdb3e7329379c5b3f3300',
        '9b9013ee9c30786a50de9c026d59f77bf4d74da395f463a32b4513f2df80af63', 'a2ebfbfd35110015f913eece5d10f6c86c4501d91fb0b7663f104ddcf2aaf9d7',
        'a6da7ed622e73a9213187a480eff4b440253d23176a4c7abd9f3087fb72d2eaf', 'b5b76650b0d1a79b1910c7a75353d7105cd054381b34244a15b7135507ea89af',
        'b934337bef3522a1dcd27ea65af9cf8211ea1cb6909f906e05b0053f678c3c8d', 'bde30a664c0003078d3016da7e9bab6f237dd0ce51bf92fb86c85f9cbf593b75',
        'c171e9240d8fb0afea4324b0fcc0f72051d7b369dcd6873bd7fc864eca8edd1c', 'c1a6466b4a7ed820a6b77ed560727b6b1f53825244afbb02755cdf032efeffa7',
        'c656f67f523d031aa9598a0d94d951358dfe39699e2b3519165d6e2e64fba366', 'c78144ef6c6b0982bc449648a6561207a6a4c43c1634560f4e315c1621b78ca4',
        'cde6478243e5299af3f442edc527b9576df17e43d7b50bcbc5cc1e233d0ab81c', 'ce961579dfb3e3bc5de06db2ac8723eb8013fb1f26e290ca53f67cb6b997d23b',
        'd198fb69f16ee88ca01d5f49ec28d9f7dc7631c771c60a4811370a9ed4551fda', 'e62eda7016797a3c372a88c4bc506b994200e763db3ed0ca48ec54180e9c68f1',
        'eb068726bd7862fbc80b6d01cb34350d8e44813101c2f08d3c7d10573dbeb3af', 'ec482a615ee87c9a25887ca70ad38cd8f542b97b430d7fd191818d163e5fd0a8',
        'f12594d9a4765875721e9128e1beedac2853cb709668f50e0ba65f24698de584',
    }),
    'typst/manual/sections/01_cell_measures.typ': frozenset({
        '033cf16bf2a7be1b82748edfc8dffa50c1b828ccb7907c5487ddd172f802a50d', '033d409b43d7d7ba80cf79f6944b3a85ce648c8bb3c57ad1652a122d40310656',
        '05d11baa212dc0188ca3488497780d1c615a1f5b2213abca8a20590b1681ef67', '062a868013c36cd6f7a85204e2461988c3587923cbe623e0458e771362d59031',
        '072ad9851e980ddccae1f3fe6cc5fb3e43f6bd07e044e5ba0e6927a52d9865f4', '081586b3157da9cf57681ed9206871c5d208dd8b35b423201abf853feb5ac125',
        '0ab07050472c6f406082aaaf33c1fe42f462d2541de04f224747d875f2bc7c1e', '0b2233a4c0261d3fd1c72c43ebe0b8981fdce5a123d3bd72ce6bd6a6b4fdbc5a',
        '0bec195676b39ca316508e52436dedff407d3186db69d9010473194090f6c83e', '0cb1b9456f2172221fe840fc59260d0492add2d2db82def2d54b63f4e7224912',
        '0f71846067a05dac415749339dbf1ff10757d5e94a5e32c79e096eda1d910119', '0f99288b7f84db64cd66cf28db77f321cf92652e7d2ffe86cf9e3e4422b8f7bc',
        '12bd5883794447b73a36a9e633ae19234a69a340c4cdbb526dc793b288602be1', '15bc2e6f918f68e1fb333ae56eba5a8acb26f5e806c1bbd7a7759c5144f4a6f1',
        '16f16186a62e24e968ea06e1ee04b7a000c68b88a6c1aebfe6fcc29f2276627c', '17e453ffe1e964a6c255a9146e6bbdc763952098b7ce9a75f9560515f9205cb6',
        '18d956047196aa10ef7ac5a222cfb1c2e5996eea9128e7315ab251d64e1f9318', '19a557d1c1be583303cd930c97095422b592adf7083b0e3005c63d5e404b1499',
        '1a70c96e26ae1eb551aae0978555b996c9f5d7ba937c0490a9679440d298a42c', '1ba3a22380e4508f3df5fcf2d31e061e2fec9ee7fb07c874f5ebd98f03622ea0',
        '1e8da9d48118ba93875057da5c57ac3c471c1365c45aa2d23a857a0c091244a9', '1ed3fefbcb1c92281353bf476ef4ffcd79a0b305d28a7d3acc78bf396952201e',
        '1f1259b01ad1d67c999df7481a9fcb118088de8751510e1f85e90a6fdbdd5b1b', '1fd5ced64cf7307ded439f65233a895a2ca276fa3bdffc37b0a447c078cfe2d4',
        '212a2ef20df8249d8b4e01a44f6f751d5a7a067083f7e6690900aa59047d638d', '236198f2760360314ec3932b49bce1c7da3cb5df857c2ed343423c91be4d65bf',
        '23ebcd2247b6a066952403058523d997d6b44599d54a50f9d1d9ab00f2b424c8', '2537d867376ab04f41870e67f3520019ec21c14f2c4cfe123eb2228c7ec72495',
        '28c4e9330eecb4213123f56e0476a9c5b9b6e4be90de28afe2d7a24489b1fe12', '297db2b2c72ceff922ec6a1e33bbcc9d1b97b75fa5fd473029faa6f5d5962c00',
        '29de844a43983b0750080b06d463888729bec70e067613831f004ca4b1b4192e', '2ab74d5856349d0857ee937bcc434b25bf4dffb873aa8904e1c78b67d4a45cf2',
        '2d784a3eb9a247fb383fbcd27eb38750831b8072ed6aa3503bc8d6a3de1e89cc', '2d96a10e3e4f14c24feaf40946beb69e8e81bd0c0d7418e7dcc098855b8fb1a7',
        '2e6e571cab070d3c8fc4b972ee00701537cfaac7b676ac2b89fd1ce4adf37f34', '301768dcd0caa09fbb44154f104f93fc144c39c8abaa3461840cb2e20d7f45fa',
        '302adab9aedad1cceb6840e30797ad335541966780ac936af98a35843b030db9', '373a0ae5882fa76f689380f27521b3780bc949a9da2ac61819f16e8fed54795c',
        '3784d130a699932602ae609baa466cf2c362c5ab11b024f343b0e86cd34618c2', '3d4f619a480605324addf8d9d9179d83d32b57caf8d2a508a2b8f24145672279',
        '3d889d2986ae5c953719b030b8ec655a454d624838341b572f36accfb8923311', '3e3a51552ea430fb42071d227c7eeaaf81055155e230af00cc3cb7b0f5d31110',
        '414e38e113c6a876ccc2622e3a5677bf9a050d26bc8371bc5c2a152aecd47ab7', '45a0976795c3bcde3ff782d46b53899798b62d6aecc1da68b0187bd6f6e1cbb8',
        '45bccb1caafe809ce21e6f1f428dd736f1f542936e6c48bb45b5a3b27059b43d', '48144dae5be82248e4e0840e1563eebf534800b826ff0e72db299a669d7b4b5d',
        '4a6c451c5e1d637d61bbf00c7b18c965333f3b9608c0a29b6110be7cdc58a37c', '4bb2ab986b2acb8fd22c4bd07ae0973b139604c0f54518bd184c5eac3644c223',
        '4c9e91a1b9d782b95a6d4572374e221e61bc7ab9ae60c2eea431d7a17c6471d9', '4d75fc1f8a84f1d2e2e7ae92af90e4b503fa37ab212d4fc45de3433e4873e031',
        '55eacfd46063a01675775380950befdc2ca817cbb6fa0306757310d672c66cd3', '56a714fc440d6d90823c78b7490e5ce91741dd798579203b00ad5051db3e5741',
        '5756c40254e016102516383ddc82506afcccd613381f6669de7c2e73dd6e061f', '58e51005fc9330c7dd0720a5ee22cf06008b1838a31ce12a4b0bb72d9ab8fa7a',
        '59c37f235320b1a6dc0e70033c900f4853637ac6d411e9246ebf8a19b6ca270c', '5a02058ecceed9036210e58aa79b73ce915c23e11da4058695a24901c7515e97',
        '5a591516cf0d26eb671286998611b93f6c18786802cebf92da8a20cd289c00b1', '60224bceec46c4987a7d025f9906916e232867ca265dc904e1ee73596249895d',
        '617ece5ca57c2cd7dde9df96c7a98af834b3bb480a5a26edb7bf1a030b5a0d32', '61e2229bfe46b4df41d73f3ed052d3f9f75010e179670bc6eda2271f9204573d',
        '6232458e32fcf690acb62cba603ee58563585ca5be50025818b675c688d6f010', '627f3d0c53a1bece47317aa33874ef5ec1a72426ca39dfa8cd8c316263331b40',
        '645c81ade87a974632ecec5c5f5fed323d3e294bd103e5f2ee4fcd48a9dbaf3a', '64f902624fcc45f4eaeb2428fc31b4c5be8601318e5a19ddc0e05c4a09d18ea7',
        '669db885273165def348f1d294ce5aab97c8dc5e0c9581a226123d93fe4d942d', '679982268b6d6e5a4f16d4adef684716863d35b1c552a4e4f63c4908542bbfb0',
        '6a52ed0113c69ee88b0d6404bcd8d0aae121c4427687163fc93b4679737129fd', '6bf1a82212bc5a0c25c787f565d09099f90e17624871471d00828e00694f1e6b',
        '6e8bbf03e012cf4f895a13bb2897b1871747433478ef85654ab0ce390c86018f', '6eb01f74d70ea66a32150c2ce6a7f89f18c6af98c17357e73712c9ad30e59874',
        '6f86238f34183a54f9b32201d0acbdb97bcabb0b26321d38c5d2475d10fc2436', '703a00997a0deacbfee70e16ed3f078421f545a2316182456e79676d19ffb19a',
        '7051e4e43010f75f166a5761b5a8475c8a9bd722a52a7e71b30df091cd07ff93', '76511c494012c8f11ebe434896ffd688a6ad169e6af85337702f46e5c2947bce',
        '78c87a59ddb277347e5afbe852aeef3352ded7c647b687c470f509c04f9a6e4d', '79a0bee0bf3f26866930071a86d9f1d784727850e71a1dda2986a667a557c04a',
        '7c00c988a00fa34fb71e72f4209b6e6f6aa0813094d51143a200cc25a1793788', '7d094ccc56446914e3ffe35649b8c9554139cac9189138e96b7c41f1c3134a54',
        '80e3fda8781a39c9965cb791184af82bb7828bd36653ed544f38ed88007b9ffe', '816586a3ea4ab1c17a20421ce9303903af9a1cfb9075c215abbed79fa541a7dd',
        '83643b3d1db3c8cd4786201209da7156923fdf974e01322658101a8740837270', '83e80ae7027a0e1ead2381580c00e9bed812405306e7c5e30a359a1d9299c085',
        '85e902bb75b52d1c1a5e091f8e176420a2768e3e374c3295408a68101334dd72', '86cec3d90103a111b5097fa1575cc3694bf50e837bd39af70de811f585414a85',
        '87ff7d3c89836e488e6b6754c7fe8d12cb58ded989be039b8d109aa80b313d2d', '8a10b5526224820d873a770b652f0ed1f02c1273a176f96906d33ddc472072e4',
        '8b9e1103db62b28893464b39aa94930e20d321ff4d0796421e5d406806238185', '8bd2a1768556f11757d473724c05d4ab96851707ba03fd1a8b2b1d07cb856d41',
        '8c1637c96cb97b7c94cd11734011604e8045ded907b71491ae342efb3e7a476f', '8d34045d0622ad65709561420681f9f072d083df85acf002d39e728dc5f2f775',
        '8d55a9ed146d331d0de8cd3c8299961302d787a009b384c1dcb990c73dc823e4', '8f9890966ef03e169add619710ca9f1179762c2800e066c59bba04cea105f18d',
        '900a8ec0b11eb2e7d5f33e0dcb7c43b299c38d82cb705aada0992342c06f0656', '941b0f0d94daf26f5c0d08e6fa8bf80bd93bd9575e4d8fe978748261b0accfc8',
        '949972ac7d71a4e854d4224081d569ee245b1f5cd209ec2131facc6c122420be', '9830f06ba34ff045bc7a8d2ff900b1480b9eed299fa67e5b92920a57095dda71',
        '9a7facd8611fae62cba254647e5949eb7a445c728b701a3dcfeb7d9729c1418e', '9f186e10368421531990b42fe53d14f91dd3125c8e3f1636eebf1604a1b1fb6b',
        '9f9303f23de412de2b603532acda6d056c94f0264ecc8f3cfcbda2044515b394', 'a2cedc6855870f460b14f0e7accc327de657bd0aec3670c74831880931e35984',
        'a579b3ec0e8147ec96a8f1508527b9e7fcb0e871ded7aab1cc8d060a1a871932', 'a64e68936220ce87580a0f37da538339f0f98a8d3935e3535f58f44ae95192b1',
        'a68d3b3ba19d9bb1e331da98b8be344e4e01a7406f4a45446ad7a52b5c43eba4', 'a7431ba95d85b9a04edeef3f6eb186cca5581e971af8c1d325368538fd9880a0',
        'ab6feae4a14706a6ce3fb9f365bf1e44f2735dc508d3abbde1989cd2a1b82078', 'ae972cfd1ab5002d94e6d1212fa599e2e970103f95df949f6615b87ce1efd885',
        'affcb2040da6de1bceb8d0de266b2d26655e26e7cda862deb9d2b7e4dd7b701b', 'b4e9d58bbb9bd8a2263a0cce349ba124c3ef0c4fb097f177cf00f1439b97d7c2',
        'b73305485fe8d0ff96f7397aab1648a3dac54c1009ceb2e499b85c356955fd5f', 'b99ff5d8c5b4c518d0cd7ca8a1d342966dfc01b2b564629428afe3fe776b3e68',
        'bb8d0fbb3f4b782139c36f109425127a07c96566be53b1b778d071302504c42f', 'bdc6f63c115957f6bce9acffd97ced88bb84a93feaae90c46ae5dc8ebc035475',
        'bf18dcbc540f7eb79d1498060bf4f2695f95fa4938b1cc04d9e74e8e1cd254f9', 'c19b1d611103d3289931d14120fa7eff3f0b0dd1cdc5b5108a51d2e8990b8da0',
        'c3bc53b14826f84acfd4e6cda3a00965cfb3dafd099b15f061e3050d1ab5a921', 'c3c5897b200b39a0fa373a5414710f62f9df2507d877eb298ffc9332a4ad0d57',
        'c733bcb320ce7e679674b2fc008c903da69e4bb5c3f37d7d0e7cd992733beb6c', 'c7d8609f229a7ec64d72ff51d1fe35777621dadddde630969da4bda4b3df11d8',
        'c81e23e7845dab84cfbc0fda0f2add955896a3c9ceef96a5fbee42d707dad8d5', 'c8941409c4dfb77273a0b470ddcc541ad2ac24bbd1dfb8eba63bbe460e800c6b',
        'c8b8970a615681bb7004483256be70bc76d42e1f2c1507e210ddbca621e74035', 'ccb3271fcf4b106fecd28960a77bb8bab99750988e116cfdd8ca5e4dad47e156',
        'cedabe145fb3e72969f4903aa5a9f6f683004d06a9995763ab5753a6e360c9b5', 'd1e5099c97852ff8ddc3007b781ae6193abb52da4fbe1491f9a568499300c9a7',
        'd363231dde8dac6cc58c4faa959f261f6d8bdf7fa2c8865764cb5ad6ac05355b', 'd974bedd62bc2bb9ebcdb19678e232dfb1ad0e160c7a072c383e627b2e440562',
        'db1e11fcb7c40486b2745d5a178c695b94c38540d096ad8ff94ccd82ac2c2444', 'e08d08162a9bb9975f67bd38b5f531bccd2c087661f7e45ab987d659c6345952',
        'e1a23decd922f59acb635adda6a714b679ec836b7d208930c58f904e0010bb4a', 'e328847823fac7e82586b7af70f6395c77b21d8da7dfd140188fb67a39e8cae9',
        'e3aa1711f28a18bd5292a973ccbdeafcd8a984a89ddf46258ee9ae592e5ece0a', 'e609d48fbbdd19eeffcd122e4fe96130906529010352a3f5b942a9d71a48eb5a',
        'e90b216f7d238f3e1e6b9f666a71aa83ed688b00d4644805a67fbbb9445dabfd', 'e94c68428f877d9ab6fe280c9a661a4bfc5047ba373702f4e48a30af76702d25',
        'ec1eb329d13280a48e5cbf23fd26cbddc32099260180684757931890d07a8c8d', 'eeb298717eb785382e715ec0ccfd8ed064a19d135de75728bf1afd73190c0b44',
        'f1cc9ce76985a2ec9db1a9c10178c2f4dbe7b58763fbce5dd99466cd953132aa', 'f2b8aa41c181230809b7cc87d9d0c8e53cd6deb109a84d4fb2c89ebad0cfcec5',
        'f3d00766db97e26c417f56afd0dfa36b96bdef22105d9130e08b249505e560f2', 'f5ae7404fde3690d93d8bd08e2d24779b45a5e9be5e5190e53ca11f90ebeca36',
        'f938f8758373467c25928d6c87bcbf2c2c60eae12a4a0c158e6aee3d0e696b4a', 'fb17487b47dc74314cec0d69e6f1428ff9752cb6f5b0cdbc9f28d1d30bef49f0',
        'fc8e0e51e049b75ae9ed0cfabd617039a0365a1e497d30b8bc7b7b667e076a08', 'fe3430bf97fedd6b93581583f04473690c4415d2009945641efff10a91bb5ecf',
        'ff6f74acb779792245879e089349281201ce34d05c8d4b6fc4ad6c89d9c44989',
    }),
    'typst/manual/sections/01_rest_energy_prediction.typ': frozenset({
        '00136d5303261619a81c5a5621bb8b95fad181d7d19bb81b934452d2c909b3be', '00867b770bede8cbbfc2a5648bc7678cb84a482fdd18b7534730faafed85bb02',
        '02e1cc49f5fb1c65b69e350e53425986cb43f4e7abd6a8013b15c225a36a0823', '02e566c905dc8f88e273076acbe5c661baec373d78b18c67709ca58ecb9c34de',
        '045d91d4b6fdb258fc1927832c8b96717602f4b6f4ae4ef40b980afcc0bf133b', '05d6440307c641eb3c865730450cb5226d0aedbe8aa5b01dff2dfc7a4b295c43',
        '060383c48471e7f768b8cb58f4c59fe44adb6d48426dd57c0f4b11d653255472', '06d2c39c070a6b43985bbcf458f7a2cb5b1bfd92921df2b074e30050081a2c12',
        '074f5db7faa407dd9137450dfe3481a0e5012c823a8504c057b8e1e71820c544', '081685e90944e5755e8eb5db4188a1f20cdc5e226797c489b26e20de736e7f01',
        '09f4867254f27c26b921c2c1dda79cb932fd63ec5207f03beb7f886068313d5b', '0bec195676b39ca316508e52436dedff407d3186db69d9010473194090f6c83e',
        '0bf9daf6113cda030822efa5c5230bc848bb036efdf5cfc0f5971b120866d8ac', '0cfb01f657033ae3ab31fd2faa75402bb671f0135dca85efc93ea9e2c76f28ff',
        '0d704e8eae99aee8c63ac9953f1d9323e19babf21b881666396dda7a3c145c5b', '0dc9a53ef70caeee4ec5a2b32044064f96cef427c1a3938c79b36a146b222d11',
        '0f130662b69d6ef364287b8e0d5fd403a86a9b1485cc8668fa87f2128760f1f8', '0f49df6c5c24a1c007c934e43560cdab67776391229ada30822a7fef2c5453eb',
        '14787f2243d31f91a58daa2e85428017356d544b5261709cd95f613e37efa302', '15c777b19c16db05b19f9bf53db7a3984b53f2a795505ff1797b3af08a709e6f',
        '1689fc04d416162adc62f71eff95cd97d3a630c0191ce4fbf7d77f193c4a2ef4', '17775e1de92b0086db0fe524a1ddfbbdce6efec900eebc68a29e3df564d40896',
        '17c251d09dc694782c8a3cfc0e577a080f8b2548f75cca45ebf09324059591f4', '186709a33d70a802eeee78f346a7826782ab75d06c3939883adaef0fc2350622',
        '190241b6648999026ac9b2b0009944db853c937e4f94483002cde887602dae14', '1952c00ff333e55f8b20851acf53ae371caa2f4b3f2bafb1ce4c0bd5150e39e7',
        '19c0ef5c6a71a5767effd314c0d37beee1b3843a608b77572d227c5d53ccf982', '1afa40fb84aa788c63f5e10db491a70cfec0eac6112dfb982a6b8bc914f080fd',
        '1c576d71f3eb79b1ea96ae9b6e37986a5782362e97beee9bb76fa1a7e7dfb40f', '1dd0f0735cfc15fe42d4b5a138e4c9a4eb6f10d16f52d1b783efc757c88feb50',
        '1fea6361ef68c3b3eedf9779a7c3a363096e66cbc0dd5647bca428d8eccb8190', '20eea654ac9bef3fca6b15e06c7e6f5605ff1bfbc91c33e7feaf25053808c1ee',
        '20f68af669c24fa9e6cc8cf7302b22a0abee4ab63ce8784650005c66b724b616', '25383bcb5fb4d385bd5ff53126e5f33e7497a4860dcc66bf1decc4221ca6f1fa',
        '28148b2f34c50ec7e18f8bccf45b5be20ae3bd900658c76b82dce3e7ffd9eefd', '299bd24bbb648e9b818c9f2bec8ca3402e1fe504ae51da37729a27134c988387',
        '2d7ac589a92dbb930e0dfc087b99dd5e7a275e2d0b2d1655d42f2123fb41ad92', '2dbaef4103a075c374a815b79347a8d263cd7b4f15020d98b82a554e08a5ab93',
        '2ec51e4cfa7c6812935bc6c66fa99f15628379bf001ebb3ca7d2401418bb96be', '2fdcec75a8998667177954460a37ba8c39f47d0f5545a71255dfb6a5362ec37d',
        '31ce523db13b5dadec46c97344c80f1c521540a91f6d6c373853c563f969ab47', '32e6b35f186c0750e8497748d209c91a5f89383474cc72cc891b570ce712df43',
        '33caba911af661640436e6288024649912a80f2a796ea2f121082abf7d76a4cf', '340197056ac6ea743aed93e0fff90b15c0b61c48672e7cd5962ba9152eb862fe',
        '348c455618fb3006d844bf236a839b8c97fa86d0c123336b72559e826be3f343', '35b7daf77f93666d8c04884bd45bbc475149a4e9d2c02dab3c65f96c6a5ab5a3',
        '374080ed76ed2362e2b55678649a525eec4da5fb3c88a400a47dc033fe732aec', '390935fd387c65e922be0750e4275583eeaff54282e50763a2a9fb486b537b5a',
        '39f7b1c0cb4818895784addb167ed4ca91faa590c0daa0698d832b9303861f9d', '3c411ce8ee69e03a74ac644c38451e6a4b4745f27bfebb3b021cb65a1bc656ef',
        '4108f01bb5d2293605091989ea7b93a4a8890c2879065f80242d17c80aea5516', '418c4a6b119c1423468a58a0d0fcd5c841be2bc8ce2bb3effae0138959d12817',
        '45dad5ffa31ee281544d414064c976470680c1394d346778ff4b1c974dab0f55', '47e9273c475af980082d3914cfe77c2a728a9e8f16e6659155070fe2f2b4690a',
        '48a354e4854dd8524543d769dc893336a505a2e6af2e44fbb5c254403ddd577a', '491d62089b2df21ea5f288f513516c4f7fce0aba97de06ceba15ae1ac73e0d15',
        '491e2cc95e2928f520e492bbd7b55f8283957fa46c85d944d1e029ddd26c2b5d', '4a72d53f9101510c658afc7ab476812558df652e41d2f62123ad13f8fb9fa647',
        '4ad01685038523f0304041d809bf2c09e98747381074007ec48893a7962be295', '4af8f2f3205ae0dfa93cf51cf4f4b79b862a20b1038a880516c219dd0a91139a',
        '4c569e60d5bd74d3782547898f5b9cebcdb1f748f8cab5fb670846ff1d3de5c9', '4cd528f4c4c81bb49cfb36a214bd5c8d1a51c0b52fac07e27fdca945bf70e384',
        '4d1de5f71f3eaddda64a386b855bedd595cb0d2cd95eafcbeb5049bc8e12e7a4', '4d4c3e71d05f7bab12b95086959285bf3a9a63c094eb4b61b1a11e8ca28bafc8',
        '4d7dec2435d769fc8fe83489b7157ea96894e49d26408e8b57cf312e9637e4c6', '4e2d3671f3631180e1fa4e62810b60d4200b9fd21d265e624044514ccd54f031',
        '4e3f1c6f8c9f3eab92c3b52910c8a18ee677bb60b842e431ab7241b3d12f4fe4', '51d6f79663cb670ef20915c1ec976388680cbfffff3bafa968aa7f9c7e8dae6e',
        '520873372c9af2aa89ee5adb9c1259758ceea751604941953ed1d317d61bcad4', '5325f87c180a654d8d83bd1a157eebff8ce203ab6bff51f57e5ee7c856e0d0e9',
        '56a2d5bcb7d4aee390dd63c0783fadbfab358d5c42e1784d542101bf115c4e96', '5737d9129f76fe9ad9108503c744211df9202854b14ca0093909dd8e0ba7c343',
        '5bd929f89ca2fde3db531d3f6414fd447a0cbe99e334d64e5d7de5a180dbae06', '5d139d2909325f5c42558593f3c8d5b9407434e3c2adc2cbba5a7786b151899b',
        '5d457ceb4382cd3e29dfd3d255c0847eeb8cbcab67f97152bc20cb13e9bc88f6', '5e731a98848a6525b08224c1bef33394a7beaa88cd41c7f9c32abd2ea4aecf5a',
        '5f0e1c29b0575b7177d47ec7d08550adb6771dbda694add9bc7a4455bf115979', '61b07a3fb1c9c1a21da0de5df7a067668fdf8d1c60643073ec1c21c4a804428b',
        '626d7cfaaf306b38590dc56d734384be6774bc0ab94dd9e0b2ecbf489910daf1', '649bffb644fe5c016a813c95d86524502cb9e55a0884f1e31c75d263717e0cb7',
        '683d123f615b7759d6e1f25ee57bc27d1196fa06576d479b3eaf60a976a087c0', '68e1d3455300b8d1e50dfbd1bb6e219d4e4af698e09ef46897c13b8a3f0ea9f1',
        '68fc1435aeab75b706237cba416971131461e97e4ffd5ae6b45afa796240f00b', '6be4ac57425a98779146035740e46b085a8f8569fa841917a6ca6a192003d0f6',
        '6bf1a82212bc5a0c25c787f565d09099f90e17624871471d00828e00694f1e6b', '6d258dcea538c3d94fbc5a6defe253bc69b9c52591eabc6c23fdf7f7c0f2d3d2',
        '6d67bfd9fbd1d084fd613235a981a94da90204a697d900e9e1fa8425a134b1f8', '6d8b562d4bb52d03303a640eaf8b6c9d3103933150d207ba21ad5ed68c0f8e96',
        '6db49309be667dd9c315dd6a13fb5fcbded93ad46e01f69ba6578e810cee4a2b', '6ea24a49662449294694b32434ade3dab00de46b72e179fd6b15b4e2c2e40f7c',
        '6eacfcce080bbbe946fdb27c354160f1ef1f7a2e9efd9203eca093ecda29e871', '6ee8e24e07dfe48e9bbaa7e3c3a6e3260e1dca82239d85f6437d55b02d018af2',
        '72b6c3054b1e6aa1bfee4a36958f68e0c4057c201379558ff02e059ebc48899f', '790ad7e9d5ea6484030bd8f19bd2c1002824a1b96b987f538ff70ea3e00b516f',
        '79a1f3535643f6c85a93ee435024d93a3f4b7b71b4f022cf9430e6b893ada618', '7a7b7f4edb299968d599ed700ce193c9929c0b582348cc2b7f954a46349b4e03',
        '7afbe7be62461592e2d21122abc609fc29161a415dc698f03d3985d75603fe97', '7bfd2f6f9f18bb6c6ea668d27a4a7f850797eac19bf09a9d0bb4e3c969a765a0',
        '81bf2197bb3c7d4c7ea838cec5444aa69a4174f81ec86b568d31da84219a6130', '8359734699e2e3a72ce36c3c0a0df3f222f5501281e949d29ddafa3212ca5489',
        '8447b8b51e22675329741dd10aec16a1ded917503ac5a65302beddbfd99c338c', '87fd90829c5286541a73931ae89d9a419eb65033c0e2672af8ba87a8b1007c61',
        '8ba30dc0d2d31234db5dfb4d4ad1ad479f5482c7a9e27cb5ab703556892039b2', '8dadedd242a2d55a76951a507528df2497de8ca5a5e88a18ed0d6ef13bd5adc7',
        '91024fbf17159b4204b63d06835ab59a6015a806fea9cf492c531518fd8b2c3f', '91b0d673f75ba94e5e594abd4a0a55cad7d39bc0d5d8ceceb574219f92a6cfe8',
        '94401a8f8c915feaa4ff3c43996e2befb7c07980ff32cad25b3eac7759ebfe10', '9c2a94235b4482521f49dbe5c0b1ed4f393d35727232a5027d3495980530e5b0',
        '9ca7d54afd78d625c06fbfb91acbc1c0f8595d100c2ef5786896fc60a007b385', '9dcba283d2d3e8f0660324565b576806b6a338f862f85c15b13e509081f1d532',
        '9ed1f210f726438a918159f411bec9673d0248220c2d839f0e5061331569814d', 'a0ef91da4c84db8578b42ef8e9cfa1cdc61ecf3cf84cdf74dd1ebb01a5a76c1c',
        'a3ff4a2f6a7ca8ac57aaa7504c56254c2c5e28fcbf43841d4096da1a2959af7c', 'a6a1d91fa5c0c21188725cbcb74edf97d0c86830e1330a1befc4c12d04b0c565',
        'a935abfcfc53df41f37093aed7cae39e37341851761efb6867a135721ed358b0', 'a95d3cc31335f64c538202af686f51844b3a8406a6bc7eaa002082359f8fbbcd',
        'aa552f6a4f3a56a3029eb582d85b707965d6f96bc13a0e2c8b215b3997b5a415', 'aaeb836e73a2ce8351a647c9a2b7a548ca13c62b259a3a6b6116f42afeedefcc',
        'ac654ea674763e17fc00c81849e8db04873c6c25df59dc14e27c97c0323854f2', 'af327bab9b618dd13e0d7a9989abde6fdcc1235319e55d5727fc7916892d9cae',
        'b2c3b84827fd89c1a13d252c1d5e0246966e2577d595623a5a30baefde0816d5', 'b48bba83d1ca60bf50f85c7cd7a25044a43d357e4a2c1df56c0d5c8a54d4707f',
        'b4b4f23d29c894e1c944ac667cb15f6016a5ea3c02556b7527d25f5efb380028', 'b61531f9ff3c6cdee23c8ec649229ca9532b52564e67271900d936bbda088f69',
        'b63afd75ea35bb03dcdcb2de7382b76fbac8e26a02a018d60e1a1dd977aaacbf', 'b7f048a5f87a3a5c3ecad492d2758c83a2ef256ba1af175f1167fb89a7ab4bbf',
        'b809980489bc808543271ea68c2b6abe93e884bf2119ace4c7adb43a675b2272', 'b98764370fe35648d242258f04ed1176ea8823245ef312339c324d3b11dfa88e',
        'b9a33570c7b1b4bd3510c6b7e125a384de1d4534e261bf3c643095e75e07702f', 'bf58a548347dddf80bce05b77c82f074de2e2d2750b4c907e347d3ab2d94e4d8',
        'bf7cdb3ce5f53152f8346441a7475ba7c63c6d93c30367b35bfa90b9c7302453', 'c05d2b70cf48abed61dfbc18d9501fd4a3b09f24f96f67fadc5d81dc5e823149',
        'c0fb3a52aa9273f49820740c6b7238bc3c31aa7e41e202bebf7e74636ab136b2', 'c2e89d1b21abc089a439702e6689a054fe3239d257deae6c51f922c59714ed6a',
        'c3fa55011f73e2c2e00841b93c2eab1d1658b55995fdb33deaba7562c2fa2f0e', 'c4c0a8b533fba9480d674f8e71dc9d0155b25301ae9b4ee41e05fd161c307c08',
        'c75c9fee3197967906352911f3be4c0b4fa72ba791d67f44dcba3637be12dd32', 'cba0f6502664da32f7df620a91f247847996c42497d3d78110eeb2f3011351af',
        'ce31ccd34bef2c6845eba5b253c29915c3d7b78e43258601714a0f1489dc0fa4', 'd782371467a5dc49145652cc9d3e71face92b3e19402db4e656646a3fbb81992',
        'd901a591709cf59f2966607a4a273fd795d1c451810daff678989b2cfc878827', 'dbff0da43511d9b1982b67506d13ee89f7965d778ef4291f15fc7cf35d968e2e',
        'ddc42e2c47607cf829094869ce85fe1649ed5988fe0dc77059352dab0f924abd', 'de1f810acc84b401fa538d990d6934111c3344016767a06cea570e44772fe459',
        'de8376985cb0baa4735f3e65d8977c17e6af506b05b045ef93fd2c6f9b803555', 'df773f84558953511628163307b06163c080224795609a02dc82037a234b54f4',
        'dfc1d5744c7ec00ee4b53a771eb2c514129e81464b747ebcf359a258d2d9a300', 'e0f926a1983e63cec1418a4a56027af8cf5c447238346519985dc78f1ce5ad7f',
        'e3608f5ecbd660106589a6be381b6d71f6ee597c14ea540360721c7bef39eec4', 'e39039a89c2bb488dea86afa5e98b57b5190f3dc4f1a885c4c1321a43a7f9dbc',
        'e5dffd73dbae3caa37656ef0c494c5ecc5bb753be2441c314f2734b49bd47c66', 'e6af47ead79b3ca31fd272b3e622ae0e6d8c863984e6927012579ced645b6557',
        'e778f2e3b2b2674bde07be71ee99ce341977e16aef29b743b9275bab04439e2b', 'ea1afc1319c035cd0ad2c537ebea05313c738c40776a6e4fcdaa91e3b244e0d5',
        'ed0a53a09740140fa23b3e625989dea42fc457051675dbd8bd7a098b4ce54930', 'ed4065eab9e6f95d5ecf072626482850aa24c8496789ce1bf4932d46de67a71a',
        'ed5a154538564cf9d4ead26a2ec88276d9d13bb323e45790574961b52c867025', 'ee9d0e66be4309a1820e0e41ad32e95172761d07e9477ecce1198c9e4fe23928',
        'eee670fa5bd1a9fd952e52d42bba7e7a98b2f2953b731de8c6e04fe3e8cf2145', 'f2c634a0973ab12f85f46d0ce78118518262a80a5022b443982421674b29e8fe',
        'f4b6cbf0fcf6c745c400cfddb8aaeba733c21fca5998bf2774b31e21940a42eb', 'f4ff7fc0814f01166e3f931b5acae8c7dd6969e2a1bbf9beaa7358546d033964',
        'f6dd758962073414c54b6111380da3b2ebe034194a5e916680aa2e2830e64a1e', 'f92b5a9d5cd277997f368a98eff5f8101cfd4fc9101a753d7b94f66a03dcd010',
        'fb0f77121310e450b2e3c390abcdaed10899e093984031d999a8e8d1bb3ec3bd', 'fcd42e8e506ffbe36de773d56e17ecd450c32ad7637c0e9bfe68aa699f935135',
        'fd21210ed979e0165f26a7b068a702e8285bd53671f47163b5e643d54edf4b2b', 'ff8e14bdd30f747eed1e4a55f693bd398c0ee9d0b7d3d6ab8fea238de2a1cae2',
    }),
    'typst/manual/sections/02_hydrogen_facing_shell_tests.typ': frozenset({
        '00af502046ebe5de02e3b452b05998042d2932649f0c6920ddea1307aa3e0724', '02c15eb75da31d728474a51bf21046f730a182ca9ecd0fa7377c581c5c2bf8f9',
        '12c8d66b3d938761ce9622e74f5dc45bb56e4f0a8f3aa22ce1a53196ce1f4f2b', '1a64187bae06bc02c183d10a80fc95256eb206397370fd73d8cc90dfcf7f47ee',
        '26a7eaf5bed1d3aea800760e68d949deb401fdae53a1218f1ec8ab737684abdd', '36465a3ed966188a56ed820cdef3a90398ce7614dc01f93c560c066c7bf98eef',
        '3a8e244a1d7ff9598e2130c9fa51b1586ca60e59cf8a981ae197975726af9ba0', '6bf1a82212bc5a0c25c787f565d09099f90e17624871471d00828e00694f1e6b',
        '6ef161d404f5638321cb69bd374342d1c3451797885ceb469f050cc8cf4b1de7', '714de1c125e742f7588864b85d4ed28013aa4a6c6d2302175caea351064c193d',
        '73d33db66a21d6a3785271c07b11501969831b8b9ca846618d028a54b2e48b71', '761187a1d70229e07c4b96e5ab06aaffdd7150c2b46eb6c7e6edc9ccdc828f7a',
        '785d78db0e1e58dbf70733e5c3eff71cd5cae318855ca964257c2150fad54420', '8b3adcfc39bf25470110b86de9400f3d621d1105bf39fd40ffd42e40e780ef58',
        '9319552229cc6383d90d8e9dd7fc5182ef040d9c707dd7ea7a409a8398192e50', 'a0ab45f79b4a2160890efa5c3d683a6ec9f712c12120e7d82b079d05c4ef5e5d',
        'a6a1d91fa5c0c21188725cbcb74edf97d0c86830e1330a1befc4c12d04b0c565', 'aa552f6a4f3a56a3029eb582d85b707965d6f96bc13a0e2c8b215b3997b5a415',
        'b866ac4d2f4db05ecd2b72ff3c32a8babe6eb54d20d307477547844758792656', 'c3fa55011f73e2c2e00841b93c2eab1d1658b55995fdb33deaba7562c2fa2f0e',
        'da46f28801147d04cef0565ded2253444d795971d59774c26f34f0d44c5773d6', 'e37894fbd1016a4c4ac74f4aee7b9b18e6b2cbde695c3bba49dfb2999dda5c38',
        'e94c25dd010fdce01605991184483ec5f2efcb20d4667fd420dd06b7b182ded8', 'ee2260796da8b7a560e0d92b78024e129caa4a7991a49bf87a1bd9a63575c1d9',
        'f285dae9437297349135f2808074ea134ae96959f4e43f2d07831d3d1c8cf652', 'f475d03adb4a698c2f8bef1d266b0248ef3d07ad8b6af1313a2db714fa51766b',
        'fd86bfd136f1604ea522c92b3fdbb9642650c41a2f11ec0c5c12907f1e080c0e',
    }),
    'typst/manual/sections/02_mapping_error.typ': frozenset({
        '02c15eb75da31d728474a51bf21046f730a182ca9ecd0fa7377c581c5c2bf8f9', '04dd3f652d45a2d6f5c16db365e44cc7809c788716d9fb89038ba9e1aec72b3e',
        '06ed58fe710d24a66556f95582c23d3468f767f73de7678de42660570c84cd42', '078bc702966c9a25d6724fac584e6a25c91918872da62afb5cf957083f1230ad',
        '0d1916944fa0b5df7374eb574aad81a10c09b5d42a36c08da4c79ec724712166', '198d7f73d0a5983ec581dcf3d4d0f897bad4cc2d2b0cfb3a445d0fe7e5373891',
        '1a196bb918bc8a2006ea6c6cae85cb4748234a2a785ae9e6b56a01b0ec7d62b3', '1bf57c1415558f6d28ad0aea288bed6b5e6c2fd481f99b312248aaced948263a',
        '207ffeda8ee579b76e71ab609f110c02b242ea7dbaf9bec5df93d1779ddaf347', '270fb5b9993af9e6e63b08417fd0f5830096c34a23fbbf2dfa3d8cf0bdeb6a49',
        '274e799252da667d1a4395463569656ab3dceb5f6bc2560a8d2167acd068a0bf', '32ae4f716d5451ee909174339bb4abb7b609267b5779f126442ab36c435ba1cc',
        '4cd528f4c4c81bb49cfb36a214bd5c8d1a51c0b52fac07e27fdca945bf70e384', '4de55e1f19424998b8b8773909b4aa31abab2ac9d7e5a6180b670542e647f201',
        '72a6ef3f2abdaadd6a88d53a27aaa9c2da55149db8b0327a5ba81733e560e550', '78eef3ae3cf7d5db5a209f80c4e9f1e017c9da1917741fd10fe2d37172f63659',
        '889e3b44d70f831be9d245d741e2194f9e60fe7a6ce3a291e5e76e0f4fa7eefe', '8aabf68b2f031b811bf8d027e1b61f01fef1a178779edfb383a552959772bb14',
        '8ac759d5d37af3e26274ee050571479a802da0303d9b6b53a0dab5a169e44aa6', '8c9148e6a2f9322f36a6b3ad796b119e219aa0d50a907e309da73679cf7a8c15',
        '954547455b85d3003332f5b7b7ec51ae33693a3a33fddb6f27c59e7a34a596f1', '959a218692a301af2f4099d53cba3fe1b5d3e4397ecef33a2d93db11d2491201',
        '9c2a94235b4482521f49dbe5c0b1ed4f393d35727232a5027d3495980530e5b0', 'a2974856c6759e84016f076d61b53e473b46ff0c7311212a8c3b053de272400e',
        'a557fe98c039b8be16ace0734378b7fe19da196dfbb2d97b03cb662ebfe8dd9d', 'cbf93a71ebd11346f4d1a3e8ae6170187aad770fbd07288316f64ac6105e98d2',
        'd425ea238deecd7fa217fd4b3723c4495dd78a06ffb453d5fa20c3a0454ec5bf', 'd753c68a74d9e6b8dc3ff2995c8de3a3a2d6c04693789e20fd89547714f0b585',
        'de50c93dba94d220a3db10497bc6e20a2321c2f74489da98b510bcb0a536522e', 'e86a89756f12d95116156c839e8964cfcf0e82742097bbeb9d97fefee00f6dc8',
        'ebddfc88dcec3fae3fff73bef86e51d952b62a207e095ee9bb318399dc5141b4', 'fcf8e8b04fbd79a45b2c2fe7270bd2a82ec310569d585551cd5a23fe9eb562b1',
    }),
    'typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ': frozenset({
        '074f5db7faa407dd9137450dfe3481a0e5012c823a8504c057b8e1e71820c544', '0dfe928ea827be46ec406e3735eca8de0ce0ecf2d38129bb9b358beeb70df130',
        '0f41d1f6a3b485e7cb0d8c1ceab5f875cef2dba77153160a147206ebb7a62cbe', '14694f97a5c19197d222f42551a187c48b8e1d5e64be47ef7fa9a8816b0e5728',
        '14b6143c4e18bc0dddbc6e08eb377f7616aa407459e65324eef146d21b99f995', '218ba31dd17c99271e1a81e6e6bbd9c481e1bc1f1f818a1832589899ee4d3a02',
        '246668d9285ecff6cc300074b8f9e1372d91347239a98cc0a0eaf96c612ef812', '28029b152c9f4f27df47be82e9f8cb5b1f6207035f3fb6ec44dba7490155b33c',
        '2a2b0b1b051972593711789a5a3b81edb1dde5417aeec0540edc7cbd14362870', '2c14e41105e4e703e3c4d8e8723e4adaf63ba3e8fadc62e8cb2e8828fe3355e0',
        '2c5459dd1beef0c36ffc3b39a9f030f5d0d56591ade121a1470b4afed486c2e6', '2d7ac589a92dbb930e0dfc087b99dd5e7a275e2d0b2d1655d42f2123fb41ad92',
        '316875780b6e660a2803496bdfa6b5167986bb9ea9e3c374a7486afc284d0ba3', '3787047d3e517984a03fe3c26f0644e3a3c042979f18fd1afd596c50fd8fb310',
        '3c543c26fd3ff756e39352de0839878b1e229b248451e902d24ca8af3283776c', '40955a9b98c072d8e7a67934d5f9bd2c236c984c6569343b77c3127b7871ad4f',
        '426c7520a8c3752a96471b157046d04cb66a9d35aaeacb90d8a64c32e8cd98bf', '476e8c4cbfc49f13d529f0b22570cc72fbf26dc18869f34befb02002bfff2f58',
        '4b44d8535ade1ecd20b9b9a9f439634924c3eee8ac5fa2ebf665ae5dedbafdb5', '4b77e58652399cdf314349fce2f1a409894bf1a28b6a050f64545fbc05efec71',
        '4d4e0969ab17c5077f30bc5c8fd1a9c784562537d80f786d47492aa7264a6943', '575bb15abb52eaa4ab7640d7a9cfdb9464c055a48fe8d942e06f392b322b396d',
        '5a590b1dee53874c9745e0b78005970c08908b34ebd824d8fe427c7b185d3677', '5bd929f89ca2fde3db531d3f6414fd447a0cbe99e334d64e5d7de5a180dbae06',
        '5beb0c399481e18a90fa20740c6991855419de52f5aa1ef6ed5477306461c243', '5bf57c9e8515640edf4ae947e82a40b16173d718f184681299d12a19a43561d8',
        '5c0a00a9b620194cb1e8e50db35b7c7e47cc1a7650ed28b3b67f7d3e1351e9fe', '5f31edb94a1cfb49d9125c703cad17bce37b877d53b04019f48cec18e8f42268',
        '65fd33e59ce6126e7de8e9ad81c9887fc0fbc60b4e0f9ce3a0aa1b1a996c7af1', '66a06a68a4867170b63dcdef5b0aa1e4faec0fd49827b18664db335a750bca5c',
        '7fd04a3f0023c373023ddb99dcae67f6065a8a32f8c27479035c4fdc7cdcb282', '80a216e5a5bcc7cc13d963dbd235338742334389ca9fc4fbb8f1bfc9f4292bc8',
        '8a2815385173a57d94aae52c7f3bfe5a85e09dd27681848f0c07fa58a868b2c4', '8ba30dc0d2d31234db5dfb4d4ad1ad479f5482c7a9e27cb5ab703556892039b2',
        '907ac973b9c5f04cd962105e04b27ac8a668e1adb05dcf0044723b0846e3ee32', '91b0d673f75ba94e5e594abd4a0a55cad7d39bc0d5d8ceceb574219f92a6cfe8',
        '968d3e2717f3c0f41ac0086c6cec5caf14e0cc7731f69a3c2e98d621049b49f1', 'a1d0fd223de3023752521b0bf237ca0f317c52f6681a8ebcb25cbfeeba37e33d',
        'a7d8a6a9df8631e1dfa34ab7779b80d77e3dfa5a12afaa5a4b95a10b2f571860', 'af6ae3f0f8e994fc3bf716e2cda7a2c22d957052bdca9fbcd89bb361f04dd655',
        'b61531f9ff3c6cdee23c8ec649229ca9532b52564e67271900d936bbda088f69', 'bc023e67814a76f63afe596310ab36587d292e60833d777f1c225cb5faa5f6f3',
        'bc0c1f7d10f4b6717c2e3b0ae8521933c3a15d569049466c3b6e17841cf1b956', 'bf9d450e769a65f4955627c5d8544e614834b3ec768bdc210f3e75960f87b0f7',
        'ca6b294a5003e661ee14c4c24e866f6d37c5a4df59f6dd39acb30a9da6704411', 'd29d4127302afe9403f44878b997f22004b028de1724ad0944464b2c90c3fb9c',
        'd5f35eab1f5c1181fd87d69df84a76e9db3d7505b1b026299f5144c96ccc2b26', 'daa86b6c5f3c1f4ecc07c37faa4f7699d2031c958154b4b4169878b7a205cefd',
        'dbff0da43511d9b1982b67506d13ee89f7965d778ef4291f15fc7cf35d968e2e', 'de167f40c1bc4184938a46fda5d38173b17f69a2dcbf4557dddd04e520e70043',
        'e115d67913ebe4e6734d3905e5593af67e2c6848ad74b7f383106479afe0d9ea', 'e26b3ef1ff1c0b84bfe8c438b3665fd387172ac99aa4f35da37721a4874a8bad',
        'ecfd0f6b3d4c77d0f75fb9ceeade496d6d638aeb5a579d1c19aa2fa9d973ecc2', 'f1cf91ffa85f6951bd37f5becdb28c3b6b1952d231fc8d712a39cd34052b09e0',
        'f3bdf7d3741f2eba50cedf9b8e08ae0d1b63809ca80d3ac5e8eb7000aa3886d9', 'f4ff7fc0814f01166e3f931b5acae8c7dd6969e2a1bbf9beaa7358546d033964',
        'faf770ef4fc082518f3753e4933a604f94028f033e0f6528d6731e9a1ac2e89d',
    }),
    'typst/manual/sections/03_temporal_observation.typ': frozenset({
        '00f969d962fccefd30e6ee48ae30ecd5fb22f7eee4da6513cdae2062c62266fc', '1807ac3b82953013cc294c56f2572db1d7c755e76a71b4ab6cb274a999061210',
        '22c6e9e35d03969de2cb4679f615f8335904612325759fe95dc6ae550e709726', '28da2a291b7225a88f894bc4790c0dda2f9f395ddfd36af391c29a1d6ea662e0',
        '2cd5178c5fc2caf62c17b6ea1279a5e6b8b073ed0c8bf17bea79df5df40b3f80', '2eb62cc74a4b8b571469ceec59e59b2ee5c1ebb4003feb84507ef092fb9ddce3',
        '3d1ecb948b5c7ae81b9725e000fd5c30d510f36dd497b81f0afd7ec6498c0a89', '45a02ef920b35fe31033076af8397c921c3e4d91a5947a17e38ad725501ea6ff',
        '4c7d3decc818e8da3e4a8473a3dfd8a2ba79c5014cf5ec1e79b6ffc0bea95ed2', '4d07224806656389130710b8f556334628f0f5a7d47fa248b3a42eee6c535105',
        '5014322e7c88f9b19da61fed340d29b8f78255ef5141e847e4a97eb485a3a544', '556fe53690b01f0aa519e303aa240e623d0128384f20135959eaacf0404c4182',
        '5f1ed2948a3375b590c8179f2aa890243b7217c9bf9fa2f982fcdfe78469c465', '6145b9f2764c4dd69ead3cc21ec3886ac36d7799a8ccb1ef2e3d8f5bcff55010',
        '61f17719b2ef6de3ced4a843bc04f62260181145f85ac9d83e65ec5cae511b87', '66b8393ab303fea6b6a99d55c40e0fc769dd1149f77399e6fb5e95a1ccfd52e5',
        '685d0991ab2b5a1c8c6b4f99ec83672f4bac0e34c5d1bb5080695331b0ab5c24', '686114c8056965611ac3c2bd4336e9a9ec26c48fff18f651eb6e1e711ad74ca3',
        '6ae91edf511295252ded459ce53bd6f696f2529924cdb61d05da36e98e73337d', '6c304782d17d56cec163146d2d3f6d4ddaa85b7e575666f03af569d326804811',
        '750cbbe86a906eecf6558ad27aedbbcbc053656ef7c8fb732ac99a63a62bb580', '7a8554deaa3032aeab234583b9044f75ce0cf4151e03432f9f82cf24903123a4',
        '7d83a3e643980831d8dc718f7620da8c9bfc529c428bf1c65cd50109947cb902', '82c149eddf8284eb61e6df222507cd1a3e9c7dd28ab19b927e23c5010acdcf8a',
        '84991b9aa24c9d5ec09601c10fcd456cf0e02bee035a86105b107ecbdb36bc5e', '86c53028db2f26625134ec9b99a0b74fda9f6d1bc76ea30256306e2ec613d310',
        '8d41ef861cfea3f55abba7fe5af2f4d27e75d06aa8176761b7e1ad636e183057', '953c3f2ea6c07d77bd91cba30ede80a52ae8335ef378745724b060d000ac49c7',
        '95b25adbb2a8a4471031238a434d45c21ce5e42c67b3950242a69aecc40dad40', '97b2ca36d4637b2728bf6a0497c2822a45db46d245bb546a6a4f128bcee96655',
        '9a4534be273d59f4c90359de530652bdeaa437b58d6785241389116701cf5ecd', '9d0d7662916c92c03e185417bc1e19a7b956c60d0d90d6cabc27ba14cf07488c',
        '9def5914cfc29e727607a2910e43fb2ad4ef3e7d042f1f53f5c751d7ea3f2abd', '9f0c34e14f79f2aded6b5af2429998938e999faa4559031eea5a09a20419cb7f',
        'a1a89f53a910e77f28d7d2931cff46cd3de139b1cd50834811b0dc3f51bc2254', 'a8ddea3a3601e268acfbebbe34da0fd5a6c89732a09bfbd3c04f7b7024fc2c3a',
        'b0eb9717b94f0ecac7e3d1aef3fdcbf8b6087fcadfdfaa4b7c35368cc3c5cb17', 'b58409539908be4e27e028c3a2bc59768516ee66316ae0d69baaca7da97f98ab',
        'be095b6bff247d23f0d5b3048e56d879444f30325f1d4f434877e3b9f629e458', 'c70fa42dc99994ff5cdd9636e949d0e674e8b43055542c9af892668d48af0ca5',
        'd79d569e6d7cf9cb73706949d4f0b273c81cfea6a4f28599f9c1c756bfc5cbb7', 'de26790e5b5b5d4aaabd145188e5456dc1dab324e34c3c710641baf98ffe7e55',
        'df4e8e01cbbe1861f30e02de436a8cf61000e5fdd6df54f9e5a33741ffae6fbe', 'e9314695956d142c4356480be52e8270ee8c3b302dbe74a1bbcb01e78bbb9560',
        'ed4e69a2265314b72a5461ef4a01f96c1d4e71b73322224cf6675d1cdfb97426', 'f0ffea7c49843cff9e9fcf7af31a3bc6a9c237bac88dd10991f1293b12ebfa74',
        'f84bb138d67eee95888ed8f8b2999779d237517b9e92576375190bbc16050a5b', 'f8c6bc66225787d6509488bb8ee6c5c336924f102defdb5397756f2de690ed9d',
        'f98d5d1bf62ba612e6b9ea4d5f9f3080f8f7b08cb2536dfbc30592c8f4b5d508',
    }),
    'typst/manual/sections/04_boundary_current_applications.typ': frozenset({
        '05fd7d6b094b759d16643e1f27c5957c00ad108ce565218cc5fb27294192a249', '1f772be451b09b475295178aadc4e587a2ec50bbc1325ba9be4ef78909a563d9',
        '217c401ad6814365f8234ffca5ba19a85b37e6c48be8d9c49e8155861a43610d', '2224034f2f2af537067e10316cd921a3e3b1753ddb1e9352015d9fa19020225c',
        '2252751f9d51c017f50778ab195bc5c6fa13a594602addae82bee121029ad42f', '2cdfe4bee88fdf2b0e5b65f87fd6135ea3707f51b52aed689fa3a95cef8835bd',
        '3454f2a12a7c6bc870be407c6f07fedb9a8f8d58874b1bb4351fcbd6875dd99c', '3d68708e85e25a011fea3021158580435b5bbbd9b2053c0bb1c2427f7cb8487b',
        '4849abfd4a01f8edf5f58542f4c1e22ba7bc3e05b2f5c3760b5d8ff8389d8de6', '6567d186d438135736a232293f0cb03f05cc24182f639b06a34ab8b61e189389',
        '6bf1a82212bc5a0c25c787f565d09099f90e17624871471d00828e00694f1e6b', '72111cb31e19d70b9a073952ed7fdf44cfe5085481308efce38cebb6ff6dcad1',
        '7681af130c993adcce822c2cc718b4e7af078377f25e9887fb62115cc4e6dd6d', '78f9f7bea7ec8c28aea287ec3ffd210fb343db14d9294d7c7bc838503434e1e2',
        '8fb06aa6a31528928f8e223b80055c67d98a57b93d25c0e79f167c13efad18d9', '9bd4458344f3983d95c5cd81e6dd902888e7b34676f8a4a5c92cc51651bc8836',
        '9c2a94235b4482521f49dbe5c0b1ed4f393d35727232a5027d3495980530e5b0', 'a2d0d3ca6555f8bddf11bffdf923a90f473544fd4fb67735fdabf2c59dec4062',
        'afb24d0f947e3375cacbb3d9bfba1065728cac275093c1bcafa7f2e1b66b1dcc', 'b25568a5524fbe9c53dce7c9235f1d850c35358054c26cf790959399d2007f02',
        'c6c0a63df737abab8624c30e0b32de359bbb316fd45bbadd8eb3167c8e4d6ef9', 'd7aa53732bb70ac9050db14030178e879343ee40381f644497724a28f71df557',
        'e2510fe1f3b544bac96439438dec9f2d021760576f7ac061a47702cc289183fd', 'e45a38a3d57597a1a477883e674d263d90e441fbeaef248963a137ff1a42df79',
        'ee405f714719681ad8005834d887ac73e067ac872c0b7bd55bf23a3f8a3b316d', 'fe431b23865c6cf281b1dc1e0235439ceb07c10c111c746a6b259090798288a6',
    }),
    'typst/manual/sections/05_solar_system_field_tests.typ': frozenset({
        '12465265cbc502ec924baadc1da660420450a6ffccdf9758b7e3b89eb7eface3', '30b1209bbd5da8d8a5e001ed35246f6f688c900e9824ef4667c1bf334d635e8e',
        '8817e5611a386e6b6a136f8ddf708f59d7d64d51e6218881b517d40fadd473cd', '97313f66bd58e97942d756e029a159fc0ce2b3944b2e58e2b7e9b1b3dd2c744b',
        'a4fff3785995fa1b2354ca7efb018813a34f8b01b751cb0b76de03c68dfcef1a', 'e2510fe1f3b544bac96439438dec9f2d021760576f7ac061a47702cc289183fd',
    }),
}

POST_BASELINE_COMPACTED_MANUAL_MATH_SEQ_SHA256: dict[str, str] = {
    'typst/manual/sections/00_awareness_fixtures.typ': '3c56f1f2a66500903a074bbe6772f76b96987a6173c3ceb779edd2b9e58bf7b0',
    'typst/manual/sections/00_dec_ledger.typ': '160a978761d77f4830e7ba95c59a8371fa0198cdb5e2a8de30955b041aec2e0d',
    'typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ': '2dc942343bf167e93fa846e55602a5fa3ab68a091d8cefc94cfd2c5bdeda348a',
    'typst/manual/sections/01_cell_measures.typ': '08bae6a1591135a6bfc957014142135d3fabdf000ed0123b114044263fac4da7',
    'typst/manual/sections/01_rest_energy_prediction.typ': '82ce38fdf710b5b75c739ea08d36d4ab4e6bcf5d12934b59d090517aa2bee3a1',
    'typst/manual/sections/02_hydrogen_facing_shell_tests.typ': '52e91d9a215862574e2cff9b4fe9a345d8b21942651b24bd3658edbdc23e55f8',
    'typst/manual/sections/02_mapping_error.typ': 'db75d49b2bab7b2302ed2982044d8fcf227e7a5be394d285c6eac434ec21b881',
    'typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ': '2b12182d16ebf673dae50b4f233221d867343f542396b051b6c3cdc86c9b017b',
    'typst/manual/sections/03_temporal_observation.typ': 'fc6f68c789a4b82e217b1e7896884ce188405320f82d5a2e2d03fbc4fe54e31b',
    'typst/manual/sections/04_boundary_current_applications.typ': '3f99844724e715fc5f60aaba087678b612853c8ec72c12a8dd33673e82bf5fcd',
    'typst/manual/sections/05_solar_system_field_tests.typ': 'ea432df98537189f44c66b92262d4af4f885d6c22cf07d464538f820b6a22eb3',
}

POST_BASELINE_COMPACTED_MANUAL_CLI_TOKENS: dict[str, tuple[str, ...]] = {
    'typst/manual/sections/00_awareness_fixtures.typ': ('python3 manual/scripts/aod_awareness.py --check-data', 'python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/00_dec_ledger.typ': ('python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ': ('python3 manual/scripts/aod_native_closure_wave.py --check-data', 'python3 manual/scripts/aod_manual_wavelet_si_alignment.py --check', 'python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/01_cell_measures.typ': ('--check-data', '--sector', '--verify-vectors', '--check-zero-float'),
    'typst/manual/sections/01_rest_energy_prediction.typ': ('python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/02_hydrogen_facing_shell_tests.typ': ('python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/02_mapping_error.typ': ('--check', 'python3 manual/scripts/aod_mapping_error.py --check', '--sector', '--verify-vectors', '--check-zero-float'),
    'typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ': ('python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float', 'python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/03_temporal_observation.typ': ('manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float', '--consumer-root', 'manual/scripts/aod_temporal_observation.py --check', '--consumer-root', 'aod_temporal_anchor.py --check-data', 'aod_manual_wavelet_si_alignment.py --check', 'manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/04_boundary_current_applications.typ': ('python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
    'typst/manual/sections/05_solar_system_field_tests.typ': ('python3 -B -m manual.engine --sector boundary_sadar', 'aod-core --verify-vectors --check-zero-float'),
}

POST_BASELINE_COMPACTED_MANUAL_QUALIFIER_COUNTS: dict[str, dict[str, int]] = {
    'typst/manual/sections/00_awareness_fixtures.typ': {'no': 11, 'not': 10, 'never': 4, 'only': 5, 'without': 11, 'unless': 1, 'none': 0, 'cannot': 7, 'neither': 4, 'nor': 2, 'conditional': 1, 'scoped': 0, 'quarantined': 1, 'declared': 11, 'unresolved': 0, 'absent': 1, 'distinct': 5, 'independent': 2, 'external': 0, 'immutable': 3, 'falsification': 6, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/00_dec_ledger.typ': {'no': 2, 'not': 2, 'never': 0, 'only': 5, 'without': 3, 'unless': 0, 'none': 0, 'cannot': 0, 'neither': 0, 'nor': 0, 'conditional': 3, 'scoped': 0, 'quarantined': 0, 'declared': 18, 'unresolved': 0, 'absent': 0, 'distinct': 2, 'independent': 0, 'external': 1, 'immutable': 0, 'falsification': 3, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ': {'no': 2, 'not': 0, 'never': 2, 'only': 6, 'without': 6, 'unless': 0, 'none': 1, 'cannot': 1, 'neither': 2, 'nor': 1, 'conditional': 0, 'scoped': 0, 'quarantined': 0, 'declared': 8, 'unresolved': 0, 'absent': 1, 'distinct': 4, 'independent': 1, 'external': 1, 'immutable': 3, 'falsification': 2, 'necessary': 0, 'sufficient': 1},
    'typst/manual/sections/01_cell_measures.typ': {'no': 3, 'not': 2, 'never': 0, 'only': 2, 'without': 5, 'unless': 0, 'none': 0, 'cannot': 2, 'neither': 1, 'nor': 1, 'conditional': 1, 'scoped': 0, 'quarantined': 1, 'declared': 5, 'unresolved': 0, 'absent': 1, 'distinct': 3, 'independent': 4, 'external': 0, 'immutable': 0, 'falsification': 1, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/01_rest_energy_prediction.typ': {'no': 1, 'not': 2, 'never': 0, 'only': 9, 'without': 3, 'unless': 1, 'none': 0, 'cannot': 1, 'neither': 0, 'nor': 0, 'conditional': 2, 'scoped': 2, 'quarantined': 7, 'declared': 11, 'unresolved': 1, 'absent': 1, 'distinct': 2, 'independent': 2, 'external': 17, 'immutable': 0, 'falsification': 3, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/02_hydrogen_facing_shell_tests.typ': {'no': 0, 'not': 2, 'never': 0, 'only': 2, 'without': 1, 'unless': 0, 'none': 0, 'cannot': 0, 'neither': 0, 'nor': 0, 'conditional': 0, 'scoped': 0, 'quarantined': 9, 'declared': 6, 'unresolved': 1, 'absent': 0, 'distinct': 0, 'independent': 0, 'external': 9, 'immutable': 0, 'falsification': 1, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/02_mapping_error.typ': {'no': 6, 'not': 3, 'never': 1, 'only': 2, 'without': 5, 'unless': 0, 'none': 0, 'cannot': 2, 'neither': 1, 'nor': 1, 'conditional': 1, 'scoped': 0, 'quarantined': 0, 'declared': 8, 'unresolved': 3, 'absent': 1, 'distinct': 3, 'independent': 3, 'external': 1, 'immutable': 0, 'falsification': 1, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ': {'no': 2, 'not': 1, 'never': 3, 'only': 3, 'without': 2, 'unless': 1, 'none': 1, 'cannot': 0, 'neither': 1, 'nor': 1, 'conditional': 2, 'scoped': 0, 'quarantined': 0, 'declared': 10, 'unresolved': 0, 'absent': 0, 'distinct': 4, 'independent': 5, 'external': 3, 'immutable': 0, 'falsification': 1, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/03_temporal_observation.typ': {'no': 5, 'not': 7, 'never': 5, 'only': 3, 'without': 9, 'unless': 0, 'none': 0, 'cannot': 2, 'neither': 4, 'nor': 3, 'conditional': 9, 'scoped': 1, 'quarantined': 0, 'declared': 3, 'unresolved': 3, 'absent': 0, 'distinct': 5, 'independent': 4, 'external': 0, 'immutable': 0, 'falsification': 3, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/04_boundary_current_applications.typ': {'no': 0, 'not': 2, 'never': 0, 'only': 1, 'without': 0, 'unless': 0, 'none': 1, 'cannot': 0, 'neither': 0, 'nor': 0, 'conditional': 1, 'scoped': 8, 'quarantined': 2, 'declared': 10, 'unresolved': 0, 'absent': 0, 'distinct': 1, 'independent': 0, 'external': 3, 'immutable': 0, 'falsification': 0, 'necessary': 0, 'sufficient': 0},
    'typst/manual/sections/05_solar_system_field_tests.typ': {'no': 0, 'not': 3, 'never': 1, 'only': 1, 'without': 0, 'unless': 0, 'none': 0, 'cannot': 0, 'neither': 0, 'nor': 0, 'conditional': 0, 'scoped': 0, 'quarantined': 1, 'declared': 5, 'unresolved': 0, 'absent': 0, 'distinct': 1, 'independent': 0, 'external': 4, 'immutable': 0, 'falsification': 0, 'necessary': 0, 'sufficient': 0},
}

POST_BASELINE_MANUAL_LABELS = frozenset({
    "fig:manual-awareness-matched-feynman",
    "fig:manual-cell-staircase-fold",
    "fig:manual-chiral-stokes-feynman",
    "fig:manual-collision-debris-feynman",
    "fig:manual-dec-chiral-flip-walk",
    "fig:manual-field-dynamics-boundary-feynman",
    "fig:manual-five-boundary-calculation-spine",
    "fig:manual-hydrogen-shell-wavelet-atlas",
    "fig:manual-lensing-ray-boundary-feynman",
    "fig:manual-native-closure-q4-walk",
    "fig:manual-qext-quarantine-firewall",
    "fig:manual-registry-engine-coverage",
    "fig:manual-rest-energy-debris-atlas",
    "fig:manual-short-window-boundary-feynman",
    "fig:manual-solar-boundary-scopes-feynman",
    "fig:manual-tau-five-boundary-sadar",
    "fig:manual-temporal-si-bridge-feynman",
    "fig:manual-typed-map-variance-feynman",
    "fig:manual-wire-moving-boundary-feynman",
    "manual:app-c:dec-lag1-walk",
    "manual:dec-ledger:chiral-flips",
    "manual:field-dynamics:dec-run-tumble-stepper",
    "manual:hydrogen:dec-wavelet-transitions",
    "manual:lensing:dec-chiral-ray-walk",
    "manual:m1:dec-closure-walk",
    "manual:m2:dec-operativity-walk",
    "manual:m3-cells:dec-staircase-fold",
    "manual:m3-maps:dec-joint-laws",
    "manual:m3-temporal:dec-si-bridge",
    "manual:qext:dec-quarantine-firewall",
    "manual:registry:engine-dec-master",
    "manual:rest:boundary-sadar-debris",
    "manual:scope:five-boundary-spine",
    "manual:short-window:dec-clipping-ledger",
    "manual:simfix:exact-rational-dec",
    "manual:solar:dec-o0-boundary-audit",
    "manual:wire:dec-moving-boundary",
    "tab:manual-app-a-exact-shedding-dec",
    "tab:manual-app-c-3d-dec-ledger",
    "tab:manual-awareness-dec-ledger",
    "tab:manual-cell-boundary-fold-ledger",
    "tab:manual-chapter-dec-boundary-index",
    "tab:manual-engine-dec-master-registry",
    "tab:manual-field-dynamics-dec-spine",
    "tab:manual-hydrogen-dec-transitions",
    "tab:manual-lensing-dec-ray-walk",
    "tab:manual-native-closure-dec-walk",
    "tab:manual-qext-precision-ledger",
    "tab:manual-short-window-dec-ledger",
    "tab:manual-solar-dec-boundary-audit",
    "tab:manual-tau-five-boundary-trace",
    "tab:manual-temporal-dec-bridge",
    "tab:manual-typed-map-joint-laws",
    "tab:manual-wire-moving-boundary-dec",
})

TRUSTED_TEMPLATE_SHA256 = {
    "typst/lib/aod_schema.typ": "6fa865ba193f1f2e1dce27fe126dd799f1dd6726ada2c4ff43531696685460b4",
    "typst/lib/aod_plots.typ": "bf0aff2c8a71f5c7d707e4c007b41d2ab308c3193ebcad87533e142fc8504d33",
    "typst/preamble.typ": "7a9c255c2411bc4bd3487be0196f10ac453eefa240f6c16095d426f210b4f112",
    "typst/manual/preamble.typ": "2b7deae2f0fa3d7011edabd8d7299b835290fb60e47990c7fe861e55bd914196",
    "typst/main.typ": "fc8d4cb59c86b59f0a6ee6fe1b0ea968edcf00f2e84d05e2cfcfb25abf57db70",
    "typst/manual/main.typ": "c3d6a18bb6a8020481259a6771611e41c50f188190e35e1c9b5ec58848d8760a",
}

# Callable -> permitted named arguments, for code / `#`-introduced calls in content files.
CONTENT_CALL_ALLOWLIST: dict[str, frozenset] = {
    "align": frozenset(), "aod-anchor": frozenset(), "aod-boxed": frozenset(),
    "aod-cite": frozenset({"supplement"}),
    "aod-csv-table": frozenset({"align", "cells", "columns", "filter-col", "filter-values", "headers", "inset", "size"}),
    "aod-definition": frozenset({"title"}), "aod-flowchart": frozenset({"height", "width"}),
    "aod-literature-note": frozenset(), "aod-noteblock": frozenset(), "aod-nowrap": frozenset(),
    "aod-panel": frozenset({"width"}),
    "aod-paragraph": frozenset(), "aod-provenance": frozenset(), "aod-raw-wrap": frozenset(),
    "aod-remark": frozenset(),
    "aod-uncaptioned-longtable": frozenset(), "appref": frozenset(), "bare-ref": frozenset(),
    "block": frozenset({"above", "below", "width"}),
    "counter": frozenset(), "counter().update": frozenset(), "emph": frozenset(), "eqnref": frozenset(),
    "eqref": frozenset(), "figref": frozenset(), "figure": frozenset({"caption", "kind"}), "image": frozenset({"width"}),
    "link": frozenset(), "mainappendix": frozenset(), "mainequation": frozenset(), "mainsection": frozenset(),
    "math.equation": frozenset({"block", "numbering"}), "pad": frozenset({"left", "right"}),
    "page": frozenset({"numbering"}), "pagebreak": frozenset({"weak"}), "par": frozenset({"justify"}),
    "raw": frozenset(), "secref": frozenset(), "strong": frozenset(), "table": frozenset({"align", "columns", "inset"}),
    "table.header": frozenset(), "tabref": frozenset(), "tagged-eq": frozenset(),
    "text": frozenset({"size", "style"}), "upright": frozenset(), "v": frozenset(),
}
CONTENT_SET_ALLOWLIST: dict[str, frozenset] = {"text": frozenset({"size"}), "par": frozenset({"justify"})}
CONTENT_FORBIDDEN_KEYWORDS = frozenset({"show", "let", "context", "if", "for", "while", "return"})
# Functions that can hide, overlay, recolour, transform or synthesize evaluated content.
EVALUATION_FORBIDDEN_CALLS = frozenset({
    "hide", "place", "scale", "move", "rotate", "skew", "eval", "read", "json", "yaml", "toml", "csv",
    "xml", "cbor", "plugin", "regex", "upper", "lower", "smallcaps", "highlight", "strike", "underline",
    "state", "metadata", "query", "locate", "here", "layout", "measure", "rect", "square", "circle",
    "ellipse", "polygon", "path", "curve", "line", "stack", "columns", "repeat", "rgb", "luma", "cmyk",
    "color", "oklab", "oklch", "gradient", "tiling", "text", "box", "block", "str", "repr", "label",
    "selector", "numbering", "sys",
})
EVALUATION_FORBIDDEN_ARGS = frozenset({
    "fill", "opacity", "clip", "tracking", "spacing", "dx", "dy", "outset", "hidden", "font", "fallback",
    "top-edge", "bottom-edge", "baseline", "cover", "overhang", "costs", "features", "lang", "region",
})
CONTENT_TEXT_SIZES = frozenset({"7.0pt", "7.5pt", "7.6pt", "8.0pt", "8.5pt", "9.5pt", "10pt", "12pt", "14pt", "17pt"})
POSITIVE_LENGTH_ARGS: dict[str, frozenset] = {
    "pad": frozenset({"left", "right"}),
    "block": frozenset({"above", "below", "width"}),
    "image": frozenset({"width"}),
    "aod-panel": frozenset({"width"}),
    "aod-flowchart": frozenset({"width", "height"}),
}
FLOWCHART_NODE_KEYS = frozenset({"id", "x", "y", "w", "h", "body", "dy-in", "dy-out"})
FLOWCHART_EDGE_KEYS = frozenset({"from", "to"})
CSV_TABLE_PATH_RE = re.compile(r"^/manual/data/boundary_sadar/[a-z0-9_]+\.csv$")
CSV_TABLE_COL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CSV_TABLE_ALIGN_VALUES = frozenset({"left", "center", "right"})
CSV_TABLE_STACK_STYLES = frozenset({"plain", "raw-wrap", "wrap-sub-paren"})
CSV_TABLE_SINGLE_COL_KINDS = frozenset({"plain", "wrap", "raw", "raw-wrap", "minus", "signed", "rat", "vec"})

_TYP_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*")
_TYP_KEYWORDS = frozenset({
    "show", "let", "set", "import", "include", "context", "if", "else", "for", "while", "return",
    "break", "continue", "in", "not", "and", "or", "none", "auto", "true", "false",
})


def _typ_skip_string(s: str, i: int) -> int:
    j = i + 1
    while j < len(s) and s[j] != '"':
        j += 2 if s[j] == "\\" else 1
    return j + 1


def _typ_skip_raw(s: str, i: int) -> int:
    fence = re.match(r"`+", s[i:]).group(0)
    if len(fence) == 2:
        return i + 2
    j = s.find(fence, i + len(fence))
    return len(s) if j < 0 else j + len(fence)


def _typ_balanced(s: str, i: int, op: str, cl: str, *, skip_math: bool = True) -> int:
    """Index just after the bracket matching s[i] == op (strings, raw spans, comments, and optionally $...$ honoured)."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == '"' and op != "[":
            j = _typ_skip_string(s, j)
            continue
        if c == "`":
            j = _typ_skip_raw(s, j)
            continue
        if skip_math and c == "$":
            j = min(_typ_math_end(s, j + 1) + 1, n)
            continue
        if s.startswith("//", j) and (j == 0 or s[j - 1] != ":"):
            k = s.find("\n", j)
            j = n if k < 0 else k
            continue
        if s.startswith("/*", j):
            k = s.find("*/", j + 2)
            j = n if k < 0 else k + 2
            continue
        if c == op:
            depth += 1
        elif c == cl:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return n


def _typ_math_end(s: str, i: int, limit: int | None = None) -> int:
    """Index of the `$` closing a math span whose body starts at s[i] (nested `#code[$..$]` honoured)."""
    limit = len(s) if limit is None else limit
    j = i
    while j < limit:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == '"':
            j = _typ_skip_string(s, j)
            continue
        if c == "$":
            return j
        if c == "#":
            m = _TYP_IDENT.match(s, j + 1)
            k = m.end() if m else j + 1
            while k < limit and s[k] in "([{":
                op = s[k]
                k = _typ_balanced(s, k, op, {"(": ")", "[": "]", "{": "}"}[op])
            j = max(k, j + 1)
            continue
        j += 1
    return limit


def _typ_split_args(args: str) -> tuple[dict[str, str], list[str]]:
    """Top-level named arguments (name -> raw value) and positional arguments of a call."""
    parts: list[str] = []
    depth, cur, i = 0, [], 0
    while i < len(args):
        c = args[i]
        if c == '"':
            j = _typ_skip_string(args, i)
            cur.append(args[i:j])
            i = j
            continue
        if c == "$":
            j = min(_typ_math_end(args, i + 1) + 1, len(args))
            cur.append(args[i:j])
            i = j
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    if "".join(cur).strip():
        parts.append("".join(cur))
    named: dict[str, str] = {}
    positional: list[str] = []
    for p in parts:
        m = re.match(r"\s*([a-z][a-z0-9-]*)\s*:(?!:)", p)
        if m:
            named[m.group(1)] = p[m.end():].strip()
        else:
            positional.append(p.strip())
    return named, positional


def _parse_positive_length(val: str, units: tuple[str, ...] = ("%", "em", "pt", "cm", "mm", "in")) -> float | None:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([A-Za-z%]+)", val.strip())
    if not m or m.group(2) not in units:
        return None
    num = float(m.group(1))
    return num if num > 0.0 else None


def _validate_flowchart_policy(where: str, named: dict[str, str], pos: list[str]) -> list[str]:
    """Validate #aod-flowchart dimensions and ensure every node box stays strictly inside [0,W]x[0,H]."""
    errs: list[str] = []
    w_cm = _parse_positive_length(named.get("width", ""), ("cm",))
    h_cm = _parse_positive_length(named.get("height", ""), ("cm",))
    if w_cm is None or h_cm is None:
        errs.append(f"{where}: flowchart width/height must be positive literal cm lengths")
        return errs
    if len(pos) != 2 or not (pos[0].startswith("(") and pos[0].endswith(")")) or not (pos[1].startswith("(") and pos[1].endswith(")")):
        errs.append(f"{where}: flowchart expects (nodes, edges) literal tuples")
        return errs
    _, node_entries = _typ_split_args(pos[0][1:-1])
    _, edge_entries = _typ_split_args(pos[1][1:-1])
    node_ids: set[str] = set()
    for entry in node_entries:
        e = entry.strip()
        if not (e.startswith("(") and e.endswith(")")):
            errs.append(f"{where}: malformed flowchart node entry")
            continue
        nd, npos = _typ_split_args(e[1:-1])
        extra_k = sorted(set(nd) - FLOWCHART_NODE_KEYS)
        if npos or extra_k:
            errs.append(f"{where}: non-allowlisted flowchart node keys/args {extra_k}")
            continue
        if "id" not in nd or not nd["id"].startswith('"'):
            errs.append(f"{where}: flowchart node id must be a string literal")
            continue
        nid, _ = parse_typ_str_lit(nd["id"], 0)
        node_ids.add(nid)
        x = _parse_positive_length(nd.get("x", ""), ("cm",))
        y = _parse_positive_length(nd.get("y", ""), ("cm",))
        nw = _parse_positive_length(nd.get("w", "4.8cm"), ("cm",))
        nh = _parse_positive_length(nd.get("h", "1.05cm"), ("cm",))
        if x is None or y is None or nw is None or nh is None:
            errs.append(f"{where}: flowchart node {nid!r} geometry must use positive literal cm lengths")
            continue
        if x - nw / 2.0 < -0.05 or x + nw / 2.0 > w_cm + 0.05 or y - nh / 2.0 < -0.05 or y + nh / 2.0 > h_cm + 0.05:
            errs.append(
                f"{where}: flowchart node {nid!r} box ({x}±{nw/2:.2f}, {y}±{nh/2:.2f}) "
                f"exceeds flowchart bounds [0, {w_cm}] x [0, {h_cm}]"
            )
    for entry in edge_entries:
        e = entry.strip()
        if not (e.startswith("(") and e.endswith(")")):
            errs.append(f"{where}: malformed flowchart edge entry")
            continue
        ed, epos = _typ_split_args(e[1:-1])
        extra_k = sorted(set(ed) - FLOWCHART_EDGE_KEYS)
        if epos or extra_k or "from" not in ed or "to" not in ed:
            errs.append(f"{where}: non-allowlisted flowchart edge keys/args {extra_k}")
            continue
        if not ed["from"].startswith('"') or not ed["to"].startswith('"'):
            errs.append(f"{where}: flowchart edge endpoints must be string literals")
            continue
        src, _ = parse_typ_str_lit(ed["from"], 0)
        dst, _ = parse_typ_str_lit(ed["to"], 0)
        if src not in node_ids or dst not in node_ids:
            errs.append(f"{where}: flowchart edge references undeclared node ({src!r} -> {dst!r})")
    return errs


def _parse_exact_typ_str_lit(val: str) -> str | None:
    s = val.strip()
    if not (len(s) >= 2 and s.startswith('"') and s.endswith('"')):
        return None
    try:
        parsed, end_idx = parse_typ_str_lit(s, 0)
    except ValueError:
        return None
    return parsed if end_idx == len(s) else None


def _is_exact_typ_content_block(val: str) -> bool:
    s = val.strip()
    return len(s) >= 2 and s.startswith("[") and _typ_balanced(s, 0, "[", "]") == len(s)


def _validate_table_inset(where: str, val: str) -> list[str]:
    s = val.strip()
    pt = _parse_positive_length(s, ("pt",))
    if pt is not None:
        return [] if pt <= 12.0 else [f"{where}: table inset {val!r} exceeds 12pt"]
    if s.startswith("(") and s.endswith(")") and _typ_balanced(s, 0, "(", ")") == len(s):
        nd, npos = _typ_split_args(s[1:-1])
        if npos or not nd or not (set(nd) <= {"x", "y"}):
            return [f"{where}: table inset {val!r} must be positive literal pt <= 12pt or (x: <pt>, y: <pt>)"]
        errs: list[str] = []
        for k, v in sorted(nd.items()):
            lpt = _parse_positive_length(v, ("pt",))
            if lpt is None or lpt > 12.0:
                errs.append(f"{where}: table inset `{k}={v!r}` must be positive literal pt <= 12pt")
        return errs
    return [f"{where}: table inset {val!r} must be positive literal pt <= 12pt or (x: <pt>, y: <pt>)"]


def _validate_csv_cell_spec(where: str, raw: str, depth: int = 0) -> list[str]:
    if depth > 4:
        return [f"{where}: aod-csv-table cell spec recursion depth exceeded"]
    s = raw.strip()
    lit = _parse_exact_typ_str_lit(s)
    if lit is not None:
        if not CSV_TABLE_COL_RE.fullmatch(lit):
            return [f"{where}: aod-csv-table column name {lit!r} is invalid"]
        return []
    if not (s.startswith("(") and s.endswith(")") and _typ_balanced(s, 0, "(", ")") == len(s)):
        return [f"{where}: aod-csv-table cell spec must be a literal column string or spec dict ({s[:60]!r})"]
    nd, npos = _typ_split_args(s[1:-1])
    if npos or "kind" not in nd:
        return [f"{where}: aod-csv-table cell spec dict must contain named `kind:` and no positional args"]
    kind = _parse_exact_typ_str_lit(nd["kind"])
    if kind is None:
        return [f"{where}: aod-csv-table cell spec `kind` must be a string literal"]

    def _check_col_key(key: str) -> list[str]:
        v = _parse_exact_typ_str_lit(nd.get(key, ""))
        if v is None or not CSV_TABLE_COL_RE.fullmatch(v):
            return [f"{where}: aod-csv-table `{kind}` key `{key}` must be a literal column identifier"]
        return []

    keys = set(nd)
    if kind in CSV_TABLE_SINGLE_COL_KINDS:
        if keys != {"kind", "col"}:
            return [f"{where}: aod-csv-table `{kind}` spec must have exact keys (kind, col), got {sorted(keys)}"]
        return _check_col_key("col")
    if kind == "arrow":
        if keys != {"kind", "left", "right"}:
            return [f"{where}: aod-csv-table `arrow` spec must have exact keys (kind, left, right), got {sorted(keys)}"]
        return _check_col_key("left") + _check_col_key("right")
    if kind == "wrap-paren":
        if keys != {"kind", "col", "paren"}:
            return [f"{where}: aod-csv-table `wrap-paren` spec must have exact keys (kind, col, paren), got {sorted(keys)}"]
        return _check_col_key("col") + _check_col_key("paren")
    if kind == "stack":
        if not ({"kind", "top", "bottom"} <= keys <= {"kind", "top", "bottom", "style"}):
            return [f"{where}: aod-csv-table `stack` spec keys {sorted(keys)} not allowed"]
        errs = _check_col_key("top") + _check_col_key("bottom")
        if "style" in nd:
            st = _parse_exact_typ_str_lit(nd["style"])
            if st not in CSV_TABLE_STACK_STYLES:
                errs.append(f"{where}: aod-csv-table `stack` style {nd['style']!r} not in {sorted(CSV_TABLE_STACK_STYLES)}")
        return errs
    if kind == "tuple":
        if keys != {"kind", "cols"}:
            return [f"{where}: aod-csv-table `tuple` spec must have exact keys (kind, cols), got {sorted(keys)}"]
        ct = nd["cols"].strip()
        if not (ct.startswith("(") and ct.endswith(")") and _typ_balanced(ct, 0, "(", ")") == len(ct)):
            return [f"{where}: aod-csv-table `tuple` cols must be a literal tuple"]
        cnd, cpos = _typ_split_args(ct[1:-1])
        if cnd or not cpos:
            return [f"{where}: aod-csv-table `tuple` cols must be a non-empty positional tuple"]
        errs: list[str] = []
        for item in cpos:
            cname = _parse_exact_typ_str_lit(item)
            if cname is None or not CSV_TABLE_COL_RE.fullmatch(cname):
                errs.append(f"{where}: aod-csv-table `tuple` column {item!r} must be a literal column identifier")
        return errs
    if kind == "slot":
        if keys != {"kind", "edge", "sigma"}:
            return [f"{where}: aod-csv-table `slot` spec must have exact keys (kind, edge, sigma), got {sorted(keys)}"]
        return _check_col_key("edge") + _check_col_key("sigma")
    if kind == "sweep-shed":
        if keys != {"kind", "sweep", "shed"}:
            return [f"{where}: aod-csv-table `sweep-shed` spec must have exact keys (kind, sweep, shed), got {sorted(keys)}"]
        return _check_col_key("sweep") + _check_col_key("shed")
    if kind == "math-eq":
        if keys != {"kind", "lhs", "col"}:
            return [f"{where}: aod-csv-table `math-eq` spec must have exact keys (kind, lhs, col), got {sorted(keys)}"]
        errs = _check_col_key("col")
        if not _is_exact_typ_content_block(nd["lhs"]):
            errs.append(f"{where}: aod-csv-table `math-eq` lhs must be a literal content block [...]")
        return errs
    if kind == "union-cur":
        if not ({"kind", "union", "cur"} <= keys <= {"kind", "union", "cur", "lhs"}):
            return [f"{where}: aod-csv-table `union-cur` spec keys {sorted(keys)} not allowed"]
        errs = _check_col_key("union") + _check_col_key("cur")
        if "lhs" in nd and not _is_exact_typ_content_block(nd["lhs"]):
            errs.append(f"{where}: aod-csv-table `union-cur` lhs must be a literal content block [...]")
        return errs
    if kind == "when":
        if keys != {"kind", "col", "eq", "then", "otherwise"}:
            return [f"{where}: aod-csv-table `when` spec must have exact keys (kind, col, eq, then, otherwise), got {sorted(keys)}"]
        errs = _check_col_key("col")
        if _parse_exact_typ_str_lit(nd["eq"]) is None:
            errs.append(f"{where}: aod-csv-table `when` eq must be a string literal")
        errs.extend(_validate_csv_cell_spec(where, nd["then"], depth + 1))
        errs.extend(_validate_csv_cell_spec(where, nd["otherwise"], depth + 1))
        return errs
    return [f"{where}: unsupported aod-csv-table cell spec kind {kind!r}"]


def _validate_csv_table_policy(where: str, named: dict[str, str], pos: list[str]) -> list[str]:
    """Strictly validate #aod-csv-table path, typography, geometry, and declarative cell specs."""
    errs: list[str] = []
    if len(pos) != 1:
        return [f"{where}: aod-csv-table requires exactly 1 positional literal CSV path"]
    csv_path = _parse_exact_typ_str_lit(pos[0])
    if csv_path is None or not CSV_TABLE_PATH_RE.fullmatch(csv_path):
        errs.append(
            f"{where}: aod-csv-table path {pos[0]!r} must be a literal matching ^/manual/data/boundary_sadar/[a-z0-9_]+\\.csv$"
        )
    if "size" in named and named["size"].strip() not in CONTENT_TEXT_SIZES:
        errs.append(f"{where}: aod-csv-table size {named['size']!r} outside the reviewed sizes")
    if "inset" in named:
        errs.extend(_validate_table_inset(where, named["inset"]))

    def _split_tuple(arg_name: str) -> list[str] | None:
        raw = named.get(arg_name, "").strip()
        if not (raw.startswith("(") and raw.endswith(")") and _typ_balanced(raw, 0, "(", ")") == len(raw)):
            errs.append(f"{where}: aod-csv-table `{arg_name}` must be a literal tuple (...)")
            return None
        nd, items = _typ_split_args(raw[1:-1])
        if nd or not items:
            errs.append(f"{where}: aod-csv-table `{arg_name}` must be a non-empty positional tuple")
            return None
        return items

    cols = _split_tuple("columns")
    aligns = _split_tuple("align")
    headers = _split_tuple("headers")
    cells = _split_tuple("cells")

    if cols is not None:
        for c in cols:
            cs = c.strip()
            if cs != "auto" and _parse_positive_length(cs, ("fr", "%", "pt", "cm", "mm", "em")) is None:
                errs.append(f"{where}: aod-csv-table column width {c!r} is not `auto` or a positive literal length")
    if aligns is not None:
        for a in aligns:
            if a.strip() not in CSV_TABLE_ALIGN_VALUES:
                errs.append(f"{where}: aod-csv-table align value {a!r} not in {sorted(CSV_TABLE_ALIGN_VALUES)}")
    if headers is not None:
        for h in headers:
            if not _is_exact_typ_content_block(h):
                errs.append(f"{where}: aod-csv-table header {h[:40]!r} must be a literal content block [...]")
    if cells is not None:
        for cell in cells:
            errs.extend(_validate_csv_cell_spec(where, cell, 0))
    if cols is not None and aligns is not None and headers is not None and cells is not None:
        if not (len(cols) == len(aligns) == len(headers) == len(cells)):
            errs.append(
                f"{where}: aod-csv-table arity mismatch (columns={len(cols)}, align={len(aligns)}, "
                f"headers={len(headers)}, cells={len(cells)})"
            )

    has_fcol = "filter-col" in named
    has_fvals = "filter-values" in named
    if has_fcol != has_fvals:
        errs.append(f"{where}: aod-csv-table must provide both `filter-col` and `filter-values` together")
    elif has_fcol and has_fvals:
        fc = _parse_exact_typ_str_lit(named["filter-col"])
        if fc is None or not CSV_TABLE_COL_RE.fullmatch(fc):
            errs.append(f"{where}: aod-csv-table `filter-col` must be a literal column identifier")
        fvals = _split_tuple("filter-values")
        if fvals is not None:
            for fv in fvals:
                if _parse_exact_typ_str_lit(fv) is None:
                    errs.append(f"{where}: aod-csv-table `filter-values` item {fv!r} must be a string literal")
    return errs


def scan_typst_events(text: str) -> list[tuple]:
    """Mode-aware scan of Typst source: (mode, kind, name, named_args, positional_args, line).

    mode: 'markup#' / 'math#' (code introduced by '#'), 'code' (inside code arguments/blocks),
    'math' (bare math-mode function call). kind: 'call', 'ref', 'kw', 'set', or 'forbidden_expr'.
    """
    events: list[tuple] = []
    n_text = len(text)

    def line_of(i: int) -> int:
        return text.count("\n", 0, i) + 1

    def code_expr(i: int, mode: str) -> int:
        m = _TYP_IDENT.match(text, i)
        if not m:
            if i < n_text and text[i] in "{(":
                op, cl = ("{", "}") if text[i] == "{" else ("(", ")")
                j = _typ_balanced(text, i, op, cl)
                if op == "(":
                    events.append((mode, "forbidden_expr", "(", {}, [], line_of(i)))
                code_block(i + 1, j - 1)
                return j
            return i
        name = m.group(0)
        j = m.end()
        head = name.split(".")[0]
        if head in _TYP_KEYWORDS:
            k, depth = j, 0
            while k < n_text:
                c = text[k]
                if c == '"':
                    k = _typ_skip_string(text, k)
                    continue
                if c in "([{":
                    depth += 1
                elif c in ")]}":
                    if depth == 0:
                        break
                    depth -= 1
                elif depth == 0 and c in "\n;":
                    break
                k += 1
            stmt = text[j:k]
            if head == "set":
                ms = _TYP_IDENT.match(stmt.lstrip())
                named: dict[str, str] = {}
                pos: list[str] = []
                pa = stmt.find("(")
                if pa >= 0:
                    pe = _typ_balanced(stmt, pa, "(", ")")
                    named, pos = _typ_split_args(stmt[pa + 1:pe - 1])
                events.append((mode, "set", ms.group(0) if ms else "", named, pos, line_of(i)))
            elif head not in ("none", "auto", "true", "false", "in", "not", "and", "or", "else"):
                events.append((mode, "kw", head, {}, [stmt.strip()[:200]], line_of(i)))
            code_block(j, k)
            return k
        named, pos = {}, []
        called = False
        while j < n_text and text[j] in "([":
            if text[j] == "(":
                e = _typ_balanced(text, j, "(", ")")
                n2, p2 = _typ_split_args(text[j + 1:e - 1])
                named.update(n2)
                pos += p2
                code_block(j + 1, e - 1)
            else:
                e = _typ_balanced(text, j, "[", "]")
                markup(j + 1, e - 1)
            j = e
            called = True
            mm = re.match(r"\.([A-Za-z_][A-Za-z0-9_-]*)", text[j:])
            if mm and j + mm.end() < n_text and text[j + mm.end()] in "([":
                events.append((mode, "call", name, named, pos, line_of(i)))
                name = name + "()." + mm.group(1)
                named, pos = {}, []
                j += mm.end()
        events.append((mode, "call" if called else "ref", name, named, pos, line_of(i)))
        return j

    def code_block(a: int, b: int) -> None:
        i = a
        while i < b:
            c = text[i]
            if c == '"':
                i = _typ_skip_string(text, i)
                continue
            if c == "`":
                i = _typ_skip_raw(text, i)
                continue
            if text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
                k = text.find("\n", i)
                i = b if k < 0 or k > b else k
                continue
            if text.startswith("/*", i):
                k = text.find("*/", i + 2)
                i = b if k < 0 else k + 2
                continue
            if c == "(":
                e = _typ_balanced(text, i, "(", ")")
                if e < b and text[e] in "([":
                    events.append(("code", "forbidden_expr", "(", {}, [], line_of(i)))
                code_block(i + 1, min(e - 1, b))
                i = e
                continue
            if c == "[":
                e = _typ_balanced(text, i, "[", "]")
                markup(i + 1, e - 1)
                i = e
                continue
            if c == "$":
                e = _typ_math_end(text, i + 1, b)
                math(i + 1, e)
                i = e + 1
                continue
            ml = re.match(r"<[A-Za-z0-9_:.-]+>", text[i:])
            if c == "<" and ml:
                i += ml.end()
                continue
            m = _TYP_IDENT.match(text, i)
            if m and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] in "_-.")):
                # Skip named-argument / dictionary keys (`key: value`, not `::`).
                k_after = m.end()
                while k_after < b and text[k_after] in " \t":
                    k_after += 1
                if k_after < b and text[k_after] == ":" and (k_after + 1 >= b or text[k_after + 1] != ":"):
                    i = k_after + 1
                    continue
                i = code_expr(i, "code")
                continue
            i += 1

    def math(a: int, b: int) -> None:
        i = a
        while i < b:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == '"':
                i = _typ_skip_string(text, i)
                continue
            if c == "#":
                i = code_expr(i + 1, "math#")
                continue
            m = _TYP_IDENT.match(text, i)
            if m and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
                j = m.end()
                if j < b and text[j] == "(":
                    e = _typ_balanced(text, j, "(", ")", skip_math=False)
                    named, pos = _typ_split_args(text[j + 1:e - 1])
                    events.append(("math", "call", m.group(0), named, pos, line_of(i)))
                    math(j + 1, e - 1)
                    i = e
                    continue
                i = j
                continue
            i += 1

    def markup(a: int, b: int) -> None:
        i = a
        while i < b:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == "`":
                i = _typ_skip_raw(text, i)
                continue
            if text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
                k = text.find("\n", i)
                i = b if k < 0 or k > b else k
                continue
            if text.startswith("/*", i):
                k = text.find("*/", i + 2)
                i = b if k < 0 else k + 2
                continue
            if c == "$":
                e = _typ_math_end(text, i + 1, b)
                math(i + 1, e)
                i = e + 1
                continue
            if c == "#":
                i = code_expr(i + 1, "markup#")
                continue
            i += 1

    markup(0, n_text)
    return events


def _has_forbidden_segment(name: str) -> bool:
    return any(seg.rstrip("_") in EVALUATION_FORBIDDEN_CALLS for seg in name.split("."))


def _content_policy_violations(rel: str, text: str, typst_targets: set[str]) -> tuple[list[str], int]:
    violations: list[str] = []
    events = scan_typst_events(text)
    base_dir = posixpath.dirname(rel)
    for mode, kind, name, named, pos, line in events:
        where = f"{rel}:{line}"
        if kind == "forbidden_expr":
            violations.append(f"{where}: parenthesized expression/callee `{name}...` is forbidden in content files")
            continue
        if kind == "kw":
            if name in CONTENT_FORBIDDEN_KEYWORDS:
                violations.append(f"{where}: forbidden `{name}` in content file ({pos[0][:80]!r})")
            elif name == "import":
                m_imp = re.fullmatch(r'"([^"]+)"\s*:\s*\*', pos[0].strip())
                tgt = posixpath.normpath(posixpath.join(base_dir, m_imp.group(1))) if m_imp else ""
                allowed_imports = ("typst/preamble.typ", "typst/manual/preamble.typ")
                if rel.startswith("typst/lib/diagrams/"):
                    allowed_imports = ("typst/lib/aod_schema.typ",)
                if tgt not in allowed_imports:
                    violations.append(f"{where}: import other than the surface preamble ({pos[0][:80]!r})")
            elif name == "include":
                m_inc = re.fullmatch(r'"([^"]+)"', pos[0].strip())
                tgt = posixpath.normpath(posixpath.join(base_dir, m_inc.group(1))) if m_inc else ""
                if tgt not in typst_targets:
                    violations.append(f"{where}: include of a file outside the manifest ({pos[0][:80]!r})")
            else:
                violations.append(f"{where}: unexpected keyword `{name}` in content file")
            continue
        if any(p.startswith("..") for p in pos):
            violations.append(f"{where}: argument spread `..` is forbidden on `{name}` in content files")
        if kind == "set":
            allowed = CONTENT_SET_ALLOWLIST.get(name)
            if allowed is None or not set(named) <= allowed or pos:
                violations.append(f"{where}: set rule `set {name}({', '.join(sorted(named))})` is not content-neutral")
            if name == "text" and named.get("size") not in CONTENT_TEXT_SIZES:
                violations.append(f"{where}: set text size {named.get('size')!r} outside the reviewed sizes")
            continue
        bad_args = sorted(set(named) & EVALUATION_FORBIDDEN_ARGS)
        if bad_args:
            violations.append(f"{where}: forbidden styling argument(s) {bad_args} on `{name}`")
        if kind != "call":
            if _has_forbidden_segment(name):
                violations.append(f"{where}: reference to evaluation-altering function `{name}`")
            continue
        if mode == "math":
            if _has_forbidden_segment(name):
                violations.append(f"{where}: forbidden math-mode call `{name}(...)`")
            continue
        allowed = CONTENT_CALL_ALLOWLIST.get(name)
        if allowed is None:
            violations.append(f"{where}: call `{name}` is not in the content allowlist")
            continue
        extra = sorted(set(named) - allowed)
        if extra:
            violations.append(f"{where}: `{name}` with non-allowlisted argument(s) {extra}")
        if name == "text" and named.get("size") not in CONTENT_TEXT_SIZES:
            violations.append(f"{where}: text size {named.get('size')!r} outside the reviewed sizes")
        if name == "table" and "inset" in named:
            violations.extend(_validate_table_inset(where, named["inset"]))
        if name == "aod-csv-table":
            violations.extend(_validate_csv_table_policy(where, named, pos))
        if name == "aod-raw-wrap":
            if len(pos) != 1 or _parse_exact_typ_str_lit(pos[0]) is None:
                violations.append(f"{where}: `aod-raw-wrap` requires exactly 1 literal string argument")
        if name == "aod-nowrap" and pos:
            violations.append(f"{where}: `aod-nowrap` accepts only a content block [...] and no positional paren arguments")
        if name in POSITIVE_LENGTH_ARGS:
            for arg_k in POSITIVE_LENGTH_ARGS[name]:
                if arg_k in named and _parse_positive_length(named[arg_k]) is None:
                    violations.append(f"{where}: `{name}` argument `{arg_k}={named[arg_k]!r}` must be a positive literal length")
        if name == "aod-flowchart":
            violations.extend(_validate_flowchart_policy(where, named, pos))
        if name == "v" and not all(re.fullmatch(r"\d+(?:\.\d+)?(?:em|pt|fr)", p) for p in pos):
            violations.append(f"{where}: vertical spacing {pos!r} is not a non-negative literal length")
        if name in ("counter", "counter().update") and pos not in (["page"], ["1"]):
            violations.append(f"{where}: counter manipulation {pos!r} is not the reviewed page reset")
    return violations, len(events)


VECTOR_FIGURE_ALLOWED_KEYWORDS = frozenset({"import", "let", "for", "if"})
VECTOR_FIGURE_FORBIDDEN_IDENTIFIERS = frozenset({
    "eval", "regex", "read", "json", "toml", "xml", "yaml", "image", "cbor",
    "plugin", "sys", "std", "bibliography", "figure", "heading", "cite", "footnote",
    "link", "metadata", "raw", "include", "show", "set",
    "hide", "query", "state", "counter", "locate", "here", "layout", "measure", "selector",
})


def _strip_typst_comments_nested(text: str) -> str:
    """Strip Typst // line comments and nested /* ... */ block comments while preserving strings, raw spans, and line numbers."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = _typ_skip_string(text, i)
            out.append(text[i:j])
            i = j
            continue
        if c == "`":
            j = _typ_skip_raw(text, i)
            out.append(text[i:j])
            i = j
            continue
        if text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
            k = text.find("\n", i)
            i = n if k < 0 else k
            continue
        if text.startswith("/*", i):
            depth = 1
            j = i + 2
            while j < n and depth > 0:
                if text.startswith("/*", j):
                    depth += 1
                    j += 2
                elif text.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            newlines = text[i:j].count("\n")
            out.append("\n" * newlines if newlines else " ")
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _vector_figure_policy_violations(rel: str, text: str, inv_entry: dict) -> list[str]:
    """Enforce strict mode-aware offline, no-show/set/include, no-aliasing, declared-literal-CSV-only policy."""
    violations: list[str] = []
    stripped = _strip_typst_comments_nested(text)
    if "@preview/" in stripped or "@local/" in stripped:
        violations.append(f"{rel}: external Typst package import is forbidden in offline vector figure")
    if re.search(r"(?<![A-Za-z0-9_-])std\.", stripped):
        violations.append(f"{rel}: `std.` module access is forbidden in vector figure component")

    declared_csvs = {
        d["path"]
        for d in inv_entry.get("data_sources", [])
        if isinstance(d, dict) and isinstance(d.get("path"), str) and d["path"].endswith(".csv")
    }

    events = scan_typst_events(stripped)
    import_count = 0
    valid_plots_import = False
    canvas_calls = 0

    for mode, kind, name, named, pos, line in events:
        where = f"{rel}:{line}"
        if kind == "forbidden_expr":
            violations.append(
                f"{where}: parenthesized/dynamic callee expression is forbidden in vector figure component"
            )
            continue
        if kind == "set":
            violations.append(f"{where}: forbidden `set` rule (`set {name}`) in vector figure component")
            continue
        if kind == "kw":
            if name == "show":
                violations.append(f"{where}: forbidden `show` rule in vector figure component")
            elif name == "include":
                violations.append(f"{where}: forbidden `include` directive in vector figure component")
            elif name == "import":
                import_count += 1
                stmt = pos[0].strip() if pos else ""
                if re.fullmatch(r'"/typst/lib/aod_plots\.typ"\s*:\s*\*', stmt):
                    valid_plots_import = True
                else:
                    violations.append(
                        f"{where}: vector figure may only contain the single `#import \"/typst/lib/aod_plots.typ\": *` "
                        f"(got `import {stmt[:80]}`)"
                    )
            elif name not in VECTOR_FIGURE_ALLOWED_KEYWORDS:
                violations.append(f"{where}: forbidden keyword `{name}` in vector figure component")
            continue

        # Check all modes including math-mode calls (e.g., `$ image(...) $` and `$ std.eval(...) $` compile in Typst!).
        segs = [seg.rstrip("()") for seg in name.split(".")]
        bad_segs = [seg for seg in segs if seg in VECTOR_FIGURE_FORBIDDEN_IDENTIFIERS]
        if bad_segs:
            violations.append(
                f"{where}: forbidden identifier/call `{name}` ({bad_segs[0]}) in vector figure component"
            )
            continue

        if "csv" in segs:
            if mode != "math" and kind == "call" and name == "csv":
                if any(a.strip().startswith("..") for a in pos) or any(k.startswith("..") for k in named):
                    violations.append(f"{where}: dynamic or non-literal csv(...) argument spread is forbidden")
                    continue
                extra_named = set(named) - {"row-type", "delimiter"}
                if extra_named:
                    violations.append(f"{where}: unexpected csv(...) named arguments {sorted(extra_named)}")
                    continue
                if len(pos) != 1:
                    violations.append(
                        f"{where}: dynamic or non-literal csv(...) call is forbidden in vector figure component (pos={pos!r})"
                    )
                    continue
                m_lit = re.fullmatch(r'"(/[^"\n]+)"', pos[0].strip())
                if m_lit is None:
                    violations.append(
                        f"{where}: dynamic or non-literal csv(...) call is forbidden in vector figure component: {pos[0]!r}"
                    )
                    continue
                raw_p = m_lit.group(1)
                rel_csv = raw_p.lstrip("/")
                if rel_csv not in declared_csvs:
                    violations.append(
                        f"{where}: unauthorized csv({raw_p!r}) outside declared figure_inventory data_sources {sorted(declared_csvs)}"
                    )
            elif mode != "math" and kind == "call" and name.startswith("csv()."):
                # Chained method on an already-validated direct csv(...) call (e.g. .filter(...).sorted(...))
                pass
            else:
                violations.append(
                    f"{where}: aliasing or non-direct reference to `csv` (`{name}`, kind={kind}) is forbidden in vector figure component"
                )
            continue

        if mode != "math" and kind == "call" and name == "aod-canvas":
            canvas_calls += 1

    if import_count != 1 or not valid_plots_import:
        msg = (
            f"{rel}: vector figure may only contain the single `#import \"/typst/lib/aod_plots.typ\": *` "
            f"(found {import_count} import directive(s))"
        )
        if not any("may only contain the single `#import" in v for v in violations):
            violations.append(msg)
    if canvas_calls != 1:
        violations.append(f"{rel}: vector figure must invoke #aod-canvas(...) exactly once (got {canvas_calls})")
    if not (
        re.search(r"#let\s+fig-width-cm\s*=\s*[0-9]+(?:\.[0-9]+)?\b", stripped)
        and re.search(r"#let\s+fig-height-cm\s*=\s*[0-9]+(?:\.[0-9]+)?\b", stripped)
    ):
        violations.append(f"{rel}: vector figure must declare literal fig-width-cm and fig-height-cm")
    return violations


def verify_typst_evaluation_policy(root: Path, manifest: dict) -> dict:
    """Gate A2: pin evaluation-defining files and constrain every Typst content and figure file."""
    targets = {e["typst_target"] for e in manifest["active_source_map"]}
    diagram_components: dict[str, str] = manifest.get("diagram_components", {})
    diagram_files = set(diagram_components)
    vector_figure_components: dict[str, str] = manifest.get("vector_figure_components", {})
    vector_figure_files = set(vector_figure_components)
    inv_map = _load_figure_inventory_map(root)

    # 1. Every active Typst unit, shared diagram component, and native vector figure matches its manifest digest.
    for e in manifest["active_source_map"]:
        p = root / e["typst_target"]
        require(p.is_file(), f"Manifest Typst target missing: {e['typst_target']}")
        require(
            sha256_file(p) == e["typst_sha256"],
            f"Typst unit digest differs from typst/manifest.json: {e['typst_target']}",
        )
    for rel, expected_sha in sorted(diagram_components.items()):
        p = root / rel
        require(p.is_file(), f"Manifest Typst diagram component missing: {rel}")
        require(
            sha256_file(p) == expected_sha,
            f"Typst diagram component digest differs from typst/manifest.json: {rel}",
        )
    for rel, expected_sha in sorted(vector_figure_components.items()):
        p = root / rel
        require(p.is_file(), f"Manifest Typst vector figure component missing: {rel}")
        require(
            sha256_file(p) == expected_sha,
            f"Typst vector figure component digest differs from typst/manifest.json: {rel}",
        )
        require(
            rel in inv_map,
            f"Vector figure component missing from typst/figure_inventory.json: {rel}",
        )
    if vector_figure_files:
        require(
            set(inv_map) == vector_figure_files,
            f"figure_inventory.json mismatch with manifest vector_figure_components: "
            f"extra={sorted(set(inv_map) - vector_figure_files)}, missing={sorted(vector_figure_files - set(inv_map))}",
        )
        inv_sha = manifest.get("figure_inventory_sha256")
        if inv_sha:
            require(
                sha256_file(root / "typst/figure_inventory.json") == inv_sha,
                "typst/figure_inventory.json digest differs from typst/manifest.json",
            )
    # 2. Evaluation-defining template/driver files are pinned by this verifier.
    for rel, digest in sorted(TRUSTED_TEMPLATE_SHA256.items()):
        p = root / rel
        require(p.is_file(), f"Trusted Typst template file missing: {rel}")
        require(
            sha256_file(p) == digest,
            f"Trusted Typst template/driver changed (evaluation semantics are pinned by the verifier): {rel}",
        )
    # 3. The Typst file set is exactly the manifest units + shared diagrams + vector figures + pinned templates.
    on_disk = {str(p.relative_to(root)).replace(os.sep, "/") for p in (root / "typst").rglob("*.typ")}
    declared = targets | set(TRUSTED_TEMPLATE_SHA256) | diagram_files | vector_figure_files
    require(
        on_disk == declared,
        f"Undeclared or missing Typst files: extra={sorted(on_disk - declared)}, missing={sorted(declared - on_disk)}",
    )
    # 4. Mode-aware allowlist over content files and shared diagram components; strict offline/CSV policy on vector figures.
    allowed_includes = targets | diagram_files | vector_figure_files
    violations: list[str] = []
    files_checked = 0
    events_checked = 0
    for rel in sorted((targets - set(TRUSTED_TEMPLATE_SHA256)) | diagram_files):
        v_list, n_ev = _content_policy_violations(rel, (root / rel).read_text(encoding="utf-8"), allowed_includes)
        violations += v_list
        files_checked += 1
        events_checked += n_ev
    for rel in sorted(vector_figure_files):
        violations += _vector_figure_policy_violations(rel, (root / rel).read_text(encoding="utf-8"), inv_map[rel])
        files_checked += 1
    require(
        not violations,
        "Typst evaluation policy violation(s) in content files:\n  " + "\n  ".join(violations[:25]),
    )
    return {
        "trusted_template_files_pinned": len(TRUSTED_TEMPLATE_SHA256),
        "diagram_components_pinned": len(diagram_files),
        "vector_figure_components_pinned": len(vector_figure_files),
        "manifest_typst_digests_enforced": len(targets),
        "content_files_policy_checked": files_checked,
        "content_events_checked": events_checked,
        "content_policy_violations": 0,
    }


# =============================================================================
# Gate B: Ordered Source-Bound Prose, Punctuation, Code, & All-Math AST Parity
# =============================================================================

def verify_source_and_content_parity(
    root: Path,
    manifest: dict,
    baseline_root: Path | None = None,
    check_generated_latex: bool = True,
    typst_bin: str | None = None,
) -> dict:
    b_root, tmp_base = _resolve_baseline_root(root, baseline_root)
    try:
        return _verify_source_and_content_parity_impl(
            root=root,
            manifest=manifest,
            b_root=b_root,
            check_generated_latex=check_generated_latex,
            typst_bin=typst_bin,
        )
    finally:
        if tmp_base is not None:
            tmp_base.cleanup()


def _verify_source_and_content_parity_impl(
    root: Path,
    manifest: dict,
    b_root: Path,
    check_generated_latex: bool,
    typst_bin: str | None,
) -> dict:
    audit_mod = load_module(root, "aod_audit_scientific_sources", "scripts/audit_scientific_sources.py")
    active_tex_main, main_parts = audit_mod.include_graph(b_root, "main", representation="tex")
    active_tex_manual, manual_parts = audit_mod.include_graph(b_root, "manual", representation="tex")
    active_tex_all = set(active_tex_main) | set(active_tex_manual)
    require(len(active_tex_main) == 21, f"Expected 21 active Main TeX files, got {len(active_tex_main)}")
    require(len(active_tex_manual) == 27, f"Expected 27 active Manual TeX files, got {len(active_tex_manual)}")

    src_map = {entry["tex_source"]: entry for entry in manifest["active_source_map"]}
    require(set(src_map) == active_tex_all,
            f"Manifest active_source_map mismatch: missing={sorted(active_tex_all - set(src_map))}, extra={sorted(set(src_map) - active_tex_all)}")

    typ_main_files = resolve_typst_includes(root, "typst/main.typ")
    typ_manual_files = resolve_typst_includes(root, "typst/manual/main.typ")
    for tex_rel in active_tex_main:
        t_rel = src_map[tex_rel]["typst_target"]
        require(t_rel in typ_main_files, f"Main Typst source unit not included by typst/main.typ: {t_rel}")
    for tex_rel in active_tex_manual:
        t_rel = src_map[tex_rel]["typst_target"]
        require(t_rel in typ_manual_files, f"Manual Typst source unit not included by typst/manual/main.typ: {t_rel}")

    # 1. Check all 7 immutable table counterparts cell-by-cell
    table_stats: dict[str, dict[str, int]] = {}
    tex_table_rows_cache: dict[str, list[list[str]]] = {}
    for tbl_tex in IMMUTABLE_MANUAL_TABLES:
        require(tbl_tex in src_map, f"Immutable table missing from manifest: {tbl_tex}")
        tbl_typ = src_map[tbl_tex]["typst_target"]
        require(tbl_typ in typ_manual_files, f"Immutable table counterpart not included by Manual: {tbl_typ}")
        tex_rows = extract_tex_table_rows(b_root / tbl_tex)
        typ_rows = extract_typst_table_rows(root / tbl_typ)
        require(
            tex_rows == typ_rows,
            f"Table cell parity mismatch for {tbl_tex} vs {tbl_typ}:\n  TeX={tex_rows[:3]}\n  Typ={typ_rows[:3]}",
        )
        tex_table_rows_cache[tbl_tex] = tex_rows
        table_stats[tbl_tex] = {"rows": len(tex_rows), "cols": len(tex_rows[0]) if tex_rows else 0}

    # 2. Check all 218 labeled equations with recursive-descent Math AST (preserving grouping!)
    tex_main_eqs = extract_tex_equations(main_parts)
    tex_manual_eqs = extract_tex_equations(manual_parts)
    typ_main_eqs = extract_typst_equations([root / f for f in typ_main_files])
    typ_manual_eqs = extract_typst_equations([root / f for f in typ_manual_files])

    eq_counts: dict[str, int] = {}
    base_asts_by_surface: dict[str, dict[str, tuple[tuple, str | None]]] = {"main": {}, "manual": {}}
    for surface, t_eqs, y_eqs in (
        ("main", tex_main_eqs, typ_main_eqs),
        ("manual", tex_manual_eqs, typ_manual_eqs),
    ):
        require(
            set(t_eqs) == set(y_eqs),
            f"{surface} labeled equation set mismatch: missing={sorted(set(t_eqs) - set(y_eqs))}, extra={sorted(set(y_eqs) - set(t_eqs))}",
        )
        for lbl in sorted(t_eqs):
            t_body, t_tag = t_eqs[lbl]
            y_body, y_tag = y_eqs[lbl]
            require(t_tag == y_tag, f"Equation tag mismatch for {lbl}: TeX={t_tag!r} vs Typ={y_tag!r}")
            t_ast, t_unsup = parse_tex_math_ast(t_body)
            y_ast, y_unsup = parse_typst_math_ast(y_body)
            require(not t_unsup and not y_unsup, f"Unsupported math construct in {lbl}: tex={t_unsup}, typ={y_unsup}")
            require(
                t_ast == y_ast,
                f"Equation structure mismatch for {lbl}:\n  TeX AST={t_ast}\n  Typ AST={y_ast}",
            )
            base_asts_by_surface[surface][lbl] = (t_ast, t_tag)
        eq_counts[surface] = len(t_eqs)

    # 3. Check ALL 44 active content files (ordered words >= 1 char, case-exact, punctuation,
    #    verbatim commands/paths, references, citations, AND all ~2,897 inline+display Math ASTs!)
    ordered_files_checked = 0
    total_ordered_tokens = 0
    total_math_asts = 0
    total_code_tokens = 0
    total_image_bindings = 0
    total_flowcharts = 0
    qualifier_totals: dict[str, int] = {q: 0 for q in SCIENTIFIC_QUALIFIERS}
    prose_clauses_by_surface: dict[str, list[tuple[str, str]]] = {"main": [], "manual": []}
    cli_commands_by_surface: dict[str, list[str]] = {"main": [], "manual": []}

    inv_map_all = _load_figure_inventory_map(root)
    authored_pdf_rels = {
        item["target_exported_pdf"].removeprefix("latex/"): item
        for item in inv_map_all.values()
        if item.get("conversion_status") == "AUTHORED_NATIVE_VECTOR"
    }

    for tex_rel, entry in sorted(src_map.items()):
        if tex_rel in ("main.tex", "preamble.tex", "manual/main.tex", "manual/preamble.tex"):
            continue
        typ_rel = entry["typst_target"]
        tex_text = (b_root / tex_rel).read_text(encoding="utf-8")
        typ_text = _inline_typst_diagram_includes(
            root, typ_rel, (root / typ_rel).read_text(encoding="utf-8")
        )

        t_toks, t_unsup = extract_tex_ordered(tex_text, tex_rel)
        y_toks, y_unsup = extract_typst_ordered(typ_text, typ_rel, root=root)
        require(not t_unsup, f"Unsupported TeX math constructs in {tex_rel}: {sorted(set(t_unsup))}")
        require(not y_unsup, f"Unsupported Typst math constructs in {typ_rel}: {sorted(set(y_unsup))}")

        if typ_rel in POST_BASELINE_MANUAL_EXTENSION_UNITS:
            yi = 0
            yn = len(y_toks)
            missing_idx = None
            for ti, ttk in enumerate(t_toks):
                while yi < yn and y_toks[yi] != ttk:
                    yi += 1
                if yi == yn:
                    missing_idx = ti
                    break
                yi += 1
            if missing_idx is not None:
                ctx_t = t_toks[max(0, missing_idx - 2):min(len(t_toks), missing_idx + 3)]
                raise ValueError(
                    f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel} "
                    f"(baseline token missing or reordered at tex[{missing_idx}]={t_toks[missing_idx]!r}):\n"
                    f"  TeX={ctx_t}"
                )
        elif typ_rel in POST_BASELINE_COMPACTED_MAIN_UNITS:
            base_imgs = [tk for tk in t_toks if tk[0] == "IMG"]
            cand_imgs = [tk for tk in y_toks if tk[0] == "IMG" and tk[1] not in authored_pdf_rels]
            require(
                base_imgs == cand_imgs,
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"figure sequence changed base={base_imgs} vs typ={cand_imgs}",
            )
            base_math_set = (
                {tk for tk in t_toks if tk[0] == "MATH"}
                | POST_BASELINE_COMPACTED_MAIN_INLINE_MATH.get(typ_rel, frozenset())
            )
            for mtk in y_toks:
                if mtk[0] == "MATH" and mtk not in base_math_set:
                    raise ValueError(
                        f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                        f"unverified math AST in compacted Main unit: {mtk!r}"
                    )
        elif typ_rel in POST_BASELINE_COMPACTED_MANUAL_UNITS:
            base_imgs = [tk for tk in t_toks if tk[0] == "IMG"]
            cand_imgs = [tk for tk in y_toks if tk[0] == "IMG" and tk[1] not in authored_pdf_rels]
            require(
                base_imgs == cand_imgs,
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"figure sequence changed base={base_imgs} vs typ={cand_imgs}",
            )
            base_fcs = [tk for tk in t_toks if tk[0] == "FLOWCHART"]
            cand_fcs = [tk for tk in y_toks if tk[0] == "FLOWCHART"]
            require(
                base_fcs == cand_fcs,
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"FLOWCHART AST changed ('FLOWCHART') base={base_fcs} vs typ={cand_fcs}",
            )
            base_math_set = {tk for tk in t_toks if tk[0] == "MATH"}
            pinned_extra_math = POST_BASELINE_COMPACTED_MANUAL_INLINE_MATH.get(typ_rel, frozenset())
            actual_extra_math: set[str] = set()
            y_math_seq: list[str] = []
            for mtk in y_toks:
                if mtk[0] == "MATH":
                    mdig = _math_ast_sha256(mtk)
                    y_math_seq.append(mdig)
                    if mtk not in base_math_set:
                        if mdig not in pinned_extra_math:
                            raise ValueError(
                                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                                f"unverified math AST in compacted Manual unit: {mtk!r}"
                            )
                        actual_extra_math.add(mdig)
            require(
                actual_extra_math == pinned_extra_math,
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"pinned compacted Manual inline math AST missing "
                f"({len(pinned_extra_math - actual_extra_math)} missing)",
            )
            actual_math_seq_sha = hashlib.sha256("\n".join(y_math_seq).encode("utf-8")).hexdigest()
            require(
                actual_math_seq_sha == POST_BASELINE_COMPACTED_MANUAL_MATH_SEQ_SHA256[typ_rel],
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"math AST sequence digest changed in compacted Manual unit",
            )
            base_cli = [tk[1] for tk in t_toks if tk[0] == "CODE" and "--" in tk[1]]
            cand_cli = tuple(tk[1] for tk in y_toks if tk[0] == "CODE" and "--" in tk[1])
            for cli_tok in base_cli:
                require(
                    any(cli_tok in cand for cand in cand_cli),
                    f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                    f"verbatim CLI flag/command token altered or missing: {cli_tok!r}",
                )
            require(
                cand_cli == POST_BASELINE_COMPACTED_MANUAL_CLI_TOKENS[typ_rel],
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"CLI code token sequence changed expected={POST_BASELINE_COMPACTED_MANUAL_CLI_TOKENS[typ_rel]!r} "
                f"vs actual={cand_cli!r}",
            )
            cand_qual_counts = {q: 0 for q in SCIENTIFIC_QUALIFIERS}
            for tk in y_toks:
                if tk[0] == "W":
                    lw = tk[1].lower()
                    if lw in cand_qual_counts:
                        cand_qual_counts[lw] += 1
            expected_qual_counts = POST_BASELINE_COMPACTED_MANUAL_QUALIFIER_COUNTS[typ_rel]
            require(
                cand_qual_counts == expected_qual_counts,
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel}: "
                f"scientific qualifier count mismatch expected={expected_qual_counts} vs actual={cand_qual_counts}",
            )
        elif t_toks != y_toks:
            sm = difflib.SequenceMatcher(None, t_toks, y_toks)
            first_diff = next((op for op in sm.get_opcodes() if op[0] != "equal"), None)
            tag, i1, i2, j1, j2 = first_diff
            ctx_t = t_toks[max(0, i1 - 3):min(len(t_toks), i2 + 3)]
            ctx_y = y_toks[max(0, j1 - 3):min(len(y_toks), j2 + 3)]
            raise ValueError(
                f"Ordered content/math parity mismatch in {tex_rel} vs {typ_rel} "
                f"({tag} at tex[{i1}:{i2}] vs typ[{j1}:{j2}]):\n"
                f"  TeX={ctx_t}\n  Typ={ctx_y}"
            )

        ordered_files_checked += 1
        total_ordered_tokens += len(y_toks)
        total_math_asts += sum(1 for tk in y_toks if tk[0] == "MATH")
        total_code_tokens += sum(1 for tk in y_toks if tk[0] == "CODE")
        total_flowcharts += sum(1 for tk in y_toks if tk[0] == "FLOWCHART")
        for tk in y_toks:
            if tk[0] == "IMG":
                if tk[1] in authored_pdf_rels:
                    comp_rel = authored_pdf_rels[tk[1]]["target_typst_component"]
                    require(
                        (root / comp_rel).is_file(),
                        f"Authored native vector figure component missing for {tk[1]!r} in {typ_rel}",
                    )
                else:
                    require(
                        tk[1] in manifest["baseline_protected_sha256"] and (root / tk[1]).is_file(),
                        f"Figure image binding {tk[1]!r} in {typ_rel} is not a protected baseline image",
                    )
                total_image_bindings += 1

        surf = entry["surface"]
        for tk in y_toks:
            if tk[0] == "W":
                lw = tk[1].lower()
                if lw in qualifier_totals:
                    qualifier_totals[lw] += 1
            elif tk[0] == "CODE" and "--" in tk[1]:
                cli_commands_by_surface[surf].append(tk[1])

        if tex_rel not in IMMUTABLE_MANUAL_TABLES:
            if typ_rel in (
                POST_BASELINE_MANUAL_EXTENSION_UNITS
                | POST_BASELINE_COMPACTED_MANUAL_UNITS
                | POST_BASELINE_COMPACTED_MAIN_UNITS
            ):
                gen_p = root / "latex" / tex_rel
                if gen_p.is_file():
                    b_toks, _ = extract_tex_ordered(gen_p.read_text(encoding="utf-8"), tex_rel, emit_boundaries=True)
                else:
                    b_toks = y_toks
            else:
                b_toks, _ = extract_tex_ordered(tex_text, tex_rel, emit_boundaries=True)
            cur_clause: list[str] = []
            for tk in b_toks:
                if tk[0] in ("W", "P"):
                    cur_clause.append(tk[1])
                else:
                    if sum(1 for x in cur_clause if x not in ";:.,?!") >= 3:
                        prose_clauses_by_surface[surf].append((tex_rel, " ".join(cur_clause)))
                    cur_clause = []
            if sum(1 for x in cur_clause if x not in ";:.,?!") >= 3:
                prose_clauses_by_surface[surf].append((tex_rel, " ".join(cur_clause)))

    # 4. Verify zero unescaped semicolons after content calls across all typst files.
    content_call_semi = re.compile(
        r"#(?:mainequation|mainsection|mainappendix|maintable|eqref|eqnref|secref|appref|figref|tabref|bare-ref|aod-cite|raw|link|emph|strong|footnote)\([^()\n]*\);"
    )
    for typ_rel in sorted(set(typ_main_files) | set(typ_manual_files)):
        txt = strip_typst_comments((root / typ_rel).read_text(encoding="utf-8"))
        for line_no, line in enumerate(txt.splitlines(), 1):
            if re.match(r"^\s*#(set|let|show|import|include|counter)\b", line):
                continue
            m_semi = content_call_semi.search(line)
            require(
                m_semi is None,
                f"Unescaped semicolon consumed by Typst after content call in {typ_rel}:{line_no}: {m_semi.group(0) if m_semi else ''}",
            )

    # Check title/epitaph ordered tokens of manual/main.tex vs typst/manual/main.typ
    m_driver_tex, m_du_t = extract_tex_ordered((b_root / "manual/main.tex").read_text(encoding="utf-8"), "manual/main.tex")
    m_driver_typ, m_du_y = extract_typst_ordered((root / "typst/manual/main.typ").read_text(encoding="utf-8"), "typst/manual/main.typ", root=root)
    require(not m_du_t and not m_du_y, f"Unsupported math in Manual driver: tex={m_du_t}, typ={m_du_y}")
    mdt_clean = [x for x in m_driver_tex if x != ("W", "Contents")]
    mdy_clean = [x for x in m_driver_typ if x != ("W", "Contents")]
    require(
        mdt_clean == mdy_clean,
        f"Manual driver title/epitaph content mismatch:\n  TeX={mdt_clean}\n  Typ={mdy_clean}",
    )

    require(total_flowcharts == 4, f"Expected 4 verified TikZ/Typst flowcharts, got {total_flowcharts}")

    # 5. Verify generated latex/ compatibility tree (derived strictly from typst/ via typ2tex.py)
    gen_latex_report: dict[str, object] = {"performed": False}
    if check_generated_latex and (root / "latex/GENERATION_MANIFEST.json").is_file():
        latex_root = root / "latex"
        gen_main_files, gen_main_parts = audit_mod.include_graph(latex_root, "main", representation="tex")
        gen_manual_files, gen_manual_parts = audit_mod.include_graph(latex_root, "manual", representation="tex")
        require(len(gen_main_files) == 21, f"Generated latex/ expected 21 active Main files, got {len(gen_main_files)}")
        require(len(gen_manual_files) == 27, f"Generated latex/ expected 27 active Manual files, got {len(gen_manual_files)}")

        base_main_labels = set(audit_mod.label_map(b_root, "main", representation="tex"))
        base_manual_labels = set(audit_mod.label_map(b_root, "manual", representation="tex"))
        gen_main_labels = set(audit_mod.label_map(latex_root, "main", representation="tex"))
        gen_manual_labels = set(audit_mod.label_map(latex_root, "manual", representation="tex"))
        expected_gen_manual_labels = base_manual_labels | POST_BASELINE_MANUAL_LABELS
        require(gen_main_labels == base_main_labels,
                f"Generated latex/ Main label set mismatch: missing={sorted(base_main_labels - gen_main_labels)}, extra={sorted(gen_main_labels - base_main_labels)}")
        require(gen_manual_labels == expected_gen_manual_labels,
                f"Generated latex/ Manual label set mismatch: missing={sorted(expected_gen_manual_labels - gen_manual_labels)}, extra={sorted(gen_manual_labels - expected_gen_manual_labels)}")

        for tbl_tex, base_rows in tex_table_rows_cache.items():
            gen_rows = extract_tex_table_rows(latex_root / tbl_tex)
            require(
                gen_rows == base_rows,
                f"Generated latex/ table cell parity mismatch for latex/{tbl_tex}",
            )

        gen_eq_counts: dict[str, int] = {}
        for surface, gen_parts in (("main", gen_main_parts), ("manual", gen_manual_parts)):
            g_eqs = extract_tex_equations(gen_parts)
            expected_map = base_asts_by_surface[surface]
            require(set(g_eqs) == set(expected_map),
                    f"Generated latex/ {surface} labeled equation set mismatch")
            for lbl, (base_ast, base_tag) in sorted(expected_map.items()):
                g_body, g_tag = g_eqs[lbl]
                require(g_tag == base_tag, f"Generated latex/ equation tag mismatch for {lbl}")
                g_ast, g_unsup = parse_tex_math_ast(g_body)
                require(not g_unsup, f"Unsupported math construct in generated latex/ {lbl}: {g_unsup}")
                require(
                    g_ast == base_ast,
                    f"Generated latex/ equation AST mismatch for {lbl}:\n  Base={base_ast}\n  Gen ={g_ast}",
                )
            gen_eq_counts[surface] = len(g_eqs)

        # Direct 1:1 ordered token + Math AST parity between canonical typst/ and generated latex/ on post-baseline units
        for tex_rel, entry in sorted(src_map.items()):
            typ_rel = entry["typst_target"]
            if typ_rel not in (
                POST_BASELINE_MANUAL_EXTENSION_UNITS
                | POST_BASELINE_COMPACTED_MANUAL_UNITS
                | POST_BASELINE_COMPACTED_MAIN_UNITS
            ):
                continue
            b_tex_toks, _ = extract_tex_ordered((b_root / tex_rel).read_text(encoding="utf-8"), tex_rel)
            b_tex_math_set = {tk for tk in b_tex_toks if tk[0] == "MATH"}
            g_tex_text = (latex_root / tex_rel).read_text(encoding="utf-8")
            y_gen_text = _inline_typst_diagram_includes(
                root, typ_rel, (root / typ_rel).read_text(encoding="utf-8"), for_generated_latex=True
            )
            g_toks, g_unsup = extract_tex_ordered(g_tex_text, tex_rel)
            yg_toks, yg_unsup = extract_typst_ordered(y_gen_text, typ_rel, root=root)
            require(not g_unsup, f"Unsupported generated TeX math constructs in latex/{tex_rel}: {sorted(set(g_unsup))}")
            require(not yg_unsup, f"Unsupported Typst math constructs in {typ_rel}: {sorted(set(yg_unsup))}")
            if g_toks != yg_toks:
                sm = difflib.SequenceMatcher(None, g_toks, yg_toks)
                for tag, i1, i2, j1, j2 in sm.get_opcodes():
                    if tag == "equal":
                        continue
                    if tag == "replace" and (i2 - i1) == 1 and (j2 - j1) == 1 and yg_toks[j1] in b_tex_math_set:
                        continue
                    ctx_g = g_toks[max(0, i1 - 3):min(len(g_toks), i2 + 3)]
                    ctx_y = yg_toks[max(0, j1 - 3):min(len(yg_toks), j2 + 3)]
                    raise ValueError(
                        f"Generated LaTeX vs Typst ordered content/math parity mismatch in latex/{tex_rel} vs {typ_rel} "
                        f"({tag} at gen[{i1}:{i2}] vs typ[{j1}:{j2}]):\n"
                        f"  GenTeX={ctx_g}\n  Typst ={ctx_y}"
                    )

        total_exported_figures = 0
        exported_by_comp: dict[str, dict] = {}
        for surf_name, fig_rel_dir, expected_count in (
            ("main", "figures/generated", 13),
            ("manual", "manual/figures/generated", 53),
        ):
            fig_dir = latex_root / fig_rel_dir
            fig_manifest_p = fig_dir / "FIGURE_MANIFEST.json"
            require(fig_manifest_p.is_file(), f"Missing latex/{fig_rel_dir}/FIGURE_MANIFEST.json")
            fig_manifest = json.loads(fig_manifest_p.read_text(encoding="utf-8"))
            # R4: committed figure manifest must remain deterministic (no extractor/compiler runtime drift)
            require(
                "typst_version" not in fig_manifest and "removed_outputs" not in fig_manifest,
                f"Committed {fig_rel_dir}/FIGURE_MANIFEST.json must not contain runtime typst_version or removed_outputs",
            )
            require(
                fig_manifest.get("background") == "white" and isinstance(fig_manifest.get("font_families"), dict),
                f"Committed {fig_rel_dir}/FIGURE_MANIFEST.json must declare deterministic background and font_families",
            )
            diagrams = fig_manifest.get("figures", [])
            require(
                len(diagrams) == expected_count,
                f"Expected {expected_count} exported {surf_name} figures in {fig_rel_dir}/FIGURE_MANIFEST.json, got {len(diagrams)}",
            )
            for d in diagrams:
                require(
                    "extracted_text_chars" not in d,
                    f"Committed FIGURE_MANIFEST.json entry {d.get('slug')} must not pin extractor-dependent extracted_text_chars",
                )
                require(
                    d.get("has_extractable_text") is True
                    and d.get("page_count") == 1
                    and d.get("raster_image_xobjects") == 0
                    and d.get("inline_raster_images") == 0
                    and d.get("total_raster_images") == 0,
                    f"Exported figure manifest invariant failed for {d.get('slug')}",
                )
                asset = fig_dir / d["output_filename"]
                require(
                    asset.is_file() and sha256_file(asset) == d["output_sha256"],
                    f"Exported figure digest mismatch: {asset.relative_to(root)}",
                )
                exported_by_comp[d["diagram_component"]] = d
                total_exported_figures += 1

        # Verify typst/figure_inventory.json binds all 62 vector figures (34 converted historical rasters + 28 authored native vectors).
        inv_map = _load_figure_inventory_map(root)
        require(len(inv_map) == 62, f"Expected 62 audited figures in typst/figure_inventory.json, got {len(inv_map)}")
        converted_cnt = authored_cnt = 0
        for comp_rel, item in sorted(inv_map.items()):
            cstatus = item.get("conversion_status")
            require(
                cstatus in ("CONVERTED_VECTOR", "AUTHORED_NATIVE_VECTOR"),
                f"Unexpected conversion_status for {comp_rel}: {cstatus!r}",
            )
            if cstatus == "CONVERTED_VECTOR":
                converted_cnt += 1
                raster_p = root / item["raster_path"]
                require(
                    raster_p.is_file() and sha256_file(raster_p) == item["raster_sha256"],
                    f"Retained historical raster altered or missing: {item['raster_path']}",
                )
            else:
                authored_cnt += 1
                require(
                    item.get("raster_path") is None and item.get("raster_sha256") is None,
                    f"Authored native vector figure must not claim a historical raster_path: {comp_rel}",
                )
            comp_p = root / comp_rel
            require(
                comp_p.is_file() and sha256_file(comp_p) == item["typst_component_sha256"],
                f"Figure inventory component hash mismatch: {comp_rel}",
            )
            require(comp_rel in exported_by_comp, f"Inventory component missing from exported manifests: {comp_rel}")
            require(
                exported_by_comp[comp_rel]["output_sha256"] == item["exported_pdf_sha256"],
                f"Figure inventory exported PDF hash mismatch: {comp_rel}",
            )
        require(
            converted_cnt == 34 and authored_cnt == 28,
            f"Unexpected converted/authored figure split: converted={converted_cnt}, authored={authored_cnt}",
        )

        # R2: bounded source checks for the four demonstrated spacing/unit boundaries
        for rel_tex, required_sub, forbidden_sub in REQUIRED_GENERATED_TEX_BOUNDARIES:
            tex_body = (latex_root / rel_tex).read_text(encoding="utf-8")
            require(
                required_sub in tex_body and forbidden_sub not in tex_body,
                f"Generated LaTeX boundary regression in latex/{rel_tex}: "
                f"expected {required_sub!r}, forbidden {forbidden_sub!r}",
            )

        # R3: bounded source checks for the six restored mathematical bookmark headings
        for rel_tex, required_sub, forbidden_sub in REQUIRED_GENERATED_TEX_BOOKMARKS:
            tex_body = (latex_root / rel_tex).read_text(encoding="utf-8")
            require(
                required_sub in tex_body and forbidden_sub not in tex_body,
                f"Generated LaTeX bookmark regression in latex/{rel_tex}: "
                f"expected {required_sub!r}, forbidden {forbidden_sub!r}",
            )

        typ2tex_check_passed = False
        if (root / "scripts/typ2tex.py").is_file():
            builder = load_module(root, "aod_build_typst", "scripts/build_typst.py")
            tbin = typst_bin
            if tbin is None:
                try:
                    tbin = builder.find_typst(None)
                except FileNotFoundError:
                    tbin = None
            if tbin is not None:
                t2t = load_module(root, "aod_typ2tex_parity_check", "scripts/typ2tex.py")
                t2t.generate_latex_tree(root, latex_root, check_only=True, typst_bin=tbin)
                typ2tex_check_passed = True

        gen_latex_report = {
            "performed": True,
            "active_main_tex_files": len(gen_main_files),
            "active_manual_tex_files": len(gen_manual_files),
            "main_labels_verified": len(gen_main_labels),
            "manual_labels_verified": len(gen_manual_labels),
            "labeled_equations_verified_structurally": gen_eq_counts,
            "immutable_tables_verified_cell_by_cell": len(tex_table_rows_cache),
            "exported_diagrams_verified": total_exported_figures,
            "spacing_unit_boundaries_verified": len(REQUIRED_GENERATED_TEX_BOUNDARIES),
            "math_bookmark_headings_verified": len(REQUIRED_GENERATED_TEX_BOOKMARKS),
            "typ2tex_check_passed": typ2tex_check_passed,
        }

    return {
        "active_main_tex_files": len(active_tex_main),
        "active_manual_tex_files": len(active_tex_manual),
        "active_files_mapped": len(src_map),
        "ordered_content_files_verified": ordered_files_checked,
        "ordered_tokens_verified": total_ordered_tokens,
        "all_math_asts_verified": total_math_asts,
        "literal_code_tokens_verified": total_code_tokens,
        "labeled_equations_verified_structurally": eq_counts,
        "immutable_tables_verified_cell_by_cell": table_stats,
        "flowcharts_verified": total_flowcharts,
        "unsupported_math_constructs": 0,
        "figure_image_bindings_verified": total_image_bindings,
        "qualifier_token_totals": qualifier_totals,
        "generated_latex_parity": gen_latex_report,
        "_prose_clauses": prose_clauses_by_surface,
        "_cli_commands": cli_commands_by_surface,
    }


def extract_tex_equation_numbers(parts: list[tuple[str, str]]) -> tuple[dict[str, str], int]:
    """Compute exact sequential LaTeX equation numbers / explicit \\tag labels and numbered count."""
    env_pat = re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}", re.S)
    counter = 0
    mapping: dict[str, str] = {}
    for _, raw in parts:
        cleaned = strip_tex_comments(raw)
        for m in env_pat.finditer(cleaned):
            env, body = m.group(1), m.group(2)
            if env.endswith("*"):
                tag_m = re.search(r"\\tag\{([^}]+)\}", body)
                if tag_m:
                    for lbl in re.findall(r"\\label\{([^}]+)\}", body):
                        mapping[lbl] = tag_m.group(1)
                continue
            if env == "equation":
                tag_m = re.search(r"\\tag\{([^}]+)\}", body)
                if tag_m:
                    num = tag_m.group(1)
                else:
                    counter += 1
                    num = str(counter)
                for lbl in re.findall(r"\\label\{([^}]+)\}", body):
                    mapping[lbl] = num
            else:
                for row in re.split(r"\\\\(?:\[[^\]]*\])?", body):
                    if not row.strip() or re.search(r"\\(?:nonumber|notag)\b", row):
                        continue
                    tag_m = re.search(r"\\tag\{([^}]+)\}", row)
                    if tag_m:
                        num = tag_m.group(1)
                    else:
                        counter += 1
                        num = str(counter)
                    for lbl in re.findall(r"\\label\{([^}]+)\}", row):
                        mapping[lbl] = num
    return mapping, counter


# =============================================================================
# Gate C: Evaluated & Rendered Publication Parity
# =============================================================================

def _pdftotext(pdf_path: Path, raw: bool = False) -> str:
    cmd = ["pdftotext"] + (["-raw"] if raw else []) + [str(pdf_path), "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return proc.stdout


_LATIN_LIGATURES = str.maketrans({
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
    "\ufb04": "ffl", "\ufb05": "st", "\ufb06": "st",
})


def _norm_rendered_text_tokens(raw_pdf_text: str, is_typst: bool, vocab: set[str] | None = None) -> str:
    """Normalize extracted PDF text for ordered clause comparison.

    Preserves ALL words (including 1- and 2-letter words like 'No', 'no', 'a', 'if'),
    exact case, and punctuation. Only removes standalone page numbers/formfeeds and
    unwraps PDF line-break hyphenation without merging real hyphenated compounds.
    """
    lines = []
    for ln in raw_pdf_text.splitlines():
        s = ln.replace("\x0c", "").strip()
        if not s or re.fullmatch(r"\d+", s):
            continue
        lines.append(s)
    t = "\n".join(lines)
    # Latin typographic ligatures (U+FB00..U+FB06) are a font/extractor artefact on either
    # side ('Adm\ufb01b' vs 'Admfib'); decompose them explicitly rather than via NFKC so
    # mathematical alphanumerics are left to the shared typography normalizer.
    t = t.translate(_LATIN_LIGATURES)
    # Typst uses U+00AD soft hyphen exclusively for automatic line-wrap hyphenation;
    # real compound hyphens remain ASCII '-' and split cleanly into words.
    t = t.replace("\u00ad\n", "").replace("\u00ad ", "").replace("\u00ad", "")
    if not is_typst:
        if vocab is not None:
            t = _dehyphenate_with_vocab(t, vocab)
        else:
            t = re.sub(r"([A-Za-z])-\n([a-z])", r"\1\2", t)
    else:
        # \SADARop renders as Fraktur U+1D516 in Typst; pdftotext reads the XeLaTeX glyph as 'S'.
        t = t.replace("\U0001d516", "S")
    t = norm_prose_typography(t)
    t = t.replace("\u2032", "'")
    toks = [m.group(0) for m in re.finditer(r"[A-Za-z0-9]+(?:['][A-Za-z]+)?|[;:.,?!]", t)]
    return " ".join(toks)


_MATH_ALNUM_CLASS = "\U0001d400-\U0001d7ff"


def _typst_math_word_counts(raw_pdf_text: str) -> Counter:
    """Count alphabetic words of the rendered Typst text that contain at least one Unicode
    mathematical alphanumeric (U+1D400..U+1D7FF), normalized as in the rendered token stream.
    Typst emits these codepoints only for math letters, never for prose words."""
    t = re.sub(r"\u00ad(?:\s*\d+\s*\x0c\s*|\s*)", "", raw_pdf_text.translate(_LATIN_LIGATURES))
    out: Counter = Counter()
    for m in re.finditer(rf"[A-Za-z0-9{_MATH_ALNUM_CLASS}]+", t):
        tok = m.group(0)
        if not re.search(rf"[{_MATH_ALNUM_CLASS}]", tok):
            continue
        for w in re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKC", tok)):
            if w.isalpha():
                out[w] += 1
    return out


def _extract_rendered_bib_entries(raw_pdf_text: str) -> dict[int, str]:
    m = re.search(r"\nReferences\s*\n", raw_pdf_text)
    require(m is not None, "References section not found in rendered PDF")
    tail = raw_pdf_text[m.end():]
    lines = []
    for ln in tail.splitlines():
        s = ln.replace("\x0c", "").strip()
        if re.fullmatch(r"\d+", s) or not s:
            continue
        lines.append(s)
    joined = "\n".join(lines)
    parts = re.split(r"(?:^|\n)\[(\d+)\]\s*", joined)
    out: dict[int, str] = {}
    for i in range(1, len(parts), 2):
        out[int(parts[i])] = re.sub(r"\s+", " ", parts[i + 1]).strip()
    return out


def _canon_bib_for_pdf_wrap(s: str) -> str:
    """Compare rendered bibliography entries case-sensitively while tolerating only
    PDF line-wrap soft-hyphens, URL wrap whitespace, NFKC math italics, and √ baseline shift."""
    t = unicodedata.normalize("NFKC", s)
    t = t.replace("\u00ad ", "").replace("\u00ad", "")
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u221a", "")
    t = re.sub(r"[\s-]+", "", t)
    return t


def _norm_pdf_dest_name(raw) -> str:
    """Normalize a PDF named destination object (TextString, ByteString, or NameObject) to str."""
    if raw is None:
        return ""
    if hasattr(raw, "get_object"):
        raw = raw.get_object()
    if isinstance(raw, bytes):
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError:
            s = raw.decode("latin-1")
    else:
        s = str(raw)
    # NameObject stringifies with a leading '/' in pypdf
    if type(raw).__name__ == "NameObject" and s.startswith("/"):
        s = s[1:]
    return s


def _extract_pdf_named_destinations(reader) -> dict[str, int]:
    """Return mapping of normalized named destination -> 1-based page number."""
    dests: dict[str, int] = {}
    raw_map = reader.named_destinations or {}
    n_pages = len(reader.pages)
    for raw_k, dest_obj in raw_map.items():
        key = _norm_pdf_dest_name(raw_k)
        if not key:
            continue
        try:
            pg0 = reader.get_destination_page_number(dest_obj)
        except Exception:
            pg0 = None
        if pg0 is not None and 0 <= pg0 < n_pages:
            dests[key] = pg0 + 1
            if key.startswith("/"):
                dests[key[1:]] = pg0 + 1
    return dests


def _extract_pdf_outlines(pdf_path: Path) -> list[tuple[int, str, int | None]]:
    """Extract full PDF bookmark hierarchy as (depth, normalized_title, target_page_1based)."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    entries: list[tuple[int, str, int | None]] = []

    def _walk(items, depth: int) -> None:
        for item in items:
            if isinstance(item, list):
                _walk(item, depth + 1)
            else:
                title = re.sub(r"\s+", " ", str(getattr(item, "title", "") or "")).strip()
                try:
                    pg0 = reader.get_destination_page_number(item)
                except Exception:
                    pg0 = None
                pg1 = (pg0 + 1) if (pg0 is not None and 0 <= pg0 < n_pages) else None
                entries.append((depth, title, pg1))

    _walk(reader.outline or [], 0)
    return entries


def _inspect_pdf_links(pdf_path: Path, expected_peer_pdf: str | None = None) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    named_dests = _extract_pdf_named_destinations(reader)
    page_id_to_num = {id(p): idx for idx, p in enumerate(reader.pages, 1)}
    page_ind_to_num = {
        getattr(p, "indirect_reference", None): idx
        for idx, p in enumerate(reader.pages, 1)
        if getattr(p, "indirect_reference", None) is not None
    }

    def _check_local_dest(src_page: int, dest_obj) -> None:
        if dest_obj is None:
            broken_local_destinations.append((src_page, "<empty-dest>"))
            return
        d = dest_obj.get_object() if hasattr(dest_obj, "get_object") else dest_obj
        if isinstance(d, list):
            if not d:
                broken_local_destinations.append((src_page, "<empty-dest-array>"))
                return
            first = d[0]
            if isinstance(first, int):
                if not (0 <= first < n_pages):
                    broken_local_destinations.append((src_page, f"page-index:{first}"))
                return
            if first in page_ind_to_num:
                return
            try:
                pg_obj = first.get_object() if hasattr(first, "get_object") else first
                if id(pg_obj) in page_id_to_num:
                    return
                if pg_obj in reader.pages:
                    return
            except Exception:
                pass
            broken_local_destinations.append((src_page, f"unresolved-page-ref:{first!r}"))
            return
        d_name = _norm_pdf_dest_name(d)
        if not d_name or d_name not in named_dests:
            broken_local_destinations.append((src_page, f"missing-local-dest:{d_name!r}"))

    internal_links = 0
    broken_local_destinations: list[tuple[int, str]] = []
    peer_pdf_links: list[tuple[int, str, int]] = []
    gotor_peer_links: list[tuple[int, str, str]] = []
    stale_main_pdf_links: list[tuple[int, str]] = []
    uri_links = 0
    external_uris: set[str] = set()
    for page_idx, page in enumerate(reader.pages, 1):
        annots = page.get("/Annots") or []
        for annot_ref in annots:
            annot = annot_ref.get_object()
            if annot.get("/Subtype") != "/Link":
                continue
            if "/Dest" in annot:
                internal_links += 1
                _check_local_dest(page_idx, annot.get("/Dest"))
                continue
            action = annot.get("/A")
            if not action:
                continue
            act_obj = action.get_object() if hasattr(action, "get_object") else action
            if "/URI" in act_obj:
                uri = str(act_obj["/URI"])
                if uri.startswith(("http://", "https://", "mailto:")):
                    uri_links += 1
                    external_uris.add(uri)
                elif expected_peer_pdf and uri.startswith(f"{expected_peer_pdf}#page="):
                    m = re.fullmatch(re.escape(expected_peer_pdf) + r"#page=(\d+)", uri)
                    require(m is not None, f"Malformed peer link URI on page {page_idx}: {uri}")
                    peer_pdf_links.append((page_idx, uri, int(m.group(1))))
                elif ".pdf#" in uri:
                    stale_main_pdf_links.append((page_idx, uri))
                else:
                    uri_links += 1
                    external_uris.add(uri)
            elif act_obj.get("/S") == "/GoTo":
                internal_links += 1
                _check_local_dest(page_idx, act_obj.get("/D"))
            elif act_obj.get("/S") == "/GoToR":
                f_obj = act_obj.get("/F")
                if hasattr(f_obj, "get_object"):
                    f_obj = f_obj.get_object()
                if isinstance(f_obj, dict):
                    target_file = str(f_obj.get("/UF") or f_obj.get("/F") or "")
                else:
                    target_file = str(f_obj or "")
                dest_raw = act_obj.get("/D")
                dest = _norm_pdf_dest_name(dest_raw)
                if expected_peer_pdf and target_file == expected_peer_pdf:
                    gotor_peer_links.append((page_idx, target_file, dest))
                else:
                    stale_main_pdf_links.append((page_idx, f"GoToR:{target_file}#{dest}"))
    return {
        "pages": n_pages,
        "internal_links": internal_links,
        "named_destinations": named_dests,
        "broken_local_destinations": broken_local_destinations,
        "peer_pdf_links": peer_pdf_links,
        "gotor_peer_links": gotor_peer_links,
        "stale_main_pdf_links": stale_main_pdf_links,
        "uri_links": uri_links,
        "unique_external_uris": sorted(external_uris),
    }


def _verify_gotor_peer_destinations(
    manual_links: dict,
    main_links: dict,
    main_pages_txt: list[str],
    *,
    baseline_manual_links: dict | None = None,
    baseline_main_links: dict | None = None,
    baseline_main_pages_txt: list[str] | None = None,
) -> dict:
    """Verify every sibling /GoToR /D destination exists in main.pdf and lands on its semantic target.

    Explicitly accepts legitimate internal destination renames (e.g. hyperref AMS.63 -> AMS.61)
    provided the destination exists in sibling main.pdf and lands on the same semantic target.
    """
    main_dests: dict[str, int] = main_links["named_destinations"]
    gotor_links: list[tuple[int, str, str]] = manual_links["gotor_peer_links"]
    missing_dests: list[tuple[int, str]] = []
    landing_mismatches: list[tuple[int, str, int, str]] = []
    resolved_pages: dict[str, int] = {}

    def _page_window_text(pages: list[str], pg1: int) -> str:
        raw = pages[pg1 - 1]
        return re.sub(r"\s+", " ", raw.replace("\xa0", " "))

    for src_page, target_file, dest_name in gotor_links:
        if not dest_name or dest_name not in main_dests:
            missing_dests.append((src_page, dest_name))
            continue
        pg1 = main_dests[dest_name]
        if not (1 <= pg1 <= len(main_pages_txt)):
            missing_dests.append((src_page, f"{dest_name}->invalid-page:{pg1}"))
            continue
        resolved_pages[dest_name] = pg1
        pg_txt = _page_window_text(main_pages_txt, pg1)
        # Semantic landing checks by hyperref destination prefix
        m_eq = re.fullmatch(r"equation\.(?:\d+\.)*(\d+)", dest_name)
        m_sec = re.fullmatch(r"(?:section|subsection|subsubsection|paragraph)\.([A-Z]|\d+(?:\.\d+)*)", dest_name)
        m_app = re.fullmatch(r"appendix\.([A-Z](?:\.\d+)*)", dest_name)
        m_tbl = re.fullmatch(r"table\.(?:caption\.)?(?:\d+\.)*(\d+)", dest_name)
        m_fig = re.fullmatch(r"figure\.(?:caption\.)?(?:\d+\.)*(\d+)", dest_name)
        if m_eq:
            needle = f"({m_eq.group(1)})"
            nxt_txt = _page_window_text(main_pages_txt, pg1 + 1) if pg1 < len(main_pages_txt) else ""
            if needle not in pg_txt and needle not in nxt_txt:
                landing_mismatches.append((src_page, dest_name, pg1, f"expected equation tag {needle!r}"))
        elif dest_name.startswith("AMS."):
            nxt_txt = _page_window_text(main_pages_txt, pg1 + 1) if pg1 < len(main_pages_txt) else ""
            if not re.search(r"\([A-Za-z0-9.\-]+\)", pg_txt) and not re.search(r"\([A-Za-z0-9.\-]+\)", nxt_txt):
                landing_mismatches.append((src_page, dest_name, pg1, "expected tagged AMS equation on target page"))
        elif m_sec:
            needle = m_sec.group(1)
            if needle not in pg_txt:
                landing_mismatches.append((src_page, dest_name, pg1, f"expected section number {needle!r}"))
        elif m_app:
            needle = m_app.group(1)
            if needle not in pg_txt:
                landing_mismatches.append((src_page, dest_name, pg1, f"expected appendix identifier {needle!r}"))
        elif m_tbl:
            if "Table" not in pg_txt:
                landing_mismatches.append((src_page, dest_name, pg1, "expected Table on target page"))
        elif m_fig:
            if "Figure" not in pg_txt:
                landing_mismatches.append((src_page, dest_name, pg1, "expected Figure on target page"))

    require(
        not missing_dests,
        f"Generated LaTeX manual.pdf has missing sibling peer /GoToR /D destination(s) in main.pdf: "
        f"{missing_dests[:10]}",
    )
    require(
        not landing_mismatches,
        f"Generated LaTeX manual.pdf sibling peer /GoToR /D landing mismatch(es): {landing_mismatches[:10]}",
    )

    # Compare unique semantic targets against baseline peer links when baseline PDFs are supplied
    renamed_internal_destinations: list[dict] = []
    if baseline_manual_links is not None and baseline_main_links is not None and baseline_main_pages_txt is not None:
        base_dests = baseline_main_links["named_destinations"]
        base_gotor_set = {d for _, _, d in baseline_manual_links["gotor_peer_links"] if d}
        gen_gotor_set = {d for _, _, d in gotor_links if d}
        # Allow legitimate internal AMS.* counter renames when tagged equation landings match
        base_non_ams = {d for d in base_gotor_set if not d.startswith("AMS.")}
        gen_non_ams = {d for d in gen_gotor_set if not d.startswith("AMS.")}
        require(
            gen_non_ams == base_non_ams,
            f"Generated LaTeX sibling peer non-AMS destination set mismatch vs baseline: "
            f"missing={sorted(base_non_ams - gen_non_ams)[:10]}, extra={sorted(gen_non_ams - base_non_ams)[:10]}",
        )
        base_ams = sorted(d for d in base_gotor_set if d.startswith("AMS."))
        gen_ams = sorted(d for d in gen_gotor_set if d.startswith("AMS."))
        require(
            len(base_ams) == len(gen_ams),
            f"Generated LaTeX sibling peer AMS destination count mismatch: base={base_ams}, gen={gen_ams}",
        )
        for b_d, g_d in zip(base_ams, gen_ams):
            b_pg = base_dests.get(b_d)
            g_pg = main_dests.get(g_d)
            require(b_pg is not None and g_pg is not None, f"Unresolved AMS peer destination: base={b_d}, gen={g_d}")
            b_tags = set(re.findall(r"\(RG\d+\)", _page_window_text(baseline_main_pages_txt, b_pg)))
            g_tags = set(re.findall(r"\(RG\d+\)", _page_window_text(main_pages_txt, g_pg)))
            if b_tags:
                require(
                    bool(b_tags & g_tags),
                    f"AMS peer destination semantic target mismatch: baseline {b_d} -> {sorted(b_tags)}, "
                    f"generated {g_d} -> {sorted(g_tags)}",
                )
            if b_d != g_d:
                renamed_internal_destinations.append({
                    "baseline_dest": b_d,
                    "generated_dest": g_d,
                    "shared_semantic_tags": sorted(b_tags & g_tags),
                })

    return {
        "gotor_peer_links_checked": len(gotor_links),
        "unique_peer_destinations_resolved": len(resolved_pages),
        "missing_peer_destinations": 0,
        "landing_mismatches": 0,
        "accepted_internal_destination_renames": renamed_internal_destinations,
    }


def _extract_pdf_bbox_lines(pdf_path: Path) -> list[tuple[int, list[tuple[float, float, float, float, str]]]]:
    """Extract per-line word bounding boxes (xMin, yMin, xMax, yMax, text) via pdftotext -bbox-layout."""
    proc = subprocess.run(
        ["pdftotext", "-bbox-layout", str(pdf_path), "-"],
        capture_output=True, text=True, errors="replace", check=True,
    )
    xml_clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", proc.stdout)
    root = ET.fromstring(xml_clean)
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    lines_out: list[tuple[int, list[tuple[float, float, float, float, str]]]] = []
    for p_idx, page in enumerate(root.findall(".//x:page", ns), 1):
        for line in page.findall(".//x:line", ns):
            words = [
                (
                    float(w.attrib["xMin"]),
                    float(w.attrib["yMin"]),
                    float(w.attrib["xMax"]),
                    float(w.attrib["yMax"]),
                    w.text or "",
                )
                for w in line.findall("x:word", ns)
            ]
            if words:
                lines_out.append((p_idx, words))
    return lines_out


def _verify_rendered_pdf_boundaries(surf: str, gen_pdf: Path, gen_raw: str) -> dict[str, float]:
    """Verify rendered glyph-position spacing/unit boundaries (R2) via text and pdftotext -bbox-layout."""
    flat = re.sub(r"\s+", " ", gen_raw.replace("\xa0", " "))
    bbox_lines = _extract_pdf_bbox_lines(gen_pdf)
    measured_gaps: dict[str, float] = {}

    if surf == "main":
        require("Duonhas" not in flat, "Generated LaTeX main.pdf boundary regression: glued 'Duonhas'")
        duon_dx: float | None = None
        for _, words in bbox_lines:
            txts = [w[4] for w in words]
            if "Duon" in txts and "support" in txts:
                for i in range(len(words) - 1):
                    if words[i][4] == "Duon" and words[i + 1][4] == "has":
                        duon_dx = round(words[i + 1][0] - words[i][2], 2)
                        break
            if duon_dx is not None:
                break
        require(
            duon_dx is not None and duon_dx >= 2.0,
            f"Generated LaTeX main.pdf rendered glyph boundary regression for 'Duon has': dx={duon_dx!r} pt (expected >= 2.0 pt)",
        )
        measured_gaps["Duon_has"] = duon_dx

        require("Reis valid" not in flat, "Generated LaTeX main.pdf boundary regression: glued 'Reis valid'")
        re_dx: float | None = None
        for _, words in bbox_lines:
            txts = [w[4] for w in words]
            if "is" in txts and "valid" in txts:
                for i in range(len(words) - 2):
                    if (
                        i + 3 < len(words)
                        and words[i][4] == "R"
                        and words[i + 1][4] == "e"
                        and words[i + 2][4] == "is"
                        and words[i + 3][4] == "valid"
                    ):
                        re_dx = round(words[i + 2][0] - words[i + 1][2], 2)
                        break
                    if (
                        words[i][4] == "Re"
                        and words[i + 1][4] == "is"
                        and words[i + 2][4] == "valid"
                    ):
                        re_dx = round(words[i + 1][0] - words[i][2], 2)
                        break
            if re_dx is not None:
                break
        require(
            re_dx is not None and re_dx >= 2.0,
            f"Generated LaTeX main.pdf rendered glyph boundary regression for 'R_e is valid': dx={re_dx!r} pt (expected >= 2.0 pt)",
        )
        measured_gaps["Re_is_valid"] = re_dx

        require("tetronis" not in flat, "Generated LaTeX main.pdf boundary regression: glued 'tetronis'")
        tetron_dx: float | None = None
        for _, words in bbox_lines:
            txts = [w[4] for w in words]
            if "enclosure" in txts and any("5.7.4" in t for t in txts):
                for i in range(len(words) - 1):
                    if words[i][4] == "tetron" and words[i + 1][4] == "is":
                        tetron_dx = round(words[i + 1][0] - words[i][2], 2)
                        break
            if tetron_dx is not None:
                break
        require(
            tetron_dx is not None and tetron_dx >= 2.0,
            f"Generated LaTeX main.pdf rendered glyph boundary regression for 'tetron is': dx={tetron_dx!r} pt (expected >= 2.0 pt)",
        )
        measured_gaps["tetron_is"] = tetron_dx
    else:
        require(
            not re.search(r"10[\u2212\-]10J\b", flat),
            "Generated LaTeX manual.pdf boundary regression: glued '10^-10J'",
        )
        joule_dx: float | None = None
        for _, words in bbox_lines:
            txts = [w[4] for w in words]
            if "2.84684357388924" in txts:
                for i in range(len(words) - 1):
                    if words[i][4] in ("\u221210", "-10") and words[i + 1][4] in ("J.", "J"):
                        joule_dx = round(words[i + 1][0] - words[i][2], 2)
                        break
            if joule_dx is not None:
                break
        require(
            joule_dx is not None and joule_dx >= 1.5,
            f"Generated LaTeX manual.pdf rendered glyph boundary regression for '10^-10 J': dx={joule_dx!r} pt (expected >= 1.5 pt)",
        )
        measured_gaps["10_minus10_J"] = joule_dx

    return measured_gaps


def _verify_pdf_outlines_and_boundaries(
    surf: str,
    gen_pdf: Path,
    gen_raw: str,
    baseline_pdf: Path | None = None,
) -> dict:
    """Verify full PDF outline hierarchy/titles (R3) and rendered glyph-position spacing/unit boundaries (R2)."""
    gen_outline = _extract_pdf_outlines(gen_pdf)
    require(len(gen_outline) > 0, f"Generated LaTeX {surf}.pdf has empty PDF outline")
    broken_outline_targets = [
        (idx, title) for idx, (_, title, pg) in enumerate(gen_outline) if pg is None
    ]
    require(
        not broken_outline_targets,
        f"Generated LaTeX {surf}.pdf has outline entries with invalid targets: {broken_outline_targets[:10]}",
    )

    gen_titles = [title for _, title, _ in gen_outline]
    gen_title_set = set(gen_titles)
    for required_title, forbidden_variants in REQUIRED_PDF_BOOKMARK_TITLES[surf]:
        require(
            required_title in gen_title_set,
            f"Generated LaTeX {surf}.pdf missing required mathematical bookmark title: {required_title!r}",
        )
        for forbidden_stripped in forbidden_variants:
            require(
                forbidden_stripped not in gen_title_set,
                f"Generated LaTeX {surf}.pdf contains symbol-stripped bookmark title: {forbidden_stripped!r}",
            )

    baseline_outline_matched = False
    if baseline_pdf is not None:
        base_outline = _extract_pdf_outlines(baseline_pdf)
        base_seq = [(d, t) for d, t, _ in base_outline]
        gen_seq = [(d, t) for d, t, _ in gen_outline]
        base_top = [x for x in base_seq if x[0] == 1]
        gen_top = [x for x in gen_seq if x[0] == 1]
        require(
            gen_top == base_top,
            f"Generated LaTeX {surf}.pdf top-level outline mismatch vs baseline: "
            f"base={base_top} vs gen={gen_top}",
        )
        # Main compacted micro-subsections in 06_field.typ (gen_seq subsequence of base_seq);
        # Manual added post-baseline subsections (base_seq subsequence of gen_seq).
        sub_seq, sup_seq = (gen_seq, base_seq) if surf == "main" else (base_seq, gen_seq)
        it = iter(sup_seq)
        missing_outline = [item for item in sub_seq if not any(cand == item for cand in it)]
        require(
            not missing_outline,
            f"Generated LaTeX {surf}.pdf outline hierarchy/title order mismatch vs baseline "
            f"(base={len(base_seq)}, gen={len(gen_seq)}): missing_or_reordered={missing_outline[:10]}",
        )
        baseline_outline_matched = True

    measured_gaps = _verify_rendered_pdf_boundaries(surf, gen_pdf, gen_raw)

    return {
        "outline_entries": len(gen_outline),
        "broken_outline_targets": 0,
        "required_math_bookmarks_verified": len(REQUIRED_PDF_BOOKMARK_TITLES[surf]),
        "baseline_outline_hierarchy_matched": baseline_outline_matched,
        "rendered_boundaries_verified": True,
        "rendered_boundary_gaps_pt": measured_gaps,
    }


def verify_delivered_peer_links(
    outdir: Path,
    build_report: dict,
    main_reg: dict,
    manual_mainrefs: list[dict],
) -> dict:
    """C2: Verify the actual delivered canonical artifact pair (main.pdf + manual.pdf)
    and confirm every cross-document link resolves to the delivered peer file and actual target page."""
    expected_peer = main_reg.get("main_pdf_filename", "")
    require(expected_peer == "main.pdf",
            f"Main registry peer filename must be 'main.pdf', got {expected_peer!r}")
    peer_path = outdir / expected_peer
    manual_path = outdir / "manual.pdf"
    require(peer_path.is_file(), f"Delivered native peer PDF missing in {outdir}: {expected_peer}")
    require(manual_path.is_file(), f"Delivered native Manual PDF missing in {outdir}: manual.pdf")
    require(
        sha256_file(peer_path) == build_report["main_pdf_sha256"],
        f"Delivered peer PDF {expected_peer} SHA-256 does not match built Main artifact",
    )
    require(
        sha256_file(manual_path) == build_report["manual_pdf_sha256"],
        "Delivered manual.pdf SHA-256 does not match built Manual artifact",
    )

    main_links = _inspect_pdf_links(peer_path, expected_peer_pdf=None)
    manual_links = _inspect_pdf_links(manual_path, expected_peer_pdf=expected_peer)

    require(
        len(manual_links["stale_main_pdf_links"]) == 0,
        f"Manual contains cross-document links targeting wrong/stale companion filename: {manual_links['stale_main_pdf_links'][:5]}",
    )
    require(
        len(manual_links["peer_pdf_links"]) >= len(manual_mainrefs),
        f"Expected at least {len(manual_mainrefs)} links targeting {expected_peer}#page=N, got {len(manual_links['peer_pdf_links'])}",
    )
    for src_pg, uri, tgt_pg in manual_links["peer_pdf_links"]:
        require(
            1 <= tgt_pg <= main_links["pages"],
            f"Out-of-range peer destination on Manual page {src_pg}: {uri} (Main pages={main_links['pages']})",
        )

    main_pages_txt = _pdftotext(peer_path).split("\x0c")
    require(len(main_pages_txt) >= main_links["pages"], "Failed to extract per-page text of main.pdf")
    witness_eq33 = None
    for item in manual_mainrefs:
        v = item["value"]
        require(v.get("peer_pdf") == expected_peer,
                f"Main ref {v['ref_id']} has wrong peer_pdf={v.get('peer_pdf')!r}")
        require(v["pdf_destination"] == f"{expected_peer}#page={v['target_page']}",
                f"Main ref {v['ref_id']} has unexpected pdf_destination={v['pdf_destination']!r}")
        pg = v["target_page"]
        kind = v["resolved_kind"]
        num = v["resolved_number"]
        pg_txt = re.sub(r"\s+", " ", main_pages_txt[pg - 1].replace("\xa0", " "))
        if kind in ("equation", "rg-equation"):
            needle = f"({num})"
        elif kind == "table":
            needle = f"Table {num}:"
        elif kind == "figure":
            needle = f"Figure {num}:"
        else:
            needle = num
        require(
            needle in pg_txt,
            f"Peer-PDF landing mismatch for {v['ref_id']} ({v['resolved_display']}): "
            f"expected {needle!r} on {expected_peer} physical page {pg}",
        )
        if v["ref_id"] == "main:eq:duad-same-current":
            witness_eq33 = {
                "ref_id": v["ref_id"],
                "resolved_display": v["resolved_display"],
                "pdf_destination": v["pdf_destination"],
                "verified_anchor_on_target_page": needle,
            }

    require(witness_eq33 is not None, "Missing concrete witness main:eq:duad-same-current (Main (33))")

    return {
        "delivered_peer_pdf": expected_peer,
        "peer_pdf_sha256_verified": True,
        "stale_peer_pdf_links": 0,
        "stale_main_pdf_links": 0,
        "peer_pdf_links_count": len(manual_links["peer_pdf_links"]),
        "all_target_page_anchors_verified": len(manual_mainrefs),
        "witness_main_eq33": witness_eq33,
        "main_stats": {
            "pages": main_links["pages"],
            "internal_links": main_links["internal_links"],
            "uri_links": main_links["uri_links"],
        },
        "manual_stats": {
            "pages": manual_links["pages"],
            "internal_links": manual_links["internal_links"],
            "peer_pdf_links": len(manual_links["peer_pdf_links"]),
            "uri_links": manual_links["uri_links"],
        },
    }


def _split_sentence_clauses(clause: str) -> list[str]:
    """Split a contiguous prose run on sentence-ending periods so clauses never straddle
    a multi-page table-row break, while preserving all short words and internal punctuation."""
    stripped = re.sub(r"^[.;:,?!]\s+", "", clause).strip()
    parts = [p.strip() for p in re.split(r"(?<=\.)\s+", stripped) if p.strip()]
    out = []
    for p in parts:
        words = [w for w in p.split() if w not in ";:.,?!"]
        if len(words) >= 3:
            out.append(p)
    return out


# --- R02: vocabulary-bound de-hyphenation, insertion detection, glyph parity, paint scan ---

# Rendered math/relation glyphs whose occurrence counts agree exactly between the retained
# XeLaTeX PDF and the native Typst PDF on the clean candidate. '−', '=', '∈', '·', '∂', '∑'
# are linearised differently by the two engines and are covered by the source math AST
# (Gate B) plus the evaluation policy (Gate A2) instead.
RENDERED_GLYPH_PARITY_SET = (
    "+", "<", ">", "\u2264", "\u2265", "\u2194", "\u00d7", "\u221e", "\u2261", "\u2205", "\u2300",
)
INSERTION_NGRAM = 4
# Exact Typst 4-grams that are absent from the baseline only because pdftotext linearises
# table cells / side notes in a different order. Every other novel 4-gram fails the gate.
RENDERED_LAYOUT_NGRAM_ALLOWLIST: dict[str, frozenset] = {
    "main": frozenset({
        "open seat seated duad", "and its exact character", "in this note Fixed",
        "this note Fixed boundary", "note Fixed boundary window", "in this note Duonic",
        "this note Duonic pressure", "note Duonic pressure Clipped",
    }),
    "manual": frozenset({
        "signed residual tally Status", "proxy required momentum fields",
        "required momentum fields angular", "quarantined target required Input",
        "target required Input group", "Source status Gate audit", "status Gate audit controls",
        "Gate audit controls null",
        "CODATA Record Target MeV", "MeV NIST CODATA Record", "NIST CODATA Record Target",
        "external target declared Record", "input gate table Record",
    }),
}
# Out-of-source-vocabulary words (>= 4 letters) may not occur more often in the Typst body than
# in the retained baseline body, except for these exact excesses (math/table-header linearisation
# and the Typst table-of-contents 'References' entry), measured on the clean candidate.
OOV_WORD_MIN_LEN = 4
RENDERED_OOV_EXCESS_ALLOWLIST: dict[str, dict[str, int]] = {
    "main": {"Anchor": 1, "Category": 1, "Entries": 1, "References": 1, "asym": 6, "decl": 1, "prop": 1},
    "manual": {
        "Artifact": 1, "Class": 1, "Jobs": 2, "Mass": 1, "Purpose": 1, "Quantity": 1,
        "References": 1, "Sheet": 1, "Unit": 1, "Value": 1, "bench": 1,
        "bend": 1, "neuro": 4, "peri": 1, "spike": 2,
    },
}
# OpenType Latin Modern Math scriptScriptPercentScaleDown = 50%: allowlisted 7.0pt/7.5pt tables
# legitimately emit nested math script-scripts at 3.5pt/3.75pt, while microscopic attacks stay < 3.5pt.
MIN_RENDERED_TEXT_SIZE = 3.5


def _source_prose_vocab(gate_b_info: dict) -> set[str]:
    vocab: set[str] = set()
    for surf in ("main", "manual"):
        for _, clause in gate_b_info["_prose_clauses"][surf]:
            vocab.update(w for w in clause.split() if w.isalpha())
    return vocab


def _dehyphenate_with_vocab(t: str, vocab: set[str]) -> str:
    """Undo XeLaTeX line-break hyphenation, bound to the source prose vocabulary."""
    def rep(m: re.Match) -> str:
        a, b = m.group(1), m.group(2)
        if (a + b) in vocab or not (a in vocab and b in vocab):
            return a + b
        return a + " " + b
    return re.sub(r"([A-Za-z]+)-\n([a-z]+)", rep, t)


def _rendered_body(raw_pdf_text: str) -> str:
    """Text before the LAST 'References' heading (the first match is the table of contents)."""
    ms = list(re.finditer(r"\nReferences\s*\n", raw_pdf_text))
    return raw_pdf_text[:ms[-1].start()] if ms else raw_pdf_text


def _vocab_runs(tokens: list[str], vocab: set[str]) -> list[list[str]]:
    runs: list[list[str]] = []
    cur: list[str] = []
    for x in tokens:
        if x.isalpha() and len(x) >= 2 and x in vocab:
            cur.append(x)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def _run_ngrams(runs: list[list[str]], n: int = INSERTION_NGRAM) -> list[str]:
    out: list[str] = []
    for r in runs:
        for i in range(len(r) - n + 1):
            out.append(" ".join(r[i:i + n]))
    return out


_PDF_TOK = re.compile(
    rb"\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>|\[|\]|/[^\s/\[\]()<>]+|[-+]?\d*\.?\d+|[A-Za-z'\"*]+"
)
_PDF_NUM = re.compile(rb"[-+]?\d*\.?\d+")


def _extract_extgstate_ca(resources) -> dict[str, float]:
    out: dict[str, float] = {}
    if not resources:
        return out
    res_obj = resources.get_object() if hasattr(resources, "get_object") else resources
    egs = res_obj.get("/ExtGState")
    if not egs:
        return out
    egs_obj = egs.get_object() if hasattr(egs, "get_object") else egs
    for k, v in egs_obj.items():
        vo = v.get_object() if hasattr(v, "get_object") else v
        if isinstance(vo, dict) and "/ca" in vo:
            out[str(k)] = float(vo["/ca"])
    return out


_SHARED_FIGURE_EXPORTER = None


def _shared_figure_exporter():
    """Load the single shared scripts/export_typst_figures.py module so raster inspection cannot diverge."""
    global _SHARED_FIGURE_EXPORTER
    if _SHARED_FIGURE_EXPORTER is None:
        exp_path = Path(__file__).resolve().parent / "export_typst_figures.py"
        _SHARED_FIGURE_EXPORTER = load_module(exp_path.parents[1], "aod_shared_export_typst_figures", "scripts/export_typst_figures.py")
    return _SHARED_FIGURE_EXPORTER


def _inspect_pdf_rasters(pdf_path: Path) -> dict:
    """Shared recursive PDF raster census covering /Image XObjects and inline BI/ID/EI images."""
    return _shared_figure_exporter().inspect_pdf_rasters(pdf_path)


def _require_zero_pdf_rasters(pdf_path: Path, label: str) -> dict:
    """Shared fail-closed pure-vector check rejecting any /Image XObject, inline image, or malformed stream."""
    return _shared_figure_exporter().require_zero_pdf_rasters(pdf_path, label)


def _count_pdf_raster_xobjects(pdf_path: Path) -> int:
    """Return total raster count (Image XObjects + inline images) via the shared PDF raster inspector."""
    return int(_inspect_pdf_rasters(pdf_path)["total_raster_images"])


def _require_zero_pdf_raster_xobjects(pdf_path: Path, label: str) -> int:
    """Backward-compatible wrapper enforcing zero XObject and inline raster images via the shared guard."""
    return int(_require_zero_pdf_rasters(pdf_path, label)["total_raster_images"])


def _pure_vector_surfaces(root: Path, vf_manifest: dict) -> set[str]:
    """Return surfaces where all active figures in typst/figure_inventory.json are CONVERTED_VECTOR."""
    vf_comps = vf_manifest.get("vector_figure_components", {})
    if not vf_comps:
        return set()
    inv_map = _load_figure_inventory_map(root)
    inv_figures = list(inv_map.values())
    require(
        bool(inv_figures),
        "typst/figure_inventory.json contains no figures despite declared vector_figure_components",
    )
    out: set[str] = set()
    for surf in ("main", "manual"):
        surf_comps = [k for k in vf_comps if k.startswith(f"typst/lib/figures/{surf}/")]
        surf_inv = [f for f in inv_figures if f.get("surface") == surf]
        if surf_comps and surf_inv and all(f.get("conversion_status") in ("CONVERTED_VECTOR", "AUTHORED_NATIVE_VECTOR") for f in surf_inv):
            out.add(surf)
    return out


def _verify_figure9_math_attachment(
    typst_bin: str,
    root: Path,
    comp_rel: str = "typst/lib/figures/main/cycle_disturbance_shedding.typ",
) -> dict:
    """Verify compiled Typst math AST of Main Figure 9: P_W^S (partial F, omega) = ... has top=S alone and baseline args."""
    comp_path = root / comp_rel
    require(comp_path.is_file(), f"Missing Main Figure 9 component: {comp_rel}")
    proc = subprocess.run(
        [typst_bin, "query", "--root", str(root), str(comp_path), "math.equation"],
        capture_output=True,
        text=True,
        check=True,
    )
    eqs = json.loads(proc.stdout)

    def _non_space_leaves(node) -> list[str]:
        if isinstance(node, dict):
            fn = node.get("func")
            if fn in ("symbol", "text"):
                return [str(node.get("text", ""))]
            if fn == "space":
                return []
            out_toks: list[str] = []
            for key in ("body", "child", "children"):
                if key in node:
                    out_toks.extend(_non_space_leaves(node[key]))
            return out_toks
        if isinstance(node, list):
            out_toks = []
            for it in node:
                out_toks.extend(_non_space_leaves(it))
            return out_toks
        return []

    matched_p_eqs = 0
    for eq in eqs:
        body = eq.get("body")
        if not isinstance(body, dict) or body.get("func") != "sequence":
            continue
        children = [c for c in body.get("children", []) if not (isinstance(c, dict) and c.get("func") == "space")]
        eq_idx = next(
            (i for i, c in enumerate(children) if isinstance(c, dict) and c.get("func") == "symbol" and c.get("text") == "="),
            None,
        )
        if eq_idx is None or eq_idx == 0:
            continue
        lhs = children[:eq_idx]
        first = lhs[0]
        if not (isinstance(first, dict) and first.get("func") == "attach" and first.get("base") == {"func": "symbol", "text": "P"}):
            continue
        matched_p_eqs += 1
        require(
            first.get("b") == {"func": "symbol", "text": "W"},
            f"Figure 9 formula bottom attachment mismatch: expected W, got {first.get('b')!r}",
        )
        require(
            first.get("t") == {"func": "symbol", "text": "S"},
            f"Figure 9 formula superscript attachment defect: top attachment must be S alone (not arguments), got {first.get('t')!r}",
        )
        require(
            len(lhs) == 2 and isinstance(lhs[1], dict) and lhs[1].get("func") == "lr",
            f"Figure 9 formula missing baseline parenthesized argument group after P_W^S: lhs={lhs!r}",
        )
        arg_tokens = _non_space_leaves(lhs[1])
        require(
            arg_tokens == ["(", "∂", "F", ",", "ω", ")"],
            f"Figure 9 formula baseline arguments mismatch: expected ['(', '∂', 'F', ',', 'ω', ')'], got {arg_tokens!r}",
        )
    require(
        matched_p_eqs == 1,
        f"Expected exactly 1 compiled P_W^S (∂F, ω) = ... equation in {comp_rel}, found {matched_p_eqs}",
    )
    return {
        "component": comp_rel,
        "base": "P",
        "bottom": "W",
        "top": "S",
        "baseline_args": ["(", "∂", "F", ",", "ω", ")"],
        "verified": True,
    }


def _scan_pdf_text_paint(pdf_path: Path) -> dict:
    """Every text-showing operator must paint opaque black fill (ca == 1), no zero-area clip,
    render mode 0, and font size >= 4pt."""
    from pypdf import PdfReader

    black = {("g", (0.0,)), ("sc", (0.0,)), ("scn", (0.0,)), ("rg", (0.0, 0.0, 0.0)), ("k", (0.0, 0.0, 0.0, 1.0))}
    reader = PdfReader(str(pdf_path))
    text_ops = 0
    bad: list[str] = []
    min_size: float | None = None

    def scan_stream(
        raw: bytes,
        resources,
        init_state: tuple = (("g", (0.0,)), 0, None, 1.0, False),
        depth: int = 0,
    ) -> None:
        nonlocal text_ops, min_size
        if depth > 6:
            return
        ext_ca = _extract_extgstate_ca(resources)
        res_obj = resources.get_object() if (resources and hasattr(resources, "get_object")) else (resources or {})
        xobjs_raw = res_obj.get("/XObject") if isinstance(res_obj, dict) else None
        xobjs = xobjs_raw.get_object() if (xobjs_raw and hasattr(xobjs_raw, "get_object")) else (xobjs_raw or {})

        fill, tr, size, ca, zero_clip = init_state
        gs: list[tuple] = []
        operands: list[bytes] = []
        path_pts: list[tuple[float, float]] = []
        pending_zero_clip = False

        for t in _PDF_TOK.findall(raw):
            if t[:1] in b"(<[]/" or _PDF_NUM.fullmatch(t):
                operands.append(t)
                continue
            op = t.decode("latin1")
            nums: list[float] = []
            for x in reversed(operands):
                if not _PDF_NUM.fullmatch(x):
                    break
                nums.insert(0, float(x))
            if op == "q":
                gs.append((fill, tr, size, ca, zero_clip))
            elif op == "Q" and gs:
                fill, tr, size, ca, zero_clip = gs.pop()
            elif op == "gs" and operands and operands[-1].startswith(b"/"):
                gs_name = operands[-1].decode("latin1")
                if gs_name in ext_ca:
                    ca = ext_ca[gs_name]
            elif op in ("m", "l") and len(nums) >= 2:
                path_pts.append((nums[-2], nums[-1]))
            elif op == "c" and len(nums) >= 6:
                path_pts.extend([(nums[-6], nums[-5]), (nums[-4], nums[-3]), (nums[-2], nums[-1])])
            elif op in ("v", "y") and len(nums) >= 4:
                path_pts.extend([(nums[-4], nums[-3]), (nums[-2], nums[-1])])
            elif op == "re" and len(nums) >= 4:
                rx, ry, rw, rh = nums[-4], nums[-3], nums[-2], nums[-1]
                path_pts.extend([(rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)])
            elif op in ("W", "W*"):
                if path_pts:
                    xs = [pt[0] for pt in path_pts]
                    ys = [pt[1] for pt in path_pts]
                    if (max(xs) - min(xs)) < 1e-4 or (max(ys) - min(ys)) < 1e-4:
                        pending_zero_clip = True
            elif op in ("n", "S", "s", "f", "F", "f*", "B", "B*", "b", "b*"):
                if pending_zero_clip:
                    zero_clip = True
                    pending_zero_clip = False
                path_pts.clear()
            elif op in ("g", "rg", "k"):
                fill = (op, tuple(nums[-{"g": 1, "rg": 3, "k": 4}[op]:]))
            elif op in ("sc", "scn"):
                fill = (op, tuple(nums))
            elif op == "Tr" and nums:
                tr = int(nums[-1])
            elif op == "Tf" and nums:
                size = nums[-1]
            elif op == "Do" and operands and operands[-1].startswith(b"/"):
                xname = operands[-1].decode("latin1")
                if isinstance(xobjs, dict) and xname in xobjs:
                    xo = xobjs[xname].get_object()
                    if xo.get("/Subtype") == "/Form":
                        scan_stream(
                            xo.get_data(),
                            xo.get("/Resources") or resources,
                            (fill, tr, size, ca, zero_clip),
                            depth + 1,
                        )
            elif op in ("Tj", "TJ", "'", '"'):
                text_ops += 1
                if size is not None:
                    min_size = size if min_size is None else min(min_size, size)
                if (
                    fill not in black
                    or tr != 0
                    or ca < 0.999
                    or zero_clip
                    or (size is not None and size < MIN_RENDERED_TEXT_SIZE)
                ):
                    if len(bad) < 10:
                        bad.append(f"fill={fill} ca={ca} clip0={zero_clip} Tr={tr} size={size}")
            operands = []

    for page in reader.pages:
        contents = page.get_contents()
        if contents is None:
            continue
        scan_stream(contents.get_data(), page.get("/Resources"))

    require(text_ops > 0, f"No text-showing operators found in {pdf_path.name}")
    require(
        not bad,
        f"Rendered text in {pdf_path.name} is not opaque black/visible (hidden or recoloured text): {bad}",
    )
    return {
        "text_show_operators": text_ops,
        "non_black_or_invisible": 0,
        "min_font_size": min_size,
        "alpha_and_clip_checked": True,
    }


def verify_evaluated_and_rendered(
    root: Path,
    typst_bin: str,
    outdir: Path,
    gate_b_info: dict | None = None,
    baseline_main_pdf: Path | None = None,
    baseline_manual_pdf: Path | None = None,
    baseline_root: Path | None = None,
    generated_latex_main_pdf: Path | None = None,
    generated_latex_manual_pdf: Path | None = None,
) -> dict:
    b_root, tmp_base = _resolve_baseline_root(root, baseline_root)
    try:
        return _verify_evaluated_and_rendered_impl(
            root=root,
            typst_bin=typst_bin,
            outdir=outdir,
            gate_b_info=gate_b_info,
            baseline_main_pdf=baseline_main_pdf,
            baseline_manual_pdf=baseline_manual_pdf,
            b_root=b_root,
            generated_latex_main_pdf=generated_latex_main_pdf,
            generated_latex_manual_pdf=generated_latex_manual_pdf,
        )
    finally:
        if tmp_base is not None:
            tmp_base.cleanup()


def _verify_evaluated_and_rendered_impl(
    root: Path,
    typst_bin: str,
    outdir: Path,
    gate_b_info: dict | None,
    baseline_main_pdf: Path | None,
    baseline_manual_pdf: Path | None,
    b_root: Path,
    generated_latex_main_pdf: Path | None,
    generated_latex_manual_pdf: Path | None,
) -> dict:
    if gate_b_info is None:
        manifest = json.loads((root / "typst/manifest.json").read_text(encoding="utf-8"))
        gate_b_info = verify_source_and_content_parity(
            root, manifest, baseline_root=b_root, typst_bin=typst_bin
        )
    builder = load_module(root, "aod_build_typst", "scripts/build_typst.py")
    audit_mod = load_module(root, "aod_audit_scientific_sources", "scripts/audit_scientific_sources.py")

    build_report = builder.build_all(
        root=root,
        outdir=outdir,
        typst_bin=typst_bin,
        write_registry=False,
        check_registry_only=True,
    )
    main_digest = build_report["main_sources_sha256"]
    manual_digest = build_report["manual_sources_sha256"]

    main_src = root / "typst" / "main.typ"
    manual_src = root / "typst" / "manual" / "main.typ"
    manual_inputs = {
        "expected_main_digest": main_digest,
        "expected_main_pdf_filename": "main.pdf",
    }

    main_entries_raw = builder.run_typst_eval(typst_bin, root, main_src, "<aod-ref-entry>")
    manual_entries_raw = builder.run_typst_eval(typst_bin, root, manual_src, "<aod-ref-entry>", inputs=manual_inputs)
    manual_mainrefs_raw = builder.run_typst_eval(typst_bin, root, manual_src, "<aod-mainref-use>", inputs=manual_inputs)
    main_bib_raw = builder.run_typst_eval(typst_bin, root, main_src, "<aod-bib-entry>")
    manual_bib_raw = builder.run_typst_eval(typst_bin, root, manual_src, "<aod-bib-entry>", inputs=manual_inputs)
    main_block_eqs_raw = builder.run_typst_eval(typst_bin, root, main_src, "math.equation.where(block: true)")
    manual_block_eqs_raw = builder.run_typst_eval(
        typst_bin, root, manual_src, "math.equation.where(block: true)", inputs=manual_inputs
    )

    _, main_parts = audit_mod.include_graph(b_root, "main", representation="tex")
    _, manual_parts = audit_mod.include_graph(b_root, "manual", representation="tex")
    tex_main_eq_nums, exp_main_numbered = extract_tex_equation_numbers(main_parts)
    tex_manual_eq_nums, exp_manual_numbered = extract_tex_equation_numbers(manual_parts)

    tex_main_labels = set(audit_mod.label_map(b_root, "main", representation="tex"))
    tex_manual_labels = set(audit_mod.label_map(b_root, "manual", representation="tex"))

    typ_main_map = {item["value"]["id"]: item["value"] for item in main_entries_raw}
    typ_manual_map = {item["value"]["id"]: item["value"] for item in manual_entries_raw}
    expected_manual_labels = tex_manual_labels | POST_BASELINE_MANUAL_LABELS
    require(set(typ_main_map) == tex_main_labels,
            f"Main label set mismatch: missing={sorted(tex_main_labels - set(typ_main_map))}, extra={sorted(set(typ_main_map) - tex_main_labels)}")
    require(set(typ_manual_map) == expected_manual_labels,
            f"Manual label set mismatch: missing={sorted(expected_manual_labels - set(typ_manual_map))}, extra={sorted(set(typ_manual_map) - expected_manual_labels)}")

    eq_numbering_report: dict[str, dict[str, int]] = {}
    for surf, block_eqs, exp_cnt, tex_eq_nums, typ_map in (
        ("main", main_block_eqs_raw, exp_main_numbered, tex_main_eq_nums, typ_main_map),
        ("manual", manual_block_eqs_raw, exp_manual_numbered, tex_manual_eq_nums, typ_manual_map),
    ):
        numbered_blocks = [e for e in block_eqs if e.get("numbering") is not None]
        unlabeled_numbered = [e for e in numbered_blocks if not e.get("label")]
        require(
            len(unlabeled_numbered) == 0,
            f"{surf} contains {len(unlabeled_numbered)} unintended unlabeled numbered block equation(s) "
            f"(numbered={len(numbered_blocks)}, expected={exp_cnt})",
        )
        require(
            len(numbered_blocks) == exp_cnt,
            f"{surf} numbered block equation count mismatch: typst={len(numbered_blocks)} vs latex={exp_cnt}",
        )
        for lbl, exp_num in sorted(tex_eq_nums.items()):
            got = typ_map.get(lbl, {}).get("number")
            require(
                got == exp_num,
                f"{surf} equation numbering mismatch for {lbl}: typst={got!r} vs latex={exp_num!r}",
            )
        eq_numbering_report[surf] = {
            "block_equations_total": len(block_eqs),
            "numbered_block_equations": len(numbered_blocks),
            "unlabeled_numbered_equations": 0,
            "labeled_equation_numbers_exact": len(tex_eq_nums),
        }

    main_reg = json.loads((root / "typst/lib/main_registry.json").read_text(encoding="utf-8"))
    require(main_reg["main_sources_sha256"] == main_digest, "Committed Main registry digest mismatch")
    for item in manual_mainrefs_raw:
        v = item["value"]
        require(v["registry_digest"] == main_digest, f"Stale registry digest in {v['ref_id']}")
        raw_id = v["raw_id"]
        require(raw_id in main_reg["entries"], f"Manual Main-ref target absent from Main registry: {raw_id}")
        entry = main_reg["entries"][raw_id]
        require(v["resolved_kind"] == entry["kind"], f"Kind mismatch on {v['ref_id']}")
        require(v["resolved_number"] == entry["number"], f"Number mismatch on {v['ref_id']}")
        require(v["target_page"] == entry["page"], f"Page mismatch on {v['ref_id']}")

    require(len(main_bib_raw) == 10, f"Expected 10 Main bibliography entries, got {len(main_bib_raw)}")
    require(len(manual_bib_raw) == 43, f"Expected 43 Manual bibliography entries, got {len(manual_bib_raw)}")

    # C2: Verify delivered canonical peer PDF pair (main.pdf + manual.pdf) & 172/172 target landings
    delivery = verify_delivered_peer_links(outdir, build_report, main_reg, manual_mainrefs_raw)

    typ_main_pdf = outdir / "main.pdf"
    typ_manual_pdf = outdir / "manual.pdf"
    typ_main_raw = _pdftotext(typ_main_pdf, raw=False)
    typ_manual_raw = _pdftotext(typ_manual_pdf, raw=False)
    typ_main_stream = _pdftotext(typ_main_pdf, raw=True)
    typ_manual_stream = _pdftotext(typ_manual_pdf, raw=True)

    # C1.1 & C1.2: Rendered hygiene, literal CLI commands, and restored semicolons
    for name, txt in (("main.pdf", typ_main_raw), ("manual.pdf", typ_manual_raw)):
        require(len(txt.strip()) > 20000, f"Rendered PDF text unexpectedly short in {name}")
        for forbidden in ("columns: (", "table.header(", "aod-definition", "aod-provenance", "aod-flowchart", "??"):
            require(forbidden not in txt, f"Leaked raw syntax or unresolved marker {forbidden!r} in {name}")

    cli_checked = 0
    for surf, raw_txt, stream_txt in (
        ("main", typ_main_raw, typ_main_stream),
        ("manual", typ_manual_raw, typ_manual_stream),
    ):
        flat_raw = re.sub(r"\s+", " ", raw_txt.replace("/\n", "/"))
        flat_stream = re.sub(r"\s+", " ", stream_txt.replace("/\n", "/").replace("-\n", "-"))
        for cmd in sorted(set(gate_b_info["_cli_commands"][surf])):
            require(
                cmd in flat_raw or cmd in flat_stream,
                f"Literal CLI command corrupted or missing in rendered {surf}.pdf: {cmd!r}",
            )
            cli_checked += 1
    require("–check-data" not in typ_manual_raw, "En-dash corruption '–check-data' detected in manual.pdf")
    require("§2; model values follow their admitted support." in re.sub(r"\s+", " ", typ_main_stream),
            "Missing literal semicolon in opening Main paragraph (§2; model values...)")
    require("(32); the unit hinge is an extra hypothesis" in re.sub(r"\s+", " ", typ_main_stream),
            "Missing literal semicolon in Appendix H.5 ((32); the unit hinge...)")

    vocab = _source_prose_vocab(gate_b_info)
    typ_norm_by_surf = {
        "main": " " + _norm_rendered_text_tokens(typ_main_stream, is_typst=True) + " ",
        "manual": " " + _norm_rendered_text_tokens(typ_manual_stream, is_typst=True) + " ",
    }

    # C3: rendered text paint (hidden / recoloured / microscopic text is rejected).
    paint = {
        "main": _scan_pdf_text_paint(typ_main_pdf),
        "manual": _scan_pdf_text_paint(typ_manual_pdf),
    }

    # C3b: shared pure-vector PDF verification (0 /Image XObjects and 0 inline BI/ID/EI images).
    vf_manifest = json.loads((root / "typst/manifest.json").read_text(encoding="utf-8"))
    pure_vector_surfs = _pure_vector_surfaces(root, vf_manifest)
    typ_rasters = {
        "main": _require_zero_pdf_rasters(typ_main_pdf, "main.pdf")
        if "main" in pure_vector_surfs else _inspect_pdf_rasters(typ_main_pdf),
        "manual": _require_zero_pdf_rasters(typ_manual_pdf, "manual.pdf")
        if "manual" in pure_vector_surfs else _inspect_pdf_rasters(typ_manual_pdf),
    }
    fig9_ast_report = (
        _verify_figure9_math_attachment(typst_bin, root)
        if (root / "typst/lib/figures/main/cycle_disturbance_shedding.typ").is_file()
        else None
    )

    def clause_variants(sent: str) -> list[str]:
        out = [" " + sent + " "]
        if " SADAR " in out[0]:
            out.append(out[0].replace(" SADAR ", " S "))
        return out

    def check_clauses_for(
        surf: str, cand_norm: str, cand_label: str, b_norm: str | None, *, cap_repeated_headers: bool = False
    ) -> dict:
        """Every source prose clause is verified against the baseline PDF (count parity) or,
        failing a baseline anchor, against the candidate rendering; others are reported."""
        all_sents = [
            (src_rel, sent)
            for src_rel, clause in gate_b_info["_prose_clauses"][surf]
            for sent in _split_sentence_clauses(clause)
        ]
        sent_src_counts = Counter(sent for _, sent in all_sents)
        total = anchored = typst_only = 0
        unverified: list[str] = []
        for src_rel, sent in all_sents:
            total += 1
            variants = clause_variants(sent)
            hit = None
            if b_norm is not None:
                hit = next((v for v in variants if b_norm.count(v) >= 1), None)
            if hit is not None:
                bc, tc = b_norm.count(hit), cand_norm.count(hit)
                expected_min = min(bc, sent_src_counts[sent]) if cap_repeated_headers else bc
                require(
                    tc >= expected_min,
                    f"Rendered prose mismatch in {cand_label} (from {src_rel}): "
                    f"clause {sent!r} count base={bc} (expected>={expected_min}) vs candidate={tc}",
                )
                anchored += 1
                continue
            if b_norm is None and any(w.lower() in SCIENTIFIC_QUALIFIERS for w in sent.split()):
                require(
                    any(v in cand_norm for v in variants),
                    f"Rendered prose clause missing in {cand_label} (possible #show rule mutation, "
                    f"from {src_rel}): {sent!r}",
                )
            if any(v in cand_norm for v in variants):
                typst_only += 1
            else:
                unverified.append(f"{src_rel}: {sent[:120]}")
        return {
            "source_clauses_total": total,
            "baseline_anchored": anchored,
            "typst_rendering_verified_only": typst_only,
            "unverified": len(unverified),
            "unverified_samples": unverified[:10],
        }

    baseline_pdf_report: dict[str, object] = {"performed": False}
    base_norm_by_surf: dict[str, str] | None = None
    base_raw_by_surf: dict[str, str] = {}
    base_stream_by_surf: dict[str, str] = {}
    if baseline_main_pdf is not None and baseline_manual_pdf is not None:
        require(baseline_main_pdf.is_file(), f"Baseline Main PDF not found: {baseline_main_pdf}")
        require(baseline_manual_pdf.is_file(), f"Baseline Manual PDF not found: {baseline_manual_pdf}")
        require(
            not os.path.samefile(baseline_main_pdf, typ_main_pdf),
            "Baseline Main PDF and candidate Typst main.pdf point to the same file",
        )
        require(
            not os.path.samefile(baseline_manual_pdf, typ_manual_pdf),
            "Baseline Manual PDF and candidate Typst manual.pdf point to the same file",
        )
        base_main_raw = _pdftotext(baseline_main_pdf, raw=False)
        base_manual_raw = _pdftotext(baseline_manual_pdf, raw=False)
        base_main_stream = _pdftotext(baseline_main_pdf, raw=True)
        base_manual_stream = _pdftotext(baseline_manual_pdf, raw=True)
        base_raw_by_surf = {"main": base_main_raw, "manual": base_manual_raw}
        base_stream_by_surf = {"main": base_main_stream, "manual": base_manual_stream}

        base_norm_by_surf = {
            "main": " " + _norm_rendered_text_tokens(base_main_stream, is_typst=False, vocab=vocab) + " ",
            "manual": " " + _norm_rendered_text_tokens(base_manual_stream, is_typst=False, vocab=vocab) + " ",
        }

        per_doc: dict[str, dict] = {}
        for surf, b_pdf, t_pdf, b_raw, t_raw, b_stream, t_stream, entries_map in (
            ("main", baseline_main_pdf, typ_main_pdf, base_main_raw, typ_main_raw, base_main_stream, typ_main_stream, typ_main_map),
            ("manual", baseline_manual_pdf, typ_manual_pdf, base_manual_raw, typ_manual_raw, base_manual_stream, typ_manual_stream, typ_manual_map),
        ):
            # (a) Exact Table & Figure & Label resolved numbers vs historical XeLaTeX PDF
            b_flat = re.sub(r"\s+", " ", b_raw.replace("\xa0", " "))
            t_flat = re.sub(r"\s+", " ", t_raw.replace("\xa0", " "))
            for prefix in ("Table", "Figure"):
                b_nums = sorted({int(x) for x in re.findall(rf"\b{prefix}\s+(\d+)\s*:", b_flat)})
                t_nums = sorted({int(x) for x in re.findall(rf"\b{prefix}\s+(\d+)\s*:", t_flat)})
                require(
                    b_nums == t_nums,
                    f"{surf} rendered {prefix} numbering drift vs historical LaTeX PDF: "
                    f"base={b_nums} vs typst={t_nums}",
                )
            for lbl, e in sorted(entries_map.items()):
                k, num = e["kind"], e["number"]
                if k == "table":
                    needle = f"Table {num}:"
                elif k == "figure":
                    needle = f"Figure {num}:"
                elif k in ("equation", "rg-equation"):
                    needle = f"({num})"
                else:
                    needle = f"{num} "
                require(
                    needle in b_flat,
                    f"{surf} resolved anchor {lbl} ({k} {num}) absent from historical baseline PDF: {needle!r}",
                )

            # (b) Complete case-sensitive rendered bibliography entry-by-entry comparison!
            b_bib = _extract_rendered_bib_entries(b_stream)
            t_bib = _extract_rendered_bib_entries(t_stream)
            require(
                set(b_bib) == set(t_bib),
                f"{surf} rendered bibliography key-index mismatch: base={len(b_bib)} vs typst={len(t_bib)}",
            )
            for idx in sorted(b_bib):
                b_can = _canon_bib_for_pdf_wrap(b_bib[idx])
                t_can = _canon_bib_for_pdf_wrap(t_bib[idx])
                require(
                    b_can == t_can,
                    f"{surf} rendered bibliography [{idx}] text mismatch vs historical LaTeX:\n"
                    f"  BASE: {b_bib[idx]}\n  TYP : {t_bib[idx]}",
                )

            # (c) Source clause -> rendered prose, in order-free count parity against the historical
            #     XeLaTeX PDF (vocabulary-bound de-hyphenation), with Typst-rendering fallback.
            clause_report = check_clauses_for(surf, typ_norm_by_surf[surf], f"{surf}.pdf", base_norm_by_surf[surf])

            # (c2) Bidirectional: every 4-gram of source-vocabulary words in the rendered Typst
            #      body must occur in the historical baseline body or in the source clauses, so
            #      evaluation-time insertions (show/figure/caption rules) are rejected.
            #      For S1b native vector figures (which replaced textless historical rasters),
            #      each pinned standalone exported vector figure PDF token sequence must occur
            #      verbatim-contiguously in the rendered Typst body and is stripped cleanly
            #      with a non-word boundary before 4-gram and OOV checks.
            src_words = [w for _, c in gate_b_info["_prose_clauses"][surf] for w in c.split()]
            src_grams = set(_run_ngrams(_vocab_runs(src_words, vocab)))
            b_body_s, t_body_s = _rendered_body(b_stream), _rendered_body(t_stream)
            b_tokens = _norm_rendered_text_tokens(b_body_s, is_typst=False, vocab=vocab).split()
            t_tokens = _norm_rendered_text_tokens(t_body_s, is_typst=True).split()

            fig_gen_dir = root / ("latex/figures/generated" if surf == "main" else "latex/manual/figures/generated")
            fig_manifest_path = fig_gen_dir / "FIGURE_MANIFEST.json"
            expected_vf_prefix = f"typst/lib/figures/{surf}/"
            expected_vf_count = sum(
                1 for k in vf_manifest.get("vector_figure_components", {}) if k.startswith(expected_vf_prefix)
            )
            fig_streams: list[str] = []
            t_tokens_non_fig = list(t_tokens)
            vector_figures_verbatim_matched = 0
            if expected_vf_count > 0:
                require(
                    fig_manifest_path.is_file(),
                    f"Missing required {fig_manifest_path.relative_to(root)} for {expected_vf_count} declared {surf} vector figure(s)",
                )
            if fig_manifest_path.is_file():
                fm_data = json.loads(fig_manifest_path.read_text(encoding="utf-8"))
                for f_entry in fm_data.get("figures", []):
                    if f_entry.get("component_kind") != "vector_figure":
                        continue
                    f_pdf = fig_gen_dir / f_entry["output_filename"]
                    require(
                        f_pdf.is_file() and sha256_file(f_pdf) == f_entry["output_sha256"],
                        f"Pinned exported vector figure PDF missing or modified: {f_pdf}",
                    )
                    _require_zero_pdf_raster_xobjects(f_pdf, str(f_pdf.relative_to(root)))
                    f_stream = _pdftotext(f_pdf, raw=True)
                    fig_streams.append(f_stream)
                    f_toks = _norm_rendered_text_tokens(f_stream, is_typst=True).split()
                    require(bool(f_toks), f"Exported vector figure {f_entry['slug']} yielded empty normalized text")
                    flen = len(f_toks)
                    matched_idx = None
                    for idx in range(len(t_tokens_non_fig) - flen + 1):
                        if t_tokens_non_fig[idx:idx + flen] == f_toks:
                            matched_idx = idx
                            break
                    require(
                        matched_idx is not None,
                        f"Pinned exported vector figure {f_entry['slug']} text missing from rendered {surf}.pdf",
                    )
                    t_tokens_non_fig = (
                        t_tokens_non_fig[:matched_idx] + ["|"] + t_tokens_non_fig[matched_idx + flen:]
                    )
                    vector_figures_verbatim_matched += 1
            require(
                vector_figures_verbatim_matched == expected_vf_count,
                f"Vector figure verbatim match count mismatch in {surf}.pdf: "
                f"matched={vector_figures_verbatim_matched} vs declared={expected_vf_count}",
            )

            base_grams = set(_run_ngrams(_vocab_runs(b_tokens, vocab)))
            t_grams = _run_ngrams(_vocab_runs(t_tokens_non_fig, vocab))
            layout_allow = RENDERED_LAYOUT_NGRAM_ALLOWLIST[surf]
            novel = [g for g in t_grams if g not in base_grams and g not in src_grams and g not in layout_allow]
            # Words outside the source vocabulary (>= 4 letters) must not exceed their baseline count.
            b_alpha = Counter(x for x in b_tokens if x.isalpha())
            for k in (2, 3):
                for i in range(len(b_tokens) - k + 1):
                    win = b_tokens[i:i + k]
                    if all(x.isalpha() for x in win):
                        b_alpha["".join(win)] += 1
            t_alpha = Counter(x for x in t_tokens_non_fig if x.isalpha())
            t_math = _typst_math_word_counts(t_body_s)
            for fs in fig_streams:
                fm_words = _typst_math_word_counts(fs)
                for mw, mc in fm_words.items():
                    t_math[mw] = max(0, t_math.get(mw, 0) - mc)
            oov_allow = RENDERED_OOV_EXCESS_ALLOWLIST[surf]
            cand = {
                w: t_alpha[w] - t_math.get(w, 0)
                for w in t_alpha
                if len(w) >= OOV_WORD_MIN_LEN and w not in vocab
            }
            cand = {w: n for w, n in cand.items() if n - b_alpha[w] > oov_allow.get(w, 0)}
            if cand:
                b_oov_tokens = [x for x in b_tokens if x.isalpha() and x not in vocab]
                for w in cand:
                    b_alpha[w] += sum(x.count(w) for x in b_oov_tokens if x != w)
            oov_excess = sorted(
                f"{w}(+{n - b_alpha[w]})"
                for w, n in cand.items()
                if n - b_alpha[w] > oov_allow.get(w, 0)
            )
            require(
                not novel and not oov_excess,
                f"Rendered insertion in {surf}.pdf: out-of-source words exceeding the baseline "
                f"{oov_excess[:8]}; {len(novel)} word 4-gram(s) absent from the historical baseline and "
                f"the source, e.g. {sorted(set(novel))[:6]}",
            )
            layout_hits = sorted({g for g in t_grams if g in layout_allow and g not in base_grams and g not in src_grams})

            # (c3) Exact rendered relation/operator glyph parity against historical baseline + pinned vector figures.
            glyphs = {}
            for g in RENDERED_GLYPH_PARITY_SET:
                bcount = b_body_s.count(g)
                fig_delta = sum(fs.count(g) for fs in fig_streams)
                tcount = t_body_s.count(g)
                require(
                    bcount + fig_delta == tcount,
                    f"Rendered glyph {g!r} count differs in {surf}.pdf: base={bcount} + vec_figs={fig_delta} vs typst={tcount}",
                )
                glyphs[g] = tcount

            # (d) Rendered body decimal check (References already verified char-for-char in step (b))
            m_bref = re.search(r"\nReferences\s*\n", b_raw)
            m_tref = re.search(r"\nReferences\s*\n", t_raw)
            b_body = b_raw[:m_bref.start()] if m_bref else b_raw
            t_body = t_raw[:m_tref.start()] if m_tref else t_raw
            b_decs = sorted(re.findall(r"(?<![A-Za-z0-9_.])\d+\.\d+(?![A-Za-z0-9_.])", b_body))
            t_decs = sorted(re.findall(r"(?<![A-Za-z0-9_.])\d+\.\d+(?![A-Za-z0-9_.])", t_body))
            missing_decs = [d for d in set(b_decs) if t_decs.count(d) < b_decs.count(d)]
            require(not missing_decs, f"{surf} rendered decimals missing vs baseline PDF: {missing_decs[:15]}")

            # (d2) Clickable external /URI destination set parity vs historical baseline PDF
            b_uris = _inspect_pdf_links(b_pdf, expected_peer_pdf=None)["unique_external_uris"]
            t_uris = _inspect_pdf_links(
                t_pdf, expected_peer_pdf="main.pdf" if surf == "manual" else None
            )["unique_external_uris"]
            require(
                b_uris == t_uris,
                f"{surf} clickable external /URI destination mismatch vs baseline PDF: "
                f"missing={sorted(set(b_uris) - set(t_uris))}, extra={sorted(set(t_uris) - set(b_uris))}",
            )

            # (d3) Exact inline citation bracket sequence parity vs historical baseline PDF
            b_cites = re.findall(r"\[\d+(?:,\s*\d+)*\]", b_body_s)
            t_cites = re.findall(r"\[\d+(?:,\s*\d+)*\]", t_body_s)
            require(
                b_cites == t_cites,
                f"{surf} rendered inline citation sequence mismatch vs baseline PDF: "
                f"base={len(b_cites)} vs typst={len(t_cites)}",
            )

            per_doc[surf] = {
                "rendered_tables_matched": len(re.findall(r"\bTable\s+\d+\s*:", t_flat)),
                "rendered_figures_matched": len(re.findall(r"\bFigure\s+\d+\s*:", t_flat)),
                "rendered_bib_entries_exact": len(t_bib),
                "rendered_inline_citations_exact": len(t_cites),
                "rendered_external_uris_exact": len(t_uris),
                "rendered_prose_clauses": clause_report,
                "rendered_insertion_ngrams_checked": len(t_grams),
                "rendered_insertion_novel_ngrams": 0,
                "rendered_oov_words_checked": sum(1 for w in t_alpha if len(w) >= OOV_WORD_MIN_LEN and w not in vocab),
                "rendered_oov_excess_beyond_allowlist": 0,
                "rendered_layout_allowlisted_ngrams": layout_hits,
                "rendered_glyph_parity": glyphs,
                "rendered_decimals_matched": len(b_decs),
                "vector_figures_verbatim_matched": vector_figures_verbatim_matched,
            }

        # (e) Verify all 172 Manual->Main reference displays appear in baseline Manual PDF
        base_manual_flat = re.sub(r"\s+", " ", base_manual_raw.replace("\xa0", " "))
        for item in manual_mainrefs_raw:
            disp = item["value"]["resolved_display"]
            require(
                disp in base_manual_flat,
                f"Resolved Manual->Main reference {disp!r} ({item['value']['ref_id']}) not found in baseline Manual PDF",
            )

        baseline_pdf_report = {
            "performed": True,
            "baseline_main_pdf_sha256": sha256_file(baseline_main_pdf),
            "baseline_manual_pdf_sha256": sha256_file(baseline_manual_pdf),
            "results": {
                **per_doc,
                "manual_mainref_displays_matched_in_baseline_pdf": len(manual_mainrefs_raw),
            },
        }
    else:
        baseline_pdf_report = {
            "performed": False,
            "rendered_prose_clauses_typst_only": {
                s: check_clauses_for(s, typ_norm_by_surf[s], f"{s}.pdf", None)
                for s in ("main", "manual")
            },
        }

    # Verify generated LaTeX compatibility PDFs (local destinations, sibling /GoToR /D landings,
    # complete outlines, rendered spacing/unit boundaries, and baseline parity).
    generated_latex_pdf_report: dict[str, object] = {"performed": False}
    require(
        (generated_latex_main_pdf is None) == (generated_latex_manual_pdf is None),
        "Both --generated-latex-main-pdf and --generated-latex-manual-pdf must be supplied together",
    )
    if generated_latex_main_pdf is not None and generated_latex_manual_pdf is not None:
        require(generated_latex_main_pdf.is_file(), f"Generated LaTeX Main PDF not found: {generated_latex_main_pdf}")
        require(generated_latex_manual_pdf.is_file(), f"Generated LaTeX Manual PDF not found: {generated_latex_manual_pdf}")
        require(
            not os.path.samefile(generated_latex_main_pdf, typ_main_pdf),
            "Generated LaTeX Main PDF and native Typst main.pdf point to the same file",
        )
        require(
            not os.path.samefile(generated_latex_manual_pdf, typ_manual_pdf),
            "Generated LaTeX Manual PDF and native Typst manual.pdf point to the same file",
        )
        if baseline_main_pdf is not None:
            require(
                not os.path.samefile(generated_latex_main_pdf, baseline_main_pdf),
                "Generated LaTeX Main PDF and historical baseline Main PDF point to the same file",
            )
        if baseline_manual_pdf is not None:
            require(
                not os.path.samefile(generated_latex_manual_pdf, baseline_manual_pdf),
                "Generated LaTeX Manual PDF and historical baseline Manual PDF point to the same file",
            )

        gen_main_links = _inspect_pdf_links(generated_latex_main_pdf, expected_peer_pdf=None)
        gen_manual_links = _inspect_pdf_links(generated_latex_manual_pdf, expected_peer_pdf="main.pdf")
        require(
            not gen_main_links["broken_local_destinations"],
            f"Generated LaTeX main.pdf has broken local link destination(s): "
            f"{gen_main_links['broken_local_destinations'][:10]}",
        )
        require(
            not gen_manual_links["broken_local_destinations"],
            f"Generated LaTeX manual.pdf has broken local link destination(s): "
            f"{gen_manual_links['broken_local_destinations'][:10]}",
        )
        gen_peer_total = len(gen_manual_links["peer_pdf_links"]) + len(gen_manual_links["gotor_peer_links"])
        require(
            len(gen_manual_links["stale_main_pdf_links"]) == 0,
            f"Generated LaTeX manual.pdf has wrong/stale peer links: {gen_manual_links['stale_main_pdf_links'][:5]}",
        )
        require(
            gen_peer_total >= len(manual_mainrefs_raw),
            f"Generated LaTeX manual.pdf expected >= {len(manual_mainrefs_raw)} peer links to sibling main.pdf, got {gen_peer_total}",
        )

        # Extract per-page text of generated main.pdf for sibling /GoToR /D landing checks
        gen_main_raw = _pdftotext(generated_latex_main_pdf, raw=False)
        gen_main_pages_txt = gen_main_raw.split("\x0c")
        if gen_main_pages_txt and gen_main_pages_txt[-1] == "":
            gen_main_pages_txt = gen_main_pages_txt[:-1]
        base_main_links = None
        base_manual_links = None
        base_main_pages_txt = None
        if baseline_main_pdf is not None and baseline_manual_pdf is not None:
            base_main_links = _inspect_pdf_links(baseline_main_pdf, expected_peer_pdf=None)
            base_manual_links = _inspect_pdf_links(baseline_manual_pdf, expected_peer_pdf="main.pdf")
            base_main_pages_txt = base_raw_by_surf["main"].split("\x0c")
            if base_main_pages_txt and base_main_pages_txt[-1] == "":
                base_main_pages_txt = base_main_pages_txt[:-1]

        peer_dest_report = _verify_gotor_peer_destinations(
            gen_manual_links,
            gen_main_links,
            gen_main_pages_txt,
            baseline_manual_links=base_manual_links,
            baseline_main_links=base_main_links,
            baseline_main_pages_txt=base_main_pages_txt,
        )

        gen_per_doc: dict[str, dict] = {}
        for surf, g_pdf, b_pdf in (
            ("main", generated_latex_main_pdf, baseline_main_pdf),
            ("manual", generated_latex_manual_pdf, baseline_manual_pdf),
        ):
            g_raw = gen_main_raw if surf == "main" else _pdftotext(g_pdf, raw=False)
            g_stream = _pdftotext(g_pdf, raw=True)
            require(len(g_raw.strip()) > 20000, f"Generated LaTeX {surf}.pdf text unexpectedly short")
            for forbidden in ("columns: (", "table.header(", "aod-definition", "aod-provenance", "aod-flowchart", "??"):
                require(forbidden not in g_raw, f"Leaked marker {forbidden!r} in generated LaTeX {surf}.pdf")
            g_flat_cli = re.sub(r"\s+", " ", g_raw.replace("/\n", "/"))
            for cmd in sorted(set(gate_b_info["_cli_commands"][surf])):
                require(cmd in g_flat_cli, f"CLI command missing in generated LaTeX {surf}.pdf: {cmd!r}")

            outline_boundary_report = _verify_pdf_outlines_and_boundaries(surf, g_pdf, g_raw, baseline_pdf=b_pdf)
            g_rasters = (
                _require_zero_pdf_rasters(g_pdf, f"latex/{surf}.pdf")
                if surf in pure_vector_surfs else _inspect_pdf_rasters(g_pdf)
            )

            g_norm = " " + _norm_rendered_text_tokens(g_stream, is_typst=False, vocab=vocab) + " "
            g_flat = re.sub(r"\s+", " ", g_raw.replace("\xa0", " "))
            g_links = gen_main_links if surf == "main" else gen_manual_links
            entry: dict[str, object] = {
                "pages": g_links["pages"],
                "pdf_sha256": sha256_file(g_pdf),
                "pdf_bytes": g_pdf.stat().st_size,
                "raster_image_xobjects": g_rasters["raster_image_xobjects"],
                "inline_raster_images": g_rasters["inline_raster_images"],
                "total_raster_images": g_rasters["total_raster_images"],
                "local_links_checked": g_links["internal_links"],
                "broken_local_destinations": 0,
                "named_destinations_count": len(g_links["named_destinations"]),
                "outlines_and_boundaries": outline_boundary_report,
            }
            if b_pdf is not None and base_norm_by_surf is not None:
                b_raw = base_raw_by_surf[surf]
                b_stream = base_stream_by_surf[surf]
                b_flat = re.sub(r"\s+", " ", b_raw.replace("\xa0", " "))
                for prefix in ("Table", "Figure"):
                    b_nums = sorted({int(x) for x in re.findall(rf"\b{prefix}\s+(\d+)\s*:", b_flat)})
                    g_nums = sorted({int(x) for x in re.findall(rf"\b{prefix}\s+(\d+)\s*:", g_flat)})
                    require(
                        b_nums == g_nums,
                        f"Generated LaTeX {surf} {prefix} numbering drift vs baseline: base={b_nums} vs gen={g_nums}",
                    )
                b_bib = _extract_rendered_bib_entries(b_stream)
                g_bib = _extract_rendered_bib_entries(g_stream)
                require(
                    set(b_bib) == set(g_bib),
                    f"Generated LaTeX {surf} bibliography count mismatch: base={len(b_bib)} vs gen={len(g_bib)}",
                )
                for idx in sorted(b_bib):
                    require(
                        _canon_bib_for_pdf_wrap(b_bib[idx]) == _canon_bib_for_pdf_wrap(g_bib[idx]),
                        f"Generated LaTeX {surf} bibliography [{idx}] mismatch vs baseline:\n"
                        f"  BASE: {b_bib[idx]}\n  GEN : {g_bib[idx]}",
                    )
                b_uris = (base_main_links if surf == "main" else base_manual_links)["unique_external_uris"]
                g_uris = g_links["unique_external_uris"]
                require(
                    b_uris == g_uris,
                    f"Generated LaTeX {surf} external /URI mismatch vs baseline: "
                    f"missing={sorted(set(b_uris) - set(g_uris))}, extra={sorted(set(g_uris) - set(b_uris))}",
                )
                b_cites = re.findall(r"\[\d+(?:,\s*\d+)*\]", _rendered_body(b_stream))
                g_cites = re.findall(r"\[\d+(?:,\s*\d+)*\]", _rendered_body(g_stream))
                require(
                    b_cites == g_cites,
                    f"Generated LaTeX {surf} inline citation sequence mismatch vs baseline: "
                    f"base={len(b_cites)} vs gen={len(g_cites)}",
                )
                m_bref = re.search(r"\nReferences\s*\n", b_raw)
                m_gref = re.search(r"\nReferences\s*\n", g_raw)
                b_decs = sorted(re.findall(r"(?<![A-Za-z0-9_.])\d+\.\d+(?![A-Za-z0-9_.])", b_raw[:m_bref.start()] if m_bref else b_raw))
                g_decs = sorted(re.findall(r"(?<![A-Za-z0-9_.])\d+\.\d+(?![A-Za-z0-9_.])", g_raw[:m_gref.start()] if m_gref else g_raw))
                missing_decs = [d for d in set(b_decs) if g_decs.count(d) < b_decs.count(d)]
                require(not missing_decs, f"Generated LaTeX {surf} rendered decimals missing vs baseline: {missing_decs[:15]}")
                g_clause_report = check_clauses_for(
                    surf, g_norm, f"latex/{surf}.pdf", base_norm_by_surf[surf], cap_repeated_headers=True
                )
                entry.update({
                    "rendered_tables_matched": len(re.findall(r"\bTable\s+\d+\s*:", g_flat)),
                    "rendered_figures_matched": len(re.findall(r"\bFigure\s+\d+\s*:", g_flat)),
                    "rendered_bib_entries_exact": len(g_bib),
                    "rendered_inline_citations_exact": len(g_cites),
                    "rendered_external_uris_exact": len(g_uris),
                    "rendered_decimals_matched": len(b_decs),
                    "rendered_prose_clauses": g_clause_report,
                })
            gen_per_doc[surf] = entry

        generated_latex_pdf_report = {
            "performed": True,
            "manual_sibling_peer_links": gen_peer_total,
            "manual_stale_peer_links": 0,
            "peer_destination_verification": peer_dest_report,
            "results": gen_per_doc,
        }

    return {
        "typst_version": build_report["typst_version"],
        "creation_timestamp": build_report["creation_timestamp"],
        "main_sources_sha256": main_digest,
        "manual_sources_sha256": manual_digest,
        "candidate_pdfs": {
            "main_pdf_sha256": build_report["main_pdf_sha256"],
            "main_pdf_bytes": build_report["main_pdf_bytes"],
            "main_raster_image_xobjects": typ_rasters["main"]["raster_image_xobjects"],
            "main_inline_raster_images": typ_rasters["main"]["inline_raster_images"],
            "main_total_raster_images": typ_rasters["main"]["total_raster_images"],
            "manual_pdf_sha256": build_report["manual_pdf_sha256"],
            "manual_pdf_bytes": build_report["manual_pdf_bytes"],
            "manual_raster_image_xobjects": typ_rasters["manual"]["raster_image_xobjects"],
            "manual_inline_raster_images": typ_rasters["manual"]["inline_raster_images"],
            "manual_total_raster_images": typ_rasters["manual"]["total_raster_images"],
            "pure_vector_surfaces_enforced": sorted(pure_vector_surfs),
        },
        "figure9_formula_attachment": fig9_ast_report,
        "main_labels_verified": len(typ_main_map),
        "manual_labels_verified": len(typ_manual_map),
        "equation_numbering": eq_numbering_report,
        "manual_mainrefs_verified": len(manual_mainrefs_raw),
        "main_bib_entries": len(main_bib_raw),
        "manual_bib_entries": len(manual_bib_raw),
        "cli_commands_verified_verbatim": cli_checked,
        "delivered_peer_pdf_verification": delivery,
        "pdf_stats": {
            "main": delivery["main_stats"],
            "manual": delivery["manual_stats"],
        },
        "rendered_text_paint": paint,
        "baseline_pdf_comparison": baseline_pdf_report,
        "generated_latex_pdf_comparison": generated_latex_pdf_report,
    }


# =============================================================================
# Gate D: Mandatory Negative Controls (Original 6 + 4 Review Mutations + Peer PDF)
# =============================================================================

# Intended diagnostic of each original / R01 control (a rejection by any other check fails Gate D).
CONTROL_EXPECTED_DIAGNOSTICS = {
    "1a_changed_table_value": "Table cell parity mismatch for manual/data/derived/sparc_summary_table.tex",
    "1b_changed_equation_exponent": "Equation structure mismatch for eq:hinge-reflection-involution",
    "2_removed_qualification": "Ordered content/math parity mismatch in sections/04_cut_running_fractal_tesseract.tex",
    "3_omitted_active_table": "not included by typst/manual/main.typ: typst/manual/tables/sparc_summary_table.typ",
    "4_wrong_reference_target_type": "Wrong Main reference type for mainequation(main:sec:m3-maps)",
    "5_stale_main_registry": "Stale Main registry",
    "6_removed_short_negation": "Ordered content/math parity mismatch in manual/sections/02_mapping_error.tex",
    "7_changed_inline_integer": "Ordered content/math parity mismatch in manual/sections/02_mapping_error.tex",
    "8_changed_equation_grouping": "Equation structure mismatch for eq:manual-m3-original-interval",
    "9_show_rule_rendered_mutation": "with no physical uncertainty model",
    "10_wrong_peer_pdf_filename": "Main companion filename mismatch",
}


def run_negative_controls(
    root: Path,
    typst_bin: str,
    baseline_main_pdf: Path | None = None,
    baseline_manual_pdf: Path | None = None,
    baseline_root: Path | None = None,
    generated_latex_main_pdf: Path | None = None,
    generated_latex_manual_pdf: Path | None = None,
) -> dict:
    manifest = json.loads((root / "typst/manifest.json").read_text(encoding="utf-8"))
    results: dict[str, dict] = {}
    b_root, tmp_base = _resolve_baseline_root(root, baseline_root)
    try:
        return _run_negative_controls_impl(
            root, typst_bin, manifest, results, b_root,
            baseline_main_pdf, baseline_manual_pdf,
            generated_latex_main_pdf, generated_latex_manual_pdf,
        )
    finally:
        if tmp_base is not None:
            tmp_base.cleanup()


def _run_negative_controls_impl(
    root: Path,
    typst_bin: str,
    manifest: dict,
    results: dict[str, dict],
    b_root: Path,
    baseline_main_pdf: Path | None,
    baseline_manual_pdf: Path | None,
    generated_latex_main_pdf: Path | None = None,
    generated_latex_manual_pdf: Path | None = None,
) -> dict:

    def make_sandbox(tmp: Path, include_figures: bool = True) -> Path:
        sb = tmp / "repo"
        sb.mkdir()
        for d in ("typst", "scripts", "contracts"):
            shutil.copytree(root / d, sb / d, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(root / "refs.bib", sb / "refs.bib")
        (sb / "manual").mkdir()
        shutil.copy2(root / "manual" / "refs.bib", sb / "manual" / "refs.bib")
        if include_figures:
            shutil.copytree(root / "figures_jpg", sb / "figures_jpg")
            shutil.copytree(root / "manual" / "figures", sb / "manual" / "figures")
            if (root / "wavelet_shedding_simulation.csv").is_file():
                shutil.copy2(root / "wavelet_shedding_simulation.csv", sb / "wavelet_shedding_simulation.csv")
            if (root / "manual" / "data").is_dir():
                shutil.copytree(root / "manual" / "data", sb / "manual" / "data")
            for gen_rel in (
                "latex/figures/generated",
                "latex/manual/figures/generated",
                "latex/sections",
                "latex/appendices",
                "latex/manual/sections",
                "latex/manual/appendices",
            ):
                if (root / gen_rel).is_dir():
                    shutil.copytree(root / gen_rel, sb / gen_rel, dirs_exist_ok=True)
        return sb

    def expect_rejection(name: str, fn, expect: str = "") -> None:
        """The mutation must be rejected, and by the intended gate (diagnostic contains `expect`)."""
        expect = expect or CONTROL_EXPECTED_DIAGNOSTICS[name]
        try:
            fn()
        except Exception as exc:
            msg = str(exc)
            if expect not in msg:
                raise ValueError(
                    f"Negative control {name} was rejected by an unintended check "
                    f"(expected diagnostic containing {expect!r}): {msg.splitlines()[0][:300] if msg else type(exc).__name__}"
                ) from exc
            m_panic = re.search(r"error: panicked with: [^\n]+", msg)
            lines = msg.splitlines()
            summary = m_panic.group(0) if m_panic else lines[0]
            if not m_panic and summary.endswith(":") and len(lines) > 1:
                summary += " " + lines[1].strip()
            summary = re.sub(r"/tmp/[^\s:\"']+", "<sandbox>", summary)
            results[name] = {"rejected": True, "expected_diagnostic": expect, "error": summary[:180]}
            return
        raise ValueError(f"Negative control FAILED to reject mutation: {name}")

    has_baselines = baseline_main_pdf is not None and baseline_manual_pdf is not None

    def repin(sb: Path, rel: str) -> dict:
        """Sandbox manifest whose digest for `rel` matches the mutated file, so the policy gate
        (not the digest pin) is the check that must reject a content-file mutation."""
        m2 = json.loads(json.dumps(manifest))
        hits = 0
        for e in m2["active_source_map"]:
            if e["typst_target"] == rel:
                e["typst_sha256"] = sha256_file(sb / rel)
                hits += 1
        if rel in m2.get("diagram_components", {}):
            m2["diagram_components"][rel] = sha256_file(sb / rel)
            hits += 1
        if rel in m2.get("vector_figure_components", {}):
            m2["vector_figure_components"][rel] = sha256_file(sb / rel)
            hits += 1
        require(hits == 1, f"Control re-pin target not in manifest: {rel}")
        return m2

    def mutate(sb: Path, rel: str, old: str, new: str) -> None:
        p = sb / rel
        txt = p.read_text(encoding="utf-8")
        require(txt.count(old) == 1, f"Control preimage not unique in {rel}: {old!r}")
        p.write_text(txt.replace(old, new, 1), encoding="utf-8")

    def source_check(sb: Path) -> dict:
        return verify_source_and_content_parity(
            sb, manifest, baseline_root=b_root, check_generated_latex=False
        )

    def rendered(sb: Path, out: Path, gate_b_sb: dict) -> None:
        verify_evaluated_and_rendered(
            sb, typst_bin, out, gate_b_sb,
            baseline_main_pdf=baseline_main_pdf,
            baseline_manual_pdf=baseline_manual_pdf,
            baseline_root=b_root,
        )

    # 1a. Changed exact table value
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/manual/tables/sparc_summary_table.typ"
        orig = p.read_text(encoding="utf-8")
        require("10893.83" in orig, "Control 1a preimage missing")
        p.write_text(orig.replace("10893.83", "10893.84", 1), encoding="utf-8")
        expect_rejection("1a_changed_table_value", lambda: source_check(sb))

    # 1b. Changed labeled-equation exponent
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/sections/03_afc_basis.typ"
        orig = p.read_text(encoding="utf-8")
        require("iota^2" in orig, "Control 1b preimage missing")
        p.write_text(orig.replace("iota^2", "iota^3", 1), encoding="utf-8")
        expect_rejection("1b_changed_equation_exponent", lambda: source_check(sb))

    # 2. Removed scientific qualification ('never')
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/sections/04_cut_running_fractal_tesseract.typ"
        orig = p.read_text(encoding="utf-8")
        require("never" in orig, "Control 2 preimage missing")
        p.write_text(orig.replace("never", "", 1), encoding="utf-8")
        expect_rejection("2_removed_qualification", lambda: source_check(sb))

    # 3. Omitted active immutable table
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/manual/sections/06_field_dynamics_applications.typ"
        orig = p.read_text(encoding="utf-8")
        require('#include "../tables/sparc_summary_table.typ"' in orig, "Control 3 preimage missing")
        p.write_text(
            orig.replace('#include "../tables/sparc_summary_table.typ"', "", 1),
            encoding="utf-8",
        )
        expect_rejection("3_omitted_active_table", lambda: source_check(sb))

    # 4. Wrong Main reference target type (mainequation pointing to a section)
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        p = sb / "typst/manual/sections/02_mapping_error.typ"
        orig = p.read_text(encoding="utf-8")
        require('#mainsection("main:sec:m3-maps")' in orig, "Control 4 preimage missing")
        p.write_text(
            orig.replace(
                '#mainsection("main:sec:m3-maps")',
                '#mainequation("main:sec:m3-maps")',
                1,
            ),
            encoding="utf-8",
        )
        builder = load_module(root, "aod_build_typst", "scripts/build_typst.py")
        main_digest, _ = builder.compute_main_sources_digest(sb)
        expect_rejection(
            "4_wrong_reference_target_type",
            lambda: builder.compile_doc(
                typst_bin, sb, sb / "typst/manual/main.typ", Path(td) / "bad.pdf",
                inputs={"expected_main_digest": main_digest, "expected_main_pdf_filename": "main.pdf"},
            ),
        )

    # 5. Stale Main registry consumed by Manual
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        p = sb / "typst/sections/01_abstract.typ"
        p.write_text(p.read_text(encoding="utf-8") + "\n// stale-registry-control\n", encoding="utf-8")
        builder = load_module(root, "aod_build_typst", "scripts/build_typst.py")
        live_digest, _ = builder.compute_main_sources_digest(sb)
        expect_rejection(
            "5_stale_main_registry",
            lambda: builder.compile_doc(
                typst_bin, sb, sb / "typst/manual/main.typ", Path(td) / "stale.pdf",
                inputs={"expected_main_digest": live_digest, "expected_main_pdf_filename": "main.pdf"},
            ),
        )

    # 6. Review Counterexample #1: Removed short negation ('no' -> 'a')
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/manual/sections/02_mapping_error.typ"
        orig = p.read_text(encoding="utf-8")
        require("because these examples supply no physical\ndiscrepancy model" in orig, "Control 6 preimage missing")
        p.write_text(orig.replace("because these examples supply no physical\ndiscrepancy model",
                                  "because these examples supply a physical\ndiscrepancy model", 1), encoding="utf-8")
        expect_rejection("6_removed_short_negation", lambda: source_check(sb))

    # 7. Review Counterexample #2: Changed inline integer (f(x)=2x -> f(x)=3x)
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/manual/sections/02_mapping_error.typ"
        orig = p.read_text(encoding="utf-8")
        require("$f(x) = 2 x$" in orig, "Control 7 preimage missing")
        p.write_text(orig.replace("$f(x) = 2 x$", "$f(x) = 3 x$", 1), encoding="utf-8")
        expect_rejection("7_changed_inline_integer", lambda: source_check(sb))

    # 8. Review Counterexample #3: Changed equation grouping (1/(1-a^2) -> 1/(1-a)^2)
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        p = sb / "typst/manual/sections/02_mapping_error.typ"
        orig = p.read_text(encoding="utf-8")
        require("bb(E)[U] = frac(1, 1 - a^2)" in orig, "Control 8 preimage missing")
        p.write_text(orig.replace("bb(E)[U] = frac(1, 1 - a^2)",
                                  "bb(E)[U] = frac(1, (1 - a)^2)", 1), encoding="utf-8")
        expect_rejection("8_changed_equation_grouping", lambda: source_check(sb))

    # 9. Review Counterexample #4: Driver #show rule changing evaluated/rendered text
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        drv = sb / "typst/manual/main.typ"
        orig = drv.read_text(encoding="utf-8")
        require("#show: aod-manual-doc\n" in orig, "Control 9 preimage missing")
        drv.write_text(
            orig.replace(
                "#show: aod-manual-doc\n",
                '#show: aod-manual-doc\n#show "no physical uncertainty model": "a physical uncertainty model"\n',
                1,
            ),
            encoding="utf-8",
        )
        gate_b_sb = source_check(sb)
        expect_rejection(
            "9_show_rule_rendered_mutation",
            lambda: rendered(sb, Path(td) / "out_show", gate_b_sb),
        )

    # 10. Review Finding #2: Wrong companion filename (wrong_main.pdf instead of main.pdf)
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        reg_p = sb / "typst/lib/main_registry.json"
        reg_data = json.loads(reg_p.read_text(encoding="utf-8"))
        reg_data["main_pdf_filename"] = "wrong_main.pdf"
        reg_p.write_text(json.dumps(reg_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        builder = load_module(root, "aod_build_typst", "scripts/build_typst.py")
        main_digest, _ = builder.compute_main_sources_digest(sb)
        expect_rejection(
            "10_wrong_peer_pdf_filename",
            lambda: builder.compile_doc(
                typst_bin, sb, sb / "typst/manual/main.typ", Path(td) / "wrong_peer.pdf",
                inputs={"expected_main_digest": main_digest, "expected_main_pdf_filename": "main.pdf"},
            ),
        )

    # --- R02 review mutations: each must be rejected by its intended gate. ---
    gate_b_clean = verify_source_and_content_parity(
        root, manifest, baseline_root=b_root, check_generated_latex=False
    )
    man_pre = "typst/manual/preamble.typ"
    man_drv = "typst/manual/main.typ"
    fixtures = "typst/manual/sections/00_awareness_fixtures.typ"

    def needs_baselines(name: str) -> None:
        results[name] = {"rejected": None, "skipped": "requires historical baseline PDFs"}

    # 11. R1c: template show rule appends an unsupported claim after every image figure.
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(sb, man_pre, "  body,\n)", "  { show figure.where(kind: image): it => { it; parbreak(); "
               "[This figure establishes a physical fifth force.]; parbreak() }; body },\n)")
        expect_rejection("11a_R1c_template_pin", lambda: verify_typst_evaluation_policy(sb, repin(sb, man_pre)),
                         "Trusted Typst template/driver changed")
        if has_baselines:
            expect_rejection("11b_R1c_rendered_insertion", lambda: rendered(sb, Path(td) / "o", gate_b_clean),
                             "'fifth(+")
        else:
            needs_baselines("11b_R1c_rendered_insertion")

    # 12. R2b: template show rule flips the rendered minus sign in display math.
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(sb, man_pre, "  body,\n)", '  { show math.equation.where(block: true): it => '
               '{ show "\u2212": "+"; it }; body },\n)')
        expect_rejection("12a_R2b_template_pin", lambda: verify_typst_evaluation_policy(sb, repin(sb, man_pre)),
                         "Trusted Typst template/driver changed")
        if has_baselines:
            expect_rejection("12b_R2b_rendered_glyph_parity", lambda: rendered(sb, Path(td) / "o", gate_b_clean),
                             "Rendered glyph '+'")
        else:
            needs_baselines("12b_R2b_rendered_glyph_parity")

    # 13. R3: show rule inside an immutable table changes a rendered integer (digest re-pinned).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        tbl = "typst/manual/tables/swells_k0_target_tallies_table.typ"
        mutate(sb, tbl, "  set par(justify: false)\n", '  set par(justify: false)\n  show "19": "91"\n')
        expect_rejection("13_R3_table_show_rule_policy",
                         lambda: verify_typst_evaluation_policy(sb, repin(sb, tbl)), "forbidden `show`")

    # 14. R4: two Higgs figure bindings swapped (captions unchanged).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        rel = "typst/manual/sections/01_rest_energy_prediction.typ"
        a_img = "../../lib/figures/manual/higgs_yro_saddle_signature.typ"
        b_img = "../../lib/figures/manual/higgs_tritrioseptyro_trace_flow.typ"
        p = sb / rel
        txt = p.read_text(encoding="utf-8")
        require(txt.count(a_img) == 1 and txt.count(b_img) == 1, "Control 14 preimage missing")
        p.write_text(txt.replace(a_img, "@@A@@").replace(b_img, a_img).replace("@@A@@", b_img), encoding="utf-8")
        expect_rejection("14_R4_figure_image_swap", lambda: source_check(sb),
                         "('IMG', 'manual/figures/higgs/")

    # 15. R5: negation painted white (content-file policy; driver variant via PDF paint scan).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, fixtures, "with no physical uncertainty model.",
               "with #text(fill: white)[no] physical uncertainty model.")
        expect_rejection("15a_R5_white_text_policy",
                         lambda: verify_typst_evaluation_policy(sb, repin(sb, fixtures)),
                         "forbidden styling argument(s) ['fill']")
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(sb, man_drv, "#show: aod-manual-doc\n",
               '#show: aod-manual-doc\n#show "no physical uncertainty model": it => text(fill: white, it)\n')
        expect_rejection("15b_R5_white_text_paint_scan", lambda: rendered(sb, Path(td) / "o", gate_b_clean),
                         "is not opaque black/visible")

    # 16. R6: show rule negates a clause (content-file policy; driver variant via rendered clauses).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, fixtures, "with no physical uncertainty model.",
               '#show "no physical uncertainty model": "a physical uncertainty model"\n'
               "with no physical uncertainty model.")
        expect_rejection("16a_R6_content_show_policy",
                         lambda: verify_typst_evaluation_policy(sb, repin(sb, fixtures)), "forbidden `show`")
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(sb, man_drv, "#show: aod-manual-doc\n",
               '#show: aod-manual-doc\n#show "invalidates replay": "validates replay"\n')
        if has_baselines:
            expect_rejection("16b_R6_rendered_clause", lambda: rendered(sb, Path(td) / "o", gate_b_clean),
                             "Rendered prose mismatch")
        else:
            needs_baselines("16b_R6_rendered_clause")

    # 17. R03 F1: nested display equation inside boxed math creates a spurious equation number.
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        shed = "typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ"
        mutate(
            sb, shed,
            '#aod-boxed($ display(T^(times)_k - T^0_k = C^(times)_k .) $)',
            '#math.equation(block: true, numbering: none, $ #box(stroke: 0.5pt + black, inset: 4pt)[$ T^(times)_k - T^0_k = C^(times)_k . $] $)',
        )
        expect_rejection(
            "17_spurious_boxed_eq_number",
            lambda: rendered(sb, Path(td) / "o", gate_b_clean),
            "unintended unlabeled numbered block equation(s)",
        )

    # 18. Symbol fidelity: empty set ∅ replaced by diameter sign ⌀ (`diameter`).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        aware = "typst/sections/08_awareness_learning_mindfulness.typ"
        p = sb / aware
        orig = p.read_text(encoding="utf-8")
        require("emptyset" in orig, "Control 18 preimage missing")
        p.write_text(orig.replace("emptyset", "diameter", 1), encoding="utf-8")
        expect_rejection(
            "18_symbol_emptyset_to_diameter",
            lambda: source_check(sb),
            "typ=['diameter']",
        )

    # 19. Matrix fidelity: removal of vertical augment bar (`augment: #1`) in Appendix A array.
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        appa = "typst/manual/appendices/A_simulation_fixtures_and_tau_prediction_context.typ"
        mutate(sb, appa, "mat(delim: #none, augment: #1, align: #left,", "mat(delim: #none, align: #left,")
        expect_rejection(
            "19_matrix_augment_removed",
            lambda: source_check(sb),
            "Ordered content/math parity mismatch",
        )

    # 20. Flowchart fidelity & bounds (R03 F2): edge reversal, node math edit, out-of-bounds overlay
    #     applied directly to the shared diagram component typst/lib/diagrams/hydrogen_shell_setup.typ.
    h2 = "typst/lib/diagrams/hydrogen_shell_setup.typ"
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, h2, '(from: "scope", to: "shells")', '(from: "shells", to: "scope")')
        expect_rejection(
            "20a_flowchart_edge_reversed",
            lambda: source_check(sb),
            "'FLOWCHART'",
        )
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, h2, "-1 slash n^2", "-2 slash n^2")
        expect_rejection(
            "20b_flowchart_math_mutated",
            lambda: source_check(sb),
            "'FLOWCHART'",
        )
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, h2, '(id: "scope", x: 7.1cm, y: 0.7cm,', '(id: "scope", x: 7.1cm, y: 12.0cm,')
        expect_rejection(
            "20c_flowchart_out_of_bounds_overlay",
            lambda: verify_typst_evaluation_policy(sb, repin(sb, h2)),
            "exceeds flowchart bounds",
        )

    # 21. R03 F3: argument spread bypass (Gate A2) & transparent black luma(0, 0%) /ca=0 (Gate C).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(
            sb, fixtures,
            "with no physical uncertainty model.",
            "with #block(..(clip: true, height: 0pt))[no] physical uncertainty model.",
        )
        expect_rejection(
            "21a_spread_hidden_block_policy",
            lambda: verify_typst_evaluation_policy(sb, repin(sb, fixtures)),
            "argument spread `..`",
        )
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(
            sb, man_drv,
            "#show: aod-manual-doc\n",
            '#show: aod-manual-doc\n#show "no physical uncertainty model": it => text(fill: luma(0, 0%), it)\n',
        )
        expect_rejection(
            "21b_transparent_luma_paint_scan",
            lambda: rendered(sb, Path(td) / "o", gate_b_clean),
            "ca=0.0",
        )

    # --- Phase 2 bounded repair controls (R1, R2, R3, R5, R6) ---
    def make_gate_a_sandbox(tmp: Path) -> Path:
        sb = tmp / "ga_repo"
        shutil.copytree(
            root,
            sb,
            ignore=shutil.ignore_patterns(".git", "dist_typst", "_build", "__pycache__", "latex"),
        )
        return sb

    # 22a. R1: actual historical 98ddfa0 old_sha256 in representation ledger for build_release_bundle.py
    hist_release_builder_sha = "571fd0aa967e6835005ae5681ffd01e1aadd3fb5edcb30abe243c4775822fe7b"
    if (root / ".git").exists():
        chk_hist = subprocess.run(
            ["git", "rev-parse", "--verify", f"{SCIENTIFIC_BASELINE_COMMIT}^{{commit}}"],
            cwd=root, capture_output=True, text=True,
        )
        if chk_hist.returncode == 0:
            raw_hist = subprocess.run(
                ["git", "show", f"{SCIENTIFIC_BASELINE_COMMIT}:scripts/build_release_bundle.py"],
                cwd=root, capture_output=True, check=True,
            ).stdout
            require(
                hashlib.sha256(raw_hist).hexdigest() == hist_release_builder_sha,
                "Control 22a fixture literal no longer matches 98ddfa0 scripts/build_release_bundle.py",
            )
    with tempfile.TemporaryDirectory() as td:
        sb = make_gate_a_sandbox(Path(td))
        lp = sb / "typst/representation_change_ledger.json"
        ldata = json.loads(lp.read_text(encoding="utf-8"))
        for rec in ldata["frozen_sha256_amendments"]:
            if rec["path"] == "scripts/build_release_bundle.py":
                rec["old_sha256"] = hist_release_builder_sha
        lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
        expect_rejection(
            "22a_R1_ledger_historical_old_hash",
            lambda: verify_baseline_immutability(sb, manifest, baseline_root=b_root),
            "disagrees with accepted Phase 1",
        )

    # 22b. R1: duplicate entry in representation ledger
    with tempfile.TemporaryDirectory() as td:
        sb = make_gate_a_sandbox(Path(td))
        lp = sb / "typst/representation_change_ledger.json"
        ldata = json.loads(lp.read_text(encoding="utf-8"))
        ldata["frozen_sha256_amendments"].append(dict(ldata["frozen_sha256_amendments"][0]))
        lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
        expect_rejection(
            "22b_R1_ledger_duplicate_entry",
            lambda: verify_baseline_immutability(sb, manifest, baseline_root=b_root),
            "Duplicate entry in representation ledger",
        )

    # 22c. R1: substituted declared Phase 1 origin commit
    with tempfile.TemporaryDirectory() as td:
        sb = make_gate_a_sandbox(Path(td))
        lp = sb / "typst/representation_change_ledger.json"
        ldata = json.loads(lp.read_text(encoding="utf-8"))
        ldata["phase1_accepted_commit"] = SCIENTIFIC_BASELINE_COMMIT
        lp.write_text(json.dumps(ldata, indent=2) + "\n", encoding="utf-8")
        expect_rejection(
            "22c_R1_ledger_substituted_origin",
            lambda: verify_baseline_immutability(sb, manifest, baseline_root=b_root),
            "phase1_accepted_commit mismatch",
        )

    # 22d. R1: undeclared transition of an untouched scientific contract
    with tempfile.TemporaryDirectory() as td:
        sb = make_gate_a_sandbox(Path(td))
        cp = sb / "contracts/scientific/ERROR_BUDGET.json"
        cp.write_text(cp.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        expect_rejection(
            "22d_R1_undeclared_contract_transition",
            lambda: verify_baseline_immutability(sb, manifest, baseline_root=b_root),
            "Undeclared contract transition outside representation ledger",
        )

    # 23a & 23b. R2 & R3: generated LaTeX spacing boundary glue & stripped bookmark heading
    if (root / "latex/GENERATION_MANIFEST.json").is_file():
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=True)
            shutil.copytree(root / "latex", sb / "latex", dirs_exist_ok=True)
            mutate(
                sb, "latex/sections/05_curl_closure_duon_current.tex",
                r"\mathrm{Duon}\ \text{has the support of }",
                r"\mathrm{Duon}\text{has the support of }",
            )
            expect_rejection(
                "23a_R2_generated_boundary_glued",
                lambda: verify_source_and_content_parity(
                    sb, manifest, baseline_root=b_root, check_generated_latex=True, typst_bin=typst_bin
                ),
                "Generated LaTeX boundary regression",
            )
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=True)
            shutil.copytree(root / "latex", sb / "latex", dirs_exist_ok=True)
            mutate(
                sb, "latex/sections/06_field.tex",
                r"\subsubsection{E2\texorpdfstring{$^{\pm}$}{±} duad}",
                r"\subsubsection{E2$^{\pm}$ duad}",
            )
            expect_rejection(
                "23b_R3_generated_bookmark_stripped",
                lambda: verify_source_and_content_parity(
                    sb, manifest, baseline_root=b_root, check_generated_latex=True, typst_bin=typst_bin
                ),
                "Generated LaTeX bookmark regression",
            )

    # 24a & 24b. S1b: forbidden show rule or unauthorized CSV read inside native vector figure component.
    vf = "typst/lib/figures/manual/higgs_mass_comparison.typ"
    if (root / vf).is_file():
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=False)
            mutate(sb, vf, "#aod-canvas(", '#show "124.928": "125.000"\n#aod-canvas(')
            expect_rejection(
                "24a_S1b_vector_figure_show_rule",
                lambda: verify_typst_evaluation_policy(sb, repin(sb, vf)),
                "forbidden `show` rule in vector figure component",
            )
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=False)
            mutate(
                sb, vf,
                'csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv"',
                'csv("/manual/data/derived/tau_ring_diagnostic.csv"',
            )
            expect_rejection(
                "24b_S1b_vector_figure_unauthorized_csv",
                lambda: verify_typst_evaluation_policy(sb, repin(sb, vf)),
                "unauthorized csv(",
            )
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=False)
            mutate(
                sb, vf,
                '#let rows = csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv", row-type: dictionary)',
                '#let p = "/manual/data/derived/tau_ring_diagnostic.csv"\n#let rows = csv(p, row-type: dictionary)',
            )
            expect_rejection(
                "24c_S1b_vector_figure_dynamic_csv",
                lambda: verify_typst_evaluation_policy(sb, repin(sb, vf)),
                "dynamic or non-literal csv(",
            )
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=False)
            mutate(
                sb, vf,
                '#import "/typst/lib/aod_plots.typ": *',
                '#import "/typst/lib/aod_plots.typ": *\n#import "/typst/lib/aod_schema.typ": aod-boxed',
            )
            expect_rejection(
                "24d_S1b_vector_figure_nonwildcard_import",
                lambda: verify_typst_evaluation_policy(sb, repin(sb, vf)),
                "may only contain the single `#import",
            )
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=False)
            mutate(
                sb, vf,
                '#let rows = csv("/manual/data/higgs/higgs_external_lhc_mass_comparison_after_freeze.csv", row-type: dictionary)',
                '#let r = csv\n#let rows = r("/manual/data/derived/tau_ring_diagnostic.csv", row-type: dictionary)',
            )
            expect_rejection(
                "24e_S1b_vector_figure_alias_csv_and_read",
                lambda: verify_typst_evaluation_policy(sb, repin(sb, vf)),
                "aliasing or non-direct reference to `csv`",
            )
        with tempfile.TemporaryDirectory() as td:
            sb = make_sandbox(Path(td), include_figures=False)
            mutate(
                sb, vf,
                "#aod-canvas(",
                "#[ok]#set text(fill: white)\n#aod-canvas(",
            )
            expect_rejection(
                "24f_S1b_vector_figure_bracket_import_and_set",
                lambda: verify_typst_evaluation_policy(sb, repin(sb, vf)),
                "forbidden `set` rule",
            )
        with tempfile.TemporaryDirectory() as td:
            from pypdf import PdfWriter
            from pypdf.generic import DictionaryObject, NameObject, NumberObject, StreamObject

            require(
                _pure_vector_surfaces(root, manifest) == {"main", "manual"},
                f"Expected pure-vector raster enforcement on both main and manual, got {_pure_vector_surfaces(root, manifest)!r}",
            )
            bad_pdf = Path(td) / "synthetic_raster.pdf"
            w_ras = PdfWriter()
            pg = w_ras.add_blank_page(width=100, height=100)
            img = StreamObject()
            img[NameObject("/Type")] = NameObject("/XObject")
            img[NameObject("/Subtype")] = NameObject("/Image")
            img[NameObject("/Width")] = NumberObject(1)
            img[NameObject("/Height")] = NumberObject(1)
            img[NameObject("/ColorSpace")] = NameObject("/DeviceGray")
            img[NameObject("/BitsPerComponent")] = NumberObject(8)
            img._data = b"\x00"
            img_ref = w_ras._add_object(img)
            pg[NameObject("/Resources")] = DictionaryObject({
                NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): img_ref}),
            })
            with bad_pdf.open("wb") as fh:
                w_ras.write(fh)
            expect_rejection(
                "24g_S1b_pdf_raster_xobject_injection",
                lambda: _require_zero_pdf_rasters(bad_pdf, "synthetic_raster.pdf"),
                "raster_image_xobjects=1",
            )
        with tempfile.TemporaryDirectory() as td:
            from pypdf import PdfReader, PdfWriter
            from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject

            inline_payload = (
                b"\nq\n18 0 0 18 72 36 cm\nBI\n/W 2 /H 2 /CS /RGB /BPC 8\nID\n"
                + b"\xff\x00\x00\x00\xff\x00\x00\x00\xff\xff\xff\x00"
                + b"\nEI\nQ\n"
            )
            # Clone a real exported vector figure PDF (when present) and append a visible 2x2 RGB inline bitmap
            fig_src = root / "latex/figures/generated/cycle-disturbance-shedding.pdf"
            bad_inline_pdf = Path(td) / "inline_raster_figure.pdf"
            w_inl = PdfWriter()
            if fig_src.is_file():
                w_inl.clone_document_from_reader(PdfReader(str(fig_src)))
                pg_i = w_inl.pages[0]
                inl_stream = DecodedStreamObject()
                inl_stream.set_data(inline_payload)
                inl_ref = w_inl._add_object(inl_stream)
                existing_c = pg_i.get("/Contents")
                if existing_c is None:
                    pg_i[NameObject("/Contents")] = inl_ref
                elif isinstance(existing_c.get_object(), ArrayObject):
                    existing_c.get_object().append(inl_ref)
                else:
                    pg_i[NameObject("/Contents")] = ArrayObject([existing_c, inl_ref])
            else:
                pg_i = w_inl.add_blank_page(width=200, height=200)
                inl_stream = DecodedStreamObject()
                inl_stream.set_data(inline_payload)
                pg_i[NameObject("/Contents")] = w_inl._add_object(inl_stream)
            with bad_inline_pdf.open("wb") as fh:
                w_inl.write(fh)
            # Also verify a nested /Form XObject containing an inline BI/ID/EI bitmap fails closed
            nested_inline_pdf = Path(td) / "nested_form_inline_raster.pdf"
            w_nf = PdfWriter()
            pg_nf = w_nf.add_blank_page(width=200, height=200)
            fm_inl = DecodedStreamObject()
            fm_inl[NameObject("/Type")] = NameObject("/XObject")
            fm_inl[NameObject("/Subtype")] = NameObject("/Form")
            fm_inl.set_data(inline_payload)
            pg_nf[NameObject("/Resources")] = DictionaryObject({
                NameObject("/XObject"): DictionaryObject({NameObject("/FmInl"): w_nf._add_object(fm_inl)}),
            })
            with nested_inline_pdf.open("wb") as fh:
                w_nf.write(fh)
            nested_rejected = False
            try:
                _require_zero_pdf_rasters(nested_inline_pdf, "nested_form_inline_raster.pdf")
            except ValueError as exc:
                nested_rejected = "inline_raster_images=1" in str(exc)
            require(nested_rejected, "Control 24h precheck failed: nested Form inline image was not rejected")
            expect_rejection(
                "24h_S1b_pdf_inline_raster_image_injection",
                lambda: _require_zero_pdf_rasters(bad_inline_pdf, "inline_raster_figure.pdf"),
                "inline_raster_images=1",
            )
        with tempfile.TemporaryDirectory() as td:
            from pypdf import PdfWriter
            from pypdf.generic import DecodedStreamObject, NameObject

            malformed_pdf = Path(td) / "malformed_stream.pdf"
            w_mal = PdfWriter()
            pg_m = w_mal.add_blank_page(width=100, height=100)
            bad_s = DecodedStreamObject()
            bad_s.set_data(b"q BI /W 2 /H 2 /CS /RGB /BPC 8 ID \xff\x00\x00")
            pg_m[NameObject("/Contents")] = w_mal._add_object(bad_s)
            with malformed_pdf.open("wb") as fh:
                w_mal.write(fh)
            expect_rejection(
                "24i_S1b_pdf_malformed_content_stream",
                lambda: _require_zero_pdf_rasters(malformed_pdf, "malformed_stream.pdf"),
                "Uninspectable or malformed PDF content stream",
            )
        fig9_rel = "typst/lib/figures/main/cycle_disturbance_shedding.typ"
        if (root / fig9_rel).is_file():
            with tempfile.TemporaryDirectory() as td:
                sb = make_sandbox(Path(td), include_figures=False)
                mutate(sb, fig9_rel, "P_W^S (partial F, omega)", "P_W^S(partial F, omega)")
                expect_rejection(
                    "24j_S1b_figure9_superscript_attachment",
                    lambda: _verify_figure9_math_attachment(typst_bin, sb, fig9_rel),
                    "Figure 9 formula superscript attachment defect",
                )

    # 24. R5: missing sibling peer /GoToR /D destination (__AOD_REVIEW_MISSING_DESTINATION__)
    with tempfile.TemporaryDirectory() as td:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

        td_p = Path(td)
        pair_main = generated_latex_main_pdf or baseline_main_pdf
        pair_manual = generated_latex_manual_pdf or baseline_manual_pdf
        if pair_main is not None and pair_manual is not None and pair_main.is_file() and pair_manual.is_file():
            w = PdfWriter()
            w.clone_document_from_reader(PdfReader(str(pair_manual)))
            mutated_dest = False
            for pg in w.pages:
                for an in (pg.get("/Annots") or []):
                    ao = an.get_object().get("/A")
                    if ao:
                        ao = ao.get_object()
                        if str(ao.get("/S") or "") == "/GoToR" and "/D" in ao:
                            ao[NameObject("/D")] = TextStringObject("__AOD_REVIEW_MISSING_DESTINATION__")
                            mutated_dest = True
                            break
                if mutated_dest:
                    break
            require(mutated_dest, "Control 24 preimage missing: no /GoToR /D link found")
            bad_manual = td_p / "manual.pdf"
            with bad_manual.open("wb") as fh:
                w.write(fh)
            m_links = _inspect_pdf_links(pair_main, expected_peer_pdf=None)
            man_links = _inspect_pdf_links(bad_manual, expected_peer_pdf="main.pdf")
            m_pages = _pdftotext(pair_main).split("\x0c")
            if m_pages and m_pages[-1] == "":
                m_pages = m_pages[:-1]
        else:
            syn_main = td_p / "main.pdf"
            syn_manual = td_p / "manual.pdf"
            wm = PdfWriter()
            wm.add_blank_page(width=612, height=792)
            with syn_main.open("wb") as fh:
                wm.write(fh)
            wman = PdfWriter()
            pg = wman.add_blank_page(width=612, height=792)
            annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([NumberObject(10), NumberObject(10), NumberObject(50), NumberObject(20)]),
                NameObject("/A"): DictionaryObject({
                    NameObject("/S"): NameObject("/GoToR"),
                    NameObject("/F"): TextStringObject("main.pdf"),
                    NameObject("/D"): TextStringObject("__AOD_REVIEW_MISSING_DESTINATION__"),
                }),
            })
            pg[NameObject("/Annots")] = ArrayObject([annot])
            with syn_manual.open("wb") as fh:
                wman.write(fh)
            m_links = _inspect_pdf_links(syn_main, expected_peer_pdf=None)
            man_links = _inspect_pdf_links(syn_manual, expected_peer_pdf="main.pdf")
            m_pages = [""]
        expect_rejection(
            "24_R5_missing_gotor_peer_destination",
            lambda: _verify_gotor_peer_destinations(man_links, m_links, m_pages),
            "missing sibling peer /GoToR /D destination",
        )

    # 25. R6: unsupported Typst syntax reports real source file:line (not :1)
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        t_rel = "typst/sections/03_afc_basis.typ"
        t_path = sb / t_rel
        orig_txt = t_path.read_text(encoding="utf-8")
        expected_line = orig_txt.count("\n") + 2
        t_path.write_text(orig_txt + "\n#unsupported-phase2-widget(1)\n", encoding="utf-8")
        t2t = load_module(root, "aod_typ2tex_ctrl25", "scripts/typ2tex.py")
        expect_rejection(
            "25_R6_unsupported_syntax_line_number",
            lambda: t2t.generate_latex_tree(sb, Path(td) / "gen_latex", check_only=False, typst_bin=typst_bin),
            f"{t_rel}:{expected_line}",
        )

    return results


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="Verify AOD M4 Phase 2 Typst primary & generated LaTeX parity.")
    ap.add_argument("--root", default=str(ROOT), help="Repository root directory")
    ap.add_argument("--outdir", default="_build/typst_parity", help="Output directory for build & parity report")
    ap.add_argument("--typst-bin", default=None, help="Explicit path to typst binary")
    ap.add_argument("--baseline-root", default=None, help="Optional materialized 98ddfa0 historical baseline directory")
    ap.add_argument("--baseline-main-pdf", default=None, help="Historical 98ddfa0 LaTeX baseline main.pdf for direct comparison")
    ap.add_argument("--baseline-manual-pdf", default=None, help="Historical 98ddfa0 LaTeX baseline manual.pdf for direct comparison")
    ap.add_argument("--generated-latex-main-pdf", default=None, help="Generated latex/main.pdf built from typ2tex output")
    ap.add_argument("--generated-latex-manual-pdf", default=None, help="Generated latex/manual.pdf built from typ2tex output")
    ap.add_argument("--skip-negative-controls", action="store_true", help="Skip Gate D negative controls (yields non-acceptance partial verdict)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = (root / outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    builder = load_module(root, "aod_build_typst", "scripts/build_typst.py")
    typst_bin = builder.find_typst(args.typst_bin)

    manifest_path = root / "typst/manifest.json"
    require(manifest_path.is_file(), f"Missing Typst migration manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    base_root_arg = Path(args.baseline_root).resolve() if args.baseline_root else None
    base_main = Path(args.baseline_main_pdf).resolve() if args.baseline_main_pdf else None
    base_manual = Path(args.baseline_manual_pdf).resolve() if args.baseline_manual_pdf else None
    gen_main = Path(args.generated_latex_main_pdf).resolve() if args.generated_latex_main_pdf else None
    gen_manual = Path(args.generated_latex_manual_pdf).resolve() if args.generated_latex_manual_pdf else None

    b_root, tmp_base = _resolve_baseline_root(root, base_root_arg)
    try:
        gate_a = verify_baseline_immutability(root, manifest, baseline_root=b_root)
        gate_a2 = verify_typst_evaluation_policy(root, manifest)
        gate_b_raw = verify_source_and_content_parity(
            root, manifest, baseline_root=b_root, typst_bin=typst_bin
        )
        gate_c = verify_evaluated_and_rendered(
            root, typst_bin, outdir, gate_b_raw,
            baseline_main_pdf=base_main,
            baseline_manual_pdf=base_manual,
            baseline_root=b_root,
            generated_latex_main_pdf=gen_main,
            generated_latex_manual_pdf=gen_manual,
        )
        gate_d = (
            {"skipped": True}
            if args.skip_negative_controls
            else run_negative_controls(
                root, typst_bin, base_main, base_manual,
                baseline_root=b_root,
                generated_latex_main_pdf=gen_main,
                generated_latex_manual_pdf=gen_manual,
            )
        )
    finally:
        if tmp_base is not None:
            tmp_base.cleanup()

    # Strip internal scratch keys from gate_b before serializing deterministic report
    gate_b = {k: v for k, v in gate_b_raw.items() if not k.startswith("_")}

    has_baselines = bool(base_main and base_manual)
    has_gen_latex = bool(gen_main and gen_manual)
    gen_src_info = gate_b.get("generated_latex_parity", {})
    gen_src_checked = bool(gen_src_info.get("performed"))
    gen_fresh_checked = bool(gen_src_info.get("typ2tex_check_passed"))
    transition_checked = bool(gate_a.get("phase1_transition_verified"))
    all_controls_ran = not args.skip_negative_controls
    unverified_clauses = 0
    typst_only_clauses = 0
    gen_unverified_clauses = 0
    if has_baselines:
        for surf in ("main", "manual"):
            cr = gate_c["baseline_pdf_comparison"]["results"][surf]["rendered_prose_clauses"]
            unverified_clauses += cr["unverified"]
            typst_only_clauses += cr["typst_rendering_verified_only"]
        if has_gen_latex:
            for surf in ("main", "manual"):
                gcr = gate_c["generated_latex_pdf_comparison"]["results"][surf]["rendered_prose_clauses"]
                gen_unverified_clauses += gcr["unverified"]

    missing_acceptance_requirements: list[str] = []
    if not transition_checked:
        missing_acceptance_requirements.append("phase1_transition_verification")
    if not gen_src_checked:
        missing_acceptance_requirements.append("generated_latex_source_parity")
    if not gen_fresh_checked:
        missing_acceptance_requirements.append("generated_latex_freshness_check")
    if not has_baselines:
        missing_acceptance_requirements.append("baseline_pdfs")
    if not has_gen_latex:
        missing_acceptance_requirements.append("generated_latex_pdfs")
    if not all_controls_ran:
        missing_acceptance_requirements.append("negative_controls")
    if unverified_clauses or typst_only_clauses or gen_unverified_clauses:
        missing_acceptance_requirements.append("rendered_prose_clauses")

    if not transition_checked:
        verdict = "PARTIAL_NON_ACCEPTANCE_MISSING_TRANSITION_CHECK"
    elif not gen_src_checked or not gen_fresh_checked:
        verdict = "PARTIAL_NON_ACCEPTANCE_MISSING_GENERATED_SOURCE_FRESHNESS"
    elif not has_baselines:
        verdict = "PARTIAL_NON_ACCEPTANCE_MISSING_BASELINE_PDFS"
    elif not has_gen_latex:
        verdict = "PARTIAL_NON_ACCEPTANCE_MISSING_GENERATED_LATEX_PDFS"
    elif not all_controls_ran:
        verdict = "PARTIAL_NON_ACCEPTANCE_SKIPPED_CONTROLS"
    elif unverified_clauses or typst_only_clauses or gen_unverified_clauses:
        verdict = "PARTIAL_NON_ACCEPTANCE_UNVERIFIED_CLAUSES"
    else:
        verdict = "PASS"

    if verdict == "PASS":
        typ2tex_status = "VERIFIED_COMPLETE_PHASE_2"
    elif has_gen_latex and gen_src_checked and gen_fresh_checked:
        typ2tex_status = "PARTIAL_GENERATED_PDFS_CHECKED_INCOMPLETE_ACCEPTANCE"
    elif gen_src_checked:
        typ2tex_status = "PARTIAL_SOURCE_ONLY_GENERATED_PDFS_NOT_VERIFIED"
    else:
        typ2tex_status = "UNVERIFIED"

    controls_executed = 0 if args.skip_negative_controls else sum(
        1 for v in gate_d.values() if v.get("rejected") is True
    )

    report = {
        "schema": "aod.typst.parity-report.v2",
        "scientific_baseline_commit": SCIENTIFIC_BASELINE_COMMIT,
        "phase1_accepted_commit": PHASE1_ACCEPTED_COMMIT,
        "verifier_sha256": sha256_file(Path(__file__).resolve()),
        "gate_a_baseline_immutability": gate_a,
        "gate_a2_typst_evaluation_policy": gate_a2,
        "gate_b_scientific_content_parity": gate_b,
        "gate_c_evaluated_and_rendered": gate_c,
        "gate_d_negative_controls": gate_d,
        "coverage": {
            "native": {
                "ordered_prose_and_short_words": True,
                "all_inline_and_display_math_ast": True,
                "matrix_delimiters_and_augment_bars": True,
                "bar_vs_overline_and_upright_bold": True,
                "flowcharts_nodes_and_edges_verified": gate_b["flowcharts_verified"],
                "exact_equation_numbering_and_block_count": True,
                "unsupported_math_constructs": gate_b["unsupported_math_constructs"],
                "immutable_tables_cell_by_cell": True,
                "delivered_peer_pdf_links_and_landings": True,
                "clickable_external_uris_vs_baseline_pdf": has_baselines,
                "inline_citation_sequence_vs_baseline_pdf": has_baselines,
                "rendered_bib_case_sensitive": has_baselines,
                "rendered_prose_clauses_vs_baseline_pdf": has_baselines,
                "rendered_prose_clauses_unverified": (
                    unverified_clauses + typst_only_clauses
                ) if has_baselines else "NOT_ASSESSED_WITHOUT_BASELINE",
                "rendered_insertion_ngrams_vs_baseline_pdf": has_baselines,
                "rendered_relation_glyph_parity_vs_baseline_pdf": has_baselines,
                "rendered_minus_equals_membership_glyphs": "SOURCE_MATH_AST_AND_EVALUATION_POLICY_ONLY",
                "rendered_text_paint_scan_alpha_and_clip": True,
                "typst_evaluation_policy_and_template_pins": True,
                "figure_image_bindings_to_protected_digests": gate_b["figure_image_bindings_verified"],
                "figure_pixels_visual_comparison": "NOT_PERFORMED_BOUND_BY_PROTECTED_DIGEST",
                "overlay_primitives": "FORBIDDEN_BY_POLICY_NOT_DETECTED_IN_PDF",
            },
            "generated_latex": {
                "source_tree_verified": gen_src_checked,
                "source_freshness_check_passed": gen_fresh_checked,
                "spacing_unit_boundaries_source_verified": bool(gen_src_info.get("spacing_unit_boundaries_verified")),
                "pdfs_supplied_and_verified": has_gen_latex,
                "pdfs_verified_vs_baseline": has_baselines and has_gen_latex,
                "local_destinations_verified": has_gen_latex,
                "sibling_peer_gotor_destinations_and_landings_verified": has_gen_latex,
                "pdf_outlines_and_math_bookmarks_verified": has_gen_latex,
                "rendered_spacing_unit_boundaries_verified": has_gen_latex,
                "rendered_prose_clauses_unverified": (
                    gen_unverified_clauses
                    if (has_baselines and has_gen_latex)
                    else "NOT_ASSESSED_WITHOUT_BASELINE_AND_GENERATED_PDFS"
                ),
            },
            "provenance_and_controls": {
                "historical_baseline_preservation_verified": bool(gate_a.get("historical_baseline_preservation_verified")),
                "phase1_transition_verified": transition_checked,
                "negative_controls_executed": controls_executed,
                "human_visual_layout_review": "SEPARATE_RECORDED_OUTSIDE_AUTOMATED_SCRIPT",
            },
            "missing_acceptance_requirements": missing_acceptance_requirements,
        },
        "typ2tex_compatibility_status": typ2tex_status,
        "canonical_source_promotion": (
            "TYPST_PRIMARY_LATEX_GENERATED_COMPATIBILITY_ACCEPTED"
            if verdict == "PASS"
            else "PARTIAL_NOT_ACCEPTED"
        ),
        "verdict": verdict,
    }
    report_path = outdir / "parity_report.json"
    report_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    report_path.write_text(report_text, encoding="utf-8")
    print(report_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
