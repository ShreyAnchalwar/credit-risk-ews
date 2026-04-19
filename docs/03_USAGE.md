# 03 — Usage

How an analyst uses the output. The pipeline exists to support this workflow — if it doesn't work here, nothing else matters.

## Who the user is

A **credit analyst** monitoring ~80 firms. They don't have time to read every 10-K. They want a short, ranked list each month of "who should I look at?"

The EWS is a **prioritization tool for analyst attention**, not an automatic decision system.

## The monthly workflow

1. **Run the pipeline** on first business day of the month (ingests latest prices, filings, macro values).
2. **Open the watchlist** — ranked table, one row per firm: rank, ticker + name, probability (0–1), decile (1–10), trend vs prior month, top 3 feature drivers.
3. **Focus on the top decile.** The decile chart (`outputs/figures/phase1_deciles.png`) shows this bucket concentrates ~3× the base rate of distress events. For 80 firms that's ~8 names/month.
4. **For each top-decile firm, open its trajectory** (`outputs/figures/phase1_trajectories.png`). Ask: new alert this month or stale? Rising or noise? Any prior realized distress? *A new rising alert is the highest-priority review.*
5. **Read the top drivers and decide** — escalate (internal watchlist + pull the 10-Q), monitor (note, check next month), or dismiss with reason (creates a feedback loop against realized outcomes).
6. **Close the loop.** Record which alerts were escalated vs dismissed. Over time, compare to realized outcomes — this is the governance data that earns the tool credibility.

## Reading the probability

Phase 1 calibration is bimodal and non-monotone; trust **ranking over level** until Phase 2 recalibration. After recalibration the number can be read literally.

## What it does NOT do

Not a trading signal. Not a loan-pricing input. Not a timing predictor for specific defaults. Not a replacement for fundamental review. It prioritizes *where* that review goes.
