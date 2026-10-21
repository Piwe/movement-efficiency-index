# NFL Outcome Notes (Phase 3)

Code: `src/outcomes.py`. Build: `PYTHONPATH=$PWD .venv/bin/python -P -m src.outcomes` (~1.5 min;
`--skip-tracking` reuses `db_coverage_plays.parquet`). Output: `data/processed/outcomes.parquet`.

## Scope

- **Regular season only** (`games.season_type == "REG"`). Preseason and playoff plays are excluded.
- Every rate/mean has a raw value, a play count `n_*`, and an empirical-Bayes estimate `*_eb`
  shrunk toward the position-group mean (weight = τ² / (τ² + noise/n)).

## Definitions

| Outcome | Positions | Plays used | Definition |
|---|---|---|---|
| separation | WR, TE | routes with separation recorded | mean `separation_at_pass_forward` (yd) |
| yprr | WR, TE | all routes | receiving yards / route (non-targets = 0) |
| epa_per_route | WR, TE | all routes | EPA on targets / route |
| pressure_allowed_rate | OL (TE) | pass-block snaps | share with `pressure_allowed` |
| sack_allowed_rate | OL | pass-block snaps | share with `sack_allowed` |
| peak_pressure_prob | OL | pass-block snaps | mean `peak_pressure_probability_allowed` |
| pressure_rate | DL | pass-rush snaps (`sack` recorded) | share with `time_to_pressure` or a sack |
| sack_rate | DL | pass-rush snaps | share with a sack |
| get_off | DL | snaps with `player_get_off` | mean get-off time (s; lower = quicker) |
| cushion | DB | snaps with cushion | mean cushion (yd) |
| db_break_accel | DB | man coverage, pass thrown (C/I/IN) | peak acceleration in 1.5 s after `pass_forward` |
| db_closing_speed | DB | same | peak speed in 1.5 s after `pass_forward` |
| snaps_per_season, starts_per_season | all | career table | per season since draft (through 2025) |
| games_active_share | all | career table | games active / (17 × seasons), capped at 1 |

## Reliability (split-half by game, Spearman-Brown; players with ≥ 20 plays per half)

| Outcome | Players | Reliability | ρ with draft pick | Use |
|---|---|---|---|---|
| DL get-off | 78 | 0.93 | +0.24 | primary |
| DB cushion | 66 | 0.96 | +0.17 | descriptive only (scheme/alignment) |
| OL peak pressure prob. | 66 | 0.80 | +0.03 | primary |
| DB closing speed | 48 | 0.76 | −0.25 | primary |
| WR/TE separation | 90 | 0.75 | −0.04 | primary |
| DL pressure rate | 76 | 0.75 | −0.28 | primary |
| OL pressure allowed | 67 | 0.72 | +0.15 | secondary |
| DB break accel | 48 | 0.71 | +0.10 | secondary |
| WR/TE yards per route | 91 | 0.62 | −0.42 | secondary |
| DL sack rate | 76 | 0.56 | −0.38 | secondary |
| WR/TE EPA per route | 91 | 0.36 | −0.19 | dropped (noise) |
| OL sacks allowed | 67 | ≈ 0 | −0.21 | dropped (noise) |
| TE pass-block pressure | — | — | — | dropped (median 10 snaps per TE) |

Negative ρ with pick = earlier picks do better. **Separation is unrelated to draft slot
(ρ = −0.04)** and **OL peak pressure probability is too (ρ = +0.03)**: if Combine movement predicts
them, it is information teams are not already pricing in.
