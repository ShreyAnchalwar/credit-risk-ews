# 01 — Pipeline

How the four input families (see README "Data sources") become the four output charts in `02_OUTPUTS.md`.

## High-level flow

```
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │   SEC    │   │ yfinance │   │   FRED   │   │   SEC    │
  │  EDGAR   │   │ (prices) │   │ (macro)  │   │  (8-K,   │
  │(fundam.) │   │          │   │          │   │  12b-25) │
  └─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
  ┌────────────────────────────────────────────────────────┐
  │         (1) INGEST  →  raw dataframes by firm          │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (2) FEATURE ENGINEERING (no-look-ahead, monthly)     │
  │       - rolling returns, vols, drawdowns               │
  │       - accounting ratios                              │
  │       - macro series aligned to month-end              │
  │       - filing-signal flags                            │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (3) LABEL CONSTRUCTION                               │
  │       - Label A: forward 12m drawdown ≥ 40%            │
  │       - Label B: forward 12m 8-K Item 1.03 filing      │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (4) PANEL ASSEMBLY → one row per (ticker, month)     │
  │       → data/processed/panel_phase1.csv                │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (5) TIME-BASED SPLIT                                 │
  │       train ≤ 2020 | val 2021–2023 | test 2024+        │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (6) MODEL FITTING (three interpretable regressions)  │
  │       a) Pooled logistic regression                    │
  │       b) Fixed-effects panel logit (firm dummies)      │
  │       c) Shumway-style discrete-time hazard logit      │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (7) EVALUATION                                       │
  │       AUROC · AUPRC · Brier · top-K · lead-time        │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │   (8) CHARTS + TABLES → outputs/figures/               │
  └────────────────────────────────────────────────────────┘
```

## Diagram ↔ code cross-reference

Each stage in the ASCII flow above maps 1:1 to a module in `src/ews/`. If the diagram tells you the *what*, this table tells you the *where*:

| Stage | Module | Key functions |
| :---- | :----- | :------------ |
| 1. Ingest | `src/ews/loaders.py` | `load_prices`, `load_fundamentals`, `load_macros` |
| 2. Feature engineering | `src/ews/features.py` | `build_market_features` |
| 3. Label construction | `src/ews/labels.py` | `compute_label_a_from_prices` (Label B lands here too when Darren ships) |
| 4. Panel assembly | `src/ews/panel.py` | `assemble_panel` |
| 5. Time split | `src/ews/panel.py` | `time_split` |
| 6. Models | `src/ews/models.py` | `model_pooled_logit`, `model_fe_logit`, `model_hazard_logit` |
| 7. Evaluation | `src/ews/eval.py` | `evaluate_model`, `compute_lead_time`, `ablation_analysis`, `robustness_rolling_window` |
| 8. Charts | `src/ews/viz.py` | `plot_roc_pr`, `plot_calibration`, `plot_risk_deciles`, `plot_firm_risk_trajectory` |

Everything is stitched together by `src/ews/pipeline.py`; `src/run.py` is a thin sys.path-setting wrapper so you can run `python src/run.py` from the repo root.

## Stage-by-stage

### (1) Ingest

Each data source has its own ingest function. Cache raw pulls locally — SEC and FRED rate-limit, yfinance occasionally throttles. Never re-download within a single dev session.

### (2) Feature engineering

The full feature vector is 14 columns, grouped by source.

| Group | Feature | Definition |
| :--- | :--- | :--- |
| Fundamentals | leverage | Total liabilities / total assets |
| | liquidity_buffer | Cash / total assets |
| | wc_ratio | (Current assets − current liabilities) / total assets |
| | profitability | Operating income / total assets |
| Market | ret_1m, ret_3m, ret_6m | Cumulative equity return over window |
| | vol_3m, vol_6m | Annualized realized volatility |
| | drawdown_12m | Peak-to-trough over past 12 months |
| Macro | vix | Month-end VIX |
| | term_spread | 10Y − 2Y Treasury |
| | credit_spread | BAA − 10Y Treasury |
| Filing | late_filing | 1 if 12b-25 filed in prior 6 months |

Derived but not a feature: `forward_max_drawdown` is the forward-looking value used to construct Label A. It must never be used as a model input.

### (3) Label construction

Label A is computed from the **same** price series that produces market features, but uses the forward window (t to t+12 months). The separation between "past prices used as feature" and "future prices used as label" is what makes this a valid prediction problem and not a tautology. Discipline here matters.

### (4) Panel assembly

Merge fundamentals, market features, macro series, and labels on `(ticker, date)`. Drop rows with any NA. Sort. The result is `data/processed/panel_phase1.csv`.

### (5) Time-based split

We split **by time, not by firm**. Every firm appears in every split window. This prevents a model from "cheating" by learning a firm's identity in training and recognizing it in test. Splits: train ≤ 2020, validation 2021–2023, test 2024+.

### (6) Models

Three models, same feature set, different assumptions. All are logistic regressions (linear in log-odds, exponential in probability) — interpretable, no black-box.

| Model | What it assumes | What it adds | Phase 1 scope |
| :--- | :--- | :--- | :--- |
| Pooled logit | Every firm-month is an independent observation | Simplicity, baseline | **Committed** (proposal Table 2) |
| Fixed-effects logit | Each firm has its own baseline distress rate | Controls for unobserved firm heterogeneity | **Preview** — delivered ahead of schedule toward Phase 2 |
| Hazard logit (Shumway) | Risk of first-event, conditioned on surviving to t | Proper time-to-event framing | **Preview** — delivered ahead of schedule toward Phase 2 |

All three produce a probability score between 0 and 1 for each firm-month.

**Framing note.** The proposal's Phase 1 milestone commits only the pooled logit to April 24. The fixed-effects and Shumway-style hazard models are implemented and fit in the same run as a preview — treat their metrics as provisional until the 60–80 firm panel lands in Phase 2. `run.py`'s tier-2 fallback policy means either preview model can fail to fit on the current 10-firm toy panel (e.g., the hazard logit hits a singular matrix on Phase 1 data) and the pipeline falls back to pooled predictions with a loud warning; this is the expected behavior, not a bug.

### (7) Evaluation

Five metric families map to the five promises in the proposal.

| Promise in proposal | Metric | Where it shows up |
| :--- | :--- | :--- |
| Discrimination | AUROC | `outputs/figures/phase1_roc_pr.png` (left) |
| Rare-event discrimination | AUPRC | `outputs/figures/phase1_roc_pr.png` (right) |
| Calibration | Brier + reliability curve | `outputs/figures/phase1_calibration.png` |
| Watchlist utility | Top-K capture, lift, risk deciles | `outputs/figures/phase1_deciles.png` |
| Early warning | Lead-time, visual trajectories | `outputs/figures/phase1_trajectories.png` |

### (8) Charts and tables

The pipeline terminal output also logs coefficient tables, odds ratios, and p-values for each model — these land in the console, not the chart files. Capture them into the final write-up manually (Phase 4 deliverable).

## Contracts between stages

If you change anything, respect these contracts:

- **Panel schema.** Every row keyed by `(ticker, date)` at month-end. Column names match `FEATURE_COLS` in the code.
- **Label semantics.** `label_a` is binary, 1 = event within next 12 months. `forward_max_drawdown` is the underlying continuous value, useful for debugging but not a feature.
- **No-look-ahead.** Any feature that touches data from month `t+1` or later breaks the project. This is non-negotiable.
- **Time split.** All evaluation metrics are computed on validation and test windows, never on training. Mixing them invalidates the claims.
