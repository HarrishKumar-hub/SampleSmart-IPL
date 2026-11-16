"""
frame.py — Build and clean the sampling frame from raw IPL data.

Member 1 owns this module.

Population unit : one batter-innings (a batter who faced ≥1 ball in innings 1 or 2).
Frame columns  : match_id, inning, batter, batting_team, runs, balls,
                  batting_position, date, season, venue, team, stratum.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# ────────────────────────────────────────────────────────────────
# Venue canonicalisation map (built empirically from the data)
# ────────────────────────────────────────────────────────────────
def _build_venue_map(venues: pd.Series) -> dict[str, str]:
    """
    Normalise venue names: strip trailing city suffixes, normalise
    punctuation, collapse duplicates.

    Returns a dict  {raw_name: canonical_name}.
    """
    mapping: dict[str, str] = {}
    canonical: dict[str, str] = {}          # key = simplified, val = first seen raw

    for v in sorted(venues.unique()):
        # 1. strip trailing ", City" or ", City Name"
        simple = re.sub(r",\s*[A-Z][A-Za-z\s]+$", "", v.strip())
        # 2. collapse dots and extra spaces
        simple = simple.replace(".", " ")
        simple = re.sub(r"\s+", " ", simple).strip()

        if simple in canonical:
            mapping[v] = canonical[simple]
        else:
            canonical[simple] = v
            mapping[v] = v          # self-map

    return mapping


def _batting_position(group: pd.DataFrame) -> pd.DataFrame:
    """
    Within one innings, assign batting_position = order in which a
    batter first appears (as striker *or* non-striker).

    The first ball's batter & non_striker are positions 1 & 2.
    Each subsequent new name increments the counter.
    """
    seen: dict[str, int] = {}
    pos = 0
    order_rows = group.sort_values(["over", "ball"])

    for _, row in order_rows.iterrows():
        for name in [row["batter"], row["non_striker"]]:
            if name not in seen:
                pos += 1
                seen[name] = pos

    return pd.DataFrame(
        {"batter": list(seen.keys()), "batting_position": list(seen.values())}
    )


def build_frame(
    deliveries_path: str = config.RAW_DELIVERIES,
    matches_path: str = config.RAW_MATCHES,
    save: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Construct the sampling frame and return (frame_df, quality_log).

    Steps
    -----
    1. Load raw CSVs.
    2. Drop super-over innings (keep inning ∈ {1, 2}).
    3. Standardise franchise names, season labels, venue names.
    4. Compute batting position per innings.
    5. Aggregate to batter-innings level.
    6. Assign strata based on batting position.
    7. Quality checks → quality_log dict.
    8. Save to parquet + CSV.
    """
    quality_log: dict = {}

    # ── 1. Load ────────────────────────────────────────────────
    deliveries = pd.read_csv(deliveries_path)
    matches    = pd.read_csv(matches_path)

    quality_log["raw_deliveries_rows"] = len(deliveries)
    quality_log["raw_matches_rows"]    = len(matches)

    # ── 2. Drop super-over innings ─────────────────────────────
    super_over_rows = deliveries[~deliveries["inning"].isin([1, 2])]
    quality_log["super_over_deliveries_dropped"] = len(super_over_rows)
    deliveries = deliveries[deliveries["inning"].isin([1, 2])].copy()

    # ── 3a. Franchise names ────────────────────────────────────
    deliveries["batting_team"]  = deliveries["batting_team"].replace(config.TEAM_MAP)
    deliveries["bowling_team"]  = deliveries["bowling_team"].replace(config.TEAM_MAP)

    for col in ["team1", "team2", "toss_winner", "winner"]:
        matches[col] = matches[col].replace(config.TEAM_MAP)

    quality_log["team_mapping"] = config.TEAM_MAP

    # ── 3b. Season labels ─────────────────────────────────────
    matches["season"] = matches["season"].astype(str).replace(config.SEASON_MAP)
    quality_log["season_mapping"] = config.SEASON_MAP

    # ── 3c. Venue names ───────────────────────────────────────
    venue_map = _build_venue_map(matches["venue"])
    matches["venue"] = matches["venue"].map(venue_map)
    quality_log["venue_mapping"] = {k: v for k, v in venue_map.items() if k != v}
    quality_log["unique_venues_after"] = matches["venue"].nunique()

    # ── 4. Merge match metadata into deliveries ───────────────
    match_info = matches[["id", "date", "season", "venue"]].rename(
        columns={"id": "match_id"}
    )
    deliveries = deliveries.merge(match_info, on="match_id", how="left")

    # ── 5. Batting position ───────────────────────────────────
    bp = (
        deliveries.groupby(["match_id", "inning"], group_keys=False)
        .apply(_batting_position)
        .reset_index(drop=True)
    )
    # The groupby-apply above returns one row per batter per innings.
    # We need (match_id, inning) back. Re-derive from deliveries:
    bp_frames = []
    for (mid, inn), grp in deliveries.groupby(["match_id", "inning"]):
        bp_one = _batting_position(grp)
        bp_one["match_id"] = mid
        bp_one["inning"]   = inn
        bp_frames.append(bp_one)
    bp = pd.concat(bp_frames, ignore_index=True)

    # ── 6. Aggregate to batter-innings ────────────────────────
    agg = (
        deliveries.groupby(["match_id", "inning", "batter"])
        .agg(
            batting_team=("batting_team", "first"),
            runs=("batsman_runs", "sum"),
            balls=("batsman_runs", "count"),   # every delivery row is one ball faced
        )
        .reset_index()
    )

    # Merge batting position
    frame = agg.merge(bp, on=["match_id", "inning", "batter"], how="left")

    # Merge match-level info
    frame = frame.merge(match_info, on="match_id", how="left")

    # team column = batting_team (for clarity downstream)
    frame["team"] = frame["batting_team"]

    # ── 7. Strata ─────────────────────────────────────────────
    frame["stratum"] = pd.cut(
        frame["batting_position"],
        bins=config.STRATA_BINS,
        labels=config.STRATA_LABELS,
        include_lowest=True,
    )

    # ── 8. Quality checks ─────────────────────────────────────
    quality_log["frame_N"] = len(frame)
    quality_log["missing_batting_position"] = int(frame["batting_position"].isna().sum())
    quality_log["missing_runs"]   = int(frame["runs"].isna().sum())
    quality_log["duplicate_rows"] = int(frame.duplicated(subset=["match_id", "inning", "batter"]).sum())
    quality_log["zero_ball_batters"] = int((frame["balls"] == 0).sum())
    quality_log["mean_runs"]  = round(float(frame["runs"].mean()), 4)
    quality_log["sd_runs_pop"] = round(float(frame["runs"].std(ddof=0)), 4)
    quality_log["sd_runs_sample"] = round(float(frame["runs"].std(ddof=1)), 4)
    quality_log["prop_30plus"]  = round(float((frame["runs"] >= 30).mean()), 4)

    # Strata summary
    strata_summary = (
        frame.groupby("stratum", observed=True)["runs"]
        .agg(["count", "mean", "std"])
        .round(2)
    )
    quality_log["strata_summary"] = strata_summary.to_dict()

    # Cluster (match) summary
    cluster_sizes = frame.groupby("match_id").size()
    quality_log["n_clusters"] = int(cluster_sizes.nunique()) if False else int(len(cluster_sizes))
    quality_log["cluster_size_mean"] = round(float(cluster_sizes.mean()), 2)
    quality_log["cluster_size_min"]  = int(cluster_sizes.min())
    quality_log["cluster_size_max"]  = int(cluster_sizes.max())

    # ── 9. Sort for systematic sampling ───────────────────────
    frame = frame.sort_values(
        ["date", "match_id", "inning", "batting_position"]
    ).reset_index(drop=True)

    # ── 10. Save ──────────────────────────────────────────────
    if save:
        Path(config.FRAME_PARQUET).parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(config.FRAME_PARQUET, index=False)
        frame.to_csv(config.FRAME_CSV, index=False)

    return frame, quality_log


def load_frame(path: str = config.FRAME_PARQUET) -> pd.DataFrame:
    """Load the pre-built frame from parquet."""
    return pd.read_parquet(path)


# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    frame, log = build_frame()

    print("=" * 60)
    print("SAMPLING FRAME — DATA QUALITY LOG")
    print("=" * 60)
    for k, v in log.items():
        if isinstance(v, dict):
            print(f"\n  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")

    print(f"\n✅ Frame saved → {config.FRAME_PARQUET}")
    print(f"✅ Frame saved → {config.FRAME_CSV}")
    print(f"\nFrame shape: {frame.shape}")
    print(frame.head(10).to_string())
