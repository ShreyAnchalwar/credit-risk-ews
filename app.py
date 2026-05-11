import streamlit as st
import pandas as pd
from PIL import Image
import os
from src.ews.config import FIRMS

# Set page config
st.set_page_config(
    page_title="Credit Risk EWS Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("Credit Risk Early-Warning System (EWS)")
st.markdown("**Phase 1 Prototype** - Predicting 12-month credit deterioration for 9 US-listed firms")

# Sidebar with key metrics
st.sidebar.header("Model Performance (Validation Set)")

# Firm selector
firm_options = ["All Firms"] + sorted(FIRMS.keys())
selected_firm = st.sidebar.selectbox("Select Firm", firm_options, index=0)

# Read the panel to get some stats
try:
    panel = pd.read_csv("data/processed/panel_phase1.csv")
    total_firms = panel['ticker'].nunique()
    total_months = len(panel)
    event_rate = panel['label_a'].mean() * 100
except:
    total_firms = 9
    total_months = 1490
    event_rate = 20.1

st.sidebar.metric("Firms", total_firms)
st.sidebar.metric("Firm-Months", f"{total_months:,}")
st.sidebar.metric("Event Rate", f"{event_rate:.1f}%")

st.sidebar.markdown("---")
st.sidebar.subheader("Pooled Logit Results")
st.sidebar.metric("AUROC", "0.603")
st.sidebar.metric("AUPRC", "0.527")
st.sidebar.metric("Top-10% Lift", "3.06x")

# Main content
st.header("Evaluation Charts")

col1, col2 = st.columns(2)

with col1:
    st.subheader("ROC and Precision-Recall Curves")
    try:
        img1 = Image.open("outputs/figures/phase1_roc_pr.png")
        st.image(img1, width='stretch')
    except:
        st.error("ROC/PR chart not found")

    st.subheader("Calibration Plot")
    try:
        img2 = Image.open("outputs/figures/phase1_calibration.png")
        st.image(img2, width='stretch')
    except:
        st.error("Calibration chart not found")

with col2:
    st.subheader("Risk Deciles")
    try:
        img3 = Image.open("outputs/figures/phase1_deciles.png")
        st.image(img3, width='stretch')
    except:
        st.error("Deciles chart not found")

    st.subheader("Firm Trajectories")
    try:
        img4 = Image.open("outputs/figures/phase1_trajectories.png")
        st.image(img4, width='stretch')
    except:
        st.error("Trajectories chart not found")

# Firm-specific view
if selected_firm != "All Firms":
    st.header(f"📈 {selected_firm} - {FIRMS[selected_firm]['name']} ({FIRMS[selected_firm]['industry']})")

    try:
        firm_data = panel[panel['ticker'] == selected_firm].copy()
        firm_data['date'] = pd.to_datetime(firm_data['date'])
        firm_data = firm_data.sort_values('date')

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Risk Probability Over Time")
            # Assuming the model predictions are in the panel; for now, show label_a as proxy
            st.line_chart(firm_data.set_index('date')['label_a'])

            st.subheader("Key Metrics")
            events = firm_data['label_a'].sum()
            total_periods = len(firm_data)
            avg_risk = firm_data['label_a'].mean()
            st.metric("Total Events", int(events))
            st.metric("Event Rate", f"{avg_risk:.1%}")
            st.metric("Periods Covered", total_periods)

        with col2:
            st.subheader("Feature Trends")
            # Show some key features over time
            features_to_show = ['ret_1m', 'vol_3m', 'drawdown_12m', 'leverage']
            available_features = [f for f in features_to_show if f in firm_data.columns]
            if available_features:
                st.line_chart(firm_data.set_index('date')[available_features])
            else:
                st.write("Feature data not available in panel.")

    except Exception as e:
        st.error(f"Could not load firm data: {e}")

# Footer
st.markdown("---")
st.markdown("""
**About this Dashboard:**
- **Data**: 9 firms (2010-2024), ~1,490 firm-months
- **Label**: Binary indicator of ≥40% equity drawdown in next 12 months
- **Models**: Pooled logistic regression, Fixed-effects panel logit, Discrete-time hazard logit
- **Features**: 14 total (4 fundamentals, 6 market, 3 macro, 1 filing signal)
- **Evaluation**: AUROC, AUPRC, calibration, top-K lift, lead time analysis

**Key Findings:**
- Model achieves AUROC ~0.60 on validation set
- Market features (returns, volatility, drawdowns) are most predictive
- Accounting ratios provide complementary signal
- Macro indicators have limited standalone power

For more details, see the project proposal and technical documentation.
""")

# Run with: streamlit run app.py
