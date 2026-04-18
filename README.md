# Credit Risk Early-Warning System (EWS)

An interpretable, open-data credit risk early-warning system for US-listed non-financial firms, 2010–2025. Outputs a monthly firm-level probability of credit deterioration within the next 12 months, plus a risk-trajectory dashboard for analyst watchlist and escalation triage.

Not for trading. For credit-risk oversight.

## Team

| Role | Name |
| :--- | :--- |
| Mentor | Yi Chen |
| Leader | Hui Fai Wong |
| Contributor | Anchalwar Shrey Sanjay |
| Contributor | Fung Tat Ki |
| Contributor | Chow Pak Ho (Ivan) |
| Contributor | Yu Yuk Lam Allen |

## Where we are

Phase 1 (prototype, due April 24) is code-complete on a **9-firm toy panel** using real yfinance prices + placeholder fundamentals + synthetic macros. The pipeline runs end-to-end and produces the four evaluation charts the proposal commits to. See `outputs/figures/` and `docs/03_OUTPUTS.md`.

Phase 2 expands to 60–80 firms with real SEC fundamentals (Allen), real FRED macros, and 8-K bankruptcy labels (Darren).

## Repo map

```
.
├── README.md                     ← you are here
├── CONTRIBUTING.md               ← how to plug work in
├── docs/
│   ├── 01_INPUTS.md              ← what the pipeline consumes
│   ├── 02_PIPELINE.md            ← how inputs become outputs
│   ├── 03_OUTPUTS.md             ← what comes out + how to read the charts
│   ├── 04_USAGE.md               ← how an analyst uses the outputs
│   └── 05_PRESENTATION.md        ← how to present to markers / committee
├── src/
│   ├── ivan_ews_phase1.py        ← Phase 1 pipeline (end-to-end runner)
│   └── ivan_ews_models.py        ← earlier model scratch
├── data/
│   └── processed/
│       └── panel_phase1.csv      ← 1,490 firm-months, 23 columns
├── outputs/
│   ├── figures/
│   │   ├── phase1_roc_pr.png
│   │   ├── phase1_calibration.png
│   │   ├── phase1_deciles.png
│   │   ├── phase1_trajectories.png
│   │   └── legacy/               ← superseded charts from earlier runs
│   └── pipeline_overview.html
└── reference/
    ├── Detailed Proposal v1.docx.md
    └── Team Catch v1 Apr 16.docx.md
```

## Quickstart

```bash
pip install pandas numpy yfinance statsmodels scikit-learn matplotlib
python src/ivan_ews_phase1.py
```

Outputs land in the current directory at runtime; copy them into `outputs/figures/` and `data/processed/` when you commit.

## Where to read next

- **New to the project?** → `docs/01_INPUTS.md` then `docs/02_PIPELINE.md`.
- **Looking at the charts and confused?** → `docs/03_OUTPUTS.md`.
- **Writing up a section or preparing slides?** → `docs/05_PRESENTATION.md`.
- **Planning to contribute code or data?** → `CONTRIBUTING.md`.

## One-paragraph project summary for outsiders

We build a monthly watchlist tool. Each month, for each of ~80 US firms, the tool reads SEC filings, stock prices, and macro stress indicators, and outputs a probability between 0 and 1 that the firm will lose more than 40% of its market cap at some point over the next 12 months. An analyst can then focus their review time on the highest-probability firms. Everything uses free, open data — no Bloomberg, no paid feeds — and every model is a standard statistical regression whose coefficients you can read and argue with, not a black-box neural network.
