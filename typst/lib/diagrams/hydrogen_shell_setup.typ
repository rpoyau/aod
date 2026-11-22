// Authoritative shared native Typst diagram for fig:manual-hydrogen-shell-setup.
#import "../aod_schema.typ": *

#aod-flowchart(
  width: 14.2cm,
  height: 6.0cm,
  (
    (id: "scope", x: 7.1cm, y: 0.7cm, w: 6.2cm, h: 1.05cm, body: [Hydrogen-facing scope \ $bold(upright(a))_H tack.r (F_H, R_H, partial R_H, omega_H)$]),
    (id: "shells", x: 7.1cm, y: 2.2cm, w: 5.8cm, h: 1.05cm, body: [Shell ladder \ $S_n, quad hat(P)_(S_n)^D = -1 slash n^2$]),
    (id: "partial", x: 3.5cm, y: 3.75cm, w: 6.0cm, h: 1.05cm, body: [Released shell-pressure magnitude \ $Delta hat(P)^D (n arrow.r m) > 0$]),
    (id: "targets", x: 10.7cm, y: 3.75cm, w: 6.0cm, h: 1.05cm, body: [Measured comparison \ $lambda, med f = c slash lambda, med E = h f$]),
    (id: "audit", x: 7.1cm, y: 5.3cm, w: 5.4cm, h: 1.05cm, body: [Audit \ ratio, error, provenance]),
  ),
  (
    (from: "scope", to: "shells"),
    (from: "shells", to: "partial"),
    (from: "shells", to: "targets"),
    (from: "partial", to: "audit"),
    (from: "targets", to: "audit"),
  ),
)
