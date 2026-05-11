**Next Action:**

- Pick 10 firms (stable but then distressed) across sectors except for financial sector

| **Category**               | **Firm**                       | **Rationale for inclusion**                                                           |
| -------------------------- | ------------------------------ | ------------------------------------------------------------------------------------- |
| **Industrial cyclicals**   | **General Electric (GE)**      | Long history of leverage cycles and restructuring; good for stress-pattern detection. |
| ---                        | ---                            | ---                                                                                   |
| **Consumer discretionary** | **Ford Motor (F)**             | High sensitivity to macro and credit conditions; frequent drawdowns.                  |
| ---                        | ---                            | ---                                                                                   |
| **Retail**                 | **Bed Bath & Beyond (BBBY)**   | Bankruptcy case study; perfect for Label B validation.                                |
| ---                        | ---                            | ---                                                                                   |
| **Energy**                 | **Exxon Mobil (XOM)**          | Stable blue-chip baseline; contrasts with distressed peers.                           |
| ---                        | ---                            | ---                                                                                   |
| **Energy (distressed)**    | **Chesapeake Energy (CHK)**    | Filed for bankruptcy 2020; strong hazard-model benchmark.                             |
| ---                        | ---                            | ---                                                                                   |
| **Technology**             | **Intel (INTC)**               | Representative of large-cap tech with cyclical earnings; low distress baseline.       |
| ---                        | ---                            | ---                                                                                   |
| **Technology (volatile)**  | **Snap Inc (SNAP)**            | High market volatility; useful for Label A sensitivity testing.                       |
| ---                        | ---                            | ---                                                                                   |
| **Healthcare**             | **Pfizer (PFE)**               | Defensive sector; helps test false-positive control.                                  |
| ---                        | ---                            | ---                                                                                   |
| **Real Estate**            | **Simon Property Group (SPG)** | REIT structure; captures leverage and liquidity dynamics.                             |
| ---                        | ---                            | ---                                                                                   |
| **Airlines**               | **American Airlines (AAL)**    | High exposure to macro shocks; multiple drawdowns; good for trajectory visualization. |
| ---                        | ---                            | ---                                                                                   |

- **Task assignment:**

| **Member**           | **Responsibility**                  | **Key outputs**                                                         |
| -------------------- | ----------------------------------- | ----------------------------------------------------------------------- |
| Vincent Hui Fai Wong | Integration, scope control, writing | proposal/report integration; narrative consistency; oral defense        |
| ---                  | ---                                 | ---                                                                     |
| Allen                | SEC fundamentals                    | companyfacts extraction; ratio construction; filing-date carry-forward  |
| ---                  | ---                                 | ---                                                                     |
| Shrey                | Market features                     | yfinance extraction; rolling returns/vol/drawdowns; monthly aggregation |
| ---                  | ---                                 | ---                                                                     |
| Darren               | Labels & filing signals             | Label A construction; 12b-25 late filing signals; 8-K Item 1.03 mapping |
| ---                  | ---                                 | ---                                                                     |
| Ivan                 | Econometrics & evaluation           | pooled/FE/hazard logit; metrics; calibration; robustness                |
| ---                  | ---                                 | ---                                                                     |

**Variables/features table**

**Table 1. Variables and features (minimal, interpretable set)**

| **Feature group** | **Variable / feature**        | **Source**                 | **Native frequency** | **Panel frequency** | **Calculation / notes**                                          |
| ----------------- | ----------------------------- | -------------------------- | -------------------- | ------------------- | ---------------------------------------------------------------- |
| Fundamentals      | Total assets (TA)             | SEC XBRL (companyfacts)    | Q/A                  | Monthly             | Last available as of (t), carry-forward by filing date           |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Fundamentals      | Total liabilities (TL)        | SEC XBRL                   | Q/A                  | Monthly             | Carry-forward                                                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Fundamentals      | Cash & equivalents            | SEC XBRL                   | Q/A                  | Monthly             | Carry-forward                                                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Fundamentals      | Current assets (CA)           | SEC XBRL                   | Q/A                  | Monthly             | Carry-forward                                                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Fundamentals      | Current liabilities (CL)      | SEC XBRL                   | Q/A                  | Monthly             | Carry-forward                                                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Fundamentals      | Operating income (EBIT proxy) | SEC XBRL                   | Q/A                  | Monthly             | TTM if feasible; else annualized last quarter (assumption)       |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Ratios            | Leverage                      | Derived                    | -                    | Monthly             | (TL/TA)                                                          |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Ratios            | Liquidity buffer              | Derived                    | -                    | Monthly             | (Cash/TA)                                                        |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Ratios            | Working-capital ratio         | Derived                    | -                    | Monthly             | ((CA-CL)/TA)                                                     |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Ratios            | Profitability                 | Derived                    | -                    | Monthly             | (EBIT/TA)                                                        |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Market            | 1m / 3m / 6m return           | yfinance                   | Daily                | Monthly             | Rolling cumulative return ending at month-end                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Market            | 3m / 6m realized volatility   | yfinance                   | Daily                | Monthly             | Std. dev. of daily returns in rolling windows                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Market            | 12m backward drawdown         | yfinance                   | Daily                | Monthly             | Peak-to-trough over prior 252 trading days                       |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Market            | Idiosyncratic volatility      | Derived + market index     | Daily                | Monthly             | Residual volatility from rolling regression (Shumway motivation) |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Filing signals    | Late filing flag              | SEC Form 12b-25            | Event                | Monthly             | Indicator: any 12b-25 filing within last 6 months                |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Macro             | VIX                           | FRED VIXCLS                | Daily                | Monthly             | Month-avg or month-end VIX                                       |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Macro             | Term spread                   | FRED yields (10Y, 2Y)      | Daily                | Monthly             | Month-avg (10Y-2Y)                                               |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Macro             | Credit conditions proxy       | FRED corporate yield (BAA) | Daily/Monthly        | Monthly             | Month-avg BAA or spread proxy                                    |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |
| Benchmark         | Altman Z-score                | Derived                    | Mixed                | Monthly             | Computed where inputs available; benchmark comparison            |
| ---               | ---                           | ---                        | ---                  | ---                 | ---                                                              |

**Meeting Minutes:**

| **Date (2026)** | **Assessment milestone**      | **Deliverables**                                                                 |
| --------------- | ----------------------------- | -------------------------------------------------------------------------------- |
| Mar 10          | Detailed Project Proposal     | Final proposal; finalized scope; variable/label specification; risk plan         |
| ---             | ---                           | ---                                                                              |
| Apr 24          | Progress Update 1             | Toy pipeline (10 firms, shorter horizon); Label A; pooled logit with time split  |
| ---             | ---                           | ---                                                                              |
| May 5           | Progress Update 2             | Full pipeline (~60-80 firms, 2010-2025); ablation baselines; preliminary metrics |
| ---             | ---                           | ---                                                                              |
| Jun 1           | Interim Report & Presentation | Interim report + slides: calibrated scores, top-K lift, lead-time examples       |
| ---             | ---                           | ---                                                                              |
| Jun 16          | Progress Update 3             | FE logit + hazard logit; filing signals; Label B mapping                         |
| ---             | ---                           | ---                                                                              |
| Jul 6           | Progress Update 4             | Robustness: threshold sensitivity; rolling windows; final model selection        |
| ---             | ---                           | ---                                                                              |
| Jul 13          | Project Webpage               | Webpage with pipeline, results, reproducibility instructions                     |
| ---             | ---                           | ---                                                                              |
| Jul 17          | Project Report                | Final report + appendices (data dictionary, leakage checks)                      |
| ---             | ---                           | ---                                                                              |
| End of Jul      | Oral Examination              | Final deck; Q&A notes; limitations/assumptions defense                           |
| ---             | ---                           | ---                                                                              |

## **Phase 1 (Now → April 24) - First Milestone**

Lecturer is looking for,

**The specific objectives of your work**

To build an **interpretable early credit warning system (EWS)** using open, publicly available data.

The specific objectives are:

- **Develop a predictive model** that estimates the probability of corporate financial distress within 12 months, based on **accounting** and **market** signals.
- **Integrate market‑based indicators** (returns, volatility, distance‑to‑default) with traditional financial ratios to capture early signs of deterioration.
- **Ensure reproducibility** by using open data sources (e.g., SEC EDGAR JSON/XBRL) instead of paid databases.
- **Evaluate model performance** in identifying high‑risk firms before deterioration occurs, focusing on interpretability and transparency.
- **Provide a scalable framework** that can be extended to other markets or integrated into bank‑level credit monitoring systems.

**Feasibility analysis of the proposed work**

- **Data availability:** **SEC EDGAR** provides structured, **machine‑readable filings** and **API**s, ensuring reliable access to **financial data.**
- **Technical feasibility:** **Logistic** and **hazard models** are well‑established and can be implemented using **Python** or **R** with standard libraries.
- **Computational feasibility:** **The dataset size (public firms) is manageable** on a standard workstation; no high‑performance computing is required.
- **Time feasibility:** The project can be completed within one semester, as the model structure and data pipeline are modular.
- **Research feasibility:** The theoretical foundation **(Altman, Ohlson, Shumway, Merton)** is academically validated, reducing conceptual risk.

Potential challenges include data cleaning and aligning quarterly accounting data with daily market signals, but these are solvable with standard preprocessing techniques.

A concrete plan for the next stages of your project.

**By April 24**, we need to show that we can build a simple model,

- We have started collecting data
- We understand how the system works
- We can produce a **basic working version(may not have time but we will work on the data part first)**

Think of this as a **prototype**, not the final product.

What we aim to have:

- A small sample of companies (10 firms - we may focus on single/few sectors only given the size of our samples are small, only 80 firms)
- Some basic data ready (prices, simple indicators)
- A simple model that gives some result
- Even if it's not perfect - it just needs to work

## **Phase 2 (April 24 → May 5)**

"After the first milestone, we expand everything.

- Increase to full number of companies
- Clean and organize the data properly
- Improve the model
- Start getting more reliable results

This is where things become more complete and structured."

## **Phase 3 (May → Early June)**

"This is the improvement stage.

- Test different settings (like −30% vs −40%) - avoid stock with manipulation
- Make sure results are stable
- Improve explanation (why model works)
- Prepare charts and findings

Basically: make our work look more professional and solid."

## **Phase 4 (June → July)**

"Final stage:

- Write report
- Prepare presentation
- Build simple webpage
- Prepare for oral exam

This is more about explaining our work clearly."