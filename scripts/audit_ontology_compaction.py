"""Scientific ownership and conservation gates for the bounded R04 compaction.

Bindings are checked in the rendered include graph. Formula bindings protect
the actual mathematical statements; unique defining signatures additionally
reject competing definitions with different labels or right-hand sides.
The data record is a reviewed source contract, not a fixture verdict.
"""
from pathlib import Path
import hashlib
import json
import re


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _formula(block):
    return re.sub(r"\s+", "", re.sub(r"\\label\{[^}]+\}", "", block))


def audit(root, main_files, main_parts, labels, equations, manual_files, manual_labels):
    root = Path(root)
    contract = json.loads((root / "evidence/ONTOLOGY_COMPACTION_BINDINGS.json").read_text())
    groups = {row["concept"]: row for row in contract["ownership"]}
    _require(len(groups) == 43, "canonical group inventory changed")

    def position(anchor):
        _require(anchor in labels, "missing active canonical anchor " + anchor)
        item = labels[anchor]
        return main_files.index(item["path"]), item["position"]

    edges = 0
    for row in groups.values():
        for anchor in row["anchors"]:
            position(anchor)
            _require(labels[anchor]["path"] == row["path"], "canonical owner changed " + anchor)
            _require(anchor in equations, "canonical mathematical body absent " + anchor)
            _require(_formula(equations[anchor]) == contract["formulas"][anchor],
                     "canonical mathematical statement changed " + anchor)
        for dependency in row["depends_on"]:
            # All refined first declarations, not merely one graph node, must
            # precede the dependent group's earliest first declaration.
            _require(max(position(a) for a in groups[dependency]["first_declarations"]) <
                     min(position(a) for a in row["first_declarations"]),
                     "substantive consumer precedes prerequisite " + row["concept"])
            edges += 1
    _require(edges == 67, "dependency edge inventory changed")

    for record in contract["first_uses"]:
        for anchor in record["required_declaration_anchors"]:
            _require(position(anchor) < position(record["first_substantive_use_anchor"]),
                     "first use precedes its actual declaration " + record["id"])

    definition_text = []
    for path, text in main_parts:
        # Protected diagrams and lookup tables summarize definitions. They do
        # not establish a competing mathematical owner. Specializations have
        # distinct arguments/types; the signatures below bind their owners.
        body = re.sub(r"\\begin\{(figure\*?|table\*?|longtable)\}.*?\\end\{\1\}",
                      "", text, flags=re.S)
        definition_text.append((path, re.sub(r"\s+", "", body)))
    for record in contract["unique_signatures"]:
        matches = [(path, match.group()) for path, body in definition_text
                   for match in re.finditer(record["pattern"], body)]
        _require(len(matches) == 1 and matches[0][0] == record["path"],
                 "competing or absent canonical binding " + record["anchor"])

    appendices = contract["appendices"]
    _require([p for p in main_files if p.startswith("appendices/")] == appendices,
             "inherited A-J paths/order changed")
    for path in appendices:
        text = dict(main_parts)[path]
        heading = re.search(r"\\(section|subsection|subsubsection)\*?\{", text)
        _require(heading is not None and heading[1] == "section",
                 "appendix is not a top-level section " + path)
    for record in contract["navigation"]:
        _require(record["replacement"] in dict(main_parts)[record["path"]],
                 "local Main provenance call absent " + record["target"])
        _require(labels.get(record["target"], {}).get("path") == record["target_path"],
                 "local Main provenance target changed " + record["target"])

    for record in contract["manual_families"]:
        _require(record["manual_path"] in manual_files and
                 manual_labels.get(record["manual_anchor"], {}).get("path") == record["manual_path"],
                 "Manual example family not rendered " + record["id"])
        for anchor in record["main_anchors"]:
            position(anchor)
    for path, wanted in contract["frozen_sha256"].items():
        _require((root / path).is_file() and
                 hashlib.sha256((root / path).read_bytes()).hexdigest() == wanted,
                 "protected engine, input, test or presentation changed " + path)
    _require(not (root / "sections/02_introduction.tex").exists(),
             "obsolete introduction restored")
    return {"canonical_groups": len(groups), "canonical_equations": len(contract["formulas"]),
            "ordered_dependencies": edges, "refined_first_uses": len(contract["first_uses"]),
            "unique_defining_signatures": len(contract["unique_signatures"]),
            "appendices": 10, "local_provenance_repairs": len(contract["navigation"]),
            "manual_example_families": len(contract["manual_families"]),
            "frozen_files": len(contract["frozen_sha256"])}
