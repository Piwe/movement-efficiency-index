"""Phase 1 data audit: sample sizes, drills, linkage and outcome coverage."""
import sys

import pandas as pd

from src.paths import RAW

pd.set_option("display.width", 200, "display.max_rows", 200, "display.max_columns", 50)


def section(title):
    print(f"\n{'=' * 8} {title} {'=' * 8}")


results = pd.read_csv(RAW / "combine_results.csv")
players = pd.read_csv(RAW / "players.csv")
career = pd.read_csv(RAW / "player_career_successes.csv")
tracking = pd.read_csv(RAW / "combine_tracking.csv")

section("combine_results: players by position x draft year")
print(pd.crosstab(results.combine_position, results.draft_year, margins=True))
section("combine_results: non-null share of traditional metrics")
print(results.drop(columns=["draft_year", "nfl_id", "combine_position"]).notna().mean().round(2))

section("combine_tracking: shape / entity types / sampling")
print(tracking.shape, tracking.entity_type.value_counts().to_dict())
t = pd.to_datetime(tracking.time)
dt = t.groupby([tracking.event_id, tracking.nfl_id, tracking.attempt]).diff().dt.total_seconds()
print("frame interval (s):", dt.describe().round(3).to_dict())

section("combine_tracking: drill types and names")
print(tracking.groupby(["drill_type", "drill_name"]).nfl_id.nunique().rename("players").to_string())

trk = tracking[["nfl_id"]].drop_duplicates().merge(results[["nfl_id", "combine_position", "draft_year"]], how="left")
section("tracked players by position x draft year (linked to combine_results)")
print(pd.crosstab(trk.combine_position.fillna("UNLINKED"), trk.draft_year.fillna(0), margins=True))

section("linkage: tracked players -> players.csv / career")
ids = set(trk.nfl_id)
print("tracked:", len(ids), "| in players.csv:", len(ids & set(players.nfl_id)),
      "| in career:", len(ids & set(career.nfl_id)),
      "| drafted:", players[players.nfl_id.isin(ids)].draft_overall_pick.notna().sum())

section("career successes (tracked players)")
c = career[career.nfl_id.isin(ids)].merge(results[["nfl_id", "combine_position"]])
print(c.groupby("combine_position").agg(
    n=("nfl_id", "size"),
    off_snaps_med=("career_offensive_snaps", "median"),
    def_snaps_med=("career_defensive_snaps", "median"),
    starts_med=("career_games_started", "median"),
    pro_bowls=("pro_bowl_original_ballot", "sum"),
    all_pro=("ap_all_pro_1st_team", "sum")))

section("player_play: columns and non-null share")
pp = pd.read_csv(RAW / "player_play.csv", low_memory=False)
print(pp.shape)
print(pp.notna().mean().round(3).to_string())
section("player_play: lined_up_position counts")
print(pp.lined_up_position.value_counts().to_string())
print("tracked players appearing in player_play:", pp.nfl_id.isin(ids).groupby(pp.nfl_id).first().sum())

if "--peek" in sys.argv:
    section("player_play sample values (object columns)")
    for col in pp.select_dtypes("object").columns:
        if col != "play_description":
            print(col, "->", pp[col].dropna().unique()[:8].tolist())
