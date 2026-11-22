// Native Typst Main title page (mirrors sections/00_title.tex).
#import "../preamble.typ": *

#page(numbering: none)[
  #v(1fr)
  #align(center)[
    #text(size: 17pt)[Alpha$arrow.l.r$Omega Dynamics (A$Omega$D)]
    #v(0.35em)
    #text(size: 14pt)[The Hidden Temporal Dynamics of Stokes]
    #v(0.45em)
    #text(size: 12pt, style: "italic")[The Art Of The Leprechaun: Fractal Calculus – #SADARop]
    #v(0.65em)
    #text(size: 12pt)[43 $""^(circle.tiny)upright("c")$]
    #v(0.45em)
    #text(size: 12pt)[#AODDocumentAuthor]
    #v(0.25em)
    #text(size: 10pt)[#AODDocumentDate]
    #v(0.55em)
    #math.equation(block: true, numbering: none, $ A scripts(arrow.l.r)_mu Omega med arrow.l.r.long med Omega scripts(arrow.l.r)_mu A $)
    #v(1.35em)
    #text(size: 10pt, style: "italic")[Epitaph]
    #v(0.2em)
    #math.equation(block: true, numbering: none, $ cal(N) equiv infinity wide cal(N) arrow.r cal(N) arrow.r cal(N) equiv cal(N) $)
    #text(size: 10pt, style: "italic")[Comprehension, cooperation, and presence are not prerequisites of AFC.]
    #v(0.2em)
    #text(size: 10pt, style: "italic")[Nuff said.]
  ]
  #v(2fr)
]
#counter(page).update(1)
