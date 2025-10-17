
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from PIL import Image

PRIMARY_BLUE = "#034EA2"
ACCENT_ORANGE = "#F79421"
BG_LIGHT = "#F9FAFB"
TEXT_DARK = "#1F2937"

BRAND_CSS = f"""
<style>
:root {{ --primary:{PRIMARY_BLUE}; --accent:{ACCENT_ORANGE}; --text:{TEXT_DARK}; }}
.header-title h1 {{ margin:0; font-size:1.6rem; line-height:1.2; color:var(--primary);}}
.smallnote {{ color:#6B7280; font-size:0.95rem; margin-top:.25rem; }}
.stButton>button {{ background:var(--primary); color:white; border-radius:8px; border:none; }}
.stButton>button:hover {{ background:#023b7b; }}
.stSlider [data-baseweb="slider"] > div > div {{ background:var(--primary);}}
.status-pill {{ display:inline-block; padding:4px 10px; border-radius:999px; font-weight:600; color:white; }}
.status-ok {{ background:var(--primary);}}
.status-warn {{ background:var(--accent);}}
.card {{ background:white; border:1px solid #E5E7EB; border-radius:12px; padding:14px;}}
.card h3 {{ margin:0 0 6px 0; font-size:1rem; color:var(--text);}}
.card .value {{ font-weight:700; font-size:1.1rem; }}
.progress-wrap {{ background:#EEF2FF; border-radius:8px; padding:10px 12px; }}
.header-logo img {{ max-height:56px; }}
@media (max-width:640px){
  .header-logo img {{ max-height:44px; }}
  .header-title h1 {{ font-size:1.25rem; }}
}
</style>
"""

def rupee_indian(x: float) -> str:
    if pd.isna(x): return "₹0"
    x_int = int(round(x))
    s = str(x_int)
    if len(s) <= 3: out = s
    else:
        last3 = s[-3:]; other = s[:-3]; groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:]); other = other[:-2]
        if other: groups.insert(0, other)
        out = ",".join(groups + [last3])
    return f"₹{out}"

def fv(rate: float, nper: int, pmt: float, pv: float, when: str = "end") -> float:
    when_val = 1 if when == "begin" else 0
    if rate == 0: return pv + pmt * nper
    return pv * (1 + rate) ** nper + pmt * (1 + rate * when_val) * (((1 + rate) ** nper - 1) / rate)

def years_until_fi(current_age, current_corpus, monthly_sip, pre_ret_annual_return,
                   sip_growth, target_corpus_func, inflation, base_monthly_expense, max_age=80):
    records = []; corpus = current_corpus; months = 0
    monthly_rate = (1 + pre_ret_annual_return) ** (1/12) - 1
    while current_age + months/12 <= max_age:
        yrs = months/12
        f_m_exp = base_monthly_expense * ((1 + inflation) ** yrs)
        f_a_exp = f_m_exp * 12
        req = target_corpus_func(yrs, f_a_exp)
        if corpus >= req:
            age_hit = current_age + months/12
            records.append({"Age": age_hit, "Invested Corpus": corpus, "Required Corpus": req})
            return age_hit, corpus, pd.DataFrame(records)
        corpus = fv(monthly_rate, 1, monthly_sip, corpus, when="end")
        months += 1
        if months % 12 == 0 and monthly_sip > 0: monthly_sip *= (1 + sip_growth)
        if months % 6 == 0:
            age_pt = current_age + months/12
            records.append({"Age": age_pt, "Invested Corpus": corpus, "Required Corpus": req})
    return max_age, corpus, pd.DataFrame(records)

def best_unit(amounts: pd.Series):
    maxv = float(np.nanmax(amounts)) if len(amounts) else 0.0
    if maxv >= 1e7: return "₹ Cr", 1e7
    elif maxv >= 1e5: return "₹ L", 1e5
    else: return "₹", 1.0

st.set_page_config(page_title="FIRE Calculator — Edelweiss", page_icon=None, layout="wide")
st.markdown(BRAND_CSS, unsafe_allow_html=True)

c1, c2 = st.columns([1, 4])
with c1:
    try: st.image(Image.open("edelweiss_logo.png"), use_container_width=True)
    except Exception: pass
with c2:
    st.markdown('<div class="header-title"><h1>FIRE Calculator — Financial Independence, Retire Early</h1><div class="smallnote">Edelweiss palette • Simple inputs • Lean/Barista/Fat • SWR • Coast-FIRE</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Quick Start")
    col_age = st.columns(2)
    with col_age[0]:
        current_age = st.number_input("Current age", 18, 70, 30, 1)
    with col_age[1]:
        target_age = st.number_input("Target FI age", current_age+1, 80, 45, 1)
    monthly_income = st.number_input("Monthly income (₹)", 0.0, value=150000.0, step=5000.0, format="%.0f",
                                     help="Your take-home per month.")
    monthly_expense = st.number_input("Monthly expenses (₹, today)", 0.0, value=80000.0, step=5000.0, format="%.0f",
                                      help="Usual living costs per month in today's value.")
    current_corpus = st.number_input("Current invested corpus (₹)", 0.0, value=1000000.0, step=50000.0, format="%.0f")
    st.markdown("---")
    st.subheader("Investing each month")
    sip_mode = st.radio("How do you want to input SIP?", ["Fixed amount", "% of income"], horizontal=True, index=0)
    if sip_mode == "% of income":
        sip_pct = st.slider("SIP as % of income", 0, 80, 30, 1, help="Set 0% if you're not investing monthly.")
        monthly_sip = monthly_income * sip_pct/100.0
    else:
        monthly_sip = st.number_input("Monthly SIP (₹)", 0.0, value=30000.0, step=5000.0, format="%.0f",
                                      help="Enter 0 if you don't currently invest monthly.")
    compact = st.toggle("Compact layout (mobile)", value=True)
    st.markdown("---")
    with st.expander("Advanced (optional)", expanded=False):
        st.caption("Tweak assumptions if you want finer control.")
        inflation = st.slider("Inflation on expenses (annual, %)", 0.0, 10.0, 6.0, 0.25) / 100.0
        income_growth = st.slider("Yearly salary hike (%, for info)", 0.0, 20.0, 8.0, 0.25) / 100.0
        pre_ret_return = st.slider("Expected return before FI (annual, %)", 0.0, 20.0, 11.0, 0.25) / 100.0
        post_ret_return = st.slider("Expected return after FI (annual, %)", 0.0, 12.0, 7.0, 0.25) / 100.0
        swr = st.slider("Safe Withdrawal Rate (%, lower = safer)", 2.5, 5.0, 4.0, 0.1) / 100.0
        if monthly_sip > 0:
            sip_growth_choice = st.radio("SIP step-up each year", ["Track salary hike", "Custom rate"], horizontal=True, index=0)
            if sip_growth_choice == "Track salary hike": sip_growth = income_growth
            else: sip_growth = st.slider("SIP growth (annual, %)", 0.0, 30.0, 8.0, 0.25) / 100.0
        else: sip_growth = 0.0; st.caption("SIP growth disabled (no monthly SIP).")
    st.markdown("---")
    st.subheader("FIRE style")
    fire_type = st.selectbox("Choose mode", ["Lean FIRE", "Barista FIRE", "Fat FIRE"], index=1)
    if fire_type == "Lean FIRE":
        lean_mult = st.slider("Lean lifestyle (x of baseline)", 0.5, 1.0, 0.8, 0.05); barista_cover = 0.0; fat_mult = 1.0
    elif fire_type == "Barista FIRE":
        barista_cover = st.slider("Part-time income covers (%) of expenses", 10, 80, 40, 5) / 100.0; lean_mult = 1.0; fat_mult = 1.0
    else:
        fat_mult = st.slider("Fat lifestyle (x of baseline)", 1.0, 2.5, 1.5, 0.1); barista_cover = 0.0; lean_mult = 1.0

if "inflation" not in locals():
    inflation = 0.06; income_growth = 0.08; pre_ret_return = 0.11; post_ret_return = 0.07; swr = 0.04
    sip_growth = 0.0 if monthly_sip <= 0 else 0.08

years_to_target = target_age - current_age
future_monthly_expense = monthly_expense * ((1 + inflation) ** years_to_target)
future_annual_expense = future_monthly_expense * 12
if fire_type == "Lean FIRE": adjusted_annual_expense = future_annual_expense * lean_mult
elif fire_type == "Barista FIRE": adjusted_annual_expense = future_annual_expense * (1 - barista_cover)
else: adjusted_annual_expense = future_annual_expense * fat_mult
required_corpus = adjusted_annual_expense / swr

monthly_rate = (1 + pre_ret_return) ** (1/12) - 1
n_months = max(0, years_to_target * 12)
corpus = float(current_corpus)
if monthly_sip > 0 and n_months > 0:
    sip = monthly_sip
    for m in range(n_months):
        corpus = fv(monthly_rate, 1, sip, corpus, when="end")
        if (m+1) % 12 == 0: sip *= (1 + sip_growth)
elif n_months > 0:
    for m in range(n_months): corpus = fv(monthly_rate, 1, 0.0, corpus, when="end")
projected_corpus_at_target = corpus

def target_corpus_func(years_from_now: float, future_annual_exp: float) -> float:
    expense = (future_annual_exp * lean_mult) if fire_type == "Lean FIRE" else \
              (future_annual_exp * (1 - barista_cover) if fire_type == "Barista FIRE" else future_annual_exp * fat_mult)
    return expense / swr

age_reached, corpus_when_reached, traj_df = years_until_fi(
    current_age=current_age, current_corpus=current_corpus, monthly_sip=max(0.0, monthly_sip),
    pre_ret_annual_return=pre_ret_return, sip_growth=sip_growth if monthly_sip > 0 else 0.0,
    target_corpus_func=target_corpus_func, inflation=inflation, base_monthly_expense=monthly_expense, max_age=80
)

def coast_check(current_corpus, pre_ret_return, current_age):
    corpus = current_corpus; months = 0
    monthly_rate = (1 + pre_ret_return) ** (1/12) - 1
    while current_age + months/12 <= 80:
        yrs = months/12
        f_m_exp = monthly_expense * ((1 + inflation) ** yrs); f_a_exp = f_m_exp * 12
        req = target_corpus_func(yrs, f_a_exp)
        if corpus >= req: return current_age + months/12, corpus
        corpus = fv(monthly_rate, 1, 0.0, corpus, when="end"); months += 1
    return None, corpus
coast_age, _ = coast_check(current_corpus, pre_ret_return, current_age)

g1, g2, g3 = st.columns([1,1,1])
with g1: st.markdown(f'<div class="card"><h3>Required corpus</h3><div class="value">{rupee_indian(required_corpus)}</div></div>', unsafe_allow_html=True)
with g2: st.markdown(f'<div class="card"><h3>Projected @ target age</h3><div class="value">{rupee_indian(projected_corpus_at_target)}</div></div>', unsafe_allow_html=True)
with g3:
    val = f"{age_reached:.1f} yrs" if age_reached <= 80 else "Not by 80"
    st.markdown(f'<div class="card"><h3>Earliest FI age</h3><div class="value">{val}</div></div>', unsafe_allow_html=True)

ratio = 0 if required_corpus <= 0 else projected_corpus_at_target / required_corpus
st.markdown('<div class="progress-wrap"><b>Progress to target corpus:</b></div>', unsafe_allow_html=True)
st.progress(max(0.0, min(1.0, ratio)), text=f"{ratio*100:.1f}% of target")

cA, cB = st.columns([1,1])
with cA:
    if projected_corpus_at_target >= required_corpus:
        st.markdown("**Status @ {}:** <span class='status-pill status-ok'>On track</span>".format(target_age), unsafe_allow_html=True)
    else:
        gap = required_corpus - projected_corpus_at_target
        st.markdown("**Status @ {}:** <span class='status-pill status-warn'>Shortfall</span>".format(target_age), unsafe_allow_html=True)
        st.write("Gap at {}: **{}**".format(target_age, rupee_indian(gap)))
with cB:
    if coast_age is not None: st.write("**Coast-FIRE:** with no more investing, FI at **age {:.1f}**.".format(coast_age))
    else: st.write("**Coast-FIRE:** not achievable by 80 with current corpus.")

st.subheader("Trajectory")
if not traj_df.empty:
    unit, div = best_unit(pd.concat([traj_df["Invested Corpus"], traj_df["Required Corpus"]], ignore_index=True))
    chart_df = traj_df.melt(id_vars="Age", value_vars=["Invested Corpus", "Required Corpus"],
                            var_name="Series", value_name="Amount")
    chart_df["AmountScaled"] = chart_df["Amount"] / div
    color_scale = alt.Scale(domain=["Invested Corpus", "Required Corpus"], range=[PRIMARY_BLUE, ACCENT_ORANGE])
    line = alt.Chart(chart_df).mark_line().encode(
        x=alt.X("Age:Q", title="Age (years)"),
        y=alt.Y("AmountScaled:Q", title=f"Amount ({unit})", axis=alt.Axis(format="~s")),
        color=alt.Color("Series:N", scale=color_scale, legend=alt.Legend(title="")),
        tooltip=[alt.Tooltip("Age:Q", format=".1f"), "Series", alt.Tooltip("Amount:Q", title="Amount (₹)", format=",.0f")]
    ).properties(height=340)
    st.altair_chart(line, use_container_width=True)
else:
    st.info("Adjust inputs on the left to see a trajectory and earliest FI age.")

with st.expander("What do these mean?"):
    st.markdown("""
- **Yearly salary hike**: your typical pay raise each year (used to optionally step-up SIP).
- **SIP step-up**: how much your monthly investing increases every year.
- **SWR (Safe Withdrawal Rate)**: how much of your corpus you plan to withdraw per year in FI. Lower is safer.
- **Lean / Barista / Fat FIRE**: minimal lifestyle vs part-time work vs abundant lifestyle targets.
    """)
