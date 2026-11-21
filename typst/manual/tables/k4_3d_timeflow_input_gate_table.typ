// Native Typst port of manual/data/lensing/k4_3d_timeflow_input_gate_table.tex (verbatim scientific content).
#import "../preamble.typ": *

#figure(
  kind: table,
  {
  set text(size: 8.5pt)
  set par(justify: false)
  table(
    columns: (16.00fr, 32.00fr, 21.00fr, 15.00fr),
    align: (left, left, left, left),
    table.header(
      toprule,
      [Input group], [Required field], [Source status], [Gate],
      midrule,
    ),
    [3D density fields], [stellar density $rho_(star) (R,z, theta )$], [external / 3D proxy], [required],
    [3D density fields], [gas density $rho_(upright("gas")) (R,z, theta )$], [external / 3D proxy], [required],
    [velocity and flow fields], [gas and stellar velocity vector field], [IFU / H I / H$alpha$], [required],
    [velocity and flow fields], [line-of-sight flow and bobbing/slosh phase], [time / kinematic proxy], [required],
    [momentum fields], [angular momentum and radial/linear momentum], [independent kinematics], [required],
    [time-window state], [duration/cadence windows for flow transfer], [declared pre-score], [required],
    [lensing target side], [image-position bins], [quarantined target], [required],
    [lensing target side], [Einstein-radius bins and image count classes], [quarantined target], [required],
    [audit controls], [null / permutation controls], [declared pre-score], [required],
    bottomrule,
  )
},
  caption: [K4 independent 3D + time-flow input gate.],
) <tab:manual-lensing-k4-gate>
