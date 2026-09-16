"""
Careem Ads — Agency Partnerships GTM Tracker (PROTOTYPE)
----------------------------------------------------------
Built for the Careem "Associate Director of Ads Sales / Agency Partnerships
Lead" application take-home brief.

What this demonstrates, mapped to the role's core responsibilities:
  1. Agency GTM strategy & pipeline ownership across UAE / KSA / Egypt
     and the Big 6 holding groups.
  2. Pipeline planning, forecasting & JBP attainment tracking — the
     operating rhythm I would monitor closely as Head of Agency Partnerships.
  3. An AI layer that auto-flags at-risk deals and auto-drafts a business
     update + recommended actions to delegate to Partner Managers so they spend 
     less time manually reviewing data and more time delivering tangible actions and outcomes.

Data: 100% dummy/synthetic (see generate_data.py). No real Careem,
agency, or client data is used anywhere in this prototype.

Run locally:   streamlit run app.py

"""
import os
import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Careem Ads — Agency Partnerships Tracker (Prototype)",
    page_icon="📈",
    layout="wide",
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "careem_ads_agency_pipeline_dummy.csv")

# Careem brand palette (brand.careem.com/colour), used consistently
# across every chart on the page rather than default colors.
CAREEM_GREEN = "#00E784"
MIDNIGHT_BLUE = "#001942"
FOREST_GREEN = "#00493E"
DESERT_SKY_BLUE = "#A6EDF2"
LIGHT_GREEN = "#D6FFEA"

# Fixed colors so Endemic / Non-endemic always mean the same thing wherever
# they appear on the page (donut, vertical breakdown, contribution chart).
CATEGORY_COLORS = {"Endemic": CAREEM_GREEN, "Non-endemic": FOREST_GREEN}
# Fixed colors so each market always means the same thing on every chart.
MARKET_COLORS = {"UAE": MIDNIGHT_BLUE, "KSA": CAREEM_GREEN, "Egypt": DESERT_SKY_BLUE}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["last_activity_date"])
    return df

df = load_data()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Careem — Agency Partnerships Lifecycle Tracker")
st.caption(
    "PROTOTYPE for the Associate Director of Ads Sales / Agency Partnerships Lead brief · "
    "100% dummy data, no confidential information · Built with Streamlit + an optional LLM layer "
    "(OpenAI's GPT-4o-mini, with GPT-4o as the alternate option in the sidebar dropdown, since the "
    "brief calls out ChatGPT as one of the free tools to consider)."
)

with st.expander("ℹ️ What is this, and why does it map to the role?", expanded=False):
    st.markdown(
        """
This is a working prototype of the kind of operating tool I believe a Head of Agency
Partnerships would want on day one: **one screen that shows pipeline health
across the Big 6 holding groups and three markets, flags what's at risk, and
uses AI to draft business update narrative and tangible next steps** — turning a task that
normally takes manual effort into one that takes just minutes review, sense check and delegate.

- **GTM ownership** → filter pipeline by market / holding group / quarter
- **Forecasting & pipeline coverage** → weighted pipeline vs. a target, JBP attainment
- **QBR operating rhythm** → one-click AI-drafted commentary per agency
- **Non-endemic growth priority** → endemic vs. non-endemic split tracked explicitly
        """
    )

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
markets = st.sidebar.multiselect("Market", sorted(df["market"].unique()), default=sorted(df["market"].unique()))
holdings = st.sidebar.multiselect("Holding Group", sorted(df["holding_group"].unique()), default=sorted(df["holding_group"].unique()))
quarters = st.sidebar.multiselect("Quarter", sorted(df["quarter"].unique()), default=sorted(df["quarter"].unique()))
categories = st.sidebar.multiselect("Client Category", sorted(df["category_type"].unique()), default=sorted(df["category_type"].unique()))

st.sidebar.divider()
st.sidebar.header("AI layer (optional)")
api_key = st.sidebar.text_input(
    "OpenAI API key",
    type="password",
    help="Paste a key to get live GPT-drafted QBR commentary. Leave blank to see the built-in "
         "template-mode output (same structure, no external call, works offline for demo purposes).",
)
model_name = st.sidebar.selectbox("Model (if key provided)", ["gpt-4o-mini", "gpt-4o"], index=0)

scope = df[
    df["market"].isin(markets)
    & df["holding_group"].isin(holdings)
    & df["quarter"].isin(quarters)
    & df["category_type"].isin(categories)
]

if scope.empty:
    st.warning("No deals match the current filters — widen your selection in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# At-risk logic (simple, transparent rules — the kind a real ops function
# would start with before layering on machine learning). A deal is flagged at-risk 
# if it's been sitting in its current stage longer than a normal deal should 
# (thresholds range from 28–60 days depending on stage), or if it's deep in the 
# funnel (Negotiation or JBP Signed) but still has a win-probability under 35%. 
# Either condition alone is enough to trigger the flag.
# ---------------------------------------------------------------------------
STAGE_STALL_THRESHOLD = {
    "Prospecting": 40, "Proposal Sent": 28, "Negotiation": 30,
    "JBP Signed": 35, "PO Received / Budget Confirmed": 45,
    "Live Campaign": 60, "Renewal": 30,
}

def flag_at_risk(row):
    threshold = STAGE_STALL_THRESHOLD.get(row["stage"], 45)
    stalled = row["days_in_current_stage"] > threshold
    underpriced_confidence = row["stage"] in ["Negotiation", "JBP Signed"] and row["win_probability"] < 0.35
    return stalled or underpriced_confidence

scope = scope.copy()
scope["at_risk"] = scope.apply(flag_at_risk, axis=1)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
total_pipeline = scope["pipeline_value_usd"].sum()
weighted_pipeline = scope["weighted_value_usd"].sum()
QUARTERLY_TARGET_USD = 20_000_000  # illustrative target for the filtered universe
coverage_ratio = total_pipeline / QUARTERLY_TARGET_USD if QUARTERLY_TARGET_USD else 0
non_endemic_share = scope.loc[scope["category_type"] == "Non-endemic", "pipeline_value_usd"].sum() / total_pipeline
jbp_signed_mask = scope["stage"].isin(["PO Received / Budget Confirmed", "Live Campaign", "Renewal"])
jbp_attainment = scope.loc[jbp_signed_mask, "pipeline_value_usd"].sum() / total_pipeline
n_at_risk = int(scope["at_risk"].sum())
n_total_deals = int(len(scope))

k0, k1, k2, k3, k4, k5, k6 = st.columns(7)
k0.metric("Total Deals", n_total_deals)
k1.metric("Total Pipeline", f"${total_pipeline/1e6:,.1f}M", help="The total revenue associated with all items in the pipeline at any stage")
k2.metric("Weighted Pipeline", f"${weighted_pipeline/1e6:,.1f}M", help="Deal value × win-probability, summed — a more realistic forecast than raw pipeline.")
k3.metric("Pipeline Coverage", f"{coverage_ratio:,.2f}x", help="Total pipeline ÷ illustrative quarterly target")
k4.metric("Non-endemic Share", f"{non_endemic_share*100:,.0f}%", help="Share of pipeline from advertisers outside Careem's listed categories.")
k5.metric("JBP / Live / Renewal Mix", f"{jbp_attainment*100:,.0f}%", help="Share of the pipeline that's actually funded (PO Received, Live, or at Renewal stage), not just agreed in principle.")
k6.metric("At-risk Deals", n_at_risk, delta=None, help="Deals stalled too long for their stage, or late-stage with low win-probability")

st.divider()

# ---------------------------------------------------------------------------
# Target Attainment - This section compares confirmed, already-won revenue against the 
# quarter's target, and shows whether the pipeline still in progress is large enough to 
# close whatever gap remains.
# ---------------------------------------------------------------------------
st.subheader("🎯 Target Attainment")
st.caption(
    "\"Confirmed\" = deals in PO Received / Budget Confirmed, Live Campaign, or Renewal — i.e. money "
    "that's actually funded, not just agreed in principle. A signed JBP is a framework agreement at "
    "the holding-group level; it still needs its own budget sign-off (a PO) before the money really "
    "moves, so JBP Signed alone doesn't count as confirmed here. This shows how much of the target "
    "is already locked in, and whether there's enough open pipeline left to cover what's missing."
)

CONFIRMED_STAGES = ["PO Received / Budget Confirmed", "Live Campaign", "Renewal"]
WARM_STAGES = ["Proposal Sent", "Negotiation"]
confirmed_value = scope.loc[scope["stage"].isin(CONFIRMED_STAGES), "pipeline_value_usd"].sum()
warm_pipeline_value = scope.loc[scope["stage"].isin(WARM_STAGES), "pipeline_value_usd"].sum()
open_pipeline_value = scope.loc[~scope["stage"].isin(CONFIRMED_STAGES), "pipeline_value_usd"].sum()
pct_of_target_committed = confirmed_value / QUARTERLY_TARGET_USD if QUARTERLY_TARGET_USD else 0
gap_to_target = QUARTERLY_TARGET_USD - confirmed_value

t1, t2, t3 = st.columns(3)
t1.metric(
    "% of Target Committed",
    f"{pct_of_target_committed*100:,.0f}%",
    help=f"${confirmed_value:,.0f} confirmed ÷ ${QUARTERLY_TARGET_USD:,.0f} target",
)
if gap_to_target > 0:
    t2.metric("Gap to Target", f"${gap_to_target/1e6:,.2f}M", help="Target minus confirmed revenue — still needs to be closed")
else:
    t2.metric("Gap to Target", "Target met ✅", help="Confirmed revenue already covers the target")
t3.metric(
    "Warm Pipeline (Proposal + Negotiation)",
    f"${warm_pipeline_value/1e6:,.2f}M",
    help="Deals in Proposal Sent or Negotiation — actively being worked, not yet confirmed, and not "
         "as early-stage as Prospecting.",
)

st.progress(min(pct_of_target_committed, 1.0), text=f"{pct_of_target_committed*100:,.0f}% of target confirmed")

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1.2, 1])

with c1:
    stage_order = ["Prospecting", "Proposal Sent", "Negotiation", "JBP Signed",
                   "PO Received / Budget Confirmed", "Live Campaign", "Renewal"]
    by_stage = (
        scope.groupby("stage")["pipeline_value_usd"].sum().reindex(stage_order).fillna(0).reset_index()
    )
    fig_funnel = px.funnel(by_stage, x="pipeline_value_usd", y="stage", title="Pipeline by Stage (USD)")
    fig_funnel.update_traces(marker=dict(color=CAREEM_GREEN))
    st.plotly_chart(fig_funnel, width='stretch')

with c2:
    by_cat = scope.groupby("category_type")["pipeline_value_usd"].sum().reset_index()
    fig_donut = px.pie(by_cat, names="category_type", values="pipeline_value_usd", hole=0.55,
                        title="Endemic vs. Non-endemic Mix",
                        color="category_type", color_discrete_map=CATEGORY_COLORS)
    st.plotly_chart(fig_donut, width='stretch')

c3, c4 = st.columns(2)
with c3:
    by_holding_market = scope.groupby(["holding_group", "market"])["weighted_value_usd"].sum().reset_index()
    fig_bar = px.bar(by_holding_market, x="holding_group", y="weighted_value_usd", color="market",
                      color_discrete_map=MARKET_COLORS,
                      title="Weighted Pipeline by Holding Group & Market", barmode="stack")
    st.plotly_chart(fig_bar, width='stretch')

with c4:
    by_vertical = (
        scope.groupby(["client_vertical", "category_type"])["pipeline_value_usd"].sum().reset_index()
    )
    fig_vert = px.bar(by_vertical, x="pipeline_value_usd", y="client_vertical", orientation="h",
                       color="category_type", color_discrete_map=CATEGORY_COLORS,
                       title="Pipeline by Client Vertical (colored by Endemic / Non-endemic)")
    fig_vert.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig_vert, width='stretch')

# ---------------------------------------------------------------------------
# Contribution by pipeline item — which individual deals are actually
# driving the total, i.e. concentration risk at the deal level rather than
# the vertical/stage/agency level already covered above.
# ---------------------------------------------------------------------------
TOP_N_DEALS = 15
top_deals = scope.nlargest(TOP_N_DEALS, "pipeline_value_usd").copy()
top_deals["label"] = top_deals["deal_id"] + " · " + top_deals["holding_group"] + " · " + top_deals["client_vertical"]
top5_share = scope.nlargest(5, "pipeline_value_usd")["pipeline_value_usd"].sum() / total_pipeline

st.subheader("📊 Contribution by Pipeline Item")
st.caption(
    f"The top {TOP_N_DEALS} individual deals in the current filters, ranked by pipeline value — the "
    f"top 5 alone account for **{top5_share*100:,.0f}%** of total pipeline. Useful for spotting "
    "concentration risk: if a handful of deals make up most of the forecast, losing even one or two "
    "materially changes the number."
)
fig_contribution = px.bar(
    top_deals.sort_values("pipeline_value_usd"), x="pipeline_value_usd", y="label", orientation="h",
    color="category_type", color_discrete_map=CATEGORY_COLORS,
    title=f"Top {TOP_N_DEALS} Deals by Pipeline Value (USD)",
)
fig_contribution.update_layout(yaxis_title=None, xaxis_title="Pipeline Value (USD)")
st.plotly_chart(fig_contribution, width='stretch')

st.divider()

# ---------------------------------------------------------------------------
# At-risk deals table
# ---------------------------------------------------------------------------
st.subheader("⚠️ At-risk deals (rule-based flagging)")
st.caption(
    "This flags deals stalled beyond a stage-specific threshold, or deep in the funnel with a low "
    "win-probability. Thresholds: Prospecting more than 40 days, Proposal Sent more than 28 days, "
    "Negotiation more than 30 days, JBP Signed more than 35 days, PO Received / Budget Confirmed "
    "more than 45 days, Live Campaign more than 60 days, Renewal more than 30 days. At first, these "
    "thresholds are set from experience and judgement. In future, once enough deal history has been "
    "generated, this would convert to a predictive model built on a real data pipeline — trained on "
    "actual won/lost/stalled outcomes — to flag at-risk deals based on learned patterns rather than "
    "fixed rules."
)
risk_cols = ["deal_id", "holding_group", "market", "client_vertical", "stage",
             "pipeline_value_usd", "win_probability", "days_in_current_stage"]
st.dataframe(
    scope.loc[scope["at_risk"], risk_cols].sort_values("days_in_current_stage", ascending=False),
    width='stretch', hide_index=True,
)

st.divider()

# ---------------------------------------------------------------------------
# AI-drafted business update
# ---------------------------------------------------------------------------
st.subheader("AI-drafted business update & recommended actions")

ALL_LABEL = "All (selected filters)"
f1, f2, f3, f4 = st.columns(4)
focus_holding = f1.selectbox("Holding Group:", [ALL_LABEL] + sorted(scope["holding_group"].unique()))
focus_market = f2.selectbox("Market:", [ALL_LABEL] + sorted(scope["market"].unique()))
focus_vertical = f3.selectbox("Client Vertical:", [ALL_LABEL] + sorted(scope["client_vertical"].unique()))
focus_category = f4.selectbox("Endemic / Non-endemic:", [ALL_LABEL] + sorted(scope["category_type"].unique()))

agency_scope = scope.copy()
if focus_holding != ALL_LABEL:
    agency_scope = agency_scope[agency_scope["holding_group"] == focus_holding]
if focus_market != ALL_LABEL:
    agency_scope = agency_scope[agency_scope["market"] == focus_market]
if focus_vertical != ALL_LABEL:
    agency_scope = agency_scope[agency_scope["client_vertical"] == focus_vertical]
if focus_category != ALL_LABEL:
    agency_scope = agency_scope[agency_scope["category_type"] == focus_category]

# A readable label for this narrowed scope, used in the prompt and the output header
_scope_bits = [v for v in [focus_holding, focus_market, focus_vertical, focus_category] if v != ALL_LABEL]
focus_agency = " · ".join(_scope_bits) if _scope_bits else ALL_LABEL

if agency_scope.empty:
    st.warning("No deals match this combination — widen your selection above.")
    st.stop()

def build_stats_block(d: pd.DataFrame) -> str:
    tp = d["pipeline_value_usd"].sum()
    wp = d["weighted_value_usd"].sum()
    ne_share = d.loc[d["category_type"] == "Non-endemic", "pipeline_value_usd"].sum() / tp if tp else 0
    risk_n = int(d["at_risk"].sum())
    risk_val = d.loc[d["at_risk"], "pipeline_value_usd"].sum()
    top_verticals = d.groupby("client_vertical")["pipeline_value_usd"].sum().sort_values(ascending=False).head(3)
    stage_mix = d.groupby("stage")["pipeline_value_usd"].sum().sort_values(ascending=False)
    return (
        f"Total pipeline: ${tp:,.0f}\n"
        f"Weighted pipeline: ${wp:,.0f}\n"
        f"Non-endemic share: {ne_share*100:.0f}%\n"
        f"At-risk deals: {risk_n} deals worth ${risk_val:,.0f}\n"
        f"Top client verticals by value: {', '.join(f'{v} (${val:,.0f})' for v, val in top_verticals.items())}\n"
        f"Stage mix (USD): {', '.join(f'{s}: ${v:,.0f}' for s, v in stage_mix.items())}\n"
    )

stats_block = build_stats_block(agency_scope)

system_prompt = (
    "You are a senior Agency Partnerships analyst at Careem Ads, the ad platform of the Careem "
    "super-app (ride-hailing, food & grocery delivery, payments) across UAE, KSA and Egypt. "
    "You write concise, board-ready business update commentary for agency holding-group relationships "
    "(e.g. WPP, Publicis, Omnicom, IPG, Dentsu, Havas). Be specific, cite the numbers you're given, "
    "flag risk plainly, and end with 3 prioritized, concrete recommended actions for the "
    "Agency Partner Manager. Keep it under 200 words. No preamble."
)
user_prompt = (
    f"Scope: {focus_agency}\n\n"
    f"Pipeline data summary:\n{stats_block}\n"
    "Draft the business update and recommended actions."
)

with st.expander("🔍 View the exact prompt sent to the AI model"):
    st.markdown("**System prompt:**")
    st.code(system_prompt, language="text")
    st.markdown("**User prompt (auto-built from the filtered data above):**")
    st.code(user_prompt, language="text")

def generate_template_commentary(d: pd.DataFrame, label: str) -> str:
    tp = d["pipeline_value_usd"].sum()
    wp = d["weighted_value_usd"].sum()
    ne_share = d.loc[d["category_type"] == "Non-endemic", "pipeline_value_usd"].sum() / tp if tp else 0
    risk_n = int(d["at_risk"].sum())
    risk_val = d.loc[d["at_risk"], "pipeline_value_usd"].sum()
    top_vertical = d.groupby("client_vertical")["pipeline_value_usd"].sum().sort_values(ascending=False).index[0]
    top_stage = d.groupby("stage")["pipeline_value_usd"].sum().sort_values(ascending=False).index[0]
    risk_pct = (risk_val / tp * 100) if tp else 0

    return f"""**Business Update — {label}** *(template mode — add an API key in the sidebar for live GPT output)*

Pipeline for this scope stands at **USD {tp:,.0f}** (**USD {wp:,.0f}** weighted), concentrated most heavily
in **{top_vertical}** and the **{top_stage}** stage. Non-endemic categories make up **{ne_share*100:.0f}%**
of value — directionally healthy against the mandate to scale non-endemic, brand-advertising revenue,
though it should keep climbing quarter over quarter as the JBP narrative matures with these agencies.

**Risk:** {risk_n} deals (**USD {risk_val:,.0f}**, ~{risk_pct:.0f}% of scope) are flagged at-risk — stalled
beyond their normal stage duration or sitting in late stages with soft win-probability. Left unaddressed,
this is the gap between forecast and closed revenue this quarter.

**Recommended actions:**
1. Personally re-engage the top 3 at-risk deals by value this week with the agency lead sponsor — don't let stage-stall become churn.
2. Push non-endemic share higher by packaging a category-specific proof-of-concept (data + case study) for the largest under-represented vertical.
3. Lock a QBR date with this holding group's leadership to reset the JBP roadmap and pipeline coverage target for next quarter.
"""

def generate_ai_commentary(system_prompt: str, user_prompt: str, api_key: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=400,
    )
    return resp.choices[0].message.content

if st.button("✨ Generate business update"):
    with st.spinner("Drafting..."):
        if api_key:
            try:
                output = generate_ai_commentary(system_prompt, user_prompt, api_key, model_name)
                st.success("Generated live by " + model_name)
            except Exception as e:
                output = generate_template_commentary(agency_scope, focus_agency)
                st.warning(f"Live API call failed ({e}) — showing template-mode output instead.")
        else:
            output = generate_template_commentary(agency_scope, focus_agency)
    # Escape literal "$" so Streamlit's markdown renderer doesn't mistake
    # currency figures for LaTeX math delimiters.
    st.markdown(output.replace("$", "\\$"))

st.divider()
st.caption(
    "Prototype by Becky · dummy data only · built with Streamlit + Plotly, optional OpenAI API layer · "
    f"generated {dt.date.today().isoformat()}"
)
