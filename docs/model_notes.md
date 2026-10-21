# Model Results (Phase 4)

Code: `src/models.py`. Build: `PYTHONPATH=$PWD .venv/bin/python -P -m src.models --perms 200` (~12 min).
Outputs: `data/processed/model_results.csv` (models, bootstrap CIs, permutation p),
`data/processed/component_assoc.csv` (single-feature Spearman, raw and partial on draft slot).

## Setup

- Ridge regression (median imputation, standardisation, internal α search), fit separately per
  position and outcome.
- **Leave-one-draft-class-out CV** (train on two Combine classes, predict the third).
- Out-of-sample R² with 1,000-sample bootstrap 95% CI; OOS Spearman ρ of predictions;
  permutation p (200 shuffles of the outcome within draft class).
- Feature sets: M0 draft slot (log pick + undrafted flag); M1 traditional (40, 10-yd split,
  vertical, broad jump, height, weight); M2 tracking (five MEI components, learned weights);
  M2b MEI with the writeup's fixed weights; M3 hybrid; each also "+ draft".
- Minimum plays: 50 (WR/TE/DL), 100 (OL pass-block snaps), 15 (DB man-coverage throws).

## Headline results (OOS Spearman ρ of predictions; permutation p)

| Outcome | n | M0 draft | M1 traditional | M2 tracking | M2b fixed MEI | M3 hybrid |
|---|---|---|---|---|---|---|
| DL get-off | 82 | 0.10 | **0.71** (p .005) | **0.66** (p .005) | 0.36 (p .08) | **0.75** |
| DL pressure rate | 79 | 0.15 | 0.44 (p .005) | **0.55** (p .005) | 0.27 (p .88) | 0.48 |
| DL sack rate | 79 | −0.27 | 0.28 (p .005) | 0.22 (p .01) | 0.04 | 0.28 |
| DB closing speed | 66 | −0.04 | 0.28 (p .03) | −0.01 (p .77) | **0.31** (p .025) | 0.29 |
| WR separation | 69 | −0.04 | **0.46** (p .005) | −0.10 (p .71) | −0.10 | 0.39 |
| OL peak pressure prob. | 66 | −0.10 | −0.07 | −0.26 | −0.18 | −0.35 |
| TE separation / YPRR | 22–23 | — | negative | negative | negative | negative |

OOS R² (95% CI): DL get-off M1 0.48 [0.33, 0.59], M2 0.40 [0.24, 0.52], M3 0.52 [0.37, 0.63].
DL pressure rate M2 0.15 [0.02, 0.24] vs. M1 0.04 [−0.29, 0.16].

## Added value

- **Tracking beyond draft slot (M2 + draft − M0):** DL get-off +0.41 [0.28, 0.55];
  DL pressure rate +0.16 [0.02, 0.43]; DL sack rate +0.16 [0.06, 0.39]. Not significant elsewhere.
- **Hybrid beyond traditional (M3 − M1):** DL get-off +0.04 [−0.01, 0.10]. Not significant
  anywhere, so tracking mostly **re-measures** what the stopwatch captures, but for everyone
  (82 DL with tracking vs. 66 with an official 40).
- **Playing time and availability** are explained by draft slot (R² 0.43–0.63 for snaps);
  Combine metrics add nothing once draft slot is known.

## MEI weights: a priori vs. learned (normalised |coef| sum = 1; + = better outcome)

| Outcome | Accel | Decel | COD | Smoothness | Recovery |
|---|---|---|---|---|---|
| Writeup (a priori) | 0.25 | 0.20 | 0.25 | 0.15 | 0.15 |
| DL get-off | 0.47 | 0.14 | −0.05 | **−0.28** | 0.06 |
| DL pressure rate | 0.35 | 0.12 | 0.03 | **−0.28** | 0.22 |
| DL sack rate | 0.39 | 0.18 | −0.05 | **−0.33** | 0.05 |
| DB closing speed | 0.18 | 0.27 | 0.08 | 0.18 | 0.29 |

Smoothness has the **wrong sign** for DL: smoother athletes get off slower and pressure less
(partial ρ with pressure rate −0.53, q < 0.001). Explosive movement is variable movement.

## Writeup hypotheses so far

| Hypothesis | Result |
|---|---|
| Hybrid beats traditional | Not supported (no significant ΔR²); tracking ≈ stopwatch for DL |
| Tracking metrics predict NFL performance | **Supported for DL** (get-off, pressure, sacks); DB closing speed via MEI; not WR/TE/OL |
| Finding 1: acceleration > top speed | Not supported for DL (partial ρ get-off: accel −0.62, top speed −0.66) |
| Finding 2: deceleration → WR separation | Not supported (partial ρ −0.10) |
| Finding 3: asymmetry → availability | Not supported (all |partial ρ| ≤ 0.14, p ≥ 0.13) |
| Finding 4: position drills carry hidden value | Partly: drill-based tracking covers every player and matches stopwatch signal for DL |

Multiple testing: 294 single-feature tests; 31 survive Benjamini-Hochberg q < 0.10, 29 of them
DL or WR availability, all involving speed/explosiveness.
