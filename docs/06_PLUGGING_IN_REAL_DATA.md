# 06 — Plugging in real data

For Allen (SEC fundamentals) and Darren (8-K labels).

This is the 5-minute version of "how to add your real data to the Phase 1 pipeline." If it takes you longer than 5 minutes to read, tell Ivan — the doc is wrong.

---

## What you own

| Teammate | Loader | Where your code lives |
| :------- | :----- | :-------------------- |
| Allen    | `load_fundamentals(source="sec")` | `src/ews/loaders.py` — `_fundamentals_sec_impl()` (you add this) |
| Darren   | `load_labels(source="8k")` | `src/ews/labels.py` — `compute_label_b_from_8k()` (you add this) |
| Future   | `load_macros(source="fred")` | `src/ews/loaders.py` — `_macros_fred_impl()` |

Today, each of those calls raises `NotImplementedError` pointing at this doc. Your job is to replace the raise with a working function that returns a DataFrame matching the schema below.

---

## The contract

Every loader must return a `pandas.DataFrame` with exactly the columns listed in `LOADER_SCHEMAS` (in `src/ews/loaders.py`). Extra columns = error. Missing columns = error. Wrong dtypes = error.

Call `check_loader(name, df)` as the last line of your implementation. If it raises, the pipeline would have rejected your output anyway — fix before committing.

### Fundamentals (Allen)

```python
# src/ews/loaders.py

def _fundamentals_sec_impl(tickers: list[str], dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Your SEC EDGAR implementation goes here.

    Must return a DataFrame with one row per (ticker, month-end-date).
    Align fundamentals to the month-end date corresponding to the quarter
    they were available (NOT the quarter-end date — filings land weeks late).
    """
    # ... your code that hits SEC EDGAR, parses 10-Q / 10-K, computes ratios ...

    df = pd.DataFrame({
        "ticker": [...],
        "date": [...],                 # pd.Timestamp, month-end
        "leverage": [...],             # total_liab / total_assets
        "liquidity_buffer": [...],     # cash / total_assets
        "wc_ratio": [...],             # (curr_assets - curr_liab) / total_assets
        "profitability": [...],        # operating_income / total_assets
        "z_score": [...],              # Altman Z approximation; see monolith for formula
        "late_filing": [...],          # 1 if 12b-25 filed in prior 6 months, else 0
    })
    df["date"] = pd.to_datetime(df["date"])

    from .loaders import check_loader
    check_loader("fundamentals", df)
    return df
```

Then wire it into the dispatch — edit `load_fundamentals` in the same file:

```python
elif source == "sec":
    df = _fundamentals_sec_impl(tickers, dates)
```

### Labels (Darren)

Label B = 1 if the firm files 8-K Item 1.03 (bankruptcy petition) within the next 12 months.

Label A already exists. You're adding Label B ALONGSIDE it. `load_labels` currently puts `label_b = NaN` in every row. Your job is to populate that column.

```python
# src/ews/labels.py

def compute_label_b_from_8k(filings_df: pd.DataFrame, horizon_months: int = 12) -> pd.DataFrame:
    """Your 8-K implementation.

    filings_df: DataFrame of 8-K filings with [ticker, filing_date, item].
                Filter to Item 1.03 yourself.

    Returns: DataFrame with columns [ticker, date, label_b].
             date = month-end for the firm-month.
             label_b = 1 if any 1.03 filing in (date, date + horizon_months], else 0.
    """
    # ... your code ...
    return df  # merged into the Label A DataFrame by the caller
```

Then in `src/ews/loaders.py`, `load_labels` dispatch:

```python
elif source == "8k":
    from . import labels as _labels
    drawdown_labels = _labels.compute_label_a_from_prices(prices_df, horizon_months, threshold)
    # You provide filings_df from your SEC pulls — probably in load_labels kwargs
    b_labels = _labels.compute_label_b_from_8k(filings_df, horizon_months)
    df = drawdown_labels.drop(columns=["label_b"]).merge(b_labels, on=["ticker", "date"], how="left")
    # Fill missing label_b with 0 after merge (any firm-month with no 8-K = not distressed)
    df["label_b"] = df["label_b"].fillna(0).astype(int)
```

---

## How to test locally, before committing

```bash
cd <repo root>
source .venv/bin/activate

# Run the pipeline with your loader as the data source.
# Edit src/ews/run.py temporarily to change:
#   fundamentals = load_fundamentals(TICKERS, monthly_dates, source="placeholder")
# to:
#   fundamentals = load_fundamentals(TICKERS, monthly_dates, source="sec")
#
# Then run:
python src/ivan_ews_phase1.py

# Or run the smoke test to check your loader passes the schema check:
python tests/smoke_test.py
```

You should see your loader's output in `data/interim/fundamentals.csv` (or `labels.csv`). Open it in Excel. If the columns, row count, and values look wrong to a human, something is wrong. Don't let a bad loader through just because the schema check passed — the schema check doesn't verify the MATH.

---

## How to validate

`check_loader(name, df)` enforces:
- No missing columns
- No extra columns (add to `LOADER_SCHEMAS` if intentional)
- `len(df) > 0`
- `date` column is datetime64

It does NOT enforce:
- Correctness of values
- No NaN rows
- Monotone dates
- Per-firm date coverage

Those are on you. Ivan's downstream code drops rows with NaN in features; if your loader produces too many NaNs the panel shrinks silently. Log NaN counts during development.

---

## What NOT to do

- **Don't look ahead.** Any feature value at month T must not depend on data from month T+1 or later. This is the single biggest integrity rule in the pipeline. If you accidentally align a Q3 filing to its filing date (after quarter-end) — that's fine. If you align it to quarter-end (before it was filed) — that's look-ahead and breaks everything.
- **Don't drop rows silently.** If your loader drops firms or months, print a loud message naming what dropped. Ivan's `load_prices` now raises on short-history tickers (see `ALLOWED_SHORT_HISTORY` in `config.py`) — follow the same pattern.
- **Don't monkey-patch the panel schema.** If you need a new column, add it to the loader contract first (via `LOADER_SCHEMAS` in `loaders.py`) and then update `config.FEATURE_COLS` if the model should use it. Don't slip columns in through a side door.
- **Don't write to `data/processed/panel_phase1.csv`.** That file is the pipeline's output; only `run.py` writes there. Your output goes in `data/interim/<your_loader>.csv`, which `run.py` generates automatically.
- **Don't use `--break-system-packages`.** Work in the venv at `.venv/`. Add deps via `pip install` inside the venv.

---

## Where to ask

- **Schema or contract questions:** Ping Ivan. The contract lives in `src/ews/loaders.py` and is authoritative.
- **SEC / EDGAR / FRED API weirdness:** Each other. The pipeline doesn't care how you produced the data, only that the output matches the schema.
- **"My loader raises LoaderError about dropped tickers":** Either your data source is missing tickers (fix the source) or the short history is intentional (add to `ALLOWED_SHORT_HISTORY` in `config.py` with a comment explaining why, see the CHK example).
