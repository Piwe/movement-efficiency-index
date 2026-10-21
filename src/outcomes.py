"""Build player-level NFL regular-season outcomes.

Usage: PYTHONPATH=$PWD python -P -m src.outcomes [--skip-tracking]
Writes data/processed/db_coverage_plays.parquet and data/processed/outcomes.parquet.
"""
import sys

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from src.paths import PROC as OUT, RAW
SEASONS = (2023, 2024, 2025)
LAST_SEASON = 2025
GAMES_PER_SEASON = 17
DT = 0.1
DB_WINDOW = 15          # frames after pass_forward used for DB reaction metrics


def load_plays():
    games = pd.read_csv(RAW / "games.csv")
    reg = games.loc[games.season_type == "REG", ["game_id", "season"]]
    pp = pd.read_csv(RAW / "player_play.csv", low_memory=False).merge(reg, on="game_id")
    res = pd.read_csv(RAW / "combine_results.csv")[["nfl_id", "combine_position"]]
    return pp.merge(res, on="nfl_id")


def shrink(df, value, n, sd=None, rate=False):
    """Empirical-Bayes shrinkage of per-player means toward the position-group mean.

    `value` is the raw per-player mean over `n` plays; `sd` is the per-play standard
    deviation column (ignored for rates, which use p(1 - p)).
    """
    out = pd.Series(np.nan, index=df.index)
    for _, g in df.groupby("combine_position"):
        g = g[g[n] > 0]
        if len(g) < 5:
            continue
        mu = np.average(g[value], weights=g[n])
        if rate:
            noise = (mu * (1 - mu)) / g[n]
        else:
            noise = (np.average(g[sd].fillna(g[sd].median()) ** 2, weights=g[n])) / g[n]
        tau2 = max(np.var(g[value]) - noise.mean(), 1e-9)
        w = tau2 / (tau2 + noise)
        out[g.index] = w * g[value] + (1 - w) * mu
    return out


def per_player(rows, value, name, rate=False):
    """Aggregate a per-play value to mean, n, sd and its shrunk estimate."""
    agg = rows.groupby(["nfl_id", "combine_position"])[value].agg(["mean", "size", "std"]).reset_index()
    agg.columns = ["nfl_id", "combine_position", name, f"n_{name}", "sd"]
    agg[f"{name}_eb"] = shrink(agg, name, f"n_{name}", "sd", rate=rate)
    return agg.drop(columns="sd")


def receiving(pp):
    routes = pp[pp.combine_position.isin(["WR", "TE"]) & pp.route_ran.notna()].copy()
    routes["rec_yards"] = routes.rec_yards.where(routes.target, 0).fillna(0)
    sep = per_player(routes.dropna(subset=["separation_at_pass_forward"]), "separation_at_pass_forward", "separation")
    yprr = per_player(routes, "rec_yards", "yprr")
    routes["epa_route"] = routes.expected_points_added.where(routes.target, 0)
    epa = per_player(routes, "epa_route", "epa_per_route")
    return [sep, yprr, epa]


def pass_block(pp):
    pb = pp[pp.combine_position.isin(["OL", "TE"]) & pp.pressure_allowed.notna()].copy()
    pb["pressure_allowed"] = pb.pressure_allowed.astype(float)
    pb["sack_allowed"] = pb.sack_allowed.astype(float)
    return [per_player(pb, "pressure_allowed", "pressure_allowed_rate", rate=True),
            per_player(pb[pb.combine_position == "OL"], "sack_allowed", "sack_allowed_rate", rate=True),
            per_player(pb[pb.combine_position == "OL"].dropna(subset=["peak_pressure_probability_allowed"]),
                       "peak_pressure_probability_allowed", "peak_pressure_prob")]


def pass_rush(pp):
    pr = pp[(pp.combine_position == "DL") & pp.sack.notna()].copy()
    pr["sack"] = pr.sack.astype(float)
    pr["pressure"] = (pr.time_to_pressure.notna() | (pr.sack > 0)).astype(float)
    get_off = pp[(pp.combine_position == "DL") & pp.player_get_off.notna()]
    return [per_player(pr, "pressure", "pressure_rate", rate=True),
            per_player(pr, "sack", "sack_rate", rate=True),
            per_player(get_off, "player_get_off", "get_off")]


def db_cushion(pp):
    db = pp[(pp.combine_position == "DB") & pp.cushion.notna()]
    return [per_player(db, "cushion", "cushion")]


def db_coverage_plays(pp):
    """Per-play DB reaction after the throw in man coverage, from game tracking."""
    man = pp[(pp.combine_position == "DB") & (pp.coverage_assignment == "MAN") & pp.pass_result.isin(["C", "I", "IN"])]
    keys = man[["game_id", "play_id", "nfl_id"]].drop_duplicates()
    want = set(map(tuple, keys.to_numpy()))
    ids = set(keys.nfl_id)
    out = []
    for season in SEASONS:
        reader = pd.read_csv(RAW / f"game_tracking_{season}.csv", usecols=["game_id", "play_id", "nfl_id", "time", "s", "event"],
                             chunksize=2_000_000)
        frames = []
        for chunk in reader:
            chunk = chunk[chunk.nfl_id.isin(ids)]
            k = list(zip(chunk.game_id, chunk.play_id, chunk.nfl_id))
            frames.append(chunk[[x in want for x in k]])
        f = pd.concat(frames).sort_values(["game_id", "play_id", "nfl_id", "time"])
        for (gid, pid, nid), g in f.groupby(["game_id", "play_id", "nfl_id"], sort=False):
            ev = g.event.to_numpy()
            throw = np.flatnonzero(ev == "pass_forward")
            if not len(throw) or throw[0] + DB_WINDOW > len(g):
                continue
            s = g.s.to_numpy()
            i0 = throw[0]
            seg = s[max(i0 - 3, 0):i0 + DB_WINDOW]
            acc = savgol_filter(seg, 5, 2, deriv=1, delta=DT)[min(i0, 3):]
            out.append(dict(game_id=gid, play_id=pid, nfl_id=nid, season=season,
                            break_accel=float(acc.max()),
                            closing_speed=float(s[i0:i0 + DB_WINDOW].max()),
                            speed_at_throw=float(s[i0])))
        print(f"season {season}: {len(out)} DB man-coverage plays so far", flush=True)
    return pd.DataFrame(out)


def db_tracking(cov):
    cov = cov.assign(combine_position="DB")
    return [per_player(cov, "break_accel", "db_break_accel"),
            per_player(cov, "closing_speed", "db_closing_speed")]


def career():
    c = pd.read_csv(RAW / "player_career_successes.csv")
    p = pd.read_csv(RAW / "players.csv")[["nfl_id", "draft_year", "draft_overall_pick"]]
    c = c.merge(p, on="nfl_id")
    seasons = LAST_SEASON - c.draft_year + 1
    c["snaps_per_season"] = (c.career_offensive_snaps + c.career_defensive_snaps) / seasons
    c["games_active_share"] = (c.career_games_active / (seasons * GAMES_PER_SEASON)).clip(upper=1)
    c["starts_per_season"] = c.career_games_started / seasons
    c["honors"] = c.ap_all_pro_1st_team + c.ap_all_pro_2nd_team + c.pro_bowl_original_ballot
    return c[["nfl_id", "draft_overall_pick", "snaps_per_season", "games_active_share", "starts_per_season", "honors"]]


def main():
    pp = load_plays()
    tables = receiving(pp) + pass_block(pp) + pass_rush(pp) + db_cushion(pp)
    cov_path = OUT / "db_coverage_plays.parquet"
    if "--skip-tracking" not in sys.argv or not cov_path.exists():
        db_coverage_plays(pp).to_parquet(cov_path, index=False)
    tables += db_tracking(pd.read_parquet(cov_path))

    res = pd.read_csv(RAW / "combine_results.csv")[["nfl_id", "draft_year", "combine_position"]]
    out = res.merge(career(), on="nfl_id", how="left")
    for t in tables:
        out = out.merge(t.drop(columns="combine_position"), on="nfl_id", how="left")
    out.to_parquet(OUT / "outcomes.parquet", index=False)
    print(out.groupby("combine_position").count().T.to_string())


if __name__ == "__main__":
    main()
