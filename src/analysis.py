"""Phase 5: learned MEI v2, transfer test, bootstrap CIs and coverage for the writeup.

Usage: PYTHONPATH=$PWD python -P -m src.analysis
Writes data/processed/analysis/*.csv.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src import models as M

OUT = M.PROC / "analysis"
N_BOOT = 2000

# primary outcome per position; "sign" orients so higher = better
PRIMARY = {"DL": ("get_off_eb", -1), "DB": ("db_closing_speed_eb", 1), "WR": ("separation_eb", 1),
           "TE": ("separation_eb", 1), "OL": ("peak_pressure_prob_eb", -1)}
COMPARE = [("DL", "get_off_eb"), ("DL", "pressure_rate_eb"), ("DL", "sack_rate_eb"),
           ("DB", "db_closing_speed_eb"), ("WR", "separation_eb"), ("OL", "peak_pressure_prob_eb")]
COMPARE_MODELS = ["M0 draft only", "M1 traditional", "M2 tracking", "M2b MEI (fixed weights)", "M3 hybrid"]


def task_frame(df, pos, outcome):
    spec = next(t for t in M.TASKS if t[0] == pos and t[1] == outcome)
    d = df[(df.combine_position == pos) & df[outcome].notna()]
    return d[d[spec[3]] >= spec[2]] if spec[3] else d


def boot_rho(y, p, rng):
    n = len(y)
    stats = [spearmanr(y[i], p[i]).statistic for i in (rng.integers(0, n, n) for _ in range(N_BOOT))]
    return np.percentile(stats, [2.5, 97.5])


def model_comparison(df, rng):
    rows = []
    for pos, outcome in COMPARE:
        d = task_frame(df, pos, outcome)
        y, g = d[outcome].to_numpy(float), d.draft_year.to_numpy()
        for name in COMPARE_MODELS:
            p = M.cv_predict(d[M.MODELS[name]].to_numpy(float), y, g)
            lo, hi = boot_rho(y, p, rng)
            rows.append(dict(position=pos, outcome=outcome, model=name, n=len(y),
                             rho=spearmanr(y, p).statistic, lo=lo, hi=hi))
    return pd.DataFrame(rows)


def learned_weights(df):
    """MEI v2 weights: ridge on the five components, per position, primary outcome, full data."""
    rows = []
    for pos, (outcome, sign) in PRIMARY.items():
        d = task_frame(df, pos, outcome)
        m = M.model().fit(d[M.TRACKING].to_numpy(float), d[outcome].to_numpy(float))
        coef = sign * m[-1].coef_
        rows += [dict(position=pos, outcome=outcome, component=c, weight=w / np.abs(coef).sum())
                 for c, w in zip(M.TRACKING, coef)]
    return pd.DataFrame(rows)


def transfer(df, rng):
    """Train the DL index on get-off in two draft classes; score the third on pass-rush outcomes."""
    dl = df[df.combine_position == "DL"].copy()
    train_rows = task_frame(df, "DL", "get_off_eb").nfl_id
    dl["index"] = np.nan
    for year in dl.draft_year.unique():
        tr = dl[dl.nfl_id.isin(train_rows) & (dl.draft_year != year)]
        m = M.model().fit(tr[M.TRACKING].to_numpy(float), -tr.get_off_eb.to_numpy(float))
        te = dl.draft_year == year
        dl.loc[te, "index"] = m.predict(dl.loc[te, M.TRACKING].to_numpy(float))
    rows = []
    for outcome in ["get_off_eb", "pressure_rate_eb", "sack_rate_eb", "snaps_per_season"]:
        d = task_frame(dl.assign(combine_position="DL"), "DL", outcome)
        y, x = d[outcome].to_numpy(float), d["index"].to_numpy(float)
        lo, hi = boot_rho(y, x, rng)
        resid = lambda v: v - np.polyval(np.polyfit(d.log_pick, v, 1), d.log_pick)
        rows.append(dict(outcome=outcome, n=len(y), rho=spearmanr(x, y).statistic, lo=lo, hi=hi,
                         partial_rho_pick=spearmanr(resid(pd.Series(x).rank().to_numpy()),
                                                    resid(pd.Series(y).rank().to_numpy())).statistic))
    dl[["nfl_id", "draft_year", "index", "accel_eff", "smoothness", "get_off_eb", "pressure_rate_eb",
        "sack_rate_eb", "n_get_off", "n_pressure_rate", "forty", "draft_overall_pick"]].to_csv(OUT / "dl_players.csv", index=False)
    return pd.DataFrame(rows)


def coverage(df):
    cols = {"Official 40-yard dash": "forty", "Official 10-yd split": "ten_yd_split", "Official vertical": "vertical",
            "Official three-cone": "three_cone", "Official short shuttle": "short_shuttle",
            "Tracking: acceleration": "accel_eff", "Tracking: change of direction": "cod_eff"}
    trad = pd.read_csv(M.RAW / "combine_results.csv")[["nfl_id", "three_cone", "short_shuttle"]]
    d = df.merge(trad, on="nfl_id")
    return pd.DataFrame([dict(metric=k, share=d[v].notna().mean(), n=int(d[v].notna().sum())) for k, v in cols.items()])


def validation():
    """Tracked drill metrics vs. the official stopwatch (Spearman)."""
    a = pd.read_parquet(M.PROC / "combine_attempts.parquet")
    res = pd.read_csv(M.RAW / "combine_results.csv").set_index("nfl_id")
    best = lambda drill, col, how: getattr(a[a.drill == drill].groupby("nfl_id")[col], how)()
    checks = [("Tracked 40 top speed vs. official 40", best("FORTY_YARD_DASH", "peak_speed", "max"), "forty"),
              ("40 acceleration efficiency vs. 10-yard split", best("FORTY_YARD_DASH", "accel_eff", "max"), "ten_yd_split"),
              ("Three-cone acceleration efficiency vs. three-cone", best("THREE_CONE_DRILL", "accel_eff", "mean"), "three_cone"),
              ("Shuttle COD efficiency vs. shuttle", best("SHORT_SHUTTLE", "cod_eff", "mean"), "short_shuttle")]
    rows = []
    for name, x, col in checks:
        d = pd.concat([x.rename("x"), res[col]], axis=1).dropna()
        rows.append(dict(check=name, n=len(d), rho=spearmanr(d.x, d[col]).statistic))
    return pd.DataFrame(rows)


def reliability():
    """Split-half (odd/even game) reliability of each outcome, Spearman-Brown corrected."""
    from src import outcomes as O
    pp = O.load_plays()
    routes = pp[pp.combine_position.isin(["WR", "TE"]) & pp.route_ran.notna()].copy()
    routes["rec_yards"] = routes.rec_yards.where(routes.target, 0).fillna(0)
    routes["epa_route"] = routes.expected_points_added.where(routes.target, 0)
    pb = pp[(pp.combine_position == "OL") & pp.pressure_allowed.notna()].astype({"pressure_allowed": float, "sack_allowed": float})
    pr = pp[(pp.combine_position == "DL") & pp.sack.notna()].copy()
    pr["sack"] = pr.sack.astype(float)
    pr["pressure"] = (pr.time_to_pressure.notna() | (pr.sack > 0)).astype(float)
    cov = pd.read_parquet(M.PROC / "db_coverage_plays.parquet")
    specs = [("WR/TE separation", routes.dropna(subset=["separation_at_pass_forward"]), "separation_at_pass_forward"),
             ("WR/TE yards per route", routes, "rec_yards"), ("WR/TE EPA per route", routes, "epa_route"),
             ("OL pressure allowed", pb, "pressure_allowed"), ("OL sacks allowed", pb, "sack_allowed"),
             ("OL peak pressure prob.", pb.dropna(subset=["peak_pressure_probability_allowed"]), "peak_pressure_probability_allowed"),
             ("DL pressure rate", pr, "pressure"), ("DL sack rate", pr, "sack"),
             ("DL get-off", pp[(pp.combine_position == "DL") & pp.player_get_off.notna()], "player_get_off"),
             ("DB cushion", pp[(pp.combine_position == "DB") & pp.cushion.notna()], "cushion"),
             ("DB break accel", cov, "break_accel"), ("DB closing speed", cov, "closing_speed")]
    rows = []
    for name, d, v in specs:
        half = d.game_id.rank(method="dense") % 2
        h = d.groupby(["nfl_id", half])[v].agg(["mean", "size"]).unstack()
        h = h[(h["size"] >= 20).all(axis=1)]
        r = np.corrcoef(h["mean"][0], h["mean"][1])[0, 1]
        rows.append(dict(outcome=name, players=len(h), split_half_r=r, reliability=2 * r / (1 + r)))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(M.SEED)
    df = M.load()
    for name, table in [("validation", validation()), ("reliability", reliability()),
                        ("model_comparison", model_comparison(df, rng)), ("learned_weights", learned_weights(df)),
                        ("transfer", transfer(df, rng)), ("coverage", coverage(df))]:
        table.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n== {name}\n{table.round(3).to_string(index=False)}")


if __name__ == "__main__":
    main()
