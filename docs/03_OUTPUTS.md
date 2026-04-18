# 03 — Outputs

What the pipeline produces, and what each thing means. If you are staring at a chart and don't know what you're looking at, this is the file.

## The two kinds of output

The pipeline produces **one data artifact** and **four diagnostic charts**. The data artifact is the thing analysts consume; the charts are the thing markers and supervisors evaluate.

### Data artifact

**`data/processed/panel_phase1.csv`** — 1,490 rows × 23 columns. Every row is one firm observed in one month. This is both an intermediate (models train on it) and a deliverable (it *is* the dataset underpinning every claim in the thesis).

Schema:

| Column | Type | Meaning |
| :--- | :--- | :--- |
| ticker | str | Stock ticker, e.g. "BBBY" |
| date | date | Month-end |
| firm_name | str | "Bed Bath & Beyond" |
| industry | str | Free-text sector |
| year, month | int | Decomposed date |
| leverage, liquidity_buffer, wc_ratio, profitability, z_score | float | Fundamentals (Phase 1: placeholder) |
| late_filing | 0/1 | 12b-25 signal in prior 6 months |
| ret_1m, ret_3m, ret_6m | float | Trailing returns |
| vol_3m, vol_6m | float | Trailing volatility, annualized |
| drawdown_12m | float | Peak-to-trough over past 12 months |
| vix, term_spread, credit_spread | float | Macro stress (Phase 1: synthetic) |
| label_a | 0/1 | **LABEL** — 1 if ≥40% drawdown in next 12 months |
| forward_max_drawdown | float | The drawdown that generated label_a (debug only, not a feature) |

### Diagnostic charts

Four charts in `outputs/figures/`. They are not optional; they are the five evaluation metrics the proposal committed to, rendered visually.

## How to read the four charts

Each section below answers three questions: **what does the chart show**, **what does a good version look like**, and **what does our Phase 1 version say**.

---

### Chart 1 — ROC & PR curves (`phase1_roc_pr.png`)

**What it shows.** The model's ability to separate firm-months that will experience a 40%+ drawdown from firm-months that will not. Two panels, two different ways of looking at that separation.

**Left panel (ROC).** For every possible alert threshold, plot (x-axis) the false-alarm rate against (y-axis) the catch rate. A perfect model hugs the top-left corner. A useless model tracks the diagonal dashed line. **AUROC** (area under this curve) is one number summarizing the chart: 0.5 = coin flip, 1.0 = perfect.

**Right panel (Precision-Recall).** For every possible alert threshold, plot (x-axis) the share of true events caught against (y-axis) how often "alert" is actually right. The flat dashed line is the base rate — what you'd get by calling everything an alert. **AUPRC** is one number summarizing this: in a rare-event problem it is a harsher and fairer metric than AUROC.

**What good looks like.** AUROC > 0.75 and AUPRC well above base rate. ROC curve rises steeply at low FPR, then plateaus near 1.0.

**What Phase 1 says.** AUROC 0.603 (pooled) / 0.629 (FE) / 0.603 (hazard). AUPRC 0.527 / 0.557 / 0.527 on a 20–26% base rate. Meaningfully better than chance, far below production-grade. Pooled and hazard lines overlap exactly — a red flag that the hazard implementation is not meaningfully different from the pooled logit in its current form.

**The one sentence to take away.** The model can tell distressed firm-months from normal ones at the extremes, but sorts poorly in the middle.

---

### Chart 2 — Calibration (`phase1_calibration.png`)

**What it shows.** Whether the model's probability output can be trusted as a probability. Two panels.

**Left panel (reliability curve).** Take every firm-month where the model said "probability = 30%." Among those, what fraction actually experienced an event? If the answer is 30%, the model is calibrated. You want the blue line on the dashed diagonal.

**Right panel (prediction histogram).** How often the model emits each probability value. A well-behaved model produces a smooth distribution. A miscalibrated or memorizing model produces a bimodal distribution (piles near 0 and near 1, empty middle).

**What good looks like.** Blue line close to the diagonal. Histogram smooth and unimodal (or at least not bimodal).

**What Phase 1 says.** Non-monotone reliability curve. Firm-months scored 0.4–0.6 actually experience events *less often* than firm-months scored 0.1–0.3. Histogram is bimodal. Meaning: the model's probability number is **not trustworthy on its own** in the mid-range. You can trust the ranking ("firm X is riskier than firm Y") more than the level ("firm X has a 47% chance").

**The one sentence to take away.** The probability scores rank firms in roughly the right order, but the number itself should not be read literally yet.

**Fix path.** Apply Platt scaling or isotonic regression on validation data before reporting. Add to Phase 2 roadmap.

---

### Chart 3 — Risk deciles (`phase1_deciles.png`)

**What it shows.** If you sort all firm-months by predicted risk and chop into 10 equal buckets (decile 1 = safest 10%, decile 10 = riskiest 10%), what fraction of each bucket actually experienced a distress event? This is the **analyst-utility chart** — it directly answers "if I only have bandwidth to review the top 10% of firms each month, will that catch most of the real distress?"

**What good looks like.** A monotone staircase rising left to right. Decile 10 should be at least 2–3× the base rate; decile 1 should be well below.

**What Phase 1 says.** Decile 10 is at 79% vs 26.2% base — ~3× lift, which is the headline operational case for the tool. But deciles 6, 7, 8 are at 9%, 3%, 9% — *below* base rate. Non-monotone in the middle. Translation: the tool is useful for "show me the top 10% of risk this month" and mostly useless for "sort everyone by risk."

**The one sentence to take away.** The top-decile watchlist works as a product; a full risk ranking does not.

---

### Chart 4 — Firm trajectories (`phase1_trajectories.png`)

**What it shows.** Nine subplots, one per firm. Blue line = predicted risk over time. Red shading = actual event periods (months where Label A = 1 because a big drawdown was incoming). Orange dashed line = the alert threshold.

**What to look for.** Does the blue line rise **before** the red shading appears? That's lead-time. Does it stay flat for firms that never experienced distress? That's specificity.

**What good looks like.** Blue line elevated for several months before every red period (early warning works). Blue line low for PFE and other stable firms (no false alarms).

**What Phase 1 says.** BBBY's blue line is elevated for years before its 2020–2023 event cluster — lead-time works for the headline case. AAL, F, GE spike in late 2019 before the March 2020 COVID red shading — lead-time works for systemic shocks. PFE stays flat with almost no alerts — specificity works. SNAP ramps into 2022, INTC late-window spike in 2024 — both look reasonable. One empty panel in the bottom-right corner: CHK's slot, because yfinance couldn't fetch CHK prices post-bankruptcy.

**The one sentence to take away.** Qualitatively, the model alerts on the right firms at the right times, even though aggregate metrics look modest.

---

## Which chart to show to whom

| Audience | Show | Because |
| :--- | :--- | :--- |
| Thesis marker checking rigor | ROC/PR + Calibration | Maps directly to AUROC, AUPRC, Brier score promises |
| Credit analyst evaluating utility | Risk deciles | Answers "does the watchlist work?" |
| Risk committee | Calibration | Decides whether the probability score is interpretable |
| Supervisor / oral exam | Trajectories | Makes the "early warning" claim concrete and firm-specific |
| Non-technical audience | Trajectories, then deciles | Story-shaped, visual, easy to narrate |

## Legacy charts

`outputs/figures/legacy/` contains earlier chart versions from prior runs (filenames `chart_*.png`). They predate the current feature set and split. Do not use them in any write-up. Kept only for diff-ing if someone asks "what changed since April 16?"
