# 01 — Inputs

What the pipeline consumes. If you are adding a new data source, your work lands here.

## The shape of every input

Every raw input eventually becomes one or more columns in a **firm-month panel**: a table where each row is one firm observed in one month, and each column is a feature describing that firm at that moment. The panel's row count is `n_firms × n_months`. For Phase 1: 9 firms × ~176 months = 1,490 rows after cleaning. For Phase 2: 60–80 firms × 180 months ≈ 14,000 rows.

## Four input families

### 1. Firm accounting data (SEC EDGAR)

**What it is.** Quarterly and annual financial statements filed with the US Securities and Exchange Commission — balance sheets, income statements, cash-flow statements.

**Source.** SEC EDGAR REST APIs, free, public.
- Submissions history: `https://data.sec.gov/submissions/CIK{##########}.json`
- Extracted XBRL company facts: `https://data.sec.gov/api/xbrl/companyfacts/CIK{##########}.json`
- SEC rate limit: 10 requests/second. Identify yourself with a user-agent header.

**What we pull.**

| Raw field | Used for |
| :--- | :--- |
| Total assets | Denominator of every ratio |
| Total liabilities | Leverage |
| Cash and equivalents | Liquidity buffer |
| Current assets / current liabilities | Working-capital ratio |
| Operating income | Profitability |
| Filing date | No-look-ahead alignment + late-filing flag (Form 12b-25) |
| 8-K Item 1.03 filings | Label B — bankruptcy/receivership ground truth |
| SIC code | Industry classification, fixed effects, filter financials out |

**Phase 1 status.** Placeholder fundamentals hard-coded in `src/ivan_ews_phase1.py` (`generate_placeholder_fundamentals`). These are per-firm constants with small noise — they do not reflect real filings. Replace in Phase 2.

**Owner.** Allen (Yu Yuk Lam).

### 2. Equity market data (yfinance)

**What it is.** Daily stock prices for each firm, adjusted for splits and dividends.

**Source.** `yfinance` Python library, free, scrapes Yahoo Finance. Not an official API — rate-limit gracefully and cache.

**What we pull.** For each ticker, daily close prices from mid-2009 (to build rolling features back to 2010) through the present. We resample to month-end.

**What we compute from it.**

| Derived feature | Description |
| :--- | :--- |
| ret_1m, ret_3m, ret_6m | Cumulative returns over 1/3/6 months |
| vol_3m, vol_6m | Realized volatility, annualized |
| drawdown_12m | Peak-to-trough drawdown over past 12 months |
| forward_max_drawdown | Peak-to-trough drawdown over **next** 12 months (used to build Label A — not a model feature) |

**Phase 1 status.** Working. One known issue: CHK (Chesapeake Energy) does not resolve through yfinance post-bankruptcy and is silently dropped. Workaround: replace with another distressed energy firm or pull CHK prices from a different source.

**Owner.** Ivan.

### 3. Macro stress indicators (FRED + Cboe)

**What it is.** Market-wide stress signals that apply to every firm in a given month.

**Source.** FRED (Federal Reserve Bank of St. Louis) REST API, free, requires a key. VIX is sourced from FRED series `VIXCLS`; methodology is Cboe's 30-day expected volatility on S&P 500 options.

**What we pull.**

| Series | FRED code | Description |
| :--- | :--- | :--- |
| VIX | VIXCLS | Implied 30-day volatility, S&P 500 |
| 10Y Treasury | DGS10 | Benchmark long rate |
| 2Y Treasury | DGS2 | Used to compute 10Y–2Y term spread |
| BAA corporate yield | DBAA | Used to compute credit-spread proxy (BAA minus 10Y) |

**Phase 1 status.** Synthetic. `generate_macro_data()` produces plausible-looking VIX/term-spread/credit-spread series but they are fabricated. Replace in Phase 2 with real FRED pulls.

**Owner.** TBD — likely Hui Fai or Shrey.

### 4. Filing signals (SEC)

**What it is.** Specific SEC filing events that are themselves distress signals.

**Source.** SEC EDGAR submissions API (same endpoint as #1).

**What we use.**

| Filing | What it tells you |
| :--- | :--- |
| Form 12b-25 | Firm notified late filing — signal of distress or internal controls problems. Coded as `late_filing` indicator in the month within 6 months of the filing. |
| Form 8-K Item 1.03 | Firm filed for bankruptcy or entered receivership. Used to build **Label B** (high-precision event label). |

**Phase 1 status.** `late_filing` is a stub (random 5% chance for BBBY/CHK). Label B is not implemented — Phase 1 uses Label A only.

**Owner.** Darren (per Ivan's notes — confirm with team leader).

## Labels (derived, not raw inputs, but live at the same conceptual layer)

The pipeline needs a ground-truth "did this firm actually deteriorate?" to train and evaluate against.

**Label A — market-implied deterioration (primary, Phase 1):** 1 if the firm experienced a peak-to-trough drawdown of ≥40% at any point during the next 12 months; 0 otherwise. Computed from the same yfinance prices that feed the features, but using the **forward** 12-month window. Robustness threshold checks at −30% and −50%.

**Label B — 8-K bankruptcy (secondary, Phase 2):** 1 if the firm files an 8-K Item 1.03 within the next 12 months; 0 otherwise. Higher precision, lower power (rare events).

## No-look-ahead rules

All features use information available at time `t` only. Fundamentals are aligned to **filing date**, not quarter-end, and carried forward. Market and macro series are lagged to month-end. The panel excludes the final 12 months of history because forward labels cannot be computed there.

## What to do if you are adding a new data source

1. Add the source to the appropriate family above in `01_INPUTS.md`.
2. Document the endpoint, rate limit, and caching strategy.
3. Implement a function in `src/` that returns a dataframe keyed by `(ticker, date)` or `(date,)` for macro-only series.
4. Merge into the main panel in `build_panel()`.
5. Update `02_PIPELINE.md` feature list.
6. Run the Phase 1 pipeline and confirm the new column appears in `panel_phase1.csv`.
7. Re-run the charts in `outputs/figures/` to confirm nothing broke.
