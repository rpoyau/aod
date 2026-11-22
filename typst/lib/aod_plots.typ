// Pure built-in offline Typst vector plotting and schematic library for AOD (S1b).
// Zero external @preview/* dependencies; all text renders in opaque black (>= 6pt)
// for print legibility and Gate C text-paint compliance.

#let aod-pal = (
  blue: rgb("#0072B2"),
  navy: rgb("#1B4965"),
  orange: rgb("#D55E00"),
  teal: rgb("#009E73"),
  sky: rgb("#56B4E9"),
  amber: rgb("#E69F00"),
  gold: rgb("#B7791F"),
  purple: rgb("#6B4C9A"),
  crimson: rgb("#C0392B"),
  green: rgb("#2E7D32"),
  slate: rgb("#566573"),
  grid: rgb("#DCDCDC"),
  axis: rgb("#222222"),
  tint-blue: rgb("#EEF5FC"),
  tint-green: rgb("#EEF8F1"),
  tint-orange: rgb("#FDF3EB"),
  tint-purple: rgb("#F5F0FB"),
  tint-gray: rgb("#F4F6F8"),
  tint-amber: rgb("#FFF7E6"),
)

// Resolve paint color from a Typst stroke or color value.
#let _stroke-paint(s) = {
  if type(s) == color {
    s
  } else if type(s) == stroke {
    if s.paint != auto { s.paint } else { black }
  } else if type(s) == dictionary {
    s.at("paint", default: black)
  } else {
    black
  }
}

// Root fixed-size white canvas for standalone vector export and direct document inclusion.
#let aod-canvas(w-cm, h-cm, body) = align(center)[
  #box(width: w-cm * 1cm, height: h-cm * 1cm, fill: white, clip: false)[
    #set text(fill: black, size: 8pt)
    #set par(leading: 0.42em, spacing: 0.38em, justify: false)
    #body
  ]
]

// Place text anchored at (x, y) in cm.
#let aod-text(
  x,
  y,
  body,
  size: 8pt,
  weight: "regular",
  style: "normal",
  anchor: "center",
  box-w: 6.0,
  box-h: 1.4,
  angle: 0deg,
) = {
  let content = [
    #set text(fill: black, size: size, weight: weight, style: style)
    #body
  ]
  if angle != 0deg {
    let inner = rotate(angle, reflow: false, content)
    let dx-val = if anchor == "right" { x - box-w } else if anchor == "left" { x } else { x - box-w / 2 }
    let al = if anchor == "right" { right + horizon } else if anchor == "left" { left + horizon } else { center + horizon }
    place(top + left, dx: dx-val * 1cm, dy: (y - box-h / 2) * 1cm, box(width: box-w * 1cm, height: box-h * 1cm, align(al, inner)))
  } else {
    let dx-val = if anchor == "right" { x - box-w } else if anchor == "left" { x } else { x - box-w / 2 }
    let al = if anchor == "right" { right + horizon } else if anchor == "left" { left + horizon } else { center + horizon }
    place(top + left, dx: dx-val * 1cm, dy: (y - box-h / 2) * 1cm, box(width: box-w * 1cm, height: box-h * 1cm, align(al, content)))
  }
}

// Rounded box centered at (x, y) in cm.
#let aod-box(
  x,
  y,
  w,
  h,
  body,
  stroke: 0.85pt + aod-pal.navy,
  fill: white,
  radius: 3pt,
  inset: 3pt,
  align-mode: center + horizon,
) = {
  place(
    top + left,
    dx: (x - w / 2) * 1cm,
    dy: (y - h / 2) * 1cm,
    box(width: w * 1cm, height: h * 1cm, fill: fill, stroke: stroke, radius: radius, inset: inset)[
      #align(align-mode)[#body]
    ],
  )
}

// Rounded box with top-left corner at (x, y) in cm.
#let aod-box-tl(
  x,
  y,
  w,
  h,
  body,
  stroke: 0.85pt + aod-pal.navy,
  fill: white,
  radius: 3pt,
  inset: 3pt,
  align-mode: center + horizon,
) = {
  aod-box(x + w / 2, y + h / 2, w, h, body, stroke: stroke, fill: fill, radius: radius, inset: inset, align-mode: align-mode)
}

// Straight vector line between (x1, y1) and (x2, y2) in cm.
#let aod-line(x1, y1, x2, y2, stroke: 0.8pt + black) = {
  place(top + left, line(start: (x1 * 1cm, y1 * 1cm), end: (x2 * 1cm, y2 * 1cm), stroke: stroke))
}

// Circle centered at (cx, cy) with radius r in cm.
#let aod-circle(cx, cy, r, fill: none, stroke: 0.9pt + aod-pal.navy) = {
  place(
    top + left,
    dx: (cx - r) * 1cm,
    dy: (cy - r) * 1cm,
    circle(radius: r * 1cm, fill: fill, stroke: stroke),
  )
}

// Arrowhead polygon pointing from (ux, uy) direction with tip at (tx, ty) in cm.
#let _arrowhead(tx, ty, ux, uy, paint, head-len: 4.6, head-half: 2.2) = {
  let bx = tx * 1cm - (ux * head-len) * 1pt
  let by = ty * 1cm - (uy * head-len) * 1pt
  let lx = bx + (-uy * head-half) * 1pt
  let ly = by + (ux * head-half) * 1pt
  let rx = bx - (-uy * head-half) * 1pt
  let ry = by - (ux * head-half) * 1pt
  place(top + left, polygon(fill: paint, (tx * 1cm, ty * 1cm), (lx, ly), (rx, ry)))
}

// Vector arrow (single or double-headed; solid or dashed stroke).
#let aod-arrow(x1, y1, x2, y2, stroke: 0.9pt + aod-pal.slate, head-len: 4.6, head-half: 2.2, both: false) = {
  let dx = x2 - x1
  let dy = y2 - y1
  let dist = calc.sqrt(dx * dx + dy * dy)
  if dist > 0.001 {
    let ux = dx / dist
    let uy = dy / dist
    let paint = _stroke-paint(stroke)
    let len-cm = head-len * 2.54 / 72.0
    let sx = if both { x1 + ux * len-cm * 0.85 } else { x1 }
    let sy = if both { y1 + uy * len-cm * 0.85 } else { y1 }
    let ex = x2 - ux * len-cm * 0.85
    let ey = y2 - uy * len-cm * 0.85
    aod-line(sx, sy, ex, ey, stroke: stroke)
    _arrowhead(x2, y2, ux, uy, paint, head-len: head-len, head-half: head-half)
    if both {
      _arrowhead(x1, y1, -ux, -uy, paint, head-len: head-len, head-half: head-half)
    }
  }
}

// Quadratic Bezier curved arrow from (x1, y1) via (cx, cy) to (x2, y2) in cm.
#let aod-curve-arrow(x1, y1, cx, cy, x2, y2, stroke: 0.9pt + aod-pal.slate, head-len: 4.4, head-half: 2.1, both: false, steps: 20) = {
  let pts = ()
  for i in range(steps + 1) {
    let t = i / steps
    let omt = 1.0 - t
    let px = omt * omt * x1 + 2 * omt * t * cx + t * t * x2
    let py = omt * omt * y1 + 2 * omt * t * cy + t * t * y2
    pts.push((px, py))
  }
  let segs = (curve.move((pts.at(0).at(0) * 1cm, pts.at(0).at(1) * 1cm)),)
  for i in range(1, pts.len()) {
    segs.push(curve.line((pts.at(i).at(0) * 1cm, pts.at(i).at(1) * 1cm)))
  }
  place(top + left, curve(stroke: stroke, ..segs))
  let paint = _stroke-paint(stroke)
  // End arrowhead tangent
  let p-prev = pts.at(pts.len() - 2)
  let p-end = pts.at(pts.len() - 1)
  let edx = p-end.at(0) - p-prev.at(0)
  let edy = p-end.at(1) - p-prev.at(1)
  let ed = calc.sqrt(edx * edx + edy * edy)
  if ed > 0.0001 {
    _arrowhead(p-end.at(0), p-end.at(1), edx / ed, edy / ed, paint, head-len: head-len, head-half: head-half)
  }
  if both {
    let p0 = pts.at(0)
    let p1 = pts.at(1)
    let sdx = p0.at(0) - p1.at(0)
    let sdy = p0.at(1) - p1.at(1)
    let sd = calc.sqrt(sdx * sdx + sdy * sdy)
    if sd > 0.0001 {
      _arrowhead(p0.at(0), p0.at(1), sdx / sd, sdy / sd, paint, head-len: head-len, head-half: head-half)
    }
  }
}

// Circular arc arrow (standard math degrees, CCW in Cartesian = decreasing y in screen coords).
#let aod-arc-arrow(cx, cy, r, deg1, deg2, stroke: 0.9pt + aod-pal.navy, head-len: 3.6, head-half: 1.7, steps: 14) = {
  let pts = ()
  for i in range(steps + 1) {
    let deg = deg1 + (deg2 - deg1) * (i / steps)
    let rad = deg * 1deg
    let px = cx + r * calc.cos(rad)
    let py = cy - r * calc.sin(rad)
    pts.push((px, py))
  }
  let segs = (curve.move((pts.at(0).at(0) * 1cm, pts.at(0).at(1) * 1cm)),)
  for i in range(1, pts.len()) {
    segs.push(curve.line((pts.at(i).at(0) * 1cm, pts.at(i).at(1) * 1cm)))
  }
  place(top + left, curve(stroke: stroke, ..segs))
  let paint = _stroke-paint(stroke)
  let p-prev = pts.at(pts.len() - 2)
  let p-end = pts.at(pts.len() - 1)
  let dx = p-end.at(0) - p-prev.at(0)
  let dy = p-end.at(1) - p-prev.at(1)
  let d = calc.sqrt(dx * dx + dy * dy)
  if d > 0.0001 {
    _arrowhead(p-end.at(0), p-end.at(1), dx / d, dy / d, paint, head-len: head-len, head-half: head-half)
  }
}

// Marker centered at (cx, cy) in cm.
#let aod-marker(cx, cy, kind: "circle", r-pt: 2.3, color: aod-pal.blue) = {
  let r-cm = r-pt * 2.54 / 72.0
  if kind == "circle" {
    aod-circle(cx, cy, r-cm, fill: color, stroke: 0.35pt + color)
  } else if kind == "open-circle" {
    aod-circle(cx, cy, r-cm, fill: white, stroke: 0.9pt + color)
  } else if kind == "cross" {
    let d = r-cm * 0.9
    aod-line(cx - d, cy - d, cx + d, cy + d, stroke: 1.0pt + color)
    aod-line(cx - d, cy + d, cx + d, cy - d, stroke: 1.0pt + color)
  }
}

// Concentric outer seat ring with n evenly placed seats.
#let aod-seat-ring(
  cx,
  cy,
  r,
  n,
  ring-stroke: 1.2pt + aod-pal.gold,
  seat-r: 0.065,
  seat-fill: aod-pal.tint-amber,
  seat-stroke: 0.7pt + aod-pal.gold,
) = {
  aod-circle(cx, cy, r, fill: none, stroke: ring-stroke)
  for k in range(n) {
    let ang = (360.0 * k / n) * 1deg
    let sx = cx + r * calc.cos(ang)
    let sy = cy - r * calc.sin(ang)
    aod-circle(sx, sy, seat-r, fill: seat-fill, stroke: seat-stroke)
  }
}

// Numbered light badge (opaque black number for Gate C text-paint compliance).
#let aod-badge(cx, cy, num, r: 0.19, fill: aod-pal.tint-blue, stroke: 0.9pt + aod-pal.navy) = {
  aod-circle(cx, cy, r, fill: fill, stroke: stroke)
  aod-text(cx, cy, [#num], size: 7pt, weight: "bold", box-w: 0.5, box-h: 0.5)
}

// =============================================================================
// 2D Cartesian Plot Engine (linear/log-y, lines, steps, stacked areas, bars,
// grouped bars, errorbars, reference lines, grids, legends).
// =============================================================================
#let aod-xy-plot(
  x0: 0.0,
  y0: 0.0,
  w: 13.5,
  h: 7.0,
  pad: (left: 1.55, right: 0.45, top: 0.72, bottom: 1.05),
  title: none,
  title-size: 9.2pt,
  xlabel: none,
  ylabel: none,
  xlim: (0.0, 1.0),
  ylim: (0.0, 1.0),
  ylog: false,
  xticks: (),
  yticks: (),
  x-tick-angle: 0deg,
  x-tick-size: 7.2pt,
  y-tick-size: 7.2pt,
  x-tick-dy: 0.24,
  xlabel-dy: 0.68,
  ylabel-dx: 1.15,
  grid-y: true,
  grid-x: false,
  frame: "box",
  layers: (),
  legend: none,
  annotations: (),
) = {
  let pl = x0 + pad.left
  let pr = x0 + w - pad.right
  let pt = y0 + pad.top
  let pb = y0 + h - pad.bottom
  let pw = pr - pl
  let ph = pb - pt

  let xmin = float(xlim.at(0))
  let xmax = float(xlim.at(1))
  let ymin = float(ylim.at(0))
  let ymax = float(ylim.at(1))
  let ly-min = if ylog { calc.log(ymin, base: 10) } else { ymin }
  let ly-max = if ylog { calc.log(ymax, base: 10) } else { ymax }

  let mx(v) = pl + ((float(v) - xmin) / (xmax - xmin)) * pw
  let my(v) = {
    let fv = float(v)
    let tv = if ylog { calc.log(calc.max(fv, ymin * 0.5), base: 10) } else { fv }
    pb - ((tv - ly-min) / (ly-max - ly-min)) * ph
  }

  // Title
  if title != none {
    aod-text((pl + pr) / 2, pt - 0.34, title, size: title-size, weight: "bold", box-w: pw + 2.0, box-h: 0.6)
  }

  // Grid lines
  if grid-y {
    for tk in yticks {
      let yv = if type(tk) == array { tk.at(0) } else { tk }
      let py = my(yv)
      if py >= pt - 0.01 and py <= pb + 0.01 {
        aod-line(pl, py, pr, py, stroke: 0.45pt + aod-pal.grid)
      }
    }
  }
  if grid-x {
    for tk in xticks {
      let xv = if type(tk) == array { tk.at(0) } else { tk }
      let px = mx(xv)
      if px >= pl - 0.01 and px <= pr + 0.01 {
        aod-line(px, pt, px, pb, stroke: 0.45pt + aod-pal.grid)
      }
    }
  }

  // Plot data layers
  for layer in layers {
    let ltype = layer.at("type")
    if ltype == "hline" {
      let py = my(layer.y)
      aod-line(pl, py, pr, py, stroke: layer.at("stroke", default: 0.8pt + aod-pal.slate))
    } else if ltype == "stacked-area" {
      let xs = layer.xs
      let n = xs.len()
      let cum-prev = range(n).map(_ => 0.0)
      for ser in layer.series {
        let ys = ser.ys
        let cum-cur = range(n).map(i => cum-prev.at(i) + float(ys.at(i)))
        let segs = (curve.move((mx(xs.at(0)) * 1cm, my(cum-cur.at(0)) * 1cm)),)
        for i in range(1, n) {
          segs.push(curve.line((mx(xs.at(i)) * 1cm, my(cum-cur.at(i)) * 1cm)))
        }
        for i in range(n - 1, -1, step: -1) {
          segs.push(curve.line((mx(xs.at(i)) * 1cm, my(cum-prev.at(i)) * 1cm)))
        }
        segs.push(curve.close())
        place(top + left, curve(fill: ser.fill, stroke: ser.at("stroke", default: none), ..segs))
        cum-prev = cum-cur
      }
    } else if ltype == "bars" {
      let xs = layer.xs
      let ys = layer.ys
      let bw = float(layer.at("bar-w", default: 0.6))
      let fills = layer.at("fills", default: aod-pal.blue)
      let b-stroke = layer.at("stroke", default: none)
      let base-v = if layer.at("base", default: none) != none {
        float(layer.base)
      } else if ylog {
        ymin
      } else {
        0.0
      }
      let y-base = my(base-v)
      let vlabels = layer.at("value-labels", default: none)
      for i in range(xs.len()) {
        let xv = float(xs.at(i))
        let yv = float(ys.at(i))
        let fl = if type(fills) == array { fills.at(i) } else { fills }
        let x-left = mx(xv - bw / 2.0)
        let x-right = mx(xv + bw / 2.0)
        let y-val = my(yv)
        let y-top = calc.min(y-val, y-base)
        let bh = calc.abs(y-val - y-base)
        if bh > 0.002 {
          place(
            top + left,
            dx: x-left * 1cm,
            dy: y-top * 1cm,
            rect(width: (x-right - x-left) * 1cm, height: bh * 1cm, fill: fl, stroke: b-stroke),
          )
        }
        if vlabels != none {
          let lbl = vlabels.at(i)
          let ly = if yv >= base-v { y-val - 0.24 } else { y-val + 0.24 }
          aod-text(mx(xv), ly, lbl, size: 8pt, weight: "bold", box-w: 1.6, box-h: 0.4)
        }
      }
    } else if ltype == "grouped-bars" {
      let xs = layer.xs
      let series = layer.series
      let m = series.len()
      let gw = float(layer.at("group-w", default: 0.72))
      let bw = gw / m
      let base-v = if layer.at("base", default: none) != none {
        float(layer.base)
      } else if ylog {
        ymin
      } else {
        0.0
      }
      let y-base = my(base-v)
      for s-idx in range(m) {
        let ser = series.at(s-idx)
        let ys = ser.ys
        let fl = ser.fill
        let b-stroke = ser.at("stroke", default: none)
        let offset = -gw / 2.0 + (s-idx + 0.5) * bw
        for i in range(xs.len()) {
          let xv = float(xs.at(i)) + offset
          let yv = float(ys.at(i))
          let x-left = mx(xv - bw / 2.0)
          let x-right = mx(xv + bw / 2.0)
          let y-val = my(yv)
          let y-top = calc.min(y-val, y-base)
          let bh = calc.abs(y-val - y-base)
          if bh > 0.002 {
            place(
              top + left,
              dx: x-left * 1cm,
              dy: y-top * 1cm,
              rect(width: (x-right - x-left) * 1cm, height: bh * 1cm, fill: fl, stroke: b-stroke),
            )
          }
        }
      }
    } else if ltype == "step" {
      let xs = layer.xs
      let ys = layer.ys
      if xs.len() >= 2 {
        let segs = (curve.move((mx(xs.at(0)) * 1cm, my(ys.at(0)) * 1cm)),)
        for i in range(xs.len() - 1) {
          segs.push(curve.line((mx(xs.at(i + 1)) * 1cm, my(ys.at(i)) * 1cm)))
          segs.push(curve.line((mx(xs.at(i + 1)) * 1cm, my(ys.at(i + 1)) * 1cm)))
        }
        place(top + left, curve(stroke: layer.stroke, ..segs))
      }
    } else if ltype == "line" {
      let xs = layer.xs
      let ys = layer.ys
      if xs.len() >= 2 {
        let segs = (curve.move((mx(xs.at(0)) * 1cm, my(ys.at(0)) * 1cm)),)
        for i in range(1, xs.len()) {
          segs.push(curve.line((mx(xs.at(i)) * 1cm, my(ys.at(i)) * 1cm)))
        }
        place(top + left, curve(stroke: layer.stroke, ..segs))
      }
      let mk = layer.at("marker", default: none)
      if mk != none {
        let mc = layer.at("marker-color", default: _stroke-paint(layer.stroke))
        let mr = layer.at("marker-r", default: 2.3)
        for i in range(xs.len()) {
          aod-marker(mx(xs.at(i)), my(ys.at(i)), kind: mk, r-pt: mr, color: mc)
        }
      }
    } else if ltype == "errorbar" {
      let xs = layer.xs
      let ys = layer.ys
      let yerrs = layer.yerrs
      let col = layer.at("color", default: aod-pal.navy)
      let lw = layer.at("lw", default: 1.2pt)
      let cap = float(layer.at("cap-cm", default: 0.14))
      let mr = layer.at("marker-r", default: 2.5)
      for i in range(xs.len()) {
        let px = mx(xs.at(i))
        let yv = float(ys.at(i))
        let ye = float(yerrs.at(i))
        let py-lo = my(yv - ye)
        let py-hi = my(yv + ye)
        aod-line(px, py-lo, px, py-hi, stroke: lw + col)
        aod-line(px - cap, py-lo, px + cap, py-lo, stroke: lw + col)
        aod-line(px - cap, py-hi, px + cap, py-hi, stroke: lw + col)
        aod-marker(px, my(yv), kind: "circle", r-pt: mr, color: col)
      }
    }
  }

  // Axis frame & ticks
  if frame == "box" {
    place(top + left, dx: pl * 1cm, dy: pt * 1cm, rect(width: pw * 1cm, height: ph * 1cm, fill: none, stroke: 0.75pt + aod-pal.axis))
  } else {
    aod-line(pl, pt, pl, pb, stroke: 0.75pt + aod-pal.axis)
    aod-line(pl, pb, pr, pb, stroke: 0.75pt + aod-pal.axis)
  }

  for tk in xticks {
    let xv = if type(tk) == array { tk.at(0) } else { tk }
    let lbl = if type(tk) == array { tk.at(1) } else { [#tk] }
    let px = mx(xv)
    if px >= pl - 0.02 and px <= pr + 0.02 {
      aod-line(px, pb, px, pb + 0.10, stroke: 0.65pt + aod-pal.axis)
      if x-tick-angle != 0deg {
        aod-text(px + 0.05, pb + x-tick-dy, lbl, size: x-tick-size, anchor: "right", box-w: 3.4, box-h: 0.7, angle: x-tick-angle)
      } else {
        aod-text(px, pb + x-tick-dy, lbl, size: x-tick-size, anchor: "center", box-w: 2.2, box-h: 0.5)
      }
    }
  }

  for tk in yticks {
    let yv = if type(tk) == array { tk.at(0) } else { tk }
    let lbl = if type(tk) == array { tk.at(1) } else { [#tk] }
    let py = my(yv)
    if py >= pt - 0.02 and py <= pb + 0.02 {
      aod-line(pl - 0.10, py, pl, py, stroke: 0.65pt + aod-pal.axis)
      aod-text(pl - 0.16, py, lbl, size: y-tick-size, anchor: "right", box-w: 1.5, box-h: 0.45)
    }
  }

  // Axis labels
  if xlabel != none {
    aod-text((pl + pr) / 2, pb + xlabel-dy, xlabel, size: 8.2pt, box-w: pw + 1.5, box-h: 0.5)
  }
  if ylabel != none {
    aod-text(pl - ylabel-dx, (pt + pb) / 2, ylabel, size: 8.2pt, box-w: ph + 1.5, box-h: 0.5, angle: -90deg)
  }

  // Optional annotations in data coordinates: (x, y, body, size)
  for ann in annotations {
    let ax = mx(ann.x)
    let ay = my(ann.y)
    aod-text(ax, ay, ann.body, size: ann.at("size", default: 7.5pt), anchor: ann.at("anchor", default: "center"), box-w: ann.at("box-w", default: 4.5), box-h: 0.5)
  }

  // Optional legend
  if legend != none {
    let pos = legend.at("pos", default: "top-right")
    let items = legend.items
    let cols = legend.at("cols", default: 1)
    let item-h = 0.34
    let col-w = float(legend.at("col-w", default: 3.35))
    let nrows = calc.ceil(items.len() / cols)
    let lw-cm = cols * col-w + 0.25
    let lh-cm = nrows * item-h + 0.18
    let lx = if pos in ("top-right", "bottom-right") {
      pr - lw-cm - 0.16
    } else if pos == "above" {
      pl + 0.05
    } else {
      pl + 0.16
    }
    let ly = if pos in ("top-right", "top-left") {
      pt + 0.14
    } else if pos == "above" {
      pt - lh-cm - 0.05
    } else {
      pb - lh-cm - 0.14
    }
    let show-frame = legend.at("frame", default: pos != "above")
    if show-frame {
      place(
        top + left,
        dx: lx * 1cm,
        dy: ly * 1cm,
        rect(width: lw-cm * 1cm, height: lh-cm * 1cm, fill: white, stroke: 0.55pt + rgb("#BBBBBB"), radius: 2pt),
      )
    }
    for idx in range(items.len()) {
      let it = items.at(idx)
      let c = calc.rem(idx, cols)
      let r = calc.quo(idx, cols)
      let ix = lx + 0.16 + c * col-w
      let iy = ly + 0.09 + (r + 0.5) * item-h
      let kind = it.at("kind", default: "line")
      let col = it.at("color", default: aod-pal.blue)
      let dash = it.at("dash", default: none)
      let st = if dash != none { (paint: col, thickness: 1.3pt, dash: dash) } else { 1.3pt + col }
      if kind == "patch" {
        place(top + left, dx: ix * 1cm, dy: (iy - 0.08) * 1cm, rect(width: 0.42cm, height: 0.16cm, fill: col, stroke: none))
      } else if kind == "errorbar" {
        aod-line(ix + 0.21, iy - 0.11, ix + 0.21, iy + 0.11, stroke: 1.0pt + col)
        aod-line(ix + 0.13, iy - 0.11, ix + 0.29, iy - 0.11, stroke: 1.0pt + col)
        aod-line(ix + 0.13, iy + 0.11, ix + 0.29, iy + 0.11, stroke: 1.0pt + col)
        aod-marker(ix + 0.21, iy, kind: "circle", r-pt: 2.0, color: col)
      } else {
        aod-line(ix, iy, ix + 0.44, iy, stroke: st)
        if it.at("marker", default: none) != none {
          aod-marker(ix + 0.22, iy, kind: it.marker, r-pt: 2.0, color: col)
        }
      }
      aod-text(ix + 0.54, iy, it.label, size: legend.at("size", default: 7.0pt), anchor: "left", box-w: col-w - 0.56, box-h: 0.36)
    }
  }
}

// =============================================================================
// Annotated Matrix Heatmap with Colorbar (high-contrast opaque black cell text)
// =============================================================================
#let aod-heatmap(
  x0: 0.0,
  y0: 0.0,
  w: 14.0,
  h: 7.0,
  pad: (left: 1.75, right: 1.55, top: 0.72, bottom: 1.65),
  title: none,
  row-labels: (),
  col-labels: (),
  matrix: (),
  vmin: 0.0,
  vmax: 31.0,
  cbar-label: "tally",
  cbar-ticks: (0, 5, 10, 15, 20, 25, 30),
) = {
  let pl = x0 + pad.left
  let pr = x0 + w - pad.right
  let pt = y0 + pad.top
  let pb = y0 + h - pad.bottom
  let pw = pr - pl
  let ph = pb - pt
  let nrows = row-labels.len()
  let ncols = col-labels.len()
  let cw = pw / ncols
  let ch = ph / nrows

  // Smooth accessible light-to-medium blue ramp (keeps black integer text high-contrast)
  let ramp(val) = {
    let t = calc.min(1.0, calc.max(0.0, (float(val) - float(vmin)) / (float(vmax) - float(vmin))))
    let r = int(calc.round(247.0 + t * (95.0 - 247.0)))
    let g = int(calc.round(251.0 + t * (162.0 - 251.0)))
    let b = int(calc.round(255.0 + t * (216.0 - 255.0)))
    rgb(r, g, b)
  }

  if title != none {
    aod-text((pl + pr) / 2, pt - 0.34, title, size: 9.2pt, weight: "bold", box-w: pw + 2.0, box-h: 0.55)
  }

  for r in range(nrows) {
    let cy = pt + (r + 0.5) * ch
    aod-text(pl - 0.16, cy, row-labels.at(r), size: 7.5pt, anchor: "right", box-w: 1.55, box-h: 0.45)
    for c in range(ncols) {
      let val = matrix.at(r).at(c)
      let cx = pl + (c + 0.5) * cw
      place(
        top + left,
        dx: (pl + c * cw) * 1cm,
        dy: (pt + r * ch) * 1cm,
        rect(width: cw * 1cm, height: ch * 1cm, fill: ramp(val), stroke: 0.25pt + rgb("#DDE6F0")),
      )
      aod-text(cx, cy, [#val], size: 7.5pt, box-w: cw, box-h: ch)
    }
  }

  place(top + left, dx: pl * 1cm, dy: pt * 1cm, rect(width: pw * 1cm, height: ph * 1cm, fill: none, stroke: 0.75pt + aod-pal.axis))

  for c in range(ncols) {
    let cx = pl + (c + 0.5) * cw
    aod-line(cx, pb, cx, pb + 0.08, stroke: 0.65pt + aod-pal.axis)
    aod-text(cx + 0.08, pb + 0.80, col-labels.at(c), size: 7.0pt, anchor: "right", box-w: 3.1, box-h: 0.6, angle: -32deg)
  }

  // Colorbar
  let cbx = pr + 0.35
  let cbw = 0.32
  let nsteps = 32
  let sh = ph / nsteps
  for i in range(nsteps) {
    let frac = (i + 0.5) / nsteps
    let val = float(vmin) + frac * (float(vmax) - float(vmin))
    let sy = pb - (i + 1) * sh
    place(top + left, dx: cbx * 1cm, dy: sy * 1cm, rect(width: cbw * 1cm, height: (sh + 0.005) * 1cm, fill: ramp(val), stroke: none))
  }
  place(top + left, dx: cbx * 1cm, dy: pt * 1cm, rect(width: cbw * 1cm, height: ph * 1cm, fill: none, stroke: 0.7pt + aod-pal.axis))
  for tk in cbar-ticks {
    let frac = (float(tk) - float(vmin)) / (float(vmax) - float(vmin))
    let ty = pb - frac * ph
    aod-line(cbx + cbw, ty, cbx + cbw + 0.08, ty, stroke: 0.6pt + aod-pal.axis)
    aod-text(cbx + cbw + 0.14, ty, [#tk], size: 7.0pt, anchor: "left", box-w: 0.7, box-h: 0.4)
  }
  aod-text(cbx + cbw + 0.72, (pt + pb) / 2, cbar-label, size: 7.8pt, box-w: 2.5, box-h: 0.45, angle: -90deg)
}

// =============================================================================
// Discrete Mode Strip (init / run / tumble color band strip)
// =============================================================================
#let aod-mode-strip(
  x0: 0.0,
  y0: 0.0,
  w: 6.2,
  h: 3.1,
  pad: (left: 0.55, right: 0.25, top: 0.58, bottom: 0.58),
  title: none,
  modes: (),
  color-map: (:),
  xticks: (0, 5, 10, 15, 20),
) = {
  let pl = x0 + pad.left
  let pr = x0 + w - pad.right
  let pt = y0 + pad.top
  let pb = y0 + h - pad.bottom
  let pw = pr - pl
  let ph = pb - pt
  let n = modes.len()
  let bw = pw / n

  if title != none {
    aod-text((pl + pr) / 2, pt - 0.28, title, size: 8.5pt, weight: "bold", box-w: pw + 1.0, box-h: 0.45)
  }
  for i in range(n) {
    let col = color-map.at(modes.at(i), default: aod-pal.slate)
    place(top + left, dx: (pl + i * bw) * 1cm, dy: pt * 1cm, rect(width: (bw + 0.005) * 1cm, height: ph * 1cm, fill: col, stroke: none))
  }
  place(top + left, dx: pl * 1cm, dy: pt * 1cm, rect(width: pw * 1cm, height: ph * 1cm, fill: none, stroke: 0.75pt + aod-pal.axis))
  let vmax = float(xticks.at(xticks.len() - 1))
  for tk in xticks {
    let px = pl + (float(tk) / vmax) * pw
    aod-line(px, pb, px, pb + 0.08, stroke: 0.65pt + aod-pal.axis)
    aod-text(px, pb + 0.24, [#tk], size: 7.0pt, box-w: 0.8, box-h: 0.35)
  }
}

// =============================================================================
// Exact Orthographic 3D Wireframe Trajectory Plot (matches matplotlib elev/azim)
// =============================================================================
#let aod-3d-wireframe(
  x0: 0.0,
  y0: 0.0,
  w: 6.2,
  h: 5.2,
  title: none,
  xlim: (0, 6),
  ylim: (0, 5),
  zlim: (0, 5),
  xticks: (0, 1, 2, 3, 4, 5, 6),
  yticks: (0, 1, 2, 3, 4, 5),
  zticks: (0, 1, 2, 3, 4, 5),
  elev: 22.0,
  azim: -58.0,
  points: (),
  stroke: 1.4pt + black,
  marker-color: black,
  chord: false,
  annotations: (),
) = {
  let el = elev * 1deg
  let az = azim * 1deg
  let raw-proj(x, y, z) = {
    let fx = float(x)
    let fy = float(y)
    let fz = float(z)
    let u = -calc.sin(az) * fx + calc.cos(az) * fy
    let v = -calc.sin(el) * calc.cos(az) * fx - calc.sin(el) * calc.sin(az) * fy + calc.cos(el) * fz
    (u, v)
  }

  let xlo = float(xlim.at(0))
  let xhi = float(xlim.at(1))
  let ylo = float(ylim.at(0))
  let yhi = float(ylim.at(1))
  let zlo = float(zlim.at(0))
  let zhi = float(zlim.at(1))

  // Compute bounding box over all 8 cube corners
  let corners = ()
  for cx in (xlo, xhi) {
    for cy in (ylo, yhi) {
      for cz in (zlo, zhi) {
        corners.push(raw-proj(cx, cy, cz))
      }
    }
  }
  let umin = calc.min(..corners.map(c => c.at(0)))
  let umax = calc.max(..corners.map(c => c.at(0)))
  let vmin = calc.min(..corners.map(c => c.at(1)))
  let vmax = calc.max(..corners.map(c => c.at(1)))

  let pl = x0 + 0.55
  let pr = x0 + w - 0.65
  let pt = y0 + (if title != none { 0.62 } else { 0.25 })
  let pb = y0 + h - 0.68
  let pw = pr - pl
  let ph = pb - pt
  let sc = calc.min(pw / (umax - umin), ph / (vmax - vmin))
  let cu = (umin + umax) / 2.0
  let cv = (vmin + vmax) / 2.0
  let midx = (pl + pr) / 2.0
  let midy = (pt + pb) / 2.0

  let proj(x, y, z) = {
    let uv = raw-proj(x, y, z)
    (midx + (uv.at(0) - cu) * sc, midy - (uv.at(1) - cv) * sc)
  }

  if title != none {
    aod-text((pl + pr) / 2, y0 + 0.26, title, size: 8.8pt, weight: "bold", box-w: w, box-h: 0.45)
  }

  // Light shaded back planes (floor z=zlo, left wall x=xlo, back wall y=yhi)
  let fill-quad(p1, p2, p3, p4, fl) = {
    place(top + left, polygon(
      fill: fl,
      stroke: 0.45pt + rgb("#B8B8B8"),
      (p1.at(0) * 1cm, p1.at(1) * 1cm),
      (p2.at(0) * 1cm, p2.at(1) * 1cm),
      (p3.at(0) * 1cm, p3.at(1) * 1cm),
      (p4.at(0) * 1cm, p4.at(1) * 1cm),
    ))
  }
  fill-quad(proj(xlo, ylo, zlo), proj(xhi, ylo, zlo), proj(xhi, yhi, zlo), proj(xlo, yhi, zlo), rgb("#F3F4F6"))
  fill-quad(proj(xlo, ylo, zlo), proj(xlo, yhi, zlo), proj(xlo, yhi, zhi), proj(xlo, ylo, zhi), rgb("#F7F8FA"))
  fill-quad(proj(xlo, yhi, zlo), proj(xhi, yhi, zlo), proj(xhi, yhi, zhi), proj(xlo, yhi, zhi), rgb("#EFF1F4"))

  // Gridlines on floor and back walls
  let g-stroke = 0.4pt + rgb("#CCCCCC")
  for xv in xticks {
    let a = proj(xv, ylo, zlo); let b = proj(xv, yhi, zlo); let c = proj(xv, yhi, zhi)
    aod-line(a.at(0), a.at(1), b.at(0), b.at(1), stroke: g-stroke)
    aod-line(b.at(0), b.at(1), c.at(0), c.at(1), stroke: g-stroke)
  }
  for yv in yticks {
    let a = proj(xlo, yv, zlo); let b = proj(xhi, yv, zlo); let c = proj(xlo, yv, zhi)
    aod-line(a.at(0), a.at(1), b.at(0), b.at(1), stroke: g-stroke)
    aod-line(a.at(0), a.at(1), c.at(0), c.at(1), stroke: g-stroke)
  }
  for zv in zticks {
    let a = proj(xlo, ylo, zv); let b = proj(xlo, yhi, zv); let c = proj(xhi, yhi, zv)
    aod-line(a.at(0), a.at(1), b.at(0), b.at(1), stroke: g-stroke)
    aod-line(b.at(0), b.at(1), c.at(0), c.at(1), stroke: g-stroke)
  }

  // Front axis spines + tick labels
  let ax-st = 0.7pt + aod-pal.axis
  let p-ox = proj(xlo, ylo, zlo); let p-x1 = proj(xhi, ylo, zlo)
  let p-y1 = proj(xhi, yhi, zlo); let p-z1 = proj(xhi, yhi, zhi)
  aod-line(p-ox.at(0), p-ox.at(1), p-x1.at(0), p-x1.at(1), stroke: ax-st)
  aod-line(p-x1.at(0), p-x1.at(1), p-y1.at(0), p-y1.at(1), stroke: ax-st)
  aod-line(p-y1.at(0), p-y1.at(1), p-z1.at(0), p-z1.at(1), stroke: ax-st)

  for xv in xticks {
    let p = proj(xv, ylo, zlo)
    aod-text(p.at(0) - 0.08, p.at(1) + 0.22, [#xv], size: 6.8pt, box-w: 0.6, box-h: 0.32)
  }
  for yv in yticks {
    let p = proj(xhi, yv, zlo)
    aod-text(p.at(0) + 0.20, p.at(1) + 0.14, [#yv], size: 6.8pt, box-w: 0.6, box-h: 0.32)
  }
  for zv in zticks {
    let p = proj(xhi, yhi, zv)
    aod-text(p.at(0) + 0.24, p.at(1), [#zv], size: 6.8pt, box-w: 0.6, box-h: 0.32)
  }
  let lx = proj((xlo + xhi) / 2.0, ylo, zlo)
  let ly = proj(xhi, (ylo + yhi) / 2.0, zlo)
  let lz = proj(xhi, yhi, (zlo + zhi) / 2.0)
  aod-text(lx.at(0) - 0.12, lx.at(1) + 0.50, [$x$], size: 8pt, box-w: 0.6, box-h: 0.35)
  aod-text(ly.at(0) + 0.46, ly.at(1) + 0.34, [$y$], size: 8pt, box-w: 0.6, box-h: 0.35)
  aod-text(lz.at(0) + 0.52, lz.at(1), [$z$], size: 8pt, box-w: 0.6, box-h: 0.35)

  // Optional dashed chord between endpoints
  if chord and points.len() >= 2 {
    let p0 = proj(..points.at(0))
    let pe = proj(..points.at(points.len() - 1))
    aod-line(p0.at(0), p0.at(1), pe.at(0), pe.at(1), stroke: (paint: aod-pal.slate, thickness: 1.0pt, dash: "dashed"))
  }

  // Trajectory polyline and node markers
  if points.len() >= 2 {
    let p2d = points.map(pt3 => proj(..pt3))
    let segs = (curve.move((p2d.at(0).at(0) * 1cm, p2d.at(0).at(1) * 1cm)),)
    for i in range(1, p2d.len()) {
      segs.push(curve.line((p2d.at(i).at(0) * 1cm, p2d.at(i).at(1) * 1cm)))
    }
    place(top + left, curve(stroke: stroke, ..segs))
    for p in p2d {
      aod-marker(p.at(0), p.at(1), kind: "circle", r-pt: 2.3, color: marker-color)
    }
  }

  // Optional 3D annotations: (x, y, z, dx, dy, body)
  for ann in annotations {
    let p = proj(ann.at(0), ann.at(1), ann.at(2))
    aod-text(p.at(0) + ann.at(3), p.at(1) + ann.at(4), ann.at(5), size: 7.6pt, box-w: 1.8, box-h: 0.45)
  }
}
