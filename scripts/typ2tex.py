#!/usr/bin/env python3
"""Bounded deterministic Typst-to-LaTeX exporter for Alpha-Omega Dynamics (AOD).

Reads ONLY canonical Typst sources under typst/, shared bibliographies
(refs.bib, manual/refs.bib), active raster assets referenced by Typst, and
shared native diagram components under typst/lib/diagrams/. Never reads
archive/ or historical editorial/table .tex files.

Emits a complete, self-contained generated LaTeX tree under --outdir (default:
latex/) that compiles outside the repository with XeLaTeX + BibTeX, along with
a deterministic GENERATION_MANIFEST.json. Supports atomic writes and --check
drift detection without mutating the target tree.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "1.0.0"
MANIFEST_NAME = "GENERATION_MANIFEST.json"
MANIFEST_SCHEMA = "aod.typ2tex.manifest.v1"

# Explicit generated-path overrides for the seven mapped table counterparts so
# generated LaTeX preserves the familiar Main/Manual include hierarchy.
TABLE_TARGET_OVERRIDES: dict[str, str] = {
    "typst/manual/tables/cycle_shedding_summary.typ": "cycle_shedding_summary.tex",
    "typst/manual/tables/run_tumble_trace_table.typ": "manual/data/run_tumble/run_tumble_trace_table.tex",
    "typst/manual/tables/sparc_summary_table.typ": "manual/data/derived/sparc_summary_table.tex",
    "typst/manual/tables/sparc5_medium_diagnostic_summary_table.typ": "manual/data/lensing/sparc5_medium_diagnostic_summary_table.tex",
    "typst/manual/tables/swells_k0_target_tallies_table.typ": "manual/data/lensing/swells_k0_target_tallies_table.tex",
    "typst/manual/tables/swells_k1_k2_k3_comparison_table.typ": "manual/data/lensing/swells_k1_k2_k3_comparison_table.tex",
    "typst/manual/tables/k4_3d_timeflow_input_gate_table.typ": "manual/data/lensing/k4_3d_timeflow_input_gate_table.tex",
}

DIAGRAM_INCLUDE_RE = re.compile(r'^(?:\.\./)+lib/diagrams/([a-z0-9_]+\.typ)$')


class Typ2TexError(ValueError):
    """Fail-closed source-located error for unsupported or malformed Typst."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Typ2TexError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_at(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def strip_typst_comments(text: str) -> str:
    """Strip // line comments and /* ... */ block comments while preserving strings and line numbers."""
    out: list[str] = []
    i = 0
    n = len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == "\\":
            if i + 1 < n:
                out.append(ch)
                out.append(text[i + 1])
                i += 2
                continue
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            # Preserve newline count; do not strip URLs like https://
            if i > 0 and text[i - 1] == ":":
                out.append("//")
                i += 2
                continue
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    out.append("\n")
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def scan_balanced(
    text: str,
    start: int,
    open_ch: str,
    close_ch: str,
    where: str,
    *,
    skip_math: bool = True,
) -> tuple[str, int]:
    """Scan a balanced (...) / [...] / {...} delimiter starting at start (on open_ch)."""
    _require(start < len(text) and text[start] == open_ch, f"{where}:{line_at(text, start)}: Expected {open_ch!r}")
    depth = 0
    i = start
    n = len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == '"':
            in_str = True
            i += 1
            continue
        if skip_math and ch == "$":
            _, i = scan_math_span(text, i, where)
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise Typ2TexError(f"{where}:{line_at(text, start)}: Unclosed {open_ch!r}")


def scan_math_span(text: str, start: int, where: str) -> tuple[str, int]:
    """Scan Typst $...$ math span starting at start (on '$'), honoring \"...\" and #[...]."""
    _require(start < len(text) and text[start] == "$", f"{where}:{line_at(text, start)}: Expected '$'")
    i = start + 1
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if ch == "#" and i + 1 < n and text[i + 1] == "[":
            _, i = scan_balanced(text, i + 1, "[", "]", where, skip_math=True)
            continue
        if ch == "$":
            return text[start + 1 : i], i + 1
        i += 1
    raise Typ2TexError(f"{where}:{line_at(text, start)}: Unclosed math span '$'")


def split_top_level(text: str, sep: str, where: str, *, skip_math: bool = True) -> list[str]:
    """Split text by single-char separator sep at depth 0, respecting quotes, math, and escapes."""
    parts: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(text)
    d_paren = d_brack = d_brace = 0
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            buf.append(ch)
            if ch == "\\" and i + 1 < n:
                buf.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            buf.append(ch)
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == '"':
            in_str = True
            buf.append(ch)
            i += 1
            continue
        if skip_math and ch == "$":
            _, nxt = scan_math_span(text, i, where)
            buf.append(text[i:nxt])
            i = nxt
            continue
        if ch == "(":
            d_paren += 1
        elif ch == ")":
            d_paren -= 1
        elif ch == "[":
            d_brack += 1
        elif ch == "]":
            d_brack -= 1
        elif ch == "{":
            d_brace += 1
        elif ch == "}":
            d_brace -= 1
        if ch == sep and d_paren == 0 and d_brack == 0 and d_brace == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def parse_call_args(arg_str: str, where: str) -> tuple[list[str], dict[str, str]]:
    """Split Typst function argument list into positional args and named key: value args."""
    pos: list[str] = []
    named: dict[str, str] = {}
    if not arg_str.strip():
        return pos, named
    for item in split_top_level(arg_str, ",", where):
        s = item.strip()
        if not s:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", s, re.S)
        if m and not s.startswith('"'):
            named[m.group(1)] = m.group(2).strip()
        else:
            pos.append(s)
    return pos, named


def unquote_typst_string(raw: str, where: str) -> str:
    s = raw.strip()
    _require(len(s) >= 2 and s[0] == '"' and s[-1] == '"', f"{where}: Expected string literal, got {raw[:40]!r}")
    out: list[str] = []
    i = 1
    n = len(s) - 1
    while i < n:
        ch = s[i]
        if ch == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt == "n":
                out.append("\n")
            elif nxt == "t":
                out.append("\t")
            elif nxt == '"':
                out.append('"')
            elif nxt == "\\":
                out.append("\\")
            elif nxt == "u" and i + 2 < n and s[i + 2] == "{":
                end_u = s.find("}", i + 3)
                _require(end_u != -1, f"{where}: Malformed unicode escape")
                out.append(chr(int(s[i + 3 : end_u], 16)))
                i = end_u + 1
                continue
            else:
                out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def escape_latex_text(s: str, *, in_texttt: bool = False) -> str:
    """Escape plain text for XeLaTeX without generating Missing character warnings."""
    if not s:
        return ""
    out: list[str] = []
    for ch in s:
        if ch == "\\":
            out.append(r"\textbackslash{}")
        elif ch == "{":
            out.append(r"\{")
        elif ch == "}":
            out.append(r"\}")
        elif ch == "$":
            out.append(r"\$")
        elif ch == "&":
            out.append(r"\&")
        elif ch == "%":
            out.append(r"\%")
        elif ch == "#":
            out.append(r"\#")
        elif ch == "_":
            out.append(r"\_")
        elif ch == "^":
            out.append(r"\textasciicircum{}")
        elif ch == "~":
            out.append(r"\textasciitilde{}")
        elif ch == "\u00a0":
            out.append(" " if in_texttt else "~")
        elif ch == "\u2013":
            out.append("-" if in_texttt else "--")
        elif ch == "\u2014":
            out.append("--" if in_texttt else "---")
        elif ch == "\u2019":
            out.append("'")
        elif ch == "\u2018":
            out.append("`")
        elif ch == "\u201c":
            out.append('"' if in_texttt else "``")
        elif ch == "\u201d":
            out.append('"' if in_texttt else "''")
        elif ch == "\u00a7":
            out.append(r"\S")
        elif ch == "\u2194":
            out.append(r"$\leftrightarrow$")
        elif ch == "\u03a9":
            out.append(r"$\Omega$")
        elif ord(ch) > 127:
            raise Typ2TexError(f"Unsupported non-ASCII prose character U+{ord(ch):04X} ({ch!r}) in {s[:60]!r}")
        else:
            out.append(ch)
    return "".join(out)


def escape_latex_href_url(url: str) -> str:
    return url.replace("%", r"\%").replace("#", r"\#")


# ---------------------------------------------------------------------------
# Typst Math -> LaTeX Recursive-Descent Translator
# ---------------------------------------------------------------------------

TYPST_MATH_SYMBOLS: dict[str, str] = {
    # AOD preamble macros
    "Null": r"\Null",
    "infD": r"\infD",
    "Qfour": r"\Qfour",
    "RCD": r"\RCD",
    "SADAR": r"\SADAR",
    "ADAR": r"\ADAR",
    "AO": r"\AO",
    "AOpkg": r"\AOpkg",
    "OAop": r"\OAop",
    "AOh": r"\AOh",
    "OAh": r"\OAh",
    "AOcycle": r"\AOcycle",
    "SADARop": r"\SADARop",
    "Qext": r"\Qext",
    "leadsto": r"\leadsto",
    # Greek uppercase
    "Gamma": r"\Gamma",
    "Delta": r"\Delta",
    "Theta": r"\Theta",
    "Lambda": r"\Lambda",
    "Xi": r"\Xi",
    "Pi": r"\Pi",
    "Sigma": r"\Sigma",
    "Upsilon": r"\Upsilon",
    "Phi": r"\Phi",
    "Psi": r"\Psi",
    "Omega": r"\Omega",
    # Greek lowercase
    "alpha": r"\alpha",
    "beta": r"\beta",
    "gamma": r"\gamma",
    "delta": r"\delta",
    "epsilon": r"\epsilon",
    "epsilon.alt": r"\varepsilon",
    "zeta": r"\zeta",
    "eta": r"\eta",
    "theta": r"\theta",
    "theta.alt": r"\vartheta",
    "iota": r"\iota",
    "kappa": r"\kappa",
    "lambda": r"\lambda",
    "mu": r"\mu",
    "nu": r"\nu",
    "xi": r"\xi",
    "pi": r"\pi",
    "pi.alt": r"\varpi",
    "rho": r"\rho",
    "rho.alt": r"\varrho",
    "sigma": r"\sigma",
    "tau": r"\tau",
    "upsilon": r"\upsilon",
    "phi": r"\phi",
    "phi.alt": r"\varphi",
    "chi": r"\chi",
    "psi": r"\psi",
    "omega": r"\omega",
    # Arrows
    "arrow.r": r"\to",
    "arrow.l": r"\leftarrow",
    "arrow.l.r": r"\leftrightarrow",
    "arrow.t": r"\uparrow",
    "arrow.b": r"\downarrow",
    "arrow.b.double": r"\Downarrow",
    "arrow.t.double": r"\Uparrow",
    "arrow.r.long": r"\longrightarrow",
    "arrow.l.long": r"\longleftarrow",
    "arrow.l.r.long": r"\longleftrightarrow",
    "arrow.r.double": r"\Rightarrow",
    "arrow.l.double": r"\Leftarrow",
    "arrow.r.double.long": r"\Longrightarrow",
    "arrow.l.r.double.long": r"\Longleftrightarrow",
    "arrow.r.double.not": r"\nRightarrow",
    "arrow.r.bar": r"\mapsto",
    "arrow.r.long.bar": r"\longmapsto",
    "arrow.r.squiggly": r"\leadsto",
    # Relations & operators
    "lt.eq": r"\le",
    "gt.eq": r"\ge",
    "eq.not": r"\ne",
    "equiv": r"\equiv",
    "approx": r"\approx",
    "tilde.op": r"\sim",
    "prec.eq": r"\preceq",
    "succ": r"\succ",
    "succ.eq": r"\succeq",
    "in": r"\in",
    "in.not": r"\notin",
    "subset": r"\subset",
    "subset.eq": r"\subseteq",
    "supset": r"\supset",
    "supset.eq": r"\supseteq",
    "union": r"\cup",
    "union.big": r"\bigcup",
    "union.sq": r"\sqcup",
    "inter": r"\cap",
    "inter.big": r"\bigcap",
    "without": r"\setminus",
    "times": r"\times",
    "plus.minus": r"\pm",
    "minus.plus": r"\mp",
    "plus.o": r"\oplus",
    "dot.o": r"\odot",
    "dot.op": r"\cdot",
    "dots.c": r"\cdots",
    "dots.h": r"\dots",
    "dots.v": r"\vdots",
    "star": r"\star",
    "ast": r"\ast",
    "bowtie": r"\bowtie",
    "perp": r"\perp",
    "parallel": r"\parallel",
    "tack.r": r"\vdash",
    "tack.l": r"\dashv",
    "and": r"\wedge",
    "or": r"\vee",
    "not": r"\neg",
    "forall": r"\forall",
    "exists": r"\exists",
    "emptyset": r"\emptyset",
    "infinity": r"\infty",
    "partial": r"\partial",
    "nabla": r"\nabla",
    "ell": r"\ell",
    "circle.tiny": r"\circ",
    "square.stroked": r"\square",
    "sum": r"\sum",
    "product": r"\prod",
    "integral": r"\int",
    # Delimiters
    "bar.v": r"|",
    "bar.v.double": r"\|",
    "brace.l": r"\{",
    "brace.r": r"\}",
    "chevron.l": r"\langle",
    "chevron.r": r"\rangle",
    "floor.l": r"\lfloor",
    "floor.r": r"\rfloor",
    "ceil.l": r"\lceil",
    "ceil.r": r"\rceil",
    "paren.l": r"(",
    "paren.r": r")",
    "slash": r"/",
    # Standard named operators
    "min": r"\min",
    "max": r"\max",
    "sup": r"\sup",
    "inf": r"\inf",
    "log": r"\log",
    "ln": r"\ln",
    "exp": r"\exp",
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "arctan": r"\arctan",
    "arg": r"\arg",
    "det": r"\det",
    "dim": r"\dim",
    "ker": r"\ker",
    "mod": r"\bmod",
    "Pr": r"\Pr",
    # Spacing
    "thin": r"\,",
    "med": r"\;",
    "thick": r"\;",
    "quad": r"\quad",
    "wide": r"\qquad",
}

MATH_FUNCS = frozenset({
    "frac", "sqrt", "upright", "bold", "sans", "mono", "cal", "bb", "frak",
    "op", "hat", "tilde", "macron", "overline", "underline", "display",
    "scripts", "mid", "lr", "attach", "stretch", "cases", "mat", "limits",
})


SINGLE_LETTER_UNITS = frozenset({
    "A", "C", "F", "H", "J", "K", "L", "N", "S", "T", "V", "W", "g", "m", "s",
})

_MATH_SPACING_IDENTIFIERS = frozenset({"thin", "med", "thick", "quad", "wide"})

_MATH_REL_OR_BIN_TEX = frozenset({
    r"\to", r"\rightarrow", r"\leftarrow", r"\leftrightarrow", r"\iff",
    r"\implies", r"\impliedby", r"\mapsto", r"\longrightarrow",
    r"\longleftrightarrow", r"\leadsto", r"\in", r"\notin", r"\subset",
    r"\subseteq", r"\supset", r"\supseteq", r"\cup", r"\cap", r"\setminus",
    r"\ne", r"\neq", r"\le", r"\ge", r"\equiv", r"\approx", r"\sim",
    r"\simeq", r"\cong", r"\propto", r"\pm", r"\mp", r"\times", r"\cdot",
    r"\circ", r"\otimes", r"\oplus", r"\land", r"\lor", r"\mid", r"\vdash",
    r"\models", r"\perp", r"\parallel", r"\colon", r"\dots", r"\ldots",
    r"\cdots", r"\{", r"\}", r"\langle", r"\rangle", r"\lfloor", r"\rfloor",
    r"\lceil", r"\rceil",
})


class _MathAtom:
    __slots__ = ("tex", "kind", "had_ws", "raw_text", "has_script")

    def __init__(
        self,
        tex: str,
        kind: str,
        *,
        had_ws: bool = False,
        raw_text: str = "",
        has_script: bool = False,
    ) -> None:
        self.tex = tex
        self.kind = kind
        self.had_ws = had_ws
        self.raw_text = raw_text
        self.has_script = has_script


def _join_math_atoms(atoms: list[_MathAtom]) -> str:
    """Join parsed math atoms preserving meaningful source whitespace at text and unit boundaries."""
    filtered = [a for a in atoms if a.tex]
    if not filtered:
        return ""
    out: list[str] = [filtered[0].tex]
    prev = filtered[0]
    for curr in filtered[1:]:
        # 1. Numeric literal or numeric power followed by whitespace + standalone upright unit
        #    (handles single-letter units such as J without a >= 2-letter heuristic,
        #    while preserving tight imaginary `2\mathrm{i}` and tight inverse-second `s^{-1}`).
        if (
            curr.had_ws
            and prev.kind == "num"
            and curr.kind == "upright"
            and not curr.has_script
            and re.fullmatch(r"[A-Za-z][A-Za-z/]*", curr.raw_text)
            and (len(curr.raw_text) >= 2 or curr.raw_text in SINGLE_LETTER_UNITS)
        ):
            out.append(r"\," + curr.tex)
        # 2. Expression/word atom followed by whitespace + prose quoted text lacking leading space/punct
        elif (
            curr.had_ws
            and curr.kind == "text"
            and curr.raw_text
            and not curr.raw_text[0].isspace()
            and curr.raw_text[0] not in ".,;:!?)]}"
            and prev.kind in ("upright", "math", "num", "ref", "text")
            and not (prev.kind == "text" and prev.raw_text and prev.raw_text[-1].isspace())
        ):
            out.append(r"\ " + curr.tex)
        # 3. Prose quoted text lacking trailing space followed by whitespace + expression/word atom
        elif (
            curr.had_ws
            and prev.kind == "text"
            and prev.raw_text
            and not prev.raw_text[-1].isspace()
            and prev.raw_text[-1] not in "([{"
            and curr.kind in ("upright", "math", "num", "ref")
        ):
            out.append(r"\ " + curr.tex)
        # 4. Prevent TeX control-sequence name gluing to an immediately following ASCII letter
        elif prev.tex and re.search(r"\\[A-Za-z]+$", prev.tex) and re.match(r"^[A-Za-z]", curr.tex):
            out.append(" " + curr.tex)
        else:
            out.append(curr.tex)
        prev = curr
    return "".join(out)


def _join_math_tokens(tokens: list[str]) -> str:
    """Backward-compatible helper joining raw math string fragments safely."""
    if not tokens:
        return ""
    out: list[str] = [tokens[0]]
    for tok in tokens[1:]:
        if not tok:
            continue
        prev = out[-1]
        if prev and re.search(r"\\[A-Za-z]+$", prev) and re.match(r"^[A-Za-z]", tok):
            out.append(" " + tok)
        else:
            out.append(tok)
    return "".join(out)


_PDF_STRING_SYMBOLS: dict[str, str] = {
    "plus.minus": "\u00b1",
    "minus.plus": "-+",
    "arrow.l.r": "<->",
    "arrow.r": "->",
    "arrow.l": "<-",
    "arrow.l.r.long": "<->",
    "arrow.r.long": "->",
    "arrow.l.r.double.long": "<=>",
    "arrow.r.double": "=>",
    "arrow.r.bar": "|->",
    "bar.v": "|",
    "eq.not": "!=",
    "lt.eq": "<=",
    "gt.eq": ">=",
    "times": "x",
    "dot.op": "*",
    "infinity": "inf",
    "Alpha": "Alpha", "Beta": "Beta", "Gamma": "Gamma", "Delta": "Delta",
    "Epsilon": "Epsilon", "Theta": "Theta", "Lambda": "Lambda", "Pi": "Pi",
    "Sigma": "Sigma", "Phi": "Phi", "Psi": "Psi", "Omega": "Omega",
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta",
    "epsilon": "epsilon", "zeta": "zeta", "eta": "eta", "theta": "theta",
    "iota": "iota", "kappa": "kappa", "lambda": "lambda", "mu": "mu",
    "nu": "nu", "xi": "xi", "pi": "pi", "pi.alt": "pi", "rho": "rho",
    "sigma": "sigma", "tau": "tau", "phi": "phi", "phi.alt": "phi",
    "chi": "chi", "psi": "psi", "omega": "omega",
    "Null": "Null", "Qfour": "Q4", "RCD": "RCD", "SADAR": "SADAR",
    "ADAR": "ADAR", "AO": "A<->Omega",
    "thin": " ", "med": " ", "thick": " ", "quad": " ", "wide": " ",
}


def _math_to_pdf_string(expr: str, where: str) -> str:
    """Derive a compatibility PDF-bookmark string directly from canonical Typst math."""
    out: list[str] = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch in ("_", "^"):
            i += 1
            while i < n and expr[i] in " \t\r\n":
                i += 1
            if i < n and expr[i] == "(":
                inner, i = scan_balanced(expr, i, "(", ")", where, skip_math=False)
                out.append(_math_to_pdf_string(inner, where))
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if expr[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if expr[j] == '"':
                    break
                j += 1
            _require(j < n, f"{where}: Unclosed string in heading math")
            val = unquote_typst_string(expr[i : j + 1], where)
            i = j + 1
            if val:
                out.append(val)
            continue
        m_num = re.match(r"[0-9]+(?:\.[0-9]+)?", expr[i:])
        if m_num:
            out.append(m_num.group(0))
            i += len(m_num.group(0))
            continue
        m_id = re.match(r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*", expr[i:])
        if m_id:
            ident = m_id.group(0)
            i += len(ident)
            if i < n and expr[i] == "(" and ident in MATH_FUNCS:
                arg_str, i = scan_balanced(expr, i, "(", ")", where, skip_math=False)
                if ident == "frac":
                    parts = split_top_level(arg_str, ",", where)
                    out.append("/".join(_math_to_pdf_string(p, where) for p in parts))
                else:
                    s = arg_str.strip()
                    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
                        out.append(unquote_typst_string(s, where))
                    else:
                        out.append(_math_to_pdf_string(s, where))
                continue
            if len(ident) == 1:
                out.append(ident)
            elif ident in _PDF_STRING_SYMBOLS:
                out.append(_PDF_STRING_SYMBOLS[ident])
            else:
                out.append(ident)
            continue
        if ch in "+-=<>:,;.!?/@*|()[]":
            out.append(ch)
            i += 1
            continue
        i += 1
    return re.sub(r"\s+", " ", "".join(out)).strip()


class _MathParser:
    def __init__(self, expr: str, where: str, inline_prose_converter):
        self.s = expr
        self.n = len(expr)
        self.i = 0
        self.where = where
        self.inline_prose = inline_prose_converter

    def _skip_ws(self) -> bool:
        start = self.i
        while self.i < self.n and self.s[self.i] in " \t\r\n":
            self.i += 1
        return self.i > start

    def parse_expr(self, stop_chars: str = "") -> str:
        atoms: list[_MathAtom] = []
        while self.i < self.n:
            had_ws = self._skip_ws()
            if self.i >= self.n:
                break
            ch = self.s[self.i]
            if stop_chars and ch in stop_chars:
                break
            atom_tex, atom_kind, raw_text = self._parse_atom(stop_chars)
            # Attach any _ or ^ scripts to this atom in exact source order
            scripts: list[tuple[str, str]] = []
            while True:
                save_i = self.i
                self._skip_ws()
                if self.i < self.n and self.s[self.i] in ("_", "^"):
                    op_ch = self.s[self.i]
                    self.i += 1
                    self._skip_ws()
                    script_val = self._parse_script_arg()
                    scripts.append((op_ch, script_val))
                else:
                    self.i = save_i
                    break
            for op_ch, val in scripts:
                if len(val) == 1 and (val.isalnum() or val in "+-*"):
                    atom_tex = f"{atom_tex}{op_ch}{val}"
                else:
                    atom_tex = f"{atom_tex}{op_ch}{{{val}}}"
            # Empty base with scripts (e.g. `""^(plus.minus)`) becomes a math atom
            if atom_kind == "empty" and scripts:
                atom_kind = "math"
            atoms.append(
                _MathAtom(
                    tex=atom_tex,
                    kind=atom_kind,
                    had_ws=had_ws,
                    raw_text=raw_text,
                    has_script=bool(scripts),
                )
            )
        return _join_math_atoms(atoms)

    def _parse_script_arg(self) -> str:
        """Parse the argument immediately following _ or ^ (strips grouping parens)."""
        self._skip_ws()
        _require(self.i < self.n, f"{self.where}: Unexpected end of math expression after _ or ^")
        if self.s[self.i] == "(":
            inner, nxt = scan_balanced(self.s, self.i, "(", ")", self.where, skip_math=False)
            self.i = nxt
            rendered = _MathParser(inner, self.where, self.inline_prose).parse_expr()
            if r"\\" in rendered and r"\begin{" not in rendered:
                return rf"\substack{{{rendered}}}"
            return rendered
        tex, _, _ = self._parse_atom("")
        return tex

    def _parse_atom(self, stop_chars: str) -> tuple[str, str, str]:
        ch = self.s[self.i]
        # Line break `\` followed by whitespace or EOL, or escaped char `\,` etc.
        if ch == "\\":
            if self.i + 1 >= self.n or self.s[self.i + 1] in " \t\r\n":
                self.i += 1
                return r"\\", "break", ""
            nxt = self.s[self.i + 1]
            self.i += 2
            if nxt == ",":
                return ",", "punct", ","
            if nxt in ("#", "$", "%", "&", "{", "}", "_"):
                return "\\" + nxt, "punct", nxt
            if nxt == "\\":
                return r"\\", "break", ""
            return nxt, "punct", nxt
        # Alignment tab
        if ch == "&":
            self.i += 1
            return " & ", "align", "&"
        # Quoted text inside math
        if ch == '"':
            j = self.i + 1
            while j < self.n:
                if self.s[j] == "\\" and j + 1 < self.n:
                    j += 2
                    continue
                if self.s[j] == '"':
                    break
                j += 1
            _require(j < self.n, f"{self.where}: Unclosed string in math")
            val = unquote_typst_string(self.s[self.i : j + 1], self.where)
            self.i = j + 1
            if val == "":
                return "", "empty", ""
            if val == ":":
                return ":", "punct", ":"
            if val == "#":
                return r"\#", "punct", "#"
            if val == "%":
                return r"\%", "punct", "%"
            if val == "|":
                return "|", "punct", "|"
            return r"\text{" + escape_latex_text(val) + "}", "text", val
        # Hash code/content inside math
        if ch == "#":
            if self.i + 1 < self.n and self.s[self.i + 1] == "[":
                inner, nxt = scan_balanced(self.s, self.i + 1, "[", "]", self.where)
                self.i = nxt
                # Split inline $...$ out of \text{...} so math tokens remain direct math
                segs: list[str] = []
                k = 0
                while k < len(inner):
                    if inner[k] == "$":
                        mb, k = scan_math_span(inner, k, self.where)
                        segs.append(convert_math(mb, self.where, self.inline_prose))
                    else:
                        j = k
                        while j < len(inner) and inner[j] != "$":
                            j += 1
                        frag = self.inline_prose(inner[k:j])
                        if frag:
                            segs.append(r"\text{" + frag + "}")
                        k = j
                return _join_math_tokens(segs), "text", inner
            m = re.match(r"#([A-Za-z_][A-Za-z0-9_-]*)", self.s[self.i:])
            _require(m is not None, f"{self.where}: Unsupported '#' inside math: {self.s[self.i:self.i+20]!r}")
            fname = m.group(1)
            self.i += len(m.group(0))
            if self.i < self.n and self.s[self.i] == "(":
                arg_str, nxt = scan_balanced(self.s, self.i, "(", ")", self.where)
                self.i = nxt
                pos, _ = parse_call_args(arg_str, self.where)
                if fname in ("secref", "eqref", "eqnref", "appref", "figref", "tabref",
                             "bare-ref", "mainequation", "mainsection", "mainappendix", "maintable"):
                    _require(len(pos) == 1, f"{self.where}: #{fname} in math expects 1 argument")
                    target = unquote_typst_string(pos[0], self.where)
                    tex_cmd = "ref" if fname == "bare-ref" else fname
                    return rf"\{tex_cmd}{{{target}}}", "ref", target
                if fname == "raw":
                    _require(len(pos) == 1, f"{self.where}: #raw in math expects 1 argument")
                    val = unquote_typst_string(pos[0], self.where)
                    return rf"\texttt{{{escape_latex_text(val, in_texttt=True)}}}", "upright", val
            raise Typ2TexError(f"{self.where}: Unsupported Typst call #{fname} inside math")
        # Parentheses / brackets (standalone atoms so half-open intervals like (u, v] work)
        if ch in "()[]":
            self.i += 1
            return ch, "punct", ch
        if ch == "{":
            self.i += 1
            return r"\{", "punct", "{"
        if ch == "}":
            self.i += 1
            return r"\}", "punct", "}"
        # Numbers
        m_num = re.match(r"[0-9]+(?:\.[0-9]+)?", self.s[self.i:])
        if m_num:
            num = m_num.group(0)
            self.i += len(num)
            return num, "num", num
        # Identifiers (dotted symbols or function calls or single letters)
        m_id = re.match(r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*", self.s[self.i:])
        if m_id:
            ident = m_id.group(0)
            self.i += len(ident)
            # Function call?
            if self.i < self.n and self.s[self.i] == "(" and ident in MATH_FUNCS:
                arg_str, nxt = scan_balanced(self.s, self.i, "(", ")", self.where)
                self.i = nxt
                rendered = self._convert_func(ident, arg_str)
                if ident == "upright":
                    s_arg = arg_str.strip()
                    raw_u = unquote_typst_string(s_arg, self.where) if (len(s_arg) >= 2 and s_arg[0] == '"' and s_arg[-1] == '"') else s_arg
                    return rendered, "upright", raw_u
                if ident == "mid":
                    return rendered, "punct", ""
                return rendered, "math", ""
            if len(ident) == 1:
                return ident, "math", ident
            if ident in TYPST_MATH_SYMBOLS:
                sym_tex = TYPST_MATH_SYMBOLS[ident]
                if ident in _MATH_SPACING_IDENTIFIERS:
                    return sym_tex, "spacer", ident
                if sym_tex in _MATH_REL_OR_BIN_TEX:
                    return sym_tex, "punct", ident
                return sym_tex, "math", ident
            raise Typ2TexError(f"{self.where}: Unsupported Typst math identifier {ident!r}")
        # Single punctuation / operators
        self.i += 1
        if ch == "|":
            return "|", "punct", "|"
        if ch == "'":
            return "'", "punct", "'"
        if ch == "~":
            return r"\sim", "punct", "~"
        if ch in "+-=<>:,;.!?/@*":
            return ch, "punct", ch
        raise Typ2TexError(f"{self.where}: Unsupported character {ch!r} in Typst math")

    def _subparse(self, inner: str) -> str:
        return _MathParser(inner, self.where, self.inline_prose).parse_expr()

    def _convert_text_arg(self, raw_arg: str) -> str:
        s = raw_arg.strip()
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            return escape_latex_text(unquote_typst_string(s, self.where))
        return self._subparse(s)

    def _convert_func(self, fname: str, arg_str: str) -> str:
        if fname == "frac":
            parts = split_top_level(arg_str, ",", self.where)
            _require(len(parts) == 2, f"{self.where}: frac() expects 2 arguments, got {len(parts)}")
            return rf"\frac{{{self._subparse(parts[0])}}}{{{self._subparse(parts[1])}}}"
        if fname == "sqrt":
            return rf"\sqrt{{{self._subparse(arg_str)}}}"
        if fname == "upright":
            return rf"\mathrm{{{self._convert_text_arg(arg_str)}}}"
        if fname == "bold":
            inner = arg_str.strip()
            if inner.startswith("upright(") and inner.endswith(")"):
                inner_body = inner[len("upright("):-1]
                return rf"\mathbf{{{self._convert_text_arg(inner_body)}}}"
            rendered = self._convert_text_arg(inner)
            if rendered.startswith("\\"):
                return rf"\boldsymbol{{{rendered}}}"
            return rf"\mathbf{{{rendered}}}"
        if fname == "sans":
            return rf"\mathsf{{{self._convert_text_arg(arg_str)}}}"
        if fname == "mono":
            return rf"\mathtt{{{self._convert_text_arg(arg_str)}}}"
        if fname == "cal":
            return rf"\mathcal{{{self._convert_text_arg(arg_str)}}}"
        if fname == "bb":
            return rf"\mathbb{{{self._convert_text_arg(arg_str)}}}"
        if fname == "frak":
            return rf"\mathfrak{{{self._convert_text_arg(arg_str)}}}"
        if fname == "op":
            return rf"\operatorname{{{self._convert_text_arg(arg_str)}}}"
        if fname == "hat":
            body = self._subparse(arg_str)
            if len(body) > 1 or body == "v" or body == "w":
                return rf"\widehat{{{body}}}"
            return rf"\hat{{{body}}}"
        if fname == "tilde":
            return rf"\tilde{{{self._subparse(arg_str)}}}"
        if fname == "macron":
            return rf"\bar{{{self._subparse(arg_str)}}}"
        if fname == "overline":
            return rf"\overline{{{self._subparse(arg_str)}}}"
        if fname == "underline":
            return rf"\underline{{{self._subparse(arg_str)}}}"
        if fname == "display":
            return self._subparse(arg_str)
        if fname in ("scripts", "limits"):
            return "{" + self._subparse(arg_str) + "}"
        if fname == "mid":
            s = arg_str.strip()
            if s in ("|", "bar.v"):
                return r"\mid"
            return r"\mathrel{" + self._subparse(s) + "}"
        if fname == "lr":
            s = arg_str.strip()
            # Simple parenthesized superscript tokens like lr((3)), lr((n))
            if s.startswith("(") and s.endswith(")"):
                inner = self._subparse(s[1:-1])
                if r"\frac" not in inner and r"\sum" not in inner and len(inner) <= 8:
                    return f"({inner})"
                return rf"\left({inner}\right)"
            if s.startswith("[") and s.endswith("]"):
                return rf"\left[{self._subparse(s[1:-1])}\right]"
            if s.startswith("brace.l") and s.endswith("brace.r"):
                return rf"\left\{{{self._subparse(s[7:-7])}\right\}}"
            if s.startswith("bar.v") and s.endswith("bar.v"):
                return rf"\left|{self._subparse(s[5:-5])}\right|"
            return self._subparse(s)
        if fname == "stretch":
            pos, _ = parse_call_args(arg_str, self.where)
            _require(len(pos) >= 1, f"{self.where}: stretch() requires a symbol argument")
            return self._subparse(pos[0])
        if fname == "attach":
            pos, named = parse_call_args(arg_str, self.where)
            _require(len(pos) == 1, f"{self.where}: attach() expects 1 positional base")
            base_raw = pos[0].strip()
            top = self._subparse(named["t"]) if "t" in named else None
            bot = self._subparse(named["b"]) if "b" in named else None
            if "arrow.r" in base_raw and "arrow.l" not in base_raw:
                if bot is not None:
                    return rf"\xrightarrow[{bot}]{{{top or ''}}}"
                return rf"\xrightarrow{{{top or ''}}}"
            if "arrow.l" in base_raw and "arrow.r" not in base_raw:
                if bot is not None:
                    return rf"\xleftarrow[{bot}]{{{top or ''}}}"
                return rf"\xleftarrow{{{top or ''}}}"
            base = self._subparse(base_raw)
            res = f"{{{base}}}"
            if bot is not None:
                res += f"_{{{bot}}}"
            if top is not None:
                res += f"^{{{top}}}"
            return res
        if fname == "cases":
            rows = [self._subparse(r) for r in split_top_level(arg_str, ",", self.where) if r.strip()]
            return r"\begin{cases}" + "\n" + " \\\\\n".join(rows) + "\n" + r"\end{cases}"
        if fname == "mat":
            # Parse optional named params (delim, augment, align) before matrix rows (separated by ';')
            delim = "("
            augment = None
            align_col = "c"
            # Split by top-level ';' for rows; first chunk may start with named params separated by ','
            semis = split_top_level(arg_str, ";", self.where)
            first_cells = split_top_level(semis[0], ",", self.where)
            real_first_cells: list[str] = []
            for cell in first_cells:
                cs = cell.strip()
                m = re.match(r"^(delim|augment|align)\s*:\s*(.*)$", cs, re.S)
                if m:
                    k, v = m.group(1), m.group(2).strip()
                    if k == "delim":
                        delim = None if v in ("#none", "none") else v.strip('"')
                    elif k == "augment":
                        augment = int(v.lstrip("#"))
                    elif k == "align":
                        av = v.lstrip("#")
                        align_col = {"left": "l", "right": "r", "center": "c"}.get(av, "c")
                else:
                    real_first_cells.append(cs)
            rows_cells: list[list[str]] = [real_first_cells]
            for seg in semis[1:]:
                if seg.strip():
                    rows_cells.append([c.strip() for c in split_top_level(seg, ",", self.where)])
            ncols = max((len(r) for r in rows_cells), default=1)
            rendered_rows = [
                " & ".join(self._subparse(c) for c in row)
                for row in rows_cells
            ]
            if augment is not None or align_col != "c":
                cols_spec = []
                for idx in range(ncols):
                    if augment is not None and idx == augment:
                        cols_spec.append("|")
                    cols_spec.append(align_col)
                body = r"\begin{array}{" + "".join(cols_spec) + "}\n" + " \\\\\n".join(rendered_rows) + "\n" + r"\end{array}"
                if delim == "(":
                    return rf"\left({body}\right)"
                if delim == "[":
                    return rf"\left[{body}\right]"
                return body
            env = {"(": "pmatrix", "[": "bmatrix", None: "matrix"}.get(delim, "matrix")
            return rf"\begin{{{env}}}" + "\n" + " \\\\\n".join(rendered_rows) + "\n" + rf"\end{{{env}}}"
        raise Typ2TexError(f"{self.where}: Unsupported Typst math function {fname}()")


def convert_math(expr: str, where: str, inline_prose_converter) -> str:
    return _MathParser(expr, where, inline_prose_converter).parse_expr()


# ---------------------------------------------------------------------------
# Typst Table -> LaTeX tabular / tabularx / longtable Converter
# ---------------------------------------------------------------------------

def _font_size_cmd(size_str: str | None) -> str:
    if not size_str:
        return ""
    m = re.match(r"([0-9]+(?:\.[0-9]+)?)pt", size_str.strip())
    if not m:
        return ""
    pt = float(m.group(1))
    if pt <= 7.8:
        return r"\scriptsize"
    if pt <= 8.8:
        return r"\footnotesize"
    if pt <= 9.8:
        return r"\small"
    return ""


def _parse_tuple_items(raw: str, where: str) -> list[str]:
    s = raw.strip()
    if s.startswith("(") and s.endswith(")"):
        return [x.strip() for x in split_top_level(s[1:-1], ",", where) if x.strip()]
    return [s]


def _build_colspec(cols: list[str], aligns: list[str], *, force_longtable: bool) -> tuple[str, bool]:
    """Return (LaTeX column spec, uses_tabularx)."""
    n = len(cols)
    if len(aligns) < n:
        aligns = aligns + ["left"] * (n - len(aligns))
    align_code = {"left": "l", "center": "c", "right": "r"}
    align_ragged = {
        "left": r">{\raggedright\arraybackslash}",
        "center": r">{\centering\arraybackslash}",
        "right": r">{\raggedleft\arraybackslash}",
    }

    has_fr = any(c.endswith("fr") for c in cols)
    has_auto = any(c == "auto" for c in cols)
    has_pct = any(c.endswith("%") for c in cols)

    # Pure auto columns -> simple tabular l/c/r
    if not has_fr and not has_pct:
        return "".join(align_code.get(a, "l") for a in aligns[:n]), False

    # All numeric fr columns (e.g. 16.00fr, 23.00fr, ...) -> proportional p{w\linewidth}
    if all(c.endswith("fr") for c in cols):
        vals = [float(c[:-2]) for c in cols]
        total = sum(vals)
        # Keep widths inside usable text width allowing 2*\tabcolsep per column
        target_total = 0.92 if n <= 4 else (0.86 if n <= 6 else 0.80)
        if total <= 95.0 and total >= 60.0:
            scale = min(1.0, target_total / (total / 100.0)) / 100.0
        else:
            scale = target_total / total
        specs = []
        for v, a in zip(vals, aligns):
            w = max(0.05, round(v * scale, 3))
            specs.append(f"{align_ragged.get(a, align_ragged['left'])}p{{{w:.3f}\\linewidth}}")
        return "".join(specs), False

    # Mixed auto / % / 1fr -> tabularx (unless forced longtable, where we compute fixed p{})
    if not force_longtable:
        specs = []
        for c, a in zip(cols, aligns):
            if c == "auto":
                specs.append(align_code.get(a, "l"))
            elif c.endswith("%"):
                w = round(float(c[:-1]) / 100.0, 3)
                specs.append(f"{align_ragged.get(a, align_ragged['left'])}p{{{w:.3f}\\linewidth}}")
            elif c.endswith("fr"):
                specs.append(f"{align_ragged.get(a, align_ragged['left'])}X")
            else:
                specs.append("l")
        return "".join(specs), True

    # Forced longtable with mixed widths: distribute remaining width across fr cols
    fixed = sum(float(c[:-1]) / 100.0 for c in cols if c.endswith("%"))
    auto_cnt = sum(1 for c in cols if c == "auto")
    fr_vals = [float(c[:-2]) for c in cols if c.endswith("fr")]
    rem = max(0.25, 0.88 - fixed - 0.14 * auto_cnt)
    fr_sum = sum(fr_vals) or 1.0
    specs = []
    for c, a in zip(cols, aligns):
        if c == "auto":
            specs.append(align_code.get(a, "l"))
        elif c.endswith("%"):
            w = round(float(c[:-1]) / 100.0, 3)
            specs.append(f"{align_ragged.get(a, align_ragged['left'])}p{{{w:.3f}\\linewidth}}")
        else:
            w = max(0.10, round(rem * (float(c[:-2]) / fr_sum), 3))
            specs.append(f"{align_ragged.get(a, align_ragged['left'])}p{{{w:.3f}\\linewidth}}")
    return "".join(specs), False


def _parse_table_call(table_args_str: str, where: str) -> dict:
    """Parse table(columns: ..., align: ..., table.header(...), [cell], ...) into structured rows."""
    items = [x.strip() for x in split_top_level(table_args_str, ",", where) if x.strip()]
    cols: list[str] = []
    aligns: list[str] = []
    header_items: list[str] = []
    body_items: list[str] = []

    for item in items:
        m = re.match(r"^(columns|align)\s*:\s*(.*)$", item, re.S)
        if m:
            if m.group(1) == "columns":
                cols = _parse_tuple_items(m.group(2), where)
            else:
                aligns = _parse_tuple_items(m.group(2), where)
            continue
        if item.startswith("table.header("):
            inner, _ = scan_balanced(item, len("table.header"), "(", ")", where)
            header_items.extend(x.strip() for x in split_top_level(inner, ",", where) if x.strip())
            continue
        body_items.append(item)

    ncols = len(cols)
    _require(ncols > 0, f"{where}: table() missing columns specification")

    def _chunk_rows(raw_items: list[str]) -> list[tuple[str, list[str] | str]]:
        # Returns sequence of ("rule", "\\toprule"|...) or ("row", [cell_content, ...])
        seq: list[tuple[str, list[str] | str]] = []
        cur: list[str] = []
        for it in raw_items:
            if it in ("toprule", "midrule", "bottomrule"):
                if cur:
                    _require(len(cur) == ncols, f"{where}: Incomplete table row ({len(cur)} != {ncols} cols)")
                    seq.append(("row", cur))
                    cur = []
                seq.append(("rule", "\\" + it))
            elif it.startswith("[") and it.endswith("]"):
                cur.append(it[1:-1])
                if len(cur) == ncols:
                    seq.append(("row", cur))
                    cur = []
            else:
                raise Typ2TexError(f"{where}: Unsupported table item: {it[:60]!r}")
        if cur:
            _require(len(cur) == ncols, f"{where}: Trailing incomplete table row ({len(cur)} != {ncols} cols)")
            seq.append(("row", cur))
        return seq

    return {
        "cols": cols,
        "aligns": aligns,
        "header": _chunk_rows(header_items),
        "body": _chunk_rows(body_items),
    }


def _render_table_latex(
    table_info: dict,
    size_cmd: str,
    convert_cell,
    *,
    as_longtable: bool = False,
    caption_tex: str | None = None,
    label_id: str | None = None,
) -> str:
    colspec, use_tabularx = _build_colspec(
        table_info["cols"], table_info["aligns"], force_longtable=as_longtable
    )

    def _fmt_seq(seq) -> list[str]:
        lines: list[str] = []
        for kind, payload in seq:
            if kind == "rule":
                lines.append(payload)
            else:
                cells = [convert_cell(c).strip() for c in payload]
                lines.append(" & ".join(cells) + r" \\")
        return lines

    header_lines = _fmt_seq(table_info["header"])
    body_lines = _fmt_seq(table_info["body"])

    if as_longtable:
        out: list[str] = []
        if size_cmd:
            out.append("{" + size_cmd)
        out.append(rf"\begin{{longtable}}{{{colspec}}}")
        if caption_tex is not None:
            lbl = rf"\label{{{label_id}}}" if label_id else ""
            out.append(rf"\caption{{{caption_tex}}}{lbl} \\")
        if header_lines:
            out.extend(header_lines)
            out.append(r"\endfirsthead")
            out.extend(header_lines)
            out.append(r"\endhead")
        out.extend(body_lines)
        out.append(r"\end{longtable}")
        if size_cmd:
            out.append("}")
        return "\n".join(out)

    env_open = rf"\begin{{tabularx}}{{\linewidth}}{{{colspec}}}" if use_tabularx else rf"\begin{{tabular}}{{{colspec}}}"
    env_close = r"\end{tabularx}" if use_tabularx else r"\end{tabular}"
    lines = [env_open, *header_lines, *body_lines, env_close]
    inner = "\n".join(lines)
    if size_cmd:
        return "{" + size_cmd + "\n" + inner + "\n}"
    return inner


# ---------------------------------------------------------------------------
# Document / Prose / Block Converter
# ---------------------------------------------------------------------------

class TypstToLatexConverter:
    def __init__(
        self,
        *,
        root: Path,
        surface: str,
        current_typ: Path,
        unit_map: dict[str, str],
        diagram_format: str,
        used_rasters: set[str],
        used_diagrams: set[str],
    ):
        self.root = root
        self.surface = surface  # "main" or "manual"
        self.current_typ = current_typ
        self.where = current_typ.relative_to(root).as_posix()
        self.unit_map = unit_map  # canonical typst relpath -> latex relpath (relative to outdir)
        self.diagram_format = diagram_format
        self.used_rasters = used_rasters
        self.used_diagrams = used_diagrams

    def _rel_to_surface_latex_dir(self, latex_rel: str) -> str:
        """Express a path relative to latex/ (Main) or latex/manual/ (Manual)."""
        if self.surface == "main":
            return latex_rel
        if latex_rel.startswith("manual/"):
            return latex_rel[len("manual/"):]
        return "../" + latex_rel

    def _resolve_include_to_latex(self, rel_arg: str) -> tuple[str, str]:
        """Resolve a Typst #include path. Returns (kind, target):
        ('diagram', 'figures/generated/<slug>.<ext>') or ('tex', '<rel_tex_path>').
        """
        m_diag = DIAGRAM_INCLUDE_RE.match(rel_arg)
        if m_diag:
            mod = m_diag.group(1)
            comp_rel = f"typst/lib/diagrams/{mod}"
            self.used_diagrams.add(comp_rel)
            slug = mod[:-4].replace("_", "-")
            return "diagram", f"figures/generated/{slug}.{self.diagram_format}"
        resolved = (self.current_typ.parent / rel_arg).resolve()
        _require(resolved.is_relative_to(self.root), f"{self.where}: Include escapes root: {rel_arg}")
        typ_rel = resolved.relative_to(self.root).as_posix()
        _require(typ_rel in self.unit_map, f"{self.where}: Unmapped Typst include: {typ_rel}")
        return "tex", self._rel_to_surface_latex_dir(self.unit_map[typ_rel])

    def _resolve_image_to_latex(self, raw_path: str) -> str:
        rel = raw_path.lstrip("/")
        src = (self.root / rel).resolve()
        _require(src.is_file() and src.is_relative_to(self.root), f"{self.where}: Missing image asset: {raw_path}")
        self.used_rasters.add(rel)
        return self._rel_to_surface_latex_dir(rel)

    def _width_to_latex(self, w_raw: str | None) -> str:
        if not w_raw:
            return r"\linewidth"
        s = w_raw.strip()
        m_pct = re.match(r"^([0-9]+(?:\.[0-9]+)?)%$", s)
        if m_pct:
            frac = float(m_pct.group(1)) / 100.0
            return rf"{frac:.2f}\linewidth"
        if re.match(r"^[0-9]+(?:\.[0-9]+)?(cm|mm|pt|in|em)$", s):
            return s
        raise Typ2TexError(f"{self.where}: Unsupported width expression: {w_raw!r}")

    def _extract_code_block_table(self, content: str) -> tuple[dict, str] | None:
        """Detect #{ set text(size: ...); set par(...); table(...) } or bare table(...)."""
        s = content.strip()
        size_cmd = ""
        if s.startswith("#{"):
            blk, end = scan_balanced(s, 1, "{", "}", self.where)
            if s[end:].strip():
                return None
            s = blk.strip()
        m_sz = re.search(r"set\s+text\(\s*size:\s*([0-9.]+pt)\s*\)", s)
        if m_sz:
            size_cmd = _font_size_cmd(m_sz.group(1))
        m_tab = re.search(r"\btable\(", s)
        if not m_tab:
            return None
        t_args, _ = scan_balanced(s, m_tab.end() - 1, "(", ")", self.where)
        return _parse_table_call(t_args, self.where), size_cmd

    def _extract_trailing_label(self, text: str, pos: int) -> tuple[str | None, int]:
        """Consume optional whitespace + <label> immediately following a block."""
        j = pos
        n = len(text)
        while j < n and text[j] in " \t":
            j += 1
        if j < n and text[j] == "<":
            m = re.match(r"<([A-Za-z0-9:._-]+)>", text[j:])
            if m:
                return m.group(1), j + len(m.group(0))
        return None, pos

    def convert_inline(self, text: str, *, base_line: int = 1, for_heading: bool = False) -> str:
        """Convert inline Typst content (prose, inline math, refs, cites, formatting)."""
        out: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            # Line break `\` at EOL (outside math)
            if ch == "\\":
                if i + 1 < n and text[i + 1] == "\n":
                    out.append(r" \\" + "\n")
                    i += 2
                    continue
                if i + 1 < n and text[i + 1] in " \t":
                    # Check if rest of line is spaces before newline
                    j = i + 1
                    while j < n and text[j] in " \t":
                        j += 1
                    if j == n or text[j] == "\n":
                        out.append(r" \\")
                        i = j
                        continue
                if i + 1 < n:
                    nxt = text[i + 1]
                    out.append(escape_latex_text(nxt))
                    i += 2
                    continue
                i += 1
                continue
            # Math span $...$
            if ch == "$":
                span_line = base_line + line_at(text, i) - 1
                span_where = f"{self.where}:{span_line}"
                mbody, nxt = scan_math_span(text, i, span_where)
                i = nxt
                is_display = len(mbody) >= 2 and mbody[0].isspace() and mbody[-1].isspace()
                tex_math = convert_math(
                    mbody,
                    span_where,
                    lambda s, _bl=span_line: self.convert_inline(s, base_line=_bl),
                )
                if is_display:
                    lbl, i = self._extract_trailing_label(text, i)
                    out.append(self._wrap_numbered_display(tex_math, lbl))
                elif for_heading:
                    pdf_str = _math_to_pdf_string(mbody, span_where)
                    # Escape braces/backslashes in PDF string if any
                    pdf_str_safe = (
                        pdf_str.replace("\\", "")
                        .replace("{", "")
                        .replace("}", "")
                        .replace("#", r"\#")
                        .replace("%", r"\%")
                    )
                    out.append(rf"\texorpdfstring{{${tex_math}$}}{{{pdf_str_safe}}}")
                else:
                    out.append(f"${tex_math}$")
                continue
            # Hash call
            if ch == "#":
                frag, nxt = self._convert_hash(text, i, base_line=base_line)
                out.append(frag)
                i = nxt
                continue
            # Inline strong *...* (only when matching closing * on same paragraph without spaces inside edges)
            if ch == "*" and i + 1 < n and not text[i + 1].isspace():
                end_s = self._find_inline_delim(text, i + 1, "*")
                if end_s is not None:
                    sub_line = base_line + line_at(text, i + 1) - 1
                    out.append(
                        r"\textbf{"
                        + self.convert_inline(text[i + 1 : end_s], base_line=sub_line, for_heading=for_heading)
                        + "}"
                    )
                    i = end_s + 1
                    continue
            # Inline emph _..._ (only at word boundary, not inside snake_case identifiers)
            if ch == "_" and (i == 0 or not text[i - 1].isalnum()) and i + 1 < n and not text[i + 1].isspace():
                end_e = self._find_inline_delim(text, i + 1, "_")
                if end_e is not None and (end_e + 1 >= n or not text[end_e + 1].isalnum()):
                    sub_line = base_line + line_at(text, i + 1) - 1
                    out.append(
                        r"\emph{"
                        + self.convert_inline(text[i + 1 : end_e], base_line=sub_line, for_heading=for_heading)
                        + "}"
                    )
                    i = end_e + 1
                    continue
            # Plain character
            out.append(escape_latex_text(ch))
            i += 1
        return "".join(out)

    def _find_inline_delim(self, text: str, start: int, delim: str) -> int | None:
        i = start
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "\n" and i + 1 < n and text[i + 1] == "\n":
                return None
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == "$":
                _, i = scan_math_span(text, i, self.where)
                continue
            if ch == delim and i > start and not text[i - 1].isspace():
                return i
            i += 1
        return None

    @staticmethod
    def _top_level_math_structure(tex_math: str) -> tuple[bool, bool]:
        """Detect top-level \\\\ and & outside {...} groups and \\begin{...}...\\end{...}."""
        has_nl = False
        has_amp = False
        brace_depth = 0
        env_depth = 0
        i = 0
        n = len(tex_math)
        while i < n:
            if tex_math.startswith(r"\begin{", i):
                env_depth += 1
                end_b = tex_math.find("}", i + 7)
                i = (end_b + 1) if end_b != -1 else i + 7
                continue
            if tex_math.startswith(r"\end{", i):
                env_depth = max(0, env_depth - 1)
                end_b = tex_math.find("}", i + 5)
                i = (end_b + 1) if end_b != -1 else i + 5
                continue
            if tex_math[i] == "\\":
                if i + 1 < n and tex_math[i + 1] == "\\":
                    if brace_depth == 0 and env_depth == 0:
                        has_nl = True
                    i += 2
                    continue
                i += 2
                continue
            if tex_math[i] == "{":
                brace_depth += 1
            elif tex_math[i] == "}":
                brace_depth = max(0, brace_depth - 1)
            elif tex_math[i] == "&" and brace_depth == 0 and env_depth == 0:
                has_amp = True
            i += 1
        return has_nl, has_amp

    def _wrap_numbered_display(self, tex_math: str, lbl: str | None) -> str:
        lbl_tex = rf"\label{{{lbl}}}" if lbl else ""
        has_nl, has_amp = self._top_level_math_structure(tex_math)
        if has_nl and has_amp:
            return f"\\begin{{equation}}{lbl_tex}\n\\begin{{aligned}}\n{tex_math}\n\\end{{aligned}}\n\\end{{equation}}"
        if has_nl:
            return f"\\begin{{equation}}{lbl_tex}\n\\begin{{gathered}}\n{tex_math}\n\\end{{gathered}}\n\\end{{equation}}"
        if has_amp:
            return f"\\begin{{equation}}{lbl_tex}\n\\begin{{aligned}}\n{tex_math}\n\\end{{aligned}}\n\\end{{equation}}"
        return f"\\begin{{equation}}{lbl_tex}\n{tex_math}\n\\end{{equation}}"

    def _wrap_unnumbered_display(self, tex_math: str) -> str:
        has_nl, has_amp = self._top_level_math_structure(tex_math)
        if has_nl and has_amp:
            return f"\\begin{{align*}}\n{tex_math}\n\\end{{align*}}"
        if has_nl:
            return f"\\begin{{gather*}}\n{tex_math}\n\\end{{gather*}}"
        if has_amp:
            return f"\\begin{{align*}}\n{tex_math}\n\\end{{align*}}"
        return f"\\[\n{tex_math}\n\\]"

    def _convert_hash(self, text: str, start: int, *, base_line: int = 1) -> tuple[str, int]:
        n = len(text)
        cur_line = base_line + line_at(text, start) - 1
        loc = f"{self.where}:{cur_line}"
        # Code block #{ ... } (tables or inline set text)
        if start + 1 < n and text[start + 1] == "{":
            blk, nxt = scan_balanced(text, start + 1, "{", "}", loc)
            tinfo = self._extract_code_block_table("#{" + blk + "}")
            if tinfo is not None:
                tab, sz = tinfo
                return _render_table_latex(
                    tab, sz, lambda s, _bl=cur_line: self.convert_inline(s, base_line=_bl)
                ), nxt
            raise Typ2TexError(f"{loc}: Unsupported Typst code block #{{...}}")

        m = re.match(r"#([A-Za-z_][A-Za-z0-9_.-]*)", text[start:])
        _require(m is not None, f"{loc}: Unexpected '#' token: {text[start:start+20]!r}")
        name = m.group(1)
        pos = start + len(m.group(0))

        # Bare symbol / constant references (no args)
        if name == "SADARop":
            return r"$\SADARop$", pos
        if name == "AODDocumentAuthor":
            return r"\AODDocumentAuthor", pos
        if name == "AODDocumentDate":
            return r"\AODDocumentDate", pos

        # Directive statements ending at EOL
        if name in ("import", "show", "set", "let"):
            eol = text.find("\n", pos)
            end = n if eol == -1 else eol + 1
            stmt = text[start:end].strip()
            if name == "import":
                return "", end
            if name == "show" and re.match(r"#show:\s*aod-(?:main|manual)-doc\b", stmt):
                return "", end
            if name == "set" and "aod-appendix-numbering" in stmt:
                return "", end
            if name == "set" and re.match(r"#set\s+text\(\s*size:\s*([0-9.]+pt)\s*\)\s*;?", stmt):
                m_semi = re.match(r"#set\s+text\(\s*size:\s*([0-9.]+pt)\s*\)\s*;?\s*", text[start:])
                return _font_size_cmd(m_semi.group(1)) + " ", start + len(m_semi.group(0))
            raise Typ2TexError(f"{loc}: Unsupported Typst directive: {stmt[:80]!r}")

        if name == "include":
            m_inc = re.match(r'\s*"([^"]+)"', text[pos:])
            _require(m_inc is not None, f"{loc}: Malformed #include statement")
            kind, target = self._resolve_include_to_latex(m_inc.group(1))
            nxt = pos + len(m_inc.group(0))
            if kind == "diagram":
                return rf"\includegraphics[width=\linewidth]{{{target}}}", nxt
            return rf"\input{{{target}}}", nxt

        # Handle counter(page).update(1)
        if name == "counter":
            m_cnt = re.match(r"\(page\)\.update\((\d+)\)", text[pos:])
            _require(m_cnt is not None, f"{loc}: Unsupported #counter expression")
            return rf"\setcounter{{page}}{{{m_cnt.group(1)}}}", pos + len(m_cnt.group(0))

        # Parse optional (...) and optional [...] trailing content arguments
        paren_arg: str | None = None
        paren_line = cur_line
        brack_args: list[str] = []
        brack_lines: list[int] = []
        if pos < n and text[pos] == "(":
            paren_line = base_line + line_at(text, pos) - 1
            paren_arg, pos = scan_balanced(text, pos, "(", ")", loc)
        while pos < n and text[pos] == "[":
            b_line = base_line + line_at(text, pos) - 1
            b_arg, pos = scan_balanced(text, pos, "[", "]", loc)
            brack_args.append(b_arg)
            brack_lines.append(b_line)

        # ---- Reference helpers ----
        if name in ("eqref", "eqnref", "secref", "appref", "figref", "tabref",
                    "bare-ref", "mainequation", "mainsection", "mainappendix", "maintable"):
            _require(paren_arg is not None, f"{loc}: #{name} requires (...)")
            pargs, _ = parse_call_args(paren_arg, loc)
            _require(len(pargs) == 1, f"{loc}: #{name} expects 1 argument")
            target = unquote_typst_string(pargs[0], loc)
            cmd = "ref" if name == "bare-ref" else name
            return rf"\{cmd}{{{target}}}", pos

        # ---- Citations ----
        if name == "aod-cite":
            _require(paren_arg is not None, f"{loc}: #aod-cite requires (...)")
            pargs, nargs = parse_call_args(paren_arg, loc)
            _require(len(pargs) == 1, f"{loc}: #aod-cite expects key string")
            keys = ",".join(k.strip() for k in unquote_typst_string(pargs[0], loc).split(",") if k.strip())
            if "supplement" in nargs:
                sup_raw = nargs["supplement"].strip()
                if sup_raw.startswith("[") and sup_raw.endswith("]"):
                    sup_tex = self.convert_inline(sup_raw[1:-1], base_line=paren_line)
                else:
                    sup_tex = escape_latex_text(unquote_typst_string(sup_raw, loc))
                return rf"\cite[{sup_tex}]{{{keys}}}", pos
            return rf"\cite{{{keys}}}", pos

        # ---- Raw literal / link / inline emphasis / strong ----
        if name == "raw":
            _require(paren_arg is not None, f"{loc}: #raw requires (...)")
            pargs, _ = parse_call_args(paren_arg, loc)
            _require(len(pargs) == 1, f"{loc}: #raw expects 1 string argument")
            val = unquote_typst_string(pargs[0], loc)
            return rf"\texttt{{{escape_latex_text(val, in_texttt=True)}}}", pos

        if name == "link":
            _require(paren_arg is not None and len(brack_args) == 1, f"{loc}: #link expects (url)[text]")
            pargs, _ = parse_call_args(paren_arg, loc)
            url = escape_latex_href_url(unquote_typst_string(pargs[0], loc))
            body = self.convert_inline(brack_args[0], base_line=brack_lines[0])
            return rf"\href{{{url}}}{{{body}}}", pos

        if name == "emph":
            _require(len(brack_args) == 1, f"{loc}: #emph expects [...]")
            return rf"\emph{{{self.convert_inline(brack_args[0], base_line=brack_lines[0])}}}", pos

        if name == "strong":
            _require(len(brack_args) == 1, f"{loc}: #strong expects [...]")
            return rf"\textbf{{{self.convert_inline(brack_args[0], base_line=brack_lines[0])}}}", pos

        if name == "text":
            _require(paren_arg is not None and len(brack_args) == 1, f"{loc}: #text expects (...)[...]")
            _, nargs = parse_call_args(paren_arg, loc)
            body = self.convert_inline(brack_args[0], base_line=brack_lines[0])
            prefix = ""
            if "size" in nargs:
                m_pt = re.match(r"([0-9.]+)pt", nargs["size"].strip())
                if m_pt:
                    pt = float(m_pt.group(1))
                    if pt >= 16:
                        prefix += r"\LARGE "
                    elif pt >= 13.5:
                        prefix += r"\Large "
                    elif pt >= 11.5:
                        prefix += r"\large "
                    elif pt <= 9.5:
                        prefix += r"\small "
            if "style" in nargs and "italic" in nargs["style"]:
                prefix += r"\itshape "
            if "weight" in nargs and "bold" in nargs["weight"]:
                prefix += r"\bfseries "
            return ("{" + prefix + body + "}") if prefix else body, pos

        # ---- Structural AOD helpers ----
        if name == "aod-paragraph":
            _require(len(brack_args) == 1, f"{loc}: #aod-paragraph expects [...]")
            return rf"\paragraph{{{self.convert_inline(brack_args[0], base_line=brack_lines[0]).strip()}}}", pos

        if name == "aod-anchor":
            _require(paren_arg is not None, f"{loc}: #aod-anchor requires (<label>)")
            s = paren_arg.strip()
            m_lbl = re.match(r"^<([A-Za-z0-9:._-]+)>$", s)
            _require(m_lbl is not None, f"{loc}: #aod-anchor expects <label>, got {s!r}")
            return rf"\label{{{m_lbl.group(1)}}}", pos

        if name == "aod-definition":
            _require(len(brack_args) == 1, f"{loc}: #aod-definition expects body [...]")
            title_opt = ""
            if paren_arg:
                _, nargs = parse_call_args(paren_arg, loc)
                if "title" in nargs:
                    t_raw = nargs["title"].strip()
                    t_tex = (
                        self.convert_inline(t_raw[1:-1], base_line=paren_line)
                        if t_raw.startswith("[")
                        else escape_latex_text(unquote_typst_string(t_raw, loc))
                    )
                    title_opt = f"[{t_tex}]"
            body = self.convert_document_body(brack_args[0], base_line=brack_lines[0]).strip()
            return f"\\begin{{definition}}{title_opt}\n{body}\n\\end{{definition}}", pos

        if name == "aod-provenance":
            _require(len(brack_args) == 1, f"{loc}: #aod-provenance expects [...]")
            return rf"\aodprovenance{{{self.convert_inline(brack_args[0], base_line=brack_lines[0]).strip()}}}", pos

        if name == "aod-literature-note":
            _require(len(brack_args) == 1, f"{loc}: #aod-literature-note expects [...]")
            return rf"\aodliteraturenote{{{self.convert_inline(brack_args[0], base_line=brack_lines[0]).strip()}}}", pos

        if name == "aod-remark":
            _require(len(brack_args) == 1, f"{loc}: #aod-remark expects [...]")
            return rf"\aodremark{{{self.convert_inline(brack_args[0], base_line=brack_lines[0]).strip()}}}", pos

        if name == "aod-noteblock":
            _require(paren_arg is not None and len(brack_args) == 1, f"{loc}: #aod-noteblock expects (title)[body]")
            pargs, _ = parse_call_args(paren_arg, loc)
            title = escape_latex_text(unquote_typst_string(pargs[0], loc))
            body = self.convert_inline(brack_args[0], base_line=brack_lines[0]).strip()
            return rf"\aodnoteblock{{{title}}}{{{body}}}", pos

        if name == "aod-panel":
            _require(len(brack_args) == 1, f"{loc}: #aod-panel expects [...]")
            width = "0.90\\linewidth"
            if paren_arg:
                _, nargs = parse_call_args(paren_arg, loc)
                if "width" in nargs:
                    width = self._width_to_latex(nargs["width"])
            inner = self.convert_document_body(brack_args[0], base_line=brack_lines[0]).strip()
            return f"\\fbox{{\\begin{{minipage}}{{{width}}}\\centering\n{inner}\n\\end{{minipage}}}}", pos

        if name == "aod-boxed":
            _require(paren_arg is not None, f"{loc}: #aod-boxed requires ($...$)")
            s = paren_arg.strip()
            _require(s.startswith("$") and s.endswith("$"), f"{loc}: #aod-boxed expects math $...$")
            tex_math = convert_math(s[1:-1], loc, lambda t, _bl=paren_line: self.convert_inline(t, base_line=_bl))
            return f"\\[\n\\boxed{{{tex_math}}}\n\\]", pos

        # ---- Equations ----
        if name == "math.equation":
            _require(paren_arg is not None, f"{loc}: #math.equation requires (...)")
            pargs, nargs = parse_call_args(paren_arg, loc)
            _require(len(pargs) == 1, f"{loc}: #math.equation expects 1 positional math body")
            ms = pargs[0].strip()
            _require(ms.startswith("$") and ms.endswith("$"), f"{loc}: #math.equation body must be $...$")
            tex_math = convert_math(ms[1:-1], loc, lambda t, _bl=paren_line: self.convert_inline(t, base_line=_bl))
            if nargs.get("numbering") == "none":
                return self._wrap_unnumbered_display(tex_math), pos
            lbl, pos = self._extract_trailing_label(text, pos)
            return self._wrap_numbered_display(tex_math, lbl), pos

        if name == "tagged-eq":
            _require(paren_arg is not None, f"{loc}: #tagged-eq requires (tag, $...$, <lbl>)")
            pargs, _ = parse_call_args(paren_arg, loc)
            _require(len(pargs) == 3, f"{loc}: #tagged-eq expects 3 arguments")
            tag = unquote_typst_string(pargs[0], loc)
            ms = pargs[1].strip()
            _require(ms.startswith("$") and ms.endswith("$"), f"{loc}: #tagged-eq body must be $...$")
            m_lbl = re.match(r"^<([A-Za-z0-9:._-]+)>$", pargs[2].strip())
            _require(m_lbl is not None, f"{loc}: #tagged-eq label must be <id>")
            lbl = m_lbl.group(1)
            tex_math = convert_math(ms[1:-1], loc, lambda t, _bl=paren_line: self.convert_inline(t, base_line=_bl))
            has_nl, has_amp = self._top_level_math_structure(tex_math)
            if has_nl and has_amp:
                return f"\\begin{{equation}}\\tag{{{tag}}}\\label{{{lbl}}}\n\\begin{{aligned}}\n{tex_math}\n\\end{{aligned}}\n\\end{{equation}}", pos
            if has_nl:
                return f"\\begin{{equation}}\\tag{{{tag}}}\\label{{{lbl}}}\n\\begin{{gathered}}\n{tex_math}\n\\end{{gathered}}\n\\end{{equation}}", pos
            return f"\\begin{{equation}}\\tag{{{tag}}}\\label{{{lbl}}}\n{tex_math}\n\\end{{equation}}", pos

        # ---- Figures, Images, and Tables ----
        if name == "image":
            _require(paren_arg is not None, f"{loc}: #image requires (...)")
            pargs, nargs = parse_call_args(paren_arg, loc)
            _require(len(pargs) == 1, f"{loc}: #image expects path string")
            img_tex = self._resolve_image_to_latex(unquote_typst_string(pargs[0], loc))
            w_tex = self._width_to_latex(nargs.get("width"))
            return rf"\includegraphics[width={w_tex}]{{{img_tex}}}", pos

        if name == "aod-uncaptioned-longtable":
            _require(len(brack_args) == 1, f"{loc}: #aod-uncaptioned-longtable expects [...]")
            tinfo = self._extract_code_block_table(brack_args[0])
            _require(tinfo is not None, f"{loc}: #aod-uncaptioned-longtable must contain table(...)")
            tab, sz = tinfo
            return _render_table_latex(
                tab, sz, lambda s, _bl=brack_lines[0]: self.convert_inline(s, base_line=_bl), as_longtable=True
            ), pos

        if name == "figure":
            _require(paren_arg is not None, f"{loc}: #figure requires (...)")
            pargs, nargs = parse_call_args(paren_arg, loc)
            kind = nargs.get("kind", "image").strip()
            body_raw = pargs[0].strip() if pargs else (brack_args[0] if brack_args else "")
            body_line = paren_line if pargs else (brack_lines[0] if brack_lines else cur_line)
            if body_raw.startswith("[") and body_raw.endswith("]"):
                body_raw = body_raw[1:-1]
            cap_raw = nargs.get("caption", "").strip()
            cap_tex = None
            if cap_raw:
                if cap_raw.startswith("[") and cap_raw.endswith("]"):
                    cap_tex = self.convert_inline(cap_raw[1:-1], base_line=paren_line).strip()
                else:
                    cap_tex = escape_latex_text(unquote_typst_string(cap_raw, loc))
            lbl, pos = self._extract_trailing_label(text, pos)

            if kind == "table":
                tinfo = self._extract_code_block_table(body_raw)
                _require(tinfo is not None, f"{loc}: #figure(kind: table) must contain table(...)")
                tab, sz = tinfo
                body_row_cnt = sum(1 for k, _ in tab["body"] if k == "row")
                uses_fr = any(c.endswith("fr") for c in tab["cols"])
                if uses_fr and body_row_cnt >= 24:
                    return _render_table_latex(
                        tab, sz, lambda s, _bl=body_line: self.convert_inline(s, base_line=_bl),
                        as_longtable=True, caption_tex=cap_tex, label_id=lbl,
                    ), pos
                inner = _render_table_latex(
                    tab, sz, lambda s, _bl=body_line: self.convert_inline(s, base_line=_bl), as_longtable=False
                )
                lines = [r"\begin{table}[H]", r"\centering"]
                if cap_tex is not None:
                    lines.append(rf"\caption{{{cap_tex}}}")
                if lbl:
                    lines.append(rf"\label{{{lbl}}}")
                lines.append(inner)
                lines.append(r"\end{table}")
                return "\n".join(lines), pos

            if kind == "image":
                inner = self.convert_document_body(body_raw, base_line=body_line).strip()
                lines = [r"\begin{figure}[H]", r"\centering", inner]
                if cap_tex is not None:
                    lines.append(rf"\caption{{{cap_tex}}}")
                if lbl:
                    lines.append(rf"\label{{{lbl}}}")
                lines.append(r"\end{figure}")
                return "\n".join(lines), pos

            raise Typ2TexError(f"{loc}: Unsupported #figure kind: {kind!r}")

        # ---- Layout / Document driver helpers ----
        if name == "align":
            _require(paren_arg is not None and len(brack_args) == 1, f"{loc}: #align expects (pos)[body]")
            where_a = paren_arg.strip()
            env = {"center": "center", "left": "flushleft", "right": "flushright"}.get(where_a)
            _require(env is not None, f"{loc}: Unsupported #align direction: {where_a!r}")
            inner = self.convert_document_body(brack_args[0], base_line=brack_lines[0]).strip()
            return f"\\begin{{{env}}}\n{inner}\n\\end{{{env}}}", pos

        if name == "page":
            _require(len(brack_args) == 1, f"{loc}: #page expects [...]")
            inner = self.convert_document_body(brack_args[0], base_line=brack_lines[0]).strip()
            return f"\\begin{{titlepage}}\n{inner}\n\\end{{titlepage}}", pos

        if name == "block":
            _require(len(brack_args) == 1, f"{loc}: #block expects [...]")
            raw_b = brack_args[0]
            b_line = brack_lines[0]
            # Recognize the canonical Abstract block in 01_abstract.typ
            m_abs = re.search(r"#align\(center\)\[\*Abstract\*\]\s*#pad\([^)]*\)\[", raw_b)
            if m_abs:
                pad_line = b_line + line_at(raw_b, m_abs.end() - 1) - 1
                pad_inner, _ = scan_balanced(raw_b, m_abs.end() - 1, "[", "]", loc)
                abs_body = self.convert_document_body(pad_inner, base_line=pad_line).strip()
                return f"\\begin{{abstract}}\n{abs_body}\n\\end{{abstract}}", pos
            return self.convert_document_body(raw_b, base_line=b_line).strip(), pos

        if name == "pad":
            _require(len(brack_args) == 1, f"{loc}: #pad expects [...]")
            inner = self.convert_document_body(brack_args[0], base_line=brack_lines[0]).strip()
            return f"\\begin{{quote}}\n{inner}\n\\end{{quote}}", pos

        if name == "v":
            _require(paren_arg is not None, f"{loc}: #v requires (length)")
            val = paren_arg.strip()
            if val == "1fr":
                return "\n\\par\\vspace*{\\fill}\n", pos
            if val == "2fr":
                return "\n\\par\\vspace*{\\fill}\\vspace*{\\fill}\n", pos
            if re.match(r"^[0-9.]+(em|pt|cm|mm)$", val):
                return f"\n\\par\\vspace{{{val}}}\\par\n", pos
            raise Typ2TexError(f"{loc}: Unsupported #v length: {val!r}")

        if name == "outline":
            return r"\tableofcontents", pos

        if name == "pagebreak":
            return r"\clearpage", pos

        if name == "aod-start-appendix":
            return r"\appendix", pos

        if name == "aod-render-bibliography":
            return "\\nocite{*}\n\\bibliographystyle{plain}\n\\bibliography{refs}", pos

        raise Typ2TexError(f"{loc}: Unsupported Typst construct: #{name}")

    def convert_document_body(self, raw_text: str, *, base_line: int = 1) -> str:
        """Convert block-level Typst document body into clean LaTeX."""
        text = strip_typst_comments(raw_text)
        out: list[str] = []
        i = 0
        n = len(text)

        while i < n:
            # Skip blank/whitespace runs while preserving paragraph breaks
            if text[i] in " \t\r\n":
                j = i
                nl_count = 0
                while j < n and text[j] in " \t\r\n":
                    if text[j] == "\n":
                        nl_count += 1
                    j += 1
                if nl_count >= 2 and out and not out[-1].endswith("\n\n"):
                    out.append("\n\n")
                elif nl_count == 1 and out and not out[-1].endswith("\n"):
                    out.append("\n")
                i = j
                continue

            at_line_start = (i == 0 or text[i - 1] == "\n" or (out and out[-1].endswith("\n")))

            # Headings at line start: =, ==, ===, ====
            if at_line_start and text[i] == "=":
                m_h = re.match(r"(=+)\s+([^\n]+)", text[i:])
                if m_h:
                    h_line = base_line + line_at(text, i) - 1
                    level = len(m_h.group(1))
                    cmd = {1: "section", 2: "subsection", 3: "subsubsection", 4: "paragraph"}.get(level)
                    _require(cmd is not None, f"{self.where}:{h_line}: Unsupported heading depth {level}")
                    raw_title = m_h.group(2).strip()
                    lbl = None
                    m_lbl = re.search(r"\s*<([A-Za-z0-9:._-]+)>\s*$", raw_title)
                    if m_lbl:
                        lbl = m_lbl.group(1)
                        raw_title = raw_title[: m_lbl.start()].strip()
                    title_tex = self.convert_inline(raw_title, base_line=h_line, for_heading=True)
                    lbl_tex = rf"\label{{{lbl}}}" if lbl else ""
                    out.append(rf"\{cmd}{{{title_tex}}}{lbl_tex}")
                    i += len(m_h.group(0))
                    continue

            # Bullet or numbered list at line start: `- ` or `+ `
            if at_line_start and text[i : i + 2] in ("- ", "+ "):
                marker = text[i : i + 2]
                env = "itemize" if marker == "- " else "enumerate"
                items: list[str] = []
                while i < n and text[i : i + 2] == marker:
                    i += 2
                    item_start = i
                    item_lines: list[str] = []
                    # First line of item
                    eol = text.find("\n", i)
                    if eol == -1:
                        item_lines.append(text[i:])
                        i = n
                    else:
                        item_lines.append(text[i:eol])
                        i = eol + 1
                    # Continuation lines (indented or non-blank non-list non-heading lines)
                    while i < n:
                        if text[i] == "\n":
                            break
                        if text[i : i + 2] in ("- ", "+ "):
                            break
                        if text[i] == "=" and re.match(r"=+\s", text[i:]):
                            break
                        if text[i] == "#" and re.match(r"#(?:aod-|figure|math\.equation|tagged-eq|align|include|pagebreak)", text[i:]):
                            break
                        eol2 = text.find("\n", i)
                        if eol2 == -1:
                            item_lines.append(text[i:])
                            i = n
                        else:
                            item_lines.append(text[i:eol2])
                            i = eol2 + 1
                    raw_item = "\n".join(item_lines)
                    lead_ws = len(raw_item) - len(raw_item.lstrip())
                    item_line = base_line + line_at(text, item_start) - 1 + raw_item[:lead_ws].count("\n")
                    items.append(self.convert_inline(raw_item.strip(), base_line=item_line))
                    # Skip single blank lines between items of the same list
                    j = i
                    while j < n and text[j] in " \t\r\n":
                        j += 1
                    if j < n and text[j : j + 2] == marker:
                        i = j
                    else:
                        break
                out.append(
                    f"\\begin{{{env}}}\n"
                    + "\n".join(f"\\item {it}" for it in items)
                    + f"\n\\end{{{env}}}"
                )
                continue

            # Block-level #... construct (inline calls like #raw/#secref stay in prose paragraphs)
            _block_hash = (
                r"#(?:aod-definition|aod-provenance|aod-literature-note|aod-remark|"
                r"aod-noteblock|aod-paragraph|aod-anchor|aod-panel|aod-boxed|"
                r"aod-uncaptioned-longtable|aod-start-appendix|aod-render-bibliography|"
                r"figure|math\.equation|tagged-eq|align|block|pad|page|pagebreak|"
                r"outline|include|import|show|set|counter|v|\{)"
            )
            if text[i] == "#" and re.match(_block_hash, text[i:]):
                frag, nxt = self._convert_hash(text, i, base_line=base_line)
                if frag:
                    out.append(frag)
                i = nxt
                continue

            # Standalone display equation $ ... $ <lbl>
            if text[i] == "$":
                eq_line = base_line + line_at(text, i) - 1
                eq_where = f"{self.where}:{eq_line}"
                mbody, nxt = scan_math_span(text, i, eq_where)
                is_display = len(mbody) >= 2 and mbody[0].isspace() and mbody[-1].isspace()
                if is_display:
                    i = nxt
                    lbl, i = self._extract_trailing_label(text, i)
                    tex_math = convert_math(
                        mbody,
                        eq_where,
                        lambda s, _bl=eq_line: self.convert_inline(s, base_line=_bl),
                    )
                    out.append(self._wrap_numbered_display(tex_math, lbl))
                    continue

            # Ordinary prose paragraph chunk up to next blank line or block boundary
            para_start = i
            while i < n:
                if text[i] == "\n":
                    if i + 1 < n and text[i + 1] == "\n":
                        break
                    nxt_line = text[i + 1 :].lstrip(" \t")
                    if (
                        nxt_line.startswith(("- ", "+ "))
                        or re.match(r"=+\s", nxt_line)
                        or re.match(_block_hash, nxt_line)
                        or re.match(r"\$ ", nxt_line)
                    ):
                        break
                    i += 1
                    continue
                if text[i] == "$":
                    cur_where = f"{self.where}:{base_line + line_at(text, i) - 1}"
                    _, i = scan_math_span(text, i, cur_where)
                    continue
                if text[i] == "#" and i + 1 < n:
                    m_hc = re.match(r"#([A-Za-z_][A-Za-z0-9_.-]*)", text[i:])
                    if m_hc:
                        cur_where = f"{self.where}:{base_line + line_at(text, i) - 1}"
                        p = i + len(m_hc.group(0))
                        if p < n and text[p] == "(":
                            _, p = scan_balanced(text, p, "(", ")", cur_where)
                        while p < n and text[p] == "[":
                            _, p = scan_balanced(text, p, "[", "]", cur_where)
                        i = p
                        continue
                i += 1
            raw_chunk = text[para_start:i]
            lead_ws = len(raw_chunk) - len(raw_chunk.lstrip())
            chunk = raw_chunk.strip()
            if chunk:
                chunk_line = base_line + line_at(text, para_start + lead_ws) - 1
                out.append(self.convert_inline(chunk, base_line=chunk_line))

        result = "".join(out).strip() + "\n"
        # Clean excessive blank lines while preserving clean paragraph separation
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result


# ---------------------------------------------------------------------------
# Controlled Preamble Templates (consuming canonical Typst metadata)
# ---------------------------------------------------------------------------

def _read_typst_metadata(root: Path) -> dict:
    schema_txt = (root / "typst/lib/aod_schema.typ").read_text(encoding="utf-8")
    m_author = re.search(r'#let\s+AODDocumentAuthor\s*=\s*"([^"]+)"', schema_txt)
    m_date = re.search(r'#let\s+AODDocumentDate\s*=\s*"([^"]+)"', schema_txt)
    _require(m_author is not None and m_date is not None, "Missing author/date in typst/lib/aod_schema.typ")

    def _parse_preamble(rel: str) -> dict:
        txt = (root / rel).read_text(encoding="utf-8")
        m_title = re.search(r'\btitle:\s*"([^"]+)"', txt)
        m_subj = re.search(r'\bsubject:\s*"([^"]+)"', txt)
        m_kw_block = re.search(r'\bkeywords:\s*\(([^)]+)\)', txt, re.S)
        _require(m_title and m_subj and m_kw_block, f"Missing metadata in {rel}")
        kws = re.findall(r'"([^"]+)"', m_kw_block.group(1))
        return {
            "title": m_title.group(1),
            "subject": m_subj.group(1),
            "keywords": ", ".join(kws),
        }

    return {
        "author": m_author.group(1),
        "date": m_date.group(1),
        "main": _parse_preamble("typst/preamble.typ"),
        "manual": _parse_preamble("typst/manual/preamble.typ"),
    }


def _generated_header(source_typ: str) -> str:
    return (
        f"% GENERATED FROM {source_typ} BY scripts/typ2tex.py (v{GENERATOR_VERSION}) — DO NOT EDIT.\n"
        f"% Edit canonical Typst under typst/ and regenerate with: python3 scripts/typ2tex.py --root . --outdir latex\n\n"
    )


def render_main_preamble(meta: dict) -> str:
    m = meta["main"]
    return _generated_header("typst/preamble.typ") + f"""\\usepackage[margin=0.85in]{{geometry}}
\\usepackage{{amsmath,amssymb,amsthm}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs,longtable,array}}
\\usepackage{{tabularx}}
\\usepackage{{float}}
\\usepackage{{xcolor}}
\\usepackage[hidelinks]{{hyperref}}

\\hypersetup{{
  pdftitle={{{m["title"]}}},
  pdfauthor={{{meta["author"]}}},
  pdfsubject={{{m["subject"]}}},
  pdfkeywords={{{m["keywords"]}}}
}}
\\usepackage{{enumitem}}
\\usepackage{{caption}}
\\usepackage{{microtype}}
\\setcounter{{secnumdepth}}{{3}}
\\setcounter{{tocdepth}}{{3}}
\\setlength{{\\parskip}}{{0.55em}}
\\setlength{{\\parindent}}{{0pt}}
\\graphicspath{{{{./}}}}

\\newcommand{{\\AODDocumentAuthor}}{{{meta["author"]}}}
\\newcommand{{\\AODDocumentDate}}{{{meta["date"]}}}
\\makeatletter
\\renewcommand*\\l@section{{\\@dottedtocline{{1}}{{0em}}{{2.6em}}}}
\\renewcommand*\\l@subsection{{\\@dottedtocline{{2}}{{1.6em}}{{3.9em}}}}
\\renewcommand*\\l@subsubsection{{\\@dottedtocline{{3}}{{4.0em}}{{5.0em}}}}
\\makeatother

\\newcommand{{\\Null}}{{\\mathcal{{N}}}}
\\newcommand{{\\infD}}{{\\infty_{{\\mathcal{{D}}}}}}
\\newcommand{{\\Qfour}}{{Q_4}}
\\newcommand{{\\RCD}}{{\\mathrm{{RCD}}}}
\\newcommand{{\\SADAR}}{{\\mathrm{{SADAR}}}}
\\newcommand{{\\ADAR}}{{\\mathrm{{ADAR}}}}
\\newcommand{{\\AO}}{{A{{\\leftrightarrow}}\\Omega}}
\\newcommand{{\\AOpkg}}{{\\operatorname{{A\\leftrightarrow_{{\\mu}}\\Omega}}}}
\\newcommand{{\\OAop}}{{\\operatorname{{\\Omega\\leftrightarrow_{{\\mu}}A}}}}
\\newcommand{{\\AOh}}{{\\mathsf{{AO}}_{{\\mu}}}}
\\newcommand{{\\OAh}}{{\\mathsf{{OA}}_{{\\mu}}}}
\\newcommand{{\\AOcycle}}{{A{{\\leftrightarrow_{{\\mu}}}}\\Omega\\;\\longleftrightarrow\\;\\Omega{{\\leftrightarrow_{{\\mu}}}}A}}
\\newcommand{{\\SADARop}}{{\\mathfrak S}}
\\newcommand{{\\Qext}}{{\\mathsf{{Q}}_{{\\mathrm{{ext}}}}}}
\\newcommand{{\\secref}}[1]{{\\S\\ref{{#1}}}}
\\newcommand{{\\appref}}[1]{{App.~\\ref{{#1}}}}
\\newcommand{{\\eqnref}}[1]{{\\eqref{{#1}}}}
\\newcommand{{\\figref}}[1]{{Fig.~\\ref{{#1}}}}
\\newcommand{{\\tabref}}[1]{{Table~\\ref{{#1}}}}

\\newcommand{{\\aodnoteblock}}[2]{{\\medskip\\begingroup\\emergencystretch=3em\\sloppy\\noindent\\emph{{#1.}}\\ #2\\par\\endgroup}}
\\newcommand{{\\aodprovenance}}[1]{{\\aodnoteblock{{Provenance}}{{#1}}}}
\\newcommand{{\\aodliteraturenote}}[1]{{\\aodnoteblock{{Literature note}}{{#1}}}}
\\newcommand{{\\aodremark}}[1]{{\\aodnoteblock{{Remark}}{{#1}}}}

\\newtheorem{{definition}}{{Definition}}
\\newtheorem{{consequence}}{{Consequence}}
\\newtheorem{{remark}}{{Remark}}

\\setlength{{\\emergencystretch}}{{2em}}
"""


def render_manual_preamble(meta: dict) -> str:
    m = meta["manual"]
    return _generated_header("typst/manual/preamble.typ") + f"""\\usepackage[margin=0.85in]{{geometry}}
\\usepackage{{amsmath,amssymb,amsthm}}
\\usepackage{{booktabs,longtable,array,tabularx}}
\\usepackage{{enumitem}}
\\usepackage{{graphicx}}
\\usepackage{{float}}
\\usepackage{{xr-hyper}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{refcount}}
\\usepackage{{bookmark}}
% Main labels retain their complete source keys and display generated Main numbers.
% Build latex/main.tex with latexmk before latex/manual/main.tex.
\\ExplSyntaxOn
\\cs_new_protected:Npn \\aod_main_reference_error:n #1
  {{
    \\PackageError{{aod-mainrefs}}{{#1}}
      {{Build~Main~with~latexmk~from~this~generated~latex~tree~before~Manual.}}
  }}
\\ior_new:N \\l_aod_main_inputs_ior
\\seq_new:N \\l_aod_main_input_seq
\\tl_new:N \\l_aod_main_input_tl
\\tl_new:N \\l_aod_main_anchor_tl
\\tl_new:N \\l_aod_main_number_tl
\\clist_map_inline:nn {{ ../main.aux, ../main.fls }}
  {{
    \\file_if_exist:nF {{#1}}
      {{ \\aod_main_reference_error:n {{Missing~Main~build~file~#1}} }}
  }}
\\ior_open:Nn \\l_aod_main_inputs_ior {{ ../main.fls }}
\\ior_str_map_inline:Nn \\l_aod_main_inputs_ior
  {{
    \\regex_extract_once:nnNT {{ \\A INPUT \\s+ (.+) \\Z }}
      {{#1}} \\l_aod_main_input_seq
      {{
        \\tl_set:Nx \\l_aod_main_input_tl
          {{ \\seq_item:Nn \\l_aod_main_input_seq {{2}} }}
        \\exp_args:NnV \\regex_match:nnT
          {{ \\.(tex|bib|png|jpe?g|eps|pdf) \\Z }} \\l_aod_main_input_tl
          {{
            \\exp_args:NnV \\regex_match:nnF {{ \\A / }} \\l_aod_main_input_tl
              {{ \\tl_put_left:Nn \\l_aod_main_input_tl {{ ../ }} }}
            \\file_if_exist:VTF \\l_aod_main_input_tl
              {{
                \\file_compare_timestamp:VNnT \\l_aod_main_input_tl > {{ ../main.aux }}
                  {{ \\aod_main_reference_error:n {{Stale~Main~AUX:~\\l_aod_main_input_tl}} }}
              }}
              {{ \\aod_main_reference_error:n {{Missing~Main~input~\\l_aod_main_input_tl}} }}
          }}
      }}
  }}
\\ior_close:N \\l_aod_main_inputs_ior
\\file_if_exist:nT {{ ../refs.bib }}
  {{
    \\file_compare_timestamp:nNnT {{ ../refs.bib }} > {{ ../main.aux }}
      {{ \\aod_main_reference_error:n {{Stale~Main~AUX:~../refs.bib}} }}
  }}
\\cs_new_protected:Npn \\aod_main_reference_check:nn #1#2
  {{
    \\regex_match:nnF {{ \\A main: }} {{#1}}
      {{ \\aod_main_reference_error:n {{Unresolved~Main~reference:~#1}} }}
    \\cs_if_exist:cTF {{ r@#1 }}
      {{
        \\tl_set:Nx \\l_aod_main_anchor_tl
          {{ \\getrefbykeydefault{{#1}}{{anchor}}{{}} }}
        \\exp_args:NnV \\regex_match:nnF {{#2}} \\l_aod_main_anchor_tl
          {{ \\aod_main_reference_error:n {{Wrong~Main~reference~type:~#1}} }}
      }}
      {{ \\aod_main_reference_error:n {{Unresolved~Main~reference:~#1}} }}
  }}
\\NewDocumentCommand{{\\mainequation}}{{m}}
  {{
    \\aod_main_reference_check:nn {{#1}}
      {{ \\A (equation\\. ([A-J]\\.)? [0-9]+ (\\.[0-9]+)* | AMS\\. [0-9]+) \\Z }}
    \\exp_args:NnV \\regex_match:nnT {{ \\A AMS\\. }} \\l_aod_main_anchor_tl
      {{
        \\tl_set:Nx \\l_aod_main_number_tl {{ \\getrefnumber{{#1}} }}
        \\tl_set:Nx \\l_aod_main_number_tl
          {{ \\tl_to_str:V \\l_aod_main_number_tl }}
        \\exp_args:NnV \\regex_match:nnF
          {{ \\A (RG[0-9]+|\\{{RG[0-9]+\\}}) \\Z }} \\l_aod_main_number_tl
          {{ \\aod_main_reference_error:n {{Wrong~Main~reference~type:~#1}} }}
      }}
    Main~\\eqref{{#1}}
  }}
\\NewDocumentCommand{{\\mainsection}}{{m}}
  {{
    \\aod_main_reference_check:nn {{#1}}
      {{ \\A (section|subsection|subsubsection)\\. [0-9]+ (\\.[0-9]+)* \\Z }}
    Main~\\S\\ref{{#1}}
  }}
\\NewDocumentCommand{{\\mainappendix}}{{m}}
  {{
    \\aod_main_reference_check:nn {{#1}}
      {{ \\A (appendix|section|subsection|subsubsection)\\. [A-J] (\\.[0-9]+)* \\Z }}
    Main~App.~\\ref{{#1}}
  }}
\\NewDocumentCommand{{\\maintable}}{{m}}
  {{
    \\aod_main_reference_check:nn {{#1}}
      {{ \\A table\\. (caption\\.)? [0-9]+ \\Z }}
    Main~Table~\\ref{{#1}}
  }}
\\ExplSyntaxOff
\\newcommand{{\\SADAR}}{{\\mathrm{{SADAR}}}}
\\newcommand{{\\AO}}{{A{{\\leftrightarrow}}\\Omega}}
\\newcommand{{\\AOpkg}}{{\\operatorname{{A\\leftrightarrow_{{\\mu}}\\Omega}}}}
\\newcommand{{\\OAop}}{{\\operatorname{{\\Omega\\leftrightarrow_{{\\mu}}A}}}}
\\newcommand{{\\AOh}}{{\\mathsf{{AO}}_{{\\mu}}}}
\\newcommand{{\\OAh}}{{\\mathsf{{OA}}_{{\\mu}}}}
\\newcommand{{\\AOcycle}}{{A{{\\leftrightarrow_{{\\mu}}}}\\Omega\\;\\longleftrightarrow\\;\\Omega{{\\leftrightarrow_{{\\mu}}}}A}}
\\newcommand{{\\SADARop}}{{\\mathfrak S}}
\\newcommand{{\\Qext}}{{\\mathsf{{Q}}_{{\\mathrm{{ext}}}}}}
\\newcommand{{\\appref}}[1]{{App.~\\ref{{#1}}}}
\\newcommand{{\\secref}}[1]{{\\S\\ref{{#1}}}}
\\newcommand{{\\eqnref}}[1]{{\\eqref{{#1}}}}
\\newcommand{{\\figref}}[1]{{Fig.~\\ref{{#1}}}}
\\newcommand{{\\tabref}}[1]{{Table~\\ref{{#1}}}}
\\newcommand{{\\aodnoteblock}}[2]{{\\medskip\\begingroup\\emergencystretch=3em\\sloppy\\noindent\\emph{{#1.}}\\ #2\\par\\endgroup}}
\\newcommand{{\\aodprovenance}}[1]{{\\aodnoteblock{{Provenance}}{{#1}}}}
\\newcommand{{\\aodliteraturenote}}[1]{{\\aodnoteblock{{Literature note}}{{#1}}}}
\\newcommand{{\\aodremark}}[1]{{\\aodnoteblock{{Remark}}{{#1}}}}
\\newcommand{{\\ADAR}}{{\\mathrm{{ADAR}}}}
\\newcommand{{\\RCD}}{{\\operatorname{{RCD}}}}
\\newcommand{{\\Qfour}}{{Q_4}}
\\newcommand{{\\Null}}{{\\mathcal N}}
\\newcommand{{\\infD}}{{\\infty_{{\\mathcal{{D}}}}}}
% Deliver latex/manual/main.pdf staged as sibling manual.pdf alongside main.pdf.
\\externaldocument[main:][nocite]{{../main}}[main.pdf]
\\setlength{{\\tabcolsep}}{{3pt}}

\\hypersetup{{
  pdftitle={{{m["title"]}}},
  pdfauthor={{{meta["author"]}}},
  pdfsubject={{{m["subject"]}}},
  pdfkeywords={{{m["keywords"]}}}
}}
\\setcounter{{secnumdepth}}{{3}}
\\setcounter{{tocdepth}}{{3}}

\\newcommand{{\\AODDocumentAuthor}}{{{meta["author"]}}}
\\newcommand{{\\AODDocumentDate}}{{{meta["date"]}}}
\\makeatletter
\\renewcommand*\\l@section{{\\@dottedtocline{{1}}{{0em}}{{2.6em}}}}
\\renewcommand*\\l@subsection{{\\@dottedtocline{{2}}{{1.6em}}{{3.9em}}}}
\\renewcommand*\\l@subsubsection{{\\@dottedtocline{{3}}{{4.0em}}{{5.0em}}}}
\\makeatother

\\newtheorem{{definition}}{{Definition}}
\\setlength{{\\emergencystretch}}{{2em}}
"""


# ---------------------------------------------------------------------------
# Active Typst Include Graph Discovery & Top-Level Generation Pipeline
# ---------------------------------------------------------------------------

def _map_typst_to_latex_rel(typ_rel: str) -> str:
    if typ_rel in TABLE_TARGET_OVERRIDES:
        return TABLE_TARGET_OVERRIDES[typ_rel]
    _require(typ_rel.startswith("typst/") and typ_rel.endswith(".typ"), f"Unexpected Typst path: {typ_rel}")
    return typ_rel[len("typst/"):-len(".typ")] + ".tex"


def discover_active_typst_units(root: Path) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Walk #include graph from typst/main.typ and typst/manual/main.typ.

    Returns:
      ordered list of (surface, typ_rel) for all active units (including drivers and preambles),
      and dict mapping typ_rel -> generated latex relative path (relative to outdir).
    """
    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()
    unit_map: dict[str, str] = {}

    def register(surface: str, typ_rel: str) -> None:
        if typ_rel in seen:
            return
        seen.add(typ_rel)
        ordered.append((surface, typ_rel))
        unit_map[typ_rel] = _map_typst_to_latex_rel(typ_rel)

    def walk(surface: str, typ_path: Path, stack: set[Path]) -> None:
        typ_path = typ_path.resolve()
        _require(typ_path not in stack, f"Recursive Typst #include detected: {typ_path}")
        _require(typ_path.is_file(), f"Missing included Typst file: {typ_path}")
        typ_rel = typ_path.relative_to(root).as_posix()
        register(surface, typ_rel)
        stack.add(typ_path)
        clean = strip_typst_comments(typ_path.read_text(encoding="utf-8"))
        for m in re.finditer(r'#include\s+"([^"]+)"', clean):
            arg = m.group(1)
            if DIAGRAM_INCLUDE_RE.match(arg):
                continue
            child = (typ_path.parent / arg).resolve()
            _require(child.is_relative_to(root / "typst"), f"Typst #include escapes typst/: {arg} in {typ_rel}")
            walk(surface, child, stack)
        stack.remove(typ_path)

    register("main", "typst/preamble.typ")
    walk("main", root / "typst/main.typ", set())
    register("manual", "typst/manual/preamble.typ")
    walk("manual", root / "typst/manual/main.typ", set())
    return ordered, unit_map


def _load_figure_exporter(root: Path):
    script = root / "scripts/export_typst_figures.py"
    _require(script.is_file(), f"Missing figure exporter: {script}")
    spec = importlib.util.spec_from_file_location("aod_export_typst_figures", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generate_latex_tree(
    root: Path,
    outdir: Path,
    *,
    check_only: bool = False,
    figure_format: str = "pdf",
    ppi: int = 300,
    typst_bin: str | None = None,
    runtime_out: dict | None = None,
    before_commit_hook=None,
) -> dict:
    root = Path(root).resolve()
    outdir = Path(outdir).resolve()
    _require((root / "typst/main.typ").is_file(), f"Missing typst/main.typ under {root}")
    _require((root / "typst/manual/main.typ").is_file(), f"Missing typst/manual/main.typ under {root}")

    meta = _read_typst_metadata(root)
    ordered_units, unit_map = discover_active_typst_units(root)
    used_rasters: set[str] = set()
    used_diagrams: set[str] = set()
    fig_mod = _load_figure_exporter(root)

    if check_only:
        stage = Path(tempfile.mkdtemp(prefix="aod_typ2tex_check_"))
    else:
        outdir.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{outdir.name}.stage.", dir=str(outdir.parent)))

    try:
        outputs: list[dict] = []
        inputs: dict[str, dict] = {}
        fig_runtime: dict = {}

        def _rec_input(rel: str, role: str) -> None:
            if rel not in inputs:
                inputs[rel] = {
                    "path": rel,
                    "role": role,
                    "sha256": sha256_file(root / rel),
                }

        _rec_input("typst/lib/aod_schema.typ", "typst_schema")

        # 1. Emit controlled preambles & rendered LaTeX units strictly from Typst
        for surface, typ_rel in ordered_units:
            _rec_input(typ_rel, "typst_source")
            latex_rel = unit_map[typ_rel]
            dst = stage / latex_rel
            dst.parent.mkdir(parents=True, exist_ok=True)

            if typ_rel == "typst/preamble.typ":
                content = render_main_preamble(meta)
                kind = "controlled_preamble"
            elif typ_rel == "typst/manual/preamble.typ":
                content = render_manual_preamble(meta)
                kind = "controlled_preamble"
            else:
                src_path = root / typ_rel
                conv = TypstToLatexConverter(
                    root=root,
                    surface=surface,
                    current_typ=src_path,
                    unit_map=unit_map,
                    diagram_format=figure_format,
                    used_rasters=used_rasters,
                    used_diagrams=used_diagrams,
                )
                body_tex = conv.convert_document_body(src_path.read_text(encoding="utf-8"), base_line=1)
                if typ_rel in ("typst/main.typ", "typst/manual/main.typ"):
                    content = (
                        _generated_header(typ_rel)
                        + "\\documentclass[11pt]{article}\n"
                        + "\\input{preamble.tex}\n"
                        + "\\begin{document}\n\n"
                        + body_tex
                        + "\n\\end{document}\n"
                    )
                else:
                    content = _generated_header(typ_rel) + body_tex
                kind = "rendered_tex"

            dst.write_text(content, encoding="utf-8")
            os.chmod(dst, 0o644)
            outputs.append({
                "path": latex_rel,
                "kind": kind,
                "source": typ_rel,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
            })

        # 2. Stage unchanged shared bibliographies
        for bib_rel in ("refs.bib", "manual/refs.bib"):
            src_bib = root / bib_rel
            _require(src_bib.is_file(), f"Missing canonical bibliography: {bib_rel}")
            _rec_input(bib_rel, "shared_bibliography")
            dst_bib = stage / bib_rel
            dst_bib.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_bib, dst_bib)
            os.chmod(dst_bib, 0o644)
            outputs.append({
                "path": bib_rel,
                "kind": "staged_bib",
                "source": bib_rel,
                "sha256": sha256_file(dst_bib),
                "bytes": dst_bib.stat().st_size,
            })

        # 3. Stage unchanged active raster assets (byte-identical copies)
        for raster_rel in sorted(used_rasters):
            src_r = root / raster_rel
            _require(src_r.is_file(), f"Missing active raster asset: {raster_rel}")
            _rec_input(raster_rel, "shared_raster")
            dst_r = stage / raster_rel
            dst_r.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_r, dst_r)
            os.chmod(dst_r, 0o644)
            outputs.append({
                "path": raster_rel,
                "kind": "staged_raster",
                "source": raster_rel,
                "sha256": sha256_file(dst_r),
                "bytes": dst_r.stat().st_size,
            })

        # 4. Export authoritative native Typst diagrams via scripts/export_typst_figures.py
        if used_diagrams:
            gen_fig_dir = stage / "manual/figures/generated"
            fig_manifest = fig_mod.export_figures(
                root,
                gen_fig_dir,
                fmt=figure_format,
                ppi=ppi,
                typst_bin=typst_bin,
                runtime_out=fig_runtime,
            )
            for comp_rel in sorted(used_diagrams):
                _rec_input(comp_rel, "typst_diagram")
            for f_entry in fig_manifest["figures"]:
                rel_out = f"manual/figures/generated/{f_entry['output_filename']}"
                outputs.append({
                    "path": rel_out,
                    "kind": "exported_diagram",
                    "source": f_entry["diagram_component"],
                    "sha256": f_entry["output_sha256"],
                    "bytes": f_entry["output_bytes"],
                })
            fm_path = gen_fig_dir / "FIGURE_MANIFEST.json"
            outputs.append({
                "path": "manual/figures/generated/FIGURE_MANIFEST.json",
                "kind": "figure_manifest",
                "source": "scripts/export_typst_figures.py",
                "sha256": sha256_file(fm_path),
                "bytes": fm_path.stat().st_size,
            })

        # 5. Build deterministic GENERATION_MANIFEST.json (zero timestamps / absolute paths / removal logs)
        outputs.sort(key=lambda e: e["path"])
        counts_by_kind: dict[str, int] = {}
        for o in outputs:
            counts_by_kind[o["kind"]] = counts_by_kind.get(o["kind"], 0) + 1

        manifest = {
            "schema": MANIFEST_SCHEMA,
            "generator": "scripts/typ2tex.py",
            "generator_version": GENERATOR_VERSION,
            "generator_sha256": sha256_file(Path(__file__).resolve()),
            "figure_exporter_sha256": sha256_file(root / "scripts/export_typst_figures.py"),
            "figure_format": figure_format,
            "figure_ppi": ppi if figure_format == "png" else None,
            "counts": {
                "total_inputs": len(inputs),
                "total_outputs": len(outputs),
                "by_kind": dict(sorted(counts_by_kind.items())),
            },
            "inputs": [inputs[k] for k in sorted(inputs)],
            "outputs": outputs,
        }
        m_path = stage / MANIFEST_NAME
        m_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        os.chmod(m_path, 0o644)

        removed_outputs: list[str] = []
        if check_only:
            _verify_trees_match(stage, outdir)
        else:
            # Rollback-safe same-filesystem swap (preserves previous managed tree on failure)
            removed_outputs = fig_mod.atomic_replace_directory(
                stage, outdir, before_commit_hook=before_commit_hook
            )

        rt_report = {
            "schema": "aod.typ2tex.runtime.v1",
            "mode": "check" if check_only else "generate",
            "removed_outputs": removed_outputs,
            "figure_export_runtime": fig_runtime if fig_runtime else None,
        }
        if runtime_out is not None:
            runtime_out.clear()
            runtime_out.update(rt_report)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _tree_inventory(base: Path) -> dict[str, str]:
    if not base.is_dir():
        return {}
    inv: dict[str, str] = {}
    for p in sorted(base.rglob("*")):
        if p.is_file():
            # Ignore transient LaTeX build intermediates when checking generated sources
            rel = p.relative_to(base).as_posix()
            if p.suffix in {".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk",
                            ".xdv", ".synctex.gz", ".bbl", ".blg", ".run.xml", ".bcf"}:
                continue
            if rel in ("main.pdf", "manual/main.pdf", "manual.pdf"):
                continue
            inv[rel] = sha256_file(p)
    return inv


def _verify_trees_match(expected_dir: Path, actual_dir: Path) -> None:
    _require(actual_dir.is_dir(), f"Generated LaTeX directory does not exist: {actual_dir}")
    exp = _tree_inventory(expected_dir)
    act = _tree_inventory(actual_dir)
    missing = sorted(set(exp) - set(act))
    extra = sorted(set(act) - set(exp))
    changed = sorted(k for k in set(exp) & set(act) if exp[k] != act[k])
    if missing or extra or changed:
        details = []
        if missing:
            details.append(f"missing={missing[:10]}")
        if extra:
            details.append(f"extra={extra[:10]}")
        if changed:
            details.append(f"changed={changed[:10]}")
        raise Typ2TexError(
            "Generated LaTeX tree differs from canonical Typst export (--check failed): "
            + "; ".join(details)
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--outdir", type=Path, default=Path("latex"))
    ap.add_argument("--check", action="store_true", help="Regenerate into temp dir and fail if outdir differs")
    ap.add_argument("--figure-format", choices=("pdf", "png"), default="pdf")
    ap.add_argument("--ppi", type=int, default=300, choices=(300, 600))
    ap.add_argument("--typst-bin", default=None)
    ap.add_argument("--runtime-report", type=Path, default=None, help="Optional JSON path for runtime/removal diagnostics")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    outdir = args.outdir if args.outdir.is_absolute() else (root / args.outdir)
    runtime_diag: dict = {}
    manifest = generate_latex_tree(
        root,
        outdir,
        check_only=args.check,
        figure_format=args.figure_format,
        ppi=args.ppi,
        typst_bin=args.typst_bin,
        runtime_out=runtime_diag,
    )
    if args.runtime_report is not None:
        rp = args.runtime_report if args.runtime_report.is_absolute() else (root / args.runtime_report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(runtime_diag, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "mode": "check" if args.check else "generate",
        "counts": manifest["counts"],
        "removed_outputs": runtime_diag.get("removed_outputs", []),
        "figure_export_runtime": runtime_diag.get("figure_export_runtime"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
