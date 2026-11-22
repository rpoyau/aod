// Manual AOD native Typst preamble (mirrors manual/preamble.tex).
#import "../lib/aod_schema.typ": *

#let aod-manual-doc(body) = aod-document(
  title: "Alpha↔Omega Dynamics (AΩD) - Manual",
  author: AODDocumentAuthor,
  subject: "The Hidden Temporal Dynamics of Stokes Manual; The Art Of The Leprechaun: Fractal Calculus; AFC/AOD finite simulation fixtures, boundary accounting, data-support classes, scoped error",
  keywords: (
    "Axiomatic Fundamentalism",
    "AFC",
    "AOD",
    "AΩD",
    "Stokes",
    "SADAR",
    "manual",
    "boundary accounting",
    "data-support classes",
    "scoped error",
    "finite simulation fixtures",
  ),
  bib-path: "/manual/refs.bib",
  is-manual: true,
  main-registry-path: "/typst/lib/main_registry.json",
  expected-main-digest: sys.inputs.at("expected_main_digest", default: none),
  body,
)
