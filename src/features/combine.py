"""Build player-level Combine movement features and the MEI.

Usage: python -P -m src.features.combine
Writes data/processed/combine_attempts.parquet, combine_cuts.parquet, combine_features.parquet.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

from src.features.kinematics import attempt_features

from src.paths import PROC as OUT, RAW

COMPONENTS = ["accel_eff", "decel_ctrl", "cod_eff", "smoothness", "recovery_acc"]
MEI_WEIGHTS = {"accel_eff": 0.25, "decel_ctrl": 0.20, "cod_eff": 0.25,
               "smoothness": 0.15, "recovery_acc": 0.15}
MIN_PLAYERS_PER_DRILL = 10
# three-cone cuts mix reversals and rounded weaves on 5-yard legs; per-cut COD there
# runs opposite to the official time even after controlling for speed (docs/feature_notes.md)
NO_CUT_SCORING = {"THREE_CONE_DRILL"}

# the same drill appears under more than one name across Combine years
DRILL_ALIASES = {
    "PASS_PRO-MIRROR_DRILL": "PASS_PRO_MIRROR_DRILL",
    "LINE": "LINE_DRILL",
    "SPEED_OUT_LEFT": "SPEED_OUT_ROUTE_LEFT",
    "OVER_THE_SHOULDER_ADJUST": "OVER_SHOULDER_ADJUST",
}


def load_tracking():
    t = pd.read_csv(RAW / "combine_tracking.csv", parse_dates=["time"])
    t = t[(t.entity_type == "PLAYER") & (t.drill_type != "SKILL_DRILLS_LB")]
    t["drill"] = t.drill_name.replace(DRILL_ALIASES)
    return t.sort_values(["nfl_id", "drill", "attempt", "time"])


def attempt_tables(t):
    attempts, cuts = [], []
    for (pid, dtype, drill, att), g in t.groupby(["nfl_id", "drill_type", "drill", "attempt"], sort=False):
        f = attempt_features(g.x.to_numpy(), g.y.to_numpy(), g.s.to_numpy())
        if f is None:
            continue
        key = dict(nfl_id=pid, drill_type=dtype, drill=drill, attempt=att)
        attempts.append({**key, "peak_speed": f.peak_speed, "accel_eff": f.accel_eff,
                         "decel_ctrl": f.decel_ctrl, "smoothness": f.smoothness, "n_cuts": len(f.cuts),
                         "cod_eff": np.median([c.cod_eff for c in f.cuts]) if f.cuts else np.nan,
                         "recovery_acc": np.median([c.recovery_acc for c in f.cuts]) if f.cuts else np.nan})
        cuts += [{**key, **vars(c)} for c in f.cuts]
    return pd.DataFrame(attempts), pd.DataFrame(cuts)


def normal_scores(s):
    """Rank-based z-scores: robust to the heavy tails of ratio metrics."""
    r = s.rank(pct=True, method="average")
    n = s.notna().sum()
    return pd.Series(norm.ppf((r * n - 0.5) / n), index=s.index)


def drill_scaled(df, cols, by="drill"):
    """Normal-score each column within drill, dropping drills with too few players."""
    keep = df.groupby(by).nfl_id.transform("nunique") >= MIN_PLAYERS_PER_DRILL
    df = df[keep].copy()
    for c in cols:
        df[c] = df.groupby(by)[c].transform(normal_scores)
    return df


def player_features(attempts, cuts, results):
    per_drill = attempts.groupby(["nfl_id", "drill_type", "drill"], as_index=False)[COMPONENTS + ["peak_speed"]].mean()
    per_drill.loc[per_drill.drill.isin(NO_CUT_SCORING), ["cod_eff", "recovery_acc"]] = np.nan
    z = drill_scaled(per_drill, COMPONENTS)
    feats = z.groupby("nfl_id")[COMPONENTS].mean()
    feats["n_drills"] = z.groupby("nfl_id").drill.nunique()

    # 40-yard dash: top speed and start quality from the best attempt
    forty = attempts[attempts.drill == "FORTY_YARD_DASH"].groupby("nfl_id").agg(
        top_speed=("peak_speed", "max"), forty_accel_eff=("accel_eff", "max"))
    feats = feats.join(forty)

    # left/right symmetry of change-of-direction efficiency
    # (reversals near 180 deg have no meaningful side, so only 35-150 deg cuts count)
    sided = cuts[cuts.turn.abs().between(35, 150)]
    c = drill_scaled(sided.assign(side=np.where(sided.turn > 0, "L", "R")), ["cod_eff"])
    side = c.pivot_table(index="nfl_id", columns="side", values="cod_eff", aggfunc="mean")
    n_side = c.pivot_table(index="nfl_id", columns="side", values="cod_eff", aggfunc="size")
    ok = (n_side.min(axis=1) >= 3)
    feats["cod_asymmetry"] = (side.L - side.R).abs().where(ok)

    feats = results[["nfl_id", "draft_year", "combine_position"]].merge(feats.reset_index(), on="nfl_id", how="left")
    # MEI: standardise components within position group, weight, re-standardise
    zpos = feats.groupby("combine_position")[COMPONENTS].transform(lambda s: (s - s.mean()) / s.std())
    mei = sum(w * zpos[c].fillna(0) for c, w in MEI_WEIGHTS.items())
    mei[zpos.isna().all(axis=1)] = np.nan
    feats["mei"] = mei.groupby(feats.combine_position).transform(lambda s: (s - s.mean()) / s.std())
    return feats


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = pd.read_csv(RAW / "combine_results.csv")
    attempts, cuts = attempt_tables(load_tracking())
    attempts.to_parquet(OUT / "combine_attempts.parquet", index=False)
    cuts.to_parquet(OUT / "combine_cuts.parquet", index=False)
    feats = player_features(attempts, cuts, results)
    feats.to_parquet(OUT / "combine_features.parquet", index=False)
    print(f"attempts={len(attempts)} cuts={len(cuts)} players={feats.mei.notna().sum()}/{len(feats)}")


if __name__ == "__main__":
    main()
