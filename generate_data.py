"""
Generates dummy Careem Ads agency pipeline data for the prototype dashboard.
All company names, deal values, and contacts are fictional/illustrative -
no confidential or real Careem data is used anywhere in this file.
"""
import random
import datetime as dt
import pandas as pd

random.seed(42)

AGENCIES = [
    ("WPP", "GroupM"),
    ("Publicis Groupe", "Publicis Media"),
    ("Omnicom", "OMD"),
    ("IPG", "Mediabrands"),
    ("Dentsu", "Dentsu Media"),
    ("Havas", "Havas Media"),
]

MARKETS = ["UAE", "KSA", "Egypt"]

# Illustrative non-endemic and endemic client categories agencies might place
CLIENT_CATEGORIES = {
    "Non-endemic": ["Telco", "Banking & Fintech", "Auto", "Electronics", "Fashion & Retail"],
    "Endemic": ["QSR & Food", "Grocery & Retail", "Travel & Mobility", "Beauty & Personal Care"],
}

# Fictional client brand names per vertical (deliberately invented, not real
# companies) plus generic campaign types, combined into a readable deal name
# alongside the deal ID — e.g. "Lumo Beauty — Ramadan Launch".
FICTIONAL_BRANDS = {
    "Beauty & Personal Care": ["Lumo Beauty", "Nour Cosmetics", "Velvet & Co."],
    "Telco": ["Sahel Mobile", "Nexa Telecom", "Wave Connect"],
    "Banking & Fintech": ["Zenith Bank", "PayNest", "Amana Finance"],
    "Auto": ["Falcon Motors", "Drive Union", "Atlas Auto"],
    "Electronics": ["Kinetic Electronics", "Byte&Co", "Circuit House"],
    "Fashion & Retail": ["Marrakesh & Main", "Loom Fashion", "Dune Retail"],
    "QSR & Food": ["Spice Route Kitchen", "Basil & Bloom", "Crave Co."],
    "Grocery & Retail": ["Fresh Fields Market", "Souk Express", "Green Basket"],
    "Travel & Mobility": ["Horizon Travel", "Wanderway", "Oasis Tours"],
}
CAMPAIGN_TYPES = [
    "Ramadan Launch", "Back-to-School Push", "Summer Refresh", "Festive Campaign",
    "Loyalty Relaunch", "Regional Expansion", "New Product Launch", "Always-On Media",
    "Brand Awareness Push", "Year-End Sale",
]

# "PO Received / Budget Confirmed" sits between JBP Signed and Live Campaign:
# a JBP is a framework agreement at the holding-group level, but individual
# client budgets often still need their own sign-off (a PO/insertion order)
# before money actually moves — this stage distinguishes "agreed" from "funded".
STAGES = ["Prospecting", "Proposal Sent", "Negotiation", "JBP Signed",
          "PO Received / Budget Confirmed", "Live Campaign", "Renewal"]
# PO Received / Budget Confirmed isn't listed here — it's hardcoded to 100%
# probability below, since a confirmed budget isn't a probability estimate.
STAGE_WEIGHT = {"Prospecting": 0.10, "Proposal Sent": 0.30, "Negotiation": 0.55,
                "JBP Signed": 0.70, "Live Campaign": 0.95, "Renewal": 0.90}

QUARTERS = ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"]

rows = []
deal_id = 1000

for holding, network in AGENCIES:
    for market in MARKETS:
        # Each agency x market has a handful of deals in different stages
        n_deals = random.randint(3, 6)
        for _ in range(n_deals):
            category_type = random.choices(["Non-endemic", "Endemic"], weights=[0.65, 0.35])[0]
            client_vertical = random.choice(CLIENT_CATEGORIES[category_type])
            stage = random.choices(STAGES, weights=[0.14, 0.18, 0.18, 0.14, 0.12, 0.16, 0.08])[0]
            base_value = random.randint(80, 900) * 1000  # USD
            # Once the budget is actually confirmed (a PO), the deal isn't a probability
            # estimate anymore — it's paid for, so win-probability is 100% by definition.
            if stage == "PO Received / Budget Confirmed":
                probability = 1.0
            else:
                probability = round(min(0.98, max(0.05, STAGE_WEIGHT[stage] + random.uniform(-0.06, 0.06))), 2)
            quarter = random.choice(QUARTERS)
            # Most deals move at a normal pace; ~18% are genuinely stalled (long tail)
            if random.random() < 0.18:
                days_in_stage = random.randint(55, 140)
            else:
                days_in_stage = random.randint(2, 35)
            last_activity = dt.date(2026, 9, 15) - dt.timedelta(days=random.randint(0, min(days_in_stage, 20)))
            confirmed_stage_family = ["JBP Signed", "PO Received / Budget Confirmed", "Live Campaign", "Renewal"]
            jbp_target = base_value * random.uniform(1.1, 1.6) if stage in confirmed_stage_family else None
            brand = random.choice(FICTIONAL_BRANDS[client_vertical])
            campaign = random.choice(CAMPAIGN_TYPES)
            deal_name = f"{brand} — {campaign}"

            rows.append({
                "deal_id": f"CA-{deal_id}",
                "deal_name": deal_name,
                "holding_group": holding,
                "agency_network": network,
                "market": market,
                "client_vertical": client_vertical,
                "category_type": category_type,
                "stage": stage,
                "pipeline_value_usd": base_value,
                "win_probability": probability,
                "weighted_value_usd": round(base_value * probability),
                "quarter": quarter,
                "days_in_current_stage": days_in_stage,
                "last_activity_date": last_activity.isoformat(),
                "jbp_annual_target_usd": round(jbp_target) if jbp_target else "",
            })
            deal_id += 1

df = pd.DataFrame(rows)
df.to_csv("careem_ads_agency_pipeline_dummy.csv", index=False)
print(f"Generated {len(df)} rows -> careem_ads_agency_pipeline_dummy.csv")
print(df.head(10).to_string())
