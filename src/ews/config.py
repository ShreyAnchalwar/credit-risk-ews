"""
Central configuration for the EWS pipeline.

Single source of truth for: firms, features, time splits, thresholds, and paths.
Anyone adding a firm edits FIRMS here; anyone changing the train/val cutoff
edits TRAIN_END_YEAR here. No magic numbers elsewhere.
"""

import os

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
# Repo root: src/ews/config.py -> ../../.. -> repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(REPO_ROOT, "data")


class PATHS:
    RAW = os.path.join(DATA_DIR, "raw")
    INTERIM = os.path.join(DATA_DIR, "interim")
    PROCESSED = os.path.join(DATA_DIR, "processed")
    FIGURES = os.path.join(REPO_ROOT, "outputs", "figures")


# -----------------------------------------------------------------------------
# Firm universe — Phase 1 prototype (10 firms)
# -----------------------------------------------------------------------------
# README says "9-firm toy panel" but the code has always had 10 (CHK was added
# post-README). Reconciliation: the charts render only 9 panels because CHK's
# yfinance history post-bankruptcy is incomplete — one trajectory subplot
# stays empty. Count in code: 10. Count in charts: 9. Update README in a
# follow-up; not blocking this refactor.
FIRMS = {
    "GE":   {"name": "General Electric",     "industry": "Industrial"},
    "F":    {"name": "Ford Motor",            "industry": "Consumer"},
    "BBBY": {"name": "Bed Bath & Beyond",     "industry": "Retail"},
    "XOM":  {"name": "Exxon Mobil",           "industry": "Energy"},
    "CHK":  {"name": "Chesapeake Energy",     "industry": "Energy"},
    "INTC": {"name": "Intel",                 "industry": "Technology"},
    "SNAP": {"name": "Snap Inc",              "industry": "Technology"},
    "PFE":  {"name": "Pfizer",                "industry": "Healthcare"},
    "SPG":  {"name": "Simon Property Group",  "industry": "RealEstate"},
    "AAL":  {"name": "American Airlines",     "industry": "Airlines"},
}

TICKERS = list(FIRMS.keys())

# Tickers allowed to have < MIN_HISTORY_DAYS of data without raising LoaderError.
# Empty by default — add a ticker here only after deciding its short history
# is acceptable for this panel.
#
# CHK (Chesapeake Energy): delisted post-bankruptcy (June 2020); yfinance
# returns no data. Intentional skip — documented in 02_OUTPUTS.md as the
# reason one trajectory subplot stays empty. The baseline Phase 1 panel was
# built without CHK; the refactor preserves that behavior.
ALLOWED_SHORT_HISTORY: set[str] = {"CHK"}

# -----------------------------------------------------------------------------
# Price-download window (daily prices; used by load_prices)
# -----------------------------------------------------------------------------
PRICE_START = "2009-06-01"   # 6mo buffer before 2010 for rolling features
PRICE_END = "2025-12-31"
MIN_HISTORY_DAYS = 100       # min per-ticker history; below this -> LoaderError

# -----------------------------------------------------------------------------
# Feature set
# -----------------------------------------------------------------------------
# Column order matters: models.py adds these as a constant list; changing the
# order here would change the coefficient output order and break stdout diff.
FEATURE_COLS = [
    "leverage", "liquidity_buffer", "wc_ratio", "profitability",
    "ret_1m", "ret_3m", "ret_6m",
    "vol_3m", "vol_6m", "drawdown_12m",
    "late_filing",
    "vix", "term_spread", "credit_spread",
]
LABEL_COL = "label_a"

# -----------------------------------------------------------------------------
# Time split
# -----------------------------------------------------------------------------
TRAIN_END_YEAR = 2020    # train <= 2020
VAL_END_YEAR = 2023      # val 2021-2023; test 2024+
PANEL_START_YEAR = 2010  # drop anything before this in panel assembly

# -----------------------------------------------------------------------------
# Label A definition (forward drawdown)
# -----------------------------------------------------------------------------
LABEL_A_THRESHOLD = -0.40         # 40% peak-to-trough drawdown
LABEL_A_HORIZON_MONTHS = 12       # over the next 12 months

# -----------------------------------------------------------------------------
# Evaluation thresholds
# -----------------------------------------------------------------------------
TOP_K_FRACTION = 0.10             # decile chart / top-K lift
LEAD_TIME_THRESHOLD = 0.3         # prob above this = "flagged"
