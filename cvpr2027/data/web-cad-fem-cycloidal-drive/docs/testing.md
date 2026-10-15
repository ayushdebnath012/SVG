# Testing

## Ratio check

Mark input and output. Turn input 15 turns → output must turn exactly
1 turn **the opposite way**. The sketch in `electronics/nema17_test.ino`
does 15 slow input revs so you can count one output rev.

## Torque check (article method)

Clamp the housing, hang/press a scale 10 cm from the output axis:

```text
T_out = F × 0.10 m
```

Article result with a 34 mm NEMA 17 rated ~26 N·cm: ~26 N at 10 cm →
~260 N·cm at the output ≈ 10× the motor (ideal 15×, so η ≈ 66%).
Expect less on a first print; friction and bore accuracy dominate.

## Accuracy / backlash check

Command known input steps, measure output angle with a pointer/protractor.
A healthy build shows negligible backlash and repeatable positioning —
the reason cycloidals are used in robotics.

## Back-drivability

This build (unlike many worm reducers) can be back-driven by hand on the
output. Useful for compliant joints; means it will not hold position
unpowered.

## If it misbehaves

- Binds once per rev → disks not 180° apart, or a pin/roller proud.
- Growls → dry bearings / profile too tight; grease lightly, check expansions.
- Slop → profile over-compensated or pin clearance too big.
