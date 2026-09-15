"""
Careem Ads — Agency Partnerships GTM Tracker (PROTOTYPE)
----------------------------------------------------------
Built for the Careem "Associate Director of Ads Sales / Agency Partnerships
Lead" application take-home brief.

What this demonstrates, mapped to the role's core responsibilities:
  1. Agency GTM strategy & pipeline ownership across UAE / KSA / Egypt
     and the Big 6 holding groups.
  2. Pipeline planning, forecasting & JBP attainment tracking — the
     operating rhythm a Head of Agency Partnerships would run monthly.
  3. An AI layer that auto-flags at-risk deals and auto-drafts QBR
     narrative + recommended actions, so Partner Managers spend less
     time building slides and more time in the room with agencies.

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
st.title("📈 Careem Ads — Agency Partnerships GTM Tracker")
st.caption(
    "PROTOTYPE for the Associate Director of Ads Sales / Agency Partnerships Lead brief · "
    "100% dummy data, no confidential information · Built with Streamlit + an optional LLM layer"
)

with st.expander("ℹ️ What is this, and why does it map to the role?", expanded=False):
    st.markdown(
        """
This is a working prototype of the kind of operating tool a Head of Agency
Partnerships would want on day one: **one screen that shows pipeline health
across the Big 6 holding groups and three markets, flags what's at risk, and
uses AI to draft the QBR narrative and next steps** — turning a task that
normally takes a Partner Manager half a day into a two-minute review.

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
# would start with before layering on ML)
# ---------------------------------------------------------------------------
STAGE_STALL_THRESHOLD = {
    "Prospecting": 45, "Proposal Sent": 40, "Negotiation": 35,
    "JBP Signed": 60, "Live Campaign": 60, "Renewal": 30,
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
QUARTERLY_TARGET_USD = 9_500_000  # illustrative target for the filtered universe
coverage_ratio = total_pipeline / QUARTERLY_TARGET_USD if QUARTERLY_TARGET_USD else 0
non_endemic_share = scope.loc[scope["category_type"] == "Non-endemic", "pipeline_value_usd"].sum() / total_pipeline
jbp_signed_mask = scope["stage"].isin(["JBP Signed", "Live Campaign", "Renewal"])
jbp_attainment = scope.loc[jbp_signed_mask, "pipeline_value_usd"].sum() / total_pipeline
n_at_risk = int(scope["at_risk"].sum())

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Pipeline", f"${total_pipeline/1e6:,.2f}M")
k2.metric("Weighted Pipeline", f"${weighted_pipeline/1e6:,.2f}M")
k3.metric("Pipeline Coverage", f"{coverage_ratio:,.2f}x", help="Total pipeline ÷ illustrative quarterly target")
k4.metric("Non-endemic Share", f"{non_endemic_share*100:,.0f}%")
k5.metric("JBP / Live / Renewal Mix", f"{jbp_attainment*100:,.0f}%")
k6.metric("⚠️ At-risk Deals", n_at_risk, delta=None)

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1.2, 1])

with c1:
    stage_order = ["Prospecting", "Proposal Sent", "Negotiation", "JBP Signed", "Live Campaign", "Renewal"]
    by_stage = (
        scope.groupby("stage")["pipeline_value_usd"].sum().reindex(stage_order).fillna(0).reset_index()
    )
    fig_funnel = px.funnel(by_stage, x="pipeline_value_usd", y="stage", title="Pipeline by Stage (USD)")
    st.plotly_chart(fig_funnel, use_container_width=True)

with c2:
    by_cat = scope.groupby("category_type")["pipeline_value_usd"].sum().reset_index()
    fig_donut = px.pie(by_cat, names="category_type", values="pipeline_value_usd", hole=0.55,
                        title="Endemic vs. Non-endemic Mix")
    st.plotly_chart(fig_donut, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    by_holding_market = scope.groupby(["holding_group", "market"])["weighted_value_usd"].sum().reset_index()
    fig_bar = px.bar(by_holding_market, x="holding_group", y="weighted_value_usd", color="market",
                      title="Weighted Pipeline by Holding Group & Market", barmode="stack")
    st.plotly_chart(fig_bar, use_container_width=True)

with c4:
    by_vertical = scope.groupby("client_vertical")["pipeline_value_usd"].sum().sort_values(ascending=True).reset_index()
    fig_vert = px.bar(by_vertical, x="pipeline_value_usd", y="client_vertical", orientation="h",
                       title="Pipeline by Client Vertical (proxy for non-endemic mix)")
    st.plotly_chart(fig_vert, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# At-risk deals table
# ---------------------------------------------------------------------------
st.subheader("⚠️ At-risk deals (rule-based flagging)")
st.caption(
    "Flags deals stalled beyond a stage-specific threshold, or in late stages with low win "
    "probability — the first pass a real function would automate before layering on a predictive model."
)
risk_cols = ["deal_id", "holding_group", "market", "client_vertical", "stage",
             "pipeline_value_usd", "win_probability", "days_in_current_stage"]
st.dataframe(
    scope.loc[scope["at_risk"], risk_cols].sort_values("days_in_current_stage", ascending=False),
    use_container_width=True, hide_index=True,
)

st.divider()

# ---------------------------------------------------------------------------
# AI-drafted QBR narrative
# ---------------------------------------------------------------------------
st.subheader("🤖 AI-drafted QBR narrative & recommended actions")

focus_agency = st.selectbox("Generate for holding group:", ["All (selected filters)"] + sorted(scope["holding_group"].unique()))
agency_scope = scope if focus_agency == "All (selected filters)" else scope[scope["holding_group"] == focus_agency]

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
    "You write concise, board-ready QBR commentary for agency holding-group relationships "
    "(e.g. WPP, Publicis, Omnicom, IPG, Dentsu, Havas). Be specific, cite the numbers you're given, "
    "flag risk plainly, and end with 3 prioritized, concrete recommended actions for the "
    "Agency Partner Manager. Keep it under 200 words. No preamble."
)
user_prompt = (
    f"Holding group scope: {focus_agency}\n\n"
    f"Pipeline data summary:\n{stats_block}\n"
    "Draft the QBR narrative and recommended actions."
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

    return f"""**QBR Summary — {label}** *(template mode — add an API key in the sidebar for live GPT output)*

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

if st.button("✨ Generate QBR narrative"):
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
