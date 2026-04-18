# Contributing

How teammates plug work into the pipeline. If you're adding data, features, or models, start here.

## Before you touch anything

Read (in order):
1. `README.md` — what the project is
2. `docs/01_INPUTS.md` — what the pipeline consumes
3. `docs/02_PIPELINE.md` — how inputs become outputs
4. `docs/03_OUTPUTS.md` — what the pipeline produces and what each chart means

You do not need to read every line of code. You do need to understand the panel schema, the no-look-ahead rule, and the time split.

## Ownership map (Phase 1 → Phase 2)

| Component | Phase 1 status | Phase 2 owner | What needs to happen |
| :--- | :--- | :--- | :--- |
| yfinance price ingest | Working | Ivan | Fix CHK (or replace) |
| Real SEC fundamentals | Placeholder | Allen | Pull XBRL, align to filing date, carry forward |
| 8-K bankruptcy label (Label B) | Not implemented | Darren | Parse 8-K Item 1.03, build binary label |
| FRED macro data | Synthetic | TBD (Hui Fai/Shrey) | Wire FRED API, pull VIXCLS / DGS10 / DGS2 / DBAA |
| Model fitting + evaluation | Working | Ivan | Recalibrate, split val/test reporting properly |
| Rolling-window validation | Stub in code | TBD | Confirm working, include in write-up |
| Ablation study | Stub in code | TBD | Confirm working, include in write-up |
| Documentation | This file | Whoever made the change | Keep docs in sync |

Confirm ownership with Hui Fai (team leader) before claiming a component.

## Adding a new data source

1. Document in `docs/01_INPUTS.md` under the appropriate family. Include endpoint, rate limit, caching strategy.
2. Add an ingest function in `src/` that returns a pandas dataframe keyed by `(ticker, date)` or `(date,)` for macro-only.
3. Respect no-look-ahead. Fundamentals align to **filing date**, not period-end. Market and macro series aggregate to month-end using only data available at t.
4. Merge into the main panel in `build_panel()`.
5. Update the feature list in `docs/02_PIPELINE.md`.
6. Run the pipeline. Confirm your new column appears in `data/processed/panel_phase1.csv`.
7. Re-run evaluation. Confirm the four charts still produce — and note any improvement in metrics.

## Adding a new feature

A feature is a column derived from raw inputs. Rules:
- Must be computable at month-end using only information available at that time.
- Must have a documented meaning (what firm-level condition does it describe?)
- Must appear in `FEATURE_COLS` in the code and in `docs/02_PIPELINE.md`.

If your feature uses any forward-looking information, it is **not** a feature. It is a label candidate.

## Adding a new model

Models must be interpretable. This is a hard constraint from the proposal — no deep learning, no gradient-boosted trees as primary models.

Acceptable: logistic regression variants, linear discriminant, Cox PH, survival forests (only as robustness check), Altman-style discriminants. Each must produce a probability (or at minimum a monotone risk score) so it can be evaluated on AUROC / AUPRC / Brier / deciles / trajectories.

Each new model needs:
- A short paragraph in `docs/02_PIPELINE.md` explaining what it assumes and what it adds.
- Coefficient outputs captured in the terminal log.
- Performance numbers on the val/test split, stored in the same comparison tables as the three baseline models.

## Code conventions

This is a research codebase, not production. That said:
- Keep the pipeline deterministic. Set random seeds where sampling is involved.
- Cache raw API pulls to disk. Never re-pull within a single session.
- Fail loudly when data is missing (don't silently drop, as CHK did — print it).
- Prefer readable over clever.

## Check-in rhythm

- **Daily async** during Phase 1 and Phase 2 crunch — short update in the team chat, what you did, what you're doing, what's blocked.
- **Weekly sync with mentor Yi Chen** — prepare a short update showing which of the five evaluation metrics improved since last week.
- **Phase deadline demos** — April 24 (Phase 1), May 5 (Phase 2), early June (Phase 3), July (Phase 4). Each demo revisits the four charts and tells the story of what changed.

## What to do when something breaks

1. Read the error. 80% of the time it's a merge key mismatch in the panel (ticker casing, date off-by-one month-end).
2. Check `data/processed/panel_phase1.csv` exists and has the expected schema.
3. Check all 14 `FEATURE_COLS` have data (no all-NaN columns).
4. Check the time split has rows on both sides (train, val, test each non-empty).
5. If the charts produce but look wrong, run the same review in `docs/03_OUTPUTS.md` — which chart says what, and which one is showing abnormal shape.
6. Ping the team before debugging solo for more than an hour.

## Definition of done for Phase 2

Phase 2 is complete when all four of these are true:
- Panel has 60–80 firms, not 9.
- Fundamentals come from real SEC XBRL, not placeholders.
- Macro series come from real FRED pulls, not synthetic.
- Label B (8-K bankruptcy) is wired and reported alongside Label A.

Phase 2 is complete *well* when:
- AUROC on test set exceeds 0.70 on Label A.
- Calibration curve is monotone.
- Decile chart is monotone increasing.
- Hazard model produces meaningfully different predictions from pooled logit.
