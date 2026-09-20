import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# تنظیمات صفحه استریم‌لیت
st.set_page_config(page_title="BESS Financial Risk Modeling", page_icon="📊", layout="wide")

st.title("📊 BESS Financial Risk & Bankability Modeling (Germany)")
st.markdown("An interactive tool to evaluate bankability, Debt Service Coverage Ratio (DSCR), and Equity IRR for Battery Energy Storage Systems across different offtake strategies.")

# ---------------------------------------------------------
# Sidebar: Project & Financing Inputs
# ---------------------------------------------------------
st.sidebar.header("⚙️ Project Assumptions")
capex = st.sidebar.number_input("Total CAPEX (€)", value=6_000_000, step=100_000)
opex = st.sidebar.number_input("Annual OPEX (€/year)", value=150_000, step=10_000)
interest_rate = st.sidebar.slider("Bank Interest Rate (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.5) / 100
debt_tenor = st.sidebar.slider("Debt Tenor (Years)", min_value=5, max_value=15, value=10)
lifetime = st.sidebar.slider("Project Lifetime (Years)", min_value=10, max_value=25, value=15)
tax_rate = st.sidebar.slider("Corporate Tax Rate (%)", min_value=10.0, max_value=40.0, value=30.0, step=1.0) / 100

st.sidebar.header("📈 Strategy Revenues & Risk (DSCR)")

merchant_rev = st.sidebar.number_input("Pure Merchant Revenue (€)", value=1_200_000, step=50_000)
merchant_dscr = st.sidebar.slider("Pure Merchant Target DSCR", 1.2, 2.5, 1.75, 0.05)

floor_rev = st.sidebar.number_input("Merchant with Floor Revenue (€)", value=950_000, step=50_000)
floor_dscr = st.sidebar.slider("Merchant with Floor Target DSCR", 1.1, 2.0, 1.40, 0.05)

tolling_rev = st.sidebar.number_input("Tolling Agreement Revenue (€)", value=700_000, step=50_000)
tolling_dscr = st.sidebar.slider("Tolling Agreement Target DSCR", 1.0, 1.8, 1.20, 0.05)

scenarios = {
    "Pure Merchant": {"annual_revenue": merchant_rev, "target_dscr": merchant_dscr},
    "Merchant with Floor": {"annual_revenue": floor_rev, "target_dscr": floor_dscr},
    "Tolling Agreement": {"annual_revenue": tolling_rev, "target_dscr": tolling_dscr}
}

# ---------------------------------------------------------
# Financial Calculations
# ---------------------------------------------------------
def calculate_pv_of_annuity(payment, rate, periods):
    if rate == 0:
        return payment * periods
    return payment * (1 - (1 + rate)**-periods) / rate

results = []
irr_results = []

for name, params in scenarios.items():
    ebitda = params["annual_revenue"] - opex
    tax_estimate = ebitda * tax_rate
    cfads = ebitda - tax_estimate
    
    max_annual_debt_service = cfads / params["target_dscr"]
    debt_size = calculate_pv_of_annuity(max_annual_debt_service, interest_rate, debt_tenor)
    debt_size = min(debt_size, capex)
    gearing = debt_size / capex
    equity_size = capex - debt_size
    
    results.append({
        "Strategy": name,
        "Target DSCR": params["target_dscr"],
        "Annual Revenue (€)": params["annual_revenue"],
        "CFADS (€)": cfads,
        "Max Debt Service (€)": max_annual_debt_service,
        "Debt Capacity (€)": debt_size,
        "Equity Required (€)": equity_size,
        "Gearing Ratio (%)": gearing * 100
    })

    # Cash flows for IRR calculation
    equity_cash_flows = [-equity_size]
    for year in range(1, lifetime + 1):
        if year <= debt_tenor:
            cash_to_equity = cfads - max_annual_debt_service
        else:
            cash_to_equity = cfads
        equity_cash_flows.append(cash_to_equity)
        
    equity_irr = npf.irr(equity_cash_flows)
    cumulative_cf = np.cumsum(equity_cash_flows)
    try:
        payback_year = np.where(cumulative_cf >= 0)[0][0]
    except IndexError:
        payback_year = ">Lifetime"
        
    irr_results.append({
        "Strategy": name,
        "Equity Required (€)": equity_size,
        "Payback Period (Years)": payback_year,
        "Equity IRR (%)": equity_irr * 100
    })

df_results = pd.DataFrame(results)
df_irr = pd.DataFrame(irr_results)

# ترکیب جدول‌ها برای نمایش
df_combined = pd.merge(
    df_results[["Strategy", "Target DSCR", "Annual Revenue (€)", "Gearing Ratio (%)"]], 
    df_irr[["Strategy", "Equity Required (€)", "Payback Period (Years)", "Equity IRR (%)"]], 
    on="Strategy"
)

# ---------------------------------------------------------
# Dashboard Layout
# ---------------------------------------------------------
st.subheader("📋 Financial Performance & Bankability Summary")
st.dataframe(df_combined.style.format({
    "Target DSCR": "{:.2f}x",
    "Annual Revenue (€)": "{:,.0f}",
    "Gearing Ratio (%)": "{:.1f}%",
    "Equity Required (€)": "{:,.0f}",
    "Equity IRR (%)": "{:.2f}%"
}), use_container_width=True)

st.subheader("📊 Bank Debt vs. Investor Return Visualization")

strategies = df_combined["Strategy"].tolist()
irrs = df_combined["Equity IRR (%)"].tolist()
gearings = df_combined["Gearing Ratio (%)"].tolist()

fig, ax1 = plt.subplots(figsize=(10, 5))

color1 = '#1f77b4'
bars = ax1.bar(strategies, gearings, color=color1, alpha=0.7, width=0.4, label='Gearing Ratio (Bank Debt %)')
ax1.set_ylabel('Gearing Ratio (%)', color=color1, fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_ylim(0, 100)
ax1.yaxis.set_major_formatter(mtick.PercentFormatter())

ax2 = ax1.twinx()
color2 = '#d62728'
line = ax2.plot(strategies, irrs, color=color2, marker='o', markersize=8, linewidth=2.5, label='Equity IRR (%)')
ax2.set_ylabel('Equity IRR (%)', color2, fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor=color2)
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

for i, v in enumerate(gearings):
    ax1.text(i, v + 2, f"{v:.1f}%", ha='center', color=color1, fontweight='bold', fontsize=10)
for i, v in enumerate(irrs):
    ax2.text(i, v + 1.5, f"{v:.2f}%", ha='center', color=color2, fontweight='bold', fontsize=10)

plt.title('BESS Bankability: Bank Debt vs. Investor Return', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()

st.pyplot(fig)
