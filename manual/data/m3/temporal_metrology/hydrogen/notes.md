# Hydrogen apparatus and observation map

The reference is [Hellwig et al. (1970)](https://tf.nist.gov/general/pdf/13.pdf), a continuous hydrogen maser comparison. The clock transition is H¹ `(F=1,mF=0) ↔ (F=0,mF=0)`. The named apparatus, preparation limits, conditions and term provenance are recorded in `protocol.json`.

Using the nominal 5 MHz reference, the published reduction is

\[
\nu_H=284\nu_R+\nu_S+\nu_B+\Delta\nu_{UTC}+\Delta\nu_N+\Delta\nu_W+\Delta\nu_D+\Delta\nu_Z.
\]

The beam-flux-insensitive tuning condition cancels cavity pulling plus spin exchange. Experiment 1 transfers the Harvard wall calibration; experiment 2 extrapolates against inverse bulb diameter. Its corrected intercept already includes the NP3 offset and removes the wall shift. Neither correction may be applied again.

| Exact arithmetic result | Hz |
|---|---:|
| Table IV nominal receiver expression | 1420405794.3007 |
| Table IV after reference corrections | 1420405751.6877 |
| Table IV after physical corrections | 1420405751.7691 |
| Table VI | 1420405751.7667 |
| Mean | 1420405751.7679 |
| Published rounded central value | 1420405751.768 |

The published uncertainties are respectively 0.0024, 0.0018 and 0.002 Hz. Both evaluations share the cesium reference.

## What the check establishes

Exact rational calculations reproduce the published reduction. That validates arithmetic and observable bookkeeping, not an AOD resonance prediction. The experiment supplied the frequency-bearing inputs. They must not become fitted hidden inputs to a claimed independent AOD result.

The guard rejects mismatched methods or transitions, missing tuning/wall/reference evidence, duplicate corrections and arbitrary source labels. It checks a reviewed metadata binding; it does not prove that a future simulator actually realizes the apparatus. An AOD adapter still needs its own explicit source-state, coupling, emission, receiver and phase mappings.

The Table V OCR regression is exploratory: eleven accepted rows give an intercept differing by approximately 0.000102149 Hz from the published intercept, within its 0.0012 Hz uncertainty but not reproducing its last digit. Rounded rows are not original measurement data. Excluded and nonoscillating bulbs remain recorded. No claim is made to have recreated the original cavity fit, raw maser oscillation, state-selector populations or complete preparation kernel.

For cavity settings \(a,b\) and beam intensities \(1,2\), the exact interpolation operator sets \(d_a=f_{a1}-f_{a2}\), \(d_b=f_{b1}-f_{b2}\), \(t=-d_a/(d_b-d_a)\) and \(f_{\rm tuned}=(1-t)f_{a1}+tf_{b1}\). Algebra gives the same result on the second beam-intensity line. A unique crossing must lie within the measured bracket. Unit checks use dimensionless arithmetic fixtures, explicitly separate from experimental data.

Run `python check_protocol.py` or `python -O check_protocol.py`; both use explicit checks that remain active with optimization. Outputs preserve exact integer ratios; decimal displays use Decimal rather than binary floats.
