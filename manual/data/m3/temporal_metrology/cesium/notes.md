# Cs-133: NIST-F2 apparatus-bound comparison

This record selects the historical NIST-F2 evaluation published in 2014, with particular care to distinguish its typical Table 1 budget from the August 2013 campaign. It is not a claim about the current best Cs clock or present NIST operations.

## Experimental chain

Laser-cooled Cs is launched through a state-selection region and then through the Ramsey cavity on ascent and descent. The clock pair is `(F=3,mF=0) ↔ (F=4,mF=0)`. State preparation, propagation through the C-field, two microwave interactions and state-selective optical detection are distinct operations. NIST-F2 has a two-zone detector with collected light, photodiodes and amplifiers. Its square-wave frequency servo measures the clock resonance; the related F1 primary papers detail the normalized F=4/F=3 population readout and two-sided line-centre estimator.

For AOD, the observable here is a population/fluorescence response to an applied microwave phase, then a servo-estimated frequency. It is not the same observable as continuous H-maser microwave emission. An AOD source, atomic coupling and optical readout must each be bound; a generic ideal Ramsey curve does not reproduce the specified apparatus.

The population-normalization interface can be written `p=N4/(N3+N4)` after detector/background calibration, with the servo comparing the response on opposite sides of the line. In the physical photodiode readout these N values are population estimates inferred from fluorescence signals, not automatically exact integer atom counts. Exact simulated populations still require the detector/estimator correspondence before comparison.

The microwave reference explicitly connects the two devices: a quartz oscillator is locked to a hydrogen maser, multiplied to 100 MHz, used to phase-lock a 9.200 GHz DRO and mixed with a nominal 7.368 MHz computer-controlled signal. Those printed GHz/MHz values are rounded nominal settings; subtracting them cannot recover the exact Cs defining frequency. The maser ensemble also acts as a flywheel during evaluations and interruptions.

## Source locations

- [Heavner et al. 2014, NIST-F2](https://tf.nist.gov/general/pdf/2704.pdf), §§2.1–2.4, 3.2–3.6, Table 1, §5. Web refs `turn63view0–3`, `turn64view0–3`, `turn70view3`.
- [Jefferts et al. 2002, NIST-F1](https://tf.nist.gov/general/pdf/1823.pdf), §§2.1 and 2.4: related apparatus preparation and servo method. Some state symbols are lost in web OCR, so no complete F2 preparation transcript is inferred from it.
- [Heavner et al. 2005, NIST-F1](https://tf.nist.gov/general/pdf/2035.pdf), §2.4 gives F=4/F=3 detection, §§2.5/2.9 give synthesis/control, §5.2 explicitly names the `|3,0>→|4,0>` clock transition and state selection. These are supporting architecture references, not a claim that every F1 setting equals F2.
- [BIPM second definition](https://www.bipm.org/en/si-base-units/second): the unperturbed Cs-133 frequency is assigned exactly 9,192,631,770 Hz.

## Exact-input transcription and uncertainty scope

The accompanying JSON preserves the reported numbers, inequality bounds and approximation flags. Typical F2 settings include 80 K interrogation environment, approximately 0.6 s Ramsey interval, 0.46 μK atomic temperature, approximately 250 nT C-field and about 7,500 detected atoms at low density. These are experimental settings, not exact AOD inputs already justified.

**Budget correction:** Table 1 gives a typical Type B standard uncertainty of `0.11×10^-15`. The full paper's conclusion gives **August 2013 Type A `0.44×10^-15` and Type B `0.16×10^-15`**, after changes to the microwave synthesizer and a renewed amplitude evaluation. The abstract foregrounds the typical `0.11` figure. Do not combine that earlier typical budget with the later campaign as though they were one unchanged setup.

The Table 1 spin-exchange entry `(-0.71 ± 0.24)×10^-15` is informational and excluded from the Type B sum. Its statistical contribution is included in Type A. Entries marked `<0.01` are bounds, not measured zeros or exact contributions for a reconstructed sum. The redshift/second-order Doppler item is a reported part of the experiment's reduction; it is not an AOD premise.

## What can be tested

If Cs supplies the SI scale, obtaining its assigned frequency after normalization is a calibration identity. Useful additional tests remain: preparation dependence, fringe shape/contrast, phase response, field/density perturbations, window/servo behavior and a held-out H/Cs ratio. For an independent ratio test, do not use the target H frequency to choose the AOD phase assignment or update parameters. Shared uncertain maser, calibration and transfer inputs require covariance tracking; the exact defining Cs number itself creates no covariance.

The historical paper provides settings and uncertainty evidence but not the complete time-stamped population, servo and environmental streams required for raw-data replay. No new Cs simulation or AOD hyperfine prediction was made in this source study.
