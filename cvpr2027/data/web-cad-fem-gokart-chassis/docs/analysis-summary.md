# Analysis Summary

## Objective

Evaluate dynamic behavior and fatigue vulnerability of a GKDC go-kart chassis modeled in AISI 4130 steel.

## Modal Analysis (ANSYS 2019 R1)

- First four modes are rigid-body/near-zero modes.
- First structural bending mode starts at **17.332 Hz**.
- Key structural modes in operating concern band:
  - Mode 5: 17.332 Hz
  - Mode 6: 23.767 Hz
  - Mode 7: 24.903 Hz
  - Mode 8: 35.873 Hz
  - Mode 9: 39.547 Hz

## Harmonic Response (0–50 Hz)

- Excitation: 1000 N harmonic load in Z-direction over 6 faces.
- Maximum deformation: **7.9579×10⁻⁴ m at 40 Hz**.
- Maximum equivalent stress: **37.248 MPa at 50 Hz**.

### Modal-Harmonic Correlation

The 40 Hz deformation peak tracks closely with Mode 9 (39.547 Hz), confirming resonance-driven amplification in this frequency band.

## Fatigue and Integrity

- Loading ratio: R = -1 (fully reversed)
- Fatigue strength factor: 0.65
- Loading scale factor: 1.5
- Reported minimum life at exact resonance: 10⁻³² s
- Yield safety factor using peak stress: FS ≈ 12.35

## Design Implications

1. Yield margin is high for the simulated load envelope.
2. Fatigue at resonant operation is the controlling risk mode, not gross plastic collapse.
3. Engine RPM mapping should avoid sustained excitation in the 17–40 Hz region and inspect weld-critical zones regularly.
