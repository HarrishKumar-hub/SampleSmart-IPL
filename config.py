"""
config.py — Central configuration for the IPL Sampling Project.
All magic numbers live here. Every module imports from config.
"""

import numpy as np

# ─── Population & Sample ───────────────────────────────────────
N = 16_515                        # population size (batter-innings, verified)
n = 1_101                         # common sample size for all designs
k = 15                            # systematic interval  (N / n = 16515 / 1101 = 15)
SEED = 42                         # reproducibility seed
ALPHA = 0.05                      # significance level
Z = 1.96                          # z_{alpha/2} for 95% CI
N_SIM = 500                       # Monte Carlo replications

# ─── Strata (batting position groups) ──────────────────────────
# Batting position → stratum name
STRATA_BINS   = [0, 2, 5, 7, 11]  # (0,2] → Openers, (2,5] → Middle, etc.
STRATA_LABELS = ["Openers (1-2)", "Middle (3-5)", "Lower-Middle (6-7)", "Tail (8-11)"]

# ─── File paths ────────────────────────────────────────────────
RAW_DELIVERIES  = "data/raw/deliveries.csv"
RAW_MATCHES     = "data/raw/matches.csv"
FRAME_PARQUET   = "data/processed/frame.parquet"
FRAME_CSV       = "data/processed/frame.csv"
FIGURES_DIR     = "results/figures"
TABLES_DIR      = "results/tables"

# ─── Franchise name mapping ────────────────────────────────────
TEAM_MAP = {
    "Delhi Daredevils":              "Delhi Capitals",
    "Kings XI Punjab":               "Punjab Kings",
    "Royal Challengers Bangalore":   "Royal Challengers Bengaluru",
    "Deccan Chargers":               "Sunrisers Hyderabad",
    "Rising Pune Supergiants":       "Rising Pune Supergiant",   # normalise plural
    "Rising Pune Supergiant":        "Rising Pune Supergiant",
    "Pune Warriors":                 "Pune Warriors India",
}

# ─── Season normalisation ──────────────────────────────────────
SEASON_MAP = {
    "2007/08": "2008",
    "2009/10": "2010",
    "2020/21": "2021",           # note: IPL 2020 was played in UAE late 2020
}
# We'll reassign after checking; the actual season year is the one used in reporting.

# ─── Plotting style ───────────────────────────────────────────
PALETTE = ["#264653", "#2A9D8F", "#E9C46A", "#F4A261", "#E76F51",
           "#606C38", "#283618", "#DDA15E"]
FIG_DPI = 300
FIG_SIZE = (10, 6)

# ─── Derived ───────────────────────────────────────────────────
RNG = np.random.default_rng(SEED)
