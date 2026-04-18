"""
Data loaders — the team-facing API.

This file defines the contract Allen (SEC fundamentals) and Darren (8-K labels)
build against. Each public loader takes a set of inputs, dispatches by
`source=` kwarg, validates output shape via `check_loader`, and returns a
long-format DataFrame.

Loader failure policy: any unexpected exception inside a loader propagates
up and halts the pipeline. Silent fallback from a real-data source to a
placeholder is explicitly prohibited — see `run.py` three-tier policy block.

To add a new source (e.g., Bloomberg prices): add a branch to the dispatch
`if`/`elif` in the public `load_*` function, implement the private
`_<name>_<source>_impl` function, and append to LOADER_SCHEMAS if the output
schema differs. Call `check_loader()` at the bottom of every implementation.
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from .config import (
    ALLOWED_SHORT_HISTORY,
    FIRMS,
    MIN_HISTORY_DAYS,
    PATHS,
    PRICE_END,
    PRICE_START,
)


# =============================================================================
# Errors
# =============================================================================

class LoaderError(RuntimeError):
    """Raised by any loader when its output cannot satisfy the pipeline contract."""


# =============================================================================
# Schema registry + validator
# =============================================================================

LOADER_SCHEMAS: dict[str, set[str]] = {
    "prices":          {"ticker", "date", "close", "adj_close"},
    "market_features": {"ticker", "date", "ret_1m", "ret_3m", "ret_6m",
                        "vol_3m", "vol_6m", "drawdown_12m"},
    "fundamentals":    {"ticker", "date", "leverage", "liquidity_buffer",
                        "wc_ratio", "profitability", "z_score", "late_filing"},
    "macros":          {"date", "vix", "term_spread", "credit_spread"},
    "labels":          {"ticker", "date", "label_a", "forward_max_drawdown", "label_b"},
}


def check_loader(name: str, df: pd.DataFrame) -> None:
    """
    Validate that `df` satisfies the contract for loader `name`.

    Raises AssertionError with a specific message for any violation. Allen
    and Darren should call this as the last line of their loader, before
    returning, to confirm the pipeline will accept their output.
    """
    if name not in LOADER_SCHEMAS:
        raise AssertionError(
            f"Unknown loader name '{name}'. "
            f"Known: {sorted(LOADER_SCHEMAS)}. "
            f"If you're adding a new loader, register its schema in LOADER_SCHEMAS."
        )
    expected = LOADER_SCHEMAS[name]
    actual = set(df.columns)
    missing = expected - actual
    extra = actual - expected
    assert not missing, f"{name} loader missing columns: {sorted(missing)}"
    assert not extra, (
        f"{name} loader has unexpected columns: {sorted(extra)}. "
        f"Add them to LOADER_SCHEMAS if intentional, or drop them before returning."
    )
    assert len(df) > 0, f"{name} loader returned 0 rows"
    if "date" in expected:
        assert pd.api.types.is_datetime64_any_dtype(df["date"]), (
            f"{name}.date must be datetime64; got {df['date'].dtype}"
        )


# =============================================================================
# load_prices
# =============================================================================

def load_prices(
    tickers: list[str],
    start: str = PRICE_START,
    end: str = PRICE_END,
    source: str = "yfinance",
) -> pd.DataFrame:
    """
    Returns raw daily prices in LONG format. No returns, no features —
    derived market math lives in features.py.

    Columns: [ticker, date, close, adj_close].
    One row per (ticker, trading-day) pair.

    source='yfinance' is the only implementation today; kept as a kwarg for
    uniformity with other loaders and to leave room for future sources
    (e.g., source='bloomberg').
    """
    if source == "yfinance":
        df = _prices_yfinance_impl(tickers, start, end)
    else:
        raise LoaderError(
            f"load_prices: unknown source={source!r}. "
            f"Supported: 'yfinance'."
        )
    check_loader("prices", df)
    return df


def _prices_yfinance_impl(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download daily prices from yfinance, with per-ticker disk caching
    in data/raw/yfinance_<TICKER>.csv. Raises LoaderError if any ticker has
    fewer than MIN_HISTORY_DAYS days and is not in ALLOWED_SHORT_HISTORY."""
    print("Loading daily prices (yfinance, with data/raw/ cache)...")
    print(f"  Tickers: {', '.join(tickers)}")

    os.makedirs(PATHS.RAW, exist_ok=True)

    records: list[pd.DataFrame] = []
    dropped: list[tuple[str, int]] = []

    for ticker in tickers:
        cache_path = os.path.join(PATHS.RAW, f"yfinance_{ticker}.csv")

        if os.path.exists(cache_path):
            raw = pd.read_csv(cache_path, parse_dates=["date"])
            print(f"  ✓ {ticker}: {len(raw)} days (cached)")
        else:
            try:
                data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            except Exception as e:
                print(f"  ✗ {ticker}: download failed ({e})")
                dropped.append((ticker, 0))
                continue

            if data is None or len(data) == 0:
                print(f"  ✗ {ticker}: no data returned")
                dropped.append((ticker, 0))
                continue

            # yfinance with auto_adjust=True gives adjusted Close as "Close".
            # We record both as the same value for schema simplicity; if a
            # future source differentiates raw vs adjusted, split them here.
            close = data["Close"].squeeze()
            raw = pd.DataFrame({
                "date": data.index,
                "close": close.values,
                "adj_close": close.values,
            })
            raw.to_csv(cache_path, index=False)
            print(f"  ✓ {ticker}: {len(raw)} days "
                  f"({raw['date'].min().strftime('%Y-%m-%d')} → "
                  f"{raw['date'].max().strftime('%Y-%m-%d')})")

        if len(raw) < MIN_HISTORY_DAYS:
            dropped.append((ticker, len(raw)))
            continue

        raw["ticker"] = ticker
        records.append(raw[["ticker", "date", "close", "adj_close"]])

    # Loud-drop policy: if any requested ticker fell below MIN_HISTORY_DAYS and
    # isn't explicitly allow-listed, raise. This prevents silent panel shrinkage
    # when a teammate adds a ticker with incomplete history.
    unexpected_drops = [(t, n) for (t, n) in dropped if t not in ALLOWED_SHORT_HISTORY]
    if unexpected_drops:
        details = ", ".join(f"{t} ({n} days)" for t, n in unexpected_drops)
        raise LoaderError(
            f"load_prices: {len(unexpected_drops)} ticker(s) have insufficient history "
            f"(< {MIN_HISTORY_DAYS} days): {details}. "
            f"Either (a) fix the data source, or (b) add these tickers to "
            f"ALLOWED_SHORT_HISTORY in config.py if the short history is intentional."
        )

    df = pd.concat(records, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    print(f"\nPrice matrix (long): {len(df)} rows, {df['ticker'].nunique()} tickers")
    return df


# =============================================================================
# load_fundamentals
# =============================================================================

def load_fundamentals(
    tickers: list[str],
    dates: pd.DatetimeIndex,
    source: str = "placeholder",
) -> pd.DataFrame:
    """
    Returns firm-month fundamentals in LONG format.

    Columns: [ticker, date, leverage, liquidity_buffer, wc_ratio,
              profitability, z_score, late_filing].

    source='placeholder' -> synthetic industry-typical profiles (Phase 1 default).
    source='sec'         -> Allen's real SEC EDGAR loader (not implemented yet).
    """
    if source == "placeholder":
        df = _fundamentals_placeholder_impl(tickers, dates)
    elif source == "sec":
        raise NotImplementedError(
            "load_fundamentals(source='sec') — Allen's SEC EDGAR loader is not yet "
            "wired. See docs/06_PLUGGING_IN_REAL_DATA.md for the contract your "
            "implementation must satisfy."
        )
    else:
        raise LoaderError(
            f"load_fundamentals: unknown source={source!r}. "
            f"Supported: 'placeholder', 'sec'."
        )
    check_loader("fundamentals", df)
    return df


def _fundamentals_placeholder_impl(tickers: list[str], dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Synthetic per-industry fundamentals with distress drift for BBBY/CHK.
    Deterministic: seed=42. DO NOT edit without re-baselining the panel SHA256."""
    print("\nGenerating placeholder fundamentals (replace with SEC data later)...")

    # Industry-typical financial profiles. Keep in sync with FIRMS in config.
    profiles = {
        "GE":   {"lev": 0.65, "liq": 0.08, "wc": 0.05, "prof": 0.04},
        "F":    {"lev": 0.75, "liq": 0.10, "wc": 0.02, "prof": 0.03},
        "BBBY": {"lev": 0.60, "liq": 0.05, "wc": 0.08, "prof": 0.02},
        "XOM":  {"lev": 0.45, "liq": 0.06, "wc": 0.10, "prof": 0.08},
        "CHK":  {"lev": 0.80, "liq": 0.03, "wc": -0.05, "prof": -0.02},
        "INTC": {"lev": 0.35, "liq": 0.15, "wc": 0.15, "prof": 0.10},
        "SNAP": {"lev": 0.50, "liq": 0.20, "wc": 0.10, "prof": -0.05},
        "PFE":  {"lev": 0.40, "liq": 0.12, "wc": 0.12, "prof": 0.12},
        "SPG":  {"lev": 0.70, "liq": 0.04, "wc": -0.02, "prof": 0.06},
        "AAL":  {"lev": 0.85, "liq": 0.08, "wc": -0.10, "prof": 0.02},
    }

    np.random.seed(42)  # reproducibility pin; identical panel byte output across runs
    records = []

    for ticker in tickers:
        p = profiles.get(ticker, {"lev": 0.5, "liq": 0.10, "wc": 0.05, "prof": 0.05})

        for date in dates:
            # Slow quarterly-ish drift + small noise.
            distress_drift = 0
            if ticker == "BBBY" and date.year >= 2018:
                distress_drift = (date.year - 2018) * 0.03
            if ticker == "CHK" and date.year >= 2015:
                distress_drift = (date.year - 2015) * 0.02

            leverage = np.clip(p["lev"] + distress_drift + np.random.normal(0, 0.02), 0.05, 0.99)
            liquidity = np.clip(p["liq"] - distress_drift * 0.3 + np.random.normal(0, 0.01), 0.01, 0.5)
            wc_ratio = np.clip(p["wc"] - distress_drift * 0.5 + np.random.normal(0, 0.02), -0.4, 0.4)
            profitability = np.clip(p["prof"] - distress_drift * 0.4 + np.random.normal(0, 0.015), -0.3, 0.3)

            # Altman Z-score approximation (same formula as original).
            z_score = 1.2 * wc_ratio + 1.4 * profitability + 3.3 * profitability + 0.6 * (1 - leverage) + 0.8

            records.append({
                "ticker": ticker,
                "date": date,
                "leverage": leverage,
                "liquidity_buffer": liquidity,
                "wc_ratio": wc_ratio,
                "profitability": profitability,
                "z_score": z_score,
                "late_filing": 1 if (ticker in ["BBBY", "CHK"] and np.random.random() < 0.05) else 0,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    print(f"  Placeholder fundamentals: {len(df)} firm-months")
    return df


# =============================================================================
# load_macros
# =============================================================================

def load_macros(dates: pd.DatetimeIndex, source: str = "synthetic") -> pd.DataFrame:
    """
    Returns monthly macro series.

    Columns: [date, vix, term_spread, credit_spread].

    source='synthetic' -> regime-aware approximations (Phase 1 default).
    source='fred'      -> FRED API loader (not implemented yet).
    """
    if source == "synthetic":
        df = _macros_synthetic_impl(dates)
    elif source == "fred":
        raise NotImplementedError(
            "load_macros(source='fred') — FRED API loader is not yet wired. "
            "See docs/06_PLUGGING_IN_REAL_DATA.md."
        )
    else:
        raise LoaderError(
            f"load_macros: unknown source={source!r}. "
            f"Supported: 'synthetic', 'fred'."
        )
    check_loader("macros", df)
    return df


def _macros_synthetic_impl(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Regime-aware VIX / term spread / credit spread approximations.
    Deterministic: seed=123. DO NOT edit without re-baselining."""
    print("\nGenerating macro indicators (replace with FRED data when available)...")

    np.random.seed(123)
    records = []
    for date in dates:
        y, m = date.year, date.month

        base_vix = 16
        if y == 2011 and m >= 8:  base_vix = 30   # Euro debt crisis
        if y == 2015 and m >= 8:  base_vix = 25   # China concerns
        if y == 2018 and m == 2:  base_vix = 33   # Volmageddon
        if y == 2018 and m >= 10: base_vix = 25   # Q4 selloff
        if y == 2020 and 2 <= m <= 4: base_vix = 55  # COVID crash
        if y == 2020 and 5 <= m <= 8: base_vix = 30  # COVID recovery
        if y == 2022 and m >= 1:  base_vix = 25   # Rate hikes
        if y == 2022 and m >= 6:  base_vix = 28

        vix = max(10, base_vix + np.random.normal(0, 3))

        base_spread = 1.5
        if y >= 2019 and y <= 2020: base_spread = 0.2
        if y >= 2022: base_spread = -0.5
        if y >= 2024: base_spread = 0.5
        term_spread = base_spread + np.random.normal(0, 0.2)

        base_credit = 2.0
        if y == 2020 and 2 <= m <= 5: base_credit = 4.0
        if y == 2022 and m >= 6: base_credit = 2.5
        credit_spread = max(0.5, base_credit + np.random.normal(0, 0.2))

        records.append({
            "date": date,
            "vix": vix,
            "term_spread": term_spread,
            "credit_spread": credit_spread,
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    print(f"  Macro data: {len(df)} months")
    return df


# =============================================================================
# load_labels
# =============================================================================

def load_labels(
    prices_df: pd.DataFrame,
    horizon_months: int = 12,
    threshold: float = -0.40,
    source: str = "drawdown",
) -> pd.DataFrame:
    """
    Returns (ticker, date, label_a, forward_max_drawdown, label_b).

    label_b is filled with NaN until Darren wires in 8-K Item 1.03 filings.
    Pipeline tolerates the NaN column (panel uses label_a as the prediction
    target; label_b is unused in Phase 1 models).

    source='drawdown' -> Label A from forward price drawdown (Phase 1 default).
    source='8k'       -> Darren's 8-K labels (not implemented yet).
    """
    # Local import: labels.py owns the actual derivation logic; this module
    # just handles dispatch + schema validation. Kept local to avoid a
    # circular import since labels.py doesn't need anything from loaders.py.
    from . import labels as _labels

    if source == "drawdown":
        df = _labels.compute_label_a_from_prices(prices_df, horizon_months, threshold)
    elif source == "8k":
        raise NotImplementedError(
            "load_labels(source='8k') — Darren's 8-K bankruptcy loader is not yet "
            "wired. See docs/06_PLUGGING_IN_REAL_DATA.md for Label B semantics."
        )
    else:
        raise LoaderError(
            f"load_labels: unknown source={source!r}. "
            f"Supported: 'drawdown', '8k'."
        )
    check_loader("labels", df)
    return df
