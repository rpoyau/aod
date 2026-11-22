// Authoritative shared native Typst diagram for fig:manual-boundary-current-spine.
#import "../aod_schema.typ": *

#aod-flowchart(
  width: 14.2cm,
  height: 7.5cm,
  (
    (id: "scope", x: 7.1cm, y: 0.65cm, w: 5.8cm, h: 1.0cm, body: [declared scope \ $bold(upright(a)) tack.r (F, R, partial R, omega)$]),
    (id: "flux", x: 7.1cm, y: 2.05cm, w: 5.8cm, h: 1.0cm, body: [scoped flux \ $phi.alt_(i j)(B) = p_(i j)^D (B) A_(i j)(B)$]),
    (id: "slice", x: 3.4cm, y: 3.5cm, w: 5.4cm, h: 1.0cm, body: [slice flux \ $Phi_(partial R)^D (t; B|_t)$]),
    (id: "moving", x: 10.6cm, y: 3.5cm, w: 6.4cm, h: 1.0cm, body: [moving boundary \ $Phi_(upright("cross"))^D - Phi_(upright("sweep"))^D + Phi_(upright("shedding"))^D$]),
    (id: "window", x: 7.1cm, y: 5.0cm, w: 5.4cm, h: 1.0cm, body: [window current \ $J_(partial R)^D (omega; B)$]),
    (id: "sadar", x: 7.1cm, y: 6.5cm, w: 6.0cm, h: 1.0cm, body: [SADAR attention \ $bold(upright(A))_F (B) = sum phi.alt_(i j)(B)$]),
  ),
  (
    (from: "scope", to: "flux"),
    (from: "flux", to: "slice"),
    (from: "flux", to: "moving"),
    (from: "slice", to: "window"),
    (from: "moving", to: "window"),
    (from: "window", to: "sadar"),
  ),
)
