# 🚀 Running the EWS Dashboard Locally

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# (If Streamlit not in requirements.txt, install it)
pip install streamlit
```

## Running the Dashboard

### **Option 1: Solo Demo on Your PC**
```bash
cd C:\Users\shrey\Dev\credit-risk-ews
streamlit run streamlit_app.py
```
- Opens at `http://localhost:8501`
- Only accessible on your machine
- Use for personal testing

### **Option 2: Share with Team on Local Network**
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```
- Shows local IP: `http://YOUR_IP:8501`
- Others on your network can access (if firewall allows)
- Great for in-person demo before meeting

### **Option 3: Share with Others (Remote)**
```bash
# Create free Streamlit Cloud deployment
# (See docs/DEPLOYMENT.md)
```

## Dashboard Structure

```
📊 Home (streamlit_app.py)
├── 📈 Model Evaluation (pages/1_Model_Evaluation.py)
│   ├── ROC & PR Curves
│   ├── Calibration Plot
│   ├── Risk Deciles
│   ├── Firm Trajectories
│   └── Ablation Study
├── 🏢 Firm Analysis (pages/2_Firm_Analysis.py)
│   ├── Firm Selector
│   ├── Risk Timeline
│   ├── Market Features Trends
│   └── Accounting Metrics
├── 🔍 Methodology (pages/3_Methodology.py)
│   ├── Data Pipeline
│   ├── Feature Definitions
│   ├── Model Specs
│   └── Evaluation Metrics
└── 📚 About (pages/4_About.py)
    ├── Team
    ├── Data Sources
    ├── Tech Stack
    └── Roadmap
```

## Troubleshooting

**Q: "streamlit: command not found"**
A: Install Streamlit: `pip install streamlit`

**Q: Images not loading**
A: Run the pipeline first: `python src/run.py`
   This generates outputs/figures/*.png

**Q: Module import errors**
A: Ensure you're in the correct directory:
   `cd C:\Users\shrey\Dev\credit-risk-ews`
   And virtual environment is activated: `.venv\Scripts\activate`

**Q: App reloads when I select a firm**
A: Normal Streamlit behavior (full re-run). Cache may improve this in Phase 2.

## For Your Supervisor Meeting

**Local Demo:**
1. Run: `streamlit run streamlit_app.py`
2. Open link in browser (or share `http://YOUR_IP:8501` if on same network)
3. Walk through pages:
   - **Home**: Overview & key metrics
   - **Model Evaluation**: Show AUROC 0.603, explain ablation
   - **Firm Analysis**: Pick BBBY, walk through distress period
   - **Methodology**: Explain no-lookahead, feature definitions

## Files Modified/Created for Multi-Page App

```
New:
├── streamlit_app.py         # Home page (replaces app.py)
└── pages/
    ├── 1_Model_Evaluation.py
    ├── 2_Firm_Analysis.py
    ├── 3_Methodology.py
    └── 4_About.py

Legacy (still works):
└── app.py                    # Single-page version (can be deleted after demo)
```

## Next Steps

**Before Meeting (May 14):**
- [ ] Test dashboard locally
- [ ] Verify all 4 pages load
- [ ] Check firm selection works (Firm Analysis page)
- [ ] Note any slow loads (optimize if needed)

**After Meeting (May 15+):**
- [ ] Deploy to Streamlit Cloud (free tier)
- [ ] Get permanent public link
- [ ] Share with team for feedback

Good luck! 🚀

