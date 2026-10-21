# Combine Feature Notes (Phase 2)

Code: `src/features/kinematics.py` (per attempt), `src/features/combine.py` (per player).
Build: `PYTHONPATH=$PWD .venv/bin/python -P -m src.features.combine` (~25 s).
Tests: `.venv/bin/python -m pytest -q tests` (synthetic sprints, cuts and reversals).

## Signal processing

- Attempts trimmed to active movement (speed > 0.5 yd/s, ±0.2 s padding).
- Savitzky-Golay smoothing (window 0.7 s, order 2). Signed tangential acceleration is the
  derivative of smoothed speed, because the provided `a` is a non-negative magnitude.
- Heading comes from smoothed x/y velocity. Positive turn = left (counter-clockwise).

## Component definitions

| Component | Definition |
|---|---|
| Acceleration Efficiency | 0.9 × peak speed ÷ time from onset to reaching 0.9 × peak speed |
| Deceleration Control | Largest deceleration episode (a < −1 yd/s², Δv ≥ 1.5): speed lost ÷ distance used |
| Change-of-Direction Efficiency | Per cut: \|heading change\| ÷ time lost vs. running the same distance at approach speed |
| Movement Smoothness | −log RMS of acceleration around its 1.5 s trend (unnecessary variation, not the intended burst) |
| Recovery Acceleration | Speed regained ÷ time, from the cut's slowest frame to 90% of approach speed (or the next cut) |
| COD Asymmetry | \|mean left-cut COD − mean right-cut COD\| (35–150° cuts only, ≥ 3 per side) |

**Cut detection** compares mean velocity over the 0.8 s before and after each frame. Peaks
≥ 35° (at least 0.8 s apart) are cuts. This catches plant-and-reverse moves where speed passes
through zero, which an angular-velocity detector misses.

## Aggregation

1. Average attempts per player × drill.
2. Normal-score each component within each drill (rank-based; drills with ≥ 10 players).
3. A player's component = mean across their drills.
4. MEI = writeup weights on components z-scored within position group, then re-standardised.

## Validation against the stopwatch

| Check | Spearman ρ |
|---|---|
| 40-yard top speed vs. official 40 time | −0.97 |
| 40-yard Acceleration Efficiency vs. 10-yard split | −0.65 |
| Three-cone Acceleration Efficiency vs. official three-cone | −0.74 |
| Shuttle COD Efficiency vs. official shuttle | −0.51 (partial, controlling for top speed and weight: −0.26) |
| Shuttle Recovery Acceleration vs. official shuttle | −0.52 |

**Three-cone excluded from COD and recovery scoring.** Its 5-yard legs mix full reversals,
a 90° turn and a rounded weave, and per-cut COD there ran opposite to the official time even
after controlling for speed (ρ = +0.27 partial). The three-cone still contributes acceleration,
deceleration and smoothness.

## Relationship to traditional metrics (within position)

MEI correlates only weakly with the 40, 10-yard split, broad jump and weight (|ρ| ≤ 0.18), so it
carries mostly new information. Smoothness correlates with *slower* 40s (ρ = +0.26): explosive
athletes show more acceleration variation, which needs care when interpreting that component.
