# Contributing

## First-time setup

```bash
git clone <repo-url> && cd hku-final
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/run.py                # run the pipeline (works from repo root)
python tests/smoke_test.py       # verify your setup (11 assertions)

# The `python -m ews.pipeline` form also works but needs PYTHONPATH:
#   PYTHONPATH=src python -m ews.pipeline
```

If the smoke test exits clean, you're ready to contribute.

## Before you touch anything

Read in order: `README.md` → `docs/01_PIPELINE.md` → `docs/05_PLUGGING_IN_REAL_DATA.md`.

You don't need to read every line of code. You do need to understand the panel schema, the no-look-ahead rule, the time split, and the loader contract in `src/ews/loaders.py`.

## Ownership (Phase 1 → Phase 2)

| Component | Status | Phase 2 owner |
| :--- | :--- | :--- |
| yfinance + market features | Working | Shrey |
| SEC fundamentals | Placeholder | Allen |
| Label A (drawdown) | Working | Darren |
| Label B (8-K Item 1.03) | Not implemented | Darren |
| 12b-25 late-filing | Stub | Darren |
| FRED macros | Synthetic | TBD (Hui Fai / Shrey) |
| Econometrics + evaluation (pooled / FE / hazard logit, ablation, rolling-window) | Working (pooled committed; FE + hazard preview) | Ivan |

Confirm ownership with Hui Fai before claiming a component.

## Adding a new data source

The concrete HOWTO is `docs/05_PLUGGING_IN_REAL_DATA.md` — function signatures, schema contract, validator, and the exact dispatch path for Allen and Darren.

## Adding a new model

Must be interpretable (proposal constraint — no deep learning, no GBMs as primary). Add to `src/ews/models.py` with the same `(train, val, test) -> (model, preds)` signature as the three baselines, and document in `docs/01_PIPELINE.md` Models section.

## Code conventions

- Pipeline must be deterministic (seed any randomness inside the function that uses it).
- Cache raw pulls to `data/raw/`; `load_prices` is the pattern.
- Fail loudly — see `LoaderError` in `loaders.py`.
- Any doc-relevant change: if you touched the schema, paths, or commands, the corresponding doc (02/03/06, README, or `requirements.txt`) goes in the same commit.

## When something breaks

1. Read the error. 80% of the time it's a merge-key mismatch in the panel.
2. `python tests/smoke_test.py` — if it fails, refactor invariants are broken before your data changes.
3. Check `data/interim/*.csv` to find which loader output broke the merge.
4. Ping the team before debugging solo for more than an hour.

## Deferred work

Phase 2+ backlog: `TODOS.md`.
