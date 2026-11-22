// Shared Alpha-Omega Dynamics (AOD) native Typst schema and presentation helpers.
// Preserves baseline scientific ontology, macro semantics, numbering, bibliography,
// and Main-to-Manual cross-reference contracts without external package dependencies.

#let AODDocumentAuthor = "Reginald Poyau"
#let AODDocumentDate = "June 1, 2026"

// --- Core AOD math symbol macros (matching preamble.tex / manual/preamble.tex) ---
#let Null = $cal(N)$
#let infD = $infinity_cal(D)$
#let Qfour = $Q_4$
#let RCD = $upright("RCD")$
#let SADAR = $upright("SADAR")$
#let ADAR = $upright("ADAR")$
#let AO = $A arrow.l.r Omega$
#let AOpkg = $op(A scripts(arrow.l.r)_mu Omega)$
#let OAop = $op(Omega scripts(arrow.l.r)_mu A)$
#let AOh = $sans("AO")_mu$
#let OAh = $sans("OA")_mu$
#let AOcycle = $A scripts(arrow.l.r)_mu Omega thin arrow.l.r.long thin Omega scripts(arrow.l.r)_mu A$
#let SADARop = $frak(S)$
#let Qext = $sans("Q")_upright("ext")$
#let leadsto = $arrow.r.squiggly$

// --- Document states & counters ---
#let aod-in-appendix = state("aod-in-appendix", false)
#let aod-def-counter = counter("aod-definition")
#let aod-main-registry = state("aod-main-registry", none)
#let aod-bib-state = state("aod-bib-entries", ())

#let _fmt-heading-num(nums, is-app) = {
  if nums.len() == 0 {
    ""
  } else if is-app {
    let letter = numbering("A", nums.at(0))
    if nums.len() == 1 {
      letter
    } else {
      letter + "." + nums.slice(1).map(str).join(".")
    }
  } else {
    nums.map(str).join(".")
  }
}

#let _heading-kind(level, is-app) = {
  let idx = calc.min(calc.max(level - 1, 0), 2)
  if is-app {
    ("appendix", "appendix-subsection", "appendix-subsubsection").at(idx)
  } else {
    ("section", "subsection", "subsubsection").at(idx)
  }
}

// Switch document into Appendix mode (A, A.1, ...) matching LaTeX \appendix.
#let aod-start-appendix() = {
  counter(heading).update(0)
  aod-in-appendix.update(true)
}

#let aod-appendix-numbering(..nums) = {
  let arr = nums.pos()
  if arr.len() == 0 {
    ""
  } else if arr.len() == 1 {
    numbering("A", arr.at(0))
  } else {
    numbering("A", arr.at(0)) + "." + arr.slice(1).map(str).join(".")
  }
}

// --- Secondary / paragraph anchor preserving exact LaTeX alias & phantomsection labels ---
#let aod-anchor(lbl) = {
  let id = str(lbl)
  [#box(width: 0pt, height: 0pt)[]#lbl]
  context {
    let loc = here()
    let is-app = aod-in-appendix.get()
    let nums = counter(heading).at(loc)
    let fmt = _fmt-heading-num(nums, is-app)
    let kind = _heading-kind(nums.len(), is-app)
    [#metadata((
      id: id,
      kind: kind,
      number: fmt,
      display: fmt,
      alias: true,
    ))<aod-ref-meta>]
    [#metadata((
      id: id,
      kind: kind,
      number: fmt,
      display: fmt,
      page: loc.page(),
      alias: true,
    ))<aod-ref-entry>]
  }
}

// --- Tagged display equation (e.g., RG1..RG12) that does not advance counter(math.equation) ---
#let tagged-eq(tag, body, lbl) = {
  let id = str(lbl)
  block(width: 100%, above: 0.7em, below: 0.7em, breakable: false)[
    #grid(
      columns: (1fr, auto, 1fr),
      align: (left, center + horizon, right + horizon),
      [],
      [#math.equation(block: true, numbering: none, body)#lbl],
      [(#tag)],
    )
  ]
  [#metadata((
    id: id,
    kind: "rg-equation",
    number: tag,
    display: "(" + tag + ")",
  ))<aod-ref-meta>]
  context {
    let loc = here()
    [#metadata((
      id: id,
      kind: "rg-equation",
      number: tag,
      display: "(" + tag + ")",
      page: loc.page(),
    ))<aod-ref-entry>]
  }
}

// --- Run-in bold paragraph heading matching LaTeX \paragraph{...} ---
#let aod-paragraph(title) = {
  parbreak()
  v(0.5em, weak: true)
  strong(title)
  h(0.55em)
}

// --- Numbered Definition environment matching amsthm \newtheorem{definition}{Definition} ---
#let aod-definition(title: none, body) = {
  aod-def-counter.step()
  block(width: 100%, above: 0.7em, below: 0.7em)[
    #context {
      let n = aod-def-counter.get().at(0)
      if title != none {
        [*Definition #n* (#title)*.* ]
      } else {
        [*Definition #n.* ]
      }
      emph(body)
    }
  ]
}

// --- Compact note blocks matching \aodnoteblock / \aodprovenance / \aodliteraturenote / \aodremark ---
#let aod-noteblock(label-text, body) = {
  block(width: 100%, above: 0.55em, below: 0.55em)[
    #emph[#label-text.] #body
  ]
}

#let aod-provenance(body) = aod-noteblock("Provenance", body)
#let aod-literature-note(body) = aod-noteblock("Literature note", body)
#let aod-remark(body) = aod-noteblock("Remark", body)

// --- Framed panel matching \fbox{\begin{minipage}{...} ... \end{minipage}} ---
#let aod-panel(width: 90%, body) = {
  align(center)[
    #box(
      width: width,
      stroke: 0.5pt + black,
      inset: 8pt,
    )[
      #align(center)[#body]
    ]
  ]
}

// --- Unnumbered tight framed display math matching LaTeX \[\boxed{...}\] ---
#let aod-boxed(body) = align(center)[
  #block(above: 0.7em, below: 0.7em, breakable: false)[
    #box(stroke: 0.5pt + black, inset: 4.5pt)[#math.equation(block: false, numbering: none, body)]
  ]
]

// --- Zero-dependency native Typst flowchart for the 4 Manual TikZ schematics ---
#let aod-flowchart(nodes, edges, width: 14.5cm, height: 8.5cm) = {
  align(center)[
    #box(width: width, height: height)[
      #let node-map = (:)
      #for n in nodes {
        node-map.insert(n.id, n)
      }
      // Draw directed edges first so boxes sit cleanly on top
      #for e in edges {
        let src = node-map.at(e.from)
        let dst = node-map.at(e.to)
        let x1 = src.x
        let y1 = src.y + src.at("dy-out", default: 0.55cm)
        let x2 = dst.x
        let y2 = dst.y - dst.at("dy-in", default: 0.55cm)
        let dx = (x2 - x1).pt()
        let dy = (y2 - y1).pt()
        let dist = calc.sqrt(dx * dx + dy * dy)
        if dist > 0.1 {
          let ux = dx / dist
          let uy = dy / dist
          let ah-len = 5.5
          let ah-half = 2.6
          let tip-x = x2
          let tip-y = y2
          let base-x = x2 - (ux * ah-len) * 1pt
          let base-y = y2 - (uy * ah-len) * 1pt
          let left-x = base-x + (-uy * ah-half) * 1pt
          let left-y = base-y + (ux * ah-half) * 1pt
          let right-x = base-x - (-uy * ah-half) * 1pt
          let right-y = base-y - (ux * ah-half) * 1pt
          place(top + left, line(start: (x1, y1), end: (base-x, base-y), stroke: 0.75pt + black))
          place(top + left, polygon(fill: black, (tip-x, tip-y), (left-x, left-y), (right-x, right-y)))
        }
      }
      // Draw rounded node boxes centered on (x, y)
      #for n in nodes {
        let w = n.at("w", default: 4.8cm)
        let h = n.at("h", default: 1.05cm)
        place(
          top + left,
          dx: n.x - w / 2,
          dy: n.y - h / 2,
          box(
            width: w,
            height: h,
            fill: white,
            stroke: 0.65pt + black,
            radius: 3pt,
            inset: 4pt,
          )[
            #align(center + horizon)[
              #set text(size: 8.5pt)
              #n.body
            ]
          ]
        )
      }
    ]
  ]
}

// --- Booktabs-style horizontal rules for native Typst tables ---
#let toprule = table.hline(stroke: 0.9pt + black)
#let midrule = table.hline(stroke: 0.45pt + black)
#let bottomrule = table.hline(stroke: 0.9pt + black)

// --- Internal cross-reference resolution with real PDF link & query metadata ---
#let _lookup-internal(id) = {
  let matches = query(<aod-ref-meta>).filter(e => e.value.id == id)
  if matches.len() == 0 {
    panic("Unresolved internal reference: " + id)
  }
  matches.at(0).value
}

#let _emit-ref-use(macro-name, id, resolved-kind, resolved-display) = {
  [#metadata((
    macro: macro-name,
    target: id,
    resolved_kind: resolved-kind,
    resolved_display: resolved-display,
  ))<aod-ref-use>]
}

#let eqref(id) = context {
  let e = _lookup-internal(id)
  if e.kind != "equation" and e.kind != "rg-equation" {
    panic("Wrong internal reference type for eqref(" + id + "): got " + e.kind)
  }
  [#_emit-ref-use("eqref", id, e.kind, e.display)#link(label(id))[#e.display]]
}

#let eqnref(id) = context {
  let e = _lookup-internal(id)
  if e.kind != "equation" and e.kind != "rg-equation" {
    panic("Wrong internal reference type for eqnref(" + id + "): got " + e.kind)
  }
  [#_emit-ref-use("eqnref", id, e.kind, e.display)#link(label(id))[#e.display]]
}

#let secref(id) = context {
  let e = _lookup-internal(id)
  let disp = "§" + e.number
  [#_emit-ref-use("secref", id, e.kind, disp)#link(label(id))[#disp]]
}

#let appref(id) = context {
  let e = _lookup-internal(id)
  let disp = "App. " + e.number
  [#_emit-ref-use("appref", id, e.kind, disp)#link(label(id))[#disp]]
}

#let figref(id) = context {
  let e = _lookup-internal(id)
  if e.kind != "figure" {
    panic("Wrong internal reference type for figref(" + id + "): got " + e.kind)
  }
  let disp = "Fig. " + e.number
  [#_emit-ref-use("figref", id, e.kind, disp)#link(label(id))[#disp]]
}

#let tabref(id) = context {
  let e = _lookup-internal(id)
  if e.kind != "table" {
    panic("Wrong internal reference type for tabref(" + id + "): got " + e.kind)
  }
  let disp = "Table " + e.number
  [#_emit-ref-use("tabref", id, e.kind, disp)#link(label(id))[#disp]]
}

#let bare-ref(id) = context {
  let e = _lookup-internal(id)
  [#_emit-ref-use("ref", id, e.kind, e.number)#link(label(id))[#e.number]]
}

// Advance the table figure counter for uncaptioned LaTeX longtables (which
// increment LaTeX's table counter even without a \caption), preserving exact
// baseline table numbering across subsequent captioned tables.
#let aod-uncaptioned-longtable(body) = {
  counter(figure.where(kind: table)).step()
  body
}

// --- Native Main-to-Manual cross-reference resolution (strict registry + type + freshness guard) ---
#let aod-load-main-registry(registry-path, expected-digest: none) = {
  let reg = json(registry-path)
  if reg.at("schema", default: "") != "aod.typst.main-registry.v1" {
    panic("Invalid Main reference registry schema in " + registry-path)
  }
  if expected-digest != none and expected-digest != "" {
    if reg.at("main_sources_sha256", default: "") != expected-digest {
      panic(
        "Stale Main registry: registry digest "
        + reg.at("main_sources_sha256", default: "<missing>")
        + " != live Main sources digest "
        + expected-digest
        + ". Build Main before Manual."
      )
    }
  }
  let reg-pdf = reg.at("main_pdf_filename", default: "")
  if reg-pdf == "" {
    panic("Main reference registry missing main_pdf_filename in " + registry-path)
  }
  let expected-pdf = sys.inputs.at("expected_main_pdf_filename", default: "")
  if expected-pdf != "" and reg-pdf != expected-pdf {
    panic(
      "Main companion filename mismatch: registry specifies "
      + reg-pdf
      + " != expected "
      + expected-pdf
    )
  }
  aod-main-registry.update(reg)
}

#let _lookup-main-ref(id, allowed-kinds, macro-name) = {
  if not id.starts-with("main:") {
    panic("Unresolved Main reference (missing main: prefix): " + id)
  }
  let reg = aod-main-registry.get()
  if reg == none {
    panic("Main reference registry not loaded before " + macro-name + "(" + id + ")")
  }
  let raw = id.slice(5)
  let entries = reg.at("entries", default: (:))
  if raw not in entries {
    panic("Unresolved Main reference: " + id)
  }
  let entry = entries.at(raw)
  if entry.kind not in allowed-kinds {
    panic("Wrong Main reference type for " + macro-name + "(" + id + "): got " + entry.kind)
  }
  if entry.kind == "rg-equation" {
    if entry.number.match(regex("^RG[0-9]+$")) == none {
      panic("Wrong Main RG tag format for " + id + ": " + entry.number)
    }
  }
  (
    entry: entry,
    digest: reg.at("main_sources_sha256", default: ""),
    peer_pdf: reg.at("main_pdf_filename", default: "main.pdf"),
  )
}

#let _render-main-ref(id, allowed-kinds, macro-name, formatter) = context {
  let res = _lookup-main-ref(id, allowed-kinds, macro-name)
  let entry = res.entry
  let disp = formatter(entry)
  let dest = res.peer_pdf + "#page=" + str(entry.page)
  [#metadata((
    macro: macro-name,
    ref_id: id,
    raw_id: id.slice(5),
    resolved_kind: entry.kind,
    resolved_number: entry.number,
    resolved_display: disp,
    target_page: entry.page,
    peer_pdf: res.peer_pdf,
    pdf_destination: dest,
    registry_digest: res.digest,
  ))<aod-mainref-use>#link(dest)[#disp]]
}

#let mainequation(id) = _render-main-ref(
  id,
  ("equation", "rg-equation"),
  "mainequation",
  e => "Main " + e.display,
)

#let mainsection(id) = _render-main-ref(
  id,
  ("section", "subsection", "subsubsection"),
  "mainsection",
  e => "Main §" + e.number,
)

#let mainappendix(id) = _render-main-ref(
  id,
  ("appendix", "appendix-subsection", "appendix-subsubsection"),
  "mainappendix",
  e => "Main App. " + e.number,
)

#let maintable(id) = _render-main-ref(
  id,
  ("table",),
  "maintable",
  e => "Main Table " + e.number,
)

// --- Pure-Typst BibTeX plain reader (reads byte-identical refs.bib / manual/refs.bib directly) ---
#let _strip-outer-braces(s) = {
  let t = s.trim()
  while t.starts-with("{") and t.ends-with("}") {
    // Only strip if the opening brace matches the very last character
    let depth = 0
    let wraps-all = true
    let chars = t.clusters()
    for (i, ch) in chars.enumerate() {
      if ch == "{" { depth += 1 }
      else if ch == "}" { depth -= 1 }
      if depth == 0 and i < chars.len() - 1 {
        wraps-all = false
        break
      }
    }
    if wraps-all {
      t = t.slice(1, t.len() - 1).trim()
    } else {
      break
    }
  }
  t
}

#let _parse-bibtex(raw) = {
  let entries = ()
  let chars = raw.clusters()
  let n = chars.len()
  let i = 0
  while i < n {
    if chars.at(i) == "@" {
      i += 1
      let etype = ""
      while i < n and chars.at(i) != "{" and chars.at(i) != "(" {
        etype += chars.at(i)
        i += 1
      }
      etype = lower(etype.trim())
      if i >= n { break }
      i += 1 // skip '{'
      let key = ""
      while i < n and chars.at(i) != "," {
        key += chars.at(i)
        i += 1
      }
      key = key.trim()
      if i < n and chars.at(i) == "," { i += 1 }
      let fields = (:)
      while i < n {
        // skip whitespace/commas
        while i < n and chars.at(i) in (" ", "\t", "\n", "\r", ",") { i += 1 }
        if i >= n or chars.at(i) == "}" {
          i += 1
          break
        }
        let fname = ""
        while i < n and chars.at(i) != "=" and chars.at(i) != "}" {
          fname += chars.at(i)
          i += 1
        }
        fname = lower(fname.trim())
        if i >= n or chars.at(i) == "}" {
          i += 1
          break
        }
        i += 1 // skip '='
        while i < n and chars.at(i) in (" ", "\t", "\n", "\r") { i += 1 }
        let fval = ""
        if i < n and chars.at(i) == "{" {
          let depth = 0
          while i < n {
            let ch = chars.at(i)
            fval += ch
            if ch == "{" { depth += 1 }
            else if ch == "}" {
              depth -= 1
              if depth == 0 {
                i += 1
                break
              }
            }
            i += 1
          }
        } else if i < n and chars.at(i) == "\"" {
          i += 1
          while i < n and chars.at(i) != "\"" {
            fval += chars.at(i)
            i += 1
          }
          if i < n { i += 1 }
        } else {
          while i < n and chars.at(i) != "," and chars.at(i) != "}" {
            fval += chars.at(i)
            i += 1
          }
        }
        let stripped = if fval.starts-with("{") and fval.ends-with("}") {
          fval.slice(1, fval.len() - 1).trim()
        } else {
          fval.trim()
        }
        fields.insert(fname, stripped)
      }
      if key != "" and etype != "comment" and etype != "preamble" and etype != "string" {
        entries.push((type: etype, key: key, fields: fields))
      }
    } else {
      i += 1
    }
  }
  entries
}

#let _split-authors(author-str) = {
  // Split on top-level " and " outside braces
  let parts = ()
  let cur = ""
  let depth = 0
  let chars = author-str.clusters()
  let n = chars.len()
  let i = 0
  while i < n {
    let ch = chars.at(i)
    if ch == "{" { depth += 1; cur += ch; i += 1 }
    else if ch == "}" { depth -= 1; cur += ch; i += 1 }
    else if depth == 0 and i + 5 <= n and chars.slice(i, i + 5).join() == " and " {
      parts.push(cur.trim())
      cur = ""
      i += 5
    } else {
      cur += ch
      i += 1
    }
  }
  if cur.trim() != "" { parts.push(cur.trim()) }
  parts
}

#let _format-one-author(raw-name) = {
  let name = raw-name.trim()
  if name == "others" { return (display: "et al.", sort: "et al", is-others: true) }
  if name.starts-with("{") and name.ends-with("}") {
    let clean = _strip-outer-braces(name)
    return (display: clean, sort: lower(clean), is-others: false)
  }
  if "," in name {
    let segs = name.split(",")
    let last = segs.at(0).trim()
    let first = segs.slice(1).join(",").trim()
    return (display: first + " " + last, sort: lower(last) + " " + lower(first), is-others: false)
  }
  let words = name.split(" ").filter(w => w != "")
  if words.len() >= 2 {
    let last = words.last()
    let first = words.slice(0, words.len() - 1).join(" ")
    return (display: name, sort: lower(last) + " " + lower(first), is-others: false)
  }
  (display: name, sort: lower(name), is-others: false)
}

#let _format-authors(author-str) = {
  if author-str == "" { return (display: "", sort: "") }
  let parts = _split-authors(author-str).map(_format-one-author)
  let sort-key = parts.map(p => p.sort).join("  ")
  if parts.len() == 1 {
    return (display: parts.at(0).display, sort: sort-key)
  }
  if parts.last().is-others {
    let lead = parts.slice(0, parts.len() - 1).map(p => p.display).join(", ")
    return (display: lead + " et al.", sort: sort-key)
  }
  if parts.len() == 2 {
    return (display: parts.at(0).display + " and " + parts.at(1).display, sort: sort-key)
  }
  let lead = parts.slice(0, parts.len() - 1).map(p => p.display).join(", ")
  (display: lead + ", and " + parts.last().display, sort: sort-key)
}

// Implement BibTeX plain.bst `change.case$("t")`: preserve the first character
// and the first non-space character after a colon, preserve characters inside
// {...} braces or $...$ math, and lowercase all other top-level ASCII letters.
#let _bibtex-sentence-case(s) = {
  let chars = s.clusters()
  let out = ""
  let depth = 0
  let in-math = false
  let at-start = true
  let after-colon = false
  for ch in chars {
    if ch == "{" {
      depth += 1
      out += ch
      at-start = false
      after-colon = false
    } else if ch == "}" {
      if depth > 0 { depth -= 1 }
      out += ch
    } else if ch == "$" {
      in-math = not in-math
      out += ch
      at-start = false
      after-colon = false
    } else if depth > 0 or in-math {
      out += ch
    } else {
      if ch == ":" {
        out += ch
        at-start = false
        after-colon = true
      } else if ch in (" ", "\t", "\n", "\r") {
        out += ch
      } else if at-start or after-colon {
        out += ch
        at-start = false
        after-colon = false
      } else {
        out += lower(ch)
      }
    }
  }
  out
}

#let _clean-bib-str(s) = {
  s.replace("{", "").replace("}", "").replace("---", "—").replace("--", "–").replace("~", "\u{00a0}").replace("'", "’")
}

// Render BibTeX string supporting \url{...} and the inline math snippets used in refs.bib / manual/refs.bib
#let _render-bib-text(s) = {
  let clean = s
  // First split on \url{...}
  let m-url = clean.match(regex("\\\\url\\{([^}]+)\\}"))
  if m-url != none {
    let before = clean.slice(0, m-url.start)
    let url-str = m-url.captures.at(0)
    let after = clean.slice(m-url.end)
    return [#_render-bib-text(before)#link(url-str)[#raw(url-str)]#_render-bib-text(after)]
  }
  // Handle inline math $...$ (including {$...$})
  let m-math = clean.match(regex("\\{?\\$([^$]+)\\$\\}?"))
  if m-math != none {
    let before = clean.slice(0, m-math.start)
    let expr = m-math.captures.at(0)
    let after = clean.slice(m-math.end)
    let rendered = if expr == "\\tau" {
      $tau$
    } else if expr == "\\sqrt{s}=7" {
      $sqrt(s) = 7$
    } else if expr == "\\sqrt{s}=13" {
      $sqrt(s) = 13$
    } else if expr == "H\\to\\gamma\\gamma" {
      $H arrow.r gamma gamma$
    } else if expr == "H\\to ZZ^*\\to4\\ell" {
      $H arrow.r Z Z^* arrow.r 4 ell$
    } else if expr == "m_\\tau=1776.86\\pm0.12\\,\\mathrm{MeV}" {
      $m_tau = 1776.86 plus.minus 0.12 thin upright("MeV")$
    } else {
      [#expr]
    }
    return [#_render-bib-text(before)#rendered#_render-bib-text(after)]
  }
  [#_clean-bib-str(clean)]
}

#let _sort-bib-entries(entries) = {
  let decorated = entries.map(e => {
    let af = _format-authors(e.fields.at("author", default: ""))
    let yr = e.fields.at("year", default: "")
    let yr-sort = if yr == "n.d." { "9999" } else { yr }
    let title-sort = lower(_clean-bib-str(e.fields.at("title", default: "")))
    let skey = af.sort + "\u{0000}" + yr-sort + "\u{0000}" + title-sort + "\u{0000}" + lower(e.key)
    (entry: e, author-display: af.display, sort-key: skey)
  })
  decorated.sorted(key: x => x.sort-key)
}

#let aod-load-bibliography(bib-path) = {
  let raw = read(bib-path)
  let parsed = _parse-bibtex(raw)
  let sorted = _sort-bib-entries(parsed)
  let numbered = ()
  for (idx, item) in sorted.enumerate() {
    numbered.push((
      num: idx + 1,
      key: item.entry.key,
      type: item.entry.type,
      author: item.author-display,
      fields: item.entry.fields,
    ))
  }
  aod-bib-state.update(numbered)
}

#let aod-cite(keys-str, supplement: none) = context {
  let entries = aod-bib-state.get()
  let keys = keys-str.split(",").map(k => k.trim()).filter(k => k != "")
  let nums = ()
  for k in keys {
    let found = entries.filter(e => e.key == k)
    if found.len() == 0 {
      panic("Unresolved citation key: " + k)
    }
    nums.push((key: k, num: found.at(0).num))
  }
  [#metadata((
    keys: keys,
    numbers: nums.map(x => x.num),
    has_supplement: supplement != none,
  ))<aod-cite-use>\[]
  for (i, item) in nums.enumerate() {
    if i > 0 { [, ] }
    link(label("bib:" + item.key))[#item.num]
  }
  if supplement != none { [, #supplement] }
  [\]]
}

#let _ensure-period(s) = {
  let t = s.trim()
  if t == "" or t.ends-with(".") or t.ends-with("?") or t.ends-with("!") {
    t
  } else {
    t + "."
  }
}

#let aod-render-bibliography(title: "References") = {
  heading(level: 1, numbering: none)[#title]
  context {
    let entries = aod-bib-state.get()
    for item in entries {
      let f = item.fields
      let etype = item.type
      let author = item.author
      let raw-title = f.at("title", default: "")
      let cased-title = if etype == "book" { raw-title } else { _bibtex-sentence-case(raw-title) }
      let journal = f.at("journal", default: "")
      let volume = f.at("volume", default: "")
      let number = f.at("number", default: "")
      let pages = f.at("pages", default: "")
      let publisher = f.at("publisher", default: "")
      let institution = f.at("institution", default: "")
      let howpub = f.at("howpublished", default: "")
      let year = f.at("year", default: "")
      let note = f.at("note", default: "")
      let lbl = label("bib:" + item.key)
      let loc = here()
      [#metadata((
        key: item.key,
        num: item.num,
        author: author,
        title: _clean-bib-str(cased-title),
        year: year,
        page: loc.page(),
      ))<aod-bib-entry>]
      block(width: 100%, above: 0.45em, below: 0.45em, breakable: false)[
        #grid(
          columns: (2.6em, 1fr),
          gutter: 0.35em,
          align: (right + top, left + top),
          [[#item.num]#lbl],
          [
            #if author != "" [#_ensure-period(author) ]
            #if etype == "book" [
              #emph[#_render-bib-text(_ensure-period(cased-title))]
              #if publisher != "" [ #_render-bib-text(publisher)#if year != "" [, #_ensure-period(year)] else [.] ] else if year != "" [ #_ensure-period(year)]
            ] else if etype == "article" [
              #_render-bib-text(_ensure-period(cased-title))
              #if journal != "" [ #emph[#_render-bib-text(journal)]#if volume != "" or pages != "" or year != "" [, ] else [.] ]
              #if volume != "" [#volume#if number != "" [(#number)]#if pages != "" [:#_clean-bib-str(pages)]#if year != "" [, #_ensure-period(year)] else [.]] else if year != "" [#_ensure-period(year)]
            ] else if etype == "techreport" [
              #_render-bib-text(_ensure-period(cased-title))
              #if number != "" [ Technical Report #_render-bib-text(number)#if institution != "" [, ] ]
              #if institution != "" [#_render-bib-text(institution)#if year != "" [, #_ensure-period(year)] else [.]] else if year != "" [ #_ensure-period(year)]
            ] else [
              // BibTeX plain.bst @misc ignores publisher and separates title from year with ", " when howpublished is absent.
              #if howpub != "" [
                #_render-bib-text(_ensure-period(cased-title)) #_render-bib-text(howpub)#if year != "" [, #_ensure-period(year)] else [.]
              ] else if year != "" [
                #_render-bib-text(cased-title.trim()), #_ensure-period(year)
              ] else [
                #_render-bib-text(_ensure-period(cased-title))
              ]
            ]
            #if note != "" [ #_render-bib-text(_ensure-period(note))]
          ]
        )
      ]
    }
  }
}

// --- Shared AOD document template ---
#let aod-document(
  title: "",
  author: AODDocumentAuthor,
  subject: "",
  keywords: (),
  bib-path: "/refs.bib",
  is-manual: false,
  main-registry-path: none,
  expected-main-digest: none,
  body,
) = {
  set document(
    title: title,
    author: author,
    description: subject,
    keywords: keywords,
  )
  set page(
    paper: "us-letter",
    margin: 0.85in,
    numbering: "1",
    number-align: center,
  )
  set text(
    font: ("Latin Modern Roman", "DejaVu Serif"),
    size: 11pt,
    lang: "en",
  )
  show raw: set text(font: ("Latin Modern Mono", "DejaVu Sans Mono"), size: 9.5pt)
  show math.equation: set text(font: ("Latin Modern Math", "New Computer Modern Math"))
  set par(leading: 0.6em, spacing: 1.05em, justify: true, first-line-indent: 0pt)
  set heading(numbering: "1.1")
  set math.equation(numbering: "(1)")
  set figure(gap: 0.65em)
  set table(inset: (x: 4pt, y: 3.5pt), stroke: none)

  // Match LaTeX figure/table caption placement (tables: caption above; figures: caption below)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set block(breakable: true)
  show figure.caption: it => {
    set text(size: 10pt)
    if it.position == top {
      block(sticky: true, it)
    } else {
      it
    }
  }

  // Heading typography & automatic reference registry metadata
  show heading.where(level: 1): set text(size: 14.5pt, weight: "bold")
  show heading.where(level: 2): set text(size: 12.5pt, weight: "bold")
  show heading.where(level: 3): set text(size: 11pt, weight: "bold")
  show heading: set block(above: 1.35em, below: 0.65em)
  show heading: it => {
    it
    if it.has("label") {
      let lbl = str(it.label)
      context {
        let el-loc = it.location()
        let is-app = aod-in-appendix.at(el-loc)
        let nums = counter(heading).at(el-loc)
        let fmt = _fmt-heading-num(nums, is-app)
        let kind = _heading-kind(it.level, is-app)
        [#metadata((
          id: lbl,
          kind: kind,
          number: fmt,
          display: fmt,
        ))<aod-ref-meta>]
        [#metadata((
          id: lbl,
          kind: kind,
          number: fmt,
          display: fmt,
          page: el-loc.page(),
        ))<aod-ref-entry>]
      }
    }
  }

  // Numbered display equations emit registry metadata (unnumbered & tagged-eq inner excluded)
  show math.equation.where(block: true): it => {
    it
    if it.numbering != none and it.has("label") {
      let lbl = str(it.label)
      context {
        let el-loc = it.location()
        let num = counter(math.equation).at(el-loc).at(0)
        [#metadata((
          id: lbl,
          kind: "equation",
          number: str(num),
          display: "(" + str(num) + ")",
        ))<aod-ref-meta>]
        [#metadata((
          id: lbl,
          kind: "equation",
          number: str(num),
          display: "(" + str(num) + ")",
          page: el-loc.page(),
        ))<aod-ref-entry>]
      }
    }
  }

  // Figures and tables emit registry metadata
  show figure: it => {
    it
    if it.has("label") {
      let lbl = str(it.label)
      let fkind = if it.kind == table { "table" } else { "figure" }
      context {
        let el-loc = it.location()
        let num = counter(figure.where(kind: it.kind)).at(el-loc).at(0)
        [#metadata((
          id: lbl,
          kind: fkind,
          number: str(num),
          display: str(num),
        ))<aod-ref-meta>]
        [#metadata((
          id: lbl,
          kind: fkind,
          number: str(num),
          display: str(num),
          page: el-loc.page(),
        ))<aod-ref-entry>]
      }
    }
  }

  // Load bibliography (and Main registry if Manual)
  aod-load-bibliography(bib-path)
  if is-manual and main-registry-path != none {
    aod-load-main-registry(main-registry-path, expected-digest: expected-main-digest)
  }

  body
}
