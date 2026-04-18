"""
Market-feature engineering.

Consumes long-format prices from `load_prices` and produces the eight derived
features the models use: 1m/3m/6m cumulative returns, 3m/6m annualized
volatility, 12m backward drawdown.

Contract:
    Input:  DataFrame with columns [ticker, date, close, adj_close] (LONG).
    Output: DataFrame with columns [ticker, date, ret_1m, ret_3m, ret_6m,
            vol_3m, vol_6m, drawdown_12m] (LONG, one row per firm-month).

Implementation note: the public contract is long-in / long-out, but internally
this function pivots to WIDE and runs the original nested-loop math from the
monolith. That preserves bit-identical output against the Phase 1 baseline
panel (SHA256 stability is the non-negotiable acceptance test). A vectorized
groupby implementation is a Phase 2 TODO — see TODOS.md TODO-2.
"""

import numpy as np
import pandas as pd

from .loaders import check_loader


def build_market_features(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly market features per firm.

    See module docstring for contract.
    """
    print("\nComputing market features from daily prices...")

    # Pivot long -> wide so we can reuse the per-ticker rolling math from the
    # original monolith without reordering arithmetic (which would drift SHA).
    wide = prices.pivot(index="date", columns="ticker", values="adj_close").sort_index()

    daily_ret = wide.pct_change()
    monthly_dates = wide.resample("ME").last().index

    records = []
    for date in monthly_dates:
        for ticker in wide.columns:
            price_series = wide[ticker].loc[:date].dropna()
            ret_series = daily_ret[ticker].loc[:date].dropna()

            if len(price_series) < 252:  # need ~1yr history for drawdown
                continue

            # Cumulative returns
            ret_1m = price_series.iloc[-1] / price_series.iloc[-min(21, len(price_series))] - 1
            ret_3m = price_series.iloc[-1] / price_series.iloc[-min(63, len(price_series))] - 1
            ret_6m = price_series.iloc[-1] / price_series.iloc[-min(126, len(price_series))] - 1

            # Annualized realized vol
            vol_3m = ret_series.iloc[-min(63, len(ret_series)):].std() * np.sqrt(252)
            vol_6m = ret_series.iloc[-min(126, len(ret_series)):].std() * np.sqrt(252)

            # 12m backward drawdown
            window_prices = price_series.iloc[-min(252, len(price_series)):]
            running_max = window_prices.cummax()
            drawdown = ((running_max - window_prices) / running_max).max()

            records.append({
                "ticker": ticker,
                "date": date,
                "ret_1m": ret_1m,
                "ret_3m": ret_3m,
                "ret_6m": ret_6m,
                "vol_3m": vol_3m,
                "vol_6m": vol_6m,
                "drawdown_12m": drawdown,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    print(f"  Market features: {len(df)} firm-months")

    check_loader("market_features", df)
    return df
