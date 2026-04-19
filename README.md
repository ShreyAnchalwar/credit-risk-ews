# Credit Risk Early-Warning System (EWS)

An interpretable, open-data credit risk early-warning system for US-listed non-financial firms, 2010–2025. Each month, for each firm in the panel, the pipeline outputs a probability of **credit deterioration** over the next 12 months — together with a risk-trajectory view for analyst watchlist and escalation triage.

Not for trading. For credit-risk oversight.

Every model is a standard interpretable regression (logistic, fixed-effects, discrete-time hazard) whose coefficients a practitioner can read and argue with. No deep learning, no black boxes. Every data source is open and free (SEC EDGAR, yfinance, FRED) — no Bloomberg, no paid feeds.

## Team

| Role | Name |
| :--- | :--- |
| Mentor | Yi Chen |
| Leader | Hui Fai Wong |
| Contributor (market features) | Anchalwar Shrey Sanjay |
| Contributor (labels & filing signals) | Fung Tat Ki (Darren) |
| Contributor (econometrics & evaluation) | Chow Pak Ho (Ivan) |
| Contributor (SEC fundamentals) | Yu Yuk Lam Allen |

## Where we are

Phase 1 (prototype, due **April 24**) is code-complete on a **10-firm toy panel** (9 with complete data; CHK was delisted post-bankruptcy in 2020 and yfinance has no history for it — see `src/ews/config.py::ALLOWED_SHORT_HISTORY`). The pipeline runs end-to-end and produces the four evaluation charts the proposal commits to. See `outputs/figures/` and `docs/02_OUTPUTS.md`.

The proposal's Phase 1 target is 30–50 firms on a shorter horizon; the current 10-firm panel validates the full pipeline end-to-end. **Phase 2** expands to 60–80 firms with real SEC fundamentals (Allen), real FRED macros, and 8-K bankruptcy labels (Darren).

**Models.** Phase 1's committed model (per proposal Table 2) is the **pooled logistic regression**. The current run also fits a **fixed-effects panel logit** and a **Shumway-style discrete-time hazard logit** — these are delivered ahead of schedule as a preview of Phase 2 work; treat their metrics as provisional until the 60–80 firm panel lands.

## Repo map

```
.
├── README.md                     ← you are here
├── CONTRIBUTING.md               ← how to plug work in
├── TODOS.md                      ← Phase 2+ backlog
├── requirements.txt              ← pinned deps
├── docs/
│   ├── 01_PIPELINE.md            ← data flow: inputs → outputs (ASCII diagram + module map)
│   ├── 02_OUTPUTS.md             ← what comes out + how to read the four charts
│   ├── 03_USAGE.md               ← how an analyst uses the outputs (1-page workflow)
│   ├── 04_PRESENTATION.md        ← how to present to markers / committee
│   └── 05_PLUGGING_IN_REAL_DATA.md  ← HOWTO for Allen + Darren (loader contract)
├── src/
│   ├── ews/                      ← the pipeline package (see docs/01_PIPELINE.md)
│   │   ├── config.py             ← firms, features, thresholds, paths
│   │   ├── loaders.py            ← team-facing data-source contract
│   │   ├── features.py           ← market-feature engineering
│   │   ├── labels.py             ← Label A construction (Label B goes here too)
│   │   ├── panel.py              ← merge + time split
│   │   ├── models.py             ← pooled / FE / hazard logit
│   │   ├── eval.py               ← metrics + ablation + robustness
│   │   ├── viz.py                ← the four charts
│   │   └── run.py                ← the orchestrator
│   └── run.py                    ← pipeline entry point (thin wrapper; sets sys.path then calls ews.pipeline.main)
├── tests/
│   └── smoke_test.py             ← 11 assertions on the refactor's new paths
├── data/
│   ├── raw/                      ← yfinance cache (committed for reproducibility)
│   ├── interim/                  ← one CSV per loader (inspectable)
│   └── processed/
│       └── panel_phase1.csv      ← 1,490 firm-months × 23 columns
├── outputs/
│   ├── figures/                  ← the four Phase 1 charts
│   └── pipeline_overview.html
└── reference/                    ← canonical source of truth
    ├── Detailed Proposal v1.docx.md
    └── Team Catch v1 Apr 16.docx.md
```

## Quickstart

```bash
# One-time setup — isolates deps from system Python (avoids PEP 668 errors on macOS)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the pipeline (first run hits yfinance ~30–60s; subsequent runs use data/raw/ cache)
python src/run.py
# or equivalently (PYTHONPATH=src is needed because there's no pyproject.toml yet):
PYTHONPATH=src python -m ews.pipeline

# Verify your setup
python tests/smoke_test.py
```

Outputs are written automatically — no manual copying required:

- `data/processed/panel_phase1.csv` — the modeling panel (1,490 firm-months × 23 columns)
- `data/interim/{prices,market_features,fundamentals,macros,labels}.csv` — per-source intermediate tables (Excel-friendly, with a provenance header)
- `outputs/figures/phase1_{roc_pr,calibration,deciles,trajectories}.png` — the four evaluation charts

## Data sources

Four families feed the panel. Full schema contract and real-loader HOWTO lives in `docs/05_PLUGGING_IN_REAL_DATA.md`.

| Family | Phase 1 source | Phase 2 owner | Source name |
| :--- | :--- | :--- | :--- |
| Equity prices | yfinance (real, cached) | Shrey | `load_prices(source="yfinance")` |
| Firm fundamentals | Placeholder synthetic | Allen | `load_fundamentals(source="sec")` |
| Macro stress | Synthetic (regime-aware) | TBD | `load_macros(source="fred")` |
| Labels (drawdown + 8-K) | Label A only (drawdown); `label_b` NaN | Darren | `load_labels(source="8k")` |

No-look-ahead is a hard rule: fundamentals align to **filing date**, not period-end; market and macro aggregate to month-end using only data available at time t.

## Where to read next

- **How it works?** → `docs/01_PIPELINE.md` (data flow + ASCII diagram + module map).
- **What the charts mean?** → `docs/02_OUTPUTS.md`.
- **How an analyst uses it?** → `docs/03_USAGE.md`.
- **Preparing slides / oral exam?** → `docs/04_PRESENTATION.md`.
- **Contributing real data (Allen / Darren)?** → `docs/05_PLUGGING_IN_REAL_DATA.md`.
- **Coding conventions / first-time setup?** → `CONTRIBUTING.md`.
- **Phase 2 backlog?** → `TODOS.md`.
- **Canonical source of truth?** → `reference/Detailed Proposal v1.docx.md`.

## One-paragraph project summary for outsiders

Each month, for each of ~80 US-listed non-financial firms, the pipeline reads SEC filings, stock prices, and macro stress indicators, and outputs a probability between 0 and 1 that the firm will experience **market-implied credit deterioration** — a peak-to-trough equity drawdown of at least 40% — at some point over the next 12 months. A credit analyst can then focus their review time on the highest-probability firms (a "monitoring scorecard" for watchlist triage). Everything uses open, reproducible data, and every model is an interpretable regression whose coefficients can be read and argued with.
