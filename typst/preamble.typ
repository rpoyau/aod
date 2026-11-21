// Main AOD native Typst preamble (mirrors preamble.tex).
#import "lib/aod_schema.typ": *

#let aod-main-doc(body) = aod-document(
  title: "Alpha↔Omega Dynamics (AΩD)",
  author: AODDocumentAuthor,
  subject: "The Hidden Temporal Dynamics of Stokes; The Art Of The Leprechaun: Fractal Calculus; AFC/AOD temporal dynamics, ontology, certified closure, discrete recurrence, relational time, finite Fourier representation, Awareness",
  keywords: (
    "Axiomatic Fundamentalism",
    "AFC",
    "AOD",
    "AΩD",
    "Stokes",
    "SADAR",
    "ontology",
    "certified closure",
    "discrete recurrence",
    "relational time",
    "finite Fourier representation",
    "Awareness",
  ),
  bib-path: "/refs.bib",
  is-manual: false,
  body,
)
