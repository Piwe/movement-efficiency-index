# Data Audit (Phase 1)

Generated from `src/audit.py` on 2026-10-21. Raw data: `data/raw/nfl-big-data-bowl-2027/`.

## Files

| File | Grain | Notes |
|---|---|---|
| `combine_results.csv` | player | 510 players; measurables, traditional drill times, NGS scores |
| `combine_tracking.csv` | frame (10 Hz) | 463k rows; player + ball; drill_type / drill_name / attempt |
| `players.csv` | player | draft year, round, overall pick (383 of 510 drafted) |
| `player_career_successes.csv` | player | snaps, games active/started, Pro Bowl, All-Pro |
| `player_play.csv` | player × play | 314k rows, 64 cols; EPA, routes, separation, pressure, get-off |
| `game_tracking_{2023,2024,2025}.csv` | frame (10 Hz) | in-game tracking for the 510 Combine players only |
| `games.csv` | game | season, week, teams |

## Sample sizes (players)

| Position | 2023 | 2024 | 2025 | Total | With NFL plays | Median plays |
|---|---|---|---|---|---|---|
| DB | 35 | 50 | 37 | 122 | 118 | 439 |
| DL | 37 | 37 | 44 | 118 | 115 | 400 |
| OL | 37 | 46 | 38 | 121 | 120 | 513 |
| TE | 12 | 13 | 17 | 42 | 38 | 185 |
| WR | 39 | 31 | 37 | 107 | 106 | 262 |

All 510 tracked players link to `combine_results`, `players` and `player_career_successes`.

## Combine tracking coverage

- 40-yard dash tracked for 418 players; short shuttle 170; three-cone 160.
- Position skill drills are tracked for nearly every player in the group (e.g. 8–15 WR routes, OL pull/mirror/wave drills, DL pass-rush/hoop/bag drills, DB backpedal/W/box drills, TE routes and block explosion).
- Traditional three-cone/shuttle times exist for only 35–39% of players, so tracking-based agility from **position drills** has far better coverage than stopwatch agility.
- Frame interval is 0.1 s; negative gaps occur between attempts and must be split on `attempt`.
- `SKILL_DRILLS_LB` has 4 players only and is out of scope.

## Outcome availability vs. writeup

| Position | Writeup outcome | Available? | Source / replacement |
|---|---|---|---|
| WR, TE | Average separation | ✅ | `separation_at_pass_forward` (88% of route rows) |
| WR, TE | EPA generated | ✅ | `expected_points_added` on targeted plays |
| WR, TE | Yards per route run | ✅ | `rec_yards` / routes (`route_ran`) |
| TE | Run block efficiency | ❌ | Replace with pass-block `pressure_allowed` (5% of TE rows) or drop |
| DB | Completion % allowed, PBUs, coverage grade | ❌ | No defender attribution (`target` true on 8 DB rows); replace with in-game movement from `game_tracking` (e.g. closing speed, break efficiency in man coverage) and `cushion` |
| DL | Pressure rate, sack rate | ✅ | `time_to_pressure` presence, `sack` |
| DL | Pass-rush win rate | ❌ | Replace with `player_get_off` (in-game first-step; 63% of DL rows) |
| OL | Pressure / sacks allowed | ✅ | `pressure_allowed`, `sack_allowed` (56% of OL rows) |
| OL | Pass block efficiency | ✅ | `peak_pressure_probability_allowed` |
| All | Injury risk (Finding 3) | ❌ | No injury data; proxy with `career_games_active` share or reframe |
| All | Draft-slot control | ✅ | `draft_overall_pick`; undrafted (127) need a flag |

## Implications for the build

1. Small samples (TE n≈38) → regularised linear models, leave-one-draft-class-out CV, bootstrap CIs.
2. In-game tracking exists for the same players, enabling a **Combine → in-game movement transfer** analysis (e.g. Combine burst vs. in-game `player_get_off`), which is a direct, non-obvious linkage.
3. Game tracking is ~2 GB CSV; convert to Parquet per season and process by player to fit 7 GB RAM.
