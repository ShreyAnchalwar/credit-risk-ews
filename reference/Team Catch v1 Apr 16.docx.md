

| Project Title: | Early Credit Risk Warning system |
| :---- | :---- |
| **Mentor:** | **Yi Chen** |
| **Student 1 (Leader)** | **Hui Fai Wong** |
| **Student 2** |  **Anchalwar Shrey Sanjay** |
| **Student 3** |  **Fung Tat Ki** |
| **Student 4** |  **Chow Pak Ho** |
| **Student 5** |  **Yu Yuk Lam Allen** |

**Aim**

| The project aims to design, implement, and rigorously validate a fully reproducible and highly interpretable Credit Risk Early-Warning System (EWS) for approximately 60–80 US-listed non-financial firms over the period 2010–2025. Using only open-source public data sources (SEC EDGAR JSON APIs, yfinance, and FRED), the system will generate a monthly firm-level probability score indicating the likelihood of credit deterioration within the next 12 months. In addition, it will produce a dynamic risk-trajectory dashboard to support analyst monitoring, watchlist creation, and escalation triage. The EWS is explicitly not intended for trading or investment decisions; its focus is practical credit-risk oversight. Grounded in canonical academic literature (Altman 1968, Ohlson 1980, Shumway 2001, with optional Merton 1974 structSural intuition), the project emphasises mixed-frequency signals that capture weakening fundamentals and market stress between quarterly reporting dates. All components—data pipeline, feature engineering, model estimation, and evaluation—will be fully transparent, time-consistent, and free of look-ahead bias, delivering an MSc-level contribution that is both academically rigorous and operationally actionable for credit analysts and risk teams.  |
| :---- |

**Brief Literature Review**

|  Credit deterioration is rarely a sudden single-day event; it is a dynamic process typically preceded by deteriorating accounting fundamentals (leverage, liquidity, profitability) and rising forward-looking market stress signals (equity drawdowns, volatility spikes, and macro funding pressures). The foundational academic literature provides a clear roadmap for building an interpretable early-warning system.  Altman (1968) — The Z-Score Model Paper: *Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy* Core idea: Uses multivariate discriminant analysis to combine accounting ratios (working capital, retained earnings, EBIT, market value of equity, total assets, sales) into a single Z-score predicting bankruptcy. Impact: First statistically validated bankruptcy-prediction model; still used by credit analysts and regulators. Limitation: Static, assumes linear separability and constant coefficients across time. Ohlson (1980) — The O-Score Model Paper: *Financial Ratios and the Probabilistic Prediction of Bankruptcy* Core idea: Introduces logistic regression to estimate the *probability* of default rather than a discriminant boundary. Variables: Size, leverage, liquidity, performance, and dummy indicators for negative earnings and insolvency. Advances: Probabilistic interpretation (0–1 likelihood). Handles non-normal distributions better than Altman’s linear discriminant. Easier to update with new data. Shumway (2001) — Hazard-Model Approach Paper: *Forecasting Bankruptcy More Accurately: A Simple Hazard Model* Core idea: Applies survival analysis (hazard models) to bankruptcy prediction. Innovation: Treats bankruptcy as a *time-to-event* process. Incorporates both accounting and market-based variables (stock returns, volatility). Allows dynamic updating each period. Impact: Became the standard for modern early-warning systems and credit-risk analytics. Recent practical challenges—namely the quarterly or annual release of core accounting data—underscore the need for higher-frequency market and macro signals that can detect adverse changes between filing dates. By combining these classic frameworks with strictly open-data sources, the project addresses a timely gap: delivering a reproducible, transparent EWS that satisfies both academic standards and real-world credit-monitoring requirements without reliance on proprietary databases.  |
| :---- |

**Proposed Methodology**

| All inputs are obtained exclusively from public, open-access platforms: SEC EDGAR RESTful JSON APIs for submissions history, extracted XBRL facts, filing dates, and SIC codes (used for industry filtering and fixed effects). yfinance library for daily equity prices to construct rolling return, volatility, and drawdown features. FRED API series (VIXCLS, Treasury yields, BAA corporate yields) for macro and stress indicators. SEC filing metadata for two targeted signals: Form 12b-25 (late-filing flag) and Form 8-K Item 1.03 (bankruptcy or receivership benchmark). The sample comprises \~60–80 US-listed non-financial firms (SIC-filtered, optionally excluding utilities for robustness), observed monthly from January 2010 to December 2025\. This yields approximately 15,360 firm-month observations after excluding the final 12 months for forward-label construction. Firms are selected via the SEC’s official ticker-CIK mapping files, requiring minimum data coverage (≥8 years of prices and ≥8 quarters of fundamentals) and stratified across 2-digit SIC groups to avoid sector concentration. Deterioration Labels (Dual-Definition Design) Label A (Primary – Market-Implied): A firm-month is labelled as deterioration if the equity price experiences a peak-to-trough drawdown of ≥40 % over the subsequent 12 months (robustness tested at –30 % and –50 % thresholds). Label B (Secondary – High-Precision Event Benchmark): An SEC Form 8-K Item 1.03 “Bankruptcy or Receivership” is filed within the next 12 months (detected via automated parsing of filing text/headers and validated on a hand-checked subset). Features (Minimal, Interpretable Set) The feature set is deliberately concise and economically meaningful (see full variable table in the detailed proposal): Fundamentals (carry-forward after filing date): Total assets, liabilities, cash, current assets/liabilities, operating income. Ratios: Leverage (TL/TA), liquidity buffer (Cash/TA), working-capital ratio, profitability (EBIT/TA), Altman Z-score benchmark. Market Signals: 1-/3-/6-month cumulative returns, 3-/6-month realised volatility, 12-month backward drawdown, idiosyncratic volatility (residual from market regression). Filing Signals: Late-filing indicator (any Form 12b-25 in prior 6 months). Macro/Stress Controls: Month-end or average VIX, term spread (10Y–2Y), BAA credit-spread proxy. All features are constructed with strict no-look-ahead rules: fundamentals are aligned to filing dates and carried forward; market and macro series are aggregated to month-end using only information available at t. Econometric Models (All Interpretable) Pooled logistic regression (baseline, Ohlson-style). Fixed-effects panel logit (SIC industry \+ month fixed effects). Discrete-time hazard logit (Shumway-style risk-set approach, conditioning on survival until t–1). (Optional under time constraints: simplified Merton-style distance-to-default proxy as an additional covariate.) Validation, Evaluation and Explainability Primary validation: Time-based splits (train 2010–2020; validation 2021–2023; test 2024–2025). Robustness: Rolling/expanding windows and threshold sensitivity checks. Metrics: AUROC, AUPRC (class-imbalance aware), Brier score (calibration), top-K lift/capture rates, and lead-time analysis. Inference: Time-clustered standard errors plus month fixed effects to address cross-sectional dependence. Explainability deliverables: Odds-ratio tables, marginal effects, probability calibration curves, reliability plots, and risk-decile event-rate monitoring for actionable watchlist logic. No black-box or deep-learning methods are employed; SHAP values are considered only for optional secondary benchmarks.  |
| :---- |

**Terms and theories:**

### **SEC EDGAR JSON/XBRL**

* **EDGAR** is the U.S. Securities and Exchange Commission’s online database where public companies upload their financial reports (like balance sheets and income statements).  
* **JSON/XBRL** are *data formats* that make those reports machine‑readable.  
  * **JSON** (JavaScript Object Notation) is a simple text format computers can easily process.  
  * **XBRL** (eXtensible Business Reporting Language) is a special format for financial data — it tags each number (e.g., “Revenue”, “Total Assets”) so software can understand what it means.  
* In your project, you use these formats to **automatically collect and clean company data** instead of typing numbers manually.

### **Logistic and Hazard Models**

These are two common ways to predict whether something will happen — in your case, whether a company will face financial distress.

**Logistic model:**  

Think of it as a yes/no prediction. It estimates the *probability* that a company will fail within a certain time (e.g., next 12 months).

* Example: “There’s a 30% chance this firm will default.”

**Hazard model:**  

This one looks at *when* the event might happen. It’s often used in survival analysis — like predicting how long a company can “survive” before distress occurs.

* Example: “The risk of default increases sharply after month 9.”

Together, they help you build a **timeline of risk**, not just a single score.

| Researcher | Year | Main Idea |
| :---- | :---- | :---- |
| Altman (1968) | Developed the Z‑Score, combining financial ratios (profitability, leverage,   liquidity) to predict bankruptcy. | Gives you a simple baseline model using   accounting data. |
| Ohlson (1980) | Used logistic regression to improve prediction accuracy and include more variables   (size, liquidity, performance). | Introduces the idea of probability‑based   distress prediction. |
| Shumway (2001) | Added time dimension — showing that risk changes over time and combining market   data (returns, volatility) with accounting data. | Supports your mixed‑frequency approach   (quarterly \+ daily signals). |
| Merton (1974) | Created the distance‑to‑default concept using stock prices and debt levels to measure how   close a firm is to failing. | Gives you a market‑based early warning   indicator. |

## **Phase 1 (Now → April 24\) — First Milestone**

Lecturer is looking for, 

The specific objectives of your work  
To build an **interpretable early credit warning system (EWS)** using open, publicly available data.

The specific objectives are:

1. **Develop a predictive model** that estimates the probability of corporate financial distress within 12 months, based on accounting and market signals.  
2. **Integrate market‑based indicators** (returns, volatility, distance‑to‑default) with traditional financial ratios to capture early signs of deterioration.  
3. **Ensure reproducibility** by using open data sources (e.g., SEC EDGAR JSON/XBRL) instead of paid databases.  
4. **Evaluate model performance** in identifying high‑risk firms before deterioration occurs, focusing on interpretability and transparency.  
5. **Provide a scalable framework** that can be extended to other markets or integrated into bank‑level credit monitoring systems.

 Feasibility analysis of the proposed work

1. **Data availability:** SEC EDGAR provides structured, machine‑readable filings and APIs, ensuring reliable access to financial data.  
2. **Technical feasibility:** Logistic and hazard models are well‑established and can be implemented using Python or R with standard libraries.  
3. **Computational feasibility:** The dataset size (public firms) is manageable on a standard workstation; no high‑performance computing is required.  
4. **Time feasibility:** The project can be completed within one semester, as the model structure and data pipeline are modular.  
5. **Research feasibility:** The theoretical foundation (Altman, Ohlson, Shumway, Merton) is academically validated, reducing conceptual risk.  
   Potential challenges include data cleaning and aligning quarterly accounting data with daily market signals, but these are solvable with standard preprocessing techniques.

A concrete plan for the next stages of your project.

**By April 24**, we need to show that we can build a simple model, 

* We have started collecting data  
* We understand how the system works  
* We can produce a **basic working version**

Think of this as a **prototype**, not the final product.

What we aim to have:

* A small sample of companies (10 firms \- we may focus on single/few sectors only given the size of our samples are small, only 80 firms)  
* Some basic data ready (prices, simple indicators)  
* A simple model that gives some result  
* Even if it’s not perfect — it just needs to work

| Stage | Description | Target Timeframe |
| :---- | :---- | :---- |
| Stage 1: Data Collection   & Cleaning | Extract JSON/XBRL data from EDGAR; align   accounting and market variables. | Weeks 1–3 |
| Stage 2: Feature Engineering | Construct financial ratios, volatility measures,   and distance‑to‑default proxies. | Weeks 4–5 |
| Stage 3: Model Development | Implement logit and hazard models; test   interpretability and predictive accuracy. | Weeks 6–8 |
| Stage 4: Validation &   Benchmarking | Compare with Altman and Ohlson benchmarks;   evaluate early‑warning lift. | Weeks 9–10 |
| Stage 5: Documentation &   Visualization | Prepare final report, charts, and reproducible   code pipeline. | Weeks 11–12   |

##  **Phase 2 (April 24 → May 5\)**

“After the first milestone, we expand everything.

* Increase to full number of companies  
* Clean and organize the data properly  
* Improve the model  
* Start getting more reliable results

 This is where things become more complete and structured.”

---

## **Phase 3 (May → Early June)**

“This is the improvement stage.

* Test different settings (like −30% vs −40%)  
* Make sure results are stable  
* Improve explanation (why model works)  
* Prepare charts and findings

Basically: make our work look more professional and solid.”

---

##  **Phase 4 (June → July)**

“Final stage:

* Write report  
* Prepare presentation  
* Build simple webpage  
* Prepare for oral exam

This is more about explaining our work clearly.”

