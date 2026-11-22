// Authoritative shared native Typst diagram for fig:manual-solar-system-spine.
#import "../aod_schema.typ": *

#aod-flowchart(
  width: 14.8cm,
  height: 5.2cm,
  (
    (id: "sun", x: 7.4cm, y: 0.7cm, w: 5.6cm, h: 1.05cm, body: [Sun field scope \ $B_dot.o = (partial F_dot.o, omega_dot.o)$]),
    (id: "mercury", x: 2.4cm, y: 2.55cm, w: 4.3cm, h: 1.05cm, body: [Mercury boundary \ perihelion window]),
    (id: "light", x: 7.4cm, y: 2.55cm, w: 4.4cm, h: 1.05cm, body: [solar-limb boundary \ light-bending record]),
    (id: "redshift", x: 12.4cm, y: 2.55cm, w: 4.5cm, h: 1.05cm, body: [solar-surface transfer \ redshift record]),
    (id: "compare", x: 7.4cm, y: 4.4cm, w: 9.2cm, h: 1.05cm, body: [comparison fixtures \ map value $arrow.r$ target $arrow.r$ residual $arrow.r$ error]),
  ),
  (
    (from: "sun", to: "mercury"),
    (from: "sun", to: "light"),
    (from: "sun", to: "redshift"),
    (from: "mercury", to: "compare"),
    (from: "light", to: "compare"),
    (from: "redshift", to: "compare"),
  ),
)
