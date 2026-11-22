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
import zlib

ROOT = Path(__file__).resolve().parents[1]

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
    """Read a balanced group; for Typst `(...)` calls, ignore delimiters inside `"..."` and `$...$`."""
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
        if op == "(" and not in_str and s[i] == "$":
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


def _extract_typst_flowchart(paren_arg: str, fname: str) -> tuple[tuple, list[str]]:
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
        ntoks, nunsup = extract_typst_ordered(b_raw[1:-1], fname)
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
                    clean_code = arg.replace(r"\_", "_").replace(r"\-", "-").replace(r"\%", "%").strip()
                    tokens.append(("CODE", clean_code))
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
                        tokens.append(("CODE", m_tt.group(1).replace(r"\_", "_")))
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


def extract_typst_ordered(typ_raw: str, fname: str = "") -> tuple[list[tuple], list[str]]:
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

                    if name == "raw" and paren_arg is not None:
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
                        fc_tok, fc_unsup = _extract_typst_flowchart(paren_arg, fname)
                        tokens.append(fc_tok)
                        unsup_math.extend(fc_unsup)
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
                                "aod-uncaptioned-longtable", "pad", "align", "emph", "strong",
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


def _inline_typst_diagram_includes(root: Path, typ_rel: str, text: str) -> str:
    """Expand `#include "../../lib/diagrams/<mod>.typ"` for flowchart AST parity verification."""
    base_dir = posixpath.dirname(typ_rel)

    def _repl(m: re.Match) -> str:
        rel_inc = m.group(1)
        resolved = posixpath.normpath(posixpath.join(base_dir, rel_inc))
        if not resolved.startswith("typst/lib/diagrams/") or not resolved.endswith(".typ"):
            return m.group(0)
        p = root / resolved
        require(p.is_file(), f"Missing included shared Typst diagram component: {resolved} (from {typ_rel})")
        body = p.read_text(encoding="utf-8")
        # Strip the component's standalone schema import when inlining inside a section file.
        body = re.sub(r'^\s*#import\s+"[^"]+"\s*:\s*\*\s*\n?', "", body, flags=re.M)
        return body

    return re.sub(r'#include\s+"([^"]+)"', _repl, text)


# =============================================================================
# Gate A: Baseline Immutability (Archived 98ddfa0 Snapshot + Representation Ledger)
# =============================================================================

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
            if entry["role"] == "archived_editorial_tex":
                archived_rel_map[orig] = entry["retained_location"]
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

    git_checked = False
    ledger_checked = False
    ledger_frozen_amendments: list[str] = []
    if (root / ".git").exists():
        chk = subprocess.run(
            ["git", "rev-parse", "--verify", f"{SCIENTIFIC_BASELINE_COMMIT}^{{commit}}"],
            cwd=root, capture_output=True, text=True,
        )
        if chk.returncode == 0:
            git_checked = True
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

            base_cb = json.loads(subprocess.run(
                ["git", "show", f"{SCIENTIFIC_BASELINE_COMMIT}:contracts/scientific/CANONICAL_BINDINGS.json"],
                cwd=root, capture_output=True, text=True, check=True,
            ).stdout)
            curr_cb = json.loads((root / "contracts/scientific/CANONICAL_BINDINGS.json").read_text(encoding="utf-8"))
            tex_to_typ = {e["tex_source"]: e["typst_target"] for e in manifest["active_source_map"]}

            # Scientific substance in CANONICAL_BINDINGS.json MUST be 100% invariant (paths only may remap)
            require(curr_cb.get("schema") == base_cb["schema"], "CANONICAL_BINDINGS.json schema changed")
            require(curr_cb.get("formulas") == base_cb["formulas"],
                    "Scientific formulas in CANONICAL_BINDINGS.json changed")
            require(len(curr_cb.get("ownership", [])) == len(base_cb["ownership"]),
                    "Ownership group count changed in CANONICAL_BINDINGS.json")
            for b_row, c_row in zip(base_cb["ownership"], curr_cb["ownership"]):
                exp_row = dict(b_row)
                if c_row.get("path") != b_row["path"]:
                    exp_row["path"] = tex_to_typ.get(b_row["path"], b_row["path"])
                require(c_row == exp_row, f"Ownership scientific content changed for {b_row.get('concept')}")
            for b_fam, c_fam in zip(base_cb["manual_families"], curr_cb["manual_families"]):
                exp_fam = dict(b_fam)
                if c_fam.get("manual_path") != b_fam["manual_path"]:
                    exp_fam["manual_path"] = tex_to_typ.get(b_fam["manual_path"], b_fam["manual_path"])
                require(c_fam == exp_fam, f"Manual family scientific content changed for {b_fam.get('id')}")
            for b_sig, c_sig in zip(base_cb["unique_signatures"], curr_cb["unique_signatures"]):
                exp_sig = dict(b_sig)
                if c_sig.get("path") != b_sig["path"]:
                    exp_sig["path"] = tex_to_typ.get(b_sig["path"], b_sig["path"])
                require(c_sig == exp_sig, f"Unique signature scientific content changed for {b_sig.get('anchor')}")
            require(set(curr_cb.get("supplemental_formulas", {})) == set(base_cb["supplemental_formulas"]),
                    "Supplemental formula keys changed in CANONICAL_BINDINGS.json")
            for k, b_sup in base_cb["supplemental_formulas"].items():
                c_sup = curr_cb["supplemental_formulas"][k]
                exp_sup = dict(b_sup)
                if c_sup.get("path") != b_sup["path"]:
                    exp_sup["path"] = tex_to_typ.get(b_sup["path"], b_sup["path"])
                require(c_sup == exp_sup, f"Supplemental formula content changed for {k}")

            ledger_path = root / "typst/representation_change_ledger.json"
            if ledger_path.is_file():
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                require(
                    ledger.get("schema") == "aod.m4.phase2.representation-change-ledger.v1",
                    "Invalid representation_change_ledger.json schema",
                )
                relocated = {e["old_path"]: e["new_path"] for e in ledger.get("frozen_sha256_relocations", [])}
                amended = {e["path"]: e for e in ledger.get("frozen_sha256_amendments", [])}
                added = {e["path"]: e for e in ledger.get("frozen_sha256_additions", [])}
                for old_k, old_sha in base_cb["frozen_sha256"].items():
                    if old_k in relocated:
                        new_k = relocated[old_k]
                        require(
                            curr_cb["frozen_sha256"].get(new_k) == old_sha,
                            f"Relocated frozen_sha256 entry {old_k} -> {new_k} digest mismatch",
                        )
                    elif old_k in amended:
                        require(
                            curr_cb["frozen_sha256"].get(old_k) == amended[old_k]["new_sha256"]
                            and amended[old_k]["old_sha256"] == old_sha,
                            f"Amended frozen_sha256 entry {old_k} disagrees with representation ledger",
                        )
                    else:
                        require(
                            curr_cb["frozen_sha256"].get(old_k) == old_sha,
                            f"Undeclared frozen_sha256 change outside representation ledger: {old_k}",
                        )
                expected_keys = (
                    (set(base_cb["frozen_sha256"]) - set(relocated))
                    | set(relocated.values())
                    | set(added)
                )
                require(
                    set(curr_cb["frozen_sha256"]) == expected_keys,
                    f"frozen_sha256 key set disagrees with representation ledger: "
                    f"extra={sorted(set(curr_cb['frozen_sha256']) - expected_keys)}, "
                    f"missing={sorted(expected_keys - set(curr_cb['frozen_sha256']))}",
                )
                for add_k, add_rec in added.items():
                    require(
                        curr_cb["frozen_sha256"].get(add_k) == add_rec["sha256"],
                        f"Added frozen_sha256 entry {add_k} disagrees with representation ledger",
                    )
                ledger_checked = True
                ledger_frozen_amendments = sorted(amended)
            else:
                require(set(curr_cb["frozen_sha256"]) == set(base_cb["frozen_sha256"]),
                        "frozen_sha256 key set changed in CANONICAL_BINDINGS.json")
                changed_frozen = {
                    k for k, v in base_cb["frozen_sha256"].items()
                    if curr_cb["frozen_sha256"][k] != v
                }
                require(
                    changed_frozen <= ALLOWED_ENGINEERING_FROZEN_AMENDMENTS,
                    f"Unexpected frozen_sha256 modifications outside planned engineering files: {sorted(changed_frozen)}",
                )
                ledger_frozen_amendments = sorted(changed_frozen)

    return {
        "protected_baseline_files": len(protected),
        "archived_editorial_tex_files": len(archived_rel_map),
        "preserved_in_place_files": len(inplace_paths),
        "tex_files_unchanged": tex_count,
        "bib_files_unchanged": bib_count,
        "image_files_unchanged": img_count,
        "manual_data_files_unchanged": data_count,
        "git_baseline_cross_checked": git_checked,
        "representation_change_ledger_verified": ledger_checked,
        "amended_frozen_entries_count": len(ledger_frozen_amendments),
    }


# =============================================================================
# Gate A2: Evaluation Policy (trusted template pins, manifest digests, and a
# mode-aware allowlist for every Typst content file). Typst show rules, local
# definitions, styling and overlays can change the evaluated publication without
# changing source tokens; content files may therefore only use the reviewed,
# content-neutral vocabulary below, and the files that define evaluation
# semantics are pinned byte-for-byte by this verifier.
# =============================================================================

TRUSTED_TEMPLATE_SHA256 = {
    "typst/lib/aod_schema.typ": "4e6861360657c906ab18499afd1c114b87c8521ead1df471ddc28ab8e9c44d46",
    "typst/preamble.typ": "7a9c255c2411bc4bd3487be0196f10ac453eefa240f6c16095d426f210b4f112",
    "typst/manual/preamble.typ": "2b7deae2f0fa3d7011edabd8d7299b835290fb60e47990c7fe861e55bd914196",
    "typst/main.typ": "fc8d4cb59c86b59f0a6ee6fe1b0ea968edcf00f2e84d05e2cfcfb25abf57db70",
    "typst/manual/main.typ": "c3d6a18bb6a8020481259a6771611e41c50f188190e35e1c9b5ec58848d8760a",
}

# Callable -> permitted named arguments, for code / `#`-introduced calls in content files.
CONTENT_CALL_ALLOWLIST: dict[str, frozenset] = {
    "align": frozenset(), "aod-anchor": frozenset(), "aod-boxed": frozenset(),
    "aod-cite": frozenset({"supplement"}),
    "aod-definition": frozenset({"title"}), "aod-flowchart": frozenset({"height", "width"}),
    "aod-literature-note": frozenset(), "aod-noteblock": frozenset(), "aod-panel": frozenset({"width"}),
    "aod-paragraph": frozenset(), "aod-provenance": frozenset(), "aod-remark": frozenset(),
    "aod-uncaptioned-longtable": frozenset(), "appref": frozenset(), "bare-ref": frozenset(),
    "block": frozenset({"above", "below", "width"}),
    "counter": frozenset(), "counter().update": frozenset(), "emph": frozenset(), "eqnref": frozenset(),
    "eqref": frozenset(), "figure": frozenset({"caption", "kind"}), "image": frozenset({"width"}),
    "link": frozenset(), "mainappendix": frozenset(), "mainequation": frozenset(), "mainsection": frozenset(),
    "math.equation": frozenset({"block", "numbering"}), "pad": frozenset({"left", "right"}),
    "page": frozenset({"numbering"}), "pagebreak": frozenset({"weak"}), "par": frozenset({"justify"}),
    "raw": frozenset(), "secref": frozenset(), "strong": frozenset(), "table": frozenset({"align", "columns"}),
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
CONTENT_TEXT_SIZES = frozenset({"8.5pt", "9.5pt", "10pt", "12pt", "14pt", "17pt"})
POSITIVE_LENGTH_ARGS: dict[str, frozenset] = {
    "pad": frozenset({"left", "right"}),
    "block": frozenset({"above", "below", "width"}),
    "image": frozenset({"width"}),
    "aod-panel": frozenset({"width"}),
    "aod-flowchart": frozenset({"width", "height"}),
}
FLOWCHART_NODE_KEYS = frozenset({"id", "x", "y", "w", "h", "body", "dy-in", "dy-out"})
FLOWCHART_EDGE_KEYS = frozenset({"from", "to"})

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


def _typ_balanced(s: str, i: int, op: str, cl: str) -> int:
    """Index just after the bracket matching s[i] == op (strings, raw spans and comments honoured)."""
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
                    e = _typ_balanced(text, j, "(", ")")
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


def verify_typst_evaluation_policy(root: Path, manifest: dict) -> dict:
    """Gate A2: pin evaluation-defining files and constrain every Typst content file."""
    targets = {e["typst_target"] for e in manifest["active_source_map"]}
    diagram_components: dict[str, str] = manifest.get("diagram_components", {})
    diagram_files = set(diagram_components)
    # 1. Every active Typst unit and shared diagram component matches its manifest digest.
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
    # 2. Evaluation-defining template/driver files are pinned by this verifier.
    for rel, digest in sorted(TRUSTED_TEMPLATE_SHA256.items()):
        p = root / rel
        require(p.is_file(), f"Trusted Typst template file missing: {rel}")
        require(
            sha256_file(p) == digest,
            f"Trusted Typst template/driver changed (evaluation semantics are pinned by the verifier): {rel}",
        )
    # 3. The Typst file set is exactly the manifest units + shared diagrams + pinned templates.
    on_disk = {str(p.relative_to(root)).replace(os.sep, "/") for p in (root / "typst").rglob("*.typ")}
    declared = targets | set(TRUSTED_TEMPLATE_SHA256) | diagram_files
    require(
        on_disk == declared,
        f"Undeclared or missing Typst files: extra={sorted(on_disk - declared)}, missing={sorted(declared - on_disk)}",
    )
    # 4. Mode-aware allowlist over content files and shared diagram components.
    allowed_includes = targets | diagram_files
    violations: list[str] = []
    files_checked = 0
    events_checked = 0
    for rel in sorted((targets - set(TRUSTED_TEMPLATE_SHA256)) | diagram_files):
        v_list, n_ev = _content_policy_violations(rel, (root / rel).read_text(encoding="utf-8"), allowed_includes)
        violations += v_list
        files_checked += 1
        events_checked += n_ev
    require(
        not violations,
        "Typst evaluation policy violation(s) in content files:\n  " + "\n  ".join(violations[:25]),
    )
    return {
        "trusted_template_files_pinned": len(TRUSTED_TEMPLATE_SHA256),
        "diagram_components_pinned": len(diagram_files),
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

    for tex_rel, entry in sorted(src_map.items()):
        if tex_rel in ("main.tex", "preamble.tex", "manual/main.tex", "manual/preamble.tex"):
            continue
        typ_rel = entry["typst_target"]
        tex_text = (b_root / tex_rel).read_text(encoding="utf-8")
        typ_text = _inline_typst_diagram_includes(
            root, typ_rel, (root / typ_rel).read_text(encoding="utf-8")
        )

        t_toks, t_unsup = extract_tex_ordered(tex_text, tex_rel)
        y_toks, y_unsup = extract_typst_ordered(typ_text, typ_rel)
        require(not t_unsup, f"Unsupported TeX math constructs in {tex_rel}: {sorted(set(t_unsup))}")
        require(not y_unsup, f"Unsupported Typst math constructs in {typ_rel}: {sorted(set(y_unsup))}")

        if t_toks != y_toks:
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
        total_ordered_tokens += len(t_toks)
        total_math_asts += sum(1 for tk in t_toks if tk[0] == "MATH")
        total_code_tokens += sum(1 for tk in t_toks if tk[0] == "CODE")
        total_flowcharts += sum(1 for tk in t_toks if tk[0] == "FLOWCHART")
        for tk in t_toks:
            if tk[0] == "IMG":
                require(
                    tk[1] in manifest["baseline_protected_sha256"] and (root / tk[1]).is_file(),
                    f"Figure image binding {tk[1]!r} in {typ_rel} is not a protected baseline image",
                )
                total_image_bindings += 1

        surf = entry["surface"]
        for tk in t_toks:
            if tk[0] == "W":
                lw = tk[1].lower()
                if lw in qualifier_totals:
                    qualifier_totals[lw] += 1
            elif tk[0] == "CODE" and "--" in tk[1]:
                cli_commands_by_surface[surf].append(tk[1])

        if tex_rel not in IMMUTABLE_MANUAL_TABLES:
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
    m_driver_typ, m_du_y = extract_typst_ordered((root / "typst/manual/main.typ").read_text(encoding="utf-8"), "typst/manual/main.typ")
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
        require(gen_main_labels == base_main_labels,
                f"Generated latex/ Main label set mismatch: missing={sorted(base_main_labels - gen_main_labels)}, extra={sorted(gen_main_labels - base_main_labels)}")
        require(gen_manual_labels == base_manual_labels,
                f"Generated latex/ Manual label set mismatch: missing={sorted(base_manual_labels - gen_manual_labels)}, extra={sorted(gen_manual_labels - base_manual_labels)}")

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

        fig_dir = latex_root / "manual/figures/generated"
        fig_manifest_p = fig_dir / "FIGURE_MANIFEST.json"
        require(fig_manifest_p.is_file(), "Missing latex/manual/figures/generated/FIGURE_MANIFEST.json")
        fig_manifest = json.loads(fig_manifest_p.read_text(encoding="utf-8"))
        diagrams = fig_manifest.get("figures", [])
        require(len(diagrams) == 4, f"Expected 4 exported diagrams in FIGURE_MANIFEST.json, got {len(diagrams)}")
        for d in diagrams:
            asset = fig_dir / d["output_filename"]
            require(asset.is_file() and sha256_file(asset) == d["output_sha256"],
                    f"Exported diagram digest mismatch: {asset.relative_to(root)}")

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
            "exported_diagrams_verified": len(diagrams),
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
        if re.fullmatch(r"\d+", s):
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
    t = raw_pdf_text.translate(_LATIN_LIGATURES).replace("\u00ad\n", "").replace("\u00ad", "")
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


def _inspect_pdf_links(pdf_path: Path, expected_peer_pdf: str | None = None) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    internal_links = 0
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
            elif act_obj.get("/S") == "/GoToR":
                f_obj = act_obj.get("/F")
                if hasattr(f_obj, "get_object"):
                    f_obj = f_obj.get_object()
                if isinstance(f_obj, dict):
                    target_file = str(f_obj.get("/UF") or f_obj.get("/F") or "")
                else:
                    target_file = str(f_obj or "")
                dest = str(act_obj.get("/D") or "")
                if expected_peer_pdf and target_file == expected_peer_pdf:
                    gotor_peer_links.append((page_idx, target_file, dest))
                else:
                    stale_main_pdf_links.append((page_idx, f"GoToR:{target_file}#{dest}"))
    return {
        "pages": len(reader.pages),
        "internal_links": internal_links,
        "peer_pdf_links": peer_pdf_links,
        "gotor_peer_links": gotor_peer_links,
        "stale_main_pdf_links": stale_main_pdf_links,
        "uri_links": uri_links,
        "unique_external_uris": sorted(external_uris),
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
        "Gate audit controls null", "side quarantine table Record",
    }),
}
# Out-of-source-vocabulary words (>= 4 letters) may not occur more often in the Typst body than
# in the retained baseline body, except for these exact excesses (math/table-header linearisation
# and the Typst table-of-contents 'References' entry), measured on the clean candidate.
OOV_WORD_MIN_LEN = 4
RENDERED_OOV_EXCESS_ALLOWLIST: dict[str, dict[str, int]] = {
    "main": {"Anchor": 1, "Category": 1, "Entries": 1, "References": 1, "asym": 6, "decl": 1, "prop": 1},
    "manual": {
        "Artifact": 1, "Class": 1, "Jobs": 2, "Purpose": 1, "References": 1, "Sheet": 1, "bench": 1,
        "bend": 1, "neuro": 4, "peri": 1, "spike": 2,
    },
}
MIN_RENDERED_TEXT_SIZE = 4.0


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
    require(set(typ_main_map) == tex_main_labels,
            f"Main label set mismatch: missing={sorted(tex_main_labels - set(typ_main_map))}, extra={sorted(set(typ_main_map) - tex_main_labels)}")
    require(set(typ_manual_map) == tex_manual_labels,
            f"Manual label set mismatch: missing={sorted(tex_manual_labels - set(typ_manual_map))}, extra={sorted(set(typ_manual_map) - tex_manual_labels)}")

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
    for surf, raw_txt in (("main", typ_main_raw), ("manual", typ_manual_raw)):
        flat_raw = re.sub(r"\s+", " ", raw_txt.replace("/\n", "/"))
        for cmd in sorted(set(gate_b_info["_cli_commands"][surf])):
            require(
                cmd in flat_raw,
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
            src_words = [w for _, c in gate_b_info["_prose_clauses"][surf] for w in c.split()]
            src_grams = set(_run_ngrams(_vocab_runs(src_words, vocab)))
            b_tokens = _norm_rendered_text_tokens(_rendered_body(b_stream), is_typst=False, vocab=vocab).split()
            t_tokens = _norm_rendered_text_tokens(_rendered_body(t_stream), is_typst=True).split()
            base_grams = set(_run_ngrams(_vocab_runs(b_tokens, vocab)))
            t_grams = _run_ngrams(_vocab_runs(t_tokens, vocab))
            layout_allow = RENDERED_LAYOUT_NGRAM_ALLOWLIST[surf]
            novel = [g for g in t_grams if g not in base_grams and g not in src_grams and g not in layout_allow]
            # Words outside the source vocabulary (>= 4 letters) must not exceed their baseline count.
            b_alpha = Counter(x for x in b_tokens if x.isalpha())
            for k in (2, 3):
                for i in range(len(b_tokens) - k + 1):
                    win = b_tokens[i:i + k]
                    if all(x.isalpha() for x in win):
                        b_alpha["".join(win)] += 1
            t_alpha = Counter(x for x in t_tokens if x.isalpha())
            t_math = _typst_math_word_counts(_rendered_body(t_stream))
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

            # (c3) Rendered relation/operator glyph parity against the historical baseline body.
            b_body_s, t_body_s = _rendered_body(b_stream), _rendered_body(t_stream)
            glyphs = {}
            for g in RENDERED_GLYPH_PARITY_SET:
                bcount, tcount = b_body_s.count(g), t_body_s.count(g)
                require(
                    bcount == tcount,
                    f"Rendered glyph {g!r} count differs in {surf}.pdf: base={bcount} vs typst={tcount}",
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

    # Optional: verify generated LaTeX compatibility PDFs against the historical baseline PDFs
    generated_latex_pdf_report: dict[str, object] = {"performed": False}
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
        gen_peer_total = len(gen_manual_links["peer_pdf_links"]) + len(gen_manual_links["gotor_peer_links"])
        require(
            len(gen_manual_links["stale_main_pdf_links"]) == 0,
            f"Generated LaTeX manual.pdf has wrong/stale peer links: {gen_manual_links['stale_main_pdf_links'][:5]}",
        )
        require(
            gen_peer_total >= len(manual_mainrefs_raw),
            f"Generated LaTeX manual.pdf expected >= {len(manual_mainrefs_raw)} peer links to sibling main.pdf, got {gen_peer_total}",
        )

        gen_per_doc: dict[str, dict] = {}
        for surf, g_pdf, b_pdf in (
            ("main", generated_latex_main_pdf, baseline_main_pdf),
            ("manual", generated_latex_manual_pdf, baseline_manual_pdf),
        ):
            g_raw = _pdftotext(g_pdf, raw=False)
            g_stream = _pdftotext(g_pdf, raw=True)
            require(len(g_raw.strip()) > 20000, f"Generated LaTeX {surf}.pdf text unexpectedly short")
            for forbidden in ("columns: (", "table.header(", "aod-definition", "aod-provenance", "aod-flowchart", "??"):
                require(forbidden not in g_raw, f"Leaked marker {forbidden!r} in generated LaTeX {surf}.pdf")
            g_flat_cli = re.sub(r"\s+", " ", g_raw.replace("/\n", "/"))
            for cmd in sorted(set(gate_b_info["_cli_commands"][surf])):
                require(cmd in g_flat_cli, f"CLI command missing in generated LaTeX {surf}.pdf: {cmd!r}")

            g_norm = " " + _norm_rendered_text_tokens(g_stream, is_typst=False, vocab=vocab) + " "
            g_flat = re.sub(r"\s+", " ", g_raw.replace("\xa0", " "))
            entry: dict[str, object] = {
                "pages": gen_main_links["pages"] if surf == "main" else gen_manual_links["pages"],
                "pdf_sha256": sha256_file(g_pdf),
                "pdf_bytes": g_pdf.stat().st_size,
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
                b_uris = _inspect_pdf_links(b_pdf, expected_peer_pdf=None)["unique_external_uris"]
                g_uris = (gen_main_links if surf == "main" else gen_manual_links)["unique_external_uris"]
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
            "manual_pdf_sha256": build_report["manual_pdf_sha256"],
            "manual_pdf_bytes": build_report["manual_pdf_bytes"],
        },
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
    "9_show_rule_rendered_mutation": "No physical uncertainty model is instantiated",
    "10_wrong_peer_pdf_filename": "Main companion filename mismatch",
}


def run_negative_controls(
    root: Path,
    typst_bin: str,
    baseline_main_pdf: Path | None = None,
    baseline_manual_pdf: Path | None = None,
    baseline_root: Path | None = None,
) -> dict:
    manifest = json.loads((root / "typst/manifest.json").read_text(encoding="utf-8"))
    results: dict[str, dict] = {}
    b_root, tmp_base = _resolve_baseline_root(root, baseline_root)
    try:
        return _run_negative_controls_impl(
            root, typst_bin, manifest, results, b_root, baseline_main_pdf, baseline_manual_pdf
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
        require("This example has no physical discrepancy model" in orig, "Control 6 preimage missing")
        p.write_text(orig.replace("This example has no physical discrepancy model",
                                  "This example has a physical discrepancy model", 1), encoding="utf-8")
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
                '#show: aod-manual-doc\n#show "No physical uncertainty model": "A physical uncertainty model"\n',
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
                             "'fifth(+34)'")
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

    # 14. R4: two Higgs figure image paths swapped (captions unchanged).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        rel = "typst/manual/sections/01_rest_energy_prediction.typ"
        a_img = "/manual/figures/higgs/higgs_yro_saddle_signature.png"
        b_img = "/manual/figures/higgs/higgs_tritrioseptyro_trace_flow.png"
        p = sb / rel
        txt = p.read_text(encoding="utf-8")
        require(txt.count(a_img) == 1 and txt.count(b_img) == 1, "Control 14 preimage missing")
        p.write_text(txt.replace(a_img, "@@A@@").replace(b_img, a_img).replace("@@A@@", b_img), encoding="utf-8")
        expect_rejection("14_R4_figure_image_swap", lambda: source_check(sb),
                         "('IMG', 'manual/figures/higgs/")

    # 15. R5: negation painted white (content-file policy; driver variant via PDF paint scan).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, fixtures, "No physical uncertainty model is instantiated.",
               "#text(fill: white)[No] physical uncertainty model is instantiated.")
        expect_rejection("15a_R5_white_text_policy",
                         lambda: verify_typst_evaluation_policy(sb, repin(sb, fixtures)),
                         "forbidden styling argument(s) ['fill']")
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(sb, man_drv, "#show: aod-manual-doc\n",
               '#show: aod-manual-doc\n#show "No physical uncertainty model": it => text(fill: white, it)\n')
        expect_rejection("15b_R5_white_text_paint_scan", lambda: rendered(sb, Path(td) / "o", gate_b_clean),
                         "is not opaque black/visible")

    # 16. R6: show rule negates a clause (content-file policy; driver variant via rendered clauses).
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td))
        mutate(sb, fixtures, "No physical uncertainty model is instantiated.",
               '#show "invalidates a retention": "validates a retention"\n'
               "No physical uncertainty model is instantiated.")
        expect_rejection("16a_R6_content_show_policy",
                         lambda: verify_typst_evaluation_policy(sb, repin(sb, fixtures)), "forbidden `show`")
    with tempfile.TemporaryDirectory() as td:
        sb = make_sandbox(Path(td), include_figures=True)
        mutate(sb, man_drv, "#show: aod-manual-doc\n",
               '#show: aod-manual-doc\n#show "invalidates a retention": "validates a retention"\n')
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
            "No physical uncertainty model is instantiated.",
            "#block(..(clip: true, height: 0pt))[No] physical uncertainty model is instantiated.",
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
            '#show: aod-manual-doc\n#show "No physical uncertainty model": it => text(fill: luma(0, 0%), it)\n',
        )
        expect_rejection(
            "21b_transparent_luma_paint_scan",
            lambda: rendered(sb, Path(td) / "o", gate_b_clean),
            "ca=0.0",
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
            else run_negative_controls(root, typst_bin, base_main, base_manual, baseline_root=b_root)
        )
    finally:
        if tmp_base is not None:
            tmp_base.cleanup()

    # Strip internal scratch keys from gate_b before serializing deterministic report
    gate_b = {k: v for k, v in gate_b_raw.items() if not k.startswith("_")}

    has_baselines = bool(base_main and base_manual)
    has_gen_latex = bool(gen_main and gen_manual)
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
    if not has_baselines:
        verdict = "PARTIAL_NON_ACCEPTANCE_MISSING_BASELINE_PDFS"
    elif not all_controls_ran:
        verdict = "PARTIAL_NON_ACCEPTANCE_SKIPPED_CONTROLS"
    elif unverified_clauses or typst_only_clauses or gen_unverified_clauses:
        verdict = "PARTIAL_NON_ACCEPTANCE_UNVERIFIED_CLAUSES"
    else:
        verdict = "PASS"

    report = {
        "schema": "aod.typst.parity-report.v2",
        "scientific_baseline_commit": SCIENTIFIC_BASELINE_COMMIT,
        "verifier_sha256": sha256_file(Path(__file__).resolve()),
        "gate_a_baseline_immutability": gate_a,
        "gate_a2_typst_evaluation_policy": gate_a2,
        "gate_b_scientific_content_parity": gate_b,
        "gate_c_evaluated_and_rendered": gate_c,
        "gate_d_negative_controls": gate_d,
        "coverage": {
            "ordered_prose_and_short_words": True,
            "all_inline_and_display_math_ast": True,
            "matrix_delimiters_and_augment_bars": True,
            "bar_vs_overline_and_upright_bold": True,
            "flowcharts_nodes_and_edges_verified": gate_b["flowcharts_verified"],
            "exact_equation_numbering_and_block_count": True,
            "unsupported_math_constructs": gate_b["unsupported_math_constructs"],
            "immutable_tables_cell_by_cell": True,
            "delivered_peer_pdf_links_and_landings": True,
            "generated_latex_source_tree_verified": bool(gate_b.get("generated_latex_parity", {}).get("performed")),
            "generated_latex_pdfs_verified_vs_baseline": has_baselines and has_gen_latex,
            "clickable_external_uris_vs_baseline_pdf": has_baselines,
            "inline_citation_sequence_vs_baseline_pdf": has_baselines,
            "rendered_bib_case_sensitive": has_baselines,
            "rendered_prose_clauses_vs_baseline_pdf": has_baselines,
            "rendered_prose_clauses_unverified": (
                unverified_clauses + typst_only_clauses + gen_unverified_clauses
            ) if has_baselines else "NOT_ASSESSED_WITHOUT_BASELINE",
            "rendered_insertion_ngrams_vs_baseline_pdf": has_baselines,
            "rendered_relation_glyph_parity_vs_baseline_pdf": has_baselines,
            "rendered_minus_equals_membership_glyphs": "SOURCE_MATH_AST_AND_EVALUATION_POLICY_ONLY",
            "rendered_text_paint_scan_alpha_and_clip": True,
            "typst_evaluation_policy_and_template_pins": True,
            "figure_image_bindings_to_protected_digests": gate_b["figure_image_bindings_verified"],
            "figure_pixels_visual_comparison": "NOT_PERFORMED_BOUND_BY_PROTECTED_DIGEST",
            "overlay_primitives": "FORBIDDEN_BY_POLICY_NOT_DETECTED_IN_PDF",
            "negative_controls_executed": 0 if args.skip_negative_controls else sum(
                1 for v in gate_d.values() if v.get("rejected") is True
            ),
            "human_visual_layout_review": "SEPARATE_RECORDED_OUTSIDE_AUTOMATED_SCRIPT",
        },
        "typ2tex_compatibility_status": "IMPLEMENTED_AND_VERIFIED_PHASE_2",
        "canonical_source_promotion": "TYPST_PRIMARY_LATEX_GENERATED_COMPATIBILITY",
        "verdict": verdict,
    }
    report_path = outdir / "parity_report.json"
    report_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    report_path.write_text(report_text, encoding="utf-8")
    print(report_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
