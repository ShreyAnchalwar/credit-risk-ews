# 04 — Usage

How someone who isn't a model-builder actually uses the output. The pipeline exists to support this workflow; if this workflow doesn't work, nothing else matters.

## Who is the user

A **credit analyst**. Their job is to monitor a portfolio of ~80 firms and flag concerning names before they deteriorate. They do not have time to read every firm's 10-K every quarter. They want a short, ranked list each month of "who should I look at?"

The EWS is **a prioritization tool for analyst attention**, not an automatic decision system.

## The monthly workflow

### Step 1 — Run the pipeline on month-end data

On the first business day of each month, the pipeline ingests the latest SEC filings, the closed prior month's prices, and the latest FRED macro values. It produces one probability score for every firm in the panel.

### Step 2 — Open the watchlist

The analyst gets a ranked table, one row per firm, sorted by predicted probability descending. The table contains:

| Column | What the analyst sees |
| :--- | :--- |
| Rank | 1 = highest risk this month |
| Firm | Ticker + name |
| Probability | 0.00–1.00 |
| Decile | 1–10 |
| Trend | Up / flat / down vs prior month |
| Top drivers | The 3 features contributing most to this score |

### Step 3 — Focus on the top decile

The risk-decile chart (`outputs/figures/phase1_deciles.png`) tells the analyst that the top 10% of scores contains roughly 3× the base rate of actual distress events. That is the tool's operational contract: **if you review the top decile every month, you will catch the majority of distress events with manageable false-positive load**.

Concretely, for an 80-firm panel that means ~8 firms per month to look at.

### Step 4 — For each top-decile firm, open its trajectory

The trajectory chart (`outputs/figures/phase1_trajectories.png`) shows that firm's predicted-risk line over the last 2–3 years. The analyst asks:

- Is this alert **new** this month, or has the firm been elevated for a while?
- Is the trend **rising**, or is this a one-month noise spike?
- Did any red shading (prior realized distress) already occur?

A brand-new alert with a rising trend is the highest-priority review. A firm that has been flat-elevated for a year with no actual drawdown yet is lower priority.

### Step 5 — Read the top drivers and decide

The analyst takes the top 3 feature contributions (e.g. "leverage +0.8 SD, drawdown_12m −45%, late_filing = 1") and either:

- **Escalate** — put the firm on the internal watchlist, pull their latest 10-Q, schedule management contact.
- **Monitor** — note the signal, check back next month.
- **Dismiss with reason** — record why (e.g. "drawdown is sector-wide, firm is fundamentally sound"). This creates a feedback loop — if dismissed firms subsequently default, that's a signal the analyst's override was wrong and the model was right.

### Step 6 — Close the loop

Each month, the team records which alerts were escalated and which were dismissed. Over time, compare those human decisions against realized outcomes. This is the governance data that lets the tool earn credibility — or lose it.

## What the tool does NOT do

| ❌ Not a use | ✅ Instead |
| :--- | :--- |
| Trade on the score | Use for credit monitoring only |
| Decide loan pricing | Feed into the analyst's narrative, never replace it |
| Predict the exact timing of a default | Signal elevated risk over a 12-month horizon |
| Work on firms outside the trained panel | Refit the model if expanding universe |
| Replace fundamental credit review | Prioritize where that review goes |

## How to interpret the probability score

Given the Phase 1 calibration issues, use these bands until calibration is repaired in Phase 2:

| Predicted probability | Interpretation |
| :--- | :--- |
| > 0.80 | High confidence signal — treat as elevated |
| 0.50–0.80 | Middle band — rely on **ranking**, not the number itself |
| 0.20–0.50 | Middle band — rely on **ranking**, not the number itself |
| < 0.20 | Low confidence signal — probably safe, but not a guarantee |

After Phase 2 recalibration, the number can be taken more literally.

## How to interpret a single firm

Rules of thumb an analyst can apply:

1. **Probability level tells you the how-worried-to-be.** Decile and rank tell you where to spend your attention.
2. **A month-over-month jump** (e.g. 0.30 → 0.65) is often more actionable than a high but stable value (0.70 flat for a year).
3. **Match the alert to the features.** If the top driver is `drawdown_12m`, the signal is market-driven; if it's `leverage` and `late_filing`, it's fundamentals-driven. Different follow-up.
4. **Sector context matters.** March 2020 alerts across the airline sector reflect COVID shock, not firm-specific deterioration. Adjust expectations accordingly.

## Governance

The tool's credibility depends on three things being true:

1. **No look-ahead bias** in any feature. Audit this quarterly.
2. **Time-separated evaluation** — all performance claims come from val/test windows, never training.
3. **Open feedback loop** — every alert must have a recorded human disposition and outcome. Without this, you cannot tell whether the model is improving or degrading.
