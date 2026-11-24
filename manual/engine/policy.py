"""Static AST zero-float/bare-assert/forbidden-import auditor and runtime payload guard.

All checks use explicit TypeError/ValueError exceptions (zero bare assert)
and zero floating-point arithmetic.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
from typing import NoReturn

_FORBIDDEN_EXP_MOD = "aod_" + "dec"
_FORBIDDEN_TOKEN_RE = re.compile(r"aod[-_]" + r"dec", re.IGNORECASE)

FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "math",
        "cmath",
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "decimal",
        "importlib",
        "builtins",
        _FORBIDDEN_EXP_MOD,
    }
)

FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset(
    {"float", "complex", "eval", "exec", "__import__", "compile", "__builtins__"}
)

FORBIDDEN_ATTR_NAMES: frozenset[str] = frozenset(
    {"float", "complex", "eval", "exec", "__import__"}
)

SYMPY_ALLOWLIST_ENTRIES: tuple[tuple[str, str], ...] = (
    ("vectors.py", "_verify_sympy_z4_dft"),
)

TYPE_GUARD_ALLOWLIST_ENTRIES: tuple[tuple[str, str], ...] = (
    ("policy.py", "require_no_floats"),
    ("policy.py", "visit_Constant"),
)


def reject_json_float(token: str) -> NoReturn:
    """``json.loads`` ``parse_float`` / ``parse_constant`` hook rejecting floats and NaN/Inf."""
    raise ValueError(f"JSON float or non-finite literal forbidden in zero-float payload: {token!r}")


def loads_zero_float(text: str) -> object:
    """Parse JSON strictly rejecting any floating-point or NaN/Infinity literal."""
    if not isinstance(text, str):
        raise TypeError(f"JSON input must be str, got {type(text).__name__}")
    return json.loads(
        text,
        parse_float=reject_json_float,
        parse_constant=reject_json_float,
    )


def require_no_floats(value: object, *, path: str = "$") -> None:
    """Recursively verify that no Python ``float`` or ``complex`` exists in ``value``."""
    if isinstance(value, (float, complex)):
        raise TypeError(f"forbidden {type(value).__name__} value at {path}: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, (float, complex)):
                raise TypeError(
                    f"forbidden {type(key).__name__} dict key at {path}: {key!r}"
                )
            require_no_floats(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            require_no_floats(item, path=f"{path}[{index}]")


def _extract_int_literal(node: ast.AST) -> tuple[bool, int | None]:
    """Return ``(True, value)`` if ``node`` is an integer literal (optionally unary signed)."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return (True, node.value)
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.USub, ast.UAdd))
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) is int
    ):
        val = -node.operand.value if isinstance(node.op, ast.USub) else node.operand.value
        return (True, val)
    return (False, None)


def _is_re_compile_attr(node: ast.Attribute) -> bool:
    """Return True strictly for ``re.compile`` regex compilation."""
    return node.attr == "compile" and isinstance(node.value, ast.Name) and node.value.id == "re"


class _EngineASTAuditor(ast.NodeVisitor):
    """AST visitor enforcing zero-float, zero-bare-assert, and import policy."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[dict[str, object]] = []
        self._fn_stack: list[str] = []

    def _record(self, node: ast.AST, rule: str, detail: str) -> None:
        lineno = getattr(node, "lineno", 0)
        self.violations.append(
            {
                "file": self.rel_path,
                "line": int(lineno),
                "rule": rule,
                "detail": detail,
            }
        )

    def _sympy_allowed_here(self) -> bool:
        return any(
            self.rel_path == allowed_file and allowed_fn in self._fn_stack
            for allowed_file, allowed_fn in SYMPY_ALLOWLIST_ENTRIES
        )

    def _type_guard_allowed_here(self) -> bool:
        return any(
            self.rel_path == allowed_file and allowed_fn in self._fn_stack
            for allowed_file, allowed_fn in TYPE_GUARD_ALLOWLIST_ENTRIES
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._fn_stack.append(node.name)
        self.generic_visit(node)
        self._fn_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._fn_stack.append(node.name)
        self.generic_visit(node)
        self._fn_stack.pop()

    def visit_Assert(self, node: ast.Assert) -> None:
        self._record(node, "bare_assert", "bare assert statement forbidden in manual/engine")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if type(node.value) in (float, complex):
            self._record(
                node,
                "float_or_complex_literal",
                f"forbidden {type(node.value).__name__} literal",
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in FORBIDDEN_CALL_NAMES:
            if node.id in ("float", "complex") and self._type_guard_allowed_here():
                return
            self._record(
                node,
                "forbidden_reference",
                f"reference to forbidden symbol {node.id!r} in manual/engine",
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in FORBIDDEN_ATTR_NAMES:
            self._record(
                node,
                "forbidden_attribute",
                f"attribute reference .{node.attr} is forbidden in manual/engine",
            )
        elif node.attr == "compile" and not _is_re_compile_attr(node):
            self._record(
                node,
                "forbidden_attribute",
                "attribute reference .compile is forbidden outside re.compile",
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        handled_func = False
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALL_NAMES:
            self._record(
                node,
                "forbidden_call",
                f"call to {node.func.id}() is forbidden in manual/engine",
            )
            handled_func = True
        elif isinstance(node.func, ast.Attribute) and (
            node.func.attr in FORBIDDEN_ATTR_NAMES
            or (node.func.attr == "compile" and not _is_re_compile_attr(node.func))
        ):
            self._record(
                node,
                "forbidden_call",
                f"attribute call .{node.func.attr}() is forbidden in manual/engine",
            )
            handled_func = True

        if handled_func:
            if isinstance(node.func, ast.Attribute):
                self.visit(node.func.value)
            for arg in node.args:
                self.visit(arg)
            for kw in node.keywords:
                self.visit(kw)
        else:
            self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Div):
            left_is_int, _ = _extract_int_literal(node.left)
            right_is_int, _ = _extract_int_literal(node.right)
            if left_is_int and right_is_int:
                self._record(
                    node,
                    "integer_true_division",
                    "true division '/' on integer literals produces float; use Fraction(a, b) or '//'",
                )
        elif isinstance(node.op, ast.Pow):
            right_is_int, exp_val = _extract_int_literal(node.right)
            if right_is_int and exp_val is not None and exp_val < 0:
                self._record(
                    node,
                    "negative_integer_exponent",
                    "negative integer literal exponent produces float; use Fraction",
                )
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.op, ast.Div):
            val_is_int, _ = _extract_int_literal(node.value)
            if val_is_int:
                self._record(
                    node,
                    "integer_true_division",
                    "augmented division '/=' with integer literal may produce float",
                )
        elif isinstance(node.op, ast.Pow):
            val_is_int, exp_val = _extract_int_literal(node.value)
            if val_is_int and exp_val is not None and exp_val < 0:
                self._record(
                    node,
                    "negative_integer_exponent",
                    "augmented negative integer literal exponent produces float",
                )
        self.generic_visit(node)

    def _check_module_name(self, node: ast.AST, mod_name: str) -> None:
        if not mod_name:
            return
        parts = mod_name.split(".")
        root_mod = parts[0]
        if mod_name == "manual.scripts" or mod_name.startswith("manual.scripts."):
            self._record(
                node,
                "forbidden_import",
                f"direct import of {mod_name!r} is forbidden; Tier-1 runs via subprocess",
            )
        elif root_mod in FORBIDDEN_IMPORT_ROOTS:
            self._record(
                node,
                "forbidden_import",
                f"forbidden float/experimental module import {mod_name!r}",
            )
        elif root_mod == "sympy":
            if not self._sympy_allowed_here():
                self._record(
                    node,
                    "forbidden_sympy_import",
                    f"sympy import {mod_name!r} outside narrow SD-001/SD-002 allowlist",
                )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module_name(node, alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        self._check_module_name(node, mod)
        if node.level > 0 and mod:
            mod_parts = mod.split(".")
            if "scripts" in mod_parts or any(part in FORBIDDEN_IMPORT_ROOTS for part in mod_parts):
                self._record(
                    node,
                    "forbidden_import",
                    f"forbidden relative import from {'.' * node.level}{mod}",
                )
            elif "sympy" in mod_parts and not self._sympy_allowed_here():
                self._record(
                    node,
                    "forbidden_sympy_import",
                    f"forbidden relative sympy import from {'.' * node.level}{mod}",
                )
        for alias in node.names:
            if mod == "manual" and alias.name == "scripts":
                self._record(
                    node,
                    "forbidden_import",
                    "direct import of 'manual.scripts' is forbidden",
                )
            elif mod == "builtins" and alias.name in FORBIDDEN_CALL_NAMES:
                self._record(
                    node,
                    "forbidden_import",
                    f"importing {alias.name!r} from builtins is forbidden",
                )
            elif node.level > 0 and (alias.name == "scripts" or alias.name in FORBIDDEN_IMPORT_ROOTS):
                self._record(
                    node,
                    "forbidden_import",
                    f"forbidden relative import of {alias.name!r}",
                )
            elif node.level > 0 and alias.name == "sympy" and not self._sympy_allowed_here():
                self._record(
                    node,
                    "forbidden_sympy_import",
                    "forbidden relative import of 'sympy'",
                )
            elif not mod and alias.name in FORBIDDEN_IMPORT_ROOTS:
                self._record(
                    node,
                    "forbidden_import",
                    f"forbidden relative import of {alias.name!r}",
                )
        self.generic_visit(node)


def audit_source_tree(engine_root: Path) -> dict[str, object]:
    """Audit all Python, Markdown, and JSONL files under ``engine_root`` against S2 policy."""
    root = Path(engine_root).resolve()
    if not root.is_dir():
        raise ValueError(f"engine source root directory does not exist: {engine_root}")

    violations: list[dict[str, object]] = []
    py_files: list[Path] = []
    md_files: list[Path] = []
    jsonl_files: list[Path] = []
    json_files: list[Path] = []

    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel_parts = path.relative_to(root).parts
        if any(part == "__pycache__" or part.startswith(".") for part in rel_parts):
            continue
        if not path.is_file():
            continue
        if path.suffix == ".py":
            py_files.append(path)
        elif path.suffix == ".md":
            md_files.append(path)
        elif path.suffix == ".jsonl":
            jsonl_files.append(path)
        elif path.suffix == ".json":
            json_files.append(path)

    for jpath in json_files:
        violations.append(
            {
                "file": jpath.relative_to(root).as_posix(),
                "line": 0,
                "rule": "forbidden_json_under_manual",
                "detail": ".json files are forbidden under manual/engine/",
            }
        )

    for py_path in py_files:
        rel = py_path.relative_to(root).as_posix()
        text = py_path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_TOKEN_RE.search(line):
                violations.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "rule": "forbidden_experimental_token",
                        "detail": "forbidden experimental token detected",
                    }
                )
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as exc:
            violations.append(
                {
                    "file": rel,
                    "line": int(exc.lineno or 0),
                    "rule": "syntax_error",
                    "detail": f"failed to parse Python file: {exc.msg}",
                }
            )
            continue
        auditor = _EngineASTAuditor(rel)
        auditor.visit(tree)
        violations.extend(auditor.violations)

    for md_path in md_files:
        rel = md_path.relative_to(root).as_posix()
        text = md_path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_TOKEN_RE.search(line):
                violations.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "rule": "forbidden_experimental_token",
                        "detail": "forbidden experimental token detected in documentation",
                    }
                )

    for jl_path in jsonl_files:
        rel = jl_path.relative_to(root).as_posix()
        text = jl_path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_TOKEN_RE.search(line):
                violations.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "rule": "forbidden_experimental_token",
                        "detail": "forbidden experimental token detected in JSONL vector file",
                    }
                )
            if line.strip():
                try:
                    loads_zero_float(line)
                except ValueError as exc:
                    violations.append(
                        {
                            "file": rel,
                            "line": lineno,
                            "rule": "forbidden_json_float",
                            "detail": str(exc),
                        }
                    )

    violations.sort(key=lambda item: (str(item["file"]), int(item["line"]), str(item["rule"])))
    return {
        "status": "PASS" if not violations else "FAIL",
        "audited_python_files": len(py_files),
        "audited_markdown_files": len(md_files),
        "audited_jsonl_files": len(jsonl_files),
        "json_files_under_engine": len(json_files),
        "sympy_allowlist": [f"{f}:{fn}" for f, fn in SYMPY_ALLOWLIST_ENTRIES],
        "violation_count": len(violations),
        "violations": violations,
    }
