// Native Typst vector figure: fractal-tesseract-beat-family (Manual §2)
// Provenance: CONCEPTUAL_SCHEMATIC (pure built-in vector geometry)
#import "/typst/lib/aod_plots.typ": *

#let fig-width-cm = 15.0
#let fig-height-cm = 9.95

#aod-canvas(fig-width-cm, fig-height-cm)[
  #aod-figure-header(
    fig-width-cm,
    [Fractal-tesseract cycle range and support family],
    subtitle: [Declared range $frak(a)$, grade $r$, and $Sigma = (3":"4, 3":"3; sans("C")_6)$ resolve $Q_4$ section supports; $frak(S)_B$ couples beats],
    top-y: 0.14,
    title-size: 10.6pt,
    subtitle-size: 8.6pt,
    gap-cm: 0.12,
    rule: true,
  )

  // --- Four-Column Pipeline (y = 1.24 .. 8.60, h = 7.36) ---
  #let y0 = 1.24
  #let ch = 7.36

  // === Col 1: Declared Range, Grade & Support Syntax (x = 0.25 .. 3.40, w = 3.15) ===
  #let c1x = 0.25
  #let c1w = 3.15
  #aod-box-tl(c1x, y0, c1w, ch, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 4pt)
  #aod-text(c1x + c1w / 2, y0 + 0.34, [*1. Declared Syntax*], size: 8.0pt, box-w: 3.0, box-h: 0.38)

  #aod-box-tl(c1x + 0.18, y0 + 0.72, c1w - 0.36, 1.00, [
    #text(size: 7.4pt, weight: "bold")[Fractal range] \
    #v(2pt)
    #text(size: 8.8pt)[$frak(a) subset cal(A)^(upright("ret"))_8$]
  ], stroke: 0.8pt + aod-pal.blue, fill: white, radius: 3pt, inset: 2pt)

  #aod-box-tl(c1x + 0.18, y0 + 1.94, c1w - 0.36, 0.86, [
    #text(size: 7.4pt, weight: "bold")[Section grade] \
    #v(2pt)
    #text(size: 8.8pt)[grade $r$]
  ], stroke: 0.8pt + aod-pal.teal, fill: white, radius: 3pt, inset: 2pt)

  #aod-box-tl(c1x + 0.18, y0 + 3.02, c1w - 0.36, 1.18, [
    #text(size: 7.4pt, weight: "bold")[Support expression] \
    #v(2pt)
    #text(size: 8.6pt)[$Sigma = (3":"4, 3":"3; sans("C")_6)$]
  ], stroke: 0.8pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 3pt, inset: 2pt)

  #aod-arrow(c1x + c1w / 2, y0 + 4.24, c1x + c1w / 2, y0 + 4.82, stroke: 1.0pt + aod-pal.navy, head-len: 4.0, head-half: 1.9)

  #aod-box-tl(c1x + 0.18, y0 + 4.86, c1w - 0.36, 2.22, [
    #text(size: 7.5pt, weight: "bold")[Cycle range operator] \
    #v(4pt)
    #text(size: 8.8pt)[$op("cycle") chevron.l frak(a), r chevron.r (Sigma)$] \
    #v(4pt)
    #text(size: 8.6pt)[$bar.v Sigma_(upright("support")) bar.v = 2$]
  ], stroke: 0.95pt + aod-pal.navy, fill: aod-pal.tint-blue, radius: 3.5pt, inset: 4pt)

  // Arrow Col 1 -> Col 2
  #aod-arrow(3.43, y0 + 3.68, 3.71, y0 + 3.68, stroke: 1.1pt + aod-pal.navy)

  // === Col 2: True 16-Vertex Q4 Tesseract + Section Slice (x = 3.74 .. 7.44, w = 3.70) ===
  #let c2x = 3.74
  #let c2w = 3.70
  #let c2cx = c2x + c2w / 2
  #aod-box-tl(c2x, y0, c2w, ch, [], stroke: 0.9pt + aod-pal.purple, fill: white, radius: 4pt)
  #aod-text(c2cx, y0 + 0.34, [*2. $Q_4$ Section Slice*], size: 8.6pt, box-w: 3.5, box-h: 0.38)

  // True 16-vertex Q4 hypercube
  #aod-tesseract-q4(c2cx, y0 + 2.18, scale: 0.90, highlight-vertex: 0)
  // Highlighted retained section slice plane overlay
  #place(top + left, dx: (c2cx - 1.04) * 1cm, dy: (y0 + 1.34) * 1cm, rect(width: 2.08cm, height: 1.68cm, fill: none, stroke: (paint: aod-pal.teal, thickness: 1.05pt, dash: "dashed"), radius: 3pt))
  #aod-box(c2cx, y0 + 4.02, 3.24, 0.56, [
    #text(size: 8.6pt)[$op("Sec")^((r))_(T, upright("ret"))(frak(a); B)$]
  ], stroke: 0.8pt + aod-pal.teal, fill: aod-pal.tint-green, radius: 3pt, inset: 2pt)

  // Support multiplicity formula box (enlarged for clean top/bottom breathing room)
  #aod-box-tl(c2x + 0.16, y0 + 4.66, c2w - 0.32, 2.42, [
    #text(size: 7.8pt, weight: "bold")[Structural multiplicity] \
    #v(2pt)
    #text(size: 8.6pt)[$N_(upright("support")) =$ \ $bar.v op("Sec")^((r))_(T, upright("ret")) bar.v thin bar.v Sigma_(upright("support")) bar.v$] \
    #v(2pt)
    #text(size: 7.4pt)[sections count support \ occurrences]
  ], stroke: 0.85pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3.5pt, inset: 4pt, leading: 0.62em)

  // Arrow Col 2 -> Col 3
  #aod-arrow(7.47, y0 + 3.68, 7.75, y0 + 3.68, stroke: 1.1pt + aod-pal.navy)

  // === Col 3: Dual Concentric C_6 Support Cards (x = 7.78 .. 11.08, w = 3.30) ===
  #let c3x = 7.78
  #let c3w = 3.30
  #let c3cx = c3x + c3w / 2
  #aod-box-tl(c3x, y0, c3w, ch, [], stroke: 0.9pt + aod-pal.gold, fill: aod-pal.tint-amber, radius: 4pt)
  #aod-text(c3cx, y0 + 0.34, [*3. Dual $sans("C")_6$ Supports*], size: 8.6pt, box-w: 3.1, box-h: 0.38)

  // Upper Card: 3:4 on C_6, RD = 137
  #aod-box-tl(c3x + 0.16, y0 + 0.68, c3w - 0.32, 3.10, [], stroke: 0.9pt + aod-pal.blue, fill: white, radius: 3.5pt)
  #aod-circle(c3cx, y0 + 1.66, 0.42, fill: aod-pal.tint-blue, stroke: 0.95pt + aod-pal.blue)
  #aod-chiral-vertex(c3cx, y0 + 1.66, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-seat-ring(c3cx, y0 + 1.66, 0.68, 6, ring-stroke: 1.2pt + aod-pal.gold, seat-r: 0.062)
  #aod-text(c3cx, y0 + 2.82, [$C_sigma [3":"4; sans("C")_6]_(A arrow.l.r Omega)$], size: 8.6pt, box-w: 2.95, box-h: 0.40)
  #aod-text(c3cx, y0 + 3.36, [$R D_(A arrow.l.r Omega) (3":"4) = 137$], size: 8.6pt, weight: "bold", box-w: 2.95, box-h: 0.40)

  // Lower Card: 3:3 on C_6, RD = 61
  #aod-box-tl(c3x + 0.16, y0 + 3.98, c3w - 0.32, 3.10, [], stroke: 0.9pt + aod-pal.teal, fill: white, radius: 3.5pt)
  #aod-circle(c3cx, y0 + 4.96, 0.42, fill: aod-pal.tint-green, stroke: 0.95pt + aod-pal.teal)
  #aod-chiral-vertex(c3cx, y0 + 4.96, [$0_H$], r: 0.28, text-size: 8.6pt)
  #aod-seat-ring(c3cx, y0 + 4.96, 0.68, 6, ring-stroke: 1.2pt + aod-pal.gold, seat-r: 0.062)
  #aod-text(c3cx, y0 + 6.12, [$C_sigma [3":"3; sans("C")_6]_(A arrow.l.r Omega)$], size: 8.6pt, box-w: 2.95, box-h: 0.40)
  #aod-text(c3cx, y0 + 6.66, [$R D_(A arrow.l.r Omega) (3":"3) = 61$], size: 8.6pt, weight: "bold", box-w: 2.95, box-h: 0.40)

  // === Col 4: S_B Coupling Vertex & LCM Firewall (x = 11.44 .. 14.75, w = 3.31) ===
  #let c4x = 11.44
  #let c4w = 3.31
  #let c4cx = c4x + c4w / 2
  #aod-box-tl(c4x, y0, c4w, ch, [], stroke: 0.9pt + aod-pal.navy, fill: aod-pal.tint-gray, radius: 4pt)
  #aod-text(c4cx, y0 + 0.34, [*4. Coupling vs LCM*], size: 8.0pt, box-w: 3.15, box-h: 0.38)

  // Upper: S_B Coupling Zone
  #aod-box-tl(c4x + 0.16, y0 + 0.68, c4w - 0.32, 3.06, [], stroke: 0.95pt + aod-pal.purple, fill: aod-pal.tint-purple, radius: 3.5pt)
  #aod-text(c4cx, y0 + 1.02, [*Admitted Coupling*], size: 8.0pt, box-w: 2.9, box-h: 0.36)
  #aod-chiral-vertex(c4x + 0.76, y0 + 1.84, [$frak(S)_B$], r: 0.31, fill: aod-pal.tint-amber, stroke: 1.05pt + aod-pal.gold, text-size: 9.0pt)
  #aod-wavy-arrow(c4x + 1.10, y0 + 1.84, c4x + c4w - 0.28, y0 + 1.84, amp: 0.065, waves: 3.0, stroke: 1.1pt + aod-pal.purple, head-len: 3.8, head-half: 1.8)
  #aod-text(c4cx, y0 + 2.66, [$frak(S)_B (C_(3":"4), C_(3":"3))$], size: 8.6pt, weight: "bold", box-w: 2.95, box-h: 0.42)
  #aod-text(c4cx, y0 + 3.24, [couples bound beats \ via committed trace], size: 7.4pt, box-w: 2.9, box-h: 0.56)

  // Crimson Firewall Divider
  #aod-line(c4x + 0.16, y0 + 3.88, c4x + c4w - 0.16, y0 + 3.88, stroke: (paint: aod-pal.crimson, thickness: 1.1pt, dash: "dashed"))

  // Lower: LCM Firewall Card
  #aod-box-tl(c4x + 0.16, y0 + 4.02, c4w - 0.32, 3.06, [], stroke: 0.95pt + aod-pal.crimson, fill: aod-pal.tint-orange, radius: 3.5pt)
  #aod-text(c4cx, y0 + 4.36, [*Periodic Display Only*], size: 8.0pt, box-w: 2.9, box-h: 0.38)
  #aod-text(c4cx, y0 + 5.02, [$T_(upright("sync")) = op("lcm")(137, 61)$], size: 8.6pt, box-w: 2.95, box-h: 0.42)
  #aod-text(c4cx, y0 + 5.52, [$= 8357$], size: 9.2pt, weight: "bold", box-w: 2.6, box-h: 0.38)
  #aod-box-tl(c4x + 0.24, y0 + 5.96, c4w - 0.48, 0.90, [
    #text(size: 7.4pt, weight: "bold")[LCM alone never \ establishes coupling]
  ], stroke: 0.8pt + aod-pal.crimson, fill: white, radius: 3pt, inset: 3pt)

  // Converging Arrows Col 3 -> Col 4 drawn on top for crisp attachment
  #aod-arrow(11.10, y0 + 2.22, 11.42, y0 + 1.98, stroke: 1.05pt + aod-pal.purple, head-len: 3.6, head-half: 1.7)
  #aod-arrow(11.10, y0 + 5.48, 11.42, y0 + 2.40, stroke: 1.05pt + aod-pal.purple, head-len: 3.6, head-half: 1.7)

  // --- Bottom Invariant Bar (y = 8.82 .. 9.70) ---
  #aod-box-tl(
    0.25, 8.82, 14.50, 0.86,
    [#text(size: 8.6pt)[*Ontological separation:* Tesseract sections count support occurrences ($N_(upright("support"))$); distinct certified reclosures count beats; $frak(S)_B$ couples bound lineages.]],
    stroke: 0.9pt + aod-pal.navy,
    fill: aod-pal.tint-blue,
    radius: 3.5pt,
    inset: 5pt,
  )
]
