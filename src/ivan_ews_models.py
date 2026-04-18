"""
=============================================================================
Credit Risk Early-Warning System — Ivan's Econometrics & Evaluation Pipeline
=============================================================================
MSc Final Project: Open-Data Credit Risk EWS for US Non-Financial Firms

This script covers Ivan's full scope:
  1. Generate fake panel data (replace with real data later)
  2. Model 1: Pooled logistic regression (baseline)
  3. Model 2: Fixed-effects panel logit (industry + time controls)
  4. Model 3: Discrete-time hazard logit (survival-style)
  5. Evaluation metrics: AUROC, AUPRC, Brier, Top-K lift, Lead time
  6. Calibration & explainability: reliability curves, odds ratios, decile charts
  7. Robustness checks: threshold sensitivity, rolling windows

Usage:
  pip install pandas numpy statsmodels scikit-learn matplotlib
  python ivan_ews_models.py
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    roc_curve,
    precision_recall_curve,
)
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Output folder for charts
import os
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# =============================================================================
# SECTION 1: FAKE DATA GENERATOR
# =============================================================================
# This creates a panel dataset that looks like what your teammates will deliver.
# Structure: each row = one firm in one month
# When real data is ready, DELETE this section and load your CSV/parquet instead.

def generate_fake_panel(n_firms=80, start_year=2010, end_year=2025, seed=42):
    """
    Generate a fake firm-month panel mimicking the proposal's Table 1 variables.
    Returns a DataFrame ready for modeling.
    """
    np.random.seed(seed)

    firms = [f"FIRM_{i:03d}" for i in range(n_firms)]

    # Assign each firm to an industry (SIC-like groups)
    industries = ["Tech", "Energy", "Healthcare", "Consumer", "Industrial"]
    firm_industry = {f: np.random.choice(industries) for f in firms}

    # Monthly date range
    dates = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-31", freq="ME")

    rows = []
    for firm in firms:
        ind = firm_industry[firm]

        # Industry-specific baseline risk (some industries are riskier)
        ind_risk = {"Tech": -0.3, "Energy": 0.5, "Healthcare": -0.1,
                    "Consumer": 0.1, "Industrial": 0.2}[ind]

        for date in dates:
            # --- Fundamental ratios (from Allen) ---
            leverage = np.clip(np.random.normal(0.5 + ind_risk * 0.1, 0.15), 0.05, 0.99)
            liquidity_buffer = np.clip(np.random.normal(0.15 - ind_risk * 0.05, 0.08), 0.01, 0.5)
            wc_ratio = np.clip(np.random.normal(0.1, 0.1), -0.3, 0.5)
            profitability = np.clip(np.random.normal(0.05 - ind_risk * 0.02, 0.06), -0.2, 0.3)

            # --- Market signals (from Shrey) ---
            ret_1m = np.random.normal(0.005, 0.08)
            ret_3m = np.random.normal(0.015, 0.14)
            ret_6m = np.random.normal(0.03, 0.20)
            vol_3m = np.clip(np.random.exponential(0.25), 0.05, 1.5)
            vol_6m = np.clip(np.random.exponential(0.23), 0.05, 1.5)
            drawdown_12m = np.clip(np.random.beta(2, 5), 0, 1)  # 0 to 1 scale

            # --- Filing signals (from Darren) ---
            late_filing = 1 if np.random.random() < 0.03 else 0  # ~3% chance

            # --- Macro (shared across firms in same month) ---
            month_frac = (date.year - start_year) / (end_year - start_year)
            vix = np.clip(np.random.normal(18 + 5 * np.sin(month_frac * 6), 5), 9, 80)
            term_spread = np.random.normal(1.5, 0.8)
            credit_spread = np.clip(np.random.normal(2.0, 0.5), 0.5, 6.0)

            # --- Altman Z-score benchmark ---
            z_score = 1.2 * wc_ratio + 1.4 * profitability + 3.3 * profitability + 0.6 * (1 - leverage) + 1.0 * 0.8

            # --- Label: probability of deterioration (logistic function of risk) ---
            # Higher leverage, drawdown, vol, VIX → more likely to deteriorate
            risk_score = (
                2.0 * leverage
                - 1.5 * liquidity_buffer
                - 1.0 * profitability
                + 1.5 * drawdown_12m
                + 0.8 * vol_3m
                - 0.5 * ret_6m
                + 0.02 * vix
                + 0.5 * late_filing
                + ind_risk
                - 1.5  # intercept to keep event rate ~5-10%
            )
            prob = 1 / (1 + np.exp(-risk_score))
            label_a = 1 if np.random.random() < prob else 0

            rows.append({
                "firm_id": firm,
                "date": date,
                "industry": ind,
                "year": date.year,
                "month": date.month,
                # Fundamentals
                "leverage": leverage,
                "liquidity_buffer": liquidity_buffer,
                "wc_ratio": wc_ratio,
                "profitability": profitability,
                # Market
                "ret_1m": ret_1m,
                "ret_3m": ret_3m,
                "ret_6m": ret_6m,
                "vol_3m": vol_3m,
                "vol_6m": vol_6m,
                "drawdown_12m": drawdown_12m,
                # Filing
                "late_filing": late_filing,
                # Macro
                "vix": vix,
                "term_spread": term_spread,
                "credit_spread": credit_spread,
                # Benchmark
                "z_score": z_score,
                # Label
                "label_a": label_a,
            })

    df = pd.DataFrame(rows)
    print(f"Panel created: {len(df)} firm-months, {df['firm_id'].nunique()} firms, "
          f"{df['label_a'].mean():.1%} event rate")
    return df


# =============================================================================
# SECTION 2: DATA PREPARATION HELPERS
# =============================================================================

# These are the columns your models will use as predictors (X variables)
FEATURE_COLS = [
    "leverage", "liquidity_buffer", "wc_ratio", "profitability",  # fundamentals
    "ret_1m", "ret_3m", "ret_6m",                                 # returns
    "vol_3m", "vol_6m", "drawdown_12m",                           # volatility/drawdown
    "late_filing",                                                  # filing signal
    "vix", "term_spread", "credit_spread",                         # macro
]

LABEL_COL = "label_a"


def time_split(df, train_end=2020, val_end=2023):
    """
    Split panel by time (no future leakage).
    Train: 2010-2020, Validation: 2021-2023, Test: 2024-2025
    """
    train = df[df["year"] <= train_end].copy()
    val = df[(df["year"] > train_end) & (df["year"] <= val_end)].copy()
    test = df[df["year"] > val_end].copy()
    print(f"Train: {len(train)} rows ({train['year'].min()}-{train['year'].max()}), "
          f"Val: {len(val)} rows, Test: {len(test)} rows")
    return train, val, test


# =============================================================================
# SECTION 3: MODEL 1 — POOLED LOGISTIC REGRESSION (Baseline)
# =============================================================================
# This is the Ohlson (1980) style approach.
# All firm-months pooled together, no adjustment for industry or time.

def model_pooled_logit(train, val, test):
    """Fit pooled logistic regression and return predictions on all splits."""
    print("\n" + "="*70)
    print("MODEL 1: POOLED LOGISTIC REGRESSION (Baseline)")
    print("="*70)

    X_train = sm.add_constant(train[FEATURE_COLS])
    y_train = train[LABEL_COL]

    # Fit logit model
    model = sm.Logit(y_train, X_train).fit(disp=0)

    # Print coefficient table (odds ratios)
    print("\nCoefficient Summary (Odds Ratios):")
    print("-" * 50)
    coef_df = pd.DataFrame({
        "coef": model.params,
        "odds_ratio": np.exp(model.params),
        "std_err": model.bse,
        "p_value": model.pvalues,
    })
    print(coef_df.round(4).to_string())

    # Predict probabilities for each split
    preds = {}
    for name, split in [("train", train), ("val", val), ("test", test)]:
        X = sm.add_constant(split[FEATURE_COLS])
        preds[name] = model.predict(X)

    return model, preds


# =============================================================================
# SECTION 4: MODEL 2 — FIXED-EFFECTS PANEL LOGIT
# =============================================================================
# Adds industry dummies + year dummies to control for cross-industry
# structure and macro regimes. Uses clustered standard errors (by month).

def model_fe_logit(train, val, test):
    """Fit fixed-effects logit with industry + year dummies."""
    print("\n" + "="*70)
    print("MODEL 2: FIXED-EFFECTS PANEL LOGIT")
    print("="*70)

    # Create dummy variables for industry and year (fixed effects)
    # pd.get_dummies creates 0/1 columns for each category
    # drop_first=True avoids the "dummy variable trap" (multicollinearity)
    train_fe = train.copy()
    val_fe = val.copy()
    test_fe = test.copy()

    # Industry dummies
    ind_dummies_train = pd.get_dummies(train_fe["industry"], prefix="ind", drop_first=True, dtype=float)
    ind_dummies_val = pd.get_dummies(val_fe["industry"], prefix="ind", drop_first=True, dtype=float)
    ind_dummies_test = pd.get_dummies(test_fe["industry"], prefix="ind", drop_first=True, dtype=float)

    # Year dummies (use training years; new years in val/test get 0s)
    year_dummies_train = pd.get_dummies(train_fe["year"], prefix="yr", drop_first=True, dtype=float)
    year_dummies_val = pd.get_dummies(val_fe["year"], prefix="yr", drop_first=True, dtype=float)
    year_dummies_test = pd.get_dummies(test_fe["year"], prefix="yr", drop_first=True, dtype=float)

    # Combine features + dummies
    fe_cols_train = list(FEATURE_COLS) + list(ind_dummies_train.columns) + list(year_dummies_train.columns)

    X_train = sm.add_constant(
        pd.concat([train_fe[FEATURE_COLS].reset_index(drop=True),
                    ind_dummies_train.reset_index(drop=True),
                    year_dummies_train.reset_index(drop=True)], axis=1)
    )
    y_train = train_fe[LABEL_COL].reset_index(drop=True)

    # Fit with clustered standard errors (cluster by year-month)
    # This accounts for the fact that macro variables (VIX etc.) are shared
    # across all firms in the same month, so errors are correlated
    train_fe = train_fe.reset_index(drop=True)
    cluster_var = train_fe["year"].astype(str) + "_" + train_fe["month"].astype(str)

    model = sm.Logit(y_train, X_train).fit(
        cov_type="cluster",
        cov_kwds={"groups": cluster_var},
        disp=0
    )

    print("\nCoefficient Summary (with clustered SEs):")
    print("-" * 50)
    coef_df = pd.DataFrame({
        "coef": model.params,
        "odds_ratio": np.exp(model.params),
        "std_err": model.bse,
        "p_value": model.pvalues,
    })
    # Only show the main feature coefficients (not all year dummies)
    main_rows = [c for c in coef_df.index if not c.startswith("yr_")]
    print(coef_df.loc[main_rows].round(4).to_string())
    print(f"\n(+ {sum(1 for c in coef_df.index if c.startswith('yr_'))} year fixed-effect dummies, not shown)")

    # Predict — need to align columns for val/test
    preds = {}
    for name, split, ind_dum, yr_dum in [
        ("train", train_fe, ind_dummies_train, year_dummies_train),
        ("val", val_fe, ind_dummies_val, year_dummies_val),
        ("test", test_fe, ind_dummies_test, year_dummies_test),
    ]:
        X = pd.concat([split[FEATURE_COLS].reset_index(drop=True),
                        ind_dum.reset_index(drop=True),
                        yr_dum.reset_index(drop=True)], axis=1)
        # Align columns: val/test may have different years
        X = X.reindex(columns=X_train.columns[1:], fill_value=0)  # exclude const
        X = sm.add_constant(X)
        preds[name] = model.predict(X)

    return model, preds


# =============================================================================
# SECTION 5: MODEL 3 — DISCRETE-TIME HAZARD LOGIT
# =============================================================================
# Shumway (2001) approach: firms exit the risk set after first event.
# This models P(event at t | survived until t) using logit.

def build_hazard_panel(df):
    """
    Restructure panel for hazard modeling:
    Keep each firm only up to (and including) their first deterioration event.
    Firms that never deteriorate stay in the full panel.
    """
    hazard_rows = []
    for firm_id, group in df.groupby("firm_id"):
        group = group.sort_values("date")
        for _, row in group.iterrows():
            hazard_rows.append(row)
            if row[LABEL_COL] == 1:
                break  # firm exits after first event
    return pd.DataFrame(hazard_rows)


def model_hazard_logit(train, val, test):
    """Fit discrete-time hazard logit (firms exit after first event)."""
    print("\n" + "="*70)
    print("MODEL 3: DISCRETE-TIME HAZARD LOGIT (Shumway-style)")
    print("="*70)

    # Restructure training data: firms exit after first event
    train_haz = build_hazard_panel(train)
    print(f"Hazard panel: {len(train_haz)} rows (was {len(train)}, "
          f"firms exit after first event)")

    # Add duration variable (months since firm entered panel)
    # This helps the model learn that risk changes over time
    train_haz = train_haz.sort_values(["firm_id", "date"])
    train_haz["duration"] = train_haz.groupby("firm_id").cumcount() + 1
    train_haz["log_duration"] = np.log(train_haz["duration"])

    hazard_features = FEATURE_COLS + ["log_duration"]

    X_train = sm.add_constant(train_haz[hazard_features])
    y_train = train_haz[LABEL_COL]

    model = sm.Logit(y_train, X_train).fit(disp=0)

    print("\nCoefficient Summary:")
    print("-" * 50)
    coef_df = pd.DataFrame({
        "coef": model.params,
        "odds_ratio": np.exp(model.params),
        "std_err": model.bse,
        "p_value": model.pvalues,
    })
    print(coef_df.round(4).to_string())

    # Predict on val/test (add duration variable)
    preds = {}
    for name, split in [("train", train_haz), ("val", val), ("test", test)]:
        s = split.copy().sort_values(["firm_id", "date"])
        s["duration"] = s.groupby("firm_id").cumcount() + 1
        s["log_duration"] = np.log(s["duration"])
        X = sm.add_constant(s[hazard_features])
        preds[name] = model.predict(X)

    return model, preds


# =============================================================================
# SECTION 6: EVALUATION METRICS
# =============================================================================
# All the metrics your proposal requires, in one function.

def evaluate_model(y_true, y_pred_proba, model_name, split_name):
    """Compute all required evaluation metrics."""
    results = {}

    # AUROC: can the model rank risky firms above safe firms?
    results["auroc"] = roc_auc_score(y_true, y_pred_proba)

    # AUPRC: important because events are rare (class imbalance)
    results["auprc"] = average_precision_score(y_true, y_pred_proba)

    # Brier Score: are the predicted probabilities calibrated? (lower = better)
    results["brier"] = brier_score_loss(y_true, y_pred_proba)

    # Top-K Lift: if we flag the top 10% riskiest, what % of actual events do we catch?
    k = max(1, int(len(y_true) * 0.10))
    top_k_idx = np.argsort(y_pred_proba)[-k:]  # indices of top 10% predictions
    events_in_top_k = y_true.iloc[top_k_idx].sum()
    total_events = y_true.sum()
    results["top10_capture"] = events_in_top_k / total_events if total_events > 0 else 0
    # Lift = capture rate / baseline rate (>1 means better than random)
    results["top10_lift"] = results["top10_capture"] / 0.10

    print(f"\n--- {model_name} | {split_name} ---")
    print(f"  AUROC:          {results['auroc']:.4f}")
    print(f"  AUPRC:          {results['auprc']:.4f}")
    print(f"  Brier Score:    {results['brier']:.4f}")
    print(f"  Top-10% Capture:{results['top10_capture']:.1%} of events")
    print(f"  Top-10% Lift:   {results['top10_lift']:.2f}x")

    return results


def compute_lead_time(df, pred_proba, threshold=0.5):
    """
    For firms that eventually deteriorate, how many months before the event
    did the model first flag them as high-risk (predicted prob > threshold)?
    """
    df = df.copy()
    df["pred"] = pred_proba.values if hasattr(pred_proba, 'values') else pred_proba
    df["flagged"] = df["pred"] > threshold

    lead_times = []
    for firm_id, group in df.groupby("firm_id"):
        group = group.sort_values("date")
        events = group[group[LABEL_COL] == 1]
        if len(events) == 0:
            continue
        first_event_date = events["date"].iloc[0]
        flags_before = group[(group["flagged"]) & (group["date"] < first_event_date)]
        if len(flags_before) > 0:
            first_flag = flags_before["date"].iloc[0]
            lead_months = (first_event_date.year - first_flag.year) * 12 + \
                          (first_event_date.month - first_flag.month)
            lead_times.append(lead_months)

    if lead_times:
        print(f"\n  Lead Time (firms with early flags): "
              f"mean={np.mean(lead_times):.1f} months, "
              f"median={np.median(lead_times):.0f} months, "
              f"range=[{min(lead_times)}, {max(lead_times)}]")
    else:
        print("\n  Lead Time: no firms were flagged before their event")
    return lead_times


# =============================================================================
# SECTION 7: CALIBRATION & EXPLAINABILITY CHARTS
# =============================================================================

def plot_calibration_curve(y_true, y_pred_proba, model_name, filename):
    """
    Reliability diagram: does the model's predicted probability match reality?
    If it says 30% chance, do ~30% actually deteriorate?
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Calibration curve
    prob_true, prob_pred = calibration_curve(y_true, y_pred_proba, n_bins=10, strategy="uniform")
    ax1.plot(prob_pred, prob_true, "s-", label=model_name, color="steelblue")
    ax1.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    ax1.set_xlabel("Predicted probability")
    ax1.set_ylabel("Actual event rate")
    ax1.set_title(f"Calibration Curve — {model_name}")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Prediction distribution
    ax2.hist(y_pred_proba, bins=50, alpha=0.7, color="steelblue", edgecolor="white")
    ax2.set_xlabel("Predicted probability")
    ax2.set_ylabel("Count")
    ax2.set_title("Distribution of Predicted Probabilities")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {filename}")


def plot_roc_pr_curves(y_true, preds_dict, filename):
    """
    ROC and Precision-Recall curves comparing all models.
    preds_dict: {"Model Name": predicted_probabilities, ...}
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    colors = ["steelblue", "coral", "seagreen"]

    for (name, y_pred), color in zip(preds_dict.items(), colors):
        # ROC
        fpr, tpr, _ = roc_curve(y_true, y_pred)
        auc = roc_auc_score(y_true, y_pred)
        ax1.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=color)

        # PR curve
        prec, rec, _ = precision_recall_curve(y_true, y_pred)
        ap = average_precision_score(y_true, y_pred)
        ax2.plot(rec, prec, label=f"{name} (AP={ap:.3f})", color=color)

    ax1.plot([0, 1], [0, 1], "k--", alpha=0.5)
    ax1.set_xlabel("False Positive Rate")
    ax1.set_ylabel("True Positive Rate")
    ax1.set_title("ROC Curves — Model Comparison")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    baseline_rate = y_true.mean()
    ax2.axhline(y=baseline_rate, color="k", linestyle="--", alpha=0.5, label=f"Baseline ({baseline_rate:.2f})")
    ax2.set_xlabel("Recall")
    ax2.set_ylabel("Precision")
    ax2.set_title("Precision-Recall Curves — Model Comparison")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {filename}")


def plot_risk_deciles(y_true, y_pred_proba, model_name, filename):
    """
    Risk-decile monitoring: divide firms into 10 buckets by predicted risk,
    show actual event rate in each bucket.
    The top decile should have much higher event rates (= useful watchlist).
    """
    df = pd.DataFrame({"y": y_true.values, "pred": y_pred_proba})
    df["decile"] = pd.qcut(df["pred"], 10, labels=False, duplicates="drop") + 1

    decile_stats = df.groupby("decile").agg(
        count=("y", "count"),
        events=("y", "sum"),
        avg_pred=("pred", "mean"),
    )
    decile_stats["event_rate"] = decile_stats["events"] / decile_stats["count"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(decile_stats.index, decile_stats["event_rate"],
                  color="steelblue", edgecolor="white", alpha=0.8)
    ax.axhline(y=y_true.mean(), color="red", linestyle="--",
               label=f"Overall event rate ({y_true.mean():.1%})")
    ax.set_xlabel("Risk Decile (1=safest, 10=riskiest)")
    ax.set_ylabel("Actual Event Rate")
    ax.set_title(f"Risk-Decile Chart — {model_name}")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Add event rate labels on bars
    for bar, rate in zip(bars, decile_stats["event_rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{rate:.1%}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {filename}")


def print_marginal_effects(model, train_df, feature_names):
    """
    Marginal effects: how much does a 1-unit increase in each variable
    change the predicted probability, evaluated at the mean values.
    """
    # Build a single-row DataFrame at the training-set mean
    X_mean = sm.add_constant(train_df[feature_names]).mean().to_frame().T

    # For logit, marginal effect = beta * p(1-p) where p = predicted prob at mean
    p = float(model.predict(X_mean).iloc[0])
    betas = model.params[1:]  # skip constant
    me_values = betas * p * (1 - p)

    print("\nMarginal Effects (at sample mean):")
    print("-" * 45)
    me_df = pd.DataFrame({
        "variable": feature_names,
        "marginal_effect": [me_values[f] for f in feature_names],
    }).sort_values("marginal_effect", key=abs, ascending=False)
    for _, row in me_df.iterrows():
        direction = "+" if row["marginal_effect"] > 0 else ""
        print(f"  {row['variable']:25s} → {direction}{row['marginal_effect']:.4f} "
              f"(1-unit increase changes prob by {abs(row['marginal_effect'])*100:.2f}pp)")


# =============================================================================
# SECTION 8: ROBUSTNESS CHECKS
# =============================================================================

def robustness_rolling_window(df, window_years=5):
    """
    Rolling/expanding window validation:
    Train on years [start, T], predict year T+1, repeat.
    Shows model stability over time.
    """
    print("\n" + "="*70)
    print("ROBUSTNESS: ROLLING/EXPANDING WINDOW")
    print("="*70)

    years = sorted(df["year"].unique())
    min_train_year = years[0] + window_years  # need at least N years to train

    results = []
    for test_year in range(min_train_year, max(years) + 1):
        train_data = df[df["year"] < test_year]
        test_data = df[df["year"] == test_year]

        if len(test_data) == 0 or test_data[LABEL_COL].nunique() < 2:
            continue

        X_tr = sm.add_constant(train_data[FEATURE_COLS])
        y_tr = train_data[LABEL_COL]
        X_te = sm.add_constant(test_data[FEATURE_COLS])
        y_te = test_data[LABEL_COL]

        try:
            model = sm.Logit(y_tr, X_tr).fit(disp=0)
            preds = model.predict(X_te)
            auroc = roc_auc_score(y_te, preds)
            auprc = average_precision_score(y_te, preds)
            results.append({"test_year": test_year, "auroc": auroc, "auprc": auprc})
        except Exception as e:
            print(f"  Year {test_year}: skipped ({e})")

    results_df = pd.DataFrame(results)
    print("\nYear-by-year out-of-sample performance:")
    print(results_df.to_string(index=False))
    print(f"\nMean AUROC: {results_df['auroc'].mean():.4f} (std: {results_df['auroc'].std():.4f})")
    print(f"Mean AUPRC: {results_df['auprc'].mean():.4f} (std: {results_df['auprc'].std():.4f})")

    return results_df


def robustness_threshold_sensitivity(df, thresholds=None):
    """
    Test if model performance changes when the deterioration threshold changes.
    In the real project: re-label with -30%, -40%, -50% drawdown thresholds.
    Here with fake data: we simulate different event rates.
    """
    print("\n" + "="*70)
    print("ROBUSTNESS: THRESHOLD SENSITIVITY")
    print("="*70)
    print("(With real data, re-run with different drawdown thresholds for Label A)")
    print("(Here we simulate by adjusting the event rate)\n")

    if thresholds is None:
        thresholds = {"Lenient (-30%)": 0.15, "Base (-40%)": 0.08, "Strict (-50%)": 0.04}

    results = []
    for label, event_rate in thresholds.items():
        df_sim = df.copy()
        # Simulate different labels with different event rates
        np.random.seed(42)
        df_sim["label_sim"] = (np.random.random(len(df_sim)) < event_rate).astype(int)

        train = df_sim[df_sim["year"] <= 2020]
        test = df_sim[df_sim["year"] > 2023]

        if test["label_sim"].nunique() < 2:
            continue

        X_tr = sm.add_constant(train[FEATURE_COLS])
        X_te = sm.add_constant(test[FEATURE_COLS])

        model = sm.Logit(train["label_sim"], X_tr).fit(disp=0)
        preds = model.predict(X_te)

        auroc = roc_auc_score(test["label_sim"], preds)
        auprc = average_precision_score(test["label_sim"], preds)
        results.append({"threshold": label, "event_rate": f"{event_rate:.0%}",
                        "auroc": auroc, "auprc": auprc})

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    return results_df


# =============================================================================
# SECTION 9: ABLATION BASELINES
# =============================================================================
# Compare: accounting-only vs market-only vs combined vs Altman Z-score

def run_ablation(train, test):
    """Compare different feature subsets to show each group's contribution."""
    print("\n" + "="*70)
    print("ABLATION: FEATURE GROUP COMPARISON")
    print("="*70)

    subsets = {
        "Accounting only": ["leverage", "liquidity_buffer", "wc_ratio", "profitability"],
        "Market only": ["ret_1m", "ret_3m", "ret_6m", "vol_3m", "vol_6m", "drawdown_12m"],
        "Macro only": ["vix", "term_spread", "credit_spread"],
        "Accounting + Market": ["leverage", "liquidity_buffer", "wc_ratio", "profitability",
                                "ret_1m", "ret_3m", "ret_6m", "vol_3m", "vol_6m", "drawdown_12m"],
        "Full model": FEATURE_COLS,
        "Altman Z-score only": ["z_score"],
    }

    results = []
    for name, cols in subsets.items():
        X_tr = sm.add_constant(train[cols])
        X_te = sm.add_constant(test[cols])
        y_tr = train[LABEL_COL]
        y_te = test[LABEL_COL]

        try:
            model = sm.Logit(y_tr, X_tr).fit(disp=0)
            preds = model.predict(X_te)
            results.append({
                "Feature set": name,
                "N features": len(cols),
                "AUROC": roc_auc_score(y_te, preds),
                "AUPRC": average_precision_score(y_te, preds),
                "Brier": brier_score_loss(y_te, preds),
            })
        except Exception as e:
            print(f"  {name}: failed ({e})")

    results_df = pd.DataFrame(results)
    print("\n" + results_df.round(4).to_string(index=False))
    return results_df


# =============================================================================
# MAIN: RUN EVERYTHING
# =============================================================================

def main():
    print("=" * 70)
    print("CREDIT RISK EWS — IVAN'S ECONOMETRICS & EVALUATION PIPELINE")
    print("=" * 70)

    # --- Step 1: Generate / load data ---
    # WHEN REAL DATA IS READY: replace this with
    #   df = pd.read_csv("your_panel_data.csv", parse_dates=["date"])
    df = generate_fake_panel(n_firms=80)

    # --- Step 2: Time-based split ---
    train, val, test = time_split(df)

    # --- Step 3: Run all three models ---
    model1, preds1 = model_pooled_logit(train, val, test)
    model2, preds2 = model_fe_logit(train, val, test)
    model3, preds3 = model_hazard_logit(train, val, test)

    # --- Step 4: Evaluate all models on TEST set ---
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS (TEST SET)")
    print("=" * 70)

    for name, preds in [("Pooled Logit", preds1),
                         ("FE Logit", preds2),
                         ("Hazard Logit", preds3)]:
        evaluate_model(test[LABEL_COL], preds["test"], name, "Test")

    # Lead time (on full dataset for Pooled Logit as example)
    print("\nLead Time Analysis (Pooled Logit on test set):")
    compute_lead_time(test, preds1["test"], threshold=0.3)

    # --- Step 5: Marginal effects ---
    print_marginal_effects(model1, train, FEATURE_COLS)

    # --- Step 6: Charts ---
    print("\n" + "=" * 70)
    print("GENERATING CHARTS")
    print("=" * 70)

    # Calibration curves for each model
    plot_calibration_curve(test[LABEL_COL], preds1["test"],
                          "Pooled Logit", "chart_calibration_pooled.png")
    plot_calibration_curve(test[LABEL_COL], preds2["test"],
                          "FE Logit", "chart_calibration_fe.png")

    # ROC + PR comparison
    plot_roc_pr_curves(
        test[LABEL_COL],
        {"Pooled Logit": preds1["test"],
         "FE Logit": preds2["test"],
         "Hazard Logit": preds3["test"]},
        "chart_roc_pr_comparison.png"
    )

    # Risk decile chart
    plot_risk_deciles(test[LABEL_COL], preds1["test"],
                      "Pooled Logit", "chart_risk_deciles.png")

    # --- Step 7: Ablation ---
    run_ablation(train, test)

    # --- Step 8: Robustness ---
    robustness_rolling_window(df)
    robustness_threshold_sensitivity(df)

    print("\n" + "=" * 70)
    print("DONE! All models, metrics, and charts generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
