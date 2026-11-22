// Authoritative shared native Typst diagram for fig:manual-short-window-setup.
#import "../aod_schema.typ": *

#aod-flowchart(
  width: 14.2cm,
  height: 7.4cm,
  (
    (id: "scope", x: 7.1cm, y: 0.7cm, w: 6.2cm, h: 1.05cm, body: [short-window scope \ $B_(upright("sw")) = (partial F_(upright("sw")), omega_(upright("sw")))$]),
    (id: "rd", x: 7.1cm, y: 2.2cm, w: 5.4cm, h: 1.05cm, body: [path support \ $rho^D = R D^((1))(1":"2) = 9$]),
    (id: "clip", x: 7.1cm, y: 3.7cm, w: 5.2cm, h: 1.05cm, body: [clip \ $rho_omega^D = min(rho^D, |omega|)$]),
    (id: "overhang", x: 3.4cm, y: 5.25cm, w: 5.8cm, h: 1.05cm, body: [pending overhang \ $Q^D = C_3 max(0, rho^D - |omega|)$]),
    (id: "closure", x: 10.8cm, y: 5.25cm, w: 5.8cm, h: 1.05cm, body: [closure residual \ $Delta^(upright("close")) = P^D - C^(upright("close"))$]),
    (id: "shed", x: 7.1cm, y: 6.75cm, w: 6.0cm, h: 1.05cm, body: [shedding \ $X_(upright("shedding")) = max(0, Delta^(upright("close")))$]),
  ),
  (
    (from: "scope", to: "rd"),
    (from: "rd", to: "clip"),
    (from: "clip", to: "overhang"),
    (from: "clip", to: "closure"),
    (from: "closure", to: "shed"),
  ),
)
