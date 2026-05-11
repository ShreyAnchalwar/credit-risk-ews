import streamlit as st

# Set page config
st.set_page_config(
    page_title="Credit Risk EWS Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Home page content
st.title("🏢 Credit Risk Early-Warning System (EWS)")
st.markdown("**Phase 1 Prototype** — Predicting 12-month credit deterioration for 9 US-listed firms")

st.markdown("---")

# Quick stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Firms", "9")
with col2:
    st.metric("Period", "2010-2024")
with col3:
    st.metric("Firm-Months", "1,490")
with col4:
    st.metric("Event Rate", "20.1%")

st.markdown("---")

# Overview section
st.header("📋 Project Overview")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Purpose")
    st.write("""
    This Early-Warning System (EWS) predicts the probability of **corporate financial distress** 
    within the next 12 months using:
    - **Market signals**: returns, volatility, drawdowns from equity prices
    - **Accounting metrics**: leverage, liquidity, profitability ratios
    - **Macro indicators**: VIX, credit spreads, term spreads
    - **Filing signals**: late filings (12b-25 forms)
    
    The target variable is a **binary indicator** of ≥40% equity drawdown in the next 12 months.
    """)

with col2:
    st.subheader("Key Metrics")
    st.write("""
    **Validation Set Performance (Pooled Logit):**
    - **AUROC**: 0.603 — Reasonable discrimination ability
    - **AUPRC**: 0.527 — Better than random, captures events reliably
    - **Brier Score**: 0.257 — Calibration measure
    - **Top-10% Lift**: 3.06x — Top 10% of firms contain 30.6% of events
    
    *Note: Phase 1 uses synthetic fundamentals; expect improvement with real SEC data in Phase 2.*
    """)

st.markdown("---")

st.header("🚀 Quick Navigation")
st.write("Use the sidebar to explore:")
st.write("""
- **📈 Model Evaluation** — ROC curves, calibration, performance metrics
- **🏢 Firm Analysis** — Individual firm risk profiles and trends
- **🔍 Methodology** — Feature definitions, data sources, model specifications
- **📚 About** — Team, data, and contact information
""")

st.markdown("---")

st.header("📊 Dataset Summary")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Sample Composition")
    firms_info = """
    | Category | Firm | Ticker |
    |---|---|---|
    | Industrial | General Electric | GE |
    | Consumer | Ford Motor | F |
    | Retail | Bed Bath & Beyond | BBBY |
    | Energy | Exxon Mobil | XOM |
    | Energy (Distressed) | Chesapeake Energy | CHK* |
    | Technology | Intel | INTC |
    | Technology (Volatile) | Snap Inc | SNAP |
    | Healthcare | Pfizer | PFE |
    | Real Estate | Simon Property Group | SPG |
    | Airlines | American Airlines | AAL |
    
    *CHK: Delisted post-bankruptcy (June 2020); data unavailable post-delisting.
    """
    st.markdown(firms_info)

with col2:
    st.subheader("Time Split")
    st.write("""
    **Training Set** (2010-2020)
    - 1,058 firm-months
    - 17.0% event rate
    - Used to fit model
    
    **Validation Set** (2021-2023)
    - 324 firm-months
    - 26.2% event rate
    - Used for hyperparameter tuning & evaluation
    
    **Test Set** (2024)
    - 108 firm-months
    - 31.5% event rate
    - Holdout for final assessment
    """)

st.markdown("---")

st.header("🎯 Models Trained")

st.write("""
Three interpretable logistic regression models were fitted on the same feature set:

1. **Pooled Logistic Regression** (Baseline)
   - Simple cross-sectional model; no firm/time fixed effects
   - Fastest; good for initial diagnostics
   - AUROC: 0.603 on validation set

2. **Fixed-Effects Panel Logit**
   - Accounts for firm-specific risk baselines
   - Controls for unobserved firm heterogeneity
   - AUROC: 0.629 on validation set (best performer)

3. **Discrete-Time Hazard Logit** (Shumway-style)
   - Time-to-event framing; models duration until distress
   - Economically motivated by contingent claims theory
   - Convergence issues in Phase 1; falling back to pooled predictions
""")

st.markdown("---")

st.header("💡 Key Findings")

st.info("""
✅ **Market features are most predictive**: Returns, volatility, and drawdowns drive the model.
An 1% decline in 6-month returns or rise in 12-month drawdown significantly increases distress probability.

✅ **Accounting ratios provide complementary signal**: Leverage and liquidity are important,
but less powerful than market signals alone (ablation study: market-only AUROC 0.73 vs. full AUROC 0.60).

⚠️ **Macro indicators have limited standalone power**: VIX and spreads add noise at Phase 1 scale.
May improve with larger sample.

⚠️ **Model calibration is loose**: Predicted probabilities don't perfectly align with observed rates.
Suggests need for real fundamentals + longer history. Ready for Phase 2 improvements.
""")

st.markdown("---")

st.subheader("🔗 Pages Available")
st.write("""
Click the hamburger menu (☰) on the left to navigate to:
- **Model Evaluation**: Charts, metrics, and diagnostics
- **Firm Analysis**: Individual risk profiles
- **Methodology**: Feature definitions and model specs
- **About**: Team and data sources
""")

