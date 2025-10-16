
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# -----------------------------
# Brand Palette (Edelweiss Life)
# -----------------------------
PRIMARY_BLUE = "#034EA2"   # Edelweiss Blue
ACCENT_ORANGE = "#F79421"  # Edelweiss Orange
BG_LIGHT = "#F9FAFB"
TEXT_DARK = "#1F2937"

# Inject minimal CSS to align accents (buttons, sliders, headers)
BRAND_CSS = f"""
<style>
:root {{
    --primary: {PRIMARY_BLUE};
    --accent: {ACCENT_ORANGE};
    --text: {TEXT_DARK};
}}
/* Headings */
h1, h2, h3, h4, h5, h6 {{
    color: var(--primary);
}}
/* Buttons */
.stButton>button {{
    background: var(--primary);
    color: white;
    border-radius: 8px;
    border: none;
}}
.stButton>button:hover {{
    background: #023b7b;
}}
/* Slider accent */
.stSlider [data-baseweb="slider"] > div > div {{
    background: var(--primary);
}}
/* Metric delta label tweak */
.gray-badge {{
    display:inline-block;
    padding:2px 8px;
    border-radius: 999px;
    background: #E5E7EB;
    color: #111827;
    font-size: 0.85rem;
    margin-left: .5rem;
}}
.status-pill {{
    display:inline-block;
    padding:4px 10px;
    border-radius: 999px;
    font-weight:600;
    color: white;
}}
.status-ok {{ background: var(--primary); }}
.status-warn {{ background: var(--accent); }}
</style>
"""

# -----------------------------
# Helpers
# -----------------------------

def rupee(x: float) -> str:
    """Format number in Indian numbering style with ₹ symbol."""
    if pd.isna(x):
        return "₹0"
    x_int = int(round(x))
    s = str(x_int)
    if len(s) <= 3:
        out = s
    else:
        last3 = s[-3:]
        other = s[:-3]
        groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:])
            other = other[:-2]
        if other:
            groups.insert(0, other)
        out = ",".join(groups + [last3])
    return f"₹{out}"

def fv(rate: float, nper: int, pmt: float, pv: float, when: str = "end") -> float:
    """Future value with periodic compounding."""
    when_val = 1 if when == "begin" else 0
    if rate == 0:
        return pv + pmt * nper
    return pv * (1 + rate) ** nper + pmt * (1 + rate * when_val) * (((1 + rate) ** nper - 1) / rate)

def years_until_fi(
    current_age: int,
    current_corpus: float,
    start_monthly_sip: float,
    pre_ret_annual_return: float,
    income_growth: float,
    sip_growth: float,
    target_corpus_func,
    inflation: float,
    current_monthly_expense: float,
    max_age: int = 80,
) -> Tuple[int, float, pd.DataFrame]:
    """Simulate until corpus >= target corpus."""
    records = []
    age = current_age
    corpus = current_corpus
    monthly_rate = (1 + pre_ret_annual_return) ** (1/12) - 1

    months = 0
    reached = None

    while age <= max_age:
        years_from_now = months / 12
        future_monthly_expense = current_monthly_expense * ((1 + inflation) ** years_from_now)
        future_annual_expense = future_monthly_expense * 12
        required_corpus = target_corpus_func(years_from_now, future_annual_expense)

        if corpus >= required_corpus:
            reached = (current_age + int(months // 12), corpus)
            records.append({
                "Age": current_age + months/12,
                "Invested Corpus": corpus,
                "Required Corpus": required_corpus,
            })
            break

        corpus = fv(monthly_rate, 1, start_monthly_sip, corpus, when="end")
        months += 1
        if months % 12 == 0:
            age = current_age + months // 12
            start_monthly_sip *= (1 + sip_growth)

        if months % 6 == 0:
            records.append({
                "Age": current_age + months/12,
                "Invested Corpus": corpus,
                "Required Corpus": required_corpus,
            })

    if reached is None:
        reached = (max_age, corpus)

    df = pd.DataFrame(records)
    return reached[0], reached[1], df

# -----------------------------
# App
# -----------------------------

st.set_page_config(page_title="FIRE Calculator (Edelweiss Theme)", page_icon="🔥", layout="wide")
st.markdown(BRAND_CSS, unsafe_allow_html=True)

st.title("🔥 FIRE Calculator — Financial Independence, Retire Early")
st.caption("Edelweiss-themed • Lean / Barista / Fat • Income-aware • Inflation & SWR • Coast-FIRE")

with st.sidebar:
    st.header("Inputs")

    col_age = st.columns(2)
    with col_age[0]:
        current_age = st.number_input("Current age", min_value=18, max_value=70, value=30, step=1)
    with col_age[1]:
        target_age = st.number_input("Target FIRE age", min_value=current_age+1, max_value=80, value=45, step=1)

    st.subheader("Earnings & Spending (Monthly, ₹)")
    monthly_income = st.number_input("Monthly take-home income (₹)", min_value=0.0, value=150000.0, step=5000.0, format="%.2f")
    monthly_expense = st.number_input("Monthly living expenses, today (₹)", min_value=0.0, value=80000.0, step=5000.0, format="%.2f")

    st.subheader("Investments")
    current_corpus = st.number_input("Current invested corpus (₹)", min_value=0.0, value=1000000.0, step=50000.0, format="%.2f")

    sip_mode = st.radio("SIP input mode", ["Fixed monthly SIP", "SIP as % of income"], index=0, horizontal=True)

    if sip_mode == "Fixed monthly SIP":
        monthly_sip = st.number_input("Monthly SIP (₹)", min_value=0.0, value=30000.0, step=5000.0, format="%.2f")
    else:
        sip_pct = st.slider("SIP as % of income", min_value=0, max_value=80, value=30, step=1)
        monthly_sip = monthly_income * sip_pct/100.0

    st.subheader("Rates & Assumptions (Annual)")
    inflation = st.slider("Inflation (₹ expenses)", min_value=0.0, max_value=10.0, value=6.0, step=0.25) / 100.0
    income_growth = st.slider("Income growth", min_value=0.0, max_value=20.0, value=8.0, step=0.25) / 100.0
    sip_growth_choice = st.radio("SIP Growth", ["Track income growth", "Custom"], horizontal=True, index=0)
    if sip_growth_choice == "Track income growth":
        sip_growth = income_growth
    else:
        sip_growth = st.slider("SIP growth (annual)", min_value=0.0, max_value=30.0, value=8.0, step=0.25) / 100.0

    pre_ret_return = st.slider("Expected return pre-FIRE (annual)", min_value=0.0, max_value=20.0, value=11.0, step=0.25) / 100.0
    post_ret_return = st.slider("Expected return post-FIRE (annual)", min_value=0.0, max_value=12.0, value=7.0, step=0.25) / 100.0
    swr = st.slider("Safe Withdrawal Rate", min_value=2.5, max_value=5.0, value=4.0, step=0.1) / 100.0

    st.subheader("FIRE Type")
    fire_type = st.selectbox("Select mode", ["Lean FIRE", "Barista FIRE", "Fat FIRE"], index=1)

    if fire_type == "Lean FIRE":
        lean_mult = st.slider("Lean lifestyle multiplier (vs. baseline)", min_value=0.5, max_value=1.0, value=0.8, step=0.05)
        barista_cover = 0.0
        fat_mult = 1.0
    elif fire_type == "Barista FIRE":
        barista_cover = st.slider("Part-time income covers % of expenses", min_value=10, max_value=80, value=40, step=5) / 100.0
        lean_mult = 1.0
        fat_mult = 1.0
    else:  # Fat
        fat_mult = st.slider("Fat lifestyle multiplier (vs. baseline)", min_value=1.0, max_value=2.5, value=1.5, step=0.1)
        barista_cover = 0.0
        lean_mult = 1.0

    st.subheader("Toggles")
    show_coast = st.toggle("Show Coast-FIRE check (no further contributions)", value=True)
    show_table = st.toggle("Show yearly table", value=True)

# Derived values
years_to_target = target_age - current_age
future_monthly_expense = monthly_expense * ((1 + inflation) ** years_to_target)
future_annual_expense = future_monthly_expense * 12

if fire_type == "Lean FIRE":
    adjusted_annual_expense = future_annual_expense * lean_mult
elif fire_type == "Barista FIRE":
    adjusted_annual_expense = future_annual_expense * (1 - barista_cover)
else:
    adjusted_annual_expense = future_annual_expense * fat_mult

required_corpus = adjusted_annual_expense / swr

monthly_rate = (1 + pre_ret_return) ** (1/12) - 1
n_months = years_to_target * 12

sip_schedule = np.full(n_months, monthly_sip, dtype=float)
if n_months > 0:
    for m in range(12, n_months, 12):
        sip_schedule[m:] *= (1 + sip_growth)

corpus = current_corpus
for m in range(n_months):
    corpus = fv(monthly_rate, 1, sip_schedule[m], corpus, when="end")
projected_corpus_at_target = corpus

def target_corpus_func(years_from_now: float, future_annual_exp: float) -> float:
    if fire_type == "Lean FIRE":
        expense = future_annual_exp * lean_mult
    elif fire_type == "Barista FIRE":
        expense = future_annual_exp * (1 - barista_cover)
    else:
        expense = future_annual_exp * fat_mult
    return expense / swr

age_reached, corpus_when_reached, traj_df = years_until_fi(
    current_age=current_age,
    current_corpus=current_corpus,
    start_monthly_sip=monthly_sip,
    pre_ret_annual_return=pre_ret_return,
    income_growth=income_growth,
    sip_growth=sip_growth,
    target_corpus_func=target_corpus_func,
    inflation=inflation,
    current_monthly_expense=monthly_expense,
    max_age=80
)

def coast_required(years_from_now: float, future_annual_exp: float) -> float:
    return target_corpus_func(years_from_now, future_annual_exp)

def coast_check(current_corpus, pre_ret_return, current_age):
    corpus = current_corpus
    months = 0
    monthly_rate = (1 + pre_ret_return) ** (1/12) - 1
    while current_age + months/12 <= 80:
        years_from_now = months / 12
        future_m_exp = monthly_expense * ((1 + inflation) ** years_from_now)
        future_a_exp = future_m_exp * 12
        req = coast_required(years_from_now, future_a_exp)
        if corpus >= req:
            return current_age + months/12, corpus
        corpus = fv(monthly_rate, 1, 0.0, corpus, when="end")
        months += 1
    return None, corpus

coast_age, coast_corpus = (None, None)
if show_coast:
    coast_age, coast_corpus = coast_check(current_corpus, pre_ret_return, current_age)

# -----------------------------
# Layout
# -----------------------------

left, right = st.columns([1,1])

with left:
    st.subheader("Your FIRE number")
    st.metric("Required corpus (₹)", rupee(required_corpus))
    st.metric("Projected corpus at target age", rupee(projected_corpus_at_target))

    if projected_corpus_at_target >= required_corpus:
        status_html = f'<span class="status-pill status-ok">On track</span>'
    else:
        status_html = f'<span class="status-pill status-warn">Shortfall</span>'
    st.markdown(f"**Status @ {target_age}:** {status_html}", unsafe_allow_html=True)

    if projected_corpus_at_target < required_corpus:
        gap = required_corpus - projected_corpus_at_target
        st.write(f"Shortfall at {target_age}: **{rupee(gap)}**")
    else:
        surplus = projected_corpus_at_target - required_corpus
        st.write(f"Surplus at {target_age}: **{rupee(surplus)}**")

    st.subheader("Earliest FI (given your SIP plan)")
    if age_reached <= 80:
        st.success(f"You reach FI by **age {age_reached:.1f}** with corpus ≈ **{rupee(corpus_when_reached)}**.")
    else:
        st.warning("FI not reached by age 80 under current assumptions.")

    if show_coast:
        st.subheader("Coast-FIRE")
        if coast_age is not None:
            st.info(f"If you **stop investing today**, your current corpus would grow to FI by **age {coast_age:.1f}**.")
        else:
            st.info("Coast-FIRE not achievable by age 80 with current corpus.")

with right:
    st.subheader("Trajectory")
    if not traj_df.empty:
        chart_df = traj_df.melt(id_vars="Age", value_vars=["Invested Corpus", "Required Corpus"],
                                var_name="Series", value_name="Amount")
        color_scale = alt.Scale(domain=["Invested Corpus", "Required Corpus"],
                                range=[PRIMARY_BLUE, ACCENT_ORANGE])
        line = alt.Chart(chart_df).mark_line().encode(
            x=alt.X("Age:Q", title="Age (years)"),
            y=alt.Y("Amount:Q", title="Amount (₹)", axis=alt.Axis(format="s")),
            color=alt.Color("Series:N", scale=color_scale, legend=alt.Legend(title="")),
            tooltip=["Age", "Series", alt.Tooltip("Amount:Q", format=",.0f")]
        ).properties(height=340)
        st.altair_chart(line, use_container_width=True)
    else:
        st.write("Adjust inputs to see the trajectory.")

    if show_table and not traj_df.empty:
        st.write("**Selected snapshots (every ~6 months):**")
        st.dataframe(traj_df.round(2))

st.divider()
with st.expander("What the modes mean"):
    st.markdown("""
**Lean FIRE** — smaller corpus by living minimally (multiplier < 1.0).  
**Barista FIRE** — part-time income covers a portion of expenses in retirement (e.g., 40%).  
**Fat FIRE** — larger corpus to maintain an abundant lifestyle (multiplier > 1.0).  
Safe Withdrawal Rate (SWR) typically 3–4% for conservatism in India, but configurable here.
    """)

with st.expander("Assumption notes & tips"):
    st.markdown(f"""
- **Inflation** applies to your *expenses* till FIRE; **post-FIRE returns** matter for sustainability but are not used in the FI-threshold (SWR-based).
- **SIP growth** can track income growth or be set custom. A higher savings rate speeds up FI dramatically.
- **Target corpus** is `Adjusted Annual Expenses / SWR`. For example, ₹24L/yr at 4% → ₹6 Cr.
- **Pre-FIRE return** compounds monthly. Use realistic expectations.
- This tool is **educational**; not investment advice.
    """)

st.caption("Edelweiss palette applied. Save as `fire_app_eli.py` and run:  `streamlit run fire_app_eli.py`")
