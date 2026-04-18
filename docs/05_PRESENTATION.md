# 05 — Presentation

How to communicate this work to different audiences. The same pipeline tells different stories depending on who's listening.

## The four audiences

| Audience | What they care about | What scares them off |
| :--- | :--- | :--- |
| Thesis marker | Academic rigor, literature grounding | Black-box models, look-ahead bias |
| Supervisor (Yi Chen) | Interpretability, time discipline | Cherry-picked metrics |
| Credit-committee / risk practitioners | Operational utility, calibration | Untested probability numbers |
| Non-technical audience (oral exam, webpage) | A clear story | Math with no narrative |

## The three-slide core

Every presentation — 5 minutes or 50 — can be built around these three slides. Add depth as the time allows; never remove them.

### Slide 1: The problem

*Credit deterioration is a process, not a day.* Firms don't fail overnight — leverage creeps up, liquidity tightens, stock starts sliding, late filings appear. Credit analysts need a tool that sees these signs **before** the drawdown happens, across 60–80 firms, every month, without a Bloomberg terminal. Existing solutions are proprietary, static, or both.

Visual: a single firm trajectory (BBBY or CHK), showing risk ramping up in the year before the event.

### Slide 2: The system

*A monthly panel of open public data, three interpretable models, one probability score per firm.*

Visual: the pipeline diagram from `02_PIPELINE.md`.

Three talking points:
- **Data is open and reproducible** — SEC EDGAR, yfinance, FRED. Anyone can rerun this.
- **Models are interpretable** — logistic regression, fixed-effects logit, discrete-time hazard. Grounded in Altman, Ohlson, Shumway.
- **No look-ahead bias** — strict time-based splits, fundamentals aligned to filing date not quarter-end.

### Slide 3: The evidence

*The four charts, with one-sentence takeaways each.*

Visual: 2×2 grid of ROC/PR, calibration, deciles, trajectories.

- ROC/PR: *"The model discriminates distress from normal at the extremes."*
- Calibration: *"Rankings are reliable; probability level will be recalibrated in Phase 2."*
- Deciles: *"Top decile concentrates 79% event rate vs 26% base — the watchlist works."*
- Trajectories: *"Alerts appear months before realized distress for BBBY, AAL, SNAP, INTC."*

## Slide templates by audience

### For a thesis marker (academic framing)

Lead with literature: Altman → Ohlson → Shumway → you. Frame every design choice as a traceable decision from that lineage. Cite Merton for the market-based intuition even if distance-to-default stays optional.

Order:
1. Research question and gap
2. Data (reproducibility emphasis)
3. Label design (Label A primary, Label B secondary, threshold robustness)
4. Models (three, all interpretable, no deep learning)
5. Validation protocol (time split, rolling windows, no look-ahead)
6. Results (ROC/PR, calibration, deciles, lead-time)
7. Limitations (Phase 1 placeholder fundamentals, small sample)
8. Phase 2+ roadmap

### For a supervisor check-in

Keep it to the gap and the evidence:
- What was promised: the five metric families in the proposal.
- What's delivered: all five, on 9-firm toy data.
- What's next: 60–80 firms with real fundamentals, recalibration, true hazard spec.
- Where you need help: CHK replacement, FRED key setup, 8-K parser.

### For a credit-committee / risk-practitioner demo

Lead with the use case, not the method. Open with the **decile chart** — "if you commit to reviewing the top 10% each month, you catch ~3× the background rate of distress." Then show trajectories as the qualitative complement. Calibration and ROC come last and only if asked. Never open with AUC to practitioners.

### For the non-technical oral exam

Build a 7-minute narrative:
1. (1m) Setup — what analysts do, what's hard, why open data.
2. (2m) Show one firm trajectory (BBBY). Let the chart do the work.
3. (2m) Show the decile chart. Explain "top 10% each month."
4. (1m) Show the pipeline diagram. One sentence per arrow.
5. (1m) State limitations honestly. Gesture at Phase 2.

## Anti-patterns — don't do these

| Anti-pattern | Why it fails |
| :--- | :--- |
| Lead with AUROC = 0.60 to a practitioner | They'll hear "barely better than random" and disengage |
| Show calibration plot without explaining the bimodal issue | Looks like you don't know it's broken |
| Present Phase 1 metrics as the final result | It's a prototype. Say so. |
| Hide BBBY dominance | Markers will ask. Get ahead of it. |
| Claim "our hazard model is Shumway-style" without showing how | The three models collapse to two in the current run. Be honest. |
| Use jargon with non-technical audiences | "Logit" is a word they do not owe you to know |

## One-liner variants you can steal

For a 30-second pitch:

> We built a free-data monthly credit-risk alert system that uses SEC filings, stock prices, and macro stress indicators to rank 80 firms by their 12-month distress probability. Analysts review the top 10% each month and catch three times the baseline rate of distress events, using interpretable regressions grounded in Altman, Ohlson, and Shumway.

For a two-sentence abstract:

> This project implements an interpretable, reproducible early-warning system for US-listed non-financial firms using only open data (SEC EDGAR, yfinance, FRED). The system produces monthly firm-level probability scores and a risk-trajectory dashboard, with evaluation based on time-separated splits and five metric families: AUROC, AUPRC, Brier score, top-K lift, and lead-time.

For the webpage tagline:

> Open-data credit risk. Monthly alerts. No black boxes.

## Assets for the final write-up and webpage

Phase 4 deliverables need these assets ready. Check them off as you build:

- [ ] Clean 2×2 chart grid (Phase 2 version, not Phase 1)
- [ ] Pipeline diagram (export from `02_PIPELINE.md` ASCII into a proper SVG/PNG)
- [ ] Coefficient tables with odds ratios and p-values
- [ ] Top-10 monthly watchlist example for a recent month
- [ ] One deep-dive firm narrative (choose the cleanest: AAL around COVID, or BBBY)
- [ ] Limitations section (be honest, this earns credibility)
- [ ] Reproducibility appendix (data sources, dates, commit hash)
