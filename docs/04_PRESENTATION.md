# 04 — Presentation

How to communicate this work. The same pipeline tells different stories depending on who's listening — but the three-slide core below works for anyone.

## The four audiences (quick reference)

| Audience | Care about | Scared by |
| :--- | :--- | :--- |
| Thesis marker | Academic rigor, literature grounding | Black boxes, look-ahead bias |
| Supervisor (Yi Chen) | Interpretability, time discipline | Cherry-picked metrics |
| Credit committee / practitioners | Operational utility, calibration | Untested probability numbers |
| Non-technical (oral exam, webpage) | Clear story | Math with no narrative |

## The three-slide core

Every presentation — 5 minutes or 50 — can be built around these three slides. Add depth when time allows; never remove them.

### Slide 1: The problem

*Credit deterioration is a process, not a day.* Firms don't fail overnight — leverage creeps up, liquidity tightens, stock starts sliding, late filings appear. Credit analysts need a tool that sees these signs **before** the drawdown, across 60–80 firms, every month, without a Bloomberg terminal. Existing solutions are proprietary, static, or both.

**Visual:** a single firm trajectory (BBBY or CHK), risk ramping up in the year before the event.

### Slide 2: The system

*A monthly panel of open public data, interpretable regressions, one probability score per firm.*

**Visual:** the pipeline diagram from `01_PIPELINE.md`.

Three talking points:
- **Open & reproducible data** — SEC EDGAR, yfinance, FRED. Anyone can rerun this.
- **Interpretable models** — pooled logit is the committed Phase 1 model (per proposal Table 2); fixed-effects panel logit and Shumway-style hazard are delivered ahead of schedule as Phase 2 previews. Grounded in Altman, Ohlson, Shumway.
- **No look-ahead bias** — strict time-based splits, fundamentals aligned to filing date not quarter-end.

### Slide 3: The evidence

*The four charts, one-sentence takeaway each.*

**Visual:** 2×2 grid of ROC/PR, calibration, deciles, trajectories.

- **ROC/PR:** "The model discriminates distress from normal at the extremes."
- **Calibration:** "Rankings are reliable; probability level will be recalibrated in Phase 2."
- **Deciles:** "Top decile concentrates ~79% event rate vs ~26% base — the watchlist works."
- **Trajectories:** "Alerts appear months before realized distress for BBBY, AAL, SNAP, INTC."

## Anti-patterns — don't do these

| Anti-pattern | Why it fails |
| :--- | :--- |
| Lead with AUROC = 0.60 to a practitioner | They hear "barely better than random" and disengage. Lead with deciles instead. |
| Show calibration plot without explaining the bimodal issue | Looks like you don't know it's broken. |
| Present Phase 1 metrics as the final result | It's a prototype. Say so. |
| Hide BBBY dominance | Markers will ask. Get ahead of it. |
| Claim Phase 1 delivers all three models as proposal commitments | Proposal Table 2 commits only pooled logit to April 24. FE + hazard are delivered **ahead of schedule** as Phase 2 previews. Saying "we previewed FE and hazard early" lands better than "we delivered all three as committed." |
| Use jargon with non-technical audiences | "Logit" is a word they don't owe you to know. |

## One-liners you can steal

**30-second pitch:**
> We built an open-data monthly credit-risk early-warning system that uses SEC filings, stock prices, and macro stress indicators to rank ~80 firms by their 12-month probability of market-implied credit deterioration. Analysts review the top 10% each month and catch three times the baseline rate of distress events, using interpretable regressions grounded in Altman, Ohlson, and Shumway.

**Two-sentence abstract:**
> This project implements an interpretable, reproducible early-warning system for US-listed non-financial firms using only open data (SEC EDGAR, yfinance, FRED). The system produces monthly firm-level probability scores and a risk-trajectory dashboard, with evaluation based on time-separated splits and five metric families: AUROC, AUPRC, Brier score, top-K lift, and lead-time.

**Webpage tagline:**
> Open-data credit risk. Monthly alerts. No black boxes.

## Final write-up / webpage assets

- [ ] Clean 2×2 chart grid (Phase 2 version, not Phase 1)
- [ ] Pipeline diagram exported as SVG/PNG
- [ ] Coefficient tables with odds ratios and p-values
- [ ] Top-10 monthly watchlist example for a recent month
- [ ] One deep-dive firm narrative (cleanest candidate: AAL around COVID, or BBBY)
- [ ] Limitations section (be honest — this earns credibility)
- [ ] Reproducibility appendix (data sources, dates, commit hash)
